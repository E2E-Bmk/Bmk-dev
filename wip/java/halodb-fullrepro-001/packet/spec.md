# halodb Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`halodb` is an embedded Java key-value storage library that persists byte-array keys and values in a local directory. It combines point operations with live-record iteration, operational statistics, restart recovery, and background reclamation of stale data.

The library is distributed as a Maven JAR. The storage model uses append-only local files and an off-heap latest-key index, so reads resolve one current value while updates and deletes leave reclaimable history for compaction.

## Non-Goals

- This specification does not require ordered access, range scans, prefix scans, or comparator-based traversal.
- This specification does not require database snapshot management or key-only iteration.
- This specification does not require public access to internal files, index carriers, memory allocators, histogram utilities, segment statistics carriers, or compaction implementation types.
- This specification does not define exact log messages, exception-message text, stack traces, object representation formatting, or statistics-map string keys.
- This specification does not require a performance-comparison executable, a command-line application, a network service, or an external storage service.
- This specification does not define multi-process write sharing; one database directory has one active owner.

## Representative Workflows

### Configure, write, read, iterate, and inspect

```java
import com.oath.halodb.HaloDB;
import com.oath.halodb.HaloDBIterator;
import com.oath.halodb.HaloDBOptions;
import com.oath.halodb.Record;

HaloDBOptions options = new HaloDBOptions();
options.setMaxFileSize(64 * 1024 * 1024);
options.setCompactionThresholdPerFile(0.70);
options.setFlushDataSizeBytes(8 * 1024 * 1024);

HaloDB db = HaloDB.open("data/catalog", options);
byte[] key = new byte[] {1, 2, 3};
byte[] value = new byte[] {9, 8, 7};
db.put(key, value);
byte[] loaded = db.get(key);

HaloDBIterator records = db.newIterator();
while (records.hasNext()) {
    Record record = records.next();
    System.out.println(record.getKey().length + ":" + record.getValue().length);
}
System.out.println(db.stats());
db.close();
```

WHEN the write succeeds, the point lookup, iterator record, live-record count, and statistics size must describe the same key-value state.

### Delete, close, and reopen

```java
import com.oath.halodb.HaloDB;
import com.oath.halodb.HaloDBOptions;

HaloDBOptions options = new HaloDBOptions();
options.setCleanUpTombstonesDuringOpen(true);

HaloDB first = HaloDB.open("data/catalog", options);
first.put(new byte[] {4}, new byte[] {40});
first.put(new byte[] {5}, new byte[] {50});
first.delete(new byte[] {4});
first.close();

HaloDB reopened = HaloDB.open("data/catalog", options);
byte[] deleted = reopened.get(new byte[] {4});
byte[] retained = reopened.get(new byte[] {5});
reopened.close();
```

WHEN a cleanly closed directory is reopened, the latest updates and recorded deletions must remain visible through point lookup, iteration, and size.

## Database Ownership and Lifecycle

This section defines how one directory becomes an active database and how its durable state crosses process lifecycles.

**Opening a directory.** A caller must open a database with `HaloDB.open`, supplying either a `String` directory path or a `File` plus a `HaloDBOptions` instance. The two `HaloDB.open` overloads must each return a `HaloDB` instance. The `HaloDBException` type must be a checked subclass of `Exception`. The `HaloDB.open`, `get`, `put`, `delete`, `close`, `newIterator`, and `pauseCompaction` methods must be the only methods in the Public Interface that declare a checked exception, and each must declare `HaloDBException`. WHEN the directory does not exist, `HaloDB.open` must create it and initialize an empty database. WHEN the directory already contains a compatible database, `HaloDB.open` must rebuild the latest-key view and resume from the persisted records and tombstones. IF the directory cannot be created, read, locked, or initialized, then `HaloDB.open` must raise `HaloDBException`.

