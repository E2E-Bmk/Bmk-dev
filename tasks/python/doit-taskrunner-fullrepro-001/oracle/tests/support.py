from __future__ import annotations

from dataclasses import replace
import importlib
import io
import os
from pathlib import Path
import sys
from typing import Any, Callable


def expect(error: type[BaseException], function: Callable[[], Any]) -> BaseException:
    try:
        function()
    except error as exc:
        return exc
    raise AssertionError(f"expected {error.__name__}")


def native_case(root_id: str, tmp_path: Path) -> None:
    doit = importlib.import_module("doit")
    task_mod = importlib.import_module("doit.task")
    action_mod = importlib.import_module("doit.action")
    tools = importlib.import_module("doit.tools")
    if root_id == "A01":
        assert doit.__version__ == (0, 38, "dev0")
        assert Path(doit.__file__).resolve().is_relative_to(Path(os.environ["SPEC2REPO_CANDIDATE_ROOT"]).resolve())
        assert importlib.import_module("doit.doit_cmd").DoitMain and importlib.import_module("doit.cmd_base").ModuleTaskLoader
    elif root_id == "A02":
        task = task_mod.Task("build", [lambda: None], file_dep=["input"], targets=["output"], doc="docs", meta={"owner": "x"})
        assert task.name == "build" and task.file_dep == {"input"} and task.targets == ["output"]
        assert task.doc == "docs" and task.meta == {"owner": "x"}
    elif root_id == "A03":
        group = task_mod.Task("all", None, task_dep=["one", "two"])
        assert group.name == "all" and group.actions == [] and group.task_dep == ["one", "two"]
    elif root_id == "A04":
        task = task_mod.dict_to_task({"name": "build", "actions": ["echo ok"], "targets": ["out"]})
        assert task.name == "build" and task.targets == ["out"] and task.actions
        expect(Exception, lambda: task_mod.dict_to_task({"actions": []}))
    elif root_id == "A05":
        text = action_mod.PythonAction(lambda: "value"); assert text.execute() is None and text.result == "value"
        values = action_mod.PythonAction(lambda: {"answer": 42}); assert values.execute() is None and values.values == {"answer": 42}
        failed = action_mod.PythonAction(lambda: False).execute(); assert isinstance(failed, action_mod.TaskFailed)
    elif root_id == "A06":
        command = action_mod.CmdAction([sys.executable, "-c", "import sys;assert sys.argv[1]=='two words'", "two words"])
        assert command.execute(io.StringIO(), io.StringIO()) is None
        failed = action_mod.CmdAction([sys.executable, "-c", "import sys;sys.exit(7)"]).execute(io.StringIO(), io.StringIO())
        assert isinstance(failed, action_mod.TaskFailed)
    elif root_id == "A07":
        task = task_mod.Task("x", []); assert tools.run_once(task, {}) is False
        task.executed = True; assert tools.run_once(task, {"result": True}) is False
        checker = tools.config_changed({"a": [1, 2]}); assert checker(task, {}) is False
        assert checker(task, {"_config_changed": checker.config_digest}) is True
    elif root_id == "A08":
        folder = tmp_path / "folder"; tools.create_folder(str(folder)); tools.create_folder(str(folder)); assert folder.is_dir()
        target = tmp_path / "target"; target.write_text("ok", encoding="utf-8")
        task = task_mod.Task("clean", [], targets=[str(target)])
        task_mod.clean_targets(task, True); assert target.exists()
        task_mod.clean_targets(task, False); assert not target.exists()
    elif root_id == "I01":
        loader_type = importlib.import_module("doit.cmd_base").ModuleTaskLoader
        loader = loader_type({"task_build": lambda: {"actions": [lambda: None], "task_dep": ["prepare"]}, "task_prepare": lambda: {"actions": []}})
        assert set(loader.namespace) >= {"task_build", "task_prepare"}
        build = task_mod.dict_to_task({"name": "build", **loader.namespace["task_build"]()})
        assert build.task_dep == ["prepare"]
    elif root_id == "I02":
        tasks = {name: task_mod.Task(name, [], task_dep=deps) for name, deps in {"base": [], "left": ["base"], "right": ["base"], "other": []}.items()}
        selected: list[str] = []
        def visit(name: str) -> None:
            for dep in tasks[name].task_dep: visit(dep)
            if name not in selected: selected.append(name)
        visit("left"); visit("right")
        assert selected == ["base", "left", "right"] and "other" not in selected
    elif root_id == "I03":
        task = task_mod.Task("x", []); task.options = {}; action = action_mod.PythonAction(lambda: {"value": "new"}, task=task)
        assert action.execute() is None and action.values == {"value": "new"}
        checker = tools.config_changed({"mode": "new"}); assert checker(task, {}) is False
        assert bool(checker(task, {"_config_changed": checker.config_digest})) is True
    elif root_id == "I04":
        owned = tmp_path / "owned"; sibling = tmp_path / "sibling"; owned.write_text("x"); sibling.write_text("y")
        task = task_mod.Task("x", [], targets=[str(owned)]); task_mod.clean_targets(task, False)
        assert not owned.exists() and sibling.read_text() == "y"
    elif root_id == "S01":
        task = task_mod.dict_to_task({"name": "build", "actions": [lambda: {"value": 2}], "targets": [str(tmp_path / "out")]})
        task.options = {}; action = task.actions[0]; assert action.execute() is None and action.values == {"value": 2}
        task.executed = True; assert tools.run_once(task, {}) is False
        checker = tools.config_changed({"task": task.name}); assert checker(task, {}) is False
        assert bool(checker(task, {"_config_changed": checker.config_digest})) is True
    elif root_id == "S02":
        bad = action_mod.PythonAction(lambda: False); assert isinstance(bad.execute(), action_mod.TaskFailed)
        corrected = action_mod.PythonAction(lambda: "fixed"); assert corrected.execute() is None and corrected.result == "fixed"
        target = tmp_path / "fixed"; target.write_text("yes"); task = task_mod.Task("fixed", [], targets=[str(target)])
        task_mod.clean_targets(task, False); assert not target.exists()
    else:
        raise KeyError(root_id)


