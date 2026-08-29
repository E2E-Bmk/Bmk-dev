package support;

import io.github.classgraph.ClassGraph;
import io.github.classgraph.ScanResult;

import java.io.File;
import java.net.URISyntaxException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

/** Shared local-only setup for the oracle. */
public final class OracleSupport {
    public static final String FIXTURE_PACKAGE = "support";

    private OracleSupport() {
    }

    public static File testClassesDirectory() {
        try {
            return Path.of(FixtureTypes.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toFile();
        } catch (URISyntaxException exception) {
            throw new IllegalStateException(exception);
        }
    }

    public static ClassGraph fixtureGraph() {
        return new ClassGraph()
                .enableClasspathEntries(testClassesDirectory())
                .acceptPackages(FIXTURE_PACKAGE);
    }

    public static ScanResult scanClassInfo() {
        return fixtureGraph().enableClassInfo().scan();
    }

    public static ScanResult scanAllInfo() {
        return fixtureGraph().enableAllInfo().scan();
    }

    public static Path writeResourceTree(final Path root) throws java.io.IOException {
        Files.createDirectories(root.resolve("templates/admin"));
        Files.createDirectories(root.resolve("docs"));
        Files.writeString(root.resolve("templates/page.html"), "alpha-β", StandardCharsets.UTF_8);
        Files.writeString(root.resolve("templates/admin/panel.html"), "panel-27", StandardCharsets.UTF_8);
        Files.writeString(root.resolve("docs/readme.txt"), "local-doc", StandardCharsets.UTF_8);
        Files.writeString(root.resolve("root.data"), "root-data", StandardCharsets.UTF_8);
        return root;
    }

    public static ScanResult scanResources(final Path root) {
        return new ClassGraph()
                .enableClasspathEntries(root.toFile())
                .acceptPaths("templates", "docs")
                .scan();
    }
}
