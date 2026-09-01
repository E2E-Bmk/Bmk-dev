# Cookiecutter Local Project Generator

Implement a Python package named `cookiecutter` for generating projects from
local directory templates and coordinating durable local releases. The product
supports ordered context resolution, Jinja rendering, lifecycle hooks, replay,
nested templates, safe output transactions, content-addressed artifacts, and a
multi-process publication workflow. Network downloads, version-control cloning,
and remote template catalogues are outside scope.

## Generator interface

The package exposes a non-empty string `cookiecutter.__version__` and:

```python
from cookiecutter.main import cookiecutter
```

The callable has this ordered signature:

```text
cookiecutter(template, checkout=None, no_input=False, extra_context=None,
 replay=None, overwrite_if_exists=False, output_dir='.', config_file=None,
 default_config=False, password=None, directory=None,
 skip_if_file_exists=False, accept_hooks=True,
 keep_project_on_failure=False) -> str
```

It returns the absolute path of the generated project. The package also exposes
`python -m cookiecutter` with local-template, no-input, output-directory,
overwrite, skip, replay, configuration, nested-directory, hook, and `key=value`
context options.

`cookiecutter.exceptions` defines `CookiecutterException` and typed subclasses
for context decoding, existing output, invalid mode combinations, failed hooks,
undefined template values, missing configuration, and missing repositories.
It also defines `BusyProjectException`, `ReplayConflictException`,
`PublicationConflictException`, `ArtifactIntegrityException`,
`ArtifactConflictException`, `ChannelConflictException`,
`LeaseConflictException`, `LineageConflictException`,
`ManifestClosureException`, `DeliveryConflictException`,
`CompensationConflictException`, and `ReceiptClosureException`.
`HookProtocolException` is a `FailedHookException`. Every product exception
derives from `CookiecutterException`.

## Release interface

The release API is imported from `cookiecutter.release`:

```python
from cookiecutter.release import (
    ArtifactCatalog, ChannelRegistry, DeliveryOutbox, LeaseRegistry,
    LineageLedger, PublicationReconciler,
)
```

`ArtifactCatalog(root)` has:

```text
seal(project, *, context, owner)
inspect(artifact_id)
list_artifacts()
restore(artifact_id, destination, *, overwrite=False)
close(artifact_ids, *, context, owner)
inspect_closure(closure_id)
list_closures()
```

`ChannelRegistry(root, catalog)` has:

```text
reserve(channel, artifact_id, *, expected_epoch=None, owner)
commit(reservation)
abort(reservation)
current(channel)
history(channel)
recover()
rollback(channel, artifact_id, *, expected_epoch, owner)
```

`LeaseRegistry(root)` has:

```text
acquire(resource, *, owner)
handoff(grant, *, owner)
recover(resource, *, owner)
acknowledge(grant, *, receipt_digest, owner)
current(resource)
history(resource)
receipt(resource, generation)
```

`LineageLedger(root)` has:

```text
prepare(subject, *, payload_digest, owner)
commit(preparation, *, owner)
acknowledge(committed, *, receipt_digest, owner)
compensate(incomplete, *, reason_digest, owner)
recover(subject, *, owner)
history(subject)
by_token(subject, token)
```

`DeliveryOutbox(root, catalog)` has:

```text
enqueue(route, closure_id, *, payload_digest, owner)
current(delivery_id)
claim(delivery_id, *, owner)
acknowledge(claim, *, receipt_digest, owner)
recover()
cancel(delivery_id, *, reason_digest, owner)
pending(route=None)
receipts(route=None)
```

`PublicationReconciler(root, catalog, channels, outbox, lineages, leases)` has:

```text
prepare(channel, closure_id, replay_path, replay_document, *,
        expected_epoch, owner, route=None)
plan(plan_id)
status(plan_id)
receipt_closure(plan_id)
commit(plan, *, owner)
reconcile(plan_id, *, owner)
close_receipts(plan_id, *, owner)
inspect_receipt_closure(receipt_closure_id)
```

Results are immutable value records. Artifact records expose `artifact_id`,
`context_digest`, `owner`, `file_count`, and `total_bytes`. Activation
reservations expose `token`, `channel`, `artifact_id`, `base_epoch`,
`next_epoch`, and `owner`. Channel states expose `channel`, `epoch`,
`artifact_id`, `parent_artifact_id`, and `owner`.

