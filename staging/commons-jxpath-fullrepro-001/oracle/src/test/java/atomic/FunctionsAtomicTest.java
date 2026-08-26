package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Set;
import org.apache.commons.jxpath.ClassFunctions;
import org.apache.commons.jxpath.FunctionLibrary;
import org.apache.commons.jxpath.JXPathContext;
import org.apache.commons.jxpath.JXPathFunctionNotFoundException;
import org.apache.commons.jxpath.PackageFunctions;
import org.junit.jupiter.api.Test;
import support.Graphs;

/** Extension functions: class sets, method calls, replacement semantics. */
class FunctionsAtomicTest {

    /**
     * Verifies: Variables and Extension Functions — ClassFunctions exposes
     * public static methods under its namespace prefix.
     */
    @Test
    void classFunctionsCallStaticMethods() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        ctx.setFunctions(new ClassFunctions(Graphs.Util.class, "t"));
        assertEquals("ADA!", ctx.getValue("t:shout(name)"));
        assertEquals(21, ctx.getValue("t:triple(7)"));
    }

    /**
     * Verifies: Variables and Extension Functions — arguments convert to the
     * declared parameter types.
     */
    @Test
    void argumentsConvertToParameterTypes() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        ctx.setFunctions(new ClassFunctions(Graphs.Util.class, "t"));
        assertEquals(27, ctx.getValue("t:triple('9')"));
        assertEquals(6, ctx.getValue("t:triple(2.0)"));
    }

    /**
     * Verifies: Variables and Extension Functions — with no installed set,
     * unprefixed non-core names resolve as method calls on the argument,
     * returning the method's actual result type.
     */
    @Test
    void defaultMethodCallFunctions() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        assertEquals(3, ctx.getValue("size(phones)"));
    }

    /**
     * Verifies: Variables and Extension Functions — installing a function set
     * replaces the default method-call resolution entirely.
     */
    @Test
    void installationReplacesDefaults() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        ctx.setFunctions(new ClassFunctions(Graphs.Util.class, "t"));
        assertThrows(JXPathFunctionNotFoundException.class, () -> ctx.getValue("size(phones)"));
    }

    /**
     * Verifies: Variables and Extension Functions — a FunctionLibrary
     * aggregates sets by namespace, restoring method calls when it contains a
     * PackageFunctions with the empty prefix.
     */
    @Test
    void functionLibraryAggregates() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        FunctionLibrary library = new FunctionLibrary();
        library.addFunctions(new ClassFunctions(Graphs.Util.class, "t"));
        library.addFunctions(new PackageFunctions("", null));
        ctx.setFunctions(library);
        assertEquals(6, ctx.getValue("t:triple(2)"));
        assertEquals(3, ctx.getValue("size(phones)"));
    }

    /**
     * Verifies: Variables and Extension Functions — removeFunctions detaches a
     * set from the library.
     */
    @Test
    void removeFunctionsDetaches() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        FunctionLibrary library = new FunctionLibrary();
        ClassFunctions set = new ClassFunctions(Graphs.Util.class, "t");
        library.addFunctions(set);
        ctx.setFunctions(library);
        assertEquals(6, ctx.getValue("t:triple(2)"));
        library.removeFunctions(set);
        assertThrows(JXPathFunctionNotFoundException.class, () -> ctx.getValue("t:triple(2)"));
    }

    /**
     * Verifies: Variables and Extension Functions — a ClassFunctions set
     * reports exactly its one namespace prefix.
     */
    @Test
    void usedNamespacesReportsPrefix() {
        assertEquals(Set.of("t"), new ClassFunctions(Graphs.Util.class, "t").getUsedNamespaces());
    }

    /**
     * Verifies: Error Semantics — a call no function set resolves raises
     * JXPathFunctionNotFoundException.
     */
    @Test
    void unresolvableFunctionRaises() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        ctx.setFunctions(new ClassFunctions(Graphs.Util.class, "t"));
        assertThrows(JXPathFunctionNotFoundException.class, () -> ctx.getValue("t:absent()"));
    }

    /**
     * Verifies: Variables and Extension Functions — core XPath functions
     * remain callable after any installation.
     */
    @Test
    void coreFunctionsSurviveInstallation() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        ctx.setFunctions(new ClassFunctions(Graphs.Util.class, "t"));
        assertEquals(3.0, ctx.getValue("string-length(name)"));
        assertEquals(3.0, ctx.getValue("count(phones)"));
    }

    /**
     * Verifies: Variables and Extension Functions — getFunctions returns the
     * installed set.
     */
    @Test
    void functionsAccessorReturnsInstalled() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        ClassFunctions set = new ClassFunctions(Graphs.Util.class, "t");
        ctx.setFunctions(set);
        assertTrue(ctx.getFunctions() == set);
    }
}
