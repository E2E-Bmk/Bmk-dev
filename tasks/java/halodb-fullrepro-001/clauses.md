# halodb v3 Clause Sidecar

Clause IDs are audit-only and do not appear in the candidate-visible specification body. Each quoted clause is verbatim from `wip/halodb/spec/spec_v3.md`; each passed the public-intent Q1 gate, the non-derivability Q2 gate, and the upstream-document/1:N/rule-not-instance Q3 gate. All 126 IDs retained from v2 remain attached to unchanged clauses.

## Representative Workflows

- `HALO-WF-001` — “WHEN the write succeeds, the point lookup, iterator record, live-record count, and statistics size must describe the same key-value state.” — `#configure-write-read-iterate-and-inspect`
- `HALO-WF-002` — “WHEN a cleanly closed directory is reopened, the latest updates and recorded deletions must remain visible through point lookup, iteration, and size.” — `#delete-close-and-reopen`

## Database Ownership and Lifecycle

- `HALO-LIFE-001` — “A caller must open a database with `HaloDB.open`, supplying either a `String` directory path or a `File` plus a `HaloDBOptions` instance.” — `#database-ownership-and-lifecycle`
- `HALO-LIFE-002` — “WHEN the directory does not exist, `HaloDB.open` must create it and initialize an empty database.” — `#database-ownership-and-lifecycle`
- `HALO-LIFE-003` — “WHEN the directory already contains a compatible database, `HaloDB.open` must rebuild the latest-key view and resume from the persisted records and tombstones.” — `#database-ownership-and-lifecycle`
- `HALO-LIFE-004` — “IF the directory cannot be created, read, locked, or initialized, then `HaloDB.open` must raise `HaloDBException`.” — `#database-ownership-and-lifecycle`
- `HALO-LIFE-005` — “WHILE one open `HaloDB` instance owns a directory, another `HaloDB.open` for the same directory must raise `HaloDBException`.” — `#database-ownership-and-lifecycle`
- `HALO-LIFE-006` — “WHEN the owning instance closes or an unsuccessful open releases its partial ownership, a later open must acquire the directory normally.” — `#database-ownership-and-lifecycle`
- `HALO-LIFE-007` — “WHEN metadata indicates an unclean shutdown or an I/O failure, `HaloDB.open` must repair incomplete writable tails, discard corrupt records that do not validate, and rebuild the live-key projection from valid persisted records.” — `#database-ownership-and-lifecycle`
- `HALO-LIFE-008` — “IF the stored maximum data-file size differs from `HaloDBOptions.getMaxFileSize()`, then `HaloDB.open` must raise `IllegalArgumentException` rather than reinterpret existing files.” — `#database-ownership-and-lifecycle`
- `HALO-LIFE-009` — “WHEN `close()` is called, the database must stop background work, flush current data, index, and tombstone writes, release file resources and the directory lock, and mark the directory cleanly closed.” — `#database-ownership-and-lifecycle`
- `HALO-LIFE-010` — “WHEN `close()` is called again after closing has started, it must return without repeating state changes.” — `#database-ownership-and-lifecycle`
- `HALO-LIFE-011` — “IF flushing or closing a resource fails, then `close()` must raise `HaloDBException`.” — `#database-ownership-and-lifecycle`
- `HALO-LIFE-012` — “The two `HaloDB.open` overloads must each return a `HaloDB` instance.” — `#database-ownership-and-lifecycle`
- `HALO-LIFE-013` — “The `HaloDBException` type must be a checked subclass of `Exception`.” — `#database-ownership-and-lifecycle`
- `HALO-LIFE-014` — “The `HaloDB.open`, `get`, `put`, `delete`, `close`, `newIterator`, and `pauseCompaction` methods must be the only methods in the Public Interface that declare a checked exception, and each must declare `HaloDBException`.” — `#database-ownership-and-lifecycle`
- `HALO-LIFE-015` — “The `close()` method must return `void`.” — `#database-ownership-and-lifecycle`

