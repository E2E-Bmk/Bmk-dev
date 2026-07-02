<!-- INTERNAL
task_id: alembic-migrations-fullrepro-001
spec_version: v3
delta: Patch v2 Stage 5 judge spec gap: documents ScriptDirectory get_heads()/get_bases() list return types.
source_boundary: G:\research\01_agents\swe-e2e\Bmk-dev\wip\alembic-migrations-fullrepro-001\filter_notes.md; G:\research\01_agents\swe-e2e\repo-pool\sqlalchemy__alembic\alembic\__init__.py; alembic\command.py; alembic\config.py; alembic\runtime\environment.py; alembic\runtime\migration.py; alembic\operations\base.py; alembic\script\base.py; alembic\script\revision.py; alembic\autogenerate\api.py; docs\build\tutorial.rst; docs\build\front.rst; docs\build\ops.rst; docs\build\offline.rst; docs\build\branches.rst; docs\build\batch.rst; docs\build\autogenerate.rst; docs\build\api\commands.rst; docs\build\api\config.rst; docs\build\api\runtime.rst; docs\build\api\operations.rst; docs\build\api\script.rst; docs\build\api\autogenerate.rst.
-->

# Alembic Specification

## Product Overview

Alembic is a database schema migration tool for SQLAlchemy applications. It manages a migration environment on disk, generates revision files, runs upgrade and downgrade functions against a database connection, and records applied revisions in a version table.

The central state is the relationship between three public views:

- a migration script directory containing `env.py`, `script.py.mako`, and revision files;
- an Alembic configuration loaded from `alembic.ini`, `pyproject.toml`, or programmatic values;
- a target database schema and version-table state.

Alembic exposes this state through a command line interface, the `alembic.command` Python API, runtime objects used by `env.py`, migration operation directives imported from `alembic.op`, script-directory inspection APIs, and autogenerate comparison output.

## Scope

This package provides the behavior needed for local migration workflows:

- creating a migration environment;
- reading Alembic configuration from files and programmatic settings;
- creating and inspecting revision files;
- running upgrades, downgrades, stamps, current/head/history queries, and offline SQL generation;
- exposing `alembic.context` inside `env.py`;
- exposing `alembic.op` inside migration scripts;
- tracking linear and branched revision graphs;
- comparing SQLAlchemy `MetaData` against a database schema for autogenerate;
- rendering and executing common schema operation directives;
- supporting batch mode for table recreation workflows.

SQLite-backed workflows must work without external services. Dialect-specific SQL rendering may be supported where SQLAlchemy can render it locally, but live PostgreSQL, MySQL, MSSQL, or Oracle servers are not required.

## Installable Surface

The distribution provides an importable `alembic` package:

```python
import alembic
from alembic import command
from alembic import context
from alembic import op
```

The package exposes a console command named `alembic`.

Documented public import paths include:

```python
from alembic.config import Config
from alembic.config import CommandLine
from alembic.runtime.environment import EnvironmentContext
from alembic.runtime.migration import MigrationContext
from alembic.operations import Operations
from alembic.operations import BatchOperations
from alembic.script import ScriptDirectory
from alembic.script import Script
from alembic.script.revision import Revision
from alembic.script.revision import RevisionMap
from alembic.autogenerate import compare_metadata
from alembic.autogenerate import render_python_code
from alembic.util import CommandError
```

`alembic.__version__` is a string version identifier. `alembic.context` and `alembic.op` behave as proxy modules: user code imports names from them like normal modules, but calls are routed to the active environment or operations context.

## Configuration

`Config` represents the configuration passed to Alembic commands and environments.

```python
Config(
    file_=None,
    toml_file=None,
    ini_section="alembic",
    output_buffer=None,
    stdout=sys.stdout,
    cmd_opts=None,
    config_args={},
    attributes=None,
)
```

Required behavior:

- `file_` points to an ini-style Alembic configuration file.
- `toml_file` points to a `pyproject.toml` file containing Alembic settings.
- `ini_section` selects the primary ini section and defaults to `alembic`.
- `stdout` receives command output produced through `Config.print_stdout()`.
- `output_buffer` receives offline SQL output when command execution is configured for SQL mode.
- `config_args` are copied into independent substitution dictionaries for ini and toml parsing.
- `%(here)s` resolves to the directory containing the corresponding configuration file.
- `attributes` stores arbitrary Python objects for use by `env.py`, such as a shared SQLAlchemy connection.
- Programmatic configuration supports `set_main_option()`, `set_section_option()`, `get_main_option()`, `get_section_option()`, and `get_section()`.
- `get_alembic_option()` reads Alembic options from ini/toml sources using Alembic's precedence rules.

