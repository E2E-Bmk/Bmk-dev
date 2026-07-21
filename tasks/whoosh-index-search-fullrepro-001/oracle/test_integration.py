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


def test_installable_index_surface_creates_an_index(tmp_path):
    directory = tmp_path / "surface-index"
    directory.mkdir()
    index.create_in(str(directory), Schema(path=ID(stored=True)))
    assert index.exists_in(str(directory)) is True


def test_installable_query_and_parser_surfaces_search_documents(tmp_path):
    _, ix = make_index(tmp_path)
    add_two(ix)
    parsed = QueryParser("body", ix.schema).parse("alpha")
    assert paths(ix, Or([Term("body", "alpha"), parsed])) == {"a"}


def test_product_state_commit_is_visible_to_a_new_searcher(tmp_path):
    _, ix = make_index(tmp_path)
    with ix.writer() as writer:
        writer.add_document(path="a", body="alpha")
    assert paths(ix, Term("body", "alpha")) == {"a"}


def test_product_state_cancel_keeps_previously_committed_projection(tmp_path):
    _, ix = make_index(tmp_path)
    add_two(ix)
    writer = ix.writer()
    writer.add_document(path="c", body="alpha")
    writer.cancel()
    assert paths(ix, Term("body", "alpha")) == {"a"}


def test_product_state_existing_searcher_keeps_its_open_generation(tmp_path):
    _, ix = make_index(tmp_path)
    add_two(ix)
    with ix.searcher() as old_searcher:
        with ix.writer() as writer:
            writer.add_document(path="c", body="alpha")
        assert {hit["path"] for hit in old_searcher.search(Term("body", "alpha"), limit=None)} == {"a"}
    assert paths(ix, Term("body", "alpha")) == {"a", "c"}


def test_exists_in_is_false_for_directory_without_an_index(tmp_path):
    assert index.exists_in(str(tmp_path)) is False


def test_create_in_makes_a_recognizable_index(tmp_path):
    directory, _ = make_index(tmp_path)
    assert index.exists_in(str(directory)) is True


def test_open_dir_reopens_committed_documents(tmp_path):
    directory, ix = make_index(tmp_path)
    add_two(ix)
    reopened = index.open_dir(str(directory))
    assert paths(reopened, Term("body", "alpha")) == {"a"}


def test_named_indexes_are_independently_openable(tmp_path):
    directory = tmp_path / "named"
    directory.mkdir()
    schema = Schema(path=ID(stored=True), body=TEXT(stored=True))
    first = index.create_in(str(directory), schema, indexname="first")
    second = index.create_in(str(directory), schema, indexname="second")
    with first.writer() as writer:
        writer.add_document(path="a", body="alpha")
    with second.writer() as writer:
        writer.add_document(path="b", body="beta")
    assert paths(index.open_dir(str(directory), indexname="first"), Term("body", "alpha")) == {"a"}
    assert paths(index.open_dir(str(directory), indexname="second"), Term("body", "beta")) == {"b"}


def test_creating_an_existing_named_index_clears_its_documents(tmp_path):
    directory, ix = make_index(tmp_path)
    add_two(ix)
    replacement = index.create_in(str(directory), ix.schema)
    assert paths(replacement, Term("body", "alpha")) == set()


def test_writer_context_commits_on_normal_exit(tmp_path):
    _, ix = make_index(tmp_path)
    with ix.writer() as writer:
        writer.add_document(path="a", body="alpha")
    assert paths(ix, Term("path", "a")) == {"a"}


def test_writer_context_cancels_on_exception(tmp_path):
    _, ix = make_index(tmp_path)
    with pytest.raises(RuntimeError):
        with ix.writer() as writer:
            writer.add_document(path="a", body="alpha")
            raise RuntimeError("stop")
    assert paths(ix, Term("body", "alpha")) == set()


def test_add_document_rejects_unknown_schema_field(tmp_path):
    _, ix = make_index(tmp_path)
    writer = ix.writer()
    with pytest.raises(UnknownFieldError):
        writer.add_document(path="a", body="alpha", untracked="x")
    writer.cancel()
    assert paths(ix, Term("body", "alpha")) == set()


def test_add_document_preserves_duplicate_documents(tmp_path):
    _, ix = make_index(tmp_path)
    with ix.writer() as writer:
        writer.add_document(path="a", body="alpha")
        writer.add_document(path="a", body="alpha")
    with ix.searcher() as searcher:
        results = searcher.search(Term("body", "alpha"), limit=None)
        assert len(results) == 2


