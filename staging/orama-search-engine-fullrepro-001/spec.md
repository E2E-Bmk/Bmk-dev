# Orama Search Engine Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`@orama/orama` is an in-memory full-text search engine for JavaScript and TypeScript that stores typed documents and answers structured queries over them. A caller creates a search instance from a schema, inserts documents, and then reads the same document set through several projections: ranked full-text hits, a document count, direct lookup by id, faceted aggregations, grouped results, sorted and deduplicated result lists, and a serializable snapshot that restores the instance state elsewhere.

The engine indexes each schema property according to its declared type. String properties feed a tokenized full-text index with prefix matching, typo tolerance, boosting, and relevance scores. Number, boolean, and enum properties feed filter indexes evaluated by `where` clauses. All projections observe one shared store, so an insertion, update, or removal is visible everywhere at once.

## Non-Goals

- This specification does not require vector search, hybrid search, embeddings, or similarity APIs.
- This specification does not require the answer-session / conversational API, result pinning rules, or the plugin system.
- This specification does not require custom component overrides, custom tokenizers, stemming, stop-word lists, or languages other than the default English tokenization.
- This specification does not require geosearch or the `geopoint` schema type.
- This specification does not define exact relevance score numbers, exact human-readable error message text, or the internal layout of the serialized snapshot.
- This specification does not require a command-line program.

## Representative Workflows

### Index Documents And Search

```ts
import { create, insertMultiple, search } from '@orama/orama'

const movies = create({
  schema: { title: 'string', year: 'number', isAvailable: 'boolean' },
})

await insertMultiple(movies, [
  { id: 'm1', title: 'The silent storm', year: 1998, isAvailable: true },
  { id: 'm2', title: 'Storm warning signs', year: 2004, isAvailable: false },
])

const result = await search(movies, { term: 'storm', where: { isAvailable: true } })
// result.count === 1, result.hits[0].id === 'm1'
```

The search tokenizes the term, matches it against indexed string properties, applies the boolean filter, and returns ranked hits together with the matched count.

### Aggregate, Persist, And Restore

```ts
import { create, insertMultiple, search, save, load, count } from '@orama/orama'

const shop = create({ schema: { name: 'string', price: 'number', section: 'enum' } })
await insertMultiple(shop, [
  { name: 'walnut desk', price: 320, section: 'furniture' },
  { name: 'oak shelf', price: 120, section: 'furniture' },
  { name: 'desk lamp', price: 45, section: 'lighting' },
])

const faceted = await search(shop, { term: 'desk', facets: { section: {} } })
// faceted.facets.section.values === { furniture: 1, lighting: 1 }

const snapshot = save(shop)
const restored = create({ schema: { name: 'string', price: 'number', section: 'enum' } })
load(restored, snapshot)
// count(restored) === 3 and searches behave identically
```

Facets aggregate over the matched documents, and a saved snapshot restores the full observable state into a fresh instance built from the same schema.

## Instance Creation And Schema

Creating an instance fixes the shape of the documents it indexes and how each property participates in queries.

**Creation.** `create` accepts an options object whose `schema` property declares the indexed properties. `create` returns a new empty instance. WHEN `create` is called with a valid schema, the instance must start with a document count of zero and empty results for every query.

**Schema types.** Each schema entry maps a property name to one of the type strings `'string'`, `'number'`, `'boolean'`, `'enum'`, `'string[]'`, `'number[]'`, `'boolean[]'`, or `'enum[]'`, or to a nested object of further entries. A nested entry is addressed everywhere else with a dot-separated path (for example `meta.rating`). String properties participate in full-text search; number, boolean, and enum properties participate in `where` filtering, faceting, sorting, and grouping as described in their sections. Array types index each element with the semantics of their element type. IF a schema entry uses an unknown type string, THEN `create` must throw an `Error` whose `code` property is `'INVALID_SCHEMA_TYPE'`.

**Awaitable results.** Every operation in this document either returns its result directly or returns a promise of it; callers must be able to `await` the return value of `insert`, `insertMultiple`, `update`, `updateMultiple`, `upsert`, `upsertMultiple`, `remove`, `removeMultiple`, `search`, `count`, and `getByID` and observe the documented result.

## Document Lifecycle

