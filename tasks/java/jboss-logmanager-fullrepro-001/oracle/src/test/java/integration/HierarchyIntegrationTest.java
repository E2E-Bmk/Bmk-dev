package integration;

import static org.junit.jupiter.api.Assertions.*;

import java.util.Collections;
import org.jboss.logmanager.ExtLogRecord;
import org.jboss.logmanager.Level;
import org.jboss.logmanager.LogContext;
import org.jboss.logmanager.Logger;
import org.junit.jupiter.api.Test;
import support.RecordingHandler;

/** Integration checks across context, logger hierarchy, level, attachment, and delivery views. */
class HierarchyIntegrationTest {
    /**
     * Verifies: JBLM-INV-001, JBLM-CTX-002, JBLM-CTX-005.
     * Seam: state consistency
     * Depends-On: lookupTransitionsFromAbsentToPresent, exposesNameDerivedParentHierarchy
     */
    @Test void hierarchyLookupAgreesAcrossContextParentAndEnumeration() throws Exception {
        try (LogContext context = LogContext.create(true)) {
            Logger leaf = context.getLogger("catalog.eu.read");
            assertSame(context, leaf.getLogContext());
            assertEquals("catalog.eu", leaf.getParent().getName());
            assertTrue(Collections.list(context.getLoggerNames()).contains("catalog.eu.read"));
        }
    }

    /**
     * Verifies: JBLM-INV-001, JBLM-CTX-001, JBLM-CTX-003.
     * Seam: state consistency
     * Depends-On: isolatesCreatedContexts, lookupTransitionsFromAbsentToPresent
     */
    @Test void sameNamedLoggersRemainIndependentlyDiscoverable() throws Exception {
        try (LogContext east = LogContext.create(true); LogContext west = LogContext.create(true)) {
            Logger eastLogger = east.getLogger("inventory.zone.worker");
            Logger westLogger = west.getLogger("inventory.zone.worker");
            assertEquals("inventory.zone.worker", eastLogger.getName());
            assertEquals("inventory.zone.worker", westLogger.getName());
            Logger eastExisting = east.getLoggerIfExists("inventory.zone.worker");
            Logger westExisting = west.getLoggerIfExists("inventory.zone.worker");
            assertNotNull(eastExisting);
            assertNotNull(westExisting);
            assertEquals("inventory.zone.worker", eastExisting.getName());
            assertEquals("inventory.zone.worker", westExisting.getName());
            assertSame(east, eastExisting.getLogContext());
            assertSame(west, westExisting.getLogContext());
            assertNotSame(eastLogger, westLogger);
        }
    }

    /**
     * Verifies: JBLM-INV-002, JBLM-CTX-014, JBLM-CTX-022.
     * Seam: protocol handoff
     * Depends-On: resolvesDocumentedLevels, inheritsEffectiveLevelFromAncestor
     */
    @Test void namedLevelControlsEffectiveValueAndPublication() throws Exception {
        try (LogContext context = LogContext.create(true)) {
            Logger logger = context.getLogger("level.named.delivery"); RecordingHandler sink = new RecordingHandler();
            logger.setUseParentHandlers(false); logger.addHandler(sink); logger.setLevelName("WARN");
            logger.info("below-101"); logger.log(Level.WARN, "accepted-102");
            assertSame(Level.WARN, logger.getLevel());
            assertEquals(Level.WARN.intValue(), logger.getEffectiveLevel());
            assertEquals(java.util.List.of("accepted-102"), sink.records().stream().map(ExtLogRecord::getMessage).toList());
        }
    }

