package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;

import javax.measure.Quantity;
import javax.measure.quantity.Temperature;
import org.junit.jupiter.api.Test;
import support.Values;
import tech.units.indriya.ComparableQuantity;
import tech.units.indriya.quantity.Quantities;
import tech.units.indriya.unit.Units;

/** Scale semantics: ABSOLUTE versus RELATIVE on offset units. */
class ScaleAtomicTest {

    private static ComparableQuantity<Temperature> relativeCelsius(int value) {
        return Quantities.getQuantity(value, Units.CELSIUS, Quantity.Scale.RELATIVE);
    }

    /**
     * Verifies: Scales and Temperature Arithmetic — the default scale is
     * ABSOLUTE.
     */
    @Test
    void defaultScaleIsAbsolute() {
        assertEquals(Quantity.Scale.ABSOLUTE,
                Quantities.getQuantity(5, Units.METRE).getScale());
    }

    /**
     * Verifies: Scales and Temperature Arithmetic — the three-argument factory
     * builds a RELATIVE quantity reported by getScale.
     */
    @Test
    void explicitRelativeScale() {
        assertEquals(Quantity.Scale.RELATIVE, relativeCelsius(10).getScale());
    }

    /**
     * Verifies: Scales and Temperature Arithmetic — an ABSOLUTE Celsius value
     * converts to kelvin with the offset applied.
     */
    @Test
    void absoluteCelsiusConvertsWithOffset() {
        assertEquals(283.15, Values.dbl(Quantities.getQuantity(10, Units.CELSIUS)
                .to(Units.KELVIN)));
    }

    /**
     * Verifies: Scales and Temperature Arithmetic — a RELATIVE Celsius delta
     * converts by scale factor only, in both directions.
     */
    @Test
    void relativeCelsiusConvertsByFactorOnly() {
        ComparableQuantity<Temperature> kelvin = relativeCelsius(10).to(Units.KELVIN);
        assertEquals(10.0, Values.dbl(kelvin));
        assertEquals(Quantity.Scale.RELATIVE, kelvin.getScale());
        ComparableQuantity<Temperature> back = kelvin.to(Units.CELSIUS);
        assertEquals(10.0, Values.dbl(back));
        assertEquals(Quantity.Scale.RELATIVE, back.getScale());
    }

    /**
     * Verifies: Scales and Temperature Arithmetic — adding two ABSOLUTE
     * offset-unit quantities operates on the absolute scale and re-expresses
     * the kelvin sum in the left unit.
     */
    @Test
    void absolutePlusAbsoluteSumsOnAbsoluteScale() {
        ComparableQuantity<Temperature> sum = Quantities.getQuantity(20, Units.CELSIUS)
                .add(Quantities.getQuantity(10, Units.CELSIUS));
        assertEquals(303.15, Values.dbl(sum));
        assertEquals(Quantity.Scale.ABSOLUTE, sum.getScale());
        assertEquals(Units.CELSIUS, sum.getUnit());
    }

    /**
     * Verifies: Scales and Temperature Arithmetic — adding a RELATIVE right
     * operand to an ABSOLUTE left operand treats the right as a delta.
     */
    @Test
    void absolutePlusRelativeTreatsDelta() {
        ComparableQuantity<Temperature> sum =
                Quantities.getQuantity(20, Units.CELSIUS).add(relativeCelsius(10));
        assertEquals(30.0, Values.dbl(sum));
        assertEquals(Quantity.Scale.ABSOLUTE, sum.getScale());
    }

    /**
     * Verifies: Scales and Temperature Arithmetic — adding two RELATIVE
     * quantities adds the deltas and stays on the relative scale.
     */
    @Test
    void relativePlusRelativeAddsDeltas() {
        ComparableQuantity<Temperature> sum = relativeCelsius(10).add(relativeCelsius(10));
        assertEquals(20.0, Values.dbl(sum));
        assertEquals(Quantity.Scale.RELATIVE, sum.getScale());
    }
}
