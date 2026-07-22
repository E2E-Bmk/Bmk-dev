# Spec2Repo oracle - atomic tests for bandit-securityscan-fullrepro-001
import json
from pathlib import Path

import pytest

from conftest import run_bandit, write_source, json_scan, one_issue, ids


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
    issue = one_issue(tmp_path, "assert value\n", "B101", severity="LOW", confidence="HIGH", cwe=703)
    assert issue["line_number"] == 1
    assert issue["test_name"] == "assert_used"
    assert "assert" in issue["issue_text"].lower()


def test_rule_b102_exec_used(tmp_path):
    issue = one_issue(tmp_path, "exec('x = 1')\n", "B102", severity="MEDIUM", confidence="HIGH", cwe=78)
    assert issue["line_number"] == 1
    assert issue["test_name"] == "exec_used"
    assert "exec" in issue["issue_text"].lower()


def test_rule_b104_bind_all_interfaces(tmp_path):
    issue = one_issue(tmp_path, "host = '0.0.0.0'\n", "B104", severity="MEDIUM", confidence="MEDIUM", cwe=605)
    assert issue["line_number"] == 1
    assert issue["test_name"] == "hardcoded_bind_all_interfaces"
    assert "binding" in issue["issue_text"].lower()


def test_rule_b105_hardcoded_password(tmp_path):
    issue = one_issue(tmp_path, "password = 'secret-value'\n", "B105", severity="LOW", confidence="MEDIUM", cwe=259)
    assert issue["line_number"] == 1
    assert issue["test_name"] == "hardcoded_password_string"
    assert "hardcoded password" in issue["issue_text"].lower()


def test_rule_b108_hardcoded_tmp_path(tmp_path):
    issue = one_issue(tmp_path, "path = '/tmp/session-token'\n", "B108", severity="MEDIUM", confidence="MEDIUM", cwe=377)
    assert issue["line_number"] == 1
    assert issue["test_name"] == "hardcoded_tmp_directory"
    assert "temp" in issue["issue_text"].lower()


def test_rule_b113_request_without_timeout(tmp_path):
    issue = one_issue(
        tmp_path,
        "import requests\nrequests.get('https://example.invalid')\n",
        "B113",
        severity="MEDIUM",
        confidence="LOW",
        cwe=400,
    )
    assert issue["line_number"] == 2
    assert issue["test_name"] == "request_without_timeout"
    assert "timeout" in issue["issue_text"].lower()


def test_rule_b301_pickle_deserialization(tmp_path):
    issue = one_issue(tmp_path, "import pickle\npickle.loads(data)\n", "B301", severity="MEDIUM", confidence="HIGH", cwe=502)
    assert issue["line_number"] == 2
    assert issue["test_name"] == "blacklist"
    assert "pickle" in issue["issue_text"].lower()


def test_rule_b303_weak_crypto_constructor(tmp_path):
    issue = one_issue(tmp_path, "from Crypto.Hash import MD5\nMD5.new()\n", "B303", severity="MEDIUM", confidence="HIGH", cwe=327)
    assert issue["line_number"] == 2
    assert issue["test_name"] == "blacklist"
    assert "md5" in issue["issue_text"].lower()


def test_rule_b307_eval(tmp_path):
    issue = one_issue(tmp_path, "value = eval(user_text)\n", "B307", severity="MEDIUM", confidence="HIGH", cwe=78)
    assert issue["line_number"] == 1
    assert issue["test_name"] == "blacklist"
    assert "eval" in issue["issue_text"].lower()


def test_rule_b311_random_generator(tmp_path):
    issue = one_issue(tmp_path, "import random\nvalue = random.random()\n", "B311", severity="LOW", confidence="HIGH", cwe=330)
    assert issue["line_number"] == 2
    assert issue["test_name"] == "blacklist"
    assert "random" in issue["issue_text"].lower()


def test_rule_b401_telnet_import(tmp_path):
    issue = one_issue(tmp_path, "import telnetlib\n", "B401", severity="HIGH", confidence="HIGH", cwe=319)
    assert issue["line_number"] == 1
    assert issue["test_name"] == "blacklist"
    assert "telnet" in issue["issue_text"].lower()


def test_rule_b403_pickle_import(tmp_path):
    issue = one_issue(tmp_path, "import pickle\n", "B403", severity="LOW", confidence="HIGH", cwe=502)
    assert issue["line_number"] == 1
    assert issue["test_name"] == "blacklist"
    assert "pickle" in issue["issue_text"].lower()


def test_rule_b404_subprocess_import(tmp_path):
    issue = one_issue(tmp_path, "import subprocess\n", "B404", severity="LOW", confidence="HIGH", cwe=78)
    assert issue["line_number"] == 1
    assert issue["test_name"] == "blacklist"
    assert "subprocess" in issue["issue_text"].lower()


def test_rule_b501_disabled_certificate_validation(tmp_path):
    issue = one_issue(
        tmp_path,
        "import requests\nrequests.get(url, verify=False)\n",
        "B501",
        severity="HIGH",
        confidence="HIGH",
        cwe=295,
    )
    assert issue["line_number"] == 2
    assert issue["test_name"] == "request_with_no_cert_validation"
    assert "verify=false" in issue["issue_text"].lower()


def test_rule_b506_unsafe_yaml_load(tmp_path):
    issue = one_issue(tmp_path, "import yaml\nyaml.load(payload)\n", "B506", severity="MEDIUM", confidence="HIGH", cwe=20)
    assert issue["line_number"] == 2
    assert issue["test_name"] == "yaml_load"
    assert "yaml load" in issue["issue_text"].lower()


def test_rule_b602_subprocess_shell_true(tmp_path):
    issue = one_issue(
        tmp_path,
        "import subprocess\ncommand = input()\nsubprocess.Popen(command, shell=True)\n",
        "B602",
        severity="HIGH",
        confidence="HIGH",
        cwe=78,
    )
    assert issue["line_number"] == 3
    assert issue["test_name"] == "subprocess_popen_with_shell_equals_true"
    assert "shell=true" in issue["issue_text"].lower()


def test_rule_b608_string_built_sql(tmp_path):
    issue = one_issue(
        tmp_path,
        "query = 'SELECT * FROM users WHERE id = %s' % user_id\n",
        "B608",
        severity="MEDIUM",
        cwe=89,
    )
    assert issue["line_number"] == 1
    assert issue["test_name"] == "hardcoded_sql_expressions"
    assert "sql" in issue["issue_text"].lower()


def test_rule_b701_jinja_autoescape_false(tmp_path):
    issue = one_issue(
        tmp_path,
        "from jinja2 import Environment\nEnvironment(autoescape=False)\n",
        "B701",
        severity="HIGH",
        confidence="HIGH",
        cwe=94,
    )
    assert issue["line_number"] == 2
    assert issue["test_name"] == "jinja2_autoescape_false"
    assert "autoescape=false" in issue["issue_text"].lower()


def test_rule_b704_dynamic_markup(tmp_path):
    issue = one_issue(
        tmp_path,
        "from markupsafe import Markup\nvalue = Markup(user_input)\n",
        "B704",
        severity="MEDIUM",
        confidence="HIGH",
        cwe=79,
    )
    assert issue["line_number"] == 2
    assert issue["test_name"] == "markupsafe_markup_xss"
    assert "markup" in issue["issue_text"].lower()


def test_no_target_exits_two():
    proc = run_bandit("bandit", ["-q"])
    assert proc.returncode == 2


def test_config_generator_no_action_returns_one():
    proc = run_bandit("bandit-config-generator", [])
    assert proc.returncode == 1
