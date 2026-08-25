package integration;

import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariDataSource;
import com.zaxxer.hikari.HikariJNDIFactory;
import com.zaxxer.hikari.HikariPoolMXBean;
import com.zaxxer.hikari.util.Credentials;
import org.junit.jupiter.api.Test;
import support.ControllableDataSource;
import support.RecordingMetrics;

import javax.naming.NamingException;
import javax.naming.Reference;
import javax.naming.StringRefAddr;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.sql.Connection;
import java.sql.SQLException;
import java.sql.SQLTransientConnectionException;
import java.sql.Statement;
import java.util.concurrent.Callable;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.BooleanSupplier;

import static org.junit.jupiter.api.Assertions.*;

/** Cross-boundary public-contract tests for pool composition and projections. */
public class HikariIntegrationTest {
   private static HikariConfig config(ControllableDataSource physical, String name) {
      HikariConfig config = new HikariConfig();
      config.setDataSource(physical);
      config.setPoolName(name);
      config.setMaximumPoolSize(3);
      config.setMinimumIdle(1);
      config.setConnectionTimeout(300);
      return config;
   }

   private static void await(BooleanSupplier condition) throws Exception {
      long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(3);
      while (!condition.getAsBoolean() && System.nanoTime() < deadline) {
         Thread.sleep(10);
      }
      assertTrue(condition.getAsBoolean());
   }

   /** Verifies: HCP-POOL-001, HCP-WF-001. Seam: lifecycle crossing. CVI-8. Depends-On: copyStateCopiesValues, lazyDataSourceStartsUnstarted. */
   @Test void eagerConstructionStartsCopiedConfiguration() {
      ControllableDataSource physical = new ControllableDataSource();
      HikariConfig original = config(physical, "eager-copy");
      try (HikariDataSource dataSource = new HikariDataSource(original)) {
         original.setPoolName("original-remains-open");
         assertAll(() -> assertTrue(dataSource.isRunning()),
            () -> assertEquals("eager-copy", dataSource.getPoolName()),
            () -> assertEquals("original-remains-open", original.getPoolName()));
      }
   }

   /** Verifies: HCP-POOL-002, HCP-STATE-004. Seam: lifecycle crossing. CVI-8. Depends-On: lazyDataSourceStartsUnstarted. */
   @Test void lazyBorrowStartsPoolAndManagementView() throws Exception {
      HikariDataSource dataSource = new HikariDataSource();
      dataSource.setDataSource(new ControllableDataSource());
      dataSource.setPoolName("lazy-start");
      dataSource.setMinimumIdle(0);
      try (Connection ignored = dataSource.getConnection()) {
         assertAll(() -> assertTrue(dataSource.isRunning()),
            () -> assertNotNull(dataSource.getHikariPoolMXBean()));
      } finally { dataSource.close(); }
   }

   /** Verifies: HCP-POOL-007, HCP-MGMT-001, HCP-STATE-001, HCP-INV-001. Seam: state consistency. CVI-1. Depends-On: lazyDataSourceStartsUnstarted, poolStatsExposesActiveAndPending. */
   @Test void borrowedHandleProjectsAsActive() throws Exception {
      try (HikariDataSource dataSource = new HikariDataSource(config(new ControllableDataSource(), "active-view"));
           Connection connection = dataSource.getConnection()) {
         HikariPoolMXBean pool = dataSource.getHikariPoolMXBean();
         assertAll(() -> assertFalse(connection.isClosed()), () -> assertEquals(1, pool.getActiveConnections()),
            () -> assertEquals(0, pool.getIdleConnections()));
      }
   }

   /** Verifies: HCP-CONN-001, HCP-STATE-002, HCP-INV-002. Seam: state consistency. CVI-2. Depends-On: poolStatsExposesActiveAndPending, repeatedCloseKeepsClosedState. */
   @Test void closeMovesOwnershipToIdle() throws Exception {
      try (HikariDataSource dataSource = new HikariDataSource(config(new ControllableDataSource(), "idle-view"))) {
         Connection connection = dataSource.getConnection();
         connection.close();
         assertAll(() -> assertEquals(0, dataSource.getHikariPoolMXBean().getActiveConnections()),
            () -> assertEquals(1, dataSource.getHikariPoolMXBean().getIdleConnections()));
      }
   }