## Key-Value State and Point Operations

- `HALO-OPS-001` — “WHEN `put(key, value)` receives a key no longer than 127 bytes and a byte-array value, it must persist the pair, make that value the current value for the key, and return whether the in-memory index accepted the update.” — `#key-value-state-and-point-operations`
- `HALO-OPS-002` — “WHEN the key already exists, `put` must replace the live value without increasing `size()`.” — `#key-value-state-and-point-operations`
- `HALO-OPS-003` — “IF `key` is longer than 127 bytes, then `put` must raise `HaloDBException`.” — `#key-value-state-and-point-operations`
- `HALO-OPS-004` — “WHEN `get(key)` addresses a live key, it must return the current byte-array value.” — `#key-value-state-and-point-operations`
- `HALO-OPS-005` — “WHEN `get(key)` addresses a key that was never written or has been deleted, it must return `null`.” — `#key-value-state-and-point-operations`
- `HALO-OPS-006` — “IF a read cannot complete after bounded retries around concurrent file replacement, then `get` must raise `HaloDBException`.” — `#key-value-state-and-point-operations`
- `HALO-OPS-007` — “WHEN `delete(key)` addresses a live key, it must remove the key from the live mapping and persist a tombstone.” — `#key-value-state-and-point-operations`
- `HALO-OPS-008` — “WHEN `delete(key)` addresses an absent key, it must return without changing the database.” — `#key-value-state-and-point-operations`
- `HALO-OPS-009` — “IF the tombstone write fails, then `delete` must raise `HaloDBException`.” — `#key-value-state-and-point-operations`
- `HALO-OPS-010` — “The `size()` method must return the number of distinct live keys.” — `#key-value-state-and-point-operations`
- `HALO-OPS-011` — “WHEN an existing key is updated, `size()` must remain unchanged.” — `#key-value-state-and-point-operations`
- `HALO-OPS-012` — “WHEN a live key is deleted, `size()` must decrease once.” — `#key-value-state-and-point-operations`
- `HALO-OPS-013` — “WHEN an absent key is deleted, `size()` must remain unchanged.” — `#key-value-state-and-point-operations`
- `HALO-OPS-014` — “The `put` method must accept exactly two `byte[]` arguments and return a primitive `boolean`.” — `#key-value-state-and-point-operations`
- `HALO-OPS-015` — “The `get` method must accept exactly one `byte[]` key and return a `byte[]` value or `null`.” — `#key-value-state-and-point-operations`
- `HALO-OPS-016` — “The `delete` method must accept exactly one `byte[]` key and return `void`.” — `#key-value-state-and-point-operations`
- `HALO-OPS-017` — “The `size()` method must return a primitive `long`.” — `#key-value-state-and-point-operations`

## Configuration and Durability

