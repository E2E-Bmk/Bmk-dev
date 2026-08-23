# Goose Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`goose` is a local database migration library and command-line tool that applies ordered SQL or Go changes to SQLite databases. Migration sources define forward and optional rollback behavior, while a version table records applied versions. The same state is observable through provider results, status and version queries, SQLite schema and data, and CLI commands.

The Go library is imported from `github.com/pressly/goose/v3`. The executable is named `goose`. Every database workflow in this specification uses local SQLite and requires no external service.

## Non-Goals

- This specification does not require any database dialect other than SQLite.
- This specification does not require Docker, network services, custom stores, distributed locks, or packages under `internal`.
- This specification does not require exact log lines, error-message text, duration formatting, colors, or `String` formatting.
- This specification does not require deprecated APIs, string-based command dispatch, configurable logging sinks, direct `Migration` execution methods, or global Go migration registration.
- This specification does not require custom migration templates or hidden CLI commands absent from the published command list.
- This specification does not require private helpers, private fields, or a particular implementation layout.

## Representative Workflows

### Apply and inspect SQL migrations

```go
db, _ := sql.Open("sqlite", "app.db")
p, _ := goose.NewProvider(
    goose.DialectSQLite3,
    db,
    os.DirFS("migrations"),
)
defer p.Close()

results, _ := p.Up(context.Background())
statuses, _ := p.Status(context.Background())
current, target, _ := p.GetVersions(context.Background())
_, _, _, _ = results, statuses, current, target
```

When numbered SQL files are pending, `Up` must execute them in ascending version order and record each successful version. Results, status, versions, the SQLite version table, and application data must describe the same final state. If execution fails, then the failed migration must not be recorded as applied.

### Move the same database through the CLI

```sh
goose -dir ./migrations sqlite3 ./app.db up
goose -dir ./migrations sqlite3 ./app.db status
goose -dir ./migrations sqlite3 ./app.db version
goose -dir ./migrations sqlite3 ./app.db down
```

These commands must apply pending migrations, report applied and pending sources, report the highest applied version, and roll back the most recently applied migration. Reopening the same SQLite file in a later process must preserve committed schema, data, and version state.

### Register a Go migration

```go
up := &goose.GoFunc{
    RunTx: func(ctx context.Context, tx *sql.Tx) error {
        _, err := tx.ExecContext(
            ctx,
            "CREATE TABLE audit (id INTEGER PRIMARY KEY)",
        )
        return err
    },
}

migration := goose.NewGoMigration(3, up, nil)
provider, err := goose.NewProvider(
    goose.DialectSQLite3,
    db,
    os.DirFS("migrations"),
    goose.WithGoMigrations(migration),
)
```

The provider must merge registered Go migrations with SQL sources by version. Applying version 3 must run the callback and record version 3. If a Go migration conflicts with another source version, then construction must return an error.

## Migration Sources and SQL Directives

Migration sources define the ordered change set used by execution and status views.

**Discovery and versions.** A migration filename must begin with a positive decimal version, an underscore, a descriptive name, and a `.sql` or `.go` extension. `NumericComponent` must return the leading version for a valid filename. If the prefix is absent, non-numeric, or non-positive, then `NumericComponent` must return an error. `CollectMigrations` must return matching sources in ascending version order within the requested interval. If no source exists, then it must return `ErrNoMigrationFiles`. Duplicate versions must make collection return an error.

**Direction blocks.** Every SQL migration must contain exactly one `-- +goose Up` annotation. A `-- +goose Down` annotation is optional and must follow Up. Statements following each annotation belong to that direction. If directives are missing, duplicated, or misordered, then validation or execution must return an error without recording the version.

**Statements and transactions.** Ordinary statements must end with semicolons. `-- +goose StatementBegin` and `-- +goose StatementEnd` must delimit one statement containing internal semicolons. SQL migrations must run in a transaction by default. Where `-- +goose NO TRANSACTION` is present at the top, both directions must run without a wrapping transaction. If transactional execution fails, then that migration’s database changes and version record must roll back together. If non-transactional execution fails, then the version must remain unrecorded.

