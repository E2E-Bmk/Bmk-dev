package integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.sql.CallableStatement;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import org.apache.commons.dbcp2.BasicDataSource;
import org.junit.jupiter.api.Test;
import support.DbcpTestSupport;

class StatementPoolingIntegrationTest {
    /**
     * CVI-8: Seam: protocol handoff preserves prepared query results through pooling.
     * Verifies: DBCP-CVI-008, DBCP-STMT-002, DBCP-STMT-003.
     * Depends-On: basicSourceEnablesStatementPoolingPolicy, driverManagerFactoryCreatesUsablePhysicalConnection.
     */
    @Test
    void pooledPreparedStatementPreservesQueryResult() throws Exception {
        try (BasicDataSource source = DbcpTestSupport.dataSource("mauve_statement_result")) {
            source.setPoolPreparedStatements(true);
            try (Connection connection = source.getConnection();
                 PreparedStatement statement = connection.prepareStatement("select ? + 5")) {
                statement.setInt(1, 37);
                try (ResultSet result = statement.executeQuery()) {
                    assertTrue(result.next());
                    assertEquals(42, result.getInt(1));
                }
            }
        }
    }

    /**
     * CVI-8: Seam: lifecycle crossing reactivates a closed logical statement.
     * Verifies: DBCP-CVI-008, DBCP-STMT-003, DBCP-STMT-007.
     * Depends-On: basicSourceEnablesStatementPoolingPolicy, closeMarksWrapperClosed.
     */
    @Test
    void repeatedPreparationAfterCloseAcceptsFreshParameters() throws Exception {
        try (BasicDataSource source = DbcpTestSupport.dataSource("navy_statement_reactivate");
             Connection connection = configurePooling(source)) {
            try (PreparedStatement first = connection.prepareStatement("select ? * 2")) {
                first.setInt(1, 13);
                assertEquals(26, scalar(first));
            }
            try (PreparedStatement second = connection.prepareStatement("select ? * 2")) {
                second.setInt(1, 17);
                assertEquals(34, scalar(second));
            }
        }
    }

    /**
     * CVI-8: Seam: error propagation enforces per-connection statement capacity.
     * Verifies: DBCP-CVI-008, DBCP-STMT-005, DBCP-ERR-006.
     * Depends-On: basicSourceStoresStatementLimit, basicSourceEnablesStatementPoolingPolicy.
     */
    @Test
    void statementLimitRejectsSecondConcurrentIdentity() throws Exception {
        try (BasicDataSource source = DbcpTestSupport.dataSource("ochre_statement_limit")) {
            source.setPoolPreparedStatements(true);
            source.setMaxOpenPreparedStatements(1);
            try (Connection connection = source.getConnection();
                 PreparedStatement first = connection.prepareStatement("select 79")) {
                assertEquals(79, scalar(first));
                assertThrows(SQLException.class,
                        () -> connection.prepareStatement("select 81"));
            }
        }
    }

    /**
     * CVI-8: Seam: state consistency clears idle statements on connection return.
     * Verifies: DBCP-CVI-008, DBCP-STMT-006, DBCP-STMT-007.
     * Depends-On: basicSourceStoresClearOnReturnPolicy, basicSourceEnablesStatementPoolingPolicy.
     */
    @Test
    void clearOnReturnStillAllowsLaterCallableResult() throws Exception {
        try (BasicDataSource source = DbcpTestSupport.dataSource("plum_statement_clear")) {
            source.setPoolPreparedStatements(true);
            source.setClearStatementPoolOnReturn(true);
            try (Connection first = source.getConnection();
                 PreparedStatement statement = first.prepareStatement("select 89")) {
                assertEquals(89, scalar(statement));
            }
            try (Connection second = source.getConnection();
                 CallableStatement statement = second.prepareCall("select 97")) {
                try (ResultSet result = statement.executeQuery()) {
                    assertTrue(result.next());
                    assertEquals(97, result.getInt(1));
                }
            }
        }
    }

    private Connection configurePooling(final BasicDataSource source) throws SQLException {
        source.setPoolPreparedStatements(true);
        source.setMaxOpenPreparedStatements(4);
        return source.getConnection();
    }

    private int scalar(final PreparedStatement statement) throws SQLException {
        try (ResultSet result = statement.executeQuery()) {
            result.next();
            return result.getInt(1);
        }
    }
}
