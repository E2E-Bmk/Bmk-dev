package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import javax.measure.IncommensurableException;
import javax.measure.MetricPrefix;
import javax.measure.UnitConverter;
import javax.measure.quantity.Length;
import javax.measure.quantity.Mass;
import javax.measure.quantity.Speed;
import javax.measure.quantity.Temperature;
import javax.measure.quantity.Time;
import org.junit.jupiter.api.Test;
import support.Values;
import tech.units.indriya.ComparableQuantity;
import tech.units.indriya.quantity.Quantities;
import tech.units.indriya.unit.Units;

/** Conversion: quantity re-expression and the underlying converter objects. */
class ConversionAtomicTest {

    /**
     * Verifies: Conversion and Converters — kilometre to metre converts
     * exactly and keeps the value integral.
     */
    @Test
    void kilometreToMetreIntegral() {
        ComparableQuantity<Length> m =
                Quantities.getQuantity(1, MetricPrefix.KILO(Units.METRE)).to(Units.METRE);
        assertEquals("1000", Values.num(m));
        assertEquals(Units.METRE, m.getUnit());
    }

    /**
     * Verifies: Conversion and Converters — hours re-express in seconds.
     */
    @Test
    void hourToSeconds() {
        ComparableQuantity<Time> s = Quantities.getQuantity(2, Units.HOUR).to(Units.SECOND);
        assertEquals("7200 s", s.toString());
    }

    /**
     * Verifies: Conversion and Converters — metres re-express in kilometres
     * with a decimal value.
     */
    @Test
    void metreToKilometre() {
        assertEquals("1.5 km", Quantities.getQuantity(1500, Units.METRE)
                .to(MetricPrefix.KILO(Units.METRE)).toString());
    }

    /**
     * Verifies: Conversion and Converters — 36 km/h converts to exactly
     * 10 m/s.
     */
    @Test
    void compoundUnitConversionExact() {
        ComparableQuantity<Speed> ms = Quantities.getQuantity(36, Units.KILOMETRE_PER_HOUR)
                .to(Units.METRE_PER_SECOND);
        assertEquals(10.0, Values.dbl(ms));
        assertEquals(Units.METRE_PER_SECOND, ms.getUnit());
    }

    /**
     * Verifies: Conversion and Converters — Celsius converts to kelvin with
     * the offset applied.
     */
    @Test
    void celsiusToKelvinOffset() {
        ComparableQuantity<Temperature> k =
                Quantities.getQuantity(20, Units.CELSIUS).to(Units.KELVIN);
        assertEquals(293.15, Values.dbl(k));
        assertEquals(Units.KELVIN, k.getUnit());
    }

    /**
     * Verifies: Conversion and Converters — grams re-express in kilograms.
     */
    @Test
    void gramToKilogram() {
        ComparableQuantity<Mass> kg = Quantities.getQuantity(1000, Units.GRAM).to(Units.KILOGRAM);
        assertEquals("1 kg", kg.toString());
    }

    /**
     * Verifies: Conversion and Converters — converting to the quantity's own
     * unit returns an equal quantity.
     */
    @Test
    void selfConversionReturnsEqual() {
        ComparableQuantity<Length> q = Quantities.getQuantity(7, Units.METRE);
        assertEquals(q, q.to(Units.METRE));
    }

    /**
     * Verifies: Conversion and Converters — converters transform raw numbers:
     * km to m, m to km.
     */
    @Test
    void converterConvertsValues() {
        assertEquals(2000.0, MetricPrefix.KILO(Units.METRE).getConverterTo(Units.METRE).convert(2));
        assertEquals(0.5, Units.METRE.getConverterTo(MetricPrefix.KILO(Units.METRE)).convert(500));
    }

    /**
     * Verifies: Conversion and Converters — the kelvin-to-Celsius converter
     * applies the offset.
     */
    @Test
    void offsetConverterValues() {
        assertEquals(26.85, Units.KELVIN.getConverterTo(Units.CELSIUS).convert(300));
    }

    /**
     * Verifies: Conversion and Converters — identity and linearity answer per
     * converter kind: self-conversion is identity, scale factors are linear,
     * offsets are not.
     */
    @Test
    void converterIdentityAndLinearity() {
        assertTrue(Units.METRE.getConverterTo(Units.METRE).isIdentity());
        UnitConverter scale = MetricPrefix.KILO(Units.METRE).getConverterTo(Units.METRE);
        assertTrue(scale.isLinear());
        UnitConverter offset = Units.KELVIN.getConverterTo(Units.CELSIUS);
        assertFalse(offset.isLinear());
    }

    /**
     * Verifies: Conversion and Converters — getConverterToAny raises the
     * checked IncommensurableException across dimensions.
     */
    @Test
    void converterToAnyIncompatibleRaises() {
        assertThrows(IncommensurableException.class,
                () -> Units.METRE.getConverterToAny(Units.SECOND));
    }
}
