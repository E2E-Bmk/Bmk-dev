package integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;

import org.apache.commons.jexl3.JexlBuilder;
import org.apache.commons.jexl3.JexlContext;
import org.apache.commons.jexl3.JexlEngine;
import org.apache.commons.jexl3.JexlException;
import org.apache.commons.jexl3.MapContext;
import org.junit.jupiter.api.Test;

/** The strict/lenient/silent/safe axes over identical source and context. */
class DisciplineMatrixIntegrationTest {

    private static final JexlEngine STRICT = new JexlBuilder().create();
    private static final JexlEngine LENIENT = new JexlBuilder().strict(false).create();
    private static final JexlEngine SILENT = new JexlBuilder().silent(true).create();

    /**
     * Verifies: Cross-View Invariants — where strict raises the
     * undefined-variable error, lenient produces the neutral-value result and
     * silent returns null, for the same source and context.
     * Depends-On: strictUndefinedVariableRaises, lenientSubstitutesNeutralValues, silentConvertsErrorsToNull.
     */
    @Test
    void undefinedVariableAcrossDisciplines() {
        String source = "missing + 10";
        assertThrows(JexlException.Variable.class,
                () -> STRICT.createExpression(source).evaluate(new MapContext()));
        assertEquals(10, LENIENT.createExpression(source).evaluate(new MapContext()));
        assertNull(SILENT.createExpression(source).evaluate(new MapContext()));
    }

    /**
     * Verifies: Cross-View Invariants — division by zero diverges across the
     * disciplines exactly as documented.
     * Depends-On: strictDivisionByZeroRaises, lenientDivisionByZeroYieldsZero, silentConvertsErrorsToNull.
     */
    @Test
    void divisionByZeroAcrossDisciplines() {
        String source = "6 / 0";
        assertThrows(JexlException.class,
                () -> STRICT.createExpression(source).evaluate(new MapContext()));
        assertEquals(0.0, LENIENT.createExpression(source).evaluate(new MapContext()));
        assertNull(SILENT.createExpression(source).evaluate(new MapContext()));
    }

    /**
     * Verifies: Cross-View Invariants — a null arithmetic operand diverges
     * across the disciplines.
     * Depends-On: strictNullOperandRaises, lenientSubstitutesNeutralValues, silentConvertsErrorsToNull.
     */
    @Test
    void nullOperandAcrossDisciplines() {
        String source = "null + 1";
        assertThrows(JexlException.class,
                () -> STRICT.createExpression(source).evaluate(new MapContext()));
        assertEquals(1, LENIENT.createExpression(source).evaluate(new MapContext()));
        assertNull(SILENT.createExpression(source).evaluate(new MapContext()));
    }

    /**
     * Verifies: Cross-View Invariants — a null if condition raises under
     * strict and selects the false branch under lenient.
     * Depends-On: strictNullConditionRaises, lenientSubstitutesNeutralValues.
     */
    @Test
    void nullConditionAcrossDisciplines() {
        String source = "if (null) 'truthy' else 'falsy'";
        assertThrows(JexlException.class,
                () -> STRICT.createScript(source).execute(new MapContext()));
        assertEquals("falsy", LENIENT.createScript(source).execute(new MapContext()));
    }

    /**
     * Verifies: Cross-View Invariants — the safe axis flips only null-base
     * navigation: safe yields null, unsafe raises, with the same context.
     * Depends-On: safeNavigationOnNullBase, unsafeNullNavigationRaises.
     */
    @Test
    void safeAxisFlipsNullNavigation() {
        JexlEngine unsafe = new JexlBuilder().safe(false).create();
        JexlContext ctx = new MapContext();
        ctx.set("nothing", null);
        assertNull(STRICT.createExpression("nothing.field").evaluate(ctx));
        assertThrows(JexlException.Variable.class,
                () -> unsafe.createExpression("nothing.field").evaluate(ctx));
    }

    /**
     * Verifies: Cross-View Invariants — parsing errors are not silenced:
     * silent(true) converts evaluation errors only.
     * Depends-On: syntaxErrorsRaiseParsing, silentConvertsErrorsToNull.
     */
    @Test
    void silenceDoesNotCoverParsing() {
        assertThrows(JexlException.Parsing.class, () -> SILENT.createExpression("1 +"));
        assertNull(SILENT.createExpression("und + 1").evaluate(new MapContext()));
    }

    /**
     * Verifies: Cross-View Invariants — truthiness is uniform across if, the
     * ternary condition, logical operators, and the elvis left side for the
     * empty string.
     * Depends-On: elvisIsTruthinessBased, ifElseSelects, logicalOperators.
     */
    @Test
    void truthinessUniformForEmptyString() {
        assertEquals("falsy", STRICT.createScript("if ('') 'truthy' else 'falsy'").execute(new MapContext()));
        assertEquals(2, STRICT.createExpression("'' ? 1 : 2").evaluate(new MapContext()));
        assertEquals(false, STRICT.createExpression("'' && true").evaluate(new MapContext()));
        assertEquals("d", STRICT.createExpression("'' ?: 'd'").evaluate(new MapContext()));
    }

    /**
     * Verifies: Cross-View Invariants — truthiness is uniform across the same
     * constructs for zero and false.
     * Depends-On: elvisIsTruthinessBased, ifElseSelects, whileLoops.
     */
    @Test
    void truthinessUniformForZeroAndFalse() {
        assertEquals("falsy", STRICT.createScript("if (0) 'truthy' else 'falsy'").execute(new MapContext()));
        assertEquals(2, STRICT.createExpression("0 ? 1 : 2").evaluate(new MapContext()));
        assertEquals("d", STRICT.createExpression("0 ?: 'd'").evaluate(new MapContext()));
        assertEquals("falsy", STRICT.createScript("if (false) 'truthy' else 'falsy'").execute(new MapContext()));
        assertEquals("d", STRICT.createExpression("false ?: 'd'").evaluate(new MapContext()));
        assertEquals("ran0", STRICT.createScript("var r = 'ran0'; while (0) { r = 'ran1' }; r").execute(new MapContext()));
    }

    /**
     * Verifies: Cross-View Invariants — truthy values select the same way in
     * every construct: non-empty string and nonzero number.
     * Depends-On: ifElseSelects, elvisIsTruthinessBased.
     */
    @Test
    void truthinessUniformForTruthyValues() {
        assertEquals("truthy", STRICT.createScript("if ('x') 'truthy' else 'falsy'").execute(new MapContext()));
        assertEquals(1, STRICT.createExpression("'x' ? 1 : 2").evaluate(new MapContext()));
        assertEquals("x", STRICT.createExpression("'x' ?: 'd'").evaluate(new MapContext()));
        assertEquals("truthy", STRICT.createScript("if (1) 'truthy' else 'falsy'").execute(new MapContext()));
        assertEquals(1, STRICT.createExpression("1 ?: 'd'").evaluate(new MapContext()));
    }
}
