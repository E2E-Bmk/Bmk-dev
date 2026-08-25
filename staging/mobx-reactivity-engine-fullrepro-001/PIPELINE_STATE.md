# Pipeline State — mobx-reactivity-engine-fullrepro-001

> Stage 1–3 packet (Definition A deliverable). Stage 4/5 pending on the release side.

---

## Current

```
state:      S3_DONE
stage:      3
spec_iter:  0
filter_iter: 0
eval_iter:  0
language:   typescript
functions_in_scope: 0 (Track A empty: upstream tests require '../../src/mobx.ts' monorepo paths)
functions_kept: 100 (Track B generated: 75 atomic / 21 integration / 4 system_e2e)
functions_excluded: 0 (Track A)
updated:    2026-08-25
```

todo:
- [x] Draft spec_v1 grounded by probing mobx@7.0.3
- [x] Generate spec-first oracle; dummy (0/100) + reference (100/100) gates; merge artifacts

---

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-25 | S1_SCREENING | S1_SELECTED | filter_notes.md complete; hard gates pass (src_loc 7249; reactive graph rule engine with >=5 projections; 804-test suite; v7.0.3 fresh major grounded by execution); decision keep |
| 2 | 2026-08-25 | S1_SELECTED | S2_SPEC_DRAFT | SELECTED row recorded in staging/PROGRESS_typescript.md ledger |
| 3 | 2026-08-25 | S2_SPEC_DRAFT | S2_SPEC_CHECK | spec_v1 drafted from mobx.js.org docs + live probing of mobx@7.0.3 (wip/probe/mobx/m1-m6.mjs) |
| 4 | 2026-08-25 | S2_SPEC_CHECK | S2_SPEC_DONE | 25 validation checks + style gate pass; modal-verb/leakage scan clean |
| 5 | 2026-08-25 | S2_SPEC_DONE | S3A_IMPORT_AUDIT | upstream tests audited: __tests__/base/*.js require('../../src/mobx.ts') monorepo-relative -> not portable to clean npm install |
| 6 | 2026-08-25 | S3A_IMPORT_AUDIT | S3B_TRIGGER | Track A discarded 100% of files; oracle_source=generated_only (precedent: orama/rrule/kysely/xstate packets) |
| 7 | 2026-08-25 | S3B_TRIGGER | S3B_GENERATE | generation started: expected run counts/events observed by executing pinned mobx@7.0.3 (probes m1-m6) |
| 8 | 2026-08-25 | S3B_GENERATE | S3B_DUMMY | 100 tests written (76 atomic / 20 integration / 4 e2e); one weak negative-only predicate test strengthened; frozen-stub dummy passes 0/100 |
| 9 | 2026-08-25 | S3B_DUMMY | S3B_REFERENCE | reference mobx@7.0.3 run: 100/100 first pass; tsc --noEmit clean after one typings cast (observable(primitive) auto-boxes at runtime, typings reject it) |
| 10 | 2026-08-25 | S3B_REFERENCE | S3_ORACLE_MERGE | filter artifacts generated: kept_nodeids (100), taxonomy.jsonl, spec_test_map.md (100 covered rows), depends_on.json (24 integration mappings); oracle_import_lint LINT_PASS on disk |
| 11 | 2026-08-25 | S3_ORACLE_MERGE | S3_REFERENCE_RUN | reference_score.json recorded (100/100, pass_rate 1.0, by layer 76/20/4) |
| 12 | 2026-08-25 | S3_REFERENCE_RUN | S3_ORACLE_MERGE | verify_task flagged integration+e2e floor (24 < 25): added one integration test (self-disposing reaction mid-stream), merged the two toJS atomic tests to hold total at 100 -> 75 atomic / 21 integration / 4 e2e |
| 13 | 2026-08-25 | S3_ORACLE_MERGE | S3_REFERENCE_RUN | gates re-run after rebalance: reference 100/100, dummy 0/100; artifacts + lint regenerated (LINT_PASS) |
| 14 | 2026-08-25 | S3_REFERENCE_RUN | S3_DONE | verify_task.py STATIC_VALID; task.json assembled; packet staged under staging/mobx-reactivity-engine-fullrepro-001 |
