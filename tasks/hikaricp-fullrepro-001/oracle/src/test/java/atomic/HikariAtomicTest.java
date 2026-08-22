package atomic;

import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariDataSource;
import com.zaxxer.hikari.SQLExceptionOverride;
import com.zaxxer.hikari.util.Credentials;
import org.junit.jupiter.api.Test;
import support.ControllableDataSource;
import support.ObservedPoolStats;
import support.PublicDriver;
import support.RecordingMetrics;

import java.sql.Connection;
import java.sql.SQLException;
import java.util.Properties;

import static org.junit.jupiter.api.Assertions.*;

/** Atomic public-contract tests for configuration, state carriers, and simple lifecycle queries. */
public class HikariAtomicTest {
   private static HikariConfig configWithSource() {
      HikariConfig config = new HikariConfig();
      config.setDataSource(new ControllableDataSource());
      return config;
   }

   /** Verifies: HCP-CONF-001. */
   @Test void defaultAutoCommitIsTrue() { assertTrue(new HikariConfig().isAutoCommit()); }
   /** Verifies: HCP-CONF-001. */
   @Test void defaultReadOnlyIsFalse() { assertFalse(new HikariConfig().isReadOnly()); }
   /** Verifies: HCP-CONF-001, HCP-CONF-020. */
   @Test void defaultConnectionTimeoutIsMilliseconds() { assertEquals(30_000L, new HikariConfig().getConnectionTimeout()); }
   /** Verifies: HCP-CONF-001, HCP-CONF-020. */
   @Test void defaultValidationTimeoutIsMilliseconds() { assertEquals(5_000L, new HikariConfig().getValidationTimeout()); }
   /** Verifies: HCP-CONF-001. */
   @Test void defaultIdleTimeoutIsTenMinutes() { assertEquals(600_000L, new HikariConfig().getIdleTimeout()); }
   /** Verifies: HCP-CONF-001. */
   @Test void defaultKeepaliveIsTwoMinutes() { assertEquals(120_000L, new HikariConfig().getKeepaliveTime()); }
   /** Verifies: HCP-CONF-001. */
   @Test void defaultMaxLifetimeIsThirtyMinutes() { assertEquals(1_800_000L, new HikariConfig().getMaxLifetime()); }
   /** Verifies: HCP-CONF-001. */
   @Test void defaultLeakDetectionIsDisabled() { assertEquals(0L, new HikariConfig().getLeakDetectionThreshold()); }
   /** Verifies: HCP-CONF-001. */
   @Test void defaultInitializationFailTimeoutIsOne() { assertEquals(1L, new HikariConfig().getInitializationFailTimeout()); }
   /** Verifies: HCP-CONF-001. */
   @Test void defaultMaximumPoolSizeIsTen() { assertEquals(10, new HikariConfig().getMaximumPoolSize()); }
   /** Verifies: HCP-CONF-001. */
   @Test void defaultSuspensionIsDisabled() { assertFalse(new HikariConfig().isAllowPoolSuspension()); }
   /** Verifies: HCP-CONF-001. */
   @Test void defaultMbeansAreDisabled() { assertFalse(new HikariConfig().isRegisterMbeans()); }
   /** Verifies: HCP-CONF-001. */
   @Test void defaultInternalQueryIsolationIsDisabled() { assertFalse(new HikariConfig().isIsolateInternalQueries()); }

