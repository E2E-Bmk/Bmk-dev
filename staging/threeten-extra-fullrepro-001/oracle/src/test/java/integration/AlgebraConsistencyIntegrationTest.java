package integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.time.Instant;
import java.time.LocalDate;
import java.util.List;
import java.util.stream.Collectors;
import org.junit.jupiter.api.Test;
import org.threeten.extra.Days;
import org.threeten.extra.Interval;
import org.threeten.extra.LocalDateRange;

/**
 * Consistency of the relational algebra across intervals and ranges, and
 * agreement between the algebra, containment, streams, and amounts.
 */
class AlgebraConsistencyIntegrationTest {

    private static final Instant T1 = Instant.parse("2020-01-01T00:00:00Z");
    private static final Instant T2 = Instant.parse("2020-01-02T00:00:00Z");
    private static final Instant T3 = Instant.parse("2020-01-03T00:00:00Z");

    /**
     * Verifies: Cross-View Invariants — intervals are connected exactly when
     * they abut or overlap, checked across touching, overlapping, and disjoint
     * pairs.
     * Depends-On: abutsDetectsSharedBoundaryOnly, overlapsExcludesBoundaryTouch, isConnectedCoversAbutAndOverlap.
     */
    @Test
    void connectedEqualsAbutsOrOverlaps() {
        Interval base = Interval.of(T1, T2);
        Interval touching = Interval.of(T2, T3);
        Interval overlapping = Interval.of(T1.plusSeconds(3600), T3);
        Interval disjoint = Interval.of(T2.plusSeconds(10), T3);
        for (Interval other : List.of(touching, overlapping, disjoint)) {
            assertEquals(base.abuts(other) || base.overlaps(other), base.isConnected(other));
        }
    }

    /**
     * Verifies: Cross-View Invariants — union equals span whenever the
     * intervals are connected.
     * Depends-On: unionMergesConnectedIntervals, spanCoversDisconnectedIntervals.
     */
    @Test
    void unionEqualsSpanWhenConnected() {
        Interval left = Interval.of(T1, T2);
        Interval right = Interval.of(T2, T3);
        assertEquals(left.span(right), left.union(right));
        Interval overlappingRight = Interval.of(T1.plusSeconds(3600), T3);
        assertEquals(left.span(overlappingRight), left.union(overlappingRight));
    }

    /**
     * Verifies: Cross-View Invariants — ranges follow the same
     * connected/abuts/overlaps relation as intervals.
     * Depends-On: abutsAndOverlapsFollowIntervalSemantics, isConnectedCoversAbutAndOverlap.
     */
    @Test
    void rangeRelationsMatchIntervalRelations() {
        LocalDateRange base = LocalDateRange.of(LocalDate.of(2020, 1, 1), LocalDate.of(2020, 1, 5));
        LocalDateRange touching = LocalDateRange.of(LocalDate.of(2020, 1, 5), LocalDate.of(2020, 1, 9));
        LocalDateRange disjoint = LocalDateRange.of(LocalDate.of(2020, 2, 1), LocalDate.of(2020, 2, 2));
        assertTrue(base.abuts(touching) && !base.overlaps(touching) && base.isConnected(touching));
        assertFalse(base.isConnected(disjoint));
        assertEquals(base.span(touching), base.union(touching));
    }

    /**
     * Verifies: Cross-View Invariants — a non-empty interval and range contain
     * their start and not their end, and an empty one contains nothing.
     * Depends-On: containsIsHalfOpen, emptyIntervalContainsNothing, equalBoundariesMakeEmptyRange.
     */
    @Test
    void halfOpenContainmentAcrossBothTypes() {
        Interval interval = Interval.of(T1, T2);
        assertTrue(interval.contains(interval.getStart()));
        assertFalse(interval.contains(interval.getEnd()));
        assertFalse(Interval.of(T1, T1).contains(T1));
        LocalDateRange range = LocalDateRange.of(LocalDate.of(2020, 1, 1), LocalDate.of(2020, 1, 5));
        assertTrue(range.contains(range.getStart()));
        assertFalse(range.contains(range.getEnd()));
        assertFalse(LocalDateRange.of(range.getStart(), range.getStart()).contains(range.getStart()));
    }

    /**
     * Verifies: Cross-View Invariants — every streamed date is contained, the
     * stream count equals lengthInDays, and Days.between carries the same
     * number.
     * Depends-On: streamYieldsIncludedDatesInOrder, lengthInDaysCountsIncludedDates, betweenMeasuresUnit.
     */
    @Test
    void streamContainmentAndLengthAgree() {
        LocalDateRange range = LocalDateRange.of(LocalDate.of(2020, 1, 1), LocalDate.of(2020, 1, 10));
        List<LocalDate> dates = range.stream().collect(Collectors.toList());
        for (LocalDate date : dates) {
            assertTrue(range.contains(date));
        }
        assertEquals(range.lengthInDays(), dates.size());
        assertEquals(range.lengthInDays(),
                Days.between(range.getStart(), range.getEnd()).getAmount());
    }

    /**
     * Verifies: Cross-View Invariants — ofClosed produces the same range as of
     * with the end advanced one day, and getEndInclusive inverts it.
     * Depends-On: ofClosedIncludesEndDate, endInclusiveIsDayBeforeEnd.
     */
    @Test
    void closedAndOpenConstructionAgree() {
        LocalDate start = LocalDate.of(2020, 1, 1);
        LocalDate last = LocalDate.of(2020, 1, 31);
        LocalDateRange closed = LocalDateRange.ofClosed(start, last);
        assertEquals(LocalDateRange.of(start, last.plusDays(1)), closed);
        assertEquals(last, closed.getEndInclusive());
        assertTrue(closed.contains(last));
        assertFalse(closed.contains(closed.getEnd()));
    }

    /**
     * Verifies: Cross-View Invariants — intersection is contained in both
     * operands and enclosed by their union.
     * Depends-On: intersectionReturnsSharedSpan, enclosesCoversContainedIntervals.
     */
    @Test
    void intersectionEnclosedByBothAndUnion() {
        Interval left = Interval.of(T1, T2.plusSeconds(3600));
        Interval right = Interval.of(T2, T3);
        Interval shared = left.intersection(right);
        assertTrue(left.encloses(shared));
        assertTrue(right.encloses(shared));
        assertTrue(left.union(right).encloses(shared));
    }

    /**
     * Verifies: Cross-View Invariants — parse of a toString result reproduces
     * intervals and ranges.
     * Depends-On: parseReadsIsoForm, ofCreatesIntervalWithIsoTextForm.
     */
    @Test
    void textRoundTripsForIntervalAndRange() {
        Interval interval = Interval.of(T1, T3);
        assertEquals(interval, Interval.parse(interval.toString()));
        LocalDateRange range = LocalDateRange.of(LocalDate.of(2020, 1, 1), LocalDate.of(2020, 3, 1));
        assertEquals(range, LocalDateRange.parse(range.toString()));
    }

    /**
     * Verifies: Cross-View Invariants — the interval between two instants a
     * day apart and the range between the same dates agree through toDuration
     * and lengthInDays.
     * Depends-On: toDurationSpansBoundaries, lengthInDaysCountsIncludedDates.
     */
    @Test
    void durationAndDayCountAgree() {
        Interval interval = Interval.of(T1, T3);
        LocalDateRange range = LocalDateRange.of(LocalDate.of(2020, 1, 1), LocalDate.of(2020, 1, 3));
        assertEquals(java.time.Duration.ofDays(range.lengthInDays()), interval.toDuration());
    }
}