- `HALO-OPT-001` — “A new `HaloDBOptions` must default `compactionThresholdPerFile` to `0.75`, `maxFileSize` to 1 MiB, `flushDataSizeBytes` to `-1`, `numberOfRecords` to 1,000,000, `compactionJobRate` to 1 GiB per second, `cleanUpInMemoryIndexOnClose` to `false`, `cleanUpTombstonesDuringOpen` to `false`, `useMemoryPool` to `false`, `fixedKeySize` to 127 bytes, `memoryPoolChunkSize` to 16 MiB, `syncWrite` to `false`, and `buildIndexThreads` to `1`.” — `#configuration-and-durability`
- `HALO-OPT-002` — “WHEN `maxTombstoneFileSize` has not been set, `getMaxTombstoneFileSize()` must return the current `maxFileSize`.” — `#configuration-and-durability`
- `HALO-OPT-003` — “WHEN `setMaxFileSize(maxFileSize)` receives a positive byte count, the matching getter must return it and newly rolled data files must use it as their target maximum.” — `#configuration-and-durability`
- `HALO-OPT-004` — “IF `maxFileSize` is zero or negative, then `setMaxFileSize` must raise `IllegalArgumentException`.” — `#configuration-and-durability`
- `HALO-OPT-005` — “WHEN `setMaxTombstoneFileSize(maxFileSize)` receives a positive byte count, the matching getter must return it and tombstone rollover must use it.” — `#configuration-and-durability`
- `HALO-OPT-006` — “IF that byte count is zero or negative, then `setMaxTombstoneFileSize` must raise `IllegalArgumentException`.” — `#configuration-and-durability`
- `HALO-OPT-007` — “WHEN `setFlushDataSizeBytes(flushDataSizeBytes)` receives a value, the matching getter must return it.” — `#configuration-and-durability`
- `HALO-OPT-008` — “WHERE `flushDataSizeBytes` is positive, accumulated writes must be forced to disk after that many bytes.” — `#configuration-and-durability`
- `HALO-OPT-009` — “WHEN `enableSyncWrites(true)` is selected, each write and delete must be forced to disk before its call returns.” — `#configuration-and-durability`
- `HALO-OPT-010` — “WHEN `setNumberOfRecords(numberOfRecords)` receives an estimate, the matching getter must return it and opening must size the off-heap index from that estimate.” — `#configuration-and-durability`
- `HALO-OPT-011` — “WHEN the estimate is too low for later growth, the database must preserve logical records while index rehash activity becomes visible through statistics.” — `#configuration-and-durability`
- `HALO-OPT-012` — “IF native index allocation fails, then the initiating open or write must fail rather than report an indexed record that is not retrievable.” — `#configuration-and-durability`
- `HALO-OPT-013` — “WHEN `setCompactionThresholdPerFile(compactionThresholdPerFile)` receives a fraction, the matching getter must return it and data files must become eligible for compaction when their stale-data fraction reaches that threshold.” — `#configuration-and-durability`
- `HALO-OPT-014` — “WHEN `setCompactionJobRate(compactionJobRate)` receives a byte rate, the matching getter must return it and background record copying must be rate-limited by that value.” — `#configuration-and-durability`
- `HALO-OPT-015` — “IF compaction I/O fails during a facade operation that waits on compaction, then that operation must raise `HaloDBException`.” — `#configuration-and-durability`
- `HALO-OPT-016` — “WHEN `setBuildIndexThreads(buildIndexThreads)` receives a value from 1 through `Runtime.getRuntime().availableProcessors()`, the matching getter must return it and open-time index scanning must use that worker count.” — `#configuration-and-durability`
- `HALO-OPT-017` — “IF the value is outside that range, then `setBuildIndexThreads` must raise `IllegalArgumentException`.” — `#configuration-and-durability`
- `HALO-OPT-018` — “WHEN `setCleanUpTombstonesDuringOpen(cleanUpTombstonesDuringOpen)` receives a boolean, the matching getter must return it and an enabled open must start cleanup of tombstones whose prior data versions have already been reclaimed.” — `#configuration-and-durability`
- `HALO-OPT-019` — “WHEN `setCleanUpInMemoryIndexOnClose(cleanUpInMemoryIndexOnClose)` receives a boolean, the matching getter must return it and an enabled close must release index allocations before returning.” — `#configuration-and-durability`
- `HALO-OPT-020` — “WHEN `setUseMemoryPool(useMemoryPool)` receives a boolean, the matching getter must return it and an enabled open must use pooled index allocation.” — `#configuration-and-durability`
- `HALO-OPT-021` — “WHEN `setFixedKeySize(fixedKeySize)` or `setMemoryPoolChunkSize(memoryPoolChunkSize)` receives a value, the matching getter must return it.” — `#configuration-and-durability`
- `HALO-OPT-022` — “WHERE memory pooling is enabled, `fixedKeySize` must be from 1 through 127 bytes, writes with longer keys must fail with `IllegalArgumentException`, and smaller keys must remain valid.” — `#configuration-and-durability`
- `HALO-OPT-023` — “IF memory pooling is enabled with an invalid fixed key size, then `HaloDB.open` must raise `IllegalArgumentException`.” — `#configuration-and-durability`
- `HALO-OPT-024` — “WHEN inserts and updates reach durable storage, their durable order must match call order.” — `#configuration-and-durability`
- `HALO-OPT-025` — “WHEN a power loss interrupts writes, each retained write must be atomic, while ordering between the insert/update stream and the delete stream is not required to be total.” — `#configuration-and-durability`
- `HALO-OPT-026` — “IF an incomplete or corrupt tail is encountered during the next open, then recovery must discard invalid records without inventing live keys.” — `#configuration-and-durability`
- `HALO-OPT-027` — “WHERE `flushDataSizeBytes` is `-1`, explicit size-triggered flushing must remain disabled.” — `#configuration-and-durability`
- `HALO-OPT-028` — “WHEN `enableSyncWrites(false)` is selected, `isSyncWrite()` must return `false` and durability must follow the configured flush threshold plus close-time flushing.” — `#configuration-and-durability`
- `HALO-OPT-029` — “The `setMaxFileSize` method must accept exactly one primitive `int` byte-count argument.” — `#configuration-and-durability`
- `HALO-OPT-030` — “The `setMaxFileSize` method must return `void`.” — `#configuration-and-durability`
- `HALO-OPT-031` — “The `getMaxFileSize()` method must return a primitive `int`.” — `#configuration-and-durability`
- `HALO-OPT-032` — “IF `setMaxFileSize` receives zero or a negative value, then `getMaxFileSize()` must retain its value from before the rejected call.” — `#configuration-and-durability`
- `HALO-OPT-033` — “The `setMaxTombstoneFileSize` method must accept exactly one primitive `int` byte-count argument.” — `#configuration-and-durability`
- `HALO-OPT-034` — “The `setMaxTombstoneFileSize` method must return `void`.” — `#configuration-and-durability`
- `HALO-OPT-035` — “The `getMaxTombstoneFileSize()` method must return a primitive `int`.” — `#configuration-and-durability`
- `HALO-OPT-036` — “IF `setMaxTombstoneFileSize` receives zero or a negative value, then `getMaxTombstoneFileSize()` must retain its value from before the rejected call.” — `#configuration-and-durability`
- `HALO-OPT-037` — “IF `setBuildIndexThreads` receives a value outside that range, then `getBuildIndexThreads()` must retain its value from before the rejected call.” — `#configuration-and-durability`
- `HALO-OPT-038` — “The `setFlushDataSizeBytes` method must accept exactly one primitive `long` byte-count argument.” — `#configuration-and-durability`
- `HALO-OPT-039` — “The `setFlushDataSizeBytes` method must return `void`.” — `#configuration-and-durability`
- `HALO-OPT-040` — “The `getFlushDataSizeBytes()` method must return a primitive `long`.” — `#configuration-and-durability`
- `HALO-OPT-041` — “The `enableSyncWrites` method must accept exactly one primitive `boolean` argument and return `void`.” — `#configuration-and-durability`
- `HALO-OPT-042` — “The `isSyncWrite()` method must return a primitive `boolean`.” — `#configuration-and-durability`
- `HALO-OPT-043` — “The `setNumberOfRecords` method must accept exactly one primitive `int` argument.” — `#configuration-and-durability`
- `HALO-OPT-044` — “The `setNumberOfRecords` method must return `void`.” — `#configuration-and-durability`
- `HALO-OPT-045` — “The `getNumberOfRecords()` method must return a primitive `int`.” — `#configuration-and-durability`
- `HALO-OPT-046` — “The `setCompactionThresholdPerFile` method must accept exactly one primitive `double` argument and return `void`.” — `#configuration-and-durability`
- `HALO-OPT-047` — “The `getCompactionThresholdPerFile()` method must return a primitive `double`.” — `#configuration-and-durability`
- `HALO-OPT-048` — “The `setCompactionJobRate` method must accept exactly one primitive `int` argument.” — `#configuration-and-durability`
- `HALO-OPT-049` — “The `setCompactionJobRate` method must return `void`.” — `#configuration-and-durability`
- `HALO-OPT-050` — “The `getCompactionJobRate()` method must return a primitive `int`.” — `#configuration-and-durability`
- `HALO-OPT-051` — “The `setBuildIndexThreads` method must accept exactly one primitive `int` argument and return `void`.” — `#configuration-and-durability`
- `HALO-OPT-052` — “The `getBuildIndexThreads()` method must return a primitive `int`.” — `#configuration-and-durability`
- `HALO-OPT-053` — “The `setCleanUpTombstonesDuringOpen` method must accept exactly one primitive `boolean` argument and return `void`.” — `#configuration-and-durability`
- `HALO-OPT-054` — “The `isCleanUpTombstonesDuringOpen()` method must return a primitive `boolean`.” — `#configuration-and-durability`
- `HALO-OPT-055` — “The `setCleanUpInMemoryIndexOnClose` and `setUseMemoryPool` methods must each accept exactly one primitive `boolean` argument and return `void`.” — `#configuration-and-durability`
- `HALO-OPT-056` — “The `isCleanUpInMemoryIndexOnClose()` and `isUseMemoryPool()` methods must each return a primitive `boolean`.” — `#configuration-and-durability`
- `HALO-OPT-057` — “The `setFixedKeySize` and `setMemoryPoolChunkSize` methods must each accept exactly one primitive `int` argument and return `void`.” — `#configuration-and-durability`
- `HALO-OPT-058` — “The `getFixedKeySize()` and `getMemoryPoolChunkSize()` methods must each return a primitive `int`.” — `#configuration-and-durability`

