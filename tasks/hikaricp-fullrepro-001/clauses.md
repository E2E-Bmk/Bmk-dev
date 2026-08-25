# hikaricp v1 Clause Sidecar

Clause IDs are audit-only and do not appear in the candidate-facing specification body. Each quoted clause is verbatim from `wip/hikaricp/spec/spec_v1.md` and passed Q1, Q2, and Q3 in `wip/hikaricp/spec/public_surface_audit.md`.

## Representative Workflows

- `HCP-WF-001` — “The configured source must be copied into the data source, construction must start the pool, borrowing must project one active logical handle, closing that handle must recycle its physical connection, and closing the data source must shut the pool down.”
- `HCP-WF-002` — “The first borrow must validate configuration and start the lazy pool; the management view must change an allowed live setting; and the custom tracker must receive lifecycle measurements tied to the same pool identity and statistics.”

## Configuration and Validation

- `HCP-CONF-001` — “The no-argument `HikariConfig` constructor must create an unsealed configuration with documented defaults: `autoCommit=true`, `readOnly=false`, `connectionTimeout=30000`, `validationTimeout=5000`, `idleTimeout=600000`, `keepaliveTime=120000`, `maxLifetime=1800000`, `leakDetectionThreshold=0`, `initializationFailTimeout=1`, `maximumPoolSize=10`, `allowPoolSuspension=false`, `registerMbeans=false`, and `isolateInternalQueries=false`.”
- `HCP-CONF-002` — “WHEN `minimumIdle` is not explicitly set, THEN validation must set it to `maximumPoolSize` so the default is a fixed-size pool.”
- `HCP-CONF-003` — “WHEN `HikariConfig(Properties)` is constructed, THEN matching JavaBean property names must populate the same configuration values as their setters, and names prefixed with `dataSource.` must populate data-source properties.”
- `HCP-CONF-004` — “WHEN `HikariConfig(String)` is constructed, THEN it must load the named filesystem properties file first and otherwise a classpath resource with that name.”
- `HCP-CONF-005` — “IF the named property resource does not exist, THEN `HikariConfig(String)` must raise `IllegalArgumentException`.”
- `HCP-CONF-006` — “WHEN `copyStateTo(other)` is called, THEN it must copy the current configuration values into `other`, and `other` must remain unsealed.”
- `HCP-CONF-007` — “The configuration must select one effective physical-connection source in this precedence order: `dataSource`, `dataSourceClassName`, `jdbcUrl`, then `dataSourceJNDI`; `driverClassName` must only refine `jdbcUrl` mode.”
- `HCP-CONF-008` — “WHEN `dataSource` is set, THEN the pool must wrap that instance and ignore `dataSourceClassName` and data-source construction properties.”
- `HCP-CONF-009` — “WHEN `dataSourceClassName` and `jdbcUrl` are both set without an explicit `dataSource`, THEN the pool must use `dataSourceClassName` and ignore `jdbcUrl`.”
- `HCP-CONF-010` — “IF `dataSourceClassName` and `driverClassName` are both set, THEN validation must raise `IllegalStateException`.”
- `HCP-CONF-011` — “IF `driverClassName` is set without `jdbcUrl`, THEN validation must raise `IllegalArgumentException`.”
- `HCP-CONF-012` — “IF none of `dataSource`, `dataSourceClassName`, `dataSourceJNDI`, or `jdbcUrl` supplies a source, THEN validation must raise `IllegalArgumentException`.”
- `HCP-CONF-013` — “WHEN `addDataSourceProperty(propertyName, value)` or `setDataSourceProperties(dsProperties)` is used in `DataSource` mode, THEN matching properties must be applied through JavaBean setters on the constructed driver data source.”
- `HCP-CONF-014` — “WHEN those properties are used in `jdbcUrl` mode, THEN they must be supplied as driver connection properties.”
- `HCP-CONF-015` — “The `username`, `password`, and `Credentials` accessors must represent one atomic credential pair, and `Credentials.of(username, password)` and the public constructor must create an immutable pair exposed through `getUsername` and `getPassword`.”
- `HCP-CONF-016` — “WHERE a `HikariCredentialsProvider` is configured, the pool must call `getCredentials` when creating a physical connection and must use the returned pair for that creation attempt.”
- `HCP-CONF-017` — “WHEN credentials change through `HikariConfigMXBean`, THEN the new pair must apply only to later physical connections in `DataSource` mode.”
- `HCP-CONF-018` — “WHEN a physical connection enters the pool, THEN `autoCommit`, `readOnly`, `catalog`, `schema`, and `transactionIsolation` must establish its borrowed default state; IF the driver rejects a configured default, THEN that physical connection creation attempt must fail.”
- `HCP-CONF-019` — “IF `transactionIsolation` is not a named `java.sql.Connection` isolation constant or a numeric isolation value, THEN pool startup must raise `IllegalArgumentException`.”
- `HCP-CONF-020` — “All timeout and lifetime configuration values must use milliseconds.”
- `HCP-CONF-021` — “IF `setConnectionTimeout` receives a value below 250 other than zero, THEN it must raise `IllegalArgumentException`; WHEN it receives zero, THEN it must represent an effectively unbounded wait.”
- `HCP-CONF-022` — “IF `setValidationTimeout` receives a value below 250, THEN it must raise `IllegalArgumentException`.”
- `HCP-CONF-023` — “IF `setIdleTimeout` receives a negative value, THEN it must raise `IllegalArgumentException`.”
- `HCP-CONF-024` — “IF `setMaximumPoolSize` receives a value below one or `setMinimumIdle` receives a negative value, THEN it must raise `IllegalArgumentException`.”
- `HCP-CONF-025` — “WHEN validation sees `minimumIdle` greater than `maximumPoolSize`, THEN it must reduce `minimumIdle` to `maximumPoolSize`.”
- `HCP-CONF-026` — “WHEN a resizable pool has a nonzero `idleTimeout` below 10000, THEN validation must restore the 600000 millisecond default; WHEN `idleTimeout` is within one second of or greater than an enabled `maxLifetime`, THEN validation must disable idle retirement by setting `idleTimeout` to zero.”
- `HCP-CONF-027` — “WHEN a nonzero `maxLifetime` is below 30000, THEN validation must restore the 1800000 millisecond default.”
- `HCP-CONF-028` — “WHEN a nonzero `keepaliveTime` is below 30000 or is not less than an enabled `maxLifetime`, THEN validation must disable keepalive by setting it to zero.”
- `HCP-CONF-029` — “WHEN a positive `leakDetectionThreshold` is below 2000 or exceeds an enabled `maxLifetime`, THEN validation must disable leak detection by setting it to zero.”
- `HCP-CONF-030` — “WHEN `poolName` is absent, THEN validation must assign a nonempty process-unique pool name; IF JMX registration is enabled and `poolName` contains a colon, THEN validation must raise `IllegalArgumentException`.”
- `HCP-CONF-031` — “WHEN a `HikariDataSource` starts, THEN startup-only setters inherited from `HikariConfig` must become sealed and later calls to those setters must raise `IllegalStateException`.”
- `HCP-CONF-032` — “WHILE a pool is running, the `HikariConfigMXBean` setters for `connectionTimeout`, `validationTimeout`, `idleTimeout`, `leakDetectionThreshold`, `maxLifetime`, `minimumIdle`, `maximumPoolSize`, `username`, `password`, `Credentials`, and `catalog` must remain available.”
- `HCP-CONF-033` — “WHEN `setMetricsTrackerFactory` has selected a factory, THEN `setMetricRegistry` must raise `IllegalStateException`; WHEN `setMetricRegistry` has selected a registry, THEN `setMetricsTrackerFactory` must raise `IllegalStateException`.”
- `HCP-CONF-034` — “IF `setMetricRegistry` receives an object other than a supported Dropwizard or Micrometer registry, THEN it must raise `IllegalArgumentException`.”
- `HCP-CONF-035` — “IF `setHealthCheckRegistry` receives an object other than a Dropwizard `HealthCheckRegistry`, THEN it must raise `IllegalArgumentException`.”

