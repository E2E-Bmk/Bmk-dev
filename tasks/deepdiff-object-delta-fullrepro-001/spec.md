# DeepDiff Object Delta Specification

## Product Overview

DeepDiff compares arbitrary Python values and exposes structured differences
for mappings, ordered iterables, sets, tuples, and ordinary objects. Related
public APIs search nested values, extract values by DeepDiff paths, hash
content, and apply or serialize deltas.

The durable contract in this package is semantic: result categories, stable
path strings, old and new values where the selected view exposes them,
container membership, policy options, search matches, and successful delta
reconstruction.

## Scope

The covered surface includes:

- `deepdiff.DeepDiff` text and tree views
- nested dictionaries, lists, tuples, sets, and simple custom objects
- value changes, additions, removals, type changes, affected paths, and root keys
- `include_paths`, `exclude_paths`, regular-expression exclusions, and ignore-order behavior
- repetition reporting, significant digits, math epsilon, case handling, and numeric type policy
- custom operators from `deepdiff.operator`
- `DeepSearch`, `grep`, `parse_path`, and `extract`
- `DeepHash` content stability
- `Delta` application, bidirectional reversal, semantic dictionary projections, and deterministic bytes serialization
- builtin JSON projections for diff results

The examples use in-memory values and public imports. Tests avoid optional
command-line integrations, multiprocessing, network integrations, and
implementation-specific data structures.

## Public Import Surface

The expected imports are:

```python
from deepdiff import DeepDiff, DeepHash, DeepSearch, Delta, extract, grep, parse_path
from deepdiff.operator import BaseOperator, PrefixOrSuffixOperator
```

`BaseOperator` receives a comparison level in its documented callback methods.
The callback may accept or reject a matched comparison; accepted comparisons
are omitted from the resulting difference.

## Product State Model

A `DeepDiff` result is a mapping whose keys are change categories such as
`values_changed`, `type_changes`, `dictionary_item_added`,
`dictionary_item_removed`, `iterable_item_added`, `iterable_item_removed`,
`set_item_added`, `set_item_removed`, and `repetition_change`.

Text-view paths are strings rooted at `root`, with dictionary keys represented
by bracketed quoted keys and sequence indexes by brackets. Tree-view entries
provide path objects whose public `path()` projection is equivalent to the
text-view path.

`Delta(diff)` stores an applicable change set. Adding it to a source value
returns a reconstructed value without changing the source by default.
Bidirectional deltas retain enough information to apply the reverse change.

## Error Semantics

The package asserts normal public Python behavior and avoids matching
incidental exception text. Unsupported optional surfaces are outside scope.
Delta reversal is exercised only with `bidirectional=True`; ordinary deltas
are forward patches. JSON projection is exercised with builtin-compatible
values or an explicit public `default_mapping`.

## Cross-View Invariants

1. Equal nested values produce an empty semantic diff even when set iteration order differs.
2. A changed leaf has a stable path and, in the normal text view, old and new values.
3. Include and exclude policies constrain the same nested comparison space.
4. Ignore-order comparison separates reordering from repetition changes.
5. Tree-view paths and text-view paths identify the same changed leaves.
6. `affected_paths` and `affected_root_keys` project the changes already present in the result.
7. Search and grep return paths that can be consumed by `extract`.
8. Applying a Delta reconstructs the target value while preserving the source unless mutation is requested.
9. A serialized Delta can be restored and applied without changing its semantic result.
10. Hash equality and an empty diff agree for equal nested content.

## Representative Workflows

Compare a nested payload and use its reported path:

```python
left = {"payload": {"items": [{"status": "new"}]}}
right = {"payload": {"items": [{"status": "ready"}]}}
diff = DeepDiff(left, right)
path = next(iter(diff["values_changed"]))
assert extract(right, path) == "ready"
```

Create and replay a Delta:

```python
left = {"count": 1, "items": [1, 2]}
right = {"count": 2, "items": [1, 3, 4]}
payload = Delta(DeepDiff(left, right)).dumps()
assert Delta(payload) + left == right
```

Search and extract a matched value:

```python
value = {"records": [{"role": "admin"}]}
matches = value | grep("admin")
assert extract(value, next(iter(matches["matched_values"]))) == "admin"
```

## Non-Goals

- network access, sockets, services, credentials, databases, and host state
- optional CLI behavior and external file or process integrations
- timing, performance, multiprocessing, and worker scheduling behavior
- private implementation modules, upstream test helpers, and source-test imports
- exact incidental ordering of unordered result containers
- whole-output snapshots, incidental exception messages, pickle security policy,
  or arbitrary unsupported custom-object serialization

## Invocation Protocol

Expose the pinned `deepdiff` source checkout or install it into the execution
environment, install the requirements listed in the package requirements file,
and run pytest against the two public test modules from this task directory.
The tests are local and deterministic and require no network.

## Environment

Run on Linux with Python 3.11 without network access. Python 3.10 is also
used for compatibility replay. The target package is not pre-installed; the
runner supplies the pinned checkout or its installation. Required packages
are `pytest`, `pytest-json-report`, `orderly-set`, and `cachebox`. No service
credentials, endpoints, databases, sockets, or optional CLI dependencies are
required.

## Evaluation Notes

Assertions prefer semantic category membership, path projections, values,
types, container equality, search results, and Delta reconstruction. They do
not require exact incidental exception strings or unordered whole-output
snapshots. The package deliberately excludes optional and nondeterministic
surfaces where a fair local contract would be difficult to establish.

Current evidence is same-process local replay only. It does not establish a
trusted black-box Stage 4 runner, an external signature, or final QUALIFIED
status. The package remains ARTIFACT_ONLY with no fabricated score or
qualification claim.