## Record Iteration

- `HALO-ITER-001` — “WHEN `newIterator()` is called on an open database, it must return a `HaloDBIterator` over live records.” — `#record-iteration`
- `HALO-ITER-002` — “IF iterator initialization cannot access the database files, then `newIterator()` must raise `HaloDBException`.” — `#record-iteration`
- `HALO-ITER-003` — “WHEN an iterator reaches a key with multiple persisted versions, it must return only the current version.” — `#record-iteration`
- `HALO-ITER-004` — “WHEN a key has a live tombstone, the iterator must omit that key.” — `#record-iteration`
- `HALO-ITER-005` — “The iterator must not promise key order, insertion order, or range order.” — `#record-iteration`
- `HALO-ITER-006` — “WHEN another live record is available, `hasNext()` must return `true` without consuming the record and `next()` must return it.” — `#record-iteration`
- `HALO-ITER-007` — “WHEN no live record remains, `hasNext()` must return `false`.” — `#record-iteration`
- `HALO-ITER-008` — “IF `next()` is called after exhaustion, then it must raise `NoSuchElementException`.” — `#record-iteration`
- `HALO-ITER-009` — “Each returned `Record` must expose its byte-array key through `getKey()` and its byte-array value through `getValue()`.” — `#record-iteration`
- `HALO-ITER-010` — “WHEN point lookup and iteration observe the same unchanged key, the record value must equal the point-lookup value.” — `#record-iteration`
- `HALO-ITER-011` — “The `hasNext()` method must return a primitive `boolean`.” — `#record-iteration`
- `HALO-ITER-012` — “The `next()` method must return a `Record`.” — `#record-iteration`
- `HALO-ITER-013` — “The `Record.getKey()` and `Record.getValue()` methods must each return a `byte[]`.” — `#record-iteration`