def workflow() -> Any:
    return importlib.import_module("doit.workflow")


def atomic_case(root_id: str, tmp_path: Path) -> None:
    w = workflow()
    if root_id == "A09":
        store = w.TaskDefinitionCatalog(tmp_path / "definitions")
        receipt = store.prepare("build", {"actions": ["echo"], "task_dep": []}, owner="alice", operation_id="d1")
        assert receipt.state == "prepared"; expect(KeyError, lambda: store.get("build"))
        snapshot = w.TaskDefinitionCatalog(tmp_path / "definitions").commit(receipt); assert snapshot.name == "build" and snapshot.generation == 1
    elif root_id == "A10":
        store = w.TaskDefinitionCatalog(tmp_path / "definitions")
        receipt = store.prepare("build", {"actions": ["a"]}, owner="alice", operation_id="same")
        one = store.commit(receipt); two = store.commit(receipt); assert one == two
        expect(w.WorkflowError, lambda: store.prepare("build", {"actions": ["b"]}, owner="alice", operation_id="same")); assert store.get("build") == one
    elif root_id == "A11":
        registry = w.SelectionPlanRegistry(tmp_path / "selection")
        plan = registry.acquire("run-1", ["build"], {"base": [], "build": ["base"]}, owner="alice", operation_id="s1")
        assert plan.selected == ("base", "build") and plan.generation == 1 and registry.current("run-1") == plan
    elif root_id == "A12":
        registry = w.SelectionPlanRegistry(tmp_path / "selection")
        old = registry.acquire("run", ["x"], {"x": []}, owner="alice", operation_id="s1")
        new = registry.handoff(old, new_owner="bob", operation_id="s2")
        expect(w.StaleGenerationError, lambda: registry.release(old, operation_id="s3")); assert new.selected == old.selected and registry.current("run").owner == "bob"
    elif root_id == "A13":
        journal = w.TaskResultJournal(tmp_path / "journal")
        attempt = journal.begin("build", owner="alice", operation_id="j1")
        completed = journal.complete(attempt, result="ok", values={"x": 1})
        acknowledged = journal.acknowledge(completed, owner="alice", operation_id="j2")
        assert (attempt.state, completed.state, acknowledged.state) == ("prepared", "completed", "acknowledged") and journal.current("build") == acknowledged
    elif root_id == "A14":
        index = w.TargetArtifactIndex(tmp_path / "targets")
        receipt = index.prepare("build", {"a.txt": "héllo", "b.bin": b"\x00\xff"}, owner="alice", operation_id="t1")
        expect(KeyError, lambda: index.current("build")); snapshot = index.publish(receipt)
        assert index.read("build", "a.txt") == "héllo".encode() and index.read("build", "b.bin") == b"\x00\xff" and index.verify(snapshot)
    elif root_id == "A15":
        ledger = w.LifecycleObligationLedger(tmp_path / "life")
        item = ledger.open("build", ("one", "two"), ("one", "two"), owner="alice", operation_id="l1")
        item = ledger.setup(item, "one"); item = ledger.setup(item, "two"); item = ledger.body(item, "success")
        item = ledger.teardown(item, "two"); item = ledger.teardown(item, "one"); item = ledger.close(item)
        assert item.state == "closed" and item.completed_teardowns == ("two", "one")
    elif root_id == "A16":
        outbox = w.ReporterOutbox(tmp_path / "outbox")
        receipt = outbox.prepare("batch", ({"event": "done"},), owner="alice", operation_id="o1")
        batch = outbox.publish(receipt); claimed = outbox.claim("batch", owner="bob", operation_id="o2")
        acknowledged = outbox.acknowledge(claimed, owner="bob", operation_id="o3")
        assert (batch.state, claimed.state, acknowledged.state) == ("published", "claimed", "acknowledged") and outbox.pending() == ()
    else:
        raise KeyError(root_id)


