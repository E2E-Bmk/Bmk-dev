import csv
import io
import json
import os
from pathlib import Path
import shlex
import subprocess
import xml.etree.ElementTree as ET

import pytest
import yaml


def _tool(name):
    override = os.environ.get(name.upper().replace("-", "_") + "_BIN")
    return override or name


def _run(name, args, *, cwd=None, stdin=None):
    env = os.environ.copy()
    bandit_command = shlex.split(_tool("bandit"))[0]
    if os.path.isabs(bandit_command):
        env["PATH"] = str(Path(bandit_command).parent) + os.pathsep + env.get("PATH", "")
    return subprocess.run(
        [*shlex.split(_tool(name)), *args],
        cwd=cwd,
        env=env,
        input=stdin,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _write(tmp_path, name, text):
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _json_scan(tmp_path, source, *args, name="sample.py"):
    target = _write(tmp_path, name, source)
    proc = _run("bandit", ["-q", "-f", "json", *args, str(target)])
    return proc, json.loads(proc.stdout), target


def _one_issue(tmp_path, source, expected_id, *, severity=None, confidence=None, cwe=None):
    proc, report, _ = _json_scan(tmp_path, source, "-t", expected_id)
    assert proc.returncode == 1
    assert len(report["results"]) == 1
    issue = report["results"][0]
    assert issue["test_id"] == expected_id
    if severity:
        assert issue["issue_severity"] == severity
    if confidence:
        assert issue["issue_confidence"] == confidence
    if cwe:
        assert issue["issue_cwe"]["id"] == cwe
    return issue


def _ids(report):
    return {item["test_id"] for item in report["results"]}


def test_package_rating_constants_are_public():
    import bandit

    assert (bandit.UNDEFINED, bandit.LOW, bandit.MEDIUM, bandit.HIGH) == (
        "UNDEFINED",
        "LOW",
        "MEDIUM",
        "HIGH",
    )


def test_issue_preserves_supplied_plugin_result_fields(tmp_path):
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

    projected = _one_issue(
        tmp_path,
        "from markupsafe import Markup\nMarkup(user_text)\n",
        "B704",
        severity="MEDIUM",
        confidence="HIGH",
        cwe=79,
    )
    assert projected["issue_cwe"]["id"] == 79


def test_issue_decodes_byte_text_as_utf8():
    import bandit

    issue = bandit.Issue(bandit.LOW, text="caf\u00e9".encode("utf-8"))
    assert issue.text == "caf\u00e9"


def test_public_decorators_accept_documented_forms():
    import bandit

    @bandit.test_id("B900")
    @bandit.checks("Call")
    @bandit.takes_config("shared")
    def plugin(context, config):
        return None

    @bandit.takes_config
    def direct(context, config):
        return None

    assert callable(plugin)
    assert callable(direct)


def test_rule_b101_assert_used(tmp_path):
    _one_issue(tmp_path, "assert value\n", "B101", severity="LOW", confidence="HIGH", cwe=703)


def test_rule_b102_exec_used(tmp_path):
    _one_issue(tmp_path, "exec('x = 1')\n", "B102", severity="MEDIUM", confidence="HIGH", cwe=78)


def test_rule_b104_bind_all_interfaces(tmp_path):
    _one_issue(tmp_path, "host = '0.0.0.0'\n", "B104", severity="MEDIUM", confidence="MEDIUM", cwe=605)


def test_rule_b105_hardcoded_password(tmp_path):
    _one_issue(tmp_path, "password = 'secret-value'\n", "B105", severity="LOW", confidence="MEDIUM", cwe=259)


def test_rule_b108_hardcoded_tmp_path(tmp_path):
    _one_issue(tmp_path, "path = '/tmp/session-token'\n", "B108", severity="MEDIUM", confidence="MEDIUM", cwe=377)


def test_rule_b110_try_except_pass(tmp_path):
    config = _write(
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
    pass_proc, pass_report, _ = _json_scan(
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
    continue_proc, continue_report, _ = _json_scan(
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


def test_rule_b113_request_without_timeout(tmp_path):
    _one_issue(tmp_path, "import requests\nrequests.get('https://example.invalid')\n", "B113", severity="MEDIUM", confidence="LOW", cwe=400)


def test_rule_b301_pickle_deserialization(tmp_path):
    _one_issue(tmp_path, "import pickle\npickle.loads(data)\n", "B301", severity="MEDIUM", confidence="HIGH", cwe=502)


def test_rule_b303_weak_crypto_constructor(tmp_path):
    _one_issue(tmp_path, "from Crypto.Hash import MD5\nMD5.new()\n", "B303", severity="MEDIUM", confidence="HIGH", cwe=327)


def test_rule_b307_eval(tmp_path):
    _one_issue(tmp_path, "value = eval(user_text)\n", "B307", severity="MEDIUM", confidence="HIGH", cwe=78)


def test_rule_b311_random_generator(tmp_path):
    _one_issue(tmp_path, "import random\nvalue = random.random()\n", "B311", severity="LOW", confidence="HIGH", cwe=330)


def test_rule_b401_telnet_import(tmp_path):
    _one_issue(tmp_path, "import telnetlib\n", "B401", severity="HIGH", confidence="HIGH", cwe=319)


def test_rule_b403_pickle_import(tmp_path):
    _one_issue(tmp_path, "import pickle\n", "B403", severity="LOW", confidence="HIGH", cwe=502)


def test_rule_b404_subprocess_import(tmp_path):
    _one_issue(tmp_path, "import subprocess\n", "B404", severity="LOW", confidence="HIGH", cwe=78)


def test_rule_b501_disabled_certificate_validation(tmp_path):
    _one_issue(tmp_path, "import requests\nrequests.get(url, verify=False)\n", "B501", severity="HIGH", confidence="HIGH", cwe=295)


def test_rule_b506_unsafe_yaml_load(tmp_path):
    _one_issue(tmp_path, "import yaml\nyaml.load(payload)\n", "B506", severity="MEDIUM", confidence="HIGH", cwe=20)


def test_rule_b602_subprocess_shell_true(tmp_path):
    _one_issue(tmp_path, "import subprocess\ncommand = input()\nsubprocess.Popen(command, shell=True)\n", "B602", severity="HIGH", confidence="HIGH", cwe=78)


def test_rule_b608_string_built_sql(tmp_path):
    _one_issue(tmp_path, "query = 'SELECT * FROM users WHERE id = %s' % user_id\n", "B608", severity="MEDIUM", cwe=89)


def test_rule_b701_jinja_autoescape_false(tmp_path):
    _one_issue(tmp_path, "from jinja2 import Environment\nEnvironment(autoescape=False)\n", "B701", severity="HIGH", confidence="HIGH", cwe=94)


def test_rule_b704_dynamic_markup(tmp_path):
    _one_issue(tmp_path, "from markupsafe import Markup\nvalue = Markup(user_input)\n", "B704", severity="MEDIUM", confidence="HIGH", cwe=79)


def test_stdin_scan_reports_stdin_filename_and_status(tmp_path):
    proc = _run("bandit", ["-q", "-f", "json", "-t", "B101", "-"], stdin="assert value\n")
    report = json.loads(proc.stdout)
    assert proc.returncode == 1
    assert report["results"][0]["filename"] == "<stdin>"
    assert report["results"][0]["test_id"] == "B101"


def test_recursive_scan_discovers_nested_python(tmp_path):
    target = _write(tmp_path, "src/nested/vulnerable.py", "assert value\n")
    proc = _run("bandit", ["-q", "-r", "-f", "json", "-t", "B101", str(tmp_path / "src")])
    report = json.loads(proc.stdout)
    assert proc.returncode == 1
    assert Path(report["results"][0]["filename"]).name == target.name


def test_cli_and_config_exclusions_are_additive(tmp_path):
    _write(tmp_path, "src/keep.py", "assert value\n")
    _write(tmp_path, "src/config_excluded.py", "assert value\n")
    _write(tmp_path, "src/cli_excluded.py", "assert value\n")
    config = _write(tmp_path, "bandit.yaml", "exclude_dirs: [config_excluded.py]\ntests: [B101]\n")
    proc = _run("bandit", ["-q", "-r", "-f", "json", "-c", str(config), "-x", "cli_excluded.py", str(tmp_path / "src")])
    report = json.loads(proc.stdout)
    assert {Path(x["filename"]).name for x in report["results"]} == {"keep.py"}


def test_tests_option_selects_only_requested_rules(tmp_path):
    proc, report, _ = _json_scan(tmp_path, "assert value\nexec('x=1')\n", "-t", "B101")
    assert proc.returncode == 1
    assert _ids(report) == {"B101"}


def test_skips_option_removes_requested_rule(tmp_path):
    proc, report, _ = _json_scan(tmp_path, "assert value\nexec('x=1')\n", "-s", "B101")
    assert proc.returncode == 1
    assert "B101" not in _ids(report)
    assert "B102" in _ids(report)


def test_overlapping_tests_and_skips_exit_two(tmp_path):
    target = _write(tmp_path, "sample.py", "assert value\n")
    proc = _run("bandit", ["-q", "-f", "json", "-t", "B101", "-s", "B101", str(target)])
    assert proc.returncode == 2
    assert not proc.stdout.strip().startswith("{")


def test_high_threshold_filters_low_issue_but_preserves_metrics(tmp_path):
    proc, report, _ = _json_scan(tmp_path, "assert value\n", "-t", "B101", "--severity-level", "high")
    assert proc.returncode == 0
    assert report["results"] == []
    assert report["metrics"]["_totals"]["SEVERITY.LOW"] == 1


def test_bare_nosec_suppresses_issue_and_updates_metric(tmp_path):
    proc, report, _ = _json_scan(tmp_path, "assert value  # nosec\n", "-t", "B101")
    assert proc.returncode == 0
    assert report["results"] == []
    assert report["metrics"]["_totals"]["nosec"] == 1


def test_selective_nosec_does_not_suppress_different_rule(tmp_path):
    proc, report, _ = _json_scan(tmp_path, "exec('x=1')  # nosec B101\n", "-t", "B102")
    assert proc.returncode == 1
    assert _ids(report) == {"B102"}


def test_ignore_nosec_restores_finding_and_resets_suppression(tmp_path):
    proc, report, _ = _json_scan(tmp_path, "assert value  # nosec\n", "-t", "B101", "--ignore-nosec")
    assert proc.returncode == 1
    assert _ids(report) == {"B101"}
    assert report["metrics"]["_totals"]["nosec"] == 0


def test_syntax_error_is_skipped_not_reported_as_issue(tmp_path):
    proc, report, target = _json_scan(tmp_path, "def broken(:\n", "-t", "B101")
    assert proc.returncode == 0
    assert report["results"] == []
    assert Path(report["errors"][0]["filename"]).name == target.name


def test_missing_config_exits_two(tmp_path):
    target = _write(tmp_path, "sample.py", "assert value\n")
    proc = _run("bandit", ["-q", "-c", str(tmp_path / "missing.yaml"), str(target)])
    assert proc.returncode == 2


def test_no_target_exits_two():
    proc = _run("bandit", ["-q"])
    assert proc.returncode == 2


def test_exit_zero_keeps_findings_but_forces_success(tmp_path):
    proc, report, _ = _json_scan(tmp_path, "assert value\n", "-t", "B101", "--exit-zero")
    assert proc.returncode == 0
    assert _ids(report) == {"B101"}


def test_named_profile_replaces_top_level_tests_then_cli_adds(tmp_path):
    target = _write(tmp_path, "sample.py", "assert value\nexec('x=1')\n")
    config = _write(tmp_path, "bandit.yaml", "tests: [B102]\nprofiles:\n  only_assert:\n    include: [B101]\n    exclude: []\n")
    proc = _run("bandit", ["-q", "-f", "json", "-c", str(config), "-p", "only_assert", "-t", "B102", str(target)])
    report = json.loads(proc.stdout)
    assert _ids(report) == {"B101", "B102"}


def test_toml_tool_bandit_tests_are_loaded(tmp_path):
    target = _write(tmp_path, "sample.py", "assert value\nexec('x=1')\n")
    config = _write(tmp_path, "pyproject.toml", "[tool.bandit]\ntests = ['B102']\n")
    proc = _run("bandit", ["-q", "-f", "json", "-c", str(config), str(target)])
    assert _ids(json.loads(proc.stdout)) == {"B102"}


def test_json_report_has_semantic_issue_and_metric_fields(tmp_path):
    proc, report, target = _json_scan(tmp_path, "assert value\n", "-t", "B101")
    issue = report["results"][0]
    assert proc.returncode == 1
    assert {"filename", "test_name", "test_id", "issue_severity", "issue_confidence", "issue_cwe", "line_number", "line_range", "col_offset", "end_col_offset", "more_info"} <= set(issue)
    assert Path(issue["filename"]).name == target.name
    assert "_totals" in report["metrics"]


def test_yaml_and_json_reports_have_equal_issue_identity_and_metrics(tmp_path):
    target = _write(tmp_path, "sample.py", "assert value\n")
    j = _run("bandit", ["-q", "-f", "json", "-t", "B101", str(target)])
    y = _run("bandit", ["-q", "-f", "yaml", "-t", "B101", str(target)])
    jr, yr = json.loads(j.stdout), yaml.safe_load(y.stdout)
    keys = ["test_id", "issue_severity", "issue_confidence", "issue_cwe", "line_number", "line_range"]
    assert {k: jr["results"][0][k] for k in keys} == {k: yr["results"][0][k] for k in keys}
    assert jr["metrics"]["_totals"] == yr["metrics"]["_totals"]


def test_csv_report_projects_semantic_issue_columns(tmp_path):
    target = _write(tmp_path, "sample.py", "assert value\n")
    proc = _run("bandit", ["-q", "-f", "csv", "-t", "B101", str(target)])
    rows = list(csv.DictReader(io.StringIO(proc.stdout)))
    assert proc.returncode == 1
    assert rows[0]["test_id"] == "B101"
    assert rows[0]["issue_severity"] == "LOW"
    assert rows[0]["issue_confidence"] == "HIGH"
    assert rows[0]["issue_cwe"].endswith("/703.html")


def test_xml_report_count_and_issue_identity(tmp_path):
    target = _write(tmp_path, "sample.py", "assert value\n")
    proc = _run("bandit", ["-q", "-f", "xml", "-t", "B101", str(target)])
    root = ET.fromstring(proc.stdout)
    error = root.find("./testcase/error")
    assert proc.returncode == 1
    assert root.attrib["name"] == "bandit"
    assert int(root.attrib["tests"]) == 1
    assert "B101" in "".join(error.itertext())


def test_sarif_report_projects_rule_result_and_metrics(tmp_path):
    target = _write(tmp_path, "sample.py", "assert value\n")
    proc = _run("bandit", ["-q", "-f", "sarif", "-t", "B101", str(target)])
    report = json.loads(proc.stdout)
    run = report["runs"][0]
    assert proc.returncode == 1
    assert run["results"][0]["ruleId"] == "B101"
    assert run["results"][0]["level"] == "note"
    assert run["properties"]["metrics"]["_totals"]["SEVERITY.LOW"] == 1


def test_sarif_projects_skipped_file_as_error_notification(tmp_path):
    target = _write(tmp_path, "broken.py", "def broken(:\n")
    proc = _run("bandit", ["-q", "-f", "sarif", str(target)])
    run = json.loads(proc.stdout)["runs"][0]
    notification = run["invocations"][0]["toolConfigurationNotifications"][0]
    uri = notification["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
    assert proc.returncode == 0
    assert run["results"] == []
    assert notification["level"] == "error"
    assert Path(uri).name == target.name


def test_html_report_contains_escaped_semantic_issue(tmp_path):
    target = _write(tmp_path, "sample.py", "assert '<unsafe>'\n")
    proc = _run("bandit", ["-q", "-f", "html", "-t", "B101", str(target)])
    assert proc.returncode == 1
    assert "B101" in proc.stdout
    assert "LOW" in proc.stdout and "HIGH" in proc.stdout
    assert "&lt;unsafe&gt;" in proc.stdout


def test_text_report_exposes_issue_and_rating_semantics(tmp_path):
    target = _write(tmp_path, "sample.py", "assert value\n")
    proc = _run("bandit", ["-q", "-f", "txt", "-t", "B101", str(target)])
    assert proc.returncode == 1
    lines = [line.casefold() for line in proc.stdout.splitlines()]
    assert any("b101" in line for line in lines)
    assert any("severity" in line and "low" in line for line in lines)
    assert any("confidence" in line and "high" in line for line in lines)


def test_custom_report_expands_documented_fields(tmp_path):
    target = _write(tmp_path, "sample.py", "assert value\n")
    template = "{test_id}|{severity}|{confidence}|{line}|{col}"
    proc = _run("bandit", ["-q", "-f", "custom", "--msg-template", template, "-t", "B101", str(target)])
    assert proc.returncode == 1
    assert proc.stdout.strip() == "B101|LOW|HIGH|1|0"


def test_cross_format_issue_count_agrees(tmp_path):
    target = _write(tmp_path, "sample.py", "assert value\nexec('x=1')\n")
    reports = {}
    for fmt in ("json", "yaml", "csv", "xml", "sarif"):
        reports[fmt] = _run("bandit", ["-q", "-f", fmt, "-t", "B101,B102", str(target)]).stdout
    counts = {
        len(json.loads(reports["json"])["results"]),
        len(yaml.safe_load(reports["yaml"])["results"]),
        len(list(csv.DictReader(io.StringIO(reports["csv"])))),
        int(ET.fromstring(reports["xml"]).attrib["tests"]),
        len(json.loads(reports["sarif"])["runs"][0]["results"]),
    }
    assert counts == {2}


def test_cross_format_threshold_removes_same_identity(tmp_path):
    target = _write(tmp_path, "sample.py", "assert value\nexec('x=1')\n")
    identities = []
    for fmt in ("json", "yaml"):
        proc = _run("bandit", ["-q", "-f", fmt, "-t", "B101,B102", "--severity-level", "medium", str(target)])
        doc = json.loads(proc.stdout) if fmt == "json" else yaml.safe_load(proc.stdout)
        identities.append({x["test_id"] for x in doc["results"]})
    assert identities == [{"B102"}, {"B102"}]


def test_per_file_metrics_sum_to_totals(tmp_path):
    first = _write(tmp_path, "first.py", "assert value\n")
    second = _write(tmp_path, "second.py", "exec('x=1')\n")
    proc = _run("bandit", ["-q", "-f", "json", "-t", "B101,B102", str(first), str(second)])
    metrics = json.loads(proc.stdout)["metrics"]
    per_file = [v for k, v in metrics.items() if k != "_totals"]
    for key in ("loc", "SEVERITY.LOW", "SEVERITY.MEDIUM", "CONFIDENCE.HIGH"):
        assert sum(item[key] for item in per_file) == metrics["_totals"][key]


def test_baseline_suppresses_moved_issue_but_keeps_new_issue(tmp_path):
    target = _write(tmp_path, "sample.py", "assert value\n")
    baseline = tmp_path / "baseline.json"
    first = _run("bandit", ["-q", "-f", "json", "-o", str(baseline), "-t", "B101,B102", str(target)])
    assert first.returncode == 1
    target.write_text("\n\nassert value\nexec('x=1')\n", encoding="utf-8")
    current = _run("bandit", ["-q", "-f", "json", "-b", str(baseline), "-t", "B101,B102", str(target)])
    report = json.loads(current.stdout)
    assert current.returncode == 1
    assert _ids(report) == {"B102"}
    assert report["metrics"]["_totals"]["SEVERITY.LOW"] == 1


def test_baseline_with_yaml_formatter_exits_two(tmp_path):
    target = _write(tmp_path, "sample.py", "assert value\n")
    baseline = tmp_path / "baseline.json"
    _run("bandit", ["-q", "-f", "json", "-o", str(baseline), "-t", "B101", str(target)])
    proc = _run("bandit", ["-q", "-f", "yaml", "-b", str(baseline), str(target)])
    assert proc.returncode == 2


def test_malformed_readable_baseline_behaves_as_empty(tmp_path):
    target = _write(tmp_path, "sample.py", "assert value\n")
    baseline = _write(tmp_path, "baseline.json", "not-json")
    proc = _run("bandit", ["-q", "-f", "json", "-b", str(baseline), "-t", "B101", str(target)])
    assert proc.returncode == 1
    assert _ids(json.loads(proc.stdout)) == {"B101"}


def test_config_generator_no_action_returns_one():
    proc = _run("bandit-config-generator", [])
    assert proc.returncode == 1


def test_config_generator_creates_parseable_profile(tmp_path):
    output = tmp_path / "bandit.yaml"
    proc = _run("bandit-config-generator", ["-o", str(output), "-t", "B101", "-s", "B102"])
    data = yaml.safe_load(output.read_text(encoding="utf-8"))
    assert proc.returncode == 0
    assert data["tests"] == ["B101"]
    assert data["skips"] == ["B102"]


def test_config_generator_refuses_existing_output(tmp_path):
    output = _write(tmp_path, "bandit.yaml", "sentinel: true\n")
    proc = _run("bandit-config-generator", ["-o", str(output)])
    assert proc.returncode == 2
    assert yaml.safe_load(output.read_text(encoding="utf-8")) == {"sentinel": True}


def test_bandit_baseline_restores_current_commit(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    source = _write(repo, "sample.py", "value = 1\n")
    subprocess.run(["git", "add", "sample.py"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=repo, check=True)
    source.write_text("value = 1\nassert value\n", encoding="utf-8")
    subprocess.run(["git", "add", "sample.py"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "finding"], cwd=repo, check=True)
    before = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    proc = _run("bandit-baseline", ["-f", "json", ".", "-r", "-t", "B101"], cwd=repo)
    after = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    assert proc.returncode == 1, (proc.stdout, proc.stderr)
    assert (repo / "bandit_baseline_result.json").exists(), (proc.stdout, proc.stderr, [p.name for p in repo.iterdir()])
    report = json.loads((repo / "bandit_baseline_result.json").read_text(encoding="utf-8"))
    assert before == after
    assert _ids(report) == {"B101"}


def test_bandit_baseline_rejects_non_repository(tmp_path):
    proc = _run("bandit-baseline", [str(tmp_path)], cwd=tmp_path)
    assert proc.returncode == 2


def test_bandit_baseline_rejects_dirty_repository(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    source = _write(repo, "sample.py", "value = 1\n")
    subprocess.run(["git", "add", "sample.py"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=repo, check=True)
    source.write_text("value = 2\n", encoding="utf-8")
    proc = _run("bandit-baseline", ["."], cwd=repo)
    assert proc.returncode == 2