## Compaction and Tombstone Reclamation

- `HALO-COMP-001` — “WHEN updates or deletes make enough bytes stale in a data file, the background compaction worker must copy still-live records, remove the superseded file, and preserve every current point value.” — `#compaction-and-tombstone-reclamation`
- `HALO-COMP-002` — “WHEN stale history is reclaimed, logical `size()`, point lookup, and live-record iteration must remain unchanged.” — `#compaction-and-tombstone-reclamation`
- `HALO-COMP-003` — “WHEN `pauseCompaction()` is called, it must wait for an in-progress file compaction to finish and then keep background compaction paused.” — `#compaction-and-tombstone-reclamation`
- `HALO-COMP-004` — “WHEN `pauseCompaction()` is called repeatedly while paused, it must preserve the paused state.” — `#compaction-and-tombstone-reclamation`
- `HALO-COMP-005` — “IF pausing encounters I/O failure, then `pauseCompaction()` must raise `HaloDBException`.” — `#compaction-and-tombstone-reclamation`
- `HALO-COMP-006` — “WHEN `resumeCompaction()` is called, it must allow background compaction to continue.” — `#compaction-and-tombstone-reclamation`
- `HALO-COMP-007` — “WHEN a key is deleted, its tombstone must keep the deletion effective across close and reopen until prior data versions no longer require it.” — `#compaction-and-tombstone-reclamation`
- `HALO-COMP-008` — “WHERE `cleanUpTombstonesDuringOpen` is enabled, open-time cleanup must remove only tombstones whose earlier data versions have already been reclaimed.” — `#compaction-and-tombstone-reclamation`
- `HALO-COMP-009` — “IF cleanup cannot safely establish that condition, then the tombstone must remain effective rather than restore a deleted key.” — `#compaction-and-tombstone-reclamation`
- `HALO-COMP-010` — “WHEN `resumeCompaction()` is called repeatedly while running, it must preserve the running state.” — `#compaction-and-tombstone-reclamation`
- `HALO-COMP-011` — “The `pauseCompaction()` and `resumeCompaction()` methods must each return `void`.” — `#compaction-and-tombstone-reclamation`

