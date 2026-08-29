package atomic;

import static org.junit.jupiter.api.Assertions.*;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.logging.Handler;
import org.jboss.logmanager.Level;
import org.jboss.logmanager.LogContext;
import org.jboss.logmanager.Logger;
import org.junit.jupiter.api.Test;
import support.RecordingHandler;

/** Atomic checks for isolated contexts, hierarchy state, levels, handlers, and attachments. */
class ContextAtomicTest {
    /** Verifies: JBLM-CTX-001. */
    @Test void isolatesCreatedContexts() throws Exception {
        try (LogContext first = LogContext.create(true); LogContext second = LogContext.create(true)) {
            Logger a = first.getLogger("payments.delta");
            assertNull(second.getLoggerIfExists("payments.delta"));
            assertEquals("payments.delta", first.getLoggerIfExists("payments.delta").getName());
            assertSame(first, a.getLogContext());
        }
    }

    /** Verifies: JBLM-CTX-002, JBLM-CTX-003, JBLM-CTX-004. */
    @Test void lookupTransitionsFromAbsentToPresent() throws Exception {
        try (LogContext context = LogContext.create(true)) {
            assertNull(context.getLoggerIfExists("alpha.beta.gamma"));
            Logger created = context.getLogger("alpha.beta.gamma");
            assertEquals(created.getName(), context.getLogger("alpha.beta.gamma").getName());
            assertTrue(Collections.list(context.getLoggerNames()).contains("alpha.beta.gamma"));
        }
    }

    /** Verifies: JBLM-CTX-005, JBLM-CTX-006, JBLM-ERR-002. */
    @Test void exposesNameDerivedParentHierarchy() throws Exception {
        try (LogContext context = LogContext.create(true)) {
            Logger child = context.getLogger("orders.eu.worker");
            assertEquals("orders.eu", child.getParent().getName());
            assertEquals("orders", child.getParent().getParent().getName());
            assertNull(context.getLogger("").getParent());
            assertThrows(SecurityException.class, () -> child.setParent(context.getLogger("other")));
        }
    }

    /** Verifies: JBLM-CTX-007, JBLM-CTX-008, JBLM-CTX-011, JBLM-ERR-001. */
    @Test void resolvesDocumentedLevels() throws Exception {
        try (LogContext context = LogContext.create(true)) {
            assertAll(
                    () -> assertEquals(1100, Level.FATAL.intValue()),
                    () -> assertEquals(1000, Level.ERROR.intValue()),
                    () -> assertEquals(900, Level.WARN.intValue()),
                    () -> assertEquals(800, Level.INFO.intValue()),
                    () -> assertEquals(500, Level.DEBUG.intValue()),
                    () -> assertEquals(400, Level.TRACE.intValue()),
                    () -> assertSame(Level.DEBUG, context.getLevelForName("DEBUG")),
                    () -> assertThrows(IllegalArgumentException.class, () -> context.getLevelForName(null)));
        }
    }

    /** Verifies: JBLM-CTX-009. */
    @Test void registersAndReplacesCustomLevels() throws Exception {
        try (LogContext context = LogContext.create(true)) {
            java.util.logging.Level first = new java.util.logging.Level("NOTICE_641", 641) { private static final long serialVersionUID = 1L; };
            java.util.logging.Level replacement = new java.util.logging.Level("NOTICE_641", 642) { private static final long serialVersionUID = 1L; };
            context.registerLevel(first, true);
            assertSame(first, context.getLevelForName("NOTICE_641"));
            context.registerLevel(replacement, true);
            assertSame(replacement, context.getLevelForName("NOTICE_641"));
            context.unregisterLevel(replacement);
        }
    }

    /** Verifies: JBLM-CTX-012, JBLM-CTX-013, JBLM-CTX-014. */
    @Test void inheritsEffectiveLevelFromAncestor() throws Exception {
        try (LogContext context = LogContext.create(true)) {
            Logger parent = context.getLogger("shipment");
            Logger child = context.getLogger("shipment.pack");
            parent.setLevel(Level.WARN);
            child.setLevel(null);
            assertEquals(Level.WARN.intValue(), child.getEffectiveLevel());
            assertFalse(child.isLoggable(Level.INFO));
            child.setLevelName("TRACE");
            assertSame(Level.TRACE, child.getLevel());
            assertTrue(child.isLoggable(Level.DEBUG));
        }
    }

    /** Verifies: JBLM-CTX-017, JBLM-CTX-018, JBLM-CTX-019, JBLM-ERR-003. */
    @Test void maintainsOrderedIndependentHandlerSnapshots() throws Exception {
        try (LogContext context = LogContext.create(true)) {
            Logger logger = context.getLogger("snapshot.channel");
            RecordingHandler one = new RecordingHandler();
            RecordingHandler two = new RecordingHandler();
            logger.setHandlers(new Handler[] {one, two});
            Handler[] snapshot = logger.getHandlers();
            snapshot[0] = two;
            assertArrayEquals(new Handler[] {one, two}, logger.getHandlers());
            Handler[] prior = logger.getAndSetHandlers(new Handler[] {two});
            assertArrayEquals(new Handler[] {one, two}, prior);
            assertThrows(IllegalArgumentException.class, () -> logger.setHandlers(new Handler[] {one, null}));
            assertThrows(NullPointerException.class, () -> logger.addHandler(null));
        }
    }

    /** Verifies: JBLM-CTX-023, JBLM-CTX-024, JBLM-CTX-025, JBLM-CTX-027, JBLM-ERR-004. */
    @Test void maintainsTypedAttachmentsAndRejectsNulls() throws Exception {
        try (LogContext context = LogContext.create(true)) {
            Logger logger = context.getLogger("attachment.node");
            Logger.AttachmentKey<String> key = new Logger.AttachmentKey<>();
            assertNull(logger.attach(key, "north"));
            assertEquals("north", logger.attachIfAbsent(key, "south"));
            assertEquals("north", logger.getAttachment(key));
            assertEquals("north", logger.detach(key));
            assertNull(logger.getAttachment(key));
            assertThrows(IllegalArgumentException.class, () -> context.attach(key, null));
        }
    }
}