## Pool Startup and Acquisition

- `HCP-POOL-001` — “WHEN `HikariDataSource(HikariConfig)` is constructed, THEN it must validate and copy the supplied configuration, start the pool eagerly, and seal only the copied data-source configuration.”
- `HCP-POOL-002` — “WHEN the no-argument `HikariDataSource` is constructed, THEN it must remain unstarted and configurable until the first `getConnection` call validates, starts, and seals it.”
- `HCP-POOL-003` — “WHILE the lazy data source is unstarted, `getHikariPoolMXBean` must return null, `getHikariConfigMXBean` must return the data source itself, and `isRunning` must return false.”
- `HCP-POOL-004` — “WHEN `initializationFailTimeout` is positive, THEN startup must wait for an initial physical connection after applying acquisition and validation timeouts and must raise a runtime initialization failure if no usable connection is created within the configured interval.”
- `HCP-POOL-005` — “WHEN `initializationFailTimeout` is zero, THEN startup must validate a physical connection when one is obtainable, must fail on setup or validation failure, and must continue starting when no connection is obtainable.”
- `HCP-POOL-006` — “WHEN `initializationFailTimeout` is negative, THEN startup must skip the initial connection attempt and continue physical connection creation in the background.”
- `HCP-POOL-007` — “WHEN an idle valid physical connection exists, THEN `getConnection()` must return a logical `Connection` handle and move that physical connection from the idle projection to the active projection.”
- `HCP-POOL-008` — “WHEN no idle connection exists and the total is below `maximumPoolSize`, THEN the pool must create physical connections until demand and `minimumIdle` policy are satisfied without exceeding `maximumPoolSize`.”
- `HCP-POOL-009` — “WHILE total connections equal `maximumPoolSize` and no idle connection exists, a caller must wait for at most `connectionTimeout` milliseconds for a returned connection.”
- `HCP-POOL-010` — “IF no connection becomes available before `connectionTimeout`, THEN `getConnection()` must raise `SQLTransientConnectionException` and the metrics tracker must receive a timeout event.”
- `HCP-POOL-011` — “IF a thread is interrupted while waiting for a connection, THEN `getConnection()` must restore the thread interrupt flag and raise `SQLException`.”
- `HCP-POOL-012` — “IF `HikariDataSource` has been closed, THEN `getConnection()` must raise `SQLException`.”
- `HCP-POOL-013` — “IF `getConnection(username, password)` is called, THEN the data source must raise `SQLFeatureNotSupportedException`.”
- `HCP-POOL-014` — “WHEN the pool has started, THEN `getLogWriter`, `setLogWriter`, `getLoginTimeout`, and `setLoginTimeout` must delegate to the wrapped physical data source; WHILE it is unstarted, getters must return null or zero and setters must have no effect.”
- `HCP-POOL-015` — “WHEN `unwrap(iface)` names a type implemented by the pool data source or wrapped physical data source, THEN it must return the matching instance; OTHERWISE it must delegate to the wrapped source and ultimately raise `SQLException` if no matching wrapper exists.”
- `HCP-POOL-016` — “WHEN `isWrapperFor(iface)` names a type implemented by the pool data source or wrapped physical data source, THEN it must return true; OTHERWISE it must return the wrapped source result or false before startup.”
- `HCP-POOL-017` — “IF `getParentLogger()` is called, THEN the data source must raise `SQLFeatureNotSupportedException`.”

