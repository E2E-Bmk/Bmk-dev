from __future__ import annotations

from pathlib import Path

from tests.helpers import planned_workflow, published_snapshot, raises


def test_i01(tmp_path: Path) -> None:
    from whoosh.workflow import AnalysisRecipeCatalog
    catalog = AnalysisRecipeCatalog(tmp_path)
    base = catalog.commit(catalog.prepare("base", {"tokenizer": "regex"}, owner="a", operation_id="p-base"))
    child = catalog.commit(catalog.prepare("child", {"filters": ["lower"]}, deps=["base"], owner="a", operation_id="p-child"))
    reopened = AnalysisRecipeCatalog(tmp_path)
    assert reopened.get("base") == base and reopened.get("child") == child and child.value["deps"] == ["base"]


def test_i02(tmp_path: Path) -> None:
    from whoosh.workflow import AnalysisRecipeCatalog, WorkflowError
    catalog = AnalysisRecipeCatalog(tmp_path)
    first = catalog.prepare("base", {"tokenizer": "regex"}, owner="a", operation_id="same")
    assert catalog.prepare("base", {"tokenizer": "regex"}, owner="a", operation_id="same") == first
    raises(WorkflowError, lambda: catalog.prepare("base", {"tokenizer": "ngram"}, owner="a", operation_id="same"))


def test_i03(tmp_path: Path) -> None:
    from whoosh.workflow import AnalysisRecipeCatalog, IntegrityError
    catalog = AnalysisRecipeCatalog(tmp_path)
    committed = catalog.commit(catalog.prepare("body", {"version": 1}, owner="a", operation_id="one"))
    raises(IntegrityError, lambda: catalog.prepare("next", {"version": 2}, deps=["missing"], owner="a", operation_id="bad"))
    raises(IntegrityError, lambda: catalog.prepare("body", {"version": 2}, deps=["body"], owner="a", operation_id="cycle"))
    assert catalog.get("body") == committed and catalog.get("next") is None


def test_i04(tmp_path: Path) -> None:
    from whoosh.workflow import AnalysisRecipeCatalog, OwnershipError
    catalog = AnalysisRecipeCatalog(tmp_path)
    prepared = catalog.prepare("body", {"version": 1}, owner="alice", operation_id="recipe")
    assert AnalysisRecipeCatalog(tmp_path).recover("recipe", owner="alice") == prepared
    raises(OwnershipError, lambda: catalog.recover("recipe", owner="bob"))


def test_i05(tmp_path: Path) -> None:
    from whoosh.workflow import DocumentIngestJournal
    journal = DocumentIngestJournal(tmp_path)
    batch = journal.begin("b", [{"key": "a", "rank": 1}, {"key": "b", "rank": 2}, {"key": "c", "rank": 3}], owner="writer", operation_id="begin")
    checked = journal.checkpoint(batch, accepted=["c", "a"], rejected={"b": "bad encoding"}, operation_id="check")
    committed = journal.commit(checked)
    reopened = DocumentIngestJournal(tmp_path).current("b")
    assert reopened == committed and reopened.value["accepted"] == ["a", "c"] and reopened.value["rejected"] == {"b": "bad encoding"}


def test_i06(tmp_path: Path) -> None:
    from whoosh.workflow import DocumentIngestJournal, IncompleteWorkflowError
    journal = DocumentIngestJournal(tmp_path)
    batch = journal.begin("b", [{"key": "a"}, {"key": "b"}], owner="writer", operation_id="begin")
    raises(IncompleteWorkflowError, lambda: journal.checkpoint(batch, accepted=["a"], rejected={}, operation_id="partial"))
    raises(IncompleteWorkflowError, lambda: journal.commit(batch))
    assert journal.current("b") is None


def test_i07(tmp_path: Path) -> None:
    from whoosh.workflow import DocumentIngestJournal, OwnershipError
    journal = DocumentIngestJournal(tmp_path)
    batch = journal.begin("b", [{"key": "a"}], owner="alice", operation_id="begin")
    forged = type(batch)(**{**batch.__dict__, "owner": "bob"})
    raises(OwnershipError, lambda: journal.checkpoint(forged, accepted=["a"], rejected={}, operation_id="foreign"))
    raises(OwnershipError, lambda: journal.recover("begin", owner="bob"))


def test_i08(tmp_path: Path) -> None:
    registry, first = published_snapshot(tmp_path, generation=1)
    lease = registry.acquire("main", owner="reader", operation_id="lease")
    prepared = registry.prepare("main", {"segments": ["seg-2"], "count": 2}, owner="indexer", operation_id="snapshot-main-2")
    second = registry.publish(prepared)
    assert first.generation == lease.value["snapshot_generation"] == 1
    assert second.generation == registry.current("main").generation == 2 and lease.prerequisites == (first.digest,)


