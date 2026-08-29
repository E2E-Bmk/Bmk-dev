package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.time.Duration;
import java.util.Properties;
import org.apache.commons.dbcp2.BasicDataSource;
import org.apache.commons.dbcp2.BasicDataSourceFactory;
import org.apache.commons.dbcp2.DriverManagerConnectionFactory;
import org.junit.jupiter.api.Test;

class SourceConfigurationAtomicTest {
    /** Verifies: DBCP-SRC-017. */
    @Test
    void defaultCapacityPolicyIsDocumented() {
        try (BasicDataSource source = new BasicDataSource()) {
            assertEquals(0, source.getInitialSize());
            assertEquals(8, source.getMaxTotal());
            assertEquals(8, source.getMaxIdle());
            assertEquals(0, source.getMinIdle());
            assertTrue(source.getMaxWaitDuration().isNegative());
            assertTrue(source.getLifo());
        } catch (SQLException exception) {
            throw new AssertionError(exception);
        }
    }

    /** Verifies: DBCP-SRC-018. */
    @Test
    void defaultValidationPolicyIsDocumented() {
        try (BasicDataSource source = new BasicDataSource()) {
            assertTrue(source.getTestOnBorrow());
            assertFalse(source.getTestOnCreate());
            assertFalse(source.getTestOnReturn());
            assertFalse(source.getTestWhileIdle());
            assertNull(source.getValidationQuery());
            assertEquals(Duration.ofMillis(-1), source.getDurationBetweenEvictionRuns());
        } catch (SQLException exception) {
            throw new AssertionError(exception);
        }
    }

    /** Verifies: DBCP-SRC-019. */
    @Test
    void defaultStatementPoolPolicyIsDocumented() {
        try (BasicDataSource source = new BasicDataSource()) {
            assertFalse(source.isPoolPreparedStatements());
            assertFalse(source.isClearStatementPoolOnReturn());
            assertEquals(-1, source.getMaxOpenPreparedStatements());
            assertFalse(source.isAccessToUnderlyingConnectionAllowed());
        } catch (SQLException exception) {
            throw new AssertionError(exception);
        }
    }

    /** Verifies: DBCP-SRC-020. */
    @Test
    void defaultReturnCleanupPolicyIsDocumented() {
        try (BasicDataSource source = new BasicDataSource()) {
            assertTrue(source.getCacheState());
            assertTrue(source.getAutoCommitOnReturn());
            assertTrue(source.getRollbackOnReturn());
            assertTrue(source.getLogExpiredConnections());
            assertFalse(source.getRemoveAbandonedOnBorrow());
            assertFalse(source.getFastFailValidation());
        } catch (SQLException exception) {
            throw new AssertionError(exception);
        }
    }

    /** Verifies: DBCP-SRC-016. */
    @Test
    void durationSettersPreserveUnits() {
        try (BasicDataSource source = new BasicDataSource()) {
            source.setMaxWait(Duration.ofMillis(417));
            source.setDurationBetweenEvictionRuns(Duration.ofMillis(823));
            source.setValidationQueryTimeout(Duration.ofSeconds(7));
            assertEquals(Duration.ofMillis(417), source.getMaxWaitDuration());
            assertEquals(Duration.ofMillis(823), source.getDurationBetweenEvictionRuns());
            assertEquals(Duration.ofSeconds(7), source.getValidationQueryTimeoutDuration());
        } catch (SQLException exception) {
            throw new AssertionError(exception);
        }
    }

    /** Verifies: DBCP-SRC-013, DBCP-SRC-016. */
    @Test
    void propertyFactoryMapsRecognizedValues() throws Exception {
        final Properties properties = new Properties();
        properties.setProperty("url", "jdbc:h2:mem:atlas_factory");
        properties.setProperty("maxTotal", "11");
        properties.setProperty("maxWaitMillis", "613");
        try (BasicDataSource source = BasicDataSourceFactory.createDataSource(properties)) {
            assertEquals("jdbc:h2:mem:atlas_factory", source.getUrl());
            assertEquals(11, source.getMaxTotal());
            assertEquals(Duration.ofMillis(613), source.getMaxWaitDuration());
            assertEquals(0, source.getNumActive());
        }
    }

    /** Verifies: DBCP-SRC-014. */
    @Test
    void propertyFactoryAcceptsNamedIsolation() throws Exception {
        final Properties properties = new Properties();
        properties.setProperty("defaultTransactionIsolation", "SERIALIZABLE");
        try (BasicDataSource source = BasicDataSourceFactory.createDataSource(properties)) {
            assertEquals(Connection.TRANSACTION_SERIALIZABLE,
                    source.getDefaultTransactionIsolation());
            assertEquals(0, source.getNumActive());
        }
    }

    /** Verifies: DBCP-SRC-001, DBCP-SRC-002. */
    @Test
    void driverManagerFactoryCreatesUsablePhysicalConnection() throws Exception {
        final DriverManagerConnectionFactory factory =
                new DriverManagerConnectionFactory("jdbc:h2:mem:aurora_physical");
        try (Connection connection = factory.createConnection();
             Statement statement = connection.createStatement();
             ResultSet resultSet = statement.executeQuery("select 47")) {
            assertTrue(resultSet.next());
            assertEquals(47, resultSet.getInt(1));
            assertFalse(connection.isClosed());
        }
    }
}
