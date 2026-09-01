# redb Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`redb` is an embedded Rust key-value database crate that stores named tables in a local database file or caller-supplied storage backend. It provides ACID write transactions, snapshot read transactions, typed table definitions, multimap tables, ordered iteration, savepoints, and database/table statistics through a `BTreeMap`-like public API.

The core state is a durable collection of table definitions and key-value records. Write transactions stage changes until commit, read transactions observe stable snapshots, and reopened databases project the latest durable committed state.

## Non-Goals

- This specification does not require implementing the `redb-derive` procedural macro crate.
- This specification does not require `no_std` operation or APIs gated only by the `experimental-api-5` feature.
- This specification does not require the `experimental_cursor` mutable cursor API.
- This specification does not define private page layout, checksum algorithms, allocator internals, or source-unit test helpers.
- This specification does not require backward-compatibility fixtures from older crate versions.
- This specification does not require exact `Debug` or `Display` message text.
- This specification does not require simulating operating-system crashes or process-kill harnesses.

## Representative Workflows

### Create, Write, Commit, and Reopen

```rust
use redb::{Database, Error, ReadableDatabase, ReadableTable, TableDefinition};

const TABLE: TableDefinition<&str, u64> = TableDefinition::new("items");

fn main() -> Result<(), Error> {
    let file = tempfile::NamedTempFile::new().unwrap();
    {
        let db = Database::create(file.path())?;
        let write = db.begin_write()?;
        {
            let mut table = write.open_table(TABLE)?;
            table.insert("a", &1)?;
            table.insert("b", &2)?;
        }
        write.commit()?;
    }

    let db = Database::open(file.path())?;
    let read = db.begin_read()?;
    let table = read.open_table(TABLE)?;
    assert_eq!(table.get("a")?.unwrap().value(), 1);
    Ok(())
}
```

Creating a database initializes an empty store when the target is empty. Committing the write transaction makes the inserted records visible to later read transactions and to a later open of the same database path.

### Snapshot Reads and Write Isolation

```rust
use redb::{Database, Error, ReadableDatabase, ReadableTable, TableDefinition};

const TABLE: TableDefinition<u64, u64> = TableDefinition::new("numbers");

fn main() -> Result<(), Error> {
    let file = tempfile::NamedTempFile::new().unwrap();
    let db = Database::create(file.path())?;

    let first = db.begin_read()?;
    let write = db.begin_write()?;
    {
        let mut table = write.open_table(TABLE)?;
        table.insert(1, &10)?;
    }
    write.commit()?;

    assert!(first.open_table(TABLE).is_err());
    let second = db.begin_read()?;
    assert_eq!(second.open_table(TABLE)?.get(1)?.unwrap().value(), 10);
    Ok(())
}
```

A read transaction observes the database state that existed when it began. A later commit does not change that existing snapshot, while a new read transaction observes the committed table.

## Database Opening and Storage

Database opening establishes the durable store and controls how callers obtain read and write transactions.

**Database Creation and Opening.** When `Database::create` receives a path that does not exist or names an empty file, it must initialize a new database at that path. When `Database::create` receives a path containing a valid database, it must open that database without deleting committed content. When `Database::open` receives an existing valid database path, it must open the stored content. If the path contains data that is not a valid database, then opening must raise `DatabaseError::Storage`.

**Builder Configuration.** The `Builder` type must provide configuration before opening or creating a database. `Builder::create` and `Builder::open` operate on paths, `Builder::open_read_only` opens an existing path for a `ReadOnlyDatabase`, `Builder::create_file` operates on an existing `File`, and `Builder::create_with_backend` operates on a supplied `StorageBackend`. `Builder::set_page_size`, `Builder::set_cache_size`, `Builder::set_region_size`, and `Builder::set_repair_callback` must affect subsequent builder operations. `InMemoryBackend::new` must construct an in-memory backend for `Builder::create_with_backend`. If incompatible or invalid storage state prevents opening, then the builder operation must raise `DatabaseError`.

