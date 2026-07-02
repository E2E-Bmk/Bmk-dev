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


def test_run_copy_renders_file_contents_and_paths(tmp_path: Path):
    from copier import run_copy

    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree(
        {
            src / "copier.yml": "project:\n  type: str\n  default: Demo\npackage:\n  type: str\n  default: demo_pkg\n",
            src / "{{ package }}/__init__.py.jinja": "__name__ = {{ project|tojson }}\n",
            src / "README.md.jinja": "# {{ project }}\n",
            src / "{{ _copier_conf.answers_file }}.jinja": answers_file_template(),
        }
    )

    run_copy(str(src), dst, data={"project": "Billing", "package": "billing"}, defaults=True)

    assert (dst / "billing" / "__init__.py").read_text(encoding="utf-8") == '__name__ = "Billing"\n'
    assert (dst / "README.md").read_text(encoding="utf-8") == "# Billing\n"
    recorded = read_yaml(dst / ".copier-answers.yml")
    assert recorded["project"] == "Billing"
    assert recorded["package"] == "billing"


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


def test_settings_defaults_are_used_when_defaults_mode_is_enabled(tmp_path: Path):
    from copier import Settings, run_copy

    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree(
        {
            src / "copier.yml": "project:\n  type: str\n  default: Builtin\n",
            src / "name.txt.jinja": "{{ project }}\n",
            src / "{{ _copier_conf.answers_file }}.jinja": answers_file_template(),
        }
    )

    run_copy(str(src), dst, defaults=True, settings=Settings(defaults={"project": "FromSettings"}))

    assert (dst / "name.txt").read_text(encoding="utf-8") == "FromSettings\n"


def test_custom_answers_file_path_is_used_for_recorded_answers(tmp_path: Path):
    from copier import run_copy

    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree(
        {
            src / "copier.yml": "_answers_file: .custom-answers.yml\nname:\n  type: str\n  default: One\n",
            src / "name.txt.jinja": "{{ name }}\n",
            src / "{{ _copier_conf.answers_file }}.jinja": answers_file_template(),
        }
    )

    run_copy(str(src), dst, data={"name": "Two"}, defaults=True)

    assert not (dst / ".copier-answers.yml").exists()
    assert read_yaml(dst / ".custom-answers.yml")["name"] == "Two"


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


def test_skip_if_exists_preserves_existing_destination_file(tmp_path: Path):
    from copier import run_copy

    src = tmp_path / "template"
    dst = tmp_path / "project"
    dst.mkdir()
    (dst / "keep.txt").write_text("local\n", encoding="utf-8")
    build_tree({src / "copier.yml": "_skip_if_exists:\n  - keep.txt\n", src / "keep.txt": "template\n"})

    run_copy(str(src), dst, defaults=True)

    assert (dst / "keep.txt").read_text(encoding="utf-8") == "local\n"


def test_force_overwrites_existing_destination_file(tmp_path: Path):
    from copier import run_copy

    src = tmp_path / "template"
    dst = tmp_path / "project"
    dst.mkdir()
    (dst / "file.txt").write_text("local\n", encoding="utf-8")
    build_tree({src / "copier.yml": "", src / "file.txt": "template\n"})

    run_copy(str(src), dst, defaults=True, overwrite=True)

    assert (dst / "file.txt").read_text(encoding="utf-8") == "template\n"


def test_jinja_environment_settings_change_template_syntax(tmp_path: Path):
    from copier import run_copy

    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree(
        {
            src
            / "copier.yml": """
                _envops:
                  variable_start_string: "[["
                  variable_end_string: "]]"
                name:
                  type: str
                  default: EnvOps
                """,
            src / "value.txt.jinja": "[[ name ]]\n",
        }
    )

    run_copy(str(src), dst, defaults=True)

    assert (dst / "value.txt").read_text(encoding="utf-8") == "EnvOps\n"


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


def test_secret_answer_can_render_but_is_not_recorded(tmp_path: Path):
    from copier import run_copy

    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree(
        {
            src / "copier.yml": "token:\n  type: str\n  secret: true\n  default: hidden\n",
            src / "visible.txt.jinja": "{{ token }}\n",
            src / "{{ _copier_conf.answers_file }}.jinja": answers_file_template(),
        }
    )

    run_copy(str(src), dst, defaults=True)

    assert (dst / "visible.txt").read_text(encoding="utf-8") == "hidden\n"
    assert "token" not in read_yaml(dst / ".copier-answers.yml")


