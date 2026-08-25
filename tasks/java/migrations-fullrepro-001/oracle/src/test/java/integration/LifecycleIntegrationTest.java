package integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import integration.OracleSupport.Database;
import integration.OracleSupport.MemoryLoader;
import integration.OracleSupport.TrackingProvider;
import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.sql.Connection;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import org.apache.ibatis.migration.Change;
import org.apache.ibatis.migration.ConnectionProvider;
import org.apache.ibatis.migration.MigrationException;
import org.apache.ibatis.migration.hook.HookContext;
import org.apache.ibatis.migration.hook.MigrationHook;
import org.apache.ibatis.migration.operations.BootstrapOperation;
import org.apache.ibatis.migration.operations.DownOperation;
import org.apache.ibatis.migration.operations.PendingOperation;
import org.apache.ibatis.migration.operations.StatusOperation;
import org.apache.ibatis.migration.operations.UpOperation;
import org.apache.ibatis.migration.operations.VersionOperation;
import org.apache.ibatis.migration.options.DatabaseOperationOption;
import org.junit.jupiter.api.Test;

class LifecycleIntegrationTest {

  /**
   * Verifies: MIG-LIFE-001, MIG-LIFE-003, MIG-STATE-002, MIG-JAVA-018
   * Depends-On: fileLoaderSortsAndFiltersMigrationFiles, databaseOptionDefaultsChangelogAndDelimiter
   * Seam: ordered loader changes -> forward SQL execution -> changelog rows
   */
  @Test
  void upAppliesAllEligibleMigrationsAndRecordsThem() throws Exception {
    Database database = OracleSupport.database();
    new UpOperation().operate(database.provider(), OracleSupport.standardLoader(), null, null);
    assertEquals(List.of(new BigDecimal("1"), new BigDecimal("2"), new BigDecimal("3"), new BigDecimal("4")), database.ids("CHANGELOG"));
    assertEquals(2, database.count("SELECT COUNT(*) FROM WIDGETS"));
  }

  /**
   * Verifies: MIG-LIFE-002, MIG-JAVA-018
   * Depends-On: changeNaturalOrderUsesAscendingNumericId
   * Seam: operation step limit -> loader ordering -> durable changelog
   */
  @Test
  void upStepLimitOneAppliesOnlyFirstEligibleMigration() throws Exception {
    Database database = OracleSupport.database();
    new UpOperation(1).operate(database.provider(), OracleSupport.standardLoader(), null, null);
    assertEquals(List.of(new BigDecimal("1")), database.ids("CHANGELOG"));
    assertFalse(database.tableExists("WIDGETS"));
  }

  /**
   * Verifies: MIG-LIFE-002, MIG-JAVA-018
   * Depends-On: changeNaturalOrderUsesAscendingNumericId
   * Seam: multi-step limit -> schema creation -> changelog boundary
   */
  @Test
  void upStepLimitTwoStopsAtSecondMigration() throws Exception {
    Database database = OracleSupport.database();
    new UpOperation(2).operate(database.provider(), OracleSupport.standardLoader(), null, null);
    assertEquals(List.of(new BigDecimal("1"), new BigDecimal("2")), database.ids("CHANGELOG"));
    assertTrue(database.tableExists("WIDGETS"));
    assertEquals(0, database.count("SELECT COUNT(*) FROM WIDGETS"));
  }

  /**
   * Verifies: MIG-LIFE-001, MIG-STATE-001, MIG-JAVA-018
   * Depends-On: changeNaturalOrderUsesAscendingNumericId
   * Seam: unsorted loader insertion -> numeric operation order -> schema dependencies
   */
  @Test
  void upConsumesChangesInNumericOrder() throws Exception {
    Database database = OracleSupport.database();
    MemoryLoader loader = new MemoryLoader()
        .migration("3", "insert", "INSERT INTO ORDER_TEST VALUES (3);", "DELETE FROM ORDER_TEST WHERE ID=3;")
        .migration("1", "log", changelogSql("CHANGELOG"), "DROP TABLE CHANGELOG;")
        .migration("2", "table", "CREATE TABLE ORDER_TEST(ID INT);", "DROP TABLE ORDER_TEST;");
    new UpOperation().operate(database.provider(), loader, null, null);
    assertEquals(3, database.count("SELECT ID FROM ORDER_TEST"));
    assertEquals(List.of(new BigDecimal("1"), new BigDecimal("2"), new BigDecimal("3")), database.ids("CHANGELOG"));
  }

