package integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.sql.Connection;
import org.apache.commons.dbcp2.BasicDataSource;
import org.junit.jupiter.api.Test;
import support.DbcpTestSupport;

class RestartIntegrationTest {
    /**
     * CVI-6: Seam: lifecycle crossing creates a fresh projection on restart.
     * Verifies: DBCP-CVI-006, DBCP-LIFE-004.
     * Depends-On: closeMarksUnstartedSourceClosed, newSourceIsOpenWithZeroCounts.
     */
    @Test
    void restartReopensClosedSourceWithFreshCounts() throws Exception {
        final BasicDataSource source = DbcpTestSupport.dataSource("ember_restart_closed");
        source.start();
        source.close();
        source.restart();
        try {
            assertFalse(source.isClosed());
            assertEquals(0, source.getNumActive());
            assertEquals(0, source.getNumIdle());
        } finally {
            source.close();
        }
    }

    /**
     * CVI-6: Seam: config interaction applies current initial size to the new pool.
     * Verifies: DBCP-CVI-006, DBCP-LIFE-004, DBCP-SRC-008.
     * Depends-On: maxIdleCanBeChangedBeforeStartup, closeMarksUnstartedSourceClosed.
     */
    @Test
    void restartUsesCurrentInitialSize() throws Exception {
        final BasicDataSource source = DbcpTestSupport.dataSource("flint_restart_initial");
        source.start();
        source.close();
        source.setInitialSize(2);
        source.restart();
        try {
            assertEquals(2, source.getNumIdle());
            assertEquals(0, source.getNumActive());
        } finally {
            source.close();
        }
    }

    /**
     * CVI-6: Seam: state consistency excludes old active handles from new counts.
     * Verifies: DBCP-CVI-006, DBCP-LIFE-004, DBCP-STATE-001.
     * Depends-On: newSourceIsOpenWithZeroCounts, maxTotalCanBeChangedBeforeStartup.
     */
    @Test
    void oldBorrowDoesNotContributeToRestartedPool() throws Exception {
        final BasicDataSource source = DbcpTestSupport.dataSource("garnet_restart_old_active");
        final Connection old = source.getConnection();
        assertEquals(1, source.getNumActive());
        source.restart();
        try {
            assertEquals(0, source.getNumActive());
            assertEquals(0, source.getNumIdle());
            assertFalse(old.isClosed());
        } finally {
            old.close();
            source.close();
        }
    }

    /**
     * CVI-6: Seam: lifecycle crossing isolates late old returns from the new pool.
     * Verifies: DBCP-CVI-006, DBCP-CONN-015, DBCP-LIFE-004.
     * Depends-On: closeMarksWrapperClosed, repeatedCloseIsIdempotent.
     */
    @Test
    void lateOldReturnDoesNotAlterRestartedProjection() throws Exception {
        final BasicDataSource source = DbcpTestSupport.dataSource("hazel_restart_late_return");
        final Connection old = source.getConnection();
        source.restart();
        old.close();
        try {
            assertTrue(old.isClosed());
            assertEquals(0, source.getNumActive());
            assertEquals(0, source.getNumIdle());
        } finally {
            source.close();
        }
    }
}
