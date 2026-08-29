package integration;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.URISyntaxException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Collection;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Properties;

import com.github.cliftonlabs.json_simple.Jsoner;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.tinylog.Level;
import org.tinylog.configuration.Configuration;
import org.tinylog.core.LogEntry;
import org.tinylog.core.TinylogContextProvider;
import org.tinylog.core.TinylogLoggingProvider;
import org.tinylog.path.DynamicSegment;
import org.tinylog.pattern.FormatPatternParser;
import org.tinylog.pattern.Token;
import org.tinylog.policies.DynamicPolicy;
import org.tinylog.writers.JsonWriter;
import org.tinylog.writers.Writer;

import support.OracleSupport;

import static org.junit.jupiter.api.Assertions.*;

public class CrossViewQuotaIntegrationTest {
    @TempDir Path tempDir;

    /**
     * Verifies: TINY-CONF-016, TINY-CONF-019, TINY-CONF-021, TINY-CONF-022, TINY-CVI-001.
     * Seam: protocol handoff
     * Depends-On: levelProjectionPreservesInput, messageProjectionPreservesInput, fileWriterRequiresFile
     */
    @Test void taggedAcceptedEntryReachesOnlySelectedWriter() throws Exception {
        Path directory = scenarioDirectory("tagged");
        Properties observed = runScenario("tagged", directory);
        String marker = "selected-blue-47";
        assertAll(
                () -> assertEquals("true", observed.getProperty("enabled")),
                () -> assertEquals("1", observed.getProperty("writers")),
                () -> assertTrue(text(directory.resolve("tagged.log")).contains(marker)),
                () -> assertFalse(text(directory.resolve("untagged.log")).contains(marker)),
                () -> assertFalse(allRollingText(directory).contains(marker)));
    }

    /**
     * Verifies: TINY-CONF-016, TINY-CONF-018, TINY-CONF-021, TINY-CONF-022, TINY-CVI-001.
     * Seam: protocol handoff
     * Depends-On: levelProjectionPreservesInput, messageProjectionPreservesInput, fileWriterRequiresFile
     */
    @Test void untaggedAcceptedEntryReachesOnlySelectedWriter() throws Exception {
        Path directory = scenarioDirectory("untagged");
        Properties observed = runScenario("untagged", directory);
        String marker = "selected-plain-53";
        assertAll(
                () -> assertEquals("true", observed.getProperty("enabled")),
                () -> assertEquals("1", observed.getProperty("writers")),
                () -> assertTrue(text(directory.resolve("untagged.log")).contains(marker)),
                () -> assertFalse(text(directory.resolve("tagged.log")).contains(marker)),
                () -> assertFalse(allRollingText(directory).contains(marker)));
    }

    /**
     * Verifies: TINY-CONF-027, TINY-CONF-028, TINY-FMT-009, TINY-WRITE-022, TINY-CVI-003, TINY-CVI-006.
     * Seam: state consistency
     * Depends-On: putAppearsInMapping, contextProjectionPreservesEntries, jsonWriterRequiresFile
     */
    @Test void contextSnapshotAgreesAcrossTokenAndJson() throws Exception {
        TinylogContextProvider contextProvider = new TinylogContextProvider();
        contextProvider.put("request", "context-61");
        Map<String, String> snapshot = contextProvider.getMapping();
        LogEntry entry = new LogEntry(null, Thread.currentThread(), snapshot,
                "sample.ContextCaller", "issue", "ContextCaller.java", 61,
                "context", Level.INFO, "ignored", null);
        Token token = new FormatPatternParser(null).parse("{context:request}");
        StringBuilder rendered = new StringBuilder();
        token.render(entry, rendered);

        Path jsonFile = tempDir.resolve("context.json");
        JsonWriter writer = new JsonWriter(OracleSupport.properties(
                "file", jsonFile.toString(), "field.request", "{context:request}"));
        writer.write(entry);
        writer.close();
        Object parsed = Jsoner.deserialize(text(jsonFile));
        assertTrue(parsed instanceof java.util.List);
        Object first = ((java.util.List<?>) parsed).get(0);
        assertTrue(first instanceof Map);
        Map<?, ?> json = (Map<?, ?>) first;

        assertAll(
                () -> assertEquals("context-61", snapshot.get("request")),
                () -> assertEquals("context-61", rendered.toString()),
                () -> assertEquals("context-61", json.get("request")));
    }

