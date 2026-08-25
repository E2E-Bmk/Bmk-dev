from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from marshmallow import Schema, ValidationError, fields, post_load, pre_load, validate
from marshmallow.evolution import (
    EvolutionError,
    GraphError,
    MigrationConflictError,
    PartialLoadJournal,
    ProcessTrace,
    ProvenanceError,
    PublicationError,
    PublicationJournal,
    SchemaEvolutionGraph,
    TransactionStateError,
)

from tests.evolution_support import ProfileSchema, graph_with_chain, make_success_journal, raises, record_values


def test_i05(tmp_path: Path) -> None:
    graph = SchemaEvolutionGraph(tmp_path / "graph")
    graph.declare("alpha", "v1", {"a": "integer"}, operation_id="a1")
    graph.declare("alpha", "v2", {"a": "integer"}, predecessors=("v1",), operation_id="a2")
    graph.declare("beta", "v1", {"b": "string"}, operation_id="b1")
    raises(GraphError, lambda: graph.declare("alpha", "v3", {}, predecessors=("missing",), operation_id="bad"))
    graph.connect("alpha", "v1", "v2", operation_id="forward")
    raises(GraphError, lambda: graph.connect("alpha", "v2", "v1", operation_id="cycle"))
    assert graph.version("beta", "v1").schema == "beta" and graph.plan("alpha", "v1", "v2").versions == ("v1", "v2")


def test_i06(tmp_path: Path) -> None:
    graph = graph_with_chain(tmp_path / "graph")
    before = graph.plan("profile", "v1", "v3")
    reopened = SchemaEvolutionGraph(tmp_path / "graph")
    assert reopened.plan("profile", "v1", "v3") == before
    assert reopened.recover("profile-connect-v1-v2") == before.steps[0]
    reopened.declare("other", "v1", {"x": "raw"}, operation_id="other-v1")
    assert reopened.version("profile", "v3").schema == "profile"


def test_i07(tmp_path: Path) -> None:
    graph = graph_with_chain(tmp_path / "graph")
    before = graph.plan("profile", "v1", "v3")
    raises(EvolutionError, lambda: graph.connect("profile", "v1", "v3", defaults={"x": 1}, operation_id="profile-connect-v1-v2"))
    raises(EvolutionError, lambda: graph.declare("profile", "v2", {"changed": True}, operation_id="new-operation"))
    assert SchemaEvolutionGraph(tmp_path / "graph").plan("profile", "v1", "v3") == before


def test_i08(tmp_path: Path) -> None:
    graph = graph_with_chain(tmp_path / "graph")
    document = {"given": "Ada", "years": "37", "retired": False, "note": {"keep": True}}
    migrated = graph.migrate(graph.plan("profile", "v1", "v3"), document)
    assert migrated == {"name": "Ada", "age": "37", "active": True, "note": {"keep": True}}
    assert document == {"given": "Ada", "years": "37", "retired": False, "note": {"keep": True}}


def test_i09(tmp_path: Path) -> None:
    graph = SchemaEvolutionGraph(tmp_path / "graph")
    for version in ("v1", "a", "b", "v3", "isolated"):
        graph.declare("item", version, {"value": version}, operation_id=f"declare-{version}")
    graph.connect("item", "v1", "a", operation_id="v1-a")
    graph.connect("item", "a", "v3", operation_id="a-v3")
    graph.connect("item", "v1", "b", operation_id="v1-b")
    graph.connect("item", "b", "v3", operation_id="b-v3")
    assert graph.plan("item", "v1", "v1").steps == ()
    raises(GraphError, lambda: graph.plan("item", "v1", "v3"))
    raises(GraphError, lambda: graph.plan("item", "v1", "isolated"))


def test_i10(tmp_path: Path) -> None:
    graph = SchemaEvolutionGraph(tmp_path / "graph")
    graph.declare("item", "v1", {"old": "string", "new": "string"}, operation_id="d1")
    graph.declare("item", "v2", {"new": "string"}, operation_id="d2")
    raises(MigrationConflictError, lambda: graph.connect("item", "v1", "v2", renames={"old": "new"}, defaults={"new": "x"}, operation_id="contradiction"))
    step = graph.connect("item", "v1", "v2", renames={"old": "new"}, operation_id="valid")
    raises(MigrationConflictError, lambda: graph.migrate(graph.plan("item", "v1", "v2"), {"old": "a", "new": "b"}))
    assert graph.recover("valid") == step


