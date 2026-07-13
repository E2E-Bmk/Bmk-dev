# Judge Diagnosis Report - boltons-coreutils-fullrepro-001

Date: 2026-07-04
Task: `boltons-coreutils-fullrepro-001`
Candidate: `candidate-runs/codex-boltons-coreutils-specv4-20260630-002`
Oracle version: `20260704-expanded-86`
Verdict: `QUALIFIED`

## Preflight output

Command:

```powershell
$env:PYTHONPATH='G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-boltons-coreutils-specv4-20260630-002\output'; python -c "import boltons; print(boltons.__file__)"
```

Literal output:

```text
G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-boltons-coreutils-specv4-20260630-002\output\boltons\__init__.py
```

The import provenance resolves inside the candidate solution directory, so score values below are eligible for inspection.

## Gate Summary

Task state is `S5_JUDGE`. The expanded active oracle has 86 scoreable nodeids, which clears the normal Stage 3 floor and supersedes the previous rejected 38-test rescope. The scoring set is mixed upstream plus generated public carrier tests, not generated-only, so Gate C is not mandatory; generated additions were still spot-checked under Gate A because they repair prior coverage gaps.

Hard-check verdicts:

| check | finding | verdict |
|---|---|---|
| Role boundary | Judge only read artifacts and wrote this diagnosis report; no oracle, score, candidate, pipeline, task, or weakness-table files were modified. | pass |
| Anti-cheat | Preflight import points into candidate `output/`; targeted scan of candidate `output/` found no forbidden artifact references. Available prompt states cleanroom source was only copied `spec.md`. Score-report/oracle-worktree references in the candidate-run directory are evaluator artifacts, not implementation evidence. | pass |
| Solvability | Reference evidence passes the expanded oracle at 86/86 on Linux/WSL. | pass |
| Fairness | Sampled tests are traceable to exact spec headings and check public behavior. Candidate failures cluster on documented public API behavior, not private internals. | pass with minor caveat |
| Coverage | Expanded oracle covers the previously blocking Cache Key Construction, FrozenDict, iterutils, and urlutils surfaces. Only secondary/convention or alias-equivalence coverage remains thin. | partial acceptable |

Final decision: `QUALIFIED`.

## Solvability

Reference evidence: `wip/boltons-coreutils-fullrepro-001/filter/reference_score_expanded_20260704.json`

Reference run platform: `Linux-5.15.153.1-microsoft-standard-WSL2-x86_64-with-glibc2.29`

Reference result: 86/86 passed.

By layer:

| layer | passed | failed | total |
|---|---:|---:|---:|
| atomic | 37 | 0 | 37 |
| integration | 25 | 0 | 25 |
| system_e2e | 24 | 0 | 24 |

This satisfies the reference ceiling requirement. The reference import path recorded by the score file is the source repo package under `repo-pool`, as expected for reference scoring, while the oracle carrier is isolated and contains no `boltons/` package.

## Candidate Score

Candidate evidence: `candidate-runs/codex-boltons-coreutils-specv4-20260630-002/score_expanded_20260704.json`

Candidate result: 78/86 passed.

By layer:

| layer | passed | failed | total |
|---|---:|---:|---:|
| atomic | 37 | 0 | 37 |
| integration | 23 | 2 | 25 |
| system_e2e | 18 | 6 | 24 |

Failing nodeids:

- `tests/test_cacheutils.py::test_callable_cached_dec`
- `tests/test_cacheutils.py::test_cachedmethod`
- `tests/test_cacheutils.py::test_min_id_map`
- `tests/test_cacheutils.py::test_threshold_counter`
- `tests/test_dictutils.py::test_update`
- `tests/test_dictutils.py::test_reversed`
- `tests/test_dictutils.py::test_ior`
- `tests/test_dictutils.py::test_many_to_many`

## Gate A - Spec Mapping Spot-Check

| nodeid | assertion summary | spec_section | verdict |
|---|---|---|---|
| `tests/test_cacheutils.py::test_lri` | on-miss generation, cache capacity, insertion order, and reinsertion eviction behavior | "### `LRI`" | derivable |
| `tests/test_cacheutils.py::test_cachedmethod` | instance cache providers, attribute-name providers, bound/unbound method callability, shared unscoped cache behavior | "### `cachedmethod`" | derivable |
| `tests/test_dictutils.py::test_many_to_many` | bidirectional link consistency, inverse mutation, removal, replacement, iteration, and equality | "### `ManyToMany`" | derivable |
| `wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_make_cache_key_kwargs_are_order_independent` | keyword argument order does not change the generated cache key | `### Cache Key Construction` | derivable |
| `wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_frozendict_hash_error_for_unhashable_values` | hashing a `FrozenDict` with unhashable values raises `FrozenHashError` | "### `FrozenDict` and `FrozenHashError`" | derivable |
| `wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_chunked_basic` | `chunked` groups input into fixed-size chunks and preserves a shorter final chunk | `### Chunking and Windows` | derivable |
| `wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_url_navigate_relative` | relative URL navigation resolves against the base URL path | "### `URL`" | derivable |
| `wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_find_all_links_with_text` | link extraction with `with_text=True` preserves surrounding text and inserts `URL` objects | `### Link Extraction` | derivable |