   /** Verifies: HCP-MGMT-001, HCP-MGMT-002, HCP-INV-003. Seam: state consistency. CVI-3. Depends-On: poolStatsExposesActiveAndPending, poolStatsTotalTriggersRefresh. */
   @Test void poolCountersShareOneOwnershipSet() throws Exception {
      try (HikariDataSource dataSource = new HikariDataSource(config(new ControllableDataSource(), "counter-balance"));
           Connection connection = dataSource.getConnection()) {
         HikariPoolMXBean pool = dataSource.getHikariPoolMXBean();
         assertEquals(pool.getTotalConnections(), pool.getActiveConnections() + pool.getIdleConnections());
      }
   }

   /** Verifies: HCP-POOL-008, HCP-MGMT-002, HCP-INV-004. Seam: config interaction. CVI-4. Depends-On: zeroMaximumPoolSizeIsRejected, poolStatsExposesActiveAndPending. */
   @Test void maximumPoolSizeBoundsPhysicalTotal() throws Exception {
      ControllableDataSource physical = new ControllableDataSource();
      HikariConfig config = config(physical, "max-bound");
      config.setMaximumPoolSize(2);
      config.setMinimumIdle(0);
      try (HikariDataSource dataSource = new HikariDataSource(config);
           Connection first = dataSource.getConnection(); Connection second = dataSource.getConnection()) {
         assertAll(() -> assertEquals(2, dataSource.getHikariPoolMXBean().getTotalConnections()),
            () -> assertEquals(2, dataSource.getHikariPoolMXBean().getActiveConnections()));
      }
   }

   /** Verifies: HCP-POOL-009, HCP-POOL-010, HCP-ERR-007, HCP-INV-004. Seam: error propagation. CVI-4. Depends-On: zeroConnectionTimeoutMeansEffectivelyUnbounded, poolStatsExposesBounds. */
   @Test void saturationRaisesTransientTimeout() throws Exception {
      HikariConfig config = config(new ControllableDataSource(), "saturation-timeout");
      config.setMaximumPoolSize(1);
      config.setMinimumIdle(0);
      config.setConnectionTimeout(250);
      try (HikariDataSource dataSource = new HikariDataSource(config);
           Connection held = dataSource.getConnection()) {
         assertThrows(SQLTransientConnectionException.class, dataSource::getConnection);
      }
   }

   /** Verifies: HCP-POOL-012, HCP-ERR-009, HCP-INV-008. Seam: lifecycle crossing. CVI-8. Depends-On: repeatedCloseKeepsClosedState. */
   @Test void closedDataSourceRejectsLaterBorrow() {
      HikariDataSource dataSource = new HikariDataSource(config(new ControllableDataSource(), "closed-borrow"));
      dataSource.close();
      assertThrows(SQLException.class, dataSource::getConnection);
   }

   /** Verifies: HCP-CONF-031, HCP-ERR-004. Seam: config interaction. CVI-8. Depends-On: copyStateCopiesValues, lazyDataSourceStartsUnstarted. */
   @Test void startedPoolSealsStartupOnlySetters() {
      try (HikariDataSource dataSource = new HikariDataSource(config(new ControllableDataSource(), "sealed-startup"))) {
         assertThrows(IllegalStateException.class,
            () -> dataSource.setDataSourceClassName(ControllableDataSource.class.getName()));
      }
   }

   /** Verifies: HCP-POOL-014. Seam: protocol handoff. CVI-10. Depends-On: unstartedDelegationDefaultsAreStable. */
   @Test void startedLogWriterDelegatesToPhysicalSource() throws Exception {
      ControllableDataSource physical = new ControllableDataSource();
      try (HikariDataSource dataSource = new HikariDataSource(config(physical, "log-delegate"))) {
         PrintWriter writer = new PrintWriter(new StringWriter());
         dataSource.setLogWriter(writer);
         assertSame(writer, dataSource.getLogWriter());
      }
   }

