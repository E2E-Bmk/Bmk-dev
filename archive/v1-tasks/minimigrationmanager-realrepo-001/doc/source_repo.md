# MiniMigrationManager Source Notes

MiniMigrationManager is inspired by Alembic-style migration workflows:

- Revision branches and multiple heads: https://alembic.sqlalchemy.org/en/latest/branches.html
- Command surfaces such as `current`, `heads`, `history`, `upgrade`, `downgrade`, `merge`, and `stamp`: https://alembic.sqlalchemy.org/en/latest/api/commands.html
- Tutorial context for generated revisions and migration environments: https://alembic.sqlalchemy.org/en/latest/tutorial.html

The task intentionally does not clone Alembic's API, file layout, SQLAlchemy integration, script environment, database connections, or generated migration template. It keeps the public product shape of revision graph plus current database state, but replaces real SQL with a deterministic toy schema language.

The benchmark target is cross-projection lifecycle consistency: graph/history, current version set, schema snapshot, dry-run plan, ledger, stamp state, downgrade behavior, and recovery marker must agree after branch, merge, stamp, downgrade, and failed-operation workflows.
