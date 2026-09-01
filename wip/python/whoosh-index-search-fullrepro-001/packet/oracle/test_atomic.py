"""Atomic tests for whoosh-index-search-fullrepro-001."""

from __future__ import annotations

from datetime import datetime

import pytest

from whoosh import index
from whoosh.fields import (
    BOOLEAN,
    DATETIME,
    ID,
    KEYWORD,
    NUMERIC,
    STORED,
    TEXT,
    FieldConfigurationError,
    Schema,
    UnknownFieldError,
)
from whoosh.qparser import MultifieldParser, QueryParser, SimpleParser
from whoosh.query import And, Or, Term
from whoosh.searching import NoTermsException

from conftest import add_two, make_index, paths


def test_installable_fields_surface_constructs_a_schema():
    schema = Schema(path=ID(stored=True), body=TEXT(stored=True))
    assert set(schema.names()) == {"path", "body"}


def test_text_field_is_searchable_and_returns_stored_value(tmp_path):
    _, ix = make_index(tmp_path)
    add_two(ix)
    with ix.searcher() as searcher:
        result = searcher.search(Term("body", "alpha"), limit=None)
        assert result[0]["body"] == "alpha beta"


def test_id_field_matches_a_complete_term_only(tmp_path):
    _, ix = make_index(tmp_path)
    add_two(ix)
    assert paths(ix, Term("path", "a")) == {"a"}
    assert paths(ix, Term("path", "al")) == set()


def test_keyword_field_applies_comma_split_and_lowercase(tmp_path):
    _, ix = make_index(tmp_path)
    add_two(ix)
    assert paths(ix, Term("tags", "red")) == {"a"}
    assert paths(ix, Term("tags", "blue")) == {"a", "b"}


def test_stored_field_is_not_searchable_but_is_returned(tmp_path):
    _, ix = make_index(tmp_path)
    add_two(ix)
    assert paths(ix, Term("note", "first")) == set()
    with ix.searcher() as searcher:
        assert searcher.search(Term("body", "alpha"), limit=None)[0]["note"] == "first"


def test_numeric_and_boolean_fields_preserve_stored_values(tmp_path):
    _, ix = make_index(tmp_path)
    add_two(ix)
    with ix.searcher() as searcher:
        hit = searcher.search(Term("path", "a"), limit=None)[0]
        assert (hit["number"], hit["flag"]) == (1, True)


def test_schema_accepts_bare_builtin_field_classes():
    schema = Schema(path=ID, body=TEXT)
    assert set(schema.names()) == {"path", "body"}


@pytest.mark.parametrize("name", ["_hidden", "has space"])
def test_schema_rejects_invalid_field_names(name):
    with pytest.raises(FieldConfigurationError):
        Schema(**{name: ID})


def test_schema_rejects_unsupported_field_definition():
    with pytest.raises(FieldConfigurationError):
        Schema(path=object())


def test_error_lock_error_is_observable(tmp_path):
    _, ix = make_index(tmp_path)
    writer = ix.writer()
    with pytest.raises(index.LockError):
        ix.writer()
    writer.cancel()


def test_error_unknown_field_error_is_observable(tmp_path):
    _, ix = make_index(tmp_path)
    writer = ix.writer()
    with pytest.raises(UnknownFieldError):
        writer.add_document(path="a", body="alpha", absent="x")
    writer.cancel()


def test_error_field_configuration_error_is_observable():
    with pytest.raises(FieldConfigurationError):
        Schema(**{"bad name": ID})


def test_error_no_terms_exception_is_observable(tmp_path):
    _, ix = make_index(tmp_path)
    add_two(ix)
    with ix.searcher() as searcher:
        with pytest.raises(NoTermsException):
            searcher.search(Term("body", "alpha"), limit=None).matched_terms()


# --- composition fix additions (2026-07-20) ---


def single_field_index(tmp_path, **extra_fields):
    directory = tmp_path / "single"
    directory.mkdir()
    schema = Schema(key=ID(stored=True), **extra_fields)
    return index.create_in(str(directory), schema)


def keys(ix, query):
    with ix.searcher() as searcher:
        return {hit["key"] for hit in searcher.search(query, limit=None)}


def test_datetime_field_returns_stored_datetime_value(tmp_path):
    ix = single_field_index(tmp_path, when=DATETIME(stored=True))
    moment = datetime(2021, 5, 4, 12, 30, 15)
    with ix.writer() as writer:
        writer.add_document(key="a", when=moment)
    with ix.searcher() as searcher:
        assert searcher.search(Term("key", "a"), limit=None)[0]["when"] == moment


def test_boolean_field_preserves_stored_false_value(tmp_path):
    _, ix = make_index(tmp_path)
    add_two(ix)
    with ix.searcher() as searcher:
        hit = searcher.search(Term("path", "b"), limit=None)[0]
        assert (hit["number"], hit["flag"]) == (2, False)


def test_numeric_field_preserves_negative_and_zero_stored_values(tmp_path):
    ix = single_field_index(tmp_path, number=NUMERIC(stored=True))
    with ix.writer() as writer:
        writer.add_document(key="neg", number=-5)
        writer.add_document(key="zero", number=0)
    with ix.searcher() as searcher:
        negative = searcher.search(Term("key", "neg"), limit=None)[0]
        zero = searcher.search(Term("key", "zero"), limit=None)[0]
        assert (negative["number"], zero["number"]) == (-5, 0)


def test_id_field_indexes_value_with_space_as_single_term(tmp_path):
    ix = single_field_index(tmp_path)
    with ix.writer() as writer:
        writer.add_document(key="hello world")
    assert keys(ix, Term("key", "hello world")) == {"hello world"}
    assert keys(ix, Term("key", "hello")) == set()


