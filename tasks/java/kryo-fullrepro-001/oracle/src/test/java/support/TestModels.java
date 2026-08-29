package support;

import com.esotericsoftware.kryo.Kryo;
import com.esotericsoftware.kryo.KryoCopyable;
import com.esotericsoftware.kryo.KryoSerializable;
import com.esotericsoftware.kryo.Serializer;
import com.esotericsoftware.kryo.io.Input;
import com.esotericsoftware.kryo.io.Output;

public final class TestModels {
    private TestModels() {
    }

    public static final class Message {
        public int number;
        public String text;

        public Message() {
        }

        public Message(int number, String text) {
            this.number = number;
            this.text = text;
        }
    }

    public static final class Node {
        public String name;
        public Node next;
        public Node other;

        public Node() {
        }

        public Node(String name) {
            this.name = name;
        }
    }

    public static final class Pair {
        public Message first;
        public Message second;

        public Pair() {
        }

        public Pair(Message first, Message second) {
            this.first = first;
            this.second = second;
        }
    }

    public static final class SerializableValue implements KryoSerializable {
        public int number;
        public String text;

        public SerializableValue() {
        }

        public SerializableValue(int number, String text) {
            this.number = number;
            this.text = text;
        }

        @Override
        public void write(Kryo kryo, Output output) {
            output.writeInt(number);
            output.writeString(text);
        }

        @Override
        public void read(Kryo kryo, Input input) {
            number = input.readInt();
            text = input.readString();
        }
    }

    public static final class CopyableNode implements KryoCopyable<CopyableNode> {
        public String name;
        public CopyableNode child;

        public CopyableNode() {
        }

        public CopyableNode(String name) {
            this.name = name;
        }

        @Override
        public CopyableNode copy(Kryo kryo) {
            CopyableNode copy = new CopyableNode(name);
            kryo.reference(copy);
            copy.child = kryo.copy(child);
            return copy;
        }
    }

    public static class MessageSerializer extends Serializer<Message> {
        public int writes;
        public int reads;
        private final int marker;

        public MessageSerializer() {
            this(71);
        }

        public MessageSerializer(int marker) {
            this.marker = marker;
        }

        @Override
        public void write(Kryo kryo, Output output, Message object) {
            writes++;
            output.writeInt(marker);
            output.writeInt(object.number);
            output.writeString(object.text);
        }

        @Override
        public Message read(Kryo kryo, Input input, Class<? extends Message> type) {
            reads++;
            int actualMarker = input.readInt();
            if (actualMarker != marker) {
                throw new IllegalStateException("unexpected marker");
            }
            return new Message(input.readInt(), input.readString());
        }

        @Override
        public Message copy(Kryo kryo, Message original) {
            return new Message(original.number, original.text);
        }
    }
}
