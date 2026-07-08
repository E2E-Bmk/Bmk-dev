# DiskCache Spec v3 Cleanroom Stage 5 Diagnosis

Verdict: **QUALIFIED**

This is a fresh Stage 5 judgment for `/Users/zijian/Bmk-dev-main/candidate-runs/codex-diskcache-spec_v3-2026-07-03-run1`. It uses the spec_v3 public packet and the current filter_v3 artifacts only. No task migration was performed.

## Anti-Cheat And Preflight

The required import provenance preflight was run before opening or quoting any score JSON.

Preflight output:

```text
/Users/zijian/Bmk-dev-main/candidate-runs/codex-diskcache-spec_v3-2026-07-03-run1/solution/diskcache/__init__.py
```

The provenance points into the cleanroom candidate solution, not the source repo or an installed package. Stage 4 scoring also used `--remove-path diskcache`, so pytest could not accidentally import the target package from the copied upstream worktree.

Anti-cheat scan: no independent trajectory/transcript artifact exists in the run directory. The available cleanroom prompt instructs the candidate to read only `public_packet/spec.md` and write only under `solution/`. A static scan of `task_prompt.txt`, `public_packet/`, and `solution/` found no references to `repo-pool`, `spec_test_map`, `kept_nodeids`, score reports, oracle worktrees, upstream test paths, or target-package install commands. No cheat is detected from available artifacts.

## Reference Pass And Environment

Reference full score: 148 / 148 passed, pass rate 1.0.

Reference non-Django score: 100 / 100 passed, pass rate 1.0.

Layer ceiling:

| layer | passed | total |
|---|---:|---:|
| atomic | 74 | 74 |
| integration | 60 | 60 |
| system_e2e | 14 | 14 |

Environment notes: scoring used run-local eval dependencies, `-o addopts=` to neutralize upstream tox addopts, and candidate `--remove-path diskcache`. The eval dependency directory name contains `spec_v2`, but the import preflight proves it did not supply `diskcache`; it supplied dependencies such as Django. Django audit: eval deps contain Django 6.0.6, whose `BaseCache.__init__` signature is `(self, params)`. The reference implementation passes the same Django environment.

Solvability verdict: **passes**.

## Instrument Validity

Core principle check: the kept set has 148 upstream-only nodeids, all represented in `taxonomy.jsonl`; `spec_test_map.md` reports `oracle_source: upstream_only`, so Gate C does not apply.

Gate A spot-check:

| area | sampled covered rows | result |
|---|---|---|
| Cache | `test_set_twice`, `test_stats`, `test_expire_rows`, `test_least_recently_used`, `test_memoize_ignore` | Headings `### Cache`, `## Cache Behavior`, and `## Cross-View Invariants` exist and predict public file-read, stats, expiration, eviction, and memoization behavior. |
| DjangoCache | `test_simple`, `test_get_many`, `test_cache_versioning_get_set_many`, `test_incr_version`, `test_memoize` | `### DjangoCache` documents backend construction, methods, timeout conversion, key prefix/version behavior, multi-key operations, and memoization. |
| FanoutCache | `test_init`, `test_add_concurrent`, `test_expire`, `test_size_limit_with_files`, `test_reversed` | `### FanoutCache` and `## Sharding Behavior` now document settings, context manager/lifecycle, per-key routing, aggregate operations, size-limit division, and iteration views. |
| Index | `test_getsetdel`, `test_popitem`, `test_state` | `### Index` and persistent container behavior predict mapping order, pop/peek semantics, and persistence/pickle behavior. |
| Recipes | `test_averager`, `test_lock`, `test_semaphore`, `test_memoize_stampede` | `### Recipes` predicts public coordination and memoization recipe behavior, including semaphore release constraints. |

Gate B failure audit: representative failures are behavioral public-contract failures, not internal-shape checks. Examples: non-file `get(read=True)` must return the stored value rather than crash; normal `check()` after ordinary operations should not report self-created empty directories as inconsistencies; FanoutCache should expose settings/reset/aggregate views and be reversible; DjangoCache must construct and operate under the installed Django backend API; BoundedSemaphore must support nested/manual acquire and release behavior. Remaining failures are candidate misses. No filter correction or spec patch is required.

Instrument conclusion: **valid scoring instrument**.

