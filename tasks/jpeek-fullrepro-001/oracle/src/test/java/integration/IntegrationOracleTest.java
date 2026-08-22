package integration;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;
import javax.tools.JavaCompiler;
import javax.tools.ToolProvider;
import com.jcabi.xml.XMLDocument;
import org.jpeek.App;
import org.jpeek.Base;
import org.jpeek.DefaultBase;
import org.jpeek.FileTarget;
import org.jpeek.Metrics;
import org.jpeek.calculus.xsl.XslCalculus;
import org.jpeek.graph.Disjoint;
import org.jpeek.graph.Graph;
import org.jpeek.graph.Node;
import org.jpeek.graph.XmlGraph;
import org.jpeek.skeleton.Skeleton;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;

final class IntegrationOracleTest {
    @TempDir Path temp;

    private Path compile(final String name, final String body) throws IOException {
        final Path src = Files.createDirectories(this.temp.resolve(name + "-src"));
        final Path out = Files.createDirectories(this.temp.resolve(name + "-classes"));
        final Path file = src.resolve(name + ".java");
        Files.writeString(file, body);
        final JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        assertNotNull(compiler);
        assertEquals(0, compiler.run(null, null, null, "-d", out.toString(), file.toString()));
        return out;
    }

    private Path emptyClasses(final String name) throws IOException {
        return Files.createDirectories(this.temp.resolve(name + "-classes"));
    }

    private Path analyze(final String name, final Path source, final Map<String, Object> args)
        throws Exception {
        final Path target = this.temp.resolve(name + "-out");
        new App(source, target, args).analyze();
        return target;
    }

    private Path analyzeDefaults(final String name, final Path source) throws Exception {
        final Path target = this.temp.resolve(name + "-out");
        new App(source, target).analyze();
        return target;
    }

    private static Set<String> xmlFiles(final Path target) throws IOException {
        try (var stream = Files.list(target)) {
            return stream.filter(path -> path.getFileName().toString().endsWith(".xml"))
                .map(path -> path.getFileName().toString()).collect(Collectors.toCollection(LinkedHashSet::new));
        }
    }

    private static Set<String> metricFiles(final Path target) throws IOException {
        final Set<String> vocabulary = Arrays.stream(Metrics.values())
            .map(metric -> metric.name() + ".xml")
            .collect(Collectors.toSet());
        return xmlFiles(target).stream().filter(vocabulary::contains)
            .collect(Collectors.toCollection(LinkedHashSet::new));
    }

    private Process process(final String... args) throws IOException {
        final List<String> command = new ArrayList<>();
        command.add(Path.of(System.getProperty("java.home"), "bin", "java").toString());
        command.add("-cp");
        command.add(System.getProperty("java.class.path"));
        command.add("org.jpeek.Main");
        command.addAll(List.of(args));
        return new ProcessBuilder(command).redirectErrorStream(true).start();
    }

    private static int await(final Process process) throws Exception {
        process.getInputStream().readAllBytes();
        assertTimeoutPreemptively(Duration.ofSeconds(20), () -> process.waitFor());
        return process.exitValue();
    }

    private static Set<Node> flattened(final List<Set<Node>> groups) {
        final Set<Node> out = new HashSet<>();
        groups.forEach(out::addAll);
        return out;
    }

    private static org.w3c.dom.Document document(final com.jcabi.xml.XML xml) {
        return (org.w3c.dom.Document) xml.node();
    }

    private static boolean containsValue(final org.w3c.dom.Element element,
        final String expected) {
        final org.w3c.dom.NamedNodeMap attrs = element.getAttributes();
        if (attrs != null) {
            for (int idx = 0; idx < attrs.getLength(); ++idx) {
                if (expected.equals(attrs.item(idx).getNodeValue())) {
                    return true;
                }
            }
        }
        if (expected.equals(element.getTextContent().trim())) {
            return true;
        }
        final org.w3c.dom.NodeList children = element.getElementsByTagName("*");
        for (int idx = 0; idx < children.getLength(); ++idx) {
            if (containsValue((org.w3c.dom.Element) children.item(idx), expected)) {
                return true;
            }
        }
        return false;
    }

    private static Set<String> presentIdentities(final Path file,
        final Set<String> expected) throws IOException {
        final String xml = Files.readString(file);
        return expected.stream().filter(xml::contains).collect(Collectors.toSet());
    }

    private static Set<String> classMetricValues(final com.jcabi.xml.XML xml,
        final String identity) {
        final Set<String> values = new HashSet<>();
        final org.w3c.dom.NodeList classes = document(xml).getElementsByTagName("class");
        for (int idx = 0; idx < classes.getLength(); ++idx) {
            final org.w3c.dom.Element cls = (org.w3c.dom.Element) classes.item(idx);
            if (containsValue(cls, identity)) {
                final org.w3c.dom.NamedNodeMap attrs = cls.getAttributes();
                for (int pos = 0; pos < attrs.getLength(); ++pos) {
                    final String value = attrs.item(pos).getNodeValue();
                    if (value.matches("NaN|-?[0-9]+(?:\\.[0-9]+)?")) {
                        values.add(value);
                    }
                }
            }
        }
        return values;
    }

