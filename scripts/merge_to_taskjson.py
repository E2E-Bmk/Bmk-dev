"""Merge scattered metadata files into task.json for each task directory."""
import json
import os
from pathlib import Path

TASKS_DIR = Path(r"G:\research\01_agents\swe-e2e\Bmk-dev\tasks")

def parse_taxonomy(path):
    taxonomy = {}
    stats = {"atomic": 0, "integration": 0, "system_e2e": 0}
    if not path.exists():
        return taxonomy, stats
    for line in path.read_text(encoding="utf-8").strip().splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        key = obj.get("taxonomy_key", "")
        layer = obj.get("layer", "unknown")
        taxonomy[key] = layer
        if layer in stats:
            stats[layer] += 1
    return taxonomy, stats

def parse_manifest(path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))

def parse_reference_score(path):
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if "pass_rate_excluding_skips" in data:
            return data["pass_rate_excluding_skips"]
        summary = data.get("summary") or data.get("grouped_results", {})
        if isinstance(summary, dict) and "passed" in summary and "total" in summary:
            t = summary["total"]
            return summary["passed"] / t if t > 0 else 0
        if "passed" in data and "total" in data:
            t = data["total"]
            return data["passed"] / t if t > 0 else 0
        return 1.0
    except:
        return None

def parse_score_result(path):
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        # Try grouped_results → summary
        gr = data.get("grouped_results", {})
        for key, val in gr.items():
            jr = val.get("json_report", {})
            s = jr.get("summary", {})
            if "passed" in s and "total" in s:
                return {"passed": s["passed"], "total": s["total"]}
        # Try top-level summary
        if "summary" in data:
            s = data["summary"]
            if "passed" in s:
                return {"passed": s["passed"], "total": s["total"]}
        # Try top-level
        if "passed" in data and "total" in data:
            return {"passed": data["passed"], "total": data["total"]}
        return None
    except:
        return None

def count_nodeids(path):
    if not path.exists():
        return 0
    lines = [l for l in path.read_text(encoding="utf-8").strip().splitlines() if l.strip()]
    return len(lines)

def process_task(task_dir):
    name = task_dir.name
    manifest = parse_manifest(task_dir / "MANIFEST.json")
    taxonomy, stats = parse_taxonomy(task_dir / "taxonomy.jsonl")
    ref_rate = parse_reference_score(task_dir / "reference_score.json")
    candidate = parse_score_result(task_dir / "score_result.json")
    oracle_count = count_nodeids(task_dir / "kept_nodeids.txt")

    scorer_isolation = manifest.get("scorer_isolation", "")
    if isinstance(scorer_isolation, list):
        scorer_isolation = scorer_isolation
    elif isinstance(scorer_isolation, str) and scorer_isolation:
        scorer_isolation = scorer_isolation.replace("score_pytest_original.py ", "").replace("harness/score_pytest_original.py ", "")
        scorer_isolation = [s.strip() for s in scorer_isolation.split() if s.startswith("--")]

    task_json = {
        "instance_id": manifest.get("task_id", name),
        "status": manifest.get("status", "QUALIFIED"),
        "repo": manifest.get("repo", ""),
        "repo_commit": manifest.get("commit", ""),
        "spec_version": manifest.get("spec_version", "v1"),
        "oracle": {
            "test_files": ["oracle/test_atomic.py", "oracle/test_integration.py"],
            "count": oracle_count,
            "scorer_isolation": scorer_isolation,
        },
        "taxonomy": taxonomy,
        "stats": stats,
        "reference_pass_rate": ref_rate,
        "candidate_score": candidate,
    }

    # Write task.json
    (task_dir / "task.json").write_text(
        json.dumps(task_json, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Delete old files
    for f in [
        "kept_nodeids.txt", "taxonomy.jsonl", "MANIFEST.json",
        "reference_score.json", "score_result.json", "diagnosis_report.md",
        "filter_notes.md", "test_taxonomy_score.csv",
    ]:
        p = task_dir / f
        if p.exists():
            p.unlink()
    # Delete reference_score_p*.json
    for p in task_dir.glob("reference_score_p*.json"):
        p.unlink()

    return name, oracle_count, stats

if __name__ == "__main__":
    results = []
    for task_dir in sorted(TASKS_DIR.iterdir()):
        if not task_dir.is_dir():
            continue
        if not (task_dir / "spec.md").exists():
            continue
        try:
            name, count, stats = process_task(task_dir)
            results.append((name, count, stats))
            print(f"OK: {name} ({count} tests, a={stats['atomic']} i={stats['integration']} e={stats['system_e2e']})")
        except Exception as e:
            print(f"ERROR: {task_dir.name}: {e}")

    print(f"\nDone: {len(results)} tasks processed")
