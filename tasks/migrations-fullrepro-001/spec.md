# Schema Migrations Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`mybatis-migrations` is a Java database-change management tool that keeps ordered forward and reverse SQL changes in a filesystem repository and records applied changes in a database changelog. It exposes the `migrate` command for repository management, online schema movement, status reporting, and offline script generation, plus a Java runtime API for applying the same migration model during application startup.

The installable Maven coordinates are `org.mybatis:mybatis-migrations`. The command runner is `org.apache.ibatis.migration.Migrator`.

## Non-Goals

- This specification does not require private command helpers, classpath-scanning utilities, JDBC driver adapters, console-color constants, or their internal layouts.
- This specification does not define exact banners, timing lines, memory statistics, exception-message wording, ANSI escape sequences, or object representations.
- This specification does not require external database servers; JDBC behavior is exercised with an in-process database.
- This specification does not require JSR-223 engines beyond those present in the environment or optional JDBC drivers not supplied by callers.
- This specification does not define direct programmatic use of command implementation classes, option-parsing carriers, low-level readers, variable-substitution helpers, JDBC script runners, or changelog persistence helpers.
- This specification does not require rollback support for `bootstrap.sql`, because bootstrap state is neither a migration entry nor an undoable changelog item.

## Representative Workflows

### Initialize and evolve a repository

```text
mkdir app-db
cd app-db
migrate init
migrate new "create account table"
migrate up
migrate status
migrate down
```

Initialization creates the repository files. The new command creates an ordered SQL migration with DO and UNDO sections. Applying and undoing the change updates both the database schema and the changelog projected by status.

### Upgrade during application startup

```java
import org.apache.ibatis.migration.DataSourceConnectionProvider;
import org.apache.ibatis.migration.JavaMigrationLoader;
import org.apache.ibatis.migration.operations.UpOperation;

new UpOperation().operate(
    new DataSourceConnectionProvider(dataSource),
    new JavaMigrationLoader("com.example.db.migrations"),
    null,
    System.out);
```

Migration classes in the selected package provide ordered IDs, descriptions, and SQL. The operation obtains a JDBC connection, executes only eligible forward scripts, and records each applied change.

### Generate an offline delta

```text
migrate --path=/srv/app-db script 0 202608150003 > upgrade.sql
migrate --path=/srv/app-db script 202608150003 0 > rollback.sql
```

The first command emits forward SQL through the upper version, while the second emits the corresponding reverse SQL in rollback order. Script generation reads repository state without applying changes to the database.

## Repository and Environment Configuration

This section defines the workspace, environment selection, and configuration precedence that make repository commands repeatable across machines.

**Repository initialization.**

- When `migrate init` targets an absent or empty base directory, the command must create the base directory, `drivers`, `environments`, and `scripts`, then create a README, `environments/development.properties`, `scripts/bootstrap.sql`, the changelog-creation migration, and a first migration template.
- If the initialization target contains any non-hidden entry, then `migrate init` must fail without replacing that entry.
- The `--path` option must select the repository base directory and must default to the current working directory.
- The `--env` option must select `environments/<environment>.properties` and must default to `development`.
- The `--envpath`, `--scriptpath`, `--driverpath`, and `--hookpath` options must replace the corresponding derived repository directories when explicitly present.
- If a database command targets a base path that is absent or is not a directory, then the command must report the invalid path and must not run the operation.

**Environment properties.**

