# Whoosh Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

Whoosh is a pure-Python library for building a full-text index over documents and searching that index through a Python API. A schema defines the document fields; a writer stages changes; committing publishes a new searchable index; a searcher returns stored document data for matching documents.

## Non-Goals

This specification does not define codec formats, reader/posting implementations, file names, segment-merging algorithms, relevance ranking details, low-level document-number behavior, multiprocessing writers, thread scheduling, custom parser plug-in internals, facets, highlighting, spelling, or language-analysis internals.

## Representative Workflows

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

## Schemas and Field Types

Schema objects define the permitted document fields and control how each field value is indexed, stored, and searched.

**Schema construction.** `Schema` must accept keyword arguments mapping field names to field type instances or supported bare built-in field classes. When no constructor options are required, a bare field class must be instantiated automatically as a field definition. A field definition that is neither a supported field instance nor a supported bare field class must raise `FieldConfigurationError`. A field name beginning with `_`, containing spaces, or duplicating an existing schema field must raise `FieldConfigurationError` rather than create an invalid schema. `Schema.names()` must return the set of all defined field names in the schema.

**TEXT.** `TEXT` must index body text by splitting it into individual words and recording positions for phrase searching. Each word of the supplied text must be independently searchable as a separate indexed term. `TEXT(stored=True)` must return the supplied text in result stored fields. A query for a term absent from any document's indexed text must return no hit.

**ID.** `ID` must index an entire value as a single term, including values that contain spaces. `ID(stored=True)` must return the supplied value in result stored fields. A `Term` query must match only the complete indexed value; a partial prefix or individual word from the value must not match.

**KEYWORD.** `KEYWORD` must index keywords separated by spaces by default, preserving the original case of each keyword. When `commas=True` is set, the field must split on commas instead of spaces, keeping multi-word terms intact as single indexable terms. When `lowercase=True` is set, the field must index lowercased keywords. A token absent after the configured splitting and normalization must return no hit.

**STORED.** `STORED` must return its supplied value in matching hits and must not make that value searchable. A `Term` query against a stored-only field must return no hit.

**NUMERIC, DATETIME, and BOOLEAN.** `NUMERIC` must accept numeric values including negative numbers and zero, and `NUMERIC(stored=True)` must preserve the exact supplied numeric value in result stored fields, including negative values and zero. `DATETIME` must accept `datetime` values, and `DATETIME(stored=True)` must return the supplied `datetime` object in result stored fields. `BOOLEAN` must accept boolean values, and `BOOLEAN(stored=True)` must preserve the exact supplied boolean value in result stored fields, including `False`. A supplied value that the chosen field type cannot process must raise an exception before commit; the writer must not publish that failed write.

**Document field omission.** A document is allowed to omit schema fields. When a document omits a stored field, the hit's stored-field mapping returned by `Hit.fields()` must contain only the fields that were actually supplied to the document.

## Creating and Opening Indexes

Index lifecycle operations create, open, and verify indexes in filesystem directories.

**Creating an index.** `create_in(dirname, schema, indexname=None)` must create an index using the supplied schema in the named directory. Calling it for an existing index name must clear that index's current contents before the new index is used. If the directory cannot be created or written, the operation must raise the underlying filesystem error and must not report a usable new index. The default index name is used when `indexname` is omitted.

**Opening and verifying.** `open_dir(dirname, indexname=None, readonly=False, schema=None)` must open the named index from that directory. `exists_in(dirname, indexname=None)` must return `True` only when the requested directory and name contain a valid index, and must return `False` when no valid index is present. Opening an index whose format is incompatible with the installed library must raise `IndexVersionError`.

**Named indexes.** Multiple named indexes in one directory must remain independently openable by their respective names. Opening a missing named index must not expose documents from another index name.

**Index metadata.** An `Index` must expose its `schema` property for query parsing and field introspection. `Index.doc_count()` must return the number of non-deleted documents in the committed index state.

## Writing Documents

The `IndexWriter` manages document additions, updates, and deletions as a transaction.

**Writer creation and locking.** `Index.writer(**kwargs)` must return an `IndexWriter`. The writer is a transaction-like context manager: normal context exit must commit staged changes, while context exit caused by an exception must cancel staged changes. A second writer request while an existing writer holds the write lock must raise `LockError` instead of allowing concurrent writes.

**Adding documents.** `add_document(**fields)` must stage one document. Field keyword names map to schema fields, and documents are allowed to omit optional fields. `add_document` must preserve duplicate documents without enforcing uniqueness. A field name absent from the schema must raise `UnknownFieldError`, and a field value that cannot be processed must raise an exception before commit, with neither failure publishing that write.