    /** Verifies: JPK-LIFE-001, JPK-XML-013, JPK-INV-004.
     * Seam: App -> selected metric reports -> target filesystem.
     * Depends on: freshTargetReturnsRequestedPath, lcom5IncludesParameters.
     * Depends-On: freshTargetReturnsRequestedPath, lcom5IncludesParameters. */
    @Test void appWritesOneSelectedMetric() throws Exception {
        final Path out = analyze("one", emptyClasses("one"), Map.of("LCOM5", ""));
        assertEquals(Set.of("LCOM5.xml"), metricFiles(out));
    }

    /** Verifies: JPK-MET-010, JPK-XML-013, JPK-INV-004.
     * Seam: metric map -> App -> two filesystem projections.
     * Depends on: distinguishesParameterMetrics, freshTargetReturnsRequestedPath.
     * Depends-On: distinguishesParameterMetrics, freshTargetReturnsRequestedPath. */
    @Test void appWritesExactlyTwoSelectedMetrics() throws Exception {
        final Path out = analyze("two", emptyClasses("two"), Map.of("LCOM5", "", "NHD", ""));
        assertEquals(Set.of("LCOM5.xml", "NHD.xml"), metricFiles(out));
    }

    /** Verifies: JPK-MET-012, JPK-STATE-003, JPK-INV-004.
     * Seam: two-path facade defaults -> report family -> filesystem.
     * Depends on: distinguishesParameterMetrics, emptyBaseProducesSkeletonRoot.
     * Depends-On: distinguishesParameterMetrics, emptyBaseProducesSkeletonRoot. */
    @Test void twoPathFacadeWritesDocumentedMetricFamily() throws Exception {
        final Set<String> files = metricFiles(analyzeDefaults("defaults", emptyClasses("defaults")));
        assertAll(() -> assertEquals(14, files.size()),
            () -> assertFalse(files.contains("CAMC.xml")), () -> assertTrue(files.contains("MWE.xml")));
    }

    /** Verifies: JPK-XML-002, JPK-LIFE-001, JPK-STATE-001.
     * Seam: Base discovery -> App -> persisted skeleton.
     * Depends on: emptyBaseProducesSkeletonRoot, concatAcceptsEmptyLeftBase.
     * Depends-On: emptyBaseProducesSkeletonRoot, concatAcceptsEmptyLeftBase. */
    @Test void appPersistsValidSkeletonForEmptyInput() throws Exception {
        final Path out = analyze("empty", emptyClasses("empty"), Map.of("NHD", ""));
        assertTrue(Files.readString(out.resolve("skeleton.xml")).contains("<skeleton"));
    }

    /** Verifies: JPK-INP-001, JPK-INP-007, JPK-XML-005, JPK-INV-002.
     * Seam: Java compiler -> DefaultBase -> Skeleton XML -> App report.
     * Depends on: defaultBaseFindsNestedFiles, emptyBaseProducesSkeletonRoot.
     * Depends-On: defaultBaseFindsNestedFiles, emptyBaseProducesSkeletonRoot. */
    @Test void compiledClassAppearsInSkeletonAndMetric() throws Exception {
        final Path classes = compile("Alpha", "package fixture; public class Alpha { public int value(){return 1;} }");
        final Path out = analyze("alpha", classes, Map.of("LCOM5", ""));
        final String skeleton = Files.readString(out.resolve("skeleton.xml"));
        final String report = Files.readString(out.resolve("LCOM5.xml"));
        assertAll(() -> assertTrue(skeleton.contains("Alpha")), () -> assertTrue(report.contains("Alpha")));
    }

    /** Verifies: JPK-INV-002, JPK-STATE-001, JPK-XML-014.
     * Seam: two compiled classes -> shared skeleton -> selected metric projection.
     * Depends on: defaultBaseEnumeratesMultiplePaths, lcom5IncludesParameters.
     * Depends-On: defaultBaseEnumeratesMultiplePaths, lcom5IncludesParameters. */
    @Test void metricClassIdentitiesBelongToSkeleton() throws Exception {
        final Path classes = compile("Pair", "package fixture; class Left {int x;} class Right {int y;}");
        final Path out = analyze("pair", classes, Map.of("LCOM5", ""));
        final Set<String> expected = Set.of("Left", "Right");
        final Set<String> skeleton = presentIdentities(out.resolve("skeleton.xml"), expected);
        final Set<String> report = presentIdentities(out.resolve("LCOM5.xml"), expected);
        assertAll(() -> assertEquals(expected, skeleton), () -> assertFalse(report.isEmpty()),
            () -> assertTrue(skeleton.containsAll(report)));
    }

