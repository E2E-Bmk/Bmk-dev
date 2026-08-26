package integration;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.time.LocalDate;
import java.time.chrono.ChronoLocalDate;
import java.time.temporal.ChronoUnit;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.threeten.extra.chrono.CopticChronology;
import org.threeten.extra.chrono.CopticDate;
import org.threeten.extra.chrono.InternationalFixedChronology;
import org.threeten.extra.chrono.InternationalFixedDate;
import org.threeten.extra.chrono.JulianChronology;
import org.threeten.extra.chrono.JulianDate;

/**
 * Round trips and epoch-day agreement between ISO dates and the three
 * alternative chronologies.
 */
class ChronologyRoundTripIntegrationTest {

    private static final List<LocalDate> SAMPLES = List.of(
            LocalDate.of(2020, 1, 1), LocalDate.of(2020, 2, 29), LocalDate.of(2020, 6, 17),
            LocalDate.of(2020, 12, 31), LocalDate.of(1999, 7, 4), LocalDate.of(1970, 1, 1));

    /**
     * Verifies: Cross-View Invariants — Coptic conversion round-trips every
     * sample ISO date.
     * Depends-On: newYearCorrespondsToIsoDate, isoNewYearCorrespondsToCopticDate.
     */
    @Test
    void copticRoundTripsSampleDates() {
        for (LocalDate iso : SAMPLES) {
            assertEquals(iso, LocalDate.from(CopticDate.from(iso)));
        }
    }

    /**
     * Verifies: Cross-View Invariants — Julian conversion round-trips every
     * sample ISO date.
     * Depends-On: thirteenDayOffsetFromIso.
     */
    @Test
    void julianRoundTripsSampleDates() {
        for (LocalDate iso : SAMPLES) {
            assertEquals(iso, LocalDate.from(JulianDate.from(iso)));
        }
    }

    /**
     * Verifies: Cross-View Invariants — International Fixed conversion
     * round-trips every sample ISO date including the special days.
     * Depends-On: januaryFirstAlignsWithIso, yearDayCorrespondsToDecember31, leapDayCorrespondsToJune17.
     */
    @Test
    void internationalFixedRoundTripsSampleDates() {
        for (LocalDate iso : SAMPLES) {
            assertEquals(iso, LocalDate.from(InternationalFixedDate.from(iso)));
        }
    }

    /**
     * Verifies: Cross-View Invariants — dateEpochDay agrees with from for each
     * chronology on each sample date.
     * Depends-On: chronologyConstructsDates, chronologyIdIsIfc.
     */
    @Test
    void epochDayConstructionAgreesWithFrom() {
        for (LocalDate iso : SAMPLES) {
            long epochDay = iso.toEpochDay();
            assertEquals(CopticDate.from(iso), CopticChronology.INSTANCE.dateEpochDay(epochDay));
            assertEquals(JulianDate.from(iso), JulianChronology.INSTANCE.dateEpochDay(epochDay));
            assertEquals(InternationalFixedDate.from(iso),
                    InternationalFixedChronology.INSTANCE.dateEpochDay(epochDay));
        }
    }

    /**
     * Verifies: Cross-View Invariants — the three calendars assign the same
     * epoch day to the same moment: converting a date between calendars
     * through LocalDate preserves it.
     * Depends-On: newYearCorrespondsToIsoDate, thirteenDayOffsetFromIso, midYearDateLandsInThirteenMonthLayout.
     */
    @Test
    void crossCalendarConversionPreservesDate() {
        LocalDate iso = LocalDate.of(2020, 9, 11);
        CopticDate coptic = CopticDate.from(iso);
        JulianDate julian = JulianDate.from(LocalDate.from(coptic));
        InternationalFixedDate ifc = InternationalFixedDate.from(LocalDate.from(julian));
        assertEquals(iso, LocalDate.from(ifc));
    }

    /**
     * Verifies: Cross-View Invariants — each chronology's leap classification
     * matches its year length on the same year.
     * Depends-On: leapRuleIsYearMod4Equals3, leapRuleHasNoCenturyException, leapRuleIsGregorian.
     */
    @Test
    void leapClassificationMatchesYearLength() {
        assertEquals(CopticChronology.INSTANCE.isLeapYear(1739),
                CopticDate.of(1739, 1, 1).lengthOfYear() == 366);
        assertEquals(JulianChronology.INSTANCE.isLeapYear(1900),
                JulianDate.of(1900, 2, 1).lengthOfMonth() == 29);
        assertEquals(InternationalFixedChronology.INSTANCE.isLeapYear(2020),
                InternationalFixedDate.of(2020, 1, 1).lengthOfYear() == 366);
    }

    /**
     * Verifies: Cross-View Invariants — calendar arithmetic agrees with
     * conversion: adding days in a chronology matches adding days in ISO.
     * Depends-On: arithmeticOperatesInCopticUnits, plusYearFromLeapDayLandsOnFeb28.
     */
    @Test
    void dayArithmeticAgreesWithIso() {
        LocalDate iso = LocalDate.of(2020, 3, 1);
        for (int days : new int[] {1, 30, 365}) {
            ChronoLocalDate advanced = CopticDate.from(iso).plus(days, ChronoUnit.DAYS);
            assertEquals(iso.plusDays(days), LocalDate.from(advanced));
        }
    }

    /**
     * Verifies: Cross-View Invariants — until between two chronology dates,
     * added back with plus, restores the later date.
     * Depends-On: untilMeasuresInJulianUnits, arithmeticOperatesInCopticUnits.
     */
    @Test
    void untilRoundTripsThroughPlus() {
        JulianDate start = JulianDate.of(2020, 1, 1);
        JulianDate end = JulianDate.of(2020, 3, 1);
        assertEquals(end, start.plus(start.until(end)));
    }
}
