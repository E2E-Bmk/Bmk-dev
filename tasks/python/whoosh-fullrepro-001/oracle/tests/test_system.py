from __future__ import annotations

from pathlib import Path

from tests.helpers import planned_workflow, published_snapshot, raises


def test_s01(tmp_path: Path) -> None:
    from whoosh.workflow import AnalysisRecipeCatalog, DocumentIngestJournal, IndexSnapshotRegistry, ResultExportOutbox, SearchSessionRegistry
    recipe_owner = AnalysisRecipeCatalog(tmp_path / "recipe")
    recipe = recipe_owner.commit(recipe_owner.prepare("body", {"tokenizer": "regex", "filters": ["lower"]}, owner="planner", operation_id="recipe"))
    ingest_owner = DocumentIngestJournal(tmp_path / "ingest")
    ingest = ingest_owner.begin("batch", [{"key": "a", "body": "amber"}, {"key": "b", "body": "blue"}], owner="writer", operation_id="ingest", prerequisites=[recipe.digest])
    ingest = ingest_owner.commit(ingest_owner.checkpoint(ingest, accepted=["a", "b"], rejected={}, operation_id="checkpoint"))
    snapshots = IndexSnapshotRegistry(tmp_path / "snapshot")
    snapshot = snapshots.publish(snapshots.prepare("main", {"keys": ingest.value["accepted"], "count": 2}, owner="indexer", operation_id="snapshot", prerequisites=[ingest.digest]))
    lease = snapshots.acquire("main", owner="reader", operation_id="lease")
    sessions = SearchSessionRegistry(tmp_path / "session")
    session = sessions.open("search", snapshot, {"term": "amber"}, [{"key": "a", "rank": 1}], owner="reader", operation_id="session", prerequisites=[lease.digest])
    rows, end = sessions.page(session, size=10)
    outbox = ResultExportOutbox(tmp_path / "export")
    export = outbox.publish(outbox.prepare("results", rows, owner="reader", operation_id="export", prerequisites=[session.digest]))
    assert end is None and outbox.rows(export) == ({"key": "a", "rank": 1},)
    assert recipe.digest in ingest.prerequisites and ingest.digest in snapshot.prerequisites and session.digest in export.prerequisites


def test_s02(tmp_path: Path) -> None:
    coordinator, first_plan = planned_workflow(tmp_path, workflow_id="wf", operation_id="plan-1")
    first = coordinator.publish(coordinator.execute(first_plan), owner="planner", operation_id="publish-1")
    second_plan = coordinator.plan({"version": 2}, [{"key": "x", "body": "silver"}], {"term": "silver"}, workflow_id="wf", owner="planner", operation_id="plan-2")
    assert second_plan.generation == 2 and coordinator.current("wf") == first
    second = coordinator.publish(coordinator.execute(second_plan), owner="planner", operation_id="publish-2")
    assert second.generation == 2 and coordinator.current("wf") == second and coordinator.verify(second)


def test_s03(tmp_path: Path) -> None:
    coordinator, planned = planned_workflow(tmp_path)
    executed = coordinator.execute(planned)
    reopened = type(coordinator)(tmp_path)
    recovered = reopened.recover("plan-wf", owner="planner")
    assert recovered == executed and reopened.current("wf") is None
    published = reopened.publish(recovered, owner="planner", operation_id="publish")
    assert type(coordinator)(tmp_path).verify(published) and type(coordinator)(tmp_path).views("wf") == published.value["views"]


def test_s04(tmp_path: Path) -> None:
    coordinator, first_plan = planned_workflow(tmp_path, operation_id="first")
    first = coordinator.publish(coordinator.execute(first_plan), owner="planner", operation_id="publish-first")
    second = coordinator.plan({"version": 2}, [{"key": "x"}], {"term": "x"}, workflow_id="wf", owner="planner", operation_id="second")
    def broken(documents, query):
        raise RuntimeError("analysis crashed")
    raises(RuntimeError, lambda: coordinator.execute(second, runner=broken))
    assert coordinator.current("wf") == first
    recovered = coordinator.recover("second", owner="planner", runner=lambda documents, query: [{"key": "x"}])
    assert recovered.state == "executed" and coordinator.current("wf") == first


