"""Atomic tests — each validates ONE public API, ONE behavior."""
import sys

import pytest

from conftest import PYTHON, write_file

from invoke import (
    Argument,
    Call,
    Collection,
    CollectionNotFound,
    CommandTimedOut,
    Config,
    Context,
    Exit,
    FailingResponder,
    Failure,
    MockContext,
    Responder,
    ResponseNotAccepted,
    Result,
    StreamWatcher,
    Task,
    UnexpectedExit,
    call,
    task,
)


# ── @task decorator ──────────────────────────────────────────────────


def test_task_bare_decorator_wraps_with_function_name():
    @task
    def compile(c):
        """Compile the project."""

    assert isinstance(compile, Task)
    assert compile.name == "compile"


def test_task_bare_decorator_preserves_docstring():
    @task
    def package(c):
        """Create distribution package."""

    assert package.__doc__ == "Create distribution package."


def test_task_configured_sets_name_aliases_default():
    @task(name="publish", aliases=("push",), default=True)
    def release(c):
        pass

    assert release.name == "publish"
    assert release.aliases == ("push",)
    assert release.is_default is True


def test_task_rejects_positional_with_pre_keyword():
    @task
    def setup(c):
        pass

    with pytest.raises(TypeError):
        task(setup, pre=[setup])


# ── Task callable contract ───────────────────────────────────────────


def test_task_called_transitions_after_invocation():
    marker = []

    @task
    def greet(c):
        marker.append(1)

    ctx = Context()
    assert greet.called is False
    greet(ctx)
    assert greet.called is True
    assert len(marker) == 1


def test_task_call_rejects_non_context_first_arg():
    @task
    def greet(c):
        pass

    with pytest.raises(TypeError):
        greet("not-a-context")


# ── Argument introspection ───────────────────────────────────────────


def test_task_get_arguments_excludes_context():
    @task
    def greet(c, recipient, loud=False):
        pass

    args = {a.name: a for a in greet.get_arguments()}
    assert "c" not in args
    assert set(args) == {"recipient", "loud"}
    assert all(isinstance(a, Argument) for a in greet.get_arguments())


def test_argument_positional_param_is_positional():
    @task
    def greet(c, recipient):
        pass

    args = {a.name: a for a in greet.get_arguments()}
    assert args["recipient"].positional is True


def test_argument_bool_default_sets_kind_bool():
    @task
    def greet(c, loud=False):
        pass

    args = {a.name: a for a in greet.get_arguments()}
    assert args["loud"].kind is bool


def test_argument_optional_iterable_incrementable_metadata():
    @task(optional=("format",), iterable=("tag",), incrementable=("debug",))
    def export(c, format=None, tag=None, debug=0):
        pass

    args = {a.name: a for a in export.get_arguments()}
    assert args["format"].optional is True
    assert args["tag"].kind is list
    assert args["debug"].incrementable is True


def test_argument_true_bool_default_keeps_kind_bool():
    @task
    def lint(c, strict=True):
        pass

    args = {a.name: a for a in lint.get_arguments()}
    assert args["strict"].kind is bool


# ── call helper / Call ───────────────────────────────────────────────


def test_call_helper_stores_task_args_kwargs():
    @task
    def publish(c, channel=None):
        pass

    obj = call(publish, "stable", force=True)
    assert isinstance(obj, Call)
    assert obj.task is publish
    assert obj.args == ("stable",)
    assert obj.kwargs == {"force": True}


def test_call_clone_replaces_data_preserves_task_ref():
    @task
    def publish(c):
        pass

    original = Call(publish, args=("x",), kwargs={"dry": False})
    cloned = original.clone(with_={"args": ("y",), "kwargs": {"dry": True}})
    assert cloned is not original
    assert cloned.task is publish
    assert cloned.args == ("y",)
    assert cloned.kwargs == {"dry": True}
    assert original.args == ("x",)


def test_call_make_context_applies_config_and_remainder():
    @task
    def publish(c):
        pass

    class FakeParsed:
        remainder = "--extra flag"

    cfg = Config(overrides={"run": {"warn": True}})
    ctx = Call(publish).make_context(cfg, FakeParsed())
    assert ctx.config is cfg
    assert ctx.remainder == "--extra flag"


# ── Collection ───────────────────────────────────────────────────────


