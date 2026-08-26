package atomic;

import static org.junit.jupiter.api.Assertions.*;

import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.snakeyaml.engine.v2.api.LoadSettings;
import org.snakeyaml.engine.v2.api.lowlevel.Compose;
import org.snakeyaml.engine.v2.common.ScalarStyle;
import org.snakeyaml.engine.v2.nodes.MappingNode;
import org.snakeyaml.engine.v2.nodes.Node;
import org.snakeyaml.engine.v2.nodes.NodeTuple;
import org.snakeyaml.engine.v2.nodes.NodeType;
import org.snakeyaml.engine.v2.nodes.ScalarNode;
import org.snakeyaml.engine.v2.nodes.SequenceNode;
import org.snakeyaml.engine.v2.nodes.Tag;

/** Atomic tests for the low-level compose entry point and node model. */
class ComposeAtomicTest {

    private static Compose compose() {
        return new Compose(LoadSettings.builder().build());
    }

    /** Verifies: Composing Node Graphs — non-empty input composes a present root. */
    @Test void nonEmptyInputComposesPresentRoot() {
        Optional<Node> root = compose().composeString("a: [1, two]");
        assertTrue(root.isPresent());
    }

    /** Verifies: Composing Node Graphs — empty input composes an empty optional. */
    @Test void emptyInputComposesEmptyOptional() {
        assertTrue(compose().composeString("").isEmpty());
    }

    /** Verifies: Composing Node Graphs — mapping root carries map tag and type. */
    @Test void mappingRootCarriesMapTagAndType() {
        Node root = compose().composeString("a: [1, two]").get();
        assertEquals(NodeType.MAPPING, root.getNodeType());
        assertEquals(Tag.MAP, root.getTag());
    }

    /** Verifies: Composing Node Graphs — tuples expose key and value nodes. */
    @Test void tuplesExposeKeyAndValueNodes() {
        MappingNode root = (MappingNode) compose().composeString("a: [1, two]").get();
        NodeTuple tuple = root.getValue().get(0);
        ScalarNode key = (ScalarNode) tuple.getKeyNode();
        assertEquals("a", key.getValue());
        assertEquals(Tag.STR, key.getTag());
        assertEquals(NodeType.SEQUENCE, tuple.getValueNode().getNodeType());
    }

    /** Verifies: Composing Node Graphs — sequence children resolve individual tags. */
    @Test void sequenceChildrenResolveIndividualTags() {
        MappingNode root = (MappingNode) compose().composeString("a: [1, two]").get();
        SequenceNode seq = (SequenceNode) root.getValue().get(0).getValueNode();
        assertEquals(Tag.INT, seq.getValue().get(0).getTag());
        assertEquals(Tag.STR, seq.getValue().get(1).getTag());
        assertEquals("1", ((ScalarNode) seq.getValue().get(0)).getValue());
    }

    /** Verifies: Composing Node Graphs — plain scalars report plain style. */
    @Test void plainScalarsReportPlainStyle() {
        MappingNode root = (MappingNode) compose().composeString("a: [1, two]").get();
        SequenceNode seq = (SequenceNode) root.getValue().get(0).getValueNode();
        assertEquals(ScalarStyle.PLAIN, ((ScalarNode) seq.getValue().get(0)).getScalarStyle());
    }

    /** Verifies: Composing Node Graphs — anchors surface on the anchored node. */
    @Test void anchorsSurfaceOnAnchoredNode() {
        Node root = compose().composeString("&x [1]").get();
        assertTrue(root.getAnchor().isPresent());
        assertEquals("x", String.valueOf(root.getAnchor().get()));
    }

    /** Verifies: Composing Node Graphs — standard tag text forms. */
    @Test void standardTagTextForms() {
        assertEquals("tag:yaml.org,2002:str", Tag.STR.toString());
        assertEquals("tag:yaml.org,2002:int", Tag.INT.toString());
        assertEquals("tag:yaml.org,2002:float", Tag.FLOAT.toString());
        assertEquals("tag:yaml.org,2002:bool", Tag.BOOL.toString());
        assertEquals("tag:yaml.org,2002:null", Tag.NULL.toString());
        assertEquals("tag:yaml.org,2002:map", Tag.MAP.toString());
        assertEquals("tag:yaml.org,2002:seq", Tag.SEQ.toString());
    }

    /** Verifies: Composing Node Graphs — alias composes as the anchored node instance. */
    @Test void aliasComposesAsAnchoredNodeInstance() {
        MappingNode root = (MappingNode) compose()
                .composeString("base: &b {x: 1}\nref: *b").get();
        assertSame(root.getValue().get(0).getValueNode(), root.getValue().get(1).getValueNode());
    }
}
