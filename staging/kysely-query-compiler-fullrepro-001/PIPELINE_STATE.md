# Pipeline State — kysely-query-compiler-fullrepro-001

> Stage 1–3 packet (Definition A deliverable). Stage 4/5 pending on the release side.

---

## Current

```
state:      S3_DONE
stage:      3
spec_iter:  1
filter_iter: 0
eval_iter:  0
language:   typescript
functions_in_scope: 0 (Track A empty: upstream tests import '../../..' repo paths and need live DB containers)
functions_kept: 96 (Track B generated: 70 atomic / 22 integration / 4 system_e2e)
functions_excluded: 0 (Track A)
updated:    2026-08-25
```

todo:
- [x] Generate spec-first oracle tests; expected SQL observed by executing kysely@0.29.5
- [x] Dummy gate (0/96), reference gate (96/96), merge artifacts

---

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-25 | S1_SCREENING | S1_SELECTED | filter_notes.md complete; hard gates pass (src_loc 44740; compiler pipeline with >=5 projections of one AST; huge suite; scope plan set); decision keep |
| 2 | 2026-08-25 | S1_SELECTED | S2_SPEC_DRAFT | SELECTED row recorded in staging/PROGRESS_typescript.md ledger |
| 3 | 2026-08-25 | S2_SPEC_DRAFT | S2_SPEC_CHECK | spec_v1 drafted from README/kysely.dev + live probing of kysely@0.29.5 (wip/probe/kysely/k1-k6.mjs) |
| 4 | 2026-08-25 | S2_SPEC_CHECK | S2_SPEC_DONE | 25 validation checks + style gate pass; modal-verb/leakage scan clean |
| 5 | 2026-08-25 | S2_SPEC_DONE | S3A_IMPORT_AUDIT | upstream tests audited: test/node/src/*.test.ts import '../../..' repo paths and a shared test-setup requiring live postgres/mysql/sqlite containers -> not portable |
| 6 | 2026-08-25 | S3A_IMPORT_AUDIT | S3B_TRIGGER | Track A discarded 100% of files; oracle_source=generated_only (precedent: orama/rrule packets) |
| 7 | 2026-08-25 | S3B_TRIGGER | S3B_GENERATE | generation started: expected SQL/parameters observed by executing pinned kysely@0.29.5 (probes k1-k8) |
| 8 | 2026-08-25 | S3B_GENERATE | S3B_DUMMY | 96 tests written (70 atomic / 22 integration / 4 e2e); inert chainable-proxy stub passes 0/96; two self-consistency tests strengthened with exact expected strings so a constant stub cannot pass them |
| 9 | 2026-08-25 | S3B_DUMMY | S3B_REFERENCE | reference kysely@0.29.5 run: 95/96 -> spec_error confirmed by re-execution (destroyed-driver rejection requires prior lazy driver init); spec corrected from reference execution, spec_iter -> 1; second run 96/96; tsc --noEmit clean |
| 10 | 2026-08-25 | S3B_REFERENCE | S3_ORACLE_MERGE | filter artifacts generated: kept_nodeids (96), taxonomy.jsonl, spec_test_map.md (96 covered rows), depends_on.json (26 integration mappings); oracle_import_lint LINT_PASS on disk |
| 11 | 2026-08-25 | S3_ORACLE_MERGE | S3_REFERENCE_RUN | reference_score.json recorded (96/96, pass_rate 1.0, by layer 70/22/4) |
| 12 | 2026-08-25 | S3_REFERENCE_RUN | S3_DONE | verify_task.py STATIC_VALID; task.json assembled; packet staged under staging/kysely-query-compiler-fullrepro-001 |
