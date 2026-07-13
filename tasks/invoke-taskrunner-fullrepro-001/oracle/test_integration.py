# Spec2Repo oracle - integration tests for invoke-taskrunner-fullrepro-001
import json
import os
import subprocess
import sys
import textwrap

import pytest

from invoke import (
    Call,
    Collection,
    Config,
    Context,
    FailingResponder,
    MockContext,
    Program,
    Responder,
    ResponseNotAccepted,
    Result,
    Runner,
    StreamWatcher,
    Task,
    UnexpectedExit,
    call,
    run,
    task,
)
from invoke.exceptions import Failure, UnknownFileType


def write_file(path, body):
    path.write_text(textwrap.dedent(body).lstrip(), encoding="utf-8")


def run_invoke(tmp_path, *args, env=None):
    command = [sys.executable, "-m", "invoke", *args]
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        command,
        cwd=str(tmp_path),
        env=merged_env,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_collection_from_module_prefers_explicit_namespace(tmp_path):
    module_path = tmp_path / "tasks.py"
    write_file(
        module_path,
        """
        from invoke import Collection, task

        @task
        def root(c):
            pass

        @task
        def selected(c):
            pass

        ns = Collection("chosen", selected)
        """,
    )
    sys.path.insert(0, str(tmp_path))
    try:
        sys.modules.pop("tasks", None)
        module = __import__("tasks")
        coll = Collection.from_module(module)
    finally:
        sys.modules.pop("tasks", None)
        sys.path.pop(0)
    assert coll.name == "chosen"
    assert "selected" in coll.task_names
    assert "root" not in coll.task_names


def test_collection_from_module_uses_top_level_tasks_without_namespace(tmp_path):
    module_path = tmp_path / "buildtasks.py"
    write_file(
        module_path,
        """
        from invoke import task

        @task
        def clean(c):
            pass
        """,
    )
    sys.path.insert(0, str(tmp_path))
    try:
        sys.modules.pop("buildtasks", None)
        module = __import__("buildtasks")
        coll = Collection.from_module(module)
    finally:
        sys.modules.pop("buildtasks", None)
        sys.path.pop(0)
    assert coll.name == "buildtasks"
    assert "clean" in coll.task_names


def test_config_environment_casts_existing_boolean_and_numeric_defaults(monkeypatch):
    monkeypatch.setenv("INVOKE_RUN_ECHO", "1")
    monkeypatch.setenv("INVOKE_TIMEOUTS_COMMAND", "5")
    config = Config(defaults={"run": {"echo": False}, "timeouts": {"command": 1}})
    config.load_shell_env()
    assert config.run.echo is True
    assert config.timeouts.command == 5


class RecordingRunner(Runner):
    seen = []

    def run(self, command, **kwargs):
        self.__class__.seen.append((command, kwargs, self.context))
        return Result(command=command, stdout="recorded\n", exited=0)


def test_context_run_uses_configured_local_runner_class():
    RecordingRunner.seen.clear()
    config = Config(overrides={"runners": {"local": RecordingRunner}})
    ctx = Context(config=config)
    result = ctx.run("build", hide=True)
    assert result.stdout == "recorded\n"
    assert RecordingRunner.seen[0][0] == "build"
    assert RecordingRunner.seen[0][2] is ctx


def test_invoke_run_creates_anonymous_context_and_returns_result():
    result = run(
        f"{sys.executable} -c \"print('hello from invoke')\"",
        hide=True,
        in_stream=False,
    )
    assert result.stdout == "hello from invoke\n"
    assert result.ok is True


def test_context_run_warn_true_returns_failed_result():
    result = Context().run(
        f"{sys.executable} -c \"import sys; sys.exit(7)\"",
        hide=True,
        warn=True,
        in_stream=False,
    )
    assert result.exited == 7
    assert result.failed is True


def test_context_run_warn_false_raises_unexpected_exit():
    with pytest.raises(UnexpectedExit) as exc:
        Context().run(
            f"{sys.executable} -c \"import sys; sys.exit(6)\"",
            hide=True,
            in_stream=False,
        )
    assert exc.value.result.exited == 6


def test_context_run_dry_returns_success_without_running_command():
    result = Context().run(
        "this-command-should-not-exist",
        dry=True,
        hide=True,
        in_stream=False,
    )
    assert result.ok is True
    assert result.stdout == ""
    assert result.stderr == ""


def test_context_cd_changes_cwd_for_command(tmp_path):
    RecordingRunner.seen.clear()
    ctx = Context(config=Config(overrides={"runners": {"local": RecordingRunner}}))
    with ctx.cd(str(tmp_path)):
        ctx.run("pwd", hide=True)
    command = RecordingRunner.seen[0][0]
    assert command.endswith(" && pwd")
    assert str(tmp_path) in command


def test_context_prefix_runs_before_command():
    ctx = Context()
    with ctx.prefix(f"{sys.executable} -c \"print('prefix')\""):
        result = ctx.run(
            f"{sys.executable} -c \"print('body')\"",
            hide=True,
            in_stream=False,
        )
    assert result.stdout.splitlines() == ["prefix", "body"]