**Stored value override.** For a field that is both indexed and stored, `add_document(field=value, _stored_field=stored_value)` must index `value` and must expose `stored_value` in the resulting hit. The optional `_boost` and `_<fieldname>_boost` inputs affect relevance ranking only and must not alter the stored field value.

**Updating documents.** `update_document(**fields)` must delete committed documents matching values in all supplied fields marked `unique=True` and then stage the replacement document. When no supplied field is unique, or no committed document matches, it must stage an additional document; it must not enforce global uniqueness for `add_document`.

**Deleting documents.** `delete_by_term(fieldname, termtext)` and `delete_by_query(query)` must stage deletion of matching documents and return the number staged for deletion. A deletion request against a query with no matches must return zero and must leave committed search results unchanged.

**Commit and cancel.** `commit()` must publish staged additions and deletions and release the write lock. `cancel()` must discard staged additions and deletions and release the write lock.

## Queries and Parsing

Query objects and parsers construct the search conditions used to find matching documents.

**Term queries.** `Term(fieldname, text)` must construct a query for a term in one field. `And(queries)` must match only documents matching every contained query, while `Or(queries)` must match documents matching at least one contained query. A query whose terms match no indexed documents must return an empty `Results` value rather than inventing a hit.

**QueryParser.** `QueryParser(fieldname, schema, ...)` must parse user query text using the supplied default field and schema. Unfielded terms must be assigned to the configured default field. A parser created with `schema=None` must return a query structure without applying schema text analysis. `parse(text)` must return a query object for valid text and must return the parser's error query outcome for invalid syntax rather than committing or mutating the index.

**Multi-field and alternative parsers.** `MultifieldParser(fieldnames, schema, ...)` must apply unfielded terms across its configured field names. `SimpleParser` and `DisMaxParser` must return their documented preconfigured parser variants. An empty or non-matching query must return a query whose search result is empty rather than returning all documents.

## Searching and Results

Searchers execute queries against the committed index state and return ranked result collections.

**Searcher creation.** `Index.searcher(**kwargs)` must return a `Searcher` over the committed index state and must support context-manager use.

**Search execution.** `Searcher.search(query, limit=..., filter=..., mask=..., terms=...)` must return a `Results` object. A positive `limit` must limit the ranked result set, while `limit=None` must request all matching documents. A non-matching query must return `Results` with length zero.

**Filtering and masking.** When `filter` is supplied, results must contain only documents permitted by the filter. When `mask` is supplied, results must omit documents excluded by the mask. A filter or mask that excludes every match must return an empty result set rather than raising for the absence of hits.

**Results and hits.** `Results` must act as a sequence of matching `Hit` values. Each `Hit` must provide dictionary-like access to its stored field values, and `Hit.fields()` must return that hit's stored-field mapping. `len(results)` must return the total number of matching documents, and `results.scored_length()` must return the number of ranked hits retained in the result object. Accessing a hit index outside the retained hit range must raise `IndexError` rather than return an unrelated document.

**Matched terms.** When `terms=True` is passed to `search`, `Results.has_matched_terms()` must report that matched-term data is available, and `Results.matched_terms()` and `Hit.matched_terms()` must return the recorded matching terms. Calling either matched-term method when the search did not use `terms=True` must raise `NoTermsException` rather than fabricate term data.

## State Model

A Whoosh index has three public projections of the same committed document state:

1. The schema projection names each permitted field and describes whether the field is indexed, stored, or both.
2. The directory projection holds an index that `exists_in()` can recognize and that `open_dir()` can reopen by its index name.
3. The search projection exposes committed, non-deleted documents as matches and exposes the stored values of each hit.

The following state rules apply:

- A document added through an `IndexWriter` must not appear in a newly opened searcher until that writer commits; cancelling the writer must return the index to its previously committed search projection.
- A successful commit must make its document changes visible through a newly opened searcher and through an index reopened from the same directory; an existing searcher must continue to expose the generation it already opened.
- A deletion committed through a writer must remove the matching document from subsequent search results; cancellation must return the pre-existing committed document to subsequent search results.
- `Index.doc_count()` must reflect the current committed document count, excluding deleted documents.
- A value supplied as `_stored_<fieldname>` for a field that is both indexed and stored must be searchable through the indexed value and must be returned through the stored value; an unknown document field name must raise `whoosh.fields.UnknownFieldError` instead of creating an untracked field.
- An index created with an `indexname` must be reopened and checked with that same name; checking a directory or name without a valid index must return `False` from `exists_in`.
- `update_document` on a committed document with matching values in a schema field marked `unique=True` must replace the prior matching document in subsequent searches; when no committed document matches, it must add the new document instead.

## Error Semantics

