# Commons Pool Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`commons-pool3` is a Java object-pooling library that manages reusable, equivalent objects through a configurable non-keyed pool. A factory owns creation and lifecycle callbacks, pooled wrappers expose per-object state and timing, and the pool exposes capacity, ordering, maintenance, abandonment, statistics, and management views over the same live population.

The public contract in this document centers on `GenericObjectPool`. It covers ordinary client borrowing and return, factory integration, idle-object policy, abandonment recovery, and observability through Java methods and the platform management server.

## Non-Goals

- This specification does not require keyed pools or keyed factories.
- This specification does not require soft-reference pools, pool decorators, proxy packages, or bytecode-generation integrations.
- This specification does not require custom subclasses of the abstract pool implementation base classes.
- This specification does not define internal deque, eviction-timer, call-stack, lock, identity-map, or rolling-statistics implementations.
- This specification does not define exact exception message text, stack-trace text, or `toString()` formatting.
- This specification does not require deprecated millisecond setters that lack a corresponding public member in the interface tables below.

## Representative Workflows

The first workflow creates a reusable buffer factory, preloads one idle object, borrows it, and returns it after use.

```java
import org.apache.commons.pool3.BasePooledObjectFactory;
import org.apache.commons.pool3.PooledObject;
import org.apache.commons.pool3.impl.DefaultPooledObject;
import org.apache.commons.pool3.impl.GenericObjectPool;

final class BufferFactory extends BasePooledObjectFactory<StringBuilder, Exception> {
    @Override public StringBuilder create() { return new StringBuilder(); }
    @Override public PooledObject<StringBuilder> wrap(StringBuilder value) {
        return new DefaultPooledObject<>(value);
    }
    @Override public void passivateObject(PooledObject<StringBuilder> value) {
        value.getObject().setLength(0);
    }
}

try (GenericObjectPool<StringBuilder, Exception> pool =
        new GenericObjectPool<>(new BufferFactory())) {
    pool.addObject();
    StringBuilder value = pool.borrowObject();
    try {
        value.append("ready");
    } finally {
        pool.returnObject(value);
    }
}
```

The second workflow configures bounded FIFO service, enables validation and maintenance, then reads both direct counters and the management projection.

```java
import java.time.Duration;
import org.apache.commons.pool3.impl.GenericObjectPool;
import org.apache.commons.pool3.impl.GenericObjectPoolConfig;

GenericObjectPoolConfig<StringBuilder> config = new GenericObjectPoolConfig<>();
config.setLifo(false);
config.setMaxTotal(4);
config.setMaxIdle(2);
config.setMinIdle(1);
config.setTestOnBorrow(true);
config.setDurationBetweenEvictionRuns(Duration.ofSeconds(30));

try (GenericObjectPool<StringBuilder, Exception> pool =
        new GenericObjectPool<>(new BufferFactory(), config)) {
    pool.preparePool();
    StringBuilder value = pool.borrowObject(Duration.ofSeconds(1));
    pool.returnObject(value);
    long borrows = pool.getBorrowedCount();
    int idle = pool.getNumIdle();
    Object managementName = pool.getJmxName();
}
```

## Factory and Pooled-Object Lifecycle

Factory callbacks separate resource creation from pool policy, while `PooledObject` wrappers expose the lifecycle state used by the pool and by management callers.

**Factory construction and callbacks.**

- The `PooledObjectFactory` must provide `makeObject`, `activateObject`, `validateObject`, `passivateObject`, and both `destroyObject` forms for wrapped values.
- The `PooledObjectFactory` must be thread-safe, and the pool must not pass the same wrapped instance to more than one factory method at the same time.
- The single-argument `destroyObject` must represent `DestroyMode.NORMAL`, and the default two-argument form must delegate to the single-argument form.
- The `BasePooledObjectFactory` must implement `makeObject` by applying `wrap` to the non-null result of `create`.
- If `BasePooledObjectFactory.create` returns null, then `makeObject` must raise `NullPointerException`.
- The default `BasePooledObjectFactory` implementations of activation, destruction, and passivation must return without changing the wrapper, while its validation must return true.