Documents enter, change, and leave the shared store through the lifecycle functions; every other projection reflects the outcome immediately.

**Insertion and ids.** `insert` adds one document and returns its id as a string. WHEN the document carries a string `id` property, the engine must use that value as the document id. WHEN the document has no `id` property, the engine must generate a unique string id and return it. `insertMultiple` accepts an array of documents and returns the array of assigned ids in the same order. IF a document is inserted with an `id` equal to an id already present, THEN the engine must throw an `Error` whose `code` property is `'DOCUMENT_ALREADY_EXISTS'`.

**Validation.** WHEN an inserted document carries a value whose type contradicts the schema entry for that property, the engine must reject the document by throwing an `Error` whose `code` property is `'SCHEMA_VALIDATION_FAILURE'`. Documents are allowed to omit schema properties, and they are allowed to carry additional properties outside the schema; omitted properties are simply absent from the corresponding indexes, and extra properties are stored verbatim but not indexed.

**Retrieval.** `count` returns the number of stored documents. `getByID` returns the stored document for an id, preserving all of its properties (including non-schema properties) verbatim. WHEN `getByID` is called with an id that is not present, it must return `undefined`.

**Removal.** `remove` deletes the document with the given id and returns `true`. WHEN `remove` is called with an id that is not present, it must return `false` and leave the store unchanged. `removeMultiple` accepts an array of ids, removes the present ones, and returns the number of documents it removed. A removed document must no longer be returned by `count`, `getByID`, `search`, facets, or groups.

**Update and upsert.** `update` replaces the document stored under an id with a new document and returns the id of the new document; the new document's own `id` property (or a generated id when absent) becomes the stored id, and the previous id must no longer resolve through `getByID` when it differs from the new one. `updateMultiple` performs the same replacement for parallel arrays of ids and documents and returns the array of new ids. `upsert` inserts the document when its `id` is not present and replaces the stored document when it is; in both cases it returns the document id, and replacing must not change the document count. `upsertMultiple` applies `upsert` across an array of documents and returns their ids.

## Full-Text Search

`search` evaluates a query object against the instance and returns one result object; the query properties below compose freely unless stated otherwise.

**Result shape.** The result object must expose: `hits`, an array of hit objects each carrying the document `id`, a numeric relevance `score`, and the stored `document`; `count`, the total number of matched documents before `limit`/`offset` slicing; and `elapsed`, an object with a numeric `raw` duration and a `formatted` string. Hits must be ordered by descending `score` unless `sortBy` or `groupBy` ordering applies. WHEN two searches with the same store state and query run, the matched id set must be identical.

**Term matching.** The `term` string is tokenized case-insensitively on non-alphanumeric boundaries. A document matches a token when any indexed string property contains a token that begins with the query token (prefix matching); a token equal to the indexed token also matches. WHEN `term` is omitted or empty, the search must match every stored document (subject to filters), and `count` must equal the number of documents passing the filters.

**Searched properties.** The `properties` query entry restricts full-text matching to the named string properties (dot paths allowed). WHEN `properties` is omitted or `'*'`, all string properties participate. IF `properties` names a property that is not an indexed string property, THEN `search` must throw an `Error` whose `code` property is `'UNKNOWN_INDEX'`.

**Exactness and tolerance.** WHERE `exact` is `true`, only whole-token matches count: prefix-only matches must be excluded, and `tolerance` must not apply. WHERE `exact` is not `true` and `tolerance` is a positive integer, a document token also matches when its edit distance from the query token is at most `tolerance`. WHEN `tolerance` is absent, a token with a spelling difference and no prefix relation must not match.

**Threshold.** The `threshold` number ranges over 0 to 1 and controls multi-token queries. WHERE `threshold` is `0`, only documents matching every query token must be returned. WHERE `threshold` is `1` (the default), documents matching any query token must be returned. Intermediate values must return all all-token matches plus that proportion of the remaining any-token matches.

**Boost.** The `boost` query entry maps property names to positive multipliers applied to the relevance contribution of matches found in that property. Boosting a property must be able to reorder hits whose matches come from different properties, and must not change which documents match.

