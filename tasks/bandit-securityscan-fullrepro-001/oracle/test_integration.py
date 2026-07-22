# Spec2Repo oracle - integration tests for bandit-securityscan-fullrepro-001
import csv
import io
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
import yaml

from conftest import run_bandit, write_source, json_scan, one_issue, ids


def test_issue_preserves_supplied_plugin_result_fields(tmp_path):
    """Seam: protocol handoff — integration path for issue preserves supplied plugin result fields across cooperating public APIs."""
    import bandit

    issue = bandit.Issue(
        bandit.HIGH,
        cwe=79,
        confidence=bandit.MEDIUM,
        text="unsafe markup",
        lineno=4,
        test_id="B900",
        col_offset=2,
        end_col_offset=8,
    )
    assert issue.severity == "HIGH"
    assert issue.confidence == "MEDIUM"
    assert issue.text == "unsafe markup"
    assert (issue.lineno, issue.test_id, issue.col_offset, issue.end_col_offset) == (4, "B900", 2, 8)

    projected = one_issue(
        tmp_path,
        "from markupsafe import Markup\nMarkup(user_text)\n",
        "B704",
        severity="MEDIUM",
        confidence="HIGH",
        cwe=79,
    )
    assert projected["issue_cwe"]["id"] == 79


def test_rule_b110_try_except_pass(tmp_path):
    """Seam: error propagation — integration path for rule b110 try except pass across cooperating public APIs."""
    config = write_source(
        tmp_path,
        "typed-exception.yaml",
        "try_except_pass:\n  check_typed_exception: false\n"
        "try_except_continue:\n  check_typed_exception: false\n",
    )
    pass_source = """try:
    work()
except:
    pass
try:
    work()
except Exception:
    pass
try:
    work()
except ZeroDivisionError:
    pass
"""
    pass_proc, pass_report, _ = json_scan(
        tmp_path, pass_source, "-c", str(config), "-t", "B110", name="pass_handlers.py"
    )
    assert pass_proc.returncode == 1
    assert len(pass_report["results"]) == 2
    assert {
        (issue["test_id"], issue["issue_severity"], issue["issue_confidence"], issue["issue_cwe"]["id"])
        for issue in pass_report["results"]
    } == {("B110", "LOW", "HIGH", 703)}

    continue_source = """for item in items:
    try:
        work(item)
    except:
        continue
for item in items:
    try:
        work(item)
    except Exception:
        continue
for item in items:
    try:
        work(item)
    except ZeroDivisionError:
        continue
"""
    continue_proc, continue_report, _ = json_scan(
        tmp_path,
        continue_source,
        "-c",
        str(config),
        "-t",
        "B112",
        name="continue_handlers.py",
    )
    assert continue_proc.returncode == 1
    assert len(continue_report["results"]) == 2
    assert {
        (issue["test_id"], issue["issue_severity"], issue["issue_confidence"], issue["issue_cwe"]["id"])
        for issue in continue_report["results"]
    } == {("B112", "LOW", "HIGH", 703)}


def test_stdin_scan_reports_stdin_filename_and_status(tmp_path):
    """Seam: protocol handoff — integration path for stdin scan reports stdin filename and status across cooperating public APIs."""
    proc = run_bandit("bandit", ["-q", "-f", "json", "-t", "B101", "-"], stdin="assert value\n")
    report = json.loads(proc.stdout)
    assert proc.returncode == 1
    assert report["results"][0]["filename"] == "<stdin>"
    assert report["results"][0]["test_id"] == "B101"


def test_recursive_scan_discovers_nested_python(tmp_path):
    """Seam: protocol handoff — integration path for recursive scan discovers nested python across cooperating public APIs."""
    target = write_source(tmp_path, "src/nested/vulnerable.py", "assert value\n")
    proc = run_bandit("bandit", ["-q", "-r", "-f", "json", "-t", "B101", str(tmp_path / "src")])
    report = json.loads(proc.stdout)
    assert proc.returncode == 1
    assert Path(report["results"][0]["filename"]).name == target.name


def test_cli_and_config_exclusions_are_additive(tmp_path):
    """Seam: config interaction — integration path for cli and config exclusions are additive across cooperating public APIs."""
    write_source(tmp_path, "src/keep.py", "assert value\n")
    write_source(tmp_path, "src/config_excluded.py", "assert value\n")
    write_source(tmp_path, "src/cli_excluded.py", "assert value\n")
    config = write_source(tmp_path, "bandit.yaml", "exclude_dirs: [config_excluded.py]\ntests: [B101]\n")
    proc = run_bandit("bandit", ["-q", "-r", "-f", "json", "-c", str(config), "-x", "cli_excluded.py", str(tmp_path / "src")])
    report = json.loads(proc.stdout)
    assert {Path(x["filename"]).name for x in report["results"]} == {"keep.py"}