**Readable Database Handles.** `Database` and `ReadOnlyDatabase` must implement `ReadableDatabase`. When `begin_read` is called, the returned `ReadTransaction` must capture only data committed before that call. While read transactions exist, the database must still permit another read transaction and one write transaction. Multiple `ReadOnlyDatabase` handles for the same file must be allowed concurrently. A writable `Database` and a `ReadOnlyDatabase` opened for the same file must not be held concurrently when the platform provides file locking; the second open must raise `DatabaseError::DatabaseAlreadyOpen`.

**Close and Locking.** Dropping a `Database` must close the store, flush buffered state, release the file lock, and make later operations through read transactions that still depend on that handle raise `StorageError::DatabaseClosed`. While a `WriteTransaction` is alive, dropping the `Database` handle must keep the store open until that write transaction commits, aborts, or is dropped. If a second writer tries to open the same locked database, then opening must raise `DatabaseError::DatabaseAlreadyOpen`.

**Integrity Checking and Compaction.** When `check_integrity` is called with no live transaction or ephemeral savepoint, it must verify the durable state and return `true` for a clean database, return `false` after a repairable problem is repaired, or raise `StorageError::Corrupted` through `DatabaseError::Storage` when repair fails. If a read transaction, write transaction, or ephemeral savepoint is alive, then `check_integrity` must raise `DatabaseError::TransactionInProgress`. When `compact` is blocked by a persistent savepoint, it must raise `CompactionError::PersistentSavepointExists`; when blocked by an ephemeral savepoint, it must raise `CompactionError::EphemeralSavepointExists`; when blocked by a transaction, it must raise `CompactionError::TransactionInProgress`.

## Transactions and Visibility

Transactions define which updates become visible and when.

**Write Transaction Lifecycle.** When `Database::begin_write` succeeds, it must return a `WriteTransaction` that stages table creation, inserts, removals, table renames, table deletion, durability changes, and savepoint operations. When `commit` succeeds, all staged writes must become visible to future read transactions atomically. When `abort` succeeds or a write transaction is dropped without commit, staged writes must not become visible to future read transactions.

**Snapshot Isolation.** A `ReadTransaction` must observe a stable snapshot. When a write commits after a read transaction begins, the existing read transaction must continue to observe its original snapshot, and a new read transaction must observe the committed state.

**Read Transaction Closing.** When `ReadTransaction::close` is called while tables, guards, ranges, or other values still reference that transaction, it must raise `TransactionError::ReadTransactionStillInUse`. When no outstanding reference exists, `close` must succeed.

**Durability.** A write transaction must default to `Durability::Immediate`. When `set_durability` sets `Durability::Immediate`, a successful commit must report only after the transaction is durable according to the storage backend. When `set_durability` sets `Durability::None`, a successful commit must become visible immediately and a later immediate commit or integrity operation must establish durable persistence. If a persistent savepoint was created or deleted in the same transaction, then lowering durability below `Durability::Immediate` must raise `SetDurabilityError::PersistentSavepointModified`.

**Commit Failure and Poisoning.** If a table-retention predicate panics, an extract operation fails during finalization, a savepoint restore fails partway through, or another mutating operation leaves the transaction poisoned, then `commit` must roll back the transaction and raise `CommitError::TransactionPoisoned`. If storage failure occurs during commit, then changes must be atomic from the caller's perspective and the database must require close and reopen before further writes.

## Tables and Ordered Records

Typed tables expose ordered key-value mappings whose behavior matches the public `Key` and `Value` contracts.

**Table Definitions and Handles.** `TableDefinition::new` must create a typed normal-table definition identified by its name. `MultimapTableDefinition::new` must create a typed multimap-table definition identified by its name. Untyped handles must identify tables by name without exposing key and value types. When a caller opens a table using a definition whose name exists with incompatible kind, key type, or value type, the operation must raise `TableError::TableIsMultimap`, `TableError::TableIsNotMultimap`, or `TableError::TableTypeMismatch` according to the mismatch.

