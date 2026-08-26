# Clause register — orama-search-engine-fullrepro-001

Clause IDs cited by oracle test docstrings (`Verifies:`). Each ID anchors one
behavioral clause of spec.md; section anchors use the spec's H2 headings.

## Instance Creation And Schema
- ORAMA-CRE-001 — "WHEN `create` is called with a valid schema, the instance must start with a document count of zero and empty results for every query."
- ORAMA-CRE-002 — "A nested entry is addressed everywhere else with a dot-separated path (for example `meta.rating`)." / schema type strings list.
- ORAMA-CRE-003 — "IF a schema entry uses an unknown type string, THEN `create` must throw an `Error` whose `code` property is `'INVALID_SCHEMA_TYPE'`."
- ORAMA-CRE-004 — "callers must be able to `await` the return value of `insert`, `insertMultiple`, ... and observe the documented result."

## Document Lifecycle
- ORAMA-DOC-001 — insert returns id; document `id` property used; generated unique string id otherwise.
- ORAMA-DOC-002 — "`insertMultiple` accepts an array of documents and returns the array of assigned ids in the same order."
- ORAMA-DOC-003 — duplicate id must throw `DOCUMENT_ALREADY_EXISTS`.
- ORAMA-DOC-004 — schema-contradicting value must throw `SCHEMA_VALIDATION_FAILURE`.
- ORAMA-DOC-005 — omitted schema properties allowed; extra properties stored verbatim but not indexed.
- ORAMA-DOC-006 — "`count` returns the number of stored documents."
- ORAMA-DOC-007 — "`getByID` returns the stored document for an id ... verbatim"; unknown id returns `undefined`.
- ORAMA-DOC-008 — `remove` returns `true`; missing id returns `false` and leaves the store unchanged.
- ORAMA-DOC-009 — "`removeMultiple` ... returns the number of documents it removed."
- ORAMA-DOC-010 — `update` replaces and returns the new id; previous id must no longer resolve.
- ORAMA-DOC-011 — `updateMultiple` parallel arrays semantics.
- ORAMA-DOC-012 — `upsert` inserts or replaces; replacing must not change the document count.
- ORAMA-DOC-013 — `upsertMultiple` applies upsert across an array.

## Full-Text Search
- ORAMA-FTS-001 — result shape: hits (id, score, document), count, elapsed (raw, formatted).
- ORAMA-FTS-002 — hits ordered by descending score unless sortBy/groupBy applies.
- ORAMA-FTS-003 — case-insensitive tokenization on non-alphanumeric boundaries.
- ORAMA-FTS-004 — prefix matching of query tokens.
- ORAMA-FTS-005 — omitted or empty term matches every stored document.
- ORAMA-FTS-006 — `properties` restricts matching; omitted or `'*'` searches all string properties.
- ORAMA-FTS-007 — unknown property in `properties` must throw `UNKNOWN_INDEX`.
- ORAMA-FTS-008 — `exact` excludes prefix-only matches and suppresses tolerance.
- ORAMA-FTS-009 — `tolerance` admits tokens within edit distance; absent tolerance excludes typos.
- ORAMA-FTS-010 — threshold 0 = all tokens; threshold 1 (default) = any token.
- ORAMA-FTS-011 — `boost` multiplies per-property relevance and must not change the match set.
- ORAMA-FTS-012 — `limit` (default 10) / `offset` (default 0) slice hits; count stays the unsliced total.
- ORAMA-FTS-013 — `preflight` reports count with empty hits.

## Filters, Facets, Groups, And Sorting
- ORAMA-STR-001 — number filters: eq/gt/gte/lt/lte/between (inclusive).
- ORAMA-STR-002 — boolean filters accept a direct boolean.
- ORAMA-STR-003 — enum filters: eq/in/nin.
- ORAMA-STR-004 — string filters match whole tokens; no prefix or tolerance expansion.
- ORAMA-STR-005 — string[] filters match documents whose array contains a matching element.
- ORAMA-STR-006 — multiple where entries conjoin; filters combine with term.
- ORAMA-STR-007 — unknown where property must throw `UNKNOWN_FILTER_PROPERTY`.
- ORAMA-STR-008 — string/boolean/enum facets: values buckets + count of distinct values.
- ORAMA-STR-009 — number facets: inclusive `"from-to"` range buckets; document counted in every containing range.
- ORAMA-STR-010 — string facet limit/offset/sort options.
- ORAMA-STR-011 — sortBy property with ASC (default) / DESC over number, string, boolean, nested paths.
- ORAMA-STR-012 — sortBy comparator receives `[id, score, document]` triples.
- ORAMA-STR-013 — groupBy partitions matched docs per value combination; maxResult bounds per group.
- ORAMA-STR-014 — groupBy on enum must throw `INVALID_GROUP_BY_PROPERTY`.
- ORAMA-STR-015 — distinctOn keeps first hit per distinct value; count stays pre-deduplication.

## Persistence
- ORAMA-PER-001 — `save` returns a JSON-serializable snapshot.
- ORAMA-PER-002 — `load` restores behavior; subsequent operations behave like a native instance.

## Error Semantics (table rows)
- ORAMA-ERR-001 — unknown schema type → INVALID_SCHEMA_TYPE.
- ORAMA-ERR-002 — schema violation on insert → SCHEMA_VALIDATION_FAILURE.
- ORAMA-ERR-003 — duplicate id → DOCUMENT_ALREADY_EXISTS.
- ORAMA-ERR-004 — unknown properties entry → UNKNOWN_INDEX.
- ORAMA-ERR-005 — unknown where property → UNKNOWN_FILTER_PROPERTY.
- ORAMA-ERR-006 — groupBy enum property → INVALID_GROUP_BY_PROPERTY.
- ORAMA-ERR-007 — getByID missing id → undefined.
- ORAMA-ERR-008 — remove missing id → false, store unchanged.

## Cross-View Invariants
- ORAMA-CVI-001 .. ORAMA-CVI-008 — invariants 1..8 of the Cross-View Invariants section, in order.
