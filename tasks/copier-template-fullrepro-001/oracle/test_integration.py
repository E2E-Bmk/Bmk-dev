# Spec2Repo oracle - integration tests for copier-template-fullrepro-001
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
    # Invoke the documented module entry point so the test does not depend on
    # how a console-script wrapper is installed or named in the carrier.
    command = [sys.executable, "-m", "copier", *args]
    return subprocess.run(command, text=True, capture_output=True, check=False)


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

    result = run_copier_cli("copy", "--defaults", str(src), str(dst))

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

    result = run_copier_cli("copy", "--defaults", "--data=name=FromCli", str(src), str(dst))

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

    result = run_copier_cli("copy", "--defaults", f"--data-file={data_file}", str(src), str(dst))

    assert result.returncode == 0, result.stdout + result.stderr
    assert (dst / "value.txt").read_text(encoding="utf-8") == "FromFile\n"


def test_cli_data_takes_precedence_over_data_file(tmp_path: Path):
    src = tmp_path / "template"
    dst = tmp_path / "project"
    data_file = tmp_path / "answers.yml"
    data_file.write_text("name: FromFile\n", encoding="utf-8")
    build_tree({src / "copier.yml": "name:\n  type: str\n  default: Default\n", src / "value.txt.jinja": "{{ name }}\n"})

    result = run_copier_cli(
        "copy",
        "--defaults",
        f"--data-file={data_file}",
        "--data=name=FromCli",
        str(src),
        str(dst),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (dst / "value.txt").read_text(encoding="utf-8") == "FromCli\n"


def test_cli_force_overwrites_existing_file(tmp_path: Path):
    src = tmp_path / "template"
    dst = tmp_path / "project"
    dst.mkdir()
    (dst / "file.txt").write_text("local\n", encoding="utf-8")
    build_tree({src / "copier.yml": "", src / "file.txt": "template\n"})

    result = run_copier_cli("copy", "--force", str(src), str(dst))

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

    result = run_copier_cli("copy", "--defaults", str(src), str(dst))

    assert result.returncode == 4
    assert not (dst / "base.txt").exists()


def test_question_type_bool_parses_cli_data(tmp_path: Path):
    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree({src / "copier.yml": "flag:\n  type: bool\n  default: false\n", src / "value.txt.jinja": "{{ flag|tojson }}\n"})

    result = run_copier_cli("copy", "--defaults", "--data=flag=true", str(src), str(dst))

    assert result.returncode == 0, result.stdout + result.stderr
    assert (dst / "value.txt").read_text(encoding="utf-8") == "true\n"


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

    result = run_copier_cli("recopy", "--defaults", "--force", str(dst))

    assert result.returncode == 0, result.stdout + result.stderr
    assert (dst / "cli.txt").read_text(encoding="utf-8") == "Cli\n"


def test_cli_pretend_copy_does_not_create_destination(tmp_path: Path):
    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree({src / "copier.yml": "name:\n  type: str\n  default: Pretend\n", src / "value.txt.jinja": "{{ name }}\n"})

    result = run_copier_cli("copy", "--defaults", "--pretend", str(src), str(dst))

    assert result.returncode == 0, result.stdout + result.stderr
    assert not dst.exists()


def test_cli_quiet_suppresses_normal_copy_output(tmp_path: Path):
    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree({src / "copier.yml": "name:\n  type: str\n  default: Quiet\n", src / "value.txt.jinja": "{{ name }}\n"})

    result = run_copier_cli("copy", "--defaults", "--quiet", str(src), str(dst))

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

    result = run_copier_cli("copy", "--defaults", "--answers-file=.custom.yml", str(src), str(dst))

    assert result.returncode == 0, result.stdout + result.stderr
    assert (dst / ".custom.yml").exists()
    assert not (dst / ".copier-answers.yml").exists()


def test_cli_skip_option_preserves_existing_file(tmp_path: Path):
    src = tmp_path / "template"
    dst = tmp_path / "project"
    dst.mkdir()
    (dst / "keep.txt").write_text("local\n", encoding="utf-8")
    build_tree({src / "copier.yml": "", src / "keep.txt": "template\n"})

    result = run_copier_cli("copy", "--defaults", "--skip=keep.txt", str(src), str(dst))

    assert result.returncode == 0, result.stdout + result.stderr
    assert (dst / "keep.txt").read_text(encoding="utf-8") == "local\n"


def test_cli_exclude_option_omits_matching_file(tmp_path: Path):
    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree({src / "copier.yml": "", src / "skip.txt": "skip\n", src / "keep.txt": "keep\n"})

    result = run_copier_cli("copy", "--defaults", "--exclude=skip.txt", str(src), str(dst))

    assert result.returncode == 0, result.stdout + result.stderr
    assert not (dst / "skip.txt").exists()
    assert (dst / "keep.txt").read_text(encoding="utf-8") == "keep\n"


def test_cli_no_cleanup_preserves_destination_after_error(tmp_path: Path):
    src = tmp_path / "template"
    dst = tmp_path / "project"
    build_tree({src / "copier.yml": "_min_copier_version: '9999.0.0'\n", src / "value.txt": "x\n"})

    result = run_copier_cli("copy", "--defaults", "--no-cleanup", str(src), str(dst))

    assert result.returncode != 0
    assert "--no-cleanup" not in result.stderr