def test_stored_override_keeps_index_and_stored_values_distinct(tmp_path):
    _, ix = make_index(tmp_path)
    with ix.writer() as writer:
        writer.add_document(path="a", body="indexed words", _stored_body="stored value")
    with ix.searcher() as searcher:
        hit = searcher.search(Term("body", "indexed"), limit=None)[0]
        assert hit["body"] == "stored value"


def test_update_document_replaces_matching_unique_document(tmp_path):
    _, ix = make_index(tmp_path)
    add_two(ix)
    with ix.writer() as writer:
        writer.update_document(path="a", body="replacement")
    assert paths(ix, Term("body", "alpha")) == set()
    assert paths(ix, Term("body", "replacement")) == {"a"}


def test_update_document_adds_when_no_unique_document_matches(tmp_path):
    _, ix = make_index(tmp_path)
    add_two(ix)
    with ix.writer() as writer:
        writer.update_document(path="c", body="alpha")
    assert paths(ix, Term("body", "alpha")) == {"a", "c"}
    assert paths(ix, Term("body", "beta")) == {"a", "b"}


def test_cancel_discards_staged_addition(tmp_path):
    _, ix = make_index(tmp_path)
    writer = ix.writer()
    writer.add_document(path="a", body="alpha")
    writer.cancel()
    assert paths(ix, Term("body", "alpha")) == set()


def test_second_writer_raises_lock_error(tmp_path):
    _, ix = make_index(tmp_path)
    writer = ix.writer()
    with pytest.raises(index.LockError):
        ix.writer()
    writer.cancel()


def test_delete_by_term_removes_committed_document(tmp_path):
    _, ix = make_index(tmp_path)
    add_two(ix)
    with ix.writer() as writer:
        writer.delete_by_term("path", "a")
    assert paths(ix, Term("path", "a")) == set()


def test_delete_by_query_removes_matching_documents(tmp_path):
    _, ix = make_index(tmp_path)
    add_two(ix)
    with ix.writer() as writer:
        writer.delete_by_query(Term("body", "gamma"))
    assert paths(ix, Term("body", "gamma")) == set()


def test_invalid_numeric_value_fails_before_commit(tmp_path):
    _, ix = make_index(tmp_path)
    writer = ix.writer()
    with pytest.raises(Exception):
        writer.add_document(path="a", body="alpha", number="not-a-number")
    writer.cancel()
    assert paths(ix, Term("body", "alpha")) == set()


def test_term_query_matches_one_field(tmp_path):
    _, ix = make_index(tmp_path)
    add_two(ix)
    assert paths(ix, Term("body", "gamma")) == {"b"}


def test_and_query_requires_every_term(tmp_path):
    _, ix = make_index(tmp_path)
    add_two(ix)
    assert paths(ix, And([Term("body", "alpha"), Term("tags", "red")])) == {"a"}
    assert paths(ix, And([Term("body", "alpha"), Term("body", "gamma")])) == set()


def test_or_query_matches_either_term(tmp_path):
    _, ix = make_index(tmp_path)
    add_two(ix)
    assert paths(ix, Or([Term("body", "alpha"), Term("body", "gamma")])) == {"a", "b"}


def test_query_parser_assigns_unfielded_terms_to_default_field(tmp_path):
    _, ix = make_index(tmp_path)
    add_two(ix)
    parser = QueryParser("body", ix.schema)
    assert paths(ix, parser.parse("alpha")) == {"a"}


def test_query_parser_without_schema_returns_a_query_object():
    assert QueryParser("body", None).parse("alpha") is not None


def test_multifield_parser_searches_configured_fields(tmp_path):
    _, ix = make_index(tmp_path)
    add_two(ix)
    parser = MultifieldParser(["body", "tags"], ix.schema)
    assert paths(ix, parser.parse("red")) == {"a"}


def test_simple_parser_returns_a_searchable_query(tmp_path):
    _, ix = make_index(tmp_path)
    add_two(ix)
    assert paths(ix, SimpleParser("body", ix.schema).parse("alpha")) == {"a"}


def test_nonmatching_query_returns_empty_results(tmp_path):
    _, ix = make_index(tmp_path)
    add_two(ix)
    assert paths(ix, Term("body", "missing")) == set()


def test_search_limit_retains_only_requested_scored_hits(tmp_path):
    _, ix = make_index(tmp_path)
    add_two(ix)
    with ix.searcher() as searcher:
        result = searcher.search(Term("body", "beta"), limit=1)
        assert result.scored_length() == 1


def test_search_limit_none_returns_all_matches(tmp_path):
    _, ix = make_index(tmp_path)
    add_two(ix)
    with ix.searcher() as searcher:
        assert len(searcher.search(Term("body", "beta"), limit=None)) == 2