def test_collection_add_task_name_alias_lookup():
    @task(aliases=("pub",))
    def publish(c):
        pass

    ns = Collection()
    ns.add_task(publish, name="release", aliases=("go",))
    assert ns["release"] is publish
    assert ns["pub"] is publish
    assert ns["go"] is publish


def test_collection_default_via_none_and_empty():
    @task(default=True)
    def main(c):
        pass

    ns = Collection(main)
    assert ns[None] is main
    assert ns[""] is main


def test_collection_rejects_second_default():
    @task(default=True)
    def alpha(c):
        pass

    @task(default=True)
    def beta(c):
        pass

    with pytest.raises(ValueError):
        Collection(alpha, beta)


def test_collection_subcollection_dotted_lookup():
    @task(default=True)
    def migrate(c):
        pass

    child = Collection("db", migrate)
    root = Collection("root")
    root.add_collection(child)
    assert root["db"] is migrate
    assert root["db.migrate"] is migrate


def test_collection_task_names_include_dotted_paths():
    @task(aliases=("m",), default=True)
    def migrate(c):
        pass

    root = Collection("root")
    root.add_collection(Collection("db", migrate))
    names = root.task_names
    assert "db.migrate" in names
    assert "db" in names["db.migrate"]
    assert "db.m" in names["db.migrate"]


def test_collection_configure_parent_overrides_child():
    @task
    def migrate(c):
        pass

    child = Collection("db", migrate)
    child.configure({"db": {"host": "child-host", "port": 3306}})
    root = Collection("root")
    root.configure({"db": {"host": "parent-host"}})
    root.add_collection(child)
    merged = root.configuration("db.migrate")
    assert merged["db"]["host"] == "parent-host"


def test_collection_from_module_prefers_explicit_ns(tmp_path):
    write_file(
        tmp_path / "taskmod_alpha.py",
        """
        from invoke import Collection, task

        @task
        def ignored(c):
            pass

        @task
        def chosen(c):
            pass

        ns = Collection("explicit", chosen)
        """,
    )
    sys.path.insert(0, str(tmp_path))
    try:
        sys.modules.pop("taskmod_alpha", None)
        module = __import__("taskmod_alpha")
        coll = Collection.from_module(module)
    finally:
        sys.modules.pop("taskmod_alpha", None)
        sys.path.pop(0)
    assert coll.name == "explicit"
    assert "chosen" in coll.task_names
    assert "ignored" not in coll.task_names


def test_collection_from_module_uses_top_level_without_ns(tmp_path):
    write_file(
        tmp_path / "taskmod_beta.py",
        """
        from invoke import task

        @task
        def check(c):
            pass
        """,
    )
    sys.path.insert(0, str(tmp_path))
    try:
        sys.modules.pop("taskmod_beta", None)
        module = __import__("taskmod_beta")
        coll = Collection.from_module(module)
    finally:
        sys.modules.pop("taskmod_beta", None)
        sys.path.pop(0)
    assert coll.name == "taskmod_beta"
    assert "check" in coll.task_names


# ── Config ───────────────────────────────────────────────────────────


def test_config_dict_and_attribute_access():
    config = Config(defaults={"release": {"channel": "stable"}})
    assert config["release"]["channel"] == "stable"
    assert config.release.channel == "stable"
    config.release.channel = "beta"
    assert config["release"]["channel"] == "beta"


def test_config_real_attribute_precedence():
    config = Config(defaults={"clone": {"depth": 1}})
    assert callable(config.clone)
    assert config["clone"]["depth"] == 1


def test_config_clone_independence():
    config = Config(defaults={"release": {"channel": "stable"}})
    copy = config.clone()
    copy.release.channel = "nightly"
    assert config.release.channel == "stable"
    assert copy.release.channel == "nightly"


def test_config_load_overrides_beats_defaults():
    config = Config(defaults={"run": {"warn": False}})
    config.load_overrides({"run": {"warn": True}})
    assert config.run.warn is True


def test_config_load_shell_env_casts_types(monkeypatch):
    monkeypatch.setenv("INVOKE_RUN_ECHO", "1")
    monkeypatch.setenv("INVOKE_TIMEOUTS_COMMAND", "8")
    config = Config(defaults={"run": {"echo": False}, "timeouts": {"command": 2}})
    config.load_shell_env()
    assert config.run.echo is True
    assert config.timeouts.command == 8


# ── Context.run basics ──────────────────────────────────────────────


