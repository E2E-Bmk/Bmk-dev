import pytest

from conftest import make_library, seed_library
from pony.orm import (
    CacheIndexError,
    DatabaseSessionIsOver,
    avg,
    commit,
    count,
    db_session,
    desc,
    flush,
    select,
    sum,
)


@pytest.mark.depends_on(
    "test_database_mapping_creates_declared_entities",
    "test_select_scalar_projection_returns_values",
)
def test_seed_projection_agrees_across_entity_and_scalar_queries():
    lib = make_library()
    with db_session:
        seed_library(lib)
        entity_titles = [
            book.title
            for book in select(book for book in lib.Book).order_by(lib.Book.id)[:]
        ]
        scalar_titles = [
            row[1]
            for row in select((book.id, book.title) for book in lib.Book).order_by(1)[:]
        ]
        assert entity_titles == scalar_titles == ["Alpha", "Beta", "Gamma", "Delta"]


@pytest.mark.depends_on(
    "test_order_by_ascending_and_descending",
    "test_sum_and_avg_aggregates",
)
def test_ordering_projection_and_aggregate_share_the_same_rows():
    lib = make_library()
    with db_session:
        seed_library(lib)
        rows = select((book.title, book.pages) for book in lib.Book).order_by(2)[:]
        ordered = [book.title for book in select(book for book in lib.Book).order_by(lib.Book.pages)[:]]
        assert rows == [
            ("Gamma", 80),
            ("Alpha", 100),
            ("Beta", 240),
            ("Delta", 320),
        ]
        assert ordered == [row[0] for row in rows]
        assert sum(book.pages for book in lib.Book) == 740


@pytest.mark.depends_on(
    "test_entity_set_updates_persisted_fields",
    "test_entity_delete_removes_row",
)
def test_create_update_delete_sequence_updates_counts_and_lookup():
    lib = make_library()
    with db_session:
        seed_library(lib)
        lib.Book(
            id=14,
            code="B14",
            title="Epsilon",
            pages=55,
            price=None,
            published=True,
            metadata={},
            author=lib.Author[3],
        )
        lib.Book[10].set(title="Alpha Revised")
        lib.Book[12].delete()
        assert count(book for book in lib.Book) == 4
        assert lib.Book[10].title == "Alpha Revised"
        assert not lib.Book.exists(id=12)
        assert lib.Book.exists(id=14)


@pytest.mark.depends_on(
    "test_filter_lambda_restricts_query",
    "test_query_slice_and_first_return_positioned_rows",
)
def test_filter_order_and_slice_preserve_the_same_projection():
    lib = make_library()
    with db_session:
        seed_library(lib)
        query = (
            lib.Book.select()
            .filter(lambda book: book.published)
            .order_by(desc(lib.Book.pages))
        )
        entity_slice = [book.title for book in query[1:3]]
        scalar_slice = select(
            (book.title, book.pages) for book in lib.Book if book.published
        ).order_by(-2)[1:3]
        assert entity_slice == [row[0] for row in scalar_slice] == ["Beta", "Alpha"]


@pytest.mark.depends_on(
    "test_db_session_success_commits",
    "test_db_session_exception_rolls_back",
)
def test_failed_transaction_preserves_the_committed_projection():
    lib = make_library()
    with db_session:
        lib.Author(id=1, name="Base")
    with pytest.raises(RuntimeError):
        with db_session:
            lib.Author[1].set(name="Temporary")
            lib.Author(id=2, name="Transient")
            raise RuntimeError("rollback")
    with db_session:
        assert lib.Author[1].name == "Base"
        assert not lib.Author.exists(id=2)


@pytest.mark.depends_on(
    "test_allowed_exception_commits",
    "test_db_session_success_commits",
)
def test_allowed_transaction_exception_keeps_public_state():
    lib = make_library()
    with pytest.raises(ValueError):
        with db_session(allowed_exceptions=[ValueError]):
            lib.Author(id=1, name="Allowed")
            raise ValueError("commit")
    with db_session:
        assert lib.Author.get(id=1).name == "Allowed"
        assert count(author for author in lib.Author) == 1


@pytest.mark.depends_on(
    "test_primary_key_lookup_and_identity",
    "test_entity_set_updates_persisted_fields",
)
def test_session_identity_cache_tracks_entity_mutations():
    lib = make_library()
    with db_session:
        seed_library(lib)
        first = lib.Book[10]
        second = lib.Book.get(id=10)
        first.set(title="Cached Update")
        assert first is second
        assert second.title == "Cached Update"
    with db_session:
        assert lib.Book[10].title == "Cached Update"


