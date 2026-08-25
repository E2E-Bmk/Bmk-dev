# TypeScript Stage 1–3 task packets — progress ledger

Branch: `cursor/8-26-50tasks-ts-a9d6`. Deliverable: ACCEPTABLE Stage 1–3 packets
under `staging/{task_id}/` (Definition A). Stage 4/5 (candidate eval, judge) and
Docker-isolated reference scoring are pending on the release side and noted per
task in `task.json.pending`.

Harness note: lint/verification used the TypeScript-aware
`harness/oracle_import_lint.py` / `harness/verify_task.py` (from commit 1161ca4,
branch li-type) with each task registered in `harness/target_imports.py`
locally; per instructions this branch only commits `staging/`, so the parent
coordinates the harness merge. Every packet passes `verify_task` STATIC_VALID
and lint LINT_PASS, its pinned npm reference passes the oracle 100%, and a
stub-package dummy run passes 0 tests.

Duplicate bans checked against `tasks/` on main (74 tasks) and the seven
TypeScript tasks on branch li-type (changesets, changesets-release-graph,
oclif-core, tinybase, typedoc, unstorage, wireit).

## Candidate ledger

| # | task_id | repo | status | oracle (a/i/e2e) | reference | dummy | notes |
|---|---------|------|--------|------------------|-----------|-------|-------|
| 1 | orama-search-engine-fullrepro-001 | oramasearch/orama (@orama/orama@3.1.18) | S3_DONE (packet committed) | 78 (52/23/3) | 78/78 local vitest | 0/78 | full-text engine; filters/facets/groups/sort/persistence |
| 2 | rrule-recurrence-engine-fullrepro-001 | jkbrzt/rrule (rrule@2.8.1) | S3_DONE (packet committed) | 90 (64/22/4) | 90/90 local vitest | 0/90 | RFC 5545 recurrence engine; expansion/string/text/set projections; 3 spec claims corrected from reference execution |
| 3 | kysely-query-compiler-fullrepro-001 | kysely-org/kysely (kysely@0.29.5) | S3_DONE (packet committed) | 96 (70/22/4) | 96/96 local vitest | 0/96 | SQL query compiler; builder AST -> pg/mysql/sqlite compile + plugin/schema transforms + DummyDriver lifecycle; 2 spec claims corrected from reference execution |
| 4 | xstate-statechart-engine-fullrepro-001 | statelyai/xstate (xstate@5.32.5) | S3_DONE (packet committed) | 96 (71/21/4) | 96/96 local vitest | 0/96 | statechart engine; SCXML-style transition selection/microsteps + actor, pure-step, query, persistence, SimulatedClock, completion projections |
| 5 | mobx-reactivity-engine-fullrepro-001 | mobxjs/mobx (mobx@7.0.3) | S3_DONE (packet committed) | 100 (75/21/4) | 100/100 local vitest | 0/100 | reactive graph engine; observables/computed/effects/actions/collections/events/introspection; v7 fresh-major memorization traps probed (observable(primitive) boxes, standalone annotation tokens, enforceActions warns) |
| 6 | chevrotain-parser-toolkit-fullrepro-001 | Chevrotain/chevrotain (chevrotain@13.2.0) | S3_DONE (packet committed) | 98 (73/21/4) | 98/98 local vitest | 0/98 | parser toolkit; tokens/lexer modes/CST/visitors/recovery/validation/GAst/serialization/dts/embedded values; v13 traps probed (content assist removed, onlyOffset drops endOffset, maxLookahead 3) |
| 7 | memfs-inmemory-fs-fullrepro-001 | streamich/memfs (memfs@4.68.1) | S3_DONE (packet committed) | 99 (73/22/4) | 99/99 local vitest | 0/99 | in-memory fs; one inode table projected through sync/callback/promise APIs, JSON snapshots, Stats/Dirents, links, fds, streams; 4.68 monorepo-line traps probed (mkdir recursive returns full path, unlink-dir EPERM, copyFile mode reset, toJSON link flattening); circular symlinks excluded (reference hangs) |
| 8 | tanstack-query-core-cache-engine-fullrepro-001 | TanStack/query (@tanstack/query-core@5.102.4) | S3_DONE (packet committed) | 98 (70/22/6) | 98/98 local vitest x4 | 0/98 | async cache engine; one QueryCache+MutationCache pair projected through imperative client, observers (select/placeholder/initialData/structural sharing), filter algebra + event stream, bulk ops, infinite paging, hydration, key utilities, managers; traps probed (find exact-by-default, Node retry default 0, notify deferred flush, cancel leaves pending/idle); upstream tests non-portable (workspace @tanstack/query-test-utils) -> generated oracle; 2 spec claims corrected from reference execution |
| 9 | prosemirror-model-doc-tree-fullrepro-001 | prosemirror/prosemirror-model (prosemirror-model@1.25.11) | S3_DONE (packet committed) | 100 (74/20/6) | 100/100 local vitest x4 | 0/100 | immutable document-tree model; one schema-governed tree projected through tree algebra, flat positions/ResolvedPos, content-expression automaton (ContentMatch/fillBefore/findWrapping), slice/replace with open depths, mark-set algebra with exclusion, text projection, eq/diff, JSON round trips; traps probed (create(null) fills required attrs with null vs create({}) RangeError, Fragment.from merges same-mark texts, findWrapping [] vs null, marks() boundary takes preceding node, construction-time SyntaxErrors); upstream tests non-portable (prosemirror-test-builder depends on real target) -> generated oracle; DOM projection excluded by non-goal |
| 10 | avsc-avro-type-engine-fullrepro-001 | mtth/avsc (avsc@5.7.9) | S3_DONE (packet committed) | 99 (72/21/6) | 99/99 local vitest x4 | 0/99 | Avro type engine; one compiled type graph projected through construction/registry, validation domains, byte-exact binary codec (zigzag/prefix/block/tag), JSON codec, canonical schema + fingerprint/equals, evolution resolvers (promotions/defaults/aliases/union rules), inference (forValue/forTypes), IDL front end; traps probed (long +/-(2^53-2), float/double accept non-finite, auto mode wraps int|float and int|long but not int|string, resolver bound to creating instance, enum default absorbs unknown symbols, trailing-byte rejection, toString() prints quoted name); upstream tests non-portable ('../lib' relative requires) -> generated oracle; RPC/services + container streams excluded by non-goal; 1 spec claim corrected from execution |

## Rejected candidates (hard gates)

| repo | gate | detail |
|------|------|--------|
| lucaong/minisearch | src LOC < 3000 | 2940 LOC (src/*.ts, excl. tests) |
| CacheControl/json-rules-engine | src LOC < 3000 | 1474 LOC (src/*.js) |
