package integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.sql.Connection;
import java.sql.SQLException;
import org.apache.commons.dbcp2.BasicDataSource;
import org.junit.jupiter.api.Test;
import support.DbcpTestSupport;

class ShutdownIntegrationTest {
    /**
     * CVI-5: Seam: lifecycle crossing keeps an outstanding borrow usable after shutdown.
     * Verifies: DBCP-CVI-005, DBCP-LIFE-002, DBCP-CONN-015.
     * Depends-On: closeMarksUnstartedSourceClosed, driverManagerFactoryCreatesUsablePhysicalConnection.
     */
    @Test
    void borrowedConnectionRemainsUsableUntilItsClose() throws Exception {
        final BasicDataSource source = DbcpTestSupport.dataSource("amber_shutdown_borrow");
        final Connection connection = source.getConnection();
        source.close();
        assertTrue(source.isClosed());
        assertEquals(71, DbcpTestSupport.queryInt(connection, "select 71"));
        assertFalse(connection.isClosed());
        connection.close();
    }

    /**
     * CVI-5: Seam: error propagation aligns closed state with acquisition failure.
     * Verifies: DBCP-CVI-005, DBCP-LIFE-003, DBCP-ERR-001.
     * Depends-On: closedSourceRejectsAcquisition, closeMarksUnstartedSourceClosed.
     */
    @Test
    void shutdownSynchronizesClosedStateAndAcquisitionFailure() throws Exception {
        final BasicDataSource source = DbcpTestSupport.dataSource("bronze_shutdown_failure");
        source.start();
        source.close();
        assertTrue(source.isClosed());
        assertThrows(SQLException.class, source::getConnection);
        assertEquals(0, source.getNumIdle());
    }

    /**
     * CVI-5: Seam: state consistency clears idle projection during shutdown.
     * Verifies: DBCP-CVI-005, DBCP-LIFE-002, DBCP-LIFE-005.
     * Depends-On: newSourceIsOpenWithZeroCounts, closeMarksWrapperClosed.
     */
    @Test
    void shutdownClearsExistingIdleConnections() throws Exception {
        final BasicDataSource source = DbcpTestSupport.dataSource("cobalt_shutdown_idle");
        try (Connection connection = source.getConnection()) {
            assertEquals(1, source.getNumActive());
        }
        assertEquals(1, source.getNumIdle());
        source.close();
        assertEquals(0, source.getNumIdle());
        assertTrue(source.isClosed());
    }

    /**
     * CVI-5: Seam: lifecycle crossing prevents a late return from entering a closed pool.
     * Verifies: DBCP-CVI-005, DBCP-CONN-015, DBCP-STATE-003.
     * Depends-On: closeMarksWrapperClosed, repeatedCloseIsIdempotent.
     */
    @Test
    void lateConnectionReturnLeavesClosedCountsAtZero() throws Exception {
        final BasicDataSource source = DbcpTestSupport.dataSource("denim_shutdown_late_return");
        final Connection connection = source.getConnection();
        source.close();
        connection.close();
        assertTrue(connection.isClosed());
        assertEquals(0, source.getNumActive());
        assertEquals(0, source.getNumIdle());
    }
}
