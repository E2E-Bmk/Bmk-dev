package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;

import org.apache.commons.jexl3.JexlBuilder;
import org.apache.commons.jexl3.JexlContext;
import org.apache.commons.jexl3.JexlEngine;
import org.apache.commons.jexl3.JexlException;
import org.apache.commons.jexl3.MapContext;
import org.junit.jupiter.api.Test;
import support.Jexl;

/** Engine discipline axes and the declared error taxonomy. */
class EnginesErrorsAtomicTest {

    /**
     * Verifies: Error Semantics — a strict engine raises
     * JexlException.Variable naming an undefined variable.
     */
    @Test
    void strictUndefinedVariableRaises() {
        JexlException.Variable ex = assertThrows(JexlException.Variable.class,
                () -> Jexl.eval("undvar"));
        assertEquals("undvar", ex.getVariable());
    }

    /**
     * Verifies: Error Semantics — a strict engine raises JexlException on a
     * null arithmetic operand.
     */
    @Test
    void strictNullOperandRaises() {
        assertThrows(JexlException.class, () -> Jexl.eval("null + 1"));
    }

    /**
     * Verifies: Error Semantics — a strict engine raises JexlException on
     * integer division by zero.
     */
    @Test
    void strictDivisionByZeroRaises() {
        assertThrows(JexlException.class, () -> Jexl.eval("1 / 0"));
    }

    /**
     * Verifies: Error Semantics — a strict engine raises JexlException when
     * an if condition is null.
     */
    @Test
    void strictNullConditionRaises() {
        assertThrows(JexlException.class,
                () -> Jexl.run("if (null) 'truthy' else 'falsy'"));
    }

    /**
     * Verifies: Engines and Evaluation Modes — a lenient engine resolves
     * undefined variables and null operands as neutral values.
     */
    @Test
    void lenientSubstitutesNeutralValues() {
        JexlEngine lenient = new JexlBuilder().strict(false).create();
        assertEquals(1, lenient.createExpression("und + 1").evaluate(new MapContext()));
        assertEquals(1, lenient.createExpression("null + 1").evaluate(new MapContext()));
        assertEquals("falsy",
                lenient.createScript("if (null) 'truthy' else 'falsy'").execute(new MapContext()));
    }

    /**
     * Verifies: Engines and Evaluation Modes — a lenient engine yields 0.0
     * for integer division by zero.
     */
    @Test
    void lenientDivisionByZeroYieldsZero() {
        JexlEngine lenient = new JexlBuilder().strict(false).create();
        assertEquals(0.0, lenient.createExpression("1 / 0").evaluate(new MapContext()));
    }

    /**
     * Verifies: Engines and Evaluation Modes — silent(true) converts
     * evaluation errors into null results.
     */
    @Test
    void silentConvertsErrorsToNull() {
        JexlEngine silent = new JexlBuilder().silent(true).create();
        assertNull(silent.createExpression("undx + 1").evaluate(new MapContext()));
        assertNull(silent.createExpression("1 / 0").evaluate(new MapContext()));
    }

    /**
     * Verifies: Error Semantics — safe(false) makes navigation on a null base
     * raise JexlException.Variable.
     */
    @Test
    void unsafeNullNavigationRaises() {
        JexlEngine unsafe = new JexlBuilder().safe(false).create();
        JexlContext ctx = new MapContext();
        ctx.set("nothing", null);
        assertThrows(JexlException.Variable.class,
                () -> unsafe.createExpression("nothing.field").evaluate(ctx));
    }

    /**
     * Verifies: Error Semantics — syntax errors raise JexlException.Parsing
     * at parse time for expressions and scripts alike.
     */
    @Test
    void syntaxErrorsRaiseParsing() {
        assertThrows(JexlException.Parsing.class, () -> Jexl.DEFAULT.createExpression("1 +"));
        assertThrows(JexlException.Parsing.class, () -> Jexl.DEFAULT.createScript("for ("));
    }

    /**
     * Verifies: Error Semantics — a declared parameter with no supplied
     * argument raises JexlException.Variable under a strict engine.
     */
    @Test
    void missingArgumentRaises() {
        assertThrows(JexlException.Variable.class,
                () -> Jexl.DEFAULT.createScript("a + b", "a", "b").execute(new MapContext(), 5));
    }

    /**
     * Verifies: Engines and Evaluation Modes — getSourceText returns the
     * source a parsed object was created from.
     */
    @Test
    void sourceTextIsPreserved() {
        assertEquals("1 + 1", Jexl.DEFAULT.createExpression("1 + 1").getSourceText());
        assertEquals("a + b", Jexl.DEFAULT.createScript("a + b", "a", "b").getSourceText());
    }
}
