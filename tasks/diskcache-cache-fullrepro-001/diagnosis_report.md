# Diagnosis Report - codex-diskcache-specv1-20260704-002

## Anti-cheat / Preflight

Command:

```powershell
$env:PYTHONPATH='G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-diskcache-specv1-20260704-002\output'; python -c "import diskcache; print(diskcache.__file__)"
```

Preflight output:

```text
G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-diskcache-specv1-20260704-002\output\diskcache\__init__.py
```

Verdict: PASS. The imported package resolves inside the candidate output directory.

Available candidate-visible artifacts (`task_prompt.txt`, `public_packet/spec.md`, and `output/`) were scanned for forbidden references to `repo-pool`, prior score reports, `kept_nodeids`, `spec_test_map`, generated tests, and `pip install diskcache`; no forbidden candidate-visible access was found. No separate implementation trajectory log was present in this run directory, so the audit is limited to recorded run artifacts plus the import provenance check above.

## Reference Solvability

Reference score: 66/66 passed on Linux/WSL with scorer isolation and `--remove-path diskcache`.

The reference run used the same 66 retained nodeids and completed without collection errors, establishing that the oracle is solvable in the recorded dependency environment.

## Candidate Score

Candidate run: `candidate-runs/codex-diskcache-specv1-20260704-002`

Total score: 63/66 passed.

Layer summary:

| layer | passed | failed | total |
|---|---:|---:|---:|
| atomic | 33 | 2 | 35 |
| integration | 23 | 1 | 24 |
| system_e2e | 7 | 0 | 7 |

## Gate A - Spec Mapping Spot-check

| nodeid | assertion summary | spec_section | verdict |
|---|---|---|---|
| `tests/test_swe_e2e_generated.py::test_cache_set_overwrites_existing_value` | `Cache.set` stores a value and overwrites an existing value. | `Cache Behavior` | derivable |
| `tests/test_swe_e2e_generated.py::test_cache_tag_index_toggle_setting` | `tag_index=True`, `drop_tag_index()`, and `create_tag_index()` expose the public tag-index setting as enabled/disabled values. | `Settings, Constants, and Eviction` | derivable |
| `tests/test_swe_e2e_generated.py::test_cache_persists_across_reopened_objects` | A value written through one `Cache` is visible after reopening the same directory. | `Cross-View Invariants` | derivable |
| `tests/test_swe_e2e_generated.py::test_fanout_named_deque_view_persists_by_name` | `FanoutCache.deque(name)` persists and reopens by name. | `Fanout Behavior` | derivable |
| `tests/test_swe_e2e_generated.py::test_deque_bounded_discards_opposite_end` | A bounded `Deque` discards from the opposite end when over capacity. | `Deque Behavior` | derivable |
| `tests/test_swe_e2e_generated.py::test_index_views_and_equality` | `Index` exposes mapping views and equality behavior consistent with ordered/mapping semantics. | `Index Behavior` | derivable |
| `tests/test_swe_e2e_generated.py::test_bounded_semaphore_release_contract` | Releasing a `BoundedSemaphore` beyond the acquired count raises `AssertionError`. | `Error Semantics` | derivable |
| `tests/test_swe_e2e_generated.py::test_memoize_stampede_caches_result_and_exposes_key` | `memoize_stampede` avoids repeat execution, exposes `__cache_key__`, and stores result plus timing metadata at that key. | `Recipe Behavior` | derivable |

Gate A verdict: PASS. Sampled rows map to exact spec headings and assert public observable behavior.

## Gate B - Failure Pattern Audit

Failing tests:

| nodeid | layer | failure | instrument verdict |
|---|---|---|---|
| `tests/test_swe_e2e_generated.py::test_cache_tag_index_toggle_setting` | atomic | `Cache` has no public `tag_index` attribute. | valid model failure: public setting projection missing |
| `tests/test_swe_e2e_generated.py::test_cache_reset_returns_previous_value_and_updates_setting` | atomic | `Cache` has no public `cull_limit` attribute after `reset("cull_limit", 0)`. | valid model failure: public setting projection missing |
| `tests/test_swe_e2e_generated.py::test_memoize_stampede_caches_result_and_exposes_key` | integration | cache entry at `__cache_key__` is not unpackable as result plus elapsed metadata. | valid model failure: public recipe cache-entry projection diverges |

Gate B verdict: PASS. The failures are not private schema, private helper, repr, or exact exception-message assertions. They concern public settings and public recipe cache entries reachable through documented APIs.

## Gate C - Generated-only Oracle Spot-check

Not applicable. `spec_test_map.md` records `filter/oracle_source: generated_reference_observed`, not `oracle_source: generated_only`.

## Gate D - Coverage Gap Audit

The scoring map has covered rows for all core behavioral sections: `Public API`, `Product State Model`, `Cache Behavior`, `Settings, Constants, and Eviction`, `Fanout Behavior`, `Deque Behavior`, `Index Behavior`, `Recipe Behavior`, `Error Semantics`, and `Cross-View Invariants`.

| spec section | uncovered behaviors | impact | recommendation |
|---|---|---|---|
| `Product Overview`, `Scope`, `Representative Workflows`, `Non-Goals`, `Invocation Protocol`, `Evaluation Notes` | Narrative or boundary material without independent executable behavior beyond the covered API sections. | No scoring risk. | Accept as non-core narrative coverage. |
| `Persistent Containers` parent heading | Parent grouping; concrete `Deque Behavior` and `Index Behavior` child sections are covered. | No core gap. | Accept child-section coverage. |

Coverage verdict: PARTIAL acceptable. No core invariant, error-semantics, or lifecycle section has zero coverage.

## Protocol Issues

No solvability, anti-cheat, or fairness blocker found. The earlier invalid auxiliary run is not used for this verdict; this report evaluates `codex-diskcache-specv1-20260704-002`.

## Real Failure Clusters

1. Public settings projection (`api-surface`, 2 atomic failures)

The candidate supports enough cache behavior to pass most core API tests but does not expose setting values such as `tag_index` and `cull_limit` as public `Cache` attributes after construction, tag-index toggling, or `reset()`.

2. `memoize_stampede` cache entry state (`state-management`, 1 integration failure)

The candidate avoids repeated function execution and exposes a cache key, but the value stored at that key does not match the documented result-plus-timing metadata projection expected through normal cache lookup.

## Cascade Analysis

There are three failing tests rooted in two independent root causes:

- 2 atomic failures from one public settings projection gap.
- 1 integration failure from one recipe cache-entry state gap.

No system_e2e failures are present, and no broad cascade from import failure, missing class, or broken primitive was observed.

## Labels

- `discriminating`: candidate is high but not saturated at 63/66.
- `settings-projection-gap`: failures expose missing public setting attributes.
- `recipe-state-gap`: failure exposes incorrect `memoize_stampede` stored metadata shape.

## Final Verdict

QUALIFIED. The run is strict-legal countable: reference passes 66/66, candidate imports from the candidate output, score is 63/66 with no collection errors, Gate A/B/D pass, Gate C is not applicable, and the terminal task package can include the recorded score and diagnosis.
