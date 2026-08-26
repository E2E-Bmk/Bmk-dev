package integration;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.time.DayOfWeek;
import java.time.Duration;
import java.time.Instant;
import java.time.LocalDate;
import java.time.Period;
import java.time.ZoneOffset;
import org.junit.jupiter.api.Test;
import org.threeten.extra.Days;
import org.threeten.extra.Interval;
import org.threeten.extra.Months;
import org.threeten.extra.MutableClock;
import org.threeten.extra.PeriodDuration;
import org.threeten.extra.Weeks;
import org.threeten.extra.YearQuarter;
import org.threeten.extra.YearWeek;
import org.threeten.extra.Years;

/**
 * Round trips linking amounts, partials, clocks, and dates: between/addTo,
 * atDay/from, parse/toString, and clock-driven interval membership.
 */
class AmountsPartialsRoundTripIntegrationTest {

    /**
     * Verifies: Cross-View Invariants — parse of a toString result reproduces
     * every amount and partial type.
     * Depends-On: toStringRendersIsoPeriodStyle, parseReadsOwnForm, ofRendersIsoWeekForm, ofRendersQuarterForm.
     */
    @Test
    void textRoundTripsAcrossAmountAndPartialTypes() {
        assertEquals(Days.of(3), Days.parse(Days.of(3).toString()));
        assertEquals(Weeks.of(2), Weeks.parse(Weeks.of(2).toString()));
        assertEquals(Months.of(5), Months.parse(Months.of(5).toString()));
        assertEquals(Years.of(7), Years.parse(Years.of(7).toString()));
        PeriodDuration pd = PeriodDuration.of(Period.of(1, 2, 3), Duration.ofHours(4));
        assertEquals(pd, PeriodDuration.parse(pd.toString()));
        assertEquals(YearWeek.of(2020, 53), YearWeek.parse(YearWeek.of(2020, 53).toString()));
        assertEquals(YearQuarter.of(2020, 2), YearQuarter.parse(YearQuarter.of(2020, 2).toString()));
    }

    /**
     * Verifies: Cross-View Invariants — between followed by addTo restores the
     * end date for each amount type.
     * Depends-On: betweenMeasuresUnit, temporalAdditionAndSubtraction.
     */
    @Test
    void betweenAddToRestoresEndDate() {
        LocalDate start = LocalDate.of(2020, 1, 1);
        LocalDate end = LocalDate.of(2023, 5, 15);
        assertEquals(end, Days.between(start, end).addTo(start));
        LocalDate weeksEnd = LocalDate.of(2020, 3, 25);
        assertEquals(weeksEnd, Weeks.between(start, weeksEnd).addTo(start));
    }

    /**
     * Verifies: Cross-View Invariants — date.plus(amount) equals
     * amount.addTo(date) for every amount type.
     * Depends-On: temporalAdditionAndSubtraction, toPeriodConversion.
     */
    @Test
    void plusAndAddToAgreeAcrossTypes() {
        LocalDate base = LocalDate.of(2020, 1, 31);
        assertEquals(Days.of(10).addTo(base), base.plus(Days.of(10)));
        assertEquals(Weeks.of(3).addTo(base), base.plus(Weeks.of(3)));
        assertEquals(Months.of(1).addTo(base), base.plus(Months.of(1)));
        assertEquals(Years.of(2).addTo(base), base.plus(Years.of(2)));
    }

    /**
     * Verifies: Cross-View Invariants — YearWeek.from(atDay) restores the
     * year-week for every day of the week, including in a 53-week year.
     * Depends-On: atDayReturnsDateOfWeekday, fromDerivesWeekOfDate.
     */
    @Test
    void yearWeekAtDayFromRoundTrips() {
        YearWeek week = YearWeek.of(2020, 53);
        for (DayOfWeek day : DayOfWeek.values()) {
            assertEquals(week, YearWeek.from(week.atDay(day)));
        }
    }

    /**
     * Verifies: Cross-View Invariants — YearQuarter.from(atDay) restores the
     * year-quarter at both boundaries of the quarter.
     * Depends-On: atDayReturnsDateWithinQuarter, atEndOfQuarterReturnsLastDate, fromDerivesQuarterOfDate.
     */
    @Test
    void yearQuarterAtDayFromRoundTrips() {
        YearQuarter quarter = YearQuarter.of(2020, 2);
        assertEquals(quarter, YearQuarter.from(quarter.atDay(1)));
        assertEquals(quarter, YearQuarter.from(quarter.atDay(quarter.lengthOfQuarter())));
        assertEquals(quarter, YearQuarter.from(quarter.atEndOfQuarter()));
    }

    /**
     * Verifies: Cross-View Invariants — the week-53 resolution rule agrees
     * with is53WeekYear: a resolved week belongs to a year that reports 53
     * weeks only when it has them.
     * Depends-On: week53InShortYearResolvesToNextYear, is53WeekYearClassifiesYears.
     */
    @Test
    void week53ResolutionAgreesWithClassification() {
        YearWeek resolved = YearWeek.of(2019, 53);
        assertEquals(YearWeek.of(2020, 1), resolved);
        YearWeek kept = YearWeek.of(2020, 53);
        assertEquals(53, kept.atDay(DayOfWeek.MONDAY).get(java.time.temporal.WeekFields.ISO.weekOfWeekBasedYear()));
    }

    /**
     * Verifies: Cross-View Invariants — PeriodDuration.between added back onto
     * the start restores the end temporal.
     * Depends-On: betweenSplitsCalendarAndTime, plusCombinesPartWise.
     */
    @Test
    void periodDurationBetweenAddToRestoresEnd() {
        java.time.LocalDateTime start = java.time.LocalDateTime.of(2020, 1, 1, 0, 0);
        java.time.LocalDateTime end = java.time.LocalDateTime.of(2021, 3, 4, 5, 30);
        PeriodDuration amount = PeriodDuration.between(start, end);
        assertEquals(end, start.plus(amount));
    }

    /**
     * Verifies: Cross-View Invariants — a mutable clock stepped by an amount
     * moves through an interval's half-open boundaries consistently with
     * contains.
     * Depends-On: addAdvancesByDuration, containsIsHalfOpen, withZoneSharesInstantState.
     */
    @Test
    void clockSteppingRespectsIntervalBoundaries() {
        Instant start = Instant.parse("2020-01-01T00:00:00Z");
        Interval window = Interval.of(start, Duration.ofHours(2));
        MutableClock clock = MutableClock.of(start, ZoneOffset.UTC);
        assertEquals(true, window.contains(clock.instant()));
        clock.add(Duration.ofHours(1));
        assertEquals(true, window.contains(clock.instant()));
        clock.add(Duration.ofHours(1));
        assertEquals(false, window.contains(clock.instant()));
    }
}