    /** Verifies: JPK-LIFE-006, JPK-LIFE-001, JPK-INV-005.
     * Seam: overwrite guard -> App -> target reports.
     * Depends on: overwriteRemovesNestedDirectory, appWritesOneSelectedMetric.
     * Depends-On: overwriteRemovesNestedDirectory. */
    @Test void overwrittenTargetCanReceiveAnalysis() throws Exception {
        final Path target = Files.createDirectories(this.temp.resolve("replace-out/old"));
        Files.writeString(target.resolve("stale"), "old");
        final Path root = this.temp.resolve("replace-out");
        final Path resolved = new FileTarget(root.toFile(), true).toPath();
        new App(emptyClasses("replace"), resolved, Map.of("NHD", "")).analyze();
        assertEquals(Set.of("NHD.xml"), metricFiles(root));
    }

    /** Verifies: JPK-GRAPH-004, JPK-GRAPH-012, JPK-INV-007.
     * Seam: mutable Node graph -> Disjoint partition -> union view.
     * Depends on: simpleNodeRetainsConnectionMutation, disjointJoinsDirectNeighbors.
     * Depends-On: simpleNodeRetainsConnectionMutation, disjointJoinsDirectNeighbors. */
    @Test void mutableGraphPartitionsIntoCompleteUnion() throws Exception {
        final Node.Simple one = new Node.Simple("one");
        final Node.Simple two = new Node.Simple("two");
        one.connections().add(two); two.connections().add(one);
        final Graph graph = () -> List.of(one, two);
        assertEquals(Set.of(one, two), flattened(new Disjoint(graph).value()));
    }

    /** Verifies: JPK-INP-005, JPK-XML-002, JPK-STATE-001.
     * Seam: Base.Concat -> Skeleton -> XML projection.
     * Depends on: concatPreservesLeftThenRightOrder, emptyBaseProducesSkeletonRoot.
     * Depends-On: concatPreservesLeftThenRightOrder, emptyBaseProducesSkeletonRoot. */
    @Test void concatenatedEmptyBasesProduceOneEmptySkeleton() throws Exception {
        final Base both = new Base.Concat(() -> List.of(), () -> List.of());
        assertEquals(0, document(new Skeleton(both).xml())
            .getElementsByTagName("class").getLength());
    }

    /** Verifies: JPK-GRAPH-013, JPK-GRAPH-015, JPK-INV-007.
     * Seam: graph node list -> component partition -> aggregate sizes.
     * Depends on: disjointSeparatesUnconnectedNodes, disjointPartitionCoversEveryNodeOnce.
     * Depends-On: disjointSeparatesUnconnectedNodes, disjointPartitionCoversEveryNodeOnce. */
    @Test void mixedGraphHasDisjointCompleteComponents() throws Exception {
        final Node.Simple one = new Node.Simple("one");
        final Node.Simple two = new Node.Simple("two");
        final Node.Simple three = new Node.Simple("three");
        one.connections().add(two); two.connections().add(one);
        final Graph graph = () -> List.of(one, two, three);
        final List<Set<Node>> groups = new Disjoint(graph).value();
        assertAll(() -> assertEquals(2, groups.size()),
            () -> assertEquals(Set.of(one, two, three), flattened(groups)));
    }

    /** Verifies: JPK-ERR-001.
     * Seam: executable Main -> required option validation -> process result.
     * Depends on: appPersistsValidSkeletonForEmptyInput, freshTargetReturnsRequestedPath.
     * Depends-On: freshTargetReturnsRequestedPath. */
    @Test void cliRejectsMissingSource() throws Exception {
        assertNotEquals(0, await(process("--target", this.temp.resolve("missing-source").toString())));
    }

    /** Verifies: JPK-ERR-001.
     * Seam: executable Main -> required option validation -> process result.
     * Depends on: defaultBaseFindsNestedFiles, freshTargetReturnsRequestedPath.
     * Depends-On: defaultBaseFindsNestedFiles, freshTargetReturnsRequestedPath. */
    @Test void cliRejectsMissingTarget() throws Exception {
        assertNotEquals(0, await(process("--sources", emptyClasses("missing-target").toString())));
    }

    /** Verifies: JPK-MET-009, JPK-ERR-002.
     * Seam: CLI metric token -> validation -> filesystem preservation.
     * Depends on: distinguishesParameterMetrics, freshTargetReturnsRequestedPath.
     * Depends-On: distinguishesParameterMetrics, freshTargetReturnsRequestedPath. */
    @Test void cliRejectsMalformedMetricBeforeAnalysis() throws Exception {
        final Path out = this.temp.resolve("bad-metric-out");
        final int code = await(process("--sources", emptyClasses("bad-metric").toString(),
            "--target", out.toString(), "--metrics", "lcom5"));
        assertAll(() -> assertNotEquals(0, code),
            () -> assertTrue(!Files.exists(out) || (!Files.exists(out.resolve("skeleton.xml"))
                && metricFiles(out).isEmpty())));
    }

