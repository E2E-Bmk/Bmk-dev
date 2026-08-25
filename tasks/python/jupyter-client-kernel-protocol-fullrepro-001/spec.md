# Jupyter Client verified-transition specification

## Overview

This package provides the ordinary client-side connection, signed-message,
kernel lifecycle, kernel-specification, and provisioner surfaces.  Long-lived
applications can coordinate those surfaces through verified transition
receipts.  A receipt is an immutable public record issued only after a state
owner commits a transition; consumers validate it against that owner's public
journal instead of trusting a look-alike mapping.

The same guarantees apply to synchronous and asynchronous managers.  Returned
snapshots and receipts are caller-owned immutable views and are not rewritten
by later activity.

## Public names

The ordinary Jupyter Client imports remain available.  The following public
names extend them:

```python
from jupyter_client.receipts import (
    TransitionReceipt,
    ReceiptValidationError,
    DependencyRejected,
)
from jupyter_client.transcript import CausalTranscript, TranscriptConflict
from jupyter_client.connect import StaleConnectionError
from jupyter_client.provisioning import StaleCatalogError
```

Receipts expose `surface`, `owner`, `sequence`, `digest`, `fact_digest`,
`parent_digest`, and `dependencies`.  `as_dict()` returns an independent
JSON-compatible projection.  Receipt identity is content-stable, but a
consumer also verifies membership in the issuing object's journal.

## Connection journal

Connection-bearing managers and clients expose `connection_generation`,
`latest_connection_receipt`, `connection_receipts()`, and
`validate_connection_receipt(receipt)`.  A complete connection contains the
transport, endpoint, five positive channel ports, byte key, and signature
scheme.

`refresh_connection_info(info)` validates the complete proposal before
publication and returns its committed receipt.  Invalid, incomplete, or
explicitly stale proposals leave values, generation, and journal unchanged.
The first successful publication has sequence one.  A legacy mapping without a
generation receives the next sequence.  A proposal older than the current
generation raises `StaleConnectionError`.

`rotate_connection_key(key, signature_scheme=None)` retains endpoint facts and
commits a child receipt whose `parent_digest` identifies the prior connection
receipt.  Writing a connection file includes the current generation and a
public receipt projection.  Loading validates the file before committing a
local receipt that cites the persisted receipt as a dependency.

A manager-created client validates the selected connection receipt against the
manager journal, snapshots exactly those facts, and exposes that receipt.
Omitting the argument selects the manager's latest committed receipt.  A
foreign, failed, stale, or shape-compatible but unjournaled receipt raises
`ReceiptValidationError`; no partial client is returned.  Later refresh or
rotation never rewrites an existing client or its Session.

## Signed delivery ledger

`Session` retains normal construction, signing, routing identities, multipart
buffers, serialization, and invalid-signature rejection.  A session also has a
replay domain over kernel, session, channel, and request generation.

After signature verification, `deserialize` admits the logical message to the
session's delivery ledger and includes an immutable `delivery_receipt` in the
returned message.  `validate_delivery_receipt(receipt, message=None)` verifies
ledger ownership and, when supplied, the authenticated message facts.  Failed
authentication or conflicting content emits no receipt and reserves no
identity.

An identical delivery in one full domain is idempotent and returns the same
receipt with `duplicate=True`.  Another domain owns an independent receipt.
`delivery_receipts()` returns independent ledger projections, and
`clear_replay(domain=None)` removes matching admission state without rewriting
receipts already accepted by another public owner.

## Causal transcript journal

`CausalTranscript(kernel_id, session_id, connection_generation)` owns a causal
graph independent of Session replay state.  Its low-level `record_delivery`
operation records an already verified delivery receipt and authenticated
message.  `accept_delivery(session, channel, message)` first requires the
Session to validate the message's delivery receipt, then delegates to that
same transition.  It never constructs an equivalent event by bypassing the
transcript journal.

Successful observations return a transcript receipt whose dependencies include
the delivery receipt digest.  Children observed before parents remain pending;
when the parent arrives, attachment receipts preserve both prior lineages.
Identical observations are idempotent.  Reusing an accepted message identity
for conflicting authenticated facts raises `TranscriptConflict`, appends a
failure observation, and retains the first successful receipt.