- The environment file must support `time_zone`, `script_char_set`, `driver`, `url`, `username`, `password`, `changelog`, `auto_commit`, `delimiter`, `full_line_delimiter`, `send_full_script`, `remove_crs`, `ignore_warnings`, `driver_path`, and the hook keys described below.
- The environment must default `time_zone` to `GMT+0:00`, `script_char_set` to the platform default charset, `changelog` to `CHANGELOG`, `delimiter` to `;`, and `ignore_warnings` to `true`; its remaining boolean settings must default to `false`.
- Where a process environment variable named `MIGRATIONS_<KEY>` is present, the environment must replace the same lower-case file property with that value.
- Where a Java system property named `MIGRATIONS_<KEY>` is present, the environment must replace both the file property and the process-environment value for that key.
- The environment must expose non-setting properties through `getVariables()` for `${name}` substitution in scripts and templates.
- An `Environment` constructed with `file` must expose the resolved settings through `getTimeZone()`, `getDelimiter()`, `getScriptCharset()`, `isFullLineDelimiter()`, `isSendFullScript()`, `isAutoCommit()`, `isRemoveCrs()`, `isIgnoreWarnings()`, `getDriverPath()`, `getDriver()`, `getUrl()`, `getUsername()`, `getPassword()`, all fourteen named hook getters, and `getVariables()`.
- If the selected environment file is absent or unreadable, then environment construction must raise `MigrationException`.

**Statement execution settings.**

- When `send_full_script` is `true`, a database operation must send the selected script as one JDBC statement; when it is `false`, the operation must split commands according to `delimiter` and `full_line_delimiter`.
- When `full_line_delimiter` is `false`, the delimiter must terminate a command at the end of a line; when it is `true`, a line containing only the delimiter must terminate the command.
- When `auto_commit` is `false`, successful script execution must commit as an operation unit and a failed statement must roll back the active unit; when it is `true`, statements must use JDBC auto-commit.
- When `ignore_warnings` is `false`, a JDBC warning must fail the operation; when it is `true`, warnings must not interrupt it.
- If a selected script ends with an unterminated command while line-by-line execution is active, then execution must raise `MigrationException`.

## Migration Files and Loaders

This section defines how migration identities, SQL sections, variables, and Java classes become the ordered change stream consumed by lifecycle operations.

**Filesystem migrations.**

- A required `FileMigrationLoader` construction form must accept, in order, `scriptsDir` as a `java.io.File`, `charset` as a nullable charset-name `String`, and `variables` as `java.util.Properties`.
- When `charset` is non-null, the file loader must resolve that name as the reader charset.
- When `charset` is `null`, the file loader must read scripts with the platform default charset.
- A filesystem migration name must have a numeric ID prefix, an underscore-separated description, and the `.sql` suffix; the loader must expose the numeric prefix as `Change.id`, spaces in place of description underscores, and the original name as `Change.filename`.
- The file loader must sort migration names in ascending filename order and must omit non-SQL files, `bootstrap.sql`, and `onabort.sql` from `getMigrations()`.
- When `getScriptReader(change, false)` is requested, the loader must return the script content above the `-- //@UNDO` marker; when `getScriptReader(change, true)` is requested, it must return the content below that marker.
- When a selected script contains `${name}` and the loader properties define `name`, the returned reader must replace the token in both DO and UNDO sections.
- If a migration filename does not contain a valid numeric prefix, then the file loader must raise `MigrationException` when discovering it.
- The file loader must return a reader for existing `bootstrap.sql` or `onabort.sql` and must return `null` when the requested special script is absent.

**Generated migration files.**

- When `migrate new <description>` runs without `--idpattern`, the command must create a timestamp-prefixed `.sql` file whose remaining name replaces description spaces with underscores.
- Where `--idpattern` or the `idpattern` global property is present, `init` and `new` must generate the next numeric ID formatted by that decimal pattern.
- The generated migration must contain the description, a forward section, and the `-- //@UNDO` boundary followed by a reverse section.
- Where `--template=<path>` is present, `new` must use that external template and replace `${description}` with the supplied description.
- Where `new_command.template` is configured and `--template` is absent, `new` must resolve that template relative to `MIGRATIONS_HOME`.
- If no description is supplied, the selected environment is unavailable, or an explicitly selected template cannot be read, then `new` must raise `MigrationException` without creating a completed migration file.

**Java and custom loaders.**

