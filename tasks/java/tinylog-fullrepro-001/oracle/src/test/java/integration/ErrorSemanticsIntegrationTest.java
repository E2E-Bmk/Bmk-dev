package integration;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.URISyntaxException;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Collection;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Properties;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.tinylog.Level;
import org.tinylog.configuration.Configuration;
import org.tinylog.core.LogEntry;
import org.tinylog.core.LogEntryValue;
import org.tinylog.core.TinylogLoggingProvider;
import org.tinylog.pattern.FormatPatternParser;
import org.tinylog.pattern.Token;
import org.tinylog.writers.FileWriter;
import org.tinylog.writers.Writer;

import support.OracleSupport;

import static org.junit.jupiter.api.Assertions.*;

public class ErrorSemanticsIntegrationTest {
    @TempDir Path tempDir;

    /**
     * Verifies: TINY-CONF-005, TINY-CONF-006, TINY-ERR-001, TINY-STATE-001.
     * Seam: config interaction
     * Depends-On: fileWriterRequiresFile, messageProjectionPreservesInput
     */
    @Test void providerFreezeRejectsLaterConfigurationMutation() throws Exception {
        Properties observed = runScenario("freeze", scenarioDirectory("freeze"));
        assertEquals("true", observed.getProperty("mutationRejected"));
    }

    /**
     * Verifies: TINY-WRITE-018, TINY-WRITE-020, TINY-ERR-004, TINY-CVI-009.
     * Seam: lifecycle crossing
     * Depends-On: fileWriterRequiresFile, messageProjectionPreservesInput
     */
    @Test void unsupportedCharsetFallsBackToJvmDefault() throws Exception {
        Path file = tempDir.resolve("charset-fallback.log");
        FileWriter writer = new FileWriter(OracleSupport.properties(
                "file", file.toString(), "format", "{message-only}", "charset", "x-no-such-charset-79"));
        writer.write(OracleSupport.entry("fallback-text"));
        writer.close();
        byte[] expected = ("fallback-text" + System.lineSeparator()).getBytes(Charset.defaultCharset());
        assertArrayEquals(expected, Files.readAllBytes(file));
    }

    /**
     * Verifies: TINY-FMT-008, TINY-FMT-018, TINY-ERR-006.
     * Seam: protocol handoff
     * Depends-On: messageProjectionPreservesInput
     */
    @Test void invalidPatternStyleStillRendersEntryWithoutThatStyle() {
        Token token = new FormatPatternParser(null).parse("{message-only|min-size=invalid}");
        StringBuilder rendered = new StringBuilder();
        token.render(OracleSupport.entry("unstyled-83"), rendered);
        assertEquals("unstyled-83", rendered.toString());
    }

    /**
     * Verifies: TINY-WRITE-001, TINY-WRITE-003, TINY-ERR-007.
     * Seam: lifecycle crossing
     * Depends-On: fileWriterRequiresFile, messageProjectionPreservesInput
     */
    @Test void directWriteAfterClosedResourcePropagatesIoFailure() throws Exception {
        Path file = tempDir.resolve("closed-writer.log");
        FileWriter writer = new FileWriter(OracleSupport.properties(
                "file", file.toString(), "format", "{message-only}"));
        writer.close();
        assertThrows(IOException.class, () -> writer.write(OracleSupport.entry("must-fail")));
    }

    /**
     * Verifies: TINY-CONF-025, TINY-CONF-026, TINY-ERR-009.
     * Seam: lifecycle crossing
     * Depends-On: fileWriterRequiresFile, messageProjectionPreservesInput
     */
    @Test void interruptedAsynchronousShutdownPropagatesInterruption() throws Exception {
        Properties observed = runScenario("interrupt", scenarioDirectory("interrupt"));
        assertEquals("true", observed.getProperty("interrupted"));
    }

    /**
     * Verifies: TINY-WRITE-004, TINY-ERR-008, TINY-CVI-001.
     * Seam: error propagation
     * Depends-On: messageProjectionPreservesInput, fileWriterRequiresFile
     */
    @Test void providerWriterFailureDoesNotBlockHealthyWriter() throws Exception {
        Path directory = scenarioDirectory("writer-failure");
        Properties observed = runScenario("writer-failure", directory);
        assertAll(
                () -> assertEquals("2", observed.getProperty("selectedWriters")),
                () -> assertTrue(text(directory.resolve("healthy.log")).contains("survives-failure")));
    }

    private Path scenarioDirectory(String name) throws Exception {
        Path directory = tempDir.resolve(name);
        Files.createDirectories(directory);
        return directory;
    }