  /**
   * Verifies: MIG-LIFE-001, MIG-HOOK-004, MIG-JAVA-018
   * Depends-On: changeEqualityUsesOnlyNumericId
   * Seam: existing changelog state -> eligibility decision -> operation no-op
   */
  @Test
  void repeatedUpIsNoOpForCurrentDatabase() throws Exception {
    Database database = OracleSupport.database();
    MemoryLoader loader = OracleSupport.standardLoader();
    new UpOperation().operate(database.provider(), loader, null, null);
    new UpOperation().operate(database.provider(), loader, null, null);
    assertEquals(4, database.count("SELECT COUNT(*) FROM CHANGELOG"));
    assertEquals(2, database.count("SELECT COUNT(*) FROM WIDGETS"));
  }

  /**
   * Verifies: MIG-JAVA-011, MIG-JAVA-018
   * Depends-On: databaseOptionDefaultsTransactionMode
   * Seam: operation completion -> fluent result identity
   */
  @Test
  void upReturnsSameOperationInstance() {
    Database database = OracleSupport.database();
    UpOperation operation = new UpOperation(1);
    assertSame(operation, operation.operate(database.provider(), OracleSupport.standardLoader(), null, null));
  }

  /**
   * Verifies: MIG-JAVA-011, MIG-JAVA-018
   * Depends-On: dataSourceConnectionProviderDelegatesEachRequest
   * Seam: provider acquisition -> operation lifecycle -> JDBC close
   */
  @Test
  void upClosesProviderConnection() throws Exception {
    Database database = OracleSupport.database();
    Connection connection = database.open();
    new UpOperation(1).operate(new TrackingProvider(connection), OracleSupport.standardLoader(), null, null);
    assertTrue(connection.isClosed());
  }

  /**
   * Verifies: MIG-JAVA-012, MIG-JAVA-018
   * Depends-On: databaseOptionDefaultsChangelogAndDelimiter
   * Seam: lifecycle execution -> optional output boundary
   */
  @Test
  void upCompletesWithNullOutputStream() throws Exception {
    Database database = OracleSupport.database();
    new UpOperation(2).operate(database.provider(), OracleSupport.standardLoader(), null, null);
    assertTrue(database.tableExists("WIDGETS"));
  }

  /**
   * Verifies: MIG-JAVA-012, MIG-JAVA-018
   * Depends-On: databaseOptionDefaultsChangelogAndDelimiter
   * Seam: lifecycle progress -> supplied print stream
   */
  @Test
  void upReportsProgressToSuppliedStream() {
    Database database = OracleSupport.database();
    ByteArrayOutputStream bytes = new ByteArrayOutputStream();
    new UpOperation(1).operate(database.provider(), OracleSupport.standardLoader(), null, new PrintStream(bytes));
    assertFalse(bytes.toString(StandardCharsets.UTF_8).isBlank());
  }

  /**
   * Verifies: MIG-JAVA-007, MIG-JAVA-018
   * Depends-On: databaseOptionDefaultsChangelogAndDelimiter, databaseOptionDefaultsTransactionMode
   * Seam: null option -> documented defaults -> successful lifecycle
   */
  @Test
  void nullOperationOptionSelectsDocumentedDefaults() throws Exception {
    Database database = OracleSupport.database();
    new UpOperation(1).operate(database.provider(), OracleSupport.standardLoader(), null, null);
    assertTrue(database.tableExists("CHANGELOG"));
    assertEquals(1, database.count("SELECT COUNT(*) FROM CHANGELOG"));
  }

  /**
   * Verifies: MIG-LIFE-006, MIG-LIFE-007, MIG-INV-003, MIG-JAVA-018
   * Depends-On: fileLoaderReturnsReverseSection, changeNaturalOrderUsesAscendingNumericId
   * Seam: latest changelog identity -> reverse reader -> schema and changelog update
   */
  @Test
  void downDefaultReversesLatestAppliedMigration() throws Exception {
    Database database = fullyUpgradedDatabase();
    new DownOperation().operate(database.provider(), OracleSupport.standardLoader(), null, null);
    assertEquals(1, database.count("SELECT COUNT(*) FROM WIDGETS"));
    assertEquals(List.of(new BigDecimal("1"), new BigDecimal("2"), new BigDecimal("3")), database.ids("CHANGELOG"));
  }

