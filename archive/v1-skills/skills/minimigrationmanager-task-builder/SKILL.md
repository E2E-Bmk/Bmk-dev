---
name: minimigrationmanager-task-builder
description: Build, revise, or audit the MiniMigrationManager SWE unit/system-gap benchmark task. Use when editing MiniMigrationManager PRDs, rubrics, reference implementations, candidate packets, score reports, or judge notes for migration DAG, schema, version-table, ledger, planning, stamp, downgrade, and recovery lifecycle invariants.
---

# MiniMigrationManager Task Builder

## Goal

Construct MiniMigrationManager as a toy migration workspace task, not an Alembic clone. The benchmark must test whether revision graph, branch heads, current version set, schema introspection, dry-run plans, applied ledger, stamps, downgrades, and recovery markers remain consistent after mixed lifecycle operations.

## Agreement Surface

Treat these as local free choices:

- migration file format and storage layout
- internal DAG representation
- schema model representation
- version-table representation
- applied ledger format
- plan rendering text
- rollback journal format

Treat these as public invariants:

- revision ids are opaque public strings matching the PRD constraints
- history, heads, current, schema, plan, and ledger describe one migration workspace
- branch and merge plans include all required parent histories
- `stamp` changes current revisions without applying schema operations
- downgrade updates schema, current, ledger, and future plans together
- irreversible downgrade paths fail before mutating public state
- failed upgrade/downgrade creates a public pending recovery marker
- mutating commands except `recover` fail while pending recovery exists
- `recover` is idempotent and restores the last committed schema/current/ledger state

## Unit Test Template

Unit rows must be feature-pure. They may use explicit in-memory fixtures or public constructor/setup helpers, but should not build complex state through unrelated subsystems.

- revision parser: valid revision, merge revision, invalid operation or missing parent
- revision graph: history order, branch heads, cycle/unknown-parent rejection
- schema engine: create table/add column, rename table, duplicate column atomicity
- version table: one current revision, multiple current heads, unknown revision validation
- planner: linear upgrade, branch merge target, no-path failure without mutation
- downgrade: reversible operation inversion and irreversible operation rejection
- recovery journal: public fail hook, pending marker visibility, idempotent `recover`

Do not unit-test private files, exact exception text, exact display text, or Alembic API compatibility.

## System Test Template

Every system row must name a cross-feature contract and compare at least three public projections.

- Branch upgrade consistency: compare `history`, `heads`, `current`, `schema`, `plan`, and `ledger` after upgrading through two branches and a merge.
- Stamp lifecycle: compare unchanged `schema` with changed `current`, changed future `plan`, and `ledger` after stamping to a revision or merge.
- Downgrade consistency: compare reverted `schema`, `current`, `ledger`, and future upgrade `plan` after downgrade to an earlier revision.
- Failed migration recovery: compare pre-failure committed `schema/current/ledger/plan`, pending marker visibility, blocked mutations, `recover`, and post-recovery projections.
- Merge target completeness: compare plan steps, schema, current, graph/history, and ledger when upgrading from one applied branch to a merge revision requiring the other branch.

System rows should use prevalidated revision fixtures so parser/path defects do not dominate residual gap scoring.

## Oracle

Use a hand-written simplified reference implementation from the PRD. Do not use Alembic as oracle because exact Alembic API, file layout, SQLAlchemy integration, and script environment behavior are out of scope and raise contamination risk.

Use `tools/score_unit_system.py` with `task/minimigrationmanager-realrepo-001/rubric.json`. Preserve score reports under `task/minimigrationmanager-realrepo-001/doc/score_reports/`.

## Fairness Rules

- Compare semantic objects, not display strings.
- Do not inspect private storage files or rollback journal internals.
- Do not require real SQL dialects, SQLAlchemy behavior, Alembic config files, or Alembic command names beyond public inspiration.
- Cluster repeated parser, exact-plan, unknown-target, or operation-inversion failures as primitive roots.
- A replay-based implementation is allowed; system loss must come from public ledger/stamp/recovery/current/schema/plan divergence, not from banning helpers.
- Accept a gap only if residual compositional loss remains at least 15pp after primitive, cascade, evaluator, provider, and contamination roots are removed.

## Stop Condition

Stop after three construction cycles. Retire or materially rescope if a fresh capable OpenHands or Codex agent scores roughly 90%+ on both unit and system after fairness cleanup, or if remaining losses are parser/display primitives, one exact plan field, or adjacent hidden checks.
