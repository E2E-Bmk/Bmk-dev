# PIPELINE STATE — prosemirror-model-doc-tree-fullrepro-001

state:      S3_DONE
stage:      3
spec_iter:  0
filter_iter: 0
eval_iter:  0
language:   typescript
functions_in_scope: 0 (Track A empty: every upstream suite imports prosemirror-test-builder, which depends on the real prosemirror-model and breaks scorer isolation)
functions_kept: 100 (Track B generated: 74 atomic / 20 integration / 6 system_e2e)
functions_excluded: 0 (Track A)
oracle_count: 100
updated:    2026-08-25

## History

| date | state | note |
|------|-------|------|
| 2026-08-25 | S1_SCREENING | screened prosemirror/prosemirror-model@1.25.11: 3.6k LOC, 309 tests, 7 projections over one immutable document tree |
| 2026-08-25 | S1_SELECTED | hard gates pass; Track A breaks scorer isolation (prosemirror-test-builder depends on real prosemirror-model) -> plan Track B generated oracle; DOM projection excluded |
| 2026-08-25 | S2_SPEC_DRAFT | spec_v1.md drafted: 8 behavior domains, 7 CVIs, all claims probe-grounded (wip/probe/pm p1-p6) |
| 2026-08-25 | S2_SPEC_DONE | validation checks + style gate pass; clauses.md sidecar (63 clauses) written |
| 2026-08-25 | S3A_IMPORT_AUDIT | Track A empty: all 8 upstream suites import prosemirror-test-builder (+ ist, jsdom); helper package depends on the real target -> Track B |
| 2026-08-25 | S3B_GENERATE | generated 100 tests (74 atomic / 20 integration / 6 system_e2e); every expected value observed from prosemirror-model@1.25.11 (p1-p6 probes) |
| 2026-08-25 | S3B_REFERENCE | one computed diff-end value and one descendant count corrected from execution; pinned release passes 100/100 local vitest x4; tsc --noEmit clean |
| 2026-08-25 | S3B_DUMMY | inert full-surface stub fails 100/100 (schema-table test strengthened with a behavioral creation phase after first run showed 1 dummy pass) |
| 2026-08-25 | S3_DONE | lint LINT_PASS; artifacts written (kept_nodeids 100, taxonomy, spec_test_map 100 covered, reference_score 100/100, depends_on 26/26); packet staged |
