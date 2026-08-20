# HikariCP Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`com.zaxxer:HikariCP` is a Java JDBC connection-pooling library that owns a bounded set of physical database connections and lends temporary `java.sql.Connection` handles through a standard `DataSource` interface. Configuration determines physical-connection creation, borrowed-connection defaults, capacity, validation, lifetime, timeout, observability, and management behavior.

The same live pool state is projected through JDBC acquisition and close behavior, `HikariPoolMXBean` counters and controls, `HikariConfigMXBean` runtime settings, metrics callbacks and registries, and data-source lifecycle queries.

## Non-Goals

- This specification does not require XA transaction management or a pooling-layer prepared-statement cache.
- This specification does not require the deprecated Hibernate connection-provider integration.
- This specification does not require a PostgreSQL service, containerized database, remote network service, or runtime dependency download.
- This specification does not define contracts for generated JDBC proxies, pool-engine implementation types, general-purpose helper types other than `Credentials`, or concrete tracker implementations created behind public metrics factories.
- This specification does not require test-only carriers, package-private members, reflection-visible fields, generated proxy class shape, scheduler thread counts, exact log text, exact exception messages, or object representations.
- This specification does not require unsupported secret system properties or command-line entry points.

## Representative Workflows

The first workflow configures and starts a local pool eagerly, borrows a connection, observes management counters, and closes the pool.

```java
import java.sql.Connection;
import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariDataSource;
import com.zaxxer.hikari.HikariPoolMXBean;
import org.h2.jdbcx.JdbcDataSource;

JdbcDataSource jdbc = new JdbcDataSource();
jdbc.setURL("jdbc:h2:mem:orders;DB_CLOSE_DELAY=-1");

HikariConfig config = new HikariConfig();
config.setDataSource(jdbc);
config.setPoolName("orders");
config.setMaximumPoolSize(4);
config.setMinimumIdle(1);

try (HikariDataSource dataSource = new HikariDataSource(config);
     Connection connection = dataSource.getConnection()) {
    HikariPoolMXBean pool = dataSource.getHikariPoolMXBean();
    System.out.println(pool.getActiveConnections());
}
```

The configured source must be copied into the data source, construction must start the pool, borrowing must project one active logical handle, closing that handle must recycle its physical connection, and closing the data source must shut the pool down.

The second workflow uses lazy startup, runtime management, and a custom metrics extension.

```java
import java.sql.Connection;
import com.zaxxer.hikari.HikariDataSource;
import com.zaxxer.hikari.metrics.IMetricsTracker;

HikariDataSource dataSource = new HikariDataSource();
dataSource.setJdbcUrl("jdbc:h2:mem:metrics");
dataSource.setUsername("sa");
dataSource.setMetricsTrackerFactory((poolName, stats) -> new IMetricsTracker() {
    @Override
    public void recordConnectionTimeout() {
        System.out.println(poolName + " timed out; total=" + stats.getTotalConnections());
    }
});

try (Connection ignored = dataSource.getConnection()) {
    dataSource.getHikariConfigMXBean().setMaximumPoolSize(6);
}
dataSource.close();
```

The first borrow must validate configuration and start the lazy pool; the management view must change an allowed live setting; and the custom tracker must receive lifecycle measurements tied to the same pool identity and statistics.

## Configuration and Validation

Configuration defines the connection source and policy that become fixed when a pool starts.

**Construction and property loading.**

- The no-argument `HikariConfig` constructor must create an unsealed configuration with documented defaults: `autoCommit=true`, `readOnly=false`, `connectionTimeout=30000`, `validationTimeout=5000`, `idleTimeout=600000`, `keepaliveTime=120000`, `maxLifetime=1800000`, `leakDetectionThreshold=0`, `initializationFailTimeout=1`, `maximumPoolSize=10`, `allowPoolSuspension=false`, `registerMbeans=false`, and `isolateInternalQueries=false`.
- WHEN `minimumIdle` is not explicitly set, THEN validation must set it to `maximumPoolSize` so the default is a fixed-size pool.
- WHEN `HikariConfig(Properties)` is constructed, THEN matching JavaBean property names must populate the same configuration values as their setters, and names prefixed with `dataSource.` must populate data-source properties.
- WHEN `HikariConfig(String)` is constructed, THEN it must load the named filesystem properties file first and otherwise a classpath resource with that name.
- IF the named property resource does not exist, THEN `HikariConfig(String)` must raise `IllegalArgumentException`.
- WHEN `copyStateTo(other)` is called, THEN it must copy the current configuration values into `other`, and `other` must remain unsealed.