def test_search_filter_keeps_only_permitted_matches(tmp_path):
    _, ix = make_index(tmp_path)
    add_two(ix)
    assert paths(ix, Term("body", "beta"), filter=Term("path", "a")) == {"a"}


def test_search_mask_omits_excluded_matches(tmp_path):
    _, ix = make_index(tmp_path)
    add_two(ix)
    assert paths(ix, Term("body", "beta"), mask=Term("path", "a")) == {"b"}


def test_results_are_a_sequence_of_dictionary_like_hits(tmp_path):
    _, ix = make_index(tmp_path)
    add_two(ix)
    with ix.searcher() as searcher:
        result = searcher.search(Term("body", "alpha"), limit=None)
        assert result[0].fields()["path"] == "a"


def test_accessing_hit_outside_scored_range_raises_index_error(tmp_path):
    _, ix = make_index(tmp_path)
    add_two(ix)
    with ix.searcher() as searcher:
        result = searcher.search(Term("body", "alpha"), limit=None)
        with pytest.raises(IndexError):
            result[1]


def test_terms_true_exposes_matched_terms(tmp_path):
    _, ix = make_index(tmp_path)
    add_two(ix)
    with ix.searcher() as searcher:
        result = searcher.search(Term("body", "alpha"), terms=True, limit=None)
        assert result.has_matched_terms() is True
        assert result.matched_terms() and result[0].matched_terms()


def test_matched_terms_without_terms_flag_raises_no_terms_exception(tmp_path):
    _, ix = make_index(tmp_path)
    add_two(ix)
    with ix.searcher() as searcher:
        result = searcher.search(Term("body", "alpha"), limit=None)
        with pytest.raises(NoTermsException):
            result.matched_terms()


def test_error_invalid_field_value_does_not_publish(tmp_path):
    _, ix = make_index(tmp_path)
    writer = ix.writer()
    with pytest.raises(Exception):
        writer.add_document(path="a", body="alpha", number="invalid")
    writer.cancel()
    assert paths(ix, Term("body", "alpha")) == set()


def test_invariant_commit_is_visible_after_open_dir(tmp_path):
    directory, ix = make_index(tmp_path)
    with ix.writer() as writer:
        writer.add_document(path="a", body="alpha")
    assert paths(index.open_dir(str(directory)), Term("body", "alpha")) == {"a"}


def test_invariant_exists_in_tracks_committed_index(tmp_path):
    directory, ix = make_index(tmp_path)
    assert index.exists_in(str(directory)) is True
    with ix.writer() as writer:
        writer.add_document(path="a", body="alpha")
    assert index.exists_in(str(directory)) is True


def test_invariant_stored_text_is_searchable_and_returned(tmp_path):
    _, ix = make_index(tmp_path)
    with ix.writer() as writer:
        writer.add_document(path="a", body="alpha")
    with ix.searcher() as searcher:
        assert searcher.search(Term("body", "alpha"), limit=None)[0]["body"] == "alpha"


def test_invariant_unique_update_removes_prior_match(tmp_path):
    _, ix = make_index(tmp_path)
    with ix.writer() as writer:
        writer.add_document(path="a", body="old")
    with ix.writer() as writer:
        writer.update_document(path="a", body="new")
    assert paths(ix, Term("body", "old")) == set()
    assert paths(ix, Term("body", "new")) == {"a"}


def test_invariant_cancel_restores_previous_document_set(tmp_path):
    _, ix = make_index(tmp_path)
    add_two(ix)
    writer = ix.writer()
    writer.delete_by_term("path", "a")
    writer.cancel()
    assert paths(ix, Term("path", "a")) == {"a"}


def test_invariant_committed_deletion_changes_doc_count(tmp_path):
    _, ix = make_index(tmp_path)
    add_two(ix)
    with ix.writer() as writer:
        writer.delete_by_term("path", "a")
    assert ix.doc_count() == 1


def test_workflow_creates_writes_and_searches_two_documents(tmp_path):
    _, ix = make_index(tmp_path)
    add_two(ix)
    assert paths(ix, QueryParser("body", ix.schema).parse("beta")) == {"a", "b"}


def test_workflow_absent_term_returns_no_hit(tmp_path):
    _, ix = make_index(tmp_path)
    add_two(ix)
    assert paths(ix, QueryParser("body", ix.schema).parse("absent")) == set()


def test_workflow_reopened_index_preserves_result_data(tmp_path):
    directory, ix = make_index(tmp_path)
    add_two(ix)
    reopened = index.open_dir(str(directory))
    with reopened.searcher() as searcher:
        hit = searcher.search(QueryParser("body", reopened.schema).parse("alpha"), limit=None)[0]
        assert hit["path"] == "a"
