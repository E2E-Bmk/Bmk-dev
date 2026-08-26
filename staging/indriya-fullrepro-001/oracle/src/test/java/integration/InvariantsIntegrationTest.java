package integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import javax.measure.MetricPrefix;
import javax.measure.Quantity;
import javax.measure.Unit;
import javax.measure.quantity.Length;
import javax.measure.quantity.Mass;
import javax.measure.quantity.Speed;
import javax.measure.quantity.Temperature;
import org.junit.jupiter.api.Test;
import support.Values;
import tech.units.indriya.AbstractUnit;
import tech.units.indriya.ComparableQuantity;
import tech.units.indriya.format.SimpleQuantityFormat;
import tech.units.indriya.format.SimpleUnitFormat;
import tech.units.indriya.quantity.Quantities;
import tech.units.indriya.unit.Units;

/** Cross-view invariants: the independent views of one measure never disagree. */
class InvariantsIntegrationTest {

    /**
     * Verifies: Cross-View Invariants — equivalence agrees with conversion and
     * is symmetric across offset and prefixed units.
     * Depends-On: equivalenceAcrossPrefixedUnits, equivalenceAcrossOffsetUnits,
     * celsiusToKelvinOffset.
     */
    @Test
    void equivalenceConversionAgreement() {
        ComparableQuantity<Length> km = Quantities.getQuantity(2, MetricPrefix.KILO(Units.METRE));
        ComparableQuantity<Length> m = Quantities.getQuantity(2000, Units.METRE);
        assertTrue(km.isEquivalentTo(m));
        assertTrue(m.isEquivalentTo(km));
        assertEquals(Values.dbl(m), Values.dbl(km.to(Units.METRE)));
        ComparableQuantity<Temperature> c = Quantities.getQuantity(20, Units.CELSIUS);
        ComparableQuantity<Temperature> k = Quantities.getQuantity(293.15, Units.KELVIN);
        assertTrue(c.isEquivalentTo(k));
        assertTrue(k.isEquivalentTo(c));
        assertEquals(Values.dbl(k), Values.dbl(c.to(Units.KELVIN)));
    }

    /**
     * Verifies: Cross-View Invariants — compareTo returns 0 exactly for
     * equivalent pairs and the relational helpers agree with its sign on every
     * cross-unit pair.
     * Depends-On: compareToOrdersAcrossUnits, relationalHelpersAgree,
     * equivalenceAcrossPrefixedUnits.
     */
    @Test
    void orderingEquivalenceCoherence() {
        List<ComparableQuantity<Length>> lengths = List.of(
                Quantities.getQuantity(500, Units.METRE),
                Quantities.getQuantity(1, MetricPrefix.KILO(Units.METRE)),
                Quantities.getQuantity(1000, Units.METRE),
                Quantities.getQuantity(0.2, MetricPrefix.KILO(Units.METRE)));
        for (ComparableQuantity<Length> a : lengths) {
            for (ComparableQuantity<Length> b : lengths) {
                int sign = a.compareTo(b);
                assertEquals(a.isEquivalentTo(b), sign == 0);
                assertEquals(sign > 0, a.isGreaterThan(b));
                assertEquals(sign < 0, a.isLessThan(b));
                assertEquals(sign >= 0, a.isGreaterThanOrEqualTo(b));
                assertEquals(sign <= 0, a.isLessThanOrEqualTo(b));
            }
        }
    }

    /**
     * Verifies: Cross-View Invariants — the unit of a quantity product,
     * quotient, and inverse equals the same algebra applied to the operand
     * units, and same-unit division lands on ONE.
     * Depends-On: multiplyQuantityComposesUnits, divideQuantityComposesUnits,
     * inverseReciprocatesValueAndUnit, sameUnitDivisionCancelsToOne.
     */
    @Test
    void arithmeticUnitAlgebraAgreement() {
        ComparableQuantity<?> p = Quantities.getQuantity(6, MetricPrefix.KILO(Units.METRE));
        ComparableQuantity<?> q = Quantities.getQuantity(3, Units.HOUR);
        assertEquals(p.getUnit().multiply(q.getUnit()), p.multiply(q).getUnit());
        assertEquals(p.getUnit().divide(q.getUnit()), p.divide(q).getUnit());
        assertEquals(p.getUnit().pow(-1), p.inverse().getUnit());
        ComparableQuantity<?> same = Quantities.getQuantity(9, Units.HOUR).divide(q);
        assertEquals(AbstractUnit.ONE, same.getUnit());
        assertEquals(3, same.getValue().intValue());
    }