- A `MigrationScript` implementation must return a unique `BigDecimal` ID, a short description, forward SQL from `getUpScript()`, and reverse SQL from `getDownScript()`.
- A `JavaMigrationLoader` must discover concrete `MigrationScript` implementations in its `packageNames`, instantiate them, expose their class names as `Change.filename`, and return changes ordered by numeric ID to consuming operations.
- When a Java loader is constructed with `classLoader`, discovery must use that loader; otherwise it must use the ordinary application classpath.
- A Java loader must return the selected class's forward or reverse SQL from `getScriptReader`, a sole `BootstrapScript` from `getBootstrapReader`, and a sole `OnAbortScript` from `getOnAbortReader`.
- If more than one implementation exists for a requested `BootstrapScript` or `OnAbortScript`, or a selected script class cannot be instantiated, then the Java loader must raise `MigrationException`.
- A custom `FileMigrationLoaderFactory` must be discoverable through `/META-INF/services/org.apache.ibatis.migration.FileMigrationLoaderFactory` and must return a `MigrationLoader` from the selected paths and environment.

## Schema Lifecycle Operations

This section defines how ordered repository changes move the database forward, backward, to a target version, or through an untracked bootstrap baseline.

**Applying changes.**

- When `up` runs without a step count, it must apply every migration whose ID is greater than the latest applied changelog ID, in ascending ID order.
- Where a positive step count is present, `up` must stop after that many eligible migrations.
- For every successfully applied migration, `up` must execute its forward SQL and insert its ID, application timestamp, and description into the changelog.
- If the `UpOperation` step count is less than one, then construction must raise `IllegalArgumentException`.
- When an up operation fails and the loader returns an on-abort reader, the operation must execute the on-abort SQL before raising `MigrationException`.

**Undoing and redoing changes.**

- When `down` runs without a step count, it must execute the reverse SQL of the latest applied migration and remove that migration from the changelog.
- Where a step count is present, `down` must repeat that behavior from newest to oldest until the count is reached or removing the changelog prevents further undo.
- When `redo` runs without a step count, it must perform one down step followed by one up step; where a count is present, it must use that count for both directions.
- A completed redo must leave the same set of applied migration IDs while re-executing both reverse and forward SQL for the selected tail.

**Targeting and out-of-order changes.**

- When `version <id>` names a repository migration above the current version, the operation must apply eligible migrations through that ID inclusively.
- When `version <id>` names a repository migration below the current version, the operation must undo applied migrations above that ID and must leave the named version applied.
- When the database is already at the requested version, the version operation must leave schema and changelog state unchanged.
- If the requested version is absent from the loader's migration set, then `VersionOperation` must raise `MigrationException`.
- When `pending` runs, it must apply every repository migration missing from the changelog in ascending ID order, including migrations whose IDs are below an already applied migration.
- If the changelog table does not exist, then `pending` must raise `MigrationException` and must direct no migration SQL to the database.

**Bootstrap baseline.**

- When `bootstrap` runs before the changelog exists and the loader supplies a bootstrap reader, it must execute that SQL without inserting a changelog row.
- When the changelog exists and force is `false`, bootstrap must leave database state unchanged.
- Where force is `true`, bootstrap must execute the available bootstrap SQL even when the changelog exists.
- When no bootstrap script exists, the bootstrap operation must return without applying SQL and must report the missing script through its output stream.

## Status and Offline Script Projections

This section defines read-oriented projections of repository and database state without changing the selected migration set.

**Status projection.**

- When status runs without a changelog table, it must return every discovered repository migration as pending.
- When status runs with a changelog table, it must combine repository migrations and changelog rows by numeric ID, marking repository-only changes pending, shared changes applied, and changelog-only changes missing.
- `StatusOperation` must expose the combined ordered list through `getCurrentStatus()` and matching totals through `getAppliedCount()`, `getPendingCount()`, and `getMissingCount()`.
- The `status` command must print each combined change in ascending ID order, including its ID, applied timestamp or pending state, and description.

**Offline delta generation.**