The sampled rows quote exact spec headings and their expected outcomes are derivable from `spec_v4.md` without private implementation knowledge.

## Gate B - Failure Pattern Audit

The candidate failures are valid model-failure evidence. They test observable public behavior documented in the spec.

| cluster | affected tests | dimension | finding |
|---|---|---|---|
| Cache decorator wrapper/descriptor edges | `test_callable_cached_dec`, `test_cachedmethod` | `api-surface` | `cached` wrapper repr must be useful/non-crashing for callable cache use, and `cachedmethod` must support public bound and unbound call behavior. Candidate raises `AttributeError`/`TypeError`. |
| Live-object ID map iteration | `test_min_id_map` | `api-surface` | Spec says iteration exposes live mappings. Candidate iteration yields tuple-shaped entries where the public iteration contract expects live objects. |
| ThresholdCounter lifecycle | `test_threshold_counter` | `state-management` | Candidate common/uncommon compaction and containment behavior diverges after updates and later additions. |
| OrderedMultiDict replacement/update behavior | `test_update` | `state-management` | Candidate self-update creates duplicate observable pairs, violating replacement/idempotence semantics. |
| OrderedMultiDict reverse iteration and union | `test_reversed`, `test_ior` | `api-surface` | Candidate omits public reverse iteration and in-place union/update support. |
| ManyToMany inverse relation equality | `test_many_to_many` | `cross-view-consistency` | Candidate `.inv` does not compare as the visible inverse relation, breaking a public cross-view consistency property. |

Cascade analysis: 8 failing nodeids reduce to about 7 root causes. The failures are not dominated by a missing module, missing import, or one primitive cascade. The cross-view signal is narrow but real in `ManyToMany`.

## Gate D - Coverage Gap Audit

The expanded map covers all core module H3 behavior groups that were blocking in the prior rescope: cache key construction, FrozenDict, iterutils, and urlutils now have active scoreable rows. Remaining thin spots are secondary or convention-level.

| spec section | uncovered behaviors | impact | recommendation |
|---|---|---|---|
| `## Package Layout` | No dedicated import smoke row for every public import listed in the opening section. Existing scoreable tests import the required modules and many public names indirectly. | secondary | Accept as indirect coverage; optional future import-surface smoke test. |
| `## General Conventions` | Broad dict-like interoperability and exception-message non-contract conventions are covered indirectly rather than mapped as standalone rows. | secondary | Accept as convention coverage through behavioral sections. |
| "### `FastIterOrderedMultiDict`" | No direct row constructs this alias/class. Its only documented contract is observable equivalence to `OrderedMultiDict`. | secondary | Optional future generated carrier can instantiate it directly; not a core invariant gap because OMD behavior is heavily covered. |
| `## Non-Goals` | Non-goal constraints are not directly scored. | non-scoreable | No action. |

Coverage verdict: `PARTIAL` but acceptable. No core invariant, state lifecycle, error-semantics, iterutils, or urlutils behavior section is empty after expansion.

## Protocol Issues

No blocking protocol issue found.

The generated selected rows are simple public carriers with expected values derivable from the spec. They do not assert private linked-list fields, private URL regexes, exact exception-message wording, or implementation-specific repr text. Upstream retained failures include a repr-related assertion in `test_update`, but the observed diff demonstrates a public duplicate-pair state bug; the failure is not merely exact repr formatting.

## Labels

- `qualified-expanded-oracle`
- `discriminating`
- `partial-secondary-coverage`
- `cross-view-consistency-signal`
- `api-surface-failures`
- `state-management-failures`

## Weakness Table Note

The task-judge skill normally appends weakness-table rows for observed model failures. This run's user instructions explicitly forbade modifying `weakness_table.md`, so this report records the weakness dimensions instead of writing that artifact.

## Final Judge Verdict

`QUALIFIED` - the expanded 86-test oracle is reference-solvable, clears the scoreable-test floor, repairs the prior Gate D gaps, and produces meaningful candidate failure evidence without cheat or fairness blockers.