Snapshots include deterministic request order, causal children, unattached
messages, terminal requests, accepted receipt projections, and failure
observations.  An IOPub idle status closes its parent.  Late children do not
reopen a terminal request.  Another kernel, session, or connection generation
is rejected before graph publication.

## Transactional lifecycle journal

Managers expose `lifecycle_generation`, `lifecycle_state`,
`latest_lifecycle_receipt`, `lifecycle_receipts()`, and
`lifecycle_snapshot()`.  Stable states are stopped and running.

Lifecycle participants provide `identity`, `prepare(operation)`,
`commit(operation, process_status)`, and `cleanup(operation)`.  Preparation
returns an immutable-style lease mapping identifying the participant,
operation, and lease token.  A start or restart validates the selected
connection receipt and participant lease before publishing process status,
connection ownership, client ownership, and one lifecycle receipt.  Its
dependencies include both prerequisite digests.  High-level lifecycle calls
may select the latest connection receipt, but cannot publish without a
journal-backed receipt.

Failure cleans the attempt, records a public failure observation, emits no
success receipt, and restores the complete prior stable snapshot and receipt.
Interrupt preserves process and connection ownership while committing a child
receipt.  Restart publishes replacement process, connection, and owner
together.  Shutdown cleans resources before publishing stopped; repeated
shutdown while already stopped returns the existing receipt without a new
transition.

Overlapping asynchronous operations serialize in request order.  Cancellation
or failure of one caller completes cleanup before a later caller can publish.

## Kernel and provisioner catalog journals

`KernelSpecManager.refresh_catalog()` scans current ordered directories,
allow-list policy, and loadable kernel files.  It returns `generation`,
`kernels`, `provenance`, and an immutable kernel-catalog receipt.  Effective
change commits a child receipt; no-change returns the existing one.  Malformed
files appear in provenance without poisoning valid entries.  Earlier returned
specifications and catalog receipts remain snapshots.

`KernelProvisionerFactory.refresh_catalog()` independently snapshots current
packaging entry points and emits a provisioner-catalog receipt.  Generation-
selected availability and creation validate that receipt against the factory's
retained journal.  Created provisioners expose a provider receipt tied to the
entry point and retained catalog receipt.  Unknown or evicted generations
raise `StaleCatalogError` without changing current state.

`KernelSpecManager.select_kernel(...)` validates explicit or current kernel
and provisioner catalog receipts, loads the specification, constructs the
provider, and returns a selection receipt.  The selection dependencies include
both catalog receipts, the provider receipt, and a digest of the public
KernelSpec projection.  It never substitutes current state for a requested
retained receipt.

## Cross-resource lifecycle

`lifecycle_from_selection(selection, provisioner_factory, *,
connection_info, process_status, owner=None)` is the catalog-aware start path.
It validates the selection and provider receipts, commits or selects a
connection receipt, obtains a participant lease, and publishes a lifecycle
receipt carrying every prerequisite.  Stale selection, provider replacement,
connection failure, or lease failure stops the path before process publication.

Across every high-level workflow, successful result receipts carry observable
dependencies for each lower-level public transition they used.  Rejection is
transitive: if a prerequisite does not commit or cannot be validated, the
consumer emits no success receipt and leaves its prior public snapshot usable.

## Native compatibility

Connection JSON uses ordinary text keys and positive integer ports on disk and
byte keys on live objects.  Session signed multipart framing preserves routing
identities and ordered buffers.  KernelSpec dictionary and JSON projections
remain equivalent.  Provisioner persistence restores kernel identity and
connection information transactionally; incomplete restoration preserves the
prior state and permits retry.

## Non-goals

- launching or communicating with an external kernel;
- private sockets, locks, cache keys, or receipt storage layout;
- prescribing a cryptographic signature for local receipts;
- exact diagnostics, wall-clock timing, or unlimited retained generations;
- trusting serialized receipt shape without owner-journal validation;
- exposing evaluator roots, vectors, fixtures, or calibration history.
