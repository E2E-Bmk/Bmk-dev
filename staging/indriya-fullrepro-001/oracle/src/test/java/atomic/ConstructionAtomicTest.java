package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import javax.measure.MetricPrefix;
import javax.measure.Quantity;
import javax.measure.quantity.Length;
import org.junit.jupiter.api.Test;
import support.Values;
import tech.units.indriya.ComparableQuantity;
import tech.units.indriya.quantity.Quantities;
import tech.units.indriya.unit.Units;

/** Quantity construction: factories, accessors, and exact numeric fidelity. */
class ConstructionAtomicTest {

    /**
     * Verifies: Quantity Construction and Values — the number/unit factory
     * binds value, unit, and the default ABSOLUTE scale.
     */
    @Test
    void factoryBindsValueUnitScale() {
        ComparableQuantity<Length> q = Quantities.getQuantity(10, Units.METRE);
        assertEquals(10, q.getValue().intValue());
        assertEquals(Units.METRE, q.getUnit());
        assertEquals(Quantity.Scale.ABSOLUTE, q.getScale());
    }

    /**
     * Verifies: Quantity Construction and Values — the three-argument factory
     * selects the scale explicitly.
     */
    @Test
    void explicitScaleFactory() {
        ComparableQuantity<Length> q =
                Quantities.getQuantity(5, Units.METRE, Quantity.Scale.RELATIVE);
        assertEquals(Quantity.Scale.RELATIVE, q.getScale());
    }

    /**
     * Verifies: Quantity Construction and Values — the text factory parses
     * "number unit-symbol" into value and unit.
     */
    @Test
    void textFactoryParsesValueAndUnit() {
        Quantity<?> q = Quantities.getQuantity("10 m");
        assertEquals(10, q.getValue().intValue());
        assertEquals(Units.METRE, q.getUnit());
    }

    /**
     * Verifies: Quantity Construction and Values — decimal text keeps its
     * decimal value through parsing.
     */
    @Test
    void textFactoryParsesDecimal() {
        Quantity<?> q = Quantities.getQuantity("2.5 s");
        assertEquals(2.5, Values.dbl(q));
        assertEquals(Units.SECOND, q.getUnit());
    }

    /**
     * Verifies: Quantity Construction and Values — prefixed unit symbols in
     * text resolve to the prefixed unit.
     */
    @Test
    void textFactoryParsesPrefixedUnit() {
        Quantity<?> q = Quantities.getQuantity("1.5 km");
        assertEquals(1.5, Values.dbl(q));
        assertEquals(MetricPrefix.KILO(Units.METRE), q.getUnit());
    }

    /**
     * Verifies: Quantity Construction and Values — integral inputs report
     * integral numbers and decimal inputs report decimals.
     */
    @Test
    void integralInputStaysIntegral() {
        assertEquals("10", Values.num(Quantities.getQuantity(10, Units.METRE)));
        assertEquals("2.5", Values.num(Quantities.getQuantity(2.5, Units.METRE)));
    }

    /**
     * Verifies: Quantity Construction and Values — toString renders
     * "value unit".
     */
    @Test
    void toStringRendersValueUnit() {
        assertEquals("10 m", Quantities.getQuantity(10, Units.METRE).toString());
        assertEquals("2.5 m", Quantities.getQuantity(2.5, Units.METRE).toString());
        assertEquals("1 km",
                Quantities.getQuantity(1, MetricPrefix.KILO(Units.METRE)).toString());
    }

    /**
     * Verifies: Quantity Construction and Values — decimal addition is exact:
     * 0.1 m + 0.2 m is exactly 0.3 m, not the binary-float sum.
     */
    @Test
    void exactDecimalAddition() {
        ComparableQuantity<Length> sum = Quantities.getQuantity(0.1, Units.METRE)
                .add(Quantities.getQuantity(0.2, Units.METRE));
        assertEquals(0.3, Values.dbl(sum));
        assertTrue(sum.isEquivalentTo(Quantities.getQuantity(0.3, Units.METRE)));
    }

    /**
     * Verifies: Quantity Construction and Values — dividing by 3 and
     * multiplying by 3 restores the exact original value.
     */
    @Test
    void exactDivisionMultiplicationRoundTrip() {
        ComparableQuantity<Length> third =
                Quantities.getQuantity(1, Units.METRE).divide(3).multiply(3);
        assertTrue(third.isEquivalentTo(Quantities.getQuantity(1, Units.METRE)));
        assertEquals("1", Values.num(third));
    }

    /**
     * Verifies: Quantity Construction and Values — exact integral results stay
     * integral (km→m conversion, same-unit sum) and fractional results report
     * decimals.
     */
    @Test
    void exactResultsKeepNumericShape() {
        ComparableQuantity<Length> km =
                Quantities.getQuantity(1, MetricPrefix.KILO(Units.METRE));
        assertEquals("1000", Values.num(km.to(Units.METRE)));
        ComparableQuantity<Length> sum = Quantities.getQuantity(10, Units.METRE)
                .add(Quantities.getQuantity(5, Units.METRE));
        assertEquals("15", Values.num(sum));
        assertEquals("2.5", Values.num(Quantities.getQuantity(10, Units.METRE).divide(4)));
    }
}
