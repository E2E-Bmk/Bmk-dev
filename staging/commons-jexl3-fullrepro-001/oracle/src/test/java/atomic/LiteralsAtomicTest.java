package atomic;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;

import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import support.Jexl;

/** Literal forms and their Java result types. */
class LiteralsAtomicTest {

    /**
     * Verifies: Expression Language — an undecorated integer literal
     * evaluates to Integer.
     */
    @Test
    void integerLiteral() {
        assertEquals(42, Jexl.eval("42"));
    }

    /**
     * Verifies: Expression Language — an l-suffixed integer literal evaluates
     * to Long.
     */
    @Test
    void longLiteral() {
        assertEquals(42L, Jexl.eval("42l"));
    }

    /**
     * Verifies: Expression Language — a literal with a decimal point
     * evaluates to Double.
     */
    @Test
    void doubleLiteral() {
        assertEquals(4.2, Jexl.eval("4.2"));
        assertEquals(42.0, Jexl.eval("42.0"));
    }

    /**
     * Verifies: Expression Language — single- and double-quoted text both
     * evaluate to String.
     */
    @Test
    void stringLiterals() {
        assertEquals("hello", Jexl.eval("'hello'"));
        assertEquals("hi", Jexl.eval("\"hi\""));
    }

    /**
     * Verifies: Expression Language — boolean and null literals.
     */
    @Test
    void booleanAndNullLiterals() {
        assertEquals(true, Jexl.eval("true"));
        assertEquals(false, Jexl.eval("false"));
        assertNull(Jexl.eval("null"));
    }

    /**
     * Verifies: Expression Language — the array literal over integer elements
     * evaluates to a Java int[].
     */
    @Test
    void arrayLiteralIsIntArray() {
        Object value = Jexl.eval("[1, 2, 3]");
        assertArrayEquals(new int[] {1, 2, 3}, (int[]) value);
    }

    /**
     * Verifies: Expression Language — the map literal evaluates to a Map with
     * the given entries.
     */
    @Test
    void mapLiteral() {
        assertEquals(Map.of("a", 1, "b", 2), Jexl.eval("{'a': 1, 'b': 2}"));
    }

    /**
     * Verifies: Expression Language — the set literal evaluates to a Set.
     */
    @Test
    void setLiteral() {
        assertEquals(Set.of(1, 2, 3), Jexl.eval("{1, 2, 3}"));
    }
}