**Connection source selection.**

- The configuration must select one effective physical-connection source in this precedence order: `dataSource`, `dataSourceClassName`, `jdbcUrl`, then `dataSourceJNDI`; `driverClassName` must only refine `jdbcUrl` mode.
- WHEN `dataSource` is set, THEN the pool must wrap that instance and ignore `dataSourceClassName` and data-source construction properties.
- WHEN `dataSourceClassName` and `jdbcUrl` are both set without an explicit `dataSource`, THEN the pool must use `dataSourceClassName` and ignore `jdbcUrl`.
- IF `dataSourceClassName` and `driverClassName` are both set, THEN validation must raise `IllegalStateException`.
- IF `driverClassName` is set without `jdbcUrl`, THEN validation must raise `IllegalArgumentException`.
- IF none of `dataSource`, `dataSourceClassName`, `dataSourceJNDI`, or `jdbcUrl` supplies a source, THEN validation must raise `IllegalArgumentException`.
- WHEN `addDataSourceProperty(propertyName, value)` or `setDataSourceProperties(dsProperties)` is used in `DataSource` mode, THEN matching properties must be applied through JavaBean setters on the constructed driver data source.
- WHEN those properties are used in `jdbcUrl` mode, THEN they must be supplied as driver connection properties.

**Credentials and connection defaults.**

- The `username`, `password`, and `Credentials` accessors must represent one atomic credential pair, and `Credentials.of(username, password)` and the public constructor must create an immutable pair exposed through `getUsername` and `getPassword`.
- WHERE a `HikariCredentialsProvider` is configured, the pool must call `getCredentials` when creating a physical connection and must use the returned pair for that creation attempt.
- WHEN credentials change through `HikariConfigMXBean`, THEN the new pair must apply only to later physical connections in `DataSource` mode.
- WHEN a physical connection enters the pool, THEN `autoCommit`, `readOnly`, `catalog`, `schema`, and `transactionIsolation` must establish its borrowed default state; IF the driver rejects a configured default, THEN that physical connection creation attempt must fail.
- IF `transactionIsolation` is not a named `java.sql.Connection` isolation constant or a numeric isolation value, THEN pool startup must raise `IllegalArgumentException`.

**Timing, capacity, and normalization.**

- All timeout and lifetime configuration values must use milliseconds.
- IF `setConnectionTimeout` receives a value below 250 other than zero, THEN it must raise `IllegalArgumentException`; WHEN it receives zero, THEN it must represent an effectively unbounded wait.
- IF `setValidationTimeout` receives a value below 250, THEN it must raise `IllegalArgumentException`.
- IF `setIdleTimeout` receives a negative value, THEN it must raise `IllegalArgumentException`.
- IF `setMaximumPoolSize` receives a value below one or `setMinimumIdle` receives a negative value, THEN it must raise `IllegalArgumentException`.
- WHEN validation sees `minimumIdle` greater than `maximumPoolSize`, THEN it must reduce `minimumIdle` to `maximumPoolSize`.
- WHEN a resizable pool has a nonzero `idleTimeout` below 10000, THEN validation must restore the 600000 millisecond default; WHEN `idleTimeout` is within one second of or greater than an enabled `maxLifetime`, THEN validation must disable idle retirement by setting `idleTimeout` to zero.
- WHEN a nonzero `maxLifetime` is below 30000, THEN validation must restore the 1800000 millisecond default.
- WHEN a nonzero `keepaliveTime` is below 30000 or is not less than an enabled `maxLifetime`, THEN validation must disable keepalive by setting it to zero.
- WHEN a positive `leakDetectionThreshold` is below 2000 or exceeds an enabled `maxLifetime`, THEN validation must disable leak detection by setting it to zero.
- WHEN `poolName` is absent, THEN validation must assign a nonempty process-unique pool name; IF JMX registration is enabled and `poolName` contains a colon, THEN validation must raise `IllegalArgumentException`.

