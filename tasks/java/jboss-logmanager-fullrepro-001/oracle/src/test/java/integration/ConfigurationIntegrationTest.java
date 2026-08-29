package integration;

import static org.junit.jupiter.api.Assertions.*;

import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.logging.Filter;
import org.jboss.logmanager.ExtLogRecord;
import org.jboss.logmanager.Level;
import org.jboss.logmanager.LogContext;
import org.jboss.logmanager.Logger;
import org.jboss.logmanager.configuration.PropertyLogContextConfigurator;
import org.jboss.logmanager.configuration.filters.FilterExpressions;
import org.jboss.logmanager.formatters.PatternFormatter;
import org.jboss.logmanager.handlers.QueueHandler;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Integration checks across UTF-8 properties, configured object graphs, and programmatic views. */
class ConfigurationIntegrationTest {
    private static void configure(LogContext context, String text) {
        new PropertyLogContextConfigurator().configure(context, new ByteArrayInputStream(text.getBytes(StandardCharsets.UTF_8)));
    }
    private static String path(Path path) { return path.toString().replace('\\', '/'); }
    private static String fileConfiguration(String logger, Path file, String level, String pattern) {
        return "loggers=" + logger + "\n"
                + "logger." + logger + ".level=" + level + "\n"
                + "logger." + logger + ".handlers=FILE\n"
                + "logger." + logger + ".useParentHandlers=false\n"
                + "handler.FILE=org.jboss.logmanager.handlers.FileHandler\n"
                + "handler.FILE.level=ALL\nhandler.FILE.formatter=TEXT\n"
                + "handler.FILE.properties=fileName,autoFlush\nhandler.FILE.fileName=" + path(file) + "\nhandler.FILE.autoFlush=true\n"
                + "formatter.TEXT=org.jboss.logmanager.formatters.PatternFormatter\n"
                + "formatter.TEXT.properties=pattern\nformatter.TEXT.pattern=" + pattern + "\n";
    }

    /**
     * Verifies: JBLM-INV-007, JBLM-CFG-005, JBLM-CFG-009.
     * Seam: config interaction
     * Depends-On: patternFormatterRendersCoreWords, propagatesInputReadFailures
     */
    @Test void configuredPatternMatchesProgrammaticFormatter(@TempDir Path directory) throws Exception {
        Path file = directory.resolve("configured-401.log");
        try (LogContext context = LogContext.create(true)) {
            configure(context, fileConfiguration("cfg.pattern", file, "WARN", "%p|%c|%m")); context.getLogger("cfg.pattern").log(Level.WARN, "aligned-402");
        }
        ExtLogRecord expectedRecord = new ExtLogRecord(Level.WARN, "aligned-402", ExtLogRecord.FormatStyle.NO_FORMAT, "caller.Type"); expectedRecord.setLoggerName("cfg.pattern");
        assertEquals(new PatternFormatter("%p|%c|%m").format(expectedRecord), Files.readString(file, StandardCharsets.UTF_8));
    }

    /**
     * Verifies: JBLM-INV-007, JBLM-CFG-009.
     * Seam: lifecycle crossing
     * Depends-On: patternFormatterRendersCoreWords, fileHandlerSelectsOverwritesAndDisablesDestinations
     */
    @Test void distinctConfiguredPatternsMatchTheirProgrammaticViews(@TempDir Path directory) throws Exception {
        Path first = directory.resolve("first-403.log"); Path second = directory.resolve("second-404.log");
        try (LogContext firstContext = LogContext.create(true); LogContext secondContext = LogContext.create(true)) {
            configure(firstContext, fileConfiguration("cfg.first", first, "INFO", "%p-%m")); firstContext.getLogger("cfg.first").info("before-405");
            configure(secondContext, fileConfiguration("cfg.second", second, "INFO", "%m:%p")); secondContext.getLogger("cfg.second").info("after-406");
        }
        assertEquals("INFO-before-405", Files.readString(first, StandardCharsets.UTF_8));
        assertEquals("after-406:INFO", Files.readString(second, StandardCharsets.UTF_8));
    }

    /**
     * Verifies: JBLM-INV-008, JBLM-CFG-003, JBLM-CFG-004, JBLM-CFG-006.
     * Seam: config interaction
     * Depends-On: inheritsEffectiveLevelFromAncestor, parsesDocumentedExpressionsAndRejectsMalformedOnes
     */
    @Test void configuredLoggerPolicyMatchesProgrammaticGetters() throws Exception {
        try (LogContext context = LogContext.create(true)) {
            configure(context, "loggers=cfg.policy\nlogger.cfg.policy.level=ERROR\nlogger.cfg.policy.filter=accept\nlogger.cfg.policy.useParentHandlers=false\n");
            Logger logger = context.getLogger("cfg.policy");
            assertSame(Level.ERROR, logger.getLevel()); assertEquals(Level.ERROR.intValue(), logger.getEffectiveLevel());
            assertFalse(logger.getUseParentHandlers()); assertTrue(logger.getFilter().isLoggable(new java.util.logging.LogRecord(Level.INFO, "probe-407")));
        }
    }