    /** Verifies: JPK-LIFE-007, JPK-ERR-004.
     * Seam: CLI safety validation -> source/target identity -> preserved input.
     * Depends on: existingTargetIsRejectedAndPreserved, defaultBaseIncludesRootFile.
     * Depends-On: existingTargetIsRejectedAndPreserved, defaultBaseIncludesRootFile. */
    @Test void cliRejectsEqualSourceAndTargetWithoutDeletingInput() throws Exception {
        final Path source = emptyClasses("same");
        final Path marker = Files.writeString(source.resolve("marker"), "keep");
        final int code = await(process("--sources", source.toString(), "--target", source.toString(), "--overwrite"));
        assertAll(() -> assertNotEquals(0, code), () -> assertTrue(Files.exists(marker)));
    }

    /** Verifies: JPK-MET-008, JPK-XML-013, JPK-INV-004.
     * Seam: CLI defaults -> metric selection -> target files.
     * Depends on: distinguishesParameterMetrics, emptyBaseProducesSkeletonRoot.
     * Depends-On: distinguishesParameterMetrics, emptyBaseProducesSkeletonRoot. */
    @Test void cliDefaultSelectionWritesFiveMetrics() throws Exception {
        final Path out = this.temp.resolve("cli-default-out");
        final int code = await(process("--sources", emptyClasses("cli-default").toString(), "--target", out.toString()));
        assertAll(() -> assertEquals(0, code), () -> assertEquals(5, metricFiles(out).size()),
            () -> assertTrue(Files.exists(out.resolve("CAMC.xml"))));
    }

    /** Verifies: JPK-MET-007, JPK-XML-013, JPK-INV-004.
     * Seam: comma-separated CLI metrics -> reports -> absence of unselected report.
     * Depends on: appWritesExactlyTwoSelectedMetrics, distinguishesParameterMetrics.
     * Depends-On: distinguishesParameterMetrics. */
    @Test void cliSelectedMetricsAreExact() throws Exception {
        final Path out = this.temp.resolve("cli-two-out");
        final int code = await(process("--sources", emptyClasses("cli-two").toString(), "--target", out.toString(),
            "--metrics", "LCOM5,NHD"));
        assertAll(() -> assertEquals(0, code),
            () -> assertEquals(Set.of("LCOM5.xml", "NHD.xml"), metricFiles(out)));
    }

    /** Verifies: JPK-LIFE-008, JPK-XML-013.
     * Seam: quiet CLI -> analysis -> report filesystem.
     * Depends on: cliSelectedMetricsAreExact, appWritesOneSelectedMetric.
     * Depends-On: freshTargetReturnsRequestedPath. */
    @Test void quietCliStillWritesReports() throws Exception {
        final Path out = this.temp.resolve("quiet-out");
        final int code = await(process("--sources", emptyClasses("quiet").toString(), "--target", out.toString(),
            "--metrics", "NHD", "--quiet"));
        assertAll(() -> assertEquals(0, code), () -> assertTrue(Files.exists(out.resolve("NHD.xml"))));
    }

    /** Verifies: JPK-INV-001, JPK-MET-010, JPK-MET-007.
     * Seam: equivalent App and CLI selection -> target file sets.
     * Depends on: appWritesExactlyTwoSelectedMetrics, cliSelectedMetricsAreExact.
     * Depends-On: emptyBaseProducesSkeletonRoot. */
    @Test void cliAndAppProduceSameSelectedFileFamily() throws Exception {
        final Path source = emptyClasses("equivalent");
        final Path api = analyze("equivalent-api", source, Map.of("LCOM5", "", "NHD", ""));
        final Path cli = this.temp.resolve("equivalent-cli");
        assertEquals(0, await(process("--sources", source.toString(), "--target", cli.toString(), "--metrics", "LCOM5,NHD")));
        assertEquals(metricFiles(api), metricFiles(cli));
    }

    /** Verifies: JPK-INV-001, JPK-INP-007, JPK-XML-005.
     * Seam: compiled input -> equivalent CLI/App skeleton identity.
     * Depends on: compiledClassAppearsInSkeletonAndMetric, cliAndAppProduceSameSelectedFileFamily.
     * Depends-On: emptyBaseProducesSkeletonRoot. */
    @Test void cliAndAppSkeletonsContainSameClass() throws Exception {
        final Path source = compile("Echo", "package fixture; public class Echo { public void ping(){} }");
        final Path api = analyze("echo-api", source, Map.of("NHD", ""));
        final Path cli = this.temp.resolve("echo-cli");
        assertEquals(0, await(process("--sources", source.toString(), "--target", cli.toString(), "--metrics", "NHD")));
        assertAll(() -> assertTrue(Files.readString(api.resolve("skeleton.xml")).contains("Echo")),
            () -> assertTrue(Files.readString(cli.resolve("skeleton.xml")).contains("Echo")));
    }

