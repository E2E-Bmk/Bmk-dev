"""Compute Integration Gap metric for all Spec2Repo tasks."""
import json
import os
from pathlib import Path

TASKS_DIR = Path(r"G:\research\01_agents\swe-e2e\Bmk-dev\tasks")


def nodeid_to_keys(nodeid: str) -> list:
    """Convert pytest nodeid to possible taxonomy keys.
    e.g. 'tests/test_transport_fullrepro.py::test_name'
      -> ['test_transport_fullrepro::test_name', 'test_transport_fullrepro.test_name']
    e.g. 'filter/generated_tests.py::test_name'
      -> ['generated_tests::test_name', 'generated_tests.test_name']
    """
    if "::" in nodeid:
        file_part, test_name = nodeid.split("::", 1)
    else:
        return [nodeid]
    
    module = file_part.rsplit("/", 1)[-1].replace(".py", "")
    return [
        f"{module}::{test_name}",
        f"{module}.{test_name}",
        test_name,
    ]


def load_taxonomy(task_dir: Path) -> dict:
    """Load taxonomy.jsonl -> dict of taxonomy_key -> layer.
    Handles both 'taxonomy_key' and 'test_id' field names.
    """
    taxonomy = {}
    path = task_dir / "taxonomy.jsonl"
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            key = entry.get("taxonomy_key") or entry.get("test_id", "")
            layer = entry.get("layer", "")
            if layer in ("atomic", "integration", "system_e2e"):
                taxonomy[key] = layer
    return taxonomy


def extract_test_outcomes(score_data: dict) -> dict:
    """Extract per-test outcomes from score_result.json.
    Returns dict of nodeid -> outcome ('passed'/'failed'/'error')
    """
    outcomes = {}
    
    grouped = score_data.get("grouped_results", {})
    for file_key, file_data in grouped.items():
        json_report = file_data.get("json_report")
        if not json_report:
            continue
        tests = json_report.get("tests", [])
        for test in tests:
            nodeid = test.get("nodeid", "")
            outcome = test.get("outcome", "unknown")
            outcomes[nodeid] = outcome
    
    return outcomes


def match_outcomes_to_taxonomy(taxonomy: dict, outcomes: dict) -> dict:
    """Match test outcomes to taxonomy layers.
    Returns by_layer dict with pass/total counts.
    """
    atomic_passed = 0
    atomic_total = 0
    integ_passed = 0
    integ_total = 0
    matched_count = 0
    
    # Build a reverse lookup: for each taxonomy_key, find possible matching nodeids
    # Strategy: normalize both sides and match
    
    # Normalize taxonomy keys
    tax_normalized = {}
    for tax_key, layer in taxonomy.items():
        # Normalize: module::test or module.test -> just the test function name as backup
        if "::" in tax_key:
            parts = tax_key.split("::", 1)
            module = parts[0]
            test_fn = parts[1]
        elif "." in tax_key:
            parts = tax_key.rsplit(".", 1)
            module = parts[0]
            test_fn = parts[1]
        else:
            module = ""
            test_fn = tax_key
        
        # Store multiple possible keys
        tax_normalized[tax_key] = {
            "layer": layer,
            "module": module,
            "test_fn": test_fn,
            "matched": False
        }
    
    # Normalize outcome keys
    out_normalized = {}
    for nodeid, outcome in outcomes.items():
        if "::" in nodeid:
            file_part, test_fn = nodeid.split("::", 1)
            module = file_part.rsplit("/", 1)[-1].replace(".py", "")
        else:
            module = ""
            test_fn = nodeid
        
        out_normalized[nodeid] = {
            "outcome": outcome,
            "module": module,
            "test_fn": test_fn,
            "colon_key": f"{module}::{test_fn}",
            "dot_key": f"{module}.{test_fn}",
        }
    
    # Match: try exact key match first, then normalized match
    for tax_key, tax_info in tax_normalized.items():
        layer = tax_info["layer"]
        found_outcome = None
        
        # Try direct match against outcome keys
        for nodeid, out_info in out_normalized.items():
            if (tax_key == out_info["colon_key"] or 
                tax_key == out_info["dot_key"] or
                tax_key == nodeid or
                (tax_info["test_fn"] == out_info["test_fn"] and 
                 tax_info["module"] == out_info["module"])):
                found_outcome = out_info["outcome"]
                matched_count += 1
                break
        
        if found_outcome is None:
            # Last resort: match by test function name only (risky if duplicates)
            for nodeid, out_info in out_normalized.items():
                if tax_info["test_fn"] == out_info["test_fn"]:
                    found_outcome = out_info["outcome"]
                    matched_count += 1
                    break
        
        if found_outcome is not None:
            if layer == "atomic":
                atomic_total += 1
                if found_outcome == "passed":
                    atomic_passed += 1
            elif layer in ("integration", "system_e2e"):
                integ_total += 1
                if found_outcome == "passed":
                    integ_passed += 1
    
    return {
        "atomic": {"passed": atomic_passed, "total": atomic_total},
        "integration_e2e": {"passed": integ_passed, "total": integ_total},
        "matched": matched_count,
        "taxonomy_total": len(taxonomy)
    }


