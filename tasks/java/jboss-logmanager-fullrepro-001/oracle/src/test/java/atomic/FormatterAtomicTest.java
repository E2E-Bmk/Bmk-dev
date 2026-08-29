package atomic;

import static org.junit.jupiter.api.Assertions.*;

import java.time.DateTimeException;
import org.jboss.logmanager.ExtLogRecord;
import org.jboss.logmanager.Level;
import org.jboss.logmanager.formatters.JsonFormatter;
import org.jboss.logmanager.formatters.PatternFormatter;
import org.jboss.logmanager.formatters.XmlFormatter;
import org.junit.jupiter.api.Test;

/** Atomic checks for pattern, JSON, and XML formatting policy. */
class FormatterAtomicTest {
    private static ExtLogRecord record(String message) {
        ExtLogRecord record = new ExtLogRecord(Level.WARN, message, ExtLogRecord.FormatStyle.NO_FORMAT, "caller.Type");
        record.setLoggerName("service.delta.worker"); record.setThreadName("thread-71"); record.setSequenceNumber(375);
        record.setHostName(""); record.setProcessName(""); record.setProcessId(-1); record.setNdc("nested-42");
        return record;
    }

    /** Verifies: JBLM-FMT-003, JBLM-FMT-005. */
    @Test void patternFormatterRendersCoreWords() {
        PatternFormatter formatter = new PatternFormatter("%p|%c{2}|%t|%m|%%");
        assertEquals("%p|%c{2}|%t|%m|%%", formatter.getPattern());
        assertEquals("WARN|delta.worker|thread-71|payload-81|%", formatter.format(record("payload-81")));
    }

    /** Verifies: JBLM-FMT-005. */
    @Test void patternFormatterRendersMdcNdcAndLineSeparator() {
        ExtLogRecord record = record("context-82");
        record.setMdc(java.util.Map.of("request", "req-553"));
        String formatted = new PatternFormatter("%X{request}|%x|%m%n").format(record);
        assertEquals("req-553|nested-42|context-82" + System.lineSeparator(), formatted);
    }

    /** Verifies: JBLM-FMT-006. */
    @Test void patternFormatterHonorsWidthAndAlignment() {
        ExtLogRecord record = record("xy");
        assertEquals("    xy|xy    ", new PatternFormatter("%6m|%-6m").format(record));
    }

    /** Verifies: JBLM-FMT-004. */
    @Test void patternFormatterHandlesNullAndIncompletePatterns() {
        PatternFormatter formatter = new PatternFormatter("%m");
        formatter.setPattern(null);
        assertEquals("", formatter.format(record("hidden-83")));
        formatter.setPattern("fixed:%m");
        assertEquals("fixed:shown-84", formatter.format(record("shown-84")));
    }

    /** Verifies: JBLM-FMT-008, JBLM-FMT-009, JBLM-FMT-010, JBLM-FMT-018, JBLM-FMT-019, JBLM-FMT-024. */
    @Test void jsonFormatterProjectsValuesAndDelimiterPolicy() {
        JsonFormatter formatter = new JsonFormatter();
        String compact = formatter.format(record("json-85"));
        assertTrue(compact.contains("\"message\":\"json-85\""));
        assertTrue(compact.contains("\"loggerName\":\"service.delta.worker\""));
        assertFalse(compact.contains("\"hostName\""));
        assertEquals("\n", compact.substring(compact.length() - 1));
        formatter.setRecordDelimiter(null);
        String noDelimiter = formatter.format(record("no-delimiter-86"));
        assertNotEquals("\n", noDelimiter.substring(noDelimiter.length() - 1));
        formatter.setPrettyPrint(true);
        assertTrue(formatter.format(record("pretty-87")).contains("\n"));
    }

    /** Verifies: JBLM-FMT-011, JBLM-FMT-012, JBLM-FMT-013, JBLM-FMT-015, JBLM-FMT-024, JBLM-ERR-008. */
    @Test void structuredFormatterAppliesTimeMetadataAndRejectsInvalidPolicy() {
        JsonFormatter formatter = new JsonFormatter();
        ExtLogRecord timed = record("metadata-88");
        formatter.setDateFormat("XXX"); formatter.setZoneId("UTC"); formatter.setMetaData("region=west-3,ring=blue-6");
        String utcOutput = formatter.format(timed);
        formatter.setZoneId("Asia/Tokyo");
        String tokyoOutput = formatter.format(timed);
        assertTrue(utcOutput.contains("\"timestamp\":\"Z\""));
        assertTrue(tokyoOutput.contains("\"timestamp\":\"+09:00\""));
        assertTrue(utcOutput.contains("\"region\":\"west-3\""));
        assertTrue(utcOutput.contains("\"ring\":\"blue-6\""));
        assertThrows(IllegalArgumentException.class, () -> formatter.setDateFormat("{"));
        assertThrows(DateTimeException.class, () -> formatter.setZoneId("Mars/Olympus"));
    }

    /** Verifies: JBLM-FMT-020, JBLM-FMT-021, JBLM-FMT-022, JBLM-FMT-023, JBLM-FMT-024. */
    @Test void xmlFormatterControlsNamespaceProjection() {
        XmlFormatter formatter = new XmlFormatter();
        assertEquals("urn:jboss:logmanager:formatter:1.0", XmlFormatter.DEFAULT_NAMESPACE);
        assertEquals(XmlFormatter.DEFAULT_NAMESPACE, formatter.getNamespaceUri());
        formatter.setPrintNamespace(true);
        String namespaced = formatter.format(record("xml-89"));
        assertTrue(namespaced.contains("xmlns=\"urn:jboss:logmanager:formatter:1.0\""));
        assertTrue(namespaced.contains("<message>xml-89</message>"));
        formatter.setNamespaceUri(null);
        assertFalse(formatter.format(record("plain-90")).contains("xmlns="));
    }
}
