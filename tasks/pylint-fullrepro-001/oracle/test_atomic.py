from __future__ import annotations

import json

from conftest import (
    invoke_pylint,
    invoke_pyreverse,
    invoke_symilar,
    relative_to,
    write_python,
)


def old_json(result):
    return json.loads(result.stdout)


def json2(result):
    return json.loads(result.stdout)


def symbols(messages):
    return [message["symbol"] for message in messages]


def test_public_import_surface_exposes_version_and_runner_names():
    import pylint

    assert isinstance(pylint.__version__, str)
    assert pylint.version == pylint.__version__
    assert callable(pylint.run_pylint)
    assert callable(pylint.run_pyreverse)
    assert callable(pylint.run_symilar)


def test_run_version_prints_pylint_and_astroid_versions(tmp_path):
    result = invoke_pylint(["--version"], tmp_path)
    assert result.code == 0
    assert "pylint" in result.stdout
    assert "astroid" in result.stdout
    assert result.stderr == ""


def test_generate_rcfile_contains_main_section_and_message_controls(tmp_path):
    result = invoke_pylint(["--generate-rcfile"], tmp_path)
    assert result.code == 0
    assert "[MAIN]" in result.stdout
    assert "[MESSAGES CONTROL]" in result.stdout
    assert "disable=" in result.stdout


def test_list_msgs_includes_emittable_message_headers(tmp_path):
    result = invoke_pylint(["--list-msgs"], tmp_path)
    assert result.code == 0
    assert "Emittable messages with current interpreter:" in result.stdout
    assert ":invalid-name (C0103):" in result.stdout
    assert ":unused-import (W0611):" in result.stdout


def test_list_msgs_enabled_includes_default_enabled_message_symbol(tmp_path):
    result = invoke_pylint(["--list-msgs-enabled"], tmp_path)
    assert result.code == 0
    assert "Enabled messages:" in result.stdout
    assert "missing-function-docstring (C0116)" in result.stdout


def test_help_msg_resolves_symbol_and_id(tmp_path):
    by_id = invoke_pylint(["--help-msg", "C0114"], tmp_path)
    by_symbol = invoke_pylint(["--help-msg", "missing-module-docstring"], tmp_path)
    assert by_id.code == 0
    assert by_symbol.code == 0
    assert ":missing-module-docstring (C0114):" in by_id.stdout
    assert ":missing-module-docstring (C0114):" in by_symbol.stdout


def test_disable_all_without_enabled_messages_exits_with_no_files_to_lint(tmp_path):
    write_python(tmp_path, "sample.py", '"""module doc."""\nVALUE = 1\n')
    result = invoke_pylint(["--disable=all", "sample.py"], tmp_path)
    assert result.code == 32
    assert "No files to lint" in result.stdout


def test_disable_all_enable_unused_import_lints_only_unused_import(tmp_path):
    write_python(tmp_path, "sample.py", '"""module doc."""\nimport os\nVALUE = 1\n')
    result = invoke_pylint(
        ["--disable=all", "--enable=unused-import", "--output-format=json", "sample.py"],
        tmp_path,
    )
    payload = old_json(result)
    assert result.code == 4
    assert symbols(payload) == ["unused-import"]
    assert payload[0]["message-id"] == "W0611"


def test_inline_disable_suppresses_unused_import_message(tmp_path):
    write_python(
        tmp_path,
        "sample.py",
        '''
        """module doc."""
        # pylint: disable=unused-import
        import os
        VALUE = 1
        ''',
    )
    result = invoke_pylint(
        ["--disable=all", "--enable=unused-import", "--output-format=json", "sample.py"],
        tmp_path,
    )
    assert result.code == 0
    assert old_json(result) == []


def test_inline_disable_and_enable_restore_message_after_scope(tmp_path):
    write_python(
        tmp_path,
        "sample.py",
        '''
        """module doc."""
        # pylint: disable=unused-import
        import os
        # pylint: enable=unused-import
        import sys
        ''',
    )
    result = invoke_pylint(
        ["--disable=all", "--enable=unused-import", "--output-format=json", "sample.py"],
        tmp_path,
    )
    payload = old_json(result)
    assert result.code == 4
    assert symbols(payload) == ["unused-import"]
    assert payload[0]["line"] > 3


def test_missing_module_docstring_can_be_disabled_by_cli(tmp_path):
    write_python(tmp_path, "sample.py", "VALUE = 1\n")
    result = invoke_pylint(
        ["--disable=missing-module-docstring", "--score=n", "sample.py"],
        tmp_path,
    )
    assert result.code == 0
    assert "missing-module-docstring" not in result.stdout


