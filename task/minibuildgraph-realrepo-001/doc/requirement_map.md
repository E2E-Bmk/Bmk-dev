# MiniBuildGraph Unit/System Requirement Map

Date: 2026-06-20

Public packet: `prd.md`
Rubric: `rubric.json`

## Public Requirements

| ID | Capability | Public packet section | Observable behavior |
| --- | --- | --- | --- |
| `REQ-load-success` | Successful graph loading | Loading | `LOAD path` parses a module file and prints `OK` |
| `REQ-load-replaces-graph` | Graph replacement | Loading, Global Invariants | A successful `LOAD` replaces the entire current graph |
| `REQ-load-error-atomicity` | Failed load recovery | Loading, Error Behavior and Recovery | Failed `LOAD` reports `ERR ...` and preserves the previous graph |
| `REQ-load-duplicate-error` | Duplicate module rejection | Loading, Module Definition Format | Duplicate module names make `LOAD` fail |
| `REQ-load-unresolved-ok` | Unresolved references allowed | Loading, Module Definition Format | Unresolved dependencies do not prevent loading |
| `REQ-list-sorted` | Module listing | Listing Modules | `LIST` prints module names in lexicographic order |
| `REQ-info-basic` | Module info | Module Info | `INFO name` prints `name=`, `type=`, and sorted `deps=` |
| `REQ-deps-basic` | Direct dependency query | Direct Dependencies | `DEPS name` prints direct dependencies |
| `REQ-deps-sorted` | Sorted direct dependency output | Direct Dependencies, Module Info | Direct dependencies are printed lexicographically |
| `REQ-rdeps-basic` | Reverse dependency query | Reverse Dependencies | `RDEPS name` prints direct reverse dependencies |
| `REQ-rdeps-sorted` | Sorted reverse dependency output | Reverse Dependencies | Reverse dependencies are printed lexicographically |
| `REQ-query-consistency` | Consistent graph views | Global Invariants | `INFO`, `DEPS`, and `RDEPS` agree on the same directed edges |
| `REQ-transitive-basic` | Transitive dependency query | Transitive Dependencies | `TRANSITIVE name` prints recursive dependencies |
| `REQ-rtransitive-basic` | Transitive reverse query | Transitive Reverse Dependencies | `RTRANSITIVE name` prints recursive reverse dependencies |
| `REQ-transitive-dedup` | Traversal deduplication | Transitive Dependencies | Recursive traversal prints each reachable name at most once |
| `REQ-transitive-cycle-safe` | Cycle-safe dependency traversal | Transitive Dependencies | Traversal terminates on cycles and does not print the start node as its own dependency |
| `REQ-rtransitive-cycle-safe` | Cycle-safe reverse traversal | Transitive Reverse Dependencies | Reverse traversal terminates on cycles and does not print the start target as its own reverse dependency |
| `REQ-cycle-detect` | Cycle detection | Cycle Detection | `CHECK_CYCLES` prints `CYCLE` or `ACYCLIC` |
| `REQ-unresolved-basic` | Unresolved dependency reporting | Unresolved Dependencies | `UNRESOLVED` prints referenced but undefined dependency names |
| `REQ-unresolved-sorted` | Sorted unresolved output | Unresolved Dependencies | Unresolved names are printed lexicographically |
| `REQ-rdeps-unresolved-target` | Reverse query for unresolved target | Reverse Dependencies | An unresolved referenced name can be queried with `RDEPS` |
| `REQ-rtransitive-unresolved-target` | Reverse transitive query for unresolved target | Transitive Reverse Dependencies | An unresolved referenced name can be queried with `RTRANSITIVE` |
| `REQ-remove-basic` | Module removal | Removing Modules | `REMOVE name` deletes a known module and prints `OK` |
| `REQ-unresolved-after-remove` | Removal creates unresolved references | Removing Modules | References to a removed module become unresolved dependencies |
| `REQ-remove-error-atomicity` | Failed remove recovery | Removing Modules, Error Behavior and Recovery | Failed `REMOVE` reports an error and preserves the graph |
| `REQ-error-invalid-command` | Invalid command error | Error Behavior and Recovery | Invalid commands print `ERR invalid command` |
| `REQ-error-unknown-module` | Unknown module error | Error Behavior and Recovery | Unknown module queries print `ERR unknown module` |

## Unit Coverage

| Test | Feature | Requirement refs | Public basis |
| --- | --- | --- | --- |
| `MBGU001` | load/list | `REQ-load-success`, `REQ-list-sorted` | Load a graph and list modules |
| `MBGU002` | info | `REQ-info-basic`, `REQ-deps-sorted` | Print module metadata and sorted deps |
| `MBGU003` | direct dependencies | `REQ-deps-basic`, `REQ-deps-sorted` | Query direct dependencies |
| `MBGU004` | reverse dependencies | `REQ-rdeps-basic`, `REQ-rdeps-sorted` | Query direct reverse dependencies |
| `MBGU005` | transitive dependencies | `REQ-transitive-basic`, `REQ-transitive-dedup` | Recursive dependency traversal |
| `MBGU006` | transitive reverse dependencies | `REQ-rtransitive-basic`, `REQ-transitive-dedup` | Recursive reverse traversal |
| `MBGU007` | unresolved dependencies | `REQ-unresolved-basic`, `REQ-load-unresolved-ok` | Unresolved references are reported after load |
| `MBGU008` | cycle detection | `REQ-cycle-detect` | Detect a simple dependency cycle |
| `MBGU009` | removal | `REQ-remove-basic`, `REQ-unresolved-after-remove` | Removed modules disappear and remaining references become unresolved |
| `MBGU010` | failed load recovery | `REQ-load-error-atomicity`, `REQ-list-sorted` | Failed load preserves the previous graph |
| `MBGU011` | duplicate modules | `REQ-load-duplicate-error` | Duplicate module names reject the load |
| `MBGU012` | errors | `REQ-error-invalid-command`, `REQ-error-unknown-module` | Stable invalid-command and unknown-module errors |

