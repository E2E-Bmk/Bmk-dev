from __future__ import annotations

from io import StringIO
from pathlib import Path

import isort
import pytest


@pytest.mark.depends_on("test_code_sorts_stdlib_and_third_party_sections", "test_check_code_reports_sortedness")
def test_api_code_and_check_round_trip(unsorted_code, sorted_code, base_config):
    formatted = isort.code(unsorted_code, config=base_config)
    assert formatted == sorted_code
    assert isort.check_code(formatted, config=base_config) is True


@pytest.mark.depends_on("test_stream_writes_sorted_code_and_reports_change", "test_check_stream_reports_sortedness")
def test_api_stream_output_is_checkable(simple_unsorted, simple_sorted, base_config):
    output = StringIO()
    assert isort.stream(StringIO(simple_unsorted), output, config=base_config) is True
    assert output.getvalue() == simple_sorted
    assert isort.check_stream(StringIO(output.getvalue()), config=base_config) is True


@pytest.mark.depends_on("test_file_rewrites_and_returns_changed", "test_check_file_reports_sortedness")
def test_api_file_rewrite_then_check(make_file, base_config):
    path = make_file("sample.py", "import z\nimport os\n")
    assert isort.file(path, config=base_config) is True
    assert isort.check_file(path, config=base_config) is True
    assert isort.file(path, config=base_config) is False


@pytest.mark.depends_on("test_file_output_stream_returns_sorted_content_without_rewriting")
def test_api_output_stream_preserves_source(make_file, base_config):
    path = make_file("sample.py", "import z\nimport os\n")
    output = StringIO()
    changed = isort.file(path, config=base_config, output=output)
    assert changed is True
    assert output.getvalue() == "import os\n\nimport z\n"
    assert path.read_text(encoding="utf-8") == "import z\nimport os\n"


@pytest.mark.depends_on("test_stream_writes_sorted_code_and_reports_change")
def test_api_diff_exposes_unified_changes(make_file, base_config):
    path = make_file("sample.py", "import z\nimport os\n")
    diff = StringIO()
    output = StringIO()
    changed = isort.stream(
        StringIO(path.read_text(encoding="utf-8")),
        output,
        config=base_config,
        file_path=path,
        show_diff=diff,
    )
    assert changed is True
    assert "@@" in diff.getvalue()
    assert "+import os" in diff.getvalue()
    assert "-import os" in diff.getvalue()


@pytest.mark.depends_on("test_config_profile_black_controls_documented_values", "test_vertical_hanging_output_mode_wraps_long_import")
def test_api_profile_wraps_and_check_code_accepts(long_from):
    config = isort.Config(profile="black", line_length=30)
    formatted = isort.code(long_from, config=config)
    assert formatted == (
        "from package import (\n"
        "    alpha,\n"
        "    beta,\n"
        "    delta,\n"
        "    gamma,\n"
        "    zeta,\n"
        ")\n"
    )
    assert isort.check_code(formatted, config=config) is True


@pytest.mark.depends_on("test_config_custom_section_places_known_module", "test_place_module_with_reason_exposes_category_and_reason")
def test_custom_section_sort_and_place_agree():
    config = isort.Config(
        known_django=["django"],
        sections=("FUTURE", "STDLIB", "DJANGO", "THIRDPARTY", "FIRSTPARTY", "LOCALFOLDER"),
    )
    source = "import z\nimport django\nimport os\n"
    assert isort.place_module("django", config) == "DJANGO"
    assert isort.code(source, config=config) == (
        "import os\n\n"
        "import django\n\n"
        "import z\n"
    )


@pytest.mark.depends_on("test_config_add_and_remove_imports_transform_code", "test_check_code_reports_sortedness")
def test_api_add_remove_and_check_round_trip(base_config):
    config = isort.Config(add_imports=["import sys"], remove_imports=["json"])
    formatted = isort.code("import z\nimport json\n", config=config)
    assert formatted == "import sys\n\nimport z\n"
    assert isort.check_code(formatted, config=config) is True