## Borrowed Connection Lifecycle

- `HCP-CONN-001` — “WHEN a borrowed logical connection is closed, THEN it must close tracked open statements, cancel its leak timer, clear warnings, and recycle or evict the physical connection exactly once.”
- `HCP-CONN-002` — “WHEN application code changes read-only, auto-commit, transaction isolation, catalog, schema, or network timeout on a borrowed connection, THEN close must restore each changed setting to the configured pool default before recycling.”
- `HCP-CONN-003` — “WHEN non-auto-commit work has changed transaction state and the borrower closes without commit or rollback, THEN close must roll back that work before recycling.”
- `HCP-CONN-004` — “WHEN a borrowed connection is closed, THEN later operations on that logical handle must observe a closed connection and must not operate on a physical connection borrowed by another caller.”
- `HCP-CONN-005` — “IF cleanup of tracked statements or connection state raises a fatal `SQLException`, THEN the pool must evict that physical connection rather than return it to idle state.”
- `HCP-CONN-006` — “WHEN `maxLifetime` is positive and an idle physical connection reaches its scheduled lifetime, THEN the pool must retire it; WHILE that connection is active, retirement must wait until it is returned.”
- `HCP-CONN-007` — “WHEN `idleTimeout` is positive and `minimumIdle` is below `maximumPoolSize`, THEN an idle connection must not be retired before the configured timeout and the pool must not retire below `minimumIdle`.”
- `HCP-CONN-008` — “WHEN `keepaliveTime` is positive, THEN only idle connections must be removed briefly, validated through JDBC `isValid` or `connectionTestQuery`, and returned or replaced.”
- `HCP-CONN-009` — “WHEN `connectionInitSql` is configured, THEN every newly created physical connection must execute it before entering the pool; IF execution fails, THEN that creation attempt must be treated as a connection failure.”
- `HCP-CONN-010` — “WHEN `connectionTestQuery` is absent, THEN validation must use JDBC `Connection.isValid`; WHERE `connectionTestQuery` is present, validation must execute that query.”
- `HCP-CONN-011` — “WHERE `isolateInternalQueries=true` and `autoCommit=false`, internal validation queries must run in an isolated transaction.”
- `HCP-CONN-012` — “WHEN a borrowed connection remains active longer than an enabled `leakDetectionThreshold`, THEN the pool must emit a leak observation; WHEN that connection is returned, THEN its leak task must be cancelled.”
- `HCP-CONN-013` — “WHEN a JDBC operation raises `SQLException`, THEN the pool must pass the exception to a configured `SQLExceptionOverride.adjudicate` before applying built-in broken-connection detection.”
- `HCP-CONN-014` — “WHEN adjudication returns `CONTINUE_EVICT`, THEN the pool must apply its built-in SQL-state and error-code policy.”
- `HCP-CONN-015` — “WHEN adjudication returns `DO_NOT_EVICT`, THEN the pool must retain the connection unless another cleanup failure makes reuse unsafe.”
- `HCP-CONN-016` — “WHEN adjudication returns `MUST_EVICT`, THEN the pool must evict the physical connection regardless of SQL state or error code.”
- `HCP-CONN-017` — “WHEN no override is configured, THEN `SQLExceptionOverride.adjudicate` must default to `CONTINUE_EVICT` behavior.”