**Opening and Listing Tables.** When `WriteTransaction::open_table` or `open_multimap_table` names a missing table, the table must be created inside the transaction. The write-transaction table-opening methods must operate through a shared write-transaction handle; callers must not be required to bind the `WriteTransaction` itself as mutable in order to open tables. When `ReadTransaction::open_table` or `open_multimap_table` names a missing table, the operation must raise `TableError::TableDoesNotExist`. `ReadTransaction::open_untyped_table` and `ReadTransaction::open_untyped_multimap_table` must open the corresponding table through its public name-bearing handle without requiring key or value types. Table listing methods must return `Result`-wrapped lazy iterators of untyped handles, return normal table handles separately from multimap table handles, and reflect the calling transaction's view. A listing iterator must support iterator adapters before collection, including mapping each handle to its public name.

**Single-Value Table Operations.** Table mutation and lookup methods must accept borrowed key and value inputs compatible with the table definition's `Value::SelfType`, so a table whose key or value type is `&str` accepts string literals directly. For table types whose key or value definition is `&str`, callers must be able to pass `"key"` and `"value"` as the key or value argument; the public methods must not force a second reference level such as `&&str`. When `Table::insert` stores a key and value, it must return an `AccessGuard` for the previous value or `None` when the key was absent. The insert method must accept a key argument in the key's borrowed self type and a value argument in the value's borrowed self type, including references such as `&u64` for integer values and direct string slices for string-slice values. When `Table::remove` removes a key, it must return an `AccessGuard` for the removed value or `None` when the key was absent. The remove and lookup methods must accept the same caller-facing key forms as insert. `Table::insert_reserve` must accept a key and value length and return an `AccessGuardMutInPlace` for the reserved value, whose mutable byte slice must be writable before commit. `Table::get_mut` must return an `AccessGuardMut` for an existing key and `None` for a missing key. When `pop_first` or `pop_last` is called on a writable table, it must remove and return the lowest or highest key-value pair, or return `None` when the table is empty. The extrema removal methods must return the key guard and value guard together so callers must be able to inspect both decoded values before the guards are dropped. When `get`, `first`, `last`, `iter`, or `range` is called on a readable table, the returned guards and iterators must expose key-value pairs ordered by the `Key` implementation.

**Range Boundaries.** When `range` receives an inclusive, exclusive, or unbounded range, it must return only entries whose keys fall inside those bounds. The public range methods must accept standard Rust range-bound values over the same key form accepted by lookup, including half-open, inclusive, and unbounded bounds. The returned range must be double-ended: forward iteration returns ascending keys and backward iteration returns descending keys over the same bounded set. If storage corruption or backend failure prevents reading an entry, then iteration must return a storage error rather than silently skipping data.

**Entry API.** `Table::entry` must accept a key in the key definition's borrowed self type and return an occupied or vacant entry tied to the table borrow. When `entry` is called for an existing key, it must return an occupied entry whose `key`, `get`, `get_mut`, `into_mut`, `insert`, `remove`, and `remove_entry` operations act on that key. Both `OccupiedEntry::key` and `VacantEntry::key` must return a reference to the decoded key in the form `&K::SelfType`; the returned reference for an integer key must yield the integer value upon dereferencing, and the returned reference for a string-slice key must yield the string slice upon dereferencing. `OccupiedEntry::get` must return a `Result` containing an `AccessGuard` for the value, and `OccupiedEntry::get_mut` and `into_mut` must return `Result`-wrapped mutable access guards. `OccupiedEntry::remove_entry` must remove the entry and return both the removed key value and the removed value guard. The removed key must be exposed as the decoded key value, not as an access guard wrapper, so callers must be able to compare it directly with values of the key type. When `entry` is called for a missing key, it must return a vacant entry whose `key`, `into_key`, and insertion operations expose or create that key. `VacantEntry::into_key` must return the decoded key value. `OccupiedEntry::insert` must replace the occupied value and return its previous value guard. `AccessGuardMut::insert` must replace the guarded value and return success; if the replacement exceeds the supported value size, it must raise `StorageError::ValueTooLarge`. `or_insert`, `or_insert_with`, `or_insert_with_key`, and `and_modify` must follow the same occupied-or-vacant control flow as the standard map entry pattern. Entry insertion methods must accept borrowed values in the value definition's borrowed self type, matching `Table::insert`. `and_modify` must pass an `AccessGuardMut` to its closure, propagate the closure's `Result`, and return the entry for continued use. When `or_insert_with_key` inserts a missing key, its closure must receive a reference to the decoded requested key and the returned value must become the stored value.

