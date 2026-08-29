package integration;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.stream.Collectors;
import java.util.zip.GZIPInputStream;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.tinylog.converters.FileConverter;
import org.tinylog.converters.GzipFileConverter;
import org.tinylog.path.DynamicSegment;
import org.tinylog.policies.DynamicPolicy;
import org.tinylog.writers.RollingFileWriter;

import support.OracleSupport;

import static org.junit.jupiter.api.Assertions.*;

class RollingPolicyConverterIntegrationTest {
    @TempDir Path tempDir;

    /**
     * Verifies: TINY-ROLL-005, TINY-ROLL-006, TINY-ROLL-016.
     * Seam: state consistency
     * Depends-On: newDynamicPolicyAcceptsEntry
     */
    @Test void dynamicTextAndExplicitPolicyResetRemainSeparate() {
        String previous = DynamicSegment.getText();
        try {
            DynamicPolicy policy = new DynamicPolicy();
            assertTrue(policy.continueCurrentFile(new byte[] {1}));
            DynamicSegment.setText("integration-blue");
            assertEquals("integration-blue", DynamicSegment.getText());
            assertTrue(policy.continueCurrentFile(new byte[] {2}));
            DynamicPolicy.setReset();
            assertFalse(policy.continueCurrentFile(new byte[] {3}));
            policy.reset();
            assertTrue(policy.continueCurrentFile(new byte[] {4}));
        } finally {
            DynamicSegment.setText(previous);
        }
    }

    /**
     * Verifies: TINY-ROLL-001, TINY-ROLL-002, TINY-ROLL-018, TINY-CVI-005, TINY-CVI-009.
     * Seam: lifecycle crossing
     * Depends-On: messageProjectionPreservesInput, startupAcceptsCurrentEntry, rollingWriterRequiresFile
     */
    @Test void rollingCountPathPersistsFormattedEntryInFirstFile() throws Exception {
        Path pattern = tempDir.resolve("count-{count}.log");
        RollingFileWriter writer = new RollingFileWriter(OracleSupport.properties("file", pattern.toString(), "format", "{message-only}"));
        writer.write(OracleSupport.entry("count-zero"));
        writer.close();
        assertEquals("count-zero" + System.lineSeparator(), text(tempDir.resolve("count-0.log")));
    }

    /**
     * Verifies: TINY-ROLL-010, TINY-ROLL-011, TINY-ROLL-013, TINY-CVI-008, TINY-CVI-009.
     * Seam: lifecycle crossing
     * Depends-On: sizeAcceptsEntryBelowLimit, sizeRejectsEntryAboveLimit, messageProjectionPreservesInput
     */
    @Test void sizePolicyRollsPendingEntryIntoNextCountFile() throws Exception {
        Path pattern = tempDir.resolve("sized-{count}.log");
        RollingFileWriter writer = new RollingFileWriter(OracleSupport.properties(
                "file", pattern.toString(), "format", "{message-only}", "policies", "size: 10 bytes"));
        writer.write(OracleSupport.entry("first"));
        writer.write(OracleSupport.entry("second"));
        writer.close();
        assertAll(
                () -> assertEquals("first" + System.lineSeparator(), text(tempDir.resolve("sized-0.log"))),
                () -> assertEquals("second" + System.lineSeparator(), text(tempDir.resolve("sized-1.log"))));
    }

    /**
     * Verifies: TINY-ROLL-023, TINY-ROLL-024, TINY-CVI-008, TINY-CVI-009.
     * Seam: lifecycle crossing
     * Depends-On: messageProjectionPreservesInput, rollingWriterRequiresFile
     */
    @Test void gzipConverterLifecyclePreservesBytesInCompressedProjection() throws Exception {
        Path file = tempDir.resolve("closed.log");
        byte[] bytes = "converter-payload".getBytes(StandardCharsets.UTF_8);
        Files.write(file, bytes);
        FileConverter converter = new GzipFileConverter();
        assertEquals(".gz", converter.getBackupSuffix());
        converter.open(file.toString());
        assertArrayEquals(bytes, converter.write(bytes));
        converter.close();
        converter.shutdown();
        Path gzip = tempDir.resolve("closed.log.gz");
        assertAll(
                () -> assertTrue(Files.exists(gzip)),
                () -> assertEquals("converter-payload", gunzip(gzip)));
    }

    private static String text(Path file) throws Exception {
        return new String(Files.readAllBytes(file), StandardCharsets.UTF_8);
    }

    private static String gunzip(Path file) throws Exception {
        try (InputStream input = new GZIPInputStream(Files.newInputStream(file));
             ByteArrayOutputStream output = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[128];
            for (int read; (read = input.read(buffer)) >= 0;) {
                output.write(buffer, 0, read);
            }
            return new String(output.toByteArray(), StandardCharsets.UTF_8);
        }
    }
}
