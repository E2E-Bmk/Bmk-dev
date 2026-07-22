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