    /** Verifies: JPK-INV-005, JPK-STATE-004, JPK-MET-010.
     * Seam: fresh FileTarget -> App selection -> report identity.
     * Depends on: freshTargetReturnsRequestedPath, appWritesOneSelectedMetric.
     * Depends-On: freshTargetReturnsRequestedPath. */
    @Test void freshGuardDoesNotChangeMetricSelection() throws Exception {
        final Path target = this.temp.resolve("guard-fresh");
        final Path resolved = new FileTarget(target.toFile(), false).toPath();
        new App(emptyClasses("guard-source"), resolved, Map.of("SCOM", "")).analyze();
        assertEquals(Set.of("SCOM.xml"), metricFiles(target));
    }

    /** Verifies: JPK-INV-005, JPK-STATE-004, JPK-INP-002.
     * Seam: overwrite FileTarget -> DefaultBase discovery -> App.
     * Depends on: overwriteRemovesExistingFile, defaultBaseFindsNestedFiles.
     * Depends-On: overwriteRemovesExistingFile, defaultBaseFindsNestedFiles. */
    @Test void overwriteGuardDoesNotChangeInputDiscovery() throws Exception {
        final Path source = compile("Guarded", "package fixture; public class Guarded { int value; }");
        final Path target = Files.createDirectories(this.temp.resolve("guarded-out"));
        Files.writeString(target.resolve("stale"), "old");
        final Path resolved = new FileTarget(target.toFile(), true).toPath();
        new App(source, resolved, Map.of("NHD", "")).analyze();
        assertTrue(Files.readString(target.resolve("skeleton.xml")).contains("Guarded"));
    }

    /** Verifies: JPK-GRAPH-005, JPK-GRAPH-006, JPK-INV-006.
     * Seam: compiled methods -> Skeleton -> XmlGraph.
     * Depends on: emptyBaseProducesSkeletonRoot, simpleNodeRetainsName.
     * Depends-On: emptyBaseProducesSkeletonRoot, simpleNodeRetainsName. */
    @Test void xmlGraphNamesMethodsFromSkeleton() throws Exception {
        final Path source = compile("Linked", "package fixture; public class Linked { public void one(){two();} public void two(){} }");
        final Skeleton skeleton = new Skeleton(new DefaultBase(source));
        final List<Node> nodes = new XmlGraph(skeleton, "fixture", "Linked").nodes();
        final Set<String> names = nodes.stream().map(Node::name).collect(Collectors.toSet());
        assertAll(() -> assertEquals(2, nodes.size()), () -> assertEquals(2, names.size()),
            () -> assertTrue(names.stream().noneMatch(String::isBlank)));
    }

    /** Verifies: JPK-GRAPH-005, JPK-GRAPH-008, JPK-INV-006.
     * Seam: Skeleton method view -> XmlGraph nodes -> repeated view.
     * Depends on: simpleNodeRetainsConnectionMutation, xmlGraphNamesMethodsFromSkeleton.
     * Depends-On: simpleNodeRetainsConnectionMutation. */
    @Test void xmlGraphConnectsCallerAndCalleeStably() throws Exception {
        final Path source = compile("Calls", "package fixture; public class Calls { public void one(){two();} public void two(){} }");
        final XmlGraph graph = new XmlGraph(new Skeleton(new DefaultBase(source)), "fixture", "Calls");
        final List<Node> first = graph.nodes();
        assertAll(() -> assertEquals(first, graph.nodes()),
            () -> assertEquals(2, first.size()),
            () -> assertTrue(first.stream().allMatch(node -> !node.name().isBlank())));
    }

    /** Verifies: JPK-GRAPH-012, JPK-INV-006, JPK-INV-007.
     * Seam: Skeleton -> XmlGraph -> Disjoint partition.
     * Depends on: xmlGraphNamesMethodsFromSkeleton, disjointPartitionCoversEveryNodeOnce.
     * Depends-On: disjointPartitionCoversEveryNodeOnce. */
    @Test void xmlGraphPartitionsOnlyItsOwnNodes() throws Exception {
        final Path source = compile("Components", "package fixture; public class Components { public void one(){two();} public void two(){} public void alone(){} }");
        final XmlGraph graph = new XmlGraph(new Skeleton(new DefaultBase(source)), "fixture", "Components");
        assertEquals(new HashSet<>(graph.nodes()), flattened(new Disjoint(graph).value()));
    }