**Startup-only and live settings.**

- WHEN a `HikariDataSource` starts, THEN startup-only setters inherited from `HikariConfig` must become sealed and later calls to those setters must raise `IllegalStateException`.
- WHILE a pool is running, the `HikariConfigMXBean` setters for `connectionTimeout`, `validationTimeout`, `idleTimeout`, `leakDetectionThreshold`, `maxLifetime`, `minimumIdle`, `maximumPoolSize`, `username`, `password`, `Credentials`, and `catalog` must remain available.
- WHEN `setMetricsTrackerFactory` has selected a factory, THEN `setMetricRegistry` must raise `IllegalStateException`; WHEN `setMetricRegistry` has selected a registry, THEN `setMetricsTrackerFactory` must raise `IllegalStateException`.
- IF `setMetricRegistry` receives an object other than a supported Dropwizard or Micrometer registry, THEN it must raise `IllegalArgumentException`.
- IF `setHealthCheckRegistry` receives an object other than a Dropwizard `HealthCheckRegistry`, THEN it must raise `IllegalArgumentException`.

## Pool Startup and Acquisition

Pool startup and acquisition turn validated policy into bounded, observable connection ownership.

**Eager and lazy startup.**

- WHEN `HikariDataSource(HikariConfig)` is constructed, THEN it must validate and copy the supplied configuration, start the pool eagerly, and seal only the copied data-source configuration.
- WHEN the no-argument `HikariDataSource` is constructed, THEN it must remain unstarted and configurable until the first `getConnection` call validates, starts, and seals it.
- WHILE the lazy data source is unstarted, `getHikariPoolMXBean` must return null, `getHikariConfigMXBean` must return the data source itself, and `isRunning` must return false.
- WHEN `initializationFailTimeout` is positive, THEN startup must wait for an initial physical connection after applying acquisition and validation timeouts and must raise a runtime initialization failure if no usable connection is created within the configured interval.
- WHEN `initializationFailTimeout` is zero, THEN startup must validate a physical connection when one is obtainable, must fail on setup or validation failure, and must continue starting when no connection is obtainable.
- WHEN `initializationFailTimeout` is negative, THEN startup must skip the initial connection attempt and continue physical connection creation in the background.

**Borrowing and saturation.**

- WHEN an idle valid physical connection exists, THEN `getConnection()` must return a logical `Connection` handle and move that physical connection from the idle projection to the active projection.
- WHEN no idle connection exists and the total is below `maximumPoolSize`, THEN the pool must create physical connections until demand and `minimumIdle` policy are satisfied without exceeding `maximumPoolSize`.
- WHILE total connections equal `maximumPoolSize` and no idle connection exists, a caller must wait for at most `connectionTimeout` milliseconds for a returned connection.
- IF no connection becomes available before `connectionTimeout`, THEN `getConnection()` must raise `SQLTransientConnectionException` and the metrics tracker must receive a timeout event.
- IF a thread is interrupted while waiting for a connection, THEN `getConnection()` must restore the thread interrupt flag and raise `SQLException`.
- IF `HikariDataSource` has been closed, THEN `getConnection()` must raise `SQLException`.
- IF `getConnection(username, password)` is called, THEN the data source must raise `SQLFeatureNotSupportedException`.

**DataSource delegation and wrapping.**

