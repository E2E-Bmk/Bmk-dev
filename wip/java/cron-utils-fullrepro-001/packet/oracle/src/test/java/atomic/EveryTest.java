package atomic;

import com.cronutils.model.field.expression.Every;
import com.cronutils.model.field.expression.On;
import com.cronutils.model.field.value.IntegerFieldValue;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

public class EveryTest {
    /** Verifies: CRON-DEF-024. */
    @Test public void testGetTime() { assertEquals(5, new Every(new IntegerFieldValue(5)).getPeriod().getValue()); }

    /** Verifies: CRON-DEF-017, CRON-DEF-024, CRON-DEF-025. */
    @Test public void testAsString() { assertEquals("0/1", new Every(new On(new IntegerFieldValue(0)), new IntegerFieldValue(1)).asString()); }
}

