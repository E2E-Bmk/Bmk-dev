package integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.sql.Connection;
import java.sql.DriverManager;
import org.apache.commons.dbcp2.BasicDataSource;
import org.junit.jupiter.api.Test;
import support.DbcpTestSupport;

class InvalidationIntegrationTest {
    /**
     * CVI-4: Seam: state consistency removes an invalidated active connection.
     * Verifies: DBCP-CVI-004, DBCP-CONN-013.
     * Depends-On: newSourceIsOpenWithZeroCounts, closedWrapperRejectsJdbcOperation.
     */
    @Test
    void invalidationRemovesActiveConnectionFromCounts() throws Exception {
        try (BasicDataSource source = DbcpTestSupport.dataSource("violet_invalidate_count")) {
            final Connection connection = source.getConnection();
            assertEquals(1, source.getNumActive());
            source.invalidateConnection(connection);
            assertEquals(0, source.getNumActive());
        }
    }

    /**
     * CVI-4: Seam: lifecycle crossing replaces an invalidated connection.
     * Verifies: DBCP-CVI-004, DBCP-CONN-013.
     * Depends-On: maxTotalCanBeChangedBeforeStartup, driverManagerFactoryCreatesUsablePhysicalConnection.
     */
    @Test
    void laterBorrowSucceedsAfterInvalidation() throws Exception {
        try (BasicDataSource source = DbcpTestSupport.dataSource("willow_invalidate_replace")) {
            final Connection first = source.getConnection();
            source.invalidateConnection(first);
            try (Connection second = source.getConnection()) {
                assertFalse(second.isClosed());
                assertEquals(61, DbcpTestSupport.queryInt(second, "select 61"));
                assertEquals(1, source.getNumActive());
            }
        }
    }

    /**
     * Seam: error propagation from validation into acquisition.
     * Verifies: DBCP-CAP-012, DBCP-ERR-006.
     * Depends-On: defaultValidationPolicyIsDocumented, driverManagerFactoryCreatesUsablePhysicalConnection.
     */
    @Test
    void invalidValidationQueryRaisesSqlException() throws Exception {
        try (BasicDataSource source = DbcpTestSupport.dataSource("xenia_validation_failure")) {
            source.setValidationQuery("select value from absent_validation_table");
            source.setTestOnBorrow(true);
            assertThrows(java.sql.SQLException.class, source::getConnection);
            assertEquals(0, source.getNumActive());
            assertEquals(0, source.getNumIdle());
        }
    }

    /**
     * CVI-4: Seam: error propagation rejects a foreign physical connection.
     * Verifies: DBCP-CVI-004, DBCP-CONN-014, DBCP-ERR-008.
     * Depends-On: driverManagerFactoryCreatesUsablePhysicalConnection, newSourceIsOpenWithZeroCounts.
     */
    @Test
    void foreignConnectionInvalidationRaisesIllegalState() throws Exception {
        try (BasicDataSource source = DbcpTestSupport.dataSource("yarrow_invalidate_foreign");
             Connection borrowed = source.getConnection();
             Connection foreign = DriverManager.getConnection("jdbc:h2:mem:zinc_foreign", "sa", "")) {
            assertThrows(IllegalStateException.class, () -> source.invalidateConnection(foreign));
            assertEquals(1, source.getNumActive());
            assertFalse(borrowed.isClosed());
            assertTrue(foreign.isValid(1));
        }
    }
}
