from __future__ import annotations

import json

import pytest

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


def make_pyreverse_package(tmp_path):
    write_python(tmp_path, "samplepkg/__init__.py", '"""sample package."""\n')
    write_python(
        tmp_path,
        "samplepkg/model.py",
        '''
        """model module."""
        class Base:
            """base class."""

        class Child(Base):
            """child class."""
            def build(self) -> Base:
                """Return a base instance."""
                return Base()
        ''',
    )


def duplicate_body() -> str:
    return "\n".join(f"VALUE_{index} = {index}" for index in range(8)) + "\n"


@pytest.mark.depends_on(
    "test_missing_function_docstring_can_be_disabled_by_config_file",
    "test_disable_all_enable_unused_import_lints_only_unused_import",
)
def test_config_discovery_from_pylintrc_and_cli_override_share_one_run(tmp_path):
    write_python(
        tmp_path,
        ".pylintrc",
        "[MESSAGES CONTROL]\ndisable=missing-module-docstring,missing-function-docstring\n",
    )
    write_python(tmp_path, "sample.py", "import os\n\ndef helper():\n    return 1\n")
    first = invoke_pylint(["--output-format=json", "sample.py"], tmp_path)
    second = invoke_pylint(
        ["--disable=unused-import", "--output-format=json", "sample.py"], tmp_path
    )
    assert [message["symbol"] for message in old_json(first)] == ["unused-import"]
    assert old_json(second) == []


@pytest.mark.depends_on(
    "test_json_reporter_serializes_message_fields",
    "test_unused_import_message_is_reported_with_symbol_and_category",
)
def test_json_and_text_reporters_agree_on_unused_import_fact(tmp_path):
    write_python(tmp_path, "sample.py", '"""module doc."""\nimport os\nVALUE = 1\n')
    json_result = invoke_pylint(
        ["--disable=all", "--enable=unused-import", "--output-format=json", "sample.py"],
        tmp_path,
    )
    text_result = invoke_pylint(
        ["--disable=all", "--enable=unused-import", "--score=n", "sample.py"],
        tmp_path,
    )
    message = old_json(json_result)[0]
    assert message["symbol"] in text_result.stdout
    assert message["message-id"] in text_result.stdout


@pytest.mark.depends_on(
    "test_json2_reporter_serializes_message_and_statistics_fields",
    "test_invalid_name_message_is_reported_for_mixed_case_function",
    "test_unused_import_message_is_reported_with_symbol_and_category",
)
def test_json2_statistics_match_messages_from_a_small_module(tmp_path):
    write_python(
        tmp_path,
        "sample.py",
        '''
        """module doc."""
        import os
        def BadName():
            """function doc."""
            return 1
        ''',
    )
    result = invoke_pylint(
        [
            "--disable=all",
            "--enable=unused-import,invalid-name",
            "--output-format=json2",
            "sample.py",
        ],
        tmp_path,
    )
    payload = json2(result)
    symbols = {message["symbol"] for message in payload["messages"]}
    counts = payload["statistics"]["messageTypeCount"]
    assert symbols == {"unused-import", "invalid-name"}
    assert counts["warning"] == 1
    assert counts["convention"] == 1


@pytest.mark.depends_on(
    "test_json_reporter_serializes_message_fields",
    "test_run_pylint_helper_accepts_explicit_argument_sequence",
)
def test_from_stdin_linting_and_json_reporting_use_the_provided_virtual_filename(tmp_path):
    stdin_text = '"""module doc."""\nimport os\nVALUE = 1\n'
    result = invoke_pylint(
        [
            "--from-stdin",
            "virtual_module.py",
            "--disable=all",
            "--enable=unused-import",
            "--output-format=json",
        ],
        tmp_path,
        stdin_text=stdin_text,
    )
    message = old_json(result)[0]
    assert message["path"].endswith("virtual_module.py")
    assert message["symbol"] == "unused-import"


