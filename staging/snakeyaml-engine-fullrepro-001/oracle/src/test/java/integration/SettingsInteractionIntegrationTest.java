package integration;

import static org.junit.jupiter.api.Assertions.*;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.snakeyaml.engine.v2.api.Dump;
import org.snakeyaml.engine.v2.api.DumpSettings;
import org.snakeyaml.engine.v2.api.Load;
import org.snakeyaml.engine.v2.api.LoadSettings;
import org.snakeyaml.engine.v2.common.FlowStyle;
import org.snakeyaml.engine.v2.exceptions.MarkedYamlEngineException;
import org.snakeyaml.engine.v2.exceptions.YamlEngineException;
import org.snakeyaml.engine.v2.schema.CoreSchema;
import support.Yaml;

/** Integration tests for settings interactions across both pipelines. */
class SettingsInteractionIntegrationTest {

    /**
     * Verifies: Dump Settings and Presentation — markers compose with flow style.
     * Depends-On: explicitStartAndEndMarkers, flowStyleRendersInline.
     */
    @Test void markersComposeWithFlowStyle() {
        Dump dump = new Dump(DumpSettings.builder()
                .setDefaultFlowStyle(FlowStyle.FLOW)
                .setExplicitStart(true)
                .setExplicitEnd(true)
                .build());
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("a", 1);
        data.put("b", List.of(1));
        assertEquals("--- {a: 1, b: [1]}\n...\n", dump.dumpToString(data));
        assertEquals(data, Yaml.load().loadFromString(dump.dumpToString(data)));
    }

    /**
     * Verifies: Dump Settings and Presentation — indentation interacts with block nesting.
     * Depends-On: indentWidthAppliesToBlockNesting, blockStyleLaysOutLineByLine.
     */
    @Test void indentationInteractsWithBlockNesting() {
        Map<String, Object> nested = new LinkedHashMap<>();
        nested.put("outer", Map.of("inner", Map.of("x", 1)));
        Dump dump = new Dump(DumpSettings.builder()
                .setDefaultFlowStyle(FlowStyle.BLOCK).setIndent(4).build());
        String out = dump.dumpToString(nested);
        assertEquals("outer:\n    inner:\n        x: 1\n", out);
        assertEquals(nested, Yaml.load().loadFromString(out));
    }

    /**
     * Verifies: Cross-View Invariants — width-wrapped output reloads to the same value.
     * Depends-On: widthWrapsLongPlainScalars, plainScalarDocumentLoadsAsScalar.
     */
    @Test void widthWrappedOutputReloadsSameValue() {
        StringBuilder words = new StringBuilder();
        for (int i = 0; i < 12; i++) {
            words.append("word").append(i).append(' ');
        }
        String value = words.toString().trim();
        Dump narrow = new Dump(DumpSettings.builder().setWidth(20).build());
        String out = narrow.dumpToString(value);
        assertTrue(out.contains("\n  "));
        assertEquals(value, Yaml.load().loadFromString(out));
    }

    /**
     * Verifies: Cross-View Invariants — multi-line flow output reloads to the same value.
     * Depends-On: multiLineFlowSpreadsFlowCollections, nestedStructuresLoadRecursively.
     */
    @Test void multiLineFlowOutputReloadsSameValue() {
        Map<String, Object> data = Map.of("k", List.of(1, 2));
        Dump dump = new Dump(DumpSettings.builder().setMultiLineFlow(true).build());
        assertEquals(data, Yaml.load().loadFromString(dump.dumpToString(data)));
    }

    /**
     * Verifies: Schemas and Scalar Resolution — the same text loads differently per schema.
     * Depends-On: hexStaysStringUnderJsonSchema, coreSchemaResolvesHexAndOctal.
     */
    @Test void sameTextLoadsDifferentlyPerSchema() {
        String text = "k: 0x1A";
        Load json = Yaml.load();
        Load core = new Load(LoadSettings.builder().setSchema(new CoreSchema()).build());
        assertEquals("0x1A", ((Map<?, ?>) json.loadFromString(text)).get("k"));
        assertEquals(26, ((Map<?, ?>) core.loadFromString(text)).get("k"));
    }

    /**
     * Verifies: Cross-View Invariants — core-schema values round trip through dump.
     * Depends-On: coreSchemaResolvesHexAndOctal, autoStyleBlocksTopLevelFlowsNested.
     */
    @Test void coreSchemaValuesRoundTripThroughDump() {
        Load core = new Load(LoadSettings.builder().setSchema(new CoreSchema()).build());
        Object loaded = core.loadFromString("hex: 0x1A\nflag: True\nnothing: ~");
        String dumped = Yaml.dump().dumpToString(loaded);
        assertEquals(loaded, core.loadFromString(dumped));
        assertEquals(loaded, Yaml.load().loadFromString(dumped));
    }

    /**
     * Verifies: Load Settings — label and marks survive through a labeled pipeline.
     * Depends-On: labelAppearsInParseErrorMessages, problemMarksCarryZeroBasedLines.
     */
    @Test void labelAndMarksSurviveThroughLabeledPipeline() {
        Load labeled = new Load(LoadSettings.builder().setLabel("pipeline-input").build());
        MarkedYamlEngineException ex = assertThrows(MarkedYamlEngineException.class,
                () -> labeled.loadFromString("ok: 1\nbad: [1,\n  2"));
        assertTrue(ex.getMessage().contains("pipeline-input"));
        assertTrue(ex.getProblemMark().isPresent());
        assertEquals(2, ex.getProblemMark().get().getLine());
    }

    /**
     * Verifies: Loading YAML Documents — alias budget interacts with document shape.
     * Depends-On: aliasBudgetEnforcesConfiguredMaximum, aliasResolvesToAnchoredInstance.
     */
    @Test void aliasBudgetInteractsWithDocumentShape() {
        Load limited = new Load(LoadSettings.builder().setMaxAliasesForCollections(2).build());
        assertEquals(Map.of("a", List.of(1), "b", List.of(List.of(1), List.of(1))),
                limited.loadFromString("a: &a [1]\nb: [*a, *a]"));
        assertThrows(YamlEngineException.class,
                () -> limited.loadFromString("a: &a [1]\nb: [*a, *a, *a]"));
    }

    /**
     * Verifies: State Model — one settings object drives many equivalent pipelines.
     * Depends-On: settingsObjectIsReusable, mappingLoadsAsInsertionOrderedMap.
     */
    @Test void oneSettingsObjectDrivesEquivalentPipelines() {
        LoadSettings settings = LoadSettings.builder().setAllowDuplicateKeys(true).build();
        Load first = new Load(settings);
        Load second = new Load(settings);
        assertEquals(first.loadFromString("a: 1\na: 2"), second.loadFromString("a: 1\na: 2"));
        assertEquals(Map.of("a", 2), first.loadFromString("a: 1\na: 2"));
    }
}
