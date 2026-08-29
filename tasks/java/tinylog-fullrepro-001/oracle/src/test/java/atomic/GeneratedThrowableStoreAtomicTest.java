package atomic;

import java.util.List;

import org.junit.jupiter.api.Test;
import org.tinylog.throwable.ThrowableData;
import org.tinylog.throwable.ThrowableStore;

import static org.junit.jupiter.api.Assertions.*;

class GeneratedThrowableStoreAtomicTest {
    private static final StackTraceElement FRAME = new StackTraceElement("sample.A", "run", "A.java", 17);
    private static final ThrowableData CAUSE = new ThrowableStore("sample.Cause", "cause-13", List.of(FRAME), null);

    /** Verifies: TINY-THR-002. */ @Test void classNameIsStored() { assertEquals("sample.Root", full().getClassName()); }
    /** Verifies: TINY-THR-002. */ @Test void messageIsStored() { assertEquals("root-27", full().getMessage()); }
    /** Verifies: TINY-THR-002. */ @Test void stackTraceIsStored() { assertEquals(List.of(FRAME), full().getStackTrace()); }
    /** Verifies: TINY-THR-002. */ @Test void causeIsStored() { assertSame(CAUSE, full().getCause()); }
    /** Verifies: TINY-THR-002. */ @Test void suppressedListIsStored() { assertEquals(List.of(CAUSE), full().getSuppressed()); }
    /** Verifies: TINY-THR-003. */ @Test void omittedSuppressedBecomesEmpty() { assertTrue(new ThrowableStore("A", "B", List.of(), null).getSuppressed().isEmpty()); }
    /** Verifies: TINY-THR-003. */ @Test void nullSuppressedBecomesEmpty() { assertTrue(new ThrowableStore("A", "B", List.of(), null, null).getSuppressed().isEmpty()); }

    private static ThrowableStore full() {
        return new ThrowableStore("sample.Root", "root-27", List.of(FRAME), CAUSE, List.of(CAUSE));
    }
}