## System Coverage

| Test | system_dimension | Crossed modules | Requirement refs | Public basis |
| --- | --- | --- | --- | --- |
| `MBGS001` | `state_accumulation` | load -> list -> load -> list | `REQ-load-success`, `REQ-load-replaces-graph`, `REQ-list-sorted` | Successful load replaces previous graph state |
| `MBGS002` | `global_invariant` | info -> deps -> rdeps | `REQ-info-basic`, `REQ-deps-basic`, `REQ-rdeps-basic`, `REQ-query-consistency` | Direct and reverse views agree on the same graph |
| `MBGS003` | `cross_feature_dataflow` | direct edges -> transitive -> reverse transitive | `REQ-transitive-basic`, `REQ-rtransitive-basic`, `REQ-transitive-dedup` | Parsed edges feed recursive traversal |
| `MBGS004` | `boundary_crossing` | unresolved -> rdeps -> rtransitive | `REQ-unresolved-basic`, `REQ-rdeps-unresolved-target`, `REQ-rtransitive-unresolved-target` | Unresolved targets still participate in reverse queries |
| `MBGS005` | `error_atomicity` | remove -> unresolved -> rdeps | `REQ-remove-basic`, `REQ-unresolved-after-remove`, `REQ-rdeps-unresolved-target` | Removing a module updates unresolved and reverse views |
| `MBGS006` | `global_invariant` | cycle check -> transitive -> reverse transitive | `REQ-cycle-detect`, `REQ-transitive-cycle-safe`, `REQ-rtransitive-cycle-safe` | Cycle traversal terminates and preserves start-node exclusion |
| `MBGS007` | `error_atomicity` | load -> failed load -> list | `REQ-load-error-atomicity`, `REQ-list-sorted` | Failed load preserves previous graph queries |
| `MBGS008` | `operation_order_sensitivity` | load -> remove -> unresolved -> replacement load | `REQ-remove-basic`, `REQ-load-replaces-graph`, `REQ-unresolved-basic` | Later load clears earlier removal/unresolved state |
| `MBGS009` | `operation_order_sensitivity` | load -> list/deps/unresolved sorting | `REQ-list-sorted`, `REQ-deps-sorted`, `REQ-unresolved-sorted` | Output order remains deterministic across query types |
| `MBGS010` | `error_atomicity` | load -> failed remove -> list | `REQ-remove-error-atomicity`, `REQ-error-unknown-module`, `REQ-list-sorted` | Failed remove preserves graph state |

System dimension coverage:

- `cross_feature_dataflow`: `MBGS003`
- `state_accumulation`: `MBGS001`
- `global_invariant`: `MBGS002`, `MBGS006`
- `error_atomicity`: `MBGS005`, `MBGS007`, `MBGS010`
- `operation_order_sensitivity`: `MBGS008`, `MBGS009`
- `boundary_crossing`: `MBGS004`

## Reference And Model Verification

Pending. To match the strict `Bmk-dev` core-strong bar, a reference solution should score 100% unit and 100% system, and at least one fresh candidate run should show unit score greater than system score with a gap of at least 15 percentage points.

## Fairness Notes

- The benchmark does not require AOSP, Soong evaluation, repo, git, Docker, network access, or a full Android checkout.
- Module files use a deliberately small block format instead of full Android Blueprint syntax.
- Load parse errors are checked by stable `ERR` shape and graph-preservation behavior, not by exact wording.
- Query outputs are line-oriented and deterministic, usually lexicographic by module name.

## Strengthening Pass 2026-06-21

Additional cases were added after comparing this task with the official core examples in `Bmk-dev`:

- `MBGU013` checks the acyclic branch of cycle detection.
- `MBGU014` checks forward references inside one loaded graph.
- `MBGU015` checks that removal drops outgoing edges from the removed module.
- `MBGU016` checks malformed dependency-list rejection.
- `MBGS011` checks unresolved dependencies across transitive and reverse-transitive queries.
- `MBGS012` checks duplicate-load error atomicity against a previous valid graph.

This brings MiniBuildGraph to 16 unit cases and 12 system cases, matching the scale used by stronger official tasks while keeping all state setup through public `LOAD` commands.

## Model-Gap Strengthening Pass 2026-06-21

After running Doubao-Seed-2.0, DeepSeek-V4-Pro, and GPT-5.5 candidates, MiniBuildGraph was strengthened with additional public-behavior system cases:

- `MBGS013` checks that a trailing dependency comma fails atomically and preserves later `INFO` behavior.
- `MBGS014` checks that an empty file cannot silently replace a valid graph.
- `MBGS015` checks that top-level garbage fails without clearing unresolved dependency state.
- `MBGS016` checks that malformed reloads after `REMOVE` preserve the already-mutated graph state.

These cases all exercise the existing PRD invariant that failed `LOAD` operations must preserve the previous graph unchanged. They use only public `LOAD`, query, and `REMOVE` commands and do not depend on private reference file formats.