- When `script <lower> <upper>` has `lower < upper`, it must emit the forward sections with IDs greater than `lower` and less than or equal to `upper`, in ascending order.
- When `script <upper> <lower>` has the first version greater than the second, it must emit the reverse sections over the same exclusive/inclusive boundary in descending rollback order.
- When the lower boundary is `0`, forward generation must include the first migration; when the destination is `0`, reverse generation must include the first migration's undo section.
- When `script pending` runs, it must emit forward SQL for the pending tail after the last applied migration; when `script pending_undo` runs, it must emit the corresponding reverse SQL.
- If the two explicit script versions are equal, absent from the repository, nonnumeric, or supplied with an invalid argument count, then the command must fail without emitting a completed delta.
- Script generation must write SQL to standard output and must not update the schema or changelog.

## Migration Hooks

This section defines configurable before/after scripts and the public context projected into operation, per-change, new-file, and offline-script hooks.

**Hook configuration and order.**

- The environment must recognize `hook_before_up`, `hook_before_each_up`, `hook_after_each_up`, `hook_after_up`, the corresponding four `down` keys, `hook_before_new`, `hook_after_new`, and the corresponding four `script` keys.
- A hook value must contain a language and filename separated by `:`, followed by zero or more `name=value` bindings.
- Up, down, and pending operations with eligible changes must invoke `before` once, `beforeEach` and `afterEach` around every selected migration, and `after` once, in that order.
- When an up or down operation selects no migration, its operation hooks must not execute.
- New hooks must run before and after file creation with a `NewHookContext`; script hooks must surround delta generation with a `ScriptHookContext` describing the selected change and direction.
- If a before-new hook raises, then the new command must fail before creating the migration file.

**Hook bindings and contexts.**

- `MigrationHook` must define callbacks named `before`, `beforeEach`, `afterEach`, and `after`.
- Each `MigrationHook` callback must accept a `java.util.Map<String,Object>` bindings map and must return no value.
- The `before` and `after` callbacks must receive an operation-level `HookContext` under `MigrationHook.HOOK_CONTEXT`, while `beforeEach` and `afterEach` must receive a defensive per-change `HookContext` under that key.
- Every hook binding map must expose its context under `MigrationHook.HOOK_CONTEXT`, whose value is the string `hookContext`.
- An operation-level `HookContext` must expose a `null` change, while each-change hooks must expose a defensive `Change` copy through `getChange()`.
- `HookContext.getConnection()` must return a new caller-closeable JDBC connection, and `executeSql(Reader)` and `executeSql(String)` must execute SQL through the active operation runner.
- `NewHookContext` must return the supplied description and generated filename; before-new observes the name before the file exists.
- `ScriptHookContext` must return the selected `Change` and must expose whether the projection is an undo through `isUndo()`.
- Hook scripts must receive repository paths as `migrationPaths`, environment variables as global bindings, and explicitly configured bindings as overrides for the selected hook.
- Where `_function` and repeated `_arg` bindings are present for a JSR-223 hook, the hook must invoke the named top-level function with those arguments.
- Where `_object`, `_method`, and repeated `_arg` bindings are present for a JSR-223 hook, the hook must invoke the named object's method with those arguments.
- If a configured hook language, file, function, object, or method cannot be resolved or executed, then the enclosing command or operation must raise `MigrationException`.

## Programmatic Runtime API

This section defines the public Java collaborators that let applications execute the migration lifecycle without invoking the command shell.

**Connections and operation parameters.**