@pytest.mark.depends_on(
    "test_related_filter_joins_forward_relationship",
    "test_to_dict_can_emit_related_objects",
)
def test_forward_relation_and_serialization_agree():
    lib = make_library()
    with db_session:
        seed_library(lib)
        book = select(book for book in lib.Book if book.author.name == "Alice").order_by(
            lib.Book.id
        ).first()
        payload = book.to_dict(related_objects=True)
        assert book.author.name == "Alice"
        assert payload["author"] is book.author
        assert payload["title"] == "Alpha"


@pytest.mark.depends_on(
    "test_reverse_set_iteration_and_count",
    "test_related_filter_joins_forward_relationship",
)
def test_reverse_relation_and_forward_filter_agree():
    lib = make_library()
    with db_session:
        seed_library(lib)
        author_titles = sorted(book.title for book in lib.Author[1].books)
        filtered_titles = select(
            book.title for book in lib.Book if book.author.id == 1
        ).order_by(1)[:]
        assert author_titles == filtered_titles == ["Alpha", "Beta"]


@pytest.mark.depends_on(
    "test_many_to_many_add_is_idempotent",
    "test_to_dict_includes_collections_when_requested",
)
def test_many_to_many_relation_and_collection_serialization_agree():
    lib = make_library()
    with db_session:
        seed_library(lib)
        book = lib.Book[11]
        labels = sorted(tag.label for tag in book.tags)
        payload = book.to_dict(with_collections=True)
        tag_ids = sorted(tag.id for tag in book.tags)
        assert labels == ["fiction", "science"]
        assert payload["tags"] == tag_ids == [100, 101]


@pytest.mark.depends_on(
    "test_many_to_many_remove_and_clear",
    "test_count_aggregate_counts_entities",
)
def test_many_to_many_mutations_change_both_relation_views():
    lib = make_library()
    with db_session:
        seed_library(lib)
        book = lib.Book[11]
        book.tags.remove(lib.Tag[100])
        assert sorted(tag.id for tag in book.tags) == [101]
        assert lib.Tag[100].books.count() == 1
        book.tags.clear()
        assert book.tags.count() == 0
        assert not lib.Tag[100].books.select(id=11).exists()


@pytest.mark.depends_on(
    "test_optional_relationship_can_be_null",
    "test_reverse_set_iteration_and_count",
)
def test_optional_editor_relation_updates_reverse_collection():
    lib = make_library()
    with db_session:
        seed_library(lib)
        gamma = lib.Book[12]
        assert gamma.editor is None
        gamma.set(editor=lib.Author[1])
        assert gamma in list(lib.Author[1].edited_books)
        assert sorted(book.title for book in lib.Author[1].edited_books) == [
            "Delta",
            "Gamma",
        ]


@pytest.mark.depends_on(
    "test_count_aggregate_counts_entities",
    "test_select_returns_entities_in_requested_order",
)
def test_grouped_count_aggregate_matches_author_collections():
    lib = make_library()
    with db_session:
        seed_library(lib)
        rows = select(
            (book.author.name, count(book)) for book in lib.Book
        ).order_by(1)[:]
        collection_counts = [
            (author.name, author.books.count())
            for author in select(author for author in lib.Author).order_by(lib.Author.name)[:]
        ]
        assert rows == collection_counts == [("Alice", 2), ("Bob", 1), ("Carol", 1)]


@pytest.mark.depends_on(
    "test_sum_and_avg_aggregates",
    "test_related_filter_joins_forward_relationship",
)
def test_grouped_sum_aggregate_matches_filtered_pages():
    lib = make_library()
    with db_session:
        seed_library(lib)
        rows = select(
            (book.author.name, sum(book.pages)) for book in lib.Book
        ).order_by(1)[:]
        filtered = [
            (name, sum(book.pages for book in lib.Book if book.author.name == name))
            for name in ["Alice", "Bob", "Carol"]
        ]
        assert rows == filtered == [("Alice", 340), ("Bob", 80), ("Carol", 320)]


@pytest.mark.depends_on(
    "test_entity_get_and_exists_report_rows",
    "test_primary_key_lookup_and_identity",
)
def test_get_exists_and_identity_form_one_lookup_contract():
    lib = make_library()
    with db_session:
        seed_library(lib)
        by_id = lib.Book[11]
        by_get = lib.Book.get(code="B11")
        assert lib.Book.exists(code="B11")
        assert by_id is by_get
        assert not lib.Book.exists(code="missing")


