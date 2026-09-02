# Online Atomic Secondary-Index Migration

## Product Overview

`github.com/hashicorp/go-memdb` is an in-memory transactional database backed by immutable radix trees. A database is created from a `DBSchema`; each table has a unique primary `id` index and may have additional secondary indexes. Read transactions and database snapshots provide stable MVCC views while a single-writer lock serializes mutations.

This extension lets a primary `MemDB` add, replace, or remove secondary indexes without rebuilding the database. Existing rows are backfilled into new index trees, a complete schema-and-root generation is published atomically, readers that began earlier keep their old generation, and concurrent writers are serialized across publication.

## Scope and Non-Goals

The supported scope is secondary-index schema migration on an existing in-memory database:

- add and backfill a secondary index;
- drop a secondary index;
- atomically replace an index by dropping and adding the same name;
- atomically migrate indexes in several tables in one call;
- preserve pre-migration transaction and snapshot views;
- wake watches associated with affected tables after successful publication;
- roll back the entire migration on validation, missing-value, uniqueness, or indexer errors.

The extension does not migrate table names, add or remove tables, change the required `id` index, persist schema history, deep-copy stored objects, or permit schema migration on a `MemDB` returned by `Snapshot`.

## Installable Surface

The module path remains `github.com/hashicorp/go-memdb`, and the package name remains `memdb`. Existing constructors, transactions, indexers, iterators, snapshots, and watch APIs remain available. The extension adds `IndexMigration`, `AddIndex`, `DropIndex`, `MigrateIndexes`, and the migration error values listed below.

No additional module dependency is required beyond the dependencies already declared by the repository.

## Representative Workflows

### Add and Query a Backfilled Index

1. Create a `MemDB` with an `id` index and one or more existing secondary indexes.
2. Insert rows using ordinary write transactions.
3. Call `AddIndex` with a valid secondary `IndexSchema`.
4. Start a new read transaction and query the new index with `Get`, `First`, or another existing read API.
5. Observe every eligible pre-existing row plus every later committed row under the new index.

### Replace an Index Without a Mixed View

1. Start a read transaction and optionally take a `Snapshot`.
2. Call `MigrateIndexes` with the old name in `Drop` and a new definition with the same name in `Add`.
3. The earlier transaction and snapshot continue using the old definition and old index tree.
4. Transactions started after publication use the replacement definition and fully backfilled tree.
5. No transaction observes the new schema paired with the old tree, or the old schema paired with the new tree.

### Failure and Retry

1. Register a watch on an existing index in a table.
2. Attempt a batch containing an indexer that returns an error, a required index that is missing on a row, or a unique index whose backfill collides.
3. The call returns a matching migration error; schema, roots, query results, and watches remain unchanged.
4. Retry with corrected definitions. The successful call publishes the complete batch and closes pre-migration watches for every affected table.

### Concurrent Writer During Backfill

1. Begin a migration whose indexer takes enough time for another goroutine to request a write transaction.
2. Existing readers continue using the old generation while backfill runs.
3. The writer waits behind the migration's writer boundary.
4. After publication, the writer starts with the new schema and updates every new index before commit.

## Migration Planning and Validation

`IndexMigration` describes the changes for exactly one table. A `MigrateIndexes` call may contain entries for several distinct tables, but the same table must not appear twice in one call. An empty migration list is a successful no-op and does not publish a generation or wake watches.

Within one table entry, each name may occur at most once in `Drop` and at most once in `Add`. Drop is interpreted before Add. Consequently, a name may occur once in both lists to atomically replace that index. Adding an already-existing name without also dropping it fails with `ErrIndexExists`. Dropping an absent name fails with `ErrIndexNotFound`.

The primary index named `id` may not be added, dropped, or replaced. A migration must name an existing table. Every added definition must be non-nil, its map key is its `Name`, and `IndexSchema.Validate` must accept it. The implementation shallow-copies each accepted `IndexSchema` before publication, so later mutation of the caller's struct does not change the published definition; the `Indexer` value itself is retained.