**Environment substitution.** Expansion is disabled by default. While a region is between `-- +goose ENVSUB ON` and `-- +goose ENVSUB OFF`, `$VAR`, `${VAR}`, `${VAR:-default}`, `${VAR-default}`, and `${VAR?message}` must follow shell-style substitution rules. If a required variable is absent, then execution must return an error without recording the migration. Text outside enabled regions must remain unchanged.

**Filesystem selection.** `SetBaseFS` must select the filesystem used to discover and read existing migrations; nil must restore operating-system discovery. Embedded filesystems must support collection and execution. `Create` and `Fix` must always modify the operating-system filesystem. If a selected path does not exist, then collection must return an error.

## Provider Construction and Status

The provider binds one SQLite connection, a source set, and version policy into a coordinator.

**Construction.** `NewProvider` accepts `DialectSQLite3`, a non-nil database, an `fs.FS`, and `ProviderOption` values. A nil filesystem must represent no file sources while registered Go migrations remain usable. If the database is nil, an option is invalid, or no source exists, then construction must return an error. The no-source error must be `ErrNoMigrations`.

**Options.** `WithTableName` must select a non-empty version-table name and defaults to `DefaultTablename`, whose value is `goose_db_version`. `WithExcludeNames` and `WithExcludeVersions` must omit the specified sources. If an exclusion is duplicated or an excluded version is non-positive, then construction must return an error. `WithAllowOutofOrder(true)` must permit missing lower versions to run before new higher versions. Without this option, detecting such a missing lower version must make pending detection and forward execution return an error without applying the new set. `WithDisableVersioning(true)` must execute changes without updating version history.

**Go migrations.** `NewGoMigration` accepts a positive version and optional up and down `GoFunc` values. For each `GoFunc`, exactly one of `RunTx` and `RunDB` must be non-nil, or both must be nil. `RunTx` must use `TransactionEnabled`; `RunDB` must use `TransactionDisabled`; an all-nil function must use its explicit `Mode` or default to `TransactionEnabled`. If a version is non-positive, both callback fields are non-nil, the mode conflicts with its callback, or two sources share a version, then provider construction must return an error.

**Public projections.** `ListSources` must return `Source` values sorted by ascending version. Each source must expose `Type`, `Path`, and `Version`. `Status` must return one `MigrationStatus` per known source in ascending order. Each status must expose `StatePending` or `StateApplied` and `AppliedAt`; pending entries must use the zero time. `HasPending` must return true exactly when at least one eligible source is unapplied and must return false when all eligible sources are applied. `GetVersions` must return the highest applied database version and the highest known source version. `GetDBVersion` must return the highest applied version, or zero when no migration is applied. With versioning disabled, `GetDBVersion` must return an error.

**Lifecycle.** `Ping` must return nil when the supplied connection responds and must return the connection error otherwise. `Close` must close the supplied connection and must return the close error when closing fails.

## Applying and Rolling Back

Migration operations transform SQLite data and version history as one observable workflow.

**Forward operations.** `Provider.Up` must apply every eligible pending migration in required order and must return one `MigrationResult` per applied source. When none are pending, it must return an empty result and nil error. `Provider.UpByOne` must apply exactly the next eligible source; if none exists, then it must return `ErrNoNextVersion`. `Provider.UpTo(v)` must apply every eligible pending source whose version is less than or equal to `v`; if none qualifies, then it must return an empty result and nil error.

**Rollback operations.** `Provider.Down` must roll back the most recently applied source; if none is applied, then it must return `ErrNoNextVersion`. `Provider.DownTo(v)` must roll back applied sources above `v` without rolling back `v`. Where out-of-order execution occurred, rollback must follow reverse application order. If `v` is negative, then `DownTo` must return an error without changing database or version state.

**Exact-version operations.** `Provider.ApplyVersion(v, true)` must apply exactly version `v`; if the source is absent, then it must return `ErrVersionNotFound`, and if already applied, then it must return `ErrAlreadyApplied`. `Provider.ApplyVersion(v, false)` must roll back exactly version `v`; if the source is absent, then it must return `ErrVersionNotFound`, and if unapplied, then it must return `ErrNotApplied`.