- WHEN the pool has started, THEN `getLogWriter`, `setLogWriter`, `getLoginTimeout`, and `setLoginTimeout` must delegate to the wrapped physical data source; WHILE it is unstarted, getters must return null or zero and setters must have no effect.
- WHEN `unwrap(iface)` names a type implemented by the pool data source or wrapped physical data source, THEN it must return the matching instance; OTHERWISE it must delegate to the wrapped source and ultimately raise `SQLException` if no matching wrapper exists.
- WHEN `isWrapperFor(iface)` names a type implemented by the pool data source or wrapped physical data source, THEN it must return true; OTHERWISE it must return the wrapped source result or false before startup.
- IF `getParentLogger()` is called, THEN the data source must raise `SQLFeatureNotSupportedException`.

## Borrowed Connection Lifecycle

Borrowed handles preserve JDBC behavior while returning clean physical connections to shared state.

**Close and reset.**

- WHEN a borrowed logical connection is closed, THEN it must close tracked open statements, cancel its leak timer, clear warnings, and recycle or evict the physical connection exactly once.
- WHEN application code changes read-only, auto-commit, transaction isolation, catalog, schema, or network timeout on a borrowed connection, THEN close must restore each changed setting to the configured pool default before recycling.
- WHEN non-auto-commit work has changed transaction state and the borrower closes without commit or rollback, THEN close must roll back that work before recycling.
- WHEN a borrowed connection is closed, THEN later operations on that logical handle must observe a closed connection and must not operate on a physical connection borrowed by another caller.
- IF cleanup of tracked statements or connection state raises a fatal `SQLException`, THEN the pool must evict that physical connection rather than return it to idle state.

**Lifetime, validation, and leak policy.**

- WHEN `maxLifetime` is positive and an idle physical connection reaches its scheduled lifetime, THEN the pool must retire it; WHILE that connection is active, retirement must wait until it is returned.
- WHEN `idleTimeout` is positive and `minimumIdle` is below `maximumPoolSize`, THEN an idle connection must not be retired before the configured timeout and the pool must not retire below `minimumIdle`.
- WHEN `keepaliveTime` is positive, THEN only idle connections must be removed briefly, validated through JDBC `isValid` or `connectionTestQuery`, and returned or replaced.
- WHEN `connectionInitSql` is configured, THEN every newly created physical connection must execute it before entering the pool; IF execution fails, THEN that creation attempt must be treated as a connection failure.
- WHEN `connectionTestQuery` is absent, THEN validation must use JDBC `Connection.isValid`; WHERE `connectionTestQuery` is present, validation must execute that query.
- WHERE `isolateInternalQueries=true` and `autoCommit=false`, internal validation queries must run in an isolated transaction.
- WHEN a borrowed connection remains active longer than an enabled `leakDetectionThreshold`, THEN the pool must emit a leak observation; WHEN that connection is returned, THEN its leak task must be cancelled.

**SQLException eviction override.**

- WHEN a JDBC operation raises `SQLException`, THEN the pool must pass the exception to a configured `SQLExceptionOverride.adjudicate` before applying built-in broken-connection detection.
- WHEN adjudication returns `CONTINUE_EVICT`, THEN the pool must apply its built-in SQL-state and error-code policy.
- WHEN adjudication returns `DO_NOT_EVICT`, THEN the pool must retain the connection unless another cleanup failure makes reuse unsafe.
- WHEN adjudication returns `MUST_EVICT`, THEN the pool must evict the physical connection regardless of SQL state or error code.
- WHEN no override is configured, THEN `SQLExceptionOverride.adjudicate` must default to `CONTINUE_EVICT` behavior.

## Management and Runtime State

Management views expose point-in-time pool state and controlled lifecycle transitions.

**Counters and views.**

- `getIdleConnections`, `getActiveConnections`, `getTotalConnections`, and `getThreadsAwaitingConnection` must return transient point-in-time counts from the same live pool.
- `getTotalConnections` must never exceed the current `maximumPoolSize`, and each connection must occupy exactly one idle or active ownership state at an instant.
- WHEN a pool is started and neither suspended nor shut down, THEN `HikariDataSource.isRunning` must return true; WHILE it is suspended, unstarted, or shut down, it must return false.

**Eviction, suspension, and resumption.**