## Management and Runtime State

- `HCP-MGMT-001` — “`getIdleConnections`, `getActiveConnections`, `getTotalConnections`, and `getThreadsAwaitingConnection` must return transient point-in-time counts from the same live pool.”
- `HCP-MGMT-002` — “`getTotalConnections` must never exceed the current `maximumPoolSize`, and each connection must occupy exactly one idle or active ownership state at an instant.”
- `HCP-MGMT-003` — “WHEN a pool is started and neither suspended nor shut down, THEN `HikariDataSource.isRunning` must return true; WHILE it is suspended, unstarted, or shut down, it must return false.”
- `HCP-MGMT-004` — “WHEN `softEvictConnections` is called, THEN idle connections must be closed and active connections must be marked for closure when returned.”
- `HCP-MGMT-005` — “WHEN `HikariDataSource.evictConnection(connection)` receives a currently borrowed connection from that data source, THEN the physical connection must be removed immediately; WHEN it receives a returned pooled handle, THEN that physical connection must be marked for later eviction.”
- `HCP-MGMT-006` — “IF `suspendPool` is called while `allowPoolSuspension=false`, THEN it must raise `IllegalStateException`.”
- `HCP-MGMT-007` — “WHEN `suspendPool` is called while suspension is allowed, THEN later `getConnection` calls must wait without applying `connectionTimeout` until `resumePool` is called.”
- `HCP-MGMT-008` — “WHEN `resumePool` is called for a suspended pool, THEN acquisition must resume and the pool must refill toward `minimumIdle`.”
- `HCP-MGMT-009` — “WHEN `HikariDataSource.close` is called, THEN it must stop acquisition, close idle physical connections, abort or close active physical connections, unregister management projections, and close its metrics tracker.”
- `HCP-MGMT-010` — “WHEN `close` is called more than once, THEN later calls must have no effect and `isClosed` must remain true.”
- `HCP-MGMT-011` — “WHEN live `minimumIdle` or `maximumPoolSize` changes, THEN later fill and acquisition decisions must use the new bounds without invalidating already borrowed logical handles.”
- `HCP-MGMT-012` — “WHEN live credentials change, THEN existing physical connections must retain their original authentication and later physical connection creation must use the new credentials.”
- `HCP-MGMT-013` — “WHEN live `catalog` changes, THEN callers must suspend the pool and evict existing connections before relying on the new catalog across all borrowers.”

