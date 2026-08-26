package integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import org.apache.commons.jxpath.AbstractFactory;
import org.apache.commons.jxpath.ClassFunctions;
import org.apache.commons.jxpath.CompiledExpression;
import org.apache.commons.jxpath.FunctionLibrary;
import org.apache.commons.jxpath.JXPathContext;
import org.apache.commons.jxpath.JXPathNotFoundException;
import org.apache.commons.jxpath.PackageFunctions;
import org.apache.commons.jxpath.Pointer;
import org.junit.jupiter.api.Test;
import support.Graphs;

/** Multi-step lifecycles: create, mutate, remove, compile, chain contexts. */
class LifecycleIntegrationTest {

    static class FullFactory extends AbstractFactory {
        @Override
        public boolean createObject(JXPathContext context, Pointer pointer, Object parent,
                String name, int index) {
            if (parent instanceof Graphs.Employee && name.equals("address")) {
                ((Graphs.Employee) parent).setAddress(new Graphs.Address());
                return true;
            }
            return false;
        }

        @Override
        public boolean declareVariable(JXPathContext context, String varName) {
            context.getVariables().declareVariable(varName, null);
            return true;
        }
    }

    /**
     * Verifies: Writing, Creating, and Removing — a created path is
     * immediately queryable, its pointer round-trips, and a fresh context over
     * the same graph sees the created structure.
     * Depends-On: createPathAndSetValueNeedsIntermediatesOnly, canonicalPathRoundTrips.
     */
    @Test
    void createThenReadAcrossContexts() {
        Graphs.Employee emp = Graphs.employee();
        JXPathContext ctx = JXPathContext.newContext(emp);
        ctx.setFactory(new FullFactory());
        Pointer created = ctx.createPathAndSetValue("address/city", "Tromso");
        assertEquals("/address/city", created.asPath());
        assertEquals("Tromso", ctx.getValue(created.asPath()));
        JXPathContext fresh = JXPathContext.newContext(emp);
        assertEquals("Tromso", fresh.getValue("address/city"));
    }

