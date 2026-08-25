from __future__ import annotations

from pathlib import Path

from tests.helpers import planned_workflow, published_snapshot, raises


def test_a01(tmp_path: Path) -> None:
    from whoosh.fields import ID, KEYWORD, STORED, TEXT, Schema
    schema = Schema(path=ID(stored=True, unique=True), body=TEXT(stored=True), tags=KEYWORD(commas=True, lowercase=True), payload=STORED)
    assert schema.names() == ["body", "path", "payload", "tags"]
    assert schema["path"].stored and schema["path"].unique
    assert schema["payload"].stored and not schema["payload"].indexed


def test_a02(tmp_path: Path) -> None:
    from whoosh.analysis import LowercaseFilter, RegexTokenizer, StopFilter
    analyzer = RegexTokenizer() | LowercaseFilter() | StopFilter(stoplist={"and"})
    tokens = [(token.text, token.pos) for token in analyzer("Amber AND Blue", positions=True)]
    assert tokens == [("amber", 0), ("blue", 1)]


def test_a03(tmp_path: Path) -> None:
    from whoosh.query import And, NullQuery, Or, Term
    left = Term("body", "amber")
    assert And([left, NullQuery]).normalize() == left
    assert Or([left, NullQuery]).normalize() == left
    assert And([left, left]).normalize() == left


def test_a04(tmp_path: Path) -> None:
    from whoosh.fields import ID, TEXT, Schema
    from whoosh.qparser import MultifieldParser, QueryParser
    from whoosh.query import And, Or, Term
    schema = Schema(title=TEXT(), body=TEXT(), tag=ID())
    assert QueryParser("body", schema).parse("amber blue") == And([Term("body", "amber"), Term("body", "blue")])
    value = MultifieldParser(["title", "body"], schema).parse("amber")
    assert value == Or([Term("title", "amber"), Term("body", "amber")])


def test_a05(tmp_path: Path) -> None:
    from datetime import datetime
    from whoosh.fields import BOOLEAN, DATETIME, NUMERIC
    number = NUMERIC(stored=True, signed=True)
    assert number.from_column_value(number.to_column_value(-7)) == -7
    moment = datetime(2024, 2, 3, 4, 5, 6)
    assert DATETIME(stored=True).from_column_value(DATETIME(stored=True).to_column_value(moment)) == moment
    boolean = BOOLEAN(stored=True)
    assert boolean.to_column_value(False) == b"f" and boolean.from_column_value(b"f") == "f"


def test_a06(tmp_path: Path) -> None:
    from whoosh.sorting import FieldFacet, MultiFacet, QueryFacet
    from whoosh.query import Term
    field = FieldFacet("category", reverse=True, allow_overlap=True)
    query = QueryFacet({"amber": Term("body", "amber")}, other="other")
    facets = MultiFacet([field, query])
    assert facets.facets == [field, query]
    assert field.reverse and field.allow_overlap and query.other == "other"


def test_a07(tmp_path: Path) -> None:
    from whoosh import index
    from whoosh.fields import ID, TEXT, Schema
    directory = tmp_path / "named"; directory.mkdir()
    schema = Schema(key=ID(stored=True, unique=True), body=TEXT(stored=True))
    assert not index.exists_in(str(directory), indexname="blue")
    created = index.create_in(str(directory), schema, indexname="blue")
    assert created.schema.names() == ["body", "key"] and index.exists_in(str(directory), indexname="blue")


def test_a08(tmp_path: Path) -> None:
    from whoosh.fields import ID, TEXT, Schema
    from whoosh.filedb.filestore import RamStorage
    from whoosh.query import Term
    ix = RamStorage().create_index(Schema(key=ID(stored=True), body=TEXT(stored=True)))
    writer = ix.writer(); writer.add_document(key="a", body="amber river"); writer.commit()
    with ix.searcher() as searcher:
        hit = searcher.search(Term("body", "amber"), limit=None)[0]
        assert hit.fields() == {"body": "amber river", "key": "a"}


def test_a09(tmp_path: Path) -> None:
    from dataclasses import FrozenInstanceError
    from whoosh.workflow import AnalysisRecipeCatalog
    catalog = AnalysisRecipeCatalog(tmp_path)
    first = catalog.prepare("body", {"filters": {"stop": True, "lower": True}}, owner="alice", operation_id="r1")
    again = catalog.prepare("body", {"filters": {"lower": True, "stop": True}}, owner="alice", operation_id="r1")
    assert first == again and len(first.digest) == 64 and first.state == "prepared"
    raises(FrozenInstanceError, lambda: setattr(first, "owner", "bob"))


def test_a10(tmp_path: Path) -> None:
    from whoosh.workflow import AnalysisRecipeCatalog
    catalog = AnalysisRecipeCatalog(tmp_path)
    prepared = catalog.prepare("body", {"tokenizer": "regex"}, owner="alice", operation_id="r1")
    assert catalog.get("body") is None
    committed = catalog.commit(prepared)
    assert committed.state == "committed" and catalog.get("body") == committed


def test_a11(tmp_path: Path) -> None:
    from whoosh.workflow import DocumentIngestJournal
    journal = DocumentIngestJournal(tmp_path)
    batch = journal.begin("b1", [{"key": "a"}, {"key": "b"}], owner="alice", operation_id="i1")
    checked = journal.checkpoint(batch, accepted=["b", "a"], rejected={}, operation_id="i2")
    committed = journal.commit(checked)
    assert committed.value["accepted"] == ["a", "b"] and journal.current("b1") == committed


def test_a12(tmp_path: Path) -> None:
    registry, snapshot = published_snapshot(tmp_path)
    assert snapshot.state == "published" and snapshot.generation == 1
    assert registry.current("main") == snapshot
    assert registry.verify(snapshot, {"count": 1, "segments": ["seg-1"]})


def test_a13(tmp_path: Path) -> None:
    registry, snapshot = published_snapshot(tmp_path)
    lease = registry.acquire("main", owner="reader", operation_id="lease-1")
    assert lease.state == "active" and lease.prerequisites == (snapshot.digest,)
    assert registry.release(lease, operation_id="release-1").state == "released"


def test_a14(tmp_path: Path) -> None:
    from whoosh.workflow import SearchSessionRegistry
    _, snapshot = published_snapshot(tmp_path / "snap")
    sessions = SearchSessionRegistry(tmp_path / "sessions")
    session = sessions.open("s", snapshot, {"term": "a"}, [{"key": "a"}, {"key": "b"}, {"key": "c"}], owner="reader", operation_id="open")
    first, cursor = sessions.page(session, size=2)
    second, end = sessions.page(session, cursor=cursor, size=2)
    assert [row["key"] for row in first + second] == ["a", "b", "c"] and end is None


def test_a15(tmp_path: Path) -> None:
    from whoosh.workflow import ResultExportOutbox
    outbox = ResultExportOutbox(tmp_path)
    prepared = outbox.prepare("e", [{"rank": 1}, {"rank": 2}], owner="search", operation_id="prepare")
    assert outbox.pending() == ()
    pending = outbox.publish(prepared)
    assert outbox.pending() == (pending,) and outbox.rows(pending) == ({"rank": 1}, {"rank": 2})


def test_a16(tmp_path: Path) -> None:
    coordinator, planned = planned_workflow(tmp_path)
    assert coordinator.current("wf") is None
    executed = coordinator.execute(planned)
    published = coordinator.publish(executed, owner="planner", operation_id="publish")
    assert published.state == "published" and coordinator.current("wf") == published and coordinator.verify(published)
