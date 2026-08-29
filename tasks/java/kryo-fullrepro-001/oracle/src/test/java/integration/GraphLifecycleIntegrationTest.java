package integration;

import static org.junit.jupiter.api.Assertions.*;

import com.esotericsoftware.kryo.Kryo;
import com.esotericsoftware.kryo.Registration;
import com.esotericsoftware.kryo.io.Input;
import com.esotericsoftware.kryo.io.Output;
import com.esotericsoftware.kryo.util.ListReferenceResolver;
import org.junit.jupiter.api.Test;
import support.TestModels.Message;
import support.TestModels.MessageSerializer;
import support.TestModels.Node;
import support.TestModels.Pair;
import support.TestModels.SerializableValue;

class GraphLifecycleIntegrationTest {
    /** Verifies: KRYO-GRAPH-001, KRYO-GRAPH-003, KRYO-INV-001. Depends-On: explicitRegistrationExposesTypeIdAndSerializer, intRoundTrip, unicodeStringRoundTrip */
    @Test void registeredTypedObjectRoundTripsThroughBytes() {
        Kryo kryo = new Kryo();
        kryo.register(Message.class);
        Message restored = typedRoundTrip(kryo, new Message(41, "typed"));
        assertEquals(41, restored.number);
        assertEquals("typed", restored.text);
    }

    /** Verifies: KRYO-GRAPH-002, KRYO-GRAPH-004, KRYO-INV-010. Depends-On: explicitRegistrationExposesTypeIdAndSerializer, intRoundTrip */
    @Test void explicitSerializerOverridesRegisteredSerializer() {
        Kryo kryo = new Kryo();
        kryo.register(Message.class, new MessageSerializer(1));
        MessageSerializer explicit = new MessageSerializer(2);
        Output output = new Output(32, -1);
        kryo.writeObject(output, new Message(7, "override"), explicit);
        Message restored = kryo.readObject(new Input(output.toBytes()), Message.class, explicit);
        assertEquals(7, restored.number);
        assertEquals("override", restored.text);
        assertEquals(1, explicit.writes);
        assertEquals(1, explicit.reads);
    }

    /** Verifies: KRYO-GRAPH-007. Depends-On: nullStringRoundTrip, defaultSessionStartsWithoutReferences */
    @Test void nullableTypedNullRoundTrips() {
        Kryo kryo = new Kryo();
        MessageSerializer serializer = new MessageSerializer();
        Output output = new Output(16, -1);
        kryo.writeObjectOrNull(output, null, serializer);
        assertNull(kryo.readObjectOrNull(new Input(output.toBytes()), Message.class, serializer));
    }

    /** Verifies: KRYO-GRAPH-008. Depends-On: intRoundTrip, asciiStringRoundTrip */
    @Test void nullableTypedValueRoundTrips() {
        Kryo kryo = new Kryo();
        MessageSerializer serializer = new MessageSerializer();
        Output output = new Output(32, -1);
        kryo.writeObjectOrNull(output, new Message(9, "nullable"), serializer);
        Message restored = kryo.readObjectOrNull(new Input(output.toBytes()), Message.class, serializer);
        assertEquals(9, restored.number);
        assertEquals("nullable", restored.text);
    }

    /** Verifies: KRYO-GRAPH-009, KRYO-INV-002. Depends-On: explicitRegistrationExposesTypeIdAndSerializer, outputSetBufferUsesProvidedArrayAndResetsCursors */
    @Test void runtimeClassObjectRoundTripsWithType() {
        Kryo kryo = new Kryo();
        kryo.register(Message.class);
        Output output = new Output(32, -1);
        kryo.writeClassAndObject(output, new Message(15, "runtime"));
        Object restored = kryo.readClassAndObject(new Input(output.toBytes()));
        assertInstanceOf(Message.class, restored);
        assertEquals(15, ((Message) restored).number);
        assertEquals("runtime", ((Message) restored).text);
    }

    /** Verifies: KRYO-GRAPH-010. Depends-On: defaultSessionStartsWithoutReferences, nullStringRoundTrip */
    @Test void runtimeClassNullRoundTrips() {
        Kryo kryo = new Kryo();
        Output output = new Output(8, -1);
        kryo.writeClassAndObject(output, null);
        assertNull(kryo.readClassAndObject(new Input(output.toBytes())));
    }

