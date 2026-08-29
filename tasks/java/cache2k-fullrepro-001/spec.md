# cache2k-core Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`cache2k-core` is an in-memory Java cache runtime that backs a separately supplied public API with concurrent key/value storage, read-through loading, atomic entry processing, expiry, refresh, resilience, events, lifecycle management, and operational observations. The runtime maintains one authoritative entry state per cache and projects it through direct cache operations, a live `ConcurrentMap`, loaders and processors, manager registries, listeners, and control/statistics snapshots.

The implementation artifact works with `cache2k-api` through Java service discovery. Applications construct caches with `Cache2kBuilder`, optionally attach loading and policy customizations, and close caches or managers when their lifecycle ends.

## Non-Goals

- This specification does not require JCache/JSR-107 adapters or TCK behavior.
- This specification does not require Spring, XML configuration, JMX, Micrometer, or other integration modules.
- This specification does not require internal eviction, timer-wheel, hash-table, storage, or provider class layouts.
- This specification does not define exact diagnostic text, `toString()` formatting, log wording, or implementation class names.
- This specification does not require wall-clock-fragile timing precision, stress behavior, or a particular eviction victim when several entries qualify.
- This specification does not define the low-level configuration-bean extension DSL, annotation package behavior, or asynchronous loader callback carrier protocol.

## Representative Workflows

The first workflow constructs a named read-through cache, observes a single load, updates the same fact through the map projection, and closes the cache.

```java
AtomicInteger loads = new AtomicInteger();
Cache<Integer, String> cache = Cache2kBuilder.of(Integer.class, String.class)
  .name("routes")
  .entryCapacity(100)
  .loader(key -> "v" + loads.incrementAndGet())
  .build();

String first = cache.get(7);                 // loads and stores "v1"
String second = cache.get(7);                // returns the stored value
cache.asMap().put(7, "manual");
String projected = cache.peek(7);            // returns "manual"
cache.close();
```

The second workflow applies an atomic mutation with per-entry expiry, observes it through entry and map views, and samples public control information.

```java
Cache<String, Integer> cache = Cache2kBuilder.of(String.class, Integer.class)
  .name("counts")
  .expireAfterWrite(Duration.ofMinutes(5))
  .build();

Integer result = cache.invoke("jobs", entry -> {
  int next = entry.exists() ? entry.getValue() + 1 : 1;
  entry.setValue(next);
  entry.setExpiryTime(entry.getStartTime() + 60_000);
  return next;
});

CacheEntry<String, Integer> snapshot = cache.peekEntry("jobs");
CacheControl control = CacheControl.of(cache);
long visibleSize = control.getSize();
CacheStatistics statistics = control.sampleStatistics();
```

## Cache Construction and Lifecycle

Cache construction binds public API configuration to a named manager and creates a runtime instance with a well-defined lifecycle.

**Runtime discovery and builders.** The `cache2k-core` artifact must provide exactly one usable `Cache2kCoreProvider` through Java `ServiceLoader` discovery when placed beside the companion API artifact. When no provider is discoverable, the first initialization of `CacheManager` must fail with `LinkageError`. `Cache2kBuilder.of` must create typed builders from key and value classes, while `forUnknownTypes` must create a builder whose key and value types are initially unrestricted. When an anonymous `Cache2kBuilder` subclass captures concrete generic parameters, the builder must retain those types for `CacheInfo`; if the subclass does not capture usable parameters, construction must raise `IllegalArgumentException`.

The `manager` setting must select the manager that owns the built cache and must raise `IllegalStateException` when applied after another manager assignment or after configuration binding has started. The `name` setting must preserve the supplied cache name. When no name is supplied, `build` must assign a unique generated name beginning with `_`. If an active cache with the same explicit name already exists in the selected manager, then `build` must raise `IllegalStateException` without replacing the existing cache.