  /**
   * Verifies: MIG-LIFE-007, MIG-INV-003, MIG-JAVA-018
   * Depends-On: fileLoaderReturnsReverseSection, changeNaturalOrderUsesAscendingNumericId
   * Seam: down step count -> descending rollback readers -> changelog deletion
   */
  @Test
  void downStepLimitReversesNewestChangesInDescendingOrder() throws Exception {
    Database database = fullyUpgradedDatabase();
    new DownOperation(2).operate(database.provider(), OracleSupport.standardLoader(), null, null);
    assertEquals(0, database.count("SELECT COUNT(*) FROM WIDGETS"));
    assertEquals(List.of(new BigDecimal("1"), new BigDecimal("2")), database.ids("CHANGELOG"));
  }

  /**
   * Verifies: MIG-JAVA-011, MIG-JAVA-018
   * Depends-On: databaseOptionDefaultsTransactionMode
   * Seam: rollback completion -> fluent result identity
   */
  @Test
  void downReturnsSameOperationInstance() throws Exception {
    Database database = fullyUpgradedDatabase();
    DownOperation operation = new DownOperation();
    assertSame(operation, operation.operate(database.provider(), OracleSupport.standardLoader(), null, null));
  }

  /**
   * Verifies: MIG-JAVA-011, MIG-JAVA-018
   * Depends-On: dataSourceConnectionProviderDelegatesEachRequest
   * Seam: rollback provider acquisition -> operation lifecycle -> JDBC close
   */
  @Test
  void downClosesProviderConnection() throws Exception {
    Database database = fullyUpgradedDatabase();
    Connection connection = database.open();
    new DownOperation().operate(new TrackingProvider(connection), OracleSupport.standardLoader(), null, null);
    assertTrue(connection.isClosed());
  }

  /**
   * Verifies: MIG-HOOK-004, MIG-HOOK-016, MIG-HOOK-017, MIG-JAVA-016
   * Depends-On: changeEqualityUsesOnlyNumericId
   * Seam: no eligible up change -> hook suppression
   */
  @Test
  void noOpUpDoesNotInvokeHooks() throws Exception {
    Database database = fullyUpgradedDatabase();
    RecordingHook hook = new RecordingHook();
    new UpOperation().operate(database.provider(), OracleSupport.standardLoader(), null, null, hook);
    assertTrue(hook.events.isEmpty());
  }

  /**
   * Verifies: MIG-LIFE-014
   * Depends-On: changeNaturalOrderUsesAscendingNumericId
   * Seam: changelog gap below latest -> pending selection -> forward SQL and row restoration
   */
  @Test
  void pendingAppliesOutOfOrderChangelogGap() throws Exception {
    Database database = fullyUpgradedDatabase();
    database.execute("DELETE FROM CHANGELOG WHERE ID=3");
    database.execute("DELETE FROM WIDGETS WHERE ID=10");
    new PendingOperation().operate(database.provider(), OracleSupport.standardLoader(), null, null);
    assertEquals(List.of(new BigDecimal("1"), new BigDecimal("2"), new BigDecimal("3"), new BigDecimal("4")), database.ids("CHANGELOG"));
    assertEquals(1, database.count("SELECT COUNT(*) FROM WIDGETS WHERE ID=10"));
  }

  /**
   * Verifies: MIG-LIFE-014, MIG-STATE-001
   * Depends-On: changeNaturalOrderUsesAscendingNumericId
   * Seam: multiple changelog gaps -> numeric pending order -> dependent SQL
   */
  @Test
  void pendingAppliesMultipleGapsInAscendingOrder() throws Exception {
    Database database = fullyUpgradedDatabase();
    database.execute("DELETE FROM CHANGELOG WHERE ID IN (3,4)");
    database.execute("DELETE FROM WIDGETS");
    new PendingOperation().operate(database.provider(), OracleSupport.standardLoader(), null, null);
    assertEquals(List.of(new BigDecimal("10"), new BigDecimal("20")), database.ids("WIDGETS"));
  }

