package integration;

import static org.junit.jupiter.api.Assertions.*;

import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.logging.Handler;
import java.util.logging.LogRecord;
import org.jboss.logmanager.ExtLogRecord;
import org.jboss.logmanager.Level;
import org.jboss.logmanager.LogContext;
import org.jboss.logmanager.Logger;
import org.jboss.logmanager.formatters.PatternFormatter;
import org.jboss.logmanager.handlers.FileHandler;
import org.jboss.logmanager.handlers.QueueHandler;
import org.jboss.logmanager.handlers.WriterHandler;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import support.RecordingHandler;
import support.TrackingWriter;

/** Integration checks for handler ordering, replay, draining, and coherent close. */
class HandlerIntegrationTest {
    private static ExtLogRecord record(String message) { return new ExtLogRecord(Level.INFO, message, ExtLogRecord.FormatStyle.NO_FORMAT, "caller.Type"); }
    private static Handler orderedHandler(String name, List<String> events) {
        return new Handler() {
            @Override public void publish(LogRecord record) { events.add(name + ":" + record.getMessage()); }
            @Override public void flush() { }
            @Override public void close() { events.add(name + ":closed"); }
        };
    }

    /**
     * Verifies: JBLM-INV-006, JBLM-CTX-017, JBLM-CTX-022.
     * Seam: protocol handoff
     * Depends-On: maintainsOrderedIndependentHandlerSnapshots, lookupTransitionsFromAbsentToPresent
     */
    @Test void loggerHandlerSnapshotOrderIsPublicationOrder() throws Exception {
        try (LogContext context = LogContext.create(true)) {
            List<String> events = new ArrayList<>(); Logger logger = context.getLogger("order.direct"); logger.setUseParentHandlers(false); logger.setLevel(Level.INFO);
            Handler first = orderedHandler("first", events); Handler second = orderedHandler("second", events); logger.setHandlers(new Handler[] {first, second});
            logger.info("event-301");
            assertEquals(List.of("first:event-301", "second:event-301"), events);
        }
    }

    /**
     * Verifies: JBLM-INV-006, JBLM-HND-024.
     * Seam: protocol handoff
     * Depends-On: queueHandlerRetainsNewestRecordsWithinItsBound, maintainsOrderedIndependentHandlerSnapshots
     */
    @Test void queueReplayPreservesRecordThenChildOrder() {
        QueueHandler queue = new QueueHandler(4); queue.publish(record("replay-302")); queue.publish(record("replay-303"));
        List<String> events = new ArrayList<>(); queue.setHandlers(new Handler[] {orderedHandler("A", events), orderedHandler("B", events)}); queue.replay();
        assertEquals(List.of("A:replay-302", "B:replay-302", "A:replay-303", "B:replay-303"), events);
    }

    /**
     * Verifies: JBLM-INV-010, JBLM-CTX-028, JBLM-HND-008.
     * Seam: lifecycle crossing
     * Depends-On: maintainsOrderedIndependentHandlerSnapshots, extHandlerDefaultsAndRequiredPolicyErrorsAreStable
     */
    @Test void contextCloseClosesAttachedLoggerHandler() throws Exception {
        LogContext context = LogContext.create(true); RecordingHandler handler = new RecordingHandler();
        context.getLogger("close.direct").addHandler(handler); AutoCloseable closeAction = handler::close; context.addCloseHandler(closeAction); context.close();
        assertTrue(handler.closed());
    }

    /**
     * Verifies: JBLM-INV-010, JBLM-CTX-028.
     * Seam: lifecycle crossing
     * Depends-On: lookupTransitionsFromAbsentToPresent, maintainsTypedAttachmentsAndRejectsNulls
     */
    @Test void contextCloseResourcesRunOnceInInsertionOrder() throws Exception {
        LogContext context = LogContext.create(true); List<String> events = new ArrayList<>();
        AutoCloseable one = () -> events.add("one"); AutoCloseable two = () -> events.add("two");
        context.addCloseHandler(one); context.addCloseHandler(two); context.addCloseHandler(one); context.close();
        assertEquals(List.of("one", "two"), events);
    }

    /**
     * Verifies: JBLM-INV-010, JBLM-HND-016, JBLM-CTX-028.
     * Seam: lifecycle crossing
     * Depends-On: fileHandlerSelectsOverwritesAndDisablesDestinations, lookupTransitionsFromAbsentToPresent
     */
    @Test void contextCloseFlushesDurableFileOutput(@TempDir Path directory) throws Exception {
        Path file = directory.resolve("close/file-304.log"); LogContext context = LogContext.create(true);
        FileHandler handler = new FileHandler(); handler.setFormatter(new PatternFormatter("%m")); handler.setFile(file.toFile()); Logger logger = context.getLogger("close.file");
        logger.setUseParentHandlers(false); logger.addHandler(handler); logger.info("durable-305"); context.close();
        assertEquals("durable-305", Files.readString(file, StandardCharsets.UTF_8));
    }

    /**
     * Verifies: JBLM-INV-010, JBLM-HND-008, JBLM-CTX-028.
     * Seam: lifecycle crossing
     * Depends-On: extHandlerDefaultsAndRequiredPolicyErrorsAreStable, maintainsOrderedIndependentHandlerSnapshots
     */
    @Test void contextClosePropagatesThroughHandlerChildren() throws Exception {
        LogContext context = LogContext.create(true); RecordingHandler first = new RecordingHandler(); RecordingHandler second = new RecordingHandler();
        QueueHandler parent = new QueueHandler(4); parent.setHandlers(new Handler[] {first, second}); context.getLogger("close.children").addHandler(parent);
        AutoCloseable closeAction = parent::close; context.addCloseHandler(closeAction); context.close();
        assertTrue(first.closed()); assertTrue(second.closed());
    }

    /**
     * Verifies: JBLM-INV-010, JBLM-HND-011, JBLM-HND-012.
     * Seam: lifecycle crossing
     * Depends-On: writerHandlerWritesHeadBodyTailAndClosesReplacedWriter, maintainsOrderedIndependentHandlerSnapshots
     */
    @Test void contextCloseWritesWriterFormatterTail() throws Exception {
        LogContext context = LogContext.create(true); TrackingWriter writer = new TrackingWriter(); WriterHandler handler = new WriterHandler();
        handler.setFormatter(new java.util.logging.Formatter() {
            @Override public String getHead(Handler h) { return "<start>"; }
            @Override public String format(LogRecord r) { return r.getMessage(); }
            @Override public String getTail(Handler h) { return "<end>"; }
        });
        handler.setWriter(writer); Logger logger = context.getLogger("close.writer"); logger.setUseParentHandlers(false); logger.addHandler(handler); logger.info("middle-316");
        AutoCloseable closeAction = handler::close; context.addCloseHandler(closeAction); context.close();
        assertEquals("<start>middle-316<end>", writer.toString()); assertTrue(writer.closed());
    }

    /**
     * Verifies: JBLM-HND-025, JBLM-HND-024, JBLM-HND-021.
     * Seam: state consistency
     * Depends-On: queueHandlerRetainsNewestRecordsWithinItsBound, queueHandlerReturnsIndependentFormattedSnapshots
     */
    @Test void replayingAttachmentBridgesRetainedAndLiveRecords() {
        QueueHandler queue = new QueueHandler(3); queue.publish(record("retained-317")); RecordingHandler child = new RecordingHandler();
        queue.addHandler(child, true); queue.publish(record("live-318"));
        assertEquals(List.of("retained-317", "live-318"), child.records().stream().map(ExtLogRecord::getMessage).toList());
    }
}
