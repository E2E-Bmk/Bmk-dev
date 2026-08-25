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

## Rejected candidates (hard gates)

| repo | gate | detail |
|------|------|--------|
| lucaong/minisearch | src LOC < 3000 | 2940 LOC (src/*.ts, excl. tests) |
| CacheControl/json-rules-engine | src LOC < 3000 | 1474 LOC (src/*.js) |