@pytest.mark.depends_on("test_inline_skip_comment_preserves_the_marked_import", "test_off_and_on_comments_preserve_only_the_disabled_block")
def test_action_comment_blocks_override_add_imports(base_config):
    config = isort.Config(add_imports=["import sys"])
    source = (
        "# isort: dont-add-imports\n"
        "import z\n"
        "import os\n"
        "# isort: off\n"
        "import b\n"
        "import a\n"
        "# isort: on\n"
    )
    assert isort.code(source, config=config) == (
        "# isort: dont-add-imports\n"
        "import os\n"
        "\n"
        "import z\n"
        "\n"
        "# isort: off\n"
        "import b\n"
        "import a\n"
        "# isort: on\n"
    )


@pytest.mark.depends_on("test_file_rewrites_and_returns_changed")
def test_cli_sorts_single_file_in_place(make_file, run_cli):
    path = make_file("sample.py", "import z\nimport os\n")
    result = run_cli([path])
    assert result.returncode == 0
    assert path.read_text(encoding="utf-8") == "import os\n\nimport z\n"


@pytest.mark.depends_on("test_check_file_reports_sortedness")
def test_cli_check_clean_file_returns_zero(make_file, run_cli):
    path = make_file("sample.py", "import os\n\nimport z\n")
    result = run_cli([path, "--check"])
    assert result.returncode == 0
    assert path.read_text(encoding="utf-8") == "import os\n\nimport z\n"


@pytest.mark.depends_on("test_check_file_reports_sortedness")
def test_cli_check_dirty_file_returns_one_without_write(make_file, run_cli):
    source = "import z\nimport os\n"
    path = make_file("sample.py", source)
    result = run_cli([path, "--check"])
    assert result.returncode == 1
    assert path.read_text(encoding="utf-8") == source


@pytest.mark.depends_on("test_check_file_reports_sortedness")
def test_cli_check_diff_reports_changes_without_write(make_file, run_cli):
    source = "import z\nimport os\n"
    path = make_file("sample.py", source)
    result = run_cli([path, "--check", "--diff"])
    assert result.returncode == 1
    assert "@@" in result.stdout
    assert "+import os" in result.stdout
    assert "-import os" in result.stdout
    assert path.read_text(encoding="utf-8") == source


@pytest.mark.depends_on("test_stream_writes_sorted_code_and_reports_change")
def test_cli_stdin_stdout_sorts_code(simple_unsorted, simple_sorted, run_cli):
    result = run_cli(["-", "--stdout"], input_text=simple_unsorted)
    assert result.returncode == 0
    assert result.stdout == simple_sorted


@pytest.mark.depends_on("test_check_stream_reports_sortedness")
def test_cli_stdin_check_reports_dirty_input(simple_unsorted, run_cli):
    result = run_cli(["-", "--check"], input_text=simple_unsorted)
    assert result.returncode == 1


@pytest.mark.depends_on("test_file_output_stream_returns_sorted_content_without_rewriting")
def test_cli_stdout_leaves_file_unchanged(make_file, run_cli):
    source = "import z\nimport os\n"
    path = make_file("sample.py", source)
    result = run_cli([path, "--stdout"])
    assert result.returncode == 0
    assert result.stdout == "import os\n\nimport z\n"
    assert path.read_text(encoding="utf-8") == source


@pytest.mark.depends_on("test_config_profile_black_controls_documented_values")
def test_cli_black_profile_formats_long_from_import(make_file, run_cli, long_from):
    path = make_file("sample.py", long_from)
    result = run_cli([path, "--profile", "black", "--line-length", "30"])
    assert result.returncode == 0
    assert path.read_text(encoding="utf-8") == (
        "from package import (\n"
        "    alpha,\n"
        "    beta,\n"
        "    delta,\n"
        "    gamma,\n"
        "    zeta,\n"
        ")\n"
    )


@pytest.mark.depends_on("test_place_module_with_reason_exposes_category_and_reason")
def test_cli_isort_cfg_changes_sectioning(tmp_path, run_cli):
    path = tmp_path / "sample.py"
    path.write_text("import z\nimport app\n", encoding="utf-8")
    (tmp_path / ".isort.cfg").write_text("[settings]\nknown_first_party=app\n", encoding="utf-8")
    result = run_cli([path])
    assert result.returncode == 0
    assert path.read_text(encoding="utf-8") == "import z\n\nimport app\n"


