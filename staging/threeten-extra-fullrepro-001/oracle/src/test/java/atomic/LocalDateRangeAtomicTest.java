package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.time.LocalDate;
import java.time.Period;
import java.util.List;
import java.util.stream.Collectors;
import org.junit.jupiter.api.Test;
import org.threeten.extra.LocalDateRange;

/** LocalDateRange construction, projections, queries, and algebra. */
class LocalDateRangeAtomicTest {

    private static final LocalDate D1 = LocalDate.of(2020, 1, 1);
    private static final LocalDate D2 = LocalDate.of(2020, 2, 1);
    private static final LocalDate D3 = LocalDate.of(2020, 3, 1);

    /**
     * Verifies: Date Ranges — of creates a half-open range with the start/end
     * text form.
     */
    @Test
    void ofCreatesRangeWithIsoTextForm() {
        LocalDateRange range = LocalDateRange.of(D1, D2);
        assertEquals("2020-01-01/2020-02-01", range.toString());
        assertEquals(D1, range.getStart());
        assertEquals(D2, range.getEnd());
    }

    /**
     * Verifies: Date Ranges — parse reads the start/end text form back into an
     * equal range.
     */
    @Test
    void parseReadsIsoForm() {
        assertEquals(LocalDateRange.of(D1, D2), LocalDateRange.parse("2020-01-01/2020-02-01"));
    }

    /**
     * Verifies: Date Ranges — ofClosed treats its second argument as the last
     * included date.
     */
    @Test
    void ofClosedIncludesEndDate() {
        LocalDateRange closed = LocalDateRange.ofClosed(D1, D2);
        assertEquals(LocalDate.of(2020, 2, 2), closed.getEnd());
        assertEquals(D2, closed.getEndInclusive());
    }

    /**
     * Verifies: Date Ranges — getEndInclusive is one day before the exclusive
     * end.
     */
    @Test
    void endInclusiveIsDayBeforeEnd() {
        assertEquals(LocalDate.of(2020, 1, 31), LocalDateRange.of(D1, D2).getEndInclusive());
    }

    /**
     * Verifies: Date Ranges — lengthInDays counts the included dates.
     */
    @Test
    void lengthInDaysCountsIncludedDates() {
        assertEquals(31, LocalDateRange.of(D1, D2).lengthInDays());
    }

    /**
     * Verifies: Date Ranges — toPeriod returns the range length as a Period.
     */
    @Test
    void toPeriodReturnsRangeLength() {
        assertEquals(Period.ofMonths(1), LocalDateRange.of(D1, D2).toPeriod());
    }

    /**
     * Verifies: Date Ranges — stream yields every included date in order.
     */
    @Test
    void streamYieldsIncludedDatesInOrder() {
        List<String> dates = LocalDateRange.of(D1, LocalDate.of(2020, 1, 5)).stream()
                .map(LocalDate::toString).collect(Collectors.toList());
        assertEquals(List.of("2020-01-01", "2020-01-02", "2020-01-03", "2020-01-04"), dates);
    }

    /**
     * Verifies: Date Ranges — contains includes the start and excludes the
     * end.
     */
    @Test
    void containsIsHalfOpen() {
        LocalDateRange range = LocalDateRange.of(D1, D2);
        assertTrue(range.contains(D1));
        assertFalse(range.contains(D2));
    }

    /**
     * Verifies: Date Ranges — a range with equal boundaries is empty.
     */
    @Test
    void equalBoundariesMakeEmptyRange() {
        assertTrue(LocalDateRange.of(D1, D1).isEmpty());
        assertFalse(LocalDateRange.of(D1, D2).isEmpty());
    }

    /**
     * Verifies: Date Ranges — abuts and overlaps follow the interval
     * semantics: boundary touch abuts and does not overlap.
     */
    @Test
    void abutsAndOverlapsFollowIntervalSemantics() {
        LocalDateRange first = LocalDateRange.of(D1, D2);
        LocalDateRange second = LocalDateRange.of(D2, D3);
        assertTrue(first.abuts(second));
        assertFalse(first.overlaps(second));
        assertTrue(first.isConnected(second));
    }

    /**
     * Verifies: Date Ranges — union merges connected ranges into the smallest
     * containing range.
     */
    @Test
    void unionMergesConnectedRanges() {
        assertEquals(LocalDateRange.of(D1, D3),
                LocalDateRange.of(D1, D2).union(LocalDateRange.of(D2, D3)));
    }

    /**
     * Verifies: Date Ranges — intersection of overlapping ranges returns the
     * shared dates.
     */
    @Test
    void intersectionReturnsSharedDates() {
        LocalDateRange left = LocalDateRange.of(D1, LocalDate.of(2020, 2, 15));
        LocalDateRange right = LocalDateRange.of(D2, D3);
        assertEquals(LocalDateRange.of(D2, LocalDate.of(2020, 2, 15)), left.intersection(right));
    }

    /**
     * Verifies: Date Ranges — span covers disconnected ranges including the
     * gap.
     */
    @Test
    void spanCoversGap() {
        LocalDateRange left = LocalDateRange.of(D1, LocalDate.of(2020, 1, 5));
        LocalDateRange right = LocalDateRange.of(D2, LocalDate.of(2020, 2, 2));
        assertEquals(LocalDateRange.of(D1, LocalDate.of(2020, 2, 2)), left.span(right));
    }

    /**
     * Verifies: Date Ranges — encloses is true when the receiver covers every
     * date of the argument.
     */
    @Test
    void enclosesCoversContainedRanges() {
        assertTrue(LocalDateRange.of(D1, D3).encloses(LocalDateRange.of(D2, D3)));
        assertFalse(LocalDateRange.of(D1, D2).encloses(LocalDateRange.of(D1, D3)));
    }
}