   /** Verifies: HCP-POOL-014. Seam: protocol handoff. CVI-10. Depends-On: unstartedDelegationDefaultsAreStable. */
   @Test void startedLoginTimeoutDelegatesToPhysicalSource() throws Exception {
      ControllableDataSource physical = new ControllableDataSource();
      try (HikariDataSource dataSource = new HikariDataSource(config(physical, "timeout-delegate"))) {
         dataSource.setLoginTimeout(17);
         assertEquals(17, dataSource.getLoginTimeout());
      }
   }

   /** Verifies: HCP-POOL-015, HCP-POOL-016. Seam: protocol handoff. CVI-10. Depends-On: unstartedDataSourceWrapsItself. */
   @Test void wrapperQueriesReachPoolAndPhysicalSource() throws Exception {
      ControllableDataSource physical = new ControllableDataSource();
      try (HikariDataSource dataSource = new HikariDataSource(config(physical, "wrapper-view"))) {
         assertAll(() -> assertSame(dataSource, dataSource.unwrap(HikariDataSource.class)),
            () -> assertSame(physical, dataSource.unwrap(ControllableDataSource.class)),
            () -> assertTrue(dataSource.isWrapperFor(ControllableDataSource.class)));
      }
   }

   /** Verifies: HCP-CONF-018, HCP-CONN-002. Seam: state consistency. CVI-2. Depends-On: connectionDefaultAccessorsRetainValues, poolStatsIdleUsesCachedRefresh. */
   @Test void closeRestoresAutoCommitDefault() throws Exception {
      ControllableDataSource physical = new ControllableDataSource();
      try (HikariDataSource dataSource = new HikariDataSource(config(physical, "reset-autocommit"))) {
         Connection connection = dataSource.getConnection();
         connection.setAutoCommit(false);
         connection.close();
         assertTrue(physical.lastPhysicalState().autoCommit);
      }
   }

   /** Verifies: HCP-CONF-018, HCP-CONN-002. Seam: state consistency. CVI-2. Depends-On: connectionDefaultAccessorsRetainValues, poolStatsIdleUsesCachedRefresh. */
   @Test void closeRestoresReadOnlyDefault() throws Exception {
      ControllableDataSource physical = new ControllableDataSource();
      try (HikariDataSource dataSource = new HikariDataSource(config(physical, "reset-readonly"))) {
         Connection connection = dataSource.getConnection();
         connection.setReadOnly(true);
         connection.close();
         assertFalse(physical.lastPhysicalState().readOnly);
      }
   }

   /** Verifies: HCP-CONF-018, HCP-CONN-002. Seam: state consistency. CVI-2. Depends-On: connectionDefaultAccessorsRetainValues, poolStatsIdleUsesCachedRefresh. */
   @Test void closeRestoresTransactionIsolationDefault() throws Exception {
      ControllableDataSource physical = new ControllableDataSource();
      try (HikariDataSource dataSource = new HikariDataSource(config(physical, "reset-isolation"))) {
         Connection connection = dataSource.getConnection();
         connection.setTransactionIsolation(Connection.TRANSACTION_SERIALIZABLE);
         connection.close();
         assertEquals(Connection.TRANSACTION_READ_COMMITTED, physical.lastPhysicalState().transactionIsolation);
      }
   }

   /** Verifies: HCP-CONF-018, HCP-CONN-002. Seam: state consistency. CVI-2. Depends-On: connectionDefaultAccessorsRetainValues, poolStatsIdleUsesCachedRefresh. */
   @Test void closeRestoresCatalogAndSchemaDefaults() throws Exception {
      ControllableDataSource physical = new ControllableDataSource();
      HikariConfig config = config(physical, "reset-catalog-schema");
      config.setCatalog("base_catalog");
      config.setSchema("base_schema");
      try (HikariDataSource dataSource = new HikariDataSource(config)) {
         Connection connection = dataSource.getConnection();
         connection.setCatalog("borrow_catalog");
         connection.setSchema("borrow_schema");
         connection.close();
         assertAll(() -> assertEquals("base_catalog", physical.lastPhysicalState().catalog),
            () -> assertEquals("base_schema", physical.lastPhysicalState().schema));
      }
   }