**Wrapper state and time.**

- A new `DefaultPooledObject` must expose its supplied object, start in `PooledObjectState.IDLE`, and initialize creation, last-borrow, last-return, and last-use instants to its creation instant.
- When `allocate` is invoked on an idle wrapper, the wrapper must enter `ALLOCATED`, update its borrow and use instants, increment its borrowed count, and return true.
- If `allocate` is invoked on a wrapper that is not idle, then the wrapper must return false, except that an eviction-tested wrapper must enter `EVICTION_RETURN_TO_HEAD`.
- When `markReturning` followed by `deallocate` is invoked on an allocated wrapper, the wrapper must enter `IDLE`, update its last-return instant, and return true.
- If `deallocate` is invoked outside `ALLOCATED` or `RETURNING`, then the wrapper must return false.
- When `invalidate`, `markAbandoned`, or `markReturning` is invoked, the wrapper must expose `INVALID`, `ABANDONED`, or `RETURNING`, respectively, through `getState`.
- When `startEvictionTest` is invoked on an idle wrapper, the wrapper must enter `EVICTION` and return true.
- If `startEvictionTest` is invoked on a non-idle wrapper, then the wrapper must return false without replacing its current state.
- The wrapper must calculate active duration from the latest borrow until the latest return or current instant, full duration from creation until the current instant, and idle duration from the latest return until the current instant with negative idle results clamped to zero; the borrowed count must increase once for each successful idle-to-allocated transition.
- Where the wrapped object implements `TrackedUse`, `getLastUsedInstant` must return the later of the wrapper's recorded use instant and the object's `getLastUsedInstant`; otherwise it must return the wrapper's recorded use instant.
- The public state vocabulary must use `IDLE` for queued availability, `ALLOCATED` for a client lease, `EVICTION` and `EVICTION_RETURN_TO_HEAD` for an idle eviction test, `VALIDATION`, `VALIDATION_PREALLOCATED`, and `VALIDATION_RETURN_TO_HEAD` for maintenance validation, `INVALID` for removal, `ABANDONED` for an expired lease, and `RETURNING` for return processing.

## Borrowing, Return, Capacity, and Ordering

The pool coordinates idle values, active leases, capacity, waiting clients, and deterministic idle ordering.

**Construction and configuration snapshots.**

- A `GenericObjectPool` must accept a `factory`, an optional `GenericObjectPoolConfig`, and an optional `AbandonedConfig`, and both configuration objects must be copied by value at construction.
- If the supplied `factory` is null, then the constructor must raise `IllegalArgumentException` and must leave no management registration behind.
- A new default configuration must use `maxTotal` 8, `maxIdle` 8, `minIdle` 0, LIFO ordering, unfair waiter service, blocking exhaustion, an unlimited negative maximum wait, a 30-minute hard idle threshold, a disabled negative soft idle threshold, three tests per eviction run, disabled validation flags, disabled periodic eviction, a ten-second evictor shutdown timeout, enabled detailed statistics, enabled JMX with prefix `pool` and a null base, and `DefaultEvictionPolicy`.
- When `setConfig` is invoked, the pool must copy LIFO ordering, maximum wait, exhaustion blocking, validation flags, eviction sampling and thresholds, maintenance interval, eviction policy, evictor shutdown timeout, detailed-statistics selection, and all three capacity values while leaving construction-time fairness and JMX registration unchanged.
- When `GenericObjectPoolConfig.clone` is invoked, it must return a distinct configuration with the same property values.

**Borrow and return.**

