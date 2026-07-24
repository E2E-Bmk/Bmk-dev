# Spec2Repo oracle - atomic tests for doit-taskrunner-fullrepro-002
from pathlib import Path

import pytest

from conftest import common_actions, run_doit, write_dodo


# ---------------------------------------------------------------------------
# get_var
# ---------------------------------------------------------------------------

def test_get_var_reads_cli_variable_during_task_loading(tmp_path):
    write_dodo(
        tmp_path,
        """
        from pathlib import Path
        from doit import get_var

        COLOR = get_var("color", "red")

        def task_show():
            return {"actions": [(lambda: Path("color.txt").write_text(COLOR, encoding="utf-8") and None)]}
        """,
    )

    run_doit(tmp_path, "color=blue")

    assert (tmp_path / "color.txt").read_text(encoding="utf-8") == "blue"


def test_get_var_uses_default_for_absent_initialized_variable(tmp_path):
    write_dodo(
        tmp_path,
        """
        from pathlib import Path
        from doit import get_var

        VALUE = get_var("flavor", "vanilla")

        def task_show():
            return {"actions": [(lambda: Path("flavor.txt").write_text(VALUE, encoding="utf-8") and None)]}
        """,
    )

    run_doit(tmp_path)

    assert (tmp_path / "flavor.txt").read_text(encoding="utf-8") == "vanilla"


# ---------------------------------------------------------------------------
# task_params
# ---------------------------------------------------------------------------

def test_task_params_long_option_is_injected_into_task_creator(tmp_path):
    write_dodo(
        tmp_path,
        """
        from pathlib import Path
        from doit import task_params

        def save(path, value):
            Path(path).write_text(value, encoding="utf-8")
            return None

        @task_params([{"name": "name", "default": "Ada", "long": "name", "help": "person"}])
        def task_greet(name):
            return {"actions": [(save, ["greeting.txt", name], {})], "targets": ["greeting.txt"]}
        """,
    )

    run_doit(tmp_path, "greet", "--name", "Grace")

    assert (tmp_path / "greeting.txt").read_text(encoding="utf-8") == "Grace"


def test_task_params_short_boolean_inverse_can_disable_default(tmp_path):
    write_dodo(
        tmp_path,
        """
        from pathlib import Path

        def save(flag):
            Path("flag.txt").write_text(str(flag), encoding="utf-8")
            return None

        def task_flag():
            return {
                "actions": [(save, [], {})],
                "params": [{"name": "flag", "short": "f", "long": "flag",
                            "type": bool, "default": True, "inverse": "no-flag"}],
            }
        """,
    )

    run_doit(tmp_path, "flag", "--no-flag")

    assert (tmp_path / "flag.txt").read_text(encoding="utf-8") == "False"


# ---------------------------------------------------------------------------
# Python action parameter injection
# ---------------------------------------------------------------------------

def test_python_action_receives_declared_dependencies_and_targets(tmp_path):
    (tmp_path / "input.txt").write_text("hello", encoding="utf-8")
    write_dodo(
        tmp_path,
        common_actions()
        + """
        def task_copy():
            return {"actions": [copy_upper], "file_dep": ["input.txt"], "targets": ["output.txt"]}
        """,
    )

    run_doit(tmp_path, "copy")

    assert (tmp_path / "output.txt").read_text(encoding="utf-8") == "HELLO"


# ---------------------------------------------------------------------------
# Python action return value semantics
# ---------------------------------------------------------------------------

def test_python_action_returning_false_reports_task_failure(tmp_path):
    write_dodo(
        tmp_path,
        """
        def task_fail():
            return {"actions": [lambda: False]}
        """,
    )

    proc = run_doit(tmp_path, "fail", check=False)

    assert proc.returncode == 1


def test_python_action_exception_reports_task_error(tmp_path):
    write_dodo(
        tmp_path,
        """
        def boom():
            raise RuntimeError("boom")

        def task_error():
            return {"actions": [boom]}
        """,
    )

    proc = run_doit(tmp_path, "error", check=False)

    assert proc.returncode == 2


