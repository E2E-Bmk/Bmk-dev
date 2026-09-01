# redb Clause Sidecar v5

| Clause ID | Section | Clause |
|---|---|---|
| REDB-DB-001 | Database Opening and Storage | When `Database::create` receives a path that does not exist or names an empty file, it must initialize a new database at that path. |
| REDB-DB-002 | Database Opening and Storage | When `Database::create` receives a path containing a valid database, it must open that database without deleting committed content. |
| REDB-DB-003 | Database Opening and Storage | When `Database::open` receives an existing valid database path, it must open the stored content. |
| REDB-DB-004 | Database Opening and Storage | If the path contains data that is not a valid database, then opening must raise `DatabaseError::Storage`. |
| REDB-DB-005 | Database Opening and Storage | When `begin_read` is called, the returned `ReadTransaction` must capture only data committed before that call. |
| REDB-DB-006 | Database Opening and Storage | Dropping a `Database` must close the store, flush buffered state, release the file lock, and make later operations through read transactions that still depend on that handle raise `StorageError::DatabaseClosed`. |
| REDB-DB-007 | Database Opening and Storage | While a `WriteTransaction` is alive, dropping the `Database` handle must keep the store open until that write transaction commits, aborts, or is dropped. |
| REDB-DB-008 | Database Opening and Storage | `Builder::create`, `Builder::open`, `Builder::open_read_only`, `Builder::create_file`, and `Builder::create_with_backend` must operate on their documented input kinds. |
| REDB-DB-009 | Database Opening and Storage | A writable `Database` and a `ReadOnlyDatabase` opened for the same file must not be held concurrently when the platform provides file locking; multiple `ReadOnlyDatabase` handles for the same file must be allowed concurrently. |
| REDB-TXN-001 | Transactions and Visibility | When `Database::begin_write` succeeds, it must return a `WriteTransaction` that stages table creation, inserts, removals, table renames, table deletion, durability changes, and savepoint operations. |
| REDB-TXN-002 | Transactions and Visibility | When `commit` succeeds, all staged writes must become visible to future read transactions atomically. |
| REDB-TXN-003 | Transactions and Visibility | When `abort` succeeds or a write transaction is dropped without commit, staged writes must not become visible to future read transactions. |
| REDB-TXN-004 | Transactions and Visibility | A `ReadTransaction` must observe a stable snapshot. |
| REDB-TXN-005 | Transactions and Visibility | When a write commits after a read transaction begins, the existing read transaction must continue to observe its original snapshot, and a new read transaction must observe the committed state. |
| REDB-TXN-006 | Transactions and Visibility | When `ReadTransaction::close` is called while tables, guards, ranges, or other values still reference that transaction, it must raise `TransactionError::ReadTransactionStillInUse`. |
| REDB-TXN-007 | Transactions and Visibility | Restoring an older savepoint below immediate durability must raise `SavepointError::ImmediateDurabilityRequired` when persistent savepoints would be modified. |
| REDB-TAB-001 | Tables and Ordered Records | `TableDefinition::new` must create a typed normal-table definition identified by its name. |
| REDB-TAB-002 | Tables and Ordered Records | When `WriteTransaction::open_table` or `open_multimap_table` names a missing table, the table must be created inside the transaction. |
| REDB-TAB-030 | Tables and Ordered Records | The write-transaction table-opening methods must operate through a shared write-transaction handle; callers must not be required to bind the `WriteTransaction` itself as mutable in order to open tables. |
| REDB-TAB-003 | Tables and Ordered Records | When `ReadTransaction::open_table` or `open_multimap_table` names a missing table, the operation must raise `TableError::TableDoesNotExist`. |
| REDB-TAB-004 | Tables and Ordered Records | When `Table::insert` stores a key and value, it must return an `AccessGuard` for the previous value or `None` when the key was absent. |
| REDB-TAB-005 | Tables and Ordered Records | When `Table::remove` removes a key, it must return an `AccessGuard` for the removed value or `None` when the key was absent. |
| REDB-TAB-006 | Tables and Ordered Records | When `get`, `first`, `last`, `iter`, or `range` is called on a readable table, the returned guards and iterators must expose key-value pairs ordered by the `Key` implementation. |
| REDB-TAB-007 | Tables and Ordered Records | When `range` receives an inclusive, exclusive, or unbounded range, it must return only entries whose keys fall inside those bounds. |
| REDB-TAB-008 | Tables and Ordered Records | If an inserted key, inserted value, reserved value, or combined key-value pair exceeds the supported storage limit, then the operation must raise `StorageError::ValueTooLarge`. |
| REDB-TAB-009 | Tables and Ordered Records | Table listing methods must return `Result`-wrapped lazy iterators of untyped handles, return normal table handles separately from multimap table handles, and reflect the calling transaction's view. |
| REDB-TAB-010 | Tables and Ordered Records | Table mutation and lookup methods must accept borrowed key and value inputs compatible with the table definition's `Value::SelfType`, so a table whose key or value type is `&str` accepts string literals directly. |
| REDB-TAB-011 | Tables and Ordered Records | When `pop_first` or `pop_last` is called on a writable table, it must remove and return the lowest or highest key-value pair, or return `None` when the table is empty. |
| REDB-TAB-012 | Tables and Ordered Records | `OccupiedEntry::remove_entry` must remove the entry and return both the removed key and the removed value guard. |
| REDB-TAB-013 | Tables and Ordered Records | `VacantEntry::key` must return a reference to the requested key before insertion. |
| REDB-TAB-014 | Tables and Ordered Records | When `or_insert_with_key` inserts a missing key, its closure must receive a reference to that key and the returned value must become the stored value. |
| REDB-TAB-015 | Tables and Ordered Records | For table types whose key or value definition is `&str`, callers must be able to pass `"key"` and `"value"` as the key or value argument; the public methods must not force a second reference level such as `&&str`. |
| REDB-TAB-016 | Tables and Ordered Records | The insert method must accept a key argument in the key's borrowed self type and a value argument in the value's borrowed self type, including references such as `&u64` for integer values and direct string slices for string-slice values. |
| REDB-TAB-017 | Tables and Ordered Records | A listing iterator must support iterator adapters before collection, including mapping each handle to its public name. |
| REDB-TAB-018 | Tables and Ordered Records | The removed key must be exposed as the decoded key value, not as an access guard wrapper, so callers must be able to compare it directly with values of the key type. |
| REDB-TAB-019 | Tables and Ordered Records | `VacantEntry::key` must return a reference to the requested decoded key before insertion, so callers must be able to dereference it or use it in arithmetic and comparison according to the key type. |
| REDB-TAB-020 | Tables and Ordered Records | When `or_insert_with_key` inserts a missing key, its closure must receive a reference to the decoded requested key and the returned value must become the stored value. |
| REDB-TAB-021 | Tables and Ordered Records | `ReadTransaction::open_untyped_table` and `ReadTransaction::open_untyped_multimap_table` must open the corresponding table through its public name-bearing handle. |
| REDB-TAB-022 | Tables and Ordered Records | `Table::insert` and `Table::remove` must return an `AccessGuard` for an existing previous or removed value. |
| REDB-TAB-023 | Tables and Ordered Records | `Table::insert_reserve` must return an `AccessGuardMutInPlace` for the reserved value, whose mutable byte slice must be writable before commit, and `Table::get_mut` must return an `AccessGuardMut` for an existing key and `None` for a missing key. |
| REDB-TAB-024 | Tables and Ordered Records | `Table::entry` must accept a key in the key definition's borrowed self type and return an entry tied to the table borrow. |
| REDB-TAB-025 | Tables and Ordered Records | `VacantEntry::into_key` must return the decoded key value and `OccupiedEntry::into_mut` must return an `AccessGuardMut` tied to the entry lifetime. |
| REDB-TAB-026 | Tables and Ordered Records | `OccupiedEntry::insert` must replace the occupied value and return its previous value guard. `AccessGuardMut::insert` must replace the guarded value and return success; if the replacement exceeds the supported value size, it must raise `StorageError::ValueTooLarge`. |
| REDB-TAB-027 | Tables and Ordered Records | `and_modify` must pass an `AccessGuardMut` to its closure, propagate the closure result, and return the entry for continued use. |
| REDB-TAB-028 | Tables and Ordered Records | A listing iterator must support iterator adapters before collection, including mapping each handle to its public name. |
| REDB-TAB-029 | Tables and Ordered Records | Table error variants identifying a table must carry the documented table name or type identity details. |
| REDB-TAB-031 | Tables and Ordered Records | Both `OccupiedEntry::key` and `VacantEntry::key` must return a reference to the decoded key in the form `&K::SelfType`; the returned reference for an integer key must yield the integer value upon dereferencing, and the returned reference for a string-slice key must yield the string slice upon dereferencing. |
| REDB-TAB-032 | Tables and Ordered Records | `OccupiedEntry::get` must return a `Result` containing an `AccessGuard` for the value, and `OccupiedEntry::get_mut` and `into_mut` must return `Result`-wrapped mutable access guards. |
| REDB-TAB-034 | Tables and Ordered Records | Entry insertion methods must accept borrowed values in the value definition's borrowed self type, matching `Table::insert`. |
| REDB-MM-001 | Multimap Tables | `MultimapTableDefinition::new` must create a typed multimap-table definition identified by its name. |
| REDB-MM-002 | Multimap Tables | When `MultimapTable::insert` receives a key-value pair that was absent, it must add the pair and return `false`. |
| REDB-MM-003 | Multimap Tables | When the same key-value pair is already present, it must leave the table unchanged and return `true`. |
| REDB-MM-004 | Multimap Tables | When `get` is called for a key in a multimap table, it must return a `MultimapValue` iterator over that key's values in ascending order. |
| REDB-MM-005 | Multimap Tables | When `remove_all` receives a key, it must remove all values for that key and return the removed values in ascending order; for a missing key it must return an empty iterator. |
| REDB-MM-006 | Multimap Tables | Multimap mutation and lookup methods must accept borrowed key and value inputs compatible with the table definition's `Value::SelfType`, matching the argument flexibility of normal tables. |
| REDB-MM-007 | Multimap Tables | When `range` or `iter` is called on a readable or writable multimap table, it must return key-to-values entries in ascending key order, and each value iterator must expose values in ascending value order. |
| REDB-MM-008 | Multimap Tables | The `range` operation must accept inclusive, exclusive, and unbounded key bounds and must be double-ended. |
| REDB-MM-009 | Multimap Tables | For multimap types whose key or value definition is `&str`, callers must be able to pass string literals directly for both key and value, without a double-reference wrapper. |
| REDB-MM-010 | Multimap Tables | The multimap remove method must accept the same key and value argument forms as multimap insert, including direct string slices for `&str` definitions. |
| REDB-GRD-001 | Owned Guards, Values, and Iterators | `ReadOnlyTable::get_owned` must return an `OwnedAccessGuard` that keeps the read transaction alive until the guard is dropped. |
| REDB-GRD-002 | Owned Guards, Values, and Iterators | `ReadOnlyTable::range_owned` must return an `OwnedRange` that keeps the read transaction alive until the range and yielded owned guards are dropped. |
| REDB-GRD-003 | Owned Guards, Values, and Iterators | `ReadOnlyTable::range_owned` must accept the same inclusive, exclusive, and unbounded range bounds as `range` and must return an `OwnedRange` that keeps the read transaction alive until the range and yielded owned guards are dropped. |
| REDB-GRD-004 | Owned Guards, Values, and Iterators | `ReadOnlyMultimapTable::range_owned` must accept the same inclusive, exclusive, and unbounded key bounds as multimap `range` and must return an `OwnedMultimapRange` that keeps the read transaction alive while key-value groups are iterated. |
| REDB-GRD-005 | Owned Guards, Values, and Iterators | The owned range iterator must yield key and value owned guards as paired items and must support double-ended iteration over the bounded set. |
| REDB-GRD-006 | Owned Guards, Values, and Iterators | The owned multimap range iterator must yield decoded key guards paired with owned value iterators and must support double-ended traversal over the bounded key groups. |
| REDB-SVP-001 | Savepoints and Table Namespace Changes | When `ephemeral_savepoint` is called before the write transaction has opened, renamed, or deleted a data table, it must return a `Savepoint` that represents the current database state. |
| REDB-SVP-002 | Savepoints and Table Namespace Changes | If the transaction is already dirty, then it must raise `SavepointError::InvalidSavepoint`. |
| REDB-SVP-003 | Savepoints and Table Namespace Changes | When `restore_savepoint` receives a valid savepoint from the same database, it must restore the write transaction's table state to that savepoint. |
| REDB-SVP-004 | Savepoints and Table Namespace Changes | When `rename_table` or `rename_multimap_table` receives a new handle name, it must move the table under that name in the current write transaction. |
| REDB-SVP-005 | Savepoints and Table Namespace Changes | `get_persistent_savepoint` and `delete_persistent_savepoint` must accept a persistent savepoint identifier. |
| REDB-SVP-006 | Savepoints and Table Namespace Changes | `list_persistent_savepoints` must return a `Result`-wrapped lazy iterator of existing persistent identifiers. |
| REDB-SVP-007 | Savepoints and Table Namespace Changes | The normal-table namespace methods must accept handle parameters implementing the sealed `TableHandle` trait, including typed `TableDefinition` values, opened `Table` handles, and untyped normal-table handles. |
| REDB-SVP-008 | Savepoints and Table Namespace Changes | The multimap namespace methods must accept handle parameters implementing the sealed `MultimapTableHandle` trait, including typed `MultimapTableDefinition` values, opened `MultimapTable` handles, and untyped multimap-table handles. |
| REDB-SVP-009 | Savepoints and Table Namespace Changes | Deleting a table must return a `Result` containing whether the named table existed. |
| REDB-TYP-001 | Typed Values and Keys | A `Value` implementation must define the borrowed `SelfType`, the bytes returned by `as_bytes`, the decode performed by `from_bytes`, fixed-width metadata through `fixed_width`, and type identity through `type_name`. |
| REDB-TYP-002 | Typed Values and Keys | A `Key` implementation must compare encoded byte slices in the same order that table iteration exposes. |
| REDB-TYP-003 | Typed Values and Keys | Opening an existing table with a different key or value `TypeName` must raise a type mismatch error rather than reading bytes as the wrong type. |
| REDB-TYP-004 | Typed Values and Keys | A `Value` implementation must define the `AsBytes` associated type and built-in `char` values must round-trip through the value encoding. |
| REDB-TYP-005 | Typed Values and Keys | A `Key` implementation must provide `separator` and `min_encoded_key` helpers that preserve encoded lookup order. |
| REDB-CMP-001 | Database Opening and Storage | Compaction blocked by persistent savepoints, ephemeral savepoints, or transactions must raise the corresponding named `CompactionError` variant. |