- When an idle value is available, `borrowObject` must select it according to `lifo`, allocate it, activate it through the factory, and return its underlying object.
- When no idle value is available and the managed population is below `maxTotal`, `borrowObject` must create, allocate, activate, and return a new value.
- While the pool is exhausted and `blockWhenExhausted` is true, `borrowObject` must wait up to its selected maximum wait duration for an idle value.
- If the pool is exhausted and `blockWhenExhausted` is false, then `borrowObject` must raise `NoSuchElementException` without waiting for capacity.
- If a finite wait expires while the pool remains exhausted, then `borrowObject` must raise `NoSuchElementException`.
- Where fairness is enabled, blocked borrowers must receive released values in request-arrival order.
- When a borrowed value is returned successfully, `returnObject` must passivate it, move its wrapper to `IDLE`, increment the returned count, decrement the active projection, and expose it through the idle projection.
- If a returned value would make the idle population exceed `maxIdle`, then `returnObject` must destroy that value instead of retaining it idle.
- If `maxIdle` is negative, then the pool must impose no idle-population limit; if `maxTotal` is negative, then the pool must impose no total-population limit.
- When `lifo` is true, a borrow from multiple idle values must return the latest returned value; when `lifo` is false, it must return the oldest idle value.
- When `addObject` is invoked on an open pool with capacity, the pool must create and passivate one value and add it to the idle projection.
- When `addObjects` is invoked with a positive `count`, the pool must invoke `addObject` exactly `count` times in sequence; when `count` is zero or negative, it must return without adding an object.
- When `addObject` is invoked without remaining total capacity, the pool must return without changing the population.
- When `preparePool` is invoked with a positive effective `minIdle`, the pool must create idle values until it reaches that target or `maxTotal` prevents further creation.
- When `clear` is invoked, the pool must destroy values that are idle at removal time without changing active leases.
- When `close` is invoked, the pool must stop maintenance, destroy current idle values, release waiting borrowers, unregister its management name, and enter the closed state; repeated close calls must return without further effect.
- While the pool is closed, returned or invalidated leases must still be accepted and destroyed rather than retained.

## Validation, Invalidation, and Destruction

Validation switches determine where factory health checks occur and which failures retire a value from the managed population.

**Validation points.**

- Where `testOnCreate` is true, a newly created wrapper must be validated before it is eligible for borrowing.
- If creation validation fails, then the creating borrow must raise `NoSuchElementException` and must not retain the rejected wrapper.
- Where `testOnBorrow` is true, each activated wrapper must be validated before its object is returned to the caller.
- If borrow validation rejects an idle wrapper, then the pool must destroy it and continue with another idle or creatable wrapper; if it rejects a newly created wrapper, then the borrow must raise `NoSuchElementException`.
- Where `testOnReturn` is true, each returning wrapper must be validated before passivation.
- If return validation fails, then the pool must destroy the wrapper, count the return, and free its capacity without raising the validation result to the caller.

**Invalidation and callback failures.**

- When `invalidateObject` receives a currently managed object, the pool must remove and destroy its wrapper with the supplied `DestroyMode`, free capacity, and decrement the active projection.
- If `invalidateObject` receives an object that does not belong to the pool and abandonment handling is absent, then the pool must raise `IllegalStateException`.
- If `returnObject` receives an object that does not belong to the pool or receives the same lease more than once and abandonment handling is absent, then the pool must raise `IllegalStateException`.
- If activation of a newly created wrapper fails, then the pool must destroy that wrapper and raise `NoSuchElementException` with the activation failure as its cause.
- If passivation of a returning wrapper fails, then the pool must destroy the wrapper, free capacity, count the return, and notify the swallowed-exception listener.
- When an exception is unavoidably swallowed during clear, return, destruction, maintenance, or abandonment, the pool must invoke `SwallowedExceptionListener.onSwallowException` when a listener is configured.

## Idle Maintenance and Eviction

Idle maintenance applies a configurable policy to a bounded sample and optionally validates surviving wrappers before replenishing the idle target.

**Scheduling and selection.**

- When `durationBetweenEvictionRuns` is positive, the pool must run periodic maintenance at that interval; when it is zero or negative, periodic maintenance must be disabled.
- When `numTestsPerEvictionRun` is positive, each eviction run must examine no more than that number of idle wrappers; when it is negative, each run must examine the ceiling of idle count divided by its absolute value.
- Successive `evict` calls must visit idle wrappers in oldest-to-youngest order and continue cyclically across the idle population.
- The `EvictionPolicy.evict` operation must receive an `EvictionConfig`, the wrapper under test, and the current idle count including that wrapper.
- The default eviction policy must return true when idle duration exceeds the hard threshold, or when it exceeds the soft threshold while idle count is greater than `minIdle`.