   /** Verifies: HCP-CONN-002. Seam: state consistency. CVI-2. Depends-On: connectionDefaultAccessorsRetainValues. */
   @Test void closeRestoresNetworkTimeout() throws Exception {
      ControllableDataSource physical = new ControllableDataSource();
      try (HikariDataSource dataSource = new HikariDataSource(config(physical, "reset-network-timeout"))) {
         Connection connection = dataSource.getConnection();
         connection.setNetworkTimeout(Runnable::run, 321);
         connection.close();
         assertEquals(0, physical.lastPhysicalState().networkTimeout);
      }
   }

   /** Verifies: HCP-CONN-003. Seam: lifecycle crossing. CVI-2. Depends-On: connectionDefaultAccessorsRetainValues, poolStatsIdleUsesCachedRefresh. */
   @Test void dirtyNonAutoCommitWorkRollsBackOnClose() throws Exception {
      ControllableDataSource physical = new ControllableDataSource();
      HikariConfig config = config(physical, "rollback-close");
      config.setAutoCommit(false);
      try (HikariDataSource dataSource = new HikariDataSource(config)) {
         Connection connection = dataSource.getConnection();
         connection.createStatement().execute("public carrier operation");
         connection.close();
         assertEquals(1, physical.rollbacks.get());
      }
   }

   /** Verifies: HCP-CONN-001. Seam: lifecycle crossing. CVI-2. Depends-On: poolStatsIdleUsesCachedRefresh. */
   @Test void connectionCloseClosesTrackedStatements() throws Exception {
      ControllableDataSource physical = new ControllableDataSource();
      try (HikariDataSource dataSource = new HikariDataSource(config(physical, "statement-close"))) {
         Connection connection = dataSource.getConnection();
         Statement statement = connection.createStatement();
         connection.close();
         assertAll(() -> assertTrue(statement.isClosed()), () -> assertEquals(1, physical.statementsClosed.get()));
      }
   }

   /** Verifies: HCP-CONN-004. Seam: lifecycle crossing. CVI-2. Depends-On: repeatedCloseKeepsClosedState, poolStatsIdleUsesCachedRefresh. */
   @Test void returnedLogicalHandleRemainsClosed() throws Exception {
      try (HikariDataSource dataSource = new HikariDataSource(config(new ControllableDataSource(), "logical-close"))) {
         Connection returned = dataSource.getConnection();
         returned.close();
         try (Connection next = dataSource.getConnection()) {
            assertAll(() -> assertTrue(returned.isClosed()), () -> assertFalse(next.isClosed()),
               () -> assertNotSame(returned, next));
         }
      }
   }

   /** Verifies: HCP-MGMT-011, HCP-STATE-003, HCP-INV-004. Seam: config interaction. CVI-4. Depends-On: poolStatsExposesBounds. */
   @Test void liveMaximumPoolSizeChangesConfigProjection() {
      try (HikariDataSource dataSource = new HikariDataSource(config(new ControllableDataSource(), "live-max"))) {
         dataSource.getHikariConfigMXBean().setMaximumPoolSize(5);
         assertAll(() -> assertEquals(5, dataSource.getHikariConfigMXBean().getMaximumPoolSize()),
            () -> assertTrue(dataSource.getHikariPoolMXBean().getTotalConnections() <= 5));
      }
   }

   /** Verifies: HCP-MGMT-011, HCP-STATE-003, HCP-INV-005. Seam: config interaction. CVI-5. Depends-On: validationClampsMinimumIdleToMaximum. */
   @Test void liveMinimumIdleChangesRefillProjection() throws Exception {
      try (HikariDataSource dataSource = new HikariDataSource(config(new ControllableDataSource(), "live-min"))) {
         dataSource.getHikariConfigMXBean().setMinimumIdle(2);
         await(() -> dataSource.getHikariPoolMXBean().getIdleConnections() >= 2);
         assertAll(() -> assertEquals(2, dataSource.getHikariConfigMXBean().getMinimumIdle()),
            () -> assertTrue(dataSource.getHikariPoolMXBean().getIdleConnections() >= 2));
      }
   }