The `entryCapacity` setting must bound the number of retained entries through eviction after insertions exceed the configured limit. The `eternal`, `expireAfterWrite`, `keepDataAfterExpired`, `refreshAhead`, `sharpExpiry`, `permitNullValues`, `disableStatistics`, loader, writer, policy, listener, executor, scheduler, and time-reference settings must take effect on the cache returned by `build`. When `eternal(true)` and a finite `expireAfterWrite` duration are both configured in either order, `build` must succeed and the finite duration must remain the effective expire-after-write interval.

**Manager identity and closure.** `CacheManager.getInstance` must return the same open manager for the same class-loader/name pair and distinct managers for distinct pairs. `STANDARD_DEFAULT_MANAGER_NAME` must be `"default"`, and `setDefaultName` must affect later default-manager lookup only when invoked before that default manager is obtained. `getActiveCaches` must enumerate caches owned by the manager that are not closed, and `getCache` must return the previously created named cache or `null` when no active cache has that name.

When a cache closes, it must release its runtime resources, remove itself from its manager's active-cache view, and report `isClosed()` as true; repeated close calls must have no additional effect. If an ordinary cache operation is invoked after close, then it must raise `CacheClosedException` or another `IllegalStateException`, while `getName`, `isClosed`, and limited diagnostic access must remain available. When a manager closes, it must close every active cache, reject creation of new caches, report `isClosed()` as true, and permit a later lookup to create a fresh manager with the same name.

## Entry Access, Mutation, and Map Projection

Direct cache operations and the concurrent-map projection expose the same entry facts while preserving the cache-specific distinction between loading and non-loading access.

**Reads and entry snapshots.** When `get` or `getEntry` receives a missing or expired key and a loader is configured, the cache must invoke the loader and return the loaded result; concurrent requests for that key must wait for the active load. When no loader is configured, `get` must return the same value-or-null result as `peek`. `peek`, `peekEntry`, and `containsKey` must inspect cache state without invoking a loader. `peekEntry` must return `null` for no visible entry and otherwise return an immutable `CacheEntry` whose `getKey`, `getValue`, `getException`, and `getExceptionInfo` describe one observation.

When null values are disabled, a null key or a stored null value must raise `NullPointerException`. Where null values are enabled, `containsKey` and `peekEntry` must distinguish an existing null mapping from an absent mapping, while value-returning operations still return `null` for both cases. If an entry holds an unsuppressed loader exception, then `containsKey` must report the mapping as present, `CacheEntry.getException` must expose the original cause, and value access must raise the configured propagated runtime exception.

**Mutations and atomic forms.** `put` and `putAll` must insert or replace mappings and must make successful changes visible to `peek`, `containsKey`, iteration, and `asMap`. `peekAndPut`, `peekAndReplace`, `peekAndRemove`, `containsAndRemove`, `putIfAbsent`, `replace`, `replaceIfEquals`, `remove`, and `removeIfEquals` must perform each single-key read/compare/write effect atomically and must not invoke the loader. If a compare condition or required-presence condition is false, then the operation must preserve the mapping and return its documented false-or-null result.

`computeIfAbsent` must invoke its function at most once for the successful atomic insertion attempt when no entry, including no exception entry, is present. If a mutation callback, expiry policy, or writer raises before commit, then the cache must preserve the previous mapping and propagate the documented wrapper or original runtime exception. `removeAll(keys)` must apply removal semantics to each supplied key, `removeAll()` must remove all mappings with removal notifications, and `clear()` must remove all mappings without entry-removal notifications.

**Live map and iteration views.** `asMap` must return a live `ConcurrentMap` whose successful mutations immediately affect the cache and whose reads reflect cache mutations. Map operations must never invoke the cache loader. Two map wrappers over the same cache must compare and hash by cache identity rather than by a detached snapshot of entries.

`keys()` and `entries()` must include every mapping visible when their iterator is obtained, emit each included key at most once, tolerate concurrent cache activity, and leave cache hit/miss statistics unchanged. `peekAll` must return an immutable map containing only visible requested mappings without loading; `getAll` must return an immutable map for requested keys after applying loading semantics. If any supplied key is null, then bulk access must raise `NullPointerException`.

## Loading, Bulk Work, and Write-Through

