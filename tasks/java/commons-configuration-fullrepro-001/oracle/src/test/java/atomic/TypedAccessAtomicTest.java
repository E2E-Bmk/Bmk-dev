package atomic;

import static org.junit.jupiter.api.Assertions.*;

import java.math.BigDecimal;
import java.math.BigInteger;
import java.time.Duration;
import java.util.Arrays;
import java.util.NoSuchElementException;

import org.apache.commons.configuration2.BaseConfiguration;
import org.apache.commons.configuration2.ConfigurationDecoder;
import org.apache.commons.configuration2.convert.DefaultListDelimiterHandler;
import org.apache.commons.configuration2.ex.ConversionException;
import org.junit.jupiter.api.Test;

class TypedAccessAtomicTest {
    private enum Mode { FAST, SAFE }

    /** Verifies: CC-PROP-009 */
    @Test void compatibleScalarsConvertToRequestedTypes() {
        BaseConfiguration c = new BaseConfiguration();
        c.setProperty("n", "42"); c.setProperty("yes", "true"); c.setProperty("decimal", "1.25");
        c.setProperty("duration", "PT15S"); c.setProperty("mode", "FAST");
        assertAll(() -> assertEquals(42, c.getInt("n")), () -> assertTrue(c.getBoolean("yes")),
                () -> assertEquals(new BigInteger("42"), c.get(BigInteger.class, "n")),
                () -> assertEquals(new BigDecimal("1.25"), c.get(BigDecimal.class, "decimal")),
                () -> assertEquals(Duration.ofSeconds(15), c.get(Duration.class, "duration")),
                () -> assertEquals(Mode.FAST, c.get(Mode.class, "mode")));
    }

    /** Verifies: CC-PROP-010, CC-PROP-011 */
    @Test void scalarUsesFirstValueAndContainersPreserveAllOrder() {
        BaseConfiguration c = new BaseConfiguration(); c.addProperty("n", "3"); c.addProperty("n", "4");
        assertAll(() -> assertEquals("3", c.getString("n")),
                () -> assertEquals(Arrays.asList(3, 4), c.getList(Integer.class, "n")),
                () -> assertArrayEquals(new String[] {"3", "4"}, c.getStringArray("n")));
    }

    /** Verifies: CC-PROP-012, CC-PROP-013 */
    @Test void missingObjectGetterUsesDefaultOrNullWithoutMutation() {
        BaseConfiguration c = new BaseConfiguration();
        assertAll(() -> assertEquals("fallback", c.getString("missing", "fallback")),
                () -> assertNull(c.getString("missing")), () -> assertFalse(c.containsKey("missing")));
    }

    /** Verifies: CC-PROP-014 */
    @Test void strictMissingObjectGetterThrows() {
        BaseConfiguration c = new BaseConfiguration(); c.setThrowExceptionOnMissing(true);
        assertThrows(NoSuchElementException.class, () -> c.getString("missing"));
    }

    /** Verifies: CC-PROP-015, CC-PROP-016 */
    @Test void primitiveMissingThrowsButContainersRemainEmpty() {
        BaseConfiguration c = new BaseConfiguration(); c.setThrowExceptionOnMissing(true);
        assertAll(() -> assertThrows(NoSuchElementException.class, () -> c.getInt("missing")),
                () -> assertTrue(c.getList("missing").isEmpty()),
                () -> assertArrayEquals(new String[0], c.getStringArray("missing")));
    }

    /** Verifies: CC-PROP-017 */
    @Test void incompatiblePresentValueRaisesConversionException() {
        BaseConfiguration c = new BaseConfiguration(); c.setProperty("n", "not-an-integer");
        assertThrows(ConversionException.class, () -> c.getInt("n"));
    }

    /** Verifies: CC-PROP-018, CC-PROP-019, CC-PROP-020 */
    @Test void delimiterHandlerControlsExpansion() {
        BaseConfiguration split = new BaseConfiguration();
        split.setListDelimiterHandler(new DefaultListDelimiterHandler(',')); split.setProperty("k", "a,b,c");
        BaseConfiguration unsplit = new BaseConfiguration(); unsplit.setProperty("k", "a,b,c");
        assertAll(() -> assertEquals(Arrays.asList("a", "b", "c"), split.getList("k")),
                () -> assertEquals(Arrays.asList("a,b,c"), unsplit.getList("k")));
    }

    /** Verifies: CC-PROP-021, CC-PROP-022, CC-PROP-023 */
    @Test void encodedStringRequiresAndUsesNonNullDecoder() {
        BaseConfiguration c = new BaseConfiguration(); c.setProperty("secret", "abc");
        ConfigurationDecoder decoder = value -> "decoded-" + value;
        assertAll(() -> assertEquals("decoded-abc", c.getEncodedString("secret", decoder)),
                () -> assertThrows(IllegalStateException.class, () -> c.getEncodedString("secret")),
                () -> assertThrows(IllegalArgumentException.class, () -> c.getEncodedString("secret", null)));
    }
}
