package integration;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.apache.commons.jexl3.JexlContext;
import org.apache.commons.jexl3.MapContext;
import org.junit.jupiter.api.Test;
import support.Jexl;

/** Composition of literals, operators, navigation, and control flow. */
class LanguageCompositionIntegrationTest {

    /**
     * Verifies: Cross-View Invariants — empty(v) is true exactly when size(v)
     * is 0 for strings, collections, arrays, and maps, with null reporting
     * size 0 and empty true.
     * Depends-On: sizeAcrossShapes, emptyAcrossShapes.
     */
    @Test
    void sizeAndEmptyAgree() {
        JexlContext ctx = new MapContext();
        ctx.set("values", List.of("", "x", List.of(), List.of(1), Map.of(), Map.of("k", 1)));
        for (String source : List.of("''", "'x'", "[]", "[1]", "{:}", "{'k': 1}", "null",
                "{1, 2}")) {
            Object size = Jexl.eval("size(" + source + ")");
            Object empty = Jexl.eval("empty(" + source + ")");
            assertEquals(((Integer) size) == 0, empty,
                    "size/empty disagree for " + source);
        }
    }

    /**
     * Verifies: Cross-View Invariants — a for loop over a context list visits
     * size(list) elements.
     * Depends-On: forIteratesCollection, sizeAcrossShapes.
     */
    @Test
    void loopCountMatchesSize() {
        JexlContext ctx = new MapContext();
        ctx.set("list", List.of(5, 6, 7, 8));
        Object visits = Jexl.run("var n = 0; for (v : list) { n = n + 1 }; n", ctx);
        assertEquals(Jexl.eval("size(list)", ctx), visits);
    }

    /**
     * Verifies: Cross-View Invariants — matching operators drive control flow
     * over context values.
     * Depends-On: containmentMatch, ifElseSelects.
     */
    @Test
    void matchingDrivesControlFlow() {
        JexlContext ctx = new MapContext();
        ctx.set("allowed", List.of("read", "write"));
        ctx.set("op", "write");
        assertEquals("granted",
                Jexl.run("if (op =~ allowed) 'granted' else 'denied'", ctx));
        ctx.set("op", "delete");
        assertEquals("denied",
                Jexl.run("if (op =~ allowed) 'granted' else 'denied'", ctx));
    }

    /**
     * Verifies: Cross-View Invariants — a lambda composes with parameters and
     * loops to transform context data.
     * Depends-On: lambdaIsCallable, parametersBindPositionally, forIteratesCollection.
     */
    @Test
    void lambdaComposesWithLoop() {
        JexlContext ctx = new MapContext();
        ctx.set("items", List.of(1, 2, 3));
        Object result = Jexl.run(
                "var twice = (v) -> { v * 2 }; var t = 0; for (i : items) { t = t + twice(i) }; t",
                ctx);
        assertEquals(12, result);
    }

    /**
     * Verifies: Cross-View Invariants — map literals navigate like context
     * maps: dot and bracket reads agree over both.
     * Depends-On: mapLiteral, propertyNavigationForms.
     */
    @Test
    void literalAndContextMapsNavigateAlike() {
        assertEquals(Jexl.eval("{'a': 7}.a"), Jexl.eval("{'a': 7}['a']"));
        JexlContext ctx = new MapContext();
        Map<String, Object> m = new HashMap<>();
        m.put("a", 7);
        ctx.set("m", m);
        assertEquals(Jexl.eval("m.a", ctx), Jexl.eval("{'a': 7}.a"));
    }

    /**
     * Verifies: Cross-View Invariants — coercing equality holds between
     * context values and literals exactly as between literals.
     * Depends-On: equalityCoerces, assignmentWritesThrough.
     */
    @Test
    void coercingEqualityWithContextValues() {
        JexlContext ctx = new MapContext();
        ctx.set("n", 2);
        ctx.set("s", "1");
        assertEquals(true, Jexl.eval("n == 2.0", ctx));
        assertEquals(true, Jexl.eval("1 == s", ctx));
        assertEquals(Jexl.eval("2 == 2.0"), Jexl.eval("n == 2.0", ctx));
    }

    /**
     * Verifies: Cross-View Invariants — fallback operators chain over context
     * state: an elvis chain picks the first truthy value, a coalescing chain
     * the first non-null.
     * Depends-On: elvisIsTruthinessBased, nullCoalescingKeepsFalsyNonNull.
     */
    @Test
    void fallbackChainsOverContext() {
        JexlContext ctx = new MapContext();
        ctx.set("primary", "");
        ctx.set("secondary", null);
        ctx.set("fallback", "value");
        assertEquals("value", Jexl.eval("primary ?: secondary ?: fallback", ctx));
        assertEquals("", Jexl.eval("primary ?? secondary ?? fallback", ctx));
    }

    /**
     * Verifies: Cross-View Invariants — string concatenation, indexing, and
     * method calls compose in one pipeline over context data.
     * Depends-On: plusConcatenatesWithStrings, listIndexing, methodCallOnValue.
     */
    @Test
    void navigationConcatenationPipeline() {
        JexlContext ctx = new MapContext();
        ctx.set("names", List.of("ada", "grace"));
        assertEquals("ADA-1", Jexl.eval("names[0].toUpperCase() + '-' + 1", ctx));
    }

    /**
     * Verifies: Cross-View Invariants — arithmetic coercion applies uniformly
     * to values read from the context, including truncation and widening.
     * Depends-On: integerDivisionTruncates, overflowWidensToLong.
     */
    @Test
    void coercionAppliesUniformlyToContextValues() {
        JexlContext ctx = new MapContext();
        ctx.set("seven", 7);
        ctx.set("two", 2);
        ctx.set("max", 2147483647);
        assertEquals(3, Jexl.eval("seven / two", ctx));
        assertEquals(2147483648L, Jexl.eval("max + 1", ctx));
        assertEquals(3.5, Jexl.eval("seven / 2.0", ctx));
    }
}
