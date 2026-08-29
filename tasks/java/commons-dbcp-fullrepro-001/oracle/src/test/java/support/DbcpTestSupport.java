package support;

import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.time.Duration;
import org.apache.commons.dbcp2.BasicDataSource;

public final class DbcpTestSupport {
    private DbcpTestSupport() {
    }

    public static BasicDataSource dataSource(final String databaseName) {
        final BasicDataSource source = new BasicDataSource();
        source.setUrl("jdbc:h2:mem:" + databaseName + ";DB_CLOSE_DELAY=-1");
        source.setUsername("sa");
        source.setPassword("");
        source.setMaxTotal(3);
        source.setMaxWait(Duration.ofMillis(300));
        return source;
    }

    public static void execute(final Connection connection, final String sql) throws SQLException {
        try (Statement statement = connection.createStatement()) {
            statement.execute(sql);
        }
    }

    public static int queryInt(final Connection connection, final String sql) throws SQLException {
        try (Statement statement = connection.createStatement();
             ResultSet resultSet = statement.executeQuery(sql)) {
            resultSet.next();
            return resultSet.getInt(1);
        }
    }
}
