from __future__ import annotations

import importlib
import io
import os
from pathlib import Path
from types import SimpleNamespace


def native_case(root_id: str, tmp_path: Path) -> None:
    invoke = importlib.import_module("invoke")
    Task = invoke.Task
    Collection = invoke.Collection
    Config = invoke.Config
    Context = invoke.Context

    if root_id == "A01":
        public = {
            "Task", "Call", "task", "call", "Collection", "Config", "Context",
            "Executor", "Runner", "Result", "Program", "ParseResult",
        }
        assert all(hasattr(invoke, name) for name in public)
        assert invoke.__version__ == "3.0.3"
        root = Path(os.environ["SPEC2REPO_CANDIDATE_ROOT"]).resolve()
        assert Path(invoke.__file__).resolve().is_relative_to(root)
    elif root_id == "A02":
        @invoke.task
        def add(c, left=1, right=2):
            """Add two values."""
            return left + right
        assert isinstance(add, Task) and add.name == "add"
        assert add.__doc__ == "Add two values."
        assert add(Context(Config(lazy=True)), 3, 4) == 7
        try:
            add(object(), 1, 2)
        except TypeError:
            pass
        else:
            raise AssertionError("Task accepted a non-Context first argument")
    elif root_id == "A03":
        @invoke.task(
            name="ship", aliases=("s",), default=True, positional=("channel",),
            optional=("force",), iterable=("tag",), incrementable=("verbose",),
        )
        def publish(c, channel="stable", force=False, tag=(), verbose=0):
            return channel, force, tag, verbose
        assert publish.name == "ship" and tuple(publish.aliases) == ("s",)
        assert publish.is_default and tuple(publish.positional) == ("channel",)
        assert set(publish.optional) == {"force"}
        assert set(publish.iterable) == {"tag"} and set(publish.incrementable) == {"verbose"}
    elif root_id == "A04":
        @invoke.task
        def publish(c, channel="stable", force=False):
            return channel, force
        original = invoke.call(publish, "stable", force=True)
        cloned = original.clone(with_={"args": ("nightly",), "kwargs": {"force": False}})
        assert isinstance(original, invoke.Call) and original.task is publish
        assert original.args == ("stable",) and original.kwargs == {"force": True}
        assert cloned is not original and cloned.task is publish and cloned.args == ("nightly",)
    elif root_id == "A05":
        @invoke.task
        def publish(c):
            return c.remainder
        parsed = invoke.ParseResult()
        parsed.remainder = "--extra flag"
        config = Config(lazy=True)
        context = invoke.call(publish).make_context(config, parsed)
        assert context.config is config and context.remainder == "--extra flag"
    elif root_id == "A06":
        @invoke.task(name="publish", aliases=("pub",), default=True)
        def publish(c):
            return "ok"
        namespace = Collection()
        namespace.add_task(publish)
        assert namespace["publish"] is publish and namespace["pub"] is publish
        assert namespace.default == "publish"
    elif root_id == "A07":
        @invoke.task
        def migrate(c):
            return c.config.project.target
        child = Collection("db", migrate)
        child.configure({"project": {"target": "database"}})
        root = Collection()
        root.add_collection(child)
        task, config = root.task_with_config("db.migrate")
        assert task is migrate and config["project"]["target"] == "database"
    elif root_id == "A08":
        config = Config(
            defaults={"project": {"target": "base", "count": 1}},
            overrides={"project": {"target": "override"}}, lazy=True,
        )
        assert config.project.target == "override" and config.project.count == 1
        cloned = config.clone()
        cloned.load_overrides({"project": {"target": "clone"}})
        assert cloned.project.target == "clone" and config.project.target == "override"
    elif root_id == "I01":
        seen = []
        @invoke.task
        def prepare(c):
            seen.append("prepare")
        @invoke.task(pre=[prepare])
        def build(c):
            seen.append("build")
        namespace = Collection(prepare, build)
        invoke.Executor(namespace, Config(lazy=True)).execute("build")
        assert seen == ["prepare", "build"]
    elif root_id == "I02":
        seen = []
        @invoke.task
        def show(c):
            seen.append(c.config.project.target)
        child = Collection("ops", show)
        child.configure({"project": {"target": "artifact"}})
        root = Collection()
        root.add_collection(child)
        invoke.Executor(root, Config(lazy=True)).execute("ops.show")
        assert seen == ["artifact"]
    elif root_id == "I03":
        @invoke.task(name="publish", aliases=("pub",), default=True)
        def publish(c):
            return None
        namespace = Collection(publish)
        program = invoke.Program(namespace=namespace)
        assert program.run(["invoke", "--list"], exit=False) is None
        assert namespace["publish"] is publish and namespace["pub"] is publish
    elif root_id == "I04":
        seen = []
        @invoke.task
        def left(c):
            seen.append(("left", id(c)))
        @invoke.task
        def right(c):
            seen.append(("right", id(c)))
        results = invoke.Executor(Collection(left, right), Config(lazy=True)).execute("left", "right")
        assert [name for name, _ in seen] == ["left", "right"]
        assert len(results) == 2 and all(result is None for result in results.values())
    elif root_id == "S01":
        seen = []
        @invoke.task(name="compile", aliases=("c",))
        def compile_task(c, target="wheel"):
            seen.append((target, c.config.release.channel))
        namespace = Collection(compile_task)
        namespace.configure({"release": {"channel": "stable"}})
        invoke.Executor(namespace, Config(lazy=True)).execute(("c", {"target": "sdist"}))
        assert seen == [("sdist", "stable")]
    elif root_id == "S02":
        seen = []
        @invoke.task(name="deploy")
        def deploy(c, channel="stable"):
            seen.append(channel)
        namespace = Collection(deploy)
        program = invoke.Program(namespace=namespace)
        program.run(["invoke", "deploy", "--channel", "nightly"], exit=False)
        assert seen == ["nightly"]
    else:
        raise KeyError(root_id)
