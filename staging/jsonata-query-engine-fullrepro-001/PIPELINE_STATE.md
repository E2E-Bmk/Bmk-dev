# PIPELINE STATE — jsonata-query-engine-fullrepro-001

state:      S3_DONE
stage:      3
spec_iter:  0
filter_iter: 0
eval_iter:  0
language:   typescript
functions_in_scope: 0 (Track A empty: drivers require('../src/jsonata') relative paths and the JSON case corpus needs the upstream driver harness)
functions_kept: 104 (79 atomic / 23 integration / 2 system_e2e)
functions_excluded: 0 (Track A)
oracle_count: 104
updated:    2026-08-25

## History

| date | state | note |
|------|-------|------|
| 2026-08-25 | S1_SCREENING | screened jsonata-js/jsonata@2.2.2: 7.7k LOC (TDOP parser + sequence-semantics evaluator + 60+ function library + signature validator + datetime picture engine), 1659 upstream expression cases |
| 2026-08-25 | S1_SELECTED | hard gates pass; Track A non-portable (relative requires + JSON corpus driver) -> plan Track B generated oracle; recovery mode, resource limits, full datetime picture matrix excluded |
| 2026-08-25 | S2_SPEC_DRAFT | spec_v1.md drafted: 8 behavior domains + state model + error table + 7 CVIs, all claims probe-grounded (wip/probe/jsonata j1-j4) |
| 2026-08-25 | S2_SPEC_DONE | validation checks + style gate pass; clauses.md sidecar (62 clauses) written |
| 2026-08-25 | S3A_IMPORT_AUDIT | Track A empty: all mocha drivers require('../src/jsonata') and the 1291-file JSON corpus needs the upstream run-test-suite harness (datasets/timelimit/depth) -> Track B |
| 2026-08-25 | S3B_GENERATE | generated 104 tests (79 atomic / 23 integration / 2 system_e2e); every expected value observed from jsonata@2.2.2 (probes j1-j5); 1 spec claim corrected from execution ('in' matches primitives only, deep-equality invariant narrowed to =/!= and $distinct) |
| 2026-08-25 | S3B_REFERENCE | pinned release passes 104/104 local vitest; tsc --noEmit clean; results compared after JSON projection (engine marks sequences with own enumerable flags; spec contracts plain JSON) |
| 2026-08-25 | S3B_DUMMY | inert stub (compile succeeds, evaluate resolves null, assign/registerFunction no-ops, ast returns {}) fails 104/104 |
| 2026-08-25 | S3_DONE | lint LINT_PASS; artifacts written (kept_nodeids 104, taxonomy, spec_test_map 104 covered, reference_score 104/104, depends_on 25/25); packet staged |
