# Durable schema workspaces for attrs

## Scope and public surface

`attrs.workspace` coordinates long-lived, versioned schema families whose
concrete classes are ordinary attrs classes.  It extends rather than replaces
attrs: generated initializers, converters, validators, defaults, assignment
hooks, `attrs.evolve`, and recursive attrs serialization retain their ordinary
meaning.

The module exports `WorkspaceError`, `SchemaConflict`, `RevisionConflict`,
`MigrationError`, `SnapshotError`, `AuditError`, `LifecycleStage`,
`FieldRecord`, `SchemaRecord`, `StateViews`, `InstanceSnapshot`, `AuditEntry`,
`OperationReceipt`, `MigrationStep`, `WorkspaceSnapshot`, and
`SchemaWorkspace`.

All records, receipts, stages, entries, and snapshots are immutable value
objects.  Mapping and collection inputs are isolated at API boundaries, and
mapping-returning methods return detached data.

## Registry and stable schema identity

`SchemaWorkspace(registry_id, generation=0)` requires a non-empty registry
identifier and a non-negative generation.  Its generation advances once for
each successful changing registry or instance transaction and never advances
for reads, compatible replays, or failed work.

`register(schema_id, version, cls, *, field_ids=None, aliases=None,
provenance=None, expected_generation=None)` registers an attrs class under a
non-empty schema identity and a positive integer version.  Versions within a
schema are monotonic.  Re-registering identical logical content is an
idempotent replay; incompatible reuse raises `SchemaConflict` without changing
the workspace.  A supplied expected generation is checked before inspection.

The effective field set is obtained through `attrs.fields`, so inherited and
dynamically created attrs classes behave like declared classes.  Every field
has a stable non-empty identity, stored name, current initializer name,
accepted aliases, and ordered lifecycle stages.  Omitted field identities are
inherited from the preceding version when the stored name remains present;
otherwise they are deterministically derived from the schema and field name.
Explicit identities allow renamed fields to retain identity.  No version may
contain duplicate field identities or ambiguous aliases.

Native initializer names, including explicit attrs aliases and leading-name
normalization, are always accepted.  Additional aliases map external names to
stored field names and accumulate across versions for a field that retains its
identity.  `record(schema_id, version=None)` returns an isolated schema record;
an omitted version selects the latest.

## Lifecycle provenance and construction

Registration records the lifecycle stages actually present on each attrs
field, in `default`, `converter`, `validator` order.  Optional provenance maps
stored field names to stage-to-label mappings.  Missing labels are derived
deterministically from the public callable or default representation.  A label
is descriptive metadata and never replaces execution by attrs.

`construct(schema_id, version, values)` accepts stored names, current
initializer names, or retained aliases.  Supplying two names for the same
field is an error.  The normalized values are passed through the registered
class initializer, so factories, converters, validators, inheritance, and
dynamic-class behavior remain native.

## State views, assignment, and evolution

`views(instance, schema_id, version)` returns `StateViews` with four complete
views of the same registered fields: stored names, current initializer names,
evolution names, and stable serialized field identities.  Nested registered
attrs instances are represented recursively and mappings are emitted in a
deterministic order.

`assign(operation_id, instance, schema_id, version, changes, *,
expected_generation=None)` accepts the same names as construction.  All native
assignment conversion and validation is executed.  Multiple assignments form
one transaction: any failure restores every registered field and all workspace
history.  A success returns an `OperationReceipt` and all four views agree.

`evolve(instance, schema_id, version, changes)` is non-mutating.  It applies
alias normalization and creates a new instance through the registered schema,
leaving the original untouched.  The result must agree with construction,
assignment, and serialization views.

Operation identifiers are non-empty durable idempotency keys.  Replaying a
committed operation returns its original logical receipt with `replayed=True`
and performs no converter, validator, assignment, generation, or audit work.

## Transactional migration and compensation

`MigrationStep(name, apply, compensate=None)` names a transformation.  `apply`
receives an isolated mutable initializer-value mapping and may mutate it or
return a replacement mapping.  A compensation, when present, receives an
isolated post-step mapping and the triggering exception.

`migrate(operation_id, instance, schema_id, from_version, to_version, *,
changes=None, steps=(), expected_generation=None)` starts from stable field
identities shared by the source and target versions, overlays normalized
changes, applies migration steps in order, and constructs the target through
its native initializer.  The original instance is never modified.  If a step
or target construction fails, completed compensations run once in reverse
order.  The workspace, generation, operation history, and audit chain remain
unchanged.  `MigrationError` retains the triggering exception and any
compensation failures.  A successful migration is one transaction and returns
the new instance together with its receipt.

Expected-generation checks on registration, assignment, migration, federation,
rollback, and repair provide optimistic stale-revision fencing and occur before
user code or mutation.

## Deterministic snapshots and reopen

`capture(instance, schema_id, version)` returns a JSON-compatible
`InstanceSnapshot` keyed by stable field identities.  Its lowercase SHA-256
digest covers schema identity, version, and recursively serialized values using
canonical serialization independent of mapping insertion order.
`reopen_instance(snapshot_or_mapping)` authenticates structure and digest,
resolves registered nested schemas, reconstructs through native initializers,
and verifies that recapture is identical before returning the instance.

`snapshot()` returns a JSON-compatible `WorkspaceSnapshot` covering registry
identity, generation, logical schema records, durable operation history, and
the audit chain.  `to_dict()` methods return detached transport mappings.
`SchemaWorkspace.reopen(snapshot_or_mapping, classes)` authenticates the whole
snapshot before publication.  `classes` maps `(schema_id, version)` pairs to
ordinary attrs classes.  It verifies field coverage, identities, lifecycle,
history, generation, and audit continuity before returning a restored
workspace.  Invalid input raises `SnapshotError` without exposing partial
state.

## Registry federation, ownership, and rollback

`federate(operation_id, other, *, expected_generation=None)` atomically imports
schema versions from another workspace.  Missing records are imported with
their originating registry ownership.  Same-key records with identical logical
content are compatible.  Any incompatible collision raises `SchemaConflict`
that identifies incumbent and incoming owners, and the entire merge rolls
back.

A changing federation returns an `OperationReceipt` containing a rollback
token.  `rollback_federation(operation_id, receipt, *,
expected_generation=None)` is permitted only for the latest unrolled
federation of that workspace.  It atomically removes exactly the imported
records, preserves pre-existing compatible records, advances generation once,
and is itself idempotent.  Stale or foreign receipts raise an appropriate
workspace error without mutation.

## Audit verification and repair

Every changing transaction appends one `AuditEntry`.  Entries form a SHA-256
chain over their index, resulting generation, operation kind and identity,
deterministic payload digest, and parent digest.  `audit()` returns detached
entries.  `verify_audit(entries=None)` validates structure, lowercase digests,
indexing, parent linkage, payload linkage to durable receipts, and generation
monotonicity; it raises `AuditError` on failure.

`repair_audit(entries, *, expected_generation=None)` fences stale callers,
retains the longest valid prefix that agrees with durable operation history,
and deterministically reconstructs the remaining entries.  It returns a
detached repaired chain without changing schemas, instances, generation, or
operation history.  Repair cannot invent or discard a durable operation.
