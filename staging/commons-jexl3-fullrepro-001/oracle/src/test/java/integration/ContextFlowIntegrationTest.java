package integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.apache.commons.jexl3.JexlContext;
import org.apache.commons.jexl3.JexlException;
import org.apache.commons.jexl3.JexlExpression;
import org.apache.commons.jexl3.JexlScript;
import org.apache.commons.jexl3.MapContext;
import org.junit.jupiter.api.Test;
import support.Jexl;

/** State flow between parsed objects and contexts. */
class ContextFlowIntegrationTest {

    /**
     * Verifies: Cross-View Invariants — after evaluating an unscoped
     * assignment, has is true and get equals the returned value.
     * Depends-On: assignmentWritesThrough, hasDistinguishesAbsentFromNull.
     */
    @Test
    void assignmentAndContextAgree() {
        JexlContext ctx = new MapContext();
        ctx.set("base", 3);
        Object returned = Jexl.eval("derived = base * 7", ctx);
        assertTrue(ctx.has("derived"));
        assertEquals(returned, ctx.get("derived"));
        assertEquals(21, returned);
    }

    /**
     * Verifies: Cross-View Invariants — a wrapped backing map and the context
     * present one store in both directions.
     * Depends-On: wrappedMapIsSharedStore, assignmentWritesThrough.
     */
    @Test
    void wrappedMapSingleStore() {
        Map<String, Object> backing = new HashMap<>();
        backing.put("in", 5);
        JexlContext ctx = new MapContext(backing);
        assertEquals(5, ctx.get("in"));
        Jexl.run("out = in + 1; in = in * 10", ctx);
        assertEquals(6, backing.get("out"));
        assertEquals(50, backing.get("in"));
        backing.put("late", 100);
        assertEquals(101, Jexl.eval("late + 1", ctx));
    }

    /**
     * Verifies: Cross-View Invariants — one parsed object is reusable against
     * different contexts in either order, each result determined by its
     * context alone.
     * Depends-On: assignmentWritesThrough, parametersBindPositionally.
     */
    @Test
    void parsedObjectReusableAcrossContexts() {
        JexlExpression e = Jexl.DEFAULT.createExpression("x * 2");
        JexlContext first = new MapContext();
        first.set("x", 10);
        JexlContext second = new MapContext();
        second.set("x", -4);
        assertEquals(20, e.evaluate(first));
        assertEquals(-8, e.evaluate(second));
        assertEquals(20, e.evaluate(first));
    }

    /**
     * Verifies: Cross-View Invariants — a bare formula produces the same
     * value through expression evaluation and script execution over equal
     * contexts.
     * Depends-On: lastStatementIsResult, integerArithmeticStaysInteger.
     */
    @Test
    void expressionAndScriptAgreeOnFormulas() {
        for (String source : List.of("6 / 4", "'a' + 1", "3 =~ [1, 2, 3]", "size('hello')",
                "null ?? 'fallback'")) {
            Object viaExpression = Jexl.DEFAULT.createExpression(source).evaluate(new MapContext());
            Object viaScript = Jexl.DEFAULT.createScript(source).execute(new MapContext());
            assertEquals(viaExpression, viaScript);
        }
    }

    /**
     * Verifies: Cross-View Invariants — a script's context writes are visible
     * to later expression evaluations over the same context.
     * Depends-On: varLocalsDoNotLeak, assignmentWritesThrough.
     */
    @Test
    void scriptWritesFeedLaterExpressions() {
        JexlContext ctx = new MapContext();
        ctx.set("list", List.of(2, 3, 4));
        Jexl.run("var t = 0; for (v : list) { t = t + v }; total = t", ctx);
        assertFalse(ctx.has("t"));
        assertEquals(9, ctx.get("total"));
        assertEquals(3, Jexl.eval("total / 3", ctx));
    }

    /**
     * Verifies: Cross-View Invariants — parameters bind per run without
     * leaking, so consecutive executions with different arguments are
     * independent.
     * Depends-On: parametersBindPositionally, parametersDoNotLeakToContext.
     */
    @Test
    void parameterRunsAreIndependent() {
        JexlScript script = Jexl.DEFAULT.createScript("a * b", "a", "b");
        JexlContext ctx = new MapContext();
        assertEquals(6, script.execute(ctx, 2, 3));
        assertEquals(40, script.execute(ctx, 5, 8));
        assertFalse(ctx.has("a"));
        assertFalse(ctx.has("b"));
    }

    /**
     * Verifies: Cross-View Invariants — every context variable whose absence
     * makes strict evaluation raise appears in getVariables.
     * Depends-On: variableIntrospection, strictUndefinedVariableRaises.
     */
    @Test
    void introspectionPredictsStrictErrors() {
        JexlScript script = Jexl.DEFAULT.createScript("alpha + beta");
        assertTrue(script.getVariables().contains(List.of("alpha")));
        assertTrue(script.getVariables().contains(List.of("beta")));

        JexlContext partial = new MapContext();
        partial.set("alpha", 1);
        JexlException.Variable ex = assertThrows(JexlException.Variable.class,
                () -> script.execute(partial));
        assertEquals("beta", ex.getVariable());
        assertTrue(script.getVariables().contains(List.of(ex.getVariable())));
    }

    /**
     * Verifies: Cross-View Invariants — getParameters lists exactly the names
     * bound by positional arguments, and unbound declared parameters raise
     * the undefined-variable error naming them.
     * Depends-On: parametersBindPositionally, missingArgumentRaises.
     */
    @Test
    void parameterListMatchesBinding() {
        JexlScript script = Jexl.DEFAULT.createScript("p1 + p2 + p3", "p1", "p2", "p3");
        assertEquals(3, script.getParameters().length);
        assertEquals(60, script.execute(new MapContext(), 10, 20, 30));
        JexlException.Variable ex = assertThrows(JexlException.Variable.class,
                () -> script.execute(new MapContext(), 10, 20));
        assertEquals("p3", ex.getVariable());
    }

    /**
     * Verifies: Cross-View Invariants — compound assignment composes with
     * loops to accumulate into the context.
     * Depends-On: compoundAssignment, forIteratesCollection.
     */
    @Test
    void compoundAssignmentAccumulatesInLoop() {
        JexlContext ctx = new MapContext();
        ctx.set("acc", 100);
        ctx.set("items", List.of(1, 2, 3));
        Jexl.run("for (i : items) { acc += i }", ctx);
        assertEquals(106, ctx.get("acc"));
    }
}
