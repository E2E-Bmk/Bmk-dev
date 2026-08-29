# Clause Sidecar — commons-dbcp-fullrepro-001

Stable clause IDs map to verbatim candidate-body sentences. IDs remain outside the candidate-visible specification and are intended for Java test Javadocs in the form `Verifies: DBCP-...`.

## Representative Workflows

- `DBCP-WFL-001` — `representative-workflows`: “WHEN the first borrow occurs, THEN it must initialize the source and pool, the checked-out handle must contribute to the active count, `Connection.close()` must return a reusable physical connection, and `BasicDataSource.close()` must close the remaining idle pool state.”
- `DBCP-WFL-002` — `representative-workflows`: “WHEN the lower-level workflow runs, THEN the lifecycle factory must create and validate pooled connections, the data source must guard each borrowed handle, and closing a pooled prepared statement must return it to its per-connection statement pool instead of closing its physical statement.”

## Connection Sources and Configuration

- `DBCP-SRC-017` — `connection-sources-and-configuration`: “WHEN a new `BasicDataSource` is constructed, THEN it must default `initialSize` to 0, `maxTotal` and `maxIdle` to 8, `minIdle` to 0, `maxWaitDuration` to an indefinite wait, and `lifo` to true.”
- `DBCP-SRC-018` — `connection-sources-and-configuration`: “WHEN a new `BasicDataSource` is constructed, THEN it must default `testOnBorrow` to true, the other three validation switches to false, periodic eviction and maximum connection lifetime to disabled, and `validationQuery` to absent.”
- `DBCP-SRC-019` — `connection-sources-and-configuration`: “WHEN a new `BasicDataSource` is constructed, THEN it must default `poolPreparedStatements` and `clearStatementPoolOnReturn` to false, `maxOpenPreparedStatements` to unlimited, and `accessToUnderlyingConnectionAllowed` to false.”
- `DBCP-SRC-020` — `connection-sources-and-configuration`: “WHEN a new `BasicDataSource` is constructed, THEN it must default `cacheState`, `autoCommitOnReturn`, `rollbackOnReturn`, `logExpiredConnections`, and `registerConnectionMBean` to true, while abandoned-removal switches, abandoned logging, abandoned usage tracking, and `fastFailValidation` must default to false.”
- `DBCP-SRC-021` — `connection-sources-and-configuration`: “WHEN connection defaults are not explicitly set, THEN auto-commit, read-only, catalog, schema, transaction isolation, and statement query timeout must remain at the JDBC driver's defaults.”
- `DBCP-SRC-001` — `connection-sources-and-configuration`: “WHEN `ConnectionFactory.createConnection()` is called, THEN the selected factory must return one new physical JDBC connection or raise `SQLException` from the underlying source.”
- `DBCP-SRC-002` — `connection-sources-and-configuration`: “WHEN `DriverManagerConnectionFactory` is constructed with only `connectionUri`, THEN `createConnection()` must call `DriverManager` without explicit credentials.”
- `DBCP-SRC-003` — `connection-sources-and-configuration`: “WHEN `DriverManagerConnectionFactory` is constructed with `connectionUri` and `properties`, THEN `createConnection()` must pass that properties object to `DriverManager`.”
- `DBCP-SRC-004` — `connection-sources-and-configuration`: “WHEN `DriverManagerConnectionFactory` is constructed with `connectionUri`, `userName`, and `userPassword`, THEN `createConnection()` must pass the credential pair explicitly and the factory must defensively copy a character-array password.”
- `DBCP-SRC-005` — `connection-sources-and-configuration`: “WHEN `DriverConnectionFactory` is constructed with `driver`, `connectString`, and `properties`, THEN `createConnection()` must return the result of that driver's `connect` operation with the same connection string and properties.”
- `DBCP-SRC-006` — `connection-sources-and-configuration`: “WHEN `DataSourceConnectionFactory` has no credential pair, THEN `createConnection()` must call the wrapped source's no-argument `getConnection()`; WHEN it has a credential pair, THEN it must call the credential overload and defensively copy a character-array password.”
- `DBCP-SRC-007` — `connection-sources-and-configuration`: “WHEN an unstarted `BasicDataSource` first receives `getConnection()`, `start()`, `getLogWriter()`, or `setLogWriter()`, THEN it must initialize at most one pool from the current startup configuration.”
- `DBCP-SRC-008` — `connection-sources-and-configuration`: “WHEN `initialSize` is positive at initialization, THEN the data source must create that many idle connections subject to the configured pool limits; IF any required initial connection cannot be created, THEN initialization must raise `SQLException` and must close the partially created pool.”
- `DBCP-SRC-009` — `connection-sources-and-configuration`: “WHEN `driver` is set, THEN the data source must use that instance; OTHERWISE, WHEN `driverClassName` is set, THEN it must load that class using `driverClassLoader` when supplied and the available application class loaders otherwise; OTHERWISE it must resolve a driver through `DriverManager` from `url`.”
- `DBCP-SRC-010` — `connection-sources-and-configuration`: “IF neither a usable `driver`, loadable `driverClassName`, nor resolvable `url` supplies a JDBC driver, THEN pool initialization must raise `SQLException`.”
- `DBCP-SRC-011` — `connection-sources-and-configuration`: “WHEN `username`, `password`, or entries added through `addConnectionProperty` are configured before initialization, THEN newly created physical connections must receive those values; WHEN these startup values change after initialization, THEN the running pool must retain its existing physical-connection factory until `restart()`.”
- `DBCP-SRC-012` — `connection-sources-and-configuration`: “WHEN `connectionInitSqls` is configured, THEN every newly created physical connection must execute the SQL strings once in iteration order before entering the pool; IF an initialization statement fails, THEN that physical connection creation must fail.”
- `DBCP-SRC-013` — `connection-sources-and-configuration`: “WHEN `BasicDataSourceFactory.createDataSource(properties)` is called, THEN recognized Java properties must configure the corresponding `BasicDataSource` values and the method must return an unstarted data source.”
- `DBCP-SRC-014` — `connection-sources-and-configuration`: “WHEN the factory parses `defaultTransactionIsolation`, THEN it must set `NONE`, `READ_COMMITTED`, `READ_UNCOMMITTED`, `REPEATABLE_READ`, `SERIALIZABLE`, or an integer isolation value; IF the token is unknown and non-integer, THEN it must ignore that token and retain the `-1` driver-default sentinel without raising `SQLException`.”
- `DBCP-SRC-015` — `connection-sources-and-configuration`: “WHEN the factory parses `connectionProperties`, THEN semicolon-delimited `name=value` entries must be added as driver properties; entries named `user` or `password` must not replace the explicit `username` and `password` properties.”
- `DBCP-SRC-016` — `connection-sources-and-configuration`: “WHEN the factory parses duration properties, THEN `maxWaitMillis`, eviction intervals, and maximum connection lifetime must use milliseconds, while validation-query timeout, abandoned timeout, and default statement-query timeout must use seconds.”

