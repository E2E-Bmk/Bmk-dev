package atomic;

import com.cronutils.mapper.WeekDay;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

public class WeekDayTest {
    /** Verifies: CRON-MAP-012. */
    @Test public void testConstructorFailsIfMondayDoWNegative() {
        assertThrows(IllegalArgumentException.class, () -> new WeekDay(-1, false));
    }

    /** Verifies: CRON-MAP-011, CRON-MAP-017. */
    @Test public void testMapIntervalWithZeroNotStartingMonday() {
        assertEquals(0, new WeekDay(1, false).mapTo(7, new WeekDay(1, true)));
    }

    /** Verifies: CRON-MAP-011, CRON-MAP-017. */
    @Test public void testMapIntervalWithZeroStartingMonday() {
        assertEquals(0, new WeekDay(1, false).mapTo(1, new WeekDay(0, true)));
    }

    /** Verifies: CRON-MAP-011, CRON-MAP-017. */
    @Test public void testMapIntervalWithoutZeroStartingMonday() {
        assertEquals(7, new WeekDay(1, false).mapTo(7, new WeekDay(1, false)));
    }

    /** Verifies: CRON-MAP-011, CRON-MAP-017. */
    @Test public void testMapIntervalWithoutZeroStartingSunday() {
        assertEquals(1, new WeekDay(1, false).mapTo(7, new WeekDay(2, false)));
    }
}

