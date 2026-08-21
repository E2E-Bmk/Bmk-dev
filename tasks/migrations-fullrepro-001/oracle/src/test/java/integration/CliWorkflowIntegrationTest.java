package integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.File;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Properties;
import java.util.stream.Collectors;
import org.apache.ibatis.migration.FileMigrationLoader;
import org.apache.ibatis.migration.JdbcConnectionProvider;
import org.apache.ibatis.migration.Migrator;
import org.apache.ibatis.migration.operations.StatusOperation;
import org.apache.ibatis.migration.operations.UpOperation;
import org.apache.ibatis.migration.options.DatabaseOperationOption;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class CliWorkflowIntegrationTest {

  @TempDir
  Path temporaryDirectory;

  /**
   * Verifies: MIG-CONF-001
   * Depends-On: environmentUsesDocumentedDefaults
   * Seam: CLI repository selection -> initialization templates -> filesystem layout
   */
  @Test
  void cliInitCreatesDocumentedRepositoryLayout() throws Exception {
    Path repository = temporaryDirectory.resolve("initialized");
    CommandResult result = run(repository, "init");
    assertEquals(0, result.exitCode);
    assertTrue(Files.isDirectory(repository.resolve("drivers")));
    assertTrue(Files.isDirectory(repository.resolve("environments")));
    assertTrue(Files.isDirectory(repository.resolve("scripts")));
    assertTrue(Files.exists(repository.resolve("environments/development.properties")));
    assertTrue(Files.exists(repository.resolve("scripts/bootstrap.sql")));
  }

  /**
   * Verifies: MIG-LOAD-008, MIG-LOAD-010
   * Depends-On: fileLoaderReturnsForwardSection, fileLoaderReturnsReverseSection
   * Seam: initialized repository -> CLI new command -> loader-readable two-direction script
   */
  @Test
  void cliNewCreatesLoaderReadableForwardAndReverseSections() throws Exception {
    Path repository = temporaryDirectory.resolve("new-command");
    assertEquals(0, run(repository, "init").exitCode);
    long before = Files.list(repository.resolve("scripts")).filter(path -> path.toString().endsWith(".sql")).count();
    CommandResult result = run(repository, "new", "create billing ledger");
    assertEquals(0, result.exitCode);
    List<Path> scripts = Files.list(repository.resolve("scripts"))
        .filter(path -> path.getFileName().toString().contains("create_billing_ledger"))
        .collect(Collectors.toList());
    assertEquals(1, scripts.size());
    assertEquals(before + 1, Files.list(repository.resolve("scripts")).filter(path -> path.toString().endsWith(".sql")).count());
    assertTrue(Files.readString(scripts.get(0)).contains("-- //@UNDO"));
  }

  /**
   * Verifies: MIG-INV-001, MIG-INV-004, MIG-JAVA-018, MIG-LOAD-001, MIG-LOAD-020
   * Depends-On: fileLoaderSortsAndFiltersMigrationFiles, databaseOptionDefaultsChangelogAndDelimiter
   * Seam: identical repository scripts -> CLI and runtime application -> equal schema and changelog identity
   */
  @Test
  void cliAndRuntimeUpProduceEquivalentSchemaAndChangelog() throws Exception {
    Repository cli = repository("cli-up", "CHANGELOG");
    Repository runtime = repository("runtime-up", "CHANGELOG");
    assertEquals(0, run(cli.root, "up").exitCode);
    new UpOperation().operate(runtime.provider(), runtime.loader(), null, null);
    assertEquals(ids(cli.url, "CHANGELOG"), ids(runtime.url, "CHANGELOG"));
    assertEquals(count(cli.url, "SELECT COUNT(*) FROM WIDGETS"), count(runtime.url, "SELECT COUNT(*) FROM WIDGETS"));
  }

  /**
   * Verifies: MIG-INV-001, MIG-LIFE-002, MIG-JAVA-018, MIG-LOAD-001, MIG-LOAD-020
   * Depends-On: changeNaturalOrderUsesAscendingNumericId
   * Seam: shared step boundary -> CLI and runtime selection -> equal partial state
   */
  @Test
  void cliAndRuntimeStepLimitedUpSelectSamePrefix() throws Exception {
    Repository cli = repository("cli-step", "CHANGELOG");
    Repository runtime = repository("runtime-step", "CHANGELOG");
    assertEquals(0, run(cli.root, "up", "2").exitCode);
    new UpOperation(2).operate(runtime.provider(), runtime.loader(), null, null);
    assertEquals(ids(cli.url, "CHANGELOG"), ids(runtime.url, "CHANGELOG"));
    assertEquals(List.of(new BigDecimal("1"), new BigDecimal("2")), ids(cli.url, "CHANGELOG"));
  }

  /**
   * Verifies: MIG-INV-002, MIG-VIEW-002, MIG-VIEW-004, MIG-LOAD-001, MIG-LOAD-020
   * Depends-On: changeEqualityUsesOnlyNumericId
   * Seam: CLI-applied database -> runtime status and CLI status -> matching applied projection
   */
  @Test
  void cliAndRuntimeStatusAgreeAfterUp() throws Exception {
    Repository repository = repository("status", "CHANGELOG");
    assertEquals(0, run(repository.root, "up").exitCode);
    StatusOperation status = new StatusOperation().operate(repository.provider(), repository.loader(), null, null);
    CommandResult output = run(repository.root, "status");
    assertEquals(0, output.exitCode);
    assertEquals(3, status.getAppliedCount());
    assertEquals(0, status.getPendingCount());
    for (BigDecimal id : status.getCurrentStatus().stream().map(change -> change.getId()).collect(Collectors.toList())) {
      assertTrue(output.output.contains(id.toPlainString()));
    }
  }

  /**
   * Verifies: MIG-INV-002, MIG-LIFE-002, MIG-LOAD-001, MIG-LOAD-020
   * Depends-On: fileLoaderSortsAndFiltersMigrationFiles
   * Seam: partially applied CLI state -> CLI and runtime status -> matching pending projection
   */
  @Test
  void cliAndRuntimeStatusAgreeAtPartialVersion() throws Exception {
    Repository repository = repository("partial-status", "CHANGELOG");
    assertEquals(0, run(repository.root, "up", "2").exitCode);
    StatusOperation status = new StatusOperation().operate(repository.provider(), repository.loader(), null, null);
    CommandResult output = run(repository.root, "status");
    assertEquals(2, status.getAppliedCount());
    assertEquals(1, status.getPendingCount());
    assertTrue(output.output.contains("3"));
  }

  /**
   * Verifies: MIG-INV-003, MIG-LIFE-006, MIG-VIEW-006, MIG-LOAD-001, MIG-LOAD-020
   * Depends-On: fileLoaderReturnsReverseSection
   * Seam: CLI down selection -> loader undo SQL -> schema and status projection
   */
  @Test
  void cliDownUsesSameUndoSectionProjectedByLoader() throws Exception {
    Repository repository = repository("down", "CHANGELOG");
    assertEquals(0, run(repository.root, "up").exitCode);
    String undo = read(repository.loader().getScriptReader(repository.loader().getMigrations().get(2), true));
    assertTrue(undo.contains("DELETE FROM WIDGETS"));
    assertEquals(0, run(repository.root, "down").exitCode);
    assertEquals(0, count(repository.url, "SELECT COUNT(*) FROM WIDGETS"));
    assertEquals(1, new StatusOperation().operate(repository.provider(), repository.loader(), null, null).getPendingCount());
  }

  /**
   * Verifies: MIG-INV-004, MIG-VIEW-005, MIG-JAVA-018, MIG-LOAD-001, MIG-LOAD-020
   * Depends-On: fileLoaderReturnsForwardSection, changeNaturalOrderUsesAscendingNumericId
   * Seam: offline forward projection -> online runtime selection -> identical ordered migration interval
   */
  @Test
  void cliForwardScriptAndRuntimeUpSelectSameOrderedInterval() throws Exception {
    Repository repository = repository("forward-script", "CHANGELOG");
    CommandResult script = run(repository.root, "script", "0", "3");
    assertEquals(0, script.exitCode);
    int changelog = script.output.indexOf("CREATE TABLE CHANGELOG");
    int table = script.output.indexOf("CREATE TABLE WIDGETS");
    int row = script.output.indexOf("INSERT INTO WIDGETS");
    assertTrue(changelog >= 0 && changelog < table && table < row);
    new UpOperation().operate(repository.provider(), repository.loader(), null, null);
    assertEquals(List.of(new BigDecimal("1"), new BigDecimal("2"), new BigDecimal("3")), ids(repository.url, "CHANGELOG"));
  }

  /**
   * Verifies: MIG-INV-008, MIG-LIFE-008, MIG-LIFE-009
   * Depends-On: fileLoaderReturnsForwardSection, fileLoaderReturnsReverseSection
   * Seam: applied CLI tail -> redo down/up lifecycle -> preserved status and restored schema effect
   */
  @Test
  void cliRedoPreservesAppliedSetAndRecreatesTailEffect() throws Exception {
    Repository repository = repository("redo-one", "CHANGELOG");
    assertEquals(0, run(repository.root, "up").exitCode);
    List<BigDecimal> before = ids(repository.url, "CHANGELOG");
    assertEquals(0, run(repository.root, "redo").exitCode);
    assertEquals(before, ids(repository.url, "CHANGELOG"));
    assertEquals(1, count(repository.url, "SELECT COUNT(*) FROM WIDGETS"));
  }

  /**
   * Verifies: MIG-INV-008, MIG-LIFE-008, MIG-LIFE-009
   * Depends-On: changeNaturalOrderUsesAscendingNumericId
   * Seam: two-change CLI tail -> multi-step redo -> stable identities and dependent schema
   */
  @Test
  void cliRedoWithCountPreservesTwoChangeTail() throws Exception {
    Repository repository = repository("redo-two", "CHANGELOG");
    assertEquals(0, run(repository.root, "up").exitCode);
    List<BigDecimal> before = ids(repository.url, "CHANGELOG");
    assertEquals(0, run(repository.root, "redo", "2").exitCode);
    assertEquals(before, ids(repository.url, "CHANGELOG"));
    assertEquals(1, count(repository.url, "SELECT COUNT(*) FROM WIDGETS"));
  }

  /**
   * Verifies: MIG-INV-007, MIG-JAVA-007, MIG-JAVA-018, MIG-LOAD-001, MIG-LOAD-020
   * Depends-On: databaseOptionMutatesChangelogAndDelimiter
   * Seam: environment changelog setting and runtime option -> matching persistence table
   */
  @Test
  void cliEnvironmentAndRuntimeOptionSelectSameCustomChangelog() throws Exception {
    Repository cli = repository("cli-custom-log", "MIG_LOG");
    Repository runtime = repository("runtime-custom-log", "MIG_LOG");
    assertEquals(0, run(cli.root, "up").exitCode);
    DatabaseOperationOption option = new DatabaseOperationOption();
    option.setChangelogTable("MIG_LOG");
    new UpOperation().operate(runtime.provider(), runtime.loader(), option, null);
    assertEquals(ids(cli.url, "MIG_LOG"), ids(runtime.url, "MIG_LOG"));
  }

  private Repository repository(String name, String changelog) throws Exception {
    Path root = temporaryDirectory.resolve(name);
    Path scripts = root.resolve("scripts");
    Path environments = root.resolve("environments");
    Files.createDirectories(scripts);
    Files.createDirectories(environments);
    String url = "jdbc:hsqldb:file:" + temporaryDirectory.resolve(name + "-db").toAbsolutePath().toString().replace('\\', '/') + ";shutdown=true";
    String properties = "driver=org.hsqldb.jdbc.JDBCDriver\nurl=" + url + "\nusername=SA\npassword=\nchangelog=" + changelog
        + "\nauto_commit=false\ndelimiter=;\nfull_line_delimiter=false\nsend_full_script=false\nremove_crs=false\nignore_warnings=true\n";
    Files.writeString(environments.resolve("development.properties"), properties, StandardCharsets.UTF_8);
    Files.writeString(scripts.resolve("001_create_changelog.sql"), changelogSql(changelog) + "\n-- //@UNDO\nDROP TABLE " + changelog + ";\n", StandardCharsets.UTF_8);
    Files.writeString(scripts.resolve("002_create_widgets.sql"), "CREATE TABLE WIDGETS(ID DECIMAL(20,0) PRIMARY KEY);\n-- //@UNDO\nDROP TABLE WIDGETS;\n", StandardCharsets.UTF_8);
    Files.writeString(scripts.resolve("003_seed_widget.sql"), "INSERT INTO WIDGETS(ID) VALUES (31);\n-- //@UNDO\nDELETE FROM WIDGETS WHERE ID=31;\n", StandardCharsets.UTF_8);
    return new Repository(root, scripts, url);
  }

  private CommandResult run(Path repository, String... arguments) throws Exception {
    String target = new File(Migrator.class.getProtectionDomain().getCodeSource().getLocation().toURI()).getAbsolutePath();
    Class<?> driver = Class.forName("org.hsqldb.jdbc.JDBCDriver");
    String hsqldb = new File(driver.getProtectionDomain().getCodeSource().getLocation().toURI()).getAbsolutePath();
    Path java = Path.of(System.getProperty("java.home"), "bin", System.getProperty("os.name").startsWith("Windows") ? "java.exe" : "java");
    List<String> command = new ArrayList<>(List.of(java.toString(), "-cp", target + File.pathSeparator + hsqldb,
        "org.apache.ibatis.migration.Migrator"));
    command.addAll(List.of(arguments));
    command.add("--path=" + repository.toAbsolutePath());
    Process process = new ProcessBuilder(command).redirectErrorStream(true).start();
    String output = new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
    return new CommandResult(process.waitFor(), output);
  }

  private static int count(String url, String sql) throws Exception {
    try (Connection connection = DriverManager.getConnection(url, "SA", "");
         Statement statement = connection.createStatement();
         ResultSet result = statement.executeQuery(sql)) {
      result.next();
      return result.getInt(1);
    }
  }

  private static List<BigDecimal> ids(String url, String table) throws Exception {
    List<BigDecimal> result = new ArrayList<>();
    try (Connection connection = DriverManager.getConnection(url, "SA", "");
         Statement statement = connection.createStatement();
         ResultSet rows = statement.executeQuery("SELECT ID FROM " + table + " ORDER BY ID")) {
      while (rows.next()) {
        result.add(rows.getBigDecimal(1));
      }
    }
    return result;
  }

  private static String changelogSql(String table) {
    return "CREATE TABLE " + table + " (ID DECIMAL(20,0) NOT NULL PRIMARY KEY, APPLIED_AT VARCHAR(100) NOT NULL, DESCRIPTION VARCHAR(255) NOT NULL);";
  }

  private static String read(java.io.Reader reader) throws Exception {
    StringBuilder text = new StringBuilder();
    char[] buffer = new char[512];
    for (int count; (count = reader.read(buffer)) != -1;) {
      text.append(buffer, 0, count);
    }
    return text.toString();
  }

  private static final class Repository {
    final Path root;
    final Path scripts;
    final String url;

    Repository(Path root, Path scripts, String url) {
      this.root = root;
      this.scripts = scripts;
      this.url = url;
    }

    FileMigrationLoader loader() {
      return new FileMigrationLoader(scripts.toFile(), "UTF-8", new Properties());
    }

    JdbcConnectionProvider provider() {
      return new JdbcConnectionProvider("org.hsqldb.jdbc.JDBCDriver", url, "SA", "");
    }
  }

  private static final class CommandResult {
    final int exitCode;
    final String output;

    CommandResult(int exitCode, String output) {
      this.exitCode = exitCode;
      this.output = output;
    }
  }
}
