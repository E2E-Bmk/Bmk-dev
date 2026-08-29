package integration;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

import com.github.cliftonlabs.json_simple.Jsoner;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.tinylog.core.LogEntryValue;
import org.tinylog.writers.FileWriter;
import org.tinylog.writers.JsonWriter;

import support.OracleSupport;

import static org.junit.jupiter.api.Assertions.*;

class FileJsonWriterIntegrationTest {
    @TempDir Path tempDir;

    /**
     * Verifies: TINY-WRITE-013, TINY-WRITE-014, TINY-WRITE-007, TINY-CVI-005, TINY-CVI-009.
     * Seam: lifecycle crossing
     * Depends-On: messageProjectionPreservesInput, fileWriterRequiresFile
     */
    @Test void fileWriterCreatesParentsAndPersistsRenderedEntry() throws Exception {
        Path file = tempDir.resolve("nested/deeper/events.log");
        FileWriter writer = new FileWriter(OracleSupport.properties("file", file.toString(), "format", "{level}|{message-only}"));
        writer.write(OracleSupport.entry("ready-31"));
        writer.close();
        assertEquals("INFO|ready-31" + System.lineSeparator(), text(file));
    }

    /**
     * Verifies: TINY-WRITE-015, TINY-WRITE-007, TINY-CVI-009.
     * Seam: lifecycle crossing
     * Depends-On: messageProjectionPreservesInput, fileWriterRequiresFile
     */
    @Test void fileWriterTruncatesExistingProjectionByDefault() throws Exception {
        Path file = tempDir.resolve("truncate.log");
        Files.write(file, "stale\n".getBytes(StandardCharsets.UTF_8));
        FileWriter writer = new FileWriter(OracleSupport.properties("file", file.toString(), "format", "{message-only}"));
        writer.write(OracleSupport.entry("fresh"));
        writer.close();
        assertEquals("fresh" + System.lineSeparator(), text(file));
    }

    /**
     * Verifies: TINY-WRITE-016, TINY-WRITE-007, TINY-CVI-005.
     * Seam: lifecycle crossing
     * Depends-On: messageProjectionPreservesInput, fileWriterRequiresFile
     */
    @Test void fileWriterAppendContinuesExistingProjection() throws Exception {
        Path file = tempDir.resolve("append.log");
        Files.write(file, "first\n".getBytes(StandardCharsets.UTF_8));
        FileWriter writer = new FileWriter(OracleSupport.properties("file", file.toString(), "format", "{message-only}", "append", "true"));
        writer.write(OracleSupport.entry("second"));
        writer.close();
        assertEquals("first\nsecond" + System.lineSeparator(), text(file));
    }

    /**
     * Verifies: TINY-WRITE-017, TINY-CVI-009.
     * Seam: lifecycle crossing
     * Depends-On: messageProjectionPreservesInput, fileWriterRequiresFile
     */
    @Test void bufferedFileWriterMakesEntryDurableOnFlush() throws Exception {
        Path file = tempDir.resolve("buffered.log");
        FileWriter writer = new FileWriter(OracleSupport.properties("file", file.toString(), "format", "{message-only}", "buffered", "true"));
        writer.write(OracleSupport.entry("flushed"));
        writer.flush();
        assertEquals("flushed" + System.lineSeparator(), text(file));
        writer.close();
    }

    /**
     * Verifies: TINY-WRITE-022, TINY-WRITE-024, TINY-WRITE-027, TINY-CVI-002, TINY-CVI-006.
     * Seam: protocol handoff
     * Depends-On: messageProjectionPreservesInput, levelProjectionPreservesInput, jsonWriterRequiresFile
     */
    @Test void jsonArrayFieldsAgreeWithEntryProjections() throws Exception {
        Path file = tempDir.resolve("fields.json");
        JsonWriter writer = new JsonWriter(OracleSupport.properties("file", file.toString(), "field.message", "{message-only}", "field.level", "{level}"));
        assertAll(
                () -> assertTrue(writer.getRequiredLogEntryValues().contains(LogEntryValue.MESSAGE)),
                () -> assertTrue(writer.getRequiredLogEntryValues().contains(LogEntryValue.LEVEL)));
        writer.write(OracleSupport.entry("json-value"));
        writer.close();
        String json = text(file).trim();
        Object parsed = Jsoner.deserialize(json);
        assertTrue(parsed instanceof List);
        List<?> array = (List<?>) parsed;
        assertEquals(1, array.size());
        assertTrue(array.get(0) instanceof Map);
        Map<?, ?> fields = (Map<?, ?>) array.get(0);
        assertAll(
                () -> assertEquals("json-value", fields.get("message")),
                () -> assertEquals("INFO", fields.get("level")));
    }