def test_tests_option_selects_only_requested_rules(tmp_path):
    """Seam: config interaction — integration path for tests option selects only requested rules across cooperating public APIs."""
    proc, report, _ = json_scan(tmp_path, "assert value\nexec('x=1')\n", "-t", "B101")
    assert proc.returncode == 1
    assert ids(report) == {"B101"}


def test_skips_option_removes_requested_rule(tmp_path):
    """Seam: config interaction — integration path for skips option removes requested rule across cooperating public APIs."""
    proc, report, _ = json_scan(tmp_path, "assert value\nexec('x=1')\n", "-s", "B101")
    assert proc.returncode == 1
    assert "B101" not in ids(report)
    assert "B102" in ids(report)


def test_overlapping_tests_and_skips_exit_two(tmp_path):
    """Seam: config interaction — integration path for overlapping tests and skips exit two across cooperating public APIs."""
    target = write_source(tmp_path, "sample.py", "assert value\n")
    proc = run_bandit("bandit", ["-q", "-f", "json", "-t", "B101", "-s", "B101", str(target)])
    assert proc.returncode == 2
    assert not proc.stdout.strip().startswith("{")


def test_high_threshold_filters_low_issue_but_preserves_metrics(tmp_path):
    """Seam: config interaction — integration path for high threshold filters low issue but preserves metrics across cooperating public APIs."""
    proc, report, _ = json_scan(tmp_path, "assert value\n", "-t", "B101", "--severity-level", "high")
    assert proc.returncode == 0
    assert report["results"] == []
    assert report["metrics"]["_totals"]["SEVERITY.LOW"] == 1


def test_bare_nosec_suppresses_issue_and_updates_metric(tmp_path):
    """Seam: config interaction — integration path for bare nosec suppresses issue and updates metric across cooperating public APIs."""
    proc, report, _ = json_scan(tmp_path, "assert value  # nosec\n", "-t", "B101")
    assert proc.returncode == 0
    assert report["results"] == []
    assert report["metrics"]["_totals"]["nosec"] == 1


def test_selective_nosec_does_not_suppress_different_rule(tmp_path):
    """Seam: config interaction — integration path for selective nosec does not suppress different rule across cooperating public APIs."""
    proc, report, _ = json_scan(tmp_path, "exec('x=1')  # nosec B101\n", "-t", "B102")
    assert proc.returncode == 1
    assert ids(report) == {"B102"}


def test_ignore_nosec_restores_finding_and_resets_suppression(tmp_path):
    """Seam: config interaction — integration path for ignore nosec restores finding and resets suppression across cooperating public APIs."""
    proc, report, _ = json_scan(tmp_path, "assert value  # nosec\n", "-t", "B101", "--ignore-nosec")
    assert proc.returncode == 1
    assert ids(report) == {"B101"}
    assert report["metrics"]["_totals"]["nosec"] == 0


def test_syntax_error_is_skipped_not_reported_as_issue(tmp_path):
    """Seam: error propagation — integration path for syntax error is skipped not reported as issue across cooperating public APIs."""
    proc, report, target = json_scan(tmp_path, "def broken(:\n", "-t", "B101")
    assert proc.returncode == 0
    assert report["results"] == []
    assert Path(report["errors"][0]["filename"]).name == target.name


def test_missing_config_exits_two(tmp_path):
    """Seam: error propagation — integration path for missing config exits two across cooperating public APIs."""
    target = write_source(tmp_path, "sample.py", "assert value\n")
    proc = run_bandit("bandit", ["-q", "-c", str(tmp_path / "missing.yaml"), str(target)])
    assert proc.returncode == 2


def test_exit_zero_keeps_findings_but_forces_success(tmp_path):
    """Seam: protocol handoff — integration path for exit zero keeps findings but forces success across cooperating public APIs."""
    proc, report, _ = json_scan(tmp_path, "assert value\n", "-t", "B101", "--exit-zero")
    assert proc.returncode == 0
    assert ids(report) == {"B101"}


