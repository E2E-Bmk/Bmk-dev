#!/usr/bin/env python3
"""Score MiniZK hidden rubrics against a candidate solution."""

import argparse
import json
import os
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path


def norm(text):
    return (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()


def write_file(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def subst(value, mapping):
    if value is None:
        return None
    for key, replacement in mapping.items():
        value = value.replace(key, replacement)
    return value


def command_for(solution_dir):
    script = solution_dir / "zmini.py"
    if script.exists():
        return ["py", "-3.11", str(script)]
    executable = solution_dir / "zmini"
    if executable.exists():
        return [str(executable)]
    raise FileNotFoundError(f"no zmini.py or zmini executable found in {solution_dir}")


def setup_case(case):
    tmp = tempfile.TemporaryDirectory(prefix="zmini-score-", dir=str(Path.cwd()))
    tmpdir = Path(tmp.name)
    nb = tmpdir / "notebook"
    other = tmpdir / "other"
    mapping = {"{tmp}": str(tmpdir), "{nb}": str(nb), "{other}": str(other)}
    for raw_path, raw_text in case.get("setup_files", {}).items():
        path = Path(subst(raw_path, mapping))
        text = subst(raw_text, mapping)
        write_file(path, text)
    for raw_dir in case.get("checks", {}).get("dirs_exist", []):
        Path(subst(raw_dir, mapping)).mkdir(parents=True, exist_ok=True)
    return tmp, tmpdir, mapping


def run_step(solution_dir, step, mapping, default_cwd, timeout):
    args = [subst(arg, mapping) for arg in step.get("args", [])]
    stdin = subst(step.get("stdin", ""), mapping)
    cwd = Path(subst(step.get("cwd", str(default_cwd)), mapping))
    cwd.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    for key, value in step.get("env", {}).items():
        env[key] = subst(value, mapping)
    proc = subprocess.run(
        command_for(solution_dir) + args,
        input=stdin,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        cwd=str(cwd),
        env=env,
        timeout=timeout,
    )
    return {"stdout": norm(proc.stdout), "stderr": norm(proc.stderr), "exit_code": proc.returncode, "args": args}


def load_json(text):
    return json.loads(text or "null")


def note_path(note):
    return str(note.get("path", note.get("file", ""))).replace("\\", "/")


def note_title(note):
    return str(note.get("title", ""))


def note_tags(note):
    tags = note.get("tags", [])
    if isinstance(tags, str):
        return {tags}
    return {str(tag) for tag in tags}


def note_links(note):
    links = note.get("links", [])
    if isinstance(links, str):
        return [links]
    return [str(link) for link in links]


def find_note(notes, expected_path):
    expected_path = expected_path.replace("\\", "/")
    for note in notes:
        path = note_path(note)
        if path == expected_path or path.endswith("/" + expected_path):
            return note
    return None


def check_json_notes(stdout, spec):
    errors = []
    data = load_json(stdout)
    notes = data if isinstance(data, list) else data.get("notes", []) if isinstance(data, dict) else []
    for path in spec.get("expected_paths_exact", []):
        if not find_note(notes, path):
            errors.append(f"missing note path {path!r}")
    for path in spec.get("forbidden_paths", []):
        if find_note(notes, path):
            errors.append(f"forbidden note path {path!r}")
    for expected in spec.get("expected", []):
        note = find_note(notes, expected["path"])
        if not note:
            errors.append(f"missing note {expected['path']!r}")
            continue
        if "title" in expected and note_title(note) != expected["title"]:
            errors.append(f"title mismatch for {expected['path']!r}: {note_title(note)!r}")
        missing_tags = set(expected.get("tags", [])) - note_tags(note)
        if missing_tags:
            errors.append(f"missing tags for {expected['path']!r}: {sorted(missing_tags)!r}")
        for needle in expected.get("links_any", []):
            if not any(needle in link for link in note_links(note)):
                errors.append(f"missing link containing {needle!r} in {note_links(note)!r}")
        if "min_word_count" in expected:
            count = int(note.get("word_count", note.get("word-count", 0)))
            if count < int(expected["min_word_count"]):
                errors.append(f"word count too low for {expected['path']!r}: {count}")
    return errors


def check_json_tags(stdout, spec):
    errors = []
    data = load_json(stdout)
    tags = data if isinstance(data, list) else data.get("tags", []) if isinstance(data, dict) else []
    counts = {}
    for item in tags:
        if isinstance(item, dict):
            name = str(item.get("name", item.get("tag", "")))
            count = int(item.get("note_count", item.get("note-count", item.get("count", 0))))
            counts[name] = count
        else:
            counts[str(item)] = counts.get(str(item), 0) + 1
    for tag, expected_count in spec.get("expected_counts", {}).items():
        if counts.get(tag) != expected_count:
            errors.append(f"tag {tag!r}: expected {expected_count}, got {counts.get(tag)}; counts={counts!r}")
    return errors


def check_json_graph(stdout, spec):
    errors = []
    data = load_json(stdout)
    nodes = data.get("nodes", []) if isinstance(data, dict) else []
    edges = data.get("edges", []) if isinstance(data, dict) else []
    node_paths = [str(node.get("path", node)) if isinstance(node, dict) else str(node) for node in nodes]
    for path in spec.get("nodes", []):
        if not any(p.endswith(path) or p == path for p in node_paths):
            errors.append(f"missing graph node {path!r}; nodes={node_paths!r}")
    edge_pairs = []
    for edge in edges:
        if isinstance(edge, dict):
            edge_pairs.append((str(edge.get("source", "")), str(edge.get("target", ""))))
        elif isinstance(edge, (list, tuple)) and len(edge) >= 2:
            edge_pairs.append((str(edge[0]), str(edge[1])))
    for source, target in spec.get("edges", []):
        if not any(s.endswith(source) and t.endswith(target) for s, t in edge_pairs):
            errors.append(f"missing edge {(source, target)!r}; edges={edge_pairs!r}")
    return errors


def check_stdout(stdout, contains=None, forbidden=None):
    errors = []
    for needle in contains or []:
        if needle not in stdout:
            errors.append(f"stdout missing {needle!r}; stdout={stdout!r}")
    for needle in forbidden or []:
        if needle in stdout:
            errors.append(f"stdout contains forbidden {needle!r}; stdout={stdout!r}")
    return errors


def check_order(text, items, label):
    errors = []
    indexes = []
    for item in items or []:
        idx = text.find(item)
        if idx < 0:
            errors.append(f"{label} missing order item {item!r}; text={text!r}")
        else:
            indexes.append(idx)
    if indexes and indexes != sorted(indexes):
        errors.append(f"{label} order mismatch for {items!r}: indexes={indexes!r}")
    return errors


def check_json_tags_order(stdout, expected_order):
    errors = []
    data = load_json(stdout)
    tags = data if isinstance(data, list) else data.get("tags", []) if isinstance(data, dict) else []
    names = [str(item.get("name", item.get("tag", ""))) if isinstance(item, dict) else str(item) for item in tags]
    positions = []
    for name in expected_order or []:
        if name not in names:
            errors.append(f"tag order missing {name!r}; names={names!r}")
        else:
            positions.append(names.index(name))
    if positions and positions != sorted(positions):
        errors.append(f"tag order mismatch {expected_order!r}; names={names!r}")
    return errors


def evaluate(case, results, mapping):
    errors = []
    checks = case.get("checks", {})
    final = results[-1] if results else {"stdout": "", "stderr": "", "exit_code": 0}
    steps = case.get("steps", [])

    for idx, step in enumerate(steps):
        allow_error = step.get("allow_error", False)
        if not allow_error and results[idx]["exit_code"] != 0:
            errors.append(f"step {idx} exit {results[idx]['exit_code']}: {results[idx]['stderr']}")

    if checks.get("expect_error") and final["exit_code"] == 0:
        errors.append("expected final command error")
    if "stderr_contains_any" in checks:
        haystack = (final["stderr"] + "\n" + final["stdout"]).lower()
        if not any(token.lower() in haystack for token in checks["stderr_contains_any"]):
            errors.append(f"stderr/stdout missing any of {checks['stderr_contains_any']!r}")
    for raw_path in checks.get("files_exist", []):
        path = Path(subst(raw_path, mapping))
        if not path.exists():
            errors.append(f"missing file/dir {path}")
    for raw_path, needles in checks.get("files_contain", {}).items():
        path = Path(subst(raw_path, mapping))
        if not path.exists():
            errors.append(f"missing file {path}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for needle in needles:
            if needle not in text:
                errors.append(f"{path} missing {needle!r}")
    errors.extend(check_stdout(final["stdout"], checks.get("stdout_contains"), checks.get("stdout_forbidden")))
    errors.extend(check_order(final["stdout"], checks.get("stdout_order"), "stdout"))
    if "json_notes" in checks:
        errors.extend(check_json_notes(final["stdout"], checks["json_notes"]))
    if "json_tags" in checks:
        errors.extend(check_json_tags(final["stdout"], checks["json_tags"]))
    if "json_tags_order" in checks:
        errors.extend(check_json_tags_order(final["stdout"], checks["json_tags_order"]))
    for idx, spec in checks.get("step_stdout_contains", {}).items():
        errors.extend(check_stdout(results[int(idx)]["stdout"], spec, []))
    for idx, spec in checks.get("step_stdout_forbidden", {}).items():
        errors.extend(check_stdout(results[int(idx)]["stdout"], [], spec))
    for idx, spec in checks.get("step_json_tags", {}).items():
        errors.extend(check_json_tags(results[int(idx)]["stdout"], spec))
    for idx, spec in checks.get("step_json_graph", {}).items():
        errors.extend(check_json_graph(results[int(idx)]["stdout"], spec))
    for idx in checks.get("step_expect_error", []):
        if results[int(idx)]["exit_code"] == 0:
            errors.append(f"step {idx} expected error")
    for idx, tokens in checks.get("step_stderr_contains_any", {}).items():
        result = results[int(idx)]
        haystack = (result["stderr"] + "\n" + result["stdout"]).lower()
        if not any(token.lower() in haystack for token in tokens):
            errors.append(f"step {idx} stderr/stdout missing any of {tokens!r}")
    return errors


def run_case(case, solution_dir, timeout):
    tmp, tmpdir, mapping = setup_case(case)
    try:
        results = [run_step(solution_dir, step, mapping, tmpdir, timeout) for step in case.get("steps", [])]
        errors = evaluate(case, results, mapping)
        return {**case, "passed": not errors, "errors": errors, "step_results": results}
    except subprocess.TimeoutExpired:
        return {**case, "passed": False, "errors": [f"timeout after {timeout}s"], "step_results": []}
    except Exception as exc:
        return {**case, "passed": False, "errors": [str(exc)], "step_results": []}
    finally:
        tmp.cleanup()


def bucket_summary(results, key_fn):
    bucket = defaultdict(lambda: {"weight": 0, "passed_weight": 0, "cases": 0, "passed": 0})
    for result in results:
        weight = int(result["weight"])
        key = key_fn(result)
        bucket[key]["weight"] += weight
        bucket[key]["cases"] += 1
        if result["passed"]:
            bucket[key]["passed_weight"] += weight
            bucket[key]["passed"] += 1
    return dict(sorted(bucket.items()))


def score_for(results, layer):
    selected = [result for result in results if result.get("layer") == layer]
    total = sum(int(result["weight"]) for result in selected)
    passed = sum(int(result["weight"]) for result in selected if result["passed"])
    return {
        "weight": total,
        "passed_weight": passed,
        "score": passed / total if total else None,
        "cases": len(selected),
        "passed_cases": sum(1 for result in selected if result["passed"]),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("rubrics", type=Path)
    parser.add_argument("--solution-dir", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    rubrics = json.loads(args.rubrics.read_text(encoding="utf-8"))
    results = [run_case(case, args.solution_dir, args.timeout) for case in rubrics]
    total_weight = sum(int(result["weight"]) for result in results)
    passed_weight = sum(int(result["weight"]) for result in results if result["passed"])
    unit_score = score_for(results, "unit")
    system_score = score_for(results, "system")
    gap = None
    if unit_score["score"] is not None and system_score["score"] is not None:
        gap = unit_score["score"] - system_score["score"]
    report = {
        "total_cases": len(results),
        "passed_cases": sum(1 for result in results if result["passed"]),
        "total_weight": total_weight,
        "passed_weight": passed_weight,
        "score": passed_weight / total_weight if total_weight else 0,
        "unit_score": unit_score,
        "system_score": system_score,
        "unit_system_gap": gap,
        "layers": bucket_summary(results, lambda r: r.get("layer", "unspecified")),
        "categories": bucket_summary(results, lambda r: r.get("category", "unspecified")),
        "system_dimensions": bucket_summary(
            [r for r in results if r.get("layer") == "system"],
            lambda r: r.get("system_dimension", "unspecified"),
        ),
        "failed_cases": [result for result in results if not result["passed"]],
        "all_cases": results,
    }
    print(f"Passed cases: {report['passed_cases']} / {report['total_cases']}")
    print(f"Weighted score: {passed_weight} / {total_weight}")
    print(f"Percentage: {report['score'] * 100:.2f}%")
    if gap is not None:
        print(f"Unit score: {unit_score['passed_weight']} / {unit_score['weight']} = {unit_score['score'] * 100:.2f}%")
        print(f"System score: {system_score['passed_weight']} / {system_score['weight']} = {system_score['score'] * 100:.2f}%")
        print(f"Gap: {gap * 100:.2f}pp")
    for result in report["failed_cases"]:
        print(f"FAIL {result['id']}: {'; '.join(result['errors'])}")
    if args.json_out:
        args.json_out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Wrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
