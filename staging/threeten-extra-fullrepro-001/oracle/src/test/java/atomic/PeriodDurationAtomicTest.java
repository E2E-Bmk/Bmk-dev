package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.time.Duration;
import java.time.LocalDateTime;
import java.time.Period;
import org.junit.jupiter.api.Test;
import org.threeten.extra.PeriodDuration;

/** Combined period-and-duration amount behavior. */
class PeriodDurationAtomicTest {

    /**
     * Verifies: Combined Period and Duration — of combines a period and a
     * duration and toString concatenates the parts.
     */
    @Test
    void ofCombinesPartsWithConcatenatedText() {
        PeriodDuration amount = PeriodDuration.of(Period.of(1, 2, 3), Duration.ofHours(4));
        assertEquals("P1Y2M3DT4H", amount.toString());
    }

    /**
     * Verifies: Combined Period and Duration — parse reads the concatenated
     * form back.
     */
    @Test
    void parseReadsConcatenatedForm() {
        assertEquals(PeriodDuration.of(Period.of(1, 2, 3), Duration.ofHours(4)),
                PeriodDuration.parse("P1Y2M3DT4H"));
    }

    /**
     * Verifies: Combined Period and Duration — ZERO has both parts zero and
     * renders as PT0S.
     */
    @Test
    void zeroRendersAsZeroDuration() {
        assertEquals("PT0S", PeriodDuration.ZERO.toString());
        assertEquals(Period.ZERO, PeriodDuration.ZERO.getPeriod());
        assertEquals(Duration.ZERO, PeriodDuration.ZERO.getDuration());
    }

    /**
     * Verifies: Combined Period and Duration — getPeriod and getDuration
     * return the constituent parts.
     */
    @Test
    void accessorsReturnParts() {
        PeriodDuration amount = PeriodDuration.of(Period.of(1, 2, 3), Duration.ofHours(4));
        assertEquals(Period.of(1, 2, 3), amount.getPeriod());
        assertEquals(Duration.ofHours(4), amount.getDuration());
    }

    /**
     * Verifies: Combined Period and Duration — plus combines part-wise.
     */
    @Test
    void plusCombinesPartWise() {
        PeriodDuration amount = PeriodDuration.of(Period.of(1, 2, 3), Duration.ofHours(4))
                .plus(PeriodDuration.of(Duration.ofMinutes(30)));
        assertEquals("P1Y2M3DT4H30M", amount.toString());
    }

    /**
     * Verifies: Combined Period and Duration — normalizedStandardDays moves
     * whole 24-hour blocks into the period's days.
     */
    @Test
    void normalizedStandardDaysMovesWholeDays() {
        assertEquals("P1DT6H",
                PeriodDuration.of(Duration.ofHours(30)).normalizedStandardDays().toString());
    }

    /**
     * Verifies: Combined Period and Duration — between measures the calendar
     * part and the remaining time part.
     */
    @Test
    void betweenSplitsCalendarAndTime() {
        PeriodDuration amount = PeriodDuration.between(
                LocalDateTime.of(2020, 1, 1, 0, 0), LocalDateTime.of(2021, 3, 4, 5, 0));
        assertEquals("P1Y2M3DT5H", amount.toString());
    }
}