## Candidate Score By Layer

Full candidate score:

| layer | passed | failed | error | total |
|---|---:|---:|---:|---:|
| atomic | 42 | 8 | 24 | 74 |
| integration | 16 | 20 | 24 | 60 |
| system_e2e | 11 | 3 | 0 | 14 |
| total | 69 | 31 | 48 | 148 |

Full pass rate excluding skips: 0.46621621621621623.

Non-Django candidate score:

| layer | passed | failed | error | total |
|---|---:|---:|---:|---:|
| atomic | 42 | 8 | 0 | 50 |
| integration | 16 | 20 | 0 | 36 |
| system_e2e | 11 | 3 | 0 | 14 |
| total | 69 | 31 | 0 | 100 |

Non-Django pass rate excluding skips: 0.69.

Non-pass distribution: `tests/test_djangocache.py` has 48 errors; `tests/test_core.py` has 18 failures; `tests/test_fanout.py` has 12 failures; `tests/test_recipes.py` has 1 failure. `tests/test_index.py` passes completely.

## Protocol Issues And Actions

No current protocol blocker.

- No `filter_correction_request.md` update: sampled failures are spec-driven and behavioral.
- No `spec_patch_request.md` update: spec_v3 already contains the FanoutCache lifecycle/context-manager clarification required by the prior loop.
- No write to `tasks/`: graduation is left to the main thread after review.
- Weakness rows may be appended because the task is QUALIFIED.

## Real Failure Clusters

| cluster | affected tests | primary dimension | diagnosis |
|---|---:|---|---|
| Django backend construction cascade | 48 errors | api-surface | `DjangoCache.__init__` calls `BaseCache.__init__` with two positional arguments, but the installed backend expects a params dict. All Django tests fail before behavioral methods run. This is a candidate miss, not dependency unfairness, because the reference passes the same Django 6.0.6 environment. |
| Cache file-backed/non-file read semantics | 2 failures | atomic-behavior | `get(read=True)` wraps unpickled non-bytes values in `BytesIO`, causing `TypeError` for ints/strings after overwrites. The public behavior requires read support without corrupting ordinary stored values. |
| Cache maintenance, culling, and consistency state | 13 core failures | state-management | Candidate reports self-created empty `files` directories as `EmptyDirWarning`, over-culls near size limits, and mismanages expiration/eviction/cull counts and queue cleanup checks. |
| Memoize ignore key/statistics consistency | 1 failure | cross-view-consistency | `memoize(ignore={1, "arg1"})` does not normalize ignored varargs/kwargs into one cache key, so repeated equivalent calls become misses rather than hits. |
| Fanout public surface and aggregate behavior | 12 failures | api-surface | FanoutCache lacks documented settings attributes, `reset`, `__reversed__`, and correct aggregate size/expiration/tag/stat behavior; concurrency add/incr also does not serialize to the documented atomic outcome. |
| BoundedSemaphore ownership/release lifecycle | 1 failure | state-management | One `_token` slot cannot represent multiple acquisitions by the same semaphore object, so manual acquire/context-manager/release sequences lose ownership state. |

## Cascade Analysis

There are 79 non-passed tests, but they collapse into a smaller set of root causes:

- 48 Django errors are one construction-signature cascade.
- Several Core failures share one false-positive `check()`/empty-directory state root.
- Several Fanout failures share missing public settings/reset/reversed plus incomplete aggregate behavior.
- The remaining roots are independent: read-mode storage, memoize key normalization, size/expiration/culling state, concurrency serialization, and semaphore acquisition accounting.

The task is discriminating: the candidate passes Index and many Cache/Fanout primitives, but fails cross-component lifecycle and persistence details. System_e2e score is not near floor, and most integration misses trace to specific primitive or aggregate roots rather than an entirely unusable implementation.

## Task Labels

`qualified`, `discriminating`, `solvable-reference-clean`, `candidate-django-cascade`, `state-management-signal`, `api-surface-signal`, `cascade-dominated`, `filter_v3-upstream-only`.

## Routing Recommendation

Accept as **QUALIFIED** after main-thread review. Append weakness rows for `codex-cleanroom` / `diskcache` / `spec_v3` / `filter_v3`; do not route back to spec-writer or test-filter, and do not migrate to `tasks/` from this subagent.
