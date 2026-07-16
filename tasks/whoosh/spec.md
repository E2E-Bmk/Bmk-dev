# Whoosh Specification

## Product Overview

Whoosh is a pure-Python library for building a full-text index over documents and searching that index through a Python API. A schema defines the document fields; a writer stages changes; committing publishes a new searchable index; a searcher returns stored document data for matching documents.

## Scope

This specification covers the documented public workflow for schemas and built-in field types, directory-backed indexes, writing and updating documents, programmatic and parsed queries, searching, stored result data, and the documented locking and empty-index outcomes.

## Installable Surface

Applications import the covered public interfaces from these paths:

- `whoosh.fields`: `Schema`, `TEXT`, `ID`, `KEYWORD`, `STORED`, `NUMERIC`, `DATETIME`, `BOOLEAN`, `FieldConfigurationError`, and `UnknownFieldError`.
- `whoosh.index`: `create_in(dirname, schema, indexname=None)`, `open_dir(dirname, indexname=None, readonly=False, schema=None)`, `exists_in(dirname, indexname=None)`, `Index`, `LockError`, `IndexError`, `IndexVersionError`, and `EmptyIndexError`.
- `whoosh.qparser`: `QueryParser(fieldname, schema, plugins=None, termclass=..., phraseclass=..., group=...)`, `MultifieldParser`, `SimpleParser`, and `DisMaxParser`.
- `whoosh.query`: `Term`, `And`, and `Or` for constructing queries directly.
- `whoosh.searching`: `Searcher`, `Results`, `Hit`, and `NoTermsException` as values and error outcomes returned by the index/search APIs.
- `whoosh.writing`: `IndexWriter` and `IndexingError`.

## Product State Model

A Whoosh index has three public projections of the same committed document state:

1. The schema projection names each permitted field and describes whether the field is indexed, stored, or both.
2. The directory projection holds an index that `exists_in()` can recognize and that `open_dir()` can reopen by its index name.
3. The search projection exposes committed, non-deleted documents as matches and exposes the stored values of each hit.

The following state rules apply:

- A document added through an `IndexWriter` must not appear in a newly opened searcher until that writer commits; cancelling the writer must return the index to its previously committed search projection.
- A successful commit must make its document changes visible through a newly opened searcher and through an index reopened from the same directory; an existing searcher must continue to expose the generation it already opened.
- A deletion committed through a writer must remove the matching document from subsequent search results; cancellation must return the pre-existing committed document to subsequent search results.
- A value supplied as `_stored_<fieldname>` for a field that is both indexed and stored must be searchable through the indexed value and must be returned through the stored value; an unknown document field name must raise `whoosh.fields.UnknownFieldError` instead of creating an untracked field.
- An index created with an `indexname` must be reopened and checked with that same name; checking a directory or name without a valid index must return `False` from `exists_in`.
- `update_document` on a committed document with matching values in a schema field marked `unique=True` must replace the prior matching document in subsequent searches; when no committed document matches, it must add the new document instead.

## Schemas and Field Types

`Schema(**fields)` maps field names to field types. A document is allowed to omit schema fields. A field definition that is neither a supported field instance nor a supported bare field class must raise `whoosh.fields.FieldConfigurationError`; a field name beginning with `_`, containing spaces, or duplicating a schema field must raise the same exception rather than create an invalid schema.

- `TEXT` indexes body text and records positions for phrase searching. `TEXT(stored=True)` must return the supplied text in result stored fields; a query that has no matching indexed term must return no hit.
- `ID` indexes an entire value as one term. `ID(stored=True)` must return the supplied value in result stored fields; a search that does not match the complete indexed value must return no hit for that `Term` query.
- `KEYWORD` indexes space-separated keywords by default. `KEYWORD(commas=True)` must split on commas, and `KEYWORD(lowercase=True)` must index lowercased keywords; a token absent after the configured splitting and normalization must return no hit.
- `STORED` must return its supplied value in matching hits and must not make that value searchable; a `Term` query against a stored-only field must return no hit.
- `NUMERIC`, `DATETIME`, and `BOOLEAN` accept their documented number, `datetime`, and boolean forms respectively. A supplied value that the chosen field type cannot process must raise an exception before commit; the writer must not publish that failed write.
- `Schema` accepts bare built-in field classes when no constructor options are required and must instantiate them as field definitions. A field definition outside the supported instance/class forms must raise `whoosh.fields.FieldConfigurationError` rather than produce a schema with an unspecified field type.

## Creating and Opening Indexes

`create_in(dirname, schema, indexname=None)` must create an index using the supplied schema in the named directory. Calling it for an existing index name must clear that index's current contents before the new index is used. If the directory cannot be created or written, the operation must raise the underlying filesystem error and must not report a usable new index.

`open_dir(dirname, indexname=None, readonly=False, schema=None)` must open the named index from that directory. `exists_in(dirname, indexname=None)` must return `True` only when the requested directory and name contain a valid index, and must return `False` when no valid index is present. Opening an index whose format is incompatible with the installed library must raise `IndexVersionError`.

The default index name is used when `indexname` is omitted. Multiple named indexes in one directory must remain independently openable by their respective names; opening a missing named index must not expose documents from another index name.

## Writing Documents

`Index.writer(**kwargs)` returns an `IndexWriter`. The writer is a transaction-like context manager: normal context exit must commit staged changes, while context exit caused by an exception must cancel staged changes. A second writer request while an existing writer holds the write lock must raise `LockError` instead of allowing concurrent writes.