def test_s05(tmp_path: Path) -> None:
    from whoosh.workflow import ResultExportOutbox, SearchSessionRegistry
    snapshots, first = published_snapshot(tmp_path / "snap", generation=1)
    lease = snapshots.acquire("main", owner="reader", operation_id="lease")
    second = snapshots.publish(snapshots.prepare("main", {"segments": ["new"], "count": 2}, owner="indexer", operation_id="new"))
    sessions = SearchSessionRegistry(tmp_path / "sessions")
    session = sessions.open("search", first, {"term": "a"}, [{"key": "a"}, {"key": "b"}, {"key": "c"}], owner="reader", operation_id="open", prerequisites=[lease.digest])
    rows1, cursor = sessions.page(session, size=2); rows2, end = sessions.page(session, cursor=cursor, size=2)
    outbox = ResultExportOutbox(tmp_path / "outbox")
    pending = outbox.publish(outbox.prepare("delivery", rows1 + rows2, owner="reader", operation_id="prepare", prerequisites=[session.digest]))
    claim = outbox.claim(pending, owner="delivery", operation_id="claim")
    assert snapshots.current("main") == second and end is None and outbox.rows(claim) == tuple(rows1 + rows2)
    outbox.acknowledge(claim, operation_id="ack"); sessions.close(session, operation_id="close"); snapshots.release(lease, operation_id="release")
    assert outbox.pending() == ()


def test_s06(tmp_path: Path) -> None:
    from dataclasses import replace
    from whoosh.workflow import IntegrityError
    coordinator, planned = planned_workflow(tmp_path)
    published = coordinator.publish(coordinator.execute(planned), owner="planner", operation_id="publish")
    assert coordinator.verify(published)
    altered = replace(published, prerequisites=published.prerequisites[:-1] + ("0" * 64,))
    raises(IntegrityError, lambda: coordinator.verify(altered))
    assert coordinator.current("wf") == published and len(coordinator.views("wf")) == 5


def test_s07(tmp_path: Path) -> None:
    from whoosh import index
    from whoosh.fields import ID, TEXT, Schema
    from whoosh.query import Every, Term
    directory = tmp_path / "indexes"; directory.mkdir(); schema = Schema(key=ID(stored=True, unique=True), body=TEXT(stored=True))
    blue = index.create_in(str(directory), schema, indexname="blue"); green = index.create_in(str(directory), schema, indexname="green")
    with blue.writer() as writer: writer.add_document(key="a", body="old amber"); writer.add_document(key="b", body="blue")
    with green.writer() as writer: writer.add_document(key="g", body="green")
    with blue.writer() as writer: writer.update_document(key="a", body="new amber"); writer.delete_by_term("key", "b")
    reopened_blue = index.open_dir(str(directory), indexname="blue"); reopened_green = index.open_dir(str(directory), indexname="green")
    with reopened_blue.searcher() as searcher:
        hits = searcher.search(Every(), limit=None); assert [(hit["key"], hit["body"]) for hit in hits] == [("a", "new amber")]
        assert len(searcher.search(Term("body", "old"), limit=None)) == 0
    with reopened_green.searcher() as searcher: assert [hit["key"] for hit in searcher.search(Every(), limit=None)] == ["g"]


def test_s08(tmp_path: Path) -> None:
    from whoosh.fields import ID, TEXT, Schema
    from whoosh.filedb.filestore import RamStorage
    from whoosh.query import And, Or, Term
    ix = RamStorage().create_index(Schema(key=ID(stored=True), body=TEXT(stored=True), group=ID(stored=True)))
    with ix.writer() as writer:
        writer.add_document(key="a", body="amber river", group="x"); writer.add_document(key="b", body="amber ridge", group="y"); writer.add_document(key="c", body="blue river", group="x")
    query = Or([Term("body", "amber"), Term("body", "river")]); permit = Term("group", "x"); exclude = Term("key", "c")
    with ix.searcher() as searcher:
        results = searcher.search(query, limit=None, filter=permit, mask=exclude, terms=True)
        assert [hit["key"] for hit in results] == ["a"] and results.has_matched_terms()
        assert set(results.matched_terms()) == {("body", b"amber"), ("body", b"river")}
        assert set(results[0].matched_terms()) == {("body", b"amber"), ("body", b"river")}

