package atomic;

import com.cronutils.model.field.expression.Between;
import com.cronutils.model.field.value.IntegerFieldValue;
import com.cronutils.model.field.value.SpecialChar;
import com.cronutils.model.field.value.SpecialCharFieldValue;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

public class BetweenTest {
    /** Verifies: CRON-DEF-016. */
    @Test public void testGetFrom() { assertEquals(1, new Between(new IntegerFieldValue(1), new IntegerFieldValue(5)).getFrom().getValue()); }

    /** Verifies: CRON-DEF-016. */
    @Test public void testGetTo() { assertEquals(5, new Between(new IntegerFieldValue(1), new IntegerFieldValue(5)).getTo().getValue()); }

    /** Verifies: CRON-DEF-017, CRON-DEF-028. */
    @Test public void testNonNumericRangeSupported() {
        Between expression = new Between(new SpecialCharFieldValue(SpecialChar.L), new IntegerFieldValue(5));
        assertEquals(SpecialChar.L, expression.getFrom().getValue());
        assertEquals("L-5", expression.asString());
    }
}