**Validation and replenishment.**

- Where `testWhileIdle` is true, an idle wrapper that the eviction policy retains must be activated, validated, and passivated during maintenance.
- If maintenance activation, validation, or passivation fails, then the pool must destroy the affected wrapper and increment both destroyed and destroyed-by-evictor counts.
- If a custom eviction policy throws a non-fatal exception, then the pool must retain the wrapper for that decision and notify the swallowed-exception listener.
- Where maintenance is enabled and effective `minIdle` is positive, each maintenance run must attempt to replenish idle wrappers up to `min(minIdle, maxIdle)` without exceeding `maxTotal`.
- The `EvictionConfig` constructor must treat non-positive hard or soft durations as effectively unlimited thresholds and must preserve the supplied `minIdle`.
- When `EvictionConfig.isEvictionThread` is invoked by the periodic maintenance thread, it must return true; when invoked by another thread, it must return false.

## Abandoned-Lease Recovery

Abandonment policy recovers allocated values whose latest use is older than a configured timeout and projects the reason through `DestroyMode.ABANDONED`.

**Configuration and triggers.**

- A new `AbandonedConfig` must disable borrow-time removal, maintenance-time removal, logging, and usage tracking; it must use a five-minute timeout and require full stack traces.
- When `setAbandonedConfig` is invoked, the pool must retain a value copy so later mutations to the caller's configuration do not affect the pool.
- Where `removeAbandonedOnBorrow` is true, a borrow must scan for abandonment only when fewer than two idle values remain and active count is greater than `maxTotal - 3`.
- Where `removeAbandonedOnMaintenance` is true, each eviction run must scan allocated wrappers for abandonment.
- When an allocated wrapper's last-used instant is no later than the configured timeout boundary, abandonment removal must mark it abandoned and destroy it with `DestroyMode.ABANDONED`.
- Where `logAbandoned` is true, abandonment removal must write the recorded borrow and use traces to the configured `PrintWriter` before destruction.
- Where usage tracking is enabled, `GenericObjectPool.use` must update the managed wrapper's last-use record for the supplied object.
- If an already removed abandoned object is later returned or invalidated, then the pool must return without raising `IllegalStateException`.

## Statistics and Management Views

Direct accessors and JMX expose configuration, population, lifecycle totals, wait estimates, timing summaries, and per-wrapper information over the same pool state.

**Counters and timing.**

- `getNumActive` must return the managed population minus the idle population, and `getNumIdle` must return the current idle population.
- Successful creation, borrow, return, destruction, borrow-validation destruction, and evictor destruction events must increment their corresponding lifetime counters exactly once.
- `getNumWaiters` must return an estimate of blocked borrowers when exhaustion blocking is enabled and must return zero when it is disabled.
- The maximum borrow wait and mean active, idle, and borrow-wait accessors must summarize observed completed lifecycle events in milliseconds or `Duration` as named.
- Where detailed statistics collection is false, successful borrow and return operations must continue updating lifetime counts but must stop adding observations to the three mean timing series and maximum borrow wait.
- `listAllObjects` must return one `DefaultPooledObjectInfo` for every currently managed idle or active wrapper and must exclude destroyed wrappers.
- A `DefaultPooledObjectInfo` must expose borrowed count, creation time, last-borrow time, last-return time, wrapped-object class name, wrapped-object string value, and the recorded borrow trace from its represented wrapper.
- The formatted time accessors on `DefaultPooledObjectInfo` must format their corresponding epoch-millisecond values as `yyyy-MM-dd HH:mm:ss Z`.
- The `DefaultPooledObjectInfo.pooledObject` operation must return the represented wrapper, and its constructor must raise `NullPointerException` for a null wrapper.
- The `GenericObjectPool.getFactory` operation must return the construction factory, `getFactoryType` must return its concrete factory class and resolved pooled-object type, and `getCreationStackTrace` must return the trace captured when the pool was constructed.

**Management registration.**

