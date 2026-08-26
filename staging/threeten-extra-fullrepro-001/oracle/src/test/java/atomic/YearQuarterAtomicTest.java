package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.time.LocalDate;
import org.junit.jupiter.api.Test;
import org.threeten.extra.Quarter;
import org.threeten.extra.YearQuarter;

/** Year-quarter partial construction, navigation, and quarter lengths. */
class YearQuarterAtomicTest {

    /**
     * Verifies: Year-Based Partials — of accepts a Quarter or an int and
     * toString renders the quarter form.
     */
    @Test
    void ofRendersQuarterForm() {
        assertEquals("2020-Q1", YearQuarter.of(2020, Quarter.Q1).toString());
        assertEquals(YearQuarter.of(2020, Quarter.Q1), YearQuarter.of(2020, 1));
    }

    /**
     * Verifies: Year-Based Partials — parse reads the quarter form back.
     */
    @Test
    void parseReadsQuarterForm() {
        assertEquals(YearQuarter.of(2020, 1), YearQuarter.parse("2020-Q1"));
    }

    /**
     * Verifies: Year-Based Partials — atDay returns the date of the given day
     * within the quarter.
     */
    @Test
    void atDayReturnsDateWithinQuarter() {
        assertEquals(LocalDate.of(2020, 1, 31), YearQuarter.of(2020, 1).atDay(31));
    }

    /**
     * Verifies: Year-Based Partials — atEndOfQuarter returns the last date of
     * the quarter.
     */
    @Test
    void atEndOfQuarterReturnsLastDate() {
        assertEquals(LocalDate.of(2020, 3, 31), YearQuarter.of(2020, 1).atEndOfQuarter());
    }

    /**
     * Verifies: Year-Based Partials — lengthOfQuarter reflects the leap status
     * of the year.
     */
    @Test
    void lengthOfQuarterReflectsLeapYear() {
        assertEquals(91, YearQuarter.of(2020, 1).lengthOfQuarter());
        assertEquals(90, YearQuarter.of(2019, 1).lengthOfQuarter());
    }

    /**
     * Verifies: Year-Based Partials — isLeapYear reports the year's leap
     * status.
     */
    @Test
    void isLeapYearReportsYearStatus() {
        assertTrue(YearQuarter.of(2020, 1).isLeapYear());
        assertFalse(YearQuarter.of(2019, 1).isLeapYear());
    }

    /**
     * Verifies: Year-Based Partials — isValidDay tests the day against the
     * quarter length.
     */
    @Test
    void isValidDayTestsQuarterLength() {
        assertTrue(YearQuarter.of(2020, 1).isValidDay(91));
        assertFalse(YearQuarter.of(2020, 1).isValidDay(92));
    }

    /**
     * Verifies: Year-Based Partials — plusQuarters and minusQuarters navigate
     * across year boundaries.
     */
    @Test
    void quarterArithmeticNavigates() {
        assertEquals(YearQuarter.of(2020, 4), YearQuarter.of(2020, 1).plusQuarters(3));
        assertEquals(YearQuarter.of(2019, 4), YearQuarter.of(2020, 1).minusQuarters(1));
    }

    /**
     * Verifies: Year-Based Partials — withQuarter and withYear replace one
     * component.
     */
    @Test
    void withReplacesOneComponent() {
        assertEquals(YearQuarter.of(2020, 3), YearQuarter.of(2020, 1).withQuarter(3));
        assertEquals(YearQuarter.of(2021, 1), YearQuarter.of(2020, 1).withYear(2021));
    }

    /**
     * Verifies: Year-Based Partials — from derives the quarter of a date.
     */
    @Test
    void fromDerivesQuarterOfDate() {
        assertEquals(YearQuarter.of(2020, 2), YearQuarter.from(LocalDate.of(2020, 5, 5)));
    }

    /**
     * Verifies: Year-Based Partials — Quarter.of maps 1-4 and Quarter.from
     * derives the quarter of a date.
     */
    @Test
    void quarterEnumFactoryAndFrom() {
        assertEquals(Quarter.Q2, Quarter.of(2));
        assertEquals(Quarter.Q2, Quarter.from(LocalDate.of(2020, 5, 5)));
    }
}
