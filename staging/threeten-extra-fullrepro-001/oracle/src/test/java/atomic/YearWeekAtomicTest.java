package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.time.DayOfWeek;
import java.time.LocalDate;
import org.junit.jupiter.api.Test;
import org.threeten.extra.YearWeek;

/** Year-week partial construction, navigation, and week-53 handling. */
class YearWeekAtomicTest {

    /**
     * Verifies: Year-Based Partials — of addresses a week and toString renders
     * the ISO week form.
     */
    @Test
    void ofRendersIsoWeekForm() {
        assertEquals("2020-W53", YearWeek.of(2020, 53).toString());
    }

    /**
     * Verifies: Year-Based Partials — parse reads the week form back.
     */
    @Test
    void parseReadsWeekForm() {
        assertEquals(YearWeek.of(2020, 53), YearWeek.parse("2020-W53"));
    }

    /**
     * Verifies: Year-Based Partials — is53WeekYear reports whether the
     * week-based year has 53 weeks.
     */
    @Test
    void is53WeekYearClassifiesYears() {
        assertTrue(YearWeek.of(2020, 1).is53WeekYear());
        assertFalse(YearWeek.of(2019, 1).is53WeekYear());
    }

    /**
     * Verifies: Year-Based Partials — week 53 in a 52-week year resolves to
     * week 1 of the following year instead of raising.
     */
    @Test
    void week53InShortYearResolvesToNextYear() {
        assertEquals(YearWeek.of(2020, 1), YearWeek.of(2019, 53));
    }

    /**
     * Verifies: Year-Based Partials — atDay returns the date of the given day
     * within the week.
     */
    @Test
    void atDayReturnsDateOfWeekday() {
        assertEquals(LocalDate.of(2020, 12, 28), YearWeek.of(2020, 53).atDay(DayOfWeek.MONDAY));
    }

    /**
     * Verifies: Year-Based Partials — from derives the year-week of a date,
     * assigning early January to the previous week-based year when the week
     * belongs there.
     */
    @Test
    void fromDerivesWeekOfDate() {
        assertEquals(YearWeek.of(2020, 53), YearWeek.from(LocalDate.of(2021, 1, 1)));
    }

    /**
     * Verifies: Year-Based Partials — plusWeeks and minusWeeks roll across
     * year boundaries.
     */
    @Test
    void plusWeeksRollsAcrossYears() {
        assertEquals(YearWeek.of(2021, 1), YearWeek.of(2020, 53).plusWeeks(1));
        assertEquals(YearWeek.of(2020, 53), YearWeek.of(2021, 1).minusWeeks(1));
    }

    /**
     * Verifies: Year-Based Partials — withYear and withWeek replace one
     * component.
     */
    @Test
    void withReplacesOneComponent() {
        assertEquals(YearWeek.of(2021, 30), YearWeek.of(2020, 30).withYear(2021));
        assertEquals(YearWeek.of(2020, 1), YearWeek.of(2020, 30).withWeek(1));
    }

    /**
     * Verifies: Year-Based Partials — lengthOfYear is 371 days for a 53-week
     * year and 364 otherwise.
     */
    @Test
    void lengthOfYearReflectsWeekCount() {
        assertEquals(371, YearWeek.of(2020, 1).lengthOfYear());
        assertEquals(364, YearWeek.of(2019, 1).lengthOfYear());
    }

    /**
     * Verifies: Year-Based Partials — compareTo orders chronologically.
     */
    @Test
    void compareToOrdersChronologically() {
        assertTrue(YearWeek.of(2020, 1).compareTo(YearWeek.of(2020, 2)) < 0);
        assertTrue(YearWeek.of(2021, 1).compareTo(YearWeek.of(2020, 53)) > 0);
    }
}
