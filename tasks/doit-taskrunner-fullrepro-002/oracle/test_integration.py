# Spec2Repo oracle - integration tests for doit-taskrunner-fullrepro-002
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest


def write_dodo(tmp_path, source):
    dodo = tmp_path / "dodo.py"
    dodo.write_text(textwrap.dedent(source), encoding="utf-8")
    return dodo


def doit_env():
    env = os.environ.copy()
    current = env.get("PYTHONPATH")
    entries = [str(entry) for entry in sys.path if entry]
    if current:
        entries.append(current)
    env["PYTHONPATH"] = os.pathsep.join(entries)
    return env


def run_doit(tmp_path, *args, check=True):
    proc = subprocess.run(
        [sys.executable, "-m", "doit", *args],
        cwd=tmp_path,
        env=doit_env(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and proc.returncode != 0:
        raise AssertionError(
            f"doit exited with {proc.returncode}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    return proc


def common_actions():
    return """
        from pathlib import Path

        def write_text(path, text):
            Path(path).write_text(str(text), encoding="utf-8")
            return None

        def append_text(path, text):
            with Path(path).open("a", encoding="utf-8") as stream:
                stream.write(str(text))
            return None

        def copy_upper(dependencies, targets):
            Path(targets[0]).write_text(Path(dependencies[0]).read_text(encoding="utf-8").upper(), encoding="utf-8")
            return None

        def count_run(path):
            p = Path(path)
            value = int(p.read_text(encoding="utf-8")) if p.exists() else 0
            p.write_text(str(value + 1), encoding="utf-8")
            return {"count": value + 1}
"""


def test_create_after_materializes_selected_delayed_task(tmp_path):
    write_dodo(
        tmp_path,
        common_actions()
        + """
        from pathlib import Path
        from doit import create_after

        def task_build():
            return {"actions": [(write_text, ["seed.txt", "seed"], {})], "targets": ["seed.txt"]}

        @create_after(executed="build", creates=["late"])
        def task_late():
            text = Path("seed.txt").read_text(encoding="utf-8") + "-late"
            return {"actions": [(write_text, ["late.txt", text], {})], "file_dep": ["seed.txt"], "targets": ["late.txt"]}
        """,
    )

    proc = run_doit(tmp_path, "late")

    assert ".  build" in proc.stdout
    assert ".  late" in proc.stdout
    assert (tmp_path / "late.txt").read_text(encoding="utf-8") == "seed-late"


def test_module_task_loader_runs_dictionary_namespace_with_doitmain(tmp_path):
    cwd = os.getcwd()
    from doit.cmd_base import ModuleTaskLoader
    from doit.doit_cmd import DoitMain

    def write_marker(targets):
        Path(targets[0]).write_text("loaded", encoding="utf-8")
        return None

    def task_build():
        return {"actions": [(write_marker,)], "targets": [str(tmp_path / "module.txt")]}

    try:
        os.chdir(tmp_path)
        result = DoitMain(ModuleTaskLoader({"task_build": task_build})).run(["run"])
    finally:
        os.chdir(cwd)

    assert result == 0
    assert (tmp_path / "module.txt").read_text(encoding="utf-8") == "loaded"


def test_generator_subtasks_are_runnable_and_visible_when_requested(tmp_path):
    write_dodo(
        tmp_path,
        common_actions()
        + """
        def task_piece():
            for name in ["a", "b"]:
                yield {"name": name, "actions": [(write_text, [f"{name}.txt", name], {})], "targets": [f"{name}.txt"]}
        """,
    )

    listing = run_doit(tmp_path, "list", "--all").stdout
    run_doit(tmp_path, "piece:a")

    assert "piece:a" in listing
    assert (tmp_path / "a.txt").read_text(encoding="utf-8") == "a"
    assert not (tmp_path / "b.txt").exists()


def test_invalid_task_dictionary_returns_command_error_without_running(tmp_path):
    write_dodo(
        tmp_path,
        """
        def task_bad():
            return {"actions": [], "unexpected": True}
        """,
    )

    proc = run_doit(tmp_path, "bad", check=False)

    assert proc.returncode == 3
    assert "bad" in proc.stderr or "bad" in proc.stdout


def test_python_action_dictionary_result_feeds_getargs(tmp_path):
    write_dodo(
        tmp_path,
        common_actions()
        + """
        from pathlib import Path

        def produce():
            return {"answer": 42}

        def consume(answer, targets):
            Path(targets[0]).write_text(str(answer), encoding="utf-8")
            return None

        def task_produce():
            return {"actions": [produce]}

        def task_consume():
            return {"actions": [(consume, [], {})], "getargs": {"answer": ("produce", "answer")}, "targets": ["answer.txt"]}
        """,
    )

    run_doit(tmp_path, "consume")

    assert (tmp_path / "answer.txt").read_text(encoding="utf-8") == "42"


def test_cmdaction_save_out_stores_stdout_for_later_getargs(tmp_path):
    write_dodo(
        tmp_path,
        """
        import sys
        from pathlib import Path
        from doit.action import CmdAction

        def consume(word, targets):
            Path(targets[0]).write_text(word.strip(), encoding="utf-8")
            return None

        def task_emit():
            return {"actions": [CmdAction([sys.executable, "-c", "print('captured')"], save_out="word")]}

        def task_use():
            return {"actions": [(consume, [], {})], "getargs": {"word": ("emit", "word")}, "targets": ["captured.txt"]}
        """,
    )

    run_doit(tmp_path, "use")

    assert (tmp_path / "captured.txt").read_text(encoding="utf-8") == "captured"


def test_file_dependency_unchanged_second_run_is_reported_up_to_date(tmp_path):
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

    proc = run_doit(tmp_path, "copy")

    assert "-- copy" in proc.stdout


def test_file_dependency_content_change_reruns_task(tmp_path):
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
    (tmp_path / "input.txt").write_text("bye", encoding="utf-8")

    proc = run_doit(tmp_path, "copy")

    assert ".  copy" in proc.stdout
    assert (tmp_path / "output.txt").read_text(encoding="utf-8") == "BYE"


def test_modifying_target_without_input_change_does_not_force_rerun(tmp_path):
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
    (tmp_path / "output.txt").write_text("manual", encoding="utf-8")

    proc = run_doit(tmp_path, "copy")

    assert "-- copy" in proc.stdout
    assert (tmp_path / "output.txt").read_text(encoding="utf-8") == "manual"


def test_missing_target_forces_rerun_and_restores_file(tmp_path):
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
    (tmp_path / "output.txt").unlink()

    proc = run_doit(tmp_path, "copy")

    assert ".  copy" in proc.stdout
    assert (tmp_path / "output.txt").read_text(encoding="utf-8") == "HELLO"


def test_setup_task_runs_only_when_selected_task_will_execute(tmp_path):
    write_dodo(
        tmp_path,
        common_actions()
        + """
        def task_prepare():
            return {"actions": [(append_text, ["events.txt", "setup;"], {})]}

        def task_build():
            return {"actions": [(write_text, ["out.txt", "built"], {})], "setup": ["prepare"], "targets": ["out.txt"]}
        """,
    )
    run_doit(tmp_path, "build")
    run_doit(tmp_path, "build")
    (tmp_path / "out.txt").unlink()
    run_doit(tmp_path, "build")

    assert (tmp_path / "events.txt").read_text(encoding="utf-8") == "setup;setup;setup;"


def test_implicit_target_dependency_runs_producer_before_consumer(tmp_path):
    write_dodo(
        tmp_path,
        common_actions()
        + """
        def task_source():
            return {"actions": [(write_text, ["source.txt", "abc"], {})], "targets": ["source.txt"]}

        def task_upper():
            return {"actions": [copy_upper], "file_dep": ["source.txt"], "targets": ["upper.txt"]}
        """,
    )

    proc = run_doit(tmp_path, "upper")

    assert ".  source" in proc.stdout
    assert ".  upper" in proc.stdout
    assert (tmp_path / "upper.txt").read_text(encoding="utf-8") == "ABC"


def test_reset_dep_records_changed_dependency_state_without_action_execution(tmp_path):
    (tmp_path / "input.txt").write_text("one", encoding="utf-8")
    write_dodo(
        tmp_path,
        common_actions()
        + """
        def task_copy():
            return {"actions": [copy_upper], "file_dep": ["input.txt"], "targets": ["output.txt"]}
        """,
    )
    run_doit(tmp_path, "copy")
    (tmp_path / "input.txt").write_text("two", encoding="utf-8")

    run_doit(tmp_path, "reset-dep", "copy")
    proc = run_doit(tmp_path, "copy")

    assert "-- copy" in proc.stdout
    assert (tmp_path / "output.txt").read_text(encoding="utf-8") == "ONE"


def test_clean_dry_run_reports_without_removing_target(tmp_path):
    write_dodo(
        tmp_path,
        common_actions()
        + """
        def task_build():
            return {"actions": [(write_text, ["artifact.txt", "x"], {})], "targets": ["artifact.txt"], "clean": True}
        """,
    )
    run_doit(tmp_path, "build")

    proc = run_doit(tmp_path, "clean", "--dry-run", "build")

    assert "artifact.txt" in proc.stdout
    assert (tmp_path / "artifact.txt").exists()


def test_list_status_changes_from_run_to_up_to_date(tmp_path):
    (tmp_path / "input.txt").write_text("x", encoding="utf-8")
    write_dodo(
        tmp_path,
        common_actions()
        + """
        def task_build():
            return {"actions": [copy_upper], "file_dep": ["input.txt"], "targets": ["artifact.txt"]}
        """,
    )
    before = run_doit(tmp_path, "list", "--status").stdout
    run_doit(tmp_path, "build")
    after = run_doit(tmp_path, "list", "--status").stdout

    assert "R" in before and "build" in before
    assert "U" in after and "build" in after


def test_info_reports_missing_target_as_reason_to_run(tmp_path):
    write_dodo(
        tmp_path,
        common_actions()
        + """
        def task_build():
            return {"actions": [(write_text, ["artifact.txt", "x"], {})], "targets": ["artifact.txt"]}
        """,
    )

    proc = run_doit(tmp_path, "info", "build", check=False)

    assert proc.returncode == 1
    assert "build" in proc.stdout
    assert "artifact.txt" in proc.stdout


def test_ignore_persists_skip_and_forget_clears_it(tmp_path):
    write_dodo(
        tmp_path,
        common_actions()
        + """
        def task_build():
            return {"actions": [(write_text, ["artifact.txt", "x"], {})], "targets": ["artifact.txt"]}
        """,
    )
    run_doit(tmp_path, "ignore", "build")

    ignored = run_doit(tmp_path, "build")
    run_doit(tmp_path, "forget", "build")
    restored = run_doit(tmp_path, "build")

    assert "!! build" in ignored.stdout
    assert ".  build" in restored.stdout
    assert (tmp_path / "artifact.txt").read_text(encoding="utf-8") == "x"


def test_forget_makes_successful_task_run_again(tmp_path):
    write_dodo(
        tmp_path,
        common_actions()
        + """
        def task_count():
            return {"actions": [(count_run, ["count.txt"], {})], "targets": ["count.txt"]}
        """,
    )
    run_doit(tmp_path, "count")
    run_doit(tmp_path, "count")
    run_doit(tmp_path, "forget", "count")
    proc = run_doit(tmp_path, "count")

    assert ".  count" in proc.stdout
    assert (tmp_path / "count.txt").read_text(encoding="utf-8") == "3"


def test_default_command_and_explicit_run_execute_same_default_task(tmp_path):
    write_dodo(
        tmp_path,
        common_actions()
        + """
        DOIT_CONFIG = {"default_tasks": ["build"]}

        def task_build():
            return {"actions": [(count_run, ["count.txt"], {})], "uptodate": [False]}
        """,
    )
    run_doit(tmp_path)
    run_doit(tmp_path, "run")

    assert (tmp_path / "count.txt").read_text(encoding="utf-8") == "2"


def test_selecting_by_target_runs_owning_task(tmp_path):
    write_dodo(
        tmp_path,
        common_actions()
        + """
        def task_build():
            return {"actions": [(write_text, ["artifact.txt", "targeted"], {})], "targets": ["artifact.txt"]}
        """,
    )

    run_doit(tmp_path, "artifact.txt")

    assert (tmp_path / "artifact.txt").read_text(encoding="utf-8") == "targeted"


def test_wildcard_selection_runs_matching_tasks_only(tmp_path):
    write_dodo(
        tmp_path,
        common_actions()
        + """
        def task_alpha_one():
            return {"actions": [(write_text, ["one.txt", "1"], {})], "targets": ["one.txt"]}

        def task_alpha_two():
            return {"actions": [(write_text, ["two.txt", "2"], {})], "targets": ["two.txt"]}

        def task_beta():
            return {"actions": [(write_text, ["beta.txt", "b"], {})], "targets": ["beta.txt"]}
        """,
    )

    run_doit(tmp_path, "alpha*")

    assert (tmp_path / "one.txt").exists()
    assert (tmp_path / "two.txt").exists()
    assert not (tmp_path / "beta.txt").exists()


def test_single_option_skips_task_dependencies(tmp_path):
    write_dodo(
        tmp_path,
        common_actions()
        + """
        def task_dep():
            return {"actions": [(write_text, ["dep.txt", "dep"], {})], "targets": ["dep.txt"]}

        def task_main():
            return {"actions": [(write_text, ["main.txt", "main"], {})], "task_dep": ["dep"], "targets": ["main.txt"]}
        """,
    )

    run_doit(tmp_path, "run", "--single", "main")

    assert (tmp_path / "main.txt").exists()
    assert not (tmp_path / "dep.txt").exists()


def test_json_reporter_reports_same_task_success_as_console_side_effect(tmp_path):
    write_dodo(
        tmp_path,
        common_actions()
        + """
        def task_build():
            return {"actions": [(write_text, ["artifact.txt", "ok"], {})], "targets": ["artifact.txt"]}
        """,
    )

    proc = run_doit(tmp_path, "run", "--reporter", "json", "build")
    report = json.loads(proc.stdout)

    assert (tmp_path / "artifact.txt").read_text(encoding="utf-8") == "ok"
    task_results = report["tasks"]
    if isinstance(task_results, list):
        build_result = next(item for item in task_results if item.get("name") == "build")
    else:
        build_result = task_results["build"]
    assert build_result["result"] == "success"


def test_run_once_skips_after_success_but_missing_target_still_runs(tmp_path):
    write_dodo(
        tmp_path,
        common_actions()
        + """
        from doit.tools import run_once

        def task_once():
            return {"actions": [(count_run, ["count.txt"], {})], "targets": ["count.txt"], "uptodate": [run_once]}
        """,
    )
    run_doit(tmp_path, "once")
    skipped = run_doit(tmp_path, "once")
    (tmp_path / "count.txt").unlink()
    rerun = run_doit(tmp_path, "once")

    assert "-- once" in skipped.stdout
    assert ".  once" in rerun.stdout
    assert (tmp_path / "count.txt").read_text(encoding="utf-8") == "1"


def test_result_dep_reruns_consumer_when_producer_result_changes(tmp_path):
    (tmp_path / "source.txt").write_text("one", encoding="utf-8")
    write_dodo(
        tmp_path,
        """
        from pathlib import Path
        from doit.tools import result_dep

        def produce():
            return Path("source.txt").read_text(encoding="utf-8")

        def consume():
            p = Path("consumer-count.txt")
            value = int(p.read_text(encoding="utf-8")) if p.exists() else 0
            p.write_text(str(value + 1), encoding="utf-8")
            return None

        def task_producer():
            return {"actions": [produce], "file_dep": ["source.txt"]}

        def task_consumer():
            return {"actions": [consume], "uptodate": [result_dep("producer")]}
        """,
    )
    run_doit(tmp_path, "consumer")
    run_doit(tmp_path, "consumer")
    (tmp_path / "source.txt").write_text("two", encoding="utf-8")
    proc = run_doit(tmp_path, "consumer")

    assert ".  producer" in proc.stdout
    assert ".  consumer" in proc.stdout
    assert (tmp_path / "consumer-count.txt").read_text(encoding="utf-8") == "2"


def test_verbosity_two_displays_python_action_stdout(tmp_path):
    write_dodo(
        tmp_path,
        """
        def speak():
            print("visible-output")
            return None

        def task_speak():
            return {"actions": [speak], "verbosity": 2}
        """,
    )

    proc = run_doit(tmp_path, "speak")

    assert "visible-output" in proc.stdout


def test_positional_arguments_are_passed_to_declared_action_name(tmp_path):
    write_dodo(
        tmp_path,
        """
        from pathlib import Path

        def save(words):
            Path("words.txt").write_text(",".join(words), encoding="utf-8")
            return None

        def task_echo():
            return {"actions": [(save, [], {})], "pos_arg": "words"}
        """,
    )

    run_doit(tmp_path, "echo", "alpha", "beta")

    assert (tmp_path / "words.txt").read_text(encoding="utf-8") == "alpha,beta"


def test_list_hides_private_tasks_until_requested(tmp_path):
    write_dodo(
        tmp_path,
        """
        def task_public():
            \"\"\"public task\"\"\"
            return {"actions": [None]}

        def task__hidden():
            \"\"\"hidden task\"\"\"
            return {"actions": [None]}
        """,
    )

    normal = run_doit(tmp_path, "list").stdout
    private = run_doit(tmp_path, "list", "--private").stdout

    assert "public" in normal
    assert "_hidden" not in normal
    assert "_hidden" in private


def test_always_execute_forces_rerun_even_when_up_to_date(tmp_path):
    write_dodo(
        tmp_path,
        common_actions()
        + """
        def task_count():
            return {"actions": [(count_run, ["count.txt"], {})], "targets": ["count.txt"], "uptodate": [True]}
        """,
    )
    run_doit(tmp_path, "count")
    run_doit(tmp_path, "count")
    forced = run_doit(tmp_path, "run", "--always-execute", "count")

    assert ".  count" in forced.stdout
    assert (tmp_path / "count.txt").read_text(encoding="utf-8") == "2"


def test_continue_runs_independent_task_after_failure(tmp_path):
    write_dodo(
        tmp_path,
        """
        from pathlib import Path

        def task_fail():
            return {"actions": [lambda: False]}

        def task_other():
            return {"actions": [(lambda: Path("other.txt").write_text("ran", encoding="utf-8") and None)]}
        """,
    )

    proc = run_doit(tmp_path, "run", "--continue", "fail", "other", check=False)

    assert proc.returncode == 1
    assert (tmp_path / "other.txt").read_text(encoding="utf-8") == "ran"


def test_clean_true_removes_target_file(tmp_path):
    write_dodo(
        tmp_path,
        common_actions()
        + """
        def task_build():
            return {"actions": [(write_text, ["artifact.txt", "x"], {})], "targets": ["artifact.txt"], "clean": True}
        """,
    )
    run_doit(tmp_path, "build")
    assert (tmp_path / "artifact.txt").exists()

    run_doit(tmp_path, "clean", "build")

    assert not (tmp_path / "artifact.txt").exists()


def test_clean_forget_clears_success_state_so_task_runs_again(tmp_path):
    write_dodo(
        tmp_path,
        common_actions()
        + """
        def task_build():
            return {"actions": [(count_run, ["count.txt"], {})], "targets": ["count.txt"], "clean": True}
        """,
    )
    run_doit(tmp_path, "build")
    run_doit(tmp_path, "clean", "--forget", "build")
    proc = run_doit(tmp_path, "build")

    assert ".  build" in proc.stdout
    assert (tmp_path / "count.txt").read_text(encoding="utf-8") == "1"


def test_doit_config_verbosity_changes_action_output_capture(tmp_path):
    write_dodo(
        tmp_path,
        """
        DOIT_CONFIG = {"verbosity": 2}

        def speak():
            print("config-visible")
            return None

        def task_speak():
            return {"actions": [speak]}
        """,
    )

    proc = run_doit(tmp_path, "speak")

    assert "config-visible" in proc.stdout


def test_pyproject_default_tasks_selects_configured_task(tmp_path):
    write_dodo(
        tmp_path,
        common_actions()
        + """
        DOIT_CONFIG = {"default_tasks": ["chosen"]}

        def task_chosen():
            return {"actions": [(write_text, ["chosen.txt", "yes"], {})], "targets": ["chosen.txt"]}

        def task_other():
            return {"actions": [(write_text, ["other.txt", "no"], {})], "targets": ["other.txt"]}
        """,
    )

    run_doit(tmp_path)

    assert (tmp_path / "chosen.txt").exists()
    assert not (tmp_path / "other.txt").exists()


def test_action_string_new_format_uses_dependencies_placeholder(tmp_path):
    (tmp_path / "input.txt").write_text("hello", encoding="utf-8")
    write_dodo(
        tmp_path,
        """
        import sys
        DOIT_CONFIG = {"action_string_formatting": "new"}

        def task_copy():
            return {"actions": [sys.executable + " -c \\"from pathlib import Path; Path('out.txt').write_text(Path('{dependencies}').read_text(encoding='utf-8').upper(), encoding='utf-8')\\""], "file_dep": ["input.txt"], "targets": ["out.txt"]}
        """,
    )

    run_doit(tmp_path, "copy")

    assert (tmp_path / "out.txt").read_text(encoding="utf-8") == "HELLO"


def test_calc_dep_adds_late_file_dependency(tmp_path):
    (tmp_path / "source.txt").write_text("one", encoding="utf-8")
    write_dodo(
        tmp_path,
        common_actions()
        + """
        def task_discover():
            return {"actions": [lambda: {"file_dep": ["source.txt"]}]}

        def task_build():
            return {"actions": [(count_run, ["count.txt"], {})], "calc_dep": ["discover"]}
        """,
    )
    run_doit(tmp_path, "build")
    run_doit(tmp_path, "build")
    (tmp_path / "source.txt").write_text("two", encoding="utf-8")
    proc = run_doit(tmp_path, "build")

    assert ".  build" in proc.stdout
    assert (tmp_path / "count.txt").read_text(encoding="utf-8") == "2"


def test_teardown_runs_after_selected_task(tmp_path):
    write_dodo(
        tmp_path,
        common_actions()
        + """
        def task_build():
            return {
                "actions": [(append_text, ["events.txt", "build;"], {})],
                "teardown": [(append_text, ["events.txt", "teardown;"], {})],
            }
        """,
    )

    run_doit(tmp_path, "build")

    assert (tmp_path / "events.txt").read_text(encoding="utf-8") == "build;teardown;"