    /**
     * Verifies: Cross-View Invariants — the quantity view and the converter
     * view of the same conversion produce the same number for scale-factor,
     * offset, and compound-unit pairs.
     * Depends-On: converterConvertsValues, offsetConverterValues,
     * compoundUnitConversionExact.
     */
    @Test
    void conversionConverterAgreement() {
        assertConverterAgrees(2.0, MetricPrefix.KILO(Units.METRE), Units.METRE);
        assertConverterAgrees(500.0, Units.METRE, MetricPrefix.KILO(Units.METRE));
        assertConverterAgrees(30.0, Units.CELSIUS, Units.KELVIN);
        assertConverterAgrees(300.0, Units.KELVIN, Units.CELSIUS);
        assertConverterAgrees(36.0, Units.KILOMETRE_PER_HOUR, Units.METRE_PER_SECOND);
    }

    private static <Q extends Quantity<Q>> void assertConverterAgrees(
            double value, Unit<Q> from, Unit<Q> to) {
        double quantityView = Values.dbl(Quantities.getQuantity(value, from).to(to));
        double converterView = from.getConverterTo(to).convert(value);
        assertEquals(converterView, quantityView);
    }

    /**
     * Verifies: Cross-View Invariants — mixed-unit addition and subtraction
     * keep the left operand's unit while the measure stays equivalent to the
     * sum computed in the other operand's unit.
     * Depends-On: addMixedUnitsKeepsLeftUnit, subtractKeepsLeftUnit.
     */
    @Test
    void leftUnitRuleAcrossPairs() {
        ComparableQuantity<Length> km = Quantities.getQuantity(1, MetricPrefix.KILO(Units.METRE));
        ComparableQuantity<Length> m = Quantities.getQuantity(500, Units.METRE);
        ComparableQuantity<Length> leftKm = km.add(m);
        ComparableQuantity<Length> leftM = m.add(km);
        assertEquals(MetricPrefix.KILO(Units.METRE), leftKm.getUnit());
        assertEquals(Units.METRE, leftM.getUnit());
        assertTrue(leftKm.isEquivalentTo(leftM));
        ComparableQuantity<Mass> g = Quantities.getQuantity(500, Units.GRAM);
        ComparableQuantity<Mass> kg = Quantities.getQuantity(1, Units.KILOGRAM);
        assertEquals(Units.GRAM, g.add(kg).getUnit());
        assertEquals(1500.0, Values.dbl(g.add(kg)));
        assertTrue(g.add(kg).isEquivalentTo(kg.add(g)));
    }

    /**
     * Verifies: Cross-View Invariants — chains of exact operations do not
     * accumulate binary floating-point error and integral inputs stay integral
     * through exact scale conversions.
     * Depends-On: exactDecimalAddition, exactDivisionMultiplicationRoundTrip,
     * exactResultsKeepNumericShape.
     */
    @Test
    void exactnessAcrossChains() {
        ComparableQuantity<Length> acc = Quantities.getQuantity(0.1, Units.METRE);
        for (int i = 0; i < 9; i++) {
            acc = acc.add(Quantities.getQuantity(0.1, Units.METRE));
        }
        assertEquals(1.0, Values.dbl(acc));
        assertEquals("1", Values.num(acc));
        assertTrue(acc.isEquivalentTo(Quantities.getQuantity(1, Units.METRE)));
        ComparableQuantity<Length> seventh =
                Quantities.getQuantity(1, Units.METRE).divide(7).multiply(7);
        assertEquals("1", Values.num(seventh));
        ComparableQuantity<Length> roundTrip = Quantities.getQuantity(3, MetricPrefix.KILO(Units.METRE))
                .to(Units.METRE).to(MetricPrefix.KILO(Units.METRE));
        assertEquals("3", Values.num(roundTrip));
    }

