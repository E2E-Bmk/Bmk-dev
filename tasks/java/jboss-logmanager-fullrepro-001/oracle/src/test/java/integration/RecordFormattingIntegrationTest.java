package integration;

import static org.junit.jupiter.api.Assertions.*;

import java.util.Map;
import org.jboss.logmanager.ExtLogRecord;
import org.jboss.logmanager.Level;
import org.jboss.logmanager.LogContext;
import org.jboss.logmanager.Logger;
import org.jboss.logmanager.MDC;
import org.jboss.logmanager.NDC;
import org.jboss.logmanager.filters.LevelChangingFilter;
import org.jboss.logmanager.filters.SubstituteFilter;
import org.jboss.logmanager.formatters.JsonFormatter;
import org.jboss.logmanager.formatters.PatternFormatter;
import org.jboss.logmanager.formatters.StructuredFormatter;
import org.jboss.logmanager.formatters.XmlFormatter;
import org.jboss.logmanager.handlers.OutputStreamHandler;
import org.jboss.logmanager.handlers.QueueHandler;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;

/** Integration checks across diagnostic snapshots, filters, and formatter projections. */
class RecordFormattingIntegrationTest {
    @AfterEach void clearDiagnosticState() { MDC.clear(); NDC.clear(); }
    private static ExtLogRecord record(String message) {
        ExtLogRecord record = new ExtLogRecord(Level.INFO, message, ExtLogRecord.FormatStyle.NO_FORMAT, "caller.Type");
        record.setLoggerName("record.integration"); record.setThreadName("record-thread"); record.setHostName(""); record.setProcessName(""); record.setProcessId(-1);
        return record;
    }

    /**
     * Verifies: JBLM-INV-004, JBLM-REC-015, JBLM-FMT-005.
     * Seam: state consistency
     * Depends-On: freezesMdcAndReturnsIndependentRecordCopies, patternFormatterRendersMdcNdcAndLineSeparator
     */
    @Test void frozenDiagnosticsAgreeWithPatternProjection() {
        MDC.put("rid", "freeze-211"); NDC.push("nested-212"); ExtLogRecord record = record("payload-213"); record.copyAll();
        MDC.put("rid", "later-214"); NDC.clear();
        String text = new PatternFormatter("%X{rid}|%x|%m").format(record);
        assertEquals("freeze-211|nested-212|payload-213", text);
        assertEquals("freeze-211", record.getMdc("rid")); assertEquals("nested-212", record.getNdc());
    }

    /**
     * Verifies: JBLM-INV-004, JBLM-FMT-018, JBLM-FMT-020, JBLM-FMT-024.
     * Seam: state consistency
     * Depends-On: freezesMdcAndReturnsIndependentRecordCopies, jsonFormatterProjectsValuesAndDelimiterPolicy, xmlFormatterControlsNamespaceProjection
     */
    @Test void frozenMdcAgreesAcrossJsonAndXml() {
        ExtLogRecord record = record("structured-215"); record.setMdc(Map.of("tenant", "blue-216")); record.setNdc("scope-217");
        String json = new JsonFormatter().format(record); String xml = new XmlFormatter().format(record);
        assertTrue(json.contains("\"tenant\":\"blue-216\"")); assertTrue(json.contains("\"ndc\":\"scope-217\""));
        assertTrue(xml.contains("<tenant>blue-216</tenant>")); assertTrue(xml.contains("<ndc>scope-217</ndc>"));
    }

    /**
     * Verifies: JBLM-INV-004, JBLM-STA-001, JBLM-HND-022.
     * Seam: lifecycle crossing
     * Depends-On: freezesMdcAndReturnsIndependentRecordCopies, queueHandlerReturnsIndependentFormattedSnapshots
     */
    @Test void queuedSnapshotRetainsFrozenDiagnosticValue() {
        MDC.put("queue-key", "before-218"); ExtLogRecord record = record("queued-219"); record.copyMdc();
        QueueHandler queue = new QueueHandler(3); queue.publish(record); MDC.put("queue-key", "after-220");
        assertEquals("before-218", queue.getQueue()[0].getMdc("queue-key"));
        assertEquals("after-220", MDC.get("queue-key"));
    }

