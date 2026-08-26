package integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import javax.measure.MetricPrefix;
import javax.measure.Quantity;
import javax.measure.quantity.Dimensionless;
import javax.measure.quantity.Length;
import javax.measure.quantity.Mass;
import javax.measure.quantity.Speed;
import javax.measure.quantity.Time;
import org.junit.jupiter.api.Test;
import support.Values;
import tech.units.indriya.AbstractUnit;
import tech.units.indriya.ComparableQuantity;
import tech.units.indriya.format.SimpleQuantityFormat;
import tech.units.indriya.quantity.Quantities;
import tech.units.indriya.unit.Units;

/** Multi-step workflows that compose construction, arithmetic, conversion, and text. */
class WorkflowIntegrationTest {

    /**
     * Verifies: Cross-View Invariants — parse text, convert to a compatible
     * unit, compute, and format: each stage feeds the next without losing the
     * measure.
     * Depends-On: quantityParseReadsBack, compoundUnitConversionExact,
     * quantityFormatRendersValueUnit.
     */
    @Test
    void parseConvertComputeFormatPipeline() {
        SimpleQuantityFormat format = SimpleQuantityFormat.getInstance();
        Quantity<?> parsed = format.parse("36 km/h");
        ComparableQuantity<Speed> speed =
                Quantities.getQuantity(parsed.getValue(), parsed.getUnit().asType(Speed.class));
        ComparableQuantity<Speed> metric = speed.to(Units.METRE_PER_SECOND);
        assertEquals(10.0, Values.dbl(metric));
        assertEquals("10 m/s", format.format(metric));
    }

    /**
     * Verifies: Cross-View Invariants — a distance-over-time trip computation
     * derives a speed whose unit comes from the operand algebra and whose
     * measure agrees with the named constant view.
     * Depends-On: divideQuantityComposesUnits,
     * structuralEqualityDistinguishesConstruction, equivalenceAcrossPrefixedUnits.
     */
    @Test
    void tripSpeedComputation() {
        ComparableQuantity<Length> distance =
                Quantities.getQuantity(100, MetricPrefix.KILO(Units.METRE));
        ComparableQuantity<Time> duration = Quantities.getQuantity(2, Units.HOUR);
        ComparableQuantity<Speed> speed = distance.divide(duration).asType(Speed.class);
        assertEquals(50, speed.getValue().intValue());
        assertEquals(MetricPrefix.KILO(Units.METRE).divide(Units.HOUR), speed.getUnit());
        assertTrue(speed.isEquivalentTo(Quantities.getQuantity(50, Units.KILOMETRE_PER_HOUR)));
        assertEquals("50 km/h", speed.to(Units.KILOMETRE_PER_HOUR).toString());
    }

    /**
     * Verifies: Cross-View Invariants — speed times time simplifies back to a
     * length: the composed unit cancels the time dimension.
     * Depends-On: multiplyQuantityComposesUnits, asTypeChecksDimension.
     */
    @Test
    void speedTimesTimeYieldsLength() {
        ComparableQuantity<?> distance = Quantities.getQuantity(10, Units.METRE_PER_SECOND)
                .multiply(Quantities.getQuantity(2, Units.SECOND));
        assertEquals(Units.METRE, distance.getUnit());
        assertEquals("20 m", distance.asType(Length.class).to(Units.METRE).toString());
    }

    /**
     * Verifies: Cross-View Invariants — a mass ledger accumulates across gram
     * and kilogram entries under the left-unit rule and converts exactly at
     * the end.
     * Depends-On: addMixedUnitsKeepsLeftUnit, gramToKilogram.
     */
    @Test
    void massLedgerAccumulation() {
        ComparableQuantity<Mass> ledger =
                Quantities.getQuantity(250, Units.GRAM)
                        .add(Quantities.getQuantity(250, Units.GRAM))
                        .add(Quantities.getQuantity(1, Units.KILOGRAM))
                        .add(Quantities.getQuantity(0.5, Units.KILOGRAM));
        assertEquals(Units.GRAM, ledger.getUnit());
        assertEquals(2000.0, Values.dbl(ledger));
        assertEquals("2 kg", ledger.to(Units.KILOGRAM).toString());
    }

    /**
     * Verifies: Cross-View Invariants — a length accumulation mixing
     * kilometres and metres stays exact and reports the left unit.
     * Depends-On: addMixedUnitsKeepsLeftUnit, exactResultsKeepNumericShape.
     */
    @Test
    void mixedUnitAccumulationStaysExact() {
        ComparableQuantity<Length> total =
                Quantities.getQuantity(1, MetricPrefix.KILO(Units.METRE))
                        .add(Quantities.getQuantity(250, Units.METRE))
                        .add(Quantities.getQuantity(250, Units.METRE));
        assertEquals(MetricPrefix.KILO(Units.METRE), total.getUnit());
        assertEquals("1.5", Values.num(total));
        assertTrue(total.isEquivalentTo(Quantities.getQuantity(1500, Units.METRE)));
    }

