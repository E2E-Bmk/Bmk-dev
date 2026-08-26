package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;
import support.Jexl;

/** Comparison, equality coercion, logic, and conditional operators. */
class ComparisonLogicAtomicTest {

    /**
     * Verifies: Expression Language — relational operators compare
     * numerically.
     */
    @Test
    void relationalOperators() {
        assertEquals(true, Jexl.eval("3 > 2"));
        assertEquals(true, Jexl.eval("3 >= 3"));
        assertEquals(false, Jexl.eval("2 > 3"));
        assertEquals(true, Jexl.eval("2 < 3"));
        assertEquals(true, Jexl.eval("2 <= 2"));
    }

    /**
     * Verifies: Expression Language — equality coerces across
     * representations.
     */
    @Test
    void equalityCoerces() {
        assertEquals(true, Jexl.eval("2 == 2.0"));
        assertEquals(true, Jexl.eval("1 == '1'"));
        assertEquals(true, Jexl.eval("'a' == 'a'"));
        assertEquals(true, Jexl.eval("1 != 2"));
    }

    /**
     * Verifies: Expression Language — eq and ne are aliases of == and !=.
     */
    @Test
    void keywordEqualityAliases() {
        assertEquals(true, Jexl.eval("3 eq 3"));
        assertEquals(true, Jexl.eval("3 ne 4"));
    }

    /**
     * Verifies: Expression Language — logical operators work on truthiness.
     */
    @Test
    void logicalOperators() {
        assertEquals(false, Jexl.eval("true && false"));
        assertEquals(true, Jexl.eval("true || false"));
        assertEquals(false, Jexl.eval("!true"));
    }

    /**
     * Verifies: Expression Language — the ternary selects by truthiness and
     * treats a null condition as false.
     */
    @Test
    void ternarySelectsByTruthiness() {
        assertEquals("yes", Jexl.eval("true ? 'yes' : 'no'"));
        assertEquals(2, Jexl.eval("null ? 1 : 2"));
    }

    /**
     * Verifies: Expression Language — the elvis form returns the left side
     * only when it is truthy: false, zero, and empty-string left sides yield
     * the right side.
     */
    @Test
    void elvisIsTruthinessBased() {
        assertEquals("set", Jexl.eval("'set' ?: 'default'"));
        assertEquals("default", Jexl.eval("null ?: 'default'"));
        assertEquals("d", Jexl.eval("false ?: 'd'"));
        assertEquals("d", Jexl.eval("0 ?: 'd'"));
        assertEquals("d", Jexl.eval("'' ?: 'd'"));
    }

    /**
     * Verifies: Expression Language — the null-coalescing form keeps false
     * and zero left sides, substituting only for null.
     */
    @Test
    void nullCoalescingKeepsFalsyNonNull() {
        assertEquals(5, Jexl.eval("5 ?? 'fallback'"));
        assertEquals("fallback", Jexl.eval("null ?? 'fallback'"));
        assertEquals(false, Jexl.eval("false ?? 'd'"));
        assertEquals(0, Jexl.eval("0 ?? 'd'"));
    }

    /**
     * Verifies: Expression Language — both fallback operators tolerate an
     * undefined left-hand variable without error in every engine mode.
     */
    @Test
    void fallbacksTolerateUndefined() {
        assertEquals("d", Jexl.eval("undef ?: 'd'"));
        assertEquals("d", Jexl.eval("undef ?? 'd'"));
    }
}
