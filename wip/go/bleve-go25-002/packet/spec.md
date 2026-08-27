# Bleve Specification

> **Specification Authority**: This document defines the supported behavior and public interface for this module version.

# Context

## Product Overview

`bleve` is a Go full-text indexing library that maps caller documents into a searchable local index. A committed index generation is projected through document counts, stored documents, field names, term dictionaries, ranked search hits, facets, highlights, aliases, and a local inspection command.

The scoped system supports in-memory indexes and durable indexes rooted in caller-owned directories. Mapping and analysis choices determine indexed terms, stored fields, and sortable or facetable values. Batch publication, deletion, close and reopen, and alias routing preserve agreement across those views.

## Non-Goals

- This specification does not require vector search, GPU acceleration, FAISS integration, remote indexes, or network transports.
- This specification does not define private segment encodings, merge scheduling, file names, or byte-for-byte index directory identity.
- This specification does not require analyzers, tokenizers, or field types beyond the text, keyword, numeric, date-time, and Boolean behaviors described here.
- This specification does not define scoring equality across semantically equivalent query-planning implementations; hit membership, ordering rules, fields, facets, and lifecycle behavior remain contractual.

# Orientation

## Concepts and Terms

A **mapping** assigns document properties to field mappings and analysis rules. An **indexed document** is the fact associated with one caller-supplied identifier. A **committed generation** is the complete logical index after one successful `Index`, `Delete`, or `Batch` publication. A **term dictionary** is the ordered public enumeration of analyzed terms for one field. An **alias** is a live routing view over one or more indexes. A **fresh observation** is made through a new search request, dictionary iterator, alias visit, command process, or reopened index handle.

## Representative Workflows

### Workflow 1: Map, index, and search local documents

1. Create an index mapping and add text, keyword, numeric, date-time, or Boolean field mappings to a document mapping.
2. Create an in-memory index or a durable index in a new directory.
3. Index several caller-owned Go values under distinct document identifiers, then publish replacements and deletions through a batch.
4. Build term, match, phrase, prefix, range, conjunction, or disjunction queries and execute new search requests.
5. Compare hit identifiers, stored fields, facets, field names, and term dictionaries from the same committed generation.
6. Build an `ObservationPlan`, capture an `IndexReceipt`, and validate that the normalized receipt reconciles all requested projections.

The mapping, metadata, and search projections must agree on field ownership and the last successful document generation.

### Workflow 2: Close, reopen, and inspect a durable index

1. Create a durable index with a caller-selected mapping and publish multiple batches.
2. Close the index, open the same directory through `Open`, and issue fresh count, dictionary, and search observations.
3. Build the local `bleve` command from the delivered source and run `count`, `fields`, `dictionary`, `mapping`, `check`, and `query` against the closed index directory.
4. Open the index again and publish a later replacement or deletion.
5. Confirm that new library and command observations expose the later generation without duplicate or resurrected documents.
6. Capture receipts before and after reopen and require storage-independent semantic equivalence for the unchanged generation.

# Behavior

## Domain 1: Mapping and Index Publication

This domain defines how mappings turn caller documents into atomically published index generations.

**Mapping construction.** When `NewIndexMapping` creates a mapping, the mapping must accept document mappings selected by type and a default document mapping. When a document mapping contains text, keyword, numeric, date-time, or Boolean field mappings, indexing must apply the selected field name, storage, indexing, analyzer, and doc-value choices to every matching value. If a mapping or synonym definition is invalid, then validation or index publication must return an error without publishing a partial document.

**Analysis lineage.** When a text field uses an analyzer, indexing and query analysis must derive compatible terms from the same analyzer selection. A keyword field must preserve its value as one searchable term. Numeric, date-time, and Boolean fields must remain addressable by their corresponding field-query or range-query families. If a query requests an invalid analyzer, date parser, field configuration, or malformed range, then request validation or search must return an error.

**Single-document publication.** When `Index` succeeds for a new identifier, `DocCount`, `Document`, field metadata, dictionaries, and later searches must observe the document. When `Index` succeeds for an existing identifier, the new mapped document must replace the prior generation without increasing the logical document count. When `Delete` succeeds, every fresh projection must omit that identifier and its now-unreferenced term contributions. If indexing or deletion returns an error, then every fresh projection must retain the preceding generation.

**Batch publication.** When a `Batch` contains indexes, replacements, deletes, and internal ordering conflicts for the same identifier, its final operation for each identifier must define the published logical document. `Batch` must publish all successful document changes as one caller-visible generation. `Reset` must empty the batch without changing the index, and `Merge` must combine pending operations while retaining the receiving batch's documented final-operation ownership. If batch publication fails, then no subset of its document changes must become visible.

## Domain 2: Query and Search Projections

This domain defines how one committed index generation appears through query, hit, facet, highlight, and dictionary views.