def test_python_action_returning_dict_succeeds(tmp_path):
    write_dodo(
        tmp_path,
        """
        def produce():
            return {"dimension": 7}

        def task_produce():
            return {"actions": [produce]}
        """,
    )

    proc = run_doit(tmp_path, "produce")

    assert proc.returncode == 0


def test_python_action_returning_string_succeeds(tmp_path):
    write_dodo(
        tmp_path,
        """
        def produce():
            return "computed-output"

        def task_produce():
            return {"actions": [produce]}
        """,
    )

    proc = run_doit(tmp_path, "produce")

    assert proc.returncode == 0


def test_python_action_returning_true_succeeds(tmp_path):
    write_dodo(
        tmp_path,
        """
        def affirm():
            return True

        def task_affirm():
            return {"actions": [affirm]}
        """,
    )

    proc = run_doit(tmp_path, "affirm")

    assert proc.returncode == 0


# ---------------------------------------------------------------------------
# Command action semantics
# ---------------------------------------------------------------------------

def test_string_command_action_creates_target_file(tmp_path):
    write_dodo(
        tmp_path,
        """
        import sys

        def task_cmd():
            return {
                "actions": [
                    f"{sys.executable} -c "
                    "\\"from pathlib import Path; "
                    "Path('cmd.txt').write_text('ok', encoding='utf-8')\\""
                ],
                "targets": ["cmd.txt"],
            }
        """,
    )

    run_doit(tmp_path, "cmd")

    assert (tmp_path / "cmd.txt").read_text(encoding="utf-8") == "ok"


def test_list_command_action_without_shell_accepts_pathlike_arguments(tmp_path):
    write_dodo(
        tmp_path,
        """
        import sys
        from pathlib import Path

        def task_cmdlist():
            return {
                "actions": [[sys.executable, "-c",
                             "from pathlib import Path; Path('listed.txt').write_text('listed', encoding='utf-8')"]],
                "targets": [Path("listed.txt")],
            }
        """,
    )

    run_doit(tmp_path, "cmdlist")

    assert (tmp_path / "listed.txt").read_text(encoding="utf-8") == "listed"


def test_command_action_nonzero_exit_reports_failure(tmp_path):
    write_dodo(
        tmp_path,
        """
        import sys

        def task_badcmd():
            return {"actions": [[sys.executable, "-c", "import sys; sys.exit(5)"]]}
        """,
    )

    proc = run_doit(tmp_path, "badcmd", check=False)

    assert proc.returncode == 1


def test_command_exit_above_125_reports_error_not_failure(tmp_path):
    write_dodo(
        tmp_path,
        """
        import sys

        def task_highexit():
            return {"actions": [[sys.executable, "-c", "import sys; sys.exit(126)"]]}
        """,
    )

    proc = run_doit(tmp_path, "highexit", check=False)

    assert proc.returncode == 2


# ---------------------------------------------------------------------------
# clean
# ---------------------------------------------------------------------------

def test_clean_callable_receives_dryrun_when_declared(tmp_path):
    write_dodo(
        tmp_path,
        """
        from pathlib import Path

        def cleanup(dryrun):
            Path("dryrun.txt").write_text(str(dryrun), encoding="utf-8")
            return None

        def task_build():
            return {
                "actions": [(lambda: Path("artifact.txt").write_text("x", encoding="utf-8") and None)],
                "clean": [cleanup],
            }
        """,
    )

    run_doit(tmp_path, "clean", "--dry-run", "build")

    assert (tmp_path / "dryrun.txt").read_text(encoding="utf-8") == "True"


# ---------------------------------------------------------------------------
# uptodate helpers
# ---------------------------------------------------------------------------