- `LockError` is raised when a writer cannot obtain the index write lock.
- `IndexVersionError` is raised when an index format cannot be read by this library version.
- `EmptyIndexError` represents an index without indexed terms; operations requiring indexed terms must raise it instead of treating that state as a successful non-empty index.
- `IndexingError` represents an indexing operation that cannot be completed; the failed operation must not publish a partial commit.
- `whoosh.fields.FieldConfigurationError` is raised when a schema definition has an unsupported field specification or invalid field name.
- `whoosh.fields.UnknownFieldError` is raised when `add_document` receives a non-special field keyword absent from the schema.
- `whoosh.searching.NoTermsException` is raised when `Results.matched_terms()` or `Hit.matched_terms()` is called for a search that did not use `terms=True`.

## Cross-View Invariants

1. A successful `commit()` must make an added document visible through `open_dir(...).searcher()` for the same directory and index name.
2. `exists_in()` must return `True` after a successful committed `create_in` workflow and must return `False` for a directory/name without a valid index.
3. A `TEXT(stored=True)` value must be searchable through a query and must be returned from the corresponding search hit.
4. An `ID(unique=True)` value used by `update_document` must identify the committed document that is absent from subsequent results after replacement.
5. `cancel()` must return subsequent searches to the document set visible before the writer staged its changes.
6. A committed deletion must make the deleted document absent from a new searcher and must make the new `doc_count()` exclude that document.
7. An existing searcher must continue to expose its opened generation even after a new writer commits additional documents to the same index.
8. A `_stored_<fieldname>` override for a field that is both indexed and stored must make the document discoverable through the indexed value and must return the stored override value through the hit's stored-field mapping.

## Public Interface

### Import Surface

Applications import the covered public interfaces from these paths:

```python
from whoosh.fields import (
    Schema, TEXT, ID, KEYWORD, STORED,
    NUMERIC, DATETIME, BOOLEAN,
    FieldConfigurationError, UnknownFieldError,
)
from whoosh.index import (
    create_in, open_dir, exists_in,
    Index, LockError, IndexError, IndexVersionError, EmptyIndexError,
)
from whoosh.qparser import QueryParser, MultifieldParser, SimpleParser, DisMaxParser
from whoosh.query import Term, And, Or
from whoosh.searching import Searcher, Results, Hit, NoTermsException
from whoosh.writing import IndexWriter, IndexingError
```

### API Catalog

| Name | Kind | Role |
|------|------|------|
| Schema | class | Map field names to field type definitions |
| TEXT | field type | Index body text with optional phrase positions |
| ID | field type | Index an entire value as one term |
| KEYWORD | field type | Index space- or comma-separated keywords |
| STORED | field type | Store a value without making it searchable |
| NUMERIC | field type | Index numeric values |
| DATETIME | field type | Index datetime values |
| BOOLEAN | field type | Index boolean values |
| FieldConfigurationError | exception | Raised for invalid schema field definitions |
| UnknownFieldError | exception | Raised when a document uses an unknown field |
| create_in | function | Create a new index in a directory |
| open_dir | function | Open an existing index from a directory |
| exists_in | function | Report whether a valid index exists in a directory |
| Index | class | Index handle for writers and searchers |
| LockError | exception | Raised when a writer cannot obtain the write lock |
| IndexError | exception | Base index error |
| IndexVersionError | exception | Raised for incompatible index formats |
| EmptyIndexError | exception | Raised when indexed terms are required but absent |
| IndexWriter | class | Transaction-like writer for document changes |
| IndexingError | exception | Raised when an indexing operation cannot complete |
| Term | class | Query one indexed term in one field |
| And | class | Query requiring all contained queries to match |
| Or | class | Query requiring at least one contained query to match |
| QueryParser | class | Parse user query text for one default field |
| MultifieldParser | class | Parse unfielded terms across multiple fields |
| SimpleParser | class | Preconfigured simple query parser |
| DisMaxParser | class | Preconfigured disjunction-max query parser |
| Searcher | class | Search committed index state |
| Results | class | Ranked search result collection |
| Hit | class | One matching document with stored-field access |
| NoTermsException | exception | Raised when matched-term data was not requested |

### CLI Entry Points

There is no console script for this package. `python -m whoosh` is not supported. Programmatic use is through Python imports.


## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Appendix B: Assessment Notes

Assessment observes only the public behavior described in this specification: schema definition, index creation and reopening, writer transactions, document updates and deletions, query construction and parsing, search results and stored fields, and the documented error classes. Each checked behavior is observed through public imports, returned values, stored-field mappings, and raised exception classes. Private modules, private attributes, on-disk file layouts, exact `repr` output, exact exception wording, and relevance-ranking internals are not examined.