@pytest.mark.depends_on(
    "test_list_msgs_includes_emittable_message_headers",
    "test_list_msgs_enabled_includes_default_enabled_message_symbol",
)
def test_list_msgs_enabled_changes_when_config_disables_a_symbol(tmp_path):
    default = invoke_pylint(["--list-msgs-enabled"], tmp_path)
    write_python(
        tmp_path,
        ".pylintrc",
        "[MESSAGES CONTROL]\ndisable=missing-function-docstring\n",
    )
    configured = invoke_pylint(["--list-msgs-enabled"], tmp_path)
    configured_enabled, configured_disabled = configured.stdout.split("Disabled messages:", 1)
    assert "missing-function-docstring (C0116)" in default.stdout
    assert "missing-function-docstring (C0116)" not in configured_enabled
    assert "missing-function-docstring (C0116)" in configured_disabled
    assert "unused-import (W0611)" in configured_enabled


@pytest.mark.depends_on(
    "test_output_option_writes_report_to_file",
    "test_text_output_reports_line_too_long_with_message_id",
)
def test_cli_output_file_and_stdout_empty_when_report_is_redirected(tmp_path):
    write_python(tmp_path, "sample.py", '"""module doc."""\nVALUE = "' + "x" * 50 + '"\n')
    result = invoke_pylint(
        [
            "--disable=all",
            "--enable=line-too-long",
            "--max-line-length=20",
            "--output-format=json",
            "--output=messages.json",
            "sample.py",
        ],
        tmp_path,
    )
    file_payload = json.loads((tmp_path / "messages.json").read_text(encoding="utf-8"))
    assert result.stdout == ""
    assert result.code == 16
    assert file_payload[0]["symbol"] == "line-too-long"


@pytest.mark.depends_on(
    "test_run_pylint_on_package_path_reports_modules_from_package",
    "test_missing_module_docstring_can_be_disabled_by_cli",
)
def test_package_linting_combines_init_and_module_messages(tmp_path):
    write_python(tmp_path, "samplepkg/__init__.py", "VALUE = 1\n")
    write_python(tmp_path, "samplepkg/tool.py", '"""module doc."""\nimport os\nVALUE = 2\n')
    result = invoke_pylint(
        [
            "--disable=all",
            "--enable=missing-module-docstring,unused-import",
            "--output-format=json",
            "samplepkg",
        ],
        tmp_path,
    )
    modules = {message["module"] for message in old_json(result)}
    assert "samplepkg" in modules
    assert "samplepkg.tool" in modules


@pytest.mark.depends_on(
    "test_disable_all_enable_unused_import_lints_only_unused_import",
    "test_missing_module_docstring_can_be_disabled_by_cli",
)
def test_enable_all_then_disable_symbol_restores_specific_message_control(tmp_path):
    write_python(tmp_path, "sample.py", '"""module doc."""\nimport os\nVALUE = 1\n')
    enabled = invoke_pylint(
        [
            "--disable=all",
            "--enable=unused-import",
            "--output-format=json",
            "sample.py",
        ],
        tmp_path,
    )
    disabled = invoke_pylint(
        [
            "--enable=all",
            "--disable=unused-import,missing-module-docstring,missing-function-docstring",
            "--output-format=json",
            "sample.py",
        ],
        tmp_path,
    )
    assert [message["symbol"] for message in old_json(enabled)] == ["unused-import"]
    assert old_json(disabled) == []


@pytest.mark.depends_on(
    "test_fail_under_above_clean_score_exits_nonzero",
    "test_exit_zero_overrides_message_status",
)
def test_fail_under_and_exit_zero_interact_with_the_same_message_run(tmp_path):
    write_python(tmp_path, "sample.py", '"""module doc."""\nimport os\nVALUE = 1\n')
    failing = invoke_pylint(
        [
            "--disable=all",
            "--enable=unused-import",
            "--fail-under=10",
            "sample.py",
        ],
        tmp_path,
    )
    forced = invoke_pylint(
        [
            "--disable=all",
            "--enable=unused-import",
            "--fail-under=10",
            "--exit-zero",
            "sample.py",
        ],
        tmp_path,
    )
    assert failing.code != 0
    assert forced.code == 0
    assert "unused-import" in failing.stdout