**Retain and Extract.** When `retain` or `retain_in` is called, entries for which the predicate returns `false` must be removed and entries for which it returns `true` must remain. When `extract_if` or `extract_from_if` is called, entries for which the predicate returns `true` must be yielded by the iterator and removed only as they are yielded. If a predicate panics, then the write transaction must be poisoned and a later commit must raise `CommitError::TransactionPoisoned`.

**Size Limits.** If an inserted key, inserted value, reserved value, or combined key-value pair exceeds the supported storage limit, then the operation must raise `StorageError::ValueTooLarge`.

## Multimap Tables

Multimap tables store multiple ordered values for each key while sharing the same transaction and persistence rules as normal tables.

**Insertion and Duplicate Values.** Multimap mutation and lookup methods must accept borrowed key and value inputs compatible with the table definition's `Value::SelfType`, matching the argument flexibility of normal tables. For multimap types whose key or value definition is `&str`, callers must be able to pass string literals directly for both key and value, without a double-reference wrapper. When `MultimapTable::insert` receives a key-value pair that was absent, it must add the pair and return `false`. When the same key-value pair is already present, it must leave the table unchanged and return `true`.

**Lookup and Ordering.** When `get` is called for a key in a multimap table, it must return a `MultimapValue` iterator over that key's values in ascending order. When the key is absent, it must return an empty iterator whose `len` returns zero and whose `is_empty` returns true. When `range` or `iter` is called on a readable or writable multimap table, it must return key-to-values entries in ascending key order, and each value iterator must expose values in ascending value order. The `range` operation must accept inclusive, exclusive, and unbounded key bounds and must be double-ended.

**Removal.** When `remove` receives an existing key-value pair, it must remove only that pair and return `true`. The multimap remove method must accept the same key and value argument forms as multimap insert, including direct string slices for `&str` definitions. When the pair is missing, it must leave the table unchanged and return `false`. When `remove_all` receives a key, it must remove all values for that key and return the removed values in ascending order; for a missing key it must return an empty iterator.

**Length and Statistics.** `ReadableTableMetadata::len` on a multimap table must return the number of key-value pairs, not the number of distinct keys. Table and multimap stats must return public counters for tree height, leaf pages, branch pages, stored bytes, metadata bytes, and fragmented bytes. The corresponding accessor methods are `tree_height()`, `leaf_pages()`, `branch_pages()`, `stored_bytes()`, `metadata_bytes()`, and `fragmented_bytes()`. If the backend cannot read the underlying state, then stats and length methods must raise a storage error.

## Owned Guards, Values, and Iterators

Guards and owned iterators expose stored bytes as typed values while preserving transaction lifetimes.

**Access Guards.** `AccessGuard::value` and `AccessGuardMut::value` must return the value decoded through the table's `Value` implementation. Mutating guard types must write changes back through the same transaction before commit. If the referenced database is closed or corrupted before access, then guard operations must raise a storage error.

**Owned Table Reads.** `ReadOnlyTable::get_owned` must return an `OwnedAccessGuard` that keeps the read transaction alive until the guard is dropped. `ReadOnlyTable::range_owned` must accept the same inclusive, exclusive, and unbounded range bounds as `range` and must return an `OwnedRange` that keeps the read transaction alive until the range and yielded owned guards are dropped. The owned range iterator must yield key and value owned guards as paired items and must support double-ended iteration over the bounded set. Owned guards must return the same values as non-owned reads over the same snapshot.