def test_subdirectory_template_root_only_copies_that_tree(tmp_path: Path):
    from copier import run_copy

    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree(
        {
            src / "copier.yml": "_subdirectory: sub\n",
            src / "outside.txt": "outside\n",
            src / "sub" / "inside.txt": "inside\n",
        }
    )

    run_copy(str(src), dst, defaults=True)

    assert (dst / "inside.txt").read_text(encoding="utf-8") == "inside\n"
    assert not (dst / "outside.txt").exists()


def test_task_runs_when_template_is_trusted(tmp_path: Path):
    from copier import run_copy

    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree(
        {
            src
            / "copier.yml": """
                _tasks:
                  - "{{ _copier_python }} -c \\"from pathlib import Path; Path('task-ran.txt').write_text('ok', encoding='utf-8')\\""
                """,
            src / "base.txt": "base\n",
        }
    )

    run_copy(str(src), dst, defaults=True, unsafe=True)

    assert (dst / "task-ran.txt").read_text(encoding="utf-8") == "ok"


def test_skip_tasks_avoids_running_trusted_tasks(tmp_path: Path):
    from copier import run_copy

    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree(
        {
            src
            / "copier.yml": """
                _tasks:
                  - "{{ _copier_python }} -c \\"from pathlib import Path; Path('task-ran.txt').write_text('ok', encoding='utf-8')\\""
                """,
            src / "base.txt": "base\n",
        }
    )

    run_copy(str(src), dst, defaults=True, unsafe=True, skip_tasks=True)

    assert not (dst / "task-ran.txt").exists()
    assert (dst / "base.txt").read_text(encoding="utf-8") == "base\n"


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


