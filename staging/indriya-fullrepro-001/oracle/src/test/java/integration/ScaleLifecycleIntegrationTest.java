package integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import javax.measure.MetricPrefix;
import javax.measure.Quantity;
import javax.measure.quantity.Length;
import javax.measure.quantity.Temperature;
import org.junit.jupiter.api.Test;
import support.Values;
import tech.units.indriya.ComparableQuantity;
import tech.units.indriya.format.SimpleQuantityFormat;
import tech.units.indriya.quantity.Quantities;
import tech.units.indriya.unit.Units;

/** Scale-aware lifecycles: temperature ledgers, delta pipelines, immutable state. */
class ScaleLifecycleIntegrationTest {

    private static ComparableQuantity<Temperature> delta(int celsius) {
        return Quantities.getQuantity(celsius, Units.CELSIUS, Quantity.Scale.RELATIVE);
    }

    /**
     * Verifies: Scales and Temperature Arithmetic — a temperature ledger of
     * absolute readings plus relative deltas accumulates deltas one at a time
     * or all at once with the same result.
     * Depends-On: absolutePlusRelativeTreatsDelta, relativePlusRelativeAddsDeltas.
     */
    @Test
    void deltaLedgerAccumulates() {
        ComparableQuantity<Temperature> stepwise =
                Quantities.getQuantity(20, Units.CELSIUS).add(delta(5)).add(delta(5));
        ComparableQuantity<Temperature> direct =
                Quantities.getQuantity(20, Units.CELSIUS).add(delta(10));
        assertEquals(30.0, Values.dbl(stepwise));
        assertEquals(Quantity.Scale.ABSOLUTE, stepwise.getScale());
        assertEquals(direct, stepwise);
        assertTrue(stepwise.isEquivalentTo(direct));
    }

    /**
     * Verifies: Scales and Temperature Arithmetic — deltas summed on the
     * relative scale apply to an absolute reading the same way as applying
     * each delta in turn.
     * Depends-On: relativePlusRelativeAddsDeltas, absolutePlusRelativeTreatsDelta.
     */
    @Test
    void summedDeltasApplyLikeSequentialDeltas() {
        ComparableQuantity<Temperature> summed = delta(4).add(delta(6));
        assertEquals(Quantity.Scale.RELATIVE, summed.getScale());
        ComparableQuantity<Temperature> viaSum =
                Quantities.getQuantity(15, Units.CELSIUS).add(summed);
        ComparableQuantity<Temperature> viaSteps =
                Quantities.getQuantity(15, Units.CELSIUS).add(delta(4)).add(delta(6));
        assertEquals(Values.dbl(viaSteps), Values.dbl(viaSum));
        assertEquals(25.0, Values.dbl(viaSum));
    }

    /**
     * Verifies: Scales and Temperature Arithmetic — a relative delta converts
     * to kelvin and back by factor only, staying a delta through the round
     * trip while an absolute reading takes the offset both ways.
     * Depends-On: relativeCelsiusConvertsByFactorOnly, absoluteCelsiusConvertsWithOffset.
     */
    @Test
    void scaleRoundTripsDiverge() {
        ComparableQuantity<Temperature> deltaRoundTrip =
                delta(10).to(Units.KELVIN).to(Units.CELSIUS);
        assertEquals(10.0, Values.dbl(deltaRoundTrip));
        assertEquals(Quantity.Scale.RELATIVE, deltaRoundTrip.getScale());
        ComparableQuantity<Temperature> absoluteRoundTrip =
                Quantities.getQuantity(10, Units.CELSIUS).to(Units.KELVIN).to(Units.CELSIUS);
        assertEquals(10.0, Values.dbl(absoluteRoundTrip));
        assertEquals(Quantity.Scale.ABSOLUTE, absoluteRoundTrip.getScale());
    }

    /**
     * Verifies: Scales and Temperature Arithmetic — the absolute-scale sum of
     * two absolute Celsius readings agrees with the same sum computed
     * explicitly in kelvin and re-expressed.
     * Depends-On: absolutePlusAbsoluteSumsOnAbsoluteScale, celsiusToKelvinOffset.
     */
    @Test
    void absoluteSumAgreesWithKelvinComputation() {
        ComparableQuantity<Temperature> sum = Quantities.getQuantity(20, Units.CELSIUS)
                .add(Quantities.getQuantity(10, Units.CELSIUS));
        ComparableQuantity<Temperature> kelvinSum =
                Quantities.getQuantity(20, Units.CELSIUS).to(Units.KELVIN)
                        .add(Quantities.getQuantity(10, Units.CELSIUS).to(Units.KELVIN));
        assertEquals(303.15, Values.dbl(sum));
        assertEquals(576.3, Values.dbl(kelvinSum));
        assertEquals(Values.dbl(kelvinSum), Values.dbl(sum.to(Units.KELVIN)));
    }

    /**
     * Verifies: State Model — a quantity used across many operations keeps its
     * triple: repeated reads through different views observe the same
     * construction.
     * Depends-On: operationsLeaveOperandsUntouched, equalTriplesBehaveIdentically.
     */
    @Test
    void quantityTripleSurvivesUse() {
        ComparableQuantity<Length> q = Quantities.getQuantity(1.5, MetricPrefix.KILO(Units.METRE));
        q.to(Units.METRE);
        q.add(Quantities.getQuantity(1, Units.METRE));
        q.compareTo(Quantities.getQuantity(1, MetricPrefix.KILO(Units.METRE)));
        SimpleQuantityFormat.getInstance().format(q);
        assertEquals(1.5, Values.dbl(q));
        assertEquals(MetricPrefix.KILO(Units.METRE), q.getUnit());
        assertEquals(Quantity.Scale.ABSOLUTE, q.getScale());
        assertEquals("1.5 km", q.toString());
    }

    /**
     * Verifies: State Model — format instances observed before and after heavy
     * use render and parse identically: no parsing state leaks between calls.
     * Depends-On: formatSingletonsAreSharedAndStateless, quantityFormatRoundTrips.
     */
    @Test
    void formatBehaviorIsStableAcrossUse() {
        SimpleQuantityFormat format = SimpleQuantityFormat.getInstance();
        String before = format.format(format.parse("1.5 km"));
        for (String text : new String[] {"10 m", "36 km/h", "2.5 s"}) {
            format.format(format.parse(text));
        }
        assertEquals(before, format.format(format.parse("1.5 km")));
        assertEquals("1.5 km", before);
    }

    /**
     * Verifies: Cross-View Invariants — ordering a mixed-unit, mixed-prefix
     * series through compareTo produces the measure order, and the equivalent
     * boundary pairs compare as ties.
     * Depends-On: compareToOrdersAcrossUnits, equivalenceAcrossPrefixedUnits.
     */
    @Test
    void mixedSeriesOrdersByMeasure() {
        ComparableQuantity<Length> small = Quantities.getQuantity(0.2, MetricPrefix.KILO(Units.METRE));
        ComparableQuantity<Length> mid = Quantities.getQuantity(500, Units.METRE);
        ComparableQuantity<Length> big = Quantities.getQuantity(1, MetricPrefix.KILO(Units.METRE));
        ComparableQuantity<Length> bigTwin = Quantities.getQuantity(1000, Units.METRE);
        assertTrue(small.compareTo(mid) < 0);
        assertTrue(mid.compareTo(big) < 0);
        assertTrue(small.compareTo(big) < 0);
        assertEquals(0, big.compareTo(bigTwin));
        assertTrue(big.isEquivalentTo(bigTwin));
    }
}
