package atomic;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.List;
import java.util.Map;
import org.jpeek.Base;
import org.jpeek.DefaultBase;
import org.jpeek.FileTarget;
import org.jpeek.Metrics;
import org.jpeek.calculus.xsl.XslCalculus;
import org.jpeek.graph.Disjoint;
import org.jpeek.graph.Graph;
import org.jpeek.graph.Node;
import org.jpeek.skeleton.Skeleton;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;

final class AtomicOracleTest {
    @TempDir Path temp;

    private static List<Path> paths(final Iterable<Path> input) {
        final List<Path> out = new ArrayList<>();
        input.forEach(out::add);
        return out;
    }

    /** Verifies: JPK-MET-002, JPK-MET-003. */
    @Test void distinguishesParameterMetrics() {
        assertTrue(Metrics.LCOM.isIncludeParams());
        assertFalse(Metrics.NHD.isIncludeParams());
    }

    /** Verifies: JPK-MET-004. */
    @Test void exposesMmacDistribution() {
        assertEquals(0.5, Metrics.MMAC.getMean());
        assertEquals(0.1, Metrics.MMAC.getSigma());
    }

    /** Verifies: JPK-GRAPH-003. */
    @Test void simpleNodeRetainsName() {
        assertEquals("alpha", new Node.Simple("alpha").name());
    }

    /** Verifies: JPK-GRAPH-004. */
    @Test void simpleNodeRetainsConnectionMutation() {
        final Node.Simple one = new Node.Simple("one");
        final Node.Simple two = new Node.Simple("two");
        one.connections().add(two);
        assertTrue(one.connections().contains(two));
    }

    /** Verifies: JPK-GRAPH-016. */
    @Test void disjointReturnsEmptyForEmptyGraph() throws Exception {
        final Graph graph = () -> List.of();
        assertTrue(new Disjoint(graph).value().isEmpty());
    }

    /** Verifies: JPK-GRAPH-012, JPK-GRAPH-015. */
    @Test void disjointSeparatesUnconnectedNodes() throws Exception {
        final Node one = new Node.Simple("one");
        final Node two = new Node.Simple("two");
        final Graph graph = () -> Arrays.asList(one, two);
        assertEquals(2, new Disjoint(graph).value().size());
    }

    /** Verifies: JPK-INP-005. */
    @Test void concatPreservesLeftThenRightOrder() throws Exception {
        final Path one = this.temp.resolve("one.class");
        final Path two = this.temp.resolve("two.class");
        final Base left = () -> List.of(one);
        final Base right = () -> List.of(two);
        assertEquals(List.of(one, two), paths(new Base.Concat(left, right).files()));
    }

    /** Verifies: JPK-LIFE-004. */
    @Test void freshTargetReturnsRequestedPath() throws Exception {
        final Path target = this.temp.resolve("fresh");
        assertEquals(target, new FileTarget(target.toFile(), false).toPath());
    }

    /** Verifies: JPK-LIFE-005, JPK-ERR-003. */
    @Test void existingTargetIsRejectedAndPreserved() throws Exception {
        final Path target = Files.writeString(this.temp.resolve("kept.txt"), "kept");
        assertThrows(IllegalStateException.class,
            () -> new FileTarget(target.toFile(), false).toPath());
        assertEquals("kept", Files.readString(target));
    }

    /** Verifies: JPK-INP-008, JPK-XML-002. */
    @Test void emptyBaseProducesSkeletonRoot() throws Exception {
        final Base base = () -> List.of();
        final var document = (org.w3c.dom.Document) new Skeleton(base).xml().node();
        assertEquals("skeleton", document.getDocumentElement().getNodeName());
    }