**Exclusive ownership.** WHILE one open `HaloDB` instance owns a directory, another `HaloDB.open` for the same directory must raise `HaloDBException`. WHEN the owning instance closes or an unsuccessful open releases its partial ownership, a later open must acquire the directory normally.

**Recovery.** WHEN metadata indicates an unclean shutdown or an I/O failure, `HaloDB.open` must repair incomplete writable tails, discard corrupt records that do not validate, and rebuild the live-key projection from valid persisted records. IF the stored maximum data-file size differs from `HaloDBOptions.getMaxFileSize()`, then `HaloDB.open` must raise `IllegalArgumentException` rather than reinterpret existing files.

**Closing.** The `close()` method must return `void`. WHEN `close()` is called, the database must stop background work, flush current data, index, and tombstone writes, release file resources and the directory lock, and mark the directory cleanly closed. WHEN `close()` is called again after closing has started, it must return without repeating state changes. IF flushing or closing a resource fails, then `close()` must raise `HaloDBException`.

## Key-Value State and Point Operations

This section defines the live byte-array mapping exposed by point reads, writes, deletes, and the record count.

**Writes and updates.** The `put` method must accept exactly two `byte[]` arguments and return a primitive `boolean`. WHEN `put(key, value)` receives a key no longer than 127 bytes and a byte-array value, it must persist the pair, make that value the current value for the key, and return whether the in-memory index accepted the update. WHEN the key already exists, `put` must replace the live value without increasing `size()`. IF `key` is longer than 127 bytes, then `put` must raise `HaloDBException`.

**Point reads.** The `get` method must accept exactly one `byte[]` key and return a `byte[]` value or `null`. WHEN `get(key)` addresses a live key, it must return the current byte-array value. WHEN `get(key)` addresses a key that was never written or has been deleted, it must return `null`. IF a read cannot complete after bounded retries around concurrent file replacement, then `get` must raise `HaloDBException`.

**Deletes.** The `delete` method must accept exactly one `byte[]` key and return `void`. WHEN `delete(key)` addresses a live key, it must remove the key from the live mapping and persist a tombstone. WHEN `delete(key)` addresses an absent key, it must return without changing the database. IF the tombstone write fails, then `delete` must raise `HaloDBException`.

**Live count.** The `size()` method must return a primitive `long`. The `size()` method must return the number of distinct live keys. WHEN an existing key is updated, `size()` must remain unchanged. WHEN a live key is deleted, `size()` must decrease once. WHEN an absent key is deleted, `size()` must remain unchanged.

## Configuration and Durability

This section defines configuration defaults, validation boundaries, and the persistence trade-offs applied by database operations.

**Default configuration.** A new `HaloDBOptions` must default `compactionThresholdPerFile` to `0.75`, `maxFileSize` to 1 MiB, `flushDataSizeBytes` to `-1`, `numberOfRecords` to 1,000,000, `compactionJobRate` to 1 GiB per second, `cleanUpInMemoryIndexOnClose` to `false`, `cleanUpTombstonesDuringOpen` to `false`, `useMemoryPool` to `false`, `fixedKeySize` to 127 bytes, `memoryPoolChunkSize` to 16 MiB, `syncWrite` to `false`, and `buildIndexThreads` to `1`. WHEN `maxTombstoneFileSize` has not been set, `getMaxTombstoneFileSize()` must return the current `maxFileSize`.

**File sizing.** The `setMaxFileSize` method must accept exactly one primitive `int` byte-count argument. The `setMaxFileSize` method must return `void`. The `getMaxFileSize()` method must return a primitive `int`. WHEN `setMaxFileSize(maxFileSize)` receives a positive byte count, the matching getter must return it and newly rolled data files must use it as their target maximum. IF `maxFileSize` is zero or negative, then `setMaxFileSize` must raise `IllegalArgumentException`. IF `setMaxFileSize` receives zero or a negative value, then `getMaxFileSize()` must retain its value from before the rejected call. The `setMaxTombstoneFileSize` method must accept exactly one primitive `int` byte-count argument. The `setMaxTombstoneFileSize` method must return `void`. The `getMaxTombstoneFileSize()` method must return a primitive `int`. WHEN `setMaxTombstoneFileSize(maxFileSize)` receives a positive byte count, the matching getter must return it and tombstone rollover must use it. IF that byte count is zero or negative, then `setMaxTombstoneFileSize` must raise `IllegalArgumentException`. IF `setMaxTombstoneFileSize` receives zero or a negative value, then `getMaxTombstoneFileSize()` must retain its value from before the rejected call.

