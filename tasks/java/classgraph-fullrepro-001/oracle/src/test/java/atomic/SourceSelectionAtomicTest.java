package atomic;

import io.github.classgraph.ClassGraph;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;

class SourceSelectionAtomicTest {
    /**
     * Verifies: CG-SRC-001.
     */
    @Test
    void configurationMethodsReturnTheSameBuilder() {
        ClassGraph graph = new ClassGraph();
        assertSame(graph, graph.acceptPackages("support"));
    }

    /**
     * Verifies: CG-SRC-003.
     */
    @Test
    void repeatedClasspathSourcesPreserveCallOrder(@TempDir final Path temp) throws Exception {
        Path first = Files.createDirectory(temp.resolve("first"));
        Path second = Files.createDirectory(temp.resolve("second"));
        ClassGraph graph = new ClassGraph()
                .enableClasspathEntries(first.toFile())
                .enableClasspathEntries(second.toFile());
        assertEquals(List.of(first.toFile(), second.toFile()), graph.getClasspathFiles());
    }

    /**
     * Verifies: CG-SRC-002.
     */
    @Test
    void emptyBuilderHasNoEnvironmentClasspath() {
        ClassGraph graph = new ClassGraph();
        assertEquals("", graph.getClasspath());
        assertEquals(List.of(), graph.getClasspathFiles());
    }

    /**
     * Verifies: CG-SRC-021, CG-ENV-001.
     */
    @Test
    void artifactVersionMatchesCandidateCoordinate() {
        assertEquals("5.0.0-SNAPSHOT", new ClassGraph().getVersion());
    }

    /**
     * Verifies: CG-SRC-006, CG-ERR-001.
     */
    @Test
    void emptyClasspathEntryListIsRejected() {
        assertThrows(IllegalArgumentException.class, () -> new ClassGraph().enableClasspathEntries());
    }

    /**
     * Verifies: CG-SRC-012, CG-ERR-002.
     */
    @Test
    void nonRecursivePackageWildcardIsRejected() {
        assertThrows(IllegalArgumentException.class,
                () -> new ClassGraph().acceptPackagesNonRecursive("support.*"));
    }

    /**
     * Verifies: CG-SRC-012, CG-ERR-002.
     */
    @Test
    void nonRecursivePathWildcardIsRejected() {
        assertThrows(IllegalArgumentException.class,
                () -> new ClassGraph().acceptPathsNonRecursive("templates/*"));
    }

    /**
     * Verifies: CG-SRC-012, CG-ERR-002.
     */
    @Test
    void jarSelectorWithDirectoryIsRejected() {
        assertThrows(IllegalArgumentException.class, () -> new ClassGraph().acceptJars("lib/demo.jar"));
    }

    /**
     * Verifies: CG-SRC-012, CG-ERR-002.
     */
    @Test
    void rootPackageRejectionIsRejected() {
        assertThrows(IllegalArgumentException.class, () -> new ClassGraph().rejectPackages(""));
    }

    /**
     * Verifies: CG-SRC-012, CG-ERR-002.
     */
    @Test
    void rootPathRejectionIsRejected() {
        assertThrows(IllegalArgumentException.class, () -> new ClassGraph().rejectPaths(""));
    }

    /**
     * Verifies: CG-SRC-013.
     */
    @Test
    void enableClassInfoReturnsSameBuilder() {
        ClassGraph graph = new ClassGraph();
        assertSame(graph, graph.enableClassInfo());
    }

    /**
     * Verifies: CG-SRC-013.
     */
    @Test
    void enableMethodInfoReturnsSameBuilder() {
        ClassGraph graph = new ClassGraph();
        assertSame(graph, graph.enableMethodInfo());
    }

    /**
     * Verifies: CG-SRC-013.
     */
    @Test
    void enableFieldInfoReturnsSameBuilder() {
        ClassGraph graph = new ClassGraph();
        assertSame(graph, graph.enableFieldInfo());
    }

    /**
     * Verifies: CG-SRC-013.
     */
    @Test
    void enableAnnotationInfoReturnsSameBuilder() {
        ClassGraph graph = new ClassGraph();
        assertSame(graph, graph.enableAnnotationInfo());
    }

    /**
     * Verifies: CG-SRC-013.
     */
    @Test
    void enableStaticFinalValuesReturnsSameBuilder() {
        ClassGraph graph = new ClassGraph();
        assertSame(graph, graph.enableStaticFinalFieldConstantInitializerValues());
    }

    /**
     * Verifies: CG-SRC-013.
     */
    @Test
    void enableInterClassDependenciesReturnsSameBuilder() {
        ClassGraph graph = new ClassGraph();
        assertSame(graph, graph.enableInterClassDependencies());
    }

    /**
     * Verifies: CG-SRC-014.
     */
    @Test
    void enableAllInfoReturnsSameBuilder() {
        ClassGraph graph = new ClassGraph();
        assertSame(graph, graph.enableAllInfo());
    }

    /**
     * Verifies: CG-SRC-015.
     */
    @Test
    void ignoreClassVisibilityReturnsSameBuilder() {
        ClassGraph graph = new ClassGraph();
        assertSame(graph, graph.ignoreClassVisibility());
    }

