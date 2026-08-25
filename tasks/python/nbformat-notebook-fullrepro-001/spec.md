# nbformat durable publication specification

## Scope and compatibility

Implement a Python package named `nbformat` compatible with nbformat 5.10.4.
The ordinary public notebook constructors, readers, writers, validators,
version packages, conversion functions, signature stores, notary behavior,
and signing application supplied by that release remain available.

This specification also defines a durable publication subsystem for notebook
work.  It records notebook commits, conversion lineage, signing-key
generations, and artifact visibility as independently persisted protocols.
The protocols are suitable for command-line workers and services that may
exit between stages.  They expose JSON-compatible receipts for audit and
dependency verification without prescribing private helpers, database table
layouts, temporary filenames, or a particular serialization library.

The extension entry points are:

```python
from nbformat.durable_store import (
    DurableStore, LeaseBusy, LeaseOwnershipError, GenerationConflict,
)
from nbformat.lineage import LineageJournal, LineageConflict, LineageStateError
from nbformat.trust_receipts import TrustLedger, TrustReceiptError
from nbformat.artifact import (
    ArtifactPublication, ArtifactBusy, ArtifactStateError,
    ArtifactRevisionConflict, verify_receipt_closure,
)
from nbformat.workflow import publish_workflow
```

Paths accepted by these APIs may be strings or path-like objects.  Each
durable owner creates its parent directory when needed and may be reopened by
a later process.  Network services and wall-clock lease expiry are outside
scope.

## Ordinary notebook behavior

`NotebookNode` remains a mutable mapping with equivalent key and attribute
access.  Recursive conversion, v1 through v4 constructors, validation,
conversion, JSON text and bytes, path and file-like I/O, multiline disk
projection, standard output types, and `NotebookNotary` retain the behavior
documented by nbformat 5.10.4.  Successful reads, writes, validation views, and
conversion do not unexpectedly mutate caller-owned values.  Transient trust
metadata is not durable notebook content.

## Receipt model

Every successful durable transition returns a JSON-compatible receipt.  A
receipt identifies its kind, owning resource, monotonically ordered event,
parent receipt identities, and the public facts of the transition.  Its
`receipt_id` is a deterministic digest of the other receipt fields.  Changing
any field invalidates that identity.  Parent identities are unique and sorted,
so equivalent dependency sets have the same representation.

Resource identity is derived from the durable resource, not from a class name
or one application-wide dictionary.  Separate store, lineage, trust, and
publication resources therefore have distinct identities even when one
workflow coordinates them.  Histories preserve event order and never rewrite
earlier receipts.

## Durable store leases and commit history

`DurableStore(path)` owns an append-only generation history.  `generation`
reports the latest committed generation and `history()` returns committed and
rolled-back lease events in durable order.

`acquire(owner, *, expected_generation=None)` creates an exclusive process
lease and returns a lease object.  A second owner receives `LeaseBusy`
immediately; acquisition does not wait on timing.  An expected generation is
checked before lease creation and stale expectations raise
`GenerationConflict`.  A lease exposes its opaque recovery token and base
generation.

`commit(payload, *, parents=())` accepts JSON-compatible payload meaning,
atomically advances the generation, appends one commit event, releases the
lease, and returns a `store-commit` receipt.  Its parents and payload digest
remain auditable after reopen.  `rollback(reason=...)` appends a rollback
event without advancing the generation and releases ownership.  A closed or
foreign lease raises `LeaseOwnershipError`.

A process that exits after acquiring may leave an orphan lease.  A reopened
store can call `adopt_orphan(token, owner)` only after the recorded process is
no longer live and only with the exact recovery token.  Adoption preserves the
leased base generation; the eventual commit records that it was adopted.
Live leases and guessed tokens are never adoptable.

## Persistent conversion lineage

`LineageJournal(path)` owns conversion-stage identity independently of the
notebook store.  A conversion implementation may perform any ordinary
nbformat conversion before recording the protocol; the journal records its
input and output meaning, not internal conversion steps.

`prepare(stage_id, *, input_digest, output_digest, parents=())` durably binds a
caller-selected replay identity to those facts and returns a
`lineage-prepare` receipt.  Repeating the same request returns the same
receipt.  Reusing the identity for different meaning raises
`LineageConflict`.

`acknowledge(prepared_receipt)` is a separate durable transition.  It accepts
only a valid preparation committed by that journal and returns a
`lineage-ack` receipt.  Repeated acknowledgement and `replay(stage_id)` return
the original acknowledgement identity rather than appending duplicates.

`rollback(stage_id, reason=...)` terminally rejects a prepared stage and
returns a `lineage-rollback` receipt.  A rolled-back stage cannot be
acknowledged or replayed; an acknowledged stage cannot be rolled back.
`history()` retains preparation and terminal events across reopen.