def test_context_run_watcher_responds_to_prompt_and_preserves_output():
    code = (
        "import sys; "
        "sys.stdout.write('Continue? '); sys.stdout.flush(); "
        "answer=sys.stdin.readline().strip(); print(answer)"
    )
    responder = Responder(pattern=r"Continue\? ", response="yes\n")
    result = Context().run(
        f"{sys.executable} -c \"{code}\"",
        watchers=[responder],
        hide=True,
        in_stream=False,
    )
    assert "Continue? " in result.stdout
    assert "yes" in result.stdout


def test_context_run_wraps_failing_watcher_in_failure():
    code = (
        "import sys; "
        "sys.stdout.write('Password: '); sys.stdout.flush(); "
        "sys.stdin.readline(); print('Sorry')"
    )
    responder = FailingResponder(
        pattern=r"Password: ",
        response="bad\n",
        sentinel=r"Sorry",
    )
    with pytest.raises(Failure) as exc:
        Context().run(
            f"{sys.executable} -c \"{code}\"",
            watchers=[responder],
            hide=True,
            in_stream=False,
        )
    assert isinstance(exc.value.reason, ResponseNotAccepted)


def test_cli_json_list_reports_tasks_aliases_and_default(tmp_path):
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task, Collection

        @task(aliases=("ship",), default=True)
        def deploy(c):
            pass

        ns = Collection("project", deploy)
        """,
    )
    proc = run_invoke(tmp_path, "--list", "--list-format=json")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["name"] == "project"
    deploy = next(item for item in payload["tasks"] if item["name"] == "deploy")
    assert deploy["aliases"] == ["ship"]


def test_cli_invokes_default_task_when_no_task_name_is_given(tmp_path):
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task, Collection

        @task(default=True)
        def deploy(c):
            print("deployed")

        ns = Collection("project", deploy)
        """,
    )
    proc = run_invoke(tmp_path)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "deployed"


def test_cli_explicit_collection_module_replaces_tasks_default(tmp_path):
    write_file(
        tmp_path / "build.py",
        """
        from invoke import task

        @task
        def clean(c):
            print("cleaned")
        """,
    )
    proc = run_invoke(tmp_path, "--collection=build", "clean")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "cleaned"


def test_cli_delivers_dashed_flag_to_underscored_python_argument(tmp_path):
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task

        @task
        def show(c, target_name):
            print(target_name)
        """,
    )
    proc = run_invoke(tmp_path, "show", "--target-name=wheel")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "wheel"


def test_cli_inverse_boolean_flag_sets_false(tmp_path):
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task

        @task
        def build(c, cache=True):
            print(cache)
        """,
    )
    proc = run_invoke(tmp_path, "build", "--no-cache")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "False"


def test_cli_optional_argument_accepts_bare_flag_and_value(tmp_path):
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task

        @task(optional=("target",))
        def build(c, target=None):
            print(repr(target))
        """,
    )
    bare = run_invoke(tmp_path, "build", "--target")
    valued = run_invoke(tmp_path, "build", "--target=dist")
    assert bare.returncode == 0, bare.stderr
    assert valued.returncode == 0, valued.stderr
    assert bare.stdout.strip() == "True"
    assert valued.stdout.strip() == "'dist'"


def test_cli_iterable_argument_accumulates_repeated_values(tmp_path):
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task

        @task(iterable=("label",))
        def build(c, label=None):
            print(",".join(label))
        """,
    )
    proc = run_invoke(tmp_path, "build", "--label=a", "--label=b")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "a,b"


def test_cli_incrementable_argument_counts_repetitions(tmp_path):
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task

        @task(incrementable=("verbose",))
        def build(c, verbose=0):
            print(verbose)
        """,
    )
    proc = run_invoke(tmp_path, "build", "--verbose", "--verbose")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "2"


def test_cli_runs_pre_and_post_tasks_around_requested_task(tmp_path):
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task

        @task
        def clean(c):
            print("clean")

        @task
        def done(c):
            print("done")

        @task(pre=[clean], post=[done])
        def build(c):
            print("build")
        """,
    )
    proc = run_invoke(tmp_path, "build")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.splitlines() == ["clean", "build", "done"]


def test_cli_dedupes_repeated_task_calls_by_default(tmp_path):
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task

        @task
        def build(c):
            print("build")
        """,
    )
    proc = run_invoke(tmp_path, "build", "build")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.splitlines() == ["build"]


def test_cli_no_dedupe_allows_repeated_task_calls(tmp_path):
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task

        @task
        def build(c):
            print("build")
        """,
    )
    proc = run_invoke(tmp_path, "--no-dedupe", "build", "build")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.splitlines() == ["build", "build"]


def test_cli_remainder_after_double_dash_reaches_context(tmp_path):
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task

        @task
        def show(c):
            print(c.remainder)
        """,
    )
    proc = run_invoke(tmp_path, "show", "--", "--not-an-invoke-flag", "value")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "--not-an-invoke-flag value"


def test_cli_project_config_is_visible_to_task_context(tmp_path):
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task

        @task
        def show(c):
            print(c.project.target)
        """,
    )
    write_file(
        tmp_path / "invoke.yaml",
        """
        project:
          target: wheel
        """,
    )
    proc = run_invoke(tmp_path, "show")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "wheel"