**Owned Multimap Reads.** `ReadOnlyMultimapTable::get_owned` must return an `OwnedMultimapValue` that keeps the read transaction alive while values are iterated. `ReadOnlyMultimapTable::range_owned` must accept the same inclusive, exclusive, and unbounded key bounds as multimap `range` and must return an `OwnedMultimapRange` that keeps the read transaction alive while key-value groups are iterated. The owned multimap range iterator must yield decoded key guards paired with owned value iterators and must support double-ended traversal over the bounded key groups.

**Iterator Finalization.** `ExtractIf::close` must finalize pending removals and return an error if finalization fails. Dropping an extract iterator must finalize through the same rules. After an extract iterator has latched an error, later iteration must keep returning an error rather than resuming with later entries.

## Savepoints and Table Namespace Changes

Savepoints and namespace operations expose rollback and metadata behavior through the public transaction API.

**Ephemeral Savepoints.** When `ephemeral_savepoint` is called before the write transaction has opened, renamed, or deleted a data table, it must return a `Savepoint` that represents the current database state. If the transaction is already dirty, then it must raise `SavepointError::InvalidSavepoint`. The savepoint must become unavailable when dropped.

**Persistent Savepoints.** When `persistent_savepoint` is called with immediate durability and a clean transaction namespace, it must persist a savepoint identifier and return that identifier. `get_persistent_savepoint` must accept a savepoint identifier and return the corresponding savepoint for an existing identifier and raise `SavepointError::InvalidSavepoint` for a missing identifier. `list_persistent_savepoints` must return a `Result`-wrapped lazy iterator of existing persistent identifiers. `delete_persistent_savepoint` must accept a savepoint identifier and return true when it deletes an existing identifier and false when no identifier existed.

**Savepoint Restore.** When `restore_savepoint` receives a valid savepoint from the same database, it must restore the write transaction's table state to that savepoint. Restoring an older savepoint must invalidate savepoints created after it. If a savepoint is from another database, already invalidated, or incompatible with the current transaction, then restore must raise `SavepointError::InvalidSavepoint`. If restoring an older savepoint would modify persistent savepoints while durability is below `Durability::Immediate`, then restore must raise `SavepointError::ImmediateDurabilityRequired`.

**Namespace Mutation.** When `rename_table` or `rename_multimap_table` receives an existing handle and a new handle name, it must move the table under that name in the current write transaction. The normal-table namespace methods must accept handle parameters implementing the sealed `TableHandle` trait, including typed `TableDefinition` values, opened `Table` handles, and untyped normal-table handles. The multimap namespace methods must accept handle parameters implementing the sealed `MultimapTableHandle` trait, including typed `MultimapTableDefinition` values, opened `MultimapTable` handles, and untyped multimap-table handles. Renaming a table to its current name must succeed and leave the table unchanged. When the target name already exists, the operation must raise `TableError::TableExists`. Deleting a table must return a `Result` containing whether the named table existed.

## Typed Values and Keys

The public type traits define how Rust values are encoded, decoded, compared, and identified.

**Value Contract.** A `Value` implementation must define the borrowed `SelfType`, the `AsBytes` associated type, the bytes returned by `as_bytes`, the decode performed by `from_bytes`, fixed-width metadata through `fixed_width`, and type identity through `type_name`. Built-in implementations for unit, booleans, integers, `char`, floats, strings, byte slices, arrays, options, and tuples must round-trip through `as_bytes` and `from_bytes`.

**Key Contract.** A `Key` implementation must compare encoded byte slices in the same order that table iteration exposes. Built-in numeric keys must sort by numeric order, string and byte-slice keys must sort lexicographically, options must sort `None` before `Some`, arrays must sort lexicographically by element sequence, and tuples must sort lexicographically by tuple field order. The `separator` helper must return an encoded key greater than or equal to the left input and less than the right input, and `min_encoded_key` must return the encoded smallest key when one exists. Both helpers must preserve lookup order.

