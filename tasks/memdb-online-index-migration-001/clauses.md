# Clause Traceability

| Clause ID | Section | Contract |
|---|---|---|
| MDB-MIG-001 | Migration Planning and Validation | An empty migration is a successful no-op that preserves the current schema generation and watches. |
| MDB-MIG-002 | Migration Planning and Validation | One table entry may add several indexes and publishes them atomically. |
| MDB-MIG-003 | Migration Planning and Validation | One call may atomically migrate several distinct tables. |
| MDB-MIG-004 | Migration Planning and Validation | Dropping a secondary index removes its name and tree from new generations. |
| MDB-MIG-005 | Migration Planning and Validation | A name present once in Drop and once in Add is atomically replaced. |
| MDB-MIG-006 | Migration Planning and Validation | Additions and removals for one table publish as one complete generation. |
| MDB-MIG-007 | Migration Planning and Validation | Validation covers the complete call before publication. |
| MDB-MIG-008 | Migration Planning and Validation | An accepted IndexSchema is shallow-copied before publication. |
| MDB-BACKFILL-001 | Atomic Backfill and Index Semantics | Added indexes contain every eligible pre-existing row and use the supplied indexer encoding. |
| MDB-BACKFILL-002 | Atomic Backfill and Index Semantics | Non-unique backfill preserves every object sharing one secondary value. |
| MDB-BACKFILL-003 | Atomic Backfill and Index Semantics | A unique index rejects collisions between distinct primary IDs. |
| MDB-BACKFILL-004 | Atomic Backfill and Index Semantics | MultiIndexer backfill publishes every emitted key. |
| MDB-BACKFILL-005 | Atomic Backfill and Index Semantics | AllowMissing skips rows that emit no index value. |
| MDB-BACKFILL-006 | Atomic Backfill and Index Semantics | Duplicate unique keys emitted by one object do not conflict with that same primary ID. |
| MDB-ROLLBACK-001 | Atomic Backfill and Index Semantics | A failed migration preserves schema generation identity. |
| MDB-ROLLBACK-002 | Atomic Backfill and Index Semantics | A failed migration preserves existing query results. |
| MDB-ROLLBACK-003 | Atomic Backfill and Index Semantics | A failed migration does not publish an added index name. |
| MDB-ROLLBACK-004 | Atomic Backfill and Index Semantics | A failing multi-index or multi-table batch publishes none of its earlier valid entries. |
| MDB-ROLLBACK-005 | Atomic Backfill and Index Semantics | A failed replacement preserves the complete old definition and tree. |
| MDB-MVCC-001 | MVCC Generations and Concurrency | A transaction created before AddIndex rejects the new index name. |
| MDB-MVCC-002 | MVCC Generations and Concurrency | A transaction created before DropIndex retains the dropped index and its contents. |
| MDB-MVCC-003 | MVCC Generations and Concurrency | A transaction created after publication sees added indexes. |
| MDB-MVCC-004 | MVCC Generations and Concurrency | Txn.Snapshot retains its source transaction's schema generation. |
| MDB-MVCC-005 | MVCC Generations and Concurrency | A pre-replacement transaction interprets the index using the former definition. |
| MDB-MVCC-006 | MVCC Generations and Concurrency | A pre-migration MemDB snapshot retains its complete old generation. |
| MDB-MVCC-007 | MVCC Generations and Concurrency | Multiple retained transactions may continue to represent distinct sequential generations. |
| MDB-MVCC-008 | MVCC Generations and Concurrency | Txn.Snapshot preserves staged rows while retaining the old schema generation. |
| MDB-CONC-001 | MVCC Generations and Concurrency | A writer already holding the writer boundary completes before migration backfill begins. |
| MDB-CONC-002 | MVCC Generations and Concurrency | A writer requested during backfill begins after successful publication and uses the new schema. |
| MDB-CONC-003 | MVCC Generations and Concurrency | A writer requested after migration failure uses the unchanged old schema. |
| MDB-CONC-004 | MVCC Generations and Concurrency | Post-migration writers enforce the new index's AllowMissing and required-value rules. |
| MDB-CONC-005 | MVCC Generations and Concurrency | New readers may acquire the old generation while backfill is still building. |
| MDB-CONC-006 | MVCC Generations and Concurrency | Concurrent migrations serialize on the writer boundary. |
| MDB-CONC-007 | MVCC Generations and Concurrency | Migration failure releases a waiting writer. |
| MDB-CONC-008 | MVCC Generations and Concurrency | Concurrent awakened readers observe a complete published generation. |
| MDB-WATCH-001 | Watch and Lifecycle Semantics | Successful migration closes old-generation watches in every affected table. |
| MDB-WATCH-002 | Watch and Lifecycle Semantics | Watch notification occurs after publication and before the migration call returns. |
| MDB-WATCH-003 | Watch and Lifecycle Semantics | Failed migration closes no watch. |
| MDB-WATCH-004 | Watch and Lifecycle Semantics | Empty migration closes no watch. |
| MDB-WATCH-005 | Watch and Lifecycle Semantics | Watches in unaffected tables remain open. |
| MDB-WATCH-006 | Watch and Lifecycle Semantics | A woken old transaction retains readable immutable index contents. |
| MDB-WATCH-007 | Watch and Lifecycle Semantics | Table-level invalidation includes every pre-migration index in the affected table. |
| MDB-ERR-001 | Error Semantics | Migration on MemDB.Snapshot returns ErrIndexMigrationSnapshot. |
| MDB-ERR-002 | Error Semantics | An unknown table returns ErrIndexMigrationTableNotFound with context. |
| MDB-ERR-003 | Error Semantics | Repeating a table entry returns ErrIndexMigrationDuplicateTable. |
| MDB-ERR-004 | Error Semantics | Repeating an index in Add or Drop returns ErrIndexMigrationDuplicateIndex. |
| MDB-ERR-005 | Error Semantics | Adding an existing name without replacement returns ErrIndexExists. |
| MDB-ERR-006 | Error Semantics | Dropping an absent name returns ErrIndexNotFound. |
| MDB-ERR-007 | Error Semantics | Adding, replacing, or dropping id returns ErrIndexMigrationPrimary. |
| MDB-ERR-008 | Error Semantics | A unique backfill collision returns ErrIndexMigrationUniqueConflict. |
| MDB-ERR-009 | Error Semantics | A required missing value returns ErrIndexMigrationMissingValue. |
| MDB-ERR-010 | Error Semantics | Nil, invalid, unsupported, or failing indexers return ErrIndexMigrationIndexer. |
| MDB-XVIEW-001 | Cross-View Invariants | DBSchema and a new transaction expose the same complete index-name generation. |
| MDB-XVIEW-002 | Cross-View Invariants | Added trees contain every eligible row from the migration's starting primary tree. |
| MDB-XVIEW-003 | Cross-View Invariants | Post-publication insert, update, and delete operations keep migrated indexes consistent. |
| MDB-XVIEW-004 | Cross-View Invariants | A pre-migration transaction never switches schema or index contents. |
| MDB-XVIEW-005 | Cross-View Invariants | A pre-migration database snapshot never switches generation. |
| MDB-XVIEW-006 | Cross-View Invariants | Replacement exposes only a complete old pair or complete new pair. |
| MDB-XVIEW-007 | Cross-View Invariants | Any migration error preserves schema, roots, and watch state together. |
| MDB-XVIEW-008 | Cross-View Invariants | An awakened reader can immediately acquire the complete new generation. |
| MDB-XVIEW-009 | Cross-View Invariants | Unaffected-table schema, roots, results, and watches remain unchanged. |
| MDB-XVIEW-010 | Cross-View Invariants | Unique backfill never silently overwrites a distinct primary ID. |
| MDB-XVIEW-011 | Cross-View Invariants | A concurrent writer cannot commit under only one side of the migration boundary. |
| MDB-XVIEW-012 | Cross-View Invariants | Dropping one index preserves primary rows and every other secondary index. |
