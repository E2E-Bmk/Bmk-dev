package atomic;

import static org.junit.jupiter.api.Assertions.*;

import java.util.Arrays;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.logging.Filter;
import org.jboss.logmanager.ExtLogRecord;
import org.jboss.logmanager.Level;
import org.jboss.logmanager.LogContext;
import org.jboss.logmanager.configuration.filters.FilterExpressions;
import org.jboss.logmanager.filters.AcceptAllFilter;
import org.jboss.logmanager.filters.AllFilter;
import org.jboss.logmanager.filters.AnyFilter;
import org.jboss.logmanager.filters.DenyAllFilter;
import org.jboss.logmanager.filters.InvertFilter;
import org.jboss.logmanager.filters.LevelChangingFilter;
import org.jboss.logmanager.filters.LevelFilter;
import org.jboss.logmanager.filters.LevelRangeFilter;
import org.jboss.logmanager.filters.RegexFilter;
import org.jboss.logmanager.filters.SubstituteFilter;
import org.junit.jupiter.api.Test;

/** Atomic checks for direct filters and the public expression grammar. */
class FilterAtomicTest {
    private static ExtLogRecord record(java.util.logging.Level level, String message) {
        return new ExtLogRecord(level, message, ExtLogRecord.FormatStyle.NO_FORMAT, "caller.Type");
    }

    /** Verifies: JBLM-FLT-001. */
    @Test void singletonFiltersReturnOppositeConstants() {
        ExtLogRecord record = record(Level.INFO, "constant-31");
        assertTrue(AcceptAllFilter.getInstance().isLoggable(record));
        assertFalse(DenyAllFilter.getInstance().isLoggable(record));
    }

    /** Verifies: JBLM-FLT-002, JBLM-FLT-004. */
    @Test void allFilterShortCircuitsAndRejectsNullIteratorMembers() {
        AtomicInteger calls = new AtomicInteger();
        Filter never = r -> false;
        Filter counted = r -> { calls.incrementAndGet(); return true; };
        assertFalse(new AllFilter(new Filter[] {never, counted}).isLoggable(record(Level.INFO, "all-32")));
        assertEquals(0, calls.get());
        assertTrue(new AllFilter(new Filter[0]).isLoggable(record(Level.INFO, "empty-all")));
        assertThrows(NullPointerException.class, () -> new AllFilter(Arrays.asList(never, null).iterator()));
    }

    /** Verifies: JBLM-FLT-003, JBLM-FLT-004. */
    @Test void anyFilterShortCircuitsAndRejectsNullIteratorMembers() {
        AtomicInteger calls = new AtomicInteger();
        Filter yes = r -> true;
        Filter counted = r -> { calls.incrementAndGet(); return false; };
        assertTrue(new AnyFilter(new Filter[] {yes, counted}).isLoggable(record(Level.INFO, "any-33")));
        assertEquals(0, calls.get());
        assertFalse(new AnyFilter(new Filter[0]).isLoggable(record(Level.INFO, "empty-any")));
        assertThrows(NullPointerException.class, () -> new AnyFilter(Arrays.asList(yes, null).iterator()));
    }

    /** Verifies: JBLM-FLT-005. */
    @Test void invertFilterNegatesItsTarget() {
        ExtLogRecord record = record(Level.INFO, "inverse-34");
        assertFalse(new InvertFilter(AcceptAllFilter.getInstance()).isLoggable(record));
        assertTrue(new InvertFilter(DenyAllFilter.getInstance()).isLoggable(record));
    }

    /** Verifies: JBLM-FLT-006. */
    @Test void levelFilterUsesConfiguredLevelObjects() {
        LevelFilter filter = new LevelFilter(List.of(Level.ERROR, Level.TRACE));
        assertTrue(filter.isLoggable(record(Level.TRACE, "trace-35")));
        assertFalse(filter.isLoggable(record(Level.DEBUG, "debug-36")));
        assertTrue(filter.isLoggable(record(Level.ERROR, "error-37")));
    }

    /** Verifies: JBLM-FLT-007, JBLM-FLT-008, JBLM-ERR-005. */
    @Test void levelRangeHonorsEndpointsAndRejectsReversal() {
        LevelRangeFilter filter = new LevelRangeFilter(Level.DEBUG, false, Level.ERROR, true);
        assertFalse(filter.isLoggable(record(Level.DEBUG, "low-edge")));
        assertTrue(filter.isLoggable(record(Level.INFO, "middle")));
        assertTrue(filter.isLoggable(record(Level.ERROR, "high-edge")));
        assertThrows(IllegalArgumentException.class, () -> new LevelRangeFilter(Level.ERROR, true, Level.TRACE, true));
    }

    /** Verifies: JBLM-FLT-009. */
    @Test void levelChangingFilterMutatesAndAccepts() {
        ExtLogRecord record = record(Level.INFO, "upgrade-38");
        assertTrue(new LevelChangingFilter(Level.FATAL).isLoggable(record));
        assertSame(Level.FATAL, record.getLevel());
    }

    /** Verifies: JBLM-FLT-010, JBLM-FLT-013, JBLM-ERR-006. */
    @Test void regexFilterFindsSubstringsAndRejectsInvalidPatterns() {
        RegexFilter filter = new RegexFilter("code-[4-6][0-9]");
        assertTrue(filter.isLoggable(record(Level.INFO, "prefix code-57 suffix")));
        assertFalse(filter.isLoggable(record(Level.INFO, "code-9")));
        assertThrows(java.util.regex.PatternSyntaxException.class, () -> new RegexFilter("[broken"));
    }

    /** Verifies: JBLM-FLT-011, JBLM-FLT-012. */
    @Test void substituteFilterSelectsFirstOrAllMatches() {
        ExtLogRecord first = record(Level.INFO, "id-17 id-18 id-19");
        assertTrue(new SubstituteFilter("id-[0-9]+", "token", false).isLoggable(first));
        assertEquals("token id-18 id-19", first.getMessage());
        assertSame(ExtLogRecord.FormatStyle.NO_FORMAT, first.getFormatStyle());
        ExtLogRecord all = record(Level.INFO, "id-27 id-28");
        new SubstituteFilter("id-[0-9]+", "token", true).isLoggable(all);
        assertEquals("token token", all.getMessage());
    }

    /** Verifies: JBLM-FLT-014, JBLM-FLT-015, JBLM-FLT-016, JBLM-FLT-017, JBLM-FLT-018, JBLM-FLT-020, JBLM-ERR-007. */
    @Test void parsesDocumentedExpressionsAndRejectsMalformedOnes() throws Exception {
        try (LogContext context = LogContext.create(true)) {
            assertNull(FilterExpressions.parse(context, ""));
            Filter nested = FilterExpressions.parse(context, "all(accept,not(deny),levelRange[DEBUG,ERROR])");
            assertTrue(nested.isLoggable(record(Level.INFO, "expression-39")));
            assertFalse(nested.isLoggable(record(Level.TRACE, "expression-40")));
            assertThrows(IllegalArgumentException.class, () -> FilterExpressions.parse(context, "unknownThing(accept)"));
            assertThrows(IllegalArgumentException.class, () -> FilterExpressions.parse(context, "levels(NO_SUCH_851)"));
        }
    }
}