## Capacity, Borrowing, and Maintenance

- `DBCP-CAP-001` — `capacity-borrowing-and-maintenance`: “WHEN an idle valid connection exists, THEN `getConnection()` must return a new guarded logical handle and move one connection from the idle projection to the active projection.”
- `DBCP-CAP-002` — `capacity-borrowing-and-maintenance`: “WHEN no idle connection exists and the total is below `maxTotal`, THEN `getConnection()` must create a physical connection and must not exceed `maxTotal`; a negative `maxTotal` must represent no fixed total limit.”
- `DBCP-CAP-003` — `capacity-borrowing-and-maintenance`: “WHILE no connection is available at the total limit, a borrower must wait for at most `maxWaitDuration`; WHEN the duration is negative, THEN the wait must be indefinite.”
- `DBCP-CAP-004` — `capacity-borrowing-and-maintenance`: “IF no connection becomes available before a finite maximum wait expires, THEN `getConnection()` must raise `SQLException` with the pool exhaustion as its cause.”
- `DBCP-CAP-005` — `capacity-borrowing-and-maintenance`: “IF a waiting borrower is interrupted, THEN `getConnection()` must restore the thread interrupt status and raise `SQLException`.”
- `DBCP-CAP-006` — `capacity-borrowing-and-maintenance`: “WHEN `setMaxTotal`, `setMaxIdle`, `setMinIdle`, `setMaxWait`, `setLifo`, or an eviction-policy setter is called after startup, THEN the corresponding running-pool policy and its getter must reflect the new value.”
- `DBCP-CAP-007` — `capacity-borrowing-and-maintenance`: “WHEN `lifo` is true, THEN idle borrowing must prefer the most recently returned connection; WHEN it is false, THEN idle borrowing must prefer return order.”
- `DBCP-CAP-008` — `capacity-borrowing-and-maintenance`: “WHERE `testOnCreate` is true, every newly created connection must pass configured validation before becoming available; IF validation fails, THEN creation must fail.”
- `DBCP-CAP-009` — `capacity-borrowing-and-maintenance`: “WHERE `testOnBorrow` is true, every borrowed connection must pass configured validation; IF an idle connection fails, THEN the pool must discard it and continue with another available or creatable connection.”
- `DBCP-CAP-010` — `capacity-borrowing-and-maintenance`: “WHERE `testOnReturn` is true, every returned connection must pass configured validation; IF validation fails, THEN the pool must discard it instead of making it idle.”
- `DBCP-CAP-011` — `capacity-borrowing-and-maintenance`: “WHERE `testWhileIdle` is true and maintenance is enabled, each retained connection selected by an eviction run must pass configured validation; IF validation fails, THEN the pool must discard it.”
- `DBCP-CAP-012` — `capacity-borrowing-and-maintenance`: “WHEN `validationQuery` is absent or empty, THEN validation must call JDBC `Connection.isValid` with the nonnegative `validationQueryTimeout`; WHEN a query is present, THEN validation must execute it and require at least one result row.”
- `DBCP-CAP-013` — `capacity-borrowing-and-maintenance`: “WHERE `fastFailValidation` is true, a pooled connection that previously reported a configured fatal SQL state must fail later validation without calling the JDBC validation operation; SQL states listed by `disconnectionIgnoreSqlCodes` must not be treated as fatal.”
- `DBCP-CAP-014` — `capacity-borrowing-and-maintenance`: “WHEN `durationBetweenEvictionRuns` is positive, THEN periodic maintenance must examine the configured `numTestsPerEvictionRun`; WHEN the duration is zero or negative, THEN periodic maintenance must remain disabled.”
- `DBCP-CAP-015` — `capacity-borrowing-and-maintenance`: “WHEN an idle connection exceeds `minEvictableIdleDuration`, THEN an eviction run must remove it; WHEN it exceeds only `softMinEvictableIdleDuration`, THEN removal must preserve at least `minIdle` idle connections.”
- `DBCP-CAP-016` — `capacity-borrowing-and-maintenance`: “WHEN `maxConnDuration` is positive and a physical connection exceeds it, THEN its next activation, passivation, or validation must fail and the pool must replace it; a zero or negative duration must disable lifetime expiry.”
- `DBCP-CAP-017` — `capacity-borrowing-and-maintenance`: “WHEN `evict()` is called on a started source, THEN it must synchronously run one idle-eviction pass; WHEN the source is unstarted, THEN it must return without creating a pool.”