    /**
     * Verifies: JBLM-INV-002, JBLM-CTX-013, JBLM-CTX-020.
     * Seam: config interaction
     * Depends-On: inheritsEffectiveLevelFromAncestor, maintainsOrderedIndependentHandlerSnapshots
     */
    @Test void inheritedLevelAndParentHandlerJointlyControlDelivery() throws Exception {
        try (LogContext context = LogContext.create(true)) {
            Logger parent = context.getLogger("level.parent"); Logger child = context.getLogger("level.parent.child");
            RecordingHandler sink = new RecordingHandler(); parent.setLevel(Level.ERROR); parent.addHandler(sink);
            child.setLevel(null); child.setUseParentHandlers(true); child.log(Level.WARN, "blocked-103"); child.log(Level.ERROR, "accepted-104");
            assertEquals(Level.ERROR.intValue(), child.getEffectiveLevel());
            assertEquals(java.util.List.of("accepted-104"), sink.records().stream().map(ExtLogRecord::getMessage).toList());
        }
    }

    /**
     * Verifies: JBLM-INV-003, JBLM-CTX-024, JBLM-CTX-026.
     * Seam: state consistency
     * Depends-On: maintainsTypedAttachmentsAndRejectsNulls, lookupTransitionsFromAbsentToPresent
     */
    @Test void contextAttachmentIsVisibleFromRootLogger() throws Exception {
        try (LogContext context = LogContext.create(true)) {
            Logger.AttachmentKey<String> key = new Logger.AttachmentKey<>(); Logger root = context.getLogger(""); Logger projectedRoot = context.getLoggerIfExists("");
            assertNotNull(projectedRoot); root.attach(key, "shared-105");
            assertEquals("shared-105", projectedRoot.getAttachment(key));
        }
    }

    /**
     * Verifies: JBLM-INV-003, JBLM-CTX-024, JBLM-CTX-026.
     * Seam: state consistency
     * Depends-On: maintainsTypedAttachmentsAndRejectsNulls, exposesNameDerivedParentHierarchy
     */
    @Test void rootLoggerDetachRemovesContextProjection() throws Exception {
        try (LogContext context = LogContext.create(true)) {
            Logger.AttachmentKey<Integer> key = new Logger.AttachmentKey<>(); Logger root = context.getLogger(""); Logger projectedRoot = context.getLoggerIfExists("");
            assertNotNull(projectedRoot); root.attach(key, 761);
            assertEquals(761, projectedRoot.detach(key));
            assertNull(root.getAttachment(key));
        }
    }

    /**
     * Verifies: JBLM-CTX-015, JBLM-CTX-016, JBLM-CTX-022.
     * Seam: config interaction
     * Depends-On: maintainsOrderedIndependentHandlerSnapshots, singletonFiltersReturnOppositeConstants
     */
    @Test void ancestorFilterParticipatesOnlyWhenEnabled() throws Exception {
        try (LogContext context = LogContext.create(true)) {
            Logger parent = context.getLogger("filter.parent"); Logger child = context.getLogger("filter.parent.child");
            RecordingHandler sink = new RecordingHandler(); child.setUseParentHandlers(false); child.addHandler(sink); child.setLevel(Level.TRACE);
            parent.setFilter(record -> false); child.setUseParentFilters(true); child.info("blocked-106");
            child.setUseParentFilters(false); child.info("accepted-107");
            assertEquals(java.util.List.of("accepted-107"), sink.records().stream().map(ExtLogRecord::getMessage).toList());
        }
    }

    /**
     * Verifies: JBLM-CTX-020, JBLM-CTX-022.
     * Seam: protocol handoff
     * Depends-On: maintainsOrderedIndependentHandlerSnapshots, inheritsEffectiveLevelFromAncestor
     */
    @Test void childAndParentHandlersReceiveSameNamedRecord() throws Exception {
        try (LogContext context = LogContext.create(true)) {
            Logger parent = context.getLogger("route.parent"); Logger child = context.getLogger("route.parent.child");
            RecordingHandler direct = new RecordingHandler(); RecordingHandler inherited = new RecordingHandler();
            child.setLevel(Level.INFO); child.addHandler(direct); parent.addHandler(inherited); child.info("routed-108");
            assertEquals("route.parent.child", direct.records().get(0).getLoggerName());
            assertEquals("route.parent.child", inherited.records().get(0).getLoggerName());
        }
    }
}
