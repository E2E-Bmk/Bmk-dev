# Commons DBCP Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`commons-dbcp2` is a Java JDBC connection-pooling library that creates physical database connections, lends guarded logical `java.sql.Connection` handles through `javax.sql.DataSource`, and recycles those connections under configurable capacity, validation, maintenance, and lifetime policies.

The same live pool state is projected through borrowed JDBC connections and statements, `BasicDataSource` configuration and lifecycle methods, active and idle counts, optional prepared-statement reuse, and the read-only `DataSourceMXBean` management view.

## Non-Goals

- This specification does not require managed or XA transactions, JTA coordination, per-user pools, shared cross-user pools, `ConnectionPoolDataSource` adapters, or JNDI object-factory deployment.
- This specification does not require the registered JDBC `PoolingDriver` access path; local callers use `DataSource` objects.
- This specification does not define contracts for private or package-private helpers, internal pool fields, statement-key representation, wrapper subclass layout, or synchronization strategy.
- This specification does not require external database servers, naming servers, remote services, or runtime dependency downloads.
- This specification does not define exact log text, exception-message text, JMX object-name formatting, stack-trace formatting, or object representations.
- This specification does not require deprecated aliases except the millisecond and integer-second accessors explicitly listed in the Public Interface.

## Representative Workflows

The first workflow configures a local JDBC pool, borrows a logical connection, observes its active projection, commits work, and returns the handle.

```java
import java.sql.Connection;
import java.sql.Statement;
import org.apache.commons.dbcp2.BasicDataSource;

BasicDataSource dataSource = new BasicDataSource();
dataSource.setUrl("jdbc:h2:mem:orders;DB_CLOSE_DELAY=-1");
dataSource.setUsername("sa");
dataSource.setMaxTotal(4);
dataSource.setInitialSize(1);
dataSource.setDefaultAutoCommit(false);

try (Connection connection = dataSource.getConnection();
     Statement statement = connection.createStatement()) {
    statement.executeUpdate("create table if not exists orders(id int primary key)");
    connection.commit();
    assert dataSource.getNumActive() == 1;
}

assert dataSource.getNumActive() == 0;
assert dataSource.getNumIdle() >= 1;
dataSource.close();
```

WHEN the first borrow occurs, THEN it must initialize the source and pool, the checked-out handle must contribute to the active count, `Connection.close()` must return a reusable physical connection, and `BasicDataSource.close()` must close the remaining idle pool state.

The second workflow assembles the lower-level public factories, enables statement pooling, and exposes the pool through `PoolingDataSource`.

```java
import java.sql.Connection;
import java.sql.PreparedStatement;
import org.apache.commons.dbcp2.ConnectionFactory;
import org.apache.commons.dbcp2.DriverManagerConnectionFactory;
import org.apache.commons.dbcp2.PoolableConnection;
import org.apache.commons.dbcp2.PoolableConnectionMXBean;
import org.apache.commons.dbcp2.PoolableConnectionFactory;
import org.apache.commons.dbcp2.PoolingDataSource;
import org.apache.commons.pool2.impl.GenericObjectPool;

ConnectionFactory physical =
    new DriverManagerConnectionFactory("jdbc:h2:mem:statements", "sa", "");
PoolableConnectionFactory lifecycle = new PoolableConnectionFactory(physical, null);
lifecycle.setPoolStatements(true);
lifecycle.setMaxOpenPreparedStatements(8);
GenericObjectPool<PoolableConnection> pool = new GenericObjectPool<>(lifecycle);
lifecycle.setPool(pool);

try (PoolingDataSource<PoolableConnection> dataSource = new PoolingDataSource<>(pool);
     Connection connection = dataSource.getConnection();
     PreparedStatement statement = connection.prepareStatement("select 1")) {
    statement.executeQuery().close();
}
```

WHEN the lower-level workflow runs, THEN the lifecycle factory must create and validate pooled connections, the data source must guard each borrowed handle, and closing a pooled prepared statement must return it to its per-connection statement pool instead of closing its physical statement.

## Connection Sources and Configuration

This section defines how physical JDBC connections and pool policy are selected before the first pool initialization.

