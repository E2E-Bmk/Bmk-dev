package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.jayway.jsonpath.Configuration;
import com.jayway.jsonpath.Criteria;
import com.jayway.jsonpath.Filter;
import com.jayway.jsonpath.JsonPath;
import com.jayway.jsonpath.Option;
import java.util.Arrays;
import java.util.List;
import org.junit.jupiter.api.Test;
import support.Json;

/** Compiled path objects: reuse, normalization, and definiteness. */
class CompiledPathsAtomicTest {

    /**
     * Verifies: Compiled Paths — a compiled path reads exactly what the static
     * read produces.
     */
    @Test
    void compiledReadEqualsStaticRead() {
        JsonPath compiled = JsonPath.compile("$.store.book[0].title");
        assertEquals("Sayings of the Century", compiled.read(Json.STORE));
        assertEquals((Object) JsonPath.read(Json.STORE, "$.store.book[0].title"), compiled.read(Json.STORE));
    }

    /**
     * Verifies: Compiled Paths — getPath returns the normalized bracket form of
     * the path text.
     */
    @Test
    void getPathNormalizesToBracketForm() {
        assertEquals("$['store']['book'][0]['title']",
                JsonPath.compile("$.store.book[0].title").getPath());
    }

    /**
     * Verifies: Compiled Paths — isDefinite is true for a path without
     * wildcard, scan, slice, union, or filter.
     */
    @Test
    void isDefiniteTrueForPlainPath() {
        assertTrue(JsonPath.compile("$.store.bicycle.color").isDefinite());
        assertTrue(JsonPath.compile("$.store.book[0]").isDefinite());
    }

    /**
     * Verifies: Compiled Paths — isDefinite is false for wildcard, scan, slice,
     * union, and filter paths.
     */
    @Test
    void isDefiniteFalseForIndefiniteConstructs() {
        assertFalse(JsonPath.compile("$.a.*").isDefinite());
        assertFalse(JsonPath.compile("$..author").isDefinite());
        assertFalse(JsonPath.compile("$.a[0:1]").isDefinite());
        assertFalse(JsonPath.compile("$.a[0,1]").isDefinite());
        assertFalse(JsonPath.compile("$.a[?(@.x)]").isDefinite());
    }

    /**
     * Verifies: Compiled Paths — a compiled path evaluates under an explicit
     * configuration passed to read.
     */
    @Test
    void compiledReadHonorsConfiguration() {
        Configuration listCfg = Configuration.builder().options(Option.ALWAYS_RETURN_LIST).build();
        Object wrapped = JsonPath.compile("$.store.bicycle.color").read(Json.STORE, listCfg);
        assertEquals(List.of("red"), wrapped);
    }

    /**
     * Verifies: Compiled Paths — compile binds [?] placeholders to the supplied
     * filters.
     */
    @Test
    void compileBindsFilterPlaceholder() {
        Filter cheap = Filter.filter(Criteria.where("price").lt(10));
        JsonPath compiled = JsonPath.compile("$.store.book[?].title", cheap);
        assertEquals(Arrays.asList("Sayings of the Century", "Moby Dick"), compiled.read(Json.STORE));
        assertFalse(compiled.isDefinite());
    }
}
