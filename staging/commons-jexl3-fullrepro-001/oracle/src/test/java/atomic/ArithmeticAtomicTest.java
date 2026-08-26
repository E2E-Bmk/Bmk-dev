package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;
import support.Jexl;

/** Arithmetic operators and numeric coercion. */
class ArithmeticAtomicTest {

    /**
     * Verifies: Expression Language — two integer operands produce an integer
     * result for + - * %.
     */
    @Test
    void integerArithmeticStaysInteger() {
        assertEquals(10, Jexl.eval("6 + 4"));
        assertEquals(2, Jexl.eval("6 - 4"));
        assertEquals(24, Jexl.eval("6 * 4"));
        assertEquals(3, Jexl.eval("7 % 4"));
    }

    /**
     * Verifies: Expression Language — integer division truncates.
     */
    @Test
    void integerDivisionTruncates() {
        assertEquals(1, Jexl.eval("6 / 4"));
        assertEquals(3, Jexl.eval("7 / 2"));
        assertEquals(2, Jexl.eval("8 / 4"));
    }

    /**
     * Verifies: Expression Language — any floating-point operand makes the
     * result a Double.
     */
    @Test
    void floatingOperandProducesDouble() {
        assertEquals(1.5, Jexl.eval("6.0 / 4"));
        assertEquals(10.5, Jexl.eval("6.5 + 4"));
    }

    /**
     * Verifies: Expression Language — an integer result too large for Integer
     * widens to Long.
     */
    @Test
    void overflowWidensToLong() {
        assertEquals(2147483648L, Jexl.eval("2147483647 + 1"));
    }

    /**
     * Verifies: Expression Language — Long operands keep Long results.
     */
    @Test
    void longArithmetic() {
        assertEquals(43L, Jexl.eval("42l + 1"));
    }

    /**
     * Verifies: Expression Language — when either operand of + is a
     * non-numeric string, + concatenates the string forms.
     */
    @Test
    void plusConcatenatesWithStrings() {
        assertEquals("ab", Jexl.eval("'a' + 'b'"));
        assertEquals("a1", Jexl.eval("'a' + 1"));
        assertEquals("12", Jexl.eval("1 + '2'"));
    }

    /**
     * Verifies: Expression Language — + is left-associative, so numeric
     * addition happens before a later string concatenation.
     */
    @Test
    void concatenationAssociativity() {
        assertEquals("3x", Jexl.eval("1 + 2 + 'x'"));
        assertEquals("x12", Jexl.eval("'x' + 1 + 2"));
    }

    /**
     * Verifies: Expression Language — unary minus negates.
     */
    @Test
    void unaryMinusNegates() {
        assertEquals(-3, Jexl.eval("-5 + 2"));
        assertEquals(-3, Jexl.eval("-7 % 4"));
    }
}