@pytest.mark.depends_on("test_place_module_with_reason_exposes_category_and_reason")
def test_cli_pyproject_changes_sectioning(tmp_path, run_cli):
    path = tmp_path / "sample.py"
    path.write_text("import z\nimport app\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        '[tool.isort]\nknown_first_party=["app"]\n',
        encoding="utf-8",
    )
    result = run_cli([path])
    assert result.returncode == 0
    assert path.read_text(encoding="utf-8") == "import z\n\nimport app\n"


@pytest.mark.depends_on("test_place_module_with_reason_exposes_category_and_reason")
def test_cli_setup_cfg_changes_sectioning(tmp_path, run_cli):
    path = tmp_path / "sample.py"
    path.write_text("import z\nimport app\n", encoding="utf-8")
    (tmp_path / "setup.cfg").write_text("[isort]\nknown_first_party=app\n", encoding="utf-8")
    result = run_cli([path])
    assert result.returncode == 0
    assert path.read_text(encoding="utf-8") == "import z\n\nimport app\n"


@pytest.mark.depends_on("test_place_module_with_reason_exposes_category_and_reason")
def test_cli_tox_ini_changes_sectioning(tmp_path, run_cli):
    path = tmp_path / "sample.py"
    path.write_text("import z\nimport app\n", encoding="utf-8")
    (tmp_path / "tox.ini").write_text("[isort]\nknown_first_party=app\n", encoding="utf-8")
    result = run_cli([path])
    assert result.returncode == 0
    assert path.read_text(encoding="utf-8") == "import z\n\nimport app\n"


@pytest.mark.depends_on("test_place_module_with_reason_exposes_category_and_reason")
def test_cli_editorconfig_changes_sectioning(tmp_path, run_cli):
    path = tmp_path / "sample.py"
    path.write_text("import z\nimport app\n", encoding="utf-8")
    (tmp_path / ".editorconfig").write_text(
        "root = true\n\n[*.py]\nknown_first_party = app\n",
        encoding="utf-8",
    )
    result = run_cli([path])
    assert result.returncode == 0
    assert path.read_text(encoding="utf-8") == "import z\n\nimport app\n"


@pytest.mark.depends_on("test_place_module_with_reason_exposes_category_and_reason")
def test_cli_settings_path_uses_custom_file(tmp_path, run_cli):
    path = tmp_path / "sample.py"
    settings = tmp_path / "custom.ini"
    path.write_text("import z\nimport app\n", encoding="utf-8")
    settings.write_text("[isort]\nknown_first_party=app\n", encoding="utf-8")
    result = run_cli([path, "--settings-path", settings])
    assert result.returncode == 0
    assert path.read_text(encoding="utf-8") == "import z\n\nimport app\n"


@pytest.mark.depends_on("test_place_module_with_reason_exposes_category_and_reason")
def test_cli_nearest_config_wins_for_nested_file(tmp_path, run_cli):
    (tmp_path / ".isort.cfg").write_text("[settings]\nknown_first_party=app\n", encoding="utf-8")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / ".isort.cfg").write_text("[settings]\nknown_third_party=app\n", encoding="utf-8")
    path = nested / "sample.py"
    path.write_text("import z\nimport app\n", encoding="utf-8")
    result = run_cli([path])
    assert result.returncode == 0
    assert path.read_text(encoding="utf-8") == "import app\nimport z\n"


@pytest.mark.depends_on("test_config_custom_section_places_known_module")
def test_cli_custom_sections_create_named_group(tmp_path, run_cli):
    path = tmp_path / "sample.py"
    path.write_text("import z\nimport django\nimport os\n", encoding="utf-8")
    (tmp_path / ".isort.cfg").write_text(
        "[settings]\n"
        "known_django=django\n"
        "sections=FUTURE,STDLIB,DJANGO,THIRDPARTY,FIRSTPARTY,LOCALFOLDER\n",
        encoding="utf-8",
    )
    result = run_cli([path])
    assert result.returncode == 0
    assert path.read_text(encoding="utf-8") == "import os\n\nimport django\n\nimport z\n"


@pytest.mark.depends_on("test_off_and_on_comments_preserve_only_the_disabled_block")
def test_cli_action_comments_preserve_off_block_and_sort_rest(make_file, run_cli):
    source = (
        "import z\n"
        "import y\n"
        "# isort: off\n"
        "import b\n"
        "import a\n"
        "# isort: on\n"
        "import d\n"
        "import c\n"
    )
    path = make_file("sample.py", source)
    result = run_cli([path])
    assert result.returncode == 0
    assert path.read_text(encoding="utf-8") == (
        "import y\n"
        "import z\n"
        "\n"
        "# isort: off\n"
        "import b\n"
        "import a\n"
        "# isort: on\n"
        "import c\n"
        "import d\n"
    )


