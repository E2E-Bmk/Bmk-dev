# MiniMigrationManager Public Product Packet

## Overview

Build `minimigrate.py`, a dependency-free Python migration workspace inspired by revision-graph migration tools. The task uses a toy schema language and a public Python API so tests compare semantic state, not exact CLI text, file layout, SQLAlchemy behavior, or Alembic compatibility.

The module must be importable from the solution directory:

```python
from minimigrate import MiniMigrationManager, MigrationError
```

`MiniMigrationManager()` constructs a fresh in-memory migration workspace. Implementations may accept an optional root/path argument for persistence, but the zero-argument form must work. Use only the Python standard library.

## Public Product Contract

### Revisions

Revision ids are public strings matching `[a-z][a-z0-9_]*`. They are opaque identifiers, not sortable timestamps.

The API must support:

- `revision(rev_id, parents=None, ops=None, message="")`
- `merge(rev_id, parents, message="")`
- `history()`
- `heads()`
- `current()`
- `schema()`
- `plan(direction, target)`
- `upgrade(target, fail_at=None)`
- `downgrade(target, fail_at=None)`
- `stamp(target)`
- `ledger()`
- `recover()`

Targets:

- `base`: empty schema before any revision.
- a known revision id.
- `heads`: all graph heads. `upgrade("heads")` applies every missing branch head reachable from the current set. `downgrade("heads")` is invalid because it is not a lower target.
- `current`: the current applied revision set.

All query methods return JSON-serializable dictionaries/lists. Tests compare semantic records and sorted fields, not display order.

### Toy Schema Operations

Revisions contain operation strings:

```text
create_table NAME col:type ...
drop_table NAME
restore_table NAME col:type ...
add_column TABLE col:type
drop_column TABLE col
restore_column TABLE col:type
rename_table OLD NEW
```

Operation semantics:

- `create_table` creates a table with ordered columns and downgrades by dropping the table.
- `drop_table` removes a table during upgrade. It is irreversible unless the same revision also contains `restore_table NAME col:type ...` metadata.
- `restore_table` is downgrade metadata only. It must not mutate schema during upgrade and is used only to reconstruct a table when reversing a `drop_table` from the same revision.
- `add_column` adds one column and downgrades by dropping it.
- `drop_column` removes one column during upgrade. It is irreversible unless the same revision also contains `restore_column TABLE col:type`.
- `restore_column` is downgrade metadata only. It must not mutate schema during upgrade and is used only to reconstruct a column when reversing a `drop_column` from the same revision.
- `rename_table OLD NEW` renames the table and downgrades by renaming `NEW` back to `OLD`.
- A downgrade plan that crosses an irreversible operation must fail before mutating schema, current, or ledger.

Malformed operations, unknown parents, duplicate revisions, duplicate columns, missing tables, and cycle-like parent relationships raise `MigrationError`.

### Semantic Records

`history()` returns revision nodes:

```python
{"id": "r1", "parents": ["base"], "children": ["r2"], "message": "", "ops": ["create_table ..."]}
```

`heads()` returns sorted graph heads. `current()` returns:

```python
{"revisions": ["r2"], "pending": None}
```

When recovery is pending, `pending` is a public record naming operation, target, and failure point.

`schema()` returns:

```python
{"tables": {"users": [["id", "int"], ["name", "text"]]}}
```

`plan(direction, target)` returns ordered steps:

```python
[{"direction": "upgrade", "revision": "r2", "ops": ["add_column users name:text"]}]
```

`ledger()` returns ordered semantic entries:

```python
{"entries": [{"kind": "apply", "revision": "r2", "before_current": ["r1"], "after_current": ["r2"]}]}
```

Ledger kind rules:

- Successful `upgrade()` records `apply` for every applied revision, including merge revisions.
- Successful `downgrade()` records `downgrade` for every reverted revision.
- `stamp()` records one `stamp` entry. The stamped target must be recoverable from `after_current`; the `revision` field may be the target string or `None`.
- `recover()` records one `recover` entry only when a pending marker existed and recovery changed state; idempotent no-op recovery does not append another entry. A `recover` ledger entry must include `revision: None` because no revision was applied or reverted.
- Failed operations do not expose temporary ledger entries through `ledger()`. Read-only projections show the last committed ledger plus the pending marker in `current()`.

`recover()` returns:

```python
{"status": "no_pending" | "rolled_back" | "completed", "before_current": [...], "after_current": [...]}
```

## Lifecycle Semantics

### Revision Graph

`revision()` adds a node to the revision DAG. Parent ids must already exist unless the parent is `base`. `merge()` adds a node with multiple parents and no schema operations unless `ops` are explicitly supplied through `revision()`.

Branch heads are graph nodes with no children. Current revisions are applied migration heads in the workspace and may differ from graph heads after partial upgrades or stamping.

### Upgrade

`upgrade(target)` applies the semantic plan from the current revision set to the target. A merge target with multiple parents must include missing branch histories before the merge revision. After success, schema, current, future plans, and ledger must agree.

### Stamp

`stamp(target)` changes current revisions without applying schema operations. It records a ledger entry and leaves `schema()` unchanged. Future `plan()` calls start from the stamped current set even when schema and current are intentionally mismatched.

### Downgrade

`downgrade(target)` reverts applied revisions down to `target`. It updates schema, current, ledger, and future upgrade plans together. If a required reverse operation is unavailable, it raises `MigrationError` before mutating public state.

### Failure And Recovery

`fail_at` is a public test hook for `upgrade()` and `downgrade()`. Supported values:

- `after_schema`
- `after_ledger`

A failing operation creates a pending recovery marker and exposes the last committed schema/current/ledger state to read-only queries. Mutating commands other than `recover()` must fail while pending recovery exists. `recover()` is idempotent and rolls back to the last committed schema/current/ledger state.

`recover()` status rules:

- `no_pending`: no pending marker existed; no state changed and no ledger entry is appended.
- `rolled_back`: pending marker existed and the workspace was restored to the last committed state; append a `recover` ledger entry.
- `completed`: reserved for implementations that can prove a failed operation had already committed every public projection consistently before the error. Reference tests should not require this status unless they deliberately construct such a committed-pending state through public behavior.

## Global Invariants

- Revision graph, heads, history, current, schema, plan, and ledger are projections of one migration workspace.
- A branch merge plan must not silently skip an unapplied parent branch.
- Stamping changes version projections without applying schema operations.
- Downgrade changes schema and current together or fails atomically.
- Failed migrations expose no mixed public state and are recoverable through `recover()`.
- Ledger order is public lifecycle evidence and cannot be recomputed away from current/schema changes.

## Non-Goals

Do not implement SQLAlchemy, real SQL execution, Alembic config files, script environments, migration autogeneration, exact Alembic command output, database connections, or dialect-specific DDL.

## Evaluation Style

Unit tests exercise feature-pure primitives: revision graph, schema operations, version table, planner, stamp, downgrade inversion, and recovery marker behavior.

System tests exercise lifecycle invariants over at least three public projections after mixed operations such as branch merge upgrade, stamp mismatch, downgrade, failed migration recovery, and one-sided branch planning.
