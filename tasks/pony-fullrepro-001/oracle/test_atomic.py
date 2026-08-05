import pytest

from conftest import make_library, seed_library
from pony.orm import (
    CacheIndexError,
    DatabaseSessionIsOver,
    avg,
    count,
    db_session,
    desc,
    flush,
    max,
    min,
    select,
    sum,
)


def test_database_mapping_creates_declared_entities():
    lib = make_library()
    with db_session:
        author = lib.Author(id=1, name="Alice")
        lib.Book(id=10, code="B10", title="Alpha", pages=100, author=author)
        assert count(book for book in lib.Book) == 1


def test_required_optional_and_default_values_round_trip():
    lib = make_library()
    with db_session:
        author = lib.Author(id=1, name="Alice")
        book = lib.Book(
            id=10,
            code="B10",
            title="Alpha",
            pages=100,
            author=author,
            price=None,
            metadata={},
        )
        assert author.active is True
        assert book.price is None
        assert book.editor is None
        assert book.metadata == {}


def test_primary_key_lookup_and_identity():
    lib = make_library()
    with db_session:
        seed_library(lib)
        first = lib.Book[10]
        second = lib.Book.get(id=10)
        assert first is second
        assert first.code == "B10"


def test_auto_primary_key_assigns_value():
    lib = make_library()
    with db_session:
        record = lib.AutoRecord(label="fresh")
        flush()
        assert isinstance(record.id, int)
        assert record.id > 0
        assert lib.AutoRecord[record.id].label == "fresh"


def test_entity_get_and_exists_report_rows():
    lib = make_library()
    with db_session:
        seed_library(lib)
        assert lib.Book.exists(id=10)
        assert not lib.Book.exists(id=999)
        assert lib.Book.get(code="B11").id == 11


def test_select_returns_entities_in_requested_order():
    lib = make_library()
    with db_session:
        seed_library(lib)
        rows = select(book for book in lib.Book).order_by(lib.Book.pages)[:]
        assert [book.id for book in rows] == [12, 10, 11, 13]


def test_select_scalar_projection_returns_values():
    lib = make_library()
    with db_session:
        seed_library(lib)
        titles = select(book.title for book in lib.Book if book.pages >= 200).order_by(1)[:]
        assert titles == ["Beta", "Delta"]


def test_filter_lambda_restricts_query():
    lib = make_library()
    with db_session:
        seed_library(lib)
        rows = lib.Book.select().filter(lambda book: book.pages >= 200).order_by(
            lib.Book.id
        )[:]
        assert [book.title for book in rows] == ["Beta", "Delta"]


def test_filter_kwargs_restricts_query():
    lib = make_library()
    with db_session:
        seed_library(lib)
        rows = lib.Book.select().filter(
            published=True, author=lib.Author[1]
        ).order_by(lib.Book.id)[:]
        assert [book.title for book in rows] == ["Alpha", "Beta"]


def test_order_by_ascending_and_descending():
    lib = make_library()
    with db_session:
        seed_library(lib)
        ascending = [
            book.title for book in select(book for book in lib.Book).order_by(lib.Book.pages)[:]
        ]
        descending = [
            book.title
            for book in select(book for book in lib.Book).order_by(desc(lib.Book.pages))[:]
        ]
        assert ascending == ["Gamma", "Alpha", "Beta", "Delta"]
        assert descending == ["Delta", "Beta", "Alpha", "Gamma"]


def test_query_slice_and_first_return_positioned_rows():
    lib = make_library()
    with db_session:
        seed_library(lib)
        query = select(book for book in lib.Book).order_by(lib.Book.pages)
        assert query.first().title == "Gamma"
        assert [book.title for book in query[1:3]] == ["Alpha", "Beta"]


def test_count_aggregate_counts_entities():
    lib = make_library()
    with db_session:
        seed_library(lib)
        assert count(book for book in lib.Book) == 4
        assert count(book for book in lib.Book if book.published) == 3


def test_sum_and_avg_aggregates():
    lib = make_library()
    with db_session:
        seed_library(lib)
        assert sum(book.pages for book in lib.Book) == 740
        assert avg(book.pages for book in lib.Book) == 185.0


def test_min_max_and_empty_aggregates():
    lib = make_library()
    with db_session:
        seed_library(lib)
        assert min(book.pages for book in lib.Book) == 80
        assert max(book.pages for book in lib.Book) == 320
        assert avg(book.pages for book in lib.Book if book.pages > 1000) is None
        assert sum(book.pages for book in lib.Book if book.pages > 1000) == 0


def test_related_filter_joins_forward_relationship():
    lib = make_library()
    with db_session:
        seed_library(lib)
        titles = select(
            book.title for book in lib.Book if book.author.name == "Alice"
        ).order_by(1)[:]
        assert titles == ["Alpha", "Beta"]


def test_reverse_set_iteration_and_count():
    lib = make_library()
    with db_session:
        seed_library(lib)
        author = lib.Author[1]
        assert author.books.count() == 2
        assert sorted(book.title for book in author.books) == ["Alpha", "Beta"]


def test_many_to_many_add_is_idempotent():
    lib = make_library()
    with db_session:
        seed_library(lib)
        book = lib.Book[10]
        book.tags.add(lib.Tag[101])
        book.tags.add(lib.Tag[101])
        assert book.tags.count() == 2
        assert sorted(tag.label for tag in book.tags) == ["fiction", "science"]


