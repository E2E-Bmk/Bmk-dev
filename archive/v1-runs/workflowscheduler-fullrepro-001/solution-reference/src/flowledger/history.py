"""Public history and status projections."""

from __future__ import annotations

from .models import utc
from .scheduler import next_run
from .spec import load_spec
from .store import state_of


TERMINAL_RUNS = {"succeeded", "failed", "cancelled"}


def _run_detail(data: dict, run: dict) -> dict:
    run_id = run["id"]
    return {
        **dict(run),
        "steps": sorted((dict(v) for v in data.get("steps", {}).get(run_id, {}).values()), key=lambda s: s.get("order", 0)),
        "attempts": [dict(a) for a in data.get("attempts", []) if a.get("run_id") == run_id],
    }

def status_report(store, workflow: str | None = None, run_id: str | None = None) -> dict:
    """Return status projection."""
    data = state_of(store)
    runs = list(data.get("runs", {}).values())
    if workflow is not None:
        runs = [r for r in runs if r.get("workflow") == workflow]
    if run_id is not None:
        runs = [r for r in runs if r.get("id") == run_id]
    runs = sorted(runs, key=lambda r: (r.get("created_at", ""), r.get("id", "")))
    counts: dict[str, int] = {}
    for run in runs:
        counts[run["status"]] = counts.get(run["status"], 0) + 1
    return {
        "runs": [_run_detail(data, run) for run in runs],
        "counts": counts,
        "filters": {"workflow": workflow, "run_id": run_id},
    }


def history_report(store, workflow: str | None = None) -> dict:
    """Return run and attempt history."""
    data = state_of(store)
    runs = list(data.get("runs", {}).values())
    if workflow is not None:
        runs = [r for r in runs if r.get("workflow") == workflow]
    runs = sorted((dict(r) for r in runs), key=lambda r: (r.get("created_at", ""), r.get("id", "")))
    run_ids = {r["id"] for r in runs}
    attempts = [dict(a) for a in data.get("attempts", []) if a.get("run_id") in run_ids]
    attempts.sort(key=lambda a: (a.get("started_at") or a.get("finished_at") or "", a.get("run_id", ""), a.get("step_id", ""), a.get("attempt", 0)))
    return {"runs": runs, "attempts": attempts}


def next_runs_report(store, now: str) -> dict:
    """Return next-run projection for known schedules."""
    data = state_of(store)
    now = utc(now)
    reports = []
    for name, spec_data in sorted(data.get("specs", {}).items()):
        spec = load_spec(spec_data)
        schedule_state = data.get("schedules", {}).get(name, {})
        report = next_run(spec, schedule_state.get("last_slot"), now)
        active = [
            r["id"]
            for r in data.get("runs", {}).values()
            if r.get("workflow") == name and r.get("status") not in TERMINAL_RUNS
        ]
        report["active_run_ids"] = sorted(active)
        reports.append(report)
    return {"now": now, "workflows": reports}