Lease grants expose `resource`, `token`, `generation`, `owner`, and
`parent_token`. Lease receipts expose `receipt_id`, `resource`, `generation`,
`lease_token`, `owner`, and `receipt_digest`. Lineage records expose `subject`,
`sequence`, `phase`, `token`, `owner`, `payload_digest`, `parent_token`, and
`receipt_digest`. Manifest closures expose `closure_id`, ordered `artifact_ids`,
`context_digest`, `owner`, `file_count`, and `total_bytes`.

Delivery entries expose `delivery_id`, `route`, `closure_id`, `payload_digest`,
`owner`, and `status`. Claims expose `token`, `delivery_id`, `attempt`, and
`owner`. Delivery receipts expose `receipt_id`, `delivery_id`, `claim_token`,
`closure_id`, `payload_digest`, and `owner`. Publication plans expose `plan_id`,
`channel`, `closure_id`, `artifact_id`, `replay_path`, `expected_epoch`,
`payload_digest`, `delivery_id`, and `owner`. Reconcile results expose
`plan_id`, `outcome`, `channel_epoch`, `owner`, `lineage_token`, and
`delivery_id`. Receipt closures expose `receipt_closure_id`, `plan_id`,
`payload_digest`, `owners`, `receipt_ids`, and `owner`.

Identifiers and digests are non-empty opaque strings. Sequence, generation,
attempt, and epoch values are positive monotonic integers where present.

## Template context and rendering

A template contains `cookiecutter.json` and a project directory whose name has
a Cookiecutter expression. JSON key order is meaningful: later defaults may
render values resolved earlier. Defaults may be strings, choices, booleans,
dictionaries, empty values, and private controls.

With `no_input=True`, defaults resolve without prompting. User configuration
`default_context` overrides template defaults, and `extra_context` has highest
precedence. Changing an earlier value recomputes later templated defaults.
Choice, boolean, and dictionary values retain their types.

The resolved context is shared by project directory, nested directories,
filenames, text, hooks, and replay. Unicode round-trips. Binary inputs are
copied byte-for-byte. Paths matched by `_copy_without_render` preserve their
input bytes while surrounding path names still render.

An existing target fails unless overwrite is enabled. With overwrite and skip
enabled together, existing files remain unchanged and missing files are added.
Hook execution can be disabled without changing rendering behavior.

Invalid context JSON, undefined values, explicit missing configuration, and
missing repositories raise their corresponding typed errors.

## Hooks, replay, and output transaction

When enabled, `pre_gen_project` runs after target preparation but before file
rendering. `post_gen_project` runs after all files are present. Hooks use the
generated project as their working directory and receive the same resolved
context. A failed hook raises the typed hook error.

A successful run stores replay in the configured replay directory. `replay=True`
loads the current template's document; a path loads an explicit document.
Replay cannot be combined with non-null extra context or explicit no-input
mode. Saved public values overlay keys still present in the current schema,
new keys use current defaults, removed keys disappear, and current private
controls replace stale private controls. The selected nested path and inherited
parent context are retained by root replay.

Replay and output publish only after rendering and post-generation hooks
succeed. Replay replacement is atomic. On ordinary failure, a new target is
removed and an overwritten target's exact prior tree is restored unless
`keep_project_on_failure=True` requests diagnostics. Unrelated output siblings
are never changed.

Nested generation participates in the root lifecycle. A child inherits resolved
public parent values, while explicit call-time values retain highest precedence.
Any failure at any depth restores state owned by the root lifecycle. A retry
resolves the current template and configuration afresh.

## Source and destination safety

Every selected source remains within its repository. A nested path or
`directory=` value is relative, has no parent traversal, and resolves below the
repository root. Every rendered destination resolves below its output boundary.
Absolute, traversing, or resolved escaping paths raise `ValueError` before an
escaping file is created. Rejection leaves output and replay unchanged.

## Content-addressed artifacts and manifests

Sealing covers relative file names and bytes plus resolved public context;
private context keys are excluded. Equal trees and public context converge on
one artifact even across source directories and owners. Changed content or
public context creates a different identity. Inspection verifies the complete
artifact. Restore verifies first and replaces atomically only when overwrite is
permitted. Concurrent equal seals converge without exposing partial objects.

A manifest closes a non-empty set of already verified artifacts. Its identity
covers the sorted unique artifact identities and public context, not input list
order or private keys. It reports aggregate file and byte counts. Closing an
unknown or corrupt artifact fails without creating a closure. Equal sets and
public context converge during concurrent close; existing artifacts and
closures remain immutable.

## Channel activation

A channel begins at epoch zero with no head. `reserve` binds channel, verified
artifact, base epoch, and owner to a single-use token. `commit` advances exactly
one epoch; `abort` consumes none. Supplied `expected_epoch` is compare-and-swap.
A missing, consumed, borrowed, changed, or stale reservation fails. One live
reservation owns a channel while distinct channels remain independent.