**Flush policy.** The `setFlushDataSizeBytes` method must accept exactly one primitive `long` byte-count argument. The `setFlushDataSizeBytes` method must return `void`. The `getFlushDataSizeBytes()` method must return a primitive `long`. The `enableSyncWrites` method must accept exactly one primitive `boolean` argument and return `void`. The `isSyncWrite()` method must return a primitive `boolean`. WHEN `setFlushDataSizeBytes(flushDataSizeBytes)` receives a value, the matching getter must return it. WHERE `flushDataSizeBytes` is positive, accumulated writes must be forced to disk after that many bytes. WHERE `flushDataSizeBytes` is `-1`, explicit size-triggered flushing must remain disabled. WHEN `enableSyncWrites(true)` is selected, each write and delete must be forced to disk before its call returns. WHEN `enableSyncWrites(false)` is selected, `isSyncWrite()` must return `false` and durability must follow the configured flush threshold plus close-time flushing.

**Capacity planning.** The `setNumberOfRecords` method must accept exactly one primitive `int` argument. The `setNumberOfRecords` method must return `void`. The `getNumberOfRecords()` method must return a primitive `int`. WHEN `setNumberOfRecords(numberOfRecords)` receives an estimate, the matching getter must return it and opening must size the off-heap index from that estimate. WHEN the estimate is too low for later growth, the database must preserve logical records while index rehash activity becomes visible through statistics. IF native index allocation fails, then the initiating open or write must fail rather than report an indexed record that is not retrievable.

**Compaction controls.** The `setCompactionThresholdPerFile` method must accept exactly one primitive `double` argument and return `void`. The `getCompactionThresholdPerFile()` method must return a primitive `double`. The `setCompactionJobRate` method must accept exactly one primitive `int` argument. The `setCompactionJobRate` method must return `void`. The `getCompactionJobRate()` method must return a primitive `int`. WHEN `setCompactionThresholdPerFile(compactionThresholdPerFile)` receives a fraction, the matching getter must return it and data files must become eligible for compaction when their stale-data fraction reaches that threshold. WHEN `setCompactionJobRate(compactionJobRate)` receives a byte rate, the matching getter must return it and background record copying must be rate-limited by that value. IF compaction I/O fails during a facade operation that waits on compaction, then that operation must raise `HaloDBException`.

**Startup work.** The `setBuildIndexThreads` method must accept exactly one primitive `int` argument and return `void`. The `getBuildIndexThreads()` method must return a primitive `int`. The `setCleanUpTombstonesDuringOpen` method must accept exactly one primitive `boolean` argument and return `void`. The `isCleanUpTombstonesDuringOpen()` method must return a primitive `boolean`. WHEN `setBuildIndexThreads(buildIndexThreads)` receives a value from 1 through `Runtime.getRuntime().availableProcessors()`, the matching getter must return it and open-time index scanning must use that worker count. IF the value is outside that range, then `setBuildIndexThreads` must raise `IllegalArgumentException`. IF `setBuildIndexThreads` receives a value outside that range, then `getBuildIndexThreads()` must retain its value from before the rejected call. WHEN `setCleanUpTombstonesDuringOpen(cleanUpTombstonesDuringOpen)` receives a boolean, the matching getter must return it and an enabled open must start cleanup of tombstones whose prior data versions have already been reclaimed.