@pytest.mark.depends_on(
    "test_json2_score_is_computed_for_clean_module",
    "test_fail_under_above_clean_score_exits_nonzero",
)
def test_clean_module_json2_score_and_exit_code_are_consistent(tmp_path):
    write_python(tmp_path, "clean.py", '"""module doc."""\nVALUE = 1\n')
    payload_result = invoke_pylint(["--output-format=json2", "clean.py"], tmp_path)
    passing = invoke_pylint(["--fail-under=9", "clean.py"], tmp_path)
    failing = invoke_pylint(["--fail-under=10.1", "clean.py"], tmp_path)
    assert json2(payload_result)["statistics"]["score"] == 10.0
    assert passing.code == 0
    assert failing.code == 1


@pytest.mark.depends_on("test_run_pyreverse_version_emits_version_string")
def test_pyreverse_dot_projection_creates_class_and_package_files(tmp_path):
    make_pyreverse_package(tmp_path)
    output_dir = tmp_path / "diagrams"
    output_dir.mkdir()
    result = invoke_pyreverse(
        ["-o", "dot", "-d", "diagrams", "-p", "sample", "samplepkg"],
        tmp_path,
    )
    classes = output_dir / "classes_sample.dot"
    packages = output_dir / "packages_sample.dot"
    text = classes.read_text(encoding="utf-8")
    assert result.code == 0
    assert classes.is_file()
    assert packages.is_file()
    assert "Base" in text
    assert "Child" in text


@pytest.mark.depends_on("test_run_pyreverse_version_emits_version_string")
def test_pyreverse_puml_projection_contains_class_names_and_relationship_tokens(tmp_path):
    make_pyreverse_package(tmp_path)
    output_dir = tmp_path / "puml"
    output_dir.mkdir()
    result = invoke_pyreverse(
        ["-o", "puml", "-d", "puml", "-p", "sample", "samplepkg"],
        tmp_path,
    )
    text = (output_dir / "classes_sample.puml").read_text(encoding="utf-8")
    assert result.code == 0
    assert "@startuml" in text
    assert "Base" in text
    assert "Child" in text


@pytest.mark.depends_on("test_run_pyreverse_version_emits_version_string")
def test_pyreverse_with_source_root_projects_package_names_from_src_layout(tmp_path):
    write_python(tmp_path, "src/srctest/__init__.py", '"""src package."""\n')
    write_python(
        tmp_path,
        "src/srctest/model.py",
        '''
        """src model."""
        class Item:
            """item class."""
        ''',
    )
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    result = invoke_pyreverse(
        [
            "-o",
            "dot",
            "-d",
            "out",
            "-p",
            "srcsample",
            "--source-roots",
            "src",
            "src/srctest",
        ],
        tmp_path,
    )
    text = (output_dir / "classes_srcsample.dot").read_text(encoding="utf-8")
    assert result.code == 0
    assert "srctest.model.Item" in text


@pytest.mark.depends_on(
    "test_run_symilar_reports_zero_duplicates_for_different_files",
    "test_run_symilar_reports_duplicate_lines_for_identical_files",
)
def test_symilar_duplicate_workflow_reports_duplicate_blocks_and_totals(tmp_path):
    write_python(tmp_path, "a.py", duplicate_body())
    write_python(tmp_path, "b.py", duplicate_body())
    result = invoke_symilar(["a.py", "b.py"], tmp_path)
    assert result.code == 0
    assert "similar lines in 2 files" in result.stdout
    assert "==a.py" in result.stdout
    assert "==b.py" in result.stdout
    assert "TOTAL lines=" in result.stdout


@pytest.mark.depends_on("test_run_symilar_reports_zero_duplicates_for_different_files")
def test_symilar_ignore_imports_removes_import_only_duplicates(tmp_path):
    imports = "\n".join(f"import module_{index}" for index in range(8)) + "\n"
    write_python(tmp_path, "a.py", imports)
    write_python(tmp_path, "b.py", imports)
    baseline = invoke_symilar(["a.py", "b.py"], tmp_path)
    ignored = invoke_symilar(["--ignore-imports", "a.py", "b.py"], tmp_path)
    assert "similar lines in 2 files" in baseline.stdout
    assert "duplicates=0" in ignored.stdout


@pytest.mark.depends_on("test_run_symilar_reports_duplicate_lines_for_identical_files")
def test_symilar_with_duplicates_zero_is_quiet_after_two_files(tmp_path):
    write_python(tmp_path, "a.py", duplicate_body())
    write_python(tmp_path, "b.py", duplicate_body())
    result = invoke_symilar(["--duplicates=0", "a.py", "b.py"], tmp_path)
    assert result.code == 0
    assert result.stdout == ""