    /**
     * Verifies: JBLM-INV-005, JBLM-FLT-009, JBLM-FMT-005.
     * Seam: protocol handoff
     * Depends-On: levelChangingFilterMutatesAndAccepts, patternFormatterRendersCoreWords
     */
    @Test void levelMutationFlowsIntoPatternText() {
        ExtLogRecord record = record("promoted-221"); new LevelChangingFilter(Level.ERROR).isLoggable(record);
        assertEquals("ERROR|promoted-221", new PatternFormatter("%p|%m").format(record));
    }

    /**
     * Verifies: JBLM-INV-005, JBLM-FLT-011, JBLM-FLT-012, JBLM-FMT-018, JBLM-FMT-024.
     * Seam: protocol handoff
     * Depends-On: substituteFilterSelectsFirstOrAllMatches, jsonFormatterProjectsValuesAndDelimiterPolicy
     */
    @Test void substitutedMessageFlowsIntoJson() {
        ExtLogRecord record = record("secret-222 and secret-223"); new SubstituteFilter("secret-[0-9]+", "masked", true).isLoggable(record);
        String json = new JsonFormatter().format(record);
        assertTrue(json.contains("\"message\":\"masked and masked\""));
        assertSame(ExtLogRecord.FormatStyle.NO_FORMAT, record.getFormatStyle());
    }

    /**
     * Verifies: JBLM-INV-005, JBLM-CTX-022, JBLM-HND-013.
     * Seam: protocol handoff
     * Depends-On: substituteFilterSelectsFirstOrAllMatches, outputStreamHandlerUsesUpdatedCharsetForLaterBytes
     */
    @Test void loggerFilterMutationReachesHandlerDestination() throws Exception {
        try (LogContext context = LogContext.create(true)) {
            java.io.ByteArrayOutputStream bytes = new java.io.ByteArrayOutputStream();
            OutputStreamHandler handler = new OutputStreamHandler(bytes, new PatternFormatter("%p:%m"));
            Logger logger = context.getLogger("mutate.delivery"); logger.setUseParentHandlers(false); logger.setLevel(Level.TRACE);
            logger.setFilter(new LevelChangingFilter(Level.FATAL)); logger.addHandler(handler); logger.info("promote-224"); handler.flush();
            assertEquals("FATAL:promote-224", bytes.toString(java.nio.charset.StandardCharsets.UTF_8));
        }
    }

    /**
     * Verifies: JBLM-INV-009, JBLM-FMT-015, JBLM-FMT-019, JBLM-FMT-020.
     * Seam: config interaction
     * Depends-On: structuredFormatterAppliesTimeMetadataAndRejectsInvalidPolicy, xmlFormatterControlsNamespaceProjection
     */
    @Test void metadataPolicyAgreesAcrossJsonAndXml() {
        JsonFormatter jsonFormatter = new JsonFormatter(); XmlFormatter xmlFormatter = new XmlFormatter();
        jsonFormatter.setMetaData("site=harbor-225"); xmlFormatter.setMetaData("site=harbor-225");
        String json = jsonFormatter.format(record("meta-226")); String xml = xmlFormatter.format(record("meta-226"));
        assertTrue(json.contains("\"site\":\"harbor-225\"")); assertTrue(xml.contains("harbor-225"));
    }

    /**
     * Verifies: JBLM-INV-009, JBLM-FMT-016, JBLM-FMT-018, JBLM-FMT-020, JBLM-FMT-024.
     * Seam: config interaction
     * Depends-On: jsonFormatterProjectsValuesAndDelimiterPolicy, xmlFormatterControlsNamespaceProjection
     */
    @Test void messageKeyOverrideAgreesAcrossJsonAndXmlSyntax() {
        Map<StructuredFormatter.Key, String> keys = Map.of(StructuredFormatter.Key.MESSAGE, "payloadField");
        String json = new JsonFormatter(keys).format(record("override-227")); String xml = new XmlFormatter(keys).format(record("override-227"));
        assertTrue(json.contains("\"payloadField\":\"override-227\""));
        assertTrue(xml.contains("<payloadField>override-227</payloadField>"));
    }
}