def test_context_run_warn_true_returns_failed():
    result = Context().run(
        f"{PYTHON} -c \"import sys; sys.exit(3)\"",
        hide=True,
        warn=True,
        in_stream=False,
    )
    assert result.failed is True
    assert result.exited == 3


def test_context_run_warn_false_raises_unexpected_exit():
    with pytest.raises(UnexpectedExit) as exc_info:
        Context().run(
            f"{PYTHON} -c \"import sys; sys.exit(4)\"",
            hide=True,
            in_stream=False,
        )
    assert exc_info.value.result.exited == 4


def test_context_run_dry_does_not_execute():
    result = Context().run(
        "nonexistent-cmd-xyzzy",
        dry=True,
        hide=True,
        in_stream=False,
    )
    assert result.ok is True
    assert result.stdout == ""
    assert result.stderr == ""


# ── Result ───────────────────────────────────────────────────────────


def test_result_exited_ok_failed_return_code():
    ok = Result(exited=0, command="echo ok")
    bad = Result(exited=5, command="false")
    assert ok.exited == 0
    assert ok.ok is True
    assert ok.failed is False
    assert ok.return_code == 0
    assert bad.exited == 5
    assert bad.ok is False
    assert bad.failed is True
    assert bad.return_code == 5


def test_result_truthy_when_ok_falsy_when_failed():
    assert bool(Result(exited=0)) is True
    assert bool(Result(exited=2)) is False


def test_result_command_stdout_stderr_env():
    r = Result(command="ls -la", stdout="file.txt\n", stderr="warning\n")
    assert r.command == "ls -la"
    assert r.stdout == "file.txt\n"
    assert r.stderr == "warning\n"
    assert r.env == {}


def test_result_tail_last_n_lines():
    r = Result(stdout="alpha\nbeta\ngamma\ndelta\n")
    tail = r.tail("stdout", count=2)
    assert "gamma" in tail
    assert "delta" in tail
    assert "alpha" not in tail


# ── MockContext ──────────────────────────────────────────────────────


def test_mock_context_string_becomes_result_stdout():
    ctx = MockContext(run={"status": "running"})
    assert ctx.run("status").stdout == "running"


def test_mock_context_false_becomes_failed_result():
    ctx = MockContext(run={"halt": False})
    assert ctx.run("halt").exited == 1


def test_mock_context_unmatched_raises_not_implemented():
    ctx = MockContext(run={})
    with pytest.raises(NotImplementedError):
        ctx.run("unknown-cmd")


# ── StreamWatcher / Responder / FailingResponder ─────────────────────


def test_stream_watcher_submit_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        StreamWatcher().submit("data")


def test_responder_yields_on_match():
    r = Responder(pattern=r"Passphrase: ", response="s3cret\n")
    assert list(r.submit("Passphrase: ")) == ["s3cret\n"]


def test_responder_consumes_segment_once_rematches_new():
    r = Responder(pattern=r"prompt", response="ok\n")
    assert list(r.submit("prompt")) == ["ok\n"]
    assert list(r.submit("prompt")) == []
    assert list(r.submit("prompt prompt")) == ["ok\n"]


def test_failing_responder_raises_on_sentinel():
    fr = FailingResponder(
        pattern=r"Passphrase: ",
        response="wrong\n",
        sentinel=r"Denied",
    )
    assert list(fr.submit("Passphrase: ")) == ["wrong\n"]
    with pytest.raises(ResponseNotAccepted):
        list(fr.submit("Passphrase: Denied"))


# ── Error Semantics ──────────────────────────────────────────────────


def test_exit_no_message_code_zero():
    assert Exit().code == 0


def test_exit_message_without_code_defaults_to_one():
    assert Exit(message="done").code == 1


def test_exit_explicit_code_overrides_default():
    assert Exit(message="custom", code=42).code == 42


def test_collection_not_found_stores_name():
    exc = CollectionNotFound("mymod", "/workspace")
    assert exc.name == "mymod"


def test_failure_exposes_result_and_reason():
    r = Result(command="cmd", exited=1)
    reason = Exception("watcher issue")
    exc = Failure(result=r, reason=reason)
    assert exc.result is r
    assert exc.reason is reason


def test_command_timed_out_exposes_timeout():
    r = Result(command="sleep 999", exited=-1)
    exc = CommandTimedOut(r, 5)
    assert exc.result is r
    assert exc.timeout == 5