Loading and writing connect cache state to application customizations while preserving per-key coordination and commit ordering.

**Read-through and bulk loading.** A `CacheLoader` must receive the requested non-null key when loading is triggered. An `AdvancedCacheLoader` must additionally receive one stable operation start time and the prior entry when reload, refresh, or retained expired data makes that entry available. A `BulkCacheLoader` must receive the set of outstanding keys for bulk-capable requests and must return a value mapping for those keys.

When `loadAll` is called, it must return immediately with a `CompletableFuture`, load only missing or expired requested keys, and complete only after every requested load finishes. When `reloadAll` is called, it must return a `CompletableFuture` and start a load for every requested key regardless of current presence. If either operation is invoked without a configured loader, then it must raise `UnsupportedOperationException` immediately. If a constituent load fails, then the returned future must complete exceptionally with cache loader failure semantics.

`getAll` must use a configured bulk loader for outstanding keys and must not promise atomicity across different keys. If every requested load fails, then `getAll` must raise `CacheLoaderException`; if at least one key succeeds, it must return the result map and defer a failed key's exception until that key is read from the returned map.

**Write-through ordering.** Where a `CacheWriter` is configured, successful insert and update operations must call `write` synchronously before committing the new cache mapping, and explicit removals must call `delete`. Expiry and `clear()` must not call `CacheWriter.delete`. If `write` or `delete` raises, then the cache must raise `CacheWriterException` and preserve the pre-operation cache mapping.

## Atomic Entry Processing

Entry processors express arbitrary single-key transactions and provide per-key result carriers for bulk invocation.

**Processor execution.** `invoke` must run an `EntryProcessor` atomically with respect to other operations on the same key and must return the processor result. The runtime must be free to restart the processor when entry information requires loading, so processor code must observe a consistent entry on every invocation and commit effects only from a normally completed execution. If processor code raises, then `invoke` must raise `EntryProcessingException` and leave the mapping unchanged.

`MutableCacheEntry.exists` must inspect presence without triggering a load, while `getValue`, `getException`, and `getExceptionInfo` must trigger configured load semantics when required. `getStartTime` must remain constant throughout one logical invocation. `setValue`, `remove`, `setException`, `setExpiryTime`, and `setModificationTime` must stage changes; when several value/remove mutations occur, only the final staged mutation must determine cache state.

If `load` is requested without a configured loader, then it must raise `UnsupportedOperationException`; if `getValue` was already requested in that invocation, then `load` must raise `IllegalStateException`. A staged `setExpiryTime` on a missing entry without a staged value must have no effect. Where a writer is configured, `remove` must call `delete` even when the entry did not previously exist.

**Bulk processor results.** `invokeAll` must return an immutable map with one `EntryProcessingResult` for each requested key, without promising invocation order. A successful result's `getResult` must return the processor value and `getException` must return `null`. A failed result's `getException` must return the original processor exception and `getResult` must raise `EntryProcessingException`. `mutate` and `mutateAll` must apply the same transaction and failure rules without a user result.

## Expiry, Refresh, Null, and Resilience Policies

Time and failure policies determine whether an entry remains visible, refreshes in the background, retains stale data, or stores a loader exception.

**Expiry values and policies.** `ExpiryTimeValues.NOW` must mean immediate expiry without caching, `REFRESH` must request immediate refresh when refresh-ahead is enabled, `ETERNAL` must request no policy expiry subject to the configured maximum, and `NEUTRAL` must preserve an existing expiry during update. `Expiry.toSharpTime` must preserve `ETERNAL` and represent a non-eternal point as a sharp-expiry value. `Expiry.earliestTime` must return the earliest candidate not before the load time, or `ETERNAL` when neither candidate qualifies.

When `ExpiryPolicy.calculateExpiryTime` runs after a successful insert, update, or load, it must receive the key, proposed value, operation start time, and previous entry when present. The effective expiry must never extend beyond `expireAfterWrite`. If the policy returns `NOW`, then the value must not remain cached; if it returns a negative point-in-time, then visibility must stop at the absolute point in time.