**Native-memory modes.** The `setCleanUpInMemoryIndexOnClose` and `setUseMemoryPool` methods must each accept exactly one primitive `boolean` argument and return `void`. The `isCleanUpInMemoryIndexOnClose()` and `isUseMemoryPool()` methods must each return a primitive `boolean`. The `setFixedKeySize` and `setMemoryPoolChunkSize` methods must each accept exactly one primitive `int` argument and return `void`. The `getFixedKeySize()` and `getMemoryPoolChunkSize()` methods must each return a primitive `int`. WHEN `setCleanUpInMemoryIndexOnClose(cleanUpInMemoryIndexOnClose)` receives a boolean, the matching getter must return it and an enabled close must release index allocations before returning. WHEN `setUseMemoryPool(useMemoryPool)` receives a boolean, the matching getter must return it and an enabled open must use pooled index allocation. WHEN `setFixedKeySize(fixedKeySize)` or `setMemoryPoolChunkSize(memoryPoolChunkSize)` receives a value, the matching getter must return it. WHERE memory pooling is enabled, `fixedKeySize` must be from 1 through 127 bytes, writes with longer keys must fail with `IllegalArgumentException`, and smaller keys must remain valid. IF memory pooling is enabled with an invalid fixed key size, then `HaloDB.open` must raise `IllegalArgumentException`.

**Crash durability.** WHEN inserts and updates reach durable storage, their durable order must match call order. WHEN a power loss interrupts writes, each retained write must be atomic, while ordering between the insert/update stream and the delete stream is not required to be total. IF an incomplete or corrupt tail is encountered during the next open, then recovery must discard invalid records without inventing live keys.

## Record Iteration

This section defines the unordered live-record view and the value objects returned from it.

**Iterator creation.** WHEN `newIterator()` is called on an open database, it must return a `HaloDBIterator` over live records. IF iterator initialization cannot access the database files, then `newIterator()` must raise `HaloDBException`.

**Live-record projection.** WHEN an iterator reaches a key with multiple persisted versions, it must return only the current version. WHEN a key has a live tombstone, the iterator must omit that key. The iterator must not promise key order, insertion order, or range order.

**Iterator protocol.** The `hasNext()` method must return a primitive `boolean`. The `next()` method must return a `Record`. WHEN another live record is available, `hasNext()` must return `true` without consuming the record and `next()` must return it. WHEN no live record remains, `hasNext()` must return `false`. IF `next()` is called after exhaustion, then it must raise `NoSuchElementException`.

**Record view.** The `Record.getKey()` and `Record.getValue()` methods must each return a `byte[]`. Each returned `Record` must expose its byte-array key through `getKey()` and its byte-array value through `getValue()`. WHEN point lookup and iteration observe the same unchanged key, the record value must equal the point-lookup value.

## Compaction and Tombstone Reclamation

This section defines how stale physical history is reclaimed without changing the live mapping.

**Background reclamation.** WHEN updates or deletes make enough bytes stale in a data file, the background compaction worker must copy still-live records, remove the superseded file, and preserve every current point value. WHEN stale history is reclaimed, logical `size()`, point lookup, and live-record iteration must remain unchanged.

**Pause and resume.** The `pauseCompaction()` and `resumeCompaction()` methods must each return `void`. WHEN `pauseCompaction()` is called, it must wait for an in-progress file compaction to finish and then keep background compaction paused. WHEN `pauseCompaction()` is called repeatedly while paused, it must preserve the paused state. IF pausing encounters I/O failure, then `pauseCompaction()` must raise `HaloDBException`. WHEN `resumeCompaction()` is called, it must allow background compaction to continue. WHEN `resumeCompaction()` is called repeatedly while running, it must preserve the running state.

**Tombstone lifecycle.** WHEN a key is deleted, its tombstone must keep the deletion effective across close and reopen until prior data versions no longer require it. WHERE `cleanUpTombstonesDuringOpen` is enabled, open-time cleanup must remove only tombstones whose earlier data versions have already been reclaimed. IF cleanup cannot safely establish that condition, then the tombstone must remain effective rather than restore a deleted key.