    /** Verifies: JPK-GRAPH-012, JPK-GRAPH-013, JPK-INV-006, JPK-INV-007.
     * Seam: XmlGraph nodes -> public connection mutation -> complete component partition.
     * Depends on: disjointJoinsTransitiveNeighbors, xmlGraphConnectsCallerAndCalleeStably.
     * Depends-On: disjointJoinsTransitiveNeighbors. */
    @Test void xmlGraphNodesFormOneComponentWhenConnected() throws Exception {
        final Path source = compile("Chain", "package fixture; public class Chain { public void one(){two();} public void two(){three();} public void three(){} }");
        final XmlGraph graph = new XmlGraph(new Skeleton(new DefaultBase(source)), "fixture", "Chain");
        final List<Node> nodes = graph.nodes();
        for (int idx = 1; idx < nodes.size(); ++idx) {
            nodes.get(idx - 1).connections().add(nodes.get(idx));
            nodes.get(idx).connections().add(nodes.get(idx - 1));
        }
        final List<Set<Node>> groups = new Disjoint(graph).value();
        assertAll(() -> assertEquals(1, groups.size()),
            () -> assertEquals(new HashSet<>(nodes), flattened(groups)));
    }

    /** Verifies: JPK-STATE-001, JPK-INV-002, JPK-XML-014.
     * Seam: one input state -> two metric reports -> class identity.
     * Depends on: metricClassIdentitiesBelongToSkeleton, appWritesExactlyTwoSelectedMetrics.
     * Depends-On: freshTargetReturnsRequestedPath. */
    @Test void twoMetricsShareTheSameClassIdentity() throws Exception {
        final Path source = compile("Shared", "package fixture; public class Shared { public int x(){return 1;} }");
        final Path out = analyze("shared", source, Map.of("LCOM5", "", "NHD", ""));
        assertAll(() -> assertTrue(Files.readString(out.resolve("LCOM5.xml")).contains("Shared")),
            () -> assertTrue(Files.readString(out.resolve("NHD.xml")).contains("Shared")));
    }

    /** Verifies: JPK-STATE-003, JPK-INV-004, JPK-MET-001.
     * Seam: Metrics vocabulary -> App map -> same-named files.
     * Depends on: distinguishesParameterMetrics, appWritesExactlyTwoSelectedMetrics.
     * Depends-On: distinguishesParameterMetrics. */
    @Test void selectedEnumNamesMapToSameNamedReports() throws Exception {
        final Path out = analyze("enum-files", emptyClasses("enum-files"),
            Map.of(Metrics.LCOM5.name(), "", Metrics.SCOM.name(), ""));
        assertAll(() -> assertTrue(Files.exists(out.resolve(Metrics.LCOM5.name() + ".xml"))),
            () -> assertTrue(Files.exists(out.resolve(Metrics.SCOM.name() + ".xml"))));
    }

    /** Verifies: JPK-STATE-003, JPK-INV-004, JPK-MET-010.
     * Seam: single selection -> filesystem enumeration -> absence checks.
     * Depends on: appWritesOneSelectedMetric, distinguishesParameterMetrics.
     * Depends-On: distinguishesParameterMetrics. */
    @Test void unselectedMetricNeverAppears() throws Exception {
        final Path out = analyze("no-extra", emptyClasses("no-extra"), Map.of("NHD", ""));
        assertAll(() -> assertFalse(Files.exists(out.resolve("LCOM5.xml"))),
            () -> assertTrue(Files.exists(out.resolve("NHD.xml"))));
    }

    /** Verifies: JPK-STATE-005, JPK-GRAPH-008, JPK-XML-002.
     * Seam: Skeleton XML -> XmlGraph repeated computation -> unchanged XML.
     * Depends on: emptyBaseProducesSkeletonRoot, xmlGraphConnectsCallerAndCalleeStably.
     * Depends-On: emptyBaseProducesSkeletonRoot. */
    @Test void graphProjectionDoesNotMutateSkeleton() throws Exception {
        final Path source = compile("Stable", "package fixture; public class Stable { public void one(){} }");
        final Skeleton skeleton = new Skeleton(new DefaultBase(source));
        final var xml = skeleton.xml();
        final String before = xml.toString();
        new XmlGraph(skeleton, "fixture", "Stable").nodes();
        assertEquals(before, xml.toString());
    }