- A `SelectedPaths` instance must default `basePath` to the current directory and must derive `envPath`, `scriptPath`, `driverPath`, and `hookPath` as `environments`, `scripts`, `drivers`, and `hooks` beneath it until `setBasePath()`, `setEnvPath()`, `setScriptPath()`, `setDriverPath()`, or `setHookPath()` supplies an override returned by its matching getter.
- `ConnectionProvider.getConnection()` must return the JDBC connection used by an operation and must propagate `SQLException` from acquisition.
- A `DataSourceConnectionProvider` must obtain each requested connection from its constructor-supplied `DataSource`.
- A `JdbcConnectionProvider` must load and register its constructor-supplied driver class, then obtain connections from `DriverManager` using `url`, `username`, and `password`; its overload with `classLoader` must load the driver through that loader.
- If a JDBC driver class cannot be loaded or instantiated, then `JdbcConnectionProvider` construction must raise `IllegalStateException`.
- A `DatabaseOperationOption` must default to changelog table `CHANGELOG`, stop-on-error enabled, warning failure enabled, auto-commit disabled, send-full-script disabled, CR removal disabled, escape processing enabled, full-line delimiter disabled, and delimiter `;`.
- The `DatabaseOperationOption` pairs `getChangelogTable()`/`setChangelogTable()`, `isStopOnError()`/`setStopOnError()`, `isThrowWarning()`/`setThrowWarning()`, `isAutoCommit()`/`setAutoCommit()`, `isSendFullScript()`/`setSendFullScript()`, `isRemoveCRs()`/`setRemoveCRs()`, `isEscapeProcessing()`/`setEscapeProcessing()`, `isFullLineDelimiter()`/`setFullLineDelimiter()`, and `getDelimiter()`/`setDelimiter()` must expose the active values; a `null` option supplied to a lifecycle `operate` method must select the defaults.

**Change values and operation results.**

- `Change` must expose mutable properties through `getId()`/`setId()`, `getDescription()`/`setDescription()`, `getAppliedTimestamp()`/`setAppliedTimestamp()`, and `getFilename()`/`setFilename()`, and its copy constructor must copy all four values.
- `Change` must support construction from a `BigDecimal` `id` alone, and `getId()` must immediately return that value.
- `Change` must support construction from a `BigDecimal` `id`, followed by a `String` `appliedTimestamp`, followed by a `String` `description`, and the matching getters must immediately return those values.
- `Environment.CHANGELOG` must equal the string `changelog` used as the public variable key for changelog-table selection.
- `Change` equality, hashing, and natural ordering must use the numeric ID so loaders and changelog views match changes independently of description, timestamp, and filename.
- `UpOperation` and `DownOperation` must each provide a hook-aware `operate` form whose arguments are, in order, a `ConnectionProvider`, a `MigrationLoader`, a `DatabaseOperationOption`, a `PrintStream`, and a `MigrationHook`.
- When a hook-aware `operate` form completes successfully, it must return the same operation instance and must apply the documented before, per-change, and after callback ordering.
- `UpOperation` and `DownOperation` must each provide a four-argument no-explicit-hook form with the same first four collaborators in the same order.
- Every lifecycle `operate` method must return the same operation instance after successful completion and must close the connection acquired from its provider.
- Where a non-null `PrintStream` is supplied, operations must report their user-facing progress to it; where it is `null`, operations must complete without requiring output.
- If connection, loader, script, or changelog work fails during a lifecycle operation, then the operation must raise `MigrationException` with the underlying cause retained.

## State Model

The core state is the ordered repository migration set paired with the durable changelog rows and database schema produced by their SQL. Public projections include CLI results, runtime operation results, status counts and changes, generated offline SQL, repository files, hook contexts, and the live schema.

- The repository migration order must derive from numeric IDs even when migrations come from filesystem or Java loaders.
- The changelog must represent successfully applied migrations by ID, application timestamp, and description.
- The status projection must derive from the union of repository IDs and changelog IDs without mutating either source.
- The offline script projection must derive from the same DO and UNDO sections as online lifecycle operations without changing database state.
- Hook contexts must describe the same selected change and direction as the surrounding lifecycle or script projection.

## Error Semantics

The following failures form the public error contract.