def test_cli_environment_variable_overrides_existing_config_key(tmp_path):
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task

        @task
        def show(c):
            print(c.config.run.echo)
        """,
    )
    proc = run_invoke(tmp_path, "show", env={"INVOKE_RUN_ECHO": "1"})
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "True"


def test_cli_runtime_config_file_overrides_project_config(tmp_path):
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task

        @task
        def show(c):
            print(c.project.target)
        """,
    )
    write_file(tmp_path / "invoke.yaml", "project:\n  target: project\n")
    runtime = tmp_path / "runtime.yaml"
    write_file(runtime, "project:\n  target: runtime\n")
    proc = run_invoke(tmp_path, "--config", str(runtime), "show")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "runtime"


def test_cli_run_flag_overrides_config_for_task_commands(tmp_path):
    write_file(
        tmp_path / "tasks.py",
        f"""
        from invoke import task

        @task
        def show(c):
            c.run({sys.executable!r} + " -c \\"print('body')\\"")
        """,
    )
    write_file(tmp_path / "invoke.yaml", "run:\n  echo: false\n")
    proc = run_invoke(tmp_path, "--echo", "show")
    assert proc.returncode == 0, proc.stderr
    assert "body" in proc.stdout
    assert "-c" in proc.stdout


def test_cli_help_for_task_includes_docstring_and_task_option(tmp_path):
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task

        @task(help={"target": "Build destination."})
        def build(c, target="dist"):
            \"\"\"Build wheels.\"\"\"
            pass
        """,
    )
    proc = run_invoke(tmp_path, "--help", "build")
    assert proc.returncode == 0, proc.stderr
    assert "Build wheels." in proc.stdout
    assert "--target" in proc.stdout
    assert "Build destination." in proc.stdout


def test_cli_unknown_task_exits_unsuccessfully(tmp_path):
    write_file(tmp_path / "tasks.py", "from invoke import task\n")
    proc = run_invoke(tmp_path, "missing")
    assert proc.returncode != 0
    assert "missing" in (proc.stderr + proc.stdout)


def test_python_module_invocation_runs_same_program(tmp_path):
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task

        @task
        def hello(c):
            print("hello")
        """,
    )
    proc = run_invoke(tmp_path, "hello")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "hello"


def test_program_run_string_argv_and_exit_false_do_not_raise_system_exit(tmp_path, capsys):
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task

        @task
        def hello(c):
            print("hello")
        """,
    )
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        program = Program()
        program.run("invoke hello", exit=False)
    finally:
        os.chdir(old_cwd)
    assert "hello" in capsys.readouterr().out


def test_program_run_unknown_task_with_exit_false_returns_without_system_exit(tmp_path, capsys):
    write_file(tmp_path / "tasks.py", "from invoke import task\n")
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        Program().run("invoke missing", exit=False)
    finally:
        os.chdir(old_cwd)
    captured = capsys.readouterr()
    assert "missing" in (captured.out + captured.err)


def test_cli_flat_list_uses_dotted_names_for_nested_collections(tmp_path):
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import Collection, task

        @task
        def deploy(c):
            pass

        ns = Collection("root")
        ns.add_collection(Collection("prod", deploy))
        """,
    )
    proc = run_invoke(tmp_path, "--list", "--list-format=flat")
    assert proc.returncode == 0, proc.stderr
    assert "prod.deploy" in proc.stdout


def test_cli_list_depth_with_json_is_an_error(tmp_path):
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task

        @task
        def build(c):
            pass
        """,
    )
    proc = run_invoke(
        tmp_path,
        "--list",
        "--list-format=json",
        "--list-depth=1",
    )
    assert proc.returncode != 0


def test_context_sudo_runtime_password_builds_prompt_responder(monkeypatch):
    class SudoRecordingRunner(Runner):
        seen = []

        def run(self, command, **kwargs):
            self.__class__.seen.append((command, kwargs))
            return Result(command=command, exited=0)

    ctx = Context(
        config=Config(
            overrides={
                "sudo": {"password": "configpass"},
                "runners": {"local": SudoRecordingRunner},
            }
        )
    )
    result = ctx.sudo("whoami", password="runtimepass", user="root")
    assert result.ok is True
    command, kwargs = SudoRecordingRunner.seen[0]
    assert command.startswith("sudo ")
    assert "-u root" in command
    assert kwargs["watchers"]


def test_sudo_rejected_response_translates_to_auth_failure(monkeypatch):
    from invoke import AuthFailure

    class RejectingRunner(Runner):
        def run(self, command, **kwargs):
            raise Failure(
                result=Result(command=command, exited=1),
                reason=ResponseNotAccepted(),
            )

    with pytest.raises(AuthFailure):
        Context(
            config=Config(
                overrides={
                    "sudo": {"password": "bad"},
                    "runners": {"local": RejectingRunner},
                }
            )
        ).sudo("id")