- WHEN `softEvictConnections` is called, THEN idle connections must be closed and active connections must be marked for closure when returned.
- WHEN `HikariDataSource.evictConnection(connection)` receives a currently borrowed connection from that data source, THEN the physical connection must be removed immediately; WHEN it receives a returned pooled handle, THEN that physical connection must be marked for later eviction.
- IF `suspendPool` is called while `allowPoolSuspension=false`, THEN it must raise `IllegalStateException`.
- WHEN `suspendPool` is called while suspension is allowed, THEN later `getConnection` calls must wait without applying `connectionTimeout` until `resumePool` is called.
- WHEN `resumePool` is called for a suspended pool, THEN acquisition must resume and the pool must refill toward `minimumIdle`.

**Shutdown and live changes.**

- WHEN `HikariDataSource.close` is called, THEN it must stop acquisition, close idle physical connections, abort or close active physical connections, unregister management projections, and close its metrics tracker.
- WHEN `close` is called more than once, THEN later calls must have no effect and `isClosed` must remain true.
- WHEN live `minimumIdle` or `maximumPoolSize` changes, THEN later fill and acquisition decisions must use the new bounds without invalidating already borrowed logical handles.
- WHEN live credentials change, THEN existing physical connections must retain their original authentication and later physical connection creation must use the new credentials.
- WHEN live `catalog` changes, THEN callers must suspend the pool and evict existing connections before relying on the new catalog across all borrowers.

## Metrics, Health, and Naming Integrations

Integration hooks project the same pool identity, timings, capacity, and health into caller-owned registries.

**Custom metrics.**

- WHEN a `MetricsTrackerFactory` is configured, THEN pool startup must call `create(poolName, poolStats)` once for that pool and use the returned `IMetricsTracker`.
- WHEN physical connection creation completes, logical acquisition completes, a logical connection is returned, or acquisition times out, THEN the tracker must receive `recordConnectionCreatedMillis`, `recordConnectionAcquiredNanos`, `recordConnectionUsageMillis`, or `recordConnectionTimeout` respectively.
- WHEN the pool shuts down, THEN it must call `IMetricsTracker.close`.
- A `PoolStats` instance must expose total, idle, active, pending, maximum, and minimum counts through its named getters.
- WHEN the first stats getter after the configured refresh interval is called, THEN `PoolStats` must invoke `update` once before returning current values; WHILE the refresh interval has not elapsed, later getters must return the cached values.

**Built-in registry adapters.**

- WHEN `CodahaleMetricsTrackerFactory` or `Dropwizard5MetricsTrackerFactory` is constructed with a registry, THEN `getRegistry` must return that same registry and `create` must bind the supplied pool name and stats to it.
- WHEN `MicrometerMetricsTrackerFactory` is constructed with a `MeterRegistry`, THEN `create` must publish acquisition, usage, creation, timeout, and pool-state measurements for the supplied pool name.
- WHEN a Prometheus factory is constructed without a registry, THEN it must use `CollectorRegistry.defaultRegistry`; WHEN constructed with a registry, THEN it must use that registry.
- WHEN `PrometheusMetricsTrackerFactory.create` is used, THEN it must publish summary-style timing metrics and pool-state gauges; WHEN `PrometheusHistogramMetricsTrackerFactory.create` is used, THEN it must publish histogram-style timing metrics and the same pool-state gauges.
- WHEN the final tracker for a Prometheus pool is closed, THEN measurements for that pool name must be removed from the associated collector.

**Health and JNDI.**

- WHERE a Dropwizard `HealthCheckRegistry` is configured, pool startup must register connectivity and optional connectivity-threshold health checks using the configured health-check properties.
- WHEN `HikariJNDIFactory.getObjectInstance` receives a `Reference` whose class name is `javax.sql.DataSource`, THEN it must retain recognized `HikariConfig` properties and `dataSource.` properties and must return a configured pooled data source.
- WHERE the accepted reference includes `dataSourceJNDI`, the factory must look up that underlying `DataSource` and wrap it with the remaining configuration.
- WHEN `getObjectInstance` receives any other object or reference class, THEN it must return null.
- IF an accepted `dataSourceJNDI` reference has no usable naming context or lookup result, THEN factory creation must raise a naming or runtime lookup failure.