**Physical connection factories.**

- WHEN `ConnectionFactory.createConnection()` is called, THEN the selected factory must return one new physical JDBC connection or raise `SQLException` from the underlying source.
- WHEN `DriverManagerConnectionFactory` is constructed with only `connectionUri`, THEN `createConnection()` must call `DriverManager` without explicit credentials.
- WHEN `DriverManagerConnectionFactory` is constructed with `connectionUri` and `properties`, THEN `createConnection()` must pass that properties object to `DriverManager`.
- WHEN `DriverManagerConnectionFactory` is constructed with `connectionUri`, `userName`, and `userPassword`, THEN `createConnection()` must pass the credential pair explicitly and the factory must defensively copy a character-array password.
- WHEN `DriverConnectionFactory` is constructed with `driver`, `connectString`, and `properties`, THEN `createConnection()` must return the result of that driver's `connect` operation with the same connection string and properties.
- WHEN `DataSourceConnectionFactory` has no credential pair, THEN `createConnection()` must call the wrapped source's no-argument `getConnection()`; WHEN it has a credential pair, THEN it must call the credential overload and defensively copy a character-array password.

**Basic data-source initialization.**

- WHEN a new `BasicDataSource` is constructed, THEN it must default `initialSize` to 0, `maxTotal` and `maxIdle` to 8, `minIdle` to 0, `maxWaitDuration` to an indefinite wait, and `lifo` to true.
- WHEN a new `BasicDataSource` is constructed, THEN it must default `testOnBorrow` to true, the other three validation switches to false, periodic eviction and maximum connection lifetime to disabled, and `validationQuery` to absent.
- WHEN a new `BasicDataSource` is constructed, THEN it must default `poolPreparedStatements` and `clearStatementPoolOnReturn` to false, `maxOpenPreparedStatements` to unlimited, and `accessToUnderlyingConnectionAllowed` to false.
- WHEN a new `BasicDataSource` is constructed, THEN it must default `cacheState`, `autoCommitOnReturn`, `rollbackOnReturn`, `logExpiredConnections`, and `registerConnectionMBean` to true, while abandoned-removal switches, abandoned logging, abandoned usage tracking, and `fastFailValidation` must default to false.
- WHEN connection defaults are not explicitly set, THEN auto-commit, read-only, catalog, schema, transaction isolation, and statement query timeout must remain at the JDBC driver's defaults.
- WHEN an unstarted `BasicDataSource` first receives `getConnection()`, `start()`, `getLogWriter()`, or `setLogWriter()`, THEN it must initialize at most one pool from the current startup configuration.
- WHEN `initialSize` is positive at initialization, THEN the data source must create that many idle connections subject to the configured pool limits; IF any required initial connection cannot be created, THEN initialization must raise `SQLException` and must close the partially created pool.
- WHEN `driver` is set, THEN the data source must use that instance; OTHERWISE, WHEN `driverClassName` is set, THEN it must load that class using `driverClassLoader` when supplied and the available application class loaders otherwise; OTHERWISE it must resolve a driver through `DriverManager` from `url`.
- IF neither a usable `driver`, loadable `driverClassName`, nor resolvable `url` supplies a JDBC driver, THEN pool initialization must raise `SQLException`.
- WHEN `username`, `password`, or entries added through `addConnectionProperty` are configured before initialization, THEN newly created physical connections must receive those values; WHEN these startup values change after initialization, THEN the running pool must retain its existing physical-connection factory until `restart()`.
- WHEN `connectionInitSqls` is configured, THEN every newly created physical connection must execute the SQL strings once in iteration order before entering the pool; IF an initialization statement fails, THEN that physical connection creation must fail.

**Property-based construction.**