`IndexWriter.add_document(**fields)` stages one document. Field keyword names map to schema fields, and documents are allowed to omit optional fields. `add_document` must preserve duplicate documents; a field name absent from the schema must raise `whoosh.fields.UnknownFieldError`, and a field value that cannot be processed must raise an exception before commit, with neither failure publishing that write.

For a field that is both indexed and stored, `add_document(field=value, _stored_field=stored_value)` must index `value` and must expose `stored_value` in the resulting hit. The optional `_boost` and `_<fieldname>_boost` inputs affect scoring only and must not alter the stored field value.

`IndexWriter.update_document(**fields)` must delete committed documents matching values in all supplied fields marked `unique=True` and then stage the replacement document. When no supplied field is unique, or no committed document matches, it must stage an additional document; it must not enforce global uniqueness for `add_document`.

`delete_by_term(fieldname, termtext)` and `delete_by_query(query)` must stage deletion of matching documents and return the number staged for deletion. `commit()` must publish staged additions and deletions and release the write lock. `cancel()` must discard staged additions and deletions and release the write lock. A deletion request against a query with no matches must return zero and must leave committed search results unchanged.

## Queries and Parsing

`Term(fieldname, text)` constructs a query for a term in one field. `And(queries)` must match only documents matching every contained query, while `Or(queries)` must match documents matching at least one contained query. A query whose terms match no indexed documents must return an empty `Results` value rather than inventing a hit.

`QueryParser(fieldname, schema, ...)` parses user query text using the supplied default field and schema. Unfielded terms must be assigned to the configured default field; a parser created with `schema=None` must return a query structure without applying schema text analysis. `parse(text)` must return a query object for valid text and must return the parser's error query outcome for invalid syntax rather than committing or mutating the index.

`MultifieldParser(fieldnames, schema, ...)` must apply unfielded terms across its configured field names. `SimpleParser` and `DisMaxParser` must return their documented preconfigured parser variants; an empty or non-matching query must return a query whose search result is empty rather than returning all documents.

## Searching and Results

`Index.searcher(**kwargs)` returns a `Searcher` over the committed index state and supports context-manager use. `Searcher.search(query, limit=..., filter=..., mask=..., terms=...)` returns a `Results` object. A positive `limit` must limit the scored result set, while `limit=None` must request all matching documents; a non-matching query must return `Results` with length zero.

When `filter` is supplied, results must contain only documents permitted by the filter. When `mask` is supplied, results must omit documents excluded by the mask. A filter or mask that excludes every match must return an empty result set rather than raising for the absence of hits.

`Results` acts as a sequence of matching `Hit` values. Each `Hit` must provide dictionary-like access to its stored field values, and `Hit.fields()` must return that hit's stored-field mapping. `len(results)` must return the total number of matching documents, and `results.scored_length()` must return the number of scored hits retained in the result object. Accessing a hit index outside the scored range must raise `IndexError` rather than return an unrelated document.

When `terms=True` is passed to `search`, `Results.has_matched_terms()` must report that matched-term data is available and `Results.matched_terms()` and `Hit.matched_terms()` must return the recorded matching terms. Calling either matched-term method when the search did not use `terms=True` must raise `whoosh.searching.NoTermsException` rather than fabricate term data.

## Error Semantics

- `LockError` is raised when a writer cannot obtain the index write lock.
- `IndexVersionError` is raised when an index format cannot be read by this library version.
- `EmptyIndexError` represents an index without indexed terms; operations requiring indexed terms must raise it instead of treating that state as a successful non-empty index.
- `IndexingError` represents an indexing operation that cannot be completed; the failed operation must not publish a partial commit.
- `whoosh.fields.FieldConfigurationError` is raised when a schema definition has an unsupported field specification or invalid field name.
- `whoosh.fields.UnknownFieldError` is raised when `add_document` receives a non-special field keyword absent from the schema.
- `whoosh.searching.NoTermsException` is raised when `Results.matched_terms()` or `Hit.matched_terms()` is called for a search that did not use `terms=True`.

## Cross-View Invariants

- A successful `commit()` must make an added document visible through `open_dir(...).searcher()` for the same directory and index name.
- `exists_in()` must return `True` after a successful committed `create_in` workflow and must return `False` for a directory/name without a valid index.
- A `TEXT(stored=True)` value must be searchable through a query and must be returned from the corresponding search hit.
- An `ID(unique=True)` value used by `update_document` must identify the committed document that is absent from subsequent results after replacement.
- `cancel()` must return subsequent searches to the document set visible before the writer staged its changes.
- A committed deletion must make the deleted document absent from a new searcher and must make the new `doc_count()` exclude that document.

## Representative Workflow

```python
from whoosh import index
from whoosh.fields import ID, TEXT, Schema
from whoosh.qparser import QueryParser

schema = Schema(path=ID(stored=True, unique=True), content=TEXT(stored=True))
ix = index.create_in("indexdir", schema)

with ix.writer() as writer:
    writer.add_document(path="/a", content="A first document")
    writer.add_document(path="/b", content="Another document")

with ix.searcher() as searcher:
    query = QueryParser("content", ix.schema).parse("first")
    results = searcher.search(query, limit=None)
    assert len(results) == 1
    assert results[0]["path"] == "/a"
```

The successful context exit must make both documents persistent in `indexdir`; searching for a term absent from both documents must return an empty result set. If the directory is unwritable or the writer cannot obtain its lock, the relevant operation must raise its filesystem error or `LockError` and must not publish a new document.

## Non-Goals

This specification does not define codec formats, reader/posting implementations, file names, segment-merging algorithms, relevance ranking details, low-level document-number behavior, multiprocessing writers, thread scheduling, custom parser plug-in internals, facets, highlighting, spelling, or language-analysis internals.
