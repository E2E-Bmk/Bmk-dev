package atomic;

import com.cronutils.mapper.ConstantsMapper;
import com.cronutils.mapper.WeekDay;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

public class ConstantsMapperTest {
    /** Verifies: CRON-MAP-010, CRON-MAP-011, CRON-MAP-015. */
    @Test public void testWeekDayMappingQuartzToJDK8time() {
        WeekDay source = ConstantsMapper.QUARTZ_WEEK_DAY;
        WeekDay target = ConstantsMapper.JAVA8;
        for (int value = 2; value < 8; value++) assertEquals(value - 1, ConstantsMapper.weekDayMapping(source, target, value));
        assertEquals(7, ConstantsMapper.weekDayMapping(source, target, 1));
    }

    /** Verifies: CRON-MAP-010, CRON-MAP-011, CRON-MAP-015. */
    @Test public void testWeekDayMappingJDK8ToQuartz() {
        for (int value = 1; value < 7; value++) assertEquals(value + 1, ConstantsMapper.weekDayMapping(ConstantsMapper.JAVA8, ConstantsMapper.QUARTZ_WEEK_DAY, value));
        assertEquals(1, ConstantsMapper.weekDayMapping(ConstantsMapper.JAVA8, ConstantsMapper.QUARTZ_WEEK_DAY, 7));
    }

    /** Verifies: CRON-MAP-010, CRON-MAP-011, CRON-MAP-015. */
    @Test public void testWeekDayMappingQuartzToCrontab() {
        for (int value = 1; value < 7; value++) assertEquals(value - 1, ConstantsMapper.weekDayMapping(ConstantsMapper.QUARTZ_WEEK_DAY, ConstantsMapper.CRONTAB_WEEK_DAY, value));
    }

    /** Verifies: CRON-MAP-010, CRON-MAP-011, CRON-MAP-015. */
    @Test public void testWeekDayMappingCrontabToQuartz() {
        for (int value = 0; value < 7; value++) assertEquals(value + 1, ConstantsMapper.weekDayMapping(ConstantsMapper.CRONTAB_WEEK_DAY, ConstantsMapper.QUARTZ_WEEK_DAY, value));
    }

    /** Verifies: CRON-MAP-010, CRON-MAP-011, CRON-MAP-015. */
    @Test public void testWeekDayMappingCrontabToJDK8() {
        for (int value = 1; value < 7; value++) assertEquals(value, ConstantsMapper.weekDayMapping(ConstantsMapper.CRONTAB_WEEK_DAY, ConstantsMapper.JAVA8, value));
        assertEquals(7, ConstantsMapper.weekDayMapping(ConstantsMapper.CRONTAB_WEEK_DAY, ConstantsMapper.JAVA8, 0));
    }

    /** Verifies: CRON-MAP-010, CRON-MAP-011, CRON-MAP-015. */
    @Test public void testWeekDayMappingJDK8ToCrontab() {
        for (int value = 1; value < 7; value++) assertEquals(value, ConstantsMapper.weekDayMapping(ConstantsMapper.JAVA8, ConstantsMapper.CRONTAB_WEEK_DAY, value));
        assertEquals(0, ConstantsMapper.weekDayMapping(ConstantsMapper.JAVA8, ConstantsMapper.CRONTAB_WEEK_DAY, 7));
    }
}

