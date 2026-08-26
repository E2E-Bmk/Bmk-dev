package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import org.apache.commons.jxpath.BasicVariables;
import org.apache.commons.jxpath.JXPathContext;
import org.apache.commons.jxpath.JXPathException;
import org.apache.commons.jxpath.JXPathNotFoundException;
import org.apache.commons.jxpath.Variables;
import org.junit.jupiter.api.Test;
import support.Graphs;

/** Declared variables: store operations and $name expression access. */
class VariablesAtomicTest {

    /**
     * Verifies: Variables and Extension Functions — declareVariable binds a
     * name readable as $name in expressions.
     */
    @Test
    void declaredVariableReadsInExpression() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        ctx.getVariables().declareVariable("bonus", 7);
        assertEquals(7, ctx.getValue("$bonus"));
    }

    /**
     * Verifies: Variables and Extension Functions — a collection-valued
     * variable indexes with $name[i].
     */
    @Test
    void collectionVariableIndexes() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        ctx.getVariables().declareVariable("list", List.of("p", "q"));
        assertEquals("q", ctx.getValue("$list[2]"));
    }

    /**
     * Verifies: Variables and Extension Functions — variables participate in
     * arithmetic with graph values, producing Double.
     */
    @Test
    void variableArithmeticIsDouble() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        ctx.getVariables().declareVariable("bonus", 7);
        assertEquals(43.0, ctx.getValue("$bonus + age"));
    }

    /**
     * Verifies: Variables and Extension Functions — a variable's value selects
     * a collection element inside a predicate.
     */
    @Test
    void variableInPredicate() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        ctx.getVariables().declareVariable("i", 2);
        assertEquals("222", ctx.getValue("phones[$i]"));
    }

    /**
     * Verifies: Variables and Extension Functions — isDeclaredVariable tracks
     * declaration; undeclareVariable removes a binding and tolerates absent
     * names.
     */
    @Test
    void declarationLifecycle() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        Variables vars = ctx.getVariables();
        assertFalse(vars.isDeclaredVariable("bonus"));
        vars.declareVariable("bonus", 7);
        assertTrue(vars.isDeclaredVariable("bonus"));
        vars.undeclareVariable("bonus");
        assertFalse(vars.isDeclaredVariable("bonus"));
        vars.undeclareVariable("bonus");
    }

    /**
     * Verifies: Variables and Extension Functions — a null value is a legal
     * binding.
     */
    @Test
    void nullBindingIsLegal() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        ctx.getVariables().declareVariable("empty", null);
        assertTrue(ctx.getVariables().isDeclaredVariable("empty"));
        assertNull(ctx.getValue("$empty"));
    }

    /**
     * Verifies: Error Semantics — BasicVariables.getVariable on an undeclared
     * name raises IllegalArgumentException.
     */
    @Test
    void basicVariablesUndeclaredGetRaises() {
        BasicVariables vars = new BasicVariables();
        assertThrows(IllegalArgumentException.class, () -> vars.getVariable("absent"));
    }

    /**
     * Verifies: Error Semantics — reading an undeclared variable in a strict
     * context raises JXPathNotFoundException; a lenient context still raises
     * JXPathException.
     */
    @Test
    void undeclaredVariableReadRaisesInBothModes() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        assertThrows(JXPathNotFoundException.class, () -> ctx.getValue("$absent"));
        ctx.setLenient(true);
        assertThrows(JXPathException.class, () -> ctx.getValue("$absent"));
    }

    /**
     * Verifies: Variables and Extension Functions — setValue on $name
     * reassigns a declared variable; an undeclared one raises JXPathException.
     */
    @Test
    void setValueReassignsDeclaredOnly() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        ctx.getVariables().declareVariable("v", "init");
        ctx.setValue("$v", "changed");
        assertEquals("changed", ctx.getVariables().getVariable("v"));
        assertThrows(JXPathException.class, () -> ctx.setValue("$absent", 1));
    }

    /**
     * Verifies: Pointers, Canonical Paths, and Relative Contexts — the pointer
     * of a variable location has the canonical path $name.
     */
    @Test
    void variablePointerCanonicalForm() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        ctx.getVariables().declareVariable("v", "init");
        assertEquals("$v", ctx.getPointer("$v").asPath());
    }

    /**
     * Verifies: Variables and Extension Functions — setVariables replaces the
     * context's variable store.
     */
    @Test
    void setVariablesReplacesStore() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        BasicVariables replacement = new BasicVariables();
        replacement.declareVariable("only", "here");
        ctx.setVariables(replacement);
        assertEquals("here", ctx.getValue("$only"));
        assertTrue(ctx.getVariables() == replacement);
    }
}
