repo: sqlalchemy__alembic
source_path: G:\research\01_agents\swe-e2e\repo-pool\sqlalchemy__alembic
commit: 96fb84812ed7fe3ba1a8d6fd7e8cd1ba9a3c4b37
src_loc: 23065
test_functions: 1477
test_files: 35
dominant_test_styles: unit and integration tests over command API, migration script generation, revision graph traversal, operations rendering/execution, autogenerate comparisons, dialect-specific DDL behavior, and offline SQL output
public_docs:
- docs/build/tutorial.rst
- docs/build/front.rst
- docs/build/ops.rst
- docs/build/autogenerate.rst
- docs/build/offline.rst
- docs/build/branches.rst
- docs/build/batch.rst
- docs/build/api/commands.rst
- docs/build/api/config.rst
- docs/build/api/runtime.rst
- docs/build/api/operations.rst
- docs/build/api/script.rst
- docs/build/api/autogenerate.rst
core_fact_source: Alembic migration environments: script directories containing revision files, alembic.ini/env.py configuration, SQLAlchemy database schema state, and Alembic version-table state.
derived_views:
- CLI commands such as init, revision, upgrade, downgrade, current, history, heads, branches, stamp, and check
- programmatic command API in alembic.command
- migration runtime behavior through EnvironmentContext and MigrationContext
- Operations API directives and rendered/executed DDL
- ScriptDirectory and revision graph inspection
- autogenerate comparison and rendered migration scripts
- offline SQL output and generated migration files on disk
external_deps: SQLAlchemy is mandatory; database behavior can be isolated to SQLite for the core oracle, with backend-specific tests for PostgreSQL/MySQL/MSSQL/Oracle excluded unless they run without services or can be mocked. Editor, post-write hook, and subprocess behavior should be kept only when isolated with temporary files and monkeypatching.
test_import_audit: clean - git grep for module-level `from alembic._` / `import alembic._` in tests returned no matches. Tests do import alembic.testing helpers and some lower-level public-ish modules, so Stage 3 must classify by asserted behavior rather than by fixture shape.
docs_test_alignment: aligned - public docs cover the same projection types exercised by many tests: CLI commands, configuration, migration runtime, script directory/revision graph behavior, operations directives, offline SQL, batch mode, and autogenerate.
contamination_note: sqlalchemy__alembic@96fb848, committed 2026-05-31, relative to training cutoff: after
decision: keep
reason: Alembic has durable migration state, multiple public projections over that state, rich official docs, and enough behavior-oriented tests to build a traceable oracle after filtering.
risks: Large portions of the upstream suite rely on alembic.testing fixtures, exact rendered strings, dialect-specific implementation details, or autogenerate internals; Stage 3 must aggressively exclude tests that cannot be tied to public spec sections or observable behavior.
