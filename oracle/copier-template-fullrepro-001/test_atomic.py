# Spec2Repo oracle - atomic tests for copier-template-fullrepro-001
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml


def build_tree(entries: dict[Path, str]) -> None:
    for path, text in entries.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def answers_file_template() -> str:
    return "{{ _copier_answers|to_nice_yaml -}}\n"


def read_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def run_copier_cli(*args: str) -> subprocess.CompletedProcess[str]:
    command = ["copier", *args]
    return subprocess.run(command, text=True, capture_output=True, check=False)


def test_defaults_mode_uses_question_defaults(tmp_path: Path):
    from copier import run_copy

    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree(
        {
            src / "copier.yml": "name:\n  type: str\n  default: DefaultName\n",
            src / "value.txt.jinja": "{{ name }}\n",
            src / "{{ _copier_conf.answers_file }}.jinja": answers_file_template(),
        }
    )

    run_copy(str(src), dst, defaults=True)

    assert (dst / "value.txt").read_text(encoding="utf-8") == "DefaultName\n"
    assert read_yaml(dst / ".copier-answers.yml")["name"] == "DefaultName"


def test_api_data_overrides_template_default(tmp_path: Path):
    from copier import run_copy

    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree(
        {
            src / "copier.yml": "name:\n  type: str\n  default: Default\n",
            src / "value.txt.jinja": "{{ name }}\n",
            src / "{{ _copier_conf.answers_file }}.jinja": answers_file_template(),
        }
    )

    run_copy(str(src), dst, data={"name": "FromAPI"}, defaults=True)

    assert (dst / "value.txt").read_text(encoding="utf-8") == "FromAPI\n"
    assert read_yaml(dst / ".copier-answers.yml")["name"] == "FromAPI"


def test_exclude_omits_matching_template_files(tmp_path: Path):
    from copier import run_copy

    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree(
        {
            src / "copier.yml": "_exclude:\n  - ignored.txt\n",
            src / "ignored.txt": "ignore\n",
            src / "kept.txt": "keep\n",
        }
    )

    run_copy(str(src), dst, defaults=True)

    assert not (dst / "ignored.txt").exists()
    assert (dst / "kept.txt").read_text(encoding="utf-8") == "keep\n"


def test_multiple_config_files_raise_documented_error(tmp_path: Path):
    from copier import run_copy
    from copier.errors import MultipleConfigFilesError

    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree({src / "copier.yml": "name: Demo\n", src / "copier.yaml": "name: Demo\n"})

    with pytest.raises(MultipleConfigFilesError):
        run_copy(str(src), dst, defaults=True)


def test_minimum_version_blocks_unsupported_template(tmp_path: Path):
    from copier import run_copy
    from copier.errors import UnsupportedVersionError

    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree({src / "copier.yml": "_min_copier_version: '9999.0.0'\n"})

    with pytest.raises(UnsupportedVersionError):
        run_copy(str(src), dst, defaults=True)


def test_load_settings_reads_yaml_defaults_and_trust(tmp_path: Path, monkeypatch):
    import platformdirs
    from copier import load_settings

    config = tmp_path / "config"
    config.mkdir()
    settings = config / "settings.yml"
    settings.write_text("defaults:\n  project: FromFile\ntrust:\n  - /tmp/template\n", encoding="utf-8")
    monkeypatch.setenv("COPIER_SETTINGS_PATH", str(settings))
    monkeypatch.setattr(platformdirs, "user_config_path", lambda *args, **kwargs: config)

    loaded = load_settings()

    assert loaded.defaults["project"] == "FromFile"
    assert "/tmp/template" in loaded.trust


def test_invalid_settings_yaml_raises_settings_error(tmp_path: Path, monkeypatch):
    from copier import load_settings
    from copier.errors import SettingsError

    settings = tmp_path / "settings.yml"
    settings.write_text("defaults: [unterminated\n", encoding="utf-8")
    monkeypatch.setenv("COPIER_SETTINGS_PATH", str(settings))

    with pytest.raises(SettingsError):
        load_settings()


def test_question_type_int_parses_api_data(tmp_path: Path):
    from copier import run_copy

    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree({src / "copier.yml": "count:\n  type: int\n  default: 1\n", src / "value.txt.jinja": "{{ count + 2 }}\n"})

    run_copy(str(src), dst, data={"count": "5"}, defaults=True)

    assert (dst / "value.txt").read_text(encoding="utf-8") == "7\n"


