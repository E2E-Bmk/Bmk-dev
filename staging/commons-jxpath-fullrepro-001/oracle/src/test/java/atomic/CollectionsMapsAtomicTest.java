package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.apache.commons.jxpath.JXPathContext;
import org.apache.commons.jxpath.JXPathNotFoundException;
import org.junit.jupiter.api.Test;
import support.Graphs;

/** Collection indexing and map dynamic-property rules. */
class CollectionsMapsAtomicTest {

    /**
     * Verifies: Object Models — list values index from 1 and last() addresses
     * the final element.
     */
    @Test
    void oneBasedIndexing() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        assertEquals("111", ctx.getValue("phones[1]"));
        assertEquals("333", ctx.getValue("phones[last()]"));
    }

    /**
     * Verifies: Contexts and Path Queries — arithmetic is usable inside
     * predicates as an index expression.
     */
    @Test
    void arithmeticIndexPredicate() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        assertEquals("222", ctx.getValue("phones[1 + 1]"));
    }

    /**
     * Verifies: Object Models — index zero and past-the-end indexes are
     * no-matches; in a strict context they raise JXPathNotFoundException.
     */
    @Test
    void outOfRangeIndexIsNoMatch() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        assertThrows(JXPathNotFoundException.class, () -> ctx.getValue("phones[0]"));
        assertThrows(JXPathNotFoundException.class, () -> ctx.getValue("phones[4]"));
    }

    /**
     * Verifies: Contexts and Path Queries — getValue on a collection-valued
     * property returns the collection object itself.
     */
    @Test
    void wholeCollectionValueIsTheCollection() {
        Graphs.Employee emp = Graphs.employee();
        JXPathContext ctx = JXPathContext.newContext(emp);
        assertEquals(true, ctx.getValue("phones") == emp.getPhones());
    }

    /**
     * Verifies: Object Models — a map entry reads through a child step named
     * by its key, and through the attribute-predicate form.
     */
    @Test
    void mapEntryReadsByKey() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        assertEquals("senior", ctx.getValue("props/grade"));
        assertEquals("senior", ctx.getValue("props[@name = 'grade']"));
    }

    /**
     * Verifies: Object Models — map keys are treated as always present:
     * reading a missing key returns null even in a strict context.
     */
    @Test
    void missingMapKeyReadsNullInStrictMode() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        assertEquals(false, ctx.isLenient());
        assertNull(ctx.getValue("props/absent"));
    }

    /**
     * Verifies: Object Models — setValue on a previously absent map key
     * inserts the entry without any factory.
     */
    @Test
    void setValueInsertsNewMapKey() {
        Graphs.Employee emp = Graphs.employee();
        JXPathContext ctx = JXPathContext.newContext(emp);
        ctx.setValue("props/team", "core");
        assertEquals("core", emp.getProps().get("team"));
    }

    /**
     * Verifies: Object Models — map entry enumeration visits keys in ascending
     * string order regardless of the map's own iteration order.
     */
    @Test
    void mapEnumerationIsKeySorted() {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("z", 26);
        map.put("m", 13);
        map.put("a", 1);
        JXPathContext ctx = JXPathContext.newContext(map);
        assertEquals(List.of(1, 13, 26), Graphs.drain(ctx.iterate("*")));
    }

    /**
     * Verifies: Pointers, Canonical Paths, and Relative Contexts — entries of
     * a root map canonicalize to the /.[@name='key'] form.
     */
    @Test
    void rootMapEntryCanonicalForm() {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("z", 26);
        map.put("a", 1);
        JXPathContext ctx = JXPathContext.newContext(map);
        assertEquals(List.of("/.[@name='a']", "/.[@name='z']"), Graphs.paths(ctx.iteratePointers("*")));
    }

    /**
     * Verifies: Object Models — writing a list element stores the value
     * unconverted because a list carries no element-type information.
     */
    @Test
    void listElementWriteStoresRawValue() {
        Graphs.Employee emp = Graphs.employee();
        JXPathContext ctx = JXPathContext.newContext(emp);
        ctx.setValue("phones[1]", 42);
        Object stored = ((List) emp.getPhones()).get(0);
        assertEquals(42, stored);
    }

    /**
     * Verifies: Object Models — maps nested in maps traverse with dynamic
     * property rules at each level.
     */
    @Test
    void nestedMapsTraverse() {
        Map<String, Object> inner = new LinkedHashMap<>();
        inner.put("x", "y");
        Map<String, Object> outer = new LinkedHashMap<>();
        outer.put("nested", inner);
        JXPathContext ctx = JXPathContext.newContext(outer);
        assertEquals("y", ctx.getValue("nested/x"));
    }
}