Configuration options used by migration workflows include `script_location`, `sqlalchemy.url`, `version_locations`, `path_separator`, `prepend_sys_path`, `file_template`, `truncate_slug_length`, `timezone`, `recursive_version_locations`, `revision_environment`, `sourceless`, `version_table`, and `version_table_schema`.

`script_location` may be a filesystem path or a package resource location. When `ScriptDirectory.from_config(config)` is used, the option is required.

## Command Line Interface

The `alembic` command accepts a config file, optional named section, verbosity flags, arbitrary `-x` arguments for `env.py`, and a subcommand. CLI subcommands correspond to functions in `alembic.command`.

Core commands:

```text
alembic init [--template TEMPLATE] [--package] DIRECTORY
alembic list_templates
alembic revision [-m MESSAGE] [--autogenerate] [--sql] [--head REV] [--splice]
                 [--branch-label LABEL] [--version-path PATH]
                 [--rev-id REV_ID] [--depends-on REV]
alembic merge REVISION [REVISION ...] [-m MESSAGE] [--branch-label LABEL]
alembic upgrade REVISION [--sql] [--tag TAG]
alembic downgrade REVISION [--sql] [--tag TAG]
alembic current [--verbose] [--check-heads]
alembic history [REV_RANGE] [--verbose] [--indicate-current]
alembic heads [--verbose] [--resolve-dependencies]
alembic branches [--verbose]
alembic show REV
alembic stamp REVISION [--sql] [--tag TAG] [--purge]
alembic ensure_version [--sql]
alembic check
```

Required behavior:

- `init` creates a migration environment directory, a `versions` directory, template files, and a configuration file when the target is empty. When package mode is enabled, it writes `__init__.py` marker files in the environment directory and in the `versions` directory.
- `list_templates` writes available environment templates and their descriptions to configured stdout.
- `revision` creates a new revision script; with `--autogenerate`, it compares target metadata against the database and writes candidate operation directives.
- `upgrade` and `downgrade` run revision functions selected by the requested target.
- `--sql` mode writes SQL text instead of mutating the database.
- `current`, `history`, `heads`, `branches`, and `show` report database or script-directory revision state through stdout.
- `stamp` changes version-table state without running migration functions.
- `merge` creates a revision file that merges multiple heads.
- `ensure_version` creates the version table if needed.
- `check` reports whether autogenerate sees pending upgrade operations.
- Invalid revision ranges, missing configuration, missing templates, ambiguous heads, and impossible graph movements raise `CommandError` or a documented Alembic exception.

## Python Command API

Every command API function accepts a `Config` object as its first argument and follows the same behavior as the corresponding CLI command:

```python
command.list_templates(config)
command.init(config, directory, template="generic", package=False)
command.revision(
    config, message=None, autogenerate=False, sql=False, head="head",
    splice=False, branch_label=None, version_path=None, rev_id=None,
    depends_on=None, process_revision_directives=None,
)
command.merge(config, revisions, message=None, branch_label=None, rev_id=None, splice=False)
command.upgrade(config, revision, sql=False, tag=None)
command.downgrade(config, revision, sql=False, tag=None)
command.show(config, rev)
command.history(config, rev_range=None, verbose=False, indicate_current=False)
command.heads(config, verbose=False, resolve_dependencies=False)
command.branches(config, verbose=False)
command.current(config, check_heads=False, verbose=False)
command.stamp(config, revision, sql=False, tag=None, purge=False)
command.edit(config, rev)
command.ensure_version(config, sql=False)
command.check(config)
```

`command.revision()` and `command.merge()` return the created `Script` when one file is generated, a list when multiple files are generated, or `None` when output is written in SQL mode or no script is produced.

The command API must allow callers to share a SQLAlchemy connection through `config.attributes["connection"]` when the environment script is written to consume it.

`command.init(..., package=True)` creates Python package marker files in both the migration environment directory and its `versions` directory.

## Migration Environment

A migration environment contains:

```text
alembic.ini or pyproject.toml
migrations/
  env.py
  README
  script.py.mako
  versions/
    <revision>_<slug>.py
```

The directory name is configurable. `env.py` is run when commands need database or migration runtime behavior. It configures the migration context, opens transactions, and calls `run_migrations()`.

Revision files contain module-level identifiers:

```python
revision = "..."
down_revision = "..."  # or None, tuple/list for multiple parents
branch_labels = None   # or a string/collection
depends_on = None      # or a string/collection

def upgrade():
    ...

def downgrade():
    ...
```

