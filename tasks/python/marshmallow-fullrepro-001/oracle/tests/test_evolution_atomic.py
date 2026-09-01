from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from marshmallow import Schema, fields
from marshmallow.evolution import (
    EvolutionError,
    GraphError,
    MigrationConflictError,
    PartialLoadJournal,
    ProcessTrace,
    ProvenanceError,
    SchemaEvolutionGraph,
    TransactionStateError,
    error_tree,
)

from tests.evolution_support import graph_with_chain, raises, record_values


def test_a09(tmp_path: Path) -> None:
    definition = {"name": {"type": "string"}}
    graph = SchemaEvolutionGraph(tmp_path / "graph")
    first = graph.declare("user", "v1", definition, operation_id="declare-v1")
    definition["name"]["type"] = "changed"
    reopened = SchemaEvolutionGraph(tmp_path / "graph").version("user", "v1")
    assert first == reopened and reopened.schema == "user" and reopened.predecessors == ()
    assert dict(reopened.definition)["name"] != {"type": "changed"}


def test_a10(tmp_path: Path) -> None:
    graph = SchemaEvolutionGraph(tmp_path / "graph")
    first = graph.declare("user", "v1", {"name": "string"}, operation_id="same")
    assert graph.declare("user", "v1", {"name": "string"}, operation_id="same") == first
    raises(EvolutionError, lambda: graph.declare("user", "v2", {"name": "string"}, operation_id="same"))
    assert graph.version("user", "v1") == first
    raises(GraphError, lambda: graph.version("user", "v2"))


def test_a11(tmp_path: Path) -> None:
    graph = SchemaEvolutionGraph(tmp_path / "graph")
    graph.declare("user", "v1", {"old": "string"}, operation_id="d1")
    graph.declare("user", "v2", {"new": "string", "flag": "boolean"}, predecessors=("v1",), operation_id="d2")
    defaults = {"flag": [True]}
    step = graph.connect("user", "v1", "v2", renames={"old": "new"}, defaults=defaults, drops=("unused",), operation_id="c1")
    defaults["flag"].append(False)
    assert step.renames == (("old", "new"),) and dict(step.defaults)["flag"] == (True,)
    assert step.drops == ("unused",) and graph.recover("c1") == step


def test_a12(tmp_path: Path) -> None:
    graph = graph_with_chain(tmp_path / "graph", "user")
    plan = graph.plan("user", "v1", "v3")
    assert plan.versions == ("v1", "v2", "v3")
    assert tuple((step.source, step.target) for step in plan.steps) == (("v1", "v2"), ("v2", "v3"))
    assert len(plan.digest) == 64


def test_a13(tmp_path: Path) -> None:
    graph = graph_with_chain(tmp_path / "graph")
    journal = PartialLoadJournal(tmp_path / "loads", graph)
    item = journal.begin("batch", "profile", "v3", (7, 2), owner="worker", operation_id="begin")
    assert item.expected == (7, 2) and item.records == () and item.state == "open"
    assert journal.recover("begin", owner="worker") == item
    raises(TransactionStateError, lambda: journal.begin("other", "profile", "v3", (1, 1), owner="worker", operation_id="bad"))


def test_a14(tmp_path: Path) -> None:
    class Target(Schema):
        name = fields.String(required=True)
        age = fields.Integer(required=True)
        active = fields.Boolean(required=True)

    graph = graph_with_chain(tmp_path / "graph")
    journal = PartialLoadJournal(tmp_path / "loads", graph)
    item = journal.begin("batch", "profile", "v3", (0,), owner="worker", operation_id="begin")
    item = journal.stage(item, 0, {"given": "Ada", "years": "37"}, "v1", Target())
    assert item.accepted == (0,) and item.rejected == ()
    assert record_values(item.records[0]) == {"name": "Ada", "age": 37, "active": True}
    assert journal.get("batch") == item


def test_a15(tmp_path: Path) -> None:
    tree = error_tree({"rows": {1: {"age": ["bad integer"]}, 3: {"name": ["missing"]}}}, stage="load", source_version="v1", target_version="v3")
    paths = tuple(node.path for node in tree.walk())
    assert paths == ((), ("rows",), ("rows", 1), ("rows", 1, "age"), ("rows", 3), ("rows", 3, "name"))
    assert tree.walk()[3].messages == ("bad integer",)
    assert all(node.source_version == "v1" and node.target_version == "v3" for node in tree.walk())


def test_a16(tmp_path: Path) -> None:
    trace = ProcessTrace()
    trace.enter(("parent",), input_path=(4,))
    trace.mark("pre-load", ("parent",), input_path=(4,))
    trace.enter(("parent", "child"), input_path=(4, "child"))
    trace.mark("field-load", ("parent", "child"), field_path=("age",))
    raises(ProvenanceError, lambda: trace.leave(("parent",)))
    trace.leave(("parent", "child"))
    trace.leave(("parent",))
    assert tuple(event.sequence for event in trace.events) == tuple(range(1, 7))
    assert tuple(event.phase for event in trace.span(("parent", "child"))) == ("enter", "field-load", "leave")
