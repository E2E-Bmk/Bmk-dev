# APScheduler recovery services

APScheduler exposes scheduler, task, job, event, and policy objects at the package top level.  This extension adds an offline recovery model for installations that must reconstruct dispatch state without starting a scheduler or contacting an external service.

The extension is available as `apscheduler.recovery`.  It is intentionally independent of a particular data store or event broker.  Identifiers are non-empty strings.  Timestamps are finite numbers and durations are positive finite numbers.  Collections returned by the API are newly allocated and ordered deterministically.

## Core package surface

The package top level exports `Scheduler` and `AsyncScheduler` as the ordinary
synchronous and asynchronous scheduler entry points. It also exports the
enumerations used to configure and inspect scheduler work:

- `SchedulerRole` has the ordered members `scheduler`, `worker`, and `both`;
- `RunState` has `starting`, `started`, `stopping`, and `stopped` in lifecycle
  order;
- `JobOutcome` has `success`, `error`, `missed_start_deadline`,
  `deserialization_failed`, `cancelled`, and `abandoned` in that order;
- `ConflictPolicy` has `replace`, `do_nothing`, and `exception`;
- `CoalescePolicy` has `earliest`, `latest`, and `all`.

The policy enumerations are independent types even when member names are used
in related scheduling decisions. `JobLookupError` and `ScheduleLookupError`
are lookup failures and therefore inherit from `LookupError`.

`task(**options)` decorates a callable without changing how that callable is
invoked. The decorated callable receives a `_apscheduler_taskdef` value whose
public fields reflect the supplied task options. Supported options include
`id`, `job_executor`, `max_running_jobs`, `misfire_grace_time`, and `metadata`.
A numeric misfire grace period is represented as a `datetime.timedelta`.
Metadata is copied per decorated callable so later changes to one task
definition cannot alter a sibling definition.

## `RecoveryState`

`RecoveryState()` creates an empty state container.  Its public methods are described below.  Records returned by the container are plain dictionaries; modifying a returned dictionary does not modify stored state.

### Lane definitions

`define_lane(lane_id, *, owner, parents=(), artifacts=()) -> dict` registers a scheduling lane.  `parents` names previously registered lanes and `artifacts` names the artifact kinds produced by work in this lane.  Parent and artifact names may not repeat.  A lane identifier may be registered only once.  Definitions must remain acyclic.

`lane(lane_id) -> dict` returns one definition.  `lanes() -> list[dict]` returns definitions in registration order.  A definition has `lane_id`, `owner`, `parents`, and `artifacts`; the two collections are tuples.

Owners are part of lane identity.  Two lanes may have the same parents and artifacts while retaining different owners and independent recovery state.

### Dispatches and dependencies

`submit(dispatch_id, *, lane_id, scheduled_for, payload_digest, dependencies=()) -> dict` records pending work.  The lane and every dependency must exist, a dispatch may not depend on itself, and its identifier is unique.  Dependency names may not repeat.  Submission order and dependency edges together define a deterministic recovery order: ready work is ordered first by `scheduled_for`, then by submission order.

`dispatch(dispatch_id) -> dict` returns a dispatch record.  `dispatches(*, state=None) -> list[dict]` returns all records in submission order, optionally restricted by state.  Dispatch state is one of `pending`, `leased`, `completed`, or `abandoned`.

### Capacity leases

`acquire(dispatch_id, *, worker, now, ttl) -> dict` leases pending work and returns a record containing `dispatch_id`, `worker`, `token`, `acquired_at`, `expires_at`, and `generation`.  Tokens are opaque non-empty strings.  A live lease excludes every worker, including the current owner.  Acquiring after expiry creates a new token and increments the generation.

`renew(dispatch_id, token, *, now, ttl) -> dict` extends the matching live lease.  Renewal preserves token and generation and sets `expires_at` from the supplied time.  A stale token, an expired lease, or a non-leased dispatch is rejected.

`release(dispatch_id, token, *, now) -> dict` releases the matching live lease and returns the dispatch to `pending`.  `expire(*, now) -> list[str]` releases every lease whose expiry is not later than `now`, returning affected dispatch identifiers in submission order.  Lease operations never erase prior journal entries.

### Outcome journal

`record_outcome(dispatch_id, token, *, outcome, finished_at, artifacts=()) -> dict` appends the terminal outcome of a live lease.  Artifact digests may not repeat and each artifact kind must be declared by the lane.  The returned journal record contains a monotonically increasing `sequence`, the dispatch and lane identifiers, owner, lease generation, outcome, finish time, and artifact tuple.  Recording marks the dispatch `completed` and consumes its lease.

Repeating the same terminal record for a completed dispatch is idempotent and returns the original record.  A conflicting repeat is rejected.  `journal(*, after=0, owner=None) -> list[dict]` returns records with a larger sequence, optionally restricted by the owner recorded at completion.

### Consumer checkpoints

`register_consumer(consumer_id) -> dict` creates an independent delivery checkpoint with `delivered=0` and `acknowledged=0`; identifiers are unique.  `deliver(consumer_id, *, limit=None) -> list[dict]` returns journal entries after that consumer's delivered sequence and advances only `delivered`.  A positive `limit` bounds the batch.

`acknowledge(consumer_id, sequence) -> dict` advances `acknowledged` only through an entry already delivered to that consumer.  Acknowledgement is monotonic, may be repeated at the current value, and does not change `delivered`.  `consumer(consumer_id) -> dict` returns the two checkpoint values.

`compact() -> list[int]` removes the longest journal prefix acknowledged by every registered consumer and returns removed sequence numbers.  With no consumers, compaction removes nothing.  Sequence numbers are never reused and consumer checkpoints do not move backward.

### Recovery planning and reconciliation

`ready(*, now) -> list[dict]` reports pending dispatches whose dependencies are completed and whose scheduled time is not later than `now`.  Active leases are not ready.  `blocked(dispatch_id) -> tuple[str, ...]` returns incomplete dependencies in declaration order.

`reconcile(*, now) -> dict` expires due leases and returns a new dictionary with `expired`, `ready`, and `blocked`.  `expired` is a tuple of identifiers, `ready` is a tuple in deterministic recovery order, and `blocked` maps pending dispatch identifiers to tuples of incomplete dependencies.  Reconciliation is observational apart from expiry and does not create leases or journal records.

`abandon(dispatch_id, *, reason, now) -> dict` marks an uncompleted dispatch abandoned, consumes any lease, and preserves its dependency and journal history.  Abandoned work does not satisfy a dependency.

### Portable snapshots

`snapshot() -> dict` returns a JSON-compatible complete representation including registration order, token counter, next journal sequence, lanes, dispatches, leases, retained journal entries, consumers, and terminal idempotency information.  `RecoveryState.from_snapshot(document) -> RecoveryState` constructs an independent state with the same behavior.

Snapshot loading rejects malformed documents, dangling references, duplicate identifiers or sequence numbers, non-monotonic counters, invalid states, lease/state disagreement, checkpoint values beyond delivered history, and lane or dispatch dependency cycles.  Repeated snapshot/load cycles preserve the observable ordering and values of all public views.

## Errors and isolation

Invalid operations raise `ValueError`, `KeyError`, or `RuntimeError` as appropriate; no failure partially changes state.  Separate `RecoveryState` instances share no mutable records, counters, leases, or checkpoints.  All behavior is deterministic and uses only supplied timestamps.