def test_many_to_many_remove_and_clear():
    lib = make_library()
    with db_session:
        seed_library(lib)
        book = lib.Book[11]
        book.tags.remove(lib.Tag[101])
        assert [tag.label for tag in book.tags] == ["fiction"]
        book.tags.clear()
        assert book.tags.count() == 0


def test_optional_relationship_can_be_null():
    lib = make_library()
    with db_session:
        seed_library(lib)
        assert lib.Book[12].editor is None
        lib.Book[12].set(editor=lib.Author[1])
        assert lib.Book[12].editor is lib.Author[1]


def test_to_dict_contains_scalar_and_foreign_key_values():
    lib = make_library()
    with db_session:
        seed_library(lib)
        payload = lib.Book[10].to_dict()
        assert payload["id"] == 10
        assert payload["title"] == "Alpha"
        assert payload["author"] == 1
        assert payload["metadata"] == {"genre": "fiction", "rank": 1}
        assert "tags" not in payload


def test_to_dict_includes_collections_when_requested():
    lib = make_library()
    with db_session:
        seed_library(lib)
        payload = lib.Book[11].to_dict(with_collections=True)
        assert payload["tags"] == [100, 101]


def test_to_dict_can_emit_related_objects():
    lib = make_library()
    with db_session:
        seed_library(lib)
        payload = lib.Book[10].to_dict(related_objects=True)
        assert payload["author"] is lib.Author[1]
        assert payload["editor"] is lib.Author[3]


def test_to_dict_only_and_exclude_are_respected():
    lib = make_library()
    with db_session:
        seed_library(lib)
        selected = lib.Book[10].to_dict(only=["id", "title", "author"])
        excluded = lib.Book[10].to_dict(exclude=["pages", "price"])
        assert set(selected) == {"id", "title", "author"}
        assert "pages" not in excluded
        assert "price" not in excluded
        assert excluded["title"] == "Alpha"


def test_json_field_round_trips_and_tracks_mutation():
    lib = make_library()
    with db_session:
        seed_library(lib)
        lib.Book[10].metadata["rank"] = 9
    with db_session:
        assert lib.Book[10].metadata["rank"] == 9


def test_entity_set_updates_persisted_fields():
    lib = make_library()
    with db_session:
        seed_library(lib)
        book = lib.Book[10]
        book.set(title="Alpha Revised", pages=101)
        assert (book.title, book.pages) == ("Alpha Revised", 101)
    with db_session:
        assert lib.Book[10].title == "Alpha Revised"


def test_entity_delete_removes_row():
    lib = make_library()
    with db_session:
        seed_library(lib)
        lib.Book[12].delete()
        assert not lib.Book.exists(id=12)


def test_query_delete_removes_matching_rows():
    lib = make_library()
    with db_session:
        seed_library(lib)
        deleted = lib.Book.select(lambda book: not book.published).delete(bulk=True)
        assert deleted == 1
        assert count(book for book in lib.Book) == 3


def test_set_collection_create_links_child():
    lib = make_library()
    with db_session:
        seed_library(lib)
        book = lib.Author[1].books.create(
            id=14,
            code="B14",
            title="Epsilon",
            pages=55,
            price=None,
            published=True,
            metadata={},
        )
        flush()
        assert book.author is lib.Author[1]
        assert lib.Book[14].title == "Epsilon"


def test_required_validation_raises_value_error():
    lib = make_library()
    with db_session:
        with pytest.raises(ValueError):
            lib.Author(id=99)


def test_invalid_value_and_unknown_attribute_raise_public_errors():
    lib = make_library()
    with db_session:
        with pytest.raises(ValueError):
            lib.Author(id="bad", name="Bad")
        with pytest.raises(TypeError):
            lib.Author(id=99, name="Bad", mystery=1)


def test_duplicate_primary_key_raises_public_error():
    lib = make_library()
    with db_session:
        seed_library(lib)
        with pytest.raises(CacheIndexError):
            lib.Author(id=1, name="Another")


def test_db_session_success_commits():
    lib = make_library()
    with db_session:
        lib.Author(id=1, name="Committed")
    with db_session:
        assert lib.Author.exists(id=1)
        assert lib.Author[1].name == "Committed"


def test_db_session_exception_rolls_back():
    lib = make_library()
    with db_session:
        lib.Author(id=1, name="Base")
    with pytest.raises(ValueError):
        with db_session:
            lib.Author(id=2, name="Rolled Back")
            raise ValueError("abort")
    with db_session:
        assert lib.Author.exists(id=1)
        assert not lib.Author.exists(id=2)


def test_allowed_exception_commits():
    lib = make_library()
    with pytest.raises(ValueError):
        with db_session(allowed_exceptions=[ValueError]):
            lib.Author(id=1, name="Allowed")
            raise ValueError("allowed")
    with db_session:
        assert lib.Author.exists(id=1)


def test_strict_session_expires_objects():
    lib = make_library()
    with db_session:
        seed_library(lib)
    with db_session(strict=True):
        book = lib.Book[10]
    with pytest.raises(DatabaseSessionIsOver):
        book.title
