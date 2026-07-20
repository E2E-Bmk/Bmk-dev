"""Track B public behavioral oracle generated from spec_v3 and reference observations."""

from __future__ import annotations

import pytest

from whoosh import index
from whoosh.fields import (
    BOOLEAN,
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


def make_index(tmp_path, name=None):
    directory = tmp_path / (name or "index")
    directory.mkdir()
    schema = Schema(
        path=ID(stored=True, unique=True),
        body=TEXT(stored=True),
        tags=KEYWORD(stored=True, commas=True, lowercase=True),
        note=STORED,
        number=NUMERIC(stored=True),
        flag=BOOLEAN(stored=True),
    )
    return directory, index.create_in(str(directory), schema, indexname=name)


def add_two(ix):
    with ix.writer() as writer:
        writer.add_document(path="a", body="alpha beta", tags="Red,Blue", note="first", number=1, flag=True)
        writer.add_document(path="b", body="beta gamma", tags="Blue", note="second", number=2, flag=False)


def paths(ix, query, **kwargs):
    with ix.searcher() as searcher:
        return {hit["path"] for hit in searcher.search(query, limit=None, **kwargs)}


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
