# Pipeline State — xstate-statechart-engine-fullrepro-001

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
functions_in_scope: 0 (Track A empty: upstream tests import '../src/index.ts' monorepo paths)
functions_kept: 96 (Track B generated: 71 atomic / 21 integration / 4 system_e2e)
functions_excluded: 0 (Track A)
updated:    2026-08-25
```

todo:
- [x] Generate spec-first oracle tests; expected snapshots observed by executing xstate@5.32.5
- [x] Dummy gate (0/96), reference gate (96/96), merge artifacts

---

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-25 | S1_SCREENING | S1_SELECTED | filter_notes.md complete; hard gates pass (src_loc 15467; statechart rule engine with >=5 projections over one machine definition; 1375-test suite; SCXML background but v5 semantics are library-specific); decision keep |
| 2 | 2026-08-25 | S1_SELECTED | S2_SPEC_DRAFT | SELECTED row recorded in staging/PROGRESS_typescript.md ledger |
| 3 | 2026-08-25 | S2_SPEC_DRAFT | S2_SPEC_CHECK | spec_v1 drafted from stately.ai docs + live probing of xstate@5.32.5 (wip/probe/xstate/x1-x4.mjs) |
| 4 | 2026-08-25 | S2_SPEC_CHECK | S2_SPEC_DONE | 25 validation checks + style gate pass; modal-verb/leakage scan clean (verify_task FORBIDDEN_BODY_TERMS checked) |
| 5 | 2026-08-25 | S2_SPEC_DONE | S3A_IMPORT_AUDIT | upstream tests audited: packages/core/test/*.test.ts import '../src/index.ts' + monorepo utils -> not portable to clean npm install |
| 6 | 2026-08-25 | S3A_IMPORT_AUDIT | S3B_TRIGGER | Track A discarded 100% of files; oracle_source=generated_only (precedent: orama/rrule/kysely packets) |
| 7 | 2026-08-25 | S3B_TRIGGER | S3B_GENERATE | generation started: expected snapshots observed by executing pinned xstate@5.32.5 (probes x1-x7) |
| 8 | 2026-08-25 | S3B_GENERATE | S3B_DUMMY | 96 tests written (71 atomic / 21 integration / 4 e2e); probes x6-x7 grounded restore/timer and e2e workflows before writing; two weak tests strengthened (empty-log-only and can-false-only assertions given positive snapshot checks); inert constant-snapshot stub passes 0/96 |
| 9 | 2026-08-25 | S3B_DUMMY | S3B_REFERENCE | reference xstate@5.32.5 run: 96/96 first pass; tsc --noEmit clean; persistence-with-armed-timer corner found non-re-arming in probes and kept out of spec and oracle |
| 10 | 2026-08-25 | S3B_REFERENCE | S3_ORACLE_MERGE | filter artifacts generated: kept_nodeids (96), taxonomy.jsonl, spec_test_map.md (96 covered rows), depends_on.json (25 integration mappings); oracle_import_lint LINT_PASS on disk |
| 11 | 2026-08-25 | S3_ORACLE_MERGE | S3_REFERENCE_RUN | reference_score.json recorded (96/96, pass_rate 1.0, by layer 71/21/4) |
| 12 | 2026-08-25 | S3_REFERENCE_RUN | S3_DONE | verify_task.py STATIC_VALID; task.json assembled; packet staged under staging/xstate-statechart-engine-fullrepro-001 |
