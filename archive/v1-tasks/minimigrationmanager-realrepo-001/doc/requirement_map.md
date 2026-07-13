# MiniMigrationManager Requirement Map

## Requirements

- `REQ-api`: module exposes `MiniMigrationManager` and `MigrationError` with the public API in `prd.md`.
- `REQ-revision-graph`: revisions, parents, merges, history, heads, and unknown/cyclic parent rejection are public graph behavior.
- `REQ-schema-engine`: toy schema operations mutate an ordered table/column schema and fail atomically on invalid operations.
- `REQ-version-current`: current applied revision set is distinct from graph heads and from schema state.
- `REQ-planner`: upgrade/downgrade plans are semantic ordered steps from current to target.
- `REQ-ledger`: apply, downgrade, stamp, merge, and recover operations append public semantic ledger entries.
- `REQ-stamp`: `stamp` changes current without applying schema operations and influences future plans.
- `REQ-downgrade`: reversible downgrades update schema/current/ledger together; irreversible downgrades fail before mutation.
- `REQ-recovery`: `fail_at` creates a pending marker, blocks mutating commands, and `recover()` is idempotent.
- `REQ-atomicity`: failed operations do not expose mixed schema/current/ledger/plan state.

## Unit Coverage Template

- `MMU001` -> `REQ-revision-graph`: linear revision creation and history.
- `MMU002` -> `REQ-revision-graph`: branch heads and merge node.
- `MMU003` -> `REQ-revision-graph`, `REQ-atomicity`: unknown parent or duplicate revision rejection.
- `MMU004` -> `REQ-schema-engine`: create table and add column over a minimal linear fixture.
- `MMU005` -> `REQ-schema-engine`: rename table and reverse operation over a minimal linear fixture.
- `MMU006` -> `REQ-schema-engine`, `REQ-atomicity`: duplicate column fails atomically over one revision.
- `MMU007` -> `REQ-planner`: linear upgrade plan.
- `MMU008` -> `REQ-planner`: merge target plan includes missing branch.
- `MMU009` -> `REQ-stamp`, `REQ-version-current`: stamp changes current but not schema.
- `MMU010` -> `REQ-downgrade`: reversible downgrade primitive without multi-projection ledger assertions.
- `MMU011` -> `REQ-downgrade`, `REQ-atomicity`: irreversible downgrade failure before mutation.
- `MMU012` -> `REQ-recovery`: fail hook, pending marker, blocked mutation, idempotent recover as a prerequisite primitive.

## System Coverage Template

- `MMS001`: branch upgrade consistency across history, heads, current, schema, plan, and ledger.
- `MMS002`: stamp mismatch consistency across schema, current, future plans, and ledger.
- `MMS003`: downgrade consistency across schema, current, ledger, and next upgrade plan.
- `MMS004`: failed migration recovery across schema, current, ledger, plan, pending marker, and blocked mutations.
- `MMS005`: merge target completeness across plan, schema, current, history, and ledger after applying only one branch.

## Expected Gap Mechanism

A candidate can pass local graph, schema, planner, version-table, and recovery primitives while failing system rows if those primitives do not share one lifecycle state. Expected residual failures include stale current sets after schema mutation, schema replay that ignores ledger/stamp entries, plans that skip an unapplied merge parent, downgrade state that reverts schema but not current, and failed migrations that expose mixed public projections.

## Primitive-Cascade Guard

System rows should use prevalidated revision fixtures and semantic comparisons. Parser/id validation, exact plan ordering within one independent path, operation syntax failures, restore metadata interpretation, ledger kind naming, and recovery status naming should be clustered as primitive roots and not counted repeatedly as residual compositional gap unless multiple public projections diverge after those primitives pass.