   /** Verifies: HCP-CONF-015. */
   @Test void credentialsFactoryExposesPair() {
      Credentials credentials = Credentials.of("river-user", "river-pass");
      assertAll(() -> assertEquals("river-user", credentials.getUsername()),
         () -> assertEquals("river-pass", credentials.getPassword()));
   }
   /** Verifies: HCP-CONF-015. */
   @Test void credentialsConstructorExposesPair() {
      Credentials credentials = new Credentials("lake-user", "lake-pass");
      assertEquals("lake-user", credentials.getUsername());
      assertEquals("lake-pass", credentials.getPassword());
   }
   /** Verifies: HCP-CONF-015. */
   @Test void configCredentialsStayAtomic() {
      HikariConfig config = new HikariConfig();
      config.setCredentials(Credentials.of("pair-user", "pair-pass"));
      assertAll(() -> assertEquals("pair-user", config.getUsername()),
         () -> assertEquals("pair-pass", config.getPassword()),
         () -> assertEquals("pair-user", config.getCredentials().getUsername()));
   }
   /** Verifies: HCP-CONF-003. */
   @Test void propertiesConstructorUsesBeanNames() {
      Properties properties = new Properties();
      properties.setProperty("maximumPoolSize", "7");
      properties.setProperty("poolName", "property-pool");
      HikariConfig config = new HikariConfig(properties);
      assertAll(() -> assertEquals(7, config.getMaximumPoolSize()),
         () -> assertEquals("property-pool", config.getPoolName()));
   }
   /** Verifies: HCP-CONF-005, HCP-ERR-001. */
   @Test void missingNamedResourceRaisesIllegalArgument() {
      assertThrows(IllegalArgumentException.class, () -> new HikariConfig("absent-stage3.properties"));
   }
   /** Verifies: HCP-CONF-006. */
   @Test void copyStateCopiesValues() {
      HikariConfig source = configWithSource();
      source.setPoolName("copy-source");
      source.setMaximumPoolSize(6);
      HikariConfig target = new HikariConfig();
      source.copyStateTo(target);
      assertAll(() -> assertEquals("copy-source", target.getPoolName()),
         () -> assertEquals(6, target.getMaximumPoolSize()),
         () -> assertSame(source.getDataSource(), target.getDataSource()));
   }
   /** Verifies: HCP-CONF-013. */
   @Test void dataSourcePropertyIsObservable() {
      HikariConfig config = new HikariConfig();
      config.addDataSourceProperty("applicationName", "stage3-app");
      assertEquals("stage3-app", config.getDataSourceProperties().getProperty("applicationName"));
   }
   /** Verifies: HCP-CONF-013. */
   @Test void replacingDataSourcePropertiesPreservesEntries() {
      Properties properties = new Properties();
      properties.setProperty("region", "west");
      HikariConfig config = new HikariConfig();
      config.setDataSourceProperties(properties);
      assertEquals("west", config.getDataSourceProperties().getProperty("region"));
   }