def test_cli_copy_with_defaults_renders_template(tmp_path: Path):
    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree(
        {
            src / "copier.yml": "name:\n  type: str\n  default: Cli\n",
            src / "value.txt.jinja": "{{ name }}\n",
            src / "{{ _copier_conf.answers_file }}.jinja": answers_file_template(),
        }
    )

    result = subprocess.run(
        [sys.executable, "-m", "copier", "copy", "--defaults", str(src), str(dst)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (dst / "value.txt").read_text(encoding="utf-8") == "Cli\n"


def test_cli_data_overrides_default(tmp_path: Path):
    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree(
        {
            src / "copier.yml": "name:\n  type: str\n  default: Default\n",
            src / "value.txt.jinja": "{{ name }}\n",
        }
    )

    result = subprocess.run(
        [sys.executable, "-m", "copier", "copy", "--defaults", "--data=name=FromCli", str(src), str(dst)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (dst / "value.txt").read_text(encoding="utf-8") == "FromCli\n"


def test_cli_data_file_is_used_for_answers(tmp_path: Path):
    src = tmp_path / "template"
    dst = tmp_path / "project"
    data_file = tmp_path / "answers.yml"
    data_file.write_text("name: FromFile\n", encoding="utf-8")
    build_tree(
        {
            src / "copier.yml": "name:\n  type: str\n  default: Default\n",
            src / "value.txt.jinja": "{{ name }}\n",
        }
    )

    result = subprocess.run(
        [sys.executable, "-m", "copier", "copy", "--defaults", f"--data-file={data_file}", str(src), str(dst)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (dst / "value.txt").read_text(encoding="utf-8") == "FromFile\n"


def test_cli_data_takes_precedence_over_data_file(tmp_path: Path):
    src = tmp_path / "template"
    dst = tmp_path / "project"
    data_file = tmp_path / "answers.yml"
    data_file.write_text("name: FromFile\n", encoding="utf-8")
    build_tree({src / "copier.yml": "name:\n  type: str\n  default: Default\n", src / "value.txt.jinja": "{{ name }}\n"})

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "copier",
            "copy",
            "--defaults",
            f"--data-file={data_file}",
            "--data=name=FromCli",
            str(src),
            str(dst),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (dst / "value.txt").read_text(encoding="utf-8") == "FromCli\n"


def test_cli_force_overwrites_existing_file(tmp_path: Path):
    src = tmp_path / "template"
    dst = tmp_path / "project"
    dst.mkdir()
    (dst / "file.txt").write_text("local\n", encoding="utf-8")
    build_tree({src / "copier.yml": "", src / "file.txt": "template\n"})

    result = subprocess.run(
        [sys.executable, "-m", "copier", "copy", "--force", str(src), str(dst)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (dst / "file.txt").read_text(encoding="utf-8") == "template\n"


def test_cli_refuses_unsafe_task_without_trust_exit_4(tmp_path: Path):
    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree(
        {
            src / "copier.yml": "_tasks:\n  - echo unsafe\n",
            src / "base.txt": "base\n",
        }
    )

    result = subprocess.run(
        [sys.executable, "-m", "copier", "copy", "--defaults", str(src), str(dst)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 4
    assert not (dst / "base.txt").exists()


def test_question_type_int_parses_api_data(tmp_path: Path):
    from copier import run_copy

    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree({src / "copier.yml": "count:\n  type: int\n  default: 1\n", src / "value.txt.jinja": "{{ count + 2 }}\n"})

    run_copy(str(src), dst, data={"count": "5"}, defaults=True)

    assert (dst / "value.txt").read_text(encoding="utf-8") == "7\n"


def test_question_type_bool_parses_cli_data(tmp_path: Path):
    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree({src / "copier.yml": "flag:\n  type: bool\n  default: false\n", src / "value.txt.jinja": "{{ flag|tojson }}\n"})

    result = subprocess.run(
        [sys.executable, "-m", "copier", "copy", "--defaults", "--data=flag=true", str(src), str(dst)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (dst / "value.txt").read_text(encoding="utf-8") == "true\n"


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


def test_pretend_copy_leaves_destination_unchanged(tmp_path: Path):
    from copier import run_copy

    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree({src / "copier.yml": "name:\n  type: str\n  default: Pretend\n", src / "value.txt.jinja": "{{ name }}\n"})

    run_copy(str(src), dst, defaults=True, pretend=True)

    assert not dst.exists()


def test_custom_answers_file_argument_overrides_template_setting(tmp_path: Path):
    from copier import run_copy

    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree(
        {
            src / "copier.yml": "_answers_file: .template-answers.yml\nname:\n  type: str\n  default: Custom\n",
            src / "value.txt.jinja": "{{ name }}\n",
            src / "{{ _copier_conf.answers_file }}.jinja": answers_file_template(),
        }
    )

    run_copy(str(src), dst, defaults=True, answers_file=".api-answers.yml")

    assert (dst / ".api-answers.yml").exists()
    assert not (dst / ".template-answers.yml").exists()


def test_run_recopy_reuses_recorded_source_and_answers(tmp_path: Path):
    from copier import run_copy, run_recopy

    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree(
        {
            src / "copier.yml": "name:\n  type: str\n  default: First\n",
            src / "value.txt.jinja": "{{ name }}\n",
            src / "{{ _copier_conf.answers_file }}.jinja": answers_file_template(),
        }
    )
    run_copy(str(src), dst, data={"name": "Recorded"}, defaults=True)
    (src / "extra.txt.jinja").write_text("{{ name }} again\n", encoding="utf-8")

    run_recopy(dst, defaults=True, overwrite=True)

    assert (dst / "value.txt").read_text(encoding="utf-8") == "Recorded\n"
    assert (dst / "extra.txt").read_text(encoding="utf-8") == "Recorded again\n"


def test_run_recopy_data_overrides_recorded_answers(tmp_path: Path):
    from copier import run_copy, run_recopy

    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree(
        {
            src / "copier.yml": "name:\n  type: str\n  default: First\n",
            src / "value.txt.jinja": "{{ name }}\n",
            src / "{{ _copier_conf.answers_file }}.jinja": answers_file_template(),
        }
    )
    run_copy(str(src), dst, data={"name": "Old"}, defaults=True)

    run_recopy(dst, data={"name": "New"}, defaults=True, overwrite=True)

    assert (dst / "value.txt").read_text(encoding="utf-8") == "New\n"
    assert read_yaml(dst / ".copier-answers.yml")["name"] == "New"


def test_run_recopy_pretend_leaves_project_files_unchanged(tmp_path: Path):
    from copier import run_copy, run_recopy

    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree(
        {
            src / "copier.yml": "name:\n  type: str\n  default: First\n",
            src / "value.txt.jinja": "{{ name }}\n",
            src / "{{ _copier_conf.answers_file }}.jinja": answers_file_template(),
        }
    )
    run_copy(str(src), dst, defaults=True)
    (src / "value.txt.jinja").write_text("changed\n", encoding="utf-8")

    run_recopy(dst, defaults=True, overwrite=True, pretend=True)

    assert (dst / "value.txt").read_text(encoding="utf-8") == "First\n"


def test_cli_recopy_reuses_answers_file(tmp_path: Path):
    from copier import run_copy

    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree(
        {
            src / "copier.yml": "name:\n  type: str\n  default: First\n",
            src / "value.txt.jinja": "{{ name }}\n",
            src / "{{ _copier_conf.answers_file }}.jinja": answers_file_template(),
        }
    )
    run_copy(str(src), dst, data={"name": "Cli"}, defaults=True)
    (src / "cli.txt.jinja").write_text("{{ name }}\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "copier", "recopy", "--defaults", "--force", str(dst)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (dst / "cli.txt").read_text(encoding="utf-8") == "Cli\n"


def test_cli_pretend_copy_does_not_create_destination(tmp_path: Path):
    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree({src / "copier.yml": "name:\n  type: str\n  default: Pretend\n", src / "value.txt.jinja": "{{ name }}\n"})

    result = subprocess.run(
        [sys.executable, "-m", "copier", "copy", "--defaults", "--pretend", str(src), str(dst)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert not dst.exists()


def test_cli_quiet_suppresses_normal_copy_output(tmp_path: Path):
    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree({src / "copier.yml": "name:\n  type: str\n  default: Quiet\n", src / "value.txt.jinja": "{{ name }}\n"})

    result = subprocess.run(
        [sys.executable, "-m", "copier", "copy", "--defaults", "--quiet", str(src), str(dst)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == ""
    assert (dst / "value.txt").read_text(encoding="utf-8") == "Quiet\n"


def test_cli_answers_file_option_controls_recorded_path(tmp_path: Path):
    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree(
        {
            src / "copier.yml": "name:\n  type: str\n  default: Answers\n",
            src / "value.txt.jinja": "{{ name }}\n",
            src / "{{ _copier_conf.answers_file }}.jinja": answers_file_template(),
        }
    )

    result = subprocess.run(
        [sys.executable, "-m", "copier", "copy", "--defaults", "--answers-file=.custom.yml", str(src), str(dst)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (dst / ".custom.yml").exists()
    assert not (dst / ".copier-answers.yml").exists()


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
    assert settings.trust == []


def test_cli_skip_option_preserves_existing_file(tmp_path: Path):
    src = tmp_path / "template"
    dst = tmp_path / "project"
    dst.mkdir()
    (dst / "keep.txt").write_text("local\n", encoding="utf-8")
    build_tree({src / "copier.yml": "", src / "keep.txt": "template\n"})

    result = subprocess.run(
        [sys.executable, "-m", "copier", "copy", "--defaults", "--skip=keep.txt", str(src), str(dst)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (dst / "keep.txt").read_text(encoding="utf-8") == "local\n"


def test_cli_exclude_option_omits_matching_file(tmp_path: Path):
    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree({src / "copier.yml": "", src / "skip.txt": "skip\n", src / "keep.txt": "keep\n"})

    result = subprocess.run(
        [sys.executable, "-m", "copier", "copy", "--defaults", "--exclude=skip.txt", str(src), str(dst)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert not (dst / "skip.txt").exists()
    assert (dst / "keep.txt").read_text(encoding="utf-8") == "keep\n"


def test_cli_no_cleanup_preserves_destination_after_error(tmp_path: Path):
    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree({src / "copier.yml": "_min_copier_version: '9999.0.0'\n", src / "value.txt": "x\n"})

    result = subprocess.run(
        [sys.executable, "-m", "copier", "copy", "--defaults", "--no-cleanup", str(src), str(dst)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--no-cleanup" not in result.stderr


def test_cli_help_lists_copy_recopy_update_and_check_update():
    result = subprocess.run(
        [sys.executable, "-m", "copier", "--help"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    for command in ["copy", "recopy", "update", "check-update"]:
        assert command in result.stdout


def test_error_namespace_exports_documented_base_classes():
    from copier.errors import CopierError, CopierWarning, TaskError, UserMessageError

    assert issubclass(TaskError, CopierError)
    assert issubclass(UserMessageError, CopierError)
    assert issubclass(CopierWarning, Warning)