## Statistics and Operational Views

This section defines the public statistics snapshot used to relate logical state, physical files, index capacity, and reclamation work.

**Snapshot semantics.** The `stats()` method must return a `HaloDBStats`. The `resetStats()` method must return `void`. The `HaloDBStats.getSize()` method must return a primitive `long`. The `HaloDBStats.getOptions()` method must return a `HaloDBOptions`. WHEN `stats()` is called, it must return a `HaloDBStats` snapshot whose `getSize()` equals `HaloDB.size()` at collection time and whose `getOptions()` returns a clone of the active options. The snapshot must remain readable without mutating database state.

**Physical and compaction metrics.** The `getNumberOfDataFiles()`, `getNumberOfTombstoneFiles()`, and `getNumberOfFilesPendingCompaction()` methods must each return a primitive `int`. The `isCompactionRunning()` method must return a primitive `boolean`. The `getStaleDataPercentPerFile()` method must return a `Map` from boxed `Integer` file identifiers to boxed `Double` percentages. The `getNumberOfRecordsCopied()`, `getNumberOfRecordsReplaced()`, `getNumberOfRecordsScanned()`, `getSizeOfRecordsCopied()`, `getSizeOfFilesDeleted()`, and `getSizeReclaimed()` methods must each return a primitive `long`. `getNumberOfDataFiles()` and `getNumberOfTombstoneFiles()` must return current file counts. `getNumberOfFilesPendingCompaction()` must return the current pending-file count. `isCompactionRunning()` must report the worker state. `getStaleDataPercentPerFile()` must map data-file identifiers with stale bytes to their stale percentages. `getNumberOfRecordsCopied()`, `getNumberOfRecordsReplaced()`, `getNumberOfRecordsScanned()`, `getSizeOfRecordsCopied()`, `getSizeOfFilesDeleted()`, and `getSizeReclaimed()` must report compaction activity since the latest statistics reset.

**Index metrics.** The `getRehashCount()`, `getNumberOfSegments()`, and `getMaxSizePerSegment()` methods must each return a primitive `long`. `getRehashCount()` must return rehash activity since the latest statistics reset. `getNumberOfSegments()` must return the off-heap index segment count, and `getMaxSizePerSegment()` must return the configured capacity of one segment. IF an index metric is unavailable because database initialization failed, then no `HaloDBStats` snapshot must be returned from that failed open.

**Open-time metrics.** The `getNumberOfTombstonesFoundDuringOpen()` and `getNumberOfTombstonesCleanedUpDuringOpen()` methods must each return a primitive `long`. `getNumberOfTombstonesFoundDuringOpen()` must report tombstones observed while rebuilding the database. WHERE tombstone cleanup is enabled, `getNumberOfTombstonesCleanedUpDuringOpen()` must report the subset removed as obsolete. WHERE tombstone cleanup is disabled, `getNumberOfTombstonesCleanedUpDuringOpen()` must return zero.

**Rate metrics and reset.** The `getCompactionRateInInternal()` and `getCompactionRateSinceBeginning()` methods must each return a primitive `long`. The `HaloDBStats.toString()` method must return a `String`. `getCompactionRateInInternal()` must return bytes copied per second since the latest statistics reset. `getCompactionRateSinceBeginning()` must return the long-lived compaction rate. WHEN `resetStats()` is called, interval index and compaction counters must reset while logical size, physical file counts, active options, and the long-lived compaction rate remain projections of the same database. `toString()` must return a nonempty human-readable summary without defining exact formatting.

## State Model

The core state is a directory-owned mapping from byte-array keys to their latest live byte-array values, plus append-only record history, deletion tombstones, an off-heap latest-key index, background compaction state, and operational counters. Its public projections are point operations, `size()`, record iteration, `HaloDBStats`, active options, and close/reopen persistence.

