package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import javax.measure.MetricPrefix;
import javax.measure.quantity.Dimensionless;
import javax.measure.quantity.Length;
import javax.measure.quantity.Mass;
import org.junit.jupiter.api.Test;
import support.Values;
import tech.units.indriya.AbstractUnit;
import tech.units.indriya.ComparableQuantity;
import tech.units.indriya.quantity.Quantities;
import tech.units.indriya.unit.Units;

/** Quantity arithmetic: dimensional composition, scaling, and typed views. */
class ArithmeticAtomicTest {

    /**
     * Verifies: Quantity Arithmetic — same-unit addition keeps the unit and
     * sums exactly.
     */
    @Test
    void addSameUnit() {
        ComparableQuantity<Length> sum = Quantities.getQuantity(10, Units.METRE)
                .add(Quantities.getQuantity(5, Units.METRE));
        assertEquals(15, sum.getValue().intValue());
        assertEquals(Units.METRE, sum.getUnit());
    }

    /**
     * Verifies: Quantity Arithmetic — mixed-unit addition converts the right
     * operand into the left operand's unit.
     */
    @Test
    void addMixedUnitsKeepsLeftUnit() {
        ComparableQuantity<Length> km = Quantities.getQuantity(1, MetricPrefix.KILO(Units.METRE));
        ComparableQuantity<Length> m = Quantities.getQuantity(500, Units.METRE);
        ComparableQuantity<Length> left = km.add(m);
        assertEquals(MetricPrefix.KILO(Units.METRE), left.getUnit());
        assertEquals(1.5, Values.dbl(left));
        ComparableQuantity<Length> right = m.add(km);
        assertEquals(Units.METRE, right.getUnit());
        assertEquals(1500.0, Values.dbl(right));
    }

    /**
     * Verifies: Quantity Arithmetic — subtraction follows the same left-unit
     * rule, including negative results.
     */
    @Test
    void subtractKeepsLeftUnit() {
        assertEquals("7.5", Values.num(Quantities.getQuantity(10, Units.METRE)
                .subtract(Quantities.getQuantity(2.5, Units.METRE))));
        ComparableQuantity<Length> mixed =
                Quantities.getQuantity(1, MetricPrefix.KILO(Units.METRE))
                        .subtract(Quantities.getQuantity(200, Units.METRE));
        assertEquals(MetricPrefix.KILO(Units.METRE), mixed.getUnit());
        assertEquals(0.8, Values.dbl(mixed));
        ComparableQuantity<Length> negative = Quantities.getQuantity(500, Units.METRE)
                .subtract(Quantities.getQuantity(1, MetricPrefix.KILO(Units.METRE)));
        assertEquals(-500.0, Values.dbl(negative));
    }

    /**
     * Verifies: Quantity Arithmetic — quantity multiplication composes units:
     * metres times metres is the square-metre unit.
     */
    @Test
    void multiplyQuantityComposesUnits() {
        ComparableQuantity<?> area = Quantities.getQuantity(10, Units.METRE)
                .multiply(Quantities.getQuantity(3, Units.METRE));
        assertEquals(30, area.getValue().intValue());
        assertEquals(Units.METRE.multiply(Units.METRE), area.getUnit());
        assertEquals(Units.SQUARE_METRE, area.getUnit());
    }

    /**
     * Verifies: Quantity Arithmetic — quantity division composes quotient
     * units: metres over seconds.
     */
    @Test
    void divideQuantityComposesUnits() {
        ComparableQuantity<?> speed = Quantities.getQuantity(10, Units.METRE)
                .divide(Quantities.getQuantity(2, Units.SECOND));
        assertEquals(5, speed.getValue().intValue());
        assertEquals(Units.METRE.divide(Units.SECOND), speed.getUnit());
        assertEquals("5 m/s", speed.toString());
    }

    /**
     * Verifies: Quantity Arithmetic — multiplying by a number scales the value
     * and keeps the unit.
     */
    @Test
    void multiplyByNumberKeepsUnit() {
        ComparableQuantity<Length> q = Quantities.getQuantity(10, Units.METRE).multiply(4);
        assertEquals(40, q.getValue().intValue());
        assertEquals(Units.METRE, q.getUnit());
    }

    /**
     * Verifies: Quantity Arithmetic — dividing by a number scales the value
     * and keeps the unit, reporting decimals when needed.
     */
    @Test
    void divideByNumberKeepsUnit() {
        ComparableQuantity<Length> q = Quantities.getQuantity(10, Units.METRE).divide(4);
        assertEquals(2.5, Values.dbl(q));
        assertEquals(Units.METRE, q.getUnit());
    }

    /**
     * Verifies: Quantity Arithmetic — same-unit division cancels to the
     * dimensionless unit ONE.
     */
    @Test
    void sameUnitDivisionCancelsToOne() {
        ComparableQuantity<?> ratio = Quantities.getQuantity(10, Units.METRE)
                .divide(Quantities.getQuantity(2, Units.METRE));
        assertEquals(5, ratio.getValue().intValue());
        assertEquals(AbstractUnit.ONE, ratio.getUnit());
    }

    /**
     * Verifies: Quantity Arithmetic — cross-unit same-dimension division keeps
     * the composed quotient unit, which converts to ONE as the plain ratio.
     */
    @Test
    void crossUnitDivisionKeepsQuotientUnit() {
        ComparableQuantity<?> ratio = Quantities.getQuantity(1, MetricPrefix.KILO(Units.METRE))
                .divide(Quantities.getQuantity(500, Units.METRE));
        assertEquals(0.002, Values.dbl(ratio));
        assertEquals(MetricPrefix.KILO(Units.METRE).divide(Units.METRE), ratio.getUnit());
        assertTrue(ratio.getUnit().isCompatible(AbstractUnit.ONE));
        assertEquals("2", Values.num(ratio.asType(Dimensionless.class).to(AbstractUnit.ONE)));
    }

    /**
     * Verifies: Quantity Arithmetic — inverse reciprocates value and unit.
     */
    @Test
    void inverseReciprocatesValueAndUnit() {
        ComparableQuantity<?> inv = Quantities.getQuantity(2, Units.SECOND).inverse();
        assertEquals(0.5, Values.dbl(inv));
        assertEquals(Units.SECOND.pow(-1), inv.getUnit());
        assertEquals(Units.SECOND.inverse(), inv.getUnit());
    }

    /**
     * Verifies: Quantity Arithmetic — negate flips the sign and keeps the
     * unit.
     */
    @Test
    void negateFlipsSign() {
        assertEquals("-10 m", Quantities.getQuantity(10, Units.METRE).negate().toString());
    }

    /**
     * Verifies: Quantity Arithmetic — asType casts on matching dimension and
     * raises ClassCastException on mismatch.
     */
    @Test
    void asTypeChecksDimension() {
        ComparableQuantity<Length> len =
                Quantities.getQuantity(3, Units.METRE).asType(Length.class);
        assertEquals(3, len.getValue().intValue());
        assertThrows(ClassCastException.class,
                () -> Quantities.getQuantity(3, Units.METRE).asType(Mass.class));
    }
}
