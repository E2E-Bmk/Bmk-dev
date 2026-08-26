package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;
import support.Jexl;

/** Matching operators and the size/empty functions. */
class MatchingSizeAtomicTest {

    /**
     * Verifies: Expression Language — =~ is a regular-expression match when
     * the right side is a string pattern.
     */
    @Test
    void regexMatch() {
        assertEquals(true, Jexl.eval("'hello' =~ 'h.*o'"));
        assertEquals(false, Jexl.eval("'hello' =~ 'x.*'"));
    }

    /**
     * Verifies: Expression Language — =~ is containment when the right side
     * is a collection or array, and !~ negates it.
     */
    @Test
    void containmentMatch() {
        assertEquals(true, Jexl.eval("3 =~ [1, 2, 3]"));
        assertEquals(true, Jexl.eval("4 !~ [1, 2, 3]"));
        assertEquals(false, Jexl.eval("3 !~ [1, 2, 3]"));
    }

    /**
     * Verifies: Expression Language — =^ tests starts-with and =$ tests
     * ends-with.
     */
    @Test
    void prefixAndSuffixOperators() {
        assertEquals(true, Jexl.eval("'hello' =^ 'he'"));
        assertEquals(false, Jexl.eval("'hello' =^ 'lo'"));
        assertEquals(true, Jexl.eval("'hello' =$ 'lo'"));
        assertEquals(false, Jexl.eval("'hello' =$ 'he'"));
    }

    /**
     * Verifies: Expression Language — size returns string length, element
     * counts of collections and maps, and 0 for null.
     */
    @Test
    void sizeAcrossShapes() {
        assertEquals(5, Jexl.eval("size('hello')"));
        assertEquals(3, Jexl.eval("size([1, 2, 3])"));
        assertEquals(1, Jexl.eval("size({'a': 1})"));
        assertEquals(0, Jexl.eval("size(null)"));
    }

    /**
     * Verifies: Expression Language — empty is true for null, the empty
     * string, and empty collections, false otherwise.
     */
    @Test
    void emptyAcrossShapes() {
        assertEquals(true, Jexl.eval("empty('')"));
        assertEquals(true, Jexl.eval("empty(null)"));
        assertEquals(false, Jexl.eval("empty([1])"));
        assertEquals(false, Jexl.eval("empty('x')"));
    }
}