   /** Verifies: HCP-CONF-021. */
   @Test void zeroConnectionTimeoutMeansEffectivelyUnbounded() {
      HikariConfig config = new HikariConfig();
      config.setConnectionTimeout(0);
      assertEquals(Integer.MAX_VALUE, config.getConnectionTimeout());
   }
   /** Verifies: HCP-CONF-021, HCP-ERR-003. */
   @Test void tooSmallConnectionTimeoutIsRejected() {
      assertThrows(IllegalArgumentException.class, () -> new HikariConfig().setConnectionTimeout(249));
   }
   /** Verifies: HCP-CONF-022, HCP-ERR-003. */
   @Test void tooSmallValidationTimeoutIsRejected() {
      assertThrows(IllegalArgumentException.class, () -> new HikariConfig().setValidationTimeout(249));
   }
   /** Verifies: HCP-CONF-023, HCP-ERR-003. */
   @Test void negativeIdleTimeoutIsRejected() {
      assertThrows(IllegalArgumentException.class, () -> new HikariConfig().setIdleTimeout(-1));
   }
   /** Verifies: HCP-CONF-024, HCP-ERR-003. */
   @Test void zeroMaximumPoolSizeIsRejected() {
      assertThrows(IllegalArgumentException.class, () -> new HikariConfig().setMaximumPoolSize(0));
   }
   /** Verifies: HCP-CONF-024, HCP-ERR-003. */
   @Test void negativeMinimumIdleIsRejected() {
      assertThrows(IllegalArgumentException.class, () -> new HikariConfig().setMinimumIdle(-1));
   }
   /** Verifies: HCP-CONF-010, HCP-ERR-002. */
   @Test void dataSourceClassAndDriverCombinationIsRejected() {
      HikariConfig config = new HikariConfig();
      config.setDataSourceClassName(ControllableDataSource.class.getName());
      config.setDriverClassName(PublicDriver.class.getName());
      assertThrows(IllegalStateException.class, config::validate);
   }
   /** Verifies: HCP-CONF-011, HCP-ERR-002. */
   @Test void driverWithoutJdbcUrlIsRejected() {
      HikariConfig config = new HikariConfig();
      config.setDriverClassName(PublicDriver.class.getName());
      assertThrows(IllegalArgumentException.class, config::validate);
   }
   /** Verifies: HCP-CONF-012, HCP-ERR-002. */
   @Test void missingConnectionSourceIsRejected() {
      assertThrows(IllegalArgumentException.class, new HikariConfig()::validate);
   }
   /** Verifies: HCP-CONF-025. */
   @Test void validationClampsMinimumIdleToMaximum() {
      HikariConfig config = configWithSource();
      config.setMaximumPoolSize(3);
      config.setMinimumIdle(8);
      config.validate();
      assertEquals(3, config.getMinimumIdle());
   }
   /** Verifies: HCP-CONF-026. */
   @Test void validationRestoresTooSmallIdleTimeout() {
      HikariConfig config = configWithSource();
      config.setMaximumPoolSize(4);
      config.setMinimumIdle(1);
      config.setIdleTimeout(9_000);
      config.validate();
      assertEquals(600_000L, config.getIdleTimeout());
   }
   /** Verifies: HCP-CONF-026. */
   @Test void validationDisablesIdleTimeoutNearLifetime() {
      HikariConfig config = configWithSource();
      config.setMaximumPoolSize(4);
      config.setMinimumIdle(1);
      config.setMaxLifetime(40_000);
      config.setIdleTimeout(39_500);
      config.validate();
      assertEquals(0L, config.getIdleTimeout());
   }
   /** Verifies: HCP-CONF-027. */
   @Test void validationRestoresTooSmallMaxLifetime() {
      HikariConfig config = configWithSource();
      config.setMaxLifetime(29_999);
      config.validate();
      assertEquals(1_800_000L, config.getMaxLifetime());
   }
   /** Verifies: HCP-CONF-028. */
   @Test void validationDisablesTooSmallKeepalive() {
      HikariConfig config = configWithSource();
      config.setKeepaliveTime(29_999);
      config.validate();
      assertEquals(0L, config.getKeepaliveTime());
   }
   /** Verifies: HCP-CONF-028. */
   @Test void validationDisablesKeepaliveAtLifetime() {
      HikariConfig config = configWithSource();
      config.setMaxLifetime(60_000);
      config.setKeepaliveTime(60_000);
      config.validate();
      assertEquals(0L, config.getKeepaliveTime());
   }
   /** Verifies: HCP-CONF-029. */
   @Test void validationDisablesTooSmallLeakThreshold() {
      HikariConfig config = configWithSource();
      config.setLeakDetectionThreshold(1_999);
      config.validate();
      assertEquals(0L, config.getLeakDetectionThreshold());
   }
   /** Verifies: HCP-CONF-030. */
   @Test void validationAssignsPoolName() {
      HikariConfig config = configWithSource();
      config.validate();
      assertNotEquals("", config.getPoolName());
   }
   /** Verifies: HCP-CONF-030. */
   @Test void jmxPoolNameRejectsColon() {
      HikariConfig config = configWithSource();
      config.setRegisterMbeans(true);
      config.setPoolName("bad:name");
      assertThrows(IllegalArgumentException.class, config::validate);
   }
   /** Verifies: HCP-CONF-033, HCP-ERR-006. */
   @Test void metricsFactoryThenRegistryIsRejected() {
      HikariConfig config = new HikariConfig();
      config.setMetricsTrackerFactory(new RecordingMetrics());
      assertThrows(IllegalStateException.class, () -> config.setMetricRegistry(new Object()));
   }
   /** Verifies: HCP-CONF-034, HCP-ERR-005. */
   @Test void unsupportedMetricRegistryIsRejected() {
      assertThrows(IllegalArgumentException.class, () -> new HikariConfig().setMetricRegistry(new Object()));
   }
   /** Verifies: HCP-CONF-017, HCP-STATE-003. */
   @Test void liveCredentialAccessorsRemainConsistent() {
      HikariConfig config = new HikariConfig();
      config.setUsername("live-user");
      config.setPassword("live-pass");
      assertEquals("live-pass", config.getCredentials().getPassword());
   }
   /** Verifies: HCP-CONF-018. */
   @Test void connectionDefaultAccessorsRetainValues() {
      HikariConfig config = new HikariConfig();
      config.setAutoCommit(false);
      config.setReadOnly(true);
      config.setCatalog("ledger");
      config.setSchema("tenant_a");
      config.setTransactionIsolation("TRANSACTION_SERIALIZABLE");
      assertAll(() -> assertFalse(config.isAutoCommit()), () -> assertTrue(config.isReadOnly()),
         () -> assertEquals("ledger", config.getCatalog()), () -> assertEquals("tenant_a", config.getSchema()),
         () -> assertEquals("TRANSACTION_SERIALIZABLE", config.getTransactionIsolation()));
   }