@pytest.mark.depends_on("test_inline_skip_comment_preserves_the_marked_import")
def test_cli_skip_file_comment_accepts_unsorted_file(make_file, run_cli):
    source = "# isort: skip_file\nimport z\nimport os\n"
    path = make_file("sample.py", source)
    result = run_cli([path, "--check"])
    assert result.returncode == 0
    assert path.read_text(encoding="utf-8") == source


@pytest.mark.depends_on("test_check_file_reports_sortedness")
def test_cli_explicit_skip_requires_filter_files(make_file, run_cli):
    source = "import z\nimport os\n"
    path = make_file("sample.py", source)
    result = run_cli([path, "--check", "--skip", path.name, "--filter-files"])
    assert result.returncode == 0
    assert path.read_text(encoding="utf-8") == source


@pytest.mark.depends_on("test_check_file_reports_sortedness")
def test_cli_skip_glob_skips_matching_file(make_file, run_cli):
    source = "import z\nimport os\n"
    path = make_file("readme.py", source)
    result = run_cli([path, "--check", "--skip-glob", "*readme.py", "--filter-files"])
    assert result.returncode == 0
    assert path.read_text(encoding="utf-8") == source


@pytest.mark.depends_on("test_config_add_and_remove_imports_transform_code")
def test_cli_add_and_remove_imports_update_file(make_file, run_cli):
    path = make_file("sample.py", "import z\nimport json\n")
    result = run_cli([path, "--add-import", "import sys", "--remove-import", "json"])
    assert result.returncode == 0
    assert path.read_text(encoding="utf-8") == "import sys\n\nimport z\n"


@pytest.mark.depends_on("test_config_add_and_remove_imports_transform_code")
def test_cli_append_only_and_force_adds_have_distinct_effects(make_file, run_cli):
    append_path = make_file("append.py", "value = 1\n")
    force_path = make_file("force.py", "value = 1\n")
    append_result = run_cli([append_path, "--add-import", "import os", "--append-only"])
    force_result = run_cli([force_path, "--add-import", "import os", "--force-adds"])
    assert append_result.returncode == 0
    assert force_result.returncode == 0
    assert append_path.read_text(encoding="utf-8") == "value = 1\n"
    assert force_path.read_text(encoding="utf-8") == "import os\n\nvalue = 1\n"


@pytest.mark.depends_on("test_place_module_identifies_standard_library", "test_place_module_with_reason_exposes_category_and_reason")
def test_cli_source_path_places_project_module(tmp_path, run_cli):
    source_root = tmp_path / "src"
    (source_root / "app").mkdir(parents=True)
    (source_root / "app" / "__init__.py").write_text("", encoding="utf-8")
    path = tmp_path / "sample.py"
    path.write_text("import z\nimport app\n", encoding="utf-8")
    result = run_cli([path, "--src", source_root])
    assert result.returncode == 0
    assert path.read_text(encoding="utf-8") == "import z\n\nimport app\n"


@pytest.mark.depends_on("test_vertical_hanging_output_mode_wraps_long_import")
def test_cli_multiline_mode_matches_api_projection(make_file, run_cli, long_from):
    path = make_file("sample.py", long_from)
    result = run_cli(
        [path, "--multi-line", "3", "--line-length", "30", "--trailing-comma"]
    )
    assert result.returncode == 0
    assert path.read_text(encoding="utf-8") == (
        "from package import (\n"
        "    alpha,\n"
        "    beta,\n"
        "    delta,\n"
        "    gamma,\n"
        "    zeta,\n"
        ")\n"
    )


@pytest.mark.depends_on("test_force_single_line_splits_from_import")
def test_cli_force_single_line_matches_documented_mode(make_file, run_cli):
    path = make_file("sample.py", "from package import b, a\n")
    result = run_cli([path, "--force-single-line-imports"])
    assert result.returncode == 0
    assert path.read_text(encoding="utf-8") == (
        "from package import a\nfrom package import b\n"
    )
