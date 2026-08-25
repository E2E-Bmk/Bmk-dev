# VCR.py durable replay workflows

VCR.py records HTTP interactions and replays them without a live service. Applications that coordinate several cassette files often also need durable planning, crash recovery, ownership transfer, exact-byte publication, and reliable delivery of replay events. This separately distributed extension adds those facilities in `vcr.workflow` over the declared VCR.py runtime while leaving the existing VCR.py API unchanged.

All stateful classes accept a local directory path. Their public state survives discarding the object and creating another instance for the same directory. Writes are atomic: an interrupted write exposes either the prior committed state or the new committed state, never a partial document. Corrupt state or a receipt whose digest cannot be verified raises `IntegrityError` and does not replace the last visible value.

## Extension compatibility

The extension is installed beside an ordinary VCR.py 8.1.1 runtime, not as a replacement implementation of that runtime. Its package search closure is exactly two locations in order: the candidate's `vcr` directory and then the declared runtime's `vcr` directory. The workflow module is supplied by the extension; ordinary VCR.py submodules continue to come from the installed distribution.

Compatibility at the package entry is identity-preserving, not merely behaviorally similar. The public `VCR` object is the exact class object exported by `vcr.config`; `mode` is the exact `RecordMode` object exported by `vcr.record_mode`; `default_vcr` is an instance of that exact class; and `use_cassette` is bound to that exact default instance. The version text agrees with installed distribution metadata. A shim must not substitute locally defined wrappers, enums, classes, or equivalent-looking aliases for ordinary runtime objects. The same identity rule applies to any other ordinary runtime object that the shim re-exports. These are normal package-extension compatibility rules, independent of any particular replay example.

## Errors and receipts

The module exports `RecoveryError`, `IntegrityError`, `OwnershipError`, `StaleGenerationError`, and `IncompleteReplayError`. They inherit from `RuntimeError`; the last four also inherit from `RecoveryError`, and `StaleGenerationError` inherits from `OwnershipError`.

Every durable transition returns a frozen `OwnerReceipt` or a record containing one. `OwnerReceipt` has the public fields `kind`, `task`, `operation_id`, `generation`, `owner`, `digest`, `state`, and `prerequisites`. `prerequisites` is an ordered tuple of receipt digests. Digests are deterministic lowercase SHA-256 text derived from the semantic receipt content. A store rejects an unknown, altered, cyclic, wrong-owner, or stale receipt before changing current state.

An `operation_id` is an idempotency key within its store. Repeating an operation with the same semantic input returns the same value. Reusing it for a different input raises `RecoveryError`. Generations start at one and rise independently for each logical key.

## Cassette plans

`CassettePlanCatalog(path)` manages named replay plans. A definition is a mapping whose conventional fields are:

- `kind`: a capture or replay strategy name;
- `destination`: the logical endpoint;
- `deps`: an ordered sequence of prerequisite plan names;
- `artifacts`: an ordered sequence of cassette artifact names.

Extra JSON-compatible fields are preserved. Duplicate dependencies or artifacts, missing dependencies, and dependency cycles are rejected without disturbing an earlier commit.

`prepare(name, definition, *, owner, operation_id)` returns a prepared receipt but does not make the definition visible. `commit(receipt)` returns a frozen `CassettePlanSnapshot(name, definition, receipt)` and makes it current. Its `generation` property delegates to the receipt. `get(name)` returns the current snapshot. `recover(operation_id, *, owner)` returns the prepared receipt or committed snapshot. Unknown names and operations raise `KeyError`.

## Cassette match policies

`CassetteMatchPolicyCatalog(path)` versions named request-matching policy independently from cassette plans. A policy contains a nonempty ordered sequence of ordinary VCR.py matcher names and an optional ordered sequence of query parameter names excluded from request identity. Names are normalized without changing their relative order; duplicates and matcher names unavailable in the installed runtime are rejected.

`prepare(name, match_on, *, ignored_query=(), owner, operation_id, prerequisites=())` creates an invisible revision. `commit(receipt)` returns a frozen `CassetteMatchPolicySnapshot` with `name`, `match_on`, `ignored_query`, `generation`, `state`, `reason`, and `receipt`. A committed revision is active and can be obtained with `current(name)` after reopening the catalog.