def compute_gap(task_dir: Path) -> dict:
    """Compute integration gap for a single task."""
    task_id = task_dir.name
    result = {"task_id": task_id}
    
    # Try by_layer from MANIFEST.json
    manifest_path = task_dir / "MANIFEST.json"
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        by_layer = manifest.get("by_layer")
        if by_layer:
            atomic = by_layer.get("atomic", {})
            integration = by_layer.get("integration", {})
            system_e2e = by_layer.get("system_e2e", {})
            
            result["atomic_passed"] = atomic.get("passed", 0)
            result["atomic_total"] = atomic.get("total", 0)
            result["integ_passed"] = integration.get("passed", 0) + system_e2e.get("passed", 0)
            result["integ_total"] = integration.get("total", 0) + system_e2e.get("total", 0)
            result["source"] = "MANIFEST.json"
            return finalize_result(result)
    
    # Try by_layer from score_result.json
    score_path = task_dir / "score_result.json"
    with open(score_path, "r", encoding="utf-8") as f:
        score_data = json.load(f)
    
    by_layer = score_data.get("by_layer")
    if by_layer:
        atomic = by_layer.get("atomic", {})
        integration = by_layer.get("integration", {})
        system_e2e = by_layer.get("system_e2e", {})
        
        result["atomic_passed"] = atomic.get("passed", 0)
        result["atomic_total"] = atomic.get("total", 0)
        result["integ_passed"] = integration.get("passed", 0) + system_e2e.get("passed", 0)
        result["integ_total"] = integration.get("total", 0) + system_e2e.get("total", 0)
        result["source"] = "score_result.by_layer"
        return finalize_result(result)
    
    # Fall back to computing from taxonomy + test outcomes
    taxonomy = load_taxonomy(task_dir)
    outcomes = extract_test_outcomes(score_data)
    
    if not outcomes:
        result["error"] = "No per-test outcomes in score_result.json"
        result["gap"] = None
        return result
    
    layer_results = match_outcomes_to_taxonomy(taxonomy, outcomes)
    
    result["atomic_passed"] = layer_results["atomic"]["passed"]
    result["atomic_total"] = layer_results["atomic"]["total"]
    result["integ_passed"] = layer_results["integration_e2e"]["passed"]
    result["integ_total"] = layer_results["integration_e2e"]["total"]
    result["matched"] = layer_results["matched"]
    result["taxonomy_total"] = layer_results["taxonomy_total"]
    result["source"] = "computed"
    
    return finalize_result(result)


def finalize_result(result: dict) -> dict:
    """Calculate rates and gap from passed/total counts."""
    at = result.get("atomic_total", 0)
    it = result.get("integ_total", 0)
    
    if at > 0:
        result["atomic_rate"] = result["atomic_passed"] / at
    else:
        result["atomic_rate"] = None
    
    if it > 0:
        result["integ_rate"] = result["integ_passed"] / it
    else:
        result["integ_rate"] = None
    
    if result["atomic_rate"] is not None and result["integ_rate"] is not None:
        result["gap"] = result["atomic_rate"] - result["integ_rate"]
    else:
        result["gap"] = None
    
    return result


def main():
    results = []
    
    for task_dir in sorted(TASKS_DIR.iterdir()):
        if not task_dir.is_dir():
            continue
        score_path = task_dir / "score_result.json"
        taxonomy_path = task_dir / "taxonomy.jsonl"
        
        if not score_path.exists() or not taxonomy_path.exists():
            continue
        
        try:
            result = compute_gap(task_dir)
            results.append(result)
        except Exception as e:
            results.append({
                "task_id": task_dir.name,
                "error": str(e),
                "gap": None
            })
    
    # Sort by gap (highest first), None values at end
    results.sort(key=lambda x: x.get("gap") if x.get("gap") is not None else -999, reverse=True)
    
    # Output as JSON
    output_path = TASKS_DIR.parent / "integration_gap_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Print summary table
    print(f"\n{'Task':<45} {'Atomic':>12} {'Integ+E2E':>12} {'Gap':>8} {'Source':<20}")
    print("-" * 100)
    for r in results:
        task = r["task_id"]
        if r.get("error"):
            print(f"{task:<45} ERROR: {r['error']}")
            continue
        
        ap = r.get('atomic_passed', 0)
        at = r.get('atomic_total', 0)
        ip = r.get('integ_passed', 0)
        it = r.get('integ_total', 0)
        
        atomic_str = f"{r['atomic_rate']*100:.1f}% ({ap}/{at})" if r.get("atomic_rate") is not None else f"N/A (0/{at})"
        integ_str = f"{r['integ_rate']*100:.1f}% ({ip}/{it})" if r.get("integ_rate") is not None else f"N/A (0/{it})"
        gap_str = f"{r['gap']*100:+.1f}pp" if r.get("gap") is not None else "N/A"
        src = r.get("source", "?")
        
        print(f"{task:<45} {atomic_str:>12} {integ_str:>12} {gap_str:>8} {src:<20}")
    
    print(f"\nTotal tasks processed: {len(results)}")
    valid = [r for r in results if r.get("gap") is not None]
    print(f"Tasks with valid Integration Gap: {len(valid)}")
    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()