@pytest.mark.depends_on(
    "test_select_returns_entities_in_requested_order",
    "test_database_mapping_creates_declared_entities",
)
def test_query_built_before_insert_evaluates_current_database_state():
    lib = make_library()
    with db_session:
        seed_library(lib)
        query = select(book for book in lib.Book if book.pages > 0)
        lib.Book(
            id=14,
            code="B14",
            title="Epsilon",
            pages=55,
            price=None,
            published=True,
            metadata={},
            author=lib.Author[1],
        )
        titles = [book.title for book in query.order_by(lib.Book.id)[:]]
        assert titles == ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]


@pytest.mark.depends_on(
    "test_filter_lambda_restricts_query",
    "test_order_by_ascending_and_descending",
)
def test_chained_filters_and_descending_order_compose():
    lib = make_library()
    with db_session:
        seed_library(lib)
        rows = (
            lib.Book.select()
            .filter(lambda book: book.pages >= 80)
            .filter(lambda book: book.published)
            .order_by(desc(lib.Book.pages))[:]
        )
        assert [book.title for book in rows] == ["Delta", "Beta", "Alpha"]


@pytest.mark.depends_on(
    "test_filter_kwargs_restricts_query",
    "test_select_scalar_projection_returns_values",
)
def test_select_kwargs_and_scalar_projection_agree():
    lib = make_library()
    with db_session:
        seed_library(lib)
        entity_titles = [book.title for book in lib.Book.select(title="Beta")]
        scalar_titles = select(book.title for book in lib.Book if book.title == "Beta")[:]
        assert entity_titles == scalar_titles == ["Beta"]


@pytest.mark.depends_on(
    "test_set_collection_create_links_child",
    "test_reverse_set_iteration_and_count",
)
def test_collection_create_is_visible_from_entity_and_reverse_queries():
    lib = make_library()
    with db_session:
        seed_library(lib)
        book = lib.Author[2].books.create(
            id=14,
            code="B14",
            title="Epsilon",
            pages=55,
            price=None,
            published=True,
            metadata={},
        )
        flush()
        reverse_titles = sorted(item.title for item in lib.Author[2].books)
        filtered_titles = select(
            item.title for item in lib.Book if item.author.id == 2
        )[:]
        assert book.author is lib.Author[2]
        assert reverse_titles == sorted(filtered_titles) == ["Epsilon", "Gamma"]


@pytest.mark.depends_on(
    "test_to_dict_contains_scalar_and_foreign_key_values",
    "test_to_dict_can_emit_related_objects",
)
def test_to_dict_scalar_and_related_modes_preserve_row_identity():
    lib = make_library()
    with db_session:
        seed_library(lib)
        plain = lib.Book[10].to_dict()
        related = lib.Book[10].to_dict(related_objects=True)
        assert plain["id"] == related["id"] == 10
        assert plain["title"] == related["title"] == "Alpha"
        assert plain["author"] == related["author"].id == 1


@pytest.mark.depends_on(
    "test_json_field_round_trips_and_tracks_mutation",
    "test_required_optional_and_default_values_round_trip",
)
def test_json_and_optional_values_survive_a_new_session():
    lib = make_library()
    with db_session:
        seed_library(lib)
        lib.Book[10].metadata["genre"] = "revised"
        lib.Book[12].set(price=None, metadata={})
    with db_session:
        assert lib.Book[10].metadata["genre"] == "revised"
        assert lib.Book[12].price is None
        assert lib.Book[12].metadata == {}


@pytest.mark.depends_on(
    "test_required_validation_raises_value_error",
    "test_entity_get_and_exists_report_rows",
)
def test_validation_failure_does_not_create_a_partial_entity():
    lib = make_library()
    with db_session:
        seed_library(lib)
        before = count(author for author in lib.Author)
        with pytest.raises(ValueError):
            lib.Author(id=99)
        assert count(author for author in lib.Author) == before
        assert not lib.Author.exists(id=99)


@pytest.mark.depends_on(
    "test_duplicate_primary_key_raises_public_error",
    "test_entity_get_and_exists_report_rows",
)
def test_duplicate_primary_key_failure_preserves_original_row():
    lib = make_library()
    with db_session:
        seed_library(lib)
        with pytest.raises(CacheIndexError):
            lib.Author(id=1, name="Replacement")
        assert lib.Author[1].name == "Alice"
        assert count(author for author in lib.Author) == 3


