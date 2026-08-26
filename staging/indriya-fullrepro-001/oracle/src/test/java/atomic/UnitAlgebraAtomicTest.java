package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import javax.measure.MetricPrefix;
import javax.measure.Unit;
import javax.measure.quantity.Speed;
import javax.measure.quantity.Time;
import org.junit.jupiter.api.Test;
import tech.units.indriya.unit.Units;

/** Unit algebra: system constants, prefixes, derivation, structural equality. */
class UnitAlgebraAtomicTest {

    /**
     * Verifies: Unit Algebra and the System of Units — base units report their
     * symbol directly.
     */
    @Test
    void baseUnitSymbols() {
        assertEquals("m", Units.METRE.getSymbol());
        assertEquals("m", Units.METRE.toString());
    }

    /**
     * Verifies: Unit Algebra and the System of Units — the system singleton
     * is named "Units" and its unit set contains the declared constants.
     */
    @Test
    void systemSingletonAndContents() {
        assertEquals("Units", Units.getInstance().getName());
        assertTrue(Units.getInstance().getUnits().contains(Units.METRE));
        assertTrue(Units.getInstance().getUnits().contains(Units.CELSIUS));
        assertTrue(Units.getInstance().getUnits().contains(Units.WATT));
    }

    /**
     * Verifies: Unit Algebra and the System of Units — metric prefixes build
     * scaled units whose printable form carries the prefix.
     */
    @Test
    void prefixBuildsScaledUnit() {
        assertEquals("km", MetricPrefix.KILO(Units.METRE).toString());
        assertEquals("ms", MetricPrefix.MILLI(Units.SECOND).toString());
    }

    /**
     * Verifies: Unit Algebra and the System of Units — a prefixed unit's
     * system unit is the unprefixed base.
     */
    @Test
    void prefixedUnitSystemUnit() {
        assertEquals(Units.METRE, MetricPrefix.KILO(Units.METRE).getSystemUnit());
    }

    /**
     * Verifies: Unit Algebra and the System of Units — a prefixed unit's
     * getSymbol is null; the printable form comes from toString.
     */
    @Test
    void prefixedUnitSymbolIsNull() {
        assertNull(MetricPrefix.KILO(Units.METRE).getSymbol());
    }

    /**
     * Verifies: Unit Algebra and the System of Units — multiply and pow derive
     * the square metre.
     */
    @Test
    void multiplyAndPowDeriveSquare() {
        assertEquals(Units.SQUARE_METRE, Units.METRE.multiply(Units.METRE));
        assertEquals(Units.SQUARE_METRE, Units.METRE.pow(2));
        assertEquals(Units.CUBIC_METRE, Units.METRE.pow(3));
    }

    /**
     * Verifies: Unit Algebra and the System of Units — divide derives the
     * metre-per-second constant.
     */
    @Test
    void divideDerivesQuotient() {
        assertEquals(Units.METRE_PER_SECOND, Units.METRE.divide(Units.SECOND));
    }

    /**
     * Verifies: Unit Algebra and the System of Units — root inverts pow.
     */
    @Test
    void rootInvertsPow() {
        assertEquals(Units.METRE, Units.SQUARE_METRE.root(2));
    }

    /**
     * Verifies: Unit Algebra and the System of Units — unit equality is
     * structural: the prefixed-and-divided construction is not the km/h
     * constant even though both render "km/h" and are compatible.
     */
    @Test
    void structuralEqualityDistinguishesConstruction() {
        Unit<Speed> algebra = MetricPrefix.KILO(Units.METRE).divide(Units.HOUR).asType(Speed.class);
        assertNotEquals(Units.KILOMETRE_PER_HOUR, algebra);
        assertEquals("km/h", algebra.toString());
        assertEquals("km/h", Units.KILOMETRE_PER_HOUR.toString());
        assertTrue(algebra.isCompatible(Units.KILOMETRE_PER_HOUR));
    }

    /**
     * Verifies: Unit Algebra and the System of Units — compatibility and
     * dimension answer semantic questions equality does not.
     */
    @Test
    void compatibilityAndDimension() {
        assertTrue(Units.METRE.isCompatible(MetricPrefix.KILO(Units.METRE)));
        assertFalse(Units.METRE.isCompatible(Units.SECOND));
        assertEquals(Units.METRE.getDimension(),
                MetricPrefix.KILO(Units.METRE).getDimension());
    }

    /**
     * Verifies: Unit Algebra and the System of Units — Unit.asType raises
     * ClassCastException on a dimension mismatch.
     */
    @Test
    void unitAsTypeChecksDimension() {
        assertThrows(ClassCastException.class, () -> Units.METRE.asType(Time.class));
    }
}