   /** Verifies: HCP-OBS-001, HCP-INV-001. Seam: protocol handoff. CVI-1. Depends-On: poolStatsTotalTriggersRefresh, copyStateCopiesValues. */
   @Test void metricsFactoryReceivesPoolIdentityAndStats() {
      RecordingMetrics metrics = new RecordingMetrics();
      HikariConfig config = config(new ControllableDataSource(), "metrics-identity");
      config.setMetricsTrackerFactory(metrics);
      try (HikariDataSource ignored = new HikariDataSource(config)) {
         assertAll(() -> assertEquals(1, metrics.createCalls.get()),
            () -> assertEquals("metrics-identity", metrics.poolName), () -> assertNotNull(metrics.poolStats));
      }
   }

   /** Verifies: HCP-OBS-002, HCP-INV-001. Seam: protocol handoff. CVI-1. Depends-On: metricsFactoryThenRegistryIsRejected, poolStatsExposesActiveAndPending. */
   @Test void successfulBorrowEmitsAcquisitionMetric() throws Exception {
      RecordingMetrics metrics = new RecordingMetrics();
      HikariConfig config = config(new ControllableDataSource(), "metrics-acquire");
      config.setMetricsTrackerFactory(metrics);
      try (HikariDataSource dataSource = new HikariDataSource(config);
           Connection ignored = dataSource.getConnection()) {
         assertAll(() -> assertEquals(1, metrics.acquiredCalls.get()),
            () -> assertTrue(metrics.lastAcquiredNanos.get() >= 0));
      }
   }

   /** Verifies: HCP-OBS-002, HCP-INV-002. Seam: protocol handoff. CVI-2. Depends-On: poolStatsExposesActiveAndPending, poolStatsIdleUsesCachedRefresh. */
   @Test void returnedBorrowEmitsUsageMetricOnce() throws Exception {
      RecordingMetrics metrics = new RecordingMetrics();
      HikariConfig config = config(new ControllableDataSource(), "metrics-usage");
      config.setMetricsTrackerFactory(metrics);
      try (HikariDataSource dataSource = new HikariDataSource(config)) {
         Connection connection = dataSource.getConnection();
         connection.close();
         connection.close();
         assertEquals(1, metrics.usageCalls.get());
      }
   }

   /** Verifies: HCP-OBS-002, HCP-POOL-010. Seam: error propagation. CVI-4. Depends-On: tooSmallConnectionTimeoutIsRejected, metricsFactoryThenRegistryIsRejected. */
   @Test void acquisitionTimeoutEmitsTimeoutMetric() throws Exception {
      RecordingMetrics metrics = new RecordingMetrics();
      HikariConfig config = config(new ControllableDataSource(), "metrics-timeout");
      config.setMaximumPoolSize(1);
      config.setMinimumIdle(0);
      config.setConnectionTimeout(250);
      config.setMetricsTrackerFactory(metrics);
      try (HikariDataSource dataSource = new HikariDataSource(config);
           Connection held = dataSource.getConnection()) {
         assertThrows(SQLTransientConnectionException.class, dataSource::getConnection);
         assertEquals(1, metrics.timeoutCalls.get());
      }
   }

   /** Verifies: HCP-OBS-003, HCP-MGMT-009, HCP-INV-008. Seam: lifecycle crossing. CVI-8. Depends-On: metricsFactoryThenRegistryIsRejected, repeatedCloseKeepsClosedState. */
   @Test void dataSourceCloseClosesMetricsTracker() {
      RecordingMetrics metrics = new RecordingMetrics();
      HikariConfig config = config(new ControllableDataSource(), "metrics-close");
      config.setMetricsTrackerFactory(metrics);
      HikariDataSource dataSource = new HikariDataSource(config);
      dataSource.close();
      assertEquals(1, metrics.closeCalls.get());
   }