def test_text_field_indexes_each_word_of_the_supplied_text(tmp_path):
    _, ix = make_index(tmp_path)
    add_two(ix)
    assert paths(ix, Term("body", "alpha")) == {"a"}
    assert paths(ix, Term("body", "beta")) == {"a", "b"}


def test_keyword_field_default_splits_on_spaces_preserving_case(tmp_path):
    ix = single_field_index(tmp_path, labels=KEYWORD(stored=True))
    with ix.writer() as writer:
        writer.add_document(key="a", labels="Red Blue")
    assert keys(ix, Term("labels", "Red")) == {"a"}
    assert keys(ix, Term("labels", "Blue")) == {"a"}
    assert keys(ix, Term("labels", "red")) == set()


def test_keyword_commas_split_keeps_multiword_terms_intact(tmp_path):
    ix = single_field_index(tmp_path, ctags=KEYWORD(stored=True, commas=True))
    with ix.writer() as writer:
        writer.add_document(key="a", ctags="Red Rose,Blue")
    assert keys(ix, Term("ctags", "Red Rose")) == {"a"}
    assert keys(ix, Term("ctags", "Blue")) == {"a"}


def test_schema_names_lists_every_defined_field():
    schema = Schema(
        path=ID(stored=True),
        body=TEXT(stored=True),
        tags=KEYWORD,
        number=NUMERIC,
        flag=BOOLEAN,
        when=DATETIME,
    )
    assert set(schema.names()) == {"path", "body", "tags", "number", "flag", "when"}


def test_document_omitting_schema_fields_stores_only_supplied_values(tmp_path):
    ix = single_field_index(tmp_path, body=TEXT(stored=True))
    with ix.writer() as writer:
        writer.add_document(key="only-key")
    with ix.searcher() as searcher:
        hit = searcher.search(Term("key", "only-key"), limit=None)[0]
        assert hit.fields() == {"key": "only-key"}


# --- new atomic tests ---


def test_doc_count_reflects_committed_document_count(tmp_path):
    """Index.doc_count() must return the number of non-deleted committed documents."""
    _, ix = make_index(tmp_path)
    assert ix.doc_count() == 0
    add_two(ix)
    assert ix.doc_count() == 2


def test_delete_by_term_returns_number_of_staged_deletions(tmp_path):
    """delete_by_term must return the number of documents staged for deletion."""
    _, ix = make_index(tmp_path)
    add_two(ix)
    writer = ix.writer()
    count = writer.delete_by_term("path", "a")
    writer.commit()
    assert count == 1


def test_delete_by_query_returns_zero_for_unmatched_query(tmp_path):
    """delete_by_query must return 0 when no committed document matches."""
    _, ix = make_index(tmp_path)
    add_two(ix)
    writer = ix.writer()
    count = writer.delete_by_query(Term("body", "nonexistent"))
    writer.commit()
    assert count == 0


def test_create_in_clears_documents_of_existing_index(tmp_path):
    """create_in for an existing index name must clear its contents."""
    directory, ix = make_index(tmp_path)
    add_two(ix)
    assert ix.doc_count() == 2
    replacement = index.create_in(str(directory), ix.schema)
    assert replacement.doc_count() == 0


def test_exists_in_false_for_empty_directory(tmp_path):
    """exists_in must return False for a directory with no index."""
    directory = tmp_path / "empty"
    directory.mkdir()
    assert index.exists_in(str(directory)) is False


def test_search_scored_length_equals_limit(tmp_path):
    """scored_length must equal the limit when more documents match than the limit."""
    _, ix = make_index(tmp_path)
    add_two(ix)
    with ix.searcher() as searcher:
        result = searcher.search(Term("body", "beta"), limit=1)
        assert result.scored_length() == 1
        assert len(result) == 2


def test_hit_fields_returns_stored_mapping_with_all_supplied_fields(tmp_path):
    """Hit.fields() must return the stored-field mapping for the matched document."""
    _, ix = make_index(tmp_path)
    add_two(ix)
    with ix.searcher() as searcher:
        hit = searcher.search(Term("path", "a"), limit=None)[0]
        fields = hit.fields()
        assert fields["path"] == "a"
        assert fields["body"] == "alpha beta"
        assert fields["number"] == 1
        assert fields["flag"] is True


def test_create_in_returns_index_object(tmp_path):
    directory = tmp_path / "create-in"
    directory.mkdir()
    ix = index.create_in(str(directory), Schema(path=ID(stored=True)))
    assert isinstance(ix, index.Index)
    assert set(ix.schema.names()) == {"path"}


def test_open_dir_returns_index_object(tmp_path):
    directory, created = make_index(tmp_path)
    ix = index.open_dir(str(directory))
    assert isinstance(ix, index.Index)
    assert set(ix.schema.names()) == set(created.schema.names())


def test_writer_add_document_succeeds_with_valid_fields(tmp_path):
    _, ix = make_index(tmp_path)
    with ix.writer() as writer:
        writer.add_document(path="x", body="hello")
    assert ix.doc_count() == 1


def test_query_parser_parses_single_word():
    parser = QueryParser("body", Schema(body=TEXT))
    q = parser.parse("hello")
    assert q == Term("body", "hello")


def test_and_query_constructor_accepts_subqueries():
    terms = [Term("body", "alpha"), Term("body", "beta")]
    q = And(terms)
    assert list(q.children()) == terms


def test_or_query_constructor_accepts_subqueries():
    terms = [Term("body", "alpha"), Term("body", "beta")]
    q = Or(terms)
    assert list(q.children()) == terms