## Metrics, Health, and Naming Integrations

- `HCP-OBS-001` — “WHEN a `MetricsTrackerFactory` is configured, THEN pool startup must call `create(poolName, poolStats)` once for that pool and use the returned `IMetricsTracker`.”
- `HCP-OBS-002` — “WHEN physical connection creation completes, logical acquisition completes, a logical connection is returned, or acquisition times out, THEN the tracker must receive `recordConnectionCreatedMillis`, `recordConnectionAcquiredNanos`, `recordConnectionUsageMillis`, or `recordConnectionTimeout` respectively.”
- `HCP-OBS-003` — “WHEN the pool shuts down, THEN it must call `IMetricsTracker.close`.”
- `HCP-OBS-004` — “A `PoolStats` instance must expose total, idle, active, pending, maximum, and minimum counts through its named getters.”
- `HCP-OBS-005` — “WHEN the first stats getter after the configured refresh interval is called, THEN `PoolStats` must invoke `update` once before returning current values; WHILE the refresh interval has not elapsed, later getters must return the cached values.”
- `HCP-OBS-006` — “WHEN `CodahaleMetricsTrackerFactory` or `Dropwizard5MetricsTrackerFactory` is constructed with a registry, THEN `getRegistry` must return that same registry and `create` must bind the supplied pool name and stats to it.”
- `HCP-OBS-007` — “WHEN `MicrometerMetricsTrackerFactory` is constructed with a `MeterRegistry`, THEN `create` must publish acquisition, usage, creation, timeout, and pool-state measurements for the supplied pool name.”
- `HCP-OBS-008` — “WHEN a Prometheus factory is constructed without a registry, THEN it must use `CollectorRegistry.defaultRegistry`; WHEN constructed with a registry, THEN it must use that registry.”
- `HCP-OBS-009` — “WHEN `PrometheusMetricsTrackerFactory.create` is used, THEN it must publish summary-style timing metrics and pool-state gauges; WHEN `PrometheusHistogramMetricsTrackerFactory.create` is used, THEN it must publish histogram-style timing metrics and the same pool-state gauges.”
- `HCP-OBS-010` — “WHEN the final tracker for a Prometheus pool is closed, THEN measurements for that pool name must be removed from the associated collector.”
- `HCP-OBS-011` — “WHERE a Dropwizard `HealthCheckRegistry` is configured, pool startup must register connectivity and optional connectivity-threshold health checks using the configured health-check properties.”
- `HCP-OBS-012` — “WHEN `HikariJNDIFactory.getObjectInstance` receives a `Reference` whose class name is `javax.sql.DataSource`, THEN it must retain recognized `HikariConfig` properties and `dataSource.` properties and must return a configured pooled data source.”
- `HCP-OBS-013` — “WHERE the accepted reference includes `dataSourceJNDI`, the factory must look up that underlying `DataSource` and wrap it with the remaining configuration.”
- `HCP-OBS-014` — “WHEN `getObjectInstance` receives any other object or reference class, THEN it must return null.”
- `HCP-OBS-015` — “IF an accepted `dataSourceJNDI` reference has no usable naming context or lookup result, THEN factory creation must raise a naming or runtime lookup failure.”

## State Model

- `HCP-STATE-001` — “WHILE a logical handle is active, its physical connection must contribute to active and total projections and must not contribute to idle projection.”
- `HCP-STATE-002` — “WHEN that logical handle closes successfully, THEN the same physical connection must move to idle projection after reset or must leave total projection after eviction.”
- `HCP-STATE-003` — “WHEN configuration changes through an allowed live setter, THEN the configuration MXBean getter and every later affected pool decision must reflect the same value.”
- `HCP-STATE-004` — “WHEN the pool state changes through start, suspend, resume, or close, THEN `isRunning`, acquisition behavior, management availability, and metrics lifecycle must reflect that transition together.”

## Error Semantics