  /**
   * Verifies: MIG-LIFE-015, MIG-ERR-007
   * Depends-On: changeDefaultInstanceExposesMutableProperties
   * Seam: pending selection -> absent changelog -> typed failure without SQL execution
   */
  @Test
  void pendingWithoutChangelogRaisesMigrationException() throws Exception {
    Database database = OracleSupport.database();
    MemoryLoader loader = new MemoryLoader().migration("2", "table", "CREATE TABLE SHOULD_NOT_EXIST(ID INT);", "DROP TABLE SHOULD_NOT_EXIST;");
    assertThrows(MigrationException.class, () -> new PendingOperation().operate(database.provider(), loader, null, null));
    assertFalse(database.tableExists("SHOULD_NOT_EXIST"));
  }

  /**
   * Verifies: MIG-LIFE-010
   * Depends-On: changeNaturalOrderUsesAscendingNumericId
   * Seam: target identity -> bounded forward selection -> schema and changelog
   */
  @Test
  void versionMovesUpThroughTargetInclusively() throws Exception {
    Database database = OracleSupport.database();
    new VersionOperation(new BigDecimal("3")).operate(database.provider(), OracleSupport.standardLoader(), null, null);
    assertEquals(List.of(new BigDecimal("1"), new BigDecimal("2"), new BigDecimal("3")), database.ids("CHANGELOG"));
    assertEquals(1, database.count("SELECT COUNT(*) FROM WIDGETS"));
  }

  /**
   * Verifies: MIG-LIFE-011
   * Depends-On: fileLoaderReturnsReverseSection, changeNaturalOrderUsesAscendingNumericId
   * Seam: lower target identity -> descending undo selection -> retained target row
   */
  @Test
  void versionMovesDownAndLeavesTargetApplied() throws Exception {
    Database database = fullyUpgradedDatabase();
    new VersionOperation(new BigDecimal("2")).operate(database.provider(), OracleSupport.standardLoader(), null, null);
    assertEquals(List.of(new BigDecimal("1"), new BigDecimal("2")), database.ids("CHANGELOG"));
    assertEquals(0, database.count("SELECT COUNT(*) FROM WIDGETS"));
  }

  /**
   * Verifies: MIG-LIFE-012
   * Depends-On: changeEqualityUsesOnlyNumericId
   * Seam: current version comparison -> no-op lifecycle -> unchanged rows
   */
  @Test
  void versionAtCurrentTargetLeavesStateUnchanged() throws Exception {
    Database database = fullyUpgradedDatabase();
    new VersionOperation(new BigDecimal("4")).operate(database.provider(), OracleSupport.standardLoader(), null, null);
    assertEquals(4, database.count("SELECT COUNT(*) FROM CHANGELOG"));
    assertEquals(2, database.count("SELECT COUNT(*) FROM WIDGETS"));
  }

  /**
   * Verifies: MIG-LIFE-013, MIG-ERR-006
   * Depends-On: changeEqualityUsesOnlyNumericId
   * Seam: target lookup -> repository miss -> typed failure
   */
  @Test
  void versionMissingTargetRaisesMigrationException() throws Exception {
    Database database = fullyUpgradedDatabase();
    assertThrows(MigrationException.class,
        () -> new VersionOperation(new BigDecimal("99")).operate(database.provider(), OracleSupport.standardLoader(), null, null));
    assertEquals(4, database.count("SELECT COUNT(*) FROM CHANGELOG"));
  }

  /**
   * Verifies: MIG-VIEW-001
   * Depends-On: changeDefaultInstanceExposesMutableProperties
   * Seam: repository loader -> absent changelog -> pending status projection
   */
  @Test
  void statusWithoutChangelogReturnsAllRepositoryChangesPending() {
    Database database = OracleSupport.database();
    StatusOperation status = new StatusOperation().operate(database.provider(), OracleSupport.standardLoader(), null, null);
    assertEquals(0, status.getAppliedCount());
    assertEquals(4, status.getPendingCount());
    assertEquals(0, status.getMissingCount());
    assertEquals(4, status.getCurrentStatus().size());
  }