1. The live mapping must determine point reads, size, and iterator membership.
2. The durable record and tombstone history must reconstruct the same live mapping after a clean close and reopen.
3. The active options must govern newly created physical files, flushing, index sizing, startup work, and compaction without changing the meaning of stored keys and values.
4. The compaction state must change physical history and operational counters without changing the live mapping.
5. The statistics state must project current logical and physical state plus resettable activity counters without becoming an independent source of database truth.

## Error Semantics

The following failures form the public error contract.

| Condition | Required result |
|---|---|
| Directory creation, locking, initialization, read, write, delete, close, or facade-level compaction I/O failure | IF such an I/O failure reaches the public facade, then the operation must raise `HaloDBException`. |
| A second owner opens an active directory | WHILE a directory lock is held, a second `HaloDB.open` must raise `HaloDBException`. |
| Data-file size changes across reopen | IF persisted metadata contains a different maximum data-file size, then `HaloDB.open` must raise `IllegalArgumentException`. |
| Key exceeds the global limit | IF `put` receives a key longer than 127 bytes, then it must raise `HaloDBException`. |
| Memory-pool key exceeds `fixedKeySize` | WHERE memory pooling is enabled and a write key exceeds `fixedKeySize`, the write must raise `IllegalArgumentException`. |
| Invalid positive-only file size | IF either file-size setter receives zero or a negative value, then it must raise `IllegalArgumentException`. |
| Invalid index-build worker count | IF `buildIndexThreads` is below 1 or above the available processor count, then its setter must raise `IllegalArgumentException`. |
| Invalid pooled fixed-key size | WHERE memory pooling is enabled and `fixedKeySize` is outside 1 through 127, `HaloDB.open` must raise `IllegalArgumentException`. |
| Missing point key | WHEN `get` addresses an absent or deleted key, it must return `null`. |
| Exhausted record iterator | IF `next()` is called after iterator exhaustion, then it must raise `NoSuchElementException`. |

## Cross-View Invariants

1. WHEN `put` succeeds for a new key, `get` must return its value, `size()` must include the key, a new iterator must contain one matching `Record`, and `stats().getSize()` must match `size()`.
2. WHEN `put` succeeds for an existing key, point lookup and a new iterator must expose only the latest value while `size()` and `stats().getSize()` remain unchanged.
3. WHEN a live key is deleted, point lookup must return `null`, a new iterator must omit the key, `size()` must exclude it, and the tombstone file count must reflect persisted deletion history when a tombstone file exists.
4. WHEN a database closes cleanly and reopens with compatible options, point values, deleted-key absence, iterator membership, and live size must match the state before close.
5. WHEN compaction reclaims stale data, point lookup, live size, iterator membership, and reopen results must preserve the same live mapping while compaction and file metrics reflect the physical work.
6. WHEN tombstone cleanup removes obsolete tombstones during open, deleted keys must remain absent from point lookup and iteration while open-time cleanup metrics report the removal.
7. WHEN compaction is paused or resumed, the worker-state projection must change accordingly while point operations, iterator membership, and live size remain unaffected.
8. WHEN statistics reset, resettable activity metrics must restart from zero while `HaloDB.size()`, `HaloDBStats.getSize()`, active option getters, and current file counts remain consistent.
9. WHERE synchronous writes are enabled, successful write and delete calls must establish the same live mapping observed before close and after reopen, without relying on the size-triggered flush threshold.

## Public Interface

### Import Surface

