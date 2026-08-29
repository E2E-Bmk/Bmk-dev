package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.sql.SQLException;
import java.time.Duration;
import java.util.List;
import org.apache.commons.dbcp2.BasicDataSource;
import org.apache.commons.dbcp2.PoolableConnection;
import org.apache.commons.dbcp2.PoolingDataSource;
import org.junit.jupiter.api.Test;

class PreparedStatementPolicyAtomicTest {
    /** Verifies: DBCP-STMT-001, DBCP-SRC-019. */
    @Test
    void basicSourceDisablesStatementPoolingByDefault() throws SQLException {
        try (BasicDataSource source = new BasicDataSource()) {
            assertFalse(source.isPoolPreparedStatements());
            assertEquals(-1, source.getMaxOpenPreparedStatements());
        }
    }

    /** Verifies: DBCP-STMT-002. */
    @Test
    void basicSourceEnablesStatementPoolingPolicy() throws SQLException {
        try (BasicDataSource source = new BasicDataSource()) {
            source.setPoolPreparedStatements(true);
            assertTrue(source.isPoolPreparedStatements());
            assertEquals(0, source.getNumActive());
        }
    }

    /** Verifies: DBCP-STMT-005. */
    @Test
    void basicSourceStoresStatementLimit() throws SQLException {
        try (BasicDataSource source = new BasicDataSource()) {
            source.setMaxOpenPreparedStatements(7);
            assertEquals(7, source.getMaxOpenPreparedStatements());
            assertFalse(source.isPoolPreparedStatements());
        }
    }

    /** Verifies: DBCP-STMT-006. */
    @Test
    void basicSourceStoresClearOnReturnPolicy() throws SQLException {
        try (BasicDataSource source = new BasicDataSource()) {
            source.setClearStatementPoolOnReturn(true);
            assertTrue(source.isClearStatementPoolOnReturn());
            assertEquals(0, source.getNumIdle());
        }
    }

    /** Verifies: DBCP-SRC-010, DBCP-ERR-005. */
    @Test
    void missingDriverConfigurationRaisesSqlException() throws SQLException {
        try (BasicDataSource source = new BasicDataSource()) {
            assertThrows(SQLException.class, source::getConnection);
            assertEquals(0, source.getNumActive());
        }
    }

    /** Verifies: DBCP-CONN-005, DBCP-ERR-007. */
    @Test
    void unsupportedUnwrapRaisesSqlException() throws SQLException {
        try (BasicDataSource source = new BasicDataSource()) {
            assertThrows(SQLException.class, () -> source.unwrap(List.class));
            assertFalse(source.isWrapperFor(List.class));
        }
    }

    /** Verifies: DBCP-LIFE-008, DBCP-ERR-010. */
    @Test
    void nullLowerLevelPoolRaisesNullPointer() {
        assertThrows(NullPointerException.class,
                () -> new PoolingDataSource<PoolableConnection>(null));
    }

    /** Verifies: DBCP-CONN-011, DBCP-STMT-007. */
    @Test
    void sourceStoresDefaultQueryTimeout() throws SQLException {
        try (BasicDataSource source = new BasicDataSource()) {
            source.setDefaultQueryTimeout(Duration.ofSeconds(23));
            assertEquals(Duration.ofSeconds(23), source.getDefaultQueryTimeoutDuration());
            assertEquals(0, source.getNumActive());
        }
    }
}
