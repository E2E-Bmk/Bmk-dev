# Pipeline State — orama-search-engine-fullrepro-001

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
functions_in_scope: 0 (Track A empty: upstream tests are monorepo-relative, not portable)
functions_kept: 0 (Track A)
functions_excluded: 0 (Track A)
oracle_count: 78 (Track B generated; 52 atomic / 23 integration / 3 system_e2e)
updated:    2026-08-25
```

todo (S4_SETUP, blocked in this environment):
- [ ] Docker sandbox scoring run via release-side TypeScript runner
- [ ] Assemble candidate packet (spec body only) and run Stage 4 evaluation

---

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-25 | S1_SCREENING | S1_SELECTED | filter_notes.md complete; hard gates pass (src_loc 9948; multi-projection; tests present; not a closed standard); decision keep |
| 2 | 2026-08-25 | S1_SELECTED | S2_SPEC_DRAFT | SELECTED row recorded in staging/PROGRESS_typescript.md ledger |
| 3 | 2026-08-25 | S2_SPEC_DRAFT | S2_SPEC_CHECK | spec_v1 drafted from docs + live probing of @orama/orama@3.1.18 (wip/probe/orama1-5.mjs) |
| 4 | 2026-08-25 | S2_SPEC_CHECK | S2_SPEC_DONE | 25 validation checks + style gate pass; two reference-grounded corrections during drafting (exact suppresses tolerance; string where filters are whole-token) |
| 5 | 2026-08-25 | S2_SPEC_DONE | S3A_IMPORT_AUDIT | upstream tests audited: 100% import monorepo-relative '../src' paths -> not portable to clean install |
| 6 | 2026-08-25 | S3A_IMPORT_AUDIT | S3B_TRIGGER | Track A discarded >50% (all files); rewrite_audit recorded in filter_notes.md + spec_test_map.md footer |
| 7 | 2026-08-25 | S3B_TRIGGER | S3B_GENERATE | 78 tests generated spec-first; expected values observed by executing pinned reference |
| 8 | 2026-08-25 | S3B_DUMMY | S3B_REFERENCE | dummy stub (14 exports returning undefined) passed 1/78 -> offending test strengthened with positive guard -> dummy 0/78 |
| 9 | 2026-08-25 | S3B_REFERENCE | S3_ORACLE_MERGE | reference (npm @orama/orama@3.1.18) passes 78/78 = 100% |
| 10 | 2026-08-25 | S3_ORACLE_MERGE | S3_REFERENCE_RUN | spec_test_map.md (78 covered rows), kept_nodeids.txt, taxonomy.jsonl, depends_on.json (26/26 integration annotated) written |
| 11 | 2026-08-25 | S3_REFERENCE_RUN | S3_DONE | filter/reference_score.json = 100%; filter/lint_result.txt first line LINT_PASS (TS-aware oracle_import_lint.py, task registered in target_imports) |

---

## Gate evidence

- Lint: `python harness/oracle_import_lint.py orama-search-engine-fullrepro-001 staging/orama-search-engine-fullrepro-001/spec.md` → LINT_PASS (filter/lint_result.txt, written after last oracle edit).
- Reference: filter/reference_score.json — 78/78 pass, pinned @orama/orama@3.1.18 (commit 2fe41e1), local Node 22 vitest; Docker sandbox run pending.
- Dummy: 0/78 pass with stub package (wip/orama-search-engine-fullrepro-001/dummy).
- Layer floors: atomic 52 ≥ 30; integration+system_e2e 26 ≥ 25; total 78 ≥ 60.
- Assertion composition: atomic positive share 43/52 = 83% ≥ 60%; zero no_check tests.
- Coverage quotas: every behavior H2 has ≥ 4 covered tests; Cross-View Invariants has 8 CVIs each covered; Error Semantics rows all covered (8 tests).