@pytest.mark.depends_on(
    "test_run_symilar_reports_duplicate_lines_for_identical_files",
    "test_unused_import_message_is_reported_with_symbol_and_category",
)
def test_duplicate_code_lint_and_symilar_agree_on_the_same_two_files(tmp_path):
    block = duplicate_body()
    write_python(tmp_path, "a.py", block + "LEFT = 1\n")
    write_python(tmp_path, "b.py", block + "RIGHT = 2\n")
    similarity = invoke_symilar(["a.py", "b.py"], tmp_path)
    lint = invoke_pylint(
        [
            "--disable=all",
            "--enable=duplicate-code",
            "--min-similarity-lines=4",
            "--output-format=json",
            "a.py",
            "b.py",
        ],
        tmp_path,
    )
    assert "similar lines in 2 files" in similarity.stdout
    assert "duplicate-code" in {message["symbol"] for message in old_json(lint)}


@pytest.mark.depends_on(
    "test_help_msg_resolves_symbol_and_id",
    "test_json_reporter_serializes_message_fields",
)
def test_help_msg_and_json_reporter_share_the_same_message_identity(tmp_path):
    write_python(tmp_path, "sample.py", '"""module doc."""\nimport os\nVALUE = 1\n')
    help_result = invoke_pylint(["--help-msg", "W0611"], tmp_path)
    json_result = invoke_pylint(
        ["--disable=all", "--enable=unused-import", "--output-format=json", "sample.py"],
        tmp_path,
    )
    message = old_json(json_result)[0]
    assert ":unused-import (W0611):" in help_result.stdout
    assert message["message-id"] == "W0611"
    assert message["symbol"] == "unused-import"


@pytest.mark.depends_on(
    "test_generate_rcfile_contains_main_section_and_message_controls",
    "test_missing_function_docstring_can_be_disabled_by_config_file",
)
def test_generate_rcfile_and_config_file_round_trip_controls_enabled_messages(tmp_path):
    generated = invoke_pylint(["--generate-rcfile"], tmp_path)
    write_python(
        tmp_path,
        ".pylintrc",
        "[MESSAGES CONTROL]\ndisable=missing-module-docstring,missing-function-docstring\n",
    )
    write_python(tmp_path, "sample.py", "def helper():\n    return 1\n")
    lint = invoke_pylint(["--score=n", "sample.py"], tmp_path)
    assert "[MESSAGES CONTROL]" in generated.stdout
    assert lint.code == 0
    assert lint.stdout == ""


@pytest.mark.depends_on(
    "test_run_pylint_on_package_path_reports_modules_from_package",
    "test_output_option_writes_report_to_file",
)
def test_cli_run_on_directory_and_file_paths_preserve_path_projection(tmp_path):
    write_python(tmp_path, "pkg/__init__.py", '"""package doc."""\n')
    write_python(tmp_path, "pkg/tool.py", '"""module doc."""\nimport os\nVALUE = 1\n')
    write_python(tmp_path, "loose.py", '"""module doc."""\nimport sys\nVALUE = 2\n')
    result = invoke_pylint(
        [
            "--disable=all",
            "--enable=unused-import",
            "--output-format=json",
            "pkg",
            "loose.py",
        ],
        tmp_path,
    )
    paths = {message["path"].replace("\\", "/") for message in old_json(result)}
    assert any(path.endswith("pkg/tool.py") for path in paths)
    assert any(path.endswith("loose.py") for path in paths)


@pytest.mark.depends_on(
    "test_json_reporter_serializes_message_fields",
    "test_json2_reporter_serializes_message_and_statistics_fields",
)
def test_json_reporter_and_json2_reporter_serialize_same_message_core_fields(tmp_path):
    write_python(tmp_path, "sample.py", '"""module doc."""\nimport os\nVALUE = 1\n')
    json_result = invoke_pylint(
        ["--disable=all", "--enable=unused-import", "--output-format=json", "sample.py"],
        tmp_path,
    )
    json2_result = invoke_pylint(
        ["--disable=all", "--enable=unused-import", "--output-format=json2", "sample.py"],
        tmp_path,
    )
    old_message = old_json(json_result)[0]
    new_message = json2(json2_result)["messages"][0]
    assert old_message["symbol"] == new_message["symbol"]
    assert old_message["message-id"] == new_message["messageId"]
    assert old_message["line"] == new_message["line"]


