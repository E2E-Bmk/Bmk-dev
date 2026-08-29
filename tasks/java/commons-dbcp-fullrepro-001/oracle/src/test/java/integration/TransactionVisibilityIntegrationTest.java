package integration;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.sql.Connection;
import org.apache.commons.dbcp2.BasicDataSource;
import org.junit.jupiter.api.Test;
import support.DbcpTestSupport;

class TransactionVisibilityIntegrationTest {
    /**
     * CVI-2: Seam: state consistency from committed write to later borrow.
     * Verifies: DBCP-CVI-002, DBCP-CONN-008.
     * Depends-On: driverManagerFactoryCreatesUsablePhysicalConnection, closeMarksWrapperClosed.
     */
    @Test
    void committedInsertIsVisibleToLaterBorrower() throws Exception {
        try (BasicDataSource source = DbcpTestSupport.dataSource("nectar_commit_visible")) {
            try (Connection first = source.getConnection()) {
                first.setAutoCommit(false);
                DbcpTestSupport.execute(first, "create table ledger_a(id int primary key)");
                DbcpTestSupport.execute(first, "insert into ledger_a values (17)");
                first.commit();
            }
            try (Connection second = source.getConnection()) {
                assertEquals(1, DbcpTestSupport.queryInt(second, "select count(*) from ledger_a"));
            }
        }
    }

    /**
     * CVI-2: Seam: lifecycle crossing applies rollback before reuse.
     * Verifies: DBCP-CVI-002, DBCP-CONN-008, DBCP-CONN-009.
     * Depends-On: cacheStateSettingRoundTrips, closeMarksWrapperClosed.
     */
    @Test
    void uncommittedInsertIsRolledBackOnReturn() throws Exception {
        try (BasicDataSource source = DbcpTestSupport.dataSource("onyx_rollback_return")) {
            try (Connection setup = source.getConnection()) {
                DbcpTestSupport.execute(setup, "create table ledger_b(id int primary key)");
            }
            try (Connection first = source.getConnection()) {
                first.setAutoCommit(false);
                DbcpTestSupport.execute(first, "insert into ledger_b values (29)");
            }
            try (Connection second = source.getConnection()) {
                assertEquals(0, DbcpTestSupport.queryInt(second, "select count(*) from ledger_b"));
                assertEquals(true, second.getAutoCommit());
            }
        }
    }

    /**
     * CVI-2: Seam: protocol handoff preserves committed update semantics.
     * Verifies: DBCP-CVI-002, DBCP-CONN-007, DBCP-CONN-008.
     * Depends-On: clearCachedStateObservesDelegateChange, driverManagerFactoryCreatesUsablePhysicalConnection.
     */
    @Test
    void committedUpdateValueSurvivesConnectionReturn() throws Exception {
        try (BasicDataSource source = DbcpTestSupport.dataSource("pearl_update_visible")) {
            try (Connection first = source.getConnection()) {
                first.setAutoCommit(false);
                DbcpTestSupport.execute(first, "create table ledger_c(id int primary key, amount int)");
                DbcpTestSupport.execute(first, "insert into ledger_c values (1, 83)");
                first.commit();
            }
            try (Connection second = source.getConnection()) {
                assertEquals(83, DbcpTestSupport.queryInt(second,
                        "select amount from ledger_c where id=1"));
            }
        }
    }

    /**
     * CVI-2: Seam: config interaction disables return rollback when requested.
     * Verifies: DBCP-CVI-002, DBCP-CONN-008.
     * Depends-On: defaultReturnCleanupPolicyIsDocumented, cacheStateSettingRoundTrips.
     */
    @Test
    void explicitCommitRemainsVisibleWithRollbackOnReturnDisabled() throws Exception {
        try (BasicDataSource source = DbcpTestSupport.dataSource("quartz_no_return_rollback")) {
            source.setRollbackOnReturn(false);
            try (Connection first = source.getConnection()) {
                first.setAutoCommit(false);
                DbcpTestSupport.execute(first, "create table ledger_d(code int primary key)");
                DbcpTestSupport.execute(first, "insert into ledger_d values (41)");
                first.commit();
            }
            try (Connection second = source.getConnection()) {
                assertEquals(41, DbcpTestSupport.queryInt(second, "select code from ledger_d"));
            }
        }
    }
}