## State Model

The core state is one validated configuration plus a bounded ownership set of physical JDBC connections. Each physical connection is creating, idle, active, reserved for validation, marked for eviction, or closed, and each borrowed logical handle refers to at most one active physical connection.

The public projections are JDBC borrow/close and wrapper behavior, data-source lifecycle queries, configuration getters and the live configuration MXBean, pool counters and controls, metrics and health registries, JNDI-created data sources, and physical-source observations.

- WHILE a logical handle is active, its physical connection must contribute to active and total projections and must not contribute to idle projection.
- WHEN that logical handle closes successfully, THEN the same physical connection must move to idle projection after reset or must leave total projection after eviction.
- WHEN configuration changes through an allowed live setter, THEN the configuration MXBean getter and every later affected pool decision must reflect the same value.
- WHEN the pool state changes through start, suspend, resume, or close, THEN `isRunning`, acquisition behavior, management availability, and metrics lifecycle must reflect that transition together.

## Error Semantics

Error outcomes use stable Java exception classes without requiring message text.

| Condition | Required result |
|---|---|
| Missing property file/resource | IF a named configuration resource is missing, THEN construction must raise `IllegalArgumentException`. |
| Invalid source combination or missing source | IF source selection is invalid or absent, THEN validation must raise `IllegalStateException` for `dataSourceClassName` plus `driverClassName`, otherwise `IllegalArgumentException`. |
| Invalid setter bound | IF connection, validation, idle, minimum-idle, or maximum-size setter bounds are violated, THEN the setter must raise `IllegalArgumentException`. |
| Startup-only setter after pool start | IF a sealed startup-only setter is called, THEN it must raise `IllegalStateException`. |
| Unsupported metric or health registry | IF a registry has an unsupported type, THEN its setter must raise `IllegalArgumentException`. |
| Mutually exclusive metric configuration | IF both metric-registry and metrics-factory paths are selected, THEN the second setter must raise `IllegalStateException`. |
| Acquisition timeout | IF no connection becomes available within `connectionTimeout`, THEN `getConnection` must raise `SQLTransientConnectionException`. |
| Acquisition interruption | IF acquisition is interrupted, THEN `getConnection` must restore interruption and raise `SQLException`. |
| Closed data source acquisition | IF `getConnection` is called after close, THEN it must raise `SQLException`. |
| Unsupported credentialed borrow or parent logger | IF credentialed `getConnection` or `getParentLogger` is called, THEN it must raise `SQLFeatureNotSupportedException`. |
| Unsupported unwrap target | IF no wrapped object implements the requested type, THEN `unwrap` must raise `SQLException`. |
| Suspension disabled | IF `suspendPool` is called while suspension is disabled, THEN it must raise `IllegalStateException`. |
| JNDI lookup failure | IF an accepted reference cannot resolve its underlying data source, THEN JNDI creation must raise a naming or runtime lookup failure. |

## Cross-View Invariants

1. A successful `getConnection` must increase or preserve total connections, must project one borrowed handle as active, and must emit acquisition metrics for the same pool name.
2. WHEN a healthy borrowed handle closes, THEN active ownership must decrease, idle ownership must increase or replacement must begin, and usage metrics must be emitted exactly once for that borrow.
3. The values returned by `HikariPoolMXBean` and `PoolStats` must describe the same live pool even when separately sampled values are transient.
4. A `maximumPoolSize` value returned by `HikariConfigMXBean` must bound physical total connections and must determine when later acquisitions wait.
5. A `minimumIdle` value returned by `HikariConfigMXBean` must govern later refill decisions and idle retirement without forcing active connections closed.
6. WHEN soft eviction is requested through the pool MXBean or explicit eviction is requested through the data source, THEN the selected physical connections must be removed from later idle reuse and from total metrics after closure completes.
7. WHEN a pool is suspended, THEN `isRunning` must become false and later acquisition must block without timeout; WHEN it is resumed, THEN `isRunning` must become true and waiting acquisition must be released.
8. WHEN the data source closes, THEN `isClosed` must become true, `isRunning` must become false, later acquisition must fail, management registration must end, and the metrics tracker must close.
9. A credential pair returned by `HikariConfig.getCredentials` must agree with username/password accessors and must be the pair used for later physical `DataSource.getConnection(username, password)` creation when no provider overrides it.
10. A pool produced by `HikariJNDIFactory` must expose the same configuration, acquisition, management, metrics, reset, and shutdown behavior as a directly constructed `HikariDataSource`.

