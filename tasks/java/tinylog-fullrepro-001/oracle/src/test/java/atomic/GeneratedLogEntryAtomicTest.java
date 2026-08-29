package atomic;

import java.util.LinkedHashMap;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.tinylog.Level;
import org.tinylog.core.LogEntry;

import static org.junit.jupiter.api.Assertions.*;

class GeneratedLogEntryAtomicTest {
    private static LogEntry entry() {
        Map<String, String> context = new LinkedHashMap<>();
        context.put("trace", "z91");
        Throwable error = new IllegalStateException("boom");
        return new LogEntry(null, Thread.currentThread(), context,
                "sample.deep.Component", "compute", "Component.java", 119,
                "metrics", Level.WARN, "payload-41", error);
    }

    /** Verifies: TINY-FMT-001. */ @Test void timestampProjectionPreservesNullInput() { assertNull(entry().getTimestamp()); }
    /** Verifies: TINY-FMT-001. */ @Test void threadProjectionPreservesInput() { assertSame(Thread.currentThread(), entry().getThread()); }
    /** Verifies: TINY-FMT-001. */ @Test void contextProjectionPreservesEntries() { assertEquals(Map.of("trace", "z91"), entry().getContext()); }
    /** Verifies: TINY-FMT-001. */ @Test void classProjectionPreservesInput() { assertEquals("sample.deep.Component", entry().getClassName()); }
    /** Verifies: TINY-FMT-001. */ @Test void methodProjectionPreservesInput() { assertEquals("compute", entry().getMethodName()); }
    /** Verifies: TINY-FMT-001. */ @Test void fileProjectionPreservesInput() { assertEquals("Component.java", entry().getFileName()); }
    /** Verifies: TINY-FMT-001. */ @Test void lineProjectionPreservesInput() { assertEquals(119, entry().getLineNumber()); }
    /** Verifies: TINY-FMT-001. */ @Test void tagProjectionPreservesInput() { assertEquals("metrics", entry().getTag()); }
    /** Verifies: TINY-FMT-001. */ @Test void levelProjectionPreservesInput() { assertEquals(Level.WARN, entry().getLevel()); }
    /** Verifies: TINY-FMT-001. */ @Test void messageProjectionPreservesInput() { assertEquals("payload-41", entry().getMessage()); }
    /** Verifies: TINY-FMT-001. */ @Test void exceptionProjectionPreservesInput() { assertEquals("boom", entry().getException().getMessage()); }

    /** Verifies: TINY-FMT-001, TINY-ERR-010. */
    @Test void nullExceptionProjectionPreservesNullInput() {
        LogEntry value = new LogEntry(null, Thread.currentThread(), Map.of("trace", "z91"),
                "sample.deep.Component", "compute", "Component.java", 119,
                "metrics", Level.WARN, "payload-41", null);
        assertNull(value.getException());
    }
}