  /**
   * Verifies: MIG-VIEW-002, MIG-VIEW-003
   * Depends-On: changeEqualityUsesOnlyNumericId
   * Seam: loader set plus changelog set -> combined counts and list
   */
  @Test
  void statusAtCurrentVersionReportsAllApplied() throws Exception {
    Database database = fullyUpgradedDatabase();
    StatusOperation status = new StatusOperation().operate(database.provider(), OracleSupport.standardLoader(), null, null);
    assertEquals(4, status.getAppliedCount());
    assertEquals(0, status.getPendingCount());
    assertEquals(0, status.getMissingCount());
    assertEquals(4, status.getCurrentStatus().size());
    assertTrue(status.getCurrentStatus().stream().allMatch(change -> change.getAppliedTimestamp() != null));
  }

  /**
   * Verifies: MIG-VIEW-002, MIG-VIEW-003, MIG-STATE-003
   * Depends-On: changeEqualityUsesOnlyNumericId
   * Seam: repository-only and changelog-only identities -> mixed status union
   */
  @Test
  void statusCombinesAppliedPendingAndMissingChanges() throws Exception {
    Database database = fullyUpgradedDatabase();
    database.execute("DELETE FROM CHANGELOG WHERE ID=4");
    database.execute("INSERT INTO CHANGELOG(ID, APPLIED_AT, DESCRIPTION) VALUES (99, 'now', 'missing file')");
    StatusOperation status = new StatusOperation().operate(database.provider(), OracleSupport.standardLoader(), null, null);
    assertEquals(3, status.getAppliedCount());
    assertEquals(1, status.getPendingCount());
    assertEquals(1, status.getMissingCount());
    assertEquals(5, status.getCurrentStatus().size());
  }

  /**
   * Verifies: MIG-VIEW-002, MIG-STATE-001
   * Depends-On: changeNaturalOrderUsesAscendingNumericId
   * Seam: status union -> numeric ordered public projection
   */
  @Test
  void statusReturnsCombinedChangesInNumericOrder() throws Exception {
    Database database = fullyUpgradedDatabase();
    database.execute("INSERT INTO CHANGELOG(ID, APPLIED_AT, DESCRIPTION) VALUES (99, 'now', 'missing file')");
    StatusOperation status = new StatusOperation().operate(database.provider(), OracleSupport.standardLoader(), null, null);
    assertEquals(List.of(new BigDecimal("1"), new BigDecimal("2"), new BigDecimal("3"), new BigDecimal("4"), new BigDecimal("99")),
        status.getCurrentStatus().stream().map(Change::getId).collect(Collectors.toList()));
  }

  /**
   * Verifies: MIG-STATE-003
   * Depends-On: changeCopyConstructorCopiesEveryPublicValue
   * Seam: status read projection -> unchanged repository and changelog sources
   */
  @Test
  void statusProjectionDoesNotMutateRepositoryOrChangelog() throws Exception {
    Database database = fullyUpgradedDatabase();
    MemoryLoader loader = OracleSupport.standardLoader();
    List<BigDecimal> beforeLoader = loader.getMigrations().stream().map(Change::getId).collect(Collectors.toList());
    List<BigDecimal> beforeDatabase = database.ids("CHANGELOG");
    new StatusOperation().operate(database.provider(), loader, null, null);
    assertEquals(beforeLoader, loader.getMigrations().stream().map(Change::getId).collect(Collectors.toList()));
    assertEquals(beforeDatabase, database.ids("CHANGELOG"));
  }

  /**
   * Verifies: MIG-LIFE-016
   * Depends-On: databaseOptionDefaultsChangelogAndDelimiter
   * Seam: special bootstrap reader -> JDBC schema effect without changelog mutation
   */
  @Test
  void bootstrapBeforeChangelogExecutesBaselineWithoutTrackingRow() throws Exception {
    Database database = OracleSupport.database();
    MemoryLoader loader = new MemoryLoader().bootstrap("CREATE TABLE BASELINE(ID INT);");
    new BootstrapOperation().operate(database.provider(), loader, null, null);
    assertTrue(database.tableExists("BASELINE"));
    assertFalse(database.tableExists("CHANGELOG"));
  }

