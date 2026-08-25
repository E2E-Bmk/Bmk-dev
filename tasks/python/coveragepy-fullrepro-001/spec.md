# Coverage measurement, data, and publication contract

Implement a `coverage` package that measures Python execution, persists and
combines measurement data, filters by context, reads project configuration, and
publishes reports through public Python and command-line interfaces.

The contract is behavioral. Private module layout, database schema and byte
encoding, tracer implementation, C-extension availability, cache internals,
and cosmetic report styling are outside scope.

## Public surface and data model

The package exposes non-empty version metadata, `Coverage`, `CoverageData`,
plugin and reporter base classes, startup support, and distinguishable public
exceptions for configuration, data, source, code, and plugin failures. A
Coverage instance provides public run and report options, independent exclude
and partial-pattern lists, collection lifecycle operations, access to its data,
and report entry points.

A CoverageData object has one established mode: lines or arcs. Adding line data
establishes line mode; adding arc data establishes arc mode. Mixing modes in one
object or through an update/combine operation is rejected without changing the
established state. Repeated values are deduplicated. Entry and exit arcs,
including negative endpoints, remain observable.

Measured-empty and unknown files are distinct. A measured-empty file belongs to
the measured-file set and returns an empty payload; an unknown file returns no
payload. Touch operations establish measured-empty files only after the data
mode is known. Batch touch behaves like the equivalent individual operations.

Source-file identity is canonical at the public data boundary. Equivalent path
spellings identify one measured file rather than parallel records. The same
identity is used by payload, context, tracer, touch, purge, update, combine, and
report operations, and it remains stable after serialization and reload.

File-tracer metadata has three states: a named tracer, an explicit empty tracer
for a known ordinary file, and no tracer value for an unknown file. Repeating
the same mapping is idempotent. A conflicting mapping is rejected without
replacing the prior value.

Purge clears a selected file's line or arc payload and its per-line context
associations while retaining measured identity and tracer metadata. Other files
are unchanged. Erase clears the complete in-memory or on-disk generation.
Public serialization and reload preserve mode, payload, contexts,
measured-empty identities, and tracer states.

## Context selection

Measurement may associate static and dynamic context names with executed data.
Context names and per-line associations survive write, reload, update, combine,
and serialization when the containing operation succeeds.

Exact selection and regular-expression selection are separate operations. An
exact selector treats every character literally, even when the value contains
characters meaningful to a regular-expression engine. Regex selection accepts
multiple expressions and exposes the union of matching contexts. Resetting the
query restores the unfiltered data view. File lists, lines or arcs, context
projections, analysis, and reports must all reflect the same active query.

## Transactional update and combine

Compatible updates merge file, payload, context, and tracer unions. Repeating
the same update is idempotent. An incompatible data mode or tracer conflict is
a transaction failure: destination mode, serialized bytes, measured files,
payload, contexts, and tracers remain as they were before the attempt, and the
source operand is unchanged.

Combining on-disk shards uses the same transaction boundary across the complete
selected input set. A late incompatible or corrupt shard must not publish a
partial destination, consume earlier successful shards, or rewrite any input.
Only a fully compatible combine may publish the new aggregate. Successful
default combine may remove consumed inputs; keep mode retains them. Discovery
order does not affect the resulting logical data.

## Configuration origins

Configuration can be supplied explicitly or discovered by ordinary project
rules. Relative paths declared in a configuration file are anchored at the
directory containing that file, not at the process working directory. This
origin applies consistently to data files, source roots, include and omit
patterns, parallel data, and report destinations.

Environment expansion occurs before canonical path projection. Moving the
process working directory between measurement, combine, and reporting does not
rebase settings declared by the same configuration file. Python and CLI views
must agree on the resulting data, source, and output locations.

## Collector ownership and recovery

`Coverage.current()` identifies the active collecting instance only while that
instance owns collection. Nested collectors form an ownership stack. Normal
exit restores the prior owner. Body, stop, tracer, or context-manager failures
still unwind the failed owner's state and restore the prior owner before the
failure is returned.

After every failed collection generation, no stale current collector, tracer,
or pending data transaction may remain. A fresh later generation must be able
to start, collect, stop, save, and report normally. Cleanup must not replace the
original operation failure with an unrelated stale-ownership failure.

## Measurement and report publication

Python measurement, CLI run, save/reload, analysis, text reports, and structured
reports must agree on measured files, executed data, contexts, and totals.
Reporting is observational with respect to measurement data.

A report destination is published atomically. If rendering, source reading,
encoding, or finalization fails, a pre-existing file or directory destination
remains byte-for-byte intact and no half-written generation is exposed. A
successful multi-file report replaces its destination as one coherent
generation. Temporary publication artifacts and data resources are closed on
both success and failure.

## Compatibility boundary

Public operations either return normally with the documented projection or
raise an appropriate public exception. Collection, process crashes, warnings,
partial setup, and missing public symbols are not substitutes for behavior.
Implementations may choose any internal architecture that preserves these
rules across varied filenames, context names, shard orders, configuration
locations, working directories, failure points, and report formats.
