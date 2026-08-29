package atomic;

import static org.junit.jupiter.api.Assertions.*;

import com.esotericsoftware.kryo.Kryo;
import com.esotericsoftware.kryo.KryoException;
import com.esotericsoftware.kryo.Registration;
import com.esotericsoftware.kryo.Serializer;
import com.esotericsoftware.kryo.io.Input;
import com.esotericsoftware.kryo.io.Output;
import com.esotericsoftware.kryo.util.ListReferenceResolver;
import com.esotericsoftware.kryo.util.MapReferenceResolver;
import org.junit.jupiter.api.Test;
import support.TestModels.Message;
import support.TestModels.MessageSerializer;

class CoreApiAtomicTest {
    /** Verifies: KRYO-REF-001 */
    @Test void defaultSessionStartsWithoutReferences() {
        assertFalse(new Kryo().getReferences());
    }

    /** Verifies: KRYO-REF-002 */
    @Test void enablingReferencesInstallsDefaultResolverAndReturnsPreviousValue() {
        Kryo kryo = new Kryo();
        assertFalse(kryo.setReferences(true));
        assertTrue(kryo.getReferences());
        assertInstanceOf(MapReferenceResolver.class, kryo.getReferenceResolver());
    }

    /** Verifies: KRYO-REF-006, KRYO-REF-007 */
    @Test void explicitReferenceResolverIsInstalledAndEnablesReferences() {
        Kryo kryo = new Kryo();
        ListReferenceResolver resolver = new ListReferenceResolver();
        kryo.setReferenceResolver(resolver);
        assertSame(resolver, kryo.getReferenceResolver());
        assertTrue(kryo.getReferences());
    }

    /** Verifies: KRYO-REF-008, KRYO-ERR-001 */
    @Test void nullReferenceResolverIsRejected() {
        assertThrows(IllegalArgumentException.class, () -> new Kryo().setReferenceResolver(null));
    }

    /** Verifies: KRYO-REF-018, KRYO-ERR-004 */
    @Test void maximumDepthBelowOneIsRejected() {
        assertThrows(IllegalArgumentException.class, () -> new Kryo().setMaxDepth(0));
    }

    /** Verifies: KRYO-REG-008, KRYO-ERR-003 */
    @Test void negativeRegistrationIdIsRejected() {
        assertThrows(IllegalArgumentException.class, () -> new Kryo().register(Message.class, -1));
    }

    /** Verifies: KRYO-REG-009, KRYO-ERR-002 */
    @Test void requiredRegistrationRejectsUnknownType() {
        Kryo kryo = new Kryo();
        kryo.setRegistrationRequired(true);
        assertThrows(IllegalArgumentException.class, () -> kryo.getRegistration(Message.class));
    }

    /** Verifies: KRYO-REG-010, KRYO-REG-011 */
    @Test void optionalRegistrationCreatesImplicitRecord() {
        Kryo kryo = new Kryo();
        kryo.setRegistrationRequired(false);
        Registration registration = kryo.getRegistration(Message.class);
        assertFalse(kryo.isRegistrationRequired());
        assertEquals(Message.class, registration.getType());
        assertNotNull(registration.getSerializer());
    }

    /** Verifies: KRYO-REG-004, KRYO-REG-018 */
    @Test void explicitRegistrationExposesTypeIdAndSerializer() {
        Kryo kryo = new Kryo();
        MessageSerializer serializer = new MessageSerializer();
        Registration registration = kryo.register(Message.class, serializer, 77);
        assertEquals(77, registration.getId());
        assertEquals(Message.class, registration.getType());
        assertSame(serializer, registration.getSerializer());
        assertSame(registration, kryo.getRegistration(77));
    }

    /** Verifies: KRYO-REG-002 */
    @Test void duplicateRegistrationWithoutSerializerReturnsExistingRecord() {
        Kryo kryo = new Kryo();
        Registration first = kryo.register(Message.class);
        Registration second = kryo.register(Message.class);
        assertSame(first, second);
        assertEquals(first.getId(), second.getId());
    }

    /** Verifies: KRYO-REG-003, KRYO-REG-005 */
    @Test void registrationSerializerCanBeReplaced() {
        Kryo kryo = new Kryo();
        Registration registration = kryo.register(Message.class, new MessageSerializer(1));
        MessageSerializer replacement = new MessageSerializer(2);
        registration.setSerializer(replacement);
        assertSame(replacement, registration.getSerializer());
        assertSame(replacement, kryo.getSerializer(Message.class));
    }

    /** Verifies: KRYO-REG-015 */
    @Test void configuredGlobalDefaultSerializerPolicySuppliesInstances() {
        Kryo kryo = new Kryo();
        kryo.setDefaultSerializer(MessageSerializer.class);
        assertInstanceOf(MessageSerializer.class, kryo.getDefaultSerializer(Message.class));
    }

    /** Verifies: KRYO-COPY-001 */
    @Test void copyOfNullReturnsNull() {
        assertNull(new Kryo().copy(null));
    }

    /** Verifies: KRYO-COPY-008 */
    @Test void immutableDefaultSerializerCopyReturnsOriginal() {
        Serializer<Message> serializer = bareSerializer();
        serializer.setImmutable(true);
        Message original = new Message(1, "one");
        assertSame(original, serializer.copy(new Kryo(), original));
    }

    /** Verifies: KRYO-COPY-009, KRYO-ERR-012 */
    @Test void nonImmutableDefaultSerializerCopyIsRejected() {
        Serializer<Message> serializer = bareSerializer();
        assertThrows(KryoException.class, () -> serializer.copy(new Kryo(), new Message(1, "one")));
    }

    private static Serializer<Message> bareSerializer() {
        return new Serializer<Message>() {
            @Override public void write(Kryo kryo, Output output, Message object) {
                output.writeInt(object.number);
            }

            @Override public Message read(Kryo kryo, Input input, Class<? extends Message> type) {
                return new Message(input.readInt(), null);
            }
        };
    }
}