    /** Verifies: JPK-MET-002. */
    @Test void lcomIncludesParameters() { assertTrue(Metrics.LCOM.isIncludeParams()); }
    /** Verifies: JPK-MET-002. */
    @Test void camcIncludesParameters() { assertTrue(Metrics.CAMC.isIncludeParams()); }
    /** Verifies: JPK-MET-002. */
    @Test void mmacIncludesParameters() { assertTrue(Metrics.MMAC.isIncludeParams()); }
    /** Verifies: JPK-MET-002. */
    @Test void lcom5IncludesParameters() { assertTrue(Metrics.LCOM5.isIncludeParams()); }
    /** Verifies: JPK-MET-002. */
    @Test void lcom4IncludesParameters() { assertTrue(Metrics.LCOM4.isIncludeParams()); }
    /** Verifies: JPK-MET-002. */
    @Test void lcom2IncludesParameters() { assertTrue(Metrics.LCOM2.isIncludeParams()); }
    /** Verifies: JPK-MET-002. */
    @Test void lcom3IncludesParameters() { assertTrue(Metrics.LCOM3.isIncludeParams()); }
    /** Verifies: JPK-MET-002. */
    @Test void scomIncludesParameters() { assertTrue(Metrics.SCOM.isIncludeParams()); }
    /** Verifies: JPK-MET-002. */
    @Test void occIncludesParameters() { assertTrue(Metrics.OCC.isIncludeParams()); }

    /** Verifies: JPK-MET-005. */
    @Test void exposesLcom5Distribution() {
        assertEquals(0.5, Metrics.LCOM5.getMean());
        assertEquals(-0.1, Metrics.LCOM5.getSigma());
    }

    /** Verifies: JPK-MET-005. */
    @Test void exposesLcom4Distribution() {
        assertEquals(0.5, Metrics.LCOM4.getMean());
        assertEquals(-0.1, Metrics.LCOM4.getSigma());
    }

    /** Verifies: JPK-GRAPH-004. */
    @Test void connectionCanBeRemoved() {
        final Node.Simple one = new Node.Simple("one");
        final Node.Simple two = new Node.Simple("two");
        one.connections().add(two);
        one.connections().remove(two);
        assertTrue(one.connections().isEmpty());
    }

    /** Verifies: JPK-GRAPH-004. */
    @Test void connectionSetCanBeCleared() {
        final Node.Simple one = new Node.Simple("one");
        one.connections().add(new Node.Simple("two"));
        one.connections().add(new Node.Simple("three"));
        one.connections().clear();
        assertEquals(0, one.connections().size());
    }

    /** Verifies: JPK-GRAPH-002, JPK-GRAPH-004. */
    @Test void nodesKeepIndependentConnectionSets() {
        final Node.Simple one = new Node.Simple("one");
        final Node.Simple two = new Node.Simple("two");
        one.connections().add(two);
        assertAll(() -> assertEquals(1, one.connections().size()),
            () -> assertTrue(two.connections().isEmpty()));
    }

    /** Verifies: JPK-GRAPH-012, JPK-GRAPH-014. */
    @Test void disjointJoinsDirectNeighbors() throws Exception {
        final Node.Simple one = new Node.Simple("one");
        final Node.Simple two = new Node.Simple("two");
        one.connections().add(two);
        two.connections().add(one);
        final Graph graph = () -> List.of(one, two);
        assertEquals(1, new Disjoint(graph).value().size());
    }

    /** Verifies: JPK-GRAPH-012, JPK-GRAPH-014. */
    @Test void disjointJoinsTransitiveNeighbors() throws Exception {
        final Node.Simple one = new Node.Simple("one");
        final Node.Simple two = new Node.Simple("two");
        final Node.Simple three = new Node.Simple("three");
        one.connections().add(two);
        two.connections().add(one);
        two.connections().add(three);
        three.connections().add(two);
        final Graph graph = () -> List.of(one, two, three);
        assertEquals(3, new Disjoint(graph).value().get(0).size());
    }

    /** Verifies: JPK-GRAPH-013, JPK-GRAPH-015. */
    @Test void disjointPartitionCoversEveryNodeOnce() throws Exception {
        final Node.Simple one = new Node.Simple("one");
        final Node.Simple two = new Node.Simple("two");
        final Node.Simple three = new Node.Simple("three");
        one.connections().add(two);
        two.connections().add(one);
        final Graph graph = () -> List.of(one, two, three);
        final Collection<? extends Collection<Node>> groups = new Disjoint(graph).value();
        assertEquals(3, groups.stream().mapToInt(Collection::size).sum());
    }

