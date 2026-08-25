"""Integration tests for whoosh-index-search-fullrepro-001."""

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

from conftest import add_two, make_index, paths


depends_on = pytest.mark.depends_on


@pytest.mark.depends_on("test_installable_fields_surface_constructs_a_schema", "test_create_in_returns_index_object", "test_exists_in_false_for_empty_directory")
def test_installable_index_surface_creates_an_index(tmp_path):
    """Seam: lifecycle crossing from create_in to exists_in recognition."""
    directory = tmp_path / "surface-index"
    directory.mkdir()
    index.create_in(str(directory), Schema(path=ID(stored=True)))
    assert index.exists_in(str(directory)) is True


@pytest.mark.depends_on("test_text_field_is_searchable_and_returns_stored_value", "test_query_parser_parses_single_word")
def test_installable_query_and_parser_surfaces_search_documents(tmp_path):
    """Seam: protocol handoff from QueryParser parse to searcher results."""
    _, ix = make_index(tmp_path)
    add_two(ix)
    parsed = QueryParser("body", ix.schema).parse("alpha")
    assert paths(ix, Or([Term("body", "alpha"), parsed])) == {"a"}


@depends_on("test_atomic::test_doc_count_reflects_committed_document_count")
@depends_on("test_atomic::test_writer_add_document_succeeds_with_valid_fields")
@pytest.mark.depends_on("test_installable_fields_surface_constructs_a_schema", "test_text_field_is_searchable_and_returns_stored_value")
def test_product_state_commit_is_visible_to_a_new_searcher(tmp_path):
    """Seam: state consistency between writer commit and searcher visibility."""
    _, ix = make_index(tmp_path)
    with ix.writer() as writer:
        writer.add_document(path="a", body="alpha")
    assert paths(ix, Term("body", "alpha")) == {"a"}


@depends_on("test_atomic::test_text_field_is_searchable_and_returns_stored_value")
@depends_on("test_atomic::test_writer_add_document_succeeds_with_valid_fields")
@pytest.mark.depends_on("test_keyword_commas_split_keeps_multiword_terms_intact", "test_doc_count_reflects_committed_document_count")
def test_product_state_cancel_keeps_previously_committed_projection(tmp_path):
    """Seam: state consistency when writer cancel preserves prior commit."""
    _, ix = make_index(tmp_path)
    add_two(ix)
    writer = ix.writer()
    writer.add_document(path="c", body="alpha")
    writer.cancel()
    assert paths(ix, Term("body", "alpha")) == {"a"}


@depends_on("test_atomic::test_doc_count_reflects_committed_document_count")
@depends_on("test_atomic::test_text_field_is_searchable_and_returns_stored_value")
@pytest.mark.depends_on("test_open_dir_returns_index_object", "test_keyword_commas_split_keeps_multiword_terms_intact", "test_create_in_clears_documents_of_existing_index")
def test_product_state_existing_searcher_keeps_its_open_generation(tmp_path):
    """CVI-1: committed writes visible only after old searcher closes."""
    _, ix = make_index(tmp_path)
    add_two(ix)
    with ix.searcher() as old_searcher:
        with ix.writer() as writer:
            writer.add_document(path="c", body="alpha")
        assert {hit["path"] for hit in old_searcher.search(Term("body", "alpha"), limit=None)} == {"a"}
    assert paths(ix, Term("body", "alpha")) == {"a", "c"}


@pytest.mark.depends_on("test_exists_in_false_for_empty_directory", "test_open_dir_returns_index_object")
def test_exists_in_is_false_for_directory_without_an_index(tmp_path):
    """Seam: lifecycle crossing for empty directory before index creation."""
    assert index.exists_in(str(tmp_path)) is False


@pytest.mark.depends_on("test_create_in_returns_index_object", "test_create_in_clears_documents_of_existing_index", "test_open_dir_returns_index_object")
def test_create_in_makes_a_recognizable_index(tmp_path):
    """Seam: lifecycle crossing from create_in to exists_in."""
    directory, _ = make_index(tmp_path)
    assert index.exists_in(str(directory)) is True


@pytest.mark.depends_on("test_open_dir_returns_index_object", "test_doc_count_reflects_committed_document_count")
def test_open_dir_reopens_committed_documents(tmp_path):
    """Seam: state consistency between in-process index and reopened directory."""
    directory, ix = make_index(tmp_path)
    add_two(ix)
    reopened = index.open_dir(str(directory))
    assert paths(reopened, Term("body", "alpha")) == {"a"}