Ordinary expiry must stop entry visibility after timer processing and must permit physical removal and expiry notification to lag. Where sharp expiry applies, the cache must stop returning the value at the specified point even when physical removal lags. `expireAt` must have no effect for a missing or already expired entry, must avoid writer deletion, and must apply the `NOW`, `REFRESH`, and `ETERNAL` meanings to a visible entry.

**Refresh and retained data.** Where refresh-ahead and a loader are enabled, reaching an ordinary expiry must start loading a replacement and keep the old value visible until the replacement succeeds. If no refresh execution resource is available, then the entry must expire and the next loading read must perform the load. Where sharp expiry and refresh-ahead apply together, reads after the expiry point must wait for the replacement instead of returning the expired value.

Where `keepDataAfterExpired` is enabled, expired data must remain unavailable to normal cache and map reads yet remain available as prior-entry context to an advanced loader and resilience policy until eviction. If a refreshed entry is not accessed during its probation interval, then the next expiry must remove it without another refresh.

**Nulls and loader failures.** If null values are disabled and a loader returns null, then the expiry policy must receive that proposed null first; a `NOW` result must discard it, while any caching result must lead to `CacheLoaderException` with a `NullPointerException` cause. Where null values are enabled, a loaded null must create an existing mapping observable through `containsKey` and entry views.

Without a `ResiliencePolicy`, a loader exception must not replace a prior successful value or remain cached, and the next loading request must retry. When `suppressExceptionUntil` returns a future time with a prior value available, the cache must return that prior value and count the loader exception as suppressed until the returned time. When suppression is not selected, `retryLoadAfter` must determine how long the exception entry remains before another load attempt; value access during that interval must raise `CacheLoaderException` or the result of the configured `ExceptionPropagator`.

`LoadExceptionInfo` must expose the key, original exception, consecutive retry count starting at zero, first-failure time, latest-load time, retry-until time, and active exception propagator. After a successful load, the next failure sequence's retry count must restart at zero.

## Events, Control, and Statistics

Listeners and operational interfaces project committed state transitions without exposing implementation structures.

**Entry events.** A listener added with `addListener` must execute synchronously for matching create, update, and remove transitions before the initiating cache operation completes, while expiry notification must execute asynchronously. A listener added with `addAsyncListener` must execute through the configured asynchronous listener executor. If a synchronous listener raises, then the cache operation must raise `CacheEventListenerException`; listener code must not mutate cached values.

Created listeners must receive the committed entry after first insertion, updated listeners must receive the previous and new entry snapshots, removed listeners must receive the removed entry, and expired listeners must receive the expired entry. When a cache closes, each configured `CacheClosedListener` must be invoked and its returned completion stage must participate in graceful closure.

**Control and information.** `CacheControl.of` and `CacheInfo.of` must resolve the operational projection for an open supported cache. `CacheInfo` must report cache and manager names, configured key and value types, visible-or-retained size estimate, capacity or weight limits, loader/weigher/statistics presence, creation and latest-clear times, configured expiry ticks, and active `TimeReference`. If `requestInterface` receives an unsupported type or the cache is closed, then it must raise `UnsupportedOperationException` or `IllegalStateException`, respectively.

`CacheOperation.clear`, `removeAll`, `close`, `destroy`, and `changeCapacity` must return futures that complete after the requested control action. `changeCapacity` must update the capacity limit and evict entries as needed to honor the new bound. If a control action cannot complete, then its future must complete exceptionally without reporting false success.

**Statistics snapshots.** When statistics are enabled, `sampleStatistics` must return a snapshot whose counters distinguish gets, misses, inserts, puts, removals, clears, successful loads, loader exceptions, suppressed loader exceptions, refresh outcomes, expiry, and eviction. `containsKey` and iteration must not increase get, hit, or miss counters. `getHitRate` must represent delivered-data requests as a percentage of get requests, and load-time aggregates need only be mutually consistent within the documented lock-free snapshot tolerance.