| Condition | Required result |
|---|---|
| Missing or unreadable environment file | If the environment file is unavailable, then construction must raise `MigrationException`. |
| Invalid or nonempty initialization path | If initialization cannot safely create an empty repository, then `init` must fail without replacing existing content. |
| Missing new-migration description or unreadable explicit template | If required new-file input is invalid, then `new` must raise `MigrationException`. |
| Invalid migration filename or script class | If a loader cannot derive or instantiate a public migration, then it must raise `MigrationException`. |
| Nonpositive up step count | If the `UpOperation` step count is less than one, then construction must raise `IllegalArgumentException`. |
| Missing version target | If a requested target ID is absent, then `VersionOperation` must raise `MigrationException`. |
| Pending operation without a changelog | If no changelog exists, then `PendingOperation` must raise `MigrationException`. |
| JDBC driver setup failure | If the driver cannot be loaded or instantiated, then `JdbcConnectionProvider` must raise `IllegalStateException`. |
| JDBC or script execution failure | If a lifecycle operation cannot complete database work, then it must raise `MigrationException` and retain the cause. |
| Hook resolution or execution failure | If a configured hook cannot be resolved or executed, then the enclosing workflow must raise `MigrationException`. |
| CLI command failure | If command execution fails, then the Java runner must terminate with status `1`; successful commands and help must return status `0`. |

## Cross-View Invariants

1. A migration applied through `migrate up` or `UpOperation.operate()` must produce the same schema effect and changelog identity for the same loader and operation options.
2. A migration present in the changelog must appear as applied in `StatusOperation` and CLI status, while a repository-only migration must appear as pending in both projections.
3. A successful down operation must remove the selected changelog row, update status to pending for a still-present repository migration, and execute the same UNDO section emitted by the corresponding reverse script projection.
4. An offline forward delta and an online up operation over the same ID interval must select the same migration IDs in the same order.
5. Filesystem and Java loaders exposing equal numeric IDs must produce equal `Change` identities and the same lifecycle ordering.
6. A hook's each-change `Change` value must match the migration currently reported to the operation stream and inserted into or removed from the changelog.
7. Environment and `DatabaseOperationOption` settings for changelog name, delimiter, transactions, full-script mode, CR handling, and warnings must affect CLI and runtime operations consistently.
8. A completed redo must preserve the status set of applied IDs while producing both the down and up schema effects for its selected tail.

## Public Interface

### Import Surface