The revision graph is determined by these identifiers, not by filename ordering. A revision with `down_revision is None` is a base. A revision with no children is a head. Multiple heads represent branches. A merge revision has multiple down revisions.

## Runtime Context

`EnvironmentContext` is the API used inside `env.py` and is made available through `alembic.context`.

Important methods and properties:

```python
context.configure(...)
context.begin_transaction()
context.run_migrations(**kw)
context.is_offline_mode()
context.is_transactional_ddl()
context.get_context()
context.get_bind()
context.get_head_revision()
context.get_head_revisions()
context.get_revision_argument()
context.get_starting_revision_argument()
context.get_tag_argument()
context.get_x_argument(as_dictionary=False)
context.static_output(text)
```

Required behavior:

- `configure()` establishes a `MigrationContext` using a connection, URL, dialect name, or dialect object.
- `target_metadata` may be a SQLAlchemy `MetaData` object or a sequence of metadata objects for autogenerate.
- `as_sql`/offline mode writes SQL to the configured output buffer and does not require a live connection.
- `transactional_ddl` and `transaction_per_migration` control how logical migration transactions are represented.
- `include_name`, `include_object`, `include_schemas`, `compare_type`, `compare_server_default`, `render_item`, `process_revision_directives`, `literal_binds`, `upgrade_token`, and `downgrade_token` affect autogenerate and rendering.
- `get_x_argument(False)` returns raw values passed with `-x`; `get_x_argument(True)` parses `key=value` items into a dictionary and stores key-only arguments with an empty string value.
- `get_tag_argument()` returns the command tag passed to upgrade, downgrade, or stamp.
- `get_context()` raises if `configure()` has not been called.
- `run_migrations(**kw)` passes keyword arguments through to revision `upgrade()` or `downgrade()` functions when templates accept them.

`MigrationContext` represents active migration execution or inspection.

```python
MigrationContext.configure(connection=None, url=None, dialect_name=None, dialect=None, environment_context=None, dialect_opts=None, opts=None)
```

Required behavior:

- Online contexts execute SQL against the configured SQLAlchemy connection.
- Offline contexts write SQL text to the output buffer.
- `get_current_heads()` returns a tuple of current version-table heads; it returns an empty tuple when no version table or no revisions are present.
- `get_current_revision()` returns a single current revision, `None` when absent, and raises when multiple current heads are present.
- In offline mode, current-head methods reflect `starting_rev` when supplied.
- `begin_transaction()` returns a context manager representing Alembic's logical transaction behavior.
- `execute(sql, execution_options=None)` emits a SQLAlchemy executable or SQL string through the active online/offline path.
- `stamp(script_directory, revision)` updates version-table state as if the graph moved to the target revision.
- `autocommit_block()` is a context manager for migration operations that need database autocommit behavior.

## Operations API

Migration scripts import operation directives through `alembic.op`:

```python
from alembic import op
```

`alembic.op` proxies to an active `Operations` object. The same directives are available as methods on `Operations` and, inside batch mode, on `BatchOperations`.

Common directives include:

```python
op.add_column(table_name, column, schema=None)
op.drop_column(table_name, column_name, schema=None)
op.alter_column(table_name, column_name, nullable=None, server_default=False,
                new_column_name=None, type_=None, existing_type=None,
                existing_server_default=False, existing_nullable=None,
                schema=None, **kw)
op.create_table(table_name, *columns, **kw)
op.drop_table(table_name, schema=None, **kw)
op.create_index(index_name, table_name, columns, unique=False, schema=None, **kw)
op.drop_index(index_name, table_name=None, schema=None, **kw)
op.create_unique_constraint(name, table_name, columns, schema=None, **kw)
op.create_foreign_key(name, source_table, referent_table, local_cols, remote_cols, **kw)
op.create_primary_key(name, table_name, columns, schema=None)
op.create_check_constraint(name, table_name, condition, schema=None, **kw)
op.drop_constraint(name, table_name, type_=None, schema=None)
op.execute(sqltext, execution_options=None)
op.get_bind()
op.get_context()
op.inline_literal(value, type_=None)
op.bulk_insert(table, rows, multiinsert=True)
```

Required behavior:

- Directives build SQLAlchemy schema constructs where appropriate and emit them through the active `MigrationContext`.
- Online mode executes against the current connection.
- Offline mode renders SQL text to the configured output buffer.
- `get_context()` returns the current `MigrationContext`; `get_bind()` returns the active connection in online mode.
- `execute()` accepts SQL strings and SQLAlchemy executable objects.
- `inline_literal()` renders values suitable for offline SQL generation.
- `bulk_insert()` inserts rows online and renders insert SQL offline.
- Constraint and index operations accept schemas and table names in the same user-facing form documented for Alembic.
- Unsupported combinations should fail with an Alembic/SQLAlchemy exception rather than silently producing incorrect migration state.

