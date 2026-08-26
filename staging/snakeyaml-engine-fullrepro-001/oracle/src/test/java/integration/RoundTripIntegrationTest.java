package integration;

import static org.junit.jupiter.api.Assertions.*;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.snakeyaml.engine.v2.api.Dump;
import org.snakeyaml.engine.v2.api.DumpSettings;
import org.snakeyaml.engine.v2.common.FlowStyle;
import org.snakeyaml.engine.v2.common.ScalarStyle;
import support.Yaml;

/** Integration tests for load–dump round trips. */
class RoundTripIntegrationTest {

    private static final String SOURCE = Yaml.doc(
            "name: test",
            "items:",
            "- 1",
            "- 2",
            "nested:",
            "  k: v");

    /**
     * Verifies: Cross-View Invariants — default round trip preserves values.
     * Depends-On: mappingLoadsAsInsertionOrderedMap, autoStyleBlocksTopLevelFlowsNested.
     */
    @Test void defaultRoundTripPreservesValues() {
        Object loaded = Yaml.load().loadFromString(SOURCE);
        String dumped = Yaml.dump().dumpToString(loaded);
        assertEquals("name: test\nitems: [1, 2]\nnested: {k: v}\n", dumped);
        assertEquals(loaded, Yaml.load().loadFromString(dumped));
    }

    /**
     * Verifies: Cross-View Invariants — round trip holds under block style.
     * Depends-On: blockStyleLaysOutLineByLine, mappingLoadsAsInsertionOrderedMap.
     */
    @Test void roundTripHoldsUnderBlockStyle() {
        Object loaded = Yaml.load().loadFromString(SOURCE);
        Dump block = new Dump(DumpSettings.builder().setDefaultFlowStyle(FlowStyle.BLOCK).build());
        assertEquals(loaded, Yaml.load().loadFromString(block.dumpToString(loaded)));
    }

    /**
     * Verifies: Cross-View Invariants — round trip holds under flow style.
     * Depends-On: flowStyleRendersInline, mappingLoadsAsInsertionOrderedMap.
     */
    @Test void roundTripHoldsUnderFlowStyle() {
        Object loaded = Yaml.load().loadFromString(SOURCE);
        Dump flow = new Dump(DumpSettings.builder().setDefaultFlowStyle(FlowStyle.FLOW).build());
        assertEquals(loaded, Yaml.load().loadFromString(flow.dumpToString(loaded)));
    }

    /**
     * Verifies: Cross-View Invariants — quoting keeps ambiguous strings type-faithful.
     * Depends-On: booleanShapedStringIsQuoted, numericShapedStringIsQuoted,
     * scalarValuesResolveToSchemaTypes.
     */
    @Test void quotingKeepsAmbiguousStringsTypeFaithful() {
        List<Object> values = List.of("true", "123", "a: b", "", "3.5");
        for (Object value : values) {
            Object back = Yaml.load().loadFromString(Yaml.dump().dumpToString(value));
            assertEquals(value, back);
            assertEquals(String.class, back.getClass());
        }
    }

    /**
     * Verifies: Cross-View Invariants — shared references dump as anchors and reload shared.
     * Depends-On: aliasResolvesToAnchoredInstance, autoStyleBlocksTopLevelFlowsNested.
     */
    @Test void sharedReferencesDumpAsAnchorsAndReloadShared() {
        List<Integer> shared = new ArrayList<>(List.of(1, 2));
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("a", shared);
        data.put("b", shared);
        String dumped = Yaml.dump().dumpToString(data);
        assertEquals("a: &id001 [1, 2]\nb: *id001\n", dumped);
        Map<?, ?> back = (Map<?, ?>) Yaml.load().loadFromString(dumped);
        assertSame(back.get("a"), back.get("b"));
    }

    /**
     * Verifies: Cross-View Invariants — dumpAll and loadAll are inverse for streams.
     * Depends-On: dumpAllMarksDocumentsAfterFirst, loadAllIteratesDocumentsInOrder.
     */
    @Test void dumpAllAndLoadAllAreInverse() {
        List<Object> docs = List.of("one", Map.of("a", 1), List.of(1, 2));
        String stream = Yaml.dump().dumpAllToString(docs.iterator());
        List<Object> back = new ArrayList<>();
        for (Object doc : Yaml.load().loadAllFromString(stream)) {
            back.add(doc);
        }
        assertEquals(docs, back);
    }

    /**
     * Verifies: Cross-View Invariants — dumpAll of one element equals dumpToString.
     * Depends-On: dumpAllMarksDocumentsAfterFirst, plainScalarRendersWithNewline.
     */
    @Test void dumpAllOfOneElementEqualsDumpToString() {
        assertEquals(Yaml.dump().dumpToString("one"),
                Yaml.dump().dumpAllToString(List.<Object>of("one").iterator()));
        Map<String, Object> map = Map.of("a", 1);
        assertEquals(Yaml.dump().dumpToString(map),
                Yaml.dump().dumpAllToString(List.<Object>of(map).iterator()));
    }

    /**
     * Verifies: Cross-View Invariants — scalar styles change text but not values.
     * Depends-On: singleQuotedScalarStyle, doubleQuotedScalarStyle, literalStyleForMultiLineStrings.
     */
    @Test void scalarStylesChangeTextNotValues() {
        Map<String, Object> data = Map.of("a", "text\nlines");
        for (ScalarStyle style : List.of(ScalarStyle.SINGLE_QUOTED,
                ScalarStyle.DOUBLE_QUOTED, ScalarStyle.LITERAL)) {
            Dump dump = new Dump(DumpSettings.builder().setDefaultScalarStyle(style).build());
            assertEquals(data, Yaml.load().loadFromString(dump.dumpToString(data)));
        }
    }

    /**
     * Verifies: Cross-View Invariants — canonical form reloads to the same values.
     * Depends-On: canonicalFormWithExplicitTags, scalarValuesResolveToSchemaTypes.
     */
    @Test void canonicalFormReloadsToSameValues() {
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("a", 1);
        data.put("b", List.of("x", true));
        Dump canonical = new Dump(DumpSettings.builder().setCanonical(true).build());
        assertEquals(data, Yaml.load().loadFromString(canonical.dumpToString(data)));
    }

    /**
     * Verifies: State Model — loading and dumping are deterministic.
     * Depends-On: mappingLoadsAsInsertionOrderedMap, autoStyleBlocksTopLevelFlowsNested.
     */
    @Test void loadingAndDumpingAreDeterministic() {
        Object first = Yaml.load().loadFromString(SOURCE);
        Object second = Yaml.load().loadFromString(SOURCE);
        assertEquals(first, second);
        assertEquals(Yaml.dump().dumpToString(first), Yaml.dump().dumpToString(second));
    }
}