- WHEN `BasicDataSourceFactory.createDataSource(properties)` is called, THEN recognized Java properties must configure the corresponding `BasicDataSource` values and the method must return an unstarted data source.
- WHEN the factory parses `defaultTransactionIsolation`, THEN it must set `NONE`, `READ_COMMITTED`, `READ_UNCOMMITTED`, `REPEATABLE_READ`, `SERIALIZABLE`, or an integer isolation value; IF the token is unknown and non-integer, THEN it must ignore that token and retain the `-1` driver-default sentinel without raising `SQLException`.
- WHEN the factory parses `connectionProperties`, THEN semicolon-delimited `name=value` entries must be added as driver properties; entries named `user` or `password` must not replace the explicit `username` and `password` properties.
- WHEN the factory parses duration properties, THEN `maxWaitMillis`, eviction intervals, and maximum connection lifetime must use milliseconds, while validation-query timeout, abandoned timeout, and default statement-query timeout must use seconds.

## Capacity, Borrowing, and Maintenance

This section defines bounded logical acquisition and the maintenance policies visible through pool counts and connection availability.

**Capacity and borrowing.**

- WHEN an idle valid connection exists, THEN `getConnection()` must return a new guarded logical handle and move one connection from the idle projection to the active projection.
- WHEN no idle connection exists and the total is below `maxTotal`, THEN `getConnection()` must create a physical connection and must not exceed `maxTotal`; a negative `maxTotal` must represent no fixed total limit.
- WHILE no connection is available at the total limit, a borrower must wait for at most `maxWaitDuration`; WHEN the duration is negative, THEN the wait must be indefinite.
- IF no connection becomes available before a finite maximum wait expires, THEN `getConnection()` must raise `SQLException` with the pool exhaustion as its cause.
- IF a waiting borrower is interrupted, THEN `getConnection()` must restore the thread interrupt status and raise `SQLException`.
- WHEN `setMaxTotal`, `setMaxIdle`, `setMinIdle`, `setMaxWait`, `setLifo`, or an eviction-policy setter is called after startup, THEN the corresponding running-pool policy and its getter must reflect the new value.
- WHEN `lifo` is true, THEN idle borrowing must prefer the most recently returned connection; WHEN it is false, THEN idle borrowing must prefer return order.

**Validation and maintenance.**

- WHERE `testOnCreate` is true, every newly created connection must pass configured validation before becoming available; IF validation fails, THEN creation must fail.
- WHERE `testOnBorrow` is true, every borrowed connection must pass configured validation; IF an idle connection fails, THEN the pool must discard it and continue with another available or creatable connection.
- WHERE `testOnReturn` is true, every returned connection must pass configured validation; IF validation fails, THEN the pool must discard it instead of making it idle.
- WHERE `testWhileIdle` is true and maintenance is enabled, each retained connection selected by an eviction run must pass configured validation; IF validation fails, THEN the pool must discard it.
- WHEN `validationQuery` is absent or empty, THEN validation must call JDBC `Connection.isValid` with the nonnegative `validationQueryTimeout`; WHEN a query is present, THEN validation must execute it and require at least one result row.
- WHERE `fastFailValidation` is true, a pooled connection that previously reported a configured fatal SQL state must fail later validation without calling the JDBC validation operation; SQL states listed by `disconnectionIgnoreSqlCodes` must not be treated as fatal.
- WHEN `durationBetweenEvictionRuns` is positive, THEN periodic maintenance must examine the configured `numTestsPerEvictionRun`; WHEN the duration is zero or negative, THEN periodic maintenance must remain disabled.
- WHEN an idle connection exceeds `minEvictableIdleDuration`, THEN an eviction run must remove it; WHEN it exceeds only `softMinEvictableIdleDuration`, THEN removal must preserve at least `minIdle` idle connections.
- WHEN `maxConnDuration` is positive and a physical connection exceeds it, THEN its next activation, passivation, or validation must fail and the pool must replace it; a zero or negative duration must disable lifetime expiry.
- WHEN `evict()` is called on a started source, THEN it must synchronously run one idle-eviction pass; WHEN the source is unstarted, THEN it must return without creating a pool.

## Borrowed Connection Lifecycle

This section defines the guarded JDBC view, transaction cleanup, state restoration, and explicit invalidation of borrowed connections.

**Guarded handles and close.**