## Batch Mode

Batch mode is entered with:

```python
with op.batch_alter_table("some_table", schema=None, recreate="auto", copy_from=None, table_args=(), table_kwargs={}, reflect_args=(), reflect_kwargs={}, naming_convention=None) as batch_op:
    batch_op.add_column(...)
    batch_op.drop_column(...)
    batch_op.alter_column(...)
```

Required behavior:

- The context manager yields a `BatchOperations` object.
- Batch directives apply to the named table without requiring the table name on each directive.
- On SQLite and for operations that require table recreation, Alembic can create a temporary replacement table, copy data, drop the old table, and rename the replacement.
- In non-recreate cases, batch mode may emit ordinary ALTER statements.
- Naming conventions may be supplied so unnamed reflected constraints can be addressed consistently.

## Script Directory And Revision Graph

`ScriptDirectory` provides programmatic access to revision files.

```python
script = ScriptDirectory.from_config(config)
script.walk_revisions(base="base", head="heads")
script.iterate_revisions(upper, lower, **kw)
script.get_revision(id_)
script.get_revisions(id_or_sequence)
script.as_revision_number(id_)
script.get_current_head()
script.get_heads(consider_depends_on=False)
script.get_base()
script.get_bases()
script.generate_revision(revid, message, head=None, splice=False,
                         branch_labels=None, version_path=None,
                         file_template=None, depends_on=None, **kw)
script.run_env()
```

Required behavior:

- `from_config()` reads `script_location` and related version-location options from `Config`.
- Symbolic names include `base`, `head`, and `heads`.
- Partial revision identifiers resolve when unambiguous.
- Ambiguous, missing, cyclic, or graph-inconsistent revisions raise Alembic revision errors or `CommandError`.
- `walk_revisions()` yields `Script` objects in graph traversal order.
- `iterate_revisions(upper, lower)` walks from an upper revision toward a lower revision according to down-revision links.
- `get_current_head()` returns a single head and raises when multiple heads exist.
- `get_heads()` returns a list of string revision identifiers for all current script heads. The list normally has one item for a linear graph and multiple items when multiple current heads exist.
- `get_base()` returns a single base and raises when multiple bases exist.
- `get_bases()` returns a list of string revision identifiers for all bases.
- `generate_revision()` renders `script.py.mako` and writes a revision file using the configured filename template, message slug, branch labels, dependencies, and version path.
- `run_env()` executes the environment's `env.py`.

`Script` objects expose the revision identifier, down revisions, branch labels, dependencies, path, module, docstring/log entry, and graph properties such as whether a script is a head, base, branch point, or merge point.

## Autogenerate

Autogenerate compares the current database schema to application `MetaData` and produces candidate migration operations.

Required behavior:

- `alembic revision --autogenerate` and `command.revision(..., autogenerate=True)` use `EnvironmentContext.configure(target_metadata=...)`.
- `compare_metadata(context, metadata)` compares a configured `MigrationContext` against SQLAlchemy `MetaData` and returns operation-difference structures describing observable schema differences.
- Added and removed tables are detected.
- Added and removed columns are detected.
- Nullable changes are detected.
- Basic index changes and explicitly named unique constraints are detected.
- Basic foreign key constraint changes are detected.
- Type comparison is enabled by default and can be disabled or customized with `compare_type`.
- Server-default comparison is disabled by default and can be enabled or customized with `compare_server_default`.
- Table and column renames are represented as add/drop pairs; users are expected to edit them into renames.
- Anonymous constraints cannot be reliably compared and should be named by the user.
- Multiple `MetaData` objects are accepted as a sequence; duplicate table keys across the sequence are an error.
- `include_name`, `include_object`, and `include_schemas` filter what is considered.
- `process_revision_directives` can inspect or mutate generated revision directives before scripts are written.
- `render_python_code()` renders operation directive structures as Python migration code for inspection or custom workflows.

Autogenerate output is a candidate migration, not a promise that every possible schema change is detected.

## Offline SQL

Offline mode is selected by CLI `--sql` or by configuring the runtime for SQL output.

Required behavior:

