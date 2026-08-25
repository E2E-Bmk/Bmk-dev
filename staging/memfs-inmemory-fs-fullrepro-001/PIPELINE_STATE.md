# PIPELINE STATE — memfs-inmemory-fs-fullrepro-001

state:      S3_DONE
stage:      3
spec_iter:  0
filter_iter: 0
eval_iter:  0
language:   typescript
functions_in_scope: 0 (Track A empty: upstream tests import '../index' and @jsonjoy.com workspace packages)
functions_kept: 99 (Track B generated: 73 atomic / 22 integration / 4 system_e2e)
functions_excluded: 0 (Track A)
oracle_count: 99
updated:    2026-08-25

## History

| date | state | note |
|------|-------|------|
| 2026-08-25 | S1_SCREENING | screened streamich/memfs (memfs@4.68.1): 6.3k core LOC, 1206 tests, 8 projections over one inode table |
| 2026-08-25 | S1_SELECTED | hard gates pass; Track A HIGH_RISK (monorepo-relative test imports) -> plan Track B generated oracle |
| 2026-08-25 | S2_SPEC_DONE | spec_v1 written; every claim grounded by executing memfs@4.68.1 (probes incl. traps: mkdir recursive return, unlink-dir EPERM, copyFile mode reset, toJSON link flattening); circular symlinks excluded (reference hangs) |
| 2026-08-25 | S3A_IMPORT_AUDIT | Track A empty: upstream tests import '../index' and @jsonjoy.com workspace packages; 0 portable files -> Track B |
| 2026-08-25 | S3B_GENERATE | generated 99 tests (73 atomic / 22 integration / 4 system_e2e), all values observed from memfs@4.68.1 |
| 2026-08-25 | S3B_DUMMY | inert full-surface stub passes 0/99 (5 weak tests strengthened with positive assertions first) |
| 2026-08-25 | S3B_REFERENCE | pinned release passes 99/99 local vitest; tsc --noEmit clean |
| 2026-08-25 | S3_DONE | lint LINT_PASS; artifacts written (kept_nodeids, taxonomy, spec_test_map, reference_score, depends_on 26/26); packet staged |
