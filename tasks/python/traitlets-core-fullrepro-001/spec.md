# Traitlets durable configuration workspaces

## Scope and public values

`traitlets.workspace` coordinates configuration evolution above an ordinary
`HasTraits` owner. Trait descriptors continue to supply defaults, coercion,
validation and native notifications. The workspace adds durable provenance,
dependency planning, generation fences, compensation, snapshots and delivery
acknowledgement without replacing Traitlets behavior.

The module exports `WorkspaceError`, `ConflictError`, `OwnershipError`,
`IntegrityError`, `DeliveryError`, immutable records `PlanNode`, `ChangePlan`,
`ViewLease`, `Revision`, `DeliveryRecord`, `WorkspaceSnapshot`,
`CompensationRecord`, `AuditRecord`, and `ConfigWorkspace`. Record collections
are deterministic tuples and record payloads never expose mutable internal
mappings. Digests are lowercase SHA-256 values over canonical logical content.

## Workspace identity and configuration provenance

`ConfigWorkspace(path, owner, workspace_id, names=None, dependencies=None)` owns
one caller directory and one `HasTraits` instance. The non-empty workspace
identity, managed trait order and acyclic dependency graph are durable. Omitted
names mean all owner traits tagged `config=True`. Explicit names are ordered,
unique, known and config-enabled. Dependencies contain only managed names, with
no self edge or cycle.

Opening an existing path authenticates its workspace identity and graph before
restoring descriptor values. A conflicting identity, field set, graph or graph
type is rejected. Corrupt, truncated or cross-view-inconsistent data raises
`IntegrityError`; it is never reset silently. `values()`, `config_view()` and
`provenance_view()` return detached projections. Different paths never share
leases, revisions, deliveries or operations even when textual identifiers
match.

Plans accept ordered configuration layers. A layer is a non-empty source label
and a mapping; later layers win. Unknown or untagged fields are ignored, while
each winning managed value retains its source. Provenance changes are material
even when descriptor values compare equal.

## DAG plans, owned leases and fences

`lease_view(owner, *, operation_id)` creates an owner-bound view at the current
generation with a monotonically increasing fence. `handoff` transfers current
ownership and advances the fence. `refresh` advances a current owned lease to
the workspace head and also advances the fence. Foreign workspace, old owner,
old generation or old fence records are rejected without publication.

`plan(operation_id, layers, *, lease, expected_generation=None)` is a pure
projection against the exact leased generation. It validates layered input,
projects values through Traitlets descriptors and emits affected `PlanNode`s in
stable topological order, using managed-name order for ties. Nodes retain old
and projected values, direct prerequisites and winning source. The plan binds
workspace identity, generation, lease identity and fence. Caller mappings and
returned values are isolated.

Operation identifiers are durable idempotency keys. Exact replay returns the
recorded logical result; reuse for different intent is a conflict. Planning an
already committed exact intent produces an authenticated replay plan. Planning
may materialize a normal dynamic default but otherwise changes no durable or
owner projection.

## Transaction publication and compensation

`commit(plan, lease, owner, *, operation_id)` authenticates the complete plan,
current owner, generation and fence. Descriptor assignment, native Traitlets
notification, config/provenance projection, one revision, generation advance,
operation registration and delivery creation form one atomic boundary. A
failed assignment or publication restores every owner and durable projection.
A changing value or provenance creates exactly one next generation. An empty
plan is a stable observation and creates neither a generation nor journal row.
Native observers see the complete committed owner state.

A revision links its predecessor and content digests, ordered changes and all
delivery tokens. Replaying an exact committed operation returns its original
logical revision marked as replayed, without notifications, delivery or
generation advance.

`compensate(revision, lease, owner, reason, *, operation_id)` appends a new
generation restoring the exact value and provenance projections immediately
before that revision. History is never rewritten. Compensation requires the
revision owner, current head and current owned fence; a foreign, stale or
already-compensated revision is rejected atomically. The compensation record
links both generations and the restored digest.

## Durable delivery, acknowledgement and retry

`subscribe(subscriber_id, callback, max_attempts=3)` binds a unique subscriber.
Bindings are process-local, while subscriber identity, attempt limit, payload
and delivery state are durable. Reopening may rebind the same subscriber with
the same attempt limit. Removing a binding prevents future deliveries but does
not discard existing work.

Each changing revision creates one delivery per subscriber snapshot. A callback
receives the immutable revision, a detached complete value projection and the
current delivery record. Successful return marks work `delivered`, awaiting an
explicit owner-matched `ack`; callback failure marks it `retryable` until the
attempt limit and then `poison`. One failed subscriber does not suppress later
subscribers or roll back the revision.

`ack(token, subscriber_id, *, operation_id)` durably acknowledges delivered
work. `retry_delivery(token, subscriber_id, *, operation_id)` retries only
retryable work and increments its attempt. Unknown, foreign, acknowledged,
unbound or poison work raises `DeliveryError`. Exact ack/retry replay is
idempotent; changed reuse conflicts. Reopen retains attempt and acknowledgement
state and permits retry after the subscriber is rebound.

## Snapshots, reopen and reconciliation

`snapshot(previous=None)` returns an immutable, JSON-compatible
`WorkspaceSnapshot`. A base snapshot contains complete values, provenance,
revision evidence and delivery evidence. A child contains only projection and
evidence changes since an authenticated earlier snapshot and links its parent
digest. Snapshot digest is independent of mapping insertion order while journal
ancestry remains visible. Historical snapshots never track later mutation.

Reopening reconstructs current descriptors, config provenance, leases,
operations, revisions, compensations, deliveries and retry state. Old plans and
leases remain fenced. `verify()` checks state checksum, generation and journal
chains, plan and revision digests, lease fences, compensation ancestry,
snapshot references, delivery payloads and operation identity. It returns an
`AuditRecord` only for a stable cross-view snapshot; disagreement raises
`IntegrityError`.

The required behavior is closed under varied valid trait values, source labels,
dependency shapes, owner and subscriber names, operation identifiers, layer
mapping order, retry outcomes, generations and reopen points. No particular
JSON layout, private Traitlets implementation detail, fixture constant or exact
exception message is required.