Recovery retires reservations whose process is no longer live and never takes
one from a live process. History is ordered and complete. Rollback selects an
earlier verified artifact by appending a new epoch; epochs never rewind.

## Cross-process lease generations

Each non-empty resource has at most one live lease owner. Initial acquisition
creates generation one. Handoff requires the exact current grant and creates
the next generation with its token as parent. A grant is owner-bound and
single-use. A live foreign owner cannot be recovered or replaced.

If the process holding the current grant is no longer live, `recover` appends a
new generation for the recovery owner. It never rewrites prior generations.
Acknowledgement requires the exact current grant and a non-empty receipt digest,
creates an immutable receipt, and releases the live resource. Current state,
history, and generation receipt remain inspectable after reopening the registry.
Resources are isolated: activity on one cannot advance or release another.

## Append-only workflow lineage

A subject begins with `prepare`, whose payload digest is bound to its token.
`commit` requires the current preparation and appends a child record.
`acknowledge` requires the current commit and appends a receipt-bound child.
Tokens cannot be borrowed between subjects or reused after a later phase.

An incomplete current record may be compensated with a reason digest. Recovery
appends a recovery fact for a recoverable incomplete subject and does not edit
or remove history. After acknowledgement or compensation, a later preparation
may start from the actual current parent. Sequence numbers are contiguous and
monotonic, and every non-initial record names its actual parent token.

## Delivery outbox

Enqueue binds a route, verified manifest closure, payload digest, and owner to a
durable pending entry. Equal projections converge. Claim gives one live process
an owner-bound attempt token. A competing process cannot claim a live attempt.
When its process is gone, recovery retires that attempt and a new claim advances
the attempt number.

Acknowledgement requires the current claim, matching owner, exact payload
digest, and exact manifest projection. It creates an immutable delivery receipt
and marks the entry delivered. Cancellation records a reason without inventing
a delivery receipt. A delivered route may be projected again only as a new
entry with its own identity. Pending entries and receipts are filterable by
route and durable across reopen.

## Publication and compensation

Preparation binds one verified manifest closure to a channel base epoch, a
replay destination and canonical replay document, a route, a fresh lease
generation, a lineage preparation, and an outbox projection. The plan identity
and payload digest cover these bindings. The plan record is durable before any
externally visible publication effect.

Commit verifies the original plan and ownership, advances the channel from the
expected epoch, atomically publishes the planned replay bytes, appends lineage
commit, and hands off then acknowledges the plan lease. The channel artifact is
the manifest's primary artifact, and the replay payload digest agrees with the
lineage and delivery projection. Repeating or borrowing a plan cannot create a
second publication.

`reconcile` examines durable public facts after interruption. If channel,
replay, manifest, and lineage already describe the planned fact, it completes
missing protocol receipts without advancing the channel again. Otherwise it
compensates the plan: a channel head created solely by that plan is rolled back
through a new monotonic epoch, prior replay bytes are restored, incomplete
lineage gains a compensation record, the outbox entry is cancelled, and the
lease is released or recovered. An unrelated channel winner is never replaced
by compensation. Compensation is idempotent and leaves enough lineage for a
fresh plan to retry from current state.

## Receipt closure

A committed plan is not terminal until its delivery is acknowledged and its
receipts close. Closure verifies the manifest, current channel head, exact
replay digest, lease receipt, lineage acknowledgement, and delivery receipt.
It includes their identities in one content-addressed terminal record.

The terminal record must contain at least four distinct non-empty owners across
planning/building, publication, delivery, and audit responsibilities. One
process may reopen and inspect records produced by other processes, but a
single owner cannot impersonate the required workflow handoffs. Missing,
mismatched, compensated, cancelled, borrowed, or incomplete facts prevent
closure. A closure is immutable, owner-bound, single-use, and inspectable after
all component objects are reopened.

## Cross-view invariants

1. Rendered names, content, hooks, replay, and CLI/API results share one context.
2. Failed generation restores only the target and replay resources it owns.
3. Manifest membership and aggregate counts describe verified immutable bytes.
4. Lease generation and lineage sequence never rewind across process recovery.
5. Channel head, replay digest, manifest, lineage, and delivery name one plan.
6. Compensation restores prior visible facts without overwriting a foreign win.
7. Receipt closure covers every durable projection and at least four owners.
8. Private records, token spellings, lock names, and staging paths are never
   generated content and are not stable public API.
