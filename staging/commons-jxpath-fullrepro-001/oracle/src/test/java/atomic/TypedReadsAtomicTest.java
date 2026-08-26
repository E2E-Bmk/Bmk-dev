package atomic;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import org.apache.commons.jxpath.JXPathContext;
import org.junit.jupiter.api.Test;
import support.Graphs;

/** Typed reads: getValue(String, Class) conversion rules. */
class TypedReadsAtomicTest {

    /**
     * Verifies: Contexts and Path Queries — Double results convert to Integer
     * on request.
     */
    @Test
    void doubleConvertsToInteger() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        assertEquals(3, ctx.getValue("count(phones)", Integer.class));
    }

    /**
     * Verifies: Contexts and Path Queries — numeric strings convert to numeric
     * wrapper types.
     */
    @Test
    void numericStringConvertsToInteger() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        assertEquals(111, ctx.getValue("phones[1]", Integer.class));
    }

    /**
     * Verifies: Contexts and Path Queries — numbers convert to String and to
     * wider numeric wrappers.
     */
    @Test
    void numberConvertsToStringAndLong() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        assertEquals("36", ctx.getValue("age", String.class));
        assertEquals(36L, ctx.getValue("age", Long.class));
    }

    /**
     * Verifies: Contexts and Path Queries — a collection converts to a scalar
     * by taking its first element.
     */
    @Test
    void collectionConvertsToScalarByFirstElement() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        assertEquals(111, ctx.getValue("phones", Integer.class));
    }

    /**
     * Verifies: Contexts and Path Queries — a collection converts to an array
     * type by converting each element.
     */
    @Test
    void collectionConvertsToArray() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        assertArrayEquals(new String[] {"111", "222", "333"},
                (String[]) ctx.getValue("phones", String[].class));
    }

    /**
     * Verifies: Error Semantics — converting non-numeric text to a numeric
     * type raises NumberFormatException.
     */
    @Test
    void nonNumericTextToNumberRaises() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        assertThrows(NumberFormatException.class, () -> ctx.getValue("name", Integer.class));
    }
}