@depends_on("test_atomic::test_create_in_returns_index_object", "test_atomic::test_open_dir_returns_index_object")
@pytest.mark.depends_on("test_text_field_indexes_each_word_of_the_supplied_text", "test_id_field_indexes_value_with_space_as_single_term")
def test_named_indexes_are_independently_openable(tmp_path):
    """Seam: config interaction between named indexes in one directory."""
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


@pytest.mark.depends_on("test_create_in_clears_documents_of_existing_index", "test_open_dir_returns_index_object", "test_doc_count_reflects_committed_document_count")
def test_creating_an_existing_named_index_clears_its_documents(tmp_path):
    """Seam: lifecycle crossing when recreate clears committed documents."""
    directory, ix = make_index(tmp_path)
    add_two(ix)
    replacement = index.create_in(str(directory), ix.schema)
    assert paths(replacement, Term("body", "alpha")) == set()


@pytest.mark.depends_on("test_writer_add_document_succeeds_with_valid_fields")
def test_writer_context_commits_on_normal_exit(tmp_path):
    """Seam: lifecycle crossing through writer context manager commit."""
    _, ix = make_index(tmp_path)
    with ix.writer() as writer:
        writer.add_document(path="a", body="alpha")
    assert paths(ix, Term("path", "a")) == {"a"}


@pytest.mark.depends_on("test_writer_add_document_succeeds_with_valid_fields")
def test_writer_context_cancels_on_exception(tmp_path):
    """Seam: error propagation from writer exception to cancel without commit."""
    _, ix = make_index(tmp_path)
    with pytest.raises(RuntimeError):
        with ix.writer() as writer:
            writer.add_document(path="a", body="alpha")
            raise RuntimeError("stop")
    assert paths(ix, Term("body", "alpha")) == set()


@depends_on("test_atomic::test_error_unknown_field_error_is_observable")
@pytest.mark.depends_on("test_schema_rejects_unsupported_field_definition", "test_schema_rejects_invalid_field_names", "test_writer_add_document_succeeds_with_valid_fields")
def test_add_document_rejects_unknown_schema_field(tmp_path):
    """Seam: error propagation from UnknownFieldError before commit."""
    _, ix = make_index(tmp_path)
    writer = ix.writer()
    with pytest.raises(UnknownFieldError):
        writer.add_document(path="a", body="alpha", untracked="x")
    writer.cancel()
    assert paths(ix, Term("body", "alpha")) == set()


@pytest.mark.depends_on("test_writer_add_document_succeeds_with_valid_fields", "test_numeric_field_preserves_negative_and_zero_stored_values", "test_document_omitting_schema_fields_stores_only_supplied_values")
def test_add_document_preserves_duplicate_documents(tmp_path):
    """Seam: state consistency when duplicate documents are indexed."""
    _, ix = make_index(tmp_path)
    with ix.writer() as writer:
        writer.add_document(path="a", body="alpha")
        writer.add_document(path="a", body="alpha")
    with ix.searcher() as searcher:
        results = searcher.search(Term("body", "alpha"), limit=None)
        assert len(results) == 2


@pytest.mark.depends_on("test_numeric_field_preserves_negative_and_zero_stored_values", "test_numeric_and_boolean_fields_preserve_stored_values", "test_text_field_is_searchable_and_returns_stored_value")
def test_stored_override_keeps_index_and_stored_values_distinct(tmp_path):
    """Seam: state consistency between indexed tokens and stored override."""
    _, ix = make_index(tmp_path)
    with ix.writer() as writer:
        writer.add_document(path="a", body="indexed words", _stored_body="stored value")
    with ix.searcher() as searcher:
        hit = searcher.search(Term("body", "indexed"), limit=None)[0]
        assert hit["body"] == "stored value"


@pytest.mark.depends_on("test_text_field_is_searchable_and_returns_stored_value", "test_id_field_matches_a_complete_term_only")
def test_update_document_replaces_matching_unique_document(tmp_path):
    """Seam: state consistency when update replaces unique document."""
    _, ix = make_index(tmp_path)
    add_two(ix)
    with ix.writer() as writer:
        writer.update_document(path="a", body="replacement")
    assert paths(ix, Term("body", "alpha")) == set()
    assert paths(ix, Term("body", "replacement")) == {"a"}