## Borrowed Connection Lifecycle

- `DBCP-CONN-001` — `borrowed-connection-lifecycle`: “WHEN a connection is borrowed, THEN the returned handle must implement `java.sql.Connection` and must delegate JDBC operations to one currently owned physical connection.”
- `DBCP-CONN-002` — `borrowed-connection-lifecycle`: “WHEN a borrowed handle is closed for the first time, THEN it must close its tracked open statements, restore configured state, and return or invalidate the physical connection exactly once; WHEN the same handle is closed again, THEN the call must have no effect.”
- `DBCP-CONN-003` — `borrowed-connection-lifecycle`: “WHILE a logical handle is closed, JDBC operations that require an open connection must raise `SQLException` and must not reach a physical connection later lent to another caller.”
- `DBCP-CONN-004` — `borrowed-connection-lifecycle`: “WHEN `accessToUnderlyingConnectionAllowed` is false, THEN `DelegatingConnection.getDelegate()` and `getInnermostDelegate()` obtained through a guarded data-source connection must return null; WHEN it is true, THEN those methods must return the corresponding delegate.”
- `DBCP-CONN-005` — `borrowed-connection-lifecycle`: “WHEN `unwrap(iface)` or `isWrapperFor(iface)` names a supported wrapper type, THEN the data source or connection must return the matching result; IF `unwrap` cannot supply the requested type, THEN it must raise `SQLException`.”
- `DBCP-CONN-006` — `borrowed-connection-lifecycle`: “WHEN `defaultAutoCommit`, `defaultReadOnly`, `defaultTransactionIsolation`, `defaultCatalog`, or `defaultSchema` is non-null or explicitly configured, THEN each newly created pooled connection must establish that borrowed default.”
- `DBCP-CONN-007` — `borrowed-connection-lifecycle`: “WHEN a borrower changes auto-commit, read-only, transaction isolation, catalog, or schema, THEN return must restore the configured default before the physical connection becomes idle.”
- `DBCP-CONN-008` — `borrowed-connection-lifecycle`: “WHERE `rollbackOnReturn` is true, WHEN a returned connection has auto-commit disabled and is not read-only, THEN return must roll back its pending transaction.”
- `DBCP-CONN-009` — `borrowed-connection-lifecycle`: “WHERE `autoCommitOnReturn` is true, WHEN a returned connection has auto-commit disabled, THEN return must enable auto-commit before reuse.”
- `DBCP-CONN-010` — `borrowed-connection-lifecycle`: “WHEN `cacheState` is true, THEN repeated auto-commit and read-only getters must use the wrapper's cached view after the first read or write; WHEN direct delegate access changes physical state, THEN `clearCachedState()` must make later getters observe the delegate again.”
- `DBCP-CONN-011` — `borrowed-connection-lifecycle`: “WHEN `defaultQueryTimeout` is non-null, THEN statements created by a borrowed connection must receive that timeout in seconds; WHEN it is null, THEN statement timeout must remain at the driver default.”
- `DBCP-CONN-012` — `borrowed-connection-lifecycle`: “WHEN `invalidateConnection(connection)` receives null, THEN it must return without changing pool state.”
- `DBCP-CONN-013` — `borrowed-connection-lifecycle`: “WHEN `invalidateConnection(connection)` receives a currently borrowed connection from the running source, THEN it must remove and close the corresponding physical connection and free pool capacity.”
- `DBCP-CONN-014` — `borrowed-connection-lifecycle`: “IF invalidation is attempted before pool initialization, after pool teardown, or with a connection that cannot unwrap to this pool's connection type, THEN `invalidateConnection` must raise `IllegalStateException`.”
- `DBCP-CONN-015` — `borrowed-connection-lifecycle`: “WHEN a borrowed connection is returned after its source has closed, THEN its physical connection must close instead of entering an idle pool.”