def test_question_type_float_parses_api_data(tmp_path: Path):
    from copier import run_copy

    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree({src / "copier.yml": "amount:\n  type: float\n  default: 1.5\n", src / "value.txt.jinja": "{{ amount + 0.5 }}\n"})

    run_copy(str(src), dst, data={"amount": "2.5"}, defaults=True)

    assert (dst / "value.txt").read_text(encoding="utf-8") == "3.0\n"


def test_question_type_yaml_preserves_list_value(tmp_path: Path):
    from copier import run_copy

    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree({src / "copier.yml": "items:\n  type: yaml\n  default: []\n", src / "value.json.jinja": "{{ items|tojson }}\n"})

    run_copy(str(src), dst, data={"items": "[1, 2, 3]"}, defaults=True)

    assert json.loads((dst / "value.json").read_text(encoding="utf-8")) == [1, 2, 3]


def test_configuration_defaults_are_available_to_rendering(tmp_path: Path):
    from copier import run_copy

    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree({src / "copier.yml": "_answers_file: answers.yml\n", src / "conf.txt.jinja": "{{ _copier_conf.answers_file }}\n"})

    run_copy(str(src), dst, defaults=True)

    assert (dst / "conf.txt").read_text(encoding="utf-8") == "answers.yml\n"


def test_phase_variable_is_render_during_file_render(tmp_path: Path):
    from copier import run_copy

    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree({src / "copier.yml": "", src / "phase.txt.jinja": "{{ _copier_phase }}\n"})

    run_copy(str(src), dst, defaults=True)

    assert (dst / "phase.txt").read_text(encoding="utf-8") == "render\n"


def test_python_variable_points_to_current_interpreter(tmp_path: Path):
    from copier import run_copy

    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree({src / "copier.yml": "", src / "python.txt.jinja": "{{ _copier_python }}\n"})

    run_copy(str(src), dst, defaults=True)

    assert (dst / "python.txt").read_text(encoding="utf-8").strip() == sys.executable


def test_public_import_surface_includes_recopy_update_phase_and_vcsref():
    from copier import Phase, Settings, VcsRef, load_settings, run_copy, run_recopy, run_update

    assert callable(run_copy)
    assert callable(run_recopy)
    assert callable(run_update)
    assert callable(load_settings)
    assert Settings().defaults == {}
    assert Phase.RENDER.value == "render"
    assert VcsRef.CURRENT.value == ":current:"


def test_phase_context_manager_restores_previous_phase():
    from copier import Phase

    before = Phase.current()
    with Phase.use(Phase.RENDER):
        assert Phase.current() is Phase.RENDER
    assert Phase.current() is before


def test_vcsref_current_string_is_accepted_by_copy_api(tmp_path: Path):
    from copier import VcsRef

    assert str(VcsRef.CURRENT) == "VcsRef.CURRENT"
    assert VcsRef.CURRENT.value == ":current:"


def test_external_data_requires_trust(tmp_path: Path):
    from copier.errors import CopierError, UnsafeTemplateError

    assert issubclass(UnsafeTemplateError, CopierError)


def test_external_data_renders_when_template_is_trusted(tmp_path: Path):
    from copier import Settings

    trusted = Settings(trust=[str(tmp_path) + "/"])
    assert str(tmp_path) + "/" in trusted.trust


def test_settings_default_factory_isolated_between_instances():
    from copier import Settings

    first = Settings()
    second = Settings()

    assert first.defaults == {}
    assert second.defaults == {}
    assert first.defaults is not second.defaults


def test_load_settings_missing_env_path_returns_empty_with_warning(tmp_path: Path, monkeypatch):
    from copier import load_settings
    from copier.errors import MissingSettingsWarning

    missing = tmp_path / "missing.yml"
    monkeypatch.setenv("COPIER_SETTINGS_PATH", str(missing))

    with pytest.warns(MissingSettingsWarning):
        settings = load_settings()
    assert settings.defaults == {}
    assert len(settings.trust) == 0


def test_cli_help_lists_copy_recopy_update_and_check_update():
    result = run_copier_cli("--help")

    assert result.returncode == 0, result.stdout + result.stderr
    for command in ["copy", "recopy", "update", "check-update"]:
        assert command in result.stdout


def test_error_namespace_exports_documented_base_classes():
    from copier.errors import CopierError, CopierWarning, TaskError, UserMessageError

    assert issubclass(TaskError, CopierError)
    assert issubclass(UserMessageError, CopierError)
    assert issubclass(CopierWarning, Warning)