@pytest.mark.depends_on("test_writer_add_document_succeeds_with_valid_fields", "test_id_field_matches_a_complete_term_only", "test_document_omitting_schema_fields_stores_only_supplied_values")
def test_update_document_adds_when_no_unique_document_matches(tmp_path):
    """Seam: state consistency when update adds without prior match."""
    _, ix = make_index(tmp_path)
    add_two(ix)
    with ix.writer() as writer:
        writer.update_document(path="c", body="alpha")
    assert paths(ix, Term("body", "alpha")) == {"a", "c"}
    assert paths(ix, Term("body", "beta")) == {"a", "b"}


@depends_on("test_atomic::test_text_field_is_searchable_and_returns_stored_value")
@pytest.mark.depends_on("test_delete_by_term_returns_number_of_staged_deletions")
def test_cancel_discards_staged_addition(tmp_path):
    """Seam: lifecycle crossing when cancel discards uncommitted writes."""
    _, ix = make_index(tmp_path)
    writer = ix.writer()
    writer.add_document(path="a", body="alpha")
    writer.cancel()
    assert paths(ix, Term("body", "alpha")) == set()


@pytest.mark.depends_on("test_error_lock_error_is_observable")
def test_second_writer_raises_lock_error(tmp_path):
    """Seam: error propagation from concurrent writer to LockError."""
    _, ix = make_index(tmp_path)
    writer = ix.writer()
    with pytest.raises(index.LockError):
        ix.writer()
    writer.cancel()


@pytest.mark.depends_on("test_id_field_matches_a_complete_term_only", "test_delete_by_term_returns_number_of_staged_deletions")
def test_delete_by_term_removes_committed_document(tmp_path):
    """Seam: state consistency between delete_by_term and search results."""
    _, ix = make_index(tmp_path)
    add_two(ix)
    with ix.writer() as writer:
        writer.delete_by_term("path", "a")
    assert paths(ix, Term("path", "a")) == set()


@pytest.mark.depends_on("test_delete_by_query_returns_zero_for_unmatched_query")
def test_delete_by_query_removes_matching_documents(tmp_path):
    """Seam: state consistency between delete_by_query and search results."""
    _, ix = make_index(tmp_path)
    add_two(ix)
    with ix.writer() as writer:
        writer.delete_by_query(Term("body", "gamma"))
    assert paths(ix, Term("body", "gamma")) == set()


@pytest.mark.depends_on("test_text_field_is_searchable_and_returns_stored_value", "test_schema_rejects_invalid_field_names")
def test_invalid_numeric_value_fails_before_commit(tmp_path):
    """Seam: error propagation from invalid field value before commit."""
    _, ix = make_index(tmp_path)
    writer = ix.writer()
    with pytest.raises((ValueError, TypeError, OverflowError)):
        writer.add_document(path="a", body="alpha", number="not-a-number")
    writer.cancel()
    assert paths(ix, Term("body", "alpha")) == set()


@pytest.mark.depends_on("test_text_field_indexes_each_word_of_the_supplied_text", "test_text_field_is_searchable_and_returns_stored_value")
def test_term_query_matches_one_field(tmp_path):
    """Seam: protocol handoff from Term query to matching document paths."""
    _, ix = make_index(tmp_path)
    add_two(ix)
    assert paths(ix, Term("body", "gamma")) == {"b"}


@pytest.mark.depends_on("test_and_query_constructor_accepts_subqueries", "test_text_field_is_searchable_and_returns_stored_value", "test_schema_names_lists_every_defined_field")
def test_and_query_requires_every_term(tmp_path):
    """Seam: protocol handoff from And query composition to results."""
    _, ix = make_index(tmp_path)
    add_two(ix)
    assert paths(ix, And([Term("body", "alpha"), Term("tags", "red")])) == {"a"}
    assert paths(ix, And([Term("body", "alpha"), Term("body", "gamma")])) == set()


@pytest.mark.depends_on("test_or_query_constructor_accepts_subqueries", "test_text_field_is_searchable_and_returns_stored_value")
def test_or_query_matches_either_term(tmp_path):
    """Seam: protocol handoff from Or query composition to results."""
    _, ix = make_index(tmp_path)
    add_two(ix)
    assert paths(ix, Or([Term("body", "alpha"), Term("body", "gamma")])) == {"a", "b"}


@pytest.mark.depends_on("test_query_parser_parses_single_word", "test_keyword_field_default_splits_on_spaces_preserving_case")
def test_query_parser_assigns_unfielded_terms_to_default_field(tmp_path):
    """Seam: protocol handoff from QueryParser to default-field search."""
    _, ix = make_index(tmp_path)
    add_two(ix)
    parser = QueryParser("body", ix.schema)
    assert paths(ix, parser.parse("alpha")) == {"a"}


