# PIPELINE STATE — tanstack-table-core-engine-fullrepro-001

state:      S3B_GENERATE
stage:      3
spec_iter:  0
filter_iter: 0
eval_iter:  0
language:   typescript
updated:    2026-08-26

todo:
- [ ] Generate oracle tests from reference observation (execute 9.1.2, assert observed values)
- [ ] Fill spec_test_map rows per test as generated
- [ ] Per-section minimums + global floor (>=60; target ~115)

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-26 | S1_SCREENING | S1_SELECTED | filter_notes complete; keep: @tanstack/table-core@9.1.2 (28.4k stars, 20.7M weekly downloads), v9 atom-based rewrite released 2026-08-07..09 (memorized v8 API actively misleads); 24.3k src LOC scoped to core engine + 11 state features; upstream tests non-portable (../../src + src/static-functions imports) -> Track B planned |
| 2 | 2026-08-26 | S1_SELECTED | S2_SPEC_DRAFT | selection recorded in filter_notes (CANDIDATES.md lives outside this staging flow, consistent with prior 13 staged tasks); behavioral probes tt1-tt8 executed against installed 9.1.2 covering construction/features bag, three-layer atom state, controlled+initial state, columns/cells/headers, row-model pipeline order, sorting/filtering/global filter, visibility/ordering, pinning start-end, selection, expanding, grouping ids, aggregation fn resolution (auto->sum for numbers, registration requirement), faceting (own-filter exclusion), pagination |
| 3 | 2026-08-26 | S2_SPEC_DRAFT | S2_SPEC_CHECK | spec.md written (six-layer, 10 behavior domains, 8 CVIs, full import surface incl. store-reactivity-bindings subpath); clauses.md sidecar with 100 EARS clause IDs; every claim grounded in probe batches tt1-tt10 (incl. dot-path id derivation user.name.first->user_name_first, no getState, reset(true) vs reset(), setPageIndex clamp asymmetry, getIsSomeRowsSelected = any-selected, unknown sortFn->basic fallback vs aggregation->undefined) |
| 4 | 2026-08-26 | S2_SPEC_CHECK | S2_SPEC_DONE | 25-check pass: phrasing scan clean (one 'can do' rephrased), Non-Goals prefixes compliant, no leakage words, API Catalog Name/Kind/Role only, behavior sections have opening sentence + bold subsections, no Python-signature inline backticks |
| 5 | 2026-08-26 | S2_SPEC_DONE | S3A_IMPORT_AUDIT | candidate body is the whole file (no internal header used, consistent with prior staged tasks) |
| 6 | 2026-08-26 | S3A_IMPORT_AUDIT | S3A_REWRITE | audit: all 63 upstream .test.ts files import '../../../../src' and/or '../../../../src/static-functions' plus tests/fixtures + tests/helpers; zero files import the published package; static-functions subpath not present in published exports map as a public API surface for tests |
| 7 | 2026-08-26 | S3A_REWRITE | S3B_TRIGGER | rewrite_audit.md written: 63/63 files discarded (100% > 50% early trigger); rewrite impossible without reproducing upstream's internal static-function architecture, which Q1 forbids |
| 8 | 2026-08-26 | S3B_TRIGGER | S3B_GENERATE | coverage step adapted for TS precedent (no Python coverage harness for vitest here): generation targets derived from spec section quota table + probe evidence instead of coverage_gaps.txt, matching immer/yjs precedent |