def test_named_profile_replaces_top_level_tests_then_cli_adds(tmp_path):
    """Seam: config interaction — integration path for named profile replaces top level tests then cli adds across cooperating public APIs."""
    target = write_source(tmp_path, "sample.py", "assert value\nexec('x=1')\n")
    config = write_source(tmp_path, "bandit.yaml", "tests: [B102]\nprofiles:\n  only_assert:\n    include: [B101]\n    exclude: []\n")
    proc = run_bandit("bandit", ["-q", "-f", "json", "-c", str(config), "-p", "only_assert", "-t", "B102", str(target)])
    report = json.loads(proc.stdout)
    assert ids(report) == {"B101", "B102"}


def test_toml_tool_bandit_tests_are_loaded(tmp_path):
    """Seam: config interaction — integration path for toml tool bandit tests are loaded across cooperating public APIs."""
    target = write_source(tmp_path, "sample.py", "assert value\nexec('x=1')\n")
    config = write_source(tmp_path, "pyproject.toml", "[tool.bandit]\ntests = ['B102']\n")
    proc = run_bandit("bandit", ["-q", "-f", "json", "-c", str(config), str(target)])
    assert ids(json.loads(proc.stdout)) == {"B102"}


def test_json_report_has_semantic_issue_and_metric_fields(tmp_path):
    """Seam: protocol handoff — integration path for json report has semantic issue and metric fields across cooperating public APIs."""
    proc, report, target = json_scan(tmp_path, "assert value\n", "-t", "B101")
    issue = report["results"][0]
    assert proc.returncode == 1
    assert {"filename", "test_name", "test_id", "issue_severity", "issue_confidence", "issue_cwe", "line_number", "line_range", "col_offset", "end_col_offset", "more_info"} <= set(issue)
    assert Path(issue["filename"]).name == target.name
    assert "_totals" in report["metrics"]


def test_yaml_and_json_reports_have_equal_issue_identity_and_metrics(tmp_path):
    """Seam: config interaction — integration path for yaml and json reports have equal issue identity and metrics across cooperating public APIs."""
    target = write_source(tmp_path, "sample.py", "assert value\n")
    j = run_bandit("bandit", ["-q", "-f", "json", "-t", "B101", str(target)])
    y = run_bandit("bandit", ["-q", "-f", "yaml", "-t", "B101", str(target)])
    jr, yr = json.loads(j.stdout), yaml.safe_load(y.stdout)
    keys = ["test_id", "issue_severity", "issue_confidence", "issue_cwe", "line_number", "line_range"]
    assert {k: jr["results"][0][k] for k in keys} == {k: yr["results"][0][k] for k in keys}
    assert jr["metrics"]["_totals"] == yr["metrics"]["_totals"]


def test_csv_report_projects_semantic_issue_columns(tmp_path):
    """Seam: protocol handoff — integration path for csv report projects semantic issue columns across cooperating public APIs."""
    target = write_source(tmp_path, "sample.py", "assert value\n")
    proc = run_bandit("bandit", ["-q", "-f", "csv", "-t", "B101", str(target)])
    rows = list(csv.DictReader(io.StringIO(proc.stdout)))
    assert proc.returncode == 1
    assert rows[0]["test_id"] == "B101"
    assert rows[0]["issue_severity"] == "LOW"
    assert rows[0]["issue_confidence"] == "HIGH"
    assert rows[0]["issue_cwe"].endswith("/703.html")


def test_xml_report_count_and_issue_identity(tmp_path):
    """Seam: error propagation — integration path for xml report count and issue identity across cooperating public APIs."""
    target = write_source(tmp_path, "sample.py", "assert value\n")
    proc = run_bandit("bandit", ["-q", "-f", "xml", "-t", "B101", str(target)])
    root = ET.fromstring(proc.stdout)
    error = root.find("./testcase/error")
    assert proc.returncode == 1
    assert root.attrib["name"] == "bandit"
    assert int(root.attrib["tests"]) == 1
    assert "B101" in "".join(error.itertext())


def test_sarif_report_projects_rule_result_and_metrics(tmp_path):
    """Seam: protocol handoff — integration path for sarif report projects rule result and metrics across cooperating public APIs."""
    target = write_source(tmp_path, "sample.py", "assert value\n")
    proc = run_bandit("bandit", ["-q", "-f", "sarif", "-t", "B101", str(target)])
    report = json.loads(proc.stdout)
    run = report["runs"][0]
    assert proc.returncode == 1
    assert run["results"][0]["ruleId"] == "B101"
    assert run["results"][0]["level"] == "note"
    assert run["properties"]["metrics"]["_totals"]["SEVERITY.LOW"] == 1


