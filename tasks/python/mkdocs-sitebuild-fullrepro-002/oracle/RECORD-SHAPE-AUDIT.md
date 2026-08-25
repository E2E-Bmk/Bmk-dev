# MkDocs v14 durable-record shape audit

Status: pre-freeze static admission check.

The six recovery-owner JSON files are public operational artifacts.  The
candidate-visible SPEC therefore defines their common envelope and every
required body key, nesting level, and JSON type in ordinary compatibility
terms.  It also states the generation domains, digest representation,
configuration projection (including `effective.plugins`), page/search/event
entry shapes, and which result arrays may be empty.

`RECORD-SHAPE-CONTRACT.json` is the evaluator's private schema registry for
those public laws.  It covers the `config`, `discovery`, `lineage`,
`publication`, `search`, and `outbox` owners, plus the shared envelope,
checksums, digest maps, change sets, page entries, search receipts, and outbox
events.  The registry also freezes the 36 durable paths directly observed by
the semantic oracle and the public collections whose indexed or selected use
requires a prior non-empty check.

`audit_record_shapes.py` validates the registry, confirms that every observed
path exists in the public schema, confirms all six owners are loaded through
the common validator, and verifies that the root and candidate-payload SPEC
are identical and contain every schema marker.  Its AST check rejects raw
subscript access in the oracle outside three small checked helpers.  It also
rejects unchecked `next()` selection, non-literal durable paths, missing
owner coverage, and removal of the public-call `KeyError` translation.

At runtime `owner()` parses each public record, validates the entire envelope
and owner body before returning it, and checks its canonical body checksum.
Every subsequent durable-field access names a preregistered path and traverses
through presence-checked mapping access.  Public list indexing checks type and
length first; searches check both the source list and the match set.  A missing
key, wrong type, or unexpectedly empty observed collection therefore raises
the oracle's assertion mismatch and remains a valid product failure.  An
unattributed raw `KeyError` or `IndexError` escaping evaluator code is still an
invalid harness run.  A `KeyError` raised by a wrapped public MkDocs constructor
or function, or whose traceback enters the sealed candidate tree through a
public method, is attributable to the product and becomes a semantic failure.

This audit neither reads candidate source nor exposes fixtures, root IDs,
expected vectors, mutation labels, or scoring mechanics in the candidate
packet.