  /**
   * Verifies: MIG-LIFE-017
   * Depends-On: databaseOptionDefaultsChangelogAndDelimiter
   * Seam: existing changelog detection -> non-forced bootstrap no-op
   */
  @Test
  void bootstrapWithChangelogAndNoForceLeavesSchemaUnchanged() throws Exception {
    Database database = fullyUpgradedDatabase();
    new BootstrapOperation(false).operate(database.provider(), new MemoryLoader().bootstrap("CREATE TABLE BASELINE(ID INT);"), null, null);
    assertFalse(database.tableExists("BASELINE"));
    assertEquals(4, database.count("SELECT COUNT(*) FROM CHANGELOG"));
  }

  /**
   * Verifies: MIG-LIFE-018
   * Depends-On: databaseOptionDefaultsChangelogAndDelimiter
   * Seam: force flag plus existing changelog -> bootstrap SQL execution
   */
  @Test
  void forcedBootstrapExecutesEvenWhenChangelogExists() throws Exception {
    Database database = fullyUpgradedDatabase();
    new BootstrapOperation(true).operate(database.provider(), new MemoryLoader().bootstrap("CREATE TABLE FORCED_BASELINE(ID INT);"), null, null);
    assertTrue(database.tableExists("FORCED_BASELINE"));
    assertEquals(4, database.count("SELECT COUNT(*) FROM CHANGELOG"));
  }

  /**
   * Verifies: MIG-LIFE-019
   * Depends-On: databaseOptionDefaultsChangelogAndDelimiter
   * Seam: absent special reader -> operation output projection without SQL
   */
  @Test
  void bootstrapWithoutScriptReportsAndDoesNotApplySql() throws Exception {
    Database database = OracleSupport.database();
    ByteArrayOutputStream bytes = new ByteArrayOutputStream();
    new BootstrapOperation().operate(database.provider(), new MemoryLoader(), null, new PrintStream(bytes));
    assertFalse(bytes.toString(StandardCharsets.UTF_8).isBlank());
    assertFalse(database.tableExists("CHANGELOG"));
  }

  /**
   * Verifies: MIG-HOOK-003, MIG-HOOK-007, MIG-HOOK-008, MIG-HOOK-016, MIG-HOOK-017, MIG-HOOK-018, MIG-INV-006, MIG-JAVA-016, MIG-JAVA-017
   * Depends-On: migrationHookContextBindingUsesPublicKey, changeCopyConstructorCopiesEveryPublicValue
   * Seam: up selection -> operation and per-change callbacks -> public hook contexts
   */
  @Test
  void upInvokesHooksInDocumentedOrderWithSelectedChanges() {
    Database database = OracleSupport.database();
    RecordingHook hook = new RecordingHook();
    new UpOperation(2).operate(database.provider(), OracleSupport.standardLoader(), null, null, hook);
    assertEquals(List.of("before:null", "beforeEach:1", "afterEach:1", "beforeEach:2", "afterEach:2", "after:null"), hook.events);
  }

  /**
   * Verifies: MIG-HOOK-003, MIG-HOOK-007, MIG-HOOK-008, MIG-HOOK-016, MIG-HOOK-017, MIG-HOOK-018, MIG-INV-006, MIG-JAVA-016, MIG-JAVA-017
   * Depends-On: migrationHookContextBindingUsesPublicKey, changeCopyConstructorCopiesEveryPublicValue
   * Seam: down selection -> operation and per-change callbacks -> public hook contexts
   */
  @Test
  void downInvokesHooksInDocumentedOrderWithSelectedChanges() throws Exception {
    Database database = fullyUpgradedDatabase();
    RecordingHook hook = new RecordingHook();
    new DownOperation(2).operate(database.provider(), OracleSupport.standardLoader(), null, null, hook);
    assertEquals(List.of("before:null", "beforeEach:4", "afterEach:4", "beforeEach:3", "afterEach:3", "after:null"), hook.events);
  }

  /**
   * Verifies: MIG-LIFE-005, MIG-JAVA-013, MIG-JAVA-018
   * Depends-On: databaseOptionDefaultsTransactionMode
   * Seam: forward SQL failure -> on-abort reader -> typed exception with cause
   */
  @Test
  void failedUpExecutesOnAbortScriptAndRetainsCause() throws Exception {
    Database database = OracleSupport.database();
    MemoryLoader loader = new MemoryLoader()
        .migration("1", "log", changelogSql("CHANGELOG"), "DROP TABLE CHANGELOG;")
        .migration("2", "bad", "THIS IS NOT SQL;", "SELECT 1;")
        .onAbort("CREATE TABLE ABORT_MARKER(ID INT);");
    Throwable failure = assertThrows(MigrationException.class,
        () -> new UpOperation().operate(database.provider(), loader, null, null));
    assertNotNull(failure.getCause());
    assertTrue(database.tableExists("ABORT_MARKER"));
  }

