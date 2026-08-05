# toolz Functional Utilities

## Product Overview

toolz is a Python library of functional programming utilities for iterable,
mapping, and callable workflows. Its public surface provides lazy sequence
transformations, immutable dictionary projections, function composition,
currying, memoization, and a curried namespace for partial application.

## Scope

This package covers public imports from `toolz` and `toolz.curried`. The
behavior surface includes iterable selection and aggregation, grouping,
partitioning, concatenation, joins, deterministic sampling with an explicit
random state, dictionary merging and transformation, immutable nested updates,
function composition and piping, `juxt`, `curry`, `memoize`, callable adapters,
and composed curried workflows.

## Public Import Surface

Applications may import the documented functions from `toolz`, including
`accumulate`, `groupby`, `merge`, `assoc`, `update_in`, `compose`, `pipe`,
`juxt`, `curry`, and `memoize`. The alternate `toolz.curried` namespace is
also public and exposes curried iterable, dictionary, and functional helpers.
The checks use standard-library callables and runner-created values only.

## Product State Model

Iterable helpers return either materialized values or lazy iterators according
to their public contract. Dictionary helpers return new mappings and preserve
the input mapping. Function helpers represent callable transformations:
composition applies functions in a defined order, `curry` accumulates
arguments until a call is valid, and `memoize` reuses a cached pure result.
Curried helpers expose the same transformations through partial application.

## Error Semantics

The checks cover public exception types only where needed for callable
application and invalid-value behavior. They do not require exact diagnostic
wording. Calls use valid, hashable deterministic values for memoization and do
not assert timing, cache eviction, or implementation-specific internals.

## Cross-View Invariants

Lazy iterable projections agree with their materialized results. Grouped and
reduced views agree on keys and totals. Dictionary transformations preserve
key/value relationships and do not mutate source mappings. Composed and
curried callables produce the same values as their expanded workflows, and
memoized repeated calls preserve output while reducing the pure function call
count.

## Representative Workflows

Representative workflows normalize records, group and reduce scores, merge and
filter mappings, build nested reports, process text tokens, rank records,
replay generator prefixes, and combine curried iterable and dictionary
operations. Each workflow combines multiple public operations over local
values.

## Non-Goals

The package excludes private implementation modules, source tests, network or
socket behavior, filesystem and subprocess behavior, performance measurement,
wall-clock timing, concurrency, unseeded randomness, exact exception text,
serialization details, and brittle whole-output snapshots. It does not infer
behavior from hidden artifacts.

## Invocation Protocol

Run pytest against this package with `--target-root` pointing to the target
checkout. The target root is inserted ahead of other import locations before
test collection. JSON reporting is used only to record local replay results.

## Environment

The reference environment is Linux with Python 3.11 and without network access.
A Python 3.10 replay uses the same deterministic checks. The target package is
not pre-installed; the selected checkout is supplied as the target root.
Required support packages are `pytest` and `pytest-json-report`.

## Evaluation Notes

The recorded results are same-process local replay evidence for this package.
They do not establish a trusted black-box Stage 4 runner, an external
signature, final QUALIFIED status, isolation, or a candidate result. The
package remains an auditable ARTIFACT_ONLY record.