    /**
     * Verifies: Cross-View Invariants — a dimensionless utilization ratio
     * derives from same-unit division, scales by a number, and converts
     * between percent and the ratio unit.
     * Depends-On: sameUnitDivisionCancelsToOne, crossUnitDivisionKeepsQuotientUnit.
     */
    @Test
    void dimensionlessRatioWorkflow() {
        ComparableQuantity<?> ratio = Quantities.getQuantity(30, Units.METRE)
                .divide(Quantities.getQuantity(60, Units.METRE));
        assertEquals(AbstractUnit.ONE, ratio.getUnit());
        assertEquals(0.5, Values.dbl(ratio));
        ComparableQuantity<Dimensionless> percent =
                Quantities.getQuantity(50, Units.PERCENT);
        assertEquals(0.5, Values.dbl(percent.to(AbstractUnit.ONE)));
        assertEquals(Values.dbl(ratio), Values.dbl(percent.to(AbstractUnit.ONE)));
    }

    /**
     * Verifies: Cross-View Invariants — converters compose across a
     * bidirectional chain: converting there and back through raw converters
     * restores the input number.
     * Depends-On: converterConvertsValues, converterIdentityAndLinearity.
     */
    @Test
    void converterChainRestoresInput() {
        double there = Units.METRE.getConverterTo(MetricPrefix.KILO(Units.METRE)).convert(123.0);
        double back = MetricPrefix.KILO(Units.METRE).getConverterTo(Units.METRE).convert(there);
        assertEquals(123.0, back);
    }

    /**
     * Verifies: Formatting and Parsing — the two text entry points and the
     * constructed quantity denote the same measure with the same rendering
     * for every documented text form.
     * Depends-On: textFactoryParsesValueAndUnit, quantityParseReadsBack,
     * factoryAgreesWithFormatParse.
     */
    @Test
    void textEntryPointsAgreeOnMeasure() {
        SimpleQuantityFormat format = SimpleQuantityFormat.getInstance();
        ComparableQuantity<Length> constructed =
                Quantities.getQuantity(1.5, MetricPrefix.KILO(Units.METRE));
        Quantity<?> viaFactory = Quantities.getQuantity("1.5 km");
        Quantity<?> viaFormat = format.parse("1.5 km");
        assertEquals("1.5 km", format.format(viaFactory));
        assertEquals("1.5 km", format.format(viaFormat));
        assertEquals(Values.dbl(constructed), Values.dbl(viaFactory));
        assertEquals(Values.dbl(constructed), Values.dbl(viaFormat));
        assertTrue(constructed.isEquivalentTo(
                Quantities.getQuantity(viaFormat.getValue(),
                        viaFormat.getUnit().asType(Length.class))));
        assertTrue(constructed.isEquivalentTo(
                Quantities.getQuantity(viaFactory.getValue(),
                        viaFactory.getUnit().asType(Length.class))));
    }

    /**
     * Verifies: Error Semantics — failed operations raise their declared types
     * and leave the shared entry points fully usable afterwards.
     * Depends-On: textFactoryUnparseableRaises, quantityAsTypeMismatchRaises,
     * converterToAnyRaisesChecked.
     */
    @Test
    void errorPathsLeaveStateIntact() {
        SimpleQuantityFormat format = SimpleQuantityFormat.getInstance();
        assertThrows(javax.measure.format.MeasurementParseException.class,
                () -> Quantities.getQuantity("garbage input"));
        assertEquals("10 m", format.format(format.parse("10 m")));
        assertThrows(ClassCastException.class,
                () -> Quantities.getQuantity(3, Units.METRE).asType(Mass.class));
        assertEquals(3, Quantities.getQuantity(3, Units.METRE)
                .asType(Length.class).getValue().intValue());
        assertThrows(javax.measure.IncommensurableException.class,
                () -> Units.METRE.getConverterToAny(Units.SECOND));
        assertEquals(2000.0,
                MetricPrefix.KILO(Units.METRE).getConverterTo(Units.METRE).convert(2));
    }

    /**
     * Verifies: Cross-View Invariants — a time-unit staircase (hours to
     * minutes to seconds) preserves the measure at every step.
     * Depends-On: hourToSeconds, equivalenceAcrossPrefixedUnits.
     */
    @Test
    void timeStaircasePreservesMeasure() {
        ComparableQuantity<Time> hours = Quantities.getQuantity(2, Units.HOUR);
        ComparableQuantity<Time> minutes = hours.to(Units.MINUTE);
        ComparableQuantity<Time> seconds = minutes.to(Units.SECOND);
        assertEquals("120", Values.num(minutes));
        assertEquals("7200", Values.num(seconds));
        assertTrue(seconds.isEquivalentTo(hours));
        assertTrue(minutes.isEquivalentTo(seconds));
        assertEquals(0, hours.compareTo(seconds));
    }
}