   /** Verifies: HCP-OBS-004, HCP-INV-003. Seam: state consistency. CVI-3. Depends-On: poolStatsExposesBounds, poolStatsTotalTriggersRefresh. */
   @Test void metricsStatsAndMxBeanDescribeSamePool() throws Exception {
      RecordingMetrics metrics = new RecordingMetrics();
      HikariConfig config = config(new ControllableDataSource(), "metrics-stats");
      config.setMetricsTrackerFactory(metrics);
      try (HikariDataSource dataSource = new HikariDataSource(config);
           Connection ignored = dataSource.getConnection()) {
         assertAll(() -> assertEquals(dataSource.getHikariPoolMXBean().getTotalConnections(), metrics.poolStats.getTotalConnections()),
            () -> assertEquals(dataSource.getHikariPoolMXBean().getActiveConnections(), metrics.poolStats.getActiveConnections()));
      }
   }

   /** Verifies: HCP-MGMT-006, HCP-ERR-012. Seam: error propagation. CVI-7. Depends-On: defaultSuspensionIsDisabled, copyStateCopiesValues. */
   @Test void disabledSuspensionRaisesIllegalState() {
      try (HikariDataSource dataSource = new HikariDataSource(config(new ControllableDataSource(), "suspend-disabled"))) {
         assertThrows(IllegalStateException.class, dataSource.getHikariPoolMXBean()::suspendPool);
      }
   }

   /** Verifies: HCP-MGMT-007, HCP-MGMT-008, HCP-INV-007. Seam: lifecycle crossing. CVI-7. Depends-On: defaultSuspensionIsDisabled, poolStatsExposesActiveAndPending. */
   @Test void suspensionAndResumptionChangeRunningView() {
      HikariConfig config = config(new ControllableDataSource(), "suspend-view");
      config.setAllowPoolSuspension(true);
      try (HikariDataSource dataSource = new HikariDataSource(config)) {
         dataSource.getHikariPoolMXBean().suspendPool();
         assertFalse(dataSource.isRunning());
         dataSource.getHikariPoolMXBean().resumePool();
         assertTrue(dataSource.isRunning());
      }
   }

   /** Verifies: HCP-MGMT-007, HCP-MGMT-008, HCP-INV-007. Seam: lifecycle crossing. CVI-7. Depends-On: defaultSuspensionIsDisabled, poolStatsExposesActiveAndPending. */
   @Test void suspendedBorrowWaitsUntilResume() throws Exception {
      HikariConfig config = config(new ControllableDataSource(), "suspend-borrow");
      config.setAllowPoolSuspension(true);
      try (HikariDataSource dataSource = new HikariDataSource(config)) {
         dataSource.getHikariPoolMXBean().suspendPool();
         CompletableFuture<Connection> waiting = CompletableFuture.supplyAsync(() -> {
            try { return dataSource.getConnection(); } catch (SQLException error) { throw new RuntimeException(error); }
         });
         Thread.sleep(100);
         assertFalse(waiting.isDone());
         dataSource.getHikariPoolMXBean().resumePool();
         try (Connection resumed = waiting.get(2, TimeUnit.SECONDS)) { assertFalse(resumed.isClosed()); }
      }
   }

   /** Verifies: HCP-POOL-011, HCP-ERR-008. Seam: error propagation. CVI-4. Depends-On: tooSmallConnectionTimeoutIsRejected, poolStatsExposesBounds. */
   @Test void interruptedWaitingBorrowRestoresFlagAndRaisesSqlException() throws Exception {
      HikariConfig config = config(new ControllableDataSource(), "interrupt-waiter");
      config.setMaximumPoolSize(1);
      config.setMinimumIdle(0);
      config.setConnectionTimeout(5_000);
      try (HikariDataSource dataSource = new HikariDataSource(config);
           Connection held = dataSource.getConnection()) {
         AtomicReference<Throwable> observed = new AtomicReference<>();
         AtomicBoolean interrupted = new AtomicBoolean();
         Thread waiter = new Thread(() -> {
            try { dataSource.getConnection(); }
            catch (Throwable error) { observed.set(error); interrupted.set(Thread.currentThread().isInterrupted()); }
         });
         waiter.start();
         await(() -> dataSource.getHikariPoolMXBean().getThreadsAwaitingConnection() == 1);
         waiter.interrupt();
         waiter.join(2_000);
         assertAll(() -> assertInstanceOf(SQLException.class, observed.get()),
            () -> assertTrue(interrupted.get()), () -> assertFalse(waiter.isAlive()));
      }
   }

