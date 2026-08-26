# rewrite_audit — tanstack-table-core-engine-fullrepro-001

Upstream test root: /tmp/repos/tanstack-table/packages/table-core/tests (tag @tanstack/table-core@9.1.2,
commit ff7653dad0bf1525ed8c3e8d6fe2e64c64e8a280). 63 .test.ts files, 1311 it/test blocks, 24069 LOC.

## Import classification (file level)

Every one of the 63 test files falls into at least one non-portable class:

| class | evidence | count | action |
|---|---|---|---|
| library internal (bidirectional): `import ... from '../../../../src'` | all unit + implementation tests construct tables through the repo source tree, not the published package | 63/63 | discard |
| library internal (bidirectional): `import { column_*, table_* } from '../../../../src/static-functions'` | unit tests drive behavior through internal static functions (e.g. `column_toggleSorting`, `table_setSorting`) that the published package does not export from its root | ~40/63 | discard |
| upstream test infrastructure: `tests/fixtures/*` (features.ts, data factories) and `tests/helpers/testUtils.ts` | shared fixture bag `testFeatures` bundles every feature incl. out-of-scope ones (sizing, resizing, row pinning, cell spanning) | ~55/63 | discard |
| out-of-scope module: worker/serialization, flex-render, declaration-emit, performance | behavior this spec excludes | 8/63 | discard |

## Rewrite feasibility

- The `src/static-functions` entry is the load-bearing import for the unit suite: assertions
  target internal static functions and their memoization wrappers. Rewriting those tests to the
  public instance API changes what each test verifies (Q1: a correct reimplementation with a
  different internal decomposition would fail the originals; the rewrite is a different test).
- The remaining implementation tests rely on `testFeatures` (all 17 stock features + all row
  models + all fn registries) and person-fixture factories; porting them drags out-of-scope
  features (sizing/resizing/row-pinning/cell-spanning) into every construction call.
- Zero files import `@tanstack/table-core` by its published name; there is no subset importable
  against the installed package.

rewrite_result: fail for all 63 files.
failure_reason (uniform): module-level imports resolve only inside the upstream repo source tree
(`../../../../src`, `../../../../src/static-functions`, `tests/fixtures`, `tests/helpers`); the
behavioral intent of the unit layer is bound to internal static functions the published package
does not expose as public API.

## Decision

Track A yields 0 portable files (100% discard > 50% early-trigger threshold) → Track B
generated oracle against the installed `@tanstack/table-core@9.1.2` package, same precedent as
immer-immutable-state-fullrepro-001 and yjs-crdt-sync-engine-fullrepro-001.

functions_in_scope (Track A): 0