**Results and partial failure.** A successful `MigrationResult` must expose `Source`, a non-negative `Duration`, `Direction` equal to `up` or `down`, `Empty`, and a nil `Error`. A failed result must set `Error` to the migration failure. If a multi-migration operation fails after successes, then it must return a `PartialError`: `Applied` contains successful results in operation order, `Failed` identifies the failed migration, and `Err` unwraps to the triggering error. A failed transactional migration must not change application or version state.

## File Maintenance and Go Registration

These operations create or register migration sources without an external service.

**Creation and fixing.** `Create` must create one timestamp-versioned file with a snake-cased name and a requested `sql` or `go` extension. If the directory is unavailable or the destination exists, then `Create` must return an error without overwriting a file. `SetSequential(true)` must select five-digit versions beginning at `00001` or following the highest sequential version. `Fix` must preserve sequential files and rename timestamped files to consecutive five-digit versions in timestamp order. Discovery or rename failures must return an error.

## Command-Line Behavior

The `goose` executable projects the same local state through process behavior.

**Invocation.** Database commands use `goose [OPTIONS] sqlite3 DBSTRING COMMAND`. `-dir` must select migrations, `-table` must select the version table, and `-timeout` must cancel database work after its duration. `-h` and `-version` must print their requested information and exit successfully. The CLI `up`, `up-by-one`, and `up-to` commands must execute their named forward operation; `down`, `down-to`, `redo`, and `reset` must execute their named rollback operation; `status` and `version` must execute their named reporting operation. A command operation error must produce a non-zero exit.

**Configuration precedence.** `GOOSE_DRIVER`, `GOOSE_DBSTRING`, `GOOSE_MIGRATION_DIR`, and `GOOSE_TABLE` must supply omitted values. Explicit arguments and flags must take precedence over environment values, which must take precedence over defaults. The executable must attempt `.env` loading by default. `-env=none` disables file loading, while `-env=PATH` requires that file to load successfully. `NO_COLOR`, `-no-color`, and `-v` affect presentation only.

**File commands.** `create NAME sql`, `create NAME go`, and `-s` must match the library creation rules. `fix` must match `Fix`. `validate` must parse `.sql` and `.go` sources without executing or changing them. Successful non-verbose validation must not require report text. Invalid input must exit unsuccessfully.

**Process outcomes.** Successful operations, help, and version display must exit 0. Missing arguments, unknown commands, invalid version text, requested environment-file failure, connection failure, validation failure, or migration failure must exit non-zero. Exact complete output lines are not contractual.

## State Model

The core state is an ordered source set, SQLite schema and data, application history in the selected table, and registered Go callbacks. Public projections are source lists, migration status, current and target versions, operation results, SQLite data, and CLI outcomes.

A successful Up transition must change one source from pending to applied after its database work succeeds. A successful Down transition must reverse its work and return it to pending. A failed transactional transition must preserve its previous state. Closing and reopening SQLite must preserve committed transitions.

## Error Semantics

| Condition | Required result |
|---|---|
| Provider has no sources | Return `ErrNoMigrations` |
| Collection finds no files | Return `ErrNoMigrationFiles` |
| No next Provider migration is available | Return `ErrNoNextVersion` |
| Exact version is absent | Return `ErrVersionNotFound` |
| Forward exact target is already applied | Return `ErrAlreadyApplied` |
| Exact rollback target is unapplied | Return `ErrNotApplied` |
| Multi-migration run fails after successes | Return `PartialError` with successful and failed results |
| SQL grammar, environment requirement, or callback is invalid | Return an error and do not record the failed version |
| CLI usage, connection, validation, or migration fails | Exit non-zero |

## Cross-View Invariants

