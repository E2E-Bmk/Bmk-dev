package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.time.DateTimeException;
import java.time.Instant;
import java.time.LocalDate;
import java.time.format.DateTimeParseException;
import org.junit.jupiter.api.Test;
import org.threeten.extra.Days;
import org.threeten.extra.Interval;
import org.threeten.extra.LocalDateRange;
import org.threeten.extra.Quarter;
import org.threeten.extra.YearQuarter;
import org.threeten.extra.YearWeek;
import org.threeten.extra.chrono.CopticDate;
import org.threeten.extra.chrono.InternationalFixedDate;
import org.threeten.extra.chrono.JulianDate;

/** Required exception classes for the specified failure conditions. */
class ErrorsAtomicTest {

    private static final Instant T1 = Instant.parse("2020-01-01T00:00:00Z");
    private static final Instant T2 = Instant.parse("2020-01-02T00:00:00Z");

    /**
     * Verifies: Error Semantics — an interval or range with end before start
     * raises DateTimeException.
     */
    @Test
    void endBeforeStartRaises() {
        assertThrows(DateTimeException.class, () -> Interval.of(T2, T1));
        assertThrows(DateTimeException.class,
                () -> LocalDateRange.of(LocalDate.of(2020, 2, 1), LocalDate.of(2020, 1, 1)));
    }

    /**
     * Verifies: Error Semantics — union and intersection on disconnected
     * intervals raise DateTimeException.
     */
    @Test
    void disconnectedIntervalAlgebraRaises() {
        Interval left = Interval.of(T1, T2);
        Interval right = Interval.of(T2.plusSeconds(10), T2.plusSeconds(20));
        assertThrows(DateTimeException.class, () -> left.union(right));
        assertThrows(DateTimeException.class, () -> left.intersection(right));
    }

    /**
     * Verifies: Error Semantics — union and intersection on disconnected
     * ranges raise DateTimeException.
     */
    @Test
    void disconnectedRangeAlgebraRaises() {
        LocalDateRange left = LocalDateRange.of(LocalDate.of(2020, 1, 1), LocalDate.of(2020, 1, 5));
        LocalDateRange right = LocalDateRange.of(LocalDate.of(2020, 2, 1), LocalDate.of(2020, 2, 2));
        assertThrows(DateTimeException.class, () -> left.union(right));
        assertThrows(DateTimeException.class, () -> left.intersection(right));
    }

    /**
     * Verifies: Error Semantics — unparseable text raises
     * DateTimeParseException across the parse surface.
     */
    @Test
    void unparseableTextRaisesParseException() {
        assertThrows(DateTimeParseException.class, () -> Interval.parse("garbage"));
        assertThrows(DateTimeParseException.class, () -> LocalDateRange.parse("garbage"));
        assertThrows(DateTimeParseException.class, () -> Days.parse("garbage"));
        assertThrows(DateTimeParseException.class, () -> YearWeek.parse("garbage"));
        assertThrows(DateTimeParseException.class, () -> YearQuarter.parse("garbage"));
    }

    /**
     * Verifies: Error Semantics — dividing an amount by zero raises
     * ArithmeticException.
     */
    @Test
    void divideByZeroRaisesArithmetic() {
        assertThrows(ArithmeticException.class, () -> Days.of(1).dividedBy(0));
    }

    /**
     * Verifies: Error Semantics — Quarter.of outside 1-4 raises
     * DateTimeException.
     */
    @Test
    void quarterOutOfRangeRaises() {
        assertThrows(DateTimeException.class, () -> Quarter.of(5));
    }

    /**
     * Verifies: Error Semantics — a week outside 1-53 raises
     * DateTimeException, while week 53 of a short year resolves instead.
     */
    @Test
    void weekOutOfRangeRaises() {
        assertThrows(DateTimeException.class, () -> YearWeek.of(2019, 54));
        assertEquals(YearWeek.of(2020, 1), YearWeek.of(2019, 53));
    }

    /**
     * Verifies: Error Semantics — atDay beyond the quarter length raises
     * DateTimeException.
     */
    @Test
    void atDayBeyondQuarterLengthRaises() {
        assertThrows(DateTimeException.class, () -> YearQuarter.of(2020, 1).atDay(92));
    }

    /**
     * Verifies: Error Semantics — invalid chronology dates raise
     * DateTimeException in each calendar.
     */
    @Test
    void invalidChronologyDatesRaise() {
        assertThrows(DateTimeException.class, () -> CopticDate.of(1740, 13, 6));
        assertThrows(DateTimeException.class, () -> JulianDate.of(2019, 2, 29));
        assertThrows(DateTimeException.class, () -> InternationalFixedDate.of(2019, 6, 29));
    }
}
