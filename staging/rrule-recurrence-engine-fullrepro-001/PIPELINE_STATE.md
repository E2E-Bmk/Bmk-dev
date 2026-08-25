# Pipeline State — rrule-recurrence-engine-fullrepro-001

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
functions_in_scope: 0 (Track A empty: upstream tests import '../src/index' relative paths, not portable)
functions_kept: 0 (Track A)
functions_excluded: 0 (Track A)
oracle_count: 90 (Track B generated; 64 atomic / 22 integration / 4 system_e2e)
updated:    2026-08-25
```

todo (S4_SETUP, blocked in this environment):
- [ ] Docker sandbox scoring run via release-side TypeScript runner
- [ ] Assemble candidate packet (spec body only) and run Stage 4 evaluation

---

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-25 | S1_SCREENING | S1_SELECTED | filter_notes.md complete; hard gates pass (src_loc 4369; 5 projections over one recurrence definition; jest suite present; RFC background but engine arithmetic is the difficulty); decision keep |
| 2 | 2026-08-25 | S1_SELECTED | S2_SPEC_DRAFT | SELECTED row recorded in staging/PROGRESS_typescript.md ledger |
| 3 | 2026-08-25 | S2_SPEC_DRAFT | S2_SPEC_CHECK | spec_v1 drafted from README + live probing of rrule@2.8.1 (wip/probe/rrule/p1-p9.mjs) |
| 4 | 2026-08-25 | S2_SPEC_CHECK | S2_SPEC_DONE | 25 validation checks + style gate pass; modal-verb scan clean |
| 5 | 2026-08-25 | S2_SPEC_DONE | S3A_IMPORT_AUDIT | upstream tests audited: all 12 files import '../src/index' + shared test/lib helpers importing '../../src' -> not portable to clean npm install |
| 6 | 2026-08-25 | S3A_IMPORT_AUDIT | S3B_TRIGGER | Track A discarded 100% of files; rewrite audit recorded in filter_notes.md (test_import_audit) and spec_test_map.md footer; oracle_source=generated_only |
| 7 | 2026-08-25 | S3B_TRIGGER | S3B_GENERATE | 90 tests generated spec-first; expected values observed by executing pinned rrule@2.8.1 |
| 8 | 2026-08-25 | S3B_GENERATE | S3B_REFERENCE | first reference run 88/92: three draft spec claims contradicted observed behavior (freq/bysetpos raise at construction; non-Date until silently accepted; multi-DTSTART set strings apply first DTSTART to all rules) -> spec corrected from reference execution (spec_error protocol), 4 tests fixed, 2 single-assert tests folded into siblings to hold expected_oracle_max=90 |
| 9 | 2026-08-25 | S3B_DUMMY | S3B_REFERENCE | dummy stub (full named-export surface as no-ops) passes 0/90 |
| 10 | 2026-08-25 | S3B_REFERENCE | S3_ORACLE_MERGE | reference (npm rrule@2.8.1) passes 90/90 = 100% |
| 11 | 2026-08-25 | S3_ORACLE_MERGE | S3_REFERENCE_RUN | spec_test_map.md (90 covered rows), kept_nodeids.txt, taxonomy.jsonl, depends_on.json (26/26 integration annotated) written |
| 12 | 2026-08-25 | S3_REFERENCE_RUN | S3_DONE | filter/reference_score.json = 100%; filter/lint_result.txt first line LINT_PASS (TS-aware oracle_import_lint.py); verify_task.py STATIC_VALID |

---

## Gate evidence

- Lint: `python harness/oracle_import_lint.py rrule-recurrence-engine-fullrepro-001 staging/rrule-recurrence-engine-fullrepro-001/spec.md` → LINT_PASS (filter/lint_result.txt, regenerated after the last spec/oracle edit).
- Reference: filter/reference_score.json — 90/90 pass, pinned rrule@2.8.1 (commit 9f2061f), local Node 22 vitest; Docker sandbox run pending.
- Dummy: 0/90 pass with stub package (wip/rrule-recurrence-engine-fullrepro-001/dummy).
- Layer floors: atomic 64 ≥ 30; integration+system_e2e 26 ≥ 25; total 90 ≥ 60.
- Assertion composition: atomic positive share 57/64 = 89% ≥ 60%; zero no_check tests.
- Coverage quotas: every behavior H2 has ≥ 4 covered tests; all 7 CVIs covered (CVI-006 implicitly through expansion tests, others directly); Error Semantics rows covered by 12 tests.
- Scope check: kept set = 90 = expected_oracle_max, subdomain matches scope_plan (tzid/byeaster/NLP-locales/cache/DateWithZone all untested).
