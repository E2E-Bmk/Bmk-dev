package atomic;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;
import java.util.List;
import java.util.Set;
import org.apache.commons.jexl3.JexlContext;
import org.apache.commons.jexl3.JexlException;
import org.apache.commons.jexl3.JexlScript;
import org.apache.commons.jexl3.MapContext;
import org.junit.jupiter.api.Test;
import support.Jexl;

/** Script statements, scoping, parameters, and introspection. */
class ScriptsAtomicTest {

    /**
     * Verifies: Scripts and Control Flow — a script's result is the value of
     * the last evaluated statement.
     */
    @Test
    void lastStatementIsResult() {
        assertEquals(12, Jexl.run("var a = 3; var b = 4; a * b"));
    }

    /**
     * Verifies: Scripts and Control Flow — var declares a script-local
     * variable invisible to the context; undeclared assignments write
     * through.
     */
    @Test
    void varLocalsDoNotLeak() {
        JexlContext ctx = new MapContext();
        Jexl.run("var local = 99; global = 1", ctx);
        assertFalse(ctx.has("local"));
        assertTrue(ctx.has("global"));
        assertEquals(1, ctx.get("global"));
    }

    /**
     * Verifies: Scripts and Control Flow — if selects statements by
     * truthiness.
     */
    @Test
    void ifElseSelects() {
        JexlContext ctx = new MapContext();
        ctx.set("n", 9);
        assertEquals("big", Jexl.run("if (n > 5) 'big' else 'small'", ctx));
        ctx.set("n", 2);
        assertEquals("small", Jexl.run("if (n > 5) 'big' else 'small'", ctx));
    }

    /**
     * Verifies: Scripts and Control Flow — while loops on truthiness.
     */
    @Test
    void whileLoops() {
        assertEquals(10,
                Jexl.run("var i = 0; var sum = 0; while (i < 5) { sum = sum + i; i = i + 1 }; sum"));
    }

    /**
     * Verifies: Scripts and Control Flow — for iterates a collection.
     */
    @Test
    void forIteratesCollection() {
        JexlContext ctx = new MapContext();
        ctx.set("list", Arrays.asList(1, 2, 3, 4));
        assertEquals(10, Jexl.run("var total = 0; for (item : list) { total = total + item }; total", ctx));
    }

    /**
     * Verifies: Scripts and Control Flow — for iterates an inclusive integer
     * range.
     */
    @Test
    void forIteratesRange() {
        assertEquals(10, Jexl.run("var t = 0; for (i : 1 .. 4) { t = t + i }; t"));
    }

    /**
     * Verifies: Scripts and Control Flow — return ends the script with the
     * given value.
     */
    @Test
    void returnEndsScript() {
        assertEquals("early", Jexl.run("if (true) { return 'early' } 'late'"));
    }

    /**
     * Verifies: Scripts and Control Flow — a lambda literal is a first-class
     * value callable within the script.
     */
    @Test
    void lambdaIsCallable() {
        assertEquals(42, Jexl.run("var f = (q) -> { q * 2 }; f(21)"));
    }

    /**
     * Verifies: Scripts and Control Flow — createScript declares named
     * parameters bound positionally by execute, and getParameters lists them
     * in order.
     */
    @Test
    void parametersBindPositionally() {
        JexlScript script = Jexl.DEFAULT.createScript("a + b", "a", "b");
        assertEquals(42, script.execute(new MapContext(), 30, 12));
        assertArrayEquals(new String[] {"a", "b"}, script.getParameters());
    }

    /**
     * Verifies: Scripts and Control Flow — parameters do not write into the
     * context.
     */
    @Test
    void parametersDoNotLeakToContext() {
        JexlContext ctx = new MapContext();
        Jexl.DEFAULT.createScript("a + 1", "a").execute(ctx, 5);
        assertFalse(ctx.has("a"));
    }

    /**
     * Verifies: Scripts and Control Flow — getVariables returns the context
     * variable references as navigation-segment lists, excluding parameters
     * and locals.
     */
    @Test
    void variableIntrospection() {
        JexlScript script = Jexl.DEFAULT.createScript("a.b + c");
        Set<List<String>> vars = script.getVariables();
        assertTrue(vars.contains(List.of("a", "b")));
        assertTrue(vars.contains(List.of("c")));
        assertEquals(2, vars.size());

        JexlScript withParam = Jexl.DEFAULT.createScript("var loc = 1; p + q + loc", "p");
        Set<List<String>> pv = withParam.getVariables();
        assertTrue(pv.contains(List.of("q")));
        assertFalse(pv.contains(List.of("p")));
        assertFalse(pv.contains(List.of("loc")));
    }

    /**
     * Verifies: Scripts and Control Flow — createExpression accepts a single
     * formula only; statements raise the parsing error.
     */
    @Test
    void expressionRejectsStatements() {
        assertThrows(JexlException.Parsing.class,
                () -> Jexl.DEFAULT.createExpression("var a = 1; a"));
    }
}