Validation and backfill cover the whole call before publication. If any entry fails, no entry in the call becomes visible.

## Atomic Backfill and Index Semantics

Backfill enumerates the table's primary `id` tree from the migration's starting generation. A `SingleIndexer` contributes at most one key per object, and a `MultiIndexer` may contribute several. The key encoding and query arguments follow the existing `Indexer`, `SingleIndexer`, and `MultiIndexer` contracts.

For a non-unique index, the primary key is appended to each encoded secondary key, matching ordinary `Txn.Insert` behavior. Every matching object remains independently queryable even when several rows have the same secondary value.

For a unique index, two distinct primary IDs must not produce the same encoded key. Such a collision returns `ErrIndexMigrationUniqueConflict`. Repeated output of the same key by one object's `MultiIndexer` is not a conflict with itself.

If an indexer returns `present == false`, backfill skips the row only when `AllowMissing` is true. Otherwise it returns `ErrIndexMigrationMissingValue`. An error returned by `FromObject`, an unsupported indexer, or an invalid added definition returns an error matching `ErrIndexMigrationIndexer`.

The batch is all-or-nothing. A failure does not change `DBSchema`, does not add or remove a root path, preserves every old query result, does not close watches, and releases the writer boundary so a later writer or migration can proceed.

## MVCC Generations and Concurrency

Each call to `Txn` captures one matching pair: a schema generation and its immutable root. `Txn.Snapshot` retains that same schema generation while incorporating the transaction's own already-staged index modifications. `MemDB.Snapshot` captures the current schema-and-root generation and remains independent of later migrations.

A read transaction or snapshot created before publication retains the old set of index names, the old definitions of replaced indexes, and the old immutable index contents. It therefore rejects a newly added index, can still query a subsequently dropped index, and interprets a replacement using the former indexer. A transaction created after publication sees the complete new generation.

Migration shares the database's single-writer boundary with write transactions. A write transaction already holding the boundary commits or aborts before migration begins. A writer requested during migration begins only after publication or failure. After successful publication it uses the new schema, so inserted, updated, and deleted rows keep every new index consistent. After failure it uses the unchanged old schema.

Backfill does not hold the short schema-publication latch. New read transactions may therefore continue to start on the old generation while backfill is running. Publication changes the schema and root as one reader-visible generation.

## Watch and Lifecycle Semantics

After a successful non-empty migration, watch channels created from any pre-migration index tree in each affected table are closed. Notification occurs only after the new schema-and-root generation is visible, so a goroutine awakened by the watch can immediately start a transaction that sees the completed migration.

This table-level invalidation includes indexes that survive unchanged, indexes that are replaced, and indexes that are dropped. It provides one conservative signal that the table's query structure changed. Watches obtained from unaffected tables are not closed by the migration.

A failed migration and an empty migration do not close any watch. Old transactions remain readable after their watches close; notification does not erase or mutate their immutable index contents.

`AddIndex`, `DropIndex`, and `MigrateIndexes` are synchronous. On return, either the whole generation has been published and notifications issued, or nothing changed. Migration on a database snapshot returns `ErrIndexMigrationSnapshot`.

## State Model

A primary database moves through these conceptual states:

- **Stable generation N**: schema N and root N are the current pair; no migration owns the writer boundary.
- **Building N+1**: a migration owns the writer boundary, validates its complete plan, backfills new trees from root N, and allows readers to keep acquiring generation N.
- **Published N+1**: schema N+1 and root N+1 become visible as one pair; old-generation watches for affected tables close; waiting writers may proceed.
- **Rolled back to N**: validation or backfill failed; schema N, root N, and all watches remain unchanged; waiting writers may proceed against N.

Read transactions and snapshots retain a reference to their captured generation even after the primary database advances.

## Error Semantics

The following exported sentinel errors support `errors.Is`:

