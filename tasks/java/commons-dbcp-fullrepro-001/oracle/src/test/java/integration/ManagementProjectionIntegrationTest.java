package integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.sql.Connection;
import java.sql.SQLException;
import java.time.Duration;
import org.apache.commons.dbcp2.BasicDataSource;
import org.apache.commons.dbcp2.DataSourceMXBean;
import org.junit.jupiter.api.Test;
import support.DbcpTestSupport;

class ManagementProjectionIntegrationTest {
    /**
     * CVI-3: Seam: state consistency between management and concrete getters.
     * Verifies: DBCP-CVI-003, DBCP-LIFE-006.
     * Depends-On: maxTotalCanBeChangedBeforeStartup, newSourceIsOpenWithZeroCounts.
     */
    @Test
    void managementMaxTotalMatchesConcreteGetter() throws Exception {
        try (BasicDataSource source = DbcpTestSupport.dataSource("raven_mx_total")) {
            final DataSourceMXBean management = source;
            source.setMaxTotal(6);
            assertEquals(source.getMaxTotal(), management.getMaxTotal());
            assertEquals(6, management.getMaxTotal());
        }
    }

    /**
     * CVI-3: Seam: error propagation honors live wait policy and interrupt status.
     * Verifies: DBCP-CVI-003, DBCP-CAP-005, DBCP-ERR-004.
     * Depends-On: finiteWaitCanBeChangedBeforeStartup, durationSettersPreserveUnits.
     */
    @Test
    void interruptedWaitRestoresInterruptStatus() throws Exception {
        try (BasicDataSource source = DbcpTestSupport.dataSource("saffron_mx_wait")) {
            source.setMaxTotal(1);
            source.setMaxWait(Duration.ofSeconds(2));
            try (Connection first = source.getConnection()) {
                Thread.currentThread().interrupt();
                assertThrows(SQLException.class, source::getConnection);
                assertTrue(Thread.currentThread().isInterrupted());
                assertEquals(1, source.getNumActive());
            } finally {
                Thread.interrupted();
            }
        }
    }

    /**
     * CVI-3: Seam: state consistency exposes active count through both views.
     * Verifies: DBCP-CVI-003, DBCP-LIFE-005, DBCP-LIFE-006.
     * Depends-On: newSourceIsOpenWithZeroCounts, driverManagerFactoryCreatesUsablePhysicalConnection.
     */
    @Test
    void managementActiveCountTracksBorrow() throws Exception {
        try (BasicDataSource source = DbcpTestSupport.dataSource("thistle_mx_active");
             Connection connection = source.getConnection()) {
            final DataSourceMXBean management = source;
            assertEquals(source.getNumActive(), management.getNumActive());
            assertEquals(1, management.getNumActive());
            assertFalse(connection.isClosed());
        }
    }

    /**
     * CVI-3: Seam: state consistency exposes idle count after return.
     * Verifies: DBCP-CVI-003, DBCP-LIFE-005, DBCP-LIFE-006.
     * Depends-On: closeMarksWrapperClosed, maxIdleCanBeChangedBeforeStartup.
     */
    @Test
    void managementIdleCountTracksReturn() throws Exception {
        try (BasicDataSource source = DbcpTestSupport.dataSource("umber_mx_idle")) {
            final DataSourceMXBean management = source;
            final Connection connection = source.getConnection();
            connection.close();
            assertEquals(source.getNumIdle(), management.getNumIdle());
            assertEquals(1, management.getNumIdle());
        }
    }
}
