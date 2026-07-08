"""Generated public-behavior oracle for the SQLFluff SWE-E2E task.

These tests intentionally avoid the upstream ``test/conftest.py`` and any
``sqlfluff.cli.commands`` or parser-segment implementation imports. They use
only the public package/API/core imports and the documented ``python -m
sqlfluff`` command surface described in ``tasks/sqlfluff/spec.md``.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


def _mark(section: str, layer: str, notes: str):
    return pytest.mark.sqlfluff_filter(
        spec_section=section,
        layer=layer,
        notes=notes,
    )


def _cli(tmp_path: Path, args: list[str], stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HOME"] = str(tmp_path / "home")
    env["XDG_CONFIG_HOME"] = str(tmp_path / "xdg")
    Path(env["HOME"]).mkdir(exist_ok=True)
    Path(env["XDG_CONFIG_HOME"]).mkdir(exist_ok=True)
    return subprocess.run(
        [sys.executable, "-m", "sqlfluff", *args],
        cwd=tmp_path,
        input=stdin,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        timeout=30,
        check=False,
    )


def _violation_codes(records):
    return [v["code"] for record in records for v in record.get("violations", [])]


def _json_contains_string(value, expected: str) -> bool:
    if isinstance(value, str):
        return expected in value
    if isinstance(value, dict):
        return any(_json_contains_string(item, expected) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_json_contains_string(item, expected) for item in value)
    return False


@_mark("section Installable Surface", "atomic", "documented package imports are available")
def test_public_import_surface_exposes_documented_names():
    import sqlfluff
    from sqlfluff.api import APIParsingError, fix, lint, list_dialects, list_rules, parse
    from sqlfluff.core import FluffConfig, Lexer, Linter, Parser
    from sqlfluff.core.config import load_config_string

    assert isinstance(sqlfluff.__version__, str) and sqlfluff.__version__
    assert sqlfluff.lint is lint
    assert sqlfluff.fix is fix
    assert sqlfluff.parse is parse
    assert callable(list_rules)
    assert callable(list_dialects)
    assert issubclass(APIParsingError, ValueError)
    assert all(callable(obj) for obj in (FluffConfig, Lexer, Linter, Parser, load_config_string))


@_mark("section Public API", "atomic", "sqlfluff.api exposes the same simple API functions")
def test_api_module_exports_match_top_level_functions():
    import sqlfluff
    import sqlfluff.api as api

    assert api.lint is sqlfluff.lint
    assert api.fix is sqlfluff.fix
    assert api.parse is sqlfluff.parse
    assert api.list_rules is sqlfluff.list_rules
    assert api.list_dialects is sqlfluff.list_dialects


@_mark("section Dialects, Rules, and Metadata", "atomic", "dialect metadata is sorted and includes core dialects")
def test_list_dialects_returns_sorted_public_metadata():
    import sqlfluff

    dialects = sqlfluff.list_dialects()
    labels = [d.label for d in dialects]

    assert labels == sorted(labels)
    assert {"ansi", "bigquery", "postgres"}.issubset(labels)
    ansi = next(d for d in dialects if d.label == "ansi")
    assert all(hasattr(ansi, field) for field in ("label", "name", "inherits_from", "docstring"))
    assert isinstance(ansi.name, str) and ansi.name
    assert isinstance(ansi.docstring, str) and ansi.docstring


@_mark("section Cross-View Invariants", "integration", "dialect_readout and list_dialects expose the same labels")
def test_dialect_readout_and_selector_match_public_dialect_list():
    import sqlfluff
    from sqlfluff.core import dialect_readout, dialect_selector

    api_labels = [d.label for d in sqlfluff.list_dialects()]
    readout = list(dialect_readout())
    readout_labels = [d.label for d in readout]
    api_rows = [(d.label, d.name, d.inherits_from, d.docstring) for d in sqlfluff.list_dialects()]
    readout_rows = [(d.label, d.name, d.inherits_from, d.docstring) for d in readout]

    assert readout_labels == api_labels
    assert readout_rows == api_rows
    assert dialect_selector("ansi") is not None
    assert dialect_selector("postgres") is not None


@_mark("section Dialects, Rules, and Metadata", "atomic", "rule metadata includes stable code, name, groups, and aliases")
def test_list_rules_contains_public_rule_metadata():
    import sqlfluff

    rules = {rule.code: rule for rule in sqlfluff.list_rules()}

    assert {"LT01", "CP01", "AM04"}.issubset(rules)
    assert rules["LT01"].name == "layout.spacing"
    assert "layout" in rules["LT01"].groups
    assert isinstance(rules["LT01"].description, str) and rules["LT01"].description
    assert isinstance(rules["LT01"].aliases, tuple)


@_mark("section Cross-View Invariants", "integration", "list_rules and Linter.rule_tuples expose the same rule identities")
def test_linter_rule_tuples_match_simple_rule_metadata():
    import sqlfluff
    from sqlfluff.core import FluffConfig, Linter

    api_codes = {rule.code for rule in sqlfluff.list_rules()}
    linter_codes = {rule.code for rule in Linter(config=FluffConfig(overrides={"dialect": "ansi"})).rule_tuples()}

    assert {"LT01", "CP01"}.issubset(linter_codes)
    assert linter_codes == api_codes


@_mark("section Public API", "atomic", "lint distinguishes clean SQL from a spacing violation")
def test_simple_lint_returns_empty_list_for_clean_sql():
    import sqlfluff

    assert sqlfluff.lint("SELECT 1\n", dialect="ansi") == []
    assert [v["code"] for v in sqlfluff.lint("SELECT  1\n", dialect="ansi", rules=["LT01"])] == ["LT01"]


@_mark("section Public API", "atomic", "lint violation records expose code, name, position, warning status, and fixes")
def test_simple_lint_spacing_violation_record_has_public_fields():
    import sqlfluff

    violations = sqlfluff.lint("SELECT  1\n", dialect="ansi")

    assert [v["code"] for v in violations] == ["LT01"]
    violation = violations[0]
    assert violation["name"] == "layout.spacing"
    assert violation["warning"] is False
    assert violation["start_line_no"] == 1
    assert violation["start_line_pos"] == 7
    assert violation["fixes"]
    assert violation["fixes"][0]["edit"] == " "


@_mark("section Public API", "atomic", "rules narrows simple linting to the selected rules")
def test_simple_lint_rule_selection_limits_reported_rules():
    import sqlfluff

    assert [v["code"] for v in sqlfluff.lint("SELECT  1\n", dialect="ansi", rules=["LT01"])] == ["LT01"]
    assert sqlfluff.lint("SELECT  1\n", dialect="ansi", rules=["CP01"]) == []


@_mark("section Cross-View Invariants", "atomic", "exclude_rules subtracts from the selected rule set")
def test_simple_lint_exclude_rules_subtracts_after_rule_selection():
    import sqlfluff

    assert [v["code"] for v in sqlfluff.lint("SELECT  1\n", dialect="ansi", rules=["layout"])] == ["LT01"]
    assert sqlfluff.lint(
        "SELECT  1\n",
        dialect="ansi",
        rules=["layout"],
        exclude_rules=["LT01"],
    ) == []


@_mark("section Public API", "atomic", "fix applies a safe spacing edit and returns SQL text")
def test_simple_fix_applies_safe_spacing_fix():
    import sqlfluff

    assert sqlfluff.fix("SELECT  1\n", dialect="ansi", rules=["LT01"]) == "SELECT 1\n"


@_mark("section Linting, Fixing, Parsing, and Rendering", "atomic", "parse returns a nested JSON-like projection")
def test_simple_parse_returns_nested_projection_for_select():
    import sqlfluff

    parsed = sqlfluff.parse("SELECT 1\n", dialect="ansi")

    assert isinstance(parsed, dict) and parsed
    json.dumps(parsed)
    assert _json_contains_string(parsed, "SELECT")
    assert _json_contains_string(parsed, "1")


@_mark("section Error Semantics", "atomic", "simple parse raises APIParsingError with violations on parse failure")
def test_simple_parse_failure_raises_api_parsing_error_with_violations():
    from sqlfluff.api import APIParsingError, parse

    with pytest.raises(APIParsingError) as excinfo:
        parse("SELEC 1\n", dialect="ansi")

    assert excinfo.value.violations
    assert any(getattr(v, "rule_code", lambda: None)() == "PRS" for v in excinfo.value.violations)


@_mark("section Public API", "integration", "supplied config object takes precedence over dialect and rules kwargs")
def test_simple_api_config_object_takes_precedence_over_kwargs():
    import sqlfluff
    from sqlfluff.core import FluffConfig

    config = FluffConfig.from_string("[sqlfluff]\ndialect=ansi\nrules=CP01\n")

    assert [v["code"] for v in sqlfluff.lint("SELECT  1\n", dialect="ansi", rules=["LT01"])] == ["LT01"]
    assert sqlfluff.lint("SELECT  1\n", dialect="ansi", rules=["LT01"], config=config) == []


@_mark("section Configuration Behavior", "atomic", "load_config_string parses nested colon sections")
def test_load_config_string_parses_nested_sections():
    from sqlfluff.core.config import load_config_string

    config = load_config_string(
        "[sqlfluff]\ndialect=postgres\n"
        "[sqlfluff:rules:capitalisation.keywords]\ncapitalisation_policy=upper\n"
    )

    assert config["core"]["dialect"] == "postgres"
    assert config["rules"]["capitalisation.keywords"]["capitalisation_policy"] == "upper"


@_mark("section Configuration Behavior", "atomic", "later config strings override earlier strings")
def test_fluffconfig_from_strings_uses_later_precedence():
    from sqlfluff.core import FluffConfig, Linter

    config = FluffConfig.from_strings(
        "[sqlfluff]\ndialect=ansi\nrules=layout,capitalisation\n",
        "[sqlfluff]\nexclude_rules=LT01\n",
    )

    assert config.get("dialect") == "ansi"
    assert config.get("exclude_rules") == "LT01"
    assert Linter(config=config).lint_string_wrapped("SELECT  1\n").as_records()[0]["violations"] == []


@_mark("section Configuration Behavior", "integration", "config_path provides config for simple string operations")
def test_simple_api_uses_explicit_config_path(tmp_path):
    import sqlfluff

    config_path = tmp_path / ".sqlfluff"
    config_path.write_text("[sqlfluff]\ndialect=ansi\nrules=LT01\n", encoding="utf-8")

    assert [v["code"] for v in sqlfluff.lint("SELECT  1\n", config_path=str(config_path))] == ["LT01"]


@_mark("section Configuration Behavior", "integration", "pyproject.toml core and rule sections affect linting")
def test_pyproject_toml_rule_section_affects_linting(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        "[tool.sqlfluff.core]\ndialect = 'ansi'\nrules = 'CP01'\n"
        "[tool.sqlfluff.rules.capitalisation.keywords]\ncapitalisation_policy = 'upper'\n",
        encoding="utf-8",
    )
    (tmp_path / "query.sql").write_text("select 1\n", encoding="utf-8")

    proc = _cli(tmp_path, ["lint", "query.sql", "--format", "json"])
    payload = json.loads(proc.stdout)

    assert proc.returncode == 1
    assert payload[0]["filepath"] == "query.sql"
    assert _violation_codes(payload) == ["CP01"]


@_mark("section Linting, Fixing, Parsing, and Rendering", "atomic", "LintedFile exposes violations, cleanliness, and fix_string")
def test_linter_lint_string_exposes_public_linted_file_methods():
    from sqlfluff.core import FluffConfig, Linter

    linted_file = Linter(config=FluffConfig(overrides={"dialect": "ansi"})).lint_string(
        "SELECT  1\n",
        fix=True,
    )

    assert linted_file.num_violations() == 1
    assert linted_file.is_clean() is False
    assert [v.rule_code() for v in linted_file.get_violations()] == ["LT01"]
    assert linted_file.fix_string() == ("SELECT 1\n", True)


@_mark("section Linting, Fixing, Parsing, and Rendering", "integration", "LintingResult serializes records and stats")
def test_linting_result_as_records_and_stats_are_public_views():
    from sqlfluff.core import FluffConfig, Linter

    result = Linter(config=FluffConfig(overrides={"dialect": "ansi"})).lint_string_wrapped("SELECT  1\n")
    records = result.as_records()
    stats = result.stats(fail_code=65, success_code=0)

    assert records[0]["filepath"] == "<string input>"
    assert [v["code"] for v in records[0]["violations"]] == ["LT01"]
    assert stats["files"] == 1
    assert stats["violations"] == 1
    assert stats["exit code"] == 65
    assert stats["status"] == "FAIL"


@_mark("section Linting, Fixing, Parsing, and Rendering", "atomic", "Lexer returns segments and lexing violations")
def test_lexer_lexes_valid_sql_without_errors():
    from sqlfluff.core import FluffConfig, Lexer, Parser

    config = FluffConfig(overrides={"dialect": "ansi"})
    segments, violations = Lexer(config=config).lex("SELECT 1\n")
    parsed = Parser(config=config).parse(segments)

    assert violations == []
    assert segments
    assert parsed is not None


@_mark("section Linting, Fixing, Parsing, and Rendering", "atomic", "Parser returns a parsed representation for valid lexed SQL")
def test_parser_parses_lexed_segments():
    from sqlfluff.core import FluffConfig, Lexer, Parser

    config = FluffConfig(overrides={"dialect": "ansi"})
    segments, violations = Lexer(config=config).lex("SELECT 1\n")
    parsed = Parser(config=config).parse(segments)

    assert violations == []
    assert parsed is not None


@_mark("section Linting, Fixing, Parsing, and Rendering", "integration", "Linter.parse_string exposes parsed root variant and violations")
def test_linter_parse_string_exposes_parsed_string_public_view():
    from sqlfluff.core import FluffConfig, Linter

    parsed = Linter(config=FluffConfig(overrides={"dialect": "ansi"})).parse_string("SELECT 1\n")

    assert parsed.violations == []
    assert parsed.root_variant() is not None


@_mark("section Templating Behavior", "integration", "Jinja templater renders configured context")
def test_cli_render_jinja_context_from_config_file(tmp_path):
    (tmp_path / ".sqlfluff").write_text(
        "[sqlfluff]\ndialect=ansi\ntemplater=jinja\n"
        "[sqlfluff:templater:jinja:context]\ntable_name=my_table\n",
        encoding="utf-8",
    )
    (tmp_path / "query.sql").write_text("SELECT * FROM {{ table_name }}\n", encoding="utf-8")

    proc = _cli(tmp_path, ["render", "query.sql"])

    assert proc.returncode == 0
    assert proc.stdout.rstrip("\n") == "SELECT * FROM my_table"


@_mark("section Templating Behavior", "integration", "Python templater renders format-string context")
def test_cli_render_python_templater_context(tmp_path):
    (tmp_path / ".sqlfluff").write_text(
        "[sqlfluff]\ndialect=ansi\ntemplater=python\n"
        "[sqlfluff:templater:python:context]\ntable_name=my_table\n",
        encoding="utf-8",
    )
    (tmp_path / "query.sql").write_text("SELECT * FROM {table_name}\n", encoding="utf-8")

    proc = _cli(tmp_path, ["render", "query.sql"])

    assert proc.returncode == 0
    assert proc.stdout.rstrip("\n") == "SELECT * FROM my_table"


@_mark("section Templating Behavior", "integration", "placeholder templater replaces colon parameters without sample values")
def test_cli_render_placeholder_templater_colon_parameter(tmp_path):
    (tmp_path / ".sqlfluff").write_text(
        "[sqlfluff]\ndialect=ansi\ntemplater=placeholder\n"
        "[sqlfluff:templater:placeholder]\nparam_style=colon\n",
        encoding="utf-8",
    )
    (tmp_path / "query.sql").write_text("SELECT * FROM users WHERE id = :user_id\n", encoding="utf-8")

    proc = _cli(tmp_path, ["render", "query.sql"])

    assert proc.returncode == 0
    assert proc.stdout.rstrip("\n") == "SELECT * FROM users WHERE id = user_id"


@_mark("section Configuration Behavior", "integration", "noqa comments suppress selected violations")
def test_noqa_comment_suppresses_selected_rule():
    from sqlfluff.core import FluffConfig, Linter

    linter = Linter(config=FluffConfig(overrides={"dialect": "ansi"}))

    assert linter.lint_string_wrapped("SELECT  1 -- noqa: LT01\n").as_records()[0]["violations"] == []
    assert [v["code"] for v in linter.lint_string_wrapped("SELECT  1\n").as_records()[0]["violations"]] == ["LT01"]


@_mark("section Cross-View Invariants", "integration", "warnings remain visible but are marked warning")
def test_warning_configuration_marks_violation_without_hiding_it():
    from sqlfluff.core import FluffConfig, Linter

    config = FluffConfig.from_string("[sqlfluff]\ndialect=ansi\nwarnings=LT01\n")
    violations = Linter(config=config).lint_string_wrapped("SELECT  1\n").as_records()[0]["violations"]

    assert [v["code"] for v in violations] == ["LT01"]
    assert violations[0]["warning"] is True


@_mark("section Command-Line Behavior", "atomic", "version command prints installed version")
def test_cli_version_prints_installed_version(tmp_path):
    proc = _cli(tmp_path, ["version"])

    assert proc.returncode == 0
    assert proc.stdout.strip()
    assert proc.stderr == ""


@_mark("section Command-Line Behavior", "integration", "lint JSON reports no violations and exit 0 for clean stdin")
def test_cli_lint_json_clean_stdin(tmp_path):
    proc = _cli(tmp_path, ["lint", "-", "--dialect", "ansi", "--format", "json"], "SELECT 1\n")

    payload = json.loads(proc.stdout)
    assert proc.returncode == 0
    assert payload[0]["filepath"] == "stdin"
    assert payload[0]["violations"] == []


@_mark("section Command-Line Behavior", "integration", "lint JSON reports violations and exit 1 for failing stdin")
def test_cli_lint_json_violation_stdin(tmp_path):
    proc = _cli(tmp_path, ["lint", "-", "--dialect", "ansi", "--format", "json"], "SELECT  1\n")

    payload = json.loads(proc.stdout)
    assert proc.returncode == 1
    assert payload[0]["filepath"] == "stdin"
    assert _violation_codes(payload) == ["LT01"]
    assert payload[0]["violations"][0]["start_line_pos"] == 7


@_mark("section Command-Line Behavior", "integration", "lint --nofail preserves serialized violations with success exit")
def test_cli_lint_nofail_changes_exit_code_not_violations(tmp_path):
    proc = _cli(
        tmp_path,
        ["lint", "-", "--dialect", "ansi", "--format", "json", "--nofail"],
        "SELECT  1\n",
    )

    assert proc.returncode == 0
    assert _violation_codes(json.loads(proc.stdout)) == ["LT01"]


@_mark("section Command-Line Behavior", "integration", "fix stdin writes fixed SQL to stdout")
def test_cli_fix_stdin_outputs_fixed_sql(tmp_path):
    proc = _cli(tmp_path, ["fix", "-", "--dialect", "ansi", "--rules", "LT01"], "SELECT  1\n")

    assert proc.returncode == 0
    assert proc.stdout == "SELECT 1\n"


@_mark("section Command-Line Behavior", "integration", "parse JSON prints filepath and segments for stdin")
def test_cli_parse_json_stdin_outputs_segments(tmp_path):
    proc = _cli(tmp_path, ["parse", "-", "--dialect", "ansi", "--format", "json"], "SELECT 1\n")

    payload = json.loads(proc.stdout)
    segments = payload[0]["segments"]
    assert proc.returncode == 0
    assert payload[0]["filepath"] == "stdin"
    assert segments is not None
    json.dumps(segments)
    assert _json_contains_string(segments, "SELECT")
    assert _json_contains_string(segments, "1")


@_mark("section Command-Line Behavior", "integration", "render prints templated SQL with configured Jinja context")
def test_cli_render_uses_jinja_context_from_config_file(tmp_path):
    (tmp_path / ".sqlfluff").write_text(
        "[sqlfluff]\ndialect=ansi\ntemplater=jinja\n"
        "[sqlfluff:templater:jinja:context]\ntable_name=my_table\n",
        encoding="utf-8",
    )
    (tmp_path / "query.sql").write_text("SELECT * FROM {{ table_name }}\n", encoding="utf-8")

    proc = _cli(tmp_path, ["render", "query.sql"])

    assert proc.returncode == 0
    assert proc.stdout.rstrip("\n") == "SELECT * FROM my_table"


@_mark("section Configuration Behavior", "system_e2e", ".sqlfluffignore removes files unless bypassed")
def test_cli_sqlfluffignore_filters_files_and_bypass_reenables_them(tmp_path):
    (tmp_path / ".sqlfluff").write_text("[sqlfluff]\ndialect=ansi\n", encoding="utf-8")
    (tmp_path / ".sqlfluffignore").write_text("bad.sql\n", encoding="utf-8")
    (tmp_path / "bad.sql").write_text("SELECT  1\n", encoding="utf-8")

    ignored = _cli(tmp_path, ["lint", "bad.sql", "--format", "json"])
    bypassed = _cli(tmp_path, ["lint", "bad.sql", "--format", "json", "--disregard-sqlfluffignores"])

    assert ignored.returncode == 0
    assert json.loads(ignored.stdout) == []
    assert bypassed.returncode == 1
    assert _violation_codes(json.loads(bypassed.stdout)) == ["LT01"]


@_mark("section Cross-View Invariants", "system_e2e", "simple API and CLI lint expose the same violation code and position")
def test_simple_api_and_cli_lint_json_agree_on_violation_code_and_position(tmp_path):
    import sqlfluff

    api_violation = sqlfluff.lint("SELECT  1\n", dialect="ansi")[0]
    proc = _cli(tmp_path, ["lint", "-", "--dialect", "ansi", "--format", "json"], "SELECT  1\n")
    cli_violation = json.loads(proc.stdout)[0]["violations"][0]

    assert proc.returncode == 1
    assert (cli_violation["code"], cli_violation["start_line_no"], cli_violation["start_line_pos"]) == (
        api_violation["code"],
        api_violation["start_line_no"],
        api_violation["start_line_pos"],
    )


@_mark("section Cross-View Invariants", "system_e2e", "simple API and CLI fix apply the same safe fix")
def test_simple_api_and_cli_fix_stdin_agree(tmp_path):
    import sqlfluff

    proc = _cli(tmp_path, ["fix", "-", "--dialect", "ansi", "--rules", "LT01"], "SELECT  1\n")

    assert proc.returncode == 0
    assert proc.stdout == sqlfluff.fix("SELECT  1\n", dialect="ansi", rules=["LT01"])


@_mark("section Cross-View Invariants", "system_e2e", "rules and dialect metadata agree across API and CLI projections")
def test_cli_metadata_commands_expose_api_rule_and_dialect_labels(tmp_path):
    import sqlfluff

    rule_codes = {rule.code for rule in sqlfluff.list_rules()}
    dialect_labels = {dialect.label for dialect in sqlfluff.list_dialects()}
    rules_proc = _cli(tmp_path, ["rules"])
    dialects_proc = _cli(tmp_path, ["dialects"])

    assert rules_proc.returncode == 0
    assert dialects_proc.returncode == 0
    assert "LT01" in rules_proc.stdout and "LT01" in rule_codes
    assert "CP01" in rules_proc.stdout and "CP01" in rule_codes
    assert "ansi" in dialects_proc.stdout and "ansi" in dialect_labels
    assert "postgres" in dialects_proc.stdout and "postgres" in dialect_labels


@_mark("section Cross-View Invariants", "system_e2e", "rendered SQL is the shared input to linting")
def test_rendered_jinja_sql_lints_through_cli_workflow(tmp_path):
    (tmp_path / ".sqlfluff").write_text(
        "[sqlfluff]\ndialect=ansi\ntemplater=jinja\n"
        "[sqlfluff:templater:jinja:context]\ntable_name=my_table\n",
        encoding="utf-8",
    )
    (tmp_path / "query.sql").write_text("SELECT  * FROM {{ table_name }}\n", encoding="utf-8")

    render_proc = _cli(tmp_path, ["render", "query.sql"])
    lint_proc = _cli(tmp_path, ["lint", "query.sql", "--format", "json"])

    assert render_proc.returncode == 0
    assert "my_table" in render_proc.stdout
    assert lint_proc.returncode == 1
    assert "LT01" in _violation_codes(json.loads(lint_proc.stdout))