   /** Verifies: HCP-OBS-004, HCP-OBS-005. */
   @Test void poolStatsTotalTriggersRefresh() {
      ObservedPoolStats stats = new ObservedPoolStats(60_000);
      assertAll(() -> assertEquals(6, stats.getTotalConnections()), () -> assertEquals(1, stats.updates.get()));
   }
   /** Verifies: HCP-OBS-004, HCP-OBS-005. */
   @Test void poolStatsIdleUsesCachedRefresh() {
      ObservedPoolStats stats = new ObservedPoolStats(60_000);
      stats.getTotalConnections();
      assertAll(() -> assertEquals(3, stats.getIdleConnections()), () -> assertEquals(1, stats.updates.get()));
   }
   /** Verifies: HCP-OBS-004. */
   @Test void poolStatsExposesActiveAndPending() {
      ObservedPoolStats stats = new ObservedPoolStats(60_000);
      assertAll(() -> assertEquals(3, stats.getActiveConnections()), () -> assertEquals(1, stats.getPendingThreads()));
   }
   /** Verifies: HCP-OBS-004. */
   @Test void poolStatsExposesBounds() {
      ObservedPoolStats stats = new ObservedPoolStats(60_000);
      assertAll(() -> assertEquals(11, stats.getMaxConnections()), () -> assertEquals(2, stats.getMinConnections()));
   }
   /** Verifies: HCP-CONN-017. */
   @Test void sqlExceptionOverrideDefaultsToContinueEvict() {
      SQLExceptionOverride override = new SQLExceptionOverride() { };
      assertEquals(SQLExceptionOverride.Override.CONTINUE_EVICT, override.adjudicate(new SQLException()));
   }
   /** Verifies: HCP-POOL-003, HCP-MGMT-003. */
   @Test void lazyDataSourceStartsUnstarted() {
      HikariDataSource dataSource = new HikariDataSource();
      assertAll(() -> assertFalse(dataSource.isRunning()), () -> assertFalse(dataSource.isClosed()),
         () -> assertNull(dataSource.getHikariPoolMXBean()), () -> assertSame(dataSource, dataSource.getHikariConfigMXBean()));
      dataSource.close();
   }
   /** Verifies: HCP-POOL-014. */
   @Test void unstartedDelegationDefaultsAreStable() throws Exception {
      HikariDataSource dataSource = new HikariDataSource();
      assertAll(() -> assertNull(dataSource.getLogWriter()), () -> assertEquals(0, dataSource.getLoginTimeout()));
      dataSource.close();
   }
   /** Verifies: HCP-POOL-016. */
   @Test void unstartedDataSourceWrapsItself() throws Exception {
      HikariDataSource dataSource = new HikariDataSource();
      assertTrue(dataSource.isWrapperFor(HikariDataSource.class));
      dataSource.close();
   }
   /** Verifies: HCP-POOL-015, HCP-ERR-011. */
   @Test void unstartedUnsupportedUnwrapRaisesSqlException() {
      HikariDataSource dataSource = new HikariDataSource();
      assertThrows(SQLException.class, () -> dataSource.unwrap(ControllableDataSource.class));
      dataSource.close();
   }
   /** Verifies: HCP-MGMT-010. */
   @Test void repeatedCloseKeepsClosedState() {
      HikariDataSource dataSource = new HikariDataSource();
      dataSource.close();
      dataSource.close();
      assertTrue(dataSource.isClosed());
   }
   /** Verifies: HCP-POOL-013, HCP-ERR-010. */
   @Test void credentialedBorrowIsUnsupported() {
      HikariDataSource dataSource = new HikariDataSource();
      assertThrows(java.sql.SQLFeatureNotSupportedException.class,
         () -> dataSource.getConnection("u", "p"));
      dataSource.close();
   }
   /** Verifies: HCP-POOL-017, HCP-ERR-010. */
   @Test void parentLoggerIsUnsupported() {
      HikariDataSource dataSource = new HikariDataSource();
      assertThrows(java.sql.SQLFeatureNotSupportedException.class, dataSource::getParentLogger);
      dataSource.close();
   }
}