**Type Names.** `TypeName::new` must create a public type identity string. The `name` accessor must return the stored identity. Opening an existing table with a different key or value `TypeName` must raise a type mismatch error rather than reading bytes as the wrong type.

## State Model

The durable state consists of database metadata, table namespace entries, normal-table records, multimap records, pending savepoint records, committed transaction roots, and storage durability state.

The public projections of this state are:

- Database handles opened through paths, files, and storage backends.
- Read snapshots obtained from `begin_read`.
- Write transactions obtained from `begin_write`.
- Normal table views exposed through `Table`, `ReadOnlyTable`, `ReadOnlyUntypedTable`, and `ReadableTable`.
- Multimap views exposed through `MultimapTable`, `ReadOnlyMultimapTable`, `ReadOnlyUntypedMultimapTable`, and `ReadableMultimapTable`.
- Guard and iterator values exposed through access guards, ranges, owned ranges, multimap values, and extract iterators.
- Namespace views exposed through table handles, list operations, rename operations, and delete operations.
- Durability, integrity, compaction, savepoint, database stats, and table stats APIs.

## Error Semantics

| Condition | Required error |
|---|---|
| Opening a writable database while an exclusive file lock is held | `DatabaseError::DatabaseAlreadyOpen` |
| Integrity check, compaction, or another exclusive operation while a transaction blocks it | `DatabaseError::TransactionInProgress` or `CompactionError::TransactionInProgress` |
| Read-only repair is required and repair is unavailable or aborted | `DatabaseError::RepairAborted` |
| Old file format requires manual upgrade | `DatabaseError::UpgradeRequired` |
| Opening a missing table from a read transaction | `TableError::TableDoesNotExist` |
| Opening a normal table as multimap or a multimap table as normal | `TableError::TableIsNotMultimap` or `TableError::TableIsMultimap` |
| Opening an existing table with incompatible key or value identity | `TableError::TableTypeMismatch` or `TableError::TypeDefinitionChanged` |
| Opening the same table mutably more than once in one write transaction | `TableError::TableAlreadyOpen` |
| Creating or restoring an invalid savepoint | `SavepointError::InvalidSavepoint` |
| Persistent savepoint operation without immediate durability | `SavepointError::ImmediateDurabilityRequired` |
| Lowering durability after persistent savepoint creation or deletion | `SetDurabilityError::PersistentSavepointModified` |
| Committing a poisoned write transaction | `CommitError::TransactionPoisoned` |
| Key, value, reserved value, or pair exceeds supported storage size | `StorageError::ValueTooLarge` |
| Operation on a closed database-backed object | `StorageError::DatabaseClosed` |
| Corrupted durable state that cannot be read or repaired | `StorageError::Corrupted` |

The error variants that identify a table name must carry that name as a
`String`: `TableDoesNotExist`, `TableIsMultimap`, `TableIsNotMultimap`,
`TableExists`, and `TableAlreadyOpen`. `StorageError::Corrupted` must carry a
diagnostic `String`, and `StorageError::ValueTooLarge` must carry the rejected
size as a `usize`. `TableError::TableTypeMismatch` and
`TableError::TypeDefinitionChanged` must carry the type identity details needed
to describe the mismatch. `CompactionError` must expose the three blocker
variants `PersistentSavepointExists`, `EphemeralSavepointExists`, and
`TransactionInProgress`.

## Cross-View Invariants