**Paging and preflight.** `limit` (default 10) bounds the number of returned hits and `offset` (default 0) skips ranked hits before collecting them; `count` must remain the unsliced total. WHERE `preflight` is `true`, the result must report the matched `count` while `hits` is an empty array.

## Filters, Facets, Groups, And Sorting

Structured projections evaluate over the same matched set that full-text matching produces, and over all documents when no `term` is given.

**Where filters.** The `where` query entry is an object keyed by schema property paths. A number property accepts an operator object with `eq`, `gt`, `gte`, `lt`, `lte`, or `between` (a two-element inclusive array). A boolean property accepts `true` or `false` directly. An enum property accepts an operator object with `eq`, `in` (array of accepted values), or `nin` (array of rejected values). A string property accepts a string; the filter tokenizes it and matches documents whose value for that property contains a token equal to a filter token — prefix and tolerance expansion must not apply to `where` filters. A `string[]` property accepts a string and matches documents whose array contains a matching element. Multiple `where` entries must all hold (conjunction), and filters must combine with `term` so only documents satisfying both are returned. IF `where` names a property that is not in the schema, THEN `search` must throw an `Error` whose `code` property is `'UNKNOWN_FILTER_PROPERTY'`.

**Facets.** The `facets` query entry requests aggregations over the matched documents, keyed by property path. For string, boolean, and enum properties the facet result must expose `values`, an object mapping each distinct value (booleans as the strings `'true'`/`'false'`) to the number of matched documents carrying it, and `count`, the number of distinct values. For number properties the facet configuration must carry `ranges`, an array of `{ from, to }` objects; the result `values` must map each `"from-to"` key to the number of matched documents whose value lies in the inclusive range, and a document must be counted in every range that contains it. WHERE the faceted property is a string property, the optional `limit` (default 10), `offset` (default 0), and `sort` (`'ASC'` or `'DESC'` by bucket count, default `'DESC'`) facet options must order and slice the reported buckets; these three options apply only to string facets.

**Sorting.** The `sortBy` query entry either names a property with `{ property, order }` — `order` is `'ASC'` (default) or `'DESC'` — or supplies a comparator function receiving two `[id, score, document]` triples. Sorting by a number, string, or boolean property must order hits by that property's value. Sorted searches must still report the same matched `count` as the unsorted query.

**Grouping.** The `groupBy` query entry carries `properties` (an array of string, number, or boolean property names) and an optional `maxResult` bounding the hits kept per group. The result must expose `groups`, an array of `{ values, result }` objects, one per distinct combination of the grouped values among matched documents, where `values` is the combination and `result` lists that group's hits. IF `groupBy` names an enum property, THEN `search` must throw an `Error` whose `code` property is `'INVALID_GROUP_BY_PROPERTY'`.

**Distinct.** The `distinctOn` query entry names a property; the returned `hits` must keep only the first hit (in ranked or sorted order) for each distinct value of that property, while `count` still reports the number of matched documents before deduplication.

## Persistence

A snapshot carries the complete observable state of an instance between processes.

**Saving.** `save` returns a JSON-serializable snapshot value capturing the documents and indexes of the instance.

**Loading.** `load` accepts an instance created from the same schema and a snapshot, and installs the snapshot state into that instance. After loading, `count`, `getByID`, `search` (including filters, facets, groups, sorting, and paging), and further insertions and removals must behave exactly as they would on the original instance at the moment `save` was called.

## State Model

The core state is one document store plus per-property typed indexes derived from it; both always describe the same document set.

The public projections of this state are:

1. `count` — the size of the stored document set.
2. `getByID` — direct document lookup.
3. `search` hits with relevance scores, paging, and `elapsed` timing.
4. `facets` aggregations over matched documents.
5. `groups` partitions over matched documents.
6. Sorted (`sortBy`) and deduplicated (`distinctOn`) result orderings.
7. `save` snapshots that `load` replays into a fresh instance.

Every lifecycle operation (`insert`, `insertMultiple`, `update`, `updateMultiple`, `upsert`, `upsertMultiple`, `remove`, `removeMultiple`, `load`) must leave all projections mutually consistent.

## Error Semantics

