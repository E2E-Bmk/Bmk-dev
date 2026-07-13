# Spec2Repo oracle - atomic tests for invoke-taskrunner-fullrepro-001
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
