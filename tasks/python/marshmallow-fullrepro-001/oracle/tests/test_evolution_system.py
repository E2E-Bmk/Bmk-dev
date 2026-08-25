from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import shutil

from marshmallow import Schema, fields, post_load, pre_load
from marshmallow.evolution import (
    EvolutionLoadCoordinator,
    PartialLoadJournal,
    ProcessTrace,
    PublicationError,
    PublicationJournal,
    SchemaEvolutionGraph,
    TransactionStateError,
)

from tests.evolution_support import ProfileSchema, graph_with_chain, make_success_journal, raises


def test_s03(tmp_path: Path) -> None:
    _, _, transaction = make_success_journal(tmp_path / "source")
    publications = PublicationJournal(tmp_path / "pub")
    prepared = publications.prepare("users", transaction, owner="worker", operation_id="prepare")
    assert PublicationJournal(tmp_path / "pub").recover("prepare", owner="worker") == prepared
    visible = PublicationJournal(tmp_path / "pub").publish(prepared)
    reopened = PublicationJournal(tmp_path / "pub")
    assert reopened.current("users") == visible
    assert reopened.recover("prepare", owner="worker") == visible


def _coordinator_with_graph(path: Path) -> EvolutionLoadCoordinator:
    coordinator = EvolutionLoadCoordinator(path)
    graph = coordinator.graph
    graph.declare("profile", "v1", {"given": "string", "years": "integer"}, operation_id="declare-v1")
    graph.declare("profile", "v2", {"name": "string", "age": "integer", "active": "boolean"}, predecessors=("v1",), operation_id="declare-v2")
    graph.connect("profile", "v1", "v2", renames={"given": "name", "years": "age"}, defaults={"active": True}, operation_id="connect")
    return coordinator


def _factory(schema_name: str, version: str, trace: ProcessTrace, index: int):
    class Target(ProfileSchema):
        @pre_load
        def before(self, data, **kwargs): trace.mark("factory-pre", (schema_name,)); return data
    return Target()


def test_s04(tmp_path: Path) -> None:
    coordinator = _coordinator_with_graph(tmp_path / "coordinator")
    run = coordinator.plan("users", "tx", "profile", "v2", (0, 1), owner="worker", operation_id="run")
    inputs = {0: ("v1", {"given": "Ada", "years": "37"}), 1: ("v1", {"given": "Grace", "years": "41"})}
    run = coordinator.execute(run, inputs, _factory)
    assert run.state == "sealed" and coordinator.verify(run)
    run = coordinator.publish(run, owner="worker", operation_id="publish")
    assert run.state == "published" and coordinator.verify(run)
    assert tuple(record.index for record in coordinator.current("users").records) == (0, 1)


def test_s05(tmp_path: Path) -> None:
    root = tmp_path / "coordinator"
    coordinator = _coordinator_with_graph(root)
    run = coordinator.plan("users", "tx", "profile", "v2", (0, 1, 2), owner="worker", operation_id="run")
    inputs = {index: ("v1", {"given": f"user-{index}", "years": str(index + 20)}) for index in range(3)}
    interrupted = coordinator.execute(run, inputs, _factory, stop_after=1)
    first_record = coordinator.loads.get("tx").records[0]
    assert interrupted.state == "executing" and first_record.index == 0
    reopened = EvolutionLoadCoordinator(root)
    resumed = reopened.recover("run", owner="worker", inputs=inputs, schema_factory=_factory)
    assert resumed.state == "sealed" and reopened.loads.get("tx").records[0] == first_record
    assert tuple(record.index for record in reopened.loads.get("tx").records) == (0, 1, 2)


def test_s06(tmp_path: Path) -> None:
    coordinator = _coordinator_with_graph(tmp_path / "coordinator")
    run = coordinator.plan("users", "tx", "profile", "v2", (0, 1), owner="worker", operation_id="run")
    inputs = {0: ("v1", {"given": "Ada", "years": "37"}), 1: ("v1", {"given": "Broken", "years": "bad"})}
    run = coordinator.execute(run, inputs, _factory, allow_partial=True)
    run = coordinator.publish(run, owner="worker", operation_id="publish")
    visible = coordinator.current("users")
    assert run.state == "published" and tuple(record.index for record in visible.records) == (0,)
    assert tuple(record.index for record in visible.errors) == (1,)
    assert ("age",) in tuple(node.path for node in visible.errors[0].error.walk()) and coordinator.verify(run)


def test_s07(tmp_path: Path) -> None:
    coordinator = EvolutionLoadCoordinator(tmp_path / "coordinator")
    coordinator.graph.declare("family", "legacy", {"members": "list"}, operation_id="d1")
    coordinator.graph.declare("family", "current", {"people": "list", "active": "boolean"}, predecessors=("legacy",), operation_id="d2")
    coordinator.graph.connect("family", "legacy", "current", renames={"members": "people"}, defaults={"active": True}, operation_id="c1")
    traces: dict[int, ProcessTrace] = {}
    def factory(schema_name, version, trace, index):
        traces[index] = trace
        class Child(Schema):
            age = fields.Integer(required=True)
            @pre_load
            def child_pre(self, data, **kwargs): trace.mark("child-pre", (schema_name, "person")); return data
        class Family(Schema):
            people = fields.List(fields.Nested(Child()), required=True)
            active = fields.Boolean(required=True)
            @pre_load
            def parent_pre(self, data, **kwargs): trace.mark("parent-pre", (schema_name,)); return data
        return Family()
    run = coordinator.plan("families", "tx", "family", "current", (0, 1), owner="worker", operation_id="run")
    inputs = {0: ("legacy", {"members": [{"age": "7"}]}), 1: ("legacy", {"members": [{"age": "bad"}]})}
    run = coordinator.execute(run, inputs, factory, allow_partial=True)
    run = coordinator.publish(run, owner="worker", operation_id="publish")
    visible = coordinator.current("families")
    assert dict(visible.records[0].values) == {"active": True, "people": ((('age', 7),),)}
    assert ("people", 0, "age") in tuple(node.path for node in visible.errors[0].error.walk())
    assert tuple(event.phase for event in traces[0].events).index("migration-step") < tuple(event.phase for event in traces[0].events).index("parent-pre")
    assert coordinator.verify(run)


def test_s08(tmp_path: Path) -> None:
    source = tmp_path / "source"
    coordinator = _coordinator_with_graph(source)
    run = coordinator.plan("users", "tx", "profile", "v2", (0,), owner="worker", operation_id="run")
    run = coordinator.execute(run, {0: ("v1", {"given": "Ada", "years": "37"})}, _factory)
    run = coordinator.publish(run, owner="worker", operation_id="publish")
    moved = tmp_path / "moved"
    shutil.copytree(source, moved)
    reopened = EvolutionLoadCoordinator(moved)
    recovered = reopened.recover("run", owner="worker")
    assert recovered.state == "published" and reopened.verify(recovered)
    raises(TransactionStateError, lambda: reopened.recover("run", owner="intruder"))
    assert not reopened.verify(replace(recovered, transaction_digest="forged"))
    assert reopened.current("users").records[0].index == 0
