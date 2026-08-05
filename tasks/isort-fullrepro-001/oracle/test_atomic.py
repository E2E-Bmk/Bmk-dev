from __future__ import annotations

from io import StringIO
from pathlib import Path

import isort
import pytest


def test_public_exports_are_available():
    for name in (
        "code",
        "check_code",
        "stream",
        "check_stream",
        "file",
        "check_file",
        "find_imports_in_code",
        "find_imports_in_stream",
        "find_imports_in_file",
        "find_imports_in_paths",
        "place_module",
        "place_module_with_reason",
    ):
        assert callable(getattr(isort, name))
    assert isort.Config is not None
    keys = tuple(
        getattr(isort.ImportKey, name)
        for name in ("PACKAGE", "MODULE", "ATTRIBUTE", "ALIAS")
    )
    assert all(keys)
    assert len(set(keys)) == 4


def test_code_sorts_stdlib_and_third_party_sections(unsorted_code, sorted_code, base_config):
    assert isort.code(unsorted_code, config=base_config) == sorted_code


def test_code_sorts_from_import_members(base_config):
    assert isort.code("from package import zeta, alpha\n", config=base_config) == (
        "from package import alpha, zeta\n"
    )


def test_check_code_reports_sortedness(simple_unsorted, simple_sorted, base_config):
    assert isort.check_code(simple_unsorted, config=base_config) is False
    assert isort.check_code(simple_sorted, config=base_config) is True


def test_stream_writes_sorted_code_and_reports_change(simple_unsorted, base_config):
    output = StringIO()
    changed = isort.stream(StringIO(simple_unsorted), output, config=base_config)
    assert changed is True
    assert output.getvalue() == "import os\n\nimport z\n"


def test_check_stream_reports_sortedness(simple_unsorted, simple_sorted, base_config):
    assert isort.check_stream(StringIO(simple_unsorted), config=base_config) is False
    assert isort.check_stream(StringIO(simple_sorted), config=base_config) is True


def test_file_rewrites_and_returns_changed(make_file, base_config):
    path = make_file("sample.py", "import z\nimport os\n")
    assert isort.file(path, config=base_config) is True
    assert path.read_text(encoding="utf-8") == "import os\n\nimport z\n"


def test_check_file_reports_sortedness(make_file, base_config):
    unsorted_path = make_file("unsorted.py", "import z\nimport os\n")
    sorted_path = make_file("sorted.py", "import os\n\nimport z\n")
    assert isort.check_file(unsorted_path, config=base_config) is False
    assert isort.check_file(sorted_path, config=base_config) is True


def test_place_module_identifies_standard_library(base_config):
    assert isort.place_module("os", base_config) == "STDLIB"


def test_place_module_identifies_relative_import(base_config):
    assert isort.place_module(".local", base_config) == "LOCALFOLDER"


def test_place_module_with_reason_exposes_category_and_reason():
    config = isort.Config(known_first_party=["app"])
    section, reason = isort.place_module_with_reason("app.client", config)
    assert section == "FIRSTPARTY"
    assert isinstance(reason, str)
    assert reason


def test_config_profile_black_controls_documented_values():
    config = isort.Config(profile="black")
    assert config.line_length == 88
    assert config.multi_line_output.name == "VERTICAL_HANGING_INDENT"
    assert config.include_trailing_comma is True
    assert config.use_parentheses is True


def test_config_custom_section_places_known_module():
    config = isort.Config(
        known_django=["django"],
        sections=("FUTURE", "STDLIB", "DJANGO", "THIRDPARTY", "FIRSTPARTY", "LOCALFOLDER"),
    )
    assert isort.place_module("django.forms", config) == "DJANGO"


def test_config_add_and_remove_imports_transform_code(base_config):
    config = isort.Config(add_imports=["import sys"], remove_imports=["json"])
    source = "import os\nimport json\n"
    assert isort.code(source, config=config) == "import os\nimport sys\n"


def test_force_to_top_moves_named_import():
    config = isort.Config(force_to_top=["sys"])
    source = "import os\nimport sys\n"
    assert isort.code(source, config=config) == "import sys\nimport os\n"


def test_no_sections_merges_import_groups():
    config = isort.Config(no_sections=True)
    assert isort.code("import z\nimport os\n", config=config) == "import os\nimport z\n"