    /**
     * Verifies: TINY-WF-002, TINY-ROLL-005, TINY-ROLL-006, TINY-ROLL-016, TINY-CVI-007, TINY-CVI-009.
     * Seam: state consistency
     * Depends-On: newDynamicPolicyAcceptsEntry, messageProjectionPreservesInput, rollingWriterRequiresFile
     */
    @Test void dynamicResetMovesInfoEntryWithoutChangingSelection() throws Exception {
        Path directory = scenarioDirectory("dynamic-info");
        Properties observed = runScenario("dynamic-info", directory);
        assertAll(
                () -> assertEquals("true", observed.getProperty("enabledBefore")),
                () -> assertEquals(observed.getProperty("enabledBefore"), observed.getProperty("enabledAfter")),
                () -> assertEquals(observed.getProperty("writersBefore"), observed.getProperty("writersAfter")),
                () -> assertEquals("before-info" + System.lineSeparator(), text(dynamicFile(directory, "info-before-67"))),
                () -> assertEquals("after-info" + System.lineSeparator(), text(dynamicFile(directory, "info-after-67"))));
    }

    /**
     * Verifies: TINY-WF-002, TINY-ROLL-005, TINY-ROLL-006, TINY-ROLL-016, TINY-CVI-007, TINY-CVI-009.
     * Seam: lifecycle crossing
     * Depends-On: newDynamicPolicyAcceptsEntry, messageProjectionPreservesInput, rollingWriterRequiresFile
     */
    @Test void dynamicResetMovesErrorEntryWithoutChangingSelection() throws Exception {
        Path directory = scenarioDirectory("dynamic-error");
        Properties observed = runScenario("dynamic-error", directory);
        assertAll(
                () -> assertEquals("true", observed.getProperty("enabledBefore")),
                () -> assertEquals(observed.getProperty("enabledBefore"), observed.getProperty("enabledAfter")),
                () -> assertEquals(observed.getProperty("writersBefore"), observed.getProperty("writersAfter")),
                () -> assertEquals("before-error" + System.lineSeparator(), text(dynamicFile(directory, "error-before-71"))),
                () -> assertEquals("after-error" + System.lineSeparator(), text(dynamicFile(directory, "error-after-71"))));
    }

    private Path scenarioDirectory(String name) throws Exception {
        Path directory = tempDir.resolve(name);
        Files.createDirectories(directory);
        return directory;
    }

