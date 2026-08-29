package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import org.apache.commons.dbcp2.DelegatingConnection;
import org.junit.jupiter.api.Test;

class BorrowedConnectionAtomicTest {
    private Connection physical(final String name) throws SQLException {
        return DriverManager.getConnection("jdbc:h2:mem:" + name, "sa", "");
    }

    /** Verifies: DBCP-CONN-001, DBCP-CONN-004. */
    @Test
    void directDelegatingConnectionExposesItsDelegate() throws Exception {
        try (Connection raw = physical("birch_delegate");
             DelegatingConnection<Connection> wrapper = new DelegatingConnection<>(raw)) {
            assertSame(raw, wrapper.getDelegate());
            assertFalse(wrapper.isClosed());
        }
    }

    /** Verifies: DBCP-CONN-001, DBCP-CONN-004. */
    @Test
    void innermostDelegateResolvesThroughNestedWrappers() throws Exception {
        try (Connection raw = physical("cedar_nested");
             DelegatingConnection<Connection> inner = new DelegatingConnection<>(raw);
             DelegatingConnection<Connection> outer = new DelegatingConnection<>(inner)) {
            assertSame(raw, outer.getInnermostDelegate());
            assertTrue(outer.innermostDelegateEquals(raw));
        }
    }

    /** Verifies: DBCP-CONN-010. */
    @Test
    void cacheStateSettingRoundTrips() throws Exception {
        try (Connection raw = physical("dahlia_cache");
             DelegatingConnection<Connection> wrapper = new DelegatingConnection<>(raw)) {
            wrapper.setCacheState(false);
            assertFalse(wrapper.getCacheState());
            wrapper.setCacheState(true);
            assertTrue(wrapper.getCacheState());
        }
    }

    /** Verifies: DBCP-CONN-011. */
    @Test
    void defaultQueryTimeoutRoundTrips() throws Exception {
        try (Connection raw = physical("elm_timeout");
             DelegatingConnection<Connection> wrapper = new DelegatingConnection<>(raw)) {
            wrapper.setDefaultQueryTimeout(19);
            assertEquals(19, wrapper.getDefaultQueryTimeout());
            wrapper.setDefaultQueryTimeout((Integer) null);
            assertEquals(null, wrapper.getDefaultQueryTimeout());
        }
    }

    /** Verifies: DBCP-CONN-002. */
    @Test
    void closeMarksWrapperClosed() throws Exception {
        final Connection raw = physical("fir_close");
        final DelegatingConnection<Connection> wrapper = new DelegatingConnection<>(raw);
        wrapper.close();
        assertTrue(wrapper.isClosed());
        assertTrue(raw.isClosed());
    }

    /** Verifies: DBCP-CONN-003. */
    @Test
    void closedWrapperRejectsJdbcOperation() throws Exception {
        final DelegatingConnection<Connection> wrapper =
                new DelegatingConnection<>(physical("grove_closed_operation"));
        wrapper.close();
        assertThrows(SQLException.class, wrapper::createStatement);
        assertTrue(wrapper.isClosed());
    }

    /** Verifies: DBCP-CONN-005. */
    @Test
    void supportedUnwrapReturnsConnectionView() throws Exception {
        try (Connection raw = physical("hemlock_unwrap");
             DelegatingConnection<Connection> wrapper = new DelegatingConnection<>(raw)) {
            assertTrue(wrapper.isWrapperFor(Connection.class));
            assertSame(wrapper, wrapper.unwrap(Connection.class));
        }
    }

    /** Verifies: DBCP-CONN-010. */
    @Test
    void clearCachedStateObservesDelegateChange() throws Exception {
        try (Connection raw = physical("iris_clear_cache");
             DelegatingConnection<Connection> wrapper = new DelegatingConnection<>(raw)) {
            assertTrue(wrapper.getAutoCommit());
            raw.setAutoCommit(false);
            assertTrue(wrapper.getAutoCommit());
            wrapper.clearCachedState();
            assertFalse(wrapper.getAutoCommit());
        }
    }
}