    /** Verifies: KRYO-GRAPH-011. Depends-On: explicitRegistrationExposesTypeIdAndSerializer, varIntLengthMatchesBytesWritten */
    @Test void classRegistrationRoundTrips() {
        Kryo kryo = new Kryo();
        Registration expected = kryo.register(Message.class, 45);
        Output output = new Output(8, -1);
        kryo.writeClass(output, Message.class);
        Registration actual = kryo.readClass(new Input(output.toBytes()));
        assertSame(expected, actual);
        assertEquals(Message.class, actual.getType());
    }

    /** Verifies: KRYO-GRAPH-012. Depends-On: defaultSessionStartsWithoutReferences, nullStringRoundTrip */
    @Test void nullClassRoundTrips() {
        Kryo kryo = new Kryo();
        Output output = new Output(8, -1);
        kryo.writeClass(output, null);
        assertNull(kryo.readClass(new Input(output.toBytes())));
    }

    /** Verifies: KRYO-GRAPH-013, KRYO-GRAPH-014. Depends-On: registrationSerializerCanBeReplaced, intRoundTrip */
    @Test void registeredSerializerReceivesWriteAndReadCallbacks() {
        Kryo kryo = new Kryo();
        MessageSerializer serializer = new MessageSerializer();
        kryo.register(Message.class, serializer);
        Message restored = typedRoundTrip(kryo, new Message(3, "callbacks"));
        assertEquals(1, serializer.writes);
        assertEquals(1, serializer.reads);
        assertEquals("callbacks", restored.text);
    }

    /** Verifies: KRYO-GRAPH-015. Depends-On: intRoundTrip, unicodeStringRoundTrip */
    @Test void kryoSerializableCallbacksDefineRoundTrip() {
        Kryo kryo = new Kryo();
        kryo.register(SerializableValue.class);
        SerializableValue value = new SerializableValue(33, "self");
        Output output = new Output(32, -1);
        kryo.writeObject(output, value);
        SerializableValue restored = kryo.readObject(new Input(output.toBytes()), SerializableValue.class);
        assertEquals(33, restored.number);
        assertEquals("self", restored.text);
    }

    /** Verifies: KRYO-REF-003, KRYO-INV-005. Depends-On: enablingReferencesInstallsDefaultResolverAndReturnsPreviousValue, explicitRegistrationExposesTypeIdAndSerializer */
    @Test void repeatedObjectRestoresSameIdentityWhenReferencesEnabled() {
        Kryo kryo = configuredPairKryo(true);
        Message shared = new Message(5, "shared");
        Pair restored = typedRoundTrip(kryo, new Pair(shared, shared));
        assertSame(restored.first, restored.second);
        assertEquals("shared", restored.first.text);
    }

    /** Verifies: KRYO-REF-004, KRYO-INV-005. Depends-On: enablingReferencesInstallsDefaultResolverAndReturnsPreviousValue, explicitRegistrationExposesTypeIdAndSerializer */
    @Test void circularGraphRestoresCycleWhenReferencesEnabled() {
        Kryo kryo = new Kryo();
        kryo.setReferences(true);
        kryo.register(Node.class);
        Node root = new Node("root");
        root.next = root;
        Node restored = typedRoundTrip(kryo, root);
        assertSame(restored, restored.next);
        assertEquals("root", restored.name);
    }

    /** Verifies: KRYO-REF-005. Depends-On: defaultSessionStartsWithoutReferences, explicitRegistrationExposesTypeIdAndSerializer */
    @Test void repeatedObjectBecomesDistinctWhenReferencesDisabled() {
        Kryo kryo = configuredPairKryo(false);
        Message shared = new Message(6, "split");
        Pair restored = typedRoundTrip(kryo, new Pair(shared, shared));
        assertNotSame(restored.first, restored.second);
        assertEquals(restored.first.text, restored.second.text);
    }

    /** Verifies: KRYO-REF-006, KRYO-REF-003. Depends-On: explicitReferenceResolverIsInstalledAndEnablesReferences, explicitRegistrationExposesTypeIdAndSerializer */
    @Test void listReferenceResolverPreservesRepeatedIdentity() {
        Kryo kryo = new Kryo();
        kryo.setReferenceResolver(new ListReferenceResolver());
        kryo.register(Pair.class);
        kryo.register(Message.class);
        Message shared = new Message(8, "list");
        Pair restored = typedRoundTrip(kryo, new Pair(shared, shared));
        assertSame(restored.first, restored.second);
    }

