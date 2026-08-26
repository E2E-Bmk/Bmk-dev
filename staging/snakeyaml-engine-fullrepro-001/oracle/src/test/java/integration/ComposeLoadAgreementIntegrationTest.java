package integration;

import static org.junit.jupiter.api.Assertions.*;

import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.snakeyaml.engine.v2.api.LoadSettings;
import org.snakeyaml.engine.v2.api.lowlevel.Compose;
import org.snakeyaml.engine.v2.nodes.MappingNode;
import org.snakeyaml.engine.v2.nodes.NodeTuple;
import org.snakeyaml.engine.v2.nodes.NodeType;
import org.snakeyaml.engine.v2.nodes.ScalarNode;
import org.snakeyaml.engine.v2.nodes.SequenceNode;
import org.snakeyaml.engine.v2.nodes.Tag;
import support.Yaml;

/** Integration tests for agreement between the compose and load projections. */
class ComposeLoadAgreementIntegrationTest {

    private static final String SOURCE = Yaml.doc(
            "text: hello",
            "count: 7",
            "ratio: 2.5",
            "flag: true",
            "nothing: null",
            "items: [1, two]");

    private static Compose compose() {
        return new Compose(LoadSettings.builder().build());
    }

    /**
     * Verifies: Cross-View Invariants — scalar tags correspond to loaded Java types.
     * Depends-On: sequenceChildrenResolveIndividualTags, scalarValuesResolveToSchemaTypes,
     * jsonSchemaResolvesNullLiteral.
     */
    @Test void scalarTagsCorrespondToLoadedTypes() {
        MappingNode root = (MappingNode) compose().composeString(SOURCE).get();
        Map<?, ?> loaded = (Map<?, ?>) Yaml.load().loadFromString(SOURCE);
        Map<String, Tag> tags = new java.util.LinkedHashMap<>();
        for (NodeTuple tuple : root.getValue()) {
            String key = ((ScalarNode) tuple.getKeyNode()).getValue();
            tags.put(key, tuple.getValueNode().getTag());
        }
        assertEquals(Tag.STR, tags.get("text"));
        assertEquals(String.class, loaded.get("text").getClass());
        assertEquals(Tag.INT, tags.get("count"));
        assertEquals(Integer.class, loaded.get("count").getClass());
        assertEquals(Tag.FLOAT, tags.get("ratio"));
        assertEquals(Double.class, loaded.get("ratio").getClass());
        assertEquals(Tag.BOOL, tags.get("flag"));
        assertEquals(Boolean.class, loaded.get("flag").getClass());
        assertEquals(Tag.NULL, tags.get("nothing"));
        assertNull(loaded.get("nothing"));
    }

    /**
     * Verifies: Cross-View Invariants — node structure mirrors loaded structure.
     * Depends-On: mappingRootCarriesMapTagAndType, nestedStructuresLoadRecursively.
     */
    @Test void nodeStructureMirrorsLoadedStructure() {
        MappingNode root = (MappingNode) compose().composeString(SOURCE).get();
        Map<?, ?> loaded = (Map<?, ?>) Yaml.load().loadFromString(SOURCE);
        assertEquals(loaded.size(), root.getValue().size());
        NodeTuple items = root.getValue().get(5);
        assertEquals("items", ((ScalarNode) items.getKeyNode()).getValue());
        SequenceNode seq = (SequenceNode) items.getValueNode();
        assertEquals(((List<?>) loaded.get("items")).size(), seq.getValue().size());
    }

    /**
     * Verifies: Cross-View Invariants — key order in the node graph is document order.
     * Depends-On: tuplesExposeKeyAndValueNodes, mappingLoadsAsInsertionOrderedMap.
     */
    @Test void keyOrderInNodeGraphIsDocumentOrder() {
        MappingNode root = (MappingNode) compose().composeString(SOURCE).get();
        Map<?, ?> loaded = (Map<?, ?>) Yaml.load().loadFromString(SOURCE);
        List<String> nodeKeys = root.getValue().stream()
                .map(tuple -> ((ScalarNode) tuple.getKeyNode()).getValue())
                .toList();
        assertEquals(new java.util.ArrayList<>(loaded.keySet()), nodeKeys);
    }

    /**
     * Verifies: Composing Node Graphs — scalar node values are the raw text.
     * Depends-On: sequenceChildrenResolveIndividualTags, scalarValuesResolveToSchemaTypes.
     */
    @Test void scalarNodeValuesAreRawText() {
        MappingNode root = (MappingNode) compose().composeString(SOURCE).get();
        NodeTuple count = root.getValue().get(1);
        assertEquals("7", ((ScalarNode) count.getValueNode()).getValue());
        NodeTuple ratio = root.getValue().get(2);
        assertEquals("2.5", ((ScalarNode) ratio.getValueNode()).getValue());
    }

    /**
     * Verifies: Cross-View Invariants — alias identity agrees between graph and objects.
     * Depends-On: aliasComposesAsAnchoredNodeInstance, aliasResolvesToAnchoredInstance.
     */
    @Test void aliasIdentityAgreesBetweenGraphAndObjects() {
        String text = "base: &b {x: 1}\nref: *b";
        MappingNode root = (MappingNode) compose().composeString(text).get();
        assertSame(root.getValue().get(0).getValueNode(), root.getValue().get(1).getValueNode());
        Map<?, ?> loaded = (Map<?, ?>) Yaml.load().loadFromString(text);
        assertSame(loaded.get("base"), loaded.get("ref"));
    }

    /**
     * Verifies: Cross-View Invariants — compose empties exactly when load returns null.
     * Depends-On: emptyInputComposesEmptyOptional, emptyInputLoadsAsNull.
     */
    @Test void composeEmptiesExactlyWhenLoadIsNull() {
        assertTrue(compose().composeString("").isEmpty());
        assertNull(Yaml.load().loadFromString(""));
        assertTrue(compose().composeString("x").isPresent());
        assertNotNull(Yaml.load().loadFromString("x"));
    }

    /**
     * Verifies: Composing Node Graphs — dumped text composes back to matching node types.
     * Depends-On: mappingRootCarriesMapTagAndType, autoStyleBlocksTopLevelFlowsNested.
     */
    @Test void dumpedTextComposesBackToMatchingNodeTypes() {
        Map<String, Object> data = new java.util.LinkedHashMap<>();
        data.put("a", 1);
        data.put("b", List.of(1, 2));
        String dumped = Yaml.dump().dumpToString(data);
        MappingNode root = (MappingNode) compose().composeString(dumped).get();
        assertEquals(NodeType.MAPPING, root.getNodeType());
        assertEquals(NodeType.SEQUENCE, root.getValue().get(1).getValueNode().getNodeType());
        assertEquals(NodeType.SCALAR, root.getValue().get(0).getValueNode().getNodeType());
    }

    /**
     * Verifies: Cross-View Invariants — quoted strings compose with string tags.
     * Depends-On: numericShapedStringIsQuoted, sequenceChildrenResolveIndividualTags.
     */
    @Test void quotedStringsComposeWithStringTags() {
        String dumped = Yaml.dump().dumpToString("123");
        ScalarNode node = (ScalarNode) compose().composeString(dumped).get();
        assertEquals(Tag.STR, node.getTag());
        assertEquals("123", node.getValue());
    }
}
