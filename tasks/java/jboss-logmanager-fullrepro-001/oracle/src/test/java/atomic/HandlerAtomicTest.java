package atomic;

import static org.junit.jupiter.api.Assertions.*;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.UnsupportedEncodingException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.logging.Formatter;
import java.util.logging.Handler;
import java.util.logging.LogRecord;
import org.jboss.logmanager.ExtLogRecord;
import org.jboss.logmanager.Level;
import org.jboss.logmanager.formatters.PatternFormatter;
import org.jboss.logmanager.handlers.AsyncHandler;
import org.jboss.logmanager.handlers.FileHandler;
import org.jboss.logmanager.handlers.OutputStreamHandler;
import org.jboss.logmanager.handlers.QueueHandler;
import org.jboss.logmanager.handlers.WriterHandler;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import support.TrackingWriter;

/** Atomic checks for handler policy, destinations, queue bounds, and lifecycle. */
class HandlerAtomicTest {
    private static ExtLogRecord record(String message) {
        return new ExtLogRecord(Level.INFO, message, ExtLogRecord.FormatStyle.NO_FORMAT, "caller.Type");
    }

    /** Verifies: JBLM-HND-019, JBLM-HND-021. */
    @Test void queueHandlerRetainsNewestRecordsWithinItsBound() {
        QueueHandler queue = new QueueHandler();
        assertEquals(10, queue.getLimit());
        queue.setLimit(3);
        queue.publish(record("q-41")); queue.publish(record("q-42")); queue.publish(record("q-43")); queue.publish(record("q-44"));
        assertEquals(List.of("q-42", "q-43", "q-44"), java.util.Arrays.stream(queue.getQueue()).map(LogRecord::getMessage).toList());
    }

    /** Verifies: JBLM-HND-022, JBLM-HND-023. */
    @Test void queueHandlerReturnsIndependentFormattedSnapshots() {
        QueueHandler queue = new QueueHandler(2);
        queue.setFormatter(new PatternFormatter("[%m]"));
        queue.publish(record("snap-51")); queue.publish(record("snap-52"));
        ExtLogRecord[] snapshot = queue.getQueue();
        snapshot[0] = record("tampered");
        assertEquals("snap-51", queue.getQueue()[0].getMessage());
        assertArrayEquals(new String[] {"[snap-51]", "[snap-52]"}, queue.getQueueAsStrings());
    }

    /** Verifies: JBLM-HND-020, JBLM-HND-026, JBLM-HND-030, JBLM-ERR-011, JBLM-ERR-012. */
    @Test void handlerBoundsAndThreadFactoryErrorsAreSpecific() {
        assertThrows(IllegalArgumentException.class, () -> new QueueHandler(0));
        QueueHandler queue = new QueueHandler(4);
        assertThrows(IllegalArgumentException.class, () -> queue.setLimit(-2));
        AsyncHandler async = new AsyncHandler(37);
        assertEquals(37, async.getQueueLength());
        assertSame(AsyncHandler.OverflowAction.BLOCK, async.getOverflowAction());
        async.close();
        assertThrows(IllegalArgumentException.class, () -> new AsyncHandler(3, runnable -> null));
    }

    /** Verifies: JBLM-HND-004, JBLM-HND-005, JBLM-HND-009, JBLM-HND-030, JBLM-ERR-009, JBLM-ERR-010. */
    @Test void extHandlerDefaultsAndRequiredPolicyErrorsAreStable() throws Exception {
        QueueHandler handler = new QueueHandler();
        assertSame(java.util.logging.Level.ALL, handler.getLevel());
        assertEquals(StandardCharsets.UTF_8, handler.getCharset());
        assertTrue(handler.isAutoFlush());
        assertTrue(handler.isCloseChildren());
        handler.setEncoding(null);
        assertEquals(StandardCharsets.UTF_8, handler.getCharset());
        assertThrows(UnsupportedEncodingException.class, () -> handler.setEncoding("NO_SUCH_CHARSET_943"));
        assertThrows(NullPointerException.class, () -> handler.setCharset(null));
        AsyncHandler async = new AsyncHandler(5);
        assertThrows(NullPointerException.class, () -> async.setOverflowAction(null));
        async.close();
    }

    /** Verifies: JBLM-HND-013, JBLM-HND-014. */
    @Test void outputStreamHandlerUsesUpdatedCharsetForLaterBytes() throws Exception {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        OutputStreamHandler handler = new OutputStreamHandler(bytes, new PatternFormatter("%m"));
        handler.setAutoFlush(true);
        handler.publish(record("plain-A"));
        int boundary = bytes.size();
        handler.setCharset(StandardCharsets.UTF_16BE);
        handler.publish(record("wide-Ω"));
        byte[] result = bytes.toByteArray();
        assertEquals("plain-A", new String(result, 0, boundary, StandardCharsets.UTF_8));
        assertEquals("wide-Ω", new String(result, boundary, result.length - boundary, StandardCharsets.UTF_16BE));
    }

    /** Verifies: JBLM-HND-010, JBLM-HND-011, JBLM-HND-012. */
    @Test void writerHandlerWritesHeadBodyTailAndClosesReplacedWriter() {
        Formatter formatter = new Formatter() {
            @Override public String getHead(Handler h) { return "HEAD-"; }
            @Override public String format(LogRecord record) { return "BODY:" + record.getMessage(); }
            @Override public String getTail(Handler h) { return "-TAIL"; }
        };
        WriterHandler handler = new WriterHandler(); handler.setFormatter(formatter);
        TrackingWriter first = new TrackingWriter(); TrackingWriter second = new TrackingWriter();
        handler.setWriter(first); handler.publish(record("writer-61")); handler.setWriter(second);
        assertEquals("HEAD-BODY:writer-61-TAIL", first.toString());
        assertTrue(first.closed());
        handler.setWriter(null);
        assertTrue(second.closed());
    }

    /** Verifies: JBLM-HND-015, JBLM-HND-016, JBLM-HND-017, JBLM-HND-018, JBLM-ERR-013. */
    @Test void fileHandlerSelectsOverwritesAndDisablesDestinations(@TempDir Path directory) throws Exception {
        Path file = directory.resolve("deep/nested/atomic-handler.log");
        FileHandler handler = new FileHandler(); handler.setFormatter(new PatternFormatter("%m"));
        assertNull(handler.getFile());
        handler.setFile(file.toFile()); handler.publish(record("file-71")); handler.close();
        assertEquals("file-71", Files.readString(file, StandardCharsets.UTF_8));
        FileHandler replacement = new FileHandler(); replacement.setFormatter(new PatternFormatter("%m")); replacement.setAppend(false); replacement.setFile(file.toFile());
        replacement.publish(record("file-72")); replacement.close();
        assertEquals("file-72", Files.readString(file, StandardCharsets.UTF_8));
        FileHandler inactive = new FileHandler(); inactive.setFile(null); assertNull(inactive.getFile());
        assertThrows(FileNotFoundException.class, () -> inactive.setFile(directory.toFile()));
    }
}
