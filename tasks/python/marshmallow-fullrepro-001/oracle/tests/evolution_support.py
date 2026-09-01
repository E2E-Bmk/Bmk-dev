from __future__ import annotations

from pathlib import Path
from typing import Any

from marshmallow import Schema, fields
from marshmallow.evolution import SchemaEvolutionGraph


def raises(error_type, function):
    try:
        function()
    except error_type as exc:
        return exc
    raise AssertionError(f"expected {error_type.__name__}")


def graph_with_chain(path: Path, schema: str = "profile") -> SchemaEvolutionGraph:
    graph = SchemaEvolutionGraph(path)
    graph.declare(schema, "v1", {"given": "string", "years": "integer"}, operation_id=f"{schema}-declare-v1")
    graph.declare(schema, "v2", {"name": "string", "years": "integer", "active": "boolean"}, predecessors=("v1",), operation_id=f"{schema}-declare-v2")
    graph.declare(schema, "v3", {"name": "string", "age": "integer", "active": "boolean"}, predecessors=("v2",), operation_id=f"{schema}-declare-v3")
    graph.connect(schema, "v1", "v2", renames={"given": "name"}, defaults={"active": True}, operation_id=f"{schema}-connect-v1-v2")
    graph.connect(schema, "v2", "v3", renames={"years": "age"}, drops=("retired",), operation_id=f"{schema}-connect-v2-v3")
    return graph


class ProfileSchema(Schema):
    name = fields.String(required=True)
    age = fields.Integer(required=True)
    active = fields.Boolean(required=True)


def record_values(record: Any) -> dict[str, Any]:
    return dict(record.values)


def make_success_journal(path: Path, *, transaction_id: str = "tx", owner: str = "worker"):
    from marshmallow.evolution import PartialLoadJournal

    graph = graph_with_chain(path / "graph")
    journal = PartialLoadJournal(path / "loads", graph)
    item = journal.begin(transaction_id, "profile", "v3", (0,), owner=owner, operation_id=f"begin-{transaction_id}")
    item = journal.stage(item, 0, {"given": "Ada", "years": "37"}, "v1", ProfileSchema())
    return graph, journal, journal.seal(item, allow_partial=False)
