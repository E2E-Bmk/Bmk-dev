package integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.sql.Connection;
import java.sql.Statement;
import org.apache.commons.dbcp2.BasicDataSource;
import org.junit.jupiter.api.Test;
import support.DbcpTestSupport;

class ReturnStateIntegrationTest {
    /**
     * CVI-7: Seam: config interaction establishes auto-commit default on borrow.
     * Verifies: DBCP-CVI-007, DBCP-CONN-006.
     * Depends-On: defaultReturnCleanupPolicyIsDocumented, cacheStateSettingRoundTrips.
     */
    @Test
    void configuredAutoCommitDefaultAppearsOnBorrow() throws Exception {
        try (BasicDataSource source = DbcpTestSupport.dataSource("indigo_state_default")) {
            source.setDefaultAutoCommit(false);
            try (Connection connection = source.getConnection()) {
                assertFalse(connection.getAutoCommit());
                assertEquals(1, source.getNumActive());
            }
        }
    }

    /**
     * CVI-7: Seam: state consistency restores auto-commit for a later borrower.
     * Verifies: DBCP-CVI-007, DBCP-CONN-007, DBCP-CONN-009.
     * Depends-On: clearCachedStateObservesDelegateChange, closeMarksWrapperClosed.
     */
    @Test
    void changedAutoCommitIsRestoredForLaterBorrower() throws Exception {
        try (BasicDataSource source = DbcpTestSupport.dataSource("jade_state_restore")) {
            source.setDefaultAutoCommit(true);
            try (Connection first = source.getConnection()) {
                first.setAutoCommit(false);
                assertFalse(first.getAutoCommit());
            }
            try (Connection second = source.getConnection()) {
                assertTrue(second.getAutoCommit());
                assertEquals(1, source.getNumActive());
            }
        }
    }

    /**
     * CVI-7: Seam: lifecycle crossing rolls back work before state reuse.
     * Verifies: DBCP-CVI-007, DBCP-CONN-008, DBCP-CONN-009.
     * Depends-On: defaultReturnCleanupPolicyIsDocumented, driverManagerFactoryCreatesUsablePhysicalConnection.
     */
    @Test
    void rollbackAndAutoCommitRestorationAgreeAcrossBorrowers() throws Exception {
        try (BasicDataSource source = DbcpTestSupport.dataSource("khaki_state_rollback")) {
            try (Connection setup = source.getConnection()) {
                DbcpTestSupport.execute(setup, "create table state_rows(id int primary key)");
            }
            try (Connection first = source.getConnection()) {
                first.setAutoCommit(false);
                DbcpTestSupport.execute(first, "insert into state_rows values (53)");
            }
            try (Connection second = source.getConnection()) {
                assertTrue(second.getAutoCommit());
                assertEquals(0, DbcpTestSupport.queryInt(second,
                        "select count(*) from state_rows"));
            }
        }
    }

    /**
     * CVI-7: Seam: config interaction hands default query timeout to JDBC statements.
     * Verifies: DBCP-CVI-007, DBCP-CONN-011.
     * Depends-On: sourceStoresDefaultQueryTimeout, driverManagerFactoryCreatesUsablePhysicalConnection.
     */
    @Test
    void statementReceivesConfiguredDefaultQueryTimeout() throws Exception {
        try (BasicDataSource source = DbcpTestSupport.dataSource("linen_state_timeout")) {
            source.setDefaultQueryTimeout(31);
            try (Connection connection = source.getConnection();
                 Statement statement = connection.createStatement()) {
                assertEquals(31, statement.getQueryTimeout());
                assertEquals(31, DbcpTestSupport.queryInt(connection, "select 31"));
            }
        }
    }
}