   /** Verifies: HCP-MGMT-004, HCP-INV-006. Seam: lifecycle crossing. CVI-6. Depends-On: poolStatsIdleUsesCachedRefresh, poolStatsTotalTriggersRefresh. */
   @Test void softEvictionRemovesIdlePhysicalConnection() throws Exception {
      ControllableDataSource physical = new ControllableDataSource();
      try (HikariDataSource dataSource = new HikariDataSource(config(physical, "soft-evict"))) {
         int before = physical.physicalCloses.get();
         dataSource.getHikariPoolMXBean().softEvictConnections();
         await(() -> physical.physicalCloses.get() > before);
         try (Connection replacement = dataSource.getConnection()) { assertFalse(replacement.isClosed()); }
      }
   }

   /** Verifies: HCP-MGMT-005, HCP-INV-006. Seam: lifecycle crossing. CVI-6. Depends-On: poolStatsExposesActiveAndPending, poolStatsIdleUsesCachedRefresh. */
   @Test void explicitEvictionRemovesBorrowedPhysicalConnection() throws Exception {
      ControllableDataSource physical = new ControllableDataSource();
      try (HikariDataSource dataSource = new HikariDataSource(config(physical, "explicit-evict"))) {
         Connection connection = dataSource.getConnection();
         dataSource.evictConnection(connection);
         await(() -> physical.physicalCloses.get() >= 1);
         connection.close();
         try (Connection replacement = dataSource.getConnection()) {
            assertFalse(replacement.isClosed());
         }
      }
   }

   /** Verifies: HCP-MGMT-009, HCP-INV-008. Seam: lifecycle crossing. CVI-8. Depends-On: repeatedCloseKeepsClosedState, poolStatsIdleUsesCachedRefresh. */
   @Test void shutdownClosesIdlePhysicalConnections() throws Exception {
      ControllableDataSource physical = new ControllableDataSource();
      HikariDataSource dataSource = new HikariDataSource(config(physical, "shutdown-physical"));
      try (Connection ignored = dataSource.getConnection()) { assertFalse(ignored.isClosed()); }
      dataSource.close();
      assertAll(() -> assertTrue(dataSource.isClosed()), () -> assertFalse(dataSource.isRunning()),
         () -> assertTrue(physical.physicalCloses.get() >= 1));
   }

   /** Verifies: HCP-CONF-015, HCP-INV-009. Seam: protocol handoff. CVI-9. Depends-On: configCredentialsStayAtomic, copyStateCopiesValues. */
   @Test void staticCredentialsReachPhysicalDataSource() {
      ControllableDataSource physical = new ControllableDataSource();
      HikariConfig config = config(physical, "static-credentials");
      config.setCredentials(Credentials.of("orchid-user", "orchid-pass"));
      try (HikariDataSource ignored = new HikariDataSource(config)) {
         assertAll(() -> assertEquals(1, physical.credentialedCalls.get()),
            () -> assertEquals("orchid-user", physical.lastUsername),
            () -> assertEquals("orchid-pass", physical.lastPassword));
      }
   }

   /** Verifies: HCP-CONF-016, HCP-INV-009. Seam: protocol handoff. CVI-9. Depends-On: configCredentialsStayAtomic, credentialsFactoryExposesPair. */
   @Test void credentialProviderOverridesStaticPair() {
      ControllableDataSource physical = new ControllableDataSource();
      HikariConfig config = config(physical, "provider-credentials");
      config.setCredentials(Credentials.of("static-user", "static-pass"));
      config.setCredentialsProvider(() -> Credentials.of("provider-user", "provider-pass"));
      try (HikariDataSource ignored = new HikariDataSource(config)) {
         assertAll(() -> assertEquals("provider-user", physical.lastUsername),
            () -> assertEquals("provider-pass", physical.lastPassword));
      }
   }