def _owners(tmp_path: Path) -> tuple[Any, Any, Any, Any, Any, Any]:
    w = workflow()
    return (w.TaskDefinitionCatalog(tmp_path / "d"), w.SelectionPlanRegistry(tmp_path / "s"), w.TaskResultJournal(tmp_path / "j"),
            w.TargetArtifactIndex(tmp_path / "t"), w.LifecycleObligationLedger(tmp_path / "l"), w.ReporterOutbox(tmp_path / "o"))


def integration_case(root_id: str, tmp_path: Path) -> None:
    w = workflow(); definitions, selections, journal, targets, lifecycle, outbox = _owners(tmp_path)
    definition = definitions.commit(definitions.prepare("build", {"task_dep": [], "targets": ["out"]}, owner="alice", operation_id="d1"))
    plan = selections.acquire("run", ["build"], {"build": []}, owner="alice", operation_id="s1")
    if root_id == "I05":
        prepared = definitions.prepare("build", {"task_dep": [], "targets": ["new"]}, owner="alice", operation_id="d2")
        assert definitions.get("build") == definition and plan.selected == ("build",) and definitions.recover("d2", owner="alice") == prepared
    elif root_id == "I06":
        expect(w.WorkflowError, lambda: definitions.prepare("build", {"targets": ["a", "a"]}, owner="alice", operation_id="bad")); assert definitions.get("build") == definition
        attempt = journal.begin("build", owner="alice", operation_id="j1", prerequisites=(definition.receipt,)); assert definition.receipt.digest in attempt.receipt.prerequisites
    elif root_id == "I07":
        snapshot = targets.seal("build", {"out": "one"}, owner="alice", operation_id="t1", prerequisites=(definition.receipt,))
        assert definition.receipt.digest in snapshot.receipt.prerequisites and w.TaskDefinitionCatalog(tmp_path / "d").get("build") == definition
    elif root_id == "I08":
        closure = selections.acquire("run-2", ["left", "right", "left"], {"base": [], "left": ["base"], "right": ["base"]}, owner="alice", operation_id="s2")
        assert closure.selected == ("base", "left", "right") and len(closure.selected) == len(set(closure.selected))
    elif root_id == "I09":
        moved = selections.handoff(plan, new_owner="bob", operation_id="s2"); expect(w.StaleGenerationError, lambda: selections.release(plan, operation_id="s3"))
        attempt = journal.begin("build", owner=moved.owner, operation_id="j1", prerequisites=(moved.receipt,)); assert attempt.owner == "bob"
    elif root_id == "I10":
        moved = selections.handoff(plan, new_owner="bob", operation_id="s2")
        receipt = outbox.prepare("run", ({"selected": list(moved.selected)},), owner=moved.owner, operation_id="o1", prerequisites=(moved.receipt,))
        assert outbox.publish(receipt).owner == "bob" and selections.current("run").selected == ("build",)
    elif root_id == "I11":
        expect(w.WorkflowError, lambda: selections.acquire("bad", ["missing"], {"build": []}, owner="alice", operation_id="s2"))
        attempt = journal.begin(plan.selected[0], owner="alice", operation_id="j1", prerequisites=(plan.receipt,)); assert attempt.task == "build"
    elif root_id == "I12":
        attempt = journal.begin("build", owner="alice", operation_id="j1"); failed = journal.fail(attempt, category="failure", detail="bad")
        item = lifecycle.open("build", ("one",), ("one",), owner="alice", operation_id="l1", prerequisites=(failed.receipt,))
        item = lifecycle.setup(item, "one"); item = lifecycle.body(item, "failure"); item = lifecycle.teardown(item, "one"); assert lifecycle.close(item).state == "closed"
        expect(w.IncompleteWorkflowError, lambda: journal.acknowledge(failed, owner="alice", operation_id="j2")); expect(KeyError, lambda: journal.current("build"))
    elif root_id == "I13":
        attempt = journal.begin("build", owner="alice", operation_id="j1"); completed = journal.complete(attempt, result="ok")
        snapshot = targets.seal("build", {"out": "ok"}, owner="alice", operation_id="t1", prerequisites=(completed.receipt,)); assert targets.verify(snapshot)
        acknowledged = journal.acknowledge(completed, owner="alice", operation_id="j2"); assert journal.current("build") == acknowledged
    elif root_id == "I14":
        attempt = journal.begin("build", owner="alice", operation_id="j1"); failed = journal.fail(attempt, category="error")
        receipt = outbox.prepare("failure", ({"state": "failed"},), owner="alice", operation_id="o1", prerequisites=(failed.receipt,)); batch = outbox.publish(receipt)
        expect(w.IncompleteWorkflowError, lambda: journal.acknowledge(failed, owner="alice", operation_id="j2")); assert dict(outbox.events(batch.batch_id)[0])["state"] == "failed"
    elif root_id == "I15":
        snapshot = targets.seal("build", {"out": "one"}, owner="alice", operation_id="t1", prerequisites=(definition.receipt,)); assert definition.receipt.digest in snapshot.receipt.prerequisites
    elif root_id == "I16":
        prepared = targets.prepare("build", {"out": "new"}, owner="alice", operation_id="t1"); expect(KeyError, lambda: targets.current("build"))
        recovered = targets.recover("t1", owner="alice"); assert recovered == prepared and targets.publish(recovered).targets == (("out", "6e6577"),)
    elif root_id == "I17":
        one = targets.seal("one", {"one": "1"}, owner="alice", operation_id="t1"); two = targets.seal("two", {"two": "2"}, owner="alice", operation_id="t2")
        changed = targets.seal("one", {"one": "new"}, owner="alice", operation_id="t3"); assert changed.generation == one.generation + 1 and targets.current("two") == two
    elif root_id == "I18":
        snapshot = targets.seal("build", {"out": "ok"}, owner="alice", operation_id="t1")
        altered = replace(snapshot, receipt=replace(snapshot.receipt, digest="0" * 64)); expect(w.IntegrityError, lambda: targets.verify(altered))
        assert targets.read("build", "out") == b"ok" and outbox.pending() == ()
    elif root_id == "I19":
        item = lifecycle.open("build", ("setup",), ("teardown",), owner="alice", operation_id="l1", prerequisites=(plan.receipt,)); assert plan.receipt.digest in item.receipt.prerequisites
    elif root_id == "I20":
        item = lifecycle.open("build", ("outer", "inner"), ("outer", "inner"), owner="alice", operation_id="l1")
        item = lifecycle.setup(item, "outer"); item = lifecycle.setup(item, "inner"); item = lifecycle.body(item, "failure")
        item = lifecycle.teardown(item, "inner"); item = lifecycle.teardown(item, "outer"); assert lifecycle.close(item).completed_teardowns == ("inner", "outer")
    elif root_id == "I21":
        old = targets.seal("build", {"out": "old"}, owner="alice", operation_id="t1")
        item = lifecycle.open("build", ("setup",), ("teardown",), owner="alice", operation_id="l1"); item = lifecycle.setup(item, "setup")
        expect(w.IncompleteWorkflowError, lambda: lifecycle.close(item)); assert targets.current("build") == old
    elif root_id == "I22":
        item = lifecycle.open("build", ("setup",), ("teardown",), owner="alice", operation_id="l1"); item = lifecycle.setup(item, "setup"); item = lifecycle.body(item, "success"); item = lifecycle.teardown(item, "teardown"); closed = lifecycle.close(item)
        batch = outbox.publish(outbox.prepare("life", ({"state": "setup"}, {"state": "body"}, {"state": "teardown"}), owner="alice", operation_id="o1", prerequisites=(closed.receipt,)))
        assert [dict(event)["state"] for event in batch.events] == ["setup", "body", "teardown"]
    elif root_id == "I23":
        attempt = journal.begin("build", owner="alice", operation_id="j1"); acknowledged = journal.acknowledge(journal.complete(attempt), owner="alice", operation_id="j2")
        batch = outbox.publish(outbox.prepare("done", ({"task": "build"},), owner="alice", operation_id="o1", prerequisites=(acknowledged.receipt,)))
        claimed = outbox.claim("done", owner="worker", operation_id="o2"); assert outbox.acknowledge(claimed, owner="worker", operation_id="o3").state == "acknowledged" and outbox.pending() == ()
    elif root_id == "I24":
        moved = selections.handoff(plan, new_owner="bob", operation_id="s2")
        batch = outbox.publish(outbox.prepare("done", ({"task": "build"},), owner="bob", operation_id="o1", prerequisites=(moved.receipt,)))
        claimed = outbox.claim(batch.batch_id, owner="bob", operation_id="o2"); expect(w.OwnershipError, lambda: outbox.acknowledge(claimed, owner="alice", operation_id="o3"))
    else:
        raise KeyError(root_id)