    /** Verifies: KRYO-REG-012, KRYO-INV-002. Depends-On: explicitRegistrationExposesTypeIdAndSerializer, outputSetBufferUsesProvidedArrayAndResetsCursors */
    @Test void matchingExplicitIdsAcrossSessionsDecodeRuntimeType() {
        Kryo writer = new Kryo();
        writer.register(Message.class, 91);
        Output output = new Output(32, -1);
        writer.writeClassAndObject(output, new Message(12, "two-sessions"));

        Kryo reader = new Kryo();
        reader.register(Message.class, 91);
        Message restored = (Message) reader.readClassAndObject(new Input(output.toBytes()));
        assertEquals(12, restored.number);
        assertEquals("two-sessions", restored.text);
    }

    /** Verifies: KRYO-INV-003. Depends-On: explicitRegistrationExposesTypeIdAndSerializer, registrationSerializerCanBeReplaced */
    @Test void registrationViewsAgreeByTypeIdAndSerializer() {
        Kryo kryo = new Kryo();
        MessageSerializer serializer = new MessageSerializer();
        Registration created = kryo.register(Message.class, serializer, 63);
        assertSame(created, kryo.getRegistration(Message.class));
        assertSame(created, kryo.getRegistration(63));
        assertSame(serializer, kryo.getSerializer(Message.class));
    }

    /** Verifies: KRYO-INV-004. Depends-On: readBytesReturnsExactLengthAndAdvancesCursor, outputSetBufferUsesProvidedArrayAndResetsCursors */
    @Test void outputPositionBoundsInputReadableRange() {
        Output output = new Output(32, -1);
        output.writeInt(11);
        output.writeString("cursor");
        Input input = new Input(output.getBuffer(), 0, output.position());
        assertEquals(11, input.readInt());
        assertEquals("cursor", input.readString());
        assertEquals(output.position(), input.position());
        assertTrue(input.end());
    }

    /** Verifies: KRYO-INV-010, KRYO-GRAPH-013, KRYO-GRAPH-014. Depends-On: registrationSerializerCanBeReplaced, intRoundTrip */
    @Test void customSerializerControlsBytesAndRestoredValues() {
        Kryo kryo = new Kryo();
        MessageSerializer serializer = new MessageSerializer(1234);
        kryo.register(Message.class, serializer);
        Output output = new Output(32, -1);
        kryo.writeObject(output, new Message(19, "marker"));
        Input bytes = new Input(output.toBytes());
        assertEquals(1234, bytes.readInt());
        Message restored = kryo.readObject(new Input(output.toBytes()), Message.class);
        assertEquals(19, restored.number);
        assertEquals("marker", restored.text);
    }

    /** Verifies: KRYO-REG-003, KRYO-INV-010. Depends-On: registrationSerializerCanBeReplaced, intRoundTrip */
    @Test void serializerReplacementChangesSubsequentByteProtocol() {
        Kryo kryo = new Kryo();
        kryo.register(Message.class, new MessageSerializer(10));
        kryo.register(Message.class, new MessageSerializer(20));
        Output output = new Output(32, -1);
        kryo.writeObject(output, new Message(1, "replacement"));
        assertEquals(20, new Input(output.toBytes()).readInt());
        Message restored = kryo.readObject(new Input(output.toBytes()), Message.class);
        assertEquals("replacement", restored.text);
    }

    /** Verifies: KRYO-REG-010, KRYO-REG-013, KRYO-INV-001. Depends-On: optionalRegistrationCreatesImplicitRecord, intRoundTrip */
    @Test void implicitRegistrationSerializerSupportsTypedRoundTrip() {
        Kryo kryo = new Kryo();
        kryo.setRegistrationRequired(false);
        assertNotNull(kryo.getSerializer(Message.class));
        Message restored = typedRoundTrip(kryo, new Message(28, "implicit"));
        assertEquals(28, restored.number);
        assertEquals("implicit", restored.text);
    }

    private static Kryo configuredPairKryo(boolean references) {
        Kryo kryo = new Kryo();
        kryo.setReferences(references);
        kryo.register(Pair.class);
        kryo.register(Message.class);
        return kryo;
    }

    private static <T> T typedRoundTrip(Kryo kryo, T value) {
        @SuppressWarnings("unchecked")
        Class<T> type = (Class<T>) value.getClass();
        Output output = new Output(128, -1);
        kryo.writeObject(output, value);
        return kryo.readObject(new Input(output.toBytes()), type);
    }
}
