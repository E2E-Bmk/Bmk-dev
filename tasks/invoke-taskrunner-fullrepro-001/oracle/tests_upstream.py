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


def test_task_decorator_bare_wraps_callable_with_public_name():
    @task
    def build(c):
        """Build the project."""

    assert isinstance(build, Task)
    assert build.name == "build"
    assert build.__doc__ == "Build the project."


def test_task_decorator_options_set_name_aliases_and_default():
    @task(name="ship", aliases=("deploy",), default=True)
    def release(c):
        pass

    assert release.name == "ship"
    assert release.aliases == ("deploy",)
    assert release.is_default is True


def test_task_decorator_rejects_positional_pretasks_and_pre_keyword():
    @task
    def clean(c):
        pass

    with pytest.raises(TypeError):
        task(clean, pre=[clean])


def test_task_call_requires_context_as_first_argument():
    @task
    def build(c):
        pass

    with pytest.raises(TypeError):
        build("not-a-context")


def test_task_call_marks_task_as_called_after_success():
    seen = []

    @task
    def build(c):
        seen.append(c)

    ctx = Context()
    assert build.called is False
    build(ctx)
    assert build.called is True
    assert seen == [ctx]


def test_task_arguments_drop_context_and_dash_underscores():
    @task
    def build(c, target_name, clean=False):
        pass

    args = {arg.name: arg for arg in build.get_arguments()}
    assert set(args) == {"target_name", "clean"}
    assert args["target_name"].positional is True
    assert args["clean"].kind is bool


def test_task_boolean_true_default_creates_inverse_flag():
    @task
    def build(c, cache=True):
        pass

    args = {arg.name: arg for arg in build.get_arguments()}
    assert set(args) == {"cache"}
    assert args["cache"].kind is bool


def test_task_optional_iterable_and_incrementable_argument_metadata():
    @task(optional=("target",), iterable=("label",), incrementable=("verbose",))
    def build(c, target=None, label=None, verbose=0):
        pass

    args = {arg.name: arg for arg in build.get_arguments()}
    assert args["target"].optional is True
    assert args["label"].kind is list
    assert args["verbose"].incrementable is True


def test_call_helper_stores_task_args_and_kwargs():
    @task
    def build(c, target=None):
        pass

    obj = call(build, "dist", force=True)
    assert isinstance(obj, Call)
    assert obj.task is build
    assert obj.args == ("dist",)
    assert obj.kwargs == {"force": True}


def test_call_clone_is_independent_and_can_replace_data():
    @task
    def build(c):
        pass

    obj = Call(build, args=("a",), kwargs={"flag": False})
    cloned = obj.clone(with_={"args": ("b",), "kwargs": {"flag": True}})
    assert cloned is not obj
    assert cloned.task is build
    assert cloned.args == ("b",)
    assert cloned.kwargs == {"flag": True}
    assert obj.args == ("a",)


def test_call_make_context_uses_config_and_remainder():
    @task
    def build(c):
        pass

    class Parsed:
        remainder = "after --"

    config = Config(overrides={"run": {"echo": True}})
    ctx = Call(build).make_context(config, Parsed())
    assert ctx.config is config
    assert ctx.remainder == "after --"


def test_collection_add_task_binds_name_alias_and_lookup():
    @task(aliases=("ship",))
    def deploy(c):
        pass

    ns = Collection()
    ns.add_task(deploy, name="release", aliases=("go",))
    assert ns["release"] is deploy
    assert ns["ship"] is deploy
    assert ns["go"] is deploy


def test_collection_empty_lookup_returns_default_task():
    @task(default=True)
    def build(c):
        pass

    ns = Collection(build)
    assert ns[None] is build
    assert ns[""] is build


def test_collection_rejects_second_default_task():
    @task(default=True)
    def one(c):
        pass

    @task(default=True)
    def two(c):
        pass

    with pytest.raises(ValueError):
        Collection(one, two)


def test_collection_dotted_subcollection_lookup_and_default():
    @task(default=True)
    def deploy(c):
        pass

    child = Collection("prod", deploy)
    root = Collection("root")
    root.add_collection(child)
    assert root["prod"] is deploy
    assert root["prod.deploy"] is deploy