Where statistics are disabled, `CacheInfo.isStatisticsEnabled` must return false and `CacheControl.sampleStatistics` must return `null`. After `clear`, `CacheInfo.getClearedTime` and clear-related statistics must reflect the operation while the cache remains open.

## State Model

The core state is a manager registry of open caches. Each cache owns configuration, lifecycle status, entry records, in-flight loads, listener registrations, and statistics. Each entry record has a key and one of four public states: absent, value-present, exception-present, or expired-retained. A value-present record also carries expiry and modification timing; an exception-present record carries `LoadExceptionInfo` and retry timing.

The public projections are direct `Cache` operations, `CacheEntry` snapshots, the live `ConcurrentMap`, key/entry iterators and bulk maps, loader/writer/policy callbacks, processor entries and results, listener callbacks, manager active-cache lookup, and `CacheInfo`/`CacheStatistics` snapshots. A transition must become visible across these projections only after its commit point.

## Error Semantics

| Condition | Required result |
|---|---|
| If a key is null, then a cache operation must raise `NullPointerException`. | The mapping must remain unchanged. |
| If a null value is stored while null values are disabled, then the cache must raise `NullPointerException`. | The mapping must remain unchanged. |
| If an active cache with the same explicit name already exists in the selected manager, then `build` must raise `IllegalStateException` without replacing the existing cache. | Duplicate active-name rejection. |
| When `eternal(true)` and a finite `expireAfterWrite` duration are both configured in either order, `build` must succeed and the finite duration must remain the effective expire-after-write interval. | Successful finite-expiry construction. |
| If an ordinary cache operation follows closure, then it must raise `CacheClosedException` or another `IllegalStateException`. | Name and closed-state inspection must remain available. |
| If loading fails without suppression, then value access must raise `CacheLoaderException` or the configured propagated runtime exception. | `CacheEntry` and `LoadExceptionInfo` must retain the original cause when the exception is cached. |
| If a writer raises, then the mutation must raise `CacheWriterException`. | The previous mapping must remain unchanged. |
| If processor code raises, then invocation must raise `EntryProcessingException` or expose that failure through `EntryProcessingResult`. | The affected mapping must remain unchanged. |
| If no loader exists for `loadAll`, `reloadAll`, or `MutableCacheEntry.load`, then the operation must raise `UnsupportedOperationException`. | Cache state must remain unchanged. |
| If an unsupported operational interface is requested, then `requestInterface` must raise `UnsupportedOperationException`. | Cache state must remain unchanged. |
| If runtime provider discovery finds no provider, then `CacheManager` initialization must fail with `LinkageError`. | No manager must be reported as available. |

## Cross-View Invariants

1. A successful mutation through `Cache` must produce the same visible key/value fact through `peekEntry`, `asMap`, `keys`, `entries`, and `CacheInfo.getSize`, subject only to documented concurrent change and eviction.
2. A successful mutation through `asMap` must be returned by direct cache reads and entry snapshots without invoking a loader.
3. A mapping removed through direct cache operations, map operations, expiry, or manager/cache closure must cease to be visible in every read and iteration projection after that transition completes.
4. A value produced by a loader must become the same committed value observed by `get`, `peek`, entry snapshots, map reads, listeners, and enabled statistics.
5. An entry-processor commit must be atomic for its key and must project the final staged value/removal and expiry consistently through cache, map, entry, listener, and control views.
6. A loader exception must preserve one original cause across `CacheEntry.getException`, `LoadExceptionInfo`, propagated cache access, resilience decisions, and enabled exception statistics.
7. A cache listed by `CacheManager.getActiveCaches` must report the same manager through `getCacheManager` and the same manager name through `CacheInfo`; after close, all three lifecycle views must agree that it is inactive.
8. `clear()` and `removeAll()` must both empty direct, map, and iteration views, while only `removeAll()` must produce per-entry removal notifications and writer deletion calls.
9. An expired-retained entry must be absent from cache/map/iteration reads yet remain available only to documented loader or resilience callback context and the size estimate until eviction.
10. Enabled statistics must describe the same committed operations exposed by cache, loader, expiry, refresh, and control views, while non-loading presence checks and iteration remain hit/miss neutral.