**Query families.** When a term query selects a field, it must match documents containing that analyzed term in the selected field. Match and phrase queries must apply their query-time analyzer and field selection. Prefix, wildcard, regular-expression, numeric-range, date-range, term-range, document-ID, conjunction, disjunction, match-all, and match-none queries must apply their documented boundary and Boolean composition rules. If query construction accepts open range endpoints, then the missing endpoint must leave that side unbounded; explicit inclusivity flags must own endpoint inclusion.

**Search requests.** When `NewSearchRequest` or `NewSearchRequestOptions` wraps a query, `Size`, `From`, field selection, sorting, facets, and highlighting must shape only the result projection, not the stored index. Search hits must use stable document identifiers, report requested stored fields, and obey the requested ordering. If pagination, sort, facet, highlight, or query options are invalid, then `Validate` or `Search` must return an error without changing index state.

**Facets and highlights.** When a facet request targets a facetable field, term buckets or named numeric/date ranges must count the same matching document set as the enclosing search. Prefix or regular-expression facet filters must restrict term buckets without changing hits. When highlighting targets a stored text field, fragments must come from the selected hit's indexed text and requested style. If the field lacks the required stored, indexed, or doc-value capability, then the request must return an error or an empty projection according to the public request contract, while the index remains unchanged.

**Fields and dictionaries.** `Fields` must enumerate fields represented by the committed index. `FieldDict`, `FieldDictPrefix`, and `FieldDictRange` must return ordered term entries with frequencies derived from live documents. Dictionary iteration must end normally and `Close` must release the iterator. Replacing or deleting a document must adjust frequencies and must remove a term when no live document contributes it. If a requested dictionary field is absent, then iteration must return an empty result or a documented error without changing state.

## Domain 3: Persistence, Aliases, and Inspection

This domain defines durable reopen behavior, alias routing, and agreement between library and local command projections.

**Lifecycle and reopen.** When `New` succeeds, the directory must contain an open durable index using the supplied mapping. When `Close` completes, later operations on that handle must return an error, and `Open` on the same valid directory must expose the last successful committed generation and mapping. If an index directory is missing, malformed, incompatible, or already unusable, then `Open` must return an error without creating an unrelated valid index in its place.

**Alias routing.** When `NewIndexAlias` receives indexes, searches, counts, fields, and dictionaries must aggregate its current members. `Add`, `Remove`, and `Swap` must change later alias routing without mutating the member indexes. An alias containing one writable index must route document writes to that index. If a write is ambiguous across multiple members or a member returns an error, then the alias must return an error and must not claim a complete aggregate publication.

**Local inspection command.** When the candidate-built `bleve` command receives a valid local index directory, `count`, `fields`, `dictionary`, `mapping`, `check`, and `query` must project the same logical state as fresh library calls. `query` must accept its documented query input and return matching identifiers and requested fields. If the directory, field, query, or command arguments are invalid, then the process must exit nonzero and must not modify the index.

## Domain 4: Observation Plans and Index Receipts

This domain defines a product-specific coordination API that captures several Bleve projections as one normalized, read-only generation receipt.

**Plan construction.** `NewObservationPlan` must return an empty plan. `ObservationPlan.AddDocument(name, id)` must select a document identifier, `AddSearch(name, request)` must associate a unique caller name with a `SearchRequest`, and `AddDictionary(name, field, start, end)` must associate a unique caller name with a field plus optional start and end term bounds. `IncludeMapping()` must select mapping projection, and `Names()` must return caller names in stable plan order. Repeating a caller name must replace the earlier plan entry without changing its original plan position. If a name or identifier is empty, a request is nil, a dictionary field is empty, or dictionary bounds are invalid, then the plan method must return an error and retain the preceding plan.

**Atomic capture.** `CaptureIndex` must accept an `Index` and an `ObservationPlan`, execute every selected document, search, dictionary, field, count, and mapping observation against one stable logical generation, and return an `IndexReceipt`. Capture must never publish index changes. If any selected projection fails or the index changes before a coherent receipt is formed, then capture must return an error and no partial receipt.

**Normalized receipt.** An `IndexReceipt` must preserve plan order, normalize field and dictionary term order, retain search hit order after the request's sort rules, and record semantic mapping content without private storage bytes. `Count()`, `Fields()`, and `Names()` expose the global facts and plan order. Named projections are read through `DocumentFields`, `SearchIDs`, `SearchTotal`, `SearchFields`, `SearchFragments`, `FacetTerms`, and `Dictionary`; `MappingJSON()` returns an isolated copy when mapping was selected. Every slice, map, and byte result must be caller-owned. `Digest` must derive from normalized public facts, so memory, durable, reopened, internally consolidated, and single-member alias views with equal semantics return the same digest. `Validate` must return an error when count, document, search, facet, dictionary, field, or mapping facts contradict each other under the plan.