## Public Interface

### Import Surface

```java
import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariConfigMXBean;
import com.zaxxer.hikari.HikariCredentialsProvider;
import com.zaxxer.hikari.HikariDataSource;
import com.zaxxer.hikari.HikariJNDIFactory;
import com.zaxxer.hikari.HikariPoolMXBean;
import com.zaxxer.hikari.SQLExceptionOverride;
import com.zaxxer.hikari.metrics.IMetricsTracker;
import com.zaxxer.hikari.metrics.MetricsTrackerFactory;
import com.zaxxer.hikari.metrics.PoolStats;
import com.zaxxer.hikari.metrics.dropwizard.CodahaleMetricsTrackerFactory;
import com.zaxxer.hikari.metrics.dropwizard.Dropwizard5MetricsTrackerFactory;
import com.zaxxer.hikari.metrics.micrometer.MicrometerMetricsTrackerFactory;
import com.zaxxer.hikari.metrics.prometheus.PrometheusHistogramMetricsTrackerFactory;
import com.zaxxer.hikari.metrics.prometheus.PrometheusMetricsTrackerFactory;
import com.zaxxer.hikari.util.Credentials;
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `HikariConfig` | class | Holds, validates, copies, and exposes pool configuration. |
| `HikariDataSource` | class | Implements JDBC `DataSource` over a managed connection pool. |
| `HikariConfigMXBean` | interface | Exposes settings that remain mutable for a running pool. |
| `HikariPoolMXBean` | interface | Exposes live counts, eviction, suspension, and resumption. |
| `HikariCredentialsProvider` | interface | Supplies credentials when physical connections are created. |
| `SQLExceptionOverride` | interface | Overrides broken-connection eviction decisions. |
| `SQLExceptionOverride.Override` | enum | Names continue, suppress, and force-eviction decisions. |
| `HikariJNDIFactory` | class | Creates pooled data sources from JNDI references. |
| `Credentials` | class | Holds an immutable username/password pair. |
| `MetricsTrackerFactory` | interface | Creates one metrics tracker for a named pool. |
| `IMetricsTracker` | interface | Receives connection timing, usage, timeout, and close events. |
| `PoolStats` | abstract class | Supplies refresh-cached pool-state values to metrics trackers. |
| `CodahaleMetricsTrackerFactory` | class | Binds a Dropwizard 3 registry to pool metrics. |
| `Dropwizard5MetricsTrackerFactory` | class | Binds a Dropwizard 5 registry to pool metrics. |
| `MicrometerMetricsTrackerFactory` | class | Binds a Micrometer registry to pool metrics. |
| `PrometheusMetricsTrackerFactory` | class | Publishes summary-style Prometheus pool metrics. |
| `PrometheusHistogramMetricsTrackerFactory` | class | Publishes histogram-style Prometheus pool metrics. |

### Public Members

| Name | Kind | Role |
|---|---|---|
| `HikariConfig` constructors | constructors | Create default, `Properties`-backed, or named-resource configuration. |
| `HikariConfig` source and driver-property accessors | methods | Select and configure the physical connection source. |
| `HikariConfig` credential accessors | methods | Read or change static and provider-based credentials. |
| `HikariConfig` connection-default accessors | methods | Configure auto-commit, read-only, catalog, schema, and isolation. |
| `HikariConfig` timeout and capacity accessors | methods | Configure acquisition, validation, lifetime, keepalive, leak, idle, startup, and size policy. |
| `HikariConfig` observability and executor accessors | methods | Configure pool identity, JMX, metrics, health, threads, and scheduling. |
| `HikariConfig.validate`, `copyStateTo` | methods | Normalize/validate a configuration and copy it into another instance. |
| `HikariDataSource` constructors | constructors | Create a lazy data source or eagerly start from copied configuration. |
| `HikariDataSource.getConnection` | methods | Borrow a logical pooled connection or report an acquisition failure. |
| `HikariDataSource` standard `DataSource` methods | methods | Delegate logging/timeouts and implement wrapper queries. |
| `HikariDataSource.isRunning`, `isClosed`, `close` | methods | Query and control pool lifecycle. |
| `HikariDataSource.getHikariPoolMXBean`, `getHikariConfigMXBean`, `evictConnection` | methods | Expose management views and explicit connection eviction. |
| `HikariConfigMXBean` getters and setters | methods | Read or update the documented live configuration subset. |
| `HikariPoolMXBean` count getters | methods | Return idle, active, total, and waiting-thread snapshots. |
| `HikariPoolMXBean.softEvictConnections`, `suspendPool`, `resumePool` | methods | Evict and control acquisition availability. |
| `HikariCredentialsProvider.getCredentials` | method | Return the credential pair for physical connection creation. |
| `SQLExceptionOverride.adjudicate` | method | Return one eviction decision for a JDBC exception. |
| `SQLExceptionOverride.Override` constants | enum members | Represent default, no-evict, and must-evict results. |
| `Credentials.of` and constructor | factories | Create immutable credential pairs. |
| `Credentials.getUsername`, `getPassword` | methods | Return credential components. |
| `MetricsTrackerFactory.create` | method | Create a tracker from pool identity and stats. |
| `IMetricsTracker` recorder methods and `close` | methods | Receive pool measurements and lifecycle completion. |
| `PoolStats` constructor and count getters | members | Configure refresh caching and return six pool-state values. |
| Built-in metrics factory constructors and `create` | members | Bind a supported registry and create a tracker. |
| Dropwizard factory `getRegistry` | methods | Return the bound registry. |
| `HikariJNDIFactory.getObjectInstance` | method | Convert an accepted JNDI reference into a pooled data source. |

### CLI Entry Points

There is no console script for this package. `java -jar HikariCP.jar` is not supported. Programmatic use is through Java imports.

## Appendix A: Environment

The working environment runs JDK 17 and Maven 3.9 on Linux inside Docker without network access. The local Maven repository contains `org.slf4j:slf4j-api:2.0.17`, `com.h2database:h2:2.3.232`, `junit:junit:4.13.2`, `org.mockito:mockito-core:3.7.7`, `org.javassist:javassist:3.29.2-GA`, `io.dropwizard.metrics:metrics-core:3.2.5`, `io.dropwizard.metrics:metrics-healthchecks:3.2.5`, `io.dropwizard.metrics5:metrics-core:5.0.0-rc17`, `io.micrometer:micrometer-core:1.5.4`, and `io.prometheus:simpleclient:0.16.0`, together with their cached transitive dependencies. The assessment environment provides the same Linux container, JDK, Maven tooling, and dependency cache. The target artifact is not preinstalled, and dependency downloads are unavailable.

The project program file must be a root `pom.xml`. It must declare Maven coordinates `com.zaxxer:HikariCP`, compile main sources for Java 11 compatibility while running under the provided JDK, and produce the library classes through the normal Maven lifecycle.

## Appendix B: Assessment Notes

Automated checks exercise public Java APIs with a local in-memory JDBC data source and caller-owned registries. Checks cover configuration defaults and validation, eager and lazy startup, bounded acquisition and timeout behavior, connection cleanup and reset, exception-driven eviction, live MXBean projections, suspension and shutdown, metrics callbacks, JNDI construction, and consistency across views. Each independent check contributes equally. Private fields, package-private methods, generated proxy class shape, exact logs, exact exception text, and external services are not inspected.