```java
import org.apache.ibatis.migration.BootstrapScript;
import org.apache.ibatis.migration.Change;
import org.apache.ibatis.migration.ConnectionProvider;
import org.apache.ibatis.migration.DataSourceConnectionProvider;
import org.apache.ibatis.migration.Environment;
import org.apache.ibatis.migration.FileMigrationLoader;
import org.apache.ibatis.migration.FileMigrationLoaderFactory;
import org.apache.ibatis.migration.JavaMigrationLoader;
import org.apache.ibatis.migration.JdbcConnectionProvider;
import org.apache.ibatis.migration.MigrationException;
import org.apache.ibatis.migration.MigrationLoader;
import org.apache.ibatis.migration.MigrationScript;
import org.apache.ibatis.migration.Migrator;
import org.apache.ibatis.migration.OnAbortScript;
import org.apache.ibatis.migration.SimpleScript;
import org.apache.ibatis.migration.hook.HookContext;
import org.apache.ibatis.migration.hook.MigrationHook;
import org.apache.ibatis.migration.hook.NewHookContext;
import org.apache.ibatis.migration.hook.ScriptHookContext;
import org.apache.ibatis.migration.operations.BootstrapOperation;
import org.apache.ibatis.migration.operations.DownOperation;
import org.apache.ibatis.migration.operations.PendingOperation;
import org.apache.ibatis.migration.operations.StatusOperation;
import org.apache.ibatis.migration.operations.UpOperation;
import org.apache.ibatis.migration.operations.VersionOperation;
import org.apache.ibatis.migration.options.DatabaseOperationOption;
import org.apache.ibatis.migration.options.SelectedPaths;
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `BootstrapScript` | interface | Supplies the sole Java bootstrap SQL script. |
| `Change` | class | Represents one migration identity and its applied-state metadata. |
| `ConnectionProvider` | interface | Supplies JDBC connections to lifecycle operations. |
| `DataSourceConnectionProvider` | class | Adapts a JDBC `DataSource` to `ConnectionProvider`. |
| `Environment` | class | Loads repository environment properties and hook configuration. |
| `Environment.CHANGELOG` | constant | Names the user-variable key that selects the changelog table. |
| `FileMigrationLoader` | class | Discovers and reads filesystem SQL migrations. |
| `FileMigrationLoaderFactory` | interface | Java SPI for replacing filesystem migration loading. |
| `JavaMigrationLoader` | class | Discovers classpath `MigrationScript` implementations. |
| `JdbcConnectionProvider` | class | Registers a JDBC driver and supplies driver-manager connections. |
| `MigrationException` | exception | Reports migration configuration and execution failures. |
| `MigrationLoader` | interface | Supplies ordered changes and their forward, reverse, bootstrap, and abort readers. |
| `MigrationScript` | interface | Defines a class-based migration's ID, description, and SQL directions. |
| `Migrator` | class | Hosts the public Java `main` entry point. |
| `OnAbortScript` | interface | Supplies the sole Java failure-recovery SQL script. |
| `SimpleScript` | interface | Supplies SQL text for a single class-based special script. |
| `HookContext` | class | Gives operation hooks a change, JDBC access, and SQL execution. |
| `MigrationHook` | interface | Defines operation-level and per-change hook callbacks. |
| `MigrationHook.HOOK_CONTEXT` | constant | Names the binding-map entry that carries the active hook context. |
| `NewHookContext` | class | Describes a generated migration file to new-file hooks. |
| `ScriptHookContext` | class | Describes a change and direction to offline-script hooks. |
| `BootstrapOperation` | class | Applies an untracked baseline schema. |
| `DownOperation` | class | Reverses the latest applied migrations. |
| `PendingOperation` | class | Applies all missing migrations regardless of ordering gaps. |
| `StatusOperation` | class | Projects combined repository and changelog status. |
| `UpOperation` | class | Applies eligible migrations in ascending order. |
| `VersionOperation` | class | Moves schema state to a named migration ID. |
| `DatabaseOperationOption` | class | Configures changelog and JDBC script execution. |
| `SelectedPaths` | class | Holds base, environment, script, driver, and hook directories. |

### CLI Entry Points

- The package must expose console script `migrate` and Java runner `org.apache.ibatis.migration.Migrator`.
- The command surface must contain `info`, `init`, `bootstrap`, `new`, `up`, `down`, `redo`, `version`, `pending`, `status`, and `script`.
- A command must accept its shortest unambiguous leading substring; if a prefix is ambiguous or unknown, then command resolution must fail.
- The option surface must contain `--path`, `--envpath`, `--scriptpath`, `--driverpath`, `--hookpath`, `--env`, `--force`, `--trace`, `--help`, `--template`, `--idpattern`, `--quiet`, and `--color`.
- When `--quiet` is present, the command must suppress operation output; when `--trace` is present, a failure must include cause details.
- When `--help` is present or no command is supplied, the runner must print usage without executing a command.

| Exit | Meaning |
|---:|---|
| 0 | Successful command or help/usage request. |
| 1 | Command resolution, configuration, hook, loader, or database execution failure. |

## Appendix A: Environment

The working environment runs Linux with JDK 17 and Maven 3.9.x without network access. The Maven cache provides JUnit Jupiter, AssertJ, and HSQLDB for the Java runner; the target artifact is not preinstalled. The execution environment provides the same JDK, Maven, and cached assessment dependencies.

The project must declare Maven packaging metadata in `pom.xml` at the project root. The POM must use coordinates `org.mybatis:mybatis-migrations`, produce a Java 11-compatible JAR, register or retain `org.apache.ibatis.migration.Migrator` as the command runner, and declare every runtime dependency required by the implementation.

## Appendix B: Assessment Notes

Assessment compiles the project with Maven and invokes public Java APIs and the Java command runner against temporary repositories and an in-process JDBC database. Checks cover repository creation, configuration precedence, migration loading, DO/UNDO selection, lifecycle operations, changelog and status consistency, offline scripts, hooks, custom loaders, failures, and cross-view invariants. Assertions focus on durable schema, changelog, files, returned values, callback order, and process status rather than private helpers or exact diagnostic text.