- WHEN a connection is borrowed, THEN the returned handle must implement `java.sql.Connection` and must delegate JDBC operations to one currently owned physical connection.
- WHEN a borrowed handle is closed for the first time, THEN it must close its tracked open statements, restore configured state, and return or invalidate the physical connection exactly once; WHEN the same handle is closed again, THEN the call must have no effect.
- WHILE a logical handle is closed, JDBC operations that require an open connection must raise `SQLException` and must not reach a physical connection later lent to another caller.
- WHEN `accessToUnderlyingConnectionAllowed` is false, THEN `DelegatingConnection.getDelegate()` and `getInnermostDelegate()` obtained through a guarded data-source connection must return null; WHEN it is true, THEN those methods must return the corresponding delegate.
- WHEN `unwrap(iface)` or `isWrapperFor(iface)` names a supported wrapper type, THEN the data source or connection must return the matching result; IF `unwrap` cannot supply the requested type, THEN it must raise `SQLException`.

**Transaction and connection-state reset.**

- WHEN `defaultAutoCommit`, `defaultReadOnly`, `defaultTransactionIsolation`, `defaultCatalog`, or `defaultSchema` is non-null or explicitly configured, THEN each newly created pooled connection must establish that borrowed default.
- WHEN a borrower changes auto-commit, read-only, transaction isolation, catalog, or schema, THEN return must restore the configured default before the physical connection becomes idle.
- WHERE `rollbackOnReturn` is true, WHEN a returned connection has auto-commit disabled and is not read-only, THEN return must roll back its pending transaction.
- WHERE `autoCommitOnReturn` is true, WHEN a returned connection has auto-commit disabled, THEN return must enable auto-commit before reuse.
- WHEN `cacheState` is true, THEN repeated auto-commit and read-only getters must use the wrapper's cached view after the first read or write; WHEN direct delegate access changes physical state, THEN `clearCachedState()` must make later getters observe the delegate again.
- WHEN `defaultQueryTimeout` is non-null, THEN statements created by a borrowed connection must receive that timeout in seconds; WHEN it is null, THEN statement timeout must remain at the driver default.

**Invalidation and shutdown interaction.**

- WHEN `invalidateConnection(connection)` receives null, THEN it must return without changing pool state.
- WHEN `invalidateConnection(connection)` receives a currently borrowed connection from the running source, THEN it must remove and close the corresponding physical connection and free pool capacity.
- IF invalidation is attempted before pool initialization, after pool teardown, or with a connection that cannot unwrap to this pool's connection type, THEN `invalidateConnection` must raise `IllegalStateException`.
- WHEN a borrowed connection is returned after its source has closed, THEN its physical connection must close instead of entering an idle pool.

## Prepared-Statement Pooling

This section defines optional per-connection pooling for prepared and callable statements while preserving normal JDBC results.

**Enablement and identity.**

- WHERE `poolPreparedStatements` is false, each `prepareStatement` or `prepareCall` operation must create a normal delegated JDBC statement whose close operation closes that statement.
- WHERE `poolPreparedStatements` is true, supported `prepareStatement` and `prepareCall` overloads must borrow from the physical connection's keyed statement pool using the SQL text and JDBC result-set, generated-key, or column selection options that distinguish statement identity.
- WHEN a pooled prepared or callable statement is closed, THEN it must close tracked result sets, mark the logical statement closed, and return the physical statement to its containing statement pool; repeated close must have no effect.
- WHEN a pooled prepared statement with pending batch entries is returned, THEN passivation must clear the batch before the statement becomes idle.
- WHEN `maxOpenPreparedStatements` is nonnegative, THEN each connection's statement pool must not exceed that number of open pooled statements; IF the limit prevents a required statement from being borrowed, THEN the JDBC preparation operation must raise `SQLException`.
- WHERE `clearStatementPoolOnReturn` is true, WHEN a connection returns to the connection pool, THEN its idle prepared and callable statements must be cleared from the statement pool.
- WHEN a pooled statement is activated again, THEN it must be open, associated with its creating logical connection, and ready for new parameter or batch state; IF its physical delegate is closed, THEN validation must reject and replace it.

## Data-Source Lifecycle and Management

This section defines start, close, restart, management projections, and lower-level `PoolingDataSource` behavior.

**Start, close, and restart.**