def test_i11(tmp_path: Path) -> None:
    seen = []
    class Target(ProfileSchema):
        @pre_load
        def inspect_target(self, data, **kwargs):
            seen.append(tuple(sorted(data)))
            return data
    graph = graph_with_chain(tmp_path / "graph")
    journal = PartialLoadJournal(tmp_path / "loads", graph)
    item = journal.begin("tx", "profile", "v3", (0,), owner="worker", operation_id="begin")
    item = journal.stage(item, 0, {"given": "Ada", "years": "37"}, "v1", Target())
    assert seen == [("active", "age", "name")]
    assert record_values(item.records[0]) == {"name": "Ada", "age": 37, "active": True}


def test_i12(tmp_path: Path) -> None:
    class Target(Schema):
        name = fields.String(required=True)
        age = fields.Integer(required=True)
        active = fields.Boolean(required=True)
    graph = graph_with_chain(tmp_path / "graph")
    journal = PartialLoadJournal(tmp_path / "loads", graph)
    item = journal.begin("tx", "profile", "v3", (0,), owner="worker", operation_id="begin")
    item = journal.stage(item, 0, {"given": "Ada", "years": "bad"}, "v1", Target())
    record = item.records[0]
    assert item.rejected == (0,) and record.state == "rejected"
    assert record_values(record) == {"name": "Ada", "active": True}
    assert ("age",) in tuple(node.path for node in record.error.walk())


def test_i13(tmp_path: Path) -> None:
    graph = graph_with_chain(tmp_path / "graph")
    journal = PartialLoadJournal(tmp_path / "loads", graph)
    initial = journal.begin("tx", "profile", "v3", (0,), owner="worker", operation_id="begin")
    raises(TransactionStateError, lambda: journal.seal(initial, allow_partial=False))
    current = journal.stage(initial, 0, {"given": "Ada", "years": "37"}, "v1", ProfileSchema())
    assert journal.stage(current, 0, {"given": "Ada", "years": "37"}, "v1", ProfileSchema()) == current
    raises(TransactionStateError, lambda: journal.stage(current, 0, {"given": "Grace", "years": "37"}, "v1", ProfileSchema()))
    raises(TransactionStateError, lambda: journal.stage(initial, 0, {"given": "Ada", "years": "37"}, "v1", ProfileSchema()))
    raises(TransactionStateError, lambda: journal.stage(current, 9, {}, "v1", ProfileSchema()))


def test_i14(tmp_path: Path) -> None:
    class Child(Schema):
        age = fields.Integer(required=True)
    class Target(Schema):
        rows = fields.List(fields.Nested(Child()), required=True)
    graph = SchemaEvolutionGraph(tmp_path / "graph")
    graph.declare("nested", "v1", {"rows": "children"}, operation_id="d1")
    journal = PartialLoadJournal(tmp_path / "loads", graph)
    item = journal.begin("tx", "nested", "v1", (0,), owner="worker", operation_id="begin")
    item = journal.stage(item, 0, {"rows": [{"age": "1"}, {"age": "bad"}]}, "v1", Target())
    paths = tuple(node.path for node in item.records[0].error.walk())
    assert ("rows", 1, "age") in paths and ("rows", 0) not in paths
    assert record_values(item.records[0]) == {"rows": ((('age', 1),), ())}


def test_i15(tmp_path: Path) -> None:
    class Target(Schema):
        score = fields.Integer(validate=[validate.Range(min=1, max=4), validate.OneOf([1, 2, 3, 4])])
    graph = SchemaEvolutionGraph(tmp_path / "graph")
    graph.declare("score", "v1", {"score_text": "string"}, operation_id="d1")
    graph.declare("score", "v2", {"score": "integer"}, operation_id="d2")
    graph.connect("score", "v1", "v2", renames={"score_text": "score"}, operation_id="c1")
    journal = PartialLoadJournal(tmp_path / "loads", graph)
    item = journal.begin("tx", "score", "v2", (0,), owner="worker", operation_id="begin")
    item = journal.stage(item, 0, {"score_text": "9"}, "v1", Target())
    node = next(node for node in item.records[0].error.walk() if node.path == ("score",))
    assert len(node.messages) == 2 and node.source_version == "v1" and node.target_version == "v2"


