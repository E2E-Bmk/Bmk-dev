package integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;

import java.sql.Connection;
import java.sql.SQLException;
import java.time.Duration;
import org.apache.commons.dbcp2.BasicDataSource;
import org.junit.jupiter.api.Test;
import support.DbcpTestSupport;

class ProjectionConsistencyIntegrationTest {
    /**
     * CVI-1: Seam: state consistency between borrow and pool counts.
     * Verifies: DBCP-CVI-001, DBCP-CAP-001, DBCP-STATE-001.
     * Depends-On: newSourceIsOpenWithZeroCounts, driverManagerFactoryCreatesUsablePhysicalConnection.
     */
    @Test
    void singleBorrowMovesOneConnectionToActiveProjection() throws Exception {
        try (BasicDataSource source = DbcpTestSupport.dataSource("juniper_projection_one");
             Connection connection = source.getConnection()) {
            assertEquals(1, source.getNumActive());
            assertEquals(0, source.getNumIdle());
            assertFalse(connection.isClosed());
        }
    }

    /**
     * CVI-1: Seam: error propagation from bounded capacity into acquisition.
     * Verifies: DBCP-CVI-001, DBCP-CAP-004, DBCP-ERR-003.
     * Depends-On: maxTotalCanBeChangedBeforeStartup, finiteWaitCanBeChangedBeforeStartup.
     */
    @Test
    void boundedPoolRaisesWhenFiniteWaitExpires() throws Exception {
        try (BasicDataSource source = DbcpTestSupport.dataSource("kelp_projection_exhausted")) {
            source.setMaxTotal(1);
            source.setMaxWait(Duration.ofMillis(35));
            try (Connection first = source.getConnection()) {
                org.junit.jupiter.api.Assertions.assertThrows(SQLException.class,
                        source::getConnection);
                assertEquals(1, source.getNumActive());
                assertFalse(first.isClosed());
            }
            assertEquals(1, source.getNumIdle());
        }
    }

    /**
     * CVI-1: Seam: lifecycle crossing from active handle to idle pool state.
     * Verifies: DBCP-CVI-001, DBCP-CONN-002, DBCP-STATE-001.
     * Depends-On: closeMarksWrapperClosed, newSourceIsOpenWithZeroCounts.
     */
    @Test
    void closingBorrowMovesConnectionToIdleProjection() throws Exception {
        try (BasicDataSource source = DbcpTestSupport.dataSource("lotus_projection_return")) {
            final Connection connection = source.getConnection();
            assertEquals(1, source.getNumActive());
            connection.close();
            assertEquals(0, source.getNumActive());
            assertEquals(1, source.getNumIdle());
        }
    }

    /**
     * CVI-1: Seam: config interaction between maxIdle and return projection.
     * Verifies: DBCP-CVI-001, DBCP-CAP-006, DBCP-STATE-001.
     * Depends-On: maxIdleCanBeChangedBeforeStartup, closeMarksWrapperClosed.
     */
    @Test
    void zeroMaxIdleClosesReturnedPhysicalConnection() throws Exception {
        try (BasicDataSource source = DbcpTestSupport.dataSource("maple_projection_zero_idle")) {
            source.setMaxIdle(0);
            final Connection connection = source.getConnection();
            connection.close();
            assertEquals(0, source.getNumActive());
            assertEquals(0, source.getNumIdle());
        }
    }
}
