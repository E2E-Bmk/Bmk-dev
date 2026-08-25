# PIPELINE STATE — tanstack-query-core-cache-engine-fullrepro-001

state:      S3_DONE
stage:      3
spec_iter:  0
filter_iter: 0
eval_iter:  0
language:   typescript
functions_in_scope: 0 (Track A empty: upstream tests import '..'/'../utils' and workspace package @tanstack/query-test-utils)
functions_kept: 98 (Track B generated: 70 atomic / 22 integration / 6 system_e2e)
functions_excluded: 0 (Track A)
oracle_count: 98
updated:    2026-08-25

## History

| date | state | note |
|------|-------|------|
| 2026-08-25 | S1_SCREENING | screened TanStack/query packages/query-core (@tanstack/query-core@5.102.4): 7.3k LOC, 636 tests, 7 projections over one cache pair |
| 2026-08-25 | S1_SELECTED | hard gates pass; Track A HIGH_RISK (workspace test-utils + relative imports) -> plan Track B generated oracle |
| 2026-08-25 | S2_SPEC_DRAFT | spec_v1.md drafted: 8 behavior domains, 7 CVIs, all claims probe-grounded (wip/probe/qc) |
| 2026-08-25 | S2_SPEC_DONE | 25 validation checks + style gate pass; clauses.md sidecar (76 clauses) written |
| 2026-08-25 | S3A_IMPORT_AUDIT | Track A empty: upstream tests import '..'/'../utils'/'../types' and @tanstack/query-test-utils; 0 portable files -> Track B |
| 2026-08-25 | S3B_GENERATE | generated 98 tests (70 atomic / 22 integration / 6 system_e2e), all values observed from @tanstack/query-core@5.102.4 (verify1-3 probes) |
| 2026-08-25 | S3B_REFERENCE | two spec_error corrections grounded in execution (find exact-by-default; notify deferred flush); pinned release passes 98/98 local vitest x4; tsc --noEmit clean |
| 2026-08-25 | S3B_DUMMY | inert full-surface stub fails 98/98 (2 emptiness-shaped tests strengthened with positive phases first) |
| 2026-08-25 | S3_DONE | lint LINT_PASS; artifacts written (kept_nodeids, taxonomy, spec_test_map 98 covered, reference_score 98/98, depends_on 28/28); packet staged |
