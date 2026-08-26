# PIPELINE STATE — immer-immutable-state-fullrepro-001

state:      S3_DONE
stage:      3
spec_iter:  0
filter_iter: 0
eval_iter:  0
language:   typescript
functions_in_scope: 0 (Track A empty: 21/22 upstream jest files import "../src/immer" relative source paths; snapshot + NODE_ENV dependence)
functions_kept: 104 (79 atomic / 22 integration / 3 system_e2e)
functions_excluded: 0 (Track A)
oracle_count: 104
updated:    2026-08-26

## History

| date | state | note |
|------|-------|------|
| 2026-08-26 | S1_SCREENING | screened immerjs/immer@11.1.18: 3305 src LOC (proxy core + finalize + patches/mapset/arrayMethods plugins), 514 upstream jest test functions in 22 files; import pre-screen: 21/22 files import "../src/immer" (0 import the published entry) |
| 2026-08-26 | S1_SELECTED | hard gates pass (LOC 3305 >= 3000, 8 public projections over one draft graph, tests present but non-portable -> Track B); v11 fresh major (2025-11-23) diverges from trained immer 9/10 surface |
| 2026-08-26 | S2_SPEC_DRAFT | spec drafted: 8 behavior domains + state model + error table + 7 CVIs; all claims probe-grounded (probes p1-p18 against immer@11.1.18); clauses.md sidecar written |
| 2026-08-26 | S2_SPEC_DONE | validation checks + style gate pass; candidate-visible body only (no internal header) |
| 2026-08-26 | S3A_IMPORT_AUDIT | Track A empty: relative src imports + jest snapshot dependence -> Track B generated oracle importing only 'immer' |
| 2026-08-26 | S3B_GENERATE | generated 104 tests (79 atomic / 22 integration / 3 system_e2e) across 4 vitest files (plugin-off gating isolated in dedicated files); every expected value observed from immer@11.1.18 |
| 2026-08-26 | S3B_REFERENCE | pinned release passes 104/104 local vitest; tsc --noEmit clean; 2 spec claims corrected from execution (set-draft snapshots narrowed to maps after reference loop; array-method callbacks receive stored values, drafted elements passed as drafts); 3 initially-failing tests were test-authoring errors, fixed from observed behavior |
| 2026-08-26 | S3B_DUMMY | inert stub (recipes invoked over raw base so in-recipe assertions execute; productions return null; predicates false; loaders no-op) fails 104/104; two tests strengthened with positive assertions after early stub run exposed vacuous passes |
| 2026-08-26 | S3_DONE | lint LINT_PASS; artifacts written (kept_nodeids 104, taxonomy, spec_test_map 104 covered, reference_score 104/104, depends_on 25/25); integration floor met by adding 4 workflows (expected_oracle_max raised 100 -> 105 in filter_notes); packet staged |