def test_i09(tmp_path: Path) -> None:
    from whoosh.workflow import WorkflowError
    registry, first = published_snapshot(tmp_path, generation=1)
    lease = registry.acquire("main", owner="reader", operation_id="lease")
    raises(WorkflowError, lambda: registry.retire(first, operation_id="retire-current"))
    second = registry.publish(registry.prepare("main", {"segments": ["seg-2"], "count": 2}, owner="indexer", operation_id="snapshot-main-2"))
    raises(WorkflowError, lambda: registry.retire(first, operation_id="retire-pinned"))
    registry.release(lease, operation_id="release")
    retired = registry.retire(first, operation_id="retire-old")
    assert retired.state == "retired" and registry.current("main") == second


def test_i10(tmp_path: Path) -> None:
    from whoosh.workflow import IntegrityError
    registry, snapshot = published_snapshot(tmp_path)
    raises(IntegrityError, lambda: registry.verify(snapshot, {"segments": ["changed"], "count": 1}))
    raises(IntegrityError, lambda: registry.verify(snapshot, {"segments": ["seg-1"], "count": 1, "extra": True}))
    assert registry.current("main") == snapshot


def test_i11(tmp_path: Path) -> None:
    from whoosh.workflow import SearchSessionRegistry, StaleGenerationError
    _, snapshot = published_snapshot(tmp_path / "snap")
    sessions = SearchSessionRegistry(tmp_path / "sessions")
    first = sessions.open("one", snapshot, {"term": "a"}, [{"key": "a"}, {"key": "b"}], owner="reader", operation_id="one")
    second = sessions.open("two", snapshot, {"term": "a"}, [{"key": "c"}, {"key": "d"}], owner="reader", operation_id="two")
    _, cursor = sessions.page(first, size=1)
    raises(StaleGenerationError, lambda: sessions.page(second, cursor=cursor, size=1))


def test_i12(tmp_path: Path) -> None:
    from whoosh.workflow import SearchSessionRegistry, StaleGenerationError
    _, snapshot = published_snapshot(tmp_path / "snap")
    sessions = SearchSessionRegistry(tmp_path / "sessions")
    first = sessions.open("s", snapshot, {"term": "a"}, [{"key": "a"}, {"key": "b"}], owner="alice", operation_id="open")
    _, cursor = sessions.page(first, size=1)
    moved = sessions.handoff(first, new_owner="bob", operation_id="move")
    raises(StaleGenerationError, lambda: sessions.page(first, cursor=cursor, size=1))
    raises(StaleGenerationError, lambda: sessions.page(moved, cursor=cursor, size=1))
    assert moved.owner == "bob" and moved.generation == 2


def test_i13(tmp_path: Path) -> None:
    from whoosh.workflow import SearchSessionRegistry
    _, snapshot = published_snapshot(tmp_path / "snap")
    sessions = SearchSessionRegistry(tmp_path / "sessions")
    opened = sessions.open("s", snapshot, {"term": "a"}, [{"rank": n} for n in range(5)], owner="reader", operation_id="open")
    first, cursor = sessions.page(opened, size=2)
    reopened = SearchSessionRegistry(tmp_path / "sessions")
    second, cursor2 = reopened.page(reopened.current("s"), cursor=cursor, size=2)
    third, end = reopened.page(reopened.current("s"), cursor=cursor2, size=2)
    assert [row["rank"] for row in first + second + third] == list(range(5)) and end is None


def test_i14(tmp_path: Path) -> None:
    from whoosh.workflow import ResultExportOutbox
    outbox = ResultExportOutbox(tmp_path)
    prepared = outbox.prepare("batch", [{"rank": 1}], owner="search", operation_id="prepare")
    assert ResultExportOutbox(tmp_path).pending() == () and ResultExportOutbox(tmp_path).current("batch") is None
    pending = outbox.publish(prepared)
    assert ResultExportOutbox(tmp_path).pending() == (pending,)


def test_i15(tmp_path: Path) -> None:
    from whoosh.workflow import ResultExportOutbox
    outbox = ResultExportOutbox(tmp_path)
    pending = outbox.publish(outbox.prepare("batch", [{"rank": 1}], owner="search", operation_id="prepare"))
    claim = outbox.claim(pending, owner="delivery", operation_id="claim")
    assert claim.state == "claimed" and claim.owner == "delivery" and outbox.pending() == (claim,)
    acknowledged = outbox.acknowledge(claim, operation_id="ack")
    assert acknowledged.state == "acknowledged" and outbox.pending() == ()


def test_i16(tmp_path: Path) -> None:
    from whoosh.workflow import OwnershipError, ResultExportOutbox
    outbox = ResultExportOutbox(tmp_path)
    pending = outbox.publish(outbox.prepare("batch", [{"rank": 1}], owner="search", operation_id="prepare"))
    claim = outbox.claim(pending, owner="delivery", operation_id="claim")
    forged = type(claim)(**{**claim.__dict__, "owner": "intruder"})
    raises(OwnershipError, lambda: outbox.acknowledge(forged, operation_id="wrong-ack"))
    assert outbox.pending() == (claim,)


def test_i17(tmp_path: Path) -> None:
    coordinator, planned = planned_workflow(tmp_path)
    reopened = type(coordinator)(tmp_path)
    assert reopened.current("wf") is None and reopened.views("wf") == {}
    assert reopened.recover("plan-wf", owner="planner").state == "executed"
    assert reopened.current("wf") is None and planned.state == "planned"