    /**
     * Verifies: Cross-View Invariants — quantity format round-trips are
     * equivalence-preserving, unit round-trips equal the named and prefixed
     * forms, and the text factory denotes the same measure as the format
     * parser with the same rendering.
     * Depends-On: quantityFormatRoundTrips, factoryAgreesWithFormatParse,
     * unitParsePrefixed, unitParseQuotient.
     */
    @Test
    void formatRoundTripAgreement() {
        SimpleQuantityFormat quantityFormat = SimpleQuantityFormat.getInstance();
        SimpleUnitFormat unitFormat = SimpleUnitFormat.getInstance();
        List<ComparableQuantity<?>> quantities = List.of(
                Quantities.getQuantity(10, Units.METRE),
                Quantities.getQuantity(1.5, MetricPrefix.KILO(Units.METRE)),
                Quantities.getQuantity(36, Units.KILOMETRE_PER_HOUR),
                Quantities.getQuantity(120, Units.SECOND));
        for (ComparableQuantity<?> q : quantities) {
            String text = quantityFormat.format(q);
            Quantity<?> reparsed = quantityFormat.parse(text);
            assertEquals(text, quantityFormat.format(reparsed));
            assertEquals(Values.dbl(q), Values.dbl(reparsed));
            Quantity<?> viaFactory = Quantities.getQuantity(text);
            assertEquals(text, quantityFormat.format(viaFactory));
            assertEquals(Values.dbl(reparsed), Values.dbl(viaFactory));
            assertTrue(reparsed.getUnit().isCompatible(viaFactory.getUnit()));
        }
        List<Unit<?>> units = List.of(Units.METRE, Units.SECOND, Units.HOUR,
                MetricPrefix.KILO(Units.METRE), MetricPrefix.MILLI(Units.SECOND),
                Units.METRE_PER_SECOND, Units.KILOMETRE_PER_HOUR, Units.GRAM, Units.KELVIN);
        for (Unit<?> u : units) {
            assertEquals(u, unitFormat.parse(unitFormat.format(u)));
        }
    }

    /**
     * Verifies: Cross-View Invariants — four independently built views of one
     * measure (constructed in metres, constructed in kilometres, parsed from
     * text, accumulated by mixed-unit addition) are pairwise equivalent, tie
     * under compareTo, and agree after conversion to a common unit.
     * Depends-On: addMixedUnitsKeepsLeftUnit, metreToKilometre,
     * equivalenceAcrossPrefixedUnits.
     */
    @Test
    void oneMeasureManyViews() {
        ComparableQuantity<Length> inMetres = Quantities.getQuantity(1500, Units.METRE);
        ComparableQuantity<Length> inKilometres =
                Quantities.getQuantity(1.5, MetricPrefix.KILO(Units.METRE));
        Quantity<?> parsedRaw = Quantities.getQuantity("1.5 km");
        ComparableQuantity<Length> parsed = Quantities.getQuantity(
                parsedRaw.getValue(), parsedRaw.getUnit().asType(Length.class));
        ComparableQuantity<Length> accumulated =
                Quantities.getQuantity(1, MetricPrefix.KILO(Units.METRE))
                        .add(Quantities.getQuantity(500, Units.METRE));
        List<ComparableQuantity<Length>> views =
                List.of(inMetres, inKilometres, parsed, accumulated);
        for (ComparableQuantity<Length> a : views) {
            for (ComparableQuantity<Length> b : views) {
                assertTrue(a.isEquivalentTo(b));
                assertEquals(0, a.compareTo(b));
                assertEquals(Values.dbl(a.to(Units.METRE)), Values.dbl(b.to(Units.METRE)));
            }
        }
        assertEquals("1.5 km", SimpleQuantityFormat.getInstance().format(inKilometres));
    }

    /**
     * Verifies: Cross-View Invariants — a unit built by algebra may reparse to
     * an equal named constant instead of its own construction: the round trip
     * lands on a compatible unit denoting the same measure.
     * Depends-On: structuralEqualityDistinguishesConstruction, unitParseQuotient.
     */
    @Test
    void algebraUnitsReparseToNamedConstants() {
        SimpleUnitFormat unitFormat = SimpleUnitFormat.getInstance();
        Unit<?> algebra = MetricPrefix.KILO(Units.METRE).divide(Units.HOUR);
        Unit<?> reparsed = unitFormat.parse(unitFormat.format(algebra));
        assertEquals(Units.KILOMETRE_PER_HOUR, reparsed);
        assertTrue(reparsed.isCompatible(algebra));
        assertTrue(Quantities.getQuantity(50, algebra.asType(Speed.class))
                .isEquivalentTo(Quantities.getQuantity(50, Units.KILOMETRE_PER_HOUR)));
    }
}