@pytest.mark.depends_on(
    "test_inline_disable_and_enable_restore_message_after_scope",
    "test_missing_function_docstring_can_be_disabled_by_config_file",
)
def test_inline_suppression_and_config_disable_compose_without_host_state(tmp_path):
    write_python(
        tmp_path,
        ".pylintrc",
        "[MESSAGES CONTROL]\ndisable=missing-module-docstring,missing-function-docstring\n",
    )
    write_python(
        tmp_path,
        "sample.py",
        '''
        # pylint: disable=unused-import
        import os
        # pylint: enable=unused-import
        import sys

        def helper():
            return 1
        ''',
    )
    result = invoke_pylint(
        ["--disable=all", "--enable=unused-import", "--output-format=json", "sample.py"],
        tmp_path,
    )
    messages = old_json(result)
    assert len(messages) == 1
    assert messages[0]["symbol"] == "unused-import"


@pytest.mark.depends_on(
    "test_generate_rcfile_contains_main_section_and_message_controls",
    "test_json2_reporter_serializes_message_and_statistics_fields",
)
def test_generated_config_and_json2_report_share_disabled_message_state(tmp_path):
    generated = invoke_pylint(["--generate-rcfile"], tmp_path)
    config = tmp_path / ".pylintrc"
    config.write_text(
        "[MESSAGES CONTROL]\n"
        "disable=missing-module-docstring,missing-function-docstring\n",
        encoding="utf-8",
    )
    write_python(tmp_path, "sample.py", "def helper():\n    return 1\n")

    result = invoke_pylint(["--output-format=json2", "sample.py"], tmp_path)
    payload = json2(result)

    assert "[MESSAGES CONTROL]" in generated.stdout
    assert result.code == 0
    assert payload["messages"] == []


@pytest.mark.depends_on(
    "test_json_reporter_serializes_message_fields",
    "test_run_pylint_helper_accepts_explicit_argument_sequence",
)
def test_file_and_stdin_json_reports_preserve_the_same_message_identity(tmp_path):
    source = '"""module doc."""\nimport os\nVALUE = 1\n'
    write_python(tmp_path, "sample.py", source)
    file_result = invoke_pylint(
        ["--disable=all", "--enable=unused-import", "--output-format=json", "sample.py"],
        tmp_path,
    )
    stdin_result = invoke_pylint(
        [
            "--from-stdin",
            "virtual.py",
            "--disable=all",
            "--enable=unused-import",
            "--output-format=json",
        ],
        tmp_path,
        stdin_text=source,
    )

    file_message = old_json(file_result)[0]
    stdin_message = old_json(stdin_result)[0]
    assert (file_message["symbol"], file_message["message-id"]) == (
        stdin_message["symbol"],
        stdin_message["message-id"],
    )
    assert stdin_message["path"].endswith("virtual.py")


@pytest.mark.depends_on(
    "test_run_pylint_on_package_path_reports_modules_from_package",
    "test_run_pyreverse_version_emits_version_string",
)
def test_package_lint_and_pyreverse_share_module_name_projection(tmp_path):
    make_pyreverse_package(tmp_path)
    model = tmp_path / "samplepkg" / "model.py"
    model.write_text(model.read_text(encoding="utf-8") + "\nimport os\n", encoding="utf-8")
    lint_result = invoke_pylint(
        [
            "--disable=all",
            "--enable=unused-import",
            "--output-format=json",
            "samplepkg",
        ],
        tmp_path,
    )
    output_dir = tmp_path / "diagram"
    output_dir.mkdir()
    reverse_result = invoke_pyreverse(
        ["-o", "dot", "-d", "diagram", "-p", "sample", "samplepkg"],
        tmp_path,
    )

    modules = {message["module"] for message in old_json(lint_result)}
    diagram = (output_dir / "classes_sample.dot").read_text(encoding="utf-8")
    assert lint_result.code == 4
    assert reverse_result.code == 0
    assert "samplepkg.model" in modules
    assert "samplepkg.model" in diagram