def test_collection_task_names_include_dotted_names_aliases_and_defaults():
    @task(aliases=("ship",), default=True)
    def deploy(c):
        pass

    root = Collection("root")
    root.add_collection(Collection("prod", deploy))
    names = root.task_names
    assert "prod.deploy" in names
    assert "prod" in names["prod.deploy"]
    assert "prod.ship" in names["prod.deploy"]


def test_collection_configuration_merges_parent_over_child_for_path():
    @task
    def deploy(c):
        pass

    child = Collection("prod", deploy)
    child.configure({"app": {"target": "child", "region": "us"}})
    root = Collection("root")
    root.configure({"app": {"target": "parent"}})
    root.add_collection(child)
    assert root.configuration("prod.deploy")["app"]["target"] == "parent"


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


def test_config_supports_dict_and_attribute_access():
    config = Config(defaults={"project": {"target": "dist"}})
    assert config["project"]["target"] == "dist"
    assert config.project.target == "dist"
    config.project.target = "wheel"
    assert config["project"]["target"] == "wheel"


def test_config_real_attributes_take_precedence_over_config_keys():
    config = Config(defaults={"clone": {"value": "from-config"}})
    assert callable(config.clone)
    assert config["clone"]["value"] == "from-config"


def test_config_clone_preserves_values_without_sharing_runtime_changes():
    config = Config(defaults={"project": {"target": "dist"}})
    clone = config.clone()
    clone.project.target = "wheel"
    assert config.project.target == "dist"
    assert clone.project.target == "wheel"


def test_config_load_overrides_beats_defaults():
    config = Config(defaults={"run": {"echo": False}})
    config.load_overrides({"run": {"echo": True}})
    assert config.run.echo is True


def test_config_environment_casts_existing_boolean_and_numeric_defaults(monkeypatch):
    monkeypatch.setenv("INVOKE_RUN_ECHO", "1")
    monkeypatch.setenv("INVOKE_TIMEOUTS_COMMAND", "5")
    config = Config(defaults={"run": {"echo": False}, "timeouts": {"command": 1}})
    config.load_shell_env()
    assert config.run.echo is True
    assert config.timeouts.command == 5


def test_config_unknown_runtime_file_extension_raises(tmp_path):
    runtime = tmp_path / "invoke.ini"
    runtime.write_text("[run]\necho = true\n", encoding="utf-8")
    config = Config(runtime_path=str(runtime))
    with pytest.raises(UnknownFileType):
        config.load_runtime()


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


def test_result_truth_return_code_and_default_env():
    ok = Result(exited=0)
    failed = Result(exited=3)
    assert bool(ok) is True
    assert bool(failed) is False
    assert failed.return_code == 3
    assert ok.env == {}


def test_result_tail_returns_requested_stream_lines():
    result = Result(stdout="one\ntwo\nthree\n")
    tail = result.tail("stdout", count=2)
    assert "two" in tail
    assert "three" in tail
    assert "one" not in tail


def test_mock_context_returns_prepared_string_and_boolean_results():
    ctx = MockContext(run={"show": "visible", "fail": False})
    assert ctx.run("show").stdout == "visible"
    assert ctx.run("fail").exited == 1


def test_mock_context_raises_when_no_prepared_result_matches():
    ctx = MockContext(run={})
    with pytest.raises(NotImplementedError):
        ctx.run("missing")


def test_stream_watcher_base_submit_is_not_implemented():
    with pytest.raises(NotImplementedError):
        StreamWatcher().submit("anything")


def test_responder_yields_response_for_regex_match():
    responder = Responder(pattern=r"Password: ", response="secret\n")
    assert list(responder.submit("Password: ")) == ["secret\n"]


def test_responder_consumes_each_stream_segment_once():
    responder = Responder(pattern=r"again", response="yes\n")
    assert list(responder.submit("again")) == ["yes\n"]
    assert list(responder.submit("again")) == []
    assert list(responder.submit("again again")) == ["yes\n"]


def test_failing_responder_raises_after_response_sentinel():
    responder = FailingResponder(
        pattern=r"Password: ",
        response="bad\n",
        sentinel=r"Sorry",
    )
    assert list(responder.submit("Password: ")) == ["bad\n"]
    with pytest.raises(ResponseNotAccepted):
        list(responder.submit("Password: Sorry"))


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