def test_config_changed_treats_same_dictionary_content_as_up_to_date(tmp_path):
    write_dodo(
        tmp_path,
        common_actions()
        + """
        from doit.tools import config_changed

        def task_cfg():
            return {"actions": [(count_run, ["count.txt"], {})],
                    "uptodate": [config_changed({"b": 2, "a": 1})]}
        """,
    )
    run_doit(tmp_path, "cfg")
    write_dodo(
        tmp_path,
        common_actions()
        + """
        from doit.tools import config_changed

        def task_cfg():
            return {"actions": [(count_run, ["count.txt"], {})],
                    "uptodate": [config_changed({"a": 1, "b": 2})]}
        """,
    )

    run_doit(tmp_path, "cfg")

    assert (tmp_path / "count.txt").read_text(encoding="utf-8") == "1"


def test_config_changed_reruns_when_configuration_changes(tmp_path):
    write_dodo(
        tmp_path,
        common_actions()
        + """
        from doit.tools import config_changed

        def task_cfg():
            return {"actions": [(count_run, ["count.txt"], {})],
                    "uptodate": [config_changed("one")]}
        """,
    )
    run_doit(tmp_path, "cfg")
    write_dodo(
        tmp_path,
        common_actions()
        + """
        from doit.tools import config_changed

        def task_cfg():
            return {"actions": [(count_run, ["count.txt"], {})],
                    "uptodate": [config_changed("two")]}
        """,
    )

    run_doit(tmp_path, "cfg")

    assert (tmp_path / "count.txt").read_text(encoding="utf-8") == "2"


def test_uptodate_false_forces_task_to_run_unconditionally(tmp_path):
    write_dodo(
        tmp_path,
        common_actions()
        + """
        def task_rerun():
            return {"actions": [(count_run, ["tally.txt"], {})], "uptodate": [False]}
        """,
    )
    run_doit(tmp_path, "rerun")
    run_doit(tmp_path, "rerun")

    assert (tmp_path / "tally.txt").read_text(encoding="utf-8") == "2"


# ---------------------------------------------------------------------------
# create_folder
# ---------------------------------------------------------------------------

def test_create_folder_action_helper_creates_nested_directory(tmp_path):
    write_dodo(
        tmp_path,
        """
        from doit.tools import create_folder

        def task_dirs():
            return {"actions": [(create_folder, ["nested/child"], {})],
                    "targets": ["nested/child"]}
        """,
    )

    run_doit(tmp_path, "dirs")

    assert (tmp_path / "nested" / "child").is_dir()


# ---------------------------------------------------------------------------
# Task naming
# ---------------------------------------------------------------------------

def test_basename_overrides_default_task_name_in_listing(tmp_path):
    write_dodo(
        tmp_path,
        """
        def task_original():
            return {"basename": "fabricate", "actions": [None]}
        """,
    )

    proc = run_doit(tmp_path, "list")

    assert "fabricate" in proc.stdout
    assert "original" not in proc.stdout.split()


def test_doc_from_docstring_used_when_no_explicit_doc_field(tmp_path):
    write_dodo(
        tmp_path,
        '''
        def task_build():
            """assemble the widget"""
            return {"actions": [None]}
        ''',
    )

    proc = run_doit(tmp_path, "list")

    assert "assemble the widget" in proc.stdout


# ---------------------------------------------------------------------------
# help / list
# ---------------------------------------------------------------------------

def test_help_task_prints_supported_task_dictionary_fields(tmp_path):
    write_dodo(tmp_path, "def task_build():\n    return {'actions': [None]}\n")

    proc = run_doit(tmp_path, "help", "task")

    assert "actions" in proc.stdout
    assert "file_dep" in proc.stdout
    assert "targets" in proc.stdout


def test_list_reports_declared_task_name(tmp_path):
    write_dodo(
        tmp_path,
        """
        def task_build():
            return {"actions": [None]}
        """,
    )

    proc = run_doit(tmp_path, "list")

    assert proc.returncode == 0
    assert "build" in proc.stdout.split()
