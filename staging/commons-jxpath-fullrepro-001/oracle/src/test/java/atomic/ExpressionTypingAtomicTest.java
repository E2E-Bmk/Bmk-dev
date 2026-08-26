package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.apache.commons.jxpath.JXPathContext;
import org.junit.jupiter.api.Test;
import support.Graphs;

/** XPath expression result typing over object graphs. */
class ExpressionTypingAtomicTest {

    /**
     * Verifies: Contexts and Path Queries — arithmetic returns Double.
     */
    @Test
    void arithmeticReturnsDouble() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        assertEquals(4.0, ctx.getValue("2 + 2"));
    }

    /**
     * Verifies: Contexts and Path Queries — count returns Double.
     */
    @Test
    void countReturnsDouble() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        assertEquals(3.0, ctx.getValue("count(phones)"));
    }

    /**
     * Verifies: Contexts and Path Queries — graph values participate in
     * arithmetic with coercion to Double.
     */
    @Test
    void graphValuesCoerceInArithmetic() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        assertEquals(37.0, ctx.getValue("age + 1"));
    }

    /**
     * Verifies: Contexts and Path Queries — comparisons and boolean functions
     * return Boolean.
     */
    @Test
    void comparisonsReturnBoolean() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        assertEquals(Boolean.TRUE, ctx.getValue("2 > 1"));
        assertEquals(Boolean.TRUE, ctx.getValue("not(age > 100)"));
    }

    /**
     * Verifies: Contexts and Path Queries — string functions return String.
     */
    @Test
    void stringFunctionsReturnString() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        assertEquals("Ada!", ctx.getValue("concat(name, '!')"));
        assertEquals("ell", ctx.getValue("substring('hello', 2, 3)"));
        assertEquals("36", ctx.getValue("string(age)"));
    }

    /**
     * Verifies: Contexts and Path Queries — string-length and number return
     * Double.
     */
    @Test
    void numericFunctionsReturnDouble() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        assertEquals(3.0, ctx.getValue("string-length(name)"));
        assertEquals(3.5, ctx.getValue("number('3.5')"));
    }

    /**
     * Verifies: Contexts and Path Queries — sum adds a node set numerically.
     */
    @Test
    void sumAddsNumerically() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.company());
        assertEquals(81.0, ctx.getValue("sum(employees/age)"));
    }

    /**
     * Verifies: Contexts and Path Queries — starts-with and contains are
     * usable in predicates over graph values.
     */
    @Test
    void stringPredicatesFilter() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.company());
        assertEquals(45, ctx.getValue("employees[starts-with(name, 'B')]/age"));
        assertEquals(1.0, ctx.getValue("count(employees[contains(name, 'o')])"));
    }

    /**
     * Verifies: Contexts and Path Queries — the union operator combines
     * matches from several paths.
     */
    @Test
    void unionCombinesPaths() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        assertEquals(java.util.List.of(36, "Ada"), ctx.selectNodes("age | name"));
    }
}