`request_key(snapshot, request)` returns a deterministic public identity view after applying the policy's ignored-query projection. `equivalent(snapshot, left, right)` applies the named VCR.py matchers to the projected requests and returns a Boolean. A revision that cannot be safely used may be moved to `quarantined` by `quarantine(snapshot, *, reason, owner, operation_id)`. Quarantine removes it from the active view but preserves recovery history. `compensate(snapshot, match_on, *, ignored_query=(), owner, operation_id)` creates the next active generation from that exact quarantined revision. Stale, wrong-owner, or non-quarantined compensation is rejected without restoring the unsafe revision. `recover(operation_id, *, owner)` returns the exact durable stage of any policy operation.

## Playback sessions

`PlaybackSessionRegistry(path)` owns dependency-closed selections. `acquire(invocation_id, requested, graph, *, owner, operation_id)` validates the graph and returns a frozen `PlaybackSession` with `invocation_id`, `requested`, `selected`, `owner`, `generation`, `state`, and `receipt`. `selected` is a stable, dependency-first tuple: shared prerequisites occur once, request order breaks ties, and unrelated names are absent.

`handoff(session, *, new_owner, operation_id)` advances the generation and transfers ownership without changing the selection. `release(session, *, operation_id)` releases only the current generation. Operations from an older generation raise `StaleGenerationError`. `current(invocation_id)` and `recover(operation_id, *, owner)` expose durable state and enforce the active owner.

## Interaction journal

`InteractionJournal(path)` records one durable attempt history per cassette task. `begin(task, *, owner, operation_id, prerequisites=())` returns an `InteractionAttempt` in `prepared` state. The record has `task`, `owner`, `generation`, `state`, `result`, `values`, `category`, `detail`, and `receipt`.

`complete(attempt, *, result=None, values=None)` records a successful terminal result. `fail(attempt, *, category, detail="")` records a failed terminal result. Neither becomes the current acknowledged result. `acknowledge(attempt_or_receipt, *, owner, operation_id)` accepts a completed attempt exactly once and makes it current; a failed or wrong-owner attempt is rejected. `current(task)` returns only the acknowledged attempt. `recover(operation_id, *, owner)` returns the durable attempt at its latest state.

## Cassette artifacts

`CassetteArtifactIndex(path)` publishes exact cassette bytes. Values supplied as `str` are encoded as UTF-8; `bytes` remain unchanged. A `CassetteArtifactSnapshot` has `task`, an ordered `targets` tuple of `(name, lowercase_hex_bytes)`, `generation`, and `receipt`.

`prepare(task, targets, *, owner, operation_id, prerequisites=())` records an invisible prepared manifest. `publish(receipt)` makes the entire manifest visible. `seal(...)` performs those two stages as one operation. `read(task, target)` returns the original bytes, `current(task)` returns the snapshot, and `verify(snapshot)` checks the receipt, names, and every byte value. `recover(operation_id, *, owner)` returns the prepared receipt or published snapshot. A later generation for one task does not alter siblings.

## Patch obligations

`PatchObligationLedger(path)` tracks reversible patch scopes such as socket interception, client adapters, and nested cassette contexts. `open(task, setups, teardowns, *, owner, operation_id, prerequisites=())` returns a `PatchObligation` with `task`, `owner`, `generation`, `setups`, `teardowns`, `completed_setups`, `completed_teardowns`, `outcome`, `state`, and `receipt`.

Call `setup(item, name)` in declared order, then `body(item, outcome)`, then `teardown(item, name)` in the reverse order corresponding to completed setup steps. `close(item)` succeeds only after the body outcome and every owed teardown are durable. Incorrect order or incomplete closure raises `IncompleteReplayError`. `recover(operation_id, *, owner)` returns the exact next durable state so another process can continue cleanup.

## Replay event delivery

`ReplayEventOutbox(path)` separates visibility from delivery. `prepare(batch_id, events, *, owner, operation_id, prerequisites=())` stores an ordered sequence of event mappings and returns an invisible receipt. `publish(receipt)` returns a visible `ReplayEventBatch(batch_id, events, owner, generation, state, receipt)`. `claim(batch_id, *, owner, operation_id)` transfers pending delivery to the claimant. `acknowledge(batch, *, owner, operation_id)` completes only that claim.

