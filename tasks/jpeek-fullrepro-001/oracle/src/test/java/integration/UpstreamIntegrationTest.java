package integration;

import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.jpeek.DefaultBase;
import org.jpeek.Main;
import org.jpeek.graph.Disjoint;
import org.jpeek.graph.Graph;
import org.jpeek.graph.Node;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import support.FixtureCompiler;

/** Public-surface integration and system tests retained from upstream intents. */
final class UpstreamIntegrationTest {

    /** Verifies: JPK-GRAPH-002, JPK-GRAPH-004, JPK-GRAPH-012, JPK-GRAPH-014. Seam: state consistency. Depends-On: givesName. */
    @Test
    void calculatesDisjointSets() throws Exception {
        final Node one = new Node.Simple("one");
        final Node two = new Node.Simple("two");
        final Node three = new Node.Simple("three");
        final Node four = new Node.Simple("four");
        final Node five = new Node.Simple("five");
        final Node six = new Node.Simple("six");
        one.connections().add(two);
        two.connections().addAll(List.of(one, three));
        three.connections().add(two);
        four.connections().add(five);
        five.connections().add(four);
        final List<Set<Node>> sets = new Disjoint(
            () -> List.of(one, two, three, four, five, six)
        ).value();
        Assertions.assertEquals(3, sets.size());
        Assertions.assertTrue(sets.stream().anyMatch(set -> set.equals(Set.of(one, two, three))));
        Assertions.assertTrue(sets.stream().anyMatch(set -> set.equals(Set.of(four, five))));
        Assertions.assertTrue(sets.stream().anyMatch(set -> set.equals(Set.of(six))));
    }

    /** Verifies: JPK-GRAPH-012, JPK-GRAPH-015. Seam: state consistency. Depends-On: givesName. */
    @Test
    void calculatesDisjointSetsForUnconnected() throws Exception {
        final List<Node> nodes = List.of(
            new Node.Simple("alpha"), new Node.Simple("beta"),
            new Node.Simple("gamma"), new Node.Simple("delta")
        );
        final Graph graph = () -> nodes;
        final List<Set<Node>> sets = new Disjoint(graph).value();
        Assertions.assertEquals(4, sets.size());
        Assertions.assertTrue(sets.stream().allMatch(set -> set.size() == 1));
    }

    /** Verifies: JPK-MET-008, JPK-XML-013. Seam: protocol handoff. Depends-On: defaultBaseFindsNestedFiles, distinguishesParameterMetrics. */
    @Test
    void createsXmlReports(@TempDir final Path temp) throws IOException {
        final Path source = UpstreamIntegrationTest.simpleFixture(temp.resolve("source"));
        final Path output = temp.resolve("output");
        UpstreamIntegrationTest.invokeMain(
            "--sources", source.toString(), "--target", output.toString()
        );
        Assertions.assertTrue(Files.exists(output.resolve("LCOM5.xml")));
    }

    /** Verifies: JPK-LIFE-007, JPK-ERR-004. Seam: error propagation. Depends-On: listsFiles. */
    @Test
    void crashesIfOverwriteAndSourceEqualsToTarget(@TempDir final Path temp)
        throws IOException {
        final Path source = UpstreamIntegrationTest.simpleFixture(temp.resolve("source"));
        Assertions.assertThrows(
            IllegalArgumentException.class,
            () -> UpstreamIntegrationTest.invokeMain(
                "--sources", source.toString(), "--target", source.toString(), "--overwrite"
            )
        );
    }

    /** Verifies: JPK-MET-009, JPK-ERR-002. Seam: error propagation. Depends-On: distinguishesParameterMetrics. */
    @Test
    void crashesIfMetricsHaveInvalidNames(@TempDir final Path temp) throws IOException {
        final Path source = UpstreamIntegrationTest.simpleFixture(temp.resolve("source"));
        Assertions.assertThrows(
            IllegalArgumentException.class,
            () -> UpstreamIntegrationTest.invokeMain(
                "--sources", source.toString(), "--target", temp.resolve("output").toString(),
                "--metrics", "#%$!"
            )
        );
    }

    /** Verifies: JPK-LIFE-006, JPK-XML-013. Seam: lifecycle crossing. Depends-On: freshTargetReturnsRequestedPath. */
    @Test
    void createsXmlReportsIfOverwriteAndTargetExists(@TempDir final Path temp)
        throws IOException {
        final Path source = UpstreamIntegrationTest.simpleFixture(temp.resolve("source"));
        final Path target = Files.createDirectory(temp.resolve("target"));
        Files.writeString(target.resolve("stale.txt"), "stale");
        UpstreamIntegrationTest.invokeMain(
            "--sources", source.toString(), "--target", target.toString(), "--overwrite"
        );
        Assertions.assertTrue(Files.exists(target.resolve("LCOM5.xml")));
        Assertions.assertFalse(Files.exists(target.resolve("stale.txt")));
    }

    private static void invokeMain(final String... args) throws IOException {
        try {
            Main.class.getMethod("main", String[].class).invoke(null, (Object) args);
        } catch (final InvocationTargetException failure) {
            final Throwable cause = failure.getCause();
            if (cause instanceof IOException io) {
                throw io;
            }
            if (cause instanceof RuntimeException runtime) {
                throw runtime;
            }
            if (cause instanceof Error error) {
                throw error;
            }
            throw new IllegalStateException(cause);
        } catch (final ReflectiveOperationException failure) {
            throw new IllegalStateException(failure);
        }
    }

    private static Path simpleFixture(final Path root) throws IOException {
        return FixtureCompiler.compile(
            root,
            Map.of(
                "OracleSample.java",
                "public final class OracleSample {"
                    + " private int value; public int value(){return value;}"
                    + "}"
            )
        );
    }

}