## Public Interface

### Import Surface

```java
import org.cache2k.Cache;
import org.cache2k.Cache2kBuilder;
import org.cache2k.CacheClosedException;
import org.cache2k.CacheEntry;
import org.cache2k.CacheException;
import org.cache2k.CacheManager;
import org.cache2k.KeyValueSource;
```

```java
import org.cache2k.config.CacheType;
```

```java
import org.cache2k.event.CacheClosedListener;
import org.cache2k.event.CacheEntryCreatedListener;
import org.cache2k.event.CacheEntryExpiredListener;
import org.cache2k.event.CacheEntryOperationListener;
import org.cache2k.event.CacheEntryRemovedListener;
import org.cache2k.event.CacheEntryUpdatedListener;
import org.cache2k.event.CacheEventListenerException;
```

```java
import org.cache2k.expiry.Expiry;
import org.cache2k.expiry.ExpiryPolicy;
import org.cache2k.expiry.ExpiryTimeValues;
import org.cache2k.expiry.ValueWithExpiryTime;
```

```java
import org.cache2k.io.AdvancedCacheLoader;
import org.cache2k.io.BulkCacheLoader;
import org.cache2k.io.CacheLoader;
import org.cache2k.io.CacheLoaderException;
import org.cache2k.io.CacheWriter;
import org.cache2k.io.CacheWriterException;
import org.cache2k.io.ExceptionPropagator;
import org.cache2k.io.LoadExceptionInfo;
import org.cache2k.io.ResiliencePolicy;
```

```java
import org.cache2k.operation.CacheControl;
import org.cache2k.operation.CacheInfo;
import org.cache2k.operation.CacheOperation;
import org.cache2k.operation.CacheStatistics;
import org.cache2k.operation.TimeReference;
```

```java
import org.cache2k.processor.EntryMutator;
import org.cache2k.processor.EntryProcessingException;
import org.cache2k.processor.EntryProcessingResult;
import org.cache2k.processor.EntryProcessor;
import org.cache2k.processor.MutableCacheEntry;
```

```java
import org.cache2k.spi.Cache2kCoreProvider;
```

### Public Members

