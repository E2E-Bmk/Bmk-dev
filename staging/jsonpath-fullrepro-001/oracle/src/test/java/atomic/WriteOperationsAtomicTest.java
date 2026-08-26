package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertSame;

import com.jayway.jsonpath.DocumentContext;
import com.jayway.jsonpath.JsonPath;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import support.Json;

/** Write operations mutating the live document model. */
class WriteOperationsAtomicTest {

    /**
     * Verifies: Write Operations — set replaces the addressed value.
     */
    @Test
    void setReplacesAddressedValue() {
        DocumentContext ctx = JsonPath.parse("{\"a\":{\"b\":1}}");
        ctx.set("$.a.b", 42);
        assertEquals(42, ctx.read("$.a.b", Integer.class));
    }

    /**
     * Verifies: Write Operations — set on an indefinite path applies to every
     * match.
     */
    @Test
    void setIndefiniteAppliesToAllMatches() {
        DocumentContext ctx = JsonPath.parse("{\"a\":[{\"x\":1},{\"x\":2}]}");
        ctx.set("$.a[*].x", 9);
        assertEquals(Arrays.asList(9, 9), ctx.read("$.a[*].x"));
    }

    /**
     * Verifies: Write Operations — put adds a member to the addressed object.
     */
    @Test
    void putAddsMember() {
        DocumentContext ctx = JsonPath.parse("{\"a\":{\"b\":1}}");
        ctx.put("$.a", "c", "new");
        assertEquals("new", ctx.read("$.a.c"));
    }

    /**
     * Verifies: Write Operations — put replaces an existing member of the
     * addressed object.
     */
    @Test
    void putReplacesExistingMember() {
        DocumentContext ctx = JsonPath.parse("{\"o\":{\"k\":1}}");
        ctx.put("$.o", "k", 99);
        assertEquals(99, ctx.read("$.o.k", Integer.class));
    }

    /**
     * Verifies: Write Operations — add appends to the addressed array.
     */
    @Test
    void addAppendsToArray() {
        DocumentContext ctx = JsonPath.parse("{\"list\":[1,2]}");
        ctx.add("$.list", 3);
        assertEquals(Arrays.asList(1, 2, 3), ctx.read("$.list"));
    }

    /**
     * Verifies: Write Operations — delete removes the addressed value from its
     * parent.
     */
    @Test
    void deleteRemovesValueFromParent() {
        DocumentContext ctx = JsonPath.parse("{\"a\":{\"b\":1,\"c\":2}}");
        ctx.delete("$.a.b");
        Map<String, Object> a = ctx.read("$.a");
        assertEquals(List.of("c"), List.copyOf(a.keySet()));
    }

    /**
     * Verifies: Write Operations — delete on a filter path removes every
     * matching element.
     */
    @Test
    void deleteWithFilterRemovesMatches() {
        DocumentContext ctx = JsonPath.parse(Json.STORE);
        ctx.delete("$.store.book[?(@.price > 10)]");
        assertEquals(2, ctx.read("$.store.book.length()", Integer.class));
        assertEquals(Arrays.asList("Sayings of the Century", "Moby Dick"), ctx.read("$.store.book[*].title"));
    }

    /**
     * Verifies: Write Operations — renameKey renames a member of the addressed
     * object keeping its value.
     */
    @Test
    void renameKeyRenamesMember() {
        DocumentContext ctx = JsonPath.parse("{\"a\":{\"b\":7}}");
        ctx.renameKey("$.a", "b", "renamed");
        assertEquals(7, ctx.read("$.a.renamed", Integer.class));
    }

    /**
     * Verifies: Write Operations — map replaces each matched value with the
     * function's result.
     */
    @Test
    void mapTransformsEachMatch() {
        DocumentContext ctx = JsonPath.parse("{\"n\":[1,2,3]}");
        ctx.map("$.n[*]", (value, configuration) -> ((Integer) value) * 10);
        assertEquals(Arrays.asList(10, 20, 30), ctx.read("$.n"));
    }

    /**
     * Verifies: Write Operations — the map function receives the current value
     * and the configuration.
     */
    @Test
    void mapFunctionReceivesConfiguration() {
        DocumentContext ctx = JsonPath.parse("{\"n\":5}");
        ctx.map("$.n", (value, configuration) ->
                ((Integer) value) + (configuration.getOptions().isEmpty() ? 100 : 0));
        assertEquals(105, ctx.read("$.n", Integer.class));
    }

    /**
     * Verifies: Write Operations — write operations return the same context for
     * chaining.
     */
    @Test
    void writesReturnSameContextForChaining() {
        DocumentContext ctx = JsonPath.parse("{\"a\":{\"b\":1},\"list\":[1,2]}");
        DocumentContext returned = ctx.set("$.a.b", 42).put("$.a", "c", "new").add("$.list", 3);
        assertSame(ctx, returned);
        assertEquals(42, ctx.read("$.a.b", Integer.class));
        assertEquals("new", ctx.read("$.a.c"));
        assertEquals(Arrays.asList(1, 2, 3), ctx.read("$.list"));
    }
}