**Receipt comparison.** `Equivalent` must compare normalized semantic facts rather than elapsed time, private statistics, index paths, or segment identity. When two receipts use different plans, `Equivalent` must return false. When a failed write leaves the prior index generation intact, a new capture under the same plan must remain equivalent to the preceding receipt.

# Contract

## State Model

An index begins as **new and empty** with a fixed mapping. Successful single-document or batch publication moves it to a new **open committed** generation. Successful deletion moves it to another committed generation with the identifier absent. `Close` moves the handle to **closed** while preserving durable state. `Open` creates a new open handle over the last durable generation. A failed mapping, indexing, batch, search, alias, or open operation leaves every valid index on its preceding generation.

A batch has **collecting**, **published**, and **reset** states independent of index state. An alias has a current member set independent of every member's durable generation. Search requests, results, facets, highlights, and dictionaries are observations and never become a second state store.

## Error Semantics

| Condition | Required result |
|---|---|
| Invalid mapping, analyzer, synonym, or field configuration | Validation or publication must return an error and retain the preceding generation. |
| Failed single-document or batch publication | The index must return an error without exposing a partial document set. |
| Invalid query, range, pagination, sort, facet, or highlight request | Validation or search must return an error without changing the index. |
| Operation on a closed index handle | The operation must return an error and durable state must remain reopenable. |
| Missing, malformed, or incompatible index directory | `Open` must return an error without replacing the directory with a new logical index. |
| Ambiguous alias write or member failure | The alias must return an error and must not report aggregate success. |
| Invalid local command input | The command must exit nonzero and leave the index directory unchanged. |

## Cross-View Invariants

1. `DocCount`, `Document`, search hits, fields, and dictionaries must describe the same committed live-document generation.
2. A field mapping's analysis and storage choices must agree across query matching, stored hit fields, highlighting, facets, and dictionary terms.
3. Replacing or deleting a document must update counts, hits, facet totals, and dictionary frequencies without retaining a second visible document generation.
4. A batch's successful publication must become visible atomically through fresh point, metadata, search, and reopened observations.
5. A durable index before close and the same index after reopen must preserve mapping, document identifiers, stored fields, live terms, and query membership.
6. An alias's count, search, fields, and dictionaries must aggregate the same current member set while member indexes retain independent state.
7. Local command count, field, dictionary, mapping, check, and query projections must agree with fresh public library observations of the same closed directory.
8. Any failed mapping, publication, query, alias, reopen, or inspection operation must leave all valid state projections on the preceding committed generation.
9. An `IndexReceipt` must reconcile every selected document, search, facet, dictionary, field, and mapping fact, and equal semantic generations must produce equal receipt digests across storage forms.

# Reference

## Public Interface

### Import Surface

