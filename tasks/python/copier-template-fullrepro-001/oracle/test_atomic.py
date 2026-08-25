"""Atomic tests for copier-template-fullrepro-001.

Each test targets ONE public API entry and ONE behavior point.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from conftest import (
    ANSWERS_FILE_ENTRY,
    ANSWERS_TEMPLATE,
    MULTI_QUESTION_YML,
    SIMPLE_COPIER_YML,
    build_template,
    read_yaml,
)


# ---------------------------------------------------------------------------
# run_copy basics
# ---------------------------------------------------------------------------


def test_run_copy_defaults_generates_destination_files(tmp_path: Path):
    """run_copy with defaults=True uses question defaults to render output."""
    from copier import run_copy

    src = build_template(
        tmp_path,
        SIMPLE_COPIER_YML,
        {"output.txt.jinja": "svc={{ billing_svc }}\n", ANSWERS_FILE_ENTRY: ANSWERS_TEMPLATE},
    )
    dst = tmp_path / "dest"

    run_copy(str(src), dst, defaults=True)

    assert (dst / "output.txt").read_text(encoding="utf-8") == "svc=payments\n"
    answers = read_yaml(dst / ".copier-answers.yml")
    assert answers["billing_svc"] == "payments"


def test_run_copy_data_overrides_default(tmp_path: Path):
    """run_copy data parameter overrides question default."""
    from copier import run_copy

    src = build_template(
        tmp_path,
        SIMPLE_COPIER_YML,
        {"output.txt.jinja": "svc={{ billing_svc }}\n", ANSWERS_FILE_ENTRY: ANSWERS_TEMPLATE},
    )
    dst = tmp_path / "dest"

    run_copy(str(src), dst, data={"billing_svc": "orders"}, defaults=True)

    assert (dst / "output.txt").read_text(encoding="utf-8") == "svc=orders\n"
    assert read_yaml(dst / ".copier-answers.yml")["billing_svc"] == "orders"


def test_run_copy_overwrite_replaces_existing_file(tmp_path: Path):
    """run_copy with overwrite=True replaces pre-existing destination files."""
    from copier import run_copy

    src = build_template(tmp_path, "", {"config.txt": "from_template\n"})
    dst = tmp_path / "dest"
    dst.mkdir()
    (dst / "config.txt").write_text("local_edit\n", encoding="utf-8")

    run_copy(str(src), dst, defaults=True, overwrite=True)

    assert (dst / "config.txt").read_text(encoding="utf-8") == "from_template\n"


def test_run_copy_pretend_does_not_create_destination(tmp_path: Path):
    """run_copy pretend=True produces no filesystem changes."""
    from copier import run_copy

    src = build_template(tmp_path, SIMPLE_COPIER_YML, {"data.txt.jinja": "{{ billing_svc }}\n"})
    dst = tmp_path / "dest"

    run_copy(str(src), dst, defaults=True, pretend=True)

    assert not dst.exists()


def test_run_copy_quiet_still_renders_correctly(tmp_path: Path):
    """run_copy quiet=True suppresses output but renders files identically."""
    from copier import run_copy

    src = build_template(
        tmp_path,
        SIMPLE_COPIER_YML,
        {"output.txt.jinja": "{{ billing_svc }}\n"},
    )
    dst = tmp_path / "dest"

    run_copy(str(src), dst, defaults=True, quiet=True)

    assert (dst / "output.txt").read_text(encoding="utf-8") == "payments\n"


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


def test_settings_empty_defaults_and_trust():
    """Settings() produces empty defaults dict and empty trust list."""
    from copier import Settings

    s = Settings()
    assert s.defaults == {}
    assert s.trust == []


def test_settings_is_frozen():
    """Settings instances are immutable (frozen dataclass)."""
    from copier import Settings

    s = Settings()
    with pytest.raises((AttributeError, TypeError)):
        s.defaults = {"x": 1}  # type: ignore[misc]


def test_settings_defaults_populates_unanswered_questions(tmp_path: Path):
    """Settings.defaults provides fallback values for questions without data."""
    from copier import Settings, run_copy

    src = build_template(
        tmp_path,
        SIMPLE_COPIER_YML,
        {"output.txt.jinja": "{{ billing_svc }}\n", ANSWERS_FILE_ENTRY: ANSWERS_TEMPLATE},
    )
    dst = tmp_path / "dest"

    run_copy(str(src), dst, defaults=True, settings=Settings(defaults={"billing_svc": "invoicing"}))

    assert (dst / "output.txt").read_text(encoding="utf-8") == "invoicing\n"


# ---------------------------------------------------------------------------
# Phase enum
# ---------------------------------------------------------------------------


def test_phase_current_returns_phase_value():
    """Phase.current() returns a Phase member."""
    from copier import Phase

    current = Phase.current()
    assert current is not None
    assert hasattr(current, "value")


def test_phase_use_temporarily_sets_phase():
    """Phase.use() context manager sets and restores phase."""
    from copier import Phase

    before = Phase.current()
    with Phase.use(Phase.RENDER):
        assert Phase.current() is Phase.RENDER
    assert Phase.current() is before


# ---------------------------------------------------------------------------
# VcsRef
# ---------------------------------------------------------------------------


def test_vcsref_current_value():
    """VcsRef.CURRENT has sentinel value ':current:'."""
    from copier import VcsRef

    assert VcsRef.CURRENT.value == ":current:"


# ---------------------------------------------------------------------------
# load_settings
# ---------------------------------------------------------------------------


def test_load_settings_missing_path_warns(tmp_path: Path, monkeypatch):
    """load_settings with non-existent COPIER_SETTINGS_PATH emits MissingSettingsWarning."""
    from copier import load_settings
    from copier.errors import MissingSettingsWarning

    monkeypatch.setenv("COPIER_SETTINGS_PATH", str(tmp_path / "nonexistent.yml"))

    with pytest.warns(MissingSettingsWarning):
        result = load_settings()

    assert result.defaults == {}
    assert result.trust == []


def test_load_settings_invalid_yaml_raises_settings_error(tmp_path: Path, monkeypatch):
    """load_settings with malformed YAML raises SettingsError."""
    from copier import load_settings
    from copier.errors import SettingsError

    bad = tmp_path / "bad.yml"
    bad.write_text("trust: [unclosed\n", encoding="utf-8")
    monkeypatch.setenv("COPIER_SETTINGS_PATH", str(bad))

    with pytest.raises(SettingsError):
        load_settings()


# ---------------------------------------------------------------------------
# Error semantics - template config
# ---------------------------------------------------------------------------


def test_multiple_config_files_raises_error(tmp_path: Path):
    """Both copier.yml and copier.yaml present raises MultipleConfigFilesError."""
    from copier import run_copy
    from copier.errors import MultipleConfigFilesError

    src = tmp_path / "tpl"
    src.mkdir()
    (src / "copier.yml").write_text("region: us\n", encoding="utf-8")
    (src / "copier.yaml").write_text("region: eu\n", encoding="utf-8")
    dst = tmp_path / "dest"

    with pytest.raises(MultipleConfigFilesError):
        run_copy(str(src), dst, defaults=True)


def test_min_copier_version_too_high_raises(tmp_path: Path):
    """_min_copier_version exceeding installed version raises UnsupportedVersionError."""
    from copier import run_copy
    from copier.errors import UnsupportedVersionError

    src = build_template(tmp_path, "_min_copier_version: '9999.1.0'\n")
    dst = tmp_path / "dest"

    with pytest.raises(UnsupportedVersionError):
        run_copy(str(src), dst, defaults=True)


def test_invalid_question_type_raises(tmp_path: Path):
    """A question with an invalid type raises InvalidTypeError."""
    from copier import run_copy
    from copier.errors import InvalidTypeError

    src = build_template(tmp_path, "item:\n  type: nosuchtype\n  default: x\n")
    dst = tmp_path / "dest"

    with pytest.raises(InvalidTypeError):
        run_copy(str(src), dst, defaults=True)


def test_unsafe_template_without_trust_raises(tmp_path: Path):
    """Template with _tasks and no trust raises UnsafeTemplateError."""
    from copier import run_copy
    from copier.errors import UnsafeTemplateError

    src = build_template(tmp_path, "_tasks:\n  - echo hello\n", {"stub.txt": "x\n"})
    dst = tmp_path / "dest"

    with pytest.raises(UnsafeTemplateError):
        run_copy(str(src), dst, defaults=True)


# ---------------------------------------------------------------------------
# Question behaviors
# ---------------------------------------------------------------------------


def test_question_when_false_not_recorded_but_default_renders(tmp_path: Path):
    """when: false skips recording but default is still in render context."""
    from copier import run_copy

    yml = (
        "enable_metrics:\n  type: bool\n  default: false\n"
        "metrics_port:\n  type: int\n  default: 9090\n  when: '{{ enable_metrics }}'\n"
    )
    src = build_template(
        tmp_path,
        yml,
        {"port.txt.jinja": "{{ metrics_port }}\n", ANSWERS_FILE_ENTRY: ANSWERS_TEMPLATE},
    )
    dst = tmp_path / "dest"

    run_copy(str(src), dst, data={"enable_metrics": False}, defaults=True)

    assert (dst / "port.txt").read_text(encoding="utf-8") == "9090\n"
    answers = read_yaml(dst / ".copier-answers.yml")
    assert "metrics_port" not in answers
    assert answers["enable_metrics"] is False


def test_secret_question_not_in_answers_file(tmp_path: Path):
    """Secret questions render but are excluded from answers file."""
    from copier import run_copy

    yml = "api_key:\n  type: str\n  secret: true\n  default: sk-abc123\n"
    src = build_template(
        tmp_path,
        yml,
        {"key.txt.jinja": "{{ api_key }}\n", ANSWERS_FILE_ENTRY: ANSWERS_TEMPLATE},
    )
    dst = tmp_path / "dest"

    run_copy(str(src), dst, defaults=True)

    assert (dst / "key.txt").read_text(encoding="utf-8") == "sk-abc123\n"
    assert "api_key" not in read_yaml(dst / ".copier-answers.yml")


def test_exclude_prevents_file_copy(tmp_path: Path):
    """_exclude patterns prevent matching files from appearing in destination."""
    from copier import run_copy

    src = build_template(
        tmp_path,
        "_exclude:\n  - '*.bak'\n",
        {"data.txt": "keep\n", "data.bak": "drop\n"},
    )
    dst = tmp_path / "dest"

    run_copy(str(src), dst, defaults=True)

    assert (dst / "data.txt").read_text(encoding="utf-8") == "keep\n"
    assert not (dst / "data.bak").exists()


def test_skip_if_exists_preserves_existing(tmp_path: Path):
    """_skip_if_exists keeps pre-existing destination file unchanged."""
    from copier import run_copy

    src = build_template(
        tmp_path,
        "_skip_if_exists:\n  - preserved.cfg\n",
        {"preserved.cfg": "template_version\n"},
    )
    dst = tmp_path / "dest"
    dst.mkdir()
    (dst / "preserved.cfg").write_text("user_edit\n", encoding="utf-8")

    run_copy(str(src), dst, defaults=True)

    assert (dst / "preserved.cfg").read_text(encoding="utf-8") == "user_edit\n"


def test_jinja_suffix_renders_and_strips(tmp_path: Path):
    """Files ending in .jinja are rendered and the suffix is stripped."""
    from copier import run_copy

    src = build_template(
        tmp_path,
        "cluster:\n  type: str\n  default: prod-east\n",
        {"info.cfg.jinja": "cluster={{ cluster }}\n"},
    )
    dst = tmp_path / "dest"

    run_copy(str(src), dst, defaults=True)

    assert (dst / "info.cfg").read_text(encoding="utf-8") == "cluster=prod-east\n"
    assert not (dst / "info.cfg.jinja").exists()


def test_subdirectory_selects_subtree(tmp_path: Path):
    """_subdirectory limits copying to the specified subdirectory."""
    from copier import run_copy

    src = build_template(
        tmp_path,
        "_subdirectory: core\n",
        {"core/main.py": "print('core')\n", "extras/plugin.py": "print('extra')\n"},
    )
    dst = tmp_path / "dest"

    run_copy(str(src), dst, defaults=True)

    assert (dst / "main.py").read_text(encoding="utf-8") == "print('core')\n"
    assert not (dst / "extras").exists()
    assert not (dst / "plugin.py").exists()


def test_envops_changes_delimiters(tmp_path: Path):
    """_envops with custom variable delimiters affects rendering."""
    from copier import run_copy

    yml = (
        "_envops:\n"
        "  variable_start_string: '<%'\n"
        "  variable_end_string: '%>'\n"
        "region_code:\n  type: str\n  default: ap-south-1\n"
    )
    src = build_template(tmp_path, yml, {"region.txt.jinja": "<% region_code %>\n"})
    dst = tmp_path / "dest"

    run_copy(str(src), dst, defaults=True)

    assert (dst / "region.txt").read_text(encoding="utf-8") == "ap-south-1\n"


def test_choices_multiselect_returns_list(tmp_path: Path):
    """A multiselect choices question returns a list value."""
    from copier import run_copy

    yml = (
        "features:\n"
        "  type: str\n"
        "  multiselect: true\n"
        "  choices:\n"
        "    - auth\n"
        "    - logging\n"
        "    - metrics\n"
        "  default:\n"
        "    - auth\n"
        "    - metrics\n"
    )
    src = build_template(
        tmp_path,
        yml,
        {"features.txt.jinja": "{{ features|tojson }}\n", ANSWERS_FILE_ENTRY: ANSWERS_TEMPLATE},
    )
    dst = tmp_path / "dest"

    run_copy(str(src), dst, defaults=True)

    import json
    result = json.loads((dst / "features.txt").read_text(encoding="utf-8"))
    assert isinstance(result, list)
    assert set(result) == {"auth", "metrics"}


# ---------------------------------------------------------------------------
# Template variables during rendering
# ---------------------------------------------------------------------------


def test_copier_phase_is_render_during_file_rendering(tmp_path: Path):
    """_copier_phase equals 'render' when template files are being rendered."""
    from copier import run_copy

    src = build_template(tmp_path, "", {"phase.txt.jinja": "{{ _copier_phase }}\n"})
    dst = tmp_path / "dest"

    run_copy(str(src), dst, defaults=True)

    assert (dst / "phase.txt").read_text(encoding="utf-8") == "render\n"


def test_copier_python_is_current_interpreter(tmp_path: Path):
    """_copier_python points to the running Python interpreter."""
    from copier import run_copy

    src = build_template(tmp_path, "", {"py.txt.jinja": "{{ _copier_python }}\n"})
    dst = tmp_path / "dest"

    run_copy(str(src), dst, defaults=True)

    assert (dst / "py.txt").read_text(encoding="utf-8").strip() == sys.executable


def test_copier_operation_is_copy(tmp_path: Path):
    """_copier_operation equals 'copy' during run_copy."""
    from copier import run_copy

    src = build_template(tmp_path, "", {"op.txt.jinja": "{{ _copier_operation }}\n"})
    dst = tmp_path / "dest"

    run_copy(str(src), dst, defaults=True)

    assert (dst / "op.txt").read_text(encoding="utf-8") == "copy\n"


def test_to_nice_yaml_filter_renders_yaml(tmp_path: Path):
    """to_nice_yaml Jinja filter produces valid YAML output."""
    from copier import run_copy

    yml = "tags:\n  type: yaml\n  default: [alpha, beta]\n"
    src = build_template(
        tmp_path,
        yml,
        {"tags.yml.jinja": "{{ tags|to_nice_yaml }}"},
    )
    dst = tmp_path / "dest"

    run_copy(str(src), dst, defaults=True)

    import yaml as _yaml
    loaded = _yaml.safe_load((dst / "tags.yml").read_text(encoding="utf-8"))
    assert loaded == ["alpha", "beta"]


def test_copier_answers_variable_contains_question_data(tmp_path: Path):
    """_copier_answers variable in Jinja context contains answered question data."""
    from copier import run_copy

    src = build_template(
        tmp_path,
        SIMPLE_COPIER_YML,
        {ANSWERS_FILE_ENTRY: ANSWERS_TEMPLATE},
    )
    dst = tmp_path / "dest"

    run_copy(str(src), dst, data={"billing_svc": "shipments"}, defaults=True)

    answers = read_yaml(dst / ".copier-answers.yml")
    assert answers["billing_svc"] == "shipments"
    assert "_src_path" in answers


# ---------------------------------------------------------------------------
# Error hierarchy
# ---------------------------------------------------------------------------


def test_error_hierarchy_base_classes():
    """Error classes follow documented inheritance."""
    from copier.errors import (
        CopierError,
        CopierWarning,
        TaskError,
        UnsafeTemplateError,
        UserMessageError,
    )

    assert issubclass(UnsafeTemplateError, CopierError)
    assert issubclass(TaskError, CopierError)
    assert issubclass(UserMessageError, CopierError)
    assert issubclass(CopierWarning, Warning)