## Prepared-Statement Pooling

- `DBCP-STMT-001` — `prepared-statement-pooling`: “WHERE `poolPreparedStatements` is false, each `prepareStatement` or `prepareCall` operation must create a normal delegated JDBC statement whose close operation closes that statement.”
- `DBCP-STMT-002` — `prepared-statement-pooling`: “WHERE `poolPreparedStatements` is true, supported `prepareStatement` and `prepareCall` overloads must borrow from the physical connection's keyed statement pool using the SQL text and JDBC result-set, generated-key, or column selection options that distinguish statement identity.”
- `DBCP-STMT-003` — `prepared-statement-pooling`: “WHEN a pooled prepared or callable statement is closed, THEN it must close tracked result sets, mark the logical statement closed, and return the physical statement to its containing statement pool; repeated close must have no effect.”
- `DBCP-STMT-004` — `prepared-statement-pooling`: “WHEN a pooled prepared statement with pending batch entries is returned, THEN passivation must clear the batch before the statement becomes idle.”
- `DBCP-STMT-005` — `prepared-statement-pooling`: “WHEN `maxOpenPreparedStatements` is nonnegative, THEN each connection's statement pool must not exceed that number of open pooled statements; IF the limit prevents a required statement from being borrowed, THEN the JDBC preparation operation must raise `SQLException`.”
- `DBCP-STMT-006` — `prepared-statement-pooling`: “WHERE `clearStatementPoolOnReturn` is true, WHEN a connection returns to the connection pool, THEN its idle prepared and callable statements must be cleared from the statement pool.”
- `DBCP-STMT-007` — `prepared-statement-pooling`: “WHEN a pooled statement is activated again, THEN it must be open, associated with its creating logical connection, and ready for new parameter or batch state; IF its physical delegate is closed, THEN validation must reject and replace it.”