- WHEN `BasicDataSource.start()` is called on a new or closed source, THEN it must mark the source open and initialize a pool from the current configuration.
- WHEN `BasicDataSource.close()` is called, THEN it must mark the source closed, close all idle physical connections, prevent later acquisition, and leave already borrowed connections usable until their eventual close; repeated close must have no effect.
- IF `BasicDataSource.getConnection()` is called while the source is closed, THEN it must raise `SQLException`.
- WHEN `BasicDataSource.restart()` is called, THEN it must close the current pool and initialize a new pool from current configuration; connections borrowed from the old pool must not contribute to the new pool's counts or capacity.
- WHEN `getNumActive()` or `getNumIdle()` is called before initialization or after teardown, THEN it must return zero; WHEN the pool is running, THEN each must return a point-in-time count from that pool.

**Management and standard DataSource operations.**

- WHEN a `DataSourceMXBean` getter is called, THEN it must report the same current configuration or count as the corresponding `BasicDataSource` getter.
- WHEN `getConnection(username, password)` is called on `BasicDataSource` or `PoolingDataSource`, THEN it must raise `UnsupportedOperationException` because per-borrow credentials are not supported.
- WHEN `PoolingDataSource` is constructed, THEN it must require a non-null `ObjectPool`; WHEN `getConnection()` succeeds, THEN it must return a guarded connection whose close returns its delegate to that pool.
- IF `PoolingDataSource.getConnection()` encounters pool exhaustion or a checked pool failure, THEN it must raise `SQLException`; IF the wait is interrupted, THEN it must restore interrupt status and raise `SQLException`.
- WHEN `PoolingDataSource.close()` is called, THEN it must close its backing pool; IF pool close fails, THEN it must raise `SQLException`.
- WHEN `BasicDataSource.getLoginTimeout()`, `BasicDataSource.setLoginTimeout()`, `PoolingDataSource.getLoginTimeout()`, or `PoolingDataSource.setLoginTimeout()` is called, THEN it must raise `UnsupportedOperationException`; WHEN either data source's `getParentLogger()` is called, THEN it must raise `SQLFeatureNotSupportedException`.

## State Model

The core state is one data-source lifecycle state plus a bounded population of physical connections. Each physical connection is uncreated, idle, active through one guarded logical handle, or closed. An active physical connection owns zero or more open logical statements, and prepared-statement pooling adds a per-connection partition of active and idle physical statements.

The public projections are configuration getters, `isClosed`, `getNumActive`, `getNumIdle`, borrowed JDBC behavior, statement behavior, factory calls, and `DataSourceMXBean` values.

- WHILE the source is running, each managed physical connection must contribute to exactly one of the active or idle projections.
- WHILE a guarded logical connection is active, its physical connection must not be lent through another logical handle.
- WHILE the source is closed, `isClosed()` must return true, idle count must remain zero after cleanup, and new acquisition must fail.
- WHEN a prepared statement moves between active and idle statement states, THEN its owning physical connection and statement identity must remain unchanged.

## Error Semantics

| Condition | Required result |
|---|---|
| Closed `BasicDataSource` receives `getConnection()` | IF the source is closed, THEN `getConnection()` must raise `SQLException`. |
| Per-borrow credentials are supplied | WHEN `getConnection(username, password)` is called, THEN the data source must raise `UnsupportedOperationException`. |
| Finite acquisition wait expires | IF no connection becomes available before the configured wait expires, THEN acquisition must raise `SQLException`. |
| Waiting borrower is interrupted | IF the wait is interrupted, THEN acquisition must restore interrupt status and raise `SQLException`. |
| Driver or physical connection setup fails | IF driver resolution, initialization SQL, or physical acquisition fails, THEN initialization or borrowing must raise `SQLException` and must not retain the failed connection. |
| Validation rejects a connection | IF configured validation rejects a connection, THEN the pool must destroy it and the triggering operation must continue with a replacement or raise `SQLException` when no replacement succeeds. |
| Unsupported wrapper requested | IF `unwrap` cannot supply the requested interface, THEN it must raise `SQLException`. |
| Invalid explicit connection invalidation | IF the source has no live pool or the connection does not belong to it, THEN `invalidateConnection` must raise `IllegalStateException`. |
| Unknown non-integer transaction-isolation token | IF the factory property is neither a supported name nor an integer, THEN `createDataSource` must return the configured unstarted data source and `getDefaultTransactionIsolation()` must retain the `-1` driver-default sentinel without raising `SQLException`. |
| Lower-level source has null pool | IF `PoolingDataSource` receives null, THEN construction must raise `NullPointerException`. |

