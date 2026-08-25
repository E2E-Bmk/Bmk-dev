#!/usr/bin/env python3
"""
Spec2Repo Evaluation Pipeline

Two-phase evaluation in pure-Linux Docker containers:
  Phase 1: Agent generates code (Docker --network=none)
  Phase 2: Scoring sandbox runs pytest (Docker, network disconnected after install)

Usage:
    python harness/evaluate.py --model deepseek-chat --tasks diskcache-cache-fullrepro-001
    python harness/evaluate.py --model claude-sonnet-4 --tasks all
    python harness/evaluate.py --score-only --tasks diskcache-cache-fullrepro-001
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agents.base import AgentConfig
from agents.minisweagent_adapter import MiniSweAgentAdapter
from harness.sandbox import ScoringSandbox
from harness.core import layout

AGENTS = {
    "minisweagent": MiniSweAgentAdapter,
}

try:
    from agents.openhands_adapter import OpenHandsAdapter
    AGENTS["openhands"] = OpenHandsAdapter
except ImportError:
    pass


def load_config() -> dict:
    p = REPO_ROOT / "agents" / "config.json"
    return json.loads(p.read_text(encoding="utf-8-sig"))


def resolve_tasks(task_arg: str, tasks_dir: Path | None) -> list[str]:
    # Default to the bucketed in-repo layout (tasks/<lang>/<id>/); an
    # explicit --tasks-dir points at a flat external pool (<id>/spec.md).
    if tasks_dir is None:
        all_ids = layout.task_ids()
    else:
        all_ids = sorted(d.name for d in tasks_dir.iterdir()
                         if d.is_dir() and (d / "spec.md").exists())
    if task_arg == "all":
        return all_ids
    requested = [t.strip() for t in task_arg.split(",")]
    missing = [t for t in requested if t not in all_ids]
    if missing:
        print(f"WARNING: tasks not found: {missing}")
    return [t for t in requested if t in all_ids]


def task_language(tasks_root: Path | None, task_id: str) -> str | None:
    """The task's declared language, or None when it does not say.

    Read from the pool being evaluated rather than left to either phase to
    guess. `--tasks-dir` would otherwise never reach the agent adapter or
    `_task_language`, both of which fall back to Python — the adapter would put
    a Go candidate in a container with no Go compiler, and the sandbox would
    score a Rust task with the Python runner. Neither failure raises; both
    return a near-zero score that reads like a hard task.
    """
    if tasks_root is None:
        return layout.declared_language(task_id)
    try:
        return json.loads(
            (tasks_root / task_id / "task.json").read_text(encoding="utf-8")
        ).get("language")
    except (OSError, ValueError):
        return None


def run_one(agent, task_id: str, results_dir: Path, score_only: bool,
            oracle_root: Path | None, tasks_root: Path | None) -> dict:
    """Run agent + scoring for a single task."""
    if tasks_root is None:
        spec = layout.spec_path(task_id) or Path("/nonexistent")
    else:
        spec = tasks_root / task_id / "spec.md"
    if oracle_root is None:
        oracle = layout.oracle_dir(task_id) or Path("/nonexistent")
    else:
        oracle = oracle_root / task_id
    workspace = results_dir / task_id / "workspace"
    lang = task_language(tasks_root, task_id)
    out = {"task_id": task_id, "language": lang or "python"}

    # Phase 1 — Agent
    if not score_only:
        if not spec.exists():
            out["agent"] = {"status": "skipped", "error": "spec.md not found"}
        else:
            workspace.mkdir(parents=True, exist_ok=True)
            print(f"  [agent] generating code …")
            ar = agent.solve(task_id, spec, workspace, language=lang or "python")
            out["agent"] = {
                "status": (
                    "ok" if ar.success
                    else "incomplete" if ar.exit_status == "LimitsExceeded"
                    else "failed"
                ),
                "exit_status": ar.exit_status,
                "elapsed": round(ar.elapsed_seconds, 1),
                "cost": round(ar.cost, 4),
                "n_calls": ar.n_calls,
                # Effective budget, so a reader can tell whether any ceiling
                # was in force when this number was produced.
                "budget": {
                    "step_limit": agent.config.max_iterations,
                    "wall_time_limit_seconds": agent.config.timeout_seconds,
                    "cost_limit": agent.config.cost_limit,
                },
                "error": ar.error,
            }
    else:
        out["agent"] = {"status": "skipped (score-only)"}

    # Phase 2 — Score
    if not oracle.exists():
        out["score"] = {"status": "skipped", "error": "oracle dir not found"}
    elif not workspace.exists() or not any(workspace.iterdir()):
        out["score"] = {"status": "skipped", "error": "workspace empty"}
    else:
        print(f"  [score] pytest in sandbox …")
        sr = ScoringSandbox().score(task_id, workspace, oracle, language=lang)
        out["score"] = {
            "status": "ok" if sr.error is None else "error",
            "platform": sr.platform,
            "count_unit": sr.count_unit,
            "atomic_passed": sr.atomic_passed,
            "atomic_total": sr.atomic_total,
            "atomic_rate": sr.atomic_pass_rate,
            "integ_passed": sr.integration_passed,
            "integ_total": sr.integration_total,
            "integ_rate": sr.integration_pass_rate,
            "gap": sr.integration_gap,
            "adjusted_gap": sr.adjusted_gap,
            "adjusted_integ_passed": sr.adjusted_integ_passed,
            "adjusted_integ_total": sr.adjusted_integ_total,
            "adjusted_integ_rate": sr.adjusted_integ_rate,
            "gap_confidence": sr.gap_confidence,
            "elapsed": round(sr.elapsed_seconds, 1),
            "provenance": sr.provenance_log,
            "error": sr.error,
            "tests": sr.tests,
            "cases": sr.cases,
            "batches": sr.batches,
        }
        # An agent that died partway — on a rate limit, a gateway fault, a step
        # cap — still leaves files behind, so scoring runs and returns a low
        # number with `status: "ok"`. That number measures how far the agent got
        # before it was interrupted, not how hard the task is, and nothing else
        # in this block says so. Carry the verdict across rather than leaving it
        # to whoever reads the two sections to notice they disagree.
        agent_status = out.get("agent", {}).get("status")
        if agent_status not in (None, "ok", "skipped (score-only)"):
            out["score"]["agent_incomplete"] = {
                "agent_status": agent_status,
                "agent_exit_status": out["agent"].get("exit_status"),
                "note": "candidate is partial; this rate understates the model, "
                        "exclude it from pass-rate aggregates",
            }
        if sr.error is not None:
            # A zero is ambiguous on its own: it reads the same whether the
            # candidate is wrong or the batch never ran. The compiler/collector
            # output is the only thing that tells the two apart, and discarding
            # it forces a full re-score just to see why. Kept to the error path
            # so a passing result.json stays the size it has always been.
            out["score"]["install_log_tail"] = sr.install_log[-4000:]
            out["score"]["raw_stdout_tail"] = sr.raw_stdout[-8000:]
            out["score"]["raw_stderr_tail"] = sr.raw_stderr[-4000:]

    # Persist per-task result
    rf = results_dir / task_id / "result.json"
    rf.parent.mkdir(parents=True, exist_ok=True)
    rf.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def print_table(results: list[dict], model: str, agent_name: str):
    w = 88
    print(f"\n{'=' * w}")
    print(f"SUMMARY | agent={agent_name} | model={model}")
    print(f"{'=' * w}")
    print(f"{'Task':<38} {'Atomic':>7} {'Integ':>7} {'Gap':>6} {'AdjGap':>7} {'Conf':>10}")
    print(f"{'-' * 38} {'-' * 7} {'-' * 7} {'-' * 6} {'-' * 7} {'-' * 10}")

    scored = []
    for r in sorted(results, key=lambda x: x["task_id"]):
        s = r.get("score", {})
        if s.get("status") == "ok":
            ar = f"{s['atomic_rate'] * 100:.0f}%"
            ir = f"{s['integ_rate'] * 100:.0f}%"
            g = f"{s['gap'] * 100:+.0f}pp"
            ag = s.get("adjusted_gap")
            ag_str = f"{ag * 100:+.0f}pp" if ag is not None else "—"
            conf = s.get("gap_confidence", "?")[:10]
            scored.append(s)
        else:
            ar = ir = g = ag_str = "N/A"
            conf = ""
        print(f"  {r['task_id']:<36} {ar:>7} {ir:>7} {g:>6} {ag_str:>7} {conf:>10}")

    if scored:
        avg_a = sum(s["atomic_rate"] for s in scored) / len(scored)
        avg_i = sum(s["integ_rate"] for s in scored) / len(scored)
        avg_g = sum(s["gap"] for s in scored) / len(scored)
        adj_gaps = [s["adjusted_gap"] for s in scored if s.get("adjusted_gap") is not None]
        avg_ag = sum(adj_gaps) / len(adj_gaps) if adj_gaps else None
        avg_ag_str = f"{avg_ag * 100:+.1f}pp" if avg_ag is not None else "—"
        print(f"{'-' * 38} {'-' * 7} {'-' * 7} {'-' * 6} {'-' * 7} {'-' * 10}")
        print(f"  {'AVG':<36} {avg_a * 100:.1f}% {avg_i * 100:.1f}% "
              f"{avg_g * 100:+.1f}pp {avg_ag_str:>7}")

    print(f"\n  Total={len(results)}  Scored={len(scored)}  Failed={len(results) - len(scored)}")
    print(f"{'=' * w}")


def main():
    ap = argparse.ArgumentParser(description="Spec2Repo Evaluation")
    ap.add_argument("--agent", choices=list(AGENTS.keys()), default="minisweagent")
    ap.add_argument("--model", required=True)
    ap.add_argument("--tasks", default="all")
    ap.add_argument("--output-dir", default=None)
    ap.add_argument(
        "--oracle-dir",
        default=None,
        help="Oracle root (defaults to the included open oracle/ directory)",
    )
    ap.add_argument(
        "--tasks-dir",
        default=None,
        help="Task root holding <id>/spec.md (defaults to tasks/). Pair with "
             "--oracle-dir to score a pool outside the release set.",
    )
    ap.add_argument("--score-only", action="store_true")
    ap.add_argument("--max-iterations", type=int, default=None,
                    help="Per-task step cap (0 = unlimited, the default)")
    ap.add_argument("--timeout", type=int, default=None,
                    help="Per-task agent wall-clock cap in seconds (0 = unlimited, the default)")
    ap.add_argument("--cost-limit", type=float, default=None,
                    help="Per-task API cost cap in USD (0 = unlimited, the default)")
    args = ap.parse_args()

    cfg = load_config()
    mc = cfg["models"].get(args.model)
    if not mc:
        print(f"ERROR: unknown model '{args.model}'. Available: {list(cfg['models'].keys())}")
        sys.exit(1)

    api_key = os.environ.get(mc["api_key_env"], "")
    if not api_key and not args.score_only:
        print(f"ERROR: set {mc['api_key_env']}")
        sys.exit(1)

    ec = cfg["evaluation"]
    ac = AgentConfig(
        model=mc["model"], api_key=api_key,
        base_url=mc.get("base_url"),
        extra_params=mc.get("extra_params", {}),
        # `or` would swallow an explicit 0, which is how a limit is disabled.
        max_iterations=args.max_iterations if args.max_iterations is not None else ec.get("max_iterations", 0),
        timeout_seconds=args.timeout if args.timeout is not None else ec.get("timeout_seconds", 0),
        cost_limit=args.cost_limit if args.cost_limit is not None else ec.get("cost_limit", 0),
    )
    agent = AGENTS[args.agent](ac)

    tasks_root = Path(args.tasks_dir).resolve() if args.tasks_dir else None
    task_ids = resolve_tasks(args.tasks, tasks_root)
    out_dir = Path(args.output_dir) if args.output_dir else REPO_ROOT / "results" / f"{args.agent}_{args.model}"
    oracle_root = Path(args.oracle_dir).resolve() if args.oracle_dir else None
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Spec2Repo Evaluation")
    print(f"  Agent: {args.agent} | Model: {args.model}")
    print(f"  Tasks: {len(task_ids)} | Output: {out_dir}")
    print(f"  Budget: steps={ac.max_iterations or 'unlimited'} "
          f"wall={str(ac.timeout_seconds) + 's' if ac.timeout_seconds else 'unlimited'} "
          f"cost={'$' + str(ac.cost_limit) if ac.cost_limit else 'unlimited'} (recorded, not enforced)")
    print(f"  Docker: pure Linux, network=none (agent) / disconnected (score)")
    print()

    all_r = []
    for i, tid in enumerate(task_ids, 1):
        print(f"[{i}/{len(task_ids)}] {tid}")
        r = run_one(agent, tid, out_dir, args.score_only, oracle_root, tasks_root)
        all_r.append(r)
        s = r.get("score", {})
        if s.get("status") == "ok":
            ag = s.get("adjusted_gap")
            ag_str = f"  adj_gap={ag * 100:+.0f}pp" if ag is not None else ""
            print(f"  → atomic={s['atomic_rate'] * 100:.0f}%  "
                  f"integ={s['integ_rate'] * 100:.0f}%  "
                  f"gap={s['gap'] * 100:+.0f}pp{ag_str}")
        else:
            print(f"  → {r.get('status', s.get('status', '?'))}: {s.get('error', '')}")
        print()

    summary = {
        "agent": args.agent, "model": args.model,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total": len(all_r),
        "scored": sum(1 for r in all_r if r.get("score", {}).get("status") == "ok"),
        "results": all_r,
    }
    sp = out_dir / "summary.json"
    sp.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print_table(all_r, args.model, args.agent)
    print(f"\nSaved: {sp}")


if __name__ == "__main__":
    main()
