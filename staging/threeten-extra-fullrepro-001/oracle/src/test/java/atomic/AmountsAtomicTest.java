package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.time.LocalDate;
import java.time.Period;
import java.time.temporal.ChronoUnit;
import org.junit.jupiter.api.Test;
import org.threeten.extra.Days;
import org.threeten.extra.Months;
import org.threeten.extra.Weeks;
import org.threeten.extra.Years;

/** Single-unit amount construction, text, arithmetic, and temporal use. */
class AmountsAtomicTest {

    /**
     * Verifies: Single-Unit Amounts — each type renders the ISO period style.
     */
    @Test
    void toStringRendersIsoPeriodStyle() {
        assertEquals("P3D", Days.of(3).toString());
        assertEquals("P2W", Weeks.of(2).toString());
        assertEquals("P5M", Months.of(5).toString());
        assertEquals("P7Y", Years.of(7).toString());
    }

    /**
     * Verifies: Single-Unit Amounts — parse reads each type's own form back.
     */
    @Test
    void parseReadsOwnForm() {
        assertEquals(Days.of(3), Days.parse("P3D"));
        assertEquals(Weeks.of(2), Weeks.parse("P2W"));
        assertEquals(Months.of(5), Months.parse("P5M"));
        assertEquals(Years.of(7), Years.parse("P7Y"));
    }

    /**
     * Verifies: Single-Unit Amounts — Days.parse accepts a weeks form at seven
     * days per week.
     */
    @Test
    void daysParseAcceptsWeeksForm() {
        assertEquals(Days.of(14), Days.parse("P2W"));
    }

    /**
     * Verifies: Single-Unit Amounts — the ZERO and ONE constants carry amounts
     * zero and one.
     */
    @Test
    void zeroAndOneConstants() {
        assertEquals(0, Days.ZERO.getAmount());
        assertEquals(1, Days.ONE.getAmount());
        assertEquals(0, Weeks.ZERO.getAmount());
        assertEquals(1, Years.ONE.getAmount());
    }

    /**
     * Verifies: Single-Unit Amounts — between measures the amount of the
     * type's unit from start to end.
     */
    @Test
    void betweenMeasuresUnit() {
        assertEquals(Days.of(31), Days.between(LocalDate.of(2020, 1, 1), LocalDate.of(2020, 2, 1)));
        assertEquals(Weeks.of(2), Weeks.between(LocalDate.of(2020, 1, 1), LocalDate.of(2020, 1, 15)));
        assertEquals(Months.of(1), Months.between(LocalDate.of(2020, 1, 31), LocalDate.of(2020, 3, 30)));
        assertEquals(Years.of(3), Years.between(LocalDate.of(2020, 1, 1), LocalDate.of(2023, 1, 1)));
    }

    /**
     * Verifies: Single-Unit Amounts — plus and minus combine amounts of the
     * same type.
     */
    @Test
    void plusAndMinusCombineAmounts() {
        assertEquals(Days.of(7), Days.of(3).plus(Days.of(4)));
        assertEquals(Days.of(-2), Days.of(3).minus(Days.of(5)));
    }

    /**
     * Verifies: Single-Unit Amounts — multipliedBy scales and dividedBy uses
     * integer division.
     */
    @Test
    void multiplyAndDivide() {
        assertEquals(Days.of(6), Days.of(3).multipliedBy(2));
        assertEquals(Days.of(3), Days.of(7).dividedBy(2));
    }

    /**
     * Verifies: Single-Unit Amounts — negated and abs adjust the sign.
     */
    @Test
    void negatedAndAbs() {
        assertEquals(Days.of(-3), Days.of(3).negated());
        assertEquals(Days.of(3), Days.of(-3).abs());
    }

    /**
     * Verifies: Single-Unit Amounts — isNegative, isZero, and isPositive
     * classify the sign.
     */
    @Test
    void signClassification() {
        assertTrue(Days.of(-1).isNegative());
        assertTrue(Days.ZERO.isZero());
        assertTrue(Days.ONE.isPositive());
    }

    /**
     * Verifies: Single-Unit Amounts — addTo and date.plus produce the same
     * result, and subtractFrom mirrors minus.
     */
    @Test
    void temporalAdditionAndSubtraction() {
        LocalDate base = LocalDate.of(2020, 1, 1);
        assertEquals(LocalDate.of(2020, 1, 4), Days.of(3).addTo(base));
        assertEquals(LocalDate.of(2020, 1, 4), base.plus(Days.of(3)));
        assertEquals(LocalDate.of(2020, 1, 7), LocalDate.of(2020, 1, 10).minus(Days.of(3)));
    }

    /**
     * Verifies: Single-Unit Amounts — get returns the amount for the type's
     * unit and getUnits lists exactly that unit.
     */
    @Test
    void unitAccessors() {
        assertEquals(3, Days.of(3).get(ChronoUnit.DAYS));
        assertEquals(1, Days.of(3).getUnits().size());
    }

    /**
     * Verifies: Single-Unit Amounts — toPeriod converts each amount, with
     * weeks converting at seven days.
     */
    @Test
    void toPeriodConversion() {
        assertEquals(Period.ofDays(14), Weeks.of(2).toPeriod());
        assertEquals(Period.ofMonths(2), Months.of(2).toPeriod());
        assertEquals(Period.ofYears(2), Years.of(2).toPeriod());
    }

    /**
     * Verifies: Single-Unit Amounts — compareTo orders by amount.
     */
    @Test
    void compareToOrdersByAmount() {
        assertTrue(Months.of(2).compareTo(Months.of(3)) < 0);
        assertTrue(Months.of(3).compareTo(Months.of(2)) > 0);
        assertEquals(0, Months.of(2).compareTo(Months.of(2)));
    }
}
