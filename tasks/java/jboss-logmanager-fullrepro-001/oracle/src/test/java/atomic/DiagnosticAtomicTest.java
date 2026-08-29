package atomic;

import static org.junit.jupiter.api.Assertions.*;

import java.util.HashMap;
import java.util.Map;
import java.util.logging.LogRecord;
import org.jboss.logmanager.ExtLogRecord;
import org.jboss.logmanager.MDC;
import org.jboss.logmanager.NDC;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;

/** Atomic checks for diagnostic context and extended record projections. */
class DiagnosticAtomicTest {
    @AfterEach void clearDiagnosticState() { MDC.clear(); NDC.clear(); }

    /** Verifies: JBLM-REC-001, JBLM-REC-002, JBLM-REC-005. */
    @Test void storesAndClearsMappedDiagnosticValues() {
        assertNull(MDC.put("trace-key", "v17"));
        assertEquals("v17", MDC.put("trace-key", "v18"));
        assertEquals("v18", MDC.get("trace-key"));
        MDC.clear();
        assertTrue(MDC.isEmpty());
        assertNull(MDC.get("trace-key"));
    }

    /** Verifies: JBLM-REC-003, JBLM-REC-004. */
    @Test void returnsIndependentMdcCopiesAndRemovedValues() {
        MDC.putObject("object-key", 271);
        Map<String, Object> copy = MDC.copyObject();
        copy.put("object-key", 999);
        assertEquals(271, MDC.getObject("object-key"));
        assertEquals(271, MDC.removeObject("object-key"));
        assertNull(MDC.getObject("object-key"));
    }

    /** Verifies: JBLM-REC-006, JBLM-REC-007, JBLM-REC-008, JBLM-REC-009. */
    @Test void exposesNestedStackDepthAndBottomIndexes() {
        NDC.push("outer-73");
        NDC.push("inner-74");
        assertEquals(2, NDC.getDepth());
        assertEquals("outer-73.inner-74", NDC.get());
        assertEquals("outer-73", NDC.get(0));
        assertEquals("inner-74", NDC.pop());
        assertEquals("outer-73", NDC.get());
    }

    /** Verifies: JBLM-REC-009, JBLM-REC-010, JBLM-REC-011. */
    @Test void trimsNestedStackAtBoundaries() {
        NDC.push("base-91"); NDC.push("mid-92"); NDC.push("top-93");
        NDC.trimTo(1);
        assertEquals(1, NDC.getDepth());
        assertEquals("base-91", NDC.get());
        NDC.clear();
        assertEquals(0, NDC.getDepth());
        assertEquals("", NDC.pop());
    }

    /** Verifies: JBLM-REC-013, JBLM-REC-019, JBLM-REC-020. */
    @Test void formatsMessagesAccordingToSelectedStyle() {
        ExtLogRecord record = new ExtLogRecord(java.util.logging.Level.INFO, "item {0}", (ExtLogRecord.FormatStyle) null, "caller.Type");
        record.setParameters(new Object[] {"A37"});
        assertEquals(ExtLogRecord.FormatStyle.MESSAGE_FORMAT, record.getFormatStyle());
        assertEquals("item A37", record.getFormattedMessage());
        record.setMessage("count=%02d", ExtLogRecord.FormatStyle.PRINTF);
        record.setParameters(new Object[] {7});
        assertEquals("count=07", record.getFormattedMessage());
        record.setMessage("literal {0}", ExtLogRecord.FormatStyle.NO_FORMAT);
        assertEquals("literal {0}", record.getFormattedMessage());
    }

    /** Verifies: JBLM-REC-014. */
    @Test void wrapsPlainRecordsWhilePreservingPublicFields() {
        LogRecord plain = new LogRecord(java.util.logging.Level.WARNING, "wrapped-219");
        plain.setLoggerName("plain.channel");
        plain.setSequenceNumber(812L);
        ExtLogRecord wrapped = ExtLogRecord.wrap(plain);
        assertEquals("wrapped-219", wrapped.getMessage());
        assertEquals("plain.channel", wrapped.getLoggerName());
        assertEquals(812L, wrapped.getSequenceNumber());
        assertSame(wrapped, ExtLogRecord.wrap(wrapped));
        assertNull(ExtLogRecord.wrap(null));
    }

    /** Verifies: JBLM-REC-015, JBLM-REC-018. */
    @Test void freezesMdcAndReturnsIndependentRecordCopies() {
        MDC.put("frozen-key", "before-44");
        ExtLogRecord record = new ExtLogRecord(java.util.logging.Level.INFO, "freeze", "caller.Type");
        record.copyMdc();
        MDC.put("frozen-key", "after-45");
        Map<String, String> copy = record.getMdcCopy();
        copy.put("frozen-key", "changed-copy");
        assertEquals("before-44", record.getMdc("frozen-key"));
        assertEquals("after-45", MDC.get("frozen-key"));
    }

    /** Verifies: JBLM-REC-017, JBLM-REC-018, JBLM-REC-023. */
    @Test void normalizesRecordMdcAndUpdatesPublicFields() {
        Map<Object, Object> source = new HashMap<>();
        source.put(87, "numeric-key"); source.put("amount", 451); source.put(null, "ignored"); source.put("nil", null);
        ExtLogRecord record = new ExtLogRecord(java.util.logging.Level.INFO, "fields", "caller.Type");
        record.setMdc(source);
        record.setMarker("marker-18"); record.setThreadName("thread-63"); record.setHostName("host-22");
        record.setProcessName("proc-61"); record.setProcessId(4061); record.setNdc("n-17"); record.setLongThreadID(9007);
        assertEquals(Map.of("87", "numeric-key", "amount", "451"), record.getMdcCopy());
        assertEquals("marker-18", record.getMarker());
        assertEquals("thread-63", record.getThreadName());
        assertEquals(4061, record.getProcessId());
        assertEquals(9007, record.getLongThreadID());
    }
}
