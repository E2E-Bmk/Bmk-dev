package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.jayway.jsonpath.Configuration;
import com.jayway.jsonpath.DocumentContext;
import com.jayway.jsonpath.JsonPath;
import com.jayway.jsonpath.Option;
import java.util.Map;
import org.junit.jupiter.api.Test;
import support.Json;

/** Parse entry points and DocumentContext read projections. */
class ContextsAtomicTest {

    /**
     * Verifies: Parsing and Document Contexts — parse returns a context whose
     * read evaluates paths against the parsed document.
     */
    @Test
    void parseReturnsReadableContext() {
        DocumentContext ctx = JsonPath.parse(Json.STORE);
        assertEquals("red", ctx.read("$.store.bicycle.color"));
    }

    /**
     * Verifies: Parsing and Document Contexts — the one-shot static read equals
     * parse followed by read.
     */
    @Test
    void staticReadEqualsParseThenRead() {
        Object oneShot = JsonPath.read(Json.STORE, "$..author");
        Object parsed = JsonPath.parse(Json.STORE).read("$..author");
        assertEquals(oneShot, parsed);
    }

    /**
     * Verifies: Parsing and Document Contexts — the typed read overload coerces
     * an integer to String.
     */
    @Test
    void typedReadCoercesIntegerToString() {
        assertEquals("10", JsonPath.parse(Json.STORE).read("$.expensive", String.class));
    }

    /**
     * Verifies: Parsing and Document Contexts — the typed read overload with
     * Integer.class returns the boxed integer.
     */
    @Test
    void typedReadKeepsInteger() {
        assertEquals(10, JsonPath.parse(Json.STORE).read("$.expensive", Integer.class));
    }

    /**
     * Verifies: Parsing and Document Contexts — the typed read overload coerces
     * a double to its String rendering.
     */
    @Test
    void typedReadCoercesDoubleToString() {
        assertEquals("19.95", JsonPath.parse(Json.STORE).read("$.store.bicycle.price", String.class));
    }

    /**
     * Verifies: Parsing and Document Contexts — json() returns the live
     * document model root.
     */
    @Test
    void jsonReturnsLiveModelRoot() {
        DocumentContext ctx = JsonPath.parse(Json.STORE);
        Object root = ctx.json();
        assertInstanceOf(Map.class, root);
        assertTrue(((Map<?, ?>) root).containsKey("store"));
        assertTrue(((Map<?, ?>) root).containsKey("expensive"));
    }

    /**
     * Verifies: Parsing and Document Contexts — jsonString() serializes the
     * current model state to JSON text that re-parses to equal values.
     */
    @Test
    void jsonStringSerializesModelState() {
        DocumentContext ctx = JsonPath.parse("{\"a\":{\"b\":1},\"list\":[1,2]}");
        DocumentContext reparsed = JsonPath.parse(ctx.jsonString());
        assertEquals(1, (int) reparsed.read("$.a.b", Integer.class));
        assertEquals((Object) ctx.read("$.list"), (Object) reparsed.read("$.list"));
    }

    /**
     * Verifies: Parsing and Document Contexts — using(configuration).parse
     * binds the context to that configuration.
     */
    @Test
    void usingBindsConfigurationToContext() {
        Configuration cfg = Configuration.builder().options(Option.ALWAYS_RETURN_LIST).build();
        DocumentContext ctx = JsonPath.using(cfg).parse("{}");
        assertTrue(ctx.configuration().getOptions().contains(Option.ALWAYS_RETURN_LIST));
    }
}
