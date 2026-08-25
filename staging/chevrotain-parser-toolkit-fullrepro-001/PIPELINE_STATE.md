# Pipeline State — chevrotain-parser-toolkit-fullrepro-001

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
functions_in_scope: 0 (Track A empty: upstream tests require '../../src/...' monorepo paths)
functions_kept: 98 (Track B generated: 73 atomic / 21 integration / 4 system_e2e)
functions_excluded: 0 (Track A)
updated:    2026-08-25
```

todo:
- [x] Generate spec-first oracle grounded by probes c1-c12
- [x] Dummy gate (0/98) + reference gate (98/98); merge artifacts, lint, verify

---

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-25 | S1_SCREENING | S1_SELECTED | filter_notes.md complete; hard gates pass (src_loc 10231; grammar rule engine with 6 projections: tokens/CST/errors/GAst/dts/embedded-values; 504-test suite; v13.2.0 fresh major 2026-08-01); decision keep |
| 2 | 2026-08-25 | S1_SELECTED | S2_SPEC_DRAFT | SELECTED row recorded in staging/PROGRESS_typescript.md ledger |
| 3 | 2026-08-25 | S2_SPEC_DRAFT | S2_SPEC_CHECK | spec_v1 drafted from chevrotain.io docs + live probing of chevrotain@13.2.0 (wip/probe/chevrotain/c1-c11.mjs); v13 removed content assist — excluded from scope |
| 4 | 2026-08-25 | S2_SPEC_CHECK | S2_SPEC_DONE | 25 validation checks + style gate pass; modal-verb/leakage scan clean after 4 rephrases |
| 5 | 2026-08-25 | S2_SPEC_DONE | S3A_IMPORT_AUDIT | upstream tests audited: import "../../src/scan/tokens_public.js" and sibling monorepo-relative paths in 100% of suites -> not portable to clean npm install |
| 6 | 2026-08-25 | S3A_IMPORT_AUDIT | S3B_TRIGGER | Track A discarded 100% of files; oracle_source=generated_only (precedent: orama/rrule/kysely/xstate/mobx packets) |
| 7 | 2026-08-25 | S3B_TRIGGER | S3B_GENERATE | generation started: all expected values observed by executing pinned chevrotain@13.2.0 (probes c1-c11) |
| 8 | 2026-08-25 | S3B_GENERATE | S3B_DUMMY | 98 tests written (73 atomic / 21 integration / 4 e2e); first run surfaced 4 defects: onlyOffset/onlyStart omit endOffset (spec corrected), duplicate CONSUME2 numeric suffix, single-extra-token handled by deletion not re-sync, NonTerminal.definition delegates to referenced rule (walk fixed) |
| 9 | 2026-08-25 | S3B_DUMMY | S3B_REFERENCE | inert-stub dummy passed 3 vacuous tests -> strengthened with positive value assertions; dummy now 0/98 |
| 10 | 2026-08-25 | S3B_REFERENCE | S3_ORACLE_MERGE | reference chevrotain@13.2.0: 98/98; tsc --noEmit clean after casting partial GAstVisitor subclasses (abstract members in typings) |
| 11 | 2026-08-25 | S3_ORACLE_MERGE | S3_REFERENCE_RUN | filter artifacts generated: kept_nodeids (98), taxonomy.jsonl, spec_test_map.md (98 covered rows), depends_on.json (25 mappings, all resolve); oracle_import_lint LINT_PASS on disk |
| 12 | 2026-08-25 | S3_REFERENCE_RUN | S3_DONE | reference_score.json recorded (98/98, by layer 73/21/4); verify_task.py STATIC_VALID; packet staged under staging/chevrotain-parser-toolkit-fullrepro-001 |