1. A value inserted through a normal table in a committed write transaction must be returned by a later read transaction opened from the same `Database` and by a database reopened from the same path.
2. A write transaction that is aborted or dropped without commit must leave later read transactions and reopened databases observing the previously committed state.
3. A read transaction must keep its original snapshot even when a later write transaction creates, updates, renames, or deletes tables.
4. `list_tables` and `list_multimap_tables` must agree with successful opens, renames, and deletes in the same transaction view.
5. Normal table `len`, `is_empty`, `first`, `last`, `iter`, and `range` must describe the same ordered key-value set.
6. Multimap `len`, `get`, `iter`, `range`, `remove`, and `remove_all` must describe the same ordered key-value-pair set.
7. Owned guards and owned ranges from read-only tables must expose the same snapshot values as non-owned reads and must keep those values accessible after the originating transaction handle is otherwise dropped.
8. Savepoint restore must make table data, namespace listings, and subsequent commit visibility match the restored snapshot.
9. Table type identity must be enforced consistently by write opens, read opens, untyped handles, and namespace listing.
10. Database and table statistics must never report fewer stored bytes or entries than the public records visible through the same transaction view.

## Public Interface

### Import Surface

```rust
use redb::{
    AccessGuard, AccessGuardMut, AccessGuardMutInPlace, Builder, CacheStats, CommitError,
    CompactionError, Database, DatabaseError, DatabaseStats, Durability, Entry, Error,
    ExtractIf, MultimapRange, MultimapTable, MultimapTableDefinition, MultimapTableHandle,
    MultimapValue, MutInPlaceValue, OccupiedEntry, OwnedAccessGuard, OwnedMultimapRange,
    OwnedMultimapValue, OwnedRange, Range, ReadOnlyDatabase, ReadOnlyMultimapTable,
    ReadOnlyTable, ReadOnlyUntypedMultimapTable, ReadOnlyUntypedTable, ReadableDatabase,
    ReadableMultimapTable, ReadableTable, ReadableTableMetadata, RepairSession,
    Savepoint, SavepointError, SetDurabilityError, StorageBackend, StorageError,
    Key, ReadTransaction, Result, Table, TableDefinition, TableError, TableHandle, TableStats,
    TransactionError, TypeName, UntypedMultimapTableHandle, UntypedTableHandle, VacantEntry,
    Value,
    WriteTransaction,
};
use redb::backends::{FileBackend, InMemoryBackend};
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Database` | struct | Opens writable embedded databases and begins read or write transactions. |
| `ReadOnlyDatabase` | struct | Opens existing databases for snapshot reads without write access. |
| `Builder` | struct | Configures storage, page sizing, cache sizing, growth, and repair behavior before opening. |
| `ReadableDatabase` | trait | Shared interface for handles that begin read transactions and expose cache stats. |
| `StorageBackend` | trait | Public backend interface for caller-supplied storage. |
| `FileBackend` | struct | File-based storage backend. |
| `InMemoryBackend` | struct | Memory-backed storage backend. |
| `ReadTransaction` | struct | Stable read snapshot over committed database state. |
| `WriteTransaction` | struct | Mutable transaction that stages writes before commit or abort. |
| `Durability` | enum | Transaction durability policy with `None` and `Immediate` variants. |
| `Savepoint` | struct | Snapshot token used to restore a write transaction. |
| `TableDefinition` | struct | Typed normal-table definition identified by name. |
| `MultimapTableDefinition` | struct | Typed multimap-table definition identified by name. |
| `TableHandle` | trait | Name-bearing handle for normal tables. |
| `MultimapTableHandle` | trait | Name-bearing handle for multimap tables. |
| `UntypedTableHandle` | struct | Name-only handle for normal tables. |
| `UntypedMultimapTableHandle` | struct | Name-only handle for multimap tables. |
| `Table` | struct | Writable normal table view inside a write transaction. |
| `ReadOnlyTable` | struct | Read-only typed table view inside a read transaction. |
| `ReadOnlyUntypedTable` | struct | Read-only name and metadata view for a normal table. |
| `ReadableTable` | trait | Shared ordered lookup and range interface for normal tables. |
| `ReadableTableMetadata` | trait | Shared length, emptiness, and statistics interface for table views. |
| `TableStats` | struct | Public storage counters for one table. |
| `AccessGuard` | struct | Read guard for a key or value decoded from storage. |
| `AccessGuardMut` | struct | Mutable guard for replacing a stored value. |
| `AccessGuardMutInPlace` | struct | Mutable guard for in-place value bytes. |
| `OwnedAccessGuard` | struct | Read guard that owns the transaction lifetime. |
| `Range` | struct | Double-ended iterator over normal-table key-value pairs. |
| `OwnedRange` | struct | Transaction-owning double-ended normal-table range iterator. |
| `Entry` | enum | Occupied or vacant entry view for a normal-table key. |
| `OccupiedEntry` | struct | Entry view for an existing normal-table key. |
| `VacantEntry` | struct | Entry view for a missing normal-table key. |
| `ExtractIf` | struct | Iterator that removes matching normal-table entries as it yields them. |
| `MultimapTable` | struct | Writable multimap table view inside a write transaction. |
| `ReadOnlyMultimapTable` | struct | Read-only typed multimap table view inside a read transaction. |
| `ReadOnlyUntypedMultimapTable` | struct | Read-only name and metadata view for a multimap table. |
| `ReadableMultimapTable` | trait | Shared ordered lookup and range interface for multimap tables. |
| `MultimapValue` | struct | Double-ended iterator over the values for one multimap key. |
| `OwnedMultimapValue` | struct | Transaction-owning iterator over the values for one multimap key. |
| `MultimapRange` | struct | Double-ended iterator over multimap key-to-values entries. |
| `OwnedMultimapRange` | struct | Transaction-owning multimap range iterator. |
| `Value` | trait | Defines byte encoding, decoding, fixed-width metadata, and type identity for stored values. |
| `MutInPlaceValue` | trait | Extends `Value` for values whose stored bytes are initialized and mutated in place. |
| `Key` | trait | Extends `Value` with encoded ordering and separator behavior for table keys. |
| `TypeName` | struct | Public type identity used to detect table definition mismatches. |
| `DatabaseStats` | struct | Public storage counters across the database. |
| `CacheStats` | struct | In-memory cache metrics when cache metrics are enabled. |
| `RepairSession` | struct | Repair callback session used by builder-driven repair. |
| `Error` | enum | Convenience superset for crate error categories. |
| `StorageError` | enum | Storage-layer, corruption, size, closure, and I/O failures. |
| `DatabaseError` | enum | Database open, repair, upgrade, and exclusive-operation failures. |
| `TableError` | enum | Table kind, type, existence, and mutable-open failures. |
| `TransactionError` | enum | Read-transaction close and storage failures. |
| `CommitError` | enum | Commit storage failures and poisoned transaction failures. |
| `SavepointError` | enum | Savepoint validity and durability failures. |
| `SetDurabilityError` | enum | Durability-setting failures. |
| `CompactionError` | enum | Compaction blockers and storage failures. |
| `Result` | type alias | Crate result alias for storage-oriented operations. |

### CLI Entry Points

There is no console script for this package. Programmatic use is through Rust crate imports.

## Appendix A: Environment

The working environment runs Rust 1.90 on Linux without network access during assessment. The assessment workspace lockfile provides the non-target crates required by the public tests: `tempfile`, `rand`, and Rust standard library crates. The assessment environment provides `cargo` and `cargo-nextest`.

The project must declare its packaging metadata in `Cargo.toml` at the project root. The package under assessment must expose a crate named `redb`; the assessment harness supplies the candidate crate to the locked workspace through Cargo patching rather than by installing a registry copy.

## Appendix B: Assessment Notes

Assessment covers public database workflows, transaction visibility, table and multimap behavior, owned guards and iterators, savepoint behavior, table namespace changes, typed value/key behavior, persistence across reopen, and documented error categories.

The tests exercise both local behavior and composed workflows that connect multiple public projections, such as writing through a transaction, observing through a read snapshot, checking namespace listings, reopening the database, and comparing table statistics. They do not require private modules, private fields, exact error message text, or raw file-format assertions.