- `Cache`: `getName`, `get`, `getEntry`, `peek`, `peekEntry`, `containsKey`, `put`, `computeIfAbsent`, `putIfAbsent`, `peekAndReplace`, `replace`, `replaceIfEquals`, `peekAndRemove`, `containsAndRemove`, `remove`, `removeIfEquals`, `removeAll`, `peekAndPut`, `expireAt`, `loadAll`, `reloadAll`, `invoke`, `mutate`, `invokeAll`, `mutateAll`, `getAll`, `peekAll`, `putAll`, `keys`, `entries`, `clear`, `close`, `getCacheManager`, `isClosed`, `requestInterface`, `asMap`.
- `Cache2kBuilder`: protected anonymous-subclass construction, `forUnknownTypes`, `of`, `manager`, `keyType`, `valueType`, `name`, `keepDataAfterExpired`, `entryCapacity`, `eternal`, `expireAfterWrite`, `exceptionPropagator`, `loader`, `bulkLoader`, `writer`, `addCacheClosedListener`, `addListener`, `addAsyncListener`, `expiryPolicy`, `refreshAhead`, `sharpExpiry`, `loaderThreadCount`, `permitNullValues`, `disableStatistics`, `loaderExecutor`, `refreshExecutor`, `executor`, `scheduler`, `timeReference`, `asyncListenerExecutor`, `config`, `getManager`, `build`.
- `CacheEntry`: `getKey`, `getValue`, `getException`, `getExceptionInfo`.
- `CacheManager`: `STANDARD_DEFAULT_MANAGER_NAME`, `getDefaultName`, `setDefaultName`, `getInstance`, `closeAll`, `close`, `isDefaultManager`, `getName`, `getActiveCaches`, `getCache`, `createCache`, `clear`, `isClosed`, `getProperties`, `getClassLoader`.
- `CacheType`: `of`, `getType`, `hasTypeArguments`, `isArray`, `getComponentType`, `getTypeArguments`, `getTypeName`.
- Entry listener members: `onEntryCreated`, `onEntryUpdated`, `onEntryRemoved`, `onEntryExpired`; `CacheClosedListener.onCacheClosed`.
- `Expiry`: `toSharpTime`, `earliestTime`, `mixTimeSpanAndPointInTime`; `ExpiryPolicy.calculateExpiryTime`; constants `NEUTRAL`, `NOW`, `REFRESH`, `ETERNAL`; `ValueWithExpiryTime.getCacheExpiryTime`.
- Loader and writer members: `CacheLoader.load`, `AdvancedCacheLoader.load`, `BulkCacheLoader.loadAll`, `CacheWriter.write`, `CacheWriter.delete`, `ExceptionPropagator.propagateException`.
- `LoadExceptionInfo`: `getKey`, `getValue`, `getException`, `getExceptionInfo`, `generateExceptionToPropagate`, `getExceptionPropagator`, `getRetryCount`, `getSinceTime`, `getLoadTime`, `getUntil`.
- `ResiliencePolicy`: `disabledPolicy`, `disable`, `suppressExceptionUntil`, `retryLoadAfter`.
- `MutableCacheEntry`: `getValue`, `getException`, `getExceptionInfo`, `exists`, `getStartTime`, `lock`, `setValue`, `load`, `remove`, `setException`, `setExpiryTime`, `getExpiryTime`, `getModificationTime`, `setModificationTime`.
- Processor members: `EntryProcessor.process`, `EntryMutator.mutate`, `EntryProcessingResult.getResult`, `EntryProcessingResult.getException`.
- `CacheControl`: `of`, `sampleStatistics`, plus inherited `CacheInfo` and `CacheOperation` members.
- `CacheInfo`: `of`, `getName`, `getManagerName`, `getKeyType`, `getValueType`, `getSize`, `getEntryCapacity`, `getMaximumWeight`, `getTotalWeight`, `getCapacityLimit`, `getImplementation`, `isLoaderPresent`, `isWeigherPresent`, `isStatisticsEnabled`, `getCreatedTime`, `getClearedTime`, `getExpiryAfterWriteTicks`, `getTimeReference`.
- `CacheOperation`: `clear`, `removeAll`, `close`, `destroy`, `changeCapacity`.
- `CacheStatistics`: `getInsertCount`, `getGetCount`, `getMissCount`, `getLoadCount`, `getLoadExceptionCount`, `getSuppressedLoadExceptionCount`, `getMillisPerLoad`, `getTotalLoadMillis`, `getRefreshCount`, `getRefreshFailedCount`, `getRefreshedHitCount`, `getExpiredCount`, `getEvictedCount`, `getEvictedOrRemovedWeight`, `getPutCount`, `getRemoveCount`, `getClearedCount`, `getClearCallsCount`, `getKeyMutationCount`, `getHitRate`.
- `TimeReference`: `DEFAULT`, `MINIMUM_TICKS`, `ticks`, `sleep`, `ticksToMillisCeiling`, `toTicks`, `ticksToInstant`.
- `Cache2kCoreProvider`: `setDefaultManagerName`, `getDefaultManagerName`, `getManager`, `getDefaultClassLoader`, `close`, `createCache`, `getDefaultConfig`, `getVersion`.

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Cache` | interface | Exposes direct, bulk, atomic, lifecycle, iteration, and map-projection cache operations. |
| `Cache2kBuilder` | class | Configures and builds a cache runtime instance. |
| `CacheClosedException` | exception | Signals access to a closed cache. |
| `CacheEntry` | interface | Provides an immutable observation of a key's value or loader failure. |
| `CacheException` | exception | Base runtime failure for cache operations. |
| `CacheManager` | abstract class | Names, creates, finds, clears, and closes groups of caches. |
| `KeyValueSource` | interface | Provides the reduced loading `get` projection. |
| `CacheType` | interface | Describes captured cache key or value types. |
| `CacheClosedListener` | interface | Observes cache closure completion. |
| `CacheEntryCreatedListener` | interface | Observes first insertion of an entry. |
| `CacheEntryExpiredListener` | interface | Observes entry expiry. |
| `CacheEntryOperationListener` | interface | Common marker for entry-operation listeners. |
| `CacheEntryRemovedListener` | interface | Observes explicit entry removal. |
| `CacheEntryUpdatedListener` | interface | Observes replacement of an existing entry. |
| `CacheEventListenerException` | exception | Wraps synchronous listener failure. |
| `Expiry` | class | Supplies expiry constants and calculation helpers. |
| `ExpiryPolicy` | interface | Calculates entry-specific expiry points. |
| `ExpiryTimeValues` | interface | Defines special expiry control values. |
| `ValueWithExpiryTime` | interface | Lets a value provide its own cache expiry point. |
| `AdvancedCacheLoader` | interface | Loads with operation time and prior-entry context. |
| `BulkCacheLoader` | interface | Loads a set of keys as one request. |
| `CacheLoader` | interface | Supplies missing or expired values by key. |
| `CacheLoaderException` | exception | Represents an unsuppressed loader failure. |
| `CacheWriter` | interface | Performs synchronous write-through mutation callbacks. |
| `CacheWriterException` | exception | Wraps writer failure. |
| `ExceptionPropagator` | interface | Converts recorded load failure information into a runtime exception. |
| `LoadExceptionInfo` | interface | Describes the current consecutive loader-failure sequence. |
| `ResiliencePolicy` | interface | Chooses stale-value suppression and exception retry timing. |
| `CacheControl` | interface | Combines information, statistics, and asynchronous control operations. |
| `CacheInfo` | interface | Exposes runtime configuration and lifecycle information. |
| `CacheOperation` | interface | Exposes asynchronous management actions. |
| `CacheStatistics` | interface | Exposes a lock-light snapshot of operation counters. |
| `TimeReference` | interface | Supplies cache-relative time and conversions. |
| `EntryMutator` | interface | Performs an atomic entry mutation without a result. |
| `EntryProcessingException` | exception | Wraps an entry-processor failure. |
| `EntryProcessingResult` | interface | Carries one bulk processor result or failure. |
| `EntryProcessor` | interface | Performs an atomic function over one mutable entry. |
| `MutableCacheEntry` | interface | Provides staged value, exception, expiry, and modification-time operations inside a processor. |
| `Cache2kCoreProvider` | interface | Connects the public API to the runtime implementation through service discovery. |

### CLI Entry Points

There is no console script for this package. No Java main-class entry point is supported. Programmatic use is through the public Java API.

## Appendix A: Environment

The working environment runs OpenJDK 17 and Maven 3 on Linux without network access. The Java standard library, `org.cache2k:cache2k-api:2.8-SNAPSHOT`, optional `org.slf4j:slf4j-api:1.7.32`, and verification-only JUnit artifacts are available from the local Maven repository. The target implementation artifact is not preinstalled. The assessment environment provides the same JDK, Maven tooling, operating system, and offline artifact set.

The project must provide a root Maven `pom.xml`, use JAR packaging and coordinate `org.cache2k:cache2k-core:2.8-SNAPSHOT`, compile production source from `src/main/java`, depend on the companion API coordinate, and provide a runtime `Cache2kCoreProvider` through Java service discovery. Every dependency must resolve from the offline repository.

## Appendix B: Assessment Notes

Assessment exercises public Java behavior across construction, manager identity and closure, direct and map access, atomic operations, bulk loading, writer rollback, entry processing, null handling, expiry and refresh, resilience, listeners, control information, statistics, and cross-view consistency. Checks compare public values, exception classes, lifecycle state, callback observations, futures, and counter relationships. They do not depend on private implementation packages, internal data structures, exact diagnostic text, external services, integration adapters, or unstable timing races.
