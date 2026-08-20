package integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.util.List;
import java.util.Properties;
import java.util.stream.Collectors;
import org.apache.ibatis.migration.Change;
import org.apache.ibatis.migration.FileMigrationLoader;
import org.apache.ibatis.migration.JavaMigrationLoader;
import org.apache.ibatis.migration.JdbcConnectionProvider;
import org.apache.ibatis.migration.operations.UpOperation;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class LoaderCrossViewIntegrationTest {

  @TempDir
  Path temporaryDirectory;

  /**
   * Verifies: MIG-INV-005, MIG-LOAD-001, MIG-LOAD-002, MIG-LOAD-015
   * Depends-On: fileLoaderSortsAndFiltersMigrationFiles, changeEqualityUsesOnlyNumericId
   * Seam: filesystem and Java discovery -> equal numeric identities -> shared ordering
   */
  @Test
  void filesystemAndJavaLoadersProduceEqualIdentitiesAndOrder() throws Exception {
    FileMigrationLoader files = fileLoader();
    JavaMigrationLoader classes = new JavaMigrationLoader("integration.javamigrations");
    List<Change> fileChanges = new java.util.ArrayList<>(files.getMigrations());
    List<Change> javaChanges = new java.util.ArrayList<>(classes.getMigrations());
    fileChanges.sort(null);
    javaChanges.sort(null);
    assertEquals(List.of(new BigDecimal("41"), new BigDecimal("42")), ids(fileChanges));
    assertEquals(ids(fileChanges), ids(javaChanges));
    assertEquals(fileChanges, javaChanges);
  }

  /**
   * Verifies: MIG-INV-005, MIG-LOAD-001, MIG-LOAD-017, MIG-LOAD-020, MIG-STATE-001, MIG-JAVA-018
   * Depends-On: fileLoaderReturnsForwardSection, changeNaturalOrderUsesAscendingNumericId
   * Seam: equal loader identities -> direction-specific readers -> equivalent lifecycle schema
   */
  @Test
  void filesystemAndJavaLoadersApplyEquivalentLifecycleState() throws Exception {
    String fileUrl = "jdbc:hsqldb:mem:file_loader_" + System.nanoTime();
    String javaUrl = "jdbc:hsqldb:mem:java_loader_" + System.nanoTime();
    new UpOperation().operate(provider(fileUrl), fileLoader(), null, null);
    new UpOperation().operate(provider(javaUrl), new JavaMigrationLoader("integration.javamigrations"), null, null);
    assertEquals(databaseIds(fileUrl), databaseIds(javaUrl));
    assertTrue(tableExists(fileUrl, "JAVA_AUDIT"));
    assertTrue(tableExists(javaUrl, "JAVA_AUDIT"));
  }

  private FileMigrationLoader fileLoader() throws Exception {
    Path scripts = temporaryDirectory.resolve("loader-scripts");
    Files.createDirectories(scripts);
    Files.writeString(scripts.resolve("041_create_changelog.sql"),
        "CREATE TABLE CHANGELOG (ID DECIMAL(20,0) NOT NULL PRIMARY KEY, APPLIED_AT VARCHAR(100) NOT NULL, DESCRIPTION VARCHAR(255) NOT NULL);\n-- //@UNDO\nDROP TABLE CHANGELOG;\n",
        StandardCharsets.UTF_8);
    Files.writeString(scripts.resolve("042_create_audit.sql"),
        "CREATE TABLE JAVA_AUDIT(ID DECIMAL(20,0) PRIMARY KEY);\n-- //@UNDO\nDROP TABLE JAVA_AUDIT;\n",
        StandardCharsets.UTF_8);
    return new FileMigrationLoader(scripts.toFile(), "UTF-8", new Properties());
  }

  private static JdbcConnectionProvider provider(String url) {
    return new JdbcConnectionProvider("org.hsqldb.jdbc.JDBCDriver", url, "SA", "");
  }

  private static List<BigDecimal> ids(List<Change> changes) {
    return changes.stream().map(Change::getId).collect(Collectors.toList());
  }

  private static List<BigDecimal> databaseIds(String url) throws Exception {
    try (Connection connection = DriverManager.getConnection(url, "SA", "");
         ResultSet rows = connection.createStatement().executeQuery("SELECT ID FROM CHANGELOG ORDER BY ID")) {
      java.util.ArrayList<BigDecimal> ids = new java.util.ArrayList<>();
      while (rows.next()) {
        ids.add(rows.getBigDecimal(1));
      }
      return ids;
    }
  }

  private static boolean tableExists(String url, String name) throws Exception {
    try (Connection connection = DriverManager.getConnection(url, "SA", "");
         ResultSet tables = connection.getMetaData().getTables(null, null, name, new String[] {"TABLE"})) {
      return tables.next();
    }
  }
}