def test_i18(tmp_path: Path) -> None:
    coordinator, planned = planned_workflow(tmp_path)
    executed = coordinator.recover("plan-wf", owner="planner")
    again = coordinator.execute(executed)
    assert executed == again and executed.state == "executed" and len(executed.prerequisites) == 5
    assert coordinator.current("wf") is None


def test_i19(tmp_path: Path) -> None:
    from whoosh.workflow import OwnershipError
    coordinator, planned = planned_workflow(tmp_path)
    moved = coordinator.handoff(planned, new_owner="worker", operation_id="handoff")
    raises(OwnershipError, lambda: coordinator.execute(planned))
    raises(OwnershipError, lambda: coordinator.recover("handoff", owner="planner"))
    executed = coordinator.execute(moved)
    assert executed.owner == "worker" and executed.generation == 2


def test_i20(tmp_path: Path) -> None:
    from whoosh.workflow import IncompleteWorkflowError
    coordinator, first_plan = planned_workflow(tmp_path, workflow_id="wf", operation_id="first")
    first = coordinator.publish(coordinator.execute(first_plan), owner="planner", operation_id="publish-first")
    second_plan = coordinator.plan({"version": 2}, [{"key": "x"}], {"term": "x"}, workflow_id="wf", owner="planner", operation_id="second")
    raises(IncompleteWorkflowError, lambda: coordinator.publish(second_plan, owner="planner", operation_id="publish-too-soon"))
    assert coordinator.current("wf") == first


def test_i21(tmp_path: Path) -> None:
    from whoosh import index
    from whoosh.fields import ID, TEXT, Schema
    from whoosh.query import Every
    directory = tmp_path / "ix"; directory.mkdir(); ix = index.create_in(str(directory), Schema(key=ID(stored=True), body=TEXT(stored=True)))
    with ix.writer() as writer: writer.add_document(key="a", body="amber")
    old = ix.searcher()
    with ix.writer() as writer: writer.add_document(key="b", body="blue")
    try:
        with ix.searcher() as new: assert [hit["key"] for hit in new.search(Every(), limit=None)] == ["a", "b"]
        assert [hit["key"] for hit in old.search(Every(), limit=None)] == ["a"]
    finally: old.close()


def test_i22(tmp_path: Path) -> None:
    from whoosh.fields import ID, NUMERIC, TEXT, Schema
    from whoosh.filedb.filestore import RamStorage
    from whoosh.qparser import QueryParser
    schema = Schema(key=ID(stored=True), title=TEXT(stored=True), rank=NUMERIC(stored=True))
    ix = RamStorage().create_index(schema)
    with ix.writer() as writer:
        writer.add_document(key="a", title="amber river", rank=2); writer.add_document(key="b", title="amber ridge", rank=8); writer.add_document(key="c", title="blue river", rank=5)
    with ix.searcher() as searcher:
        assert {hit["key"] for hit in searcher.search(QueryParser("title", schema).parse('"amber river"'), limit=None)} == {"a"}
        assert {hit["key"] for hit in searcher.search(QueryParser("title", schema).parse("amb*"), limit=None)} == {"a", "b"}
        assert {hit["key"] for hit in searcher.search(QueryParser("title", schema).parse("rank:[3 to 9]"), limit=None)} == {"b", "c"}


def test_i23(tmp_path: Path) -> None:
    from whoosh.fields import ID, NUMERIC, Schema
    from whoosh.filedb.filestore import RamStorage
    from whoosh.query import Every
    from whoosh.sorting import FieldFacet
    ix = RamStorage().create_index(Schema(key=ID(stored=True), group=ID(stored=True), rank=NUMERIC(stored=True)))
    with ix.writer() as writer:
        for key, group, rank in [("a", "x", 3), ("b", "y", 1), ("c", "x", 2)]: writer.add_document(key=key, group=group, rank=rank)
    with ix.searcher() as searcher:
        result = searcher.search(Every(), limit=None, sortedby="rank", groupedby=FieldFacet("group"))
        assert [hit["key"] for hit in result] == ["b", "c", "a"]
        assert {name: len(docnums) for name, docnums in result.groups().items()} == {"x": 2, "y": 1}
        page = searcher.search_page(Every(), 2, pagelen=2, sortedby="rank")
        assert [hit["key"] for hit in page] == ["a"] and page.pagecount == 2


def test_i24(tmp_path: Path) -> None:
    from whoosh.fields import ID, TEXT, Schema
    from whoosh.filedb.filestore import RamStorage
    from whoosh.query import Term
    ix = RamStorage().create_index(Schema(key=ID(stored=True), body=TEXT(stored=True, spelling=True)))
    with ix.writer() as writer: writer.add_document(key="a", body="amber river"); writer.add_document(key="b", body="blue ridge")
    with ix.searcher() as searcher:
        corrected = searcher.correct_query(Term("body", "ambr"), "ambr")
        assert corrected.query == Term("body", "amber") and corrected.tokens[0].original == "ambr" and corrected.tokens[0].text == "amber"
        hit = searcher.search(Term("body", "amber"))[0]
        assert "<b class=\"match term0\">amber</b>" in hit.highlights("body")
