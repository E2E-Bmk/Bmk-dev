package atomic;

import static org.junit.jupiter.api.Assertions.*;

import com.esotericsoftware.kryo.KryoException;
import com.esotericsoftware.kryo.io.Input;
import com.esotericsoftware.kryo.io.KryoBufferOverflowException;
import com.esotericsoftware.kryo.io.KryoBufferUnderflowException;
import com.esotericsoftware.kryo.io.Output;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.util.concurrent.atomic.AtomicBoolean;
import org.junit.jupiter.api.Test;

class CoreIoAtomicTest {
    /** Verifies: KRYO-IO-003, KRYO-IO-007 */
    @Test void outputSetBufferUsesProvidedArrayAndResetsCursors() {
        byte[] buffer = new byte[12];
        Output output = new Output();
        output.setBuffer(buffer);
        assertSame(buffer, output.getBuffer());
        assertEquals(0, output.position());
        assertEquals(0L, output.total());
    }

    /** Verifies: KRYO-IO-004, KRYO-IO-007 */
    @Test void inputSetBufferUsesRequestedSlice() {
        byte[] buffer = {9, 8, 7, 6, 5};
        Input input = new Input();
        input.setBuffer(buffer, 1, 3);
        assertSame(buffer, input.getBuffer());
        assertEquals(1, input.position());
        assertEquals(4, input.limit());
        assertEquals(8, input.readByteUnsigned());
    }

    /** Verifies: KRYO-IO-008 */
    @Test void outputResetClearsPositionAndTotal() {
        Output output = new Output(8, 32);
        output.writeInt(42);
        output.reset();
        assertEquals(0, output.position());
        assertEquals(0L, output.total());
    }

    /** Verifies: KRYO-IO-008 */
    @Test void inputResetClearsPositionAndTotal() {
        Input input = new Input(new byte[] {1, 2, 3});
        assertEquals(1, input.readByteUnsigned());
        input.reset();
        assertEquals(0, input.position());
        assertEquals(0L, input.total());
    }

    /** Verifies: KRYO-IO-009 */
    @Test void expandableOutputGrowsAndPreservesBytes() {
        Output output = new Output(2, -1);
        output.writeBytes(new byte[] {1, 2, 3, 4, 5});
        assertArrayEquals(new byte[] {1, 2, 3, 4, 5}, output.toBytes());
        assertTrue(output.getBuffer().length >= 5);
    }

    /** Verifies: KRYO-IO-010 */
    @Test void flushMovesPendingBytesToStreamAndUpdatesTotal() {
        ByteArrayOutputStream sink = new ByteArrayOutputStream();
        Output output = new Output(sink, 8);
        output.writeBytes(new byte[] {3, 4, 5});
        output.flush();
        assertArrayEquals(new byte[] {3, 4, 5}, sink.toByteArray());
        assertEquals(0, output.position());
        assertEquals(3L, output.total());
    }

    /** Verifies: KRYO-IO-011 */
    @Test void outputCloseClosesAssociatedStream() {
        AtomicBoolean closed = new AtomicBoolean();
        ByteArrayOutputStream sink = new ByteArrayOutputStream() {
            @Override public void close() throws IOException {
                closed.set(true);
                super.close();
            }
        };
        Output output = new Output(sink, 8);
        output.writeByte(1);
        output.close();
        assertTrue(closed.get());
        assertArrayEquals(new byte[] {1}, sink.toByteArray());
    }

    /** Verifies: KRYO-IO-012 */
    @Test void inputRefillsAcrossSmallStreamBuffer() {
        Input input = new Input(new ByteArrayInputStream(new byte[] {1, 2, 3, 4}), 2);
        assertArrayEquals(new byte[] {1, 2, 3, 4}, input.readBytes(4));
        assertTrue(input.end());
    }

    /** Verifies: KRYO-IO-013 */
    @Test void inputCloseClosesAssociatedStream() {
        AtomicBoolean closed = new AtomicBoolean();
        ByteArrayInputStream source = new ByteArrayInputStream(new byte[] {1}) {
            @Override public void close() throws IOException {
                closed.set(true);
                super.close();
            }
        };
        Input input = new Input(source);
        input.close();
        assertTrue(closed.get());
    }

    /** Verifies: KRYO-IO-014 */
    @Test void readAtEndReturnsMinusOneAndEndIsTrue() {
        Input input = new Input(new byte[] {7});
        assertEquals(7, input.read());
        assertEquals(-1, input.read());
        assertTrue(input.end());
    }

