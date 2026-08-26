# PIPELINE STATE — yjs-crdt-sync-engine-fullrepro-001

state:      S3_DONE
stage:      3
spec_iter:  0
filter_iter: 0
eval_iter:  0
language:   typescript
functions_in_scope: 0 (Track A empty: all 11 upstream files import '../src/*' and require the lib0/testing runner + testHelper fuzz infrastructure)
functions_kept: 116 (88 atomic / 24 integration / 4 system_e2e)
functions_excluded: 0 (Track A)
oracle_count: 116
updated:    2026-08-26

## History

| date | state | note |
|------|-------|------|
| 2026-08-26 | S1_SCREENING | screened yjs/yjs@13.6.32: 10867 src LOC (CRDT structs + types + utils), ~300 upstream lib0/testing functions in 11 files (6840 LOC); import pre-screen: 11/11 files import relative '../src' paths, 0 import the published entry |
| 2026-08-26 | S1_SELECTED | hard gates pass (LOC 10867 >= 3000, 7 public projections over one CRDT store, tests present but non-portable -> Track B); difficulty rests on convergence/idempotency/update-algebra properties a delivery must implement, not recall |
| 2026-08-26 | S2_SPEC_DRAFT | behavior probed against yjs@13.6.32 (probes y1-y13: doc identity, types, updates v1/v2 + algebra, events incl. in-handler-only changes computation, undo origins, snapshots gc rule, relative positions); spec drafted: 8 behavior domains + state model + error table + 7 CVIs, all claims probe-grounded; clauses.md sidecar written |
| 2026-08-26 | S2_SPEC_DONE | validation checks + style gate pass; candidate-visible body only (no internal header) |
| 2026-08-26 | S3A_IMPORT_AUDIT | Track A empty: all 11 upstream files use lib0/testing runner + relative '../src' imports + testHelper fuzz infra -> Track B generated oracle importing only 'yjs' |
| 2026-08-26 | S3B_GENERATE | generated 116 tests (88 atomic / 24 integration / 4 system_e2e) across 4 vitest files; every expected value observed from yjs@13.6.32 |
| 2026-08-26 | S3B_REFERENCE | pinned release passes 116/116 local vitest; tsc --noEmit clean; 1 spec claim corrected from execution (map 'add' records report oldValue undefined, not null - earlier probe masked undefined through JSON serialization); 1 lint fix (YArrayEvent type annotation replaced with structural type - symbol not in spec) |
| 2026-08-26 | S3B_DUMMY | inert stub (no-throw no-op types, empty payload producers, false predicates, observers never fire, abs positions index -1) fails 116/116; 5 tests strengthened with positive assertions after early stub runs exposed vacuous passes (no-op transaction, map clear, sv-from-update, default capture merge, merge/diff pipeline) |
| 2026-08-26 | S3_DONE | lint LINT_PASS (fresh, newer than all oracle files); artifacts written (kept_nodeids 116, taxonomy, spec_test_map 116 covered, reference_score 116/116, depends_on 28/28); atomic positive share 90%, zero no_check; packet staged |