- Upgrade, downgrade, stamp, ensure-version, and revision SQL workflows write SQL text to the output buffer or stdout instead of applying database changes.
- Offline mode can use a dialect name or URL to determine SQL rendering.
- Range syntax such as `start:end` is meaningful for upgrade/downgrade SQL generation.
- `starting_rev` is visible through runtime context methods for offline scripts.
- `static_output(text)` writes text directly to the offline stream without treating it as an executable SQL statement.
- Literal bind rendering is available when configured for offline SQL generation.

## Error Semantics

Alembic-specific errors are importable from documented public modules. `CommandError` is the common user-facing error for invalid command usage or invalid migration state.

Required triggers:

- Missing `script_location` when constructing a `ScriptDirectory` from `Config` raises `CommandError`.
- `init` on a non-empty target directory raises `CommandError`.
- Unknown init templates raise `CommandError`.
- A single-head query on a script directory with multiple heads raises `CommandError`.
- A single-current-revision query on a database with multiple current heads raises `CommandError`.
- Revision ranges that are only valid in SQL mode raise `CommandError` when used in online upgrade/downgrade commands.
- Missing or ambiguous revision identifiers raise Alembic revision errors or are wrapped as `CommandError` in command-facing APIs.
- Autogenerate without enough database/configuration context raises a user-facing Alembic/SQLAlchemy error instead of generating misleading output.

Exact exception message text is not part of the public contract.

## Cross-View Invariants

- A revision file created by `revision` is visible through `ScriptDirectory` inspection without requiring database access.
- The heads reported by CLI `heads`, `command.heads()`, and `ScriptDirectory.get_heads()` describe the same script graph.
- Upgrading a database to a head changes the version table so `current` and `MigrationContext.get_current_heads()` report that head.
- Stamping changes version-table state without running revision `upgrade()` or `downgrade()` functions.
- Offline upgrade SQL describes the same graph movement that online upgrade would apply, but it writes text instead of mutating the database.
- `alembic.context` inside `env.py` and a directly held `EnvironmentContext` expose the same configured migration context.
- `alembic.op` directives inside a revision script and an explicit `Operations` object bound to the same `MigrationContext` emit through the same online/offline execution path.
- Autogenerate compares database schema to `target_metadata`; generated operation directives must correspond to observable schema differences after filters are applied.
- Branch labels, dependencies, bases, and heads must be consistent across generated files, script graph traversal, command output, and version-table movement.
- Configuration values loaded from files and values set programmatically must lead to the same migration behavior when they describe the same script location, database URL, and runtime options.

## Representative Workflow

Create and run a small SQLite migration project:

```python
from pathlib import Path
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine
from alembic.config import Config
from alembic import command

project = Path("demo")
project.mkdir()

cfg = Config(str(project / "alembic.ini"))
command.init(cfg, str(project / "migrations"))

cfg = Config(str(project / "alembic.ini"))
cfg.set_main_option("script_location", str(project / "migrations"))
cfg.set_main_option("sqlalchemy.url", "sqlite:///demo.db")

metadata = MetaData()
Table("account", metadata, Column("id", Integer, primary_key=True), Column("name", String(50)))

# env.py should configure target_metadata=metadata and call context.run_migrations().
script = command.revision(cfg, message="create account", autogenerate=True)
command.upgrade(cfg, "head")
command.current(cfg)
command.downgrade(cfg, "base")
```

The generated revision file belongs to the script directory, `upgrade()` applies schema changes and updates the version table, `current` reports the applied revision after upgrade, and `downgrade("base")` returns the database to the base revision state.

## Non-Goals

- No requirement to reproduce private helper modules, private object layouts, or internal testing utilities.
- No requirement to match exact status-message wording, log formatting, traceback text, or generated whitespace beyond valid and equivalent user-facing output.
- No requirement to support live external database servers.
- No requirement to implement every backend-specific DDL nuance when it cannot be exercised through SQLAlchemy's local dialect rendering or SQLite.
- No requirement to clone Alembic's internal source layout.
- No requirement for autogenerate to infer table or column renames as renames.
- No requirement to support undocumented environment templates, undocumented hooks, or private extension points.

## Evaluation Notes

Validation focuses on observable behavior through the public interfaces described above. Checks exercise configuration loading, environment creation, command API behavior, CLI behavior, revision graph inspection, version-table movement, runtime context access, operation directive execution/rendering, offline SQL output, autogenerate comparison, and batch-mode table alteration.

A correct implementation should preserve behavior across views: files produced on disk should be visible to script-directory APIs, database version state should match command output, and operation directives should affect online and offline migration output consistently. Equivalent SQLAlchemy constructs and semantically equivalent generated files are acceptable; private object shapes and exact internal formatting are not part of the contract.