def test_from_first_orders_from_import_before_straight_import():
    config = isort.Config(from_first=True)
    source = "import b\nfrom a import a\n"
    assert isort.code(source, config=config) == "from a import a\nimport b\n"


def test_force_single_line_splits_from_import():
    config = isort.Config(force_single_line=True)
    source = "from package import b, a\n"
    assert isort.code(source, config=config) == (
        "from package import a\nfrom package import b\n"
    )


def test_length_sort_orders_shorter_modules_first():
    config = isort.Config(length_sort=True)
    source = "import verylongmodule\nimport os\n"
    assert isort.code(source, config=config) == "import os\n\nimport verylongmodule\n"


def test_import_heading_is_added_to_its_section():
    config = isort.Config(import_heading_stdlib="Standard Library")
    source = "import z\nimport os\n"
    assert isort.code(source, config=config) == (
        "# Standard Library\nimport os\n\nimport z\n"
    )


def test_vertical_hanging_output_mode_wraps_long_import():
    config = isort.Config(
        line_length=30,
        multi_line_output=3,
        include_trailing_comma=True,
        use_parentheses=True,
    )
    assert isort.code("from package import zeta, alpha, beta, gamma, delta\n", config=config) == (
        "from package import (\n"
        "    alpha,\n"
        "    beta,\n"
        "    delta,\n"
        "    gamma,\n"
        "    zeta,\n"
        ")\n"
    )


def test_inline_skip_comment_preserves_the_marked_import(base_config):
    source = "import z\nimport a  # isort: skip\n"
    assert isort.code(source, config=base_config) == (
        "import z\n\nimport a  # isort: skip\n"
    )


def test_off_and_on_comments_preserve_only_the_disabled_block(base_config):
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
    assert isort.code(source, config=base_config) == (
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


def test_split_comment_starts_a_new_import_group(base_config):
    source = "import z\nimport y\n# isort: split\nimport b\nimport a\n"
    assert isort.code(source, config=base_config) == (
        "import y\n"
        "import z\n"
        "\n"
        "# isort: split\n"
        "import a\n"
        "import b\n"
    )


def test_no_inline_sort_preserves_member_order():
    config = isort.Config(no_inline_sort=True)
    assert isort.code("from package import b, a\n", config=config) == (
        "from package import b, a\n"
    )


def test_find_imports_in_code_returns_all_imports(base_config):
    source = "import os\nfrom package import value\nimport os\n\ndef f():\n    import nested\n"
    assert len(list(isort.find_imports_in_code(source, config=base_config))) == 4


def test_find_imports_unique_by_module_removes_duplicate_module_entries(base_config):
    source = "from package import a\nfrom package import b\nimport os\n"
    imports = list(
        isort.find_imports_in_code(
            source,
            config=base_config,
            unique=isort.ImportKey.MODULE,
        )
    )
    assert len(imports) == 2


def test_find_imports_top_only_excludes_nested_imports(base_config):
    source = "import os\nfrom package import value\n\ndef f():\n    import nested\n"
    imports = list(
        isort.find_imports_in_code(source, config=base_config, top_only=True)
    )
    assert len(imports) == 2


def test_find_imports_in_stream_reads_the_given_stream(base_config):
    source = "import os\nimport sys\n"
    assert len(list(isort.find_imports_in_stream(StringIO(source), config=base_config))) == 2


def test_find_imports_in_file_reads_a_source_file(make_file, base_config):
    path = make_file("imports.py", "import os\nimport sys\n")
    assert len(list(isort.find_imports_in_file(path, config=base_config))) == 2


def test_find_imports_in_paths_walks_python_files(tmp_path, base_config):
    package = tmp_path / "package"
    package.mkdir()
    (package / "first.py").write_text("import os\n", encoding="utf-8")
    (package / "second.py").write_text("import sys\n", encoding="utf-8")
    imports = list(isort.find_imports_in_paths(iter([package]), config=base_config))
    assert len(imports) == 2


def test_file_output_stream_returns_sorted_content_without_rewriting(make_file, base_config):
    path = make_file("sample.py", "import z\nimport os\n")
    output = StringIO()
    assert isort.file(path, config=base_config, output=output) is True
    assert output.getvalue() == "import os\n\nimport z\n"
    assert path.read_text(encoding="utf-8") == "import z\nimport os\n"