- `ErrIndexMigrationSnapshot`: migration was requested on a database snapshot.
- `ErrIndexMigrationTableNotFound`: an entry names an unknown table.
- `ErrIndexMigrationDuplicateTable`: a batch contains more than one entry for a table.
- `ErrIndexMigrationDuplicateIndex`: an entry repeats a name within `Add` or within `Drop`.
- `ErrIndexExists`: an added name already exists and is not replaced in the same entry.
- `ErrIndexNotFound`: a dropped name is absent.
- `ErrIndexMigrationPrimary`: the call attempts to add, replace, or drop `id`.
- `ErrIndexMigrationMissingValue`: a required new index is missing on an existing object.
- `ErrIndexMigrationUniqueConflict`: distinct primary IDs collide in a new unique index.
- `ErrIndexMigrationIndexer`: an added definition is nil or invalid, an indexer type is unsupported, or `FromObject` returns an error.

Errors may wrap table and index context. Callers should use `errors.Is` rather than comparing formatted strings.

## Cross-View Invariants

1. `DBSchema` and queries from a newly started transaction describe the same index-name set.
2. A newly published index contains every eligible row visible in the primary `id` tree at migration start.
3. A post-publication writer updates the primary tree and every migrated secondary tree in the same ordinary transaction.
4. A pre-migration transaction's schema names and index contents never switch to the new generation.
5. A pre-migration database snapshot remains on its captured generation after add, drop, or replacement.
6. Replacing an index exposes either the complete old definition/tree pair or the complete new definition/tree pair, never a mixed pair.
7. Any migration error leaves schema identity, root-backed query results, and watch state unchanged.
8. A successful migration closes affected-table old-generation watches only after new transactions can observe the new generation.
9. Unaffected-table schema, roots, results, and watches do not change.
10. Unique backfill never silently overwrites an object with a different primary ID.
11. Concurrent writers cannot commit a row under only one side of the migration boundary.
12. Dropping an index removes it from new transactions without removing rows from the primary index or other secondary indexes.

## Public Interface

```go
type IndexMigration struct {
    Table string
    Add   []*IndexSchema
    Drop  []string
}

func (db *MemDB) AddIndex(table string, index *IndexSchema) error
func (db *MemDB) DropIndex(table, index string) error
func (db *MemDB) MigrateIndexes(migrations ...IndexMigration) error

var ErrIndexMigrationSnapshot error
var ErrIndexMigrationTableNotFound error
var ErrIndexMigrationDuplicateTable error
var ErrIndexMigrationDuplicateIndex error
var ErrIndexExists error
var ErrIndexNotFound error
var ErrIndexMigrationPrimary error
var ErrIndexMigrationMissingValue error
var ErrIndexMigrationUniqueConflict error
var ErrIndexMigrationIndexer error
```

The pre-existing `NewMemDB`, `DBSchema`, `TableSchema`, `IndexSchema`, `StringFieldIndex`, `StringSliceFieldIndex`, `MemDB.DBSchema`, `MemDB.Txn`, `MemDB.Snapshot`, `Txn.Snapshot`, transaction mutation/query APIs, `ResultIterator.WatchCh`, and `FirstWatch` remain part of the interactions described above.

## Invocation Protocol

Construct a valid database and populate it normally. Invoke migration methods directly on the primary `*MemDB`; no scheduler, background service, file, environment variable, or command-line wrapper is involved. Migration methods return only after publication plus notification or complete rollback.

Use ordinary transactions to observe results. Abort read transactions when convenient; commit or abort every write transaction so the single-writer boundary is released.

## Environment

The implementation targets the Go version declared by the repository's `go.mod`. It must work on supported Go platforms with the repository's existing immutable-radix dependency. Correctness must not depend on sleeps, filesystem state, network access, map iteration order, or a particular goroutine scheduler.

## Evaluation Notes

Correct implementations should be tested with multiple pre-existing rows, non-unique and unique definitions, multi-key indexers, missing values, deterministic indexer errors, multi-index and multi-table batches, replacement, old transactions, old snapshots, watch ordering, a writer held before migration, and a writer requested during backfill. Assertions should observe exported errors, schemas, transaction results, watch channels, and completion boundaries.
