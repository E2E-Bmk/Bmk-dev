package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.threeten.extra.chrono.JulianChronology;
import org.threeten.extra.chrono.JulianDate;
import org.threeten.extra.chrono.JulianEra;

/** Julian calendar dates: leap rule, ISO offset, eras, arithmetic. */
class JulianAtomicTest {

    /**
     * Verifies: Alternative Chronologies — a Julian date renders with its
     * calendar name and era.
     */
    @Test
    void toStringRendersCalendarAndEra() {
        assertEquals("Julian AD 2020-02-29", JulianDate.of(2020, 2, 29).toString());
    }

    /**
     * Verifies: Alternative Chronologies — the Julian calendar runs 13 days
     * behind ISO in the current era, both directions.
     */
    @Test
    void thirteenDayOffsetFromIso() {
        assertEquals(LocalDate.of(2020, 3, 13), LocalDate.from(JulianDate.of(2020, 2, 29)));
        assertEquals(JulianDate.of(2020, 2, 29), JulianDate.from(LocalDate.of(2020, 3, 13)));
    }

    /**
     * Verifies: Alternative Chronologies — every fourth year is a Julian leap
     * year with no century exception.
     */
    @Test
    void leapRuleHasNoCenturyException() {
        assertTrue(JulianChronology.INSTANCE.isLeapYear(1900));
        assertEquals(LocalDate.of(1900, 3, 13), LocalDate.from(JulianDate.of(1900, 2, 29)));
    }

    /**
     * Verifies: Alternative Chronologies — February has 29 days in a Julian
     * leap year and 28 otherwise.
     */
    @Test
    void februaryLengthFollowsJulianRule() {
        assertEquals(29, JulianDate.of(1900, 2, 1).lengthOfMonth());
        assertEquals(28, JulianDate.of(1901, 2, 1).lengthOfMonth());
    }

    /**
     * Verifies: Alternative Chronologies — adding a year to a Julian leap day
     * lands on February 28 of the following year.
     */
    @Test
    void plusYearFromLeapDayLandsOnFeb28() {
        assertEquals(JulianDate.of(1901, 2, 28), JulianDate.of(1900, 2, 29).plus(1, ChronoUnit.YEARS));
    }

    /**
     * Verifies: Alternative Chronologies — the eras are BC and AD.
     */
    @Test
    void erasAreBcAndAd() {
        assertEquals(JulianEra.AD, JulianDate.of(2020, 2, 29).getEra());
        assertEquals(List.of(JulianEra.BC, JulianEra.AD), JulianChronology.INSTANCE.eras());
    }

    /**
     * Verifies: Alternative Chronologies — until measures in Julian calendar
     * units and the chronology id is "Julian".
     */
    @Test
    void untilMeasuresInJulianUnits() {
        assertEquals("Julian", JulianChronology.INSTANCE.getId());
        assertEquals("Julian P2M",
                JulianDate.of(2020, 1, 1).until(JulianDate.of(2020, 3, 1)).toString());
    }
}