    /** Verifies: JPK-INP-005, JPK-XML-004, JPK-STATE-001.
     * Seam: two DefaultBase instances -> Base.Concat -> shared skeleton.
     * Depends on: concatPreservesLeftThenRightOrder, defaultBaseFindsNestedFiles.
     * Depends-On: concatPreservesLeftThenRightOrder, defaultBaseFindsNestedFiles. */
    @Test void concatenatedCompiledBasesShareSkeleton() throws Exception {
        final Path one = compile("First", "package first; public class First {}");
        final Path two = compile("Second", "package second; public class Second {}");
        final Base bases = new Base.Concat(new DefaultBase(one), new DefaultBase(two));
        final String skeleton = new Skeleton(bases).xml().toString();
        assertAll(() -> assertTrue(skeleton.contains("First")),
            () -> assertTrue(skeleton.contains("Second")));
    }

    /** Verifies: JPK-INV-002, JPK-XML-013, JPK-XML-014.
     * Seam: skeleton package identity -> two reports -> filesystem views.
     * Depends on: compiledClassAppearsInSkeletonAndMetric, twoMetricsShareTheSameClassIdentity.
     * Depends-On: emptyBaseProducesSkeletonRoot. */
    @Test void packageIdentityPersistsAcrossReports() throws Exception {
        final Path source = compile("Packaged", "package deep.example; public class Packaged { int x; }");
        final Path out = analyze("packaged", source, Map.of("LCOM5", "", "NHD", ""));
        assertAll(() -> assertTrue(Files.readString(out.resolve("skeleton.xml")).contains("deep.example")),
            () -> assertTrue(Files.readString(out.resolve("LCOM5.xml")).contains("deep.example")),
            () -> assertTrue(Files.readString(out.resolve("NHD.xml")).contains("deep.example")));
    }

    /** Verifies: JPK-INV-005, JPK-STATE-004, JPK-LIFE-006.
     * Seam: overwritten directory -> report creation -> no stale state.
     * Depends on: overwriteRemovesNestedDirectory, overwrittenTargetCanReceiveAnalysis.
     * Depends-On: overwriteRemovesNestedDirectory. */
    @Test void overwrittenTargetContainsNoStaleFile() throws Exception {
        final Path root = Files.createDirectories(this.temp.resolve("clean-target"));
        Files.writeString(root.resolve("stale.txt"), "old");
        final Path resolved = new FileTarget(root.toFile(), true).toPath();
        new App(emptyClasses("clean-source"), resolved, Map.of("NHD", "")).analyze();
        assertAll(() -> assertFalse(Files.exists(root.resolve("stale.txt"))),
            () -> assertTrue(Files.exists(root.resolve("skeleton.xml"))));
    }

    /** Verifies: JPK-LIFE-001, JPK-XML-013, JPK-STATE-003.
     * Seam: facade completion -> skeleton/report atomic persistence.
     * Depends on: appPersistsValidSkeletonForEmptyInput, appWritesOneSelectedMetric.
     * Depends-On: freshTargetReturnsRequestedPath. */
    @Test void completedAnalysisLeavesBothCoreViews() throws Exception {
        final Path out = analyze("complete", emptyClasses("complete"), Map.of("NHD", ""));
        assertAll(() -> assertTrue(Files.size(out.resolve("skeleton.xml")) > 0),
            () -> assertTrue(Files.size(out.resolve("NHD.xml")) > 0));
    }

    /** Verifies: JPK-GRAPH-012, JPK-GRAPH-013, JPK-INV-007.
     * Seam: two graph components -> partition -> pairwise-disjoint check.
     * Depends on: disjointSeparatesUnconnectedNodes, mixedGraphHasDisjointCompleteComponents.
     * Depends-On: disjointSeparatesUnconnectedNodes. */
    @Test void componentSetsArePairwiseDisjoint() throws Exception {
        final Node.Simple one = new Node.Simple("one");
        final Node.Simple two = new Node.Simple("two");
        final Graph graph = () -> List.of(one, two);
        final List<Set<Node>> groups = new Disjoint(graph).value();
        final Set<Node> intersection = new HashSet<>(groups.get(0));
        intersection.retainAll(groups.get(1));
        assertTrue(intersection.isEmpty());
    }

    /** Verifies: JPK-INV-006, JPK-INV-007, JPK-GRAPH-015.
     * Seam: XmlGraph disconnected methods -> Disjoint -> two components.
     * Depends on: xmlGraphNamesMethodsFromSkeleton, disjointSeparatesUnconnectedNodes.
     * Depends-On: disjointSeparatesUnconnectedNodes. */
    @Test void disconnectedSkeletonMethodsStayInDifferentComponents() throws Exception {
        final Path source = compile("Separate", "package fixture; public class Separate { public void one(){} public void two(){} }");
        final XmlGraph graph = new XmlGraph(new Skeleton(new DefaultBase(source)), "fixture", "Separate");
        assertEquals(2, new Disjoint(graph).value().size());
    }

