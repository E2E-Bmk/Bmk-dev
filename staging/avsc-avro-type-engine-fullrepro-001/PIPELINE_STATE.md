# PIPELINE STATE — avsc-avro-type-engine-fullrepro-001

state:      S3_DONE
stage:      3
spec_iter:  0
filter_iter: 0
eval_iter:  0
language:   typescript
functions_in_scope: 0 (Track A empty: every upstream mocha suite requires '../lib' relative paths, not the published package entry; several reach module internals)
functions_kept: 99 (72 atomic / 21 integration / 6 system_e2e)
functions_excluded: 0 (Track A)
oracle_count: 99
updated:    2026-08-25

## History

| date | state | note |
|------|-------|------|
| 2026-08-25 | S1_SCREENING | screened mtth/avsc@5.7.9: 8.3k LOC, 631 tests, 8 projections over one compiled Avro type graph |
| 2026-08-25 | S1_SELECTED | hard gates pass; Track A non-portable ('../lib' relative requires) -> plan Track B generated oracle; services/RPC + container streams excluded |
| 2026-08-25 | S2_SPEC_DRAFT | spec_v1.md drafted: 9 behavior domains, 7 CVIs, all claims probe-grounded (wip/probe/avsc a1-a4) |
| 2026-08-25 | S2_SPEC_DONE | validation checks + style gate pass; clauses.md sidecar (72 clauses) written |
| 2026-08-25 | S3A_IMPORT_AUDIT | Track A empty: all 6 upstream mocha suites require '../lib' / '../lib/<module>' relative paths and test_utils/test_containers reach internals -> Track B |
| 2026-08-25 | S3B_GENERATE | generated 99 tests (72 atomic / 21 integration / 6 system_e2e); every expected value observed from avsc@5.7.9 (probes a1-a6); 1 spec claim corrected from execution (float/double accept non-finite numbers) |
| 2026-08-25 | S3B_REFERENCE | pinned release passes 99/99 local vitest x4 on first run; tsc --noEmit clean after 4 forValue cast fixes |
| 2026-08-25 | S3B_DUMMY | inert full-surface stub (Type statics return inert instances, methods return empty/false/null, nothing throws) fails 99/99 |
| 2026-08-25 | S3_DONE | lint LINT_PASS; artifacts written (kept_nodeids 99, taxonomy, spec_test_map 99 covered, reference_score 99/99, depends_on 27/27); packet staged |