    /** Verifies: KRYO-IO-015 */
    @Test void availableCombinesBufferedAndStreamBytes() throws IOException {
        Input input = new Input(new ByteArrayInputStream(new byte[] {1, 2, 3, 4}), 2);
        assertEquals(4, input.available());
        input.readByte();
        assertEquals(3, input.available());
    }

    /** Verifies: KRYO-IO-016, KRYO-ERR-007 */
    @Test void requiredReadBeyondDataRaisesUnderflow() {
        Input input = new Input(new ByteArrayInputStream(new byte[] {1}), 4);
        assertThrows(KryoBufferUnderflowException.class, input::readInt);
    }

    /** Verifies: KRYO-IO-017, KRYO-ERR-008 */
    @Test void writeBeyondFiniteMaximumRaisesOverflow() {
        Output output = new Output(2, 2);
        assertThrows(KryoBufferOverflowException.class, () -> output.writeInt(9));
    }

    /** Verifies: KRYO-IO-018 */
    @Test void byteRoundTrip() {
        Output out = new Output(8, -1); out.writeByte(-7);
        assertEquals(-7, new Input(out.toBytes()).readByte());
    }

    /** Verifies: KRYO-IO-018 */
    @Test void shortRoundTrip() {
        Output out = new Output(8, -1); out.writeShort(-1234);
        assertEquals(-1234, new Input(out.toBytes()).readShort());
    }

    /** Verifies: KRYO-IO-018 */
    @Test void charRoundTrip() {
        Output out = new Output(8, -1); out.writeChar('界');
        assertEquals('界', new Input(out.toBytes()).readChar());
    }

    /** Verifies: KRYO-IO-018 */
    @Test void booleanRoundTrip() {
        Output out = new Output(8, -1); out.writeBoolean(true);
        assertTrue(new Input(out.toBytes()).readBoolean());
    }

    /** Verifies: KRYO-IO-018 */
    @Test void intRoundTrip() {
        Output out = new Output(8, -1); out.writeInt(0x12345678);
        assertEquals(0x12345678, new Input(out.toBytes()).readInt());
    }

    /** Verifies: KRYO-IO-018 */
    @Test void longRoundTrip() {
        Output out = new Output(16, -1); out.writeLong(-9000000000001L);
        assertEquals(-9000000000001L, new Input(out.toBytes()).readLong());
    }

    /** Verifies: KRYO-IO-018 */
    @Test void floatRoundTrip() {
        Output out = new Output(8, -1); out.writeFloat(12.5f);
        assertEquals(12.5f, new Input(out.toBytes()).readFloat());
    }

    /** Verifies: KRYO-IO-018 */
    @Test void doubleRoundTrip() {
        Output out = new Output(16, -1); out.writeDouble(-0.125d);
        assertEquals(-0.125d, new Input(out.toBytes()).readDouble());
    }

    /** Verifies: KRYO-IO-019 */
    @Test void positiveVarIntRoundTripReportsLength() {
        Output out = new Output(8, -1);
        int count = out.writeVarInt(300, true);
        assertEquals(count, out.position());
        assertEquals(300, new Input(out.toBytes()).readVarInt(true));
    }

    /** Verifies: KRYO-IO-019 */
    @Test void signedVarIntRoundTripReportsLength() {
        Output out = new Output(8, -1);
        int count = out.writeVarInt(-300, false);
        assertEquals(count, out.position());
        assertEquals(-300, new Input(out.toBytes()).readVarInt(false));
    }

    /** Verifies: KRYO-IO-019 */
    @Test void positiveVarLongRoundTripReportsLength() {
        Output out = new Output(16, -1);
        int count = out.writeVarLong(9000000000L, true);
        assertEquals(count, out.position());
        assertEquals(9000000000L, new Input(out.toBytes()).readVarLong(true));
    }

    /** Verifies: KRYO-IO-019 */
    @Test void signedVarLongRoundTripReportsLength() {
        Output out = new Output(16, -1);
        int count = out.writeVarLong(-9000000000L, false);
        assertEquals(count, out.position());
        assertEquals(-9000000000L, new Input(out.toBytes()).readVarLong(false));
    }

    /** Verifies: KRYO-IO-020 */
    @Test void varIntLengthMatchesBytesWritten() {
        Output out = new Output(8, -1);
        int actual = out.writeVarInt(16384, true);
        assertEquals(Output.varIntLength(16384, true), actual);
    }

    /** Verifies: KRYO-IO-020 */
    @Test void varLongLengthMatchesBytesWritten() {
        Output out = new Output(16, -1);
        int actual = out.writeVarLong(Long.MAX_VALUE, true);
        assertEquals(Output.varLongLength(Long.MAX_VALUE, true), actual);
    }

