package integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.jayway.jsonpath.Configuration;
import com.jayway.jsonpath.DocumentContext;
import com.jayway.jsonpath.JsonPath;
import com.jayway.jsonpath.Option;
import com.jayway.jsonpath.PathNotFoundException;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import support.Json;

/**
 * Coherence of the document model across write operations and every read
 * projection: reads, the live root, and the serialized text.
 */
class WriteReadCoherenceIntegrationTest {

    /**
     * Verifies: Cross-View Invariants — after a set, the read projection, the
     * live root, and re-parsing jsonString all present the new value.
     * Depends-On: setReplacesAddressedValue, jsonReturnsLiveModelRoot, jsonStringSerializesModelState.
     */
    @Test
    void setVisibleThroughAllProjections() {
        DocumentContext ctx = JsonPath.parse("{\"a\":{\"b\":1}}");
        ctx.set("$.a.b", 42);
        assertEquals(42, ctx.read("$.a.b", Integer.class));
        Map<String, Object> root = (Map<String, Object>) ctx.json();
        assertEquals(42, ((Map<?, ?>) root.get("a")).get("b"));
        assertEquals(42, JsonPath.parse(ctx.jsonString()).read("$.a.b", Integer.class));
    }

    /**
     * Verifies: Write Operations — a chained write sequence accumulates every
     * mutation in the model.
     * Depends-On: writesReturnSameContextForChaining, renameKeyRenamesMember.
     */
    @Test
    void chainedWriteSequenceAccumulates() {
        DocumentContext ctx = JsonPath.parse("{\"o\":{\"k\":1},\"l\":[]}");
        ctx.add("$.l", "x").renameKey("$.o", "k", "kk").set("$.o.kk", 2).put("$.o", "n", 3);
        assertEquals(List.of("x"), ctx.read("$.l"));
        assertEquals(2, ctx.read("$.o.kk", Integer.class));
        assertEquals(3, ctx.read("$.o.n", Integer.class));
    }

    /**
     * Verifies: State Model — after delete, a definite read of the removed
     * location raises PathNotFoundException.
     * Depends-On: deleteRemovesValueFromParent, missingPropertyRaisesPathNotFound.
     */
    @Test
    void deletedLocationNoLongerReadable() {
        DocumentContext ctx = JsonPath.parse("{\"a\":{\"b\":1}}");
        ctx.delete("$.a.b");
        assertThrows(PathNotFoundException.class, () -> ctx.read("$.a.b"));
    }

    /**
     * Verifies: Write Operations — renameKey moves the value to the new key
     * and removes the old one.
     * Depends-On: renameKeyRenamesMember, missingPropertyRaisesPathNotFound.
     */
    @Test
    void renameKeyPreservesValueAndDropsOldKey() {
        DocumentContext ctx = JsonPath.parse("{\"a\":{\"b\":7}}");
        ctx.renameKey("$.a", "b", "renamed");
        assertEquals(7, ctx.read("$.a.renamed", Integer.class));
        assertThrows(PathNotFoundException.class, () -> ctx.read("$.a.b"));
    }

    /**
     * Verifies: Cross-View Invariants — a map transformation is visible in the
     * serialized text.
     * Depends-On: mapTransformsEachMatch, jsonStringSerializesModelState.
     */
    @Test
    void mapTransformationVisibleInJsonString() {
        DocumentContext ctx = JsonPath.parse("{\"n\":[1,2,3]}");
        ctx.map("$.n[*]", (value, configuration) -> ((Integer) value) * 10);
        assertEquals(Arrays.asList(10, 20, 30), JsonPath.parse(ctx.jsonString()).read("$.n"));
    }

    /**
     * Verifies: State Model — json() returns the same live root across writes,
     * reflecting each mutation.
     * Depends-On: jsonReturnsLiveModelRoot, setReplacesAddressedValue.
     */
    @Test
    void jsonRootIsLiveAcrossWrites() {
        DocumentContext ctx = JsonPath.parse("{\"a\":1}");
        Object before = ctx.json();
        ctx.set("$.a", 7);
        assertSame(before, ctx.json());
        assertEquals(7, ((Map<?, ?>) ctx.json()).get("a"));
    }

    /**
     * Verifies: State Model — a document re-parsed from jsonString is
     * independent: later writes to the original do not affect it.
     * Depends-On: jsonStringSerializesModelState, setReplacesAddressedValue.
     */
    @Test
    void reparsedDocumentIsIndependent() {
        DocumentContext original = JsonPath.parse("{\"a\":1}");
        DocumentContext snapshot = JsonPath.parse(original.jsonString());
        original.set("$.a", 2);
        assertEquals(2, original.read("$.a", Integer.class));
        assertEquals(1, snapshot.read("$.a", Integer.class));
    }

    /**
     * Verifies: Cross-View Invariants — a write sequence on the store document
     * keeps reads, functions, and filters coherent.
     * Depends-On: deleteWithFilterRemovesMatches, addAppendsToArray, lengthYieldsArraySize.
     */
    @Test
    void storeWriteSequenceKeepsProjectionsCoherent() {
        DocumentContext ctx = JsonPath.parse(Json.STORE);
        ctx.delete("$.store.book[?(@.price > 10)]");
        assertEquals(2, ctx.read("$.store.book.length()", Integer.class));
        ctx.add("$.store.book", Map.of("category", "poetry", "author", "Anon", "title", "Leaves", "price", 5.0));
        assertEquals(3, ctx.read("$.store.book.length()", Integer.class));
        assertEquals(Arrays.asList("Sayings of the Century", "Moby Dick", "Leaves"),
                ctx.read("$.store.book[*].title"));
        assertEquals(List.of("Leaves"), ctx.read("$.store.book[?(@.price < 8)].title"));
        DocumentContext reparsed = JsonPath.parse(ctx.jsonString());
        assertEquals((Object) ctx.read("$.store.book[*].title"),
                (Object) reparsed.read("$.store.book[*].title"));
    }

    /**
     * Verifies: Cross-View Invariants — a property added by put is immediately
     * visible to filter evaluation.
     * Depends-On: putAddsMember, filterMatchingNothingYieldsEmptyList.
     */
    @Test
    void putPropertyVisibleToFilters() {
        DocumentContext ctx = JsonPath.parse(Json.STORE);
        assertEquals(List.of(), ctx.read("$.store.book[?(@.starred == true)].title"));
        ctx.put("$.store.book[0]", "starred", true);
        assertEquals(List.of("Sayings of the Century"), ctx.read("$.store.book[?(@.starred == true)].title"));
    }

    /**
     * Verifies: Cross-View Invariants — after an indefinite set, an
     * AS_PATH_LIST view names every written location and each re-reads to the
     * new value.
     * Depends-On: setIndefiniteAppliesToAllMatches, asPathListReturnsNormalizedPaths.
     */
    @Test
    void indefiniteSetVisibleThroughPathList() {
        DocumentContext ctx = JsonPath.parse("{\"a\":[{\"x\":1},{\"x\":2}]}");
        ctx.set("$.a[*].x", 9);
        String state = ctx.jsonString();
        Configuration pathCfg = Configuration.builder().options(Option.AS_PATH_LIST).build();
        List<String> paths = JsonPath.using(pathCfg).parse(state).read("$.a[*].x");
        assertEquals(List.of("$['a'][0]['x']", "$['a'][1]['x']"), paths);
        for (String path : paths) {
            assertEquals(9, (int) JsonPath.parse(state).read(path, Integer.class));
        }
    }
}