def _definitions() -> dict[str, dict[str, Any]]:
    return {"base": {"task_dep": [], "targets": ["base.txt"]}, "build": {"task_dep": ["base"], "targets": ["build.txt"]}}


def system_case(root_id: str, tmp_path: Path) -> None:
    w = workflow(); coordinator = w.TaskWorkflowCoordinator(tmp_path / "workflow")
    if root_id in {"S03", "S04", "S05", "S06", "S07", "S08"}:
        prepared = coordinator.plan(_definitions(), ["build"], invocation_id="run", owner="alice", operation_id="w1")
    if root_id == "S03":
        executed = coordinator.execute(prepared); published = coordinator.publish(executed, owner="alice", operation_id="publish")
        assert coordinator.verify(published) and set(coordinator.owner_generations("build")) == {"definition", "selection", "journal", "artifact", "lifecycle", "outbox"}
    elif root_id == "S04":
        first = coordinator.publish(coordinator.execute(prepared), owner="alice", operation_id="publish")
        retry = coordinator.plan(_definitions(), ["build"], invocation_id="run-2", owner="alice", operation_id="w2")
        failed = coordinator.execute(retry, runner=lambda task, definition: 5); expect(w.IncompleteWorkflowError, lambda: coordinator.publish(failed, owner="alice", operation_id="bad"))
        assert coordinator.current("build") == first
    elif root_id == "S05":
        moved = coordinator.handoff("w1", current_owner="alice", new_owner="bob", transfer_operation_id="move")
        expect(w.OwnershipError, lambda: coordinator.execute(prepared)); published = coordinator.publish(coordinator.execute(moved), owner="bob", operation_id="publish")
        assert w.TaskWorkflowCoordinator(tmp_path / "workflow").current("build") == published
    elif root_id == "S06":
        same = coordinator.plan(_definitions(), ["build"], invocation_id="run", owner="alice", operation_id="w1"); assert same == prepared
        expect(w.WorkflowError, lambda: coordinator.plan({"other": {"task_dep": []}}, ["other"], invocation_id="run", owner="alice", operation_id="w1"))
        assert coordinator.verify(coordinator.recover("w1", owner="alice"))
    elif root_id == "S07":
        executed = coordinator.execute(prepared); reopened = w.TaskWorkflowCoordinator(tmp_path / "workflow")
        published = reopened.recover("w1", owner="alice"); assert published.state == "published" and reopened.recover("w1", owner="alice") == published
    elif root_id == "S08":
        published = coordinator.publish(coordinator.execute(prepared), owner="alice", operation_id="publish")
        altered = replace(published, digest="f" * 64, prerequisites=(published.digest,)); expect(w.IntegrityError, lambda: coordinator.verify(altered))
        assert coordinator.current("build") == published
    else:
        raise KeyError(root_id)