    /**
     * Verifies: JBLM-INV-008, JBLM-CFG-005, JBLM-CFG-011.
     * Seam: config interaction
     * Depends-On: queueHandlerRetainsNewestRecordsWithinItsBound, maintainsOrderedIndependentHandlerSnapshots
     */
    @Test void configuredHandlerPolicyMatchesPublicHandlerView() throws Exception {
        String text = "loggers=cfg.handler\nlogger.cfg.handler.handlers=QUEUE\nlogger.cfg.handler.useParentHandlers=false\n"
                + "handler.QUEUE=org.jboss.logmanager.handlers.QueueHandler\nhandler.QUEUE.level=WARN\n"
                + "handler.QUEUE.formatter=TEXT\nhandler.QUEUE.properties=limit\nhandler.QUEUE.limit=7\n"
                + "formatter.TEXT=org.jboss.logmanager.formatters.PatternFormatter\nformatter.TEXT.properties=pattern\nformatter.TEXT.pattern=%m\n";
        try (LogContext context = LogContext.create(true)) {
            configure(context, text); QueueHandler queue = (QueueHandler) context.getLogger("cfg.handler").getHandlers()[0];
            assertSame(Level.WARN, queue.getLevel()); assertEquals(7, queue.getLimit()); assertEquals("%m", ((PatternFormatter) queue.getFormatter()).getPattern());
        }
    }

    /**
     * Verifies: JBLM-INV-008, JBLM-CFG-006, JBLM-FLT-010.
     * Seam: protocol handoff
     * Depends-On: regexFilterFindsSubstringsAndRejectsInvalidPatterns, parsesDocumentedExpressionsAndRejectsMalformedOnes
     */
    @Test void configuredFilterMatchesDirectlyParsedFilter() throws Exception {
        String expression = "match(\"allow-[5-7][0-9]\")";
        try (LogContext context = LogContext.create(true)) {
            configure(context, "loggers=cfg.filter.view\nlogger.cfg.filter.view.filter=" + expression + "\n");
            Filter configured = context.getLogger("cfg.filter.view").getFilter(); Filter direct = FilterExpressions.parse(context, expression);
            ExtLogRecord accepted = new ExtLogRecord(Level.INFO, "prefix allow-63 suffix", "caller.Type");
            ExtLogRecord denied = new ExtLogRecord(Level.INFO, "allow-91", "caller.Type");
            assertEquals(direct.isLoggable(accepted), configured.isLoggable(accepted)); assertEquals(direct.isLoggable(denied), configured.isLoggable(denied));
        }
    }

    /**
     * Verifies: JBLM-CFG-001, JBLM-CFG-012, JBLM-INV-007.
     * Seam: protocol handoff
     * Depends-On: fileHandlerSelectsOverwritesAndDisablesDestinations, patternFormatterRendersCoreWords
     */
    @Test void utf8ConfigurationAndDestinationPreserveUnicode(@TempDir Path directory) throws Exception {
        Path file = directory.resolve("utf8-408.log");
        try (LogContext context = LogContext.create(true)) {
            configure(context, fileConfiguration("cfg.utf8", file, "INFO", "固定:%m")); context.getLogger("cfg.utf8").info("café-Ω-409");
        }
        assertEquals("固定:café-Ω-409", Files.readString(file, StandardCharsets.UTF_8));
    }

    /**
     * Verifies: JBLM-INV-008, JBLM-CFG-004, JBLM-CFG-014.
     * Seam: config interaction
     * Depends-On: resolvesDocumentedLevels, inheritsEffectiveLevelFromAncestor
     */
    @Test void reconfigurationUpdatesTheProgrammaticLevelView() throws Exception {
        try (LogContext context = LogContext.create(true)) {
            configure(context, "loggers=cfg.level.view\nlogger.cfg.level.view.level=WARN\n");
            assertSame(Level.WARN, context.getLogger("cfg.level.view").getLevel());
            configure(context, "loggers=cfg.level.view\nlogger.cfg.level.view.level=TRACE\n");
            assertSame(Level.TRACE, context.getLogger("cfg.level.view").getLevel());
        }
    }

    /**
     * Verifies: JBLM-INV-010, JBLM-CFG-014, JBLM-HND-016.
     * Seam: lifecycle crossing
     * Depends-On: propagatesInputReadFailures, fileHandlerSelectsOverwritesAndDisablesDestinations
     */
    @Test void contextCloseCompletesConfiguredFileLifecycle(@TempDir Path directory) throws Exception {
        Path file = directory.resolve("lifecycle-410.log"); LogContext context = LogContext.create(true);
        configure(context, fileConfiguration("cfg.close", file, "INFO", "%m")); context.getLogger("cfg.close").info("closed-411"); context.close();
        assertTrue(Files.exists(file)); assertEquals("closed-411", Files.readString(file, StandardCharsets.UTF_8));
    }
}
