package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import org.junit.jupiter.api.Test;
import org.threeten.extra.chrono.CopticChronology;
import org.threeten.extra.chrono.CopticDate;
import org.threeten.extra.chrono.CopticEra;

/** Coptic calendar dates: structure, leap rule, conversion, arithmetic. */
class CopticAtomicTest {

    /**
     * Verifies: Alternative Chronologies — a Coptic date renders with its
     * calendar name and era.
     */
    @Test
    void toStringRendersCalendarAndEra() {
        assertEquals("Coptic AM 1737-01-01", CopticDate.of(1737, 1, 1).toString());
    }

    /**
     * Verifies: Alternative Chronologies — Coptic New Year 1737 corresponds to
     * ISO 2020-09-11 in both directions.
     */
    @Test
    void newYearCorrespondsToIsoDate() {
        assertEquals(LocalDate.of(2020, 9, 11), LocalDate.from(CopticDate.of(1737, 1, 1)));
        assertEquals(CopticDate.of(1737, 1, 1), CopticDate.from(LocalDate.of(2020, 9, 11)));
    }

    /**
     * Verifies: Alternative Chronologies — ISO 2020-01-01 corresponds to
     * Coptic 1736-04-22.
     */
    @Test
    void isoNewYearCorrespondsToCopticDate() {
        assertEquals(CopticDate.of(1736, 4, 22), CopticDate.from(LocalDate.of(2020, 1, 1)));
    }

    /**
     * Verifies: Alternative Chronologies — a Coptic year is a leap year
     * exactly when year modulo four is three.
     */
    @Test
    void leapRuleIsYearMod4Equals3() {
        assertTrue(CopticChronology.INSTANCE.isLeapYear(1739));
        assertFalse(CopticChronology.INSTANCE.isLeapYear(1740));
    }

    /**
     * Verifies: Alternative Chronologies — month 13 has six days in a leap
     * year and five otherwise; months 1-12 have 30 days.
     */
    @Test
    void monthLengthsFollowCopticStructure() {
        assertEquals(6, CopticDate.of(1739, 13, 1).lengthOfMonth());
        assertEquals(5, CopticDate.of(1740, 13, 1).lengthOfMonth());
        assertEquals(30, CopticDate.of(1737, 1, 1).lengthOfMonth());
    }

    /**
     * Verifies: Alternative Chronologies — the year length is 366 in a leap
     * year and 365 otherwise.
     */
    @Test
    void yearLengthFollowsLeapRule() {
        assertEquals(366, CopticDate.of(1739, 1, 1).lengthOfYear());
        assertEquals(365, CopticDate.of(1740, 1, 1).lengthOfYear());
    }

    /**
     * Verifies: Alternative Chronologies — the era in use is AM and
     * prolepticYear maps era-year through it.
     */
    @Test
    void eraIsAnnoMartyrum() {
        assertEquals(CopticEra.AM, CopticDate.of(1737, 1, 1).getEra());
        assertEquals(1737, CopticChronology.INSTANCE.prolepticYear(CopticEra.AM, 1737));
    }

    /**
     * Verifies: Alternative Chronologies — plus operates in Coptic months and
     * until returns a chronology-aware period.
     */
    @Test
    void arithmeticOperatesInCopticUnits() {
        assertEquals(CopticDate.of(1737, 2, 1), CopticDate.of(1737, 1, 1).plus(1, ChronoUnit.MONTHS));
        assertEquals("Coptic P1M4D",
                CopticDate.of(1737, 1, 1).until(CopticDate.of(1737, 2, 5)).toString());
    }

    /**
     * Verifies: Alternative Chronologies — the chronology constructs dates by
     * components and by epoch day, with id "Coptic".
     */
    @Test
    void chronologyConstructsDates() {
        assertEquals("Coptic", CopticChronology.INSTANCE.getId());
        assertEquals(CopticDate.of(1737, 1, 1), CopticChronology.INSTANCE.date(1737, 1, 1));
        assertEquals(CopticDate.of(1737, 1, 1),
                CopticChronology.INSTANCE.dateEpochDay(LocalDate.of(2020, 9, 11).toEpochDay()));
    }
}
