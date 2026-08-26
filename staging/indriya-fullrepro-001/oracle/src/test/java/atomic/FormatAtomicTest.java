package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import javax.measure.MetricPrefix;
import javax.measure.Quantity;
import javax.measure.Unit;
import javax.measure.format.MeasurementParseException;
import javax.measure.quantity.Speed;
import org.junit.jupiter.api.Test;
import tech.units.indriya.format.SimpleQuantityFormat;
import tech.units.indriya.format.SimpleUnitFormat;
import tech.units.indriya.quantity.Quantities;
import tech.units.indriya.unit.Units;

/** Formatting and parsing through the simple format classes. */
class FormatAtomicTest {

    private final SimpleQuantityFormat quantityFormat = SimpleQuantityFormat.getInstance();
    private final SimpleUnitFormat unitFormat = SimpleUnitFormat.getInstance();

    /**
     * Verifies: Formatting and Parsing — format renders "value unit" using the
     * unit's symbol form.
     */
    @Test
    void quantityFormatRendersValueUnit() {
        assertEquals("10 m", quantityFormat.format(Quantities.getQuantity(10, Units.METRE)));
        assertEquals("1 km", quantityFormat.format(
                Quantities.getQuantity(1, MetricPrefix.KILO(Units.METRE))));
        assertEquals("5 m/s", quantityFormat.format(
                Quantities.getQuantity(5, Units.METRE_PER_SECOND)));
    }

    /**
     * Verifies: Formatting and Parsing — parse reads value and unit back from
     * the same form: the result denotes the same measure as the named-constant
     * view and formats back to the input.
     */
    @Test
    void quantityParseReadsBack() {
        Quantity<?> parsed = quantityFormat.parse("36 km/h");
        assertEquals(36, parsed.getValue().intValue());
        assertEquals("36 km/h", quantityFormat.format(parsed));
        assertTrue(Quantities.getQuantity(parsed.getValue(),
                        parsed.getUnit().asType(Speed.class))
                .isEquivalentTo(Quantities.getQuantity(36, Units.KILOMETRE_PER_HOUR)));
    }

    /**
     * Verifies: Formatting and Parsing — format(parse(s)) returns s for the
     * documented inputs.
     */
    @Test
    void quantityFormatRoundTrips() {
        for (String text : new String[] {"10 m", "1.5 km", "36 km/h", "2.5 s", "7200 s"}) {
            assertEquals(text, quantityFormat.format(quantityFormat.parse(text)));
        }
    }

    /**
     * Verifies: Formatting and Parsing — on whole-number base-unit text the
     * text factory and the quantity format parser return equal quantities.
     */
    @Test
    void factoryAgreesWithFormatParse() {
        assertEquals(quantityFormat.parse("10 m"), Quantities.getQuantity("10 m"));
        assertEquals(quantityFormat.parse("120 s"), Quantities.getQuantity("120 s"));
        assertEquals(Quantities.getQuantity(10, Units.METRE), Quantities.getQuantity("10 m"));
    }

    /**
     * Verifies: Formatting and Parsing — the unit format renders symbol forms
     * for prefixed and quotient units.
     */
    @Test
    void unitFormatRendersSymbols() {
        assertEquals("km", unitFormat.format(MetricPrefix.KILO(Units.METRE)));
        assertEquals("m/s", unitFormat.format(Units.METRE.divide(Units.SECOND)));
    }

    /**
     * Verifies: Formatting and Parsing — parsing "km" yields a unit equal to
     * the prefixed metre.
     */
    @Test
    void unitParsePrefixed() {
        assertEquals(MetricPrefix.KILO(Units.METRE), unitFormat.parse("km"));
    }

    /**
     * Verifies: Formatting and Parsing — parsing "m/s" yields a unit equal to
     * the metre-second quotient.
     */
    @Test
    void unitParseQuotient() {
        Unit<?> parsed = unitFormat.parse("m/s");
        assertEquals(Units.METRE.divide(Units.SECOND), parsed);
        assertEquals(Units.METRE_PER_SECOND, parsed);
    }

    /**
     * Verifies: Formatting and Parsing — an unknown unit symbol raises
     * MeasurementParseException.
     */
    @Test
    void unknownUnitSymbolRaises() {
        assertThrows(MeasurementParseException.class, () -> unitFormat.parse("zorkmid"));
    }

    /**
     * Verifies: Formatting and Parsing — quantity text without a leading
     * parseable number raises MeasurementParseException.
     */
    @Test
    void nonNumericQuantityTextRaises() {
        assertThrows(MeasurementParseException.class, () -> quantityFormat.parse("notanumber m"));
    }
}