## Data-Source Lifecycle and Management

- `DBCP-LIFE-001` — `data-source-lifecycle-and-management`: “WHEN `BasicDataSource.start()` is called on a new or closed source, THEN it must mark the source open and initialize a pool from the current configuration.”
- `DBCP-LIFE-002` — `data-source-lifecycle-and-management`: “WHEN `BasicDataSource.close()` is called, THEN it must mark the source closed, close all idle physical connections, prevent later acquisition, and leave already borrowed connections usable until their eventual close; repeated close must have no effect.”
- `DBCP-LIFE-003` — `data-source-lifecycle-and-management`: “IF `BasicDataSource.getConnection()` is called while the source is closed, THEN it must raise `SQLException`.”
- `DBCP-LIFE-004` — `data-source-lifecycle-and-management`: “WHEN `BasicDataSource.restart()` is called, THEN it must close the current pool and initialize a new pool from current configuration; connections borrowed from the old pool must not contribute to the new pool's counts or capacity.”
- `DBCP-LIFE-005` — `data-source-lifecycle-and-management`: “WHEN `getNumActive()` or `getNumIdle()` is called before initialization or after teardown, THEN it must return zero; WHEN the pool is running, THEN each must return a point-in-time count from that pool.”
- `DBCP-LIFE-006` — `data-source-lifecycle-and-management`: “WHEN a `DataSourceMXBean` getter is called, THEN it must report the same current configuration or count as the corresponding `BasicDataSource` getter.”
- `DBCP-LIFE-007` — `data-source-lifecycle-and-management`: “WHEN `getConnection(username, password)` is called on `BasicDataSource` or `PoolingDataSource`, THEN it must raise `UnsupportedOperationException` because per-borrow credentials are not supported.”
- `DBCP-LIFE-008` — `data-source-lifecycle-and-management`: “WHEN `PoolingDataSource` is constructed, THEN it must require a non-null `ObjectPool`; WHEN `getConnection()` succeeds, THEN it must return a guarded connection whose close returns its delegate to that pool.”
- `DBCP-LIFE-009` — `data-source-lifecycle-and-management`: “IF `PoolingDataSource.getConnection()` encounters pool exhaustion or a checked pool failure, THEN it must raise `SQLException`; IF the wait is interrupted, THEN it must restore interrupt status and raise `SQLException`.”
- `DBCP-LIFE-010` — `data-source-lifecycle-and-management`: “WHEN `PoolingDataSource.close()` is called, THEN it must close its backing pool; IF pool close fails, THEN it must raise `SQLException`.”
- `DBCP-LIFE-011` — `data-source-lifecycle-and-management`: “WHEN `BasicDataSource.getLoginTimeout()`, `BasicDataSource.setLoginTimeout()`, `PoolingDataSource.getLoginTimeout()`, or `PoolingDataSource.setLoginTimeout()` is called, THEN it must raise `UnsupportedOperationException`; WHEN either data source's `getParentLogger()` is called, THEN it must raise `SQLFeatureNotSupportedException`.”

## State Model

- `DBCP-STATE-001` — `state-model`: “WHILE the source is running, each managed physical connection must contribute to exactly one of the active or idle projections.”
- `DBCP-STATE-002` — `state-model`: “WHILE a guarded logical connection is active, its physical connection must not be lent through another logical handle.”
- `DBCP-STATE-003` — `state-model`: “WHILE the source is closed, `isClosed()` must return true, idle count must remain zero after cleanup, and new acquisition must fail.”
- `DBCP-STATE-004` — `state-model`: “WHEN a prepared statement moves between active and idle statement states, THEN its owning physical connection and statement identity must remain unchanged.”