def test_missing_function_docstring_can_be_disabled_by_config_file(tmp_path):
    write_python(tmp_path, ".pylintrc", "[MESSAGES CONTROL]\ndisable=missing-function-docstring\n")
    write_python(
        tmp_path,
        "sample.py",
        '''
        """module doc."""
        def helper():
            return 1
        ''',
    )
    result = invoke_pylint(["--score=n", "sample.py"], tmp_path)
    assert result.code == 0
    assert "missing-function-docstring" not in result.stdout


def test_json_reporter_serializes_message_fields():
    from pylint.interfaces import HIGH
    from pylint.message import Message
    from pylint.reporters.json_reporter import JSONReporter
    from pylint.typing import MessageLocationTuple

    message = Message(
        msg_id="W0611",
        symbol="unused-import",
        msg="Unused import os",
        confidence=HIGH,
        location=MessageLocationTuple(
            abspath="sample.py",
            path="sample.py",
            module="sample",
            obj="",
            line=2,
            column=0,
            end_line=None,
            end_column=None,
        ),
    )
    payload = JSONReporter.serialize(message)
    assert payload["message-id"] == "W0611"
    assert payload["symbol"] == "unused-import"
    assert payload["path"] == "sample.py"


def test_json2_reporter_serializes_message_and_statistics_fields():
    from pylint.interfaces import HIGH
    from pylint.message import Message
    from pylint.reporters.json_reporter import JSON2Reporter
    from pylint.typing import MessageLocationTuple

    message = Message(
        msg_id="W0611",
        symbol="unused-import",
        msg="Unused import os",
        confidence=HIGH,
        location=MessageLocationTuple(
            abspath="sample.py",
            path="sample.py",
            module="sample",
            obj="",
            line=2,
            column=0,
            end_line=2,
            end_column=9,
        ),
    )
    payload = JSON2Reporter.serialize(message)
    assert payload["messageId"] == "W0611"
    assert payload["confidence"] == "HIGH"
    assert payload["absolutePath"] == "sample.py"


def test_text_output_reports_line_too_long_with_message_id(tmp_path):
    write_python(tmp_path, "sample.py", '"""module doc."""\nVALUE = "' + "x" * 60 + '"\n')
    result = invoke_pylint(
        [
            "--disable=all",
            "--enable=line-too-long",
            "--max-line-length=20",
            "--score=n",
            "sample.py",
        ],
        tmp_path,
    )
    assert result.code == 16
    assert "C0301" in result.stdout
    assert "line-too-long" in result.stdout


def test_unused_import_message_is_reported_with_symbol_and_category(tmp_path):
    write_python(tmp_path, "sample.py", '"""module doc."""\nimport os\nVALUE = 1\n')
    result = invoke_pylint(
        ["--disable=all", "--enable=unused-import", "--output-format=json", "sample.py"],
        tmp_path,
    )
    message = old_json(result)[0]
    assert message["type"] == "warning"
    assert message["symbol"] == "unused-import"
    assert message["message-id"] == "W0611"


def test_invalid_name_message_is_reported_for_mixed_case_function(tmp_path):
    write_python(
        tmp_path,
        "sample.py",
        '''
        """module doc."""
        def BadName():
            """function doc."""
            return 1
        ''',
    )
    result = invoke_pylint(
        ["--disable=all", "--enable=invalid-name", "--output-format=json", "sample.py"],
        tmp_path,
    )
    message = old_json(result)[0]
    assert result.code == 16
    assert message["symbol"] == "invalid-name"
    assert message["message-id"] == "C0103"


def test_syntax_error_is_reported_as_error_and_nonzero(tmp_path):
    write_python(tmp_path, "broken.py", "def broken(:\n    pass\n")
    result = invoke_pylint(["--output-format=json", "broken.py"], tmp_path)
    message = old_json(result)[0]
    assert result.code == 2
    assert message["symbol"] == "syntax-error"
    assert message["type"] == "error"


def test_import_error_message_is_reported_for_missing_local_module(tmp_path):
    write_python(
        tmp_path,
        "sample.py",
        '''
        """module doc."""
        import definitely_missing_local_module
        VALUE = 1
        ''',
    )
    result = invoke_pylint(
        ["--disable=all", "--enable=import-error", "--output-format=json", "sample.py"],
        tmp_path,
    )
    message = old_json(result)[0]
    assert result.code == 2
    assert message["symbol"] == "import-error"
    assert message["message-id"] == "E0401"