1. An applied `Status` entry must exist in SQLite version history and its database changes must be observable.
2. A pending `Status` entry must be eligible for its next matching Up operation and must not be reported as applied.
3. After `Provider.Up`, `HasPending`, `GetVersions`, `GetDBVersion`, results, version history, and SQLite schema must agree.
4. After `Provider.Down`, the source must become pending, its Down effects must be observable, and current version must match remaining history.
5. A failed transactional migration must leave status, history, schema, and data at their pre-migration state.
6. A database migrated through the library must expose the same status and version through the CLI with the same directory and table.
7. A database migrated through the CLI must expose the same status and version through `NewProvider`.
8. Excluding a source must remove it from sources, status, pending detection, and later results without deleting unrelated history.
9. Out-of-order execution must place missing lower versions before new higher versions in results and history.
10. Disabling versioning must permit database changes while leaving history unchanged or absent.
11. A registered Go migration must have matching type and version in sources, status, results, and history.
12. Reopening a SQLite file must preserve committed schema, data, applied state, and current version.

## Public Interface

### Import Surface

```go
import "github.com/pressly/goose/v3"
```

The executable is built from `github.com/pressly/goose/v3/cmd/goose` and installed as `goose`.

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Dialect`, `DialectSQLite3` | type/constant | Select SQLite behavior |
| `Provider`, `NewProvider` | type/function | Coordinate sources, database state, and execution |
| `ProviderOption` | interface | Configure a provider |
| `WithTableName` | function | Configure version-table naming |
| `WithExcludeNames`, `WithExcludeVersions` | functions | Filter migration sources |
| `WithGoMigrations` | function | Configure provider-local Go migration sources |
| `WithAllowOutofOrder`, `WithDisableVersioning` | functions | Configure ordering and version tracking |
| `Source`, `MigrationStatus`, `MigrationResult`, `PartialError` | types | Project source, status, and operation results |
| `MigrationType`, `TypeGo`, `TypeSQL` | type/constants | Identify source kind |
| `State`, `StatePending`, `StateApplied` | type/constants | Identify application state |
| `Migration`, `GoFunc`, `NewGoMigration` | types/function | Define Go migrations |
| `TransactionMode`, `TransactionEnabled`, `TransactionDisabled` | type/constants | Define callback transaction behavior |
| `Migrations`, `CollectMigrations`, `NumericComponent` | type/functions | Represent and discover migration sources |
| `ErrNoMigrations`, `ErrNoMigrationFiles`, `ErrNoNextVersion` | error variables | Report missing sources and next Provider targets |
| `ErrVersionNotFound`, `ErrAlreadyApplied`, `ErrNotApplied` | error variables | Report exact-version conflicts |
| `SetBaseFS` | function | Configure migration-source discovery |
| `Create`, `SetSequential`, `Fix` | functions | Maintain migration files |

### CLI Entry Points

Console script: `goose`.

| Commands | Role |
|---|---|
| `up`, `up-by-one`, `up-to VERSION` | Apply migrations |
| `down`, `down-to VERSION`, `redo`, `reset` | Roll back or reapply migrations |
| `status`, `version` | Inspect database migration state |
| `create NAME [sql\|go]`, `fix`, `validate` | Maintain migration sources |

| Exit | Meaning |
|---:|---|
| 0 | Operation completed successfully |
| non-zero | Usage, configuration, validation, connection, or migration failure |

## Appendix A: Environment

The working environment runs Go 1.26.6 on Linux/amd64 without network access. The module cache contains project dependencies, including `modernc.org/sqlite` for local SQLite. The assessment environment provides the same toolchain and cached module set.

The project must provide a standard `go.mod` at its root. `go test` and `go build` must resolve dependencies from the module cache without downloads. Database workflows must use local temporary files or in-memory SQLite databases.

## Appendix B: Assessment Notes

Implementations are exercised through exported Go identifiers and the `goose` executable. Checks cover source discovery, SQL directives, transactions, provider construction, forward and rollback behavior, SQLite version persistence, state projections, Go registration, file maintenance, environment precedence, CLI exits, and agreement across library, CLI, filesystem, and database views. Private structures, exact text formatting, and non-SQLite integrations are not assessed.
