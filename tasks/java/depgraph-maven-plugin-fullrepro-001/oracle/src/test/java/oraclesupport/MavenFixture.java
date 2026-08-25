package oraclesupport;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;

/** Shared black-box Maven fixture support for the Java oracle. */
public final class MavenFixture {
  private static final String COORDINATE =
      "com.github.ferstl:depgraph-maven-plugin:LATEST:";
  private static final ObjectMapper JSON = new ObjectMapper();

  private MavenFixture() {
  }

  public static final class RunResult {
    public final Path root;
    public final int exitCode;
    public final String output;

    private RunResult(Path root, int exitCode, String output) {
      this.root = root;
      this.exitCode = exitCode;
      this.output = output;
    }

    public Path file(String relative) {
      return root.resolve(relative.replace('/', java.io.File.separatorChar));
    }

    public boolean exists(String relative) {
      return Files.isRegularFile(file(relative));
    }

    public String text(String relative) throws IOException {
      return new String(Files.readAllBytes(file(relative)), StandardCharsets.UTF_8);
    }

    public JsonNode json(String relative) throws IOException {
      return JSON.readTree(file(relative).toFile());
    }
  }

  public static RunResult project(String goal, String... properties) throws Exception {
    return dependencyProject(goal, properties);
  }

  public static RunResult builtInExample(String... properties) throws Exception {
    return projectWithFiles("example", Collections.emptyMap(), properties);
  }

  public static RunResult dependencyProject(String goal, String... properties) throws Exception {
    Path root = Files.createTempDirectory("dgm-oracle-dependency-project-");
    write(root.resolve("pom.xml"), dependencyPom());
    return invoke(root, goal, properties);
  }

  public static RunResult dependencyProjectWithFiles(
      String goal, Map<String, String> files, String... properties) throws Exception {
    Path root = Files.createTempDirectory("dgm-oracle-dependency-project-");
    write(root.resolve("pom.xml"), dependencyPom());
    for (Map.Entry<String, String> entry : files.entrySet()) {
      write(root.resolve(entry.getKey()), entry.getValue());
    }
    return invoke(root, goal, properties);
  }

  public static RunResult projectWithFiles(
      String goal, Map<String, String> files, String... properties) throws Exception {
    Path root = Files.createTempDirectory("dgm-oracle-project-");
    write(root.resolve("pom.xml"), singlePom());
    for (Map.Entry<String, String> entry : files.entrySet()) {
      write(root.resolve(entry.getKey()), entry.getValue());
    }
    return invoke(root, goal, properties);
  }

  public static RunResult noProject(String goal, String... properties) throws Exception {
    Path root = Files.createTempDirectory("dgm-oracle-noproject-");
    return invoke(root, goal, properties);
  }

  public static RunResult reactor(String goal, String... properties) throws Exception {
    Path root = Files.createTempDirectory("dgm-oracle-reactor-");
    write(root.resolve("pom.xml"), reactorRootPom());
    write(root.resolve("cobalt-core/pom.xml"), modulePom("dev.spec2repo.cobalt", "cobalt-core", ""));
    write(root.resolve("mint-service/pom.xml"), modulePom(
        "dev.spec2repo.mint", "mint-service",
        dependency("dev.spec2repo.cobalt", "cobalt-core")));
    write(root.resolve("violet-app/pom.xml"), modulePom(
        "dev.spec2repo.violet", "violet-app",
        dependency("dev.spec2repo.cobalt", "cobalt-core")
            + dependency("dev.spec2repo.mint", "mint-service")));
    write(root.resolve("amber-runtime/pom.xml"), modulePom(
        "dev.spec2repo.amber", "amber-runtime",
        dependency("dev.spec2repo.cobalt", "cobalt-core", "runtime")));
    return invoke(root, goal, properties);
  }

  public static RunResult projectWithFakeGraphviz(String outputName) throws Exception {
    Path root = Files.createTempDirectory("dgm-oracle-image-");
    write(root.resolve("pom.xml"), dependencyPom());
    String executableName = isWindows() ? "fake-dot.cmd" : "fake-dot";
    Path executable = root.resolve(executableName);
    String script = isWindows()
        ? "@echo off\r\nsetlocal EnableDelayedExpansion\r\nset want=\r\nset out=\r\nset source=\r\n"
            + "for %%A in (%*) do (\r\n"
            + "  if defined want (set out=%%~A& set want=)\r\n"
            + "  if \"%%~A\"==\"-o\" set want=1\r\n"
            + "  if /I \"%%~xA\"==\".dot\" set source=%%~fA\r\n"
            + ")\r\nif not defined out exit /b 9\r\n"
            + "if not defined source exit /b 8\r\n"
            + "if not exist \"!source!\" exit /b 7\r\n"
            + "> \"%~dp0graphviz-source.txt\" echo !source!\r\n"
            + "> \"!out!\" echo spec2repo-fake-image\r\nexit /b 0\r\n"
        : "#!/bin/sh\nout=''\nwant=''\nsource=''\nfor arg in \"$@\"; do\n"
            + "  if [ -n \"$want\" ]; then out=\"$arg\"; want=''; fi\n"
            + "  if [ \"$arg\" = '-o' ]; then want=1; fi\n"
            + "  case \"$arg\" in *.dot) source=\"$arg\" ;; esac\n"
            + "done\n[ -n \"$out\" ] || exit 9\n[ -n \"$source\" ] || exit 8\n"
            + "[ -f \"$source\" ] || exit 7\nprintf '%s\\n' \"$source\" > \"$(dirname \"$0\")/graphviz-source.txt\"\n"
            + "printf 'spec2repo-fake-image\\n' > \"$out\"\nexit 0\n";
    write(executable, script);
    executable.toFile().setExecutable(true, false);
    return invoke(root, "graph",
        "-DgraphFormat=dot", "-DcreateImage=true", "-DimageFormat=png",
        "-DdotExecutable=" + executable.toAbsolutePath(), "-DoutputFileName=" + outputName);
  }