## Cross-View Invariants

1. A successful `getConnection()` must increase the active projection by one relative to the same pool state, and closing that handle must decrease active count while either increasing idle count or closing the physical connection under an applicable policy.
2. A transaction committed through a borrowed connection must remain visible through a later borrowed connection to the same local database, while uncommitted work subject to `rollbackOnReturn` must not become visible after that handle closes.
3. Configuration visible through `DataSourceMXBean` must equal the corresponding `BasicDataSource` getter, and live capacity or maintenance changes must govern subsequent pool behavior.
4. Invalidating a borrowed connection must make that physical connection disappear from active and idle projections, and a later borrow must use another or newly created physical connection.
5. Closing a data source must synchronize `isClosed`, acquisition failure, zero idle count, old-pool retirement, and eventual physical close of outstanding connections.
6. Restarting a closed source must create an independent active and idle projection from current configuration, and late returns from the old pool must not change the new projection.
7. Borrowed connection defaults, return-time rollback, auto-commit restoration, and later JDBC getters must agree across consecutive borrowers of the same physical connection.
8. Prepared-statement pooling must preserve JDBC query results while statement close and later preparation agree with statement-pool capacity, clearing, and physical-connection ownership.

## Public Interface

### Import Surface

```java
import org.apache.commons.dbcp2.BasicDataSource;
import org.apache.commons.dbcp2.BasicDataSourceFactory;
import org.apache.commons.dbcp2.BasicDataSourceMXBean;
import org.apache.commons.dbcp2.DataSourceMXBean;
import org.apache.commons.dbcp2.ConnectionFactory;
import org.apache.commons.dbcp2.DriverManagerConnectionFactory;
import org.apache.commons.dbcp2.DriverConnectionFactory;
import org.apache.commons.dbcp2.DataSourceConnectionFactory;
import org.apache.commons.dbcp2.PoolableConnection;
import org.apache.commons.dbcp2.PoolableConnectionFactory;
import org.apache.commons.dbcp2.PoolingDataSource;
import org.apache.commons.dbcp2.DelegatingConnection;
```

### Public Members