## Trust generations and lineage-bound signatures

`TrustLedger(path)` owns signing-key generations and retirement independently
of conversion lineage.  `issue_generation(key_id, secret, *, parents=())`
creates the next generation for that key identifier.  Its public receipt
contains a secret fingerprint, never the secret itself.  Multiple generations
remain distinguishable after reopen.

`sign(payload, *, domain, key_id, lineage_receipt)` uses the newest active
generation and accepts only an acknowledged lineage receipt.  The returned
`trust-sign` receipt binds the canonical JSON meaning of the payload, the
domain, exact lineage acknowledgement, key identity, and key generation.  It
depends on both the key-generation and lineage receipts.

`check(payload, signed_receipt, *, accepted_generations=None)` validates the
receipt identity, current retirement state, generation policy, and signature.
Changing semantic payload content fails validation.  `retire(key_id,
generation)` durably retires exactly one generation and returns a receipt;
retirement is idempotent and persists across reopen.  A later generation can
authorize new work without reviving the retired generation.  `history()`
returns the durable key, signing, and retirement events.

## Artifact prepare, visibility, acknowledgement, and recovery

`ArtifactPublication(destination)` owns one visible JSON artifact plus a
separate durable publication journal.  A visible envelope contains schema,
monotonic revision, notebook, audit data, dependency receipts, and publication
state.  The schema is `nbformat-durable-publication-v1`.

`prepare(notebook, *, audit, dependency_receipts, expected_revision=None)`
requires valid receipts from a store commit, an acknowledged lineage, and a
trust signature.  It validates JSON compatibility, checks the expected
visible revision, durably records an artifact preparation, and stages complete
bytes without changing the destination.  It returns an `artifact-prepare`
receipt whose parents are the supplied dependency receipts.

`make_visible(prepared_receipt)` acquires exclusive destination ownership,
rechecks the expected revision, and atomically replaces the destination with
the complete staged envelope.  It returns an `artifact-visible` receipt.
Competing ownership raises `ArtifactBusy`; a destination changed since prepare
raises `ArtifactRevisionConflict` and retains the current visible bytes.

Visibility and acknowledgement are deliberately separate.  A visible
envelope initially reports that it is not acknowledged.  `acknowledge` accepts
the corresponding visibility receipt, atomically marks the envelope
acknowledged, persists an `artifact-ack` receipt, and is idempotent.

`recover(prepare_id)` is safe after reopening the owner.  It completes a
durable preparation, acknowledges a visible-unacknowledged artifact, or
returns the existing acknowledgement.  Recovery neither invents a new
revision nor leaves staging or ownership artifacts after success.
`history()` exposes prepare, visibility, and acknowledgement events in order.

## Dependency closure and workflow

`verify_receipt_closure(receipts, terminal)` validates receipt identities and
walks parent links from the terminal receipt.  It returns true only when the
reachable graph includes store commit, acknowledged lineage, key generation,
trust signature, artifact preparation, visibility, and acknowledgement owned
by at least four distinct durable resources.  Unrelated receipts elsewhere in
the input do not complete a missing dependency.

`publish_workflow` is a convenience coordinator.  It receives a notebook and
distinct paths for the store, lineage, trust ledger, and destination, plus
owner, stage, key, secret, domain, and optional expected revision.  It commits
notebook meaning, acknowledges conversion lineage, issues and consumes a key
generation, publishes and acknowledges the artifact, verifies the receipt
closure, and returns the visible artifact, all receipts, and terminal receipt.
The coordinator does not collapse the owners or weaken their individual
failure and recovery laws.

## Cross-component guarantees

1. A committed store generation can anchor several independent lineage
   resources without making those resources interchangeable.
2. Prepared or rolled-back lineage never authorizes trust; replayed
   acknowledgement retains one identity.
3. Key retirement is observed after reopen and before any later publication.
4. Publication dependency packets preserve the exact receipt values used to
   authorize visibility.
5. A stale prepared artifact cannot replace a newer visible revision.
6. Process crash and owner reopen preserve append-only histories and explicit
   adoption or recovery boundaries.
7. A complete workflow proves a reachable dependency closure across distinct
   owners rather than merely returning a successful final notebook.

## Non-goals

- distributed consensus, network locks, clock-based lease expiry, or remote
  secret management;
- prescribing SQLite schemas, file suffixes, UUID generation, digest helper
  names, internal classes, or exact error prose;
- embedding secrets or transient process identifiers in notebook JSON;
- replacing ordinary nbformat conversion or validation algorithms;
- recovery from ambiguous or syntactically invalid JSON token streams.