    private Properties runScenario(String scenario, Path directory) throws Exception {
        String java = Paths.get(System.getProperty("java.home"), "bin", "java").toString();
        String classpath = String.join(File.pathSeparator,
                location(CrossViewQuotaIntegrationTest.class),
                location(TinylogLoggingProvider.class),
                location(Configuration.class));
        Process process = new ProcessBuilder(java, "-cp", classpath,
                ProviderScenario.class.getName(), scenario, directory.toString())
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

    private static Path dynamicFile(Path directory, String text) {
        return directory.resolve("dynamic-" + text + "-0.log");
    }

    private static String allRollingText(Path directory) throws Exception {
        StringBuilder all = new StringBuilder();
        try (java.util.stream.Stream<Path> paths = Files.list(directory)) {
            for (Path path : (Iterable<Path>) paths.filter(p -> p.getFileName().toString().startsWith("dynamic-")).filter(Files::isRegularFile)::iterator) {
                all.append(text(path));
            }
        }
        return all.toString();
    }

    private static void flush(Collection<Writer> writers) throws Exception {
        for (Writer writer : writers) {
            writer.flush();
        }
    }

    private static String text(Path file) throws Exception {
        if (!Files.exists(file)) {
            return "";
        }
        return new String(Files.readAllBytes(file), StandardCharsets.UTF_8);
    }

    /** Runs one configuration-frozen provider workflow in its own JVM. */
    public static final class ProviderScenario {
        private ProviderScenario() { }

        public static void main(String[] arguments) throws Exception {
            String scenario = arguments[0];
            Path directory = Paths.get(arguments[1]);
            Map<String, String> configuration = configuration(directory);
            Configuration.replace(configuration);
            TinylogLoggingProvider provider = new TinylogLoggingProvider();
            Properties observed = new Properties();
            try {
                if ("tagged".equals(scenario)) {
                    runSelected(provider, "blue", Level.INFO, "selected-blue-47", observed);
                } else if ("untagged".equals(scenario)) {
                    runSelected(provider, null, Level.WARN, "selected-plain-53", observed);
                } else if ("dynamic-info".equals(scenario)) {
                    runDynamic(provider, Level.INFO, "info-before-67", "info-after-67",
                            "before-info", "after-info", observed);
                } else if ("dynamic-error".equals(scenario)) {
                    runDynamic(provider, Level.ERROR, "error-before-71", "error-after-71",
                            "before-error", "after-error", observed);
                } else {
                    throw new IllegalArgumentException("Unknown scenario");
                }
            } finally {
                provider.shutdown();
            }
            try (OutputStream output = Files.newOutputStream(directory.resolve("observed.properties"))) {
                observed.store(output, null);
            }
        }

        private static Map<String, String> configuration(Path directory) {
            Map<String, String> values = new LinkedHashMap<>();
            values.put("writerBlue", "file");
            values.put("writerBlue.file", directory.resolve("tagged.log").toString());
            values.put("writerBlue.format", "{message-only}");
            values.put("writerBlue.tag", "blue");
            values.put("writerBlue.level", "info");
            values.put("writerPlain", "file");
            values.put("writerPlain.file", directory.resolve("untagged.log").toString());
            values.put("writerPlain.format", "{message-only}");
            values.put("writerPlain.tag", "-");
            values.put("writerPlain.level", "warn");
            values.put("writerRoll", "rolling file");
            values.put("writerRoll.file", directory.resolve("dynamic-{dynamic:bootstrap}-{count}.log").toString());
            values.put("writerRoll.format", "{message-only}");
            values.put("writerRoll.tag", "roll");
            values.put("writerRoll.level", "info");
            values.put("writerRoll.policies", "dynamic");
            values.put("level", "trace");
            values.put("writingthread", "false");
            return values;
        }

        private static void runSelected(TinylogLoggingProvider provider, String tag, Level level,
                                        String marker, Properties observed) throws Exception {
            Collection<Writer> writers = provider.getWriters(tag, level);
            observed.setProperty("enabled", Boolean.toString(provider.isEnabled(ProviderScenario.class.getName(), tag, level)));
            observed.setProperty("writers", Integer.toString(writers.size()));
            provider.log(ProviderScenario.class.getName(), tag, level, null, null, marker, new Object[0]);
            flush(writers);
        }

        private static void runDynamic(TinylogLoggingProvider provider, Level level,
                                       String beforeText, String afterText,
                                       String beforeMessage, String afterMessage,
                                       Properties observed) throws Exception {
            DynamicSegment.setText(beforeText);
            DynamicPolicy.setReset();
            Collection<Writer> beforeWriters = provider.getWriters("roll", level);
            observed.setProperty("enabledBefore", Boolean.toString(provider.isEnabled(ProviderScenario.class.getName(), "roll", level)));
            observed.setProperty("writersBefore", Integer.toString(beforeWriters.size()));
            provider.log(ProviderScenario.class.getName(), "roll", level, null, null, beforeMessage, new Object[0]);
            flush(beforeWriters);

            DynamicSegment.setText(afterText);
            DynamicPolicy.setReset();
            Collection<Writer> afterWriters = provider.getWriters("roll", level);
            observed.setProperty("enabledAfter", Boolean.toString(provider.isEnabled(ProviderScenario.class.getName(), "roll", level)));
            observed.setProperty("writersAfter", Integer.toString(afterWriters.size()));
            provider.log(ProviderScenario.class.getName(), "roll", level, null, null, afterMessage, new Object[0]);
            flush(afterWriters);
        }
    }
}