    /**
     * Verifies: Writing, Creating, and Removing — the factory's
     * declareVariable hook makes createPath on an undeclared variable succeed
     * and leaves the variable declared on the context.
     * Depends-On: createPathBuildsThroughFactory, declarationLifecycle.
     */
    @Test
    void factoryDeclaresVariables() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        ctx.setFactory(new FullFactory());
        Pointer p = ctx.createPath("$fresh");
        assertEquals("$fresh", p.asPath());
        assertTrue(ctx.getVariables().isDeclaredVariable("fresh"));
        ctx.createPathAndSetValue("$loaded", "value");
        assertEquals("value", ctx.getValue("$loaded"));
    }

    /**
     * Verifies: Writing, Creating, and Removing — a full write-remove cycle:
     * insert a map key, overwrite it, remove it, and observe each stage
     * through reads and the caller's map.
     * Depends-On: setValueInsertsNewMapKey, removePathDeletesMapEntry, missingMapKeyReadsNullInStrictMode.
     */
    @Test
    void mapEntryLifecycle() {
        Graphs.Employee emp = Graphs.employee();
        JXPathContext ctx = JXPathContext.newContext(emp);
        ctx.setValue("props/team", "core");
        assertEquals("core", ctx.getValue("props/team"));
        ctx.setValue("props/team", "infra");
        assertEquals("infra", emp.getProps().get("team"));
        ctx.removePath("props/team");
        assertNull(ctx.getValue("props/team"));
        assertEquals(false, emp.getProps().containsKey("team"));
    }

    /**
     * Verifies: Writing, Creating, and Removing — list removal reindexes: the
     * pointer canonical form written before a removal addresses the shifted
     * element afterwards.
     * Depends-On: removePathShrinksList, oneBasedIndexing.
     */
    @Test
    void listRemovalReindexes() {
        Graphs.Employee emp = Graphs.employee();
        JXPathContext ctx = JXPathContext.newContext(emp);
        ctx.removePath("phones[1]");
        assertEquals(List.of("222", "333"), emp.getPhones());
        assertEquals("222", ctx.getValue("phones[1]"));
        ctx.removeAll("phones");
        assertEquals(0.0, ctx.getValue("count(phones)"));
        assertEquals(List.of(), ctx.selectNodes("phones"));
    }

    /**
     * Verifies: Cross-View Invariants — each CompiledExpression operation
     * produces the same result as the same-named context operation.
     * Depends-On: compileRejectsBadSyntax, oneBasedIndexing, pointerWritesThrough.
     */
    @Test
    void compiledOperationsMirrorContextOperations() {
        Graphs.Employee emp = Graphs.employee();
        JXPathContext ctx = JXPathContext.newContext(emp);
        CompiledExpression expr = JXPathContext.compile("phones[2]");
        assertEquals(ctx.getValue("phones[2]"), expr.getValue(ctx));
        assertEquals(ctx.getValue("phones[2]", Integer.class), expr.getValue(ctx, Integer.class));
        assertEquals(ctx.getPointer("phones[2]").asPath(), expr.getPointer(ctx, "phones[2]").asPath());
        assertEquals(Graphs.drain(ctx.iterate("phones[2]")), Graphs.drain(expr.iterate(ctx)));
        expr.setValue(ctx, "888");
        assertEquals("888", emp.getPhones().get(1));
        expr.removePath(ctx);
        assertEquals(List.of("111", "333"), emp.getPhones());
    }

    /**
     * Verifies: Leniency, Nested Contexts, and Compiled Expressions — one
     * compiled expression evaluated against two graphs reports each graph's
     * own values; against a missing path it follows each context's own
     * discipline.
     * Depends-On: compileRejectsBadSyntax, strictIsDefaultAndRaises, lenientReturnsNull.
     */
    @Test
    void compiledExpressionIsContextIndependent() {
        CompiledExpression expr = JXPathContext.compile("name");
        Graphs.Employee ada = Graphs.employee();
        Graphs.Employee bob = Graphs.employee();
        bob.setName("Bob");
        assertEquals("Ada", expr.getValue(JXPathContext.newContext(ada)));
        assertEquals("Bob", expr.getValue(JXPathContext.newContext(bob)));
        CompiledExpression missing = JXPathContext.compile("nosuch");
        JXPathContext strict = JXPathContext.newContext(ada);
        assertThrows(JXPathNotFoundException.class, () -> missing.getValue(strict));
        JXPathContext lenient = JXPathContext.newContext(ada);
        lenient.setLenient(true);
        assertNull(missing.getValue(lenient));
    }

    /**
     * Verifies: Leniency, Nested Contexts, and Compiled Expressions — a child
     * context resolves parent variables inside queries over its own graph, and
     * its own declarations shadow nothing upward.
     * Depends-On: childContextInherits, variableInPredicate.
     */
    @Test
    void contextChainResolvesVariables() {
        JXPathContext parent = JXPathContext.newContext(Graphs.employee());
        parent.getVariables().declareVariable("min", 40);
        JXPathContext child = JXPathContext.newContext(parent, Graphs.company());
        assertEquals("Bob", child.getValue("employees[age > $min]/name"));
        child.getVariables().declareVariable("local", "only-here");
        assertEquals("only-here", child.getValue("$local"));
        assertEquals(false, parent.getVariables().isDeclaredVariable("local"));
    }

    /**
     * Verifies: Variables and Extension Functions — functions, variables, and
     * predicates compose in one query pipeline.
     * Depends-On: classFunctionsCallStaticMethods, functionLibraryAggregates, variableInPredicate.
     */
    @Test
    void functionsAndVariablesCompose() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.company());
        FunctionLibrary library = new FunctionLibrary();
        library.addFunctions(new ClassFunctions(Graphs.Util.class, "t"));
        library.addFunctions(new PackageFunctions("", null));
        ctx.setFunctions(library);
        ctx.getVariables().declareVariable("min", 40);
        assertEquals("BOB!", ctx.getValue("t:shout(employees[age > $min]/name)"));
        assertEquals(2, ctx.getValue("size(employees)"));
        assertEquals(135.0, ctx.getValue("t:triple(employees[2]/age) + 0.0"));
    }

    /**
     * Verifies: State Model — per-context settings are independent: leniency,
     * variables, factories, and functions on one context never affect another
     * context over the same graph.
     * Depends-On: lenientReturnsNull, installationReplacesDefaults, factoryAccessorReturnsInstalled.
     */
    @Test
    void contextSettingsAreIndependent() {
        Graphs.Employee shared = Graphs.employee();
        JXPathContext configured = JXPathContext.newContext(shared);
        configured.setLenient(true);
        configured.setFunctions(new ClassFunctions(Graphs.Util.class, "t"));
        configured.getVariables().declareVariable("v", 1);
        configured.setFactory(new FullFactory());
        JXPathContext plain = JXPathContext.newContext(shared);
        assertEquals(false, plain.isLenient());
        assertEquals(3, plain.getValue("size(phones)"));
        assertThrows(JXPathNotFoundException.class, () -> plain.getValue("$v"));
        assertNull(plain.getFactory());
        assertNull(configured.getValue("nosuch"));
    }
}