def test_i16(tmp_path: Path) -> None:
    class Child(Schema):
        required_value = fields.Integer(required=True)
        optional_value = fields.Integer(required=True)
    class Target(Schema):
        title = fields.String(required=True)
        child = fields.Nested(Child(), required=True)
    graph = SchemaEvolutionGraph(tmp_path / "graph")
    graph.declare("partial", "v1", {"title": "string", "child": "object"}, operation_id="d1")
    journal = PartialLoadJournal(tmp_path / "loads", graph)
    item = journal.begin("tx", "partial", "v1", (0,), owner="worker", operation_id="begin")
    item = journal.stage(item, 0, {"title": "kept", "child": {"required_value": "bad"}}, "v1", Target(), partial=("child.optional_value",))
    record = item.records[0]
    paths = tuple(node.path for node in record.error.walk())
    assert ("child", "required_value") in paths and ("child", "optional_value") not in paths
    assert record_values(record)["title"] == "kept"


def test_i17(tmp_path: Path) -> None:
    graph = graph_with_chain(tmp_path / "graph")
    journal = PartialLoadJournal(tmp_path / "loads", graph)
    item = journal.begin("tx", "profile", "v3", (0,), owner="worker", operation_id="begin")
    item = journal.stage(item, 0, {"given": "Ada", "years": "bad"}, "v1", ProfileSchema())
    reopened = PartialLoadJournal(tmp_path / "loads", SchemaEvolutionGraph(tmp_path / "graph")).get("tx")
    assert reopened == item and reopened.records[0].error.walk() == item.records[0].error.walk()
    raises(TransactionStateError, lambda: journal.seal(replace(item, digest="forged"), allow_partial=True))


def test_i18(tmp_path: Path) -> None:
    trace = ProcessTrace()
    order = []
    class Child(Schema):
        value = fields.Integer()
        @pre_load
        def child_pre(self, data, **kwargs): order.append("child-pre"); trace.mark("child-pre", ("nested", "child")); return data
        @post_load
        def child_post(self, data, **kwargs): order.append("child-post"); trace.mark("child-post", ("nested", "child")); return data
    class Parent(Schema):
        child = fields.Nested(Child())
        @pre_load
        def parent_pre(self, data, **kwargs): order.append("parent-pre"); trace.mark("parent-pre", ("nested",)); return data
        @post_load
        def parent_post(self, data, **kwargs): order.append("parent-post"); trace.mark("parent-post", ("nested",)); return data
    graph = SchemaEvolutionGraph(tmp_path / "graph"); graph.declare("nested", "v1", {"child": "object"}, operation_id="d1")
    journal = PartialLoadJournal(tmp_path / "loads", graph)
    item = journal.begin("tx", "nested", "v1", (0,), owner="worker", operation_id="begin")
    item = journal.stage(item, 0, {"child": {"value": "2"}}, "v1", Parent(), trace=trace)
    assert order == ["parent-pre", "child-pre", "child-post", "parent-post"]
    phases = tuple(event.phase for event in item.records[0].trace)
    assert phases.index("parent-pre") < phases.index("child-pre") < phases.index("child-post") < phases.index("parent-post")


def test_i19(tmp_path: Path) -> None:
    trace = ProcessTrace()
    class Target(ProfileSchema):
        @pre_load
        def hook(self, data, **kwargs): trace.mark("target-hook", ("profile",)); return data
    graph = graph_with_chain(tmp_path / "graph")
    journal = PartialLoadJournal(tmp_path / "loads", graph)
    item = journal.begin("tx", "profile", "v3", (0,), owner="worker", operation_id="begin")
    item = journal.stage(item, 0, {"given": "Ada", "years": "37"}, "v1", Target(), trace=trace)
    phases = tuple(event.phase for event in item.records[0].trace)
    assert phases == ("enter", "migration-plan", "migration-step", "migration-step", "pre-load", "target-hook", "post-load", "leave")