| Type | Public members in scope |
|---|---|
| `BasicDataSource` | constructor; `addConnectionProperty`, `removeConnectionProperty`; `getConnection`; `start`, `close`, `restart`, `isClosed`; `invalidateConnection`, `evict`; `getNumActive`, `getNumIdle`; `unwrap`, `isWrapperFor`; standard `DataSource` log-writer, login-timeout, and parent-logger methods; getters and setters for `url`, `username`, `password`, `driver`, `driverClassName`, `driverClassLoader`, `connectionProperties`, `connectionFactoryClassName`, connection defaults, connection initialization SQL, capacity, wait, LIFO, validation, eviction, lifetime, abandoned recovery, prepared-statement pooling, state caching, return cleanup, fatal SQL states, JMX name, and connection-MBean registration |
| `BasicDataSourceFactory` | constructor, `createDataSource`, `getObjectInstance` |
| `DataSourceMXBean` | read-only getters corresponding to `BasicDataSource` configuration and counts; `start`, `restart` |
| `BasicDataSourceMXBean` | all `DataSourceMXBean` members and deprecated `getPassword` |
| `ConnectionFactory` | `createConnection` |
| `DriverManagerConnectionFactory` | four constructors; `createConnection`, `getConnectionUri`, `getProperties`, `getUserName` |
| `DriverConnectionFactory` | constructor; `createConnection`, `getConnectionString`, `getDriver`, `getProperties` |
| `DataSourceConnectionFactory` | three constructors; `createConnection`, `getDataSource`, `getUserName`, `getUserPassword` |
| `PoolableConnection` | public constructors; JDBC operations inherited from `DelegatingConnection`; `close`, `reallyClose`, `validate`, `getDisconnectionSqlCodes`, `isFastFailValidation`, `setLastUsed`; `PoolableConnectionMXBean` connection-state operations |
| `PoolableConnectionMXBean` | `clearCachedState`, `clearWarnings`, `close`, `reallyClose`; getters and setters for auto-commit, read-only, catalog, schema, holdability, transaction isolation, and state caching; `isClosed`, `getToString` |
| `PoolableConnectionFactory` | constructor; `makeObject`, `activateObject`, `passivateObject`, `validateObject`, `destroyObject`; `setPool`, `getPool`, `getConnectionFactory`; getters and setters for connection defaults, initialization SQL, validation, lifetime, fatal SQL states, state caching, return cleanup, and prepared-statement pooling |
| `PoolingDataSource` | constructor; `getConnection`, `close`; `isAccessToUnderlyingConnectionAllowed`, `setAccessToUnderlyingConnectionAllowed`; `unwrap`, `isWrapperFor`; standard `DataSource` log-writer, login-timeout, and parent-logger methods |
| `DelegatingConnection` | constructor; JDBC `Connection` methods; `getDelegate`, `getInnermostDelegate`, `innermostDelegateEquals`; `getCacheState`, `setCacheState`, `clearCachedState`; default-query-timeout getters and setters; `unwrap`, `isWrapperFor` |

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `BasicDataSource` | class | Configures, starts, exposes, restarts, and closes a local JDBC connection pool. |
| `BasicDataSourceFactory` | class | Creates a configured `BasicDataSource` from Java properties or a naming reference. |
| `DataSourceMXBean` | interface | Defines the management projection of data-source policy, counts, and lifecycle controls. |
| `BasicDataSourceMXBean` | interface | Preserves the management-compatible extension surface for `BasicDataSource`. |
| `ConnectionFactory` | interface | Creates physical JDBC connections for a pool. |
| `DriverManagerConnectionFactory` | class | Creates physical connections through `DriverManager`. |
| `DriverConnectionFactory` | class | Creates physical connections through a supplied JDBC `Driver`. |
| `DataSourceConnectionFactory` | class | Creates physical connections through another `DataSource`. |
| `PoolableConnection` | class | Wraps a physical connection with pool return, validation, fatal-error, and management behavior. |
| `PoolableConnectionMXBean` | interface | Defines the management-visible state and controls of one poolable connection. |
| `PoolableConnectionFactory` | class | Adapts a physical connection factory to Commons Pool lifecycle callbacks. |
| `PoolingDataSource` | class | Exposes an existing connection object pool as a guarded JDBC `DataSource`. |
| `DelegatingConnection` | class | Delegates JDBC operations while exposing controlled wrapper and cached-state behavior. |

### CLI Entry Points

There is no console script for this package. Executing the artifact with `java -jar` is not supported. Programmatic use is through Maven dependencies and Java imports.

## Appendix A: Environment

The working environment runs Java 17 on Linux without network access. The Java standard library, Commons Pool 2, Commons Logging, Jakarta Transactions, JUnit Jupiter, and H2 are preinstalled and available from the local Maven repository. The target artifact is not preinstalled. The assessment environment provides the same JDK, package set, and offline execution policy.

The project must provide a Maven `pom.xml` at its root with coordinate `org.apache.commons:commons-dbcp2`. Source must compile through the standard Maven lifecycle using locally available artifacts.

## Appendix B: Assessment Notes

Assessment exercises public construction and property mapping, physical connection factories, lazy and explicit startup, capacity and wait behavior, validation and eviction, transaction and state cleanup, invalidation, prepared-statement reuse, shutdown and restart, management counts, and lower-level pool assembly. Checks compare observable return values, JDBC effects, exception classes, lifecycle callbacks, and cross-view consistency; they do not require private fields, package-private helpers, exact diagnostic text, or a particular concurrency implementation. Each independently passing public behavior case contributes equally, with integration cases checking complete lifecycles across multiple projections.
