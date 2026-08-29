package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.sql.SQLException;
import java.sql.SQLFeatureNotSupportedException;
import org.apache.commons.dbcp2.BasicDataSource;
import org.junit.jupiter.api.Test;

class DataSourceLifecycleAtomicTest {
    /** Verifies: DBCP-LIFE-001, DBCP-LIFE-005. */
    @Test
    void newSourceIsOpenWithZeroCounts() throws SQLException {
        try (BasicDataSource source = new BasicDataSource()) {
            assertFalse(source.isClosed());
            assertEquals(0, source.getNumActive());
            assertEquals(0, source.getNumIdle());
        }
    }

    /** Verifies: DBCP-LIFE-002, DBCP-STATE-003. */
    @Test
    void closeMarksUnstartedSourceClosed() throws SQLException {
        final BasicDataSource source = new BasicDataSource();
        source.close();
        assertTrue(source.isClosed());
        assertEquals(0, source.getNumIdle());
    }

    /** Verifies: DBCP-LIFE-002. */
    @Test
    void repeatedCloseIsIdempotent() throws SQLException {
        final BasicDataSource source = new BasicDataSource();
        source.close();
        source.close();
        assertTrue(source.isClosed());
        assertEquals(0, source.getNumActive());
    }

    /** Verifies: DBCP-LIFE-003, DBCP-ERR-001. */
    @Test
    void closedSourceRejectsAcquisition() throws SQLException {
        final BasicDataSource source = new BasicDataSource();
        source.close();
        assertThrows(SQLException.class, source::getConnection);
        assertTrue(source.isClosed());
    }

    /** Verifies: DBCP-LIFE-007, DBCP-ERR-002. */
    @Test
    void perBorrowCredentialsAreUnsupported() throws SQLException {
        try (BasicDataSource source = new BasicDataSource()) {
            assertThrows(UnsupportedOperationException.class,
                    () -> source.getConnection("mercury", "violet"));
            assertEquals(0, source.getNumActive());
        }
    }

    /** Verifies: DBCP-LIFE-011. */
    @Test
    void getLoginTimeoutIsUnsupported() throws SQLException {
        try (BasicDataSource source = new BasicDataSource()) {
            assertThrows(UnsupportedOperationException.class, source::getLoginTimeout);
            assertFalse(source.isClosed());
        }
    }

    /** Verifies: DBCP-LIFE-011. */
    @Test
    void setLoginTimeoutIsUnsupported() throws SQLException {
        try (BasicDataSource source = new BasicDataSource()) {
            assertThrows(UnsupportedOperationException.class, () -> source.setLoginTimeout(29));
            assertFalse(source.isClosed());
        }
    }

    /** Verifies: DBCP-LIFE-011. */
    @Test
    void parentLoggerIsUnsupported() throws SQLException {
        try (BasicDataSource source = new BasicDataSource()) {
            assertThrows(SQLFeatureNotSupportedException.class, source::getParentLogger);
            assertEquals(0, source.getNumActive() + source.getNumIdle());
        }
    }
}
