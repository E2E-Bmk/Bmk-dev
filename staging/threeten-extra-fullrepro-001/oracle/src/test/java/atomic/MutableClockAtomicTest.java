package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.time.Duration;
import java.time.Instant;
import java.time.LocalDate;
import java.time.Period;
import java.time.ZoneId;
import java.time.ZoneOffset;
import org.junit.jupiter.api.Test;
import org.threeten.extra.MutableClock;

/** MutableClock construction, mutation, and shared zone views. */
class MutableClockAtomicTest {

    /**
     * Verifies: Mutable Clock — epochUTC starts at the epoch instant in UTC.
     */
    @Test
    void epochUtcStartsAtEpoch() {
        MutableClock clock = MutableClock.epochUTC();
        assertEquals(Instant.EPOCH, clock.instant());
        assertEquals(ZoneOffset.UTC, clock.getZone());
    }

    /**
     * Verifies: Mutable Clock — of sets the initial instant and zone.
     */
    @Test
    void ofSetsInitialState() {
        MutableClock clock = MutableClock.of(Instant.parse("2020-06-01T12:00:00Z"), ZoneOffset.UTC);
        assertEquals(Instant.parse("2020-06-01T12:00:00Z"), clock.instant());
    }

    /**
     * Verifies: Mutable Clock — setInstant replaces the current instant.
     */
    @Test
    void setInstantReplacesInstant() {
        MutableClock clock = MutableClock.epochUTC();
        clock.setInstant(Instant.parse("2020-06-01T12:00:00Z"));
        assertEquals(Instant.parse("2020-06-01T12:00:00Z"), clock.instant());
    }

    /**
     * Verifies: Mutable Clock — add advances the clock by a duration.
     */
    @Test
    void addAdvancesByDuration() {
        MutableClock clock = MutableClock.of(Instant.parse("2020-06-01T12:00:00Z"), ZoneOffset.UTC);
        clock.add(Duration.ofHours(3));
        assertEquals(Instant.parse("2020-06-01T15:00:00Z"), clock.instant());
    }

    /**
     * Verifies: Mutable Clock — add accepts a period as well.
     */
    @Test
    void addAdvancesByPeriod() {
        MutableClock clock = MutableClock.of(Instant.parse("2020-03-03T00:00:00Z"), ZoneOffset.UTC);
        clock.add(Period.ofDays(2));
        assertEquals(Instant.parse("2020-03-05T00:00:00Z"), clock.instant());
    }

    /**
     * Verifies: Mutable Clock — set with a LocalDate moves the clock to the
     * start of that day in the clock's zone.
     */
    @Test
    void setAdjustsToStartOfDay() {
        MutableClock clock = MutableClock.epochUTC();
        clock.set(LocalDate.of(2020, 3, 3));
        assertEquals(Instant.parse("2020-03-03T00:00:00Z"), clock.instant());
    }

    /**
     * Verifies: Mutable Clock — withZone returns a view over the same instant
     * state, and mutations through either object are visible through both.
     */
    @Test
    void withZoneSharesInstantState() {
        MutableClock utc = MutableClock.of(Instant.parse("2020-06-01T12:00:00Z"), ZoneOffset.UTC);
        MutableClock newYork = utc.withZone(ZoneId.of("America/New_York"));
        assertEquals(utc.instant(), newYork.instant());
        newYork.add(Duration.ofHours(1));
        assertEquals(Instant.parse("2020-06-01T13:00:00Z"), utc.instant());
        assertEquals(ZoneId.of("America/New_York"), newYork.getZone());
    }

    /**
     * Verifies: Mutable Clock — toString renders the instant and zone.
     */
    @Test
    void toStringRendersInstantAndZone() {
        assertEquals("MutableClock[1970-01-01T00:00:00Z,Z]", MutableClock.epochUTC().toString());
    }
}
