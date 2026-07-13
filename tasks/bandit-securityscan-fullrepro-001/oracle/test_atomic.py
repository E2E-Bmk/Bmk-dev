# Spec2Repo oracle - atomic tests for bandit-securityscan-fullrepro-001
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


def test_no_target_exits_two():
    proc = _run("bandit", ["-q"])
    assert proc.returncode == 2


def test_config_generator_no_action_returns_one():
    proc = _run("bandit-config-generator", [])
    assert proc.returncode == 1