## Statistics and Operational Views

- `HALO-STAT-001` — “WHEN `stats()` is called, it must return a `HaloDBStats` snapshot whose `getSize()` equals `HaloDB.size()` at collection time and whose `getOptions()` returns a clone of the active options.” — `#statistics-and-operational-views`
- `HALO-STAT-002` — “The snapshot must remain readable without mutating database state.” — `#statistics-and-operational-views`
- `HALO-STAT-003` — “`getNumberOfDataFiles()` and `getNumberOfTombstoneFiles()` must return current file counts.” — `#statistics-and-operational-views`
- `HALO-STAT-004` — “`getStaleDataPercentPerFile()` must map data-file identifiers with stale bytes to their stale percentages.” — `#statistics-and-operational-views`
- `HALO-STAT-005` — “`getNumberOfRecordsCopied()`, `getNumberOfRecordsReplaced()`, `getNumberOfRecordsScanned()`, `getSizeOfRecordsCopied()`, `getSizeOfFilesDeleted()`, and `getSizeReclaimed()` must report compaction activity since the latest statistics reset.” — `#statistics-and-operational-views`
- `HALO-STAT-006` — “`getRehashCount()` must return rehash activity since the latest statistics reset.” — `#statistics-and-operational-views`
- `HALO-STAT-007` — “`getNumberOfSegments()` must return the off-heap index segment count, and `getMaxSizePerSegment()` must return the configured capacity of one segment.” — `#statistics-and-operational-views`
- `HALO-STAT-008` — “IF an index metric is unavailable because database initialization failed, then no `HaloDBStats` snapshot must be returned from that failed open.” — `#statistics-and-operational-views`
- `HALO-STAT-009` — “`getNumberOfTombstonesFoundDuringOpen()` must report tombstones observed while rebuilding the database.” — `#statistics-and-operational-views`
- `HALO-STAT-010` — “WHERE tombstone cleanup is enabled, `getNumberOfTombstonesCleanedUpDuringOpen()` must report the subset removed as obsolete.” — `#statistics-and-operational-views`
- `HALO-STAT-011` — “`getCompactionRateInInternal()` must return bytes copied per second since the latest statistics reset.” — `#statistics-and-operational-views`
- `HALO-STAT-012` — “WHEN `resetStats()` is called, interval index and compaction counters must reset while logical size, physical file counts, active options, and the long-lived compaction rate remain projections of the same database.” — `#statistics-and-operational-views`
- `HALO-STAT-013` — “`toString()` must return a nonempty human-readable summary without defining exact formatting.” — `#statistics-and-operational-views`
- `HALO-STAT-014` — “`getNumberOfFilesPendingCompaction()` must return the current pending-file count.” — `#statistics-and-operational-views`
- `HALO-STAT-015` — “`isCompactionRunning()` must report the worker state.” — `#statistics-and-operational-views`
- `HALO-STAT-016` — “WHERE tombstone cleanup is disabled, `getNumberOfTombstonesCleanedUpDuringOpen()` must return zero.” — `#statistics-and-operational-views`
- `HALO-STAT-017` — “`getCompactionRateSinceBeginning()` must return the long-lived compaction rate.” — `#statistics-and-operational-views`
- `HALO-STAT-018` — “The `stats()` method must return a `HaloDBStats`.” — `#statistics-and-operational-views`
- `HALO-STAT-019` — “The `resetStats()` method must return `void`.” — `#statistics-and-operational-views`
- `HALO-STAT-020` — “The `HaloDBStats.getSize()` method must return a primitive `long`.” — `#statistics-and-operational-views`
- `HALO-STAT-021` — “The `HaloDBStats.getOptions()` method must return a `HaloDBOptions`.” — `#statistics-and-operational-views`
- `HALO-STAT-022` — “The `getNumberOfDataFiles()`, `getNumberOfTombstoneFiles()`, and `getNumberOfFilesPendingCompaction()` methods must each return a primitive `int`.” — `#statistics-and-operational-views`
- `HALO-STAT-023` — “The `isCompactionRunning()` method must return a primitive `boolean`.” — `#statistics-and-operational-views`
- `HALO-STAT-024` — “The `getStaleDataPercentPerFile()` method must return a `Map` from boxed `Integer` file identifiers to boxed `Double` percentages.” — `#statistics-and-operational-views`
- `HALO-STAT-025` — “The `getNumberOfRecordsCopied()`, `getNumberOfRecordsReplaced()`, `getNumberOfRecordsScanned()`, `getSizeOfRecordsCopied()`, `getSizeOfFilesDeleted()`, and `getSizeReclaimed()` methods must each return a primitive `long`.” — `#statistics-and-operational-views`
- `HALO-STAT-026` — “The `getRehashCount()`, `getNumberOfSegments()`, and `getMaxSizePerSegment()` methods must each return a primitive `long`.” — `#statistics-and-operational-views`
- `HALO-STAT-027` — “The `getNumberOfTombstonesFoundDuringOpen()` and `getNumberOfTombstonesCleanedUpDuringOpen()` methods must each return a primitive `long`.” — `#statistics-and-operational-views`
- `HALO-STAT-028` — “The `getCompactionRateInInternal()` and `getCompactionRateSinceBeginning()` methods must each return a primitive `long`.” — `#statistics-and-operational-views`
- `HALO-STAT-029` — “The `HaloDBStats.toString()` method must return a `String`.” — `#statistics-and-operational-views`

