package atomic;

import static org.junit.jupiter.api.Assertions.assertThrows;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import org.jboss.logmanager.LogContext;
import org.jboss.logmanager.configuration.PropertyLogContextConfigurator;
import org.junit.jupiter.api.Test;

/** Atomic rejection checks for the properties configurator entry point. */
class ConfigurationAtomicTest {
    private static ByteArrayInputStream properties(String value) {
        return new ByteArrayInputStream(value.getBytes(StandardCharsets.UTF_8));
    }

    /** Verifies: JBLM-CFG-009, JBLM-CFG-012, JBLM-CFG-013, JBLM-ERR-015. */
    @Test void rejectsNonConvertibleHandlerProperties() throws Exception {
        try (LogContext context = LogContext.create(true)) {
            String text = "loggers=cfg.bound\nlogger.cfg.bound.handlers=BROKEN\n"
                    + "handler.BROKEN=org.jboss.logmanager.handlers.QueueHandler\n"
                    + "handler.BROKEN.properties=limit\nhandler.BROKEN.limit=not-an-integer\n";
            assertThrows(RuntimeException.class, () -> new PropertyLogContextConfigurator().configure(context, properties(text)));
        }
    }

    /** Verifies: JBLM-CFG-004, JBLM-CFG-007, JBLM-ERR-015. */
    @Test void rejectsUnknownConfiguredLevels() throws Exception {
        try (LogContext context = LogContext.create(true)) {
            String text = "loggers=cfg.level\nlogger.cfg.level.level=NOT_A_LEVEL_772\n";
            assertThrows(RuntimeException.class, () -> new PropertyLogContextConfigurator().configure(context, properties(text)));
        }
    }

    /** Verifies: JBLM-CFG-006, JBLM-CFG-007, JBLM-ERR-007. */
    @Test void rejectsMalformedConfiguredFilters() throws Exception {
        try (LogContext context = LogContext.create(true)) {
            String text = "loggers=cfg.filter\nlogger.cfg.filter.filter=match(\\\"unterminated)\n";
            assertThrows(RuntimeException.class, () -> new PropertyLogContextConfigurator().configure(context, properties(text)));
        }
    }

    /** Verifies: JBLM-CFG-002, JBLM-ERR-014. */
    @Test void propagatesInputReadFailures() throws Exception {
        InputStream broken = new InputStream() { @Override public int read() throws IOException { throw new IOException("probe"); } };
        try (LogContext context = LogContext.create(true)) {
            assertThrows(RuntimeException.class, () -> new PropertyLogContextConfigurator().configure(context, broken));
        }
    }
}