    /**
     * Verifies: TINY-WRITE-023, TINY-CVI-006.
     * Seam: protocol handoff
     * Depends-On: messageProjectionPreservesInput, jsonWriterRequiresFile
     */
    @Test void bareAndBracedJsonPlaceholdersAgree() throws Exception {
        Path file = tempDir.resolve("optional-braces.json");
        JsonWriter writer = new JsonWriter(OracleSupport.properties("file", file.toString(), "field.bare", "message-only", "field.braced", "{message-only}"));
        writer.write(OracleSupport.entry("same-value"));
        writer.close();
        Object parsed = Jsoner.deserialize(text(file));
        assertTrue(parsed instanceof List);
        List<?> array = (List<?>) parsed;
        assertEquals(1, array.size());
        assertTrue(array.get(0) instanceof Map);
        Map<?, ?> fields = (Map<?, ?>) array.get(0);
        assertAll(
                () -> assertEquals("same-value", fields.get("bare")),
                () -> assertEquals("same-value", fields.get("braced")));
    }

    /**
     * Verifies: TINY-WRITE-026, TINY-WRITE-030, TINY-CVI-006.
     * Seam: protocol handoff
     * Depends-On: messageProjectionPreservesInput, jsonWriterRequiresFile
     */
    @Test void jsonWriterEscapesEntryControlCharacters() throws Exception {
        Path file = tempDir.resolve("escaped.json");
        JsonWriter writer = new JsonWriter(OracleSupport.properties("file", file.toString(), "field.value", "{message-only}"));
        writer.write(OracleSupport.entry("slash\\ quote\" line\n tab\t back\b form\f return\r"));
        writer.close();
        String json = text(file);
        assertAll(
                () -> assertTrue(json.contains("slash\\\\ quote\\\" line\\n tab\\t back\\b form\\f return\\n")),
                () -> assertFalse(json.contains("return\\r")));
    }

    /**
     * Verifies: TINY-WRITE-025, TINY-CVI-006, TINY-CVI-009.
     * Seam: lifecycle crossing
     * Depends-On: messageProjectionPreservesInput, jsonWriterRequiresFile
     */
    @Test void ldjsonWritesOneEntryProjectionPerLine() throws Exception {
        Path file = tempDir.resolve("events.ldjson");
        JsonWriter writer = new JsonWriter(OracleSupport.properties("file", file.toString(), "format", "LDJSON", "field.value", "{message-only}"));
        writer.write(OracleSupport.entry("first"));
        writer.write(OracleSupport.entry("second"));
        writer.close();
        String[] lines = text(file).trim().split("\\R");
        Object first = Jsoner.deserialize(lines[0]);
        Object second = Jsoner.deserialize(lines[1]);
        assertTrue(first instanceof Map);
        assertTrue(second instanceof Map);
        assertAll(
                () -> assertEquals(2, lines.length),
                () -> assertEquals("first", ((Map<?, ?>) first).get("value")),
                () -> assertEquals("second", ((Map<?, ?>) second).get("value")));
    }

    /**
     * Verifies: TINY-WRITE-028, TINY-CVI-002, TINY-CVI-009.
     * Seam: lifecycle crossing
     * Depends-On: messageProjectionPreservesInput, jsonWriterRequiresFile
     */
    @Test void zeroFieldJsonWriterPersistsEmptyObjectEnvelope() throws Exception {
        Path file = tempDir.resolve("empty-object.json");
        JsonWriter writer = new JsonWriter(Map.of("file", file.toString()));
        assertTrue(writer.getRequiredLogEntryValues().isEmpty());
        writer.write(OracleSupport.entry("ignored"));
        writer.close();
        assertEquals("[{}]", text(file).replaceAll("\\s+", ""));
    }

    /**
     * Verifies: TINY-WRITE-027, TINY-CVI-009.
     * Seam: lifecycle crossing
     * Depends-On: messageProjectionPreservesInput, jsonWriterRequiresFile
     */
    @Test void jsonFlushLeavesACompleteReadableArray() throws Exception {
        Path file = tempDir.resolve("flush.json");
        JsonWriter writer = new JsonWriter(OracleSupport.properties("file", file.toString(), "field.value", "{message-only}"));
        writer.write(OracleSupport.entry("before-flush"));
        writer.flush();
        String flushed = text(file).trim();
        assertAll(
                () -> assertTrue(flushed.startsWith("[")),
                () -> assertTrue(flushed.endsWith("]")),
                () -> assertTrue(flushed.contains("before-flush")));
        writer.close();
    }

    private static String text(Path file) throws Exception {
        return new String(Files.readAllBytes(file), StandardCharsets.UTF_8);
    }
}
