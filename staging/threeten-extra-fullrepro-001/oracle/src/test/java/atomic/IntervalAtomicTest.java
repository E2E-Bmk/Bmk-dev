package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.time.Duration;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.threeten.extra.Interval;

/** Interval construction, accessors, queries, and relational algebra. */
class IntervalAtomicTest {

    private static final Instant T1 = Instant.parse("2020-01-01T00:00:00Z");
    private static final Instant T2 = Instant.parse("2020-01-02T00:00:00Z");
    private static final Instant T3 = Instant.parse("2020-01-03T00:00:00Z");

    /**
     * Verifies: Time Intervals — of creates a half-open interval whose
     * toString is the ISO start/end form.
     */
    @Test
    void ofCreatesIntervalWithIsoTextForm() {
        Interval interval = Interval.of(T1, T2);
        assertEquals("2020-01-01T00:00:00Z/2020-01-02T00:00:00Z", interval.toString());
        assertEquals(T1, interval.getStart());
        assertEquals(T2, interval.getEnd());
    }

    /**
     * Verifies: Time Intervals — parse reads the start/end text form back into
     * an equal interval.
     */
    @Test
    void parseReadsIsoForm() {
        assertEquals(Interval.of(T1, T2),
                Interval.parse("2020-01-01T00:00:00Z/2020-01-02T00:00:00Z"));
    }

    /**
     * Verifies: Time Intervals — of with a duration derives the end by
     * addition.
     */
    @Test
    void ofWithDurationDerivesEnd() {
        Interval interval = Interval.of(T1, Duration.ofHours(6));
        assertEquals(Instant.parse("2020-01-01T06:00:00Z"), interval.getEnd());
    }

    /**
     * Verifies: Time Intervals — contains includes the start and excludes the
     * end of a non-empty interval.
     */
    @Test
    void containsIsHalfOpen() {
        Interval interval = Interval.of(T1, T2);
        assertTrue(interval.contains(T1));
        assertFalse(interval.contains(T2));
    }

    /**
     * Verifies: Time Intervals — an empty interval contains nothing, not even
     * its own boundary instant.
     */
    @Test
    void emptyIntervalContainsNothing() {
        Interval empty = Interval.of(T1, T1);
        assertTrue(empty.isEmpty());
        assertFalse(empty.contains(T1));
    }

    /**
     * Verifies: Time Intervals — toDuration returns the span between the
     * boundaries.
     */
    @Test
    void toDurationSpansBoundaries() {
        assertEquals(Duration.ofHours(24), Interval.of(T1, T2).toDuration());
    }

    /**
     * Verifies: Time Intervals — ALL is unbounded at both ends.
     */
    @Test
    void allIsUnbounded() {
        assertTrue(Interval.ALL.isUnboundedStart());
        assertTrue(Interval.ALL.isUnboundedEnd());
    }

    /**
     * Verifies: Time Intervals — abuts is true for intervals touching at one
     * boundary and false for an interval against itself.
     */
    @Test
    void abutsDetectsSharedBoundaryOnly() {
        assertTrue(Interval.of(T1, T2).abuts(Interval.of(T2, T3)));
        assertFalse(Interval.of(T1, T2).abuts(Interval.of(T1, T2)));
    }

    /**
     * Verifies: Time Intervals — overlaps is false for abutting intervals and
     * true for intervals sharing more than a boundary.
     */
    @Test
    void overlapsExcludesBoundaryTouch() {
        assertFalse(Interval.of(T1, T2).overlaps(Interval.of(T2, T3)));
        assertTrue(Interval.of(T1, T3).overlaps(Interval.of(T2, T3)));
        assertTrue(Interval.of(T1, T2).overlaps(Interval.of(T1, T2)));
    }

    /**
     * Verifies: Time Intervals — encloses is true when every instant of the
     * argument lies within the receiver, including itself.
     */
    @Test
    void enclosesCoversContainedIntervals() {
        Interval outer = Interval.of(T1, T3);
        assertTrue(outer.encloses(Interval.of(T1, T2)));
        assertTrue(outer.encloses(outer));
        assertFalse(Interval.of(T1, T2).encloses(outer));
    }

    /**
     * Verifies: Time Intervals — isConnected is true when intervals abut or
     * overlap.
     */
    @Test
    void isConnectedCoversAbutAndOverlap() {
        assertTrue(Interval.of(T1, T2).isConnected(Interval.of(T2, T3)));
        assertTrue(Interval.of(T1, T3).isConnected(Interval.of(T2, T3)));
        assertFalse(Interval.of(T1, T2).isConnected(Interval.of(T2.plusSeconds(1), T3)));
    }

    /**
     * Verifies: Time Intervals — union of connected intervals returns the
     * smallest containing interval.
     */
    @Test
    void unionMergesConnectedIntervals() {
        assertEquals(Interval.of(T1, T3), Interval.of(T1, T2).union(Interval.of(T2, T3)));
    }

    /**
     * Verifies: Time Intervals — intersection of overlapping intervals returns
     * the shared interval.
     */
    @Test
    void intersectionReturnsSharedSpan() {
        assertEquals(Interval.of(T2, T3), Interval.of(T1, T3).intersection(Interval.of(T2, T3)));
    }

    /**
     * Verifies: Time Intervals — span fills the gap between disconnected
     * intervals.
     */
    @Test
    void spanCoversDisconnectedIntervals() {
        Interval left = Interval.of(T1, T1.plusSeconds(3600));
        Interval right = Interval.of(T3, T3.plusSeconds(3600));
        assertEquals(Interval.of(T1, T3.plusSeconds(3600)), left.span(right));
    }

    /**
     * Verifies: Time Intervals — isBefore and isAfter compare the whole
     * interval to an instant.
     */
    @Test
    void isBeforeAndIsAfterCompareToInstant() {
        Interval interval = Interval.of(T1, T2);
        assertTrue(interval.isBefore(T3));
        assertTrue(interval.isAfter(Instant.parse("2019-12-31T00:00:00Z")));
    }

    /**
     * Verifies: Time Intervals — intervals are equal when both boundaries are
     * equal.
     */
    @Test
    void equalityIsByBoundaries() {
        assertEquals(Interval.of(T1, T2), Interval.of(T1, T2));
        assertFalse(Interval.of(T1, T2).equals(Interval.of(T1, T3)));
    }
}