def test_sarif_projects_skipped_file_as_error_notification(tmp_path):
    """Seam: error propagation — integration path for sarif projects skipped file as error notification across cooperating public APIs."""
    target = write_source(tmp_path, "broken.py", "def broken(:\n")
    proc = run_bandit("bandit", ["-q", "-f", "sarif", str(target)])
    run = json.loads(proc.stdout)["runs"][0]
    notification = run["invocations"][0]["toolConfigurationNotifications"][0]
    uri = notification["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
    assert proc.returncode == 0
    assert run["results"] == []
    assert notification["level"] == "error"
    assert Path(uri).name == target.name


def test_html_report_contains_escaped_semantic_issue(tmp_path):
    """Seam: protocol handoff — integration path for html report contains escaped semantic issue across cooperating public APIs."""
    target = write_source(tmp_path, "sample.py", "assert '<unsafe>'\n")
    proc = run_bandit("bandit", ["-q", "-f", "html", "-t", "B101", str(target)])
    assert proc.returncode == 1
    assert "B101" in proc.stdout
    assert "LOW" in proc.stdout and "HIGH" in proc.stdout
    assert "&lt;unsafe&gt;" in proc.stdout


def test_text_report_exposes_issue_and_rating_semantics(tmp_path):
    """Seam: protocol handoff — integration path for text report exposes issue and rating semantics across cooperating public APIs."""
    target = write_source(tmp_path, "sample.py", "assert value\n")
    proc = run_bandit("bandit", ["-q", "-f", "txt", "-t", "B101", str(target)])
    assert proc.returncode == 1
    lines = [line.casefold() for line in proc.stdout.splitlines()]
    assert any("b101" in line for line in lines)
    assert any("severity" in line and "low" in line for line in lines)
    assert any("confidence" in line and "high" in line for line in lines)


def test_custom_report_expands_documented_fields(tmp_path):
    """Seam: protocol handoff — integration path for custom report expands documented fields across cooperating public APIs."""
    target = write_source(tmp_path, "sample.py", "assert value\n")
    template = "{test_id}|{severity}|{confidence}|{line}|{col}"
    proc = run_bandit("bandit", ["-q", "-f", "custom", "--msg-template", template, "-t", "B101", str(target)])
    assert proc.returncode == 1
    assert proc.stdout.strip() == "B101|LOW|HIGH|1|0"


def test_cross_format_issue_count_agrees(tmp_path):
    """Seam: config interaction — integration path for cross format issue count agrees across cooperating public APIs."""
    target = write_source(tmp_path, "sample.py", "assert value\nexec('x=1')\n")
    reports = {}
    for fmt in ("json", "yaml", "csv", "xml", "sarif"):
        reports[fmt] = run_bandit("bandit", ["-q", "-f", fmt, "-t", "B101,B102", str(target)]).stdout
    counts = {
        len(json.loads(reports["json"])["results"]),
        len(yaml.safe_load(reports["yaml"])["results"]),
        len(list(csv.DictReader(io.StringIO(reports["csv"])))),
        int(ET.fromstring(reports["xml"]).attrib["tests"]),
        len(json.loads(reports["sarif"])["runs"][0]["results"]),
    }
    assert counts == {2}


def test_cross_format_threshold_removes_same_identity(tmp_path):
    """Seam: config interaction — integration path for cross format threshold removes same identity across cooperating public APIs."""
    target = write_source(tmp_path, "sample.py", "assert value\nexec('x=1')\n")
    identities = []
    for fmt in ("json", "yaml"):
        proc = run_bandit("bandit", ["-q", "-f", fmt, "-t", "B101,B102", "--severity-level", "medium", str(target)])
        doc = json.loads(proc.stdout) if fmt == "json" else yaml.safe_load(proc.stdout)
        identities.append({x["test_id"] for x in doc["results"]})
    assert identities == [{"B102"}, {"B102"}]


def test_per_file_metrics_sum_to_totals(tmp_path):
    """Seam: state consistency — integration path for per file metrics sum to totals across cooperating public APIs."""
    first = write_source(tmp_path, "first.py", "assert value\n")
    second = write_source(tmp_path, "second.py", "exec('x=1')\n")
    proc = run_bandit("bandit", ["-q", "-f", "json", "-t", "B101,B102", str(first), str(second)])
    metrics = json.loads(proc.stdout)["metrics"]
    per_file = [v for k, v in metrics.items() if k != "_totals"]
    for key in ("loc", "SEVERITY.LOW", "SEVERITY.MEDIUM", "CONFIDENCE.HIGH"):
        assert sum(item[key] for item in per_file) == metrics["_totals"][key]


def test_baseline_suppresses_moved_issue_but_keeps_new_issue(tmp_path):
    """Seam: lifecycle crossing — integration path for baseline suppresses moved issue but keeps new issue across cooperating public APIs."""
    target = write_source(tmp_path, "sample.py", "assert value\n")
    baseline = tmp_path / "baseline.json"
    first = run_bandit("bandit", ["-q", "-f", "json", "-o", str(baseline), "-t", "B101,B102", str(target)])
    assert first.returncode == 1
    target.write_text("\n\nassert value\nexec('x=1')\n", encoding="utf-8")
    current = run_bandit("bandit", ["-q", "-f", "json", "-b", str(baseline), "-t", "B101,B102", str(target)])
    report = json.loads(current.stdout)
    assert current.returncode == 1
    assert ids(report) == {"B102"}
    assert report["metrics"]["_totals"]["SEVERITY.LOW"] == 1


def test_baseline_with_yaml_formatter_exits_two(tmp_path):
    """Seam: config interaction — integration path for baseline with yaml formatter exits two across cooperating public APIs."""
    target = write_source(tmp_path, "sample.py", "assert value\n")
    baseline = tmp_path / "baseline.json"
    run_bandit("bandit", ["-q", "-f", "json", "-o", str(baseline), "-t", "B101", str(target)])
    proc = run_bandit("bandit", ["-q", "-f", "yaml", "-b", str(baseline), str(target)])
    assert proc.returncode == 2


def test_malformed_readable_baseline_behaves_as_empty(tmp_path):
    """Seam: error propagation — integration path for malformed readable baseline behaves as empty across cooperating public APIs."""
    target = write_source(tmp_path, "sample.py", "assert value\n")
    baseline = write_source(tmp_path, "baseline.json", "not-json")
    proc = run_bandit("bandit", ["-q", "-f", "json", "-b", str(baseline), "-t", "B101", str(target)])
    assert proc.returncode == 1
    assert ids(json.loads(proc.stdout)) == {"B101"}


def test_config_generator_creates_parseable_profile(tmp_path):
    """Seam: config interaction — integration path for config generator creates parseable profile across cooperating public APIs."""
    output = tmp_path / "bandit.yaml"
    proc = run_bandit("bandit-config-generator", ["-o", str(output), "-t", "B101", "-s", "B102"])
    data = yaml.safe_load(output.read_text(encoding="utf-8"))
    assert proc.returncode == 0
    assert data["tests"] == ["B101"]
    assert data["skips"] == ["B102"]


def test_config_generator_refuses_existing_output(tmp_path):
    """Seam: config interaction — integration path for config generator refuses existing output across cooperating public APIs."""
    output = write_source(tmp_path, "bandit.yaml", "sentinel: true\n")
    proc = run_bandit("bandit-config-generator", ["-o", str(output)])
    assert proc.returncode == 2
    assert yaml.safe_load(output.read_text(encoding="utf-8")) == {"sentinel": True}


def test_bandit_baseline_restores_current_commit(tmp_path):
    """Seam: error propagation — integration path for bandit baseline restores current commit across cooperating public APIs."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    source = write_source(repo, "sample.py", "value = 1\n")
    subprocess.run(["git", "add", "sample.py"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=repo, check=True)
    source.write_text("value = 1\nassert value\n", encoding="utf-8")
    subprocess.run(["git", "add", "sample.py"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "finding"], cwd=repo, check=True)
    before = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    proc = run_bandit("bandit-baseline", ["-f", "json", ".", "-r", "-t", "B101"], cwd=repo)
    after = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    assert proc.returncode == 1, (proc.stdout, proc.stderr)
    assert (repo / "bandit_baseline_result.json").exists(), (proc.stdout, proc.stderr, [p.name for p in repo.iterdir()])
    report = json.loads((repo / "bandit_baseline_result.json").read_text(encoding="utf-8"))
    assert before == after
    assert ids(report) == {"B101"}


def test_bandit_baseline_rejects_non_repository(tmp_path):
    """Seam: error propagation — integration path for bandit baseline rejects non repository across cooperating public APIs."""
    proc = run_bandit("bandit-baseline", [str(tmp_path)], cwd=tmp_path)
    assert proc.returncode == 2


def test_bandit_baseline_rejects_dirty_repository(tmp_path):
    """Seam: error propagation — integration path for bandit baseline rejects dirty repository across cooperating public APIs."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    source = write_source(repo, "sample.py", "value = 1\n")
    subprocess.run(["git", "add", "sample.py"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=repo, check=True)
    source.write_text("value = 2\n", encoding="utf-8")
    proc = run_bandit("bandit-baseline", ["."], cwd=repo)
    assert proc.returncode == 2