    /** Verifies: JPK-GRAPH-012. */
    @Test void disjointReturnsSingletonForOneNode() throws Exception {
        final Node one = new Node.Simple("one");
        final Graph graph = () -> List.of(one);
        assertEquals(java.util.Set.of(one), new Disjoint(graph).value().get(0));
    }

    /** Verifies: JPK-INP-005. */
    @Test void concatAcceptsEmptyLeftBase() throws Exception {
        final Path only = this.temp.resolve("only.class");
        assertEquals(List.of(only), paths(new Base.Concat(() -> List.of(), () -> List.of(only)).files()));
    }

    /** Verifies: JPK-INP-005. */
    @Test void concatAcceptsEmptyRightBase() throws Exception {
        final Path only = this.temp.resolve("only.class");
        assertEquals(List.of(only), paths(new Base.Concat(() -> List.of(only), () -> List.of()).files()));
    }

    /** Verifies: JPK-INP-006. */
    @Test void concatPropagatesLeftFailure() {
        final Base broken = () -> { throw new IOException("injected"); };
        assertThrows(IOException.class, () -> new Base.Concat(broken, () -> List.of()).files());
    }

    /** Verifies: JPK-INP-006. */
    @Test void concatPropagatesRightFailure() {
        final Base broken = () -> { throw new IOException("injected"); };
        assertThrows(IOException.class, () -> new Base.Concat(() -> List.of(), broken).files());
    }

    /** Verifies: JPK-INP-002. */
    @Test void defaultBaseFindsNestedFiles() throws Exception {
        final Path nested = Files.createDirectories(this.temp.resolve("a/b"));
        final Path file = Files.write(nested.resolve("Thing.class"), new byte[]{1});
        assertTrue(paths(new DefaultBase(this.temp).files()).contains(file));
    }

    /** Verifies: JPK-INP-002. */
    @Test void defaultBaseIncludesRootFile() throws Exception {
        final Path file = Files.write(this.temp.resolve("Root.class"), new byte[]{1});
        assertTrue(paths(new DefaultBase(this.temp).files()).contains(file));
    }

    /** Verifies: JPK-INP-002. */
    @Test void defaultBaseEnumeratesMultiplePaths() throws Exception {
        final Path one = Files.write(this.temp.resolve("one.class"), new byte[]{1});
        final Path two = Files.write(this.temp.resolve("two.class"), new byte[]{2});
        final List<Path> found = paths(new DefaultBase(this.temp).files());
        assertAll(() -> assertTrue(found.contains(one)), () -> assertTrue(found.contains(two)));
    }

    /** Verifies: JPK-LIFE-006. */
    @Test void overwriteRemovesExistingFile() throws Exception {
        final Path file = Files.writeString(this.temp.resolve("old"), "data");
        assertEquals(file, new FileTarget(file.toFile(), true).toPath());
        assertFalse(Files.exists(file));
    }

    /** Verifies: JPK-LIFE-006. */
    @Test void overwriteRemovesNestedDirectory() throws Exception {
        final Path dir = Files.createDirectories(this.temp.resolve("old/a/b"));
        Files.writeString(dir.resolve("data"), "data");
        final Path root = this.temp.resolve("old");
        assertEquals(root, new FileTarget(root.toFile(), true).toPath());
        assertFalse(Files.exists(root));
    }

    /** Verifies: JPK-XML-002, JPK-INP-008. */
    @Test void emptySkeletonHasNoClassElements() throws Exception {
        final Base base = () -> List.of();
        final var document = (org.w3c.dom.Document) new Skeleton(base).xml().node();
        assertEquals(0, document.getElementsByTagName("class").getLength());
    }

    /** Verifies: JPK-INP-003, JPK-ERR-005. */
    @Test void missingInputTreeRaisesIoFailure() {
        final Path missing = this.temp.resolve("does-not-exist");
        assertThrows(IOException.class, () -> new DefaultBase(missing).files());
    }

    /** Verifies: JPK-CALC-004, JPK-ERR-007. */
    @Test void missingTransformationFailsWithoutFallback() throws Exception {
        final Skeleton skeleton = new Skeleton(() -> List.of());
        assertThrows(Exception.class,
            () -> new XslCalculus().node("NO_SUCH_METRIC", Map.of(), skeleton.xml()));
    }
}