`pending()` returns visible batches not yet acknowledged in stable order. `events(batch_id)` returns fresh mapping views in original order. `recover(operation_id, *, owner)` returns the durable receipt or batch. Publishing is not acknowledgement; a crash after publish or claim leaves the batch pending. A claimant from the wrong ownership generation cannot acknowledge.

## Replay checkpoints

`ReplayCheckpointLedger(path)` owns the durable consumption position for a `(session_id, cassette)` pair. `open(session_id, cassette, interactions, *, owner, operation_id, prerequisites=())` creates an active frozen `ReplayCheckpoint` containing `session_id`, `cassette`, the ordered tuple of interaction digests, `position`, `owner`, `generation`, `state`, and `receipt`. The sequence is nonempty and contains unique lowercase SHA-256 text. Repeating the same operation is idempotent; conflicting reuse is rejected.

`advance(checkpoint, interaction_digest, *, owner, operation_id, prerequisites=())` accepts only the exact next digest of the current active checkpoint. It advances one position and binds both the prior checkpoint receipt and the supplied causal prerequisites. Skipping, reordering, duplicating, using a stale generation, or advancing as the wrong owner fails before changing current state. `complete(checkpoint, *, owner, operation_id)` succeeds only after every digest has advanced. `handoff(checkpoint, *, new_owner, operation_id)` preserves the sequence and position, advances the generation, and fences the prior owner. `current(session_id, cassette)` and `recover(operation_id, *, owner)` preserve the exact durable position across reopen.

A checkpoint is an independent owner: journal completion, cassette bytes, patch cleanup, and event publication do not imply that replay consumption advanced. Cross-plane workflows bind the current playback-session receipt into a checkpoint and bind the completed checkpoint into later journal or event receipts. A crash or handoff therefore resumes at one exact next interaction without duplicating an already advanced interaction or silently skipping an unadvanced one.

## Coordinated replay

`DurableReplayCoordinator(path)` combines independent durable owners. It exposes `definitions`, `selections`, `journal`, `targets`, `lifecycle`, `outbox`, and `checkpoints` for their public views.

`plan(definitions, requested, *, invocation_id, owner, operation_id)` commits definitions, acquires one dependency-closed session, and returns a prepared workflow receipt. Repeating the same operation is idempotent; changing its semantic input is a conflict.

`execute(receipt, *, runner=None)` processes selected plans in dependency order. A runner is called as `runner(name, definition)` and may return `(status, result, values, targets, events)`. Status zero completes the attempt, closes patch obligations, seals artifacts, and publishes an event batch. A nonzero status records a failed attempt, closes cleanup, stops later work, and publishes no successful current result. With no runner, deterministic local values are produced.

`publish(receipt, *, owner, operation_id)` is permitted only for a successful executed workflow. It acknowledges every completed journal attempt and every replay event batch before publishing the workflow receipt. The previous published generation stays current if planning, execution, byte verification, cleanup, or delivery fails.

`recover(operation_id, *, owner, runner=None)` resumes a prepared or executed workflow and is idempotent after publication. `handoff(operation_id, *, current_owner, new_owner, transfer_operation_id)` transfers only a prepared workflow and fences the previous owner. `current(task)` returns the published workflow receipt for that task. `verify(receipt)` validates the entire prerequisite closure across all six owners. `owner_generations(task)` returns generation information for `definition`, `selection`, `journal`, `artifact`, `lifecycle`, and `outbox`.

## Composition laws

The durable owners remain separate even when coordinated. A prepared plan is invisible to a fresh session; an unacknowledged attempt is not a published replay result; prepared bytes are not readable; completed patch cleanup does not imply event delivery; and a published event remains pending until acknowledged.

Ownership moves as one public capability chain. Handoff fences every stale action that could publish a later view. Receipt prerequisites preserve causality from plan and selection through journal, artifact, cleanup, checkpoint advancement, event delivery, and final workflow publication.

Failure is local and closed. A rejected plan revision, stale session, failed interaction, interrupted artifact write, incomplete cleanup, corrupt receipt, or unacknowledged event cannot replace a prior verified workflow. Reopening from the same path must either resume the same operation once or expose the preceding committed generation.
