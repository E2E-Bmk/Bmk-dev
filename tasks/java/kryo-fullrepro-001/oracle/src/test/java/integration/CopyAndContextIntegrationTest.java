package integration;

import static org.junit.jupiter.api.Assertions.*;

import com.esotericsoftware.kryo.Kryo;
import com.esotericsoftware.kryo.KryoException;
import com.esotericsoftware.kryo.Serializer;
import com.esotericsoftware.kryo.io.Input;
import com.esotericsoftware.kryo.io.Output;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import support.TestModels.CopyableNode;
import support.TestModels.Message;
import support.TestModels.MessageSerializer;
import support.TestModels.Node;
import support.TestModels.Pair;

class CopyAndContextIntegrationTest {
    /** Verifies: KRYO-COPY-003, KRYO-INV-008. Depends-On: copyOfNullReturnsNull, registrationSerializerCanBeReplaced */
    @Test void deepCopyDuplicatesRootAndMutableDescendant() {
        Kryo kryo = new Kryo();
        kryo.register(Node.class);
        Node root = new Node("root");
        root.next = new Node("child");
        Node copy = kryo.copy(root);
        assertNotSame(root, copy);
        assertNotSame(root.next, copy.next);
        assertEquals("child", copy.next.name);
    }

    /** Verifies: KRYO-COPY-004, KRYO-INV-009. Depends-On: copyOfNullReturnsNull, registrationSerializerCanBeReplaced */
    @Test void shallowCopyDuplicatesRootButSharesDescendant() {
        Kryo kryo = new Kryo();
        kryo.register(Node.class);
        Node root = new Node("root");
        root.next = new Node("child");
        Node copy = kryo.copyShallow(root);
        assertNotSame(root, copy);
        assertSame(root.next, copy.next);
        assertEquals("root", copy.name);
    }

    /** Verifies: KRYO-COPY-005, KRYO-INV-010. Depends-On: registrationSerializerCanBeReplaced, copyOfNullReturnsNull */
    @Test void explicitCopySerializerOverridesRegisteredSerializer() {
        Kryo kryo = new Kryo();
        kryo.register(Message.class, new MessageSerializer(1));
        MessageSerializer explicit = new MessageSerializer(2);
        Message original = new Message(44, "explicit-copy");
        Message copy = kryo.copy(original, explicit);
        assertNotSame(original, copy);
        assertEquals(44, copy.number);
        assertEquals("explicit-copy", copy.text);
    }

    /** Verifies: KRYO-COPY-006, KRYO-INV-008. Depends-On: copyOfNullReturnsNull, enablingReferencesInstallsDefaultResolverAndReturnsPreviousValue */
    @Test void deepCopyPreservesRepeatedReferenceTopology() {
        Kryo kryo = new Kryo();
        kryo.register(Pair.class);
        kryo.register(Message.class);
        Message shared = new Message(9, "shared");
        Pair copy = kryo.copy(new Pair(shared, shared));
        assertSame(copy.first, copy.second);
        assertNotSame(shared, copy.first);
    }

    /** Verifies: KRYO-COPY-006. Depends-On: copyOfNullReturnsNull, enablingReferencesInstallsDefaultResolverAndReturnsPreviousValue */
    @Test void deepCopyPreservesCycle() {
        Kryo kryo = new Kryo();
        kryo.register(Node.class);
        Node root = new Node("cycle");
        root.next = root;
        Node copy = kryo.copy(root);
        assertNotSame(root, copy);
        assertSame(copy, copy.next);
    }

    /** Verifies: KRYO-COPY-007. Depends-On: copyOfNullReturnsNull, defaultSessionStartsWithoutReferences */
    @Test void disablingCopyReferencesDuplicatesRepeatedValues() {
        Kryo kryo = new Kryo();
        kryo.setCopyReferences(false);
        kryo.register(Pair.class);
        kryo.register(Message.class);
        Message shared = new Message(9, "split-copy");
        Pair copy = kryo.copy(new Pair(shared, shared));
        assertNotSame(copy.first, copy.second);
        assertEquals(copy.first.text, copy.second.text);
    }

    /** Verifies: KRYO-COPY-002, KRYO-COPY-010. Depends-On: immutableDefaultSerializerCopyReturnsOriginal, copyOfNullReturnsNull */
    @Test void kryoCopyableCallbackProducesRecursiveCopy() {
        Kryo kryo = new Kryo();
        CopyableNode root = new CopyableNode("root");
        root.child = new CopyableNode("child");
        CopyableNode copy = kryo.copy(root);
        assertNotSame(root, copy);
        assertNotSame(root.child, copy.child);
        assertEquals("child", copy.child.name);
    }

    /** Verifies: KRYO-REF-017. Depends-On: registrationSerializerCanBeReplaced, unicodeStringRoundTrip */
    @Test void nestedSerializerCallbacksObserveIncreasingDepthAndCompletionRestoresZero() {
        Kryo kryo = new Kryo();
        DepthSerializer serializer = new DepthSerializer();
        kryo.register(Node.class, serializer);
        Node root = new Node("root");
        root.next = new Node("child");
        Output output = new Output(64, -1);
        kryo.writeObject(output, root);
        assertTrue(serializer.depths.size() >= 2);
        assertTrue(serializer.depths.get(1) > serializer.depths.get(0));
        assertEquals(0, kryo.getDepth());
    }

    /** Verifies: KRYO-REF-018, KRYO-ERR-011. Depends-On: maximumDepthBelowOneIsRejected, explicitRegistrationExposesTypeIdAndSerializer */
    @Test void graphBeyondConfiguredDepthIsRejected() {
        Kryo kryo = new Kryo();
        kryo.setMaxDepth(2);
        kryo.register(Node.class);
        Node root = new Node("one");
        root.next = new Node("two");
        root.next.next = new Node("three");
        Output output = new Output(64, -1);
        assertThrows(KryoException.class, () -> kryo.writeObject(output, root));
    }

    private static final class DepthSerializer extends Serializer<Node> {
        private final List<Integer> depths = new ArrayList<>();

        @Override public void write(Kryo kryo, Output output, Node object) {
            depths.add(kryo.getDepth());
            output.writeString(object.name);
            kryo.writeObjectOrNull(output, object.next, this);
        }

        @Override public Node read(Kryo kryo, Input input, Class<? extends Node> type) {
            Node value = new Node(input.readString());
            value.next = kryo.readObjectOrNull(input, Node.class, this);
            return value;
        }
    }
}