def test_undefined_variable_message_reports_error_symbol(tmp_path):
    write_python(
        tmp_path,
        "sample.py",
        '''
        """module doc."""
        def helper():
            """function doc."""
            return missing_name
        ''',
    )
    result = invoke_pylint(
        [
            "--disable=all",
            "--enable=undefined-variable",
            "--output-format=json",
            "sample.py",
        ],
        tmp_path,
    )
    message = old_json(result)[0]
    assert result.code == 2
    assert message["symbol"] == "undefined-variable"
    assert message["message-id"] == "E0602"


def test_fail_under_above_clean_score_exits_nonzero(tmp_path):
    write_python(tmp_path, "clean.py", '"""module doc."""\nVALUE = 1\n')
    result = invoke_pylint(["--fail-under=10.1", "clean.py"], tmp_path)
    assert result.code == 1
    assert "rated at" in result.stdout


def test_exit_zero_overrides_message_status(tmp_path):
    write_python(tmp_path, "sample.py", '"""module doc."""\nimport os\nVALUE = 1\n')
    result = invoke_pylint(
        [
            "--disable=all",
            "--enable=unused-import",
            "--exit-zero",
            "--score=n",
            "sample.py",
        ],
        tmp_path,
    )
    assert result.code == 0
    assert "unused-import" in result.stdout


def test_score_can_be_suppressed_from_text_output(tmp_path):
    write_python(tmp_path, "clean.py", '"""module doc."""\nVALUE = 1\n')
    result = invoke_pylint(["--score=n", "clean.py"], tmp_path)
    assert result.code == 0
    assert "rated at" not in result.stdout


def test_json2_score_is_computed_for_clean_module(tmp_path):
    write_python(tmp_path, "clean.py", '"""module doc."""\nVALUE = 1\n')
    result = invoke_pylint(["--output-format=json2", "clean.py"], tmp_path)
    payload = json2(result)
    assert result.code == 0
    assert payload["messages"] == []
    assert payload["statistics"]["score"] == 10.0


def test_output_option_writes_report_to_file(tmp_path):
    write_python(tmp_path, "sample.py", '"""module doc."""\nimport os\nVALUE = 1\n')
    result = invoke_pylint(
        [
            "--disable=all",
            "--enable=unused-import",
            "--output-format=json",
            "--output=lint.json",
            "sample.py",
        ],
        tmp_path,
    )
    payload = json.loads((tmp_path / "lint.json").read_text(encoding="utf-8"))
    assert result.code == 4
    assert result.stdout == ""
    assert symbols(payload) == ["unused-import"]


def test_run_pylint_helper_accepts_explicit_argument_sequence(tmp_path):
    write_python(tmp_path, "clean.py", '"""module doc."""\nVALUE = 1\n')
    result = invoke_pylint(["--score=n", "clean.py"], tmp_path)
    assert result.code == 0
    assert result.stderr == ""


def test_run_pylint_on_package_path_reports_modules_from_package(tmp_path):
    write_python(tmp_path, "samplepkg/__init__.py", '"""package doc."""\n')
    write_python(tmp_path, "samplepkg/tool.py", '"""module doc."""\nimport os\nVALUE = 1\n')
    result = invoke_pylint(
        [
            "--disable=all",
            "--enable=unused-import",
            "--output-format=json",
            "samplepkg",
        ],
        tmp_path,
    )
    payload = old_json(result)
    assert result.code == 4
    assert payload[0]["module"] == "samplepkg.tool"
    assert payload[0]["path"].endswith("tool.py")


def test_run_pyreverse_version_emits_version_string(tmp_path):
    result = invoke_pyreverse(["--version"], tmp_path)
    assert result.code == 0
    assert "pyreverse is included in pylint" in result.stdout
    assert "pylint" in result.stdout


def test_run_symilar_reports_zero_duplicates_for_different_files(tmp_path):
    write_python(tmp_path, "a.py", '"""a."""\nVALUE = 1\n')
    write_python(tmp_path, "b.py", '"""b."""\nVALUE = 2\n')
    result = invoke_symilar(["a.py", "b.py"], tmp_path)
    assert result.code == 0
    assert "duplicates=0" in result.stdout
    assert "TOTAL lines=" in result.stdout


def test_run_symilar_reports_duplicate_lines_for_identical_files(tmp_path):
    block = "\n".join(f"VALUE_{index} = {index}" for index in range(8))
    write_python(tmp_path, "a.py", block + "\n")
    write_python(tmp_path, "b.py", block + "\n")
    result = invoke_symilar(["a.py", "b.py"], tmp_path)
    assert result.code == 0
    assert "similar lines in 2 files" in result.stdout
    assert "duplicates=" in result.stdout
