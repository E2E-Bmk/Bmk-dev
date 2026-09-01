from __future__ import annotations

from pathlib import Path
from typing import Any, Callable


def raises(error: type[BaseException], call: Callable[[], Any]) -> BaseException:
    try:
        call()
    except error as exc:
        return exc
    raise AssertionError(f"expected {error.__name__}")


def published_snapshot(path: Path, name: str = "main", generation: int = 1):
    from whoosh.workflow import IndexSnapshotRegistry
    registry = IndexSnapshotRegistry(path)
    snapshot = None
    for number in range(1, generation + 1):
        prepared = registry.prepare(name, {"segments": [f"seg-{number}"], "count": number}, owner="indexer", operation_id=f"snapshot-{name}-{number}")
        snapshot = registry.publish(prepared)
    return registry, snapshot


def planned_workflow(path: Path, workflow_id: str = "wf", operation_id: str = "plan-wf"):
    from whoosh.workflow import SearchWorkflowCoordinator
    coordinator = SearchWorkflowCoordinator(path)
    planned = coordinator.plan(
        {"analyzer": "folded-text", "version": 1},
        [{"key": "doc-a", "body": "amber river"}, {"key": "doc-b", "body": "blue ridge"}],
        {"term": "amber"}, workflow_id=workflow_id, owner="planner", operation_id=operation_id,
    )
    return coordinator, planned