## State Model

- `HALO-STATE-001` — “The live mapping must determine point reads, size, and iterator membership.” — `#state-model`
- `HALO-STATE-002` — “The durable record and tombstone history must reconstruct the same live mapping after a clean close and reopen.” — `#state-model`
- `HALO-STATE-003` — “The active options must govern newly created physical files, flushing, index sizing, startup work, and compaction without changing the meaning of stored keys and values.” — `#state-model`
- `HALO-STATE-004` — “The compaction state must change physical history and operational counters without changing the live mapping.” — `#state-model`
- `HALO-STATE-005` — “The statistics state must project current logical and physical state plus resettable activity counters without becoming an independent source of database truth.” — `#state-model`

## Error Semantics

- `HALO-ERR-001` — “IF such an I/O failure reaches the public facade, then the operation must raise `HaloDBException`.” — `#error-semantics`
- `HALO-ERR-002` — “WHILE a directory lock is held, a second `HaloDB.open` must raise `HaloDBException`.” — `#error-semantics`
- `HALO-ERR-003` — “IF persisted metadata contains a different maximum data-file size, then `HaloDB.open` must raise `IllegalArgumentException`.” — `#error-semantics`
- `HALO-ERR-004` — “IF `put` receives a key longer than 127 bytes, then it must raise `HaloDBException`.” — `#error-semantics`
- `HALO-ERR-005` — “WHERE memory pooling is enabled and a write key exceeds `fixedKeySize`, the write must raise `IllegalArgumentException`.” — `#error-semantics`
- `HALO-ERR-006` — “IF either file-size setter receives zero or a negative value, then it must raise `IllegalArgumentException`.” — `#error-semantics`
- `HALO-ERR-007` — “IF `buildIndexThreads` is below 1 or above the available processor count, then its setter must raise `IllegalArgumentException`.” — `#error-semantics`
- `HALO-ERR-008` — “WHERE memory pooling is enabled and `fixedKeySize` is outside 1 through 127, `HaloDB.open` must raise `IllegalArgumentException`.” — `#error-semantics`
- `HALO-ERR-009` — “WHEN `get` addresses an absent or deleted key, it must return `null`.” — `#error-semantics`
- `HALO-ERR-010` — “IF `next()` is called after iterator exhaustion, then it must raise `NoSuchElementException`.” — `#error-semantics`

