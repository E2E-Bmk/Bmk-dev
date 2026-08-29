package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.sql.SQLException;
import java.time.Duration;
import org.apache.commons.dbcp2.BasicDataSource;
import org.junit.jupiter.api.Test;

class CapacityPolicyAtomicTest {
    /** Verifies: DBCP-CAP-002, DBCP-CAP-006. */
    @Test
    void maxTotalCanBeChangedBeforeStartup() throws SQLException {
        try (BasicDataSource source = new BasicDataSource()) {
            source.setMaxTotal(13);
            assertEquals(13, source.getMaxTotal());
            assertEquals(0, source.getNumActive());
        }
    }

    /** Verifies: DBCP-CAP-006. */
    @Test
    void maxIdleCanBeChangedBeforeStartup() throws SQLException {
        try (BasicDataSource source = new BasicDataSource()) {
            source.setMaxIdle(5);
            assertEquals(5, source.getMaxIdle());
            assertEquals(0, source.getNumIdle());
        }
    }

    /** Verifies: DBCP-CAP-006. */
    @Test
    void minIdleCanBeChangedBeforeStartup() throws SQLException {
        try (BasicDataSource source = new BasicDataSource()) {
            source.setMinIdle(2);
            assertEquals(2, source.getMinIdle());
            assertEquals(0, source.getNumIdle());
        }
    }

    /** Verifies: DBCP-CAP-003, DBCP-CAP-006. */
    @Test
    void finiteWaitCanBeChangedBeforeStartup() throws SQLException {
        try (BasicDataSource source = new BasicDataSource()) {
            source.setMaxWait(Duration.ofMillis(271));
            assertEquals(Duration.ofMillis(271), source.getMaxWaitDuration());
            assertFalse(source.getMaxWaitDuration().isNegative());
        }
    }

    /** Verifies: DBCP-CAP-007. */
    @Test
    void lifoPolicyCanBeDisabled() throws SQLException {
        try (BasicDataSource source = new BasicDataSource()) {
            source.setLifo(false);
            assertFalse(source.getLifo());
            source.setLifo(true);
            assertTrue(source.getLifo());
        }
    }

    /** Verifies: DBCP-CAP-014, DBCP-CAP-015. */
    @Test
    void defaultEvictionDurationsAreDocumented() throws SQLException {
        try (BasicDataSource source = new BasicDataSource()) {
            assertEquals(Duration.ofMillis(-1), source.getDurationBetweenEvictionRuns());
            assertEquals(Duration.ofMinutes(30), source.getMinEvictableIdleDuration());
            assertEquals(Duration.ofMillis(-1), source.getSoftMinEvictableIdleDuration());
        }
    }

    /** Verifies: DBCP-CAP-017, DBCP-LIFE-005. */
    @Test
    void unstartedEvictionDoesNotCreatePool() throws Exception {
        try (BasicDataSource source = new BasicDataSource()) {
            source.evict();
            assertEquals(0, source.getNumActive());
            assertEquals(0, source.getNumIdle());
            assertFalse(source.isClosed());
        }
    }

    /** Verifies: DBCP-CAP-002. */
    @Test
    void negativeMaxTotalRepresentsUnboundedPolicy() throws SQLException {
        try (BasicDataSource source = new BasicDataSource()) {
            source.setMaxTotal(-3);
            assertEquals(-3, source.getMaxTotal());
            assertEquals(0, source.getNumActive() + source.getNumIdle());
        }
    }
}