  public static Map<String, String> files(String name, String content) {
    Map<String, String> result = new LinkedHashMap<>();
    result.put(name, content);
    return result;
  }

  private static RunResult invoke(Path root, String goal, String... properties) throws Exception {
    String repository = System.getProperty("maven.repo.local");
    if (repository == null || repository.trim().isEmpty()) {
      repository = Paths.get(System.getProperty("user.home"), ".m2", "repository").toString();
    }
    List<String> command = new ArrayList<>();
    command.add(isWindows() ? "mvn.cmd" : "mvn");
    command.add("-B");
    command.add("-o");
    command.add("-Dmaven.repo.local=" + repository);
    command.add(COORDINATE + goal);
    for (String property : properties) {
      command.add(property.replace("@ROOT@", root.toAbsolutePath().toString()));
    }

    Process process = new ProcessBuilder(command)
        .directory(root.toFile())
        .redirectErrorStream(true)
        .start();
    ByteArrayOutputStream captured = new ByteArrayOutputStream();
    Thread reader = new Thread(() -> copy(process.getInputStream(), captured));
    reader.setDaemon(true);
    reader.start();
    if (!process.waitFor(120, TimeUnit.SECONDS)) {
      process.destroyForcibly();
      throw new IllegalStateException("Nested Maven invocation timed out: " + command);
    }
    reader.join(5000);
    return new RunResult(
        root,
        process.exitValue(),
        new String(captured.toByteArray(), StandardCharsets.UTF_8));
  }

  private static void copy(InputStream input, ByteArrayOutputStream output) {
    byte[] buffer = new byte[8192];
    int read;
    try {
      while ((read = input.read(buffer)) >= 0) {
        output.write(buffer, 0, read);
      }
    } catch (IOException ignored) {
      // The process exit status remains the observable result.
    }
  }

  private static void write(Path path, String content) throws IOException {
    Files.createDirectories(path.getParent());
    Files.write(path, content.getBytes(StandardCharsets.UTF_8));
  }

  private static boolean isWindows() {
    return System.getProperty("os.name", "").toLowerCase().contains("win");
  }

  private static String singlePom() {
    return "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        + "<project xmlns=\"http://maven.apache.org/POM/4.0.0\">\n"
        + "  <modelVersion>4.0.0</modelVersion>\n"
        + "  <groupId>dev.spec2repo.aurora</groupId>\n"
        + "  <artifactId>amber-lattice</artifactId>\n"
        + "  <version>1.0.0</version>\n"
        + "</project>\n";
  }

  private static String dependencyPom() {
    return "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        + "<project xmlns=\"http://maven.apache.org/POM/4.0.0\">\n"
        + "  <modelVersion>4.0.0</modelVersion>\n"
        + "  <groupId>dev.spec2repo.aurora</groupId>\n"
        + "  <artifactId>amber-lattice</artifactId>\n"
        + "  <version>1.0.0</version>\n"
        + "  <dependencies>\n"
        + "    <dependency><groupId>org.junit.jupiter</groupId><artifactId>junit-jupiter-api</artifactId>"
        + "<version>5.9.1</version><optional>true</optional></dependency>\n"
        + "    <dependency><groupId>org.junit.jupiter</groupId><artifactId>junit-jupiter-engine</artifactId>"
        + "<version>5.9.1</version><scope>test</scope></dependency>\n"
        + "    <dependency><groupId>com.fasterxml.jackson.core</groupId><artifactId>jackson-databind</artifactId>"
        + "<version>2.14.1</version><scope>runtime</scope></dependency>\n"
        + "    <dependency><groupId>org.junit.platform</groupId><artifactId>junit-platform-commons</artifactId>"
        + "<version>1.3.2</version></dependency>\n"
        + "  </dependencies>\n"
        + "</project>\n";
  }

  private static String reactorRootPom() {
    return "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        + "<project xmlns=\"http://maven.apache.org/POM/4.0.0\">\n"
        + "  <modelVersion>4.0.0</modelVersion>\n"
        + "  <groupId>dev.spec2repo.reactor</groupId>\n"
        + "  <artifactId>prism-parent</artifactId>\n"
        + "  <version>7.3.1</version>\n"
        + "  <packaging>pom</packaging>\n"
        + "  <modules><module>cobalt-core</module><module>mint-service</module>"
        + "<module>violet-app</module><module>amber-runtime</module></modules>\n"
        + "</project>\n";
  }

  private static String modulePom(String group, String artifact, String dependencies) {
    return "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        + "<project xmlns=\"http://maven.apache.org/POM/4.0.0\">\n"
        + "  <modelVersion>4.0.0</modelVersion>\n"
        + "  <parent><groupId>dev.spec2repo.reactor</groupId><artifactId>prism-parent</artifactId>"
        + "<version>7.3.1</version><relativePath>../pom.xml</relativePath></parent>\n"
        + "  <groupId>" + group + "</groupId>\n"
        + "  <artifactId>" + artifact + "</artifactId>\n"
        + "  <packaging>jar</packaging>\n"
        + (dependencies.isEmpty() ? "" : "  <dependencies>" + dependencies + "</dependencies>\n")
        + "</project>\n";
  }

  private static String dependency(String group, String artifact) {
    return dependency(group, artifact, "compile");
  }

  private static String dependency(String group, String artifact, String scope) {
    return "<dependency><groupId>" + group + "</groupId><artifactId>" + artifact
        + "</artifactId><version>7.3.1</version><scope>" + scope + "</scope></dependency>";
  }
}