## Cross-View Invariants

- `HALO-INV-001` — “WHEN `put` succeeds for a new key, `get` must return its value, `size()` must include the key, a new iterator must contain one matching `Record`, and `stats().getSize()` must match `size()`.” — `#cross-view-invariants`
- `HALO-INV-002` — “WHEN `put` succeeds for an existing key, point lookup and a new iterator must expose only the latest value while `size()` and `stats().getSize()` remain unchanged.” — `#cross-view-invariants`
- `HALO-INV-003` — “WHEN a live key is deleted, point lookup must return `null`, a new iterator must omit the key, `size()` must exclude it, and the tombstone file count must reflect persisted deletion history when a tombstone file exists.” — `#cross-view-invariants`
- `HALO-INV-004` — “WHEN a database closes cleanly and reopens with compatible options, point values, deleted-key absence, iterator membership, and live size must match the state before close.” — `#cross-view-invariants`
- `HALO-INV-005` — “WHEN compaction reclaims stale data, point lookup, live size, iterator membership, and reopen results must preserve the same live mapping while compaction and file metrics reflect the physical work.” — `#cross-view-invariants`
- `HALO-INV-006` — “WHEN tombstone cleanup removes obsolete tombstones during open, deleted keys must remain absent from point lookup and iteration while open-time cleanup metrics report the removal.” — `#cross-view-invariants`
- `HALO-INV-007` — “WHEN compaction is paused or resumed, the worker-state projection must change accordingly while point operations, iterator membership, and live size remain unaffected.” — `#cross-view-invariants`
- `HALO-INV-008` — “WHEN statistics reset, resettable activity metrics must restart from zero while `HaloDB.size()`, `HaloDBStats.getSize()`, active option getters, and current file counts remain consistent.” — `#cross-view-invariants`
- `HALO-INV-009` — “WHERE synchronous writes are enabled, successful write and delete calls must establish the same live mapping observed before close and after reopen, without relying on the size-triggered flush threshold.” — `#cross-view-invariants`

## Environment

- `HALO-ENV-001` — “The project must declare Maven metadata in `pom.xml` at the project root, use coordinates `com.oath.halodb:halodb:0.5.6`, produce JAR packaging, target Java 8 bytecode, and declare every runtime dependency used by the implementation.” — `#appendix-a-environment`
- `HALO-ENV-002` — “Maven resolution must succeed entirely from the offline repository.” — `#appendix-a-environment`
