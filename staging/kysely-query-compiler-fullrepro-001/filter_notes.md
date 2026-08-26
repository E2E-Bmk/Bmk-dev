# filter_notes — kysely-query-compiler-fullrepro-001

```
repo: kysely-org/kysely (npm name kysely)
source_path: https://github.com/kysely-org/kysely (local mirror wip/repo-cache/kysely)
commit: f24018c789c3cf7ad03ccc672ada63a1ded87f88 (tag v0.29.5, npm kysely@0.29.5)
language: typescript
src_loc: 44740 (src/**/*.ts excluding tests)
test_functions: 714 it() call sites under test/node/src
test_files: test/node/src/*.test.ts (~40 files: select, where, insert, update, delete, join, with, raw-sql, camel-case, schema, ...)
dominant_test_styles: integration through the public API against live postgres/mysql/sqlite containers, asserting compiled SQL text + parameters per dialect (testSql helper) and executed row effects; oracle keeps only the compile-side assertions, which need no database
public_docs: kysely.dev (Getting started, Playground examples, API docs), README.md — constructor options, select/insert/update/delete builders, expression builder, sql template tag, plugins, schema builder
core_fact_source: one immutable query AST (OperationNode tree) built by the fluent builder API
derived_views: (1) PostgresQueryCompiler SQL + parameters, (2) MysqlQueryCompiler SQL + parameters, (3) SqliteQueryCompiler SQL + parameters, (4) plugin-transformed compilation (CamelCasePlugin, withSchema), (5) execution path via DummyDriver (empty result contract, lifecycle errors), (6) raw sql fragment compilation via the sql template tag
external_deps: none at runtime; oracle needs only vitest/typescript; no database (compile-only scope + DummyDriver)
test_import_audit: HIGH_RISK for direct reuse — upstream tests import from '../../..' repo-relative paths and require live database containers via a shared test-setup module; not portable to a clean npm install; oracle is Track B generated (precedent: orama-search-engine-fullrepro-001)
docs_test_alignment: aligned — docs and tests both center on builder -> compiled SQL per dialect
contamination_note: kysely@0.29.5, released 2026-08-10 (recent); the API surface tested here is stable since 0.27 (2024, before plausible cutoffs) → treat as known; anti-memorization via novel table/column fixtures (no person/pet examples reused verbatim: oracle uses distinct schemas and values where upstream examples exist, and probing confirmed expected strings)
decision: keep
reason: multi-component compiler pipeline (fluent builder -> immutable AST -> per-dialect compilers -> plugin transformers) with >= 5 public projections of one AST; SQL generation rules per dialect are a format-rule reimplementation, the candidate-selector difficulty shape that resists pattern-matching
risks: very large API surface (44.7k LOC) -> strict scope plan required; upstream examples (person/pet) are famous -> anti-memorization fixtures; type-level API is huge but type checking is not scored (behavioral compile output only)
scope_plan: target_subdomain=query compilation for select/insert/update/delete + expressions + CTE/set operations + raw sql tag + CamelCasePlugin/withSchema + schema DDL basics + DummyDriver execution lifecycle, across postgres/mysql/sqlite compilers; expected_oracle_max=100. Excluded: live database execution, transactions, migrations module, introspection, streaming, mergeInto, cold/exotic dialects (mssql), type-level inference guarantees, plugin authoring API.
difficulty_shapes: reimplementation-of-format-rule (SQL rendering per dialect); integration tests spanning >=3 projections (builder -> pg/mysql/sqlite compile -> plugin transform); equivalence judgement (same AST must render consistently across dialects)
```
