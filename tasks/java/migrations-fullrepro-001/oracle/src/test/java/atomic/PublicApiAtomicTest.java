package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.File;
import java.io.PrintWriter;
import java.io.Reader;
import java.math.BigDecimal;
import java.nio.charset.Charset;
import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.sql.SQLFeatureNotSupportedException;
import java.util.List;
import java.util.Properties;
import java.util.logging.Logger;
import javax.sql.DataSource;
import org.apache.ibatis.migration.Change;
import org.apache.ibatis.migration.DataSourceConnectionProvider;
import org.apache.ibatis.migration.Environment;
import org.apache.ibatis.migration.FileMigrationLoader;
import org.apache.ibatis.migration.JdbcConnectionProvider;
import org.apache.ibatis.migration.MigrationException;
import org.apache.ibatis.migration.hook.MigrationHook;
import org.apache.ibatis.migration.hook.NewHookContext;
import org.apache.ibatis.migration.hook.ScriptHookContext;
import org.apache.ibatis.migration.operations.UpOperation;
import org.apache.ibatis.migration.options.DatabaseOperationOption;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class PublicApiAtomicTest {

  @TempDir
  Path temporaryDirectory;

  /** Verifies: MIG-JAVA-006 */
  @Test
  void databaseOptionDefaultsChangelogAndDelimiter() {
    DatabaseOperationOption option = new DatabaseOperationOption();
    assertEquals("CHANGELOG", option.getChangelogTable());
    assertEquals(";", option.getDelimiter());
  }

  /** Verifies: MIG-JAVA-006 */
  @Test
  void databaseOptionDefaultsErrorFlags() {
    DatabaseOperationOption option = new DatabaseOperationOption();
    assertTrue(option.isStopOnError());
    assertTrue(option.isThrowWarning());
  }

  /** Verifies: MIG-JAVA-006 */
  @Test
  void databaseOptionDefaultsTransactionMode() {
    assertFalse(new DatabaseOperationOption().isAutoCommit());
  }

  /** Verifies: MIG-JAVA-006 */
  @Test
  void databaseOptionDefaultsScriptModes() {
    DatabaseOperationOption option = new DatabaseOperationOption();
    assertFalse(option.isSendFullScript());
    assertFalse(option.isRemoveCRs());
    assertTrue(option.isEscapeProcessing());
    assertFalse(option.isFullLineDelimiter());
  }

  /** Verifies: MIG-JAVA-007 */
  @Test
  void databaseOptionMutatesChangelogAndDelimiter() {
    DatabaseOperationOption option = new DatabaseOperationOption();
    option.setChangelogTable("MIG_LOG");
    option.setDelimiter("//");
    assertEquals("MIG_LOG", option.getChangelogTable());
    assertEquals("//", option.getDelimiter());
  }

  /** Verifies: MIG-JAVA-007 */
  @Test
  void databaseOptionMutatesErrorFlags() {
    DatabaseOperationOption option = new DatabaseOperationOption();
    option.setStopOnError(false);
    option.setThrowWarning(false);
    assertFalse(option.isStopOnError());
    assertFalse(option.isThrowWarning());
  }

  /** Verifies: MIG-JAVA-007 */
  @Test
  void databaseOptionMutatesAutoCommit() {
    DatabaseOperationOption option = new DatabaseOperationOption();
    option.setAutoCommit(true);
    assertTrue(option.isAutoCommit());
  }

  /** Verifies: MIG-JAVA-007 */
  @Test
  void databaseOptionMutatesFullScriptMode() {
    DatabaseOperationOption option = new DatabaseOperationOption();
    option.setSendFullScript(true);
    assertTrue(option.isSendFullScript());
  }

  /** Verifies: MIG-JAVA-007 */
  @Test
  void databaseOptionMutatesCrRemoval() {
    DatabaseOperationOption option = new DatabaseOperationOption();
    option.setRemoveCRs(true);
    assertTrue(option.isRemoveCRs());
  }

  /** Verifies: MIG-JAVA-007 */
  @Test
  void databaseOptionMutatesEscapeProcessing() {
    DatabaseOperationOption option = new DatabaseOperationOption();
    option.setEscapeProcessing(false);
    assertFalse(option.isEscapeProcessing());
  }

  /** Verifies: MIG-JAVA-007 */
  @Test
  void databaseOptionMutatesFullLineDelimiter() {
    DatabaseOperationOption option = new DatabaseOperationOption();
    option.setFullLineDelimiter(true);
    assertTrue(option.isFullLineDelimiter());
  }

  /** Verifies: MIG-JAVA-008 */
  @Test
  void changeDefaultInstanceExposesMutableProperties() {
    Change change = new Change();
    change.setId(new BigDecimal("17"));
    change.setDescription("create ledger");
    change.setAppliedTimestamp("2026-08-15 09:00:00");
    change.setFilename("17_create_ledger.sql");
    assertEquals(new BigDecimal("17"), change.getId());
    assertEquals("create ledger", change.getDescription());
    assertEquals("2026-08-15 09:00:00", change.getAppliedTimestamp());
    assertEquals("17_create_ledger.sql", change.getFilename());
  }

  /** Verifies: MIG-JAVA-008, MIG-JAVA-015 */
  @Test
  void changeCopyConstructorCopiesEveryPublicValue() {
    Change original = new Change(new BigDecimal("19"), "seed", "19_seed.sql");
    original.setAppliedTimestamp("now");
    Change copy = new Change(original);
    assertEquals(original.getId(), copy.getId());
    assertEquals(original.getDescription(), copy.getDescription());
    assertEquals(original.getAppliedTimestamp(), copy.getAppliedTimestamp());
    assertEquals(original.getFilename(), copy.getFilename());
  }

  /** Verifies: MIG-JAVA-010, MIG-JAVA-015 */
  @Test
  void changeEqualityUsesOnlyNumericId() {
    Change left = new Change(new BigDecimal("20"), "left", "left.sql");
    Change right = new Change(new BigDecimal("20"), "right", "right.sql");
    assertEquals(left, right);
  }

  /** Verifies: MIG-JAVA-010, MIG-JAVA-014 */
  @Test
  void changeNaturalOrderUsesAscendingNumericId() {
    List<Change> changes = new java.util.ArrayList<>(List.of(new Change(new BigDecimal("11")), new Change(new BigDecimal("2"))));
    changes.sort(null);
    assertEquals(List.of(new BigDecimal("2"), new BigDecimal("11")), List.of(changes.get(0).getId(), changes.get(1).getId()));
  }

  /** Verifies: MIG-JAVA-010, MIG-JAVA-015 */
  @Test
  void changeNaturalOrderTreatsEquivalentScalesAsEqual() {
    Change first = new Change(new BigDecimal("22.0"), "first", "first.sql");
    Change second = new Change(new BigDecimal("22.00"), "second", "second.sql");
    List<Change> changes = new java.util.ArrayList<>(List.of(first, second));
    changes.sort(null);
    assertEquals(List.of(first, second), changes);
  }

  /** Verifies: MIG-JAVA-009 */
  @Test
  void environmentChangelogVariableKeyIsPublicConstant() throws Exception {
    assertEquals("changelog", Environment.class.getField("CHANGELOG").get(null));
  }

  /** Verifies: MIG-ERR-001 */
  @Test
  void environmentMissingFileRaisesMigrationException() {
    File missing = temporaryDirectory.resolve("absent.properties").toFile();
    assertThrows(MigrationException.class, () -> new Environment(missing));
  }

  /** Verifies: MIG-CONF-009 */
  @Test
  void environmentUsesDocumentedDefaults() throws Exception {
    File file = write("empty.properties", "");
    Environment environment = new Environment(file);
    assertEquals("GMT+0:00", environment.getTimeZone());
    assertEquals(Charset.defaultCharset().name(), environment.getScriptCharset());
    assertEquals(";", environment.getDelimiter());
    assertTrue(environment.isIgnoreWarnings());
    assertFalse(environment.isAutoCommit());
  }

  /** Verifies: MIG-CONF-010 */
  @Test
  void environmentReadsExplicitScalarSettings() throws Exception {
    File file = write("scalar.properties", "time_zone=GMT+8:00\nscript_char_set=UTF-8\ndelimiter=//\ndriver_path=lib/db.jar\ndriver=driver.Type\nurl=jdbc:test\nusername=u\npassword=p\n");
    Environment environment = new Environment(file);
    assertEquals("GMT+8:00", environment.getTimeZone());
    assertEquals("UTF-8", environment.getScriptCharset());
    assertEquals("//", environment.getDelimiter());
    assertEquals("lib/db.jar", environment.getDriverPath());
    assertEquals("driver.Type", environment.getDriver());
    assertEquals("jdbc:test", environment.getUrl());
    assertEquals("u", environment.getUsername());
    assertEquals("p", environment.getPassword());
  }

  /** Verifies: MIG-CONF-010 */
  @Test
  void environmentReadsExplicitBooleanSettings() throws Exception {
    File file = write("boolean.properties", "full_line_delimiter=true\nsend_full_script=true\nauto_commit=true\nremove_crs=true\nignore_warnings=false\n");
    Environment environment = new Environment(file);
    assertTrue(environment.isFullLineDelimiter());
    assertTrue(environment.isSendFullScript());
    assertTrue(environment.isAutoCommit());
    assertTrue(environment.isRemoveCrs());
    assertFalse(environment.isIgnoreWarnings());
  }

  /** Verifies: MIG-CONF-013 */
  @Test
  void environmentExposesNonSettingVariables() throws Exception {
    Environment environment = new Environment(write("variables.properties", "tenant=blue\nregion=east\n"));
    assertEquals("blue", environment.getVariables().getProperty("tenant"));
    assertEquals("east", environment.getVariables().getProperty("region"));
  }

  /** Verifies: MIG-LOAD-001, MIG-LOAD-002 */
  @Test
  void fileLoaderDiscoversSqlMigrationIdentity() throws Exception {
    write("7_create_account_table.sql", "CREATE TABLE ACCOUNT(ID INT);\n-- //@UNDO\nDROP TABLE ACCOUNT;\n");
    Change change = new FileMigrationLoader(temporaryDirectory.toFile(), "UTF-8", new Properties()).getMigrations().get(0);
    assertEquals(new BigDecimal("7"), change.getId());
    assertEquals("create account table", change.getDescription());
    assertEquals("7_create_account_table.sql", change.getFilename());
  }

  /** Verifies: MIG-LOAD-001, MIG-LOAD-003, MIG-STATE-001 */
  @Test
  void fileLoaderSortsAndFiltersMigrationFiles() throws Exception {
    write("20_later.sql", "SELECT 20;\n-- //@UNDO\nSELECT -20;\n");
    write("03_earlier.sql", "SELECT 3;\n-- //@UNDO\nSELECT -3;\n");
    write("notes.txt", "ignored");
    write("bootstrap.sql", "SELECT 0;");
    write("onabort.sql", "SELECT -1;");
    List<Change> changes = new FileMigrationLoader(temporaryDirectory.toFile(), "UTF-8", new Properties()).getMigrations();
    assertEquals(List.of(new BigDecimal("3"), new BigDecimal("20")), List.of(changes.get(0).getId(), changes.get(1).getId()));
  }

  /** Verifies: MIG-LOAD-001, MIG-LOAD-004, MIG-LOAD-020 */
  @Test
  void fileLoaderReturnsForwardSection() throws Exception {
    write("8_sections.sql", "CREATE TABLE FORWARD_ONLY(ID INT);\n-- //@UNDO\nDROP TABLE FORWARD_ONLY;\n");
    FileMigrationLoader loader = new FileMigrationLoader(temporaryDirectory.toFile(), "UTF-8", new Properties());
    assertTrue(read(loader.getScriptReader(loader.getMigrations().get(0), false)).contains("CREATE TABLE FORWARD_ONLY"));
    assertFalse(read(loader.getScriptReader(loader.getMigrations().get(0), false)).contains("DROP TABLE FORWARD_ONLY"));
  }

  /** Verifies: MIG-LOAD-001, MIG-LOAD-004, MIG-LOAD-020 */
  @Test
  void fileLoaderReturnsReverseSection() throws Exception {
    write("9_sections.sql", "CREATE TABLE REVERSE_ONLY(ID INT);\n-- //@UNDO\nDROP TABLE REVERSE_ONLY;\n");
    FileMigrationLoader loader = new FileMigrationLoader(temporaryDirectory.toFile(), "UTF-8", new Properties());
    assertTrue(read(loader.getScriptReader(loader.getMigrations().get(0), true)).contains("DROP TABLE REVERSE_ONLY"));
    assertFalse(read(loader.getScriptReader(loader.getMigrations().get(0), true)).contains("CREATE TABLE REVERSE_ONLY"));
  }

  /** Verifies: MIG-LOAD-001, MIG-LOAD-005, MIG-LOAD-020 */
  @Test
  void fileLoaderSubstitutesVariablesInBothDirections() throws Exception {
    write("10_substitute.sql", "CREATE TABLE ${table_name}(ID INT);\n-- //@UNDO\nDROP TABLE ${table_name};\n");
    Properties variables = new Properties();
    variables.setProperty("table_name", "LEDGER_ENTRY");
    FileMigrationLoader loader = new FileMigrationLoader(temporaryDirectory.toFile(), "UTF-8", variables);
    Change change = loader.getMigrations().get(0);
    assertTrue(read(loader.getScriptReader(change, false)).contains("LEDGER_ENTRY"));
    assertTrue(read(loader.getScriptReader(change, true)).contains("LEDGER_ENTRY"));
  }

  /** Verifies: MIG-LOAD-001, MIG-LOAD-007, MIG-LOAD-020 */
  @Test
  void fileLoaderReturnsExistingAndMissingSpecialScripts() throws Exception {
    write("bootstrap.sql", "CREATE TABLE BASELINE(ID INT);");
    FileMigrationLoader loader = new FileMigrationLoader(temporaryDirectory.toFile(), "UTF-8", new Properties());
    assertTrue(read(loader.getBootstrapReader()).contains("BASELINE"));
    assertNull(loader.getOnAbortReader());
  }

  /** Verifies: MIG-LOAD-001, MIG-LOAD-006, MIG-ERR-004 */
  @Test
  void fileLoaderRejectsMalformedMigrationName() throws Exception {
    write("not_numeric.sql", "SELECT 1;\n-- //@UNDO\nSELECT 2;\n");
    assertThrows(MigrationException.class,
        () -> new FileMigrationLoader(temporaryDirectory.toFile(), "UTF-8", new Properties()).getMigrations());
  }

  /** Verifies: MIG-JAVA-003 */
  @Test
  void dataSourceConnectionProviderDelegatesEachRequest() throws Exception {
    String url = "jdbc:hsqldb:mem:atomic_ds_" + System.nanoTime();
    Connection expected = DriverManager.getConnection(url, "SA", "");
    DataSource source = singleConnectionDataSource(expected);
    assertSame(expected, new DataSourceConnectionProvider(source).getConnection());
    expected.close();
  }

  /** Verifies: MIG-JAVA-005, MIG-ERR-008 */
  @Test
  void jdbcConnectionProviderRejectsMissingDriver() {
    assertThrows(IllegalStateException.class,
        () -> new JdbcConnectionProvider("missing.driver.Type", "jdbc:missing", "u", "p"));
  }

  /** Verifies: MIG-ERR-005 */
  @Test
  void upRejectsZeroStepCount() {
    assertThrows(IllegalArgumentException.class, () -> new UpOperation(0));
  }

  /** Verifies: MIG-ERR-005 */
  @Test
  void upRejectsNegativeStepCount() {
    assertThrows(IllegalArgumentException.class, () -> new UpOperation(-3));
  }

  /** Verifies: MIG-HOOK-007 */
  @Test
  void migrationHookContextBindingUsesPublicKey() throws Exception {
    assertEquals("hookContext", MigrationHook.class.getField("HOOK_CONTEXT").get(null));
  }

  /** Verifies: MIG-HOOK-010 */
  @Test
  void newHookContextExposesSuppliedDescriptionAndFilename() {
    NewHookContext context = new NewHookContext("create invoice", "25_create_invoice.sql");
    assertEquals("create invoice", context.getDescription());
    assertEquals("25_create_invoice.sql", context.getFilename());
  }

  /** Verifies: MIG-HOOK-011, MIG-JAVA-008, MIG-JAVA-014 */
  @Test
  void scriptHookContextExposesForwardSelection() {
    Change change = new Change(new BigDecimal("26"));
    change.setDescription("create invoice");
    change.setAppliedTimestamp("2026-08-15 10:00:00");
    change.setFilename("26_create_invoice.sql");
    ScriptHookContext context = new ScriptHookContext(change, false);
    Change selected = context.getChange();
    assertEquals(change.getId(), selected.getId());
    assertEquals(change.getDescription(), selected.getDescription());
    assertEquals(change.getAppliedTimestamp(), selected.getAppliedTimestamp());
    assertEquals(change.getFilename(), selected.getFilename());
    assertFalse(context.isUndo());
  }

  /** Verifies: MIG-HOOK-011, MIG-JAVA-008, MIG-JAVA-014 */
  @Test
  void scriptHookContextExposesUndoSelection() {
    Change change = new Change(new BigDecimal("27"));
    change.setDescription("drop invoice");
    change.setAppliedTimestamp("2026-08-15 11:00:00");
    change.setFilename("27_drop_invoice.sql");
    ScriptHookContext context = new ScriptHookContext(change, true);
    Change selected = context.getChange();
    assertEquals(change.getId(), selected.getId());
    assertEquals(change.getDescription(), selected.getDescription());
    assertEquals(change.getAppliedTimestamp(), selected.getAppliedTimestamp());
    assertEquals(change.getFilename(), selected.getFilename());
    assertTrue(context.isUndo());
  }

  private File write(String name, String content) throws Exception {
    Path path = temporaryDirectory.resolve(name);
    Files.writeString(path, content);
    return path.toFile();
  }

  private static String read(Reader reader) throws Exception {
    try (Reader closeable = reader) {
      StringBuilder text = new StringBuilder();
      char[] buffer = new char[256];
      int count;
      while ((count = closeable.read(buffer)) >= 0) {
        text.append(buffer, 0, count);
      }
      return text.toString();
    }
  }

  private static DataSource singleConnectionDataSource(Connection connection) {
    return new DataSource() {
      @Override public Connection getConnection() { return connection; }
      @Override public Connection getConnection(String username, String password) { return connection; }
      @Override public PrintWriter getLogWriter() { return null; }
      @Override public void setLogWriter(PrintWriter out) { }
      @Override public void setLoginTimeout(int seconds) { }
      @Override public int getLoginTimeout() { return 0; }
      @Override public Logger getParentLogger() throws SQLFeatureNotSupportedException { throw new SQLFeatureNotSupportedException(); }
      @Override public <T> T unwrap(Class<T> iface) throws SQLException { throw new SQLException(); }
      @Override public boolean isWrapperFor(Class<?> iface) { return false; }
    };
  }
}
