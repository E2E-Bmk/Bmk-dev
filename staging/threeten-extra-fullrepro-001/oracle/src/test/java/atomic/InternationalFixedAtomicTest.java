package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import org.junit.jupiter.api.Test;
import org.threeten.extra.chrono.InternationalFixedChronology;
import org.threeten.extra.chrono.InternationalFixedDate;

/** International Fixed calendar: 13-month structure and special days. */
class InternationalFixedAtomicTest {

    /**
     * Verifies: Alternative Chronologies — an International Fixed date renders
     * with the Ifc id and CE era.
     */
    @Test
    void toStringRendersIfcForm() {
        assertEquals("Ifc CE 2020/01/01", InternationalFixedDate.of(2020, 1, 1).toString());
    }

    /**
     * Verifies: Alternative Chronologies — January 1 aligns with ISO in both
     * directions.
     */
    @Test
    void januaryFirstAlignsWithIso() {
        assertEquals(LocalDate.of(2020, 1, 1), LocalDate.from(InternationalFixedDate.of(2020, 1, 1)));
        assertEquals(InternationalFixedDate.of(2020, 1, 1),
                InternationalFixedDate.from(LocalDate.of(2020, 1, 1)));
    }

    /**
     * Verifies: Alternative Chronologies — a mid-year ISO date lands in the
     * 13-month layout.
     */
    @Test
    void midYearDateLandsInThirteenMonthLayout() {
        assertEquals(InternationalFixedDate.of(2020, 7, 17),
                InternationalFixedDate.from(LocalDate.of(2020, 7, 4)));
    }

    /**
     * Verifies: Alternative Chronologies — the year day is day 29 of month 13
     * and corresponds to ISO December 31.
     */
    @Test
    void yearDayCorrespondsToDecember31() {
        assertEquals(LocalDate.of(2020, 12, 31),
                LocalDate.from(InternationalFixedDate.of(2020, 13, 29)));
    }

    /**
     * Verifies: Alternative Chronologies — the leap day is day 29 of month 6,
     * present only in leap years, corresponding to ISO June 17.
     */
    @Test
    void leapDayCorrespondsToJune17() {
        assertEquals(LocalDate.of(2020, 6, 17),
                LocalDate.from(InternationalFixedDate.of(2020, 6, 29)));
    }

    /**
     * Verifies: Alternative Chronologies — the leap rule is the ISO rule: 2020
     * is a leap year, 1900 is not.
     */
    @Test
    void leapRuleIsGregorian() {
        assertTrue(InternationalFixedChronology.INSTANCE.isLeapYear(2020));
        assertFalse(InternationalFixedChronology.INSTANCE.isLeapYear(1900));
    }

    /**
     * Verifies: Alternative Chronologies — month lengths are 28, with 29 for
     * month 13 and for month 6 in a leap year.
     */
    @Test
    void monthLengthsIncludeSpecialDays() {
        assertEquals(28, InternationalFixedDate.of(2020, 1, 1).lengthOfMonth());
        assertEquals(29, InternationalFixedDate.of(2020, 6, 1).lengthOfMonth());
        assertEquals(29, InternationalFixedDate.of(2019, 13, 1).lengthOfMonth());
    }

    /**
     * Verifies: Alternative Chronologies — the year length is 366 in a leap
     * year and 365 otherwise.
     */
    @Test
    void yearLengthFollowsLeapRule() {
        assertEquals(366, InternationalFixedDate.of(2020, 1, 1).lengthOfYear());
        assertEquals(365, InternationalFixedDate.of(2019, 1, 1).lengthOfYear());
    }

    /**
     * Verifies: Alternative Chronologies — month arithmetic from the year day
     * lands on the last ordinary day of the target month.
     */
    @Test
    void plusMonthFromYearDayLandsOnOrdinaryDay() {
        assertEquals(InternationalFixedDate.of(2021, 1, 28),
                InternationalFixedDate.of(2020, 13, 29).plus(1, ChronoUnit.MONTHS));
    }

    /**
     * Verifies: Alternative Chronologies — the chronology id is "Ifc".
     */
    @Test
    void chronologyIdIsIfc() {
        assertEquals("Ifc", InternationalFixedChronology.INSTANCE.getId());
    }
}