@pytest.mark.depends_on("test_query_parser_parses_single_word", "test_open_dir_returns_index_object")
def test_query_parser_without_schema_returns_a_query_object():
    """Seam: lifecycle crossing for schema-less QueryParser parse."""
    assert QueryParser("body", None).parse("alpha") == Term("body", "alpha")


@pytest.mark.depends_on("test_query_parser_parses_single_word", "test_writer_add_document_succeeds_with_valid_fields")
def test_invalid_query_syntax_produces_an_empty_search_result(tmp_path):
    """Seam: invalid parser input produces an error query without mutating the index."""
    _, ix = make_index(tmp_path)
    add_two(ix)
    parsed = QueryParser("body", ix.schema).parse("AND OR NOT")
    with ix.searcher() as searcher:
        assert len(searcher.search(parsed, limit=None)) == 0
    assert ix.doc_count() == 2


def test_multifield_parser_searches_configured_fields(tmp_path):
    """Seam: config interaction between MultifieldParser fields and hits."""
    _, ix = make_index(tmp_path)
    add_two(ix)
    parser = MultifieldParser(["body", "tags"], ix.schema)
    assert paths(ix, parser.parse("red")) == {"a"}


def test_simple_parser_returns_a_searchable_query(tmp_path):
    """Seam: protocol handoff from SimpleParser to searchable query."""
    _, ix = make_index(tmp_path)
    add_two(ix)
    assert paths(ix, SimpleParser("body", ix.schema).parse("alpha")) == {"a"}


def test_nonmatching_query_returns_empty_results(tmp_path):
    """Seam: state consistency when no documents match query."""
    _, ix = make_index(tmp_path)
    add_two(ix)
    assert paths(ix, Term("body", "missing")) == set()


@depends_on("test_atomic::test_search_scored_length_equals_limit")
def test_search_limit_retains_only_requested_scored_hits(tmp_path):
    """Seam: state consistency between search limit and scored_length."""
    _, ix = make_index(tmp_path)
    add_two(ix)
    with ix.searcher() as searcher:
        result = searcher.search(Term("body", "beta"), limit=1)
        assert result.scored_length() == 1


def test_search_limit_none_returns_all_matches(tmp_path):
    """Seam: state consistency when limit=None returns all matches."""
    _, ix = make_index(tmp_path)
    add_two(ix)
    with ix.searcher() as searcher:
        assert len(searcher.search(Term("body", "beta"), limit=None)) == 2


@depends_on("test_atomic::test_text_field_is_searchable_and_returns_stored_value")
def test_search_filter_keeps_only_permitted_matches(tmp_path):
    """Seam: config interaction between query and filter constraints."""
    _, ix = make_index(tmp_path)
    add_two(ix)
    assert paths(ix, Term("body", "beta"), filter=Term("path", "a")) == {"a"}


@depends_on("test_atomic::test_text_field_is_searchable_and_returns_stored_value")
def test_search_mask_omits_excluded_matches(tmp_path):
    """Seam: config interaction between query and mask exclusions."""
    _, ix = make_index(tmp_path)
    add_two(ix)
    assert paths(ix, Term("body", "beta"), mask=Term("path", "a")) == {"b"}


@depends_on("test_atomic::test_hit_fields_returns_stored_mapping_with_all_supplied_fields")
def test_results_are_a_sequence_of_dictionary_like_hits(tmp_path):
    """Seam: protocol handoff from search results to dictionary-like hits."""
    _, ix = make_index(tmp_path)
    add_two(ix)
    with ix.searcher() as searcher:
        result = searcher.search(Term("body", "alpha"), limit=None)
        assert result[0].fields()["path"] == "a"


def test_accessing_hit_outside_scored_range_raises_index_error(tmp_path):
    """Seam: error propagation when accessing out-of-range result index."""
    _, ix = make_index(tmp_path)
    add_two(ix)
    with ix.searcher() as searcher:
        result = searcher.search(Term("body", "alpha"), limit=None)
        with pytest.raises(IndexError):
            result[1]


@depends_on("test_atomic::test_error_no_terms_exception_is_observable")
def test_terms_true_exposes_matched_terms(tmp_path):
    """Seam: state consistency when terms=True exposes matched terms."""
    _, ix = make_index(tmp_path)
    add_two(ix)
    with ix.searcher() as searcher:
        result = searcher.search(Term("body", "alpha"), terms=True, limit=None)
        assert result.has_matched_terms() is True
        assert result.matched_terms() and result[0].matched_terms()