  /**
   * Verifies: MIG-JAVA-013, MIG-JAVA-018, MIG-ERR-009
   * Depends-On: dataSourceConnectionProviderDelegatesEachRequest
   * Seam: connection-provider failure -> lifecycle exception translation with cause
   */
  @Test
  void connectionFailureBecomesMigrationExceptionWithCause() {
    ConnectionProvider provider = () -> { throw new SQLException("unavailable"); };
    Throwable failure = assertThrows(MigrationException.class,
        () -> new UpOperation().operate(provider, OracleSupport.standardLoader(), null, null));
    assertTrue(failure.getCause() instanceof SQLException);
  }

  /**
   * Verifies: MIG-JAVA-007, MIG-JAVA-018, MIG-INV-007
   * Depends-On: databaseOptionMutatesChangelogAndDelimiter
   * Seam: custom operation option -> matching migration DDL -> custom changelog persistence
   */
  @Test
  void customChangelogOptionControlsLifecyclePersistence() throws Exception {
    Database database = OracleSupport.database();
    DatabaseOperationOption option = new DatabaseOperationOption();
    option.setChangelogTable("MIG_LOG");
    MemoryLoader loader = new MemoryLoader().migration("1", "custom log", changelogSql("MIG_LOG"), "DROP TABLE MIG_LOG;");
    new UpOperation().operate(database.provider(), loader, option, null);
    assertEquals(List.of(new BigDecimal("1")), database.ids("MIG_LOG"));
    assertFalse(database.tableExists("CHANGELOG"));
  }

  /**
   * Verifies: MIG-JAVA-007, MIG-JAVA-018, MIG-INV-007
   * Depends-On: databaseOptionMutatesAutoCommit
   * Seam: auto-commit option -> script execution -> durable schema and changelog
   */
  @Test
  void autoCommitOptionStillPersistsSuccessfulLifecycle() throws Exception {
    Database database = OracleSupport.database();
    DatabaseOperationOption option = new DatabaseOperationOption();
    option.setAutoCommit(true);
    new UpOperation(2).operate(database.provider(), OracleSupport.standardLoader(), option, null);
    assertTrue(database.tableExists("WIDGETS"));
    assertEquals(2, database.count("SELECT COUNT(*) FROM CHANGELOG"));
  }

  private static Database fullyUpgradedDatabase() {
    Database database = OracleSupport.database();
    new UpOperation().operate(database.provider(), OracleSupport.standardLoader(), null, null);
    return database;
  }

  private static String changelogSql(String table) {
    return "CREATE TABLE " + table + " (ID DECIMAL(20,0) NOT NULL PRIMARY KEY, APPLIED_AT VARCHAR(100) NOT NULL, DESCRIPTION VARCHAR(255) NOT NULL);";
  }

  static class RecordingHook implements MigrationHook {
    final List<String> events = new ArrayList<>();

    @Override public void before(Map<String, Object> bindings) { events.add("before:" + id(bindings)); }
    @Override public void beforeEach(Map<String, Object> bindings) { events.add("beforeEach:" + id(bindings)); }
    @Override public void afterEach(Map<String, Object> bindings) { events.add("afterEach:" + id(bindings)); }
    @Override public void after(Map<String, Object> bindings) { events.add("after:" + id(bindings)); }

    static HookContext context(Map<String, Object> bindings) {
      String key = contextKey();
      assertTrue(bindings.containsKey(key));
      return (HookContext) bindings.get(key);
    }

    private static String contextKey() {
      try {
        return (String) MigrationHook.class.getField("HOOK_CONTEXT").get(null);
      } catch (ReflectiveOperationException failure) {
        throw new AssertionError(failure);
      }
    }

    private static String id(Map<String, Object> bindings) {
      Change change = context(bindings).getChange();
      return change == null ? "null" : change.getId().toPlainString();
    }
  }
}
