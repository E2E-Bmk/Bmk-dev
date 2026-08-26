package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;
import org.apache.commons.jexl3.JexlContext;
import org.apache.commons.jexl3.MapContext;
import org.junit.jupiter.api.Test;
import support.Jexl;

/** Navigation, method calls, assignment, and the context store. */
class NavigationContextAtomicTest {

    /**
     * Verifies: Expression Language — dot and bracket forms both read a map
     * entry.
     */
    @Test
    void propertyNavigationForms() {
        JexlContext ctx = new MapContext();
        Map<String, Object> user = new HashMap<>();
        user.put("name", "Ada");
        ctx.set("user", user);
        assertEquals("Ada", Jexl.eval("user.name", ctx));
        assertEquals("Ada", Jexl.eval("user['name']", ctx));
    }

    /**
     * Verifies: Expression Language — indexing reads lists from 0.
     */
    @Test
    void listIndexing() {
        JexlContext ctx = new MapContext();
        ctx.set("nums", Arrays.asList(10, 20, 30));
        assertEquals(10, Jexl.eval("nums[0]", ctx));
        assertEquals(20, Jexl.eval("nums[1]", ctx));
    }

    /**
     * Verifies: Expression Language — a method call on a value invokes the
     * underlying Java method.
     */
    @Test
    void methodCallOnValue() {
        assertEquals("TEXT", Jexl.eval("'text'.toUpperCase()"));
    }

    /**
     * Verifies: Engines and Evaluation Modes — under the default safe axis,
     * navigation on a null base yields null instead of raising.
     */
    @Test
    void safeNavigationOnNullBase() {
        JexlContext ctx = new MapContext();
        ctx.set("nothing", null);
        assertNull(Jexl.eval("nothing.field", ctx));
    }

    /**
     * Verifies: Expression Language — assignment writes the variable into the
     * context and yields the value.
     */
    @Test
    void assignmentWritesThrough() {
        JexlContext ctx = new MapContext();
        ctx.set("x", 10);
        assertEquals(20, Jexl.eval("y = x * 2", ctx));
        assertTrue(ctx.has("y"));
        assertEquals(20, ctx.get("y"));
    }

    /**
     * Verifies: Expression Language — the compound form reads, applies, and
     * writes back.
     */
    @Test
    void compoundAssignment() {
        JexlContext ctx = new MapContext();
        ctx.set("acc", 10);
        Jexl.run("acc += 5", ctx);
        assertEquals(15, ctx.get("acc"));
    }

    /**
     * Verifies: Contexts — has distinguishes absent names from names set to
     * null, and get of an absent name returns null.
     */
    @Test
    void hasDistinguishesAbsentFromNull() {
        JexlContext ctx = new MapContext();
        ctx.set("present", null);
        assertTrue(ctx.has("present"));
        assertNull(ctx.get("present"));
        assertFalse(ctx.has("absent"));
        assertNull(ctx.get("absent"));
    }

    /**
     * Verifies: Contexts — MapContext over an existing map exposes its
     * entries as variables and lands writes in the same map.
     */
    @Test
    void wrappedMapIsSharedStore() {
        Map<String, Object> backing = new HashMap<>();
        backing.put("k", 7);
        JexlContext ctx = new MapContext(backing);
        assertEquals(8, Jexl.eval("k2 = k + 1", ctx));
        assertEquals(8, backing.get("k2"));
    }
}