    private Properties runScenario(String scenario, Path directory) throws Exception {
        String java = Paths.get(System.getProperty("java.home"), "bin", "java").toString();
        String classpath = String.join(File.pathSeparator,
                location(ErrorSemanticsIntegrationTest.class),
                location(TinylogLoggingProvider.class),
                location(Configuration.class));
        Process process = new ProcessBuilder(java, "-cp", classpath,
                ErrorScenario.class.getName(), scenario, directory.toString())
                .redirectErrorStream(true)
                .start();
        String output;
        try (InputStream input = process.getInputStream();
             ByteArrayOutputStream bytes = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[256];
            for (int read; (read = input.read(buffer)) >= 0;) {
                bytes.write(buffer, 0, read);
            }
            output = new String(bytes.toByteArray(), StandardCharsets.UTF_8);
        }
        assertEquals(0, process.waitFor(), output);
        Properties observed = new Properties();
        try (InputStream input = Files.newInputStream(directory.resolve("observed.properties"))) {
            observed.load(input);
        }
        return observed;
    }

    private static String location(Class<?> type) throws URISyntaxException {
        return Paths.get(type.getProtectionDomain().getCodeSource().getLocation().toURI()).toString();
    }

    private static String text(Path file) throws Exception {
        return new String(Files.readAllBytes(file), StandardCharsets.UTF_8);
    }

    /** Executes configuration-freezing error workflows in an isolated JVM. */
    public static final class ErrorScenario {
        private ErrorScenario() { }

        public static void main(String[] arguments) throws Exception {
            String scenario = arguments[0];
            Path directory = Paths.get(arguments[1]);
            Properties observed = new Properties();
            if ("freeze".equals(scenario)) {
                runFreeze(directory, observed);
            } else if ("interrupt".equals(scenario)) {
                runInterruptedShutdown(directory, observed);
            } else if ("writer-failure".equals(scenario)) {
                runWriterFailure(directory, observed);
            } else {
                throw new IllegalArgumentException("Unknown scenario");
            }
            try (OutputStream output = Files.newOutputStream(directory.resolve("observed.properties"))) {
                observed.store(output, null);
            }
        }

        private static void runFreeze(Path directory, Properties observed) throws Exception {
            Configuration.replace(singleFileConfiguration(directory.resolve("freeze.log"), false));
            TinylogLoggingProvider provider = new TinylogLoggingProvider();
            boolean rejected = false;
            try {
                Configuration.set("level", "error");
            } catch (UnsupportedOperationException expected) {
                rejected = true;
            } finally {
                provider.shutdown();
            }
            observed.setProperty("mutationRejected", Boolean.toString(rejected));
        }

        private static void runInterruptedShutdown(Path directory, Properties observed) throws Exception {
            Configuration.replace(singleFileConfiguration(directory.resolve("async.log"), true));
            TinylogLoggingProvider provider = new TinylogLoggingProvider();
            provider.log(ErrorScenario.class.getName(), null, Level.INFO,
                    null, null, "queued", new Object[0]);
            boolean interrupted = false;
            Thread.currentThread().interrupt();
            try {
                provider.shutdown();
            } catch (InterruptedException expected) {
                interrupted = true;
            } finally {
                Thread.interrupted();
                provider.shutdown();
            }
            observed.setProperty("interrupted", Boolean.toString(interrupted));
        }

        private static void runWriterFailure(Path directory, Properties observed) throws Exception {
            Map<String, String> values = singleFileConfiguration(directory.resolve("healthy.log"), false);
            values.put("writerBad", FailingWriter.class.getName());
            Configuration.replace(values);
            TinylogLoggingProvider provider = new TinylogLoggingProvider();
            Collection<Writer> writers = provider.getWriters(null, Level.INFO);
            observed.setProperty("selectedWriters", Integer.toString(writers.size()));
            provider.log(ErrorScenario.class.getName(), null, Level.INFO,
                    null, null, "survives-failure", new Object[0]);
            for (Writer writer : writers) {
                writer.flush();
            }
            provider.shutdown();
        }

        private static Map<String, String> singleFileConfiguration(Path file, boolean asynchronous) {
            Map<String, String> values = new LinkedHashMap<>();
            values.put("writer", "file");
            values.put("writer.file", file.toString());
            values.put("writer.format", "{message-only}");
            values.put("level", "trace");
            values.put("writingthread", Boolean.toString(asynchronous));
            return values;
        }
    }

    /** Public failing writer used only through the configured Writer contract. */
    public static final class FailingWriter implements Writer {
        public FailingWriter() { }
        public FailingWriter(Map<String, String> properties) { }

        @Override public Collection<LogEntryValue> getRequiredLogEntryValues() {
            return Collections.singleton(LogEntryValue.MESSAGE);
        }

        @Override public void write(LogEntry logEntry) throws IOException {
            throw new IOException("intentional public writer failure");
        }

        @Override public void flush() { }
        @Override public void close() { }
    }
}