- Where JMX is enabled, construction must register the pool under its configured base and prefix using the platform MBean server and `getJmxName` must return the registered `ObjectName`.
- Where JMX is disabled or registration fails, `getJmxName` must return null.
- The registered `GenericObjectPoolMXBean` must expose the same configuration, counters, population estimates, lifecycle totals, closed state, and `listAllObjects` results as direct calls on the pool.
- When a registered pool closes, its management name must be unregistered from the platform MBean server.

## State Model

The core state is a managed set of pooled wrappers partitioned into idle wrappers and active leases, plus a closed flag, configuration snapshot, factory callback history, lifetime statistics, maintenance state, and optional management registration. Public projections include operation results, wrapper state and timestamps, pool counts and statistics, configuration getters, per-object management records, and the MXBean view.

- A managed wrapper must occupy exactly one public lifecycle state at an instant, and an object must not be leased to two callers simultaneously.
- While a wrapper is idle, it must contribute to `getNumIdle` and not to `getNumActive`; while it is allocated, it must contribute to `getNumActive` and not to `getNumIdle`.
- When a wrapper is destroyed, it must cease contributing to active, idle, and `listAllObjects` projections while its destruction remains reflected in lifetime counters.
- The pool configuration getters must reflect the copied construction or latest `setConfig` values, except that effective `minIdle` must not exceed `maxIdle`.
- While the pool is closed, `isClosed` must return true, the idle projection must remain empty after cleanup, and no new borrow or add operation must succeed.

## Error Semantics

| Condition | Required result |
|---|---|
| Null factory passed to a pool constructor | If a null factory is supplied, then the constructor must raise `IllegalArgumentException`. |
| Factory creation returns null | If factory creation returns null, then the creating operation must raise `NullPointerException`. |
| Borrow or add invoked after close | If borrow or add is invoked after close, then the operation must raise `IllegalStateException`. |
| Exhausted non-blocking pool, or exhausted blocking pool after its finite wait | If the applicable exhaustion condition holds, then `borrowObject` must raise `NoSuchElementException`. |
| Newly created wrapper fails activation or configured validation | If a newly created wrapper fails activation or configured validation, then `borrowObject` must raise `NoSuchElementException`. |
| Unknown object returned or invalidated without abandonment handling | If an unknown object is returned or invalidated without abandonment handling, then the operation must raise `IllegalStateException`. |
| Same object returned more than once without abandonment handling | If the same object is returned more than once without abandonment handling, then `returnObject` must raise `IllegalStateException`. |
| Eviction policy class name does not resolve to an instantiable `EvictionPolicy` | If a policy class name does not resolve to an instantiable `EvictionPolicy`, then `setEvictionPolicyClassName` must raise `IllegalArgumentException`. |
| Management registration failure | If management registration fails, then construction must continue and `getJmxName` must return null. |

## Cross-View Invariants

1. A successful borrow must move exactly one wrapper from idle-or-new into active, increment `getBorrowedCount`, update that wrapper's borrowed count and state, and appear consistently in `listAllObjects` and the MXBean view.
2. A successful return retained by the pool must move exactly one wrapper from active to idle, increment `getReturnedCount`, update its last-return instant, and preserve it in `listAllObjects`.
3. Invalidation, validation rejection, eviction, abandonment, idle overflow, and close cleanup must remove the affected wrapper from population projections and increment destruction totals through the corresponding reason-specific view.
4. LIFO or FIFO ordering selected through configuration or a setter must govern subsequent idle borrows and must be reported identically by the direct getter and MXBean projection.
5. Capacity changes through `maxTotal`, `maxIdle`, and `minIdle` must constrain borrow creation, return retention, and maintenance replenishment while their effective values remain visible through direct and management getters.
6. Validation flags must govern factory callback history at create, borrow, return, and maintenance boundaries, and each rejection must produce the matching population and counter changes.
7. Closing a pool must synchronize the operation view, closed flag, idle population, waiting borrowers, destruction counters, and management registration without preventing cleanup of outstanding leases.
8. Abandonment detection must use the wrapper's last-used projection, destroy with `DestroyMode.ABANDONED`, update population and destruction views, and tolerate a later client return of the removed object.

