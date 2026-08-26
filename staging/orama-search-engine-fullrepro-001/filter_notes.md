# filter_notes — orama-search-engine-fullrepro-001

```
repo: oramasearch/orama (monorepo package packages/orama, npm name @orama/orama)
source_path: https://github.com/oramasearch/orama (local mirror wip/repo-cache/orama)
commit: 2fe41e163c2bdd7830eed7496c69134aea8ee3ba (tag v3.1.18, npm @orama/orama@3.1.18)
language: typescript
src_loc: 9948 (packages/orama/src/**/*.ts, excluding tests)
test_functions: 445 (t.test/it/test call sites under packages/orama/tests)
test_files: packages/orama/tests/*.test.ts (~30 files: search, filters, facets, group_by, sort, serialization, insert, remove, update, tokenizer, threshold, boost, ...)
dominant_test_styles: unit + integration over the public API via node:test; expected values are concrete structured results; few snapshot checks
public_docs: https://docs.orama.com/docs/orama-js (usage, search, filters, facets, sorting, grouping, threshold, preflight, utilities), README.md, typedoc-style types shipped with the package
core_fact_source: one in-memory search instance: document store + typed per-property indexes (radix-tree full-text, numeric/boolean/enum filter structures) + sorter state
derived_views: (1) search hits with scores, (2) count, (3) getByID, (4) facets aggregation, (5) groupBy groups, (6) sorted / distinct projections, (7) save()/load() RawData round-trip
external_deps: none at runtime (pure ESM JS); oracle needs only vitest/typescript
test_import_audit: HIGH_RISK for direct reuse — 100% of upstream test files import from monorepo-relative '../src/index.js' paths, not the published package name; Track A reuse is not portable, oracle is Track B generated (precedent: tinybase-reactive-store-fullrepro-001, oracle_source=generated_only)
docs_test_alignment: aligned — docs describe the same library-API projections the tests exercise
contamination_note: @orama/orama@3.1.18, released 2026-07 (npm time.modified 2026-07-27); the project is public since 2023, before any plausible cutoff → treat as known; anti-memorization via novel fixture values in oracle
decision: keep
reason: multi-component engine (tokenizer, typed indexes, scoring, filter/facet/group/sort pipelines) over one shared fact source with >= 6 independent public projections; rule-engine-like search semantics (threshold, tolerance, exact, boost) resist pattern-matching
risks: large API surface -> scope plan required; dual sync/promise API (every method awaitable); error identity is carried by Error.code strings, which the spec must declare to stay fair
scope_plan: target_subdomain=full-text search + document lifecycle + filters/facets/groups/sort/distinct + save/load serialization; expected_oracle_max=100. Excluded: vector search, hybrid search, AnswerSession/RAG, pinning rules, plugin system, custom components, non-English languages/stemming.
```

## Difficulty shapes (candidate-selector heuristic)

- **Reimplementation of a rule**: tokenizer + prefix matching + typo tolerance (bounded edit distance) + threshold semantics (0 = all tokens AND, 1 = any token OR) + per-property boost on scoring.
- **Multi-projection integration**: the same index state must agree across search hits, count, getByID, facets, groups, sorted/distinct output, and a save/load round-trip.
- **Equivalence judgement**: save() → load() must reproduce identical observable behavior in a fresh instance.

## Notes

- Reference behavior verified by running @orama/orama@3.1.18 in Node 22 (see wip/probe/orama*.mjs).
- groupBy allows string/number/boolean properties only (enum rejected with INVALID_GROUP_BY_PROPERTY).
- facet limit/offset/sort options apply only to string-typed facets.
- update() returns the new document id; remove() of a missing id returns false.
- threshold: 0 → only documents matching all tokens; 1 → any token (default).