@pytest.mark.depends_on(
    "test_fail_under_above_clean_score_exits_nonzero",
    "test_json2_score_is_computed_for_clean_module",
)
def test_fail_under_threshold_and_json2_score_agree_on_a_clean_package(tmp_path):
    write_python(tmp_path, "clean.py", '"""module doc."""\nVALUE = 1\n')
    score = json2(invoke_pylint(["--output-format=json2", "clean.py"], tmp_path))
    accepted = invoke_pylint(["--fail-under=9.9", "clean.py"], tmp_path)
    rejected = invoke_pylint(["--fail-under=10.1", "clean.py"], tmp_path)

    assert score["statistics"]["score"] == 10.0
    assert accepted.code == 0
    assert rejected.code == 1


@pytest.mark.depends_on(
    "test_run_symilar_reports_zero_duplicates_for_different_files",
    "test_run_symilar_reports_duplicate_lines_for_identical_files",
)
def test_symilar_ignore_imports_and_duplicate_limit_compose_for_clean_files(tmp_path):
    body = "\n".join(f"VALUE_{index} = {index}" for index in range(8)) + "\n"
    write_python(tmp_path, "a.py", "import os\n" + body)
    write_python(tmp_path, "b.py", "import os\n" + body)
    result = invoke_symilar(["--ignore-imports", "--duplicates=0", "a.py", "b.py"], tmp_path)

    assert result.code == 0
    assert result.stdout == ""


@pytest.mark.depends_on(
    "test_help_msg_resolves_symbol_and_id",
    "test_text_output_reports_line_too_long_with_message_id",
)
def test_help_lookup_and_json_report_keep_message_id_for_line_too_long(tmp_path):
    write_python(tmp_path, "sample.py", '"""module doc."""\nVALUE = "' + "x" * 60 + '"\n')
    report = invoke_pylint(
        [
            "--disable=all",
            "--enable=line-too-long",
            "--max-line-length=20",
            "--output-format=json",
            "sample.py",
        ],
        tmp_path,
    )
    help_result = invoke_pylint(["--help-msg", "C0301"], tmp_path)
    message = old_json(report)[0]

    assert message["message-id"] == "C0301"
    assert ":line-too-long (C0301):" in help_result.stdout


@pytest.mark.depends_on(
    "test_inline_disable_suppresses_unused_import_message",
    "test_inline_disable_and_enable_restore_message_after_scope",
)
def test_inline_disable_scope_and_json2_report_preserve_only_reenabled_messages(tmp_path):
    write_python(
        tmp_path,
        "sample.py",
        '"""module doc."""\n'
        "# pylint: disable=unused-import\n"
        "import os\n"
        "# pylint: enable=unused-import\n"
        "import sys\n",
    )
    result = invoke_pylint(
        ["--disable=all", "--enable=unused-import", "--output-format=json2", "sample.py"],
        tmp_path,
    )
    messages = json2(result)["messages"]

    assert len(messages) == 1
    assert messages[0]["symbol"] == "unused-import"


@pytest.mark.depends_on(
    "test_output_option_writes_report_to_file",
    "test_json_reporter_serializes_message_fields",
)
def test_output_file_and_stdout_json_reports_preserve_the_same_semantic_message(tmp_path):
    write_python(tmp_path, "sample.py", '"""module doc."""\nimport os\nVALUE = 1\n')
    stdout_result = invoke_pylint(
        ["--disable=all", "--enable=unused-import", "--output-format=json", "sample.py"],
        tmp_path,
    )
    file_result = invoke_pylint(
        [
            "--disable=all",
            "--enable=unused-import",
            "--output-format=json",
            "--output=messages.json",
            "sample.py",
        ],
        tmp_path,
    )
    stdout_message = old_json(stdout_result)[0]
    file_message = json.loads((tmp_path / "messages.json").read_text(encoding="utf-8"))[0]

    assert file_result.stdout == ""
    assert (file_message["symbol"], file_message["message-id"], file_message["line"]) == (
        stdout_message["symbol"],
        stdout_message["message-id"],
        stdout_message["line"],
    )