## Public Interface

### Import Surface

```java
import org.apache.commons.pool3.ObjectPool;
import org.apache.commons.pool3.PooledObjectFactory;
import org.apache.commons.pool3.BasePooledObjectFactory;
import org.apache.commons.pool3.PooledObject;
import org.apache.commons.pool3.PooledObjectState;
import org.apache.commons.pool3.DestroyMode;
import org.apache.commons.pool3.TrackedUse;
import org.apache.commons.pool3.UsageTracking;
import org.apache.commons.pool3.SwallowedExceptionListener;
```

```java
import org.apache.commons.pool3.impl.BaseObjectPoolConfig;
import org.apache.commons.pool3.impl.GenericObjectPoolConfig;
import org.apache.commons.pool3.impl.GenericObjectPool;
import org.apache.commons.pool3.impl.GenericObjectPoolMXBean;
import org.apache.commons.pool3.impl.AbandonedConfig;
import org.apache.commons.pool3.impl.EvictionConfig;
import org.apache.commons.pool3.impl.EvictionPolicy;
import org.apache.commons.pool3.impl.DefaultEvictionPolicy;
import org.apache.commons.pool3.impl.DefaultPooledObject;
import org.apache.commons.pool3.impl.DefaultPooledObjectInfo;
import org.apache.commons.pool3.impl.DefaultPooledObjectInfoMBean;
```

### Public Members