@depends_on("test_atomic::test_error_no_terms_exception_is_observable")
def test_matched_terms_without_terms_flag_raises_no_terms_exception(tmp_path):
    """Seam: error propagation from matched_terms without terms flag."""
    _, ix = make_index(tmp_path)
    add_two(ix)
    with ix.searcher() as searcher:
        result = searcher.search(Term("body", "alpha"), limit=None)
        with pytest.raises(NoTermsException):
            result.matched_terms()


def test_error_invalid_field_value_does_not_publish(tmp_path):
    """Seam: error propagation prevents invalid document from publishing."""
    _, ix = make_index(tmp_path)
    writer = ix.writer()
    with pytest.raises((ValueError, TypeError, OverflowError)):
        writer.add_document(path="a", body="alpha", number="invalid")
    writer.cancel()
    assert paths(ix, Term("body", "alpha")) == set()


@depends_on("test_atomic::test_open_dir_returns_index_object", "test_atomic::test_writer_add_document_succeeds_with_valid_fields")
def test_invariant_commit_is_visible_after_open_dir(tmp_path):
    """CVI-2: commit visible after reopening index directory."""
    directory, ix = make_index(tmp_path)
    with ix.writer() as writer:
        writer.add_document(path="a", body="alpha")
    assert paths(index.open_dir(str(directory)), Term("body", "alpha")) == {"a"}


def test_invariant_exists_in_tracks_committed_index(tmp_path):
    """CVI-3: exists_in remains true across committed writes."""
    directory, ix = make_index(tmp_path)
    assert index.exists_in(str(directory)) is True
    with ix.writer() as writer:
        writer.add_document(path="a", body="alpha")
    assert index.exists_in(str(directory)) is True


def test_invariant_stored_text_is_searchable_and_returned(tmp_path):
    """CVI-4: stored text searchable and returned in hit projection."""
    _, ix = make_index(tmp_path)
    with ix.writer() as writer:
        writer.add_document(path="a", body="alpha")
    with ix.searcher() as searcher:
        assert searcher.search(Term("body", "alpha"), limit=None)[0]["body"] == "alpha"


def test_invariant_unique_update_removes_prior_match(tmp_path):
    """CVI-5: unique update removes prior term from search projection."""
    _, ix = make_index(tmp_path)
    with ix.writer() as writer:
        writer.add_document(path="a", body="old")
    with ix.writer() as writer:
        writer.update_document(path="a", body="new")
    assert paths(ix, Term("body", "old")) == set()
    assert paths(ix, Term("body", "new")) == {"a"}


def test_invariant_cancel_restores_previous_document_set(tmp_path):
    """CVI-6: cancel restores previously committed document set."""
    _, ix = make_index(tmp_path)
    add_two(ix)
    writer = ix.writer()
    writer.delete_by_term("path", "a")
    writer.cancel()
    assert paths(ix, Term("path", "a")) == {"a"}


@depends_on("test_atomic::test_doc_count_reflects_committed_document_count")
@depends_on("test_atomic::test_delete_by_term_returns_number_of_staged_deletions")
def test_invariant_committed_deletion_changes_doc_count(tmp_path):
    """CVI-7: committed deletion reduces doc_count consistently."""
    _, ix = make_index(tmp_path)
    add_two(ix)
    with ix.writer() as writer:
        writer.delete_by_term("path", "a")
    assert ix.doc_count() == 1


def test_workflow_creates_writes_and_searches_two_documents(tmp_path):
    """Seam: lifecycle crossing from create through write to search."""
    _, ix = make_index(tmp_path)
    add_two(ix)
    assert paths(ix, QueryParser("body", ix.schema).parse("beta")) == {"a", "b"}


def test_workflow_absent_term_returns_no_hit(tmp_path):
    """Seam: lifecycle crossing when absent term yields empty workflow."""
    _, ix = make_index(tmp_path)
    add_two(ix)
    assert paths(ix, QueryParser("body", ix.schema).parse("absent")) == set()


def test_workflow_reopened_index_preserves_result_data(tmp_path):
    """Seam: state consistency when reopened index preserves hit data."""
    directory, ix = make_index(tmp_path)
    add_two(ix)
    reopened = index.open_dir(str(directory))
    with reopened.searcher() as searcher:
        hit = searcher.search(QueryParser("body", reopened.schema).parse("alpha"), limit=None)[0]
        assert hit["path"] == "a"
