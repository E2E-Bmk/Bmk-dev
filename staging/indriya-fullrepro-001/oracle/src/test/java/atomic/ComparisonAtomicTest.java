package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import javax.measure.MetricPrefix;
import javax.measure.quantity.Length;
import org.junit.jupiter.api.Test;
import tech.units.indriya.ComparableQuantity;
import tech.units.indriya.quantity.Quantities;
import tech.units.indriya.unit.Units;

/** Comparison regimes: strict equality, ordering, and measure equivalence. */
class ComparisonAtomicTest {

    private final ComparableQuantity<Length> oneKm =
            Quantities.getQuantity(1, MetricPrefix.KILO(Units.METRE));
    private final ComparableQuantity<Length> thousandM =
            Quantities.getQuantity(1000, Units.METRE);

    /**
     * Verifies: Comparison and Equivalence — equals is unit-sensitive: 1 km
     * never equals 1000 m.
     */
    @Test
    void equalsIsUnitSensitive() {
        assertNotEquals(oneKm, thousandM);
    }

    /**
     * Verifies: Comparison and Equivalence — equals is
     * representation-insensitive on values: 10 m equals 10.0 m.
     */
    @Test
    void equalsIsRepresentationInsensitive() {
        assertEquals(Quantities.getQuantity(10, Units.METRE),
                Quantities.getQuantity(10.0, Units.METRE));
    }

    /**
     * Verifies: Comparison and Equivalence — equal value and equal unit make
     * equal quantities.
     */
    @Test
    void equalTriplesAreEqual() {
        assertEquals(Quantities.getQuantity(10, Units.METRE),
                Quantities.getQuantity(10, Units.METRE));
    }

    /**
     * Verifies: Comparison and Equivalence — compareTo orders by measure
     * across units and returns 0 for equivalent pairs.
     */
    @Test
    void compareToOrdersAcrossUnits() {
        assertTrue(Quantities.getQuantity(500, Units.METRE).compareTo(oneKm) < 0);
        assertEquals(0, oneKm.compareTo(thousandM));
    }

    /**
     * Verifies: Comparison and Equivalence — compareTo ignores the numeric
     * representation of equal values.
     */
    @Test
    void compareToNumericTypeInsensitive() {
        assertEquals(0, Quantities.getQuantity(10, Units.METRE)
                .compareTo(Quantities.getQuantity(10.0, Units.METRE)));
    }

    /**
     * Verifies: Comparison and Equivalence — the relational helpers apply the
     * same cross-unit measure comparison as compareTo.
     */
    @Test
    void relationalHelpersAgree() {
        ComparableQuantity<Length> halfKm = Quantities.getQuantity(500, Units.METRE);
        assertTrue(halfKm.isLessThan(oneKm));
        assertFalse(halfKm.isGreaterThan(oneKm));
        assertTrue(oneKm.isGreaterThan(halfKm));
        assertTrue(oneKm.isGreaterThanOrEqualTo(thousandM));
        assertTrue(oneKm.isLessThanOrEqualTo(thousandM));
    }

    /**
     * Verifies: Comparison and Equivalence — equivalence across prefixed units
     * holds symmetrically.
     */
    @Test
    void equivalenceAcrossPrefixedUnits() {
        assertTrue(oneKm.isEquivalentTo(thousandM));
        assertTrue(thousandM.isEquivalentTo(oneKm));
    }

    /**
     * Verifies: Comparison and Equivalence — equivalence spans offset units:
     * 20 °C denotes the same measure as 293.15 K.
     */
    @Test
    void equivalenceAcrossOffsetUnits() {
        assertTrue(Quantities.getQuantity(20, Units.CELSIUS)
                .isEquivalentTo(Quantities.getQuantity(293.15, Units.KELVIN)));
    }

    /**
     * Verifies: Comparison and Equivalence — equivalence ignores numeric
     * representation: 10 m is equivalent to 10.0 m.
     */
    @Test
    void equivalenceRepresentationInsensitive() {
        assertTrue(Quantities.getQuantity(10, Units.METRE)
                .isEquivalentTo(Quantities.getQuantity(10.0, Units.METRE)));
    }
}