```java
import com.oath.halodb.HaloDB;
import com.oath.halodb.HaloDBException;
import com.oath.halodb.HaloDBIterator;
import com.oath.halodb.HaloDBOptions;
import com.oath.halodb.HaloDBStats;
import com.oath.halodb.Record;
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `HaloDB` | class | Owns one directory-backed database instance. |
| `HaloDB.open` | static method | Opens a database from a `String` path or `File`. |
| `HaloDB.get` | method | Reads the current value for a byte-array key. |
| `HaloDB.put` | method | Inserts or updates a byte-array key-value pair. |
| `HaloDB.delete` | method | Removes a live key and persists deletion history. |
| `HaloDB.close` | method | Flushes and releases the database. |
| `HaloDB.size` | method | Reports the live-key count. |
| `HaloDB.stats` | method | Captures operational statistics. |
| `HaloDB.resetStats` | method | Resets interval activity counters. |
| `HaloDB.newIterator` | method | Creates an unordered live-record iterator. |
| `HaloDB.pauseCompaction` | method | Pauses background compaction after current work. |
| `HaloDB.resumeCompaction` | method | Resumes background compaction. |
| `HaloDBOptions` | class | Holds database configuration. |
| `HaloDBOptions.HaloDBOptions` | constructor | Creates the default configuration. |
| `HaloDBOptions.setCompactionThresholdPerFile` | method | Sets the per-file stale-data threshold. |
| `HaloDBOptions.getCompactionThresholdPerFile` | method | Returns the per-file stale-data threshold. |
| `HaloDBOptions.setMaxFileSize` | method | Sets the target maximum data-file size. |
| `HaloDBOptions.getMaxFileSize` | method | Returns the target maximum data-file size. |
| `HaloDBOptions.setMaxTombstoneFileSize` | method | Sets the target maximum tombstone-file size. |
| `HaloDBOptions.getMaxTombstoneFileSize` | method | Returns the effective tombstone-file size. |
| `HaloDBOptions.setFlushDataSizeBytes` | method | Sets the size-triggered flush threshold. |
| `HaloDBOptions.getFlushDataSizeBytes` | method | Returns the size-triggered flush threshold. |
| `HaloDBOptions.setNumberOfRecords` | method | Sets the expected live-record count for index sizing. |
| `HaloDBOptions.getNumberOfRecords` | method | Returns the expected live-record count. |
| `HaloDBOptions.setCompactionJobRate` | method | Sets the compaction copy rate. |
| `HaloDBOptions.getCompactionJobRate` | method | Returns the compaction copy rate. |
| `HaloDBOptions.setCleanUpInMemoryIndexOnClose` | method | Configures native index release during close. |
| `HaloDBOptions.isCleanUpInMemoryIndexOnClose` | method | Reports native index release configuration. |
| `HaloDBOptions.setCleanUpTombstonesDuringOpen` | method | Configures obsolete tombstone cleanup during open. |
| `HaloDBOptions.isCleanUpTombstonesDuringOpen` | method | Reports open-time tombstone cleanup configuration. |
| `HaloDBOptions.setUseMemoryPool` | method | Selects pooled index allocation. |
| `HaloDBOptions.isUseMemoryPool` | method | Reports pooled index allocation selection. |
| `HaloDBOptions.setFixedKeySize` | method | Sets the pooled-index key-size ceiling. |
| `HaloDBOptions.getFixedKeySize` | method | Returns the pooled-index key-size ceiling. |
| `HaloDBOptions.setMemoryPoolChunkSize` | method | Sets the pooled-index chunk size. |
| `HaloDBOptions.getMemoryPoolChunkSize` | method | Returns the pooled-index chunk size. |
| `HaloDBOptions.enableSyncWrites` | method | Selects force-to-disk write completion. |
| `HaloDBOptions.isSyncWrite` | method | Reports synchronous-write selection. |
| `HaloDBOptions.setBuildIndexThreads` | method | Sets open-time index scanning workers. |
| `HaloDBOptions.getBuildIndexThreads` | method | Returns open-time index scanning workers. |
| `HaloDBIterator` | class | Iterates live key-value records. |
| `HaloDBIterator.hasNext` | method | Reports whether another live record remains. |
| `HaloDBIterator.next` | method | Returns the next live record. |
| `Record` | class | Carries one live key-value pair. |
| `Record.getKey` | method | Returns the record key bytes. |
| `Record.getValue` | method | Returns the record value bytes. |
| `HaloDBStats` | class | Captures one operational statistics view. |
| `HaloDBStats.getSize` | method | Returns the live-key count. |
| `HaloDBStats.getNumberOfFilesPendingCompaction` | method | Returns pending compaction files. |
| `HaloDBStats.getStaleDataPercentPerFile` | method | Returns stale percentages by data-file identifier. |
| `HaloDBStats.getRehashCount` | method | Returns interval index rehash activity. |
| `HaloDBStats.getNumberOfSegments` | method | Returns the index segment count. |
| `HaloDBStats.getMaxSizePerSegment` | method | Returns per-segment index capacity. |
| `HaloDBStats.getNumberOfRecordsCopied` | method | Returns interval compaction copy count. |
| `HaloDBStats.getNumberOfRecordsReplaced` | method | Returns interval replacement count during compaction. |
| `HaloDBStats.getNumberOfRecordsScanned` | method | Returns interval compaction scan count. |
| `HaloDBStats.getSizeOfRecordsCopied` | method | Returns interval copied bytes. |
| `HaloDBStats.getSizeOfFilesDeleted` | method | Returns interval deleted-file bytes. |
| `HaloDBStats.getSizeReclaimed` | method | Returns interval reclaimed bytes. |
| `HaloDBStats.getOptions` | method | Returns a clone of active options. |
| `HaloDBStats.getNumberOfDataFiles` | method | Returns the data-file count. |
| `HaloDBStats.getNumberOfTombstoneFiles` | method | Returns the tombstone-file count. |
| `HaloDBStats.getNumberOfTombstonesFoundDuringOpen` | method | Returns tombstones observed during open. |
| `HaloDBStats.getNumberOfTombstonesCleanedUpDuringOpen` | method | Returns obsolete tombstones removed during open. |
| `HaloDBStats.getCompactionRateInInternal` | method | Returns compaction rate for the reset interval. |
| `HaloDBStats.getCompactionRateSinceBeginning` | method | Returns long-lived compaction rate. |
| `HaloDBStats.isCompactionRunning` | method | Reports compaction worker state. |
| `HaloDBStats.toString` | method | Returns a human-readable statistics summary. |
| `HaloDBException` | exception | Reports facade-level storage and lifecycle failures. |

### CLI Entry Points

There is no console executable or public `main` entry point for this artifact. Programmatic use is through the Maven dependency and Java imports.

## Appendix A: Environment

The working environment runs JDK 8 and Maven 3.9 on Linux in a Docker container without network access. The offline Maven repository provides `org.slf4j:slf4j-api:1.7.12`, `com.google.guava:guava:18.0`, `net.java.dev.jna:jna:4.1.0`, optional `net.jpountz.lz4:lz4:1.3`, `org.testng:testng:6.9.10`, `org.jmockit:jmockit:1.38`, `org.assertj:assertj-core:3.8.0`, `org.hamcrest:hamcrest-all:1.3`, `org.apache.logging.log4j:log4j-core:2.3`, `org.apache.logging.log4j:log4j-slf4j-impl:2.3`, and their transitive artifacts. The assessment environment provides the same JDK, Maven, operating system, container isolation, and offline artifact set.

The project must declare Maven metadata in `pom.xml` at the project root, use coordinates `com.oath.halodb:halodb:0.5.6`, produce JAR packaging, target Java 8 bytecode, and declare every runtime dependency used by the implementation. Maven resolution must succeed entirely from the offline repository.

## Appendix B: Assessment Notes

Assessment compiles the Maven artifact and invokes only the documented public Java types against local temporary database directories. Checks cover configuration defaults and validation, CRUD and update semantics, iteration, live counts, statistics, exclusive ownership, close/reopen persistence, tombstones, compaction controls, crash-oriented recovery, and consistency across point, iterator, statistics, and filesystem-lifecycle views. Assertions focus on observable behavior and exception classes, not private types, exact diagnostics, timing-sensitive throughput, native allocation addresses, or presentation formatting.