- `github.com/blevesearch/bleve/v2`: `Index`, `Batch`, `IndexAlias`, `New`, `NewMemOnly`, `NewUsing`, `Open`, `OpenUsing`, `NewIndexAlias`, `NewIndexMapping`, `NewDocumentMapping`, `NewDocumentStaticMapping`, `NewDocumentDisabledMapping`, `NewTextFieldMapping`, `NewKeywordFieldMapping`, `NewNumericFieldMapping`, `NewDateTimeFieldMapping`, `NewBooleanFieldMapping`, `NewTermQuery`, `NewMatchQuery`, `NewMatchPhraseQuery`, `NewPhraseQuery`, `NewPrefixQuery`, `NewWildcardQuery`, `NewRegexpQuery`, `NewNumericRangeQuery`, `NewNumericRangeInclusiveQuery`, `NewDateRangeQuery`, `NewDateRangeInclusiveQuery`, `NewTermRangeQuery`, `NewTermRangeInclusiveQuery`, `NewDocIDQuery`, `NewConjunctionQuery`, `NewDisjunctionQuery`, `NewMatchAllQuery`, `NewMatchNoneQuery`, `NewQueryStringQuery`, `SearchRequest`, `SearchResult`, `FacetRequest`, `HighlightRequest`, `IndexStat`, `Error`, `ObservationPlan`, `NewObservationPlan`, `IndexReceipt`, `CaptureIndex`
- `github.com/blevesearch/bleve/v2/mapping`: `IndexMapping`, `IndexMappingImpl`, `DocumentMapping`, `FieldMapping`
- `github.com/blevesearch/bleve/v2/search/query`: `Query` and concrete query values returned by root-package constructors
- `github.com/blevesearch/bleve/v2/search`: `DocumentMatch`, `FacetResult`
- `github.com/blevesearch/bleve_index_api`: `Document`, `FieldDict`, `DictEntry`

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Index` | interface | Owns one open searchable index generation and its lifecycle. |
| `New`, `NewMemOnly`, `NewUsing`, `Open`, `OpenUsing` | functions | Create or open local index handles. |
| `Batch` | type | Collects document indexes, replacements, deletes, and batch metadata for one publication. |
| `IndexAlias`, `NewIndexAlias` | interface and function | Present a live aggregate routing view over member indexes. |
| `NewIndexMapping` | function | Creates a configurable index mapping. |
| `NewDocumentMapping`, `NewDocumentStaticMapping`, `NewDocumentDisabledMapping` | functions | Create document mapping policies. |
| `NewTextFieldMapping`, `NewKeywordFieldMapping`, `NewNumericFieldMapping`, `NewDateTimeFieldMapping`, `NewBooleanFieldMapping` | functions | Create supported field mapping policies. |
| `IndexMapping`, `IndexMappingImpl` | interface and type | Define type selection, default mapping, analysis, and document mapping behavior. |
| `DocumentMapping`, `FieldMapping` | types | Describe document-property and field-level indexing behavior. |
| Query constructors | functions | Create term, match, phrase, prefix, wildcard, regular-expression, range, identifier, and Boolean queries. |
| `query.Query` | interface | Supplies a validated query to a search request. |
| `SearchRequest`, `NewSearchRequest`, `NewSearchRequestOptions` | type and functions | Define query execution, pagination, fields, sorting, facets, and highlighting. |
| `SearchResult` | type | Reports status, totals, ranked hits, facets, and timing information. |
| `FacetRequest`, `NewFacetRequest` | type and function | Define term or named range aggregation for one field. |
| `HighlightRequest`, `NewHighlight`, `NewHighlightWithStyle` | type and functions | Select stored fields and styles for hit fragments. |
| `search.DocumentMatch`, `search.FacetResult` | types | Represent public hit and facet projections. |
| `bleve_index_api.Document`, `bleve_index_api.FieldDict`, `bleve_index_api.DictEntry` | interfaces and type | Expose stored documents and ordered field-term enumeration. |
| `IndexStat` | type | Reports public index statistics. |
| `Error` | error type | Represents package-defined index errors. |
| `ObservationPlan`, `NewObservationPlan` | type and function | Select named document, search, dictionary, and mapping projections for one capture; `AddDocument`, `AddSearch`, `AddDictionary`, `IncludeMapping`, and `Names` form its public planning surface. |
| `CaptureIndex` | function | Captures a read-only stable logical generation under an observation plan. |
| `IndexReceipt` | type | Normalizes captured facts and exposes `Count`, `Fields`, `Names`, `DocumentFields`, `SearchIDs`, `SearchTotal`, `SearchFields`, `SearchFragments`, `FacetTerms`, `Dictionary`, `MappingJSON`, `Digest`, `Validate`, and `Equivalent`. |

The fully qualified method surface is `ObservationPlan.AddDocument`, `ObservationPlan.AddSearch`, `ObservationPlan.AddDictionary`, `ObservationPlan.IncludeMapping`, `ObservationPlan.Names`, `IndexReceipt.Count`, `IndexReceipt.Fields`, `IndexReceipt.Names`, `IndexReceipt.DocumentFields`, `IndexReceipt.SearchIDs`, `IndexReceipt.SearchTotal`, `IndexReceipt.SearchFields`, `IndexReceipt.SearchFragments`, `IndexReceipt.FacetTerms`, `IndexReceipt.Dictionary`, `IndexReceipt.MappingJSON`, `IndexReceipt.Digest`, `IndexReceipt.Validate`, and `IndexReceipt.Equivalent`.

### CLI Entry Points

The `bleve` command is built from the delivered source. Its scoped subcommands are `count`, `fields`, `dictionary`, `mapping`, `check`, and `query`.

| Outcome | Exit behavior |
|---|---|
| Valid command over a readable local index | The process must exit with status zero after writing its documented projection. |
| Invalid arguments, unreadable index, invalid field, or invalid query | The process must exit nonzero and leave the index unchanged. |

# Meta

## Appendix A: Environment

The working environment runs the pinned Go toolchain on Linux amd64 without network access. The complete allowed module closure is preloaded in a read-only module cache, and `CGO_ENABLED=0` is set. Each run receives a new temporary directory for indexes, command output, `HOME`, and Go build caches. The project must retain the module path `github.com/blevesearch/bleve/v2` and build with the supplied dependency closure.

## Appendix B: Compatibility Notes

The supported behavior covers mapping families, analyzer choices, document replacement, deletion, batch conflicts, query families, range boundaries, search options, stored fields, facets, highlights, dictionaries, alias membership, close/reopen cycles, and local command agreement. Compatibility is defined by semantic index behavior and caller-visible state; private segment bytes, background scheduling, exact timing strings, and the order of equally ranked hits without an explicit secondary sort have no contractual meaning.
