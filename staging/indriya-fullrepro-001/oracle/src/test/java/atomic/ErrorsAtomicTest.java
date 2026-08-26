package atomic;

import static org.junit.jupiter.api.Assertions.assertThrows;

import javax.measure.IncommensurableException;
import javax.measure.format.MeasurementParseException;
import javax.measure.quantity.Mass;
import javax.measure.quantity.Time;
import org.junit.jupiter.api.Test;
import tech.units.indriya.format.SimpleQuantityFormat;
import tech.units.indriya.format.SimpleUnitFormat;
import tech.units.indriya.quantity.Quantities;
import tech.units.indriya.unit.Units;

/** Error taxonomy: each declared failure condition raises its declared type. */
class ErrorsAtomicTest {

    /**
     * Verifies: Error Semantics — the text factory raises
     * MeasurementParseException on unparseable text.
     */
    @Test
    void textFactoryUnparseableRaises() {
        assertThrows(MeasurementParseException.class,
                () -> Quantities.getQuantity("garbage input"));
    }

    /**
     * Verifies: Error Semantics — the quantity format raises
     * MeasurementParseException when the text has no leading parseable number.
     */
    @Test
    void formatParseWithoutNumberRaises() {
        assertThrows(MeasurementParseException.class,
                () -> SimpleQuantityFormat.getInstance().parse("threeve m"));
    }

    /**
     * Verifies: Error Semantics — the unit format raises
     * MeasurementParseException on an unknown symbol.
     */
    @Test
    void unitParseUnknownRaises() {
        assertThrows(MeasurementParseException.class,
                () -> SimpleUnitFormat.getInstance().parse("blorbs"));
    }

    /**
     * Verifies: Error Semantics — Quantity.asType raises ClassCastException on
     * a dimension-incompatible quantity type.
     */
    @Test
    void quantityAsTypeMismatchRaises() {
        assertThrows(ClassCastException.class,
                () -> Quantities.getQuantity(3, Units.METRE).asType(Mass.class));
    }

    /**
     * Verifies: Error Semantics — Unit.asType raises ClassCastException on a
     * dimension-incompatible quantity type.
     */
    @Test
    void unitAsTypeMismatchRaises() {
        assertThrows(ClassCastException.class, () -> Units.METRE.asType(Time.class));
    }

    /**
     * Verifies: Error Semantics — getConverterToAny raises the checked
     * IncommensurableException between incompatible dimensions.
     */
    @Test
    void converterToAnyRaisesChecked() {
        assertThrows(IncommensurableException.class,
                () -> Units.SECOND.getConverterToAny(Units.KILOGRAM));
    }
}
