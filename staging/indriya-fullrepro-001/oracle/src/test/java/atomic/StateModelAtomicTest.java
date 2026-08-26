package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertSame;

import javax.measure.MetricPrefix;
import javax.measure.quantity.Length;
import org.junit.jupiter.api.Test;
import tech.units.indriya.ComparableQuantity;
import tech.units.indriya.format.SimpleQuantityFormat;
import tech.units.indriya.format.SimpleUnitFormat;
import tech.units.indriya.quantity.Quantities;
import tech.units.indriya.unit.Units;

/** State model: immutability of quantities and units, shared singletons. */
class StateModelAtomicTest {

    /**
     * Verifies: State Model — arithmetic, conversion, and comparison return
     * new quantities and leave their operands untouched.
     */
    @Test
    void operationsLeaveOperandsUntouched() {
        ComparableQuantity<Length> base = Quantities.getQuantity(10, Units.METRE);
        base.add(Quantities.getQuantity(5, Units.METRE));
        base.to(MetricPrefix.KILO(Units.METRE));
        base.multiply(3);
        base.negate();
        assertEquals("10 m", base.toString());
        assertEquals(Units.METRE, base.getUnit());
    }

    /**
     * Verifies: State Model — two quantities with equal (value, unit, scale)
     * triples behave identically everywhere.
     */
    @Test
    void equalTriplesBehaveIdentically() {
        ComparableQuantity<Length> a = Quantities.getQuantity(10, Units.METRE);
        ComparableQuantity<Length> b = Quantities.getQuantity(10, Units.METRE);
        assertEquals(a, b);
        assertEquals(a.toString(), b.toString());
        assertEquals(a.to(MetricPrefix.KILO(Units.METRE)),
                b.to(MetricPrefix.KILO(Units.METRE)));
        assertEquals(a.getScale(), b.getScale());
    }

    /**
     * Verifies: State Model — the shared format instances are process-wide
     * singletons and parsing registers no state that changes later results.
     */
    @Test
    void formatSingletonsAreSharedAndStateless() {
        assertSame(SimpleQuantityFormat.getInstance(), SimpleQuantityFormat.getInstance());
        assertSame(SimpleUnitFormat.getInstance(), SimpleUnitFormat.getInstance());
        SimpleQuantityFormat format = SimpleQuantityFormat.getInstance();
        String first = format.format(format.parse("10 m"));
        format.parse("36 km/h");
        assertEquals(first, format.format(format.parse("10 m")));
    }

    /**
     * Verifies: State Model — the system-of-units singleton is stable across
     * accesses and use.
     */
    @Test
    void unitsSingletonIsStable() {
        assertSame(Units.getInstance(), Units.getInstance());
        Quantities.getQuantity(3, Units.METRE).to(MetricPrefix.KILO(Units.METRE));
        assertEquals("Units", Units.getInstance().getName());
    }

    /**
     * Verifies: State Model — unit algebra derives new units without mutating
     * the constants it starts from.
     */
    @Test
    void unitAlgebraLeavesConstantsUntouched() {
        Units.METRE.multiply(Units.METRE);
        Units.METRE.divide(Units.SECOND);
        Units.METRE.pow(3);
        assertEquals("m", Units.METRE.toString());
        assertEquals("m", Units.METRE.getSymbol());
    }
}
