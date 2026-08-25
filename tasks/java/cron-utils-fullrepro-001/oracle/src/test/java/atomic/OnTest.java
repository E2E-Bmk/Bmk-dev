package atomic;

import com.cronutils.model.field.expression.On;
import com.cronutils.model.field.value.IntegerFieldValue;
import com.cronutils.model.field.value.SpecialChar;
import com.cronutils.model.field.value.SpecialCharFieldValue;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

public class OnTest {
    /** Verifies: CRON-DEF-025. */
    @Test public void testGetTime() { assertEquals(5, new On(new IntegerFieldValue(5)).getTime().getValue()); }

    /** Verifies: CRON-DEF-019, CRON-DEF-025. */
    @Test public void testGetNth() { assertEquals(3, new On(new IntegerFieldValue(5), new SpecialCharFieldValue(SpecialChar.HASH), new IntegerFieldValue(3)).getNth().getValue()); }

    /** Verifies: CRON-DEF-023, CRON-DEF-025. */
    @Test public void testOnlyNthFails() { assertThrows(RuntimeException.class, () -> new On(null, new SpecialCharFieldValue(SpecialChar.HASH), new IntegerFieldValue(3))); }

    /** Verifies: CRON-DEF-019, CRON-DEF-025. */
    @Test public void testAsStringJustNumber() { assertEquals("3", new On(new IntegerFieldValue(3)).asString()); }

    /** Verifies: CRON-DEF-019, CRON-DEF-025. */
    @Test public void testAsStringSpecialCharW() { assertEquals("1W", new On(new IntegerFieldValue(1), new SpecialCharFieldValue(SpecialChar.W)).asString()); }

    /** Verifies: CRON-DEF-019, CRON-DEF-025. */
    @Test public void testAsStringSpecialCharL() { assertEquals("L", new On(new SpecialCharFieldValue(SpecialChar.L)).asString()); }

    /** Verifies: CRON-DEF-019, CRON-DEF-025. */
    @Test public void testAsStringSpecialCharLWithNth() { assertEquals("L-3", new On(new IntegerFieldValue(-1), new SpecialCharFieldValue(SpecialChar.L), new IntegerFieldValue(3)).asString()); }

    /** Verifies: CRON-DEF-019, CRON-DEF-025. */
    @Test public void testAsStringWithNth() { assertEquals("3#4", new On(new IntegerFieldValue(3), new SpecialCharFieldValue(SpecialChar.HASH), new IntegerFieldValue(4)).asString()); }
}

