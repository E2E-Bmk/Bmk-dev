package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import org.apache.commons.jxpath.JXPathContext;
import org.apache.commons.jxpath.JXPathInvalidAccessException;
import org.apache.commons.jxpath.JXPathInvalidSyntaxException;
import org.apache.commons.jxpath.JXPathNotFoundException;
import org.apache.commons.jxpath.Pointer;
import org.junit.jupiter.api.Test;
import support.Graphs;

/** Strict/lenient lookup discipline and syntax errors. */
class LeniencyAtomicTest {

    /**
     * Verifies: Leniency, Nested Contexts, and Compiled Expressions — a fresh
     * context is strict and raises on no-match reads.
     */
    @Test
    void strictIsDefaultAndRaises() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        assertFalse(ctx.isLenient());
        assertThrows(JXPathNotFoundException.class, () -> ctx.getValue("nosuch"));
        assertThrows(JXPathNotFoundException.class, () -> ctx.getPointer("nosuch"));
        assertThrows(JXPathNotFoundException.class, () -> ctx.selectSingleNode("nosuch"));
    }

    /**
     * Verifies: Leniency, Nested Contexts, and Compiled Expressions — a
     * lenient context returns null from getValue and selectSingleNode on a
     * no-match.
     */
    @Test
    void lenientReturnsNull() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        ctx.setLenient(true);
        assertTrue(ctx.isLenient());
        assertNull(ctx.getValue("nosuch"));
        assertNull(ctx.selectSingleNode("nosuch"));
        assertNull(ctx.getValue("nosuch", String.class));
    }

    /**
     * Verifies: Leniency, Nested Contexts, and Compiled Expressions — lenient
     * getPointer returns a placeholder rendering the requested path with null
     * value and node.
     */
    @Test
    void lenientPointerIsPlaceholder() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        ctx.setLenient(true);
        Pointer p = ctx.getPointer("nosuch");
        assertEquals("/nosuch", p.asPath());
        assertNull(p.getValue());
        assertNull(p.getNode());
    }

    /**
     * Verifies: Error Semantics — writing through a lenient placeholder
     * pointer raises JXPathInvalidAccessException.
     */
    @Test
    void placeholderWriteRaises() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        ctx.setLenient(true);
        Pointer p = ctx.getPointer("nosuch");
        assertThrows(JXPathInvalidAccessException.class, () -> p.setValue("x"));
    }

    /**
     * Verifies: Leniency, Nested Contexts, and Compiled Expressions — iterate,
     * iteratePointers, and selectNodes produce empty results for missing paths
     * in both modes.
     */
    @Test
    void iterationIsEmptySafeInBothModes() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        assertEquals(List.of(), Graphs.drain(ctx.iterate("nosuch")));
        assertEquals(List.of(), ctx.selectNodes("nosuch"));
        ctx.setLenient(true);
        assertEquals(List.of(), Graphs.drain(ctx.iterate("nosuch")));
        assertEquals(List.of(), Graphs.paths(ctx.iteratePointers("nosuch")));
        assertEquals(List.of(), ctx.selectNodes("nosuch"));
    }

    /**
     * Verifies: Error Semantics — unparseable expression text raises
     * JXPathInvalidSyntaxException, including the empty string.
     */
    @Test
    void syntaxErrorsRaise() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        assertThrows(JXPathInvalidSyntaxException.class, () -> ctx.getValue("phones["));
        assertThrows(JXPathInvalidSyntaxException.class, () -> ctx.getValue("foo///"));
        assertThrows(JXPathInvalidSyntaxException.class, () -> ctx.getValue(""));
    }

    /**
     * Verifies: Leniency, Nested Contexts, and Compiled Expressions — compile
     * surfaces syntax errors before any context is involved.
     */
    @Test
    void compileRejectsBadSyntax() {
        assertThrows(JXPathInvalidSyntaxException.class, () -> JXPathContext.compile("x["));
    }

    /**
     * Verifies: Leniency, Nested Contexts, and Compiled Expressions — a child
     * context reads variables through its parent and starts with the parent's
     * leniency.
     */
    @Test
    void childContextInherits() {
        JXPathContext parent = JXPathContext.newContext(Graphs.employee());
        parent.getVariables().declareVariable("shared", "inherited");
        parent.setLenient(true);
        JXPathContext child = JXPathContext.newContext(parent, Graphs.company());
        assertEquals("inherited", child.getValue("$shared"));
        assertTrue(child.isLenient());
        assertTrue(child.getParentContext() == parent);
        assertNull(parent.getParentContext());
    }
}