@pytest.mark.depends_on(
    "test_auto_primary_key_assigns_value",
    "test_to_dict_contains_scalar_and_foreign_key_values",
)
def test_auto_primary_key_and_to_dict_share_the_inserted_identity():
    lib = make_library()
    with db_session:
        record = lib.AutoRecord(label="Serialized")
        payload = record.to_dict()
        assert payload["id"] == record.id
        assert payload["label"] == "Serialized"
        assert lib.AutoRecord[record.id] is record


@pytest.mark.depends_on(
    "test_db_session_success_commits",
    "test_entity_set_updates_persisted_fields",
)
def test_explicit_commit_preserves_later_entity_updates():
    lib = make_library()
    with db_session:
        author = lib.Author(id=1, name="Before")
        commit()
        author.set(name="After")
    with db_session:
        assert lib.Author[1].name == "After"


@pytest.mark.depends_on(
    "test_db_session_exception_rolls_back",
    "test_json_field_round_trips_and_tracks_mutation",
)
def test_rollback_on_exception_restores_json_and_scalar_values():
    lib = make_library()
    with db_session:
        seed_library(lib)
    with pytest.raises(RuntimeError):
        with db_session:
            lib.Book[10].metadata["rank"] = 99
            lib.Book[10].set(title="Temporary")
            raise RuntimeError("abort")
    with db_session:
        assert lib.Book[10].title == "Alpha"
        assert lib.Book[10].metadata["rank"] == 1


@pytest.mark.depends_on(
    "test_primary_key_lookup_and_identity",
    "test_db_session_success_commits",
)
def test_nested_db_sessions_share_the_outer_cache():
    lib = make_library()
    with db_session:
        author = lib.Author(id=1, name="Outer")
        with db_session:
            same = lib.Author[1]
            same.set(name="Inner")
        assert same is author
        assert author.name == "Inner"
    with db_session:
        assert lib.Author[1].name == "Inner"


@pytest.mark.depends_on(
    "test_reverse_set_iteration_and_count",
    "test_select_returns_entities_in_requested_order",
)
def test_collection_query_and_global_query_return_the_same_children():
    lib = make_library()
    with db_session:
        seed_library(lib)
        author = lib.Author[1]
        from_collection = [
            book.title for book in author.books.select().order_by(lib.Book.id)[:]
        ]
        global_query = select(
            book.title for book in lib.Book if book.author == author
        ).order_by(1)[:]
        assert from_collection == global_query == ["Alpha", "Beta"]


@pytest.mark.depends_on(
    "test_optional_relationship_can_be_null",
    "test_related_filter_joins_forward_relationship",
)
def test_optional_relation_query_matches_reverse_editor_collection():
    lib = make_library()
    with db_session:
        seed_library(lib)
        query_titles = select(
            book.title for book in lib.Book if book.editor.name == "Bob"
        ).order_by(1)[:]
        reverse_titles = [
            book.title for book in lib.Author[2].edited_books
        ]
        assert query_titles == reverse_titles == ["Beta"]


@pytest.mark.depends_on(
    "test_many_to_many_remove_and_clear",
    "test_to_dict_includes_collections_when_requested",
)
def test_end_to_end_library_projection_remains_consistent_after_mutations():
    lib = make_library()
    with db_session:
        seed_library(lib)
        lib.Book[10].tags.add(lib.Tag[102])
        lib.Book[10].set(pages=150, title="Alpha Revised")
        payload = lib.Book[10].to_dict(with_collections=True)
        selected = select(
            (book.title, book.pages, count(book.tags)) for book in lib.Book
            if book.id == 10
        )[:]
        assert payload["title"] == "Alpha Revised"
        assert payload["tags"] == [100, 102]
        assert selected == [("Alpha Revised", 150, 2)]
        lib.Book[12].delete()
        assert count(book for book in lib.Book) == 3


@pytest.mark.depends_on(
    "test_strict_session_expires_objects",
    "test_to_dict_can_emit_related_objects",
)
def test_prefetched_relation_is_readable_inside_strict_session_only():
    lib = make_library()
    with db_session:
        seed_library(lib)
    with db_session(strict=True):
        book = select(book for book in lib.Book if book.id == 10).first()
        author = book.author
        assert author.name == "Alice"
    with pytest.raises(DatabaseSessionIsOver):
        author.name