def test_i20(tmp_path: Path) -> None:
    graph = graph_with_chain(tmp_path / "graph")
    journal = PartialLoadJournal(tmp_path / "loads", graph)
    item = journal.begin("tx", "profile", "v3", (1, 2), owner="worker", operation_id="begin")
    item = journal.stage(item, 2, {"given": "two", "years": "2"}, "v1", ProfileSchema())
    item = journal.stage(item, 1, {"given": "one", "years": "1"}, "v1", ProfileSchema())
    assert tuple(record.index for record in item.records) == (1, 2)
    assert tuple(record.trace[0].input_path for record in item.records) == ((1,), (2,))
    assert all(tuple(event.sequence for event in record.trace) == tuple(range(1, len(record.trace) + 1)) for record in item.records)


def test_i21(tmp_path: Path) -> None:
    trace = ProcessTrace()
    class Child(Schema):
        value = fields.Integer(required=True)
        @pre_load
        def before(self, data, **kwargs): trace.mark("child-before", ("nested", "child")); return data
    class Parent(Schema):
        child = fields.Nested(Child())
        @pre_load
        def before(self, data, **kwargs): trace.mark("parent-before", ("nested",)); return data
    graph = SchemaEvolutionGraph(tmp_path / "graph"); graph.declare("nested", "v1", {"child": "object"}, operation_id="d1")
    journal = PartialLoadJournal(tmp_path / "loads", graph)
    item = journal.begin("tx", "nested", "v1", (0,), owner="worker", operation_id="begin")
    item = journal.stage(item, 0, {"child": {"value": "bad"}}, "v1", Parent(), trace=trace)
    phases = tuple(event.phase for event in item.records[0].trace)
    assert "parent-before" in phases and "child-before" in phases and phases[-2:] == ("validation-error", "leave")
    assert item.records[0].trace[-1].detail == "rejected"


def test_i22(tmp_path: Path) -> None:
    _, _, transaction = make_success_journal(tmp_path / "source")
    publications = PublicationJournal(tmp_path / "pub")
    prepared = publications.prepare("users", transaction, owner="worker", operation_id="prepare")
    assert prepared.state == "prepared" and prepared.records[0].index == 0
    raises(PublicationError, lambda: publications.current("users"))
    assert publications.recover("prepare", owner="worker") == prepared


def test_i23(tmp_path: Path) -> None:
    class Target(ProfileSchema):
        pass
    graph = graph_with_chain(tmp_path / "graph")
    journal = PartialLoadJournal(tmp_path / "loads", graph)
    item = journal.begin("tx", "profile", "v3", (0, 1), owner="worker", operation_id="begin")
    item = journal.stage(item, 0, {"given": "Ada", "years": "37"}, "v1", Target())
    item = journal.stage(item, 1, {"given": "Bad", "years": "no"}, "v1", Target())
    item = journal.seal(item, allow_partial=True)
    publications = PublicationJournal(tmp_path / "pub")
    visible = publications.publish(publications.prepare("users", item, owner="worker", operation_id="prepare"))
    assert visible.state == "published" and tuple(record.index for record in visible.records) == (0,)
    assert tuple(record.index for record in visible.errors) == (1,) and visible.errors[0].error is not None
    assert publications.current("users") == visible


def test_i24(tmp_path: Path) -> None:
    _, _, first_tx = make_success_journal(tmp_path / "first", transaction_id="first")
    _, _, second_tx = make_success_journal(tmp_path / "second", transaction_id="second")
    publications = PublicationJournal(tmp_path / "pub")
    first = publications.publish(publications.prepare("users", first_tx, owner="worker", operation_id="p1"))
    other = publications.publish(publications.prepare("other", second_tx, owner="worker", operation_id="p2"))
    second = publications.publish(publications.prepare("users", second_tx, owner="worker", operation_id="p3"))
    assert (first.generation, second.generation, other.generation) == (1, 2, 1)
    assert PublicationJournal(tmp_path / "pub").current("users") == second
    raises(EvolutionError, lambda: publications.prepare("changed", first_tx, owner="worker", operation_id="p3"))
