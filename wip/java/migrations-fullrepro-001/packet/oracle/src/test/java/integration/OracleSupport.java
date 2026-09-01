package integration;

import java.io.Reader;
import java.io.StringReader;
import java.math.BigDecimal;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;
import org.apache.ibatis.migration.Change;
import org.apache.ibatis.migration.ConnectionProvider;
import org.apache.ibatis.migration.JdbcConnectionProvider;
import org.apache.ibatis.migration.MigrationLoader;

final class OracleSupport {

  private static final AtomicInteger DATABASE_SEQUENCE = new AtomicInteger();

  private OracleSupport() {
  }

  static Database database() {
    return new Database("jdbc:hsqldb:mem:migrations_oracle_" + DATABASE_SEQUENCE.incrementAndGet());
  }

  static MemoryLoader standardLoader() {
    return new MemoryLoader()
        .migration("1", "create changelog",
            "CREATE TABLE CHANGELOG (ID DECIMAL(20,0) NOT NULL PRIMARY KEY, APPLIED_AT VARCHAR(100) NOT NULL, DESCRIPTION VARCHAR(255) NOT NULL);",
            "DROP TABLE CHANGELOG;")
        .migration("2", "create widgets",
            "CREATE TABLE WIDGETS (ID INTEGER NOT NULL PRIMARY KEY, NAME VARCHAR(100));",
            "DROP TABLE WIDGETS;")
        .migration("3", "seed alpha",
            "INSERT INTO WIDGETS (ID, NAME) VALUES (10, 'alpha');",
            "DELETE FROM WIDGETS WHERE ID = 10;")
        .migration("4", "seed beta",
            "INSERT INTO WIDGETS (ID, NAME) VALUES (20, 'beta');",
            "DELETE FROM WIDGETS WHERE ID = 20;");
  }

  static final class Database {
    final String url;

    Database(String url) {
      this.url = url;
    }

    ConnectionProvider provider() {
      return new JdbcConnectionProvider("org.hsqldb.jdbc.JDBCDriver", url, "SA", "");
    }

    Connection open() throws SQLException {
      return DriverManager.getConnection(url, "SA", "");
    }

    void execute(String sql) throws SQLException {
      try (Connection connection = open(); Statement statement = connection.createStatement()) {
        statement.execute(sql);
      }
    }

    int count(String sql) throws SQLException {
      try (Connection connection = open(); Statement statement = connection.createStatement(); ResultSet result = statement.executeQuery(sql)) {
        result.next();
        return result.getInt(1);
      }
    }

    List<BigDecimal> ids(String table) throws SQLException {
      List<BigDecimal> ids = new ArrayList<>();
      try (Connection connection = open(); Statement statement = connection.createStatement(); ResultSet result = statement.executeQuery("SELECT ID FROM " + table + " ORDER BY ID")) {
        while (result.next()) {
          ids.add(result.getBigDecimal(1));
        }
      }
      return ids;
    }

    boolean tableExists(String name) throws SQLException {
      try (Connection connection = open(); ResultSet tables = connection.getMetaData().getTables(null, null, name.toUpperCase(), new String[] {"TABLE"})) {
        return tables.next();
      }
    }
  }

  static final class MemoryLoader implements MigrationLoader {
    private final Map<Change, String[]> migrations = new LinkedHashMap<>();
    private String bootstrap;
    private String onAbort;

    MemoryLoader migration(String id, String description, String up, String down) {
      Change change = new Change();
      change.setId(new BigDecimal(id));
      change.setDescription(description);
      change.setFilename(id + "_" + description.replace(' ', '_') + ".sql");
      migrations.put(change, new String[] {up, down});
      return this;
    }

    MemoryLoader bootstrap(String script) {
      bootstrap = script;
      return this;
    }

    MemoryLoader onAbort(String script) {
      onAbort = script;
      return this;
    }

    @Override
    public List<Change> getMigrations() {
      List<Change> changes = new ArrayList<>(migrations.keySet());
      changes.sort(Comparator.naturalOrder());
      return changes;
    }

    @Override
    public Reader getScriptReader(Change change, boolean undo) {
      String[] scripts = migrations.get(change);
      return scripts == null ? null : new StringReader(scripts[undo ? 1 : 0]);
    }

    @Override
    public Reader getBootstrapReader() {
      return bootstrap == null ? null : new StringReader(bootstrap);
    }

    @Override
    public Reader getOnAbortReader() {
      return onAbort == null ? null : new StringReader(onAbort);
    }
  }

  static final class TrackingProvider implements ConnectionProvider {
    private final Connection connection;

    TrackingProvider(Connection connection) {
      this.connection = connection;
    }

    @Override
    public Connection getConnection() {
      return connection;
    }
  }
}