| Condition | Required result |
|---|---|
| `create` receives a schema entry with an unknown type string | Throw an `Error` with `code === 'INVALID_SCHEMA_TYPE'` |
| Inserted document value contradicts the schema type for its property | Throw an `Error` with `code === 'SCHEMA_VALIDATION_FAILURE'` |
| Inserted document reuses an existing document id | Throw an `Error` with `code === 'DOCUMENT_ALREADY_EXISTS'` |
| `search` `properties` names a non-indexed property | Throw an `Error` with `code === 'UNKNOWN_INDEX'` |
| `where` names a property absent from the schema | Throw an `Error` with `code === 'UNKNOWN_FILTER_PROPERTY'` |
| `groupBy` names an enum property | Throw an `Error` with `code === 'INVALID_GROUP_BY_PROPERTY'` |
| `getByID` id not present | Return `undefined` |
| `remove` id not present | Return `false`; store unchanged |

Error message wording is unconstrained; the `code` property carries the contract.

## Cross-View Invariants

1. A document returned by `insert`/`insertMultiple` must be observable through `count`, `getByID`, term-less `search`, and matching facets and groups until it is removed.
2. After `remove` or `removeMultiple`, the removed ids must disappear from `count`, `getByID`, `search` hits, facet bucket counts, and groups simultaneously.
3. `search(...).count` must equal the number of ids the same query yields through `hits` when `limit` is large enough, and must remain that total under `limit`/`offset` slicing, `preflight`, and `distinctOn` deduplication.
4. For every hit, `hits[i].document` must deep-equal the document `getByID` returns for `hits[i].id`.
5. The sum of facet bucket counts for a boolean or enum property must equal the number of matched documents carrying that property, for the same query that produced the facets.
6. After `update` or `upsert`, full-text matching, filters, facets, and sorting must reflect only the new document content; content that existed solely in the replaced version must no longer match.
7. `save` followed by `load` into a fresh instance of the same schema must preserve `count`, `getByID` results, and the ranked id sequence of any search, and documents inserted after `load` must be searchable alongside restored ones.
8. A `groupBy` search must place every matched document carrying the grouped properties in exactly one group, and each group's `result` hits must obey `maxResult`.

## Public Interface

### Import Surface

```ts
import {
  create,
  insert,
  insertMultiple,
  update,
  updateMultiple,
  upsert,
  upsertMultiple,
  remove,
  removeMultiple,
  count,
  getByID,
  search,
  save,
  load,
} from '@orama/orama'
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `create` | function | Creates an empty search instance from a schema. |
| `insert` | function | Adds one document and returns its id. |
| `insertMultiple` | function | Adds an array of documents and returns their ids. |
| `update` | function | Replaces the document under an id and returns the new id. |
| `updateMultiple` | function | Replaces several documents and returns the new ids. |
| `upsert` | function | Inserts or replaces one document by id and returns the id. |
| `upsertMultiple` | function | Inserts or replaces several documents and returns their ids. |
| `remove` | function | Removes a document by id, returning whether it existed. |
| `removeMultiple` | function | Removes several documents and returns how many were removed. |
| `count` | function | Returns the number of stored documents. |
| `getByID` | function | Returns the stored document for an id, or `undefined`. |
| `search` | function | Evaluates a query object and returns hits, count, elapsed, facets, and groups. |
| `save` | function | Returns a serializable snapshot of the instance state. |
| `load` | function | Installs a snapshot into an instance created from the same schema. |

### CLI Entry Points

There is no console script for this package. Programmatic use is through ECMAScript module imports.

## Appendix A: Environment

The working environment runs Node.js 22 on Linux without network access during behavioral checks. TypeScript, Vitest, and tsx are available as development dependencies. The target module `@orama/orama` is not preinstalled from a registry; the delivered project must provide it.

The project must declare ECMAScript module mode and its module entry point in `package.json` so that `import { create } from '@orama/orama'` resolves after a local install of the delivered package.

## Appendix B: Assessment Notes

Assessment exercises instance creation, schema validation, document lifecycle (insert, update, upsert, remove, count, id lookup), full-text matching (prefix, exactness, tolerance, threshold, boost, paging, preflight), structured projections (where filters, facets, groups, sorting, distinct), persistence round-trips, and the error conditions in Error Semantics. Checks compare structured values and observable state transitions across projections; they do not depend on exact relevance score values, error message text, internal snapshot layout, or private module structure.