## Error Semantics

- `DBCP-ERR-001` — `error-semantics`: “IF the source is closed, THEN `getConnection()` must raise `SQLException`.”
- `DBCP-ERR-002` — `error-semantics`: “WHEN `getConnection(username, password)` is called, THEN the data source must raise `UnsupportedOperationException`.”
- `DBCP-ERR-003` — `error-semantics`: “IF no connection becomes available before the configured wait expires, THEN acquisition must raise `SQLException`.”
- `DBCP-ERR-004` — `error-semantics`: “IF the wait is interrupted, THEN acquisition must restore interrupt status and raise `SQLException`.”
- `DBCP-ERR-005` — `error-semantics`: “IF driver resolution, initialization SQL, or physical acquisition fails, THEN initialization or borrowing must raise `SQLException` and must not retain the failed connection.”
- `DBCP-ERR-006` — `error-semantics`: “IF configured validation rejects a connection, THEN the pool must destroy it and the triggering operation must continue with a replacement or raise `SQLException` when no replacement succeeds.”
- `DBCP-ERR-007` — `error-semantics`: “IF `unwrap` cannot supply the requested interface, THEN it must raise `SQLException`.”
- `DBCP-ERR-008` — `error-semantics`: “IF the source has no live pool or the connection does not belong to it, THEN `invalidateConnection` must raise `IllegalStateException`.”
- `DBCP-ERR-009` — `error-semantics`: “IF the factory property is neither a supported name nor an integer, THEN `createDataSource` must return the configured unstarted data source and `getDefaultTransactionIsolation()` must retain the `-1` driver-default sentinel without raising `SQLException`.”
- `DBCP-ERR-010` — `error-semantics`: “IF `PoolingDataSource` receives null, THEN construction must raise `NullPointerException`.”

## Cross-View Invariants

- `DBCP-CVI-001` — `cross-view-invariants`: “A successful `getConnection()` must increase the active projection by one relative to the same pool state, and closing that handle must decrease active count while either increasing idle count or closing the physical connection under an applicable policy.”
- `DBCP-CVI-002` — `cross-view-invariants`: “A transaction committed through a borrowed connection must remain visible through a later borrowed connection to the same local database, while uncommitted work subject to `rollbackOnReturn` must not become visible after that handle closes.”
- `DBCP-CVI-003` — `cross-view-invariants`: “Configuration visible through `DataSourceMXBean` must equal the corresponding `BasicDataSource` getter, and live capacity or maintenance changes must govern subsequent pool behavior.”
- `DBCP-CVI-004` — `cross-view-invariants`: “Invalidating a borrowed connection must make that physical connection disappear from active and idle projections, and a later borrow must use another or newly created physical connection.”
- `DBCP-CVI-005` — `cross-view-invariants`: “Closing a data source must synchronize `isClosed`, acquisition failure, zero idle count, old-pool retirement, and eventual physical close of outstanding connections.”
- `DBCP-CVI-006` — `cross-view-invariants`: “Restarting a closed source must create an independent active and idle projection from current configuration, and late returns from the old pool must not change the new projection.”
- `DBCP-CVI-007` — `cross-view-invariants`: “Borrowed connection defaults, return-time rollback, auto-commit restoration, and later JDBC getters must agree across consecutive borrowers of the same physical connection.”
- `DBCP-CVI-008` — `cross-view-invariants`: “Prepared-statement pooling must preserve JDBC query results while statement close and later preparation agree with statement-pool capacity, clearing, and physical-connection ownership.”

## Environment

- `DBCP-ENV-001` — `appendix-a-environment`: “The project must provide a Maven `pom.xml` at its root with coordinate `org.apache.commons:commons-dbcp2`.”
- `DBCP-ENV-002` — `appendix-a-environment`: “Source must compile through the standard Maven lifecycle using locally available artifacts.”

Clause count: **97**.