    /**
     * Verifies: CG-SRC-015.
     */
    @Test
    void ignoreMethodVisibilityReturnsSameBuilder() {
        ClassGraph graph = new ClassGraph();
        assertSame(graph, graph.ignoreMethodVisibility());
    }

    /**
     * Verifies: CG-SRC-015.
     */
    @Test
    void ignoreFieldVisibilityReturnsSameBuilder() {
        ClassGraph graph = new ClassGraph();
        assertSame(graph, graph.ignoreFieldVisibility());
    }

    /**
     * Verifies: CG-SRC-016.
     */
    @Test
    void enableExternalClassesReturnsSameBuilder() {
        ClassGraph graph = new ClassGraph();
        assertSame(graph, graph.enableExternalClasses());
    }

    /**
     * Verifies: CG-SRC-017.
     */
    @Test
    void disableRuntimeInvisibleAnnotationsReturnsSameBuilder() {
        ClassGraph graph = new ClassGraph();
        assertSame(graph, graph.disableRuntimeInvisibleAnnotations());
    }

    /**
     * Verifies: CG-SRC-018.
     */
    @Test
    void enableMultiReleaseVersionsReturnsSameBuilder() {
        ClassGraph graph = new ClassGraph();
        assertSame(graph, graph.enableMultiReleaseVersions());
    }

    /**
     * Verifies: CG-SRC-011.
     */
    @Test
    void disableJarScanningReturnsSameBuilder() {
        ClassGraph graph = new ClassGraph();
        assertSame(graph, graph.disableJarScanning());
    }

    /**
     * Verifies: CG-SRC-011.
     */
    @Test
    void disableNestedJarScanningReturnsSameBuilder() {
        ClassGraph graph = new ClassGraph();
        assertSame(graph, graph.disableNestedJarScanning());
    }

    /**
     * Verifies: CG-SRC-011.
     */
    @Test
    void disableDirectoryScanningReturnsSameBuilder() {
        ClassGraph graph = new ClassGraph();
        assertSame(graph, graph.disableDirScanning());
    }

    /**
     * Verifies: CG-SRC-003.
     */
    @Test
    void enableClasspathReturnsSameBuilder() {
        ClassGraph graph = new ClassGraph();
        assertSame(graph, graph.enableClasspath());
    }

    /**
     * Verifies: CG-SRC-003.
     */
    @Test
    void enableClasspathEntriesReturnsSameBuilder(@TempDir final Path temp) throws Exception {
        Path classes = Files.createDirectory(temp.resolve("classes"));
        ClassGraph graph = new ClassGraph();
        assertSame(graph, graph.enableClasspathEntries(classes.toFile()));
    }

    /**
     * Verifies: CG-SRC-007.
     */
    @Test
    void acceptPathsReturnsSameBuilder() {
        ClassGraph graph = new ClassGraph();
        assertSame(graph, graph.acceptPaths("templates"));
    }

    /**
     * Verifies: CG-SRC-008.
     */
    @Test
    void acceptClassesReturnsSameBuilder() {
        ClassGraph graph = new ClassGraph();
        assertSame(graph, graph.acceptClasses("support.FixtureTypes"));
    }

    /**
     * Verifies: CG-SRC-008.
     */
    @Test
    void acceptJarsReturnsSameBuilder() {
        ClassGraph graph = new ClassGraph();
        assertSame(graph, graph.acceptJars("fixture-*.jar"));
    }

    /**
     * Verifies: CG-SRC-008.
     */
    @Test
    void acceptModulesReturnsSameBuilder() {
        ClassGraph graph = new ClassGraph();
        assertSame(graph, graph.acceptModules("fixture.module"));
    }

    /**
     * Verifies: CG-SRC-008, CG-SRC-009.
     */
    @Test
    void rejectClassesReturnsSameBuilder() {
        ClassGraph graph = new ClassGraph();
        assertSame(graph, graph.rejectClasses("support.Unwanted"));
    }

    /**
     * Verifies: CG-SRC-008, CG-SRC-009.
     */
    @Test
    void rejectJarsReturnsSameBuilder() {
        ClassGraph graph = new ClassGraph();
        assertSame(graph, graph.rejectJars("unwanted-*.jar"));
    }

    /**
     * Verifies: CG-SRC-022.
     */
    @Test
    void removeTemporaryFilesReturnsSameBuilder() {
        ClassGraph graph = new ClassGraph();
        assertSame(graph, graph.removeTemporaryFilesAfterScan());
    }

    /**
     * Verifies: CG-SRC-022.
     */
    @Test
    void setMaxBufferedJarRamReturnsSameBuilder() {
        ClassGraph graph = new ClassGraph();
        assertSame(graph, graph.setMaxBufferedJarRAMSize(4096));
    }

    /**
     * Verifies: CG-SRC-022.
     */
    @Test
    void setWorkerTimeoutReturnsSameBuilder() {
        ClassGraph graph = new ClassGraph();
        assertSame(graph, graph.setWorkerTimeout(Duration.ofSeconds(17)));
    }
}