- `HCP-ERR-001` — “IF a named configuration resource is missing, THEN construction must raise `IllegalArgumentException`.”
- `HCP-ERR-002` — “IF source selection is invalid or absent, THEN validation must raise `IllegalStateException` for `dataSourceClassName` plus `driverClassName`, otherwise `IllegalArgumentException`.”
- `HCP-ERR-003` — “IF connection, validation, idle, minimum-idle, or maximum-size setter bounds are violated, THEN the setter must raise `IllegalArgumentException`.”
- `HCP-ERR-004` — “IF a sealed startup-only setter is called, THEN it must raise `IllegalStateException`.”
- `HCP-ERR-005` — “IF a registry has an unsupported type, THEN its setter must raise `IllegalArgumentException`.”
- `HCP-ERR-006` — “IF both metric-registry and metrics-factory paths are selected, THEN the second setter must raise `IllegalStateException`.”
- `HCP-ERR-007` — “IF no connection becomes available within `connectionTimeout`, THEN `getConnection` must raise `SQLTransientConnectionException`.”
- `HCP-ERR-008` — “IF acquisition is interrupted, THEN `getConnection` must restore interruption and raise `SQLException`.”
- `HCP-ERR-009` — “IF `getConnection` is called after close, THEN it must raise `SQLException`.”
- `HCP-ERR-010` — “IF credentialed `getConnection` or `getParentLogger` is called, THEN it must raise `SQLFeatureNotSupportedException`.”
- `HCP-ERR-011` — “IF no wrapped object implements the requested type, THEN `unwrap` must raise `SQLException`.”
- `HCP-ERR-012` — “IF `suspendPool` is called while suspension is disabled, THEN it must raise `IllegalStateException`.”
- `HCP-ERR-013` — “IF an accepted reference cannot resolve its underlying data source, THEN JNDI creation must raise a naming or runtime lookup failure.”

## Cross-View Invariants

- `HCP-INV-001` — “A successful `getConnection` must increase or preserve total connections, must project one borrowed handle as active, and must emit acquisition metrics for the same pool name.”
- `HCP-INV-002` — “WHEN a healthy borrowed handle closes, THEN active ownership must decrease, idle ownership must increase or replacement must begin, and usage metrics must be emitted exactly once for that borrow.”
- `HCP-INV-003` — “The values returned by `HikariPoolMXBean` and `PoolStats` must describe the same live pool even when separately sampled values are transient.”
- `HCP-INV-004` — “A `maximumPoolSize` value returned by `HikariConfigMXBean` must bound physical total connections and must determine when later acquisitions wait.”
- `HCP-INV-005` — “A `minimumIdle` value returned by `HikariConfigMXBean` must govern later refill decisions and idle retirement without forcing active connections closed.”
- `HCP-INV-006` — “WHEN soft eviction is requested through the pool MXBean or explicit eviction is requested through the data source, THEN the selected physical connections must be removed from later idle reuse and from total metrics after closure completes.”
- `HCP-INV-007` — “WHEN a pool is suspended, THEN `isRunning` must become false and later acquisition must block without timeout; WHEN it is resumed, THEN `isRunning` must become true and waiting acquisition must be released.”
- `HCP-INV-008` — “WHEN the data source closes, THEN `isClosed` must become true, `isRunning` must become false, later acquisition must fail, management registration must end, and the metrics tracker must close.”
- `HCP-INV-009` — “A credential pair returned by `HikariConfig.getCredentials` must agree with username/password accessors and must be the pair used for later physical `DataSource.getConnection(username, password)` creation when no provider overrides it.”
- `HCP-INV-010` — “A pool produced by `HikariJNDIFactory` must expose the same configuration, acquisition, management, metrics, reset, and shutdown behavior as a directly constructed `HikariDataSource`.”

## CLI Entry Points

- `HCP-CLI-001` — “There is no console script for this package.”
- `HCP-CLI-002` — “`java -jar HikariCP.jar` is not supported.”
- `HCP-CLI-003` — “Programmatic use is through Java imports.”

## Maven Build Surface

- `HCP-BUILD-001` — “The project program file must be a root `pom.xml`.”
- `HCP-BUILD-002` — “It must declare Maven coordinates `com.zaxxer:HikariCP`, compile main sources for Java 11 compatibility while running under the provided JDK, and produce the library classes through the normal Maven lifecycle.”