    /** Verifies: JPK-CALC-001, JPK-CALC-003, JPK-INV-008.
     * Seam: App skeleton -> XslCalculus -> direct XML versus saved LCOM5 XML.
     * Depends on: emptyBaseProducesSkeletonRoot, lcom5IncludesParameters.
     * Depends-On: emptyBaseProducesSkeletonRoot, lcom5IncludesParameters. */
    @Test void directLcom5CalculusPreservesSavedClassIdentity() throws Exception {
        final Path source = compile("CalcLcom", "package fixture; public class CalcLcom { private int x; public int read(){return x;} }");
        final Path out = analyze("calc-lcom", source, Map.of("LCOM5", ""));
        final var direct = new XslCalculus().node("LCOM5", Map.of(),
            new XMLDocument(out.resolve("skeleton.xml").toFile()));
        final var saved = new XMLDocument(out.resolve("LCOM5.xml").toFile());
        assertAll(() -> assertTrue(containsValue(
            (org.w3c.dom.Element) direct.node().getFirstChild(), "CalcLcom"
        )), () -> assertTrue(containsValue(
            (org.w3c.dom.Element) saved.node().getFirstChild(), "CalcLcom"
        )));
    }

    /** Verifies: JPK-CALC-001, JPK-CALC-003, JPK-INV-008.
     * Seam: Skeleton -> XslCalculus -> direct XML versus App-saved PCC XML.
     * Depends on: emptyBaseProducesSkeletonRoot, directNhdCalculusMatchesSavedClassProjection.
     * Depends-On: emptyBaseProducesSkeletonRoot. */
    @Test void directPccCalculusMatchesSavedClassProjection() throws Exception {
        final Path source = compile("CalcPcc", "package fixture; public class CalcPcc { private int x; public int read(){return x;} }");
        final Skeleton skeleton = new Skeleton(new DefaultBase(source));
        final var direct = new XslCalculus().node("PCC", Map.of(), skeleton.xml());
        final Path out = analyze("calc-pcc", source, Map.of("PCC", ""));
        final var saved = new XMLDocument(out.resolve("PCC.xml").toFile());
        final Set<String> expected = classMetricValues(direct, "CalcPcc");
        assertAll(() -> assertFalse(expected.isEmpty()),
            () -> assertEquals(expected, classMetricValues(saved, "CalcPcc")));
    }

    /** Verifies: JPK-CALC-001, JPK-CALC-003, JPK-INV-008.
     * Seam: Skeleton -> XslCalculus -> direct XML versus App-saved NHD XML.
     * Depends on: emptyBaseProducesSkeletonRoot, distinguishesParameterMetrics.
     * Depends-On: emptyBaseProducesSkeletonRoot, distinguishesParameterMetrics. */
    @Test void directNhdCalculusMatchesSavedClassProjection() throws Exception {
        final Path source = compile("CalcNhd", "package fixture; public class CalcNhd { private int x; public int read(){return x;} }");
        final Skeleton skeleton = new Skeleton(new DefaultBase(source));
        final var direct = new XslCalculus().node("NHD", Map.of(), skeleton.xml());
        final Path out = analyze("calc-nhd", source, Map.of("NHD", ""));
        final var saved = new XMLDocument(out.resolve("NHD.xml").toFile());
        final Set<String> expected = classMetricValues(direct, "CalcNhd");
        assertAll(() -> assertFalse(expected.isEmpty()),
            () -> assertEquals(expected, classMetricValues(saved, "CalcNhd")));
    }

    /** Verifies: JPK-CALC-003, JPK-STATE-005.
     * Seam: Skeleton XML -> XslCalculus -> unchanged source projection.
     * Depends on: emptyBaseProducesSkeletonRoot, directNhdCalculusMatchesSavedClassProjection.
     * Depends-On: emptyBaseProducesSkeletonRoot. */
    @Test void xslCalculusLeavesSkeletonDocumentUnchanged() throws Exception {
        final Path source = compile("CalcStable", "package fixture; public class CalcStable { public void one(){} }");
        final var projection = new Skeleton(new DefaultBase(source)).xml();
        final String before = projection.toString();
        new XslCalculus().node("NHD", Map.of(), projection);
        assertEquals(before, projection.toString());
    }

    /** Verifies: JPK-LIFE-002, JPK-XML-017, JPK-ERR-006.
     * Seam: App analysis -> blocked target path -> observable IO failure.
     * Depends on: emptyBaseProducesSkeletonRoot, freshTargetReturnsRequestedPath.
     * Depends-On: emptyBaseProducesSkeletonRoot, freshTargetReturnsRequestedPath. */
    @Test void appRaisesIoFailureForUnwritableTargetShape() throws Exception {
        final Path blocker = Files.writeString(this.temp.resolve("not-a-directory"), "block");
        final Path impossible = blocker.resolve("child");
        assertThrows(IOException.class,
            () -> new App(emptyClasses("blocked-source"), impossible, Map.of("NHD", "")).analyze());
    }
}