   /** Verifies: HCP-CONN-009. Seam: protocol handoff. CVI-1. Depends-On: dataSourcePropertyIsObservable, copyStateCopiesValues. */
   @Test void connectionInitSqlRunsOnPhysicalCreation() {
      ControllableDataSource physical = new ControllableDataSource();
      HikariConfig config = config(physical, "init-sql");
      config.setConnectionInitSql("PUBLIC CARRIER INIT");
      try (HikariDataSource ignored = new HikariDataSource(config)) {
         assertAll(() -> assertEquals(1, physical.statementsCreated.get()),
            () -> assertEquals(1, physical.statementsClosed.get()));
      }
   }

   /** Verifies: HCP-OBS-002, HCP-INV-001. Seam: protocol handoff. CVI-1. Depends-On: metricsFactoryThenRegistryIsRejected, copyStateCopiesValues. */
   @Test void physicalCreationEmitsCreationMetric() throws Exception {
      RecordingMetrics metrics = new RecordingMetrics();
      HikariConfig config = config(new ControllableDataSource(), "metrics-created");
      config.setMinimumIdle(0);
      config.setMetricsTrackerFactory(metrics);
      try (HikariDataSource dataSource = new HikariDataSource(config);
           Connection ignored = dataSource.getConnection()) {
         await(() -> metrics.createdCalls.get() >= 1);
         assertTrue(metrics.createdCalls.get() >= 1);
      }
   }

   /** Verifies: HCP-OBS-012, HCP-INV-010. Seam: protocol handoff. CVI-10. Depends-On: propertiesConstructorUsesBeanNames, copyStateCopiesValues. */
   @Test void jndiFactoryCreatesEquivalentPooledDataSource() throws Exception {
      Reference reference = new Reference("javax.sql.DataSource");
      reference.add(new StringRefAddr("dataSourceClassName", ControllableDataSource.class.getName()));
      reference.add(new StringRefAddr("poolName", "jndi-public-pool"));
      reference.add(new StringRefAddr("maximumPoolSize", "2"));
      reference.add(new StringRefAddr("minimumIdle", "1"));
      Object produced = new HikariJNDIFactory().getObjectInstance(reference, null, null, null);
      assertInstanceOf(HikariDataSource.class, produced);
      try (HikariDataSource dataSource = (HikariDataSource) produced;
           Connection connection = dataSource.getConnection()) {
         assertAll(() -> assertEquals("jndi-public-pool", dataSource.getPoolName()),
            () -> assertTrue(dataSource.isRunning()), () -> assertFalse(connection.isClosed()));
      }
   }

   /** Verifies: HCP-OBS-013, HCP-OBS-015, HCP-ERR-013. Seam: error propagation. CVI-10. Depends-On: propertiesConstructorUsesBeanNames, missingNamedResourceRaisesIllegalArgument. */
   @Test void unresolvedJndiSourceFailsDeterministically() throws Exception {
      Reference reference = new Reference("javax.sql.DataSource");
      reference.add(new StringRefAddr("dataSourceJNDI", "java:comp/env/jdbc/absent-stage3"));
      Callable<Object> lookup =
         () -> new HikariJNDIFactory().getObjectInstance(reference, null, null, null);
      Object acceptedFailure = null;
      try {
         lookup.call();
      }
      catch (NamingException | RuntimeException expected) {
         acceptedFailure = expected;
      }
      assertNotNull(acceptedFailure);
   }

   /** Verifies: HCP-MGMT-011, HCP-INV-005. Seam: config interaction. CVI-5. Depends-On: validationClampsMinimumIdleToMaximum, poolStatsIdleUsesCachedRefresh. */
   @Test void loweringMinimumIdleDoesNotCloseBorrowedHandle() throws Exception {
      try (HikariDataSource dataSource = new HikariDataSource(config(new ControllableDataSource(), "lower-min"));
           Connection connection = dataSource.getConnection()) {
         dataSource.getHikariConfigMXBean().setMinimumIdle(0);
         assertAll(() -> assertEquals(0, dataSource.getHikariConfigMXBean().getMinimumIdle()),
            () -> assertFalse(connection.isClosed()),
            () -> assertEquals(1, dataSource.getHikariPoolMXBean().getActiveConnections()));
      }
   }
}