| Type | Public members in scope |
|---|---|
| `ObjectPool` | `addObject`, `addObjects`, `borrowObject`, `clear`, `close`, `getNumActive`, `getNumIdle`, `invalidateObject`, `returnObject` |
| `PooledObjectFactory` | `activateObject`, `destroyObject`, `makeObject`, `passivateObject`, `validateObject` |
| `BasePooledObjectFactory` | constructor, `activateObject`, `create`, `destroyObject`, `makeObject`, `passivateObject`, `validateObject`, `wrap` |
| `PooledObject` | `allocate`, `deallocate`, `getActiveDuration`, `getBorrowedCount`, `getCreateInstant`, `getFullDuration`, `getIdleDuration`, `getLastBorrowInstant`, `getLastReturnInstant`, `getLastUsedInstant`, `getObject`, `getState`, `invalidate`, `markAbandoned`, `markReturning`, `startEvictionTest`, `use` |
| `PooledObjectState` | `IDLE`, `ALLOCATED`, `EVICTION`, `EVICTION_RETURN_TO_HEAD`, `VALIDATION`, `VALIDATION_PREALLOCATED`, `VALIDATION_RETURN_TO_HEAD`, `INVALID`, `ABANDONED`, `RETURNING` |
| `DestroyMode` | `NORMAL`, `ABANDONED` |
| `TrackedUse` | `getLastUsedInstant` |
| `UsageTracking` | `use` |
| `SwallowedExceptionListener` | `onSwallowException` |
| `BaseObjectPoolConfig` | public `DEFAULT_*` constants; getters and setters for `blockWhenExhausted`, detailed statistics, eviction interval and policy, fairness, JMX naming, LIFO, maximum wait, hard and soft idle thresholds, eviction sample size, and validation flags |
| `GenericObjectPoolConfig` | `DEFAULT_MAX_TOTAL`, `DEFAULT_MAX_IDLE`, `DEFAULT_MIN_IDLE`, constructor, `clone`, `getMaxTotal`, `setMaxTotal`, `getMaxIdle`, `setMaxIdle`, `getMinIdle`, `setMinIdle` |
| `GenericObjectPool` | three constructors; lifecycle methods from `ObjectPool`; `borrowObject` duration and millisecond overloads; `evict`, `preparePool`, `use`, `listAllObjects`, factory/configuration getters and setters, counter/timing getters, `getNumWaiters`, `getJmxName`, `isClosed`, and abandonment getters/setter |
| `GenericObjectPoolMXBean` | read-only configuration, capacity, lifecycle-counter, timing, waiting, abandonment, closed-state, factory-type, and `listAllObjects` operations corresponding to direct pool accessors |
| `AbandonedConfig` | `DEFAULT_REMOVE_ABANDONED_TIMEOUT_DURATION`, `copy`, constructor, getters and setters for removal triggers, timeout, logging writer, full-stack-trace selection, and usage tracking |
| `EvictionConfig` | `isEvictionThread`, constructor, `getIdleEvictDuration`, `getIdleSoftEvictDuration`, `getMinIdle` |
| `EvictionPolicy` | `evict` |
| `DefaultEvictionPolicy` | constructor, `evict` |
| `DefaultPooledObject` | constructor and all `PooledObject` operations |
| `DefaultPooledObjectInfo` | constructor, all `DefaultPooledObjectInfoMBean` getters, `pooledObject` |
| `DefaultPooledObjectInfoMBean` | `getBorrowedCount`, `getCreateTime`, `getCreateTimeFormatted`, `getLastBorrowTime`, `getLastBorrowTimeFormatted`, `getLastBorrowTrace`, `getLastReturnTime`, `getLastReturnTimeFormatted`, `getPooledObjectToString`, `getPooledObjectType` |

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `ObjectPool` | interface | Defines non-keyed borrow, return, invalidation, preload, cleanup, and population operations. |
| `PooledObjectFactory` | interface | Supplies creation and lifecycle callbacks for wrapped values. |
| `BasePooledObjectFactory` | abstract class | Supplies no-op lifecycle defaults around caller-defined creation and wrapping. |
| `PooledObject` | interface | Exposes a wrapped value with lifecycle state, timestamps, and transition operations. |
| `PooledObjectState` | enum | Names the observable states of a pooled wrapper. |
| `DestroyMode` | enum | Distinguishes normal destruction from abandonment recovery. |
| `TrackedUse` | interface | Supplies a last-use instant from a pooled value. |
| `UsageTracking` | interface | Accepts client-reported uses of a borrowed value. |
| `SwallowedExceptionListener` | interface | Receives exceptions the pool cannot propagate. |
| `BaseObjectPoolConfig` | abstract class | Holds configuration shared by generic pool types. |
| `GenericObjectPoolConfig` | class | Holds the copied configuration for a non-keyed generic pool. |
| `GenericObjectPool` | class | Implements the configurable, thread-safe non-keyed pool. |
| `GenericObjectPoolMXBean` | interface | Defines the pool's management projection. |
| `AbandonedConfig` | class | Configures detection, logging, and removal of abandoned leases. |
| `EvictionConfig` | class | Carries immutable threshold values to an eviction policy. |
| `EvictionPolicy` | interface | Decides whether an idle wrapper is evicted. |
| `DefaultEvictionPolicy` | class | Applies hard and soft idle-duration eviction rules. |
| `DefaultPooledObject` | class | Provides the standard thread-safe pooled wrapper. |
| `DefaultPooledObjectInfo` | class | Projects one managed wrapper into management-friendly values. |
| `DefaultPooledObjectInfoMBean` | interface | Defines per-wrapper management attributes. |

### CLI Entry Points

There is no console script for this package. Java callers use the library through Maven dependencies and Java imports.

## Appendix A: Environment

The working environment runs Java 17 on Linux without network access. The Java standard library is available; no third-party runtime library beyond the target artifact is guaranteed to the implementation. The assessment environment provides the same JDK and offline execution policy.

The project must provide a Maven `pom.xml` at its root with coordinate `org.apache.commons:commons-pool3`. Source must compile through the standard Maven lifecycle using locally available artifacts.

## Appendix B: Assessment Notes

Assessment exercises public construction and method calls across factory callbacks, wrapper transitions, borrow/return lifecycle, capacity and ordering, validation failures, eviction, abandonment, statistics, and management views. Tests compare observable return values, exception classes, callbacks, state projections, and cross-view consistency; they do not require private field layout, internal helper types, exact diagnostic strings, or a particular synchronization data structure. Assessment outcomes reflect the proportion of independently passing public behavior cases, with integration cases checking that multiple projections remain consistent across complete lifecycles.