    /** Verifies: KRYO-IO-021 */
    @Test void canReadVarIntDoesNotConsumeValue() {
        Output out = new Output(8, -1); out.writeVarInt(321, true);
        Input input = new Input(out.toBytes());
        assertTrue(input.canReadVarInt());
        assertEquals(0, input.position());
        assertEquals(321, input.readVarInt(true));
    }

    /** Verifies: KRYO-IO-022 */
    @Test void variableLengthSettingControlsConfiguredIntOverload() {
        Output variable = new Output(8, -1);
        variable.setVariableLengthEncoding(true);
        variable.writeInt(1, true);
        Output fixed = new Output(8, -1);
        fixed.setVariableLengthEncoding(false);
        fixed.writeInt(1, true);
        assertEquals(1, variable.position());
        assertEquals(4, fixed.position());
    }

    /** Verifies: KRYO-IO-023 */
    @Test void nullStringRoundTrip() {
        Output out = new Output(8, -1); out.writeString((String)null);
        assertNull(new Input(out.toBytes()).readString());
    }

    /** Verifies: KRYO-IO-023 */
    @Test void emptyStringRoundTrip() {
        Output out = new Output(8, -1); out.writeString("");
        assertEquals("", new Input(out.toBytes()).readString());
    }

    /** Verifies: KRYO-IO-023 */
    @Test void asciiStringRoundTrip() {
        Output out = new Output(16, -1); out.writeString("kryo-123");
        assertEquals("kryo-123", new Input(out.toBytes()).readString());
    }

    /** Verifies: KRYO-IO-023 */
    @Test void unicodeStringRoundTrip() {
        Output out = new Output(16, -1); out.writeString("你好-λ");
        assertEquals("你好-λ", new Input(out.toBytes()).readString());
    }

    /** Verifies: KRYO-IO-024 */
    @Test void asciiWriterFeedsStringBuilderReader() {
        Output out = new Output(16, -1); out.writeAscii("plain");
        assertEquals("plain", new Input(out.toBytes()).readStringBuilder().toString());
    }

    /** Verifies: KRYO-IO-026 */
    @Test void intArraySliceRoundTrip() {
        Output out = new Output(32, -1);
        out.writeInts(new int[] {10, 20, 30, 40}, 1, 2);
        assertArrayEquals(new int[] {20, 30}, new Input(out.toBytes()).readInts(2));
    }

    /** Verifies: KRYO-IO-026 */
    @Test void longArraySliceRoundTrip() {
        Output out = new Output(48, -1);
        out.writeLongs(new long[] {1L, 2L, 3L}, 1, 2);
        assertArrayEquals(new long[] {2L, 3L}, new Input(out.toBytes()).readLongs(2));
    }

    /** Verifies: KRYO-IO-026 */
    @Test void booleanArrayRoundTrip() {
        Output out = new Output(16, -1);
        out.writeBooleans(new boolean[] {true, false, true}, 0, 3);
        assertArrayEquals(new boolean[] {true, false, true}, new Input(out.toBytes()).readBooleans(3));
    }

    /** Verifies: KRYO-IO-027 */
    @Test void readBytesReturnsExactLengthAndAdvancesCursor() {
        Input input = new Input(new byte[] {4, 5, 6, 7});
        assertArrayEquals(new byte[] {4, 5, 6}, input.readBytes(3));
        assertEquals(3, input.position());
    }

    /** Verifies: KRYO-IO-031, KRYO-ERR-005 */
    @Test void negativeMaximumArraySizeIsRejected() {
        Input input = new Input(new byte[] {1});
        assertThrows(IllegalArgumentException.class, () -> input.setMaxArraySize(-1));
    }

    /** Verifies: KRYO-IO-030 */
    @Test void feasibleArrayLengthIsReturned() {
        Input input = new Input(new byte[] {1, 2, 3, 4});
        assertEquals(2, input.validateArrayLength(2, 2));
    }

    /** Verifies: KRYO-IO-032, KRYO-ERR-006 */
    @Test void initialOutputSizeAboveMaximumIsRejected() {
        assertThrows(IllegalArgumentException.class, () -> new Output(5, 4));
    }

    /** Verifies: KRYO-IO-032, KRYO-ERR-006 */
    @Test void outputMaximumBelowUnlimitedSentinelIsRejected() {
        assertThrows(IllegalArgumentException.class, () -> new Output(1, -2));
    }
}
