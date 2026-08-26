package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.jayway.jsonpath.Configuration;
import com.jayway.jsonpath.JsonPath;
import com.jayway.jsonpath.Option;
import com.jayway.jsonpath.PathNotFoundException;
import java.util.List;
import org.junit.jupiter.api.Test;
import support.Json;

/** Configuration construction and the result-shape options. */
class OptionsAtomicTest {

    /**
     * Verifies: Configuration Options — the default configuration carries no
     * options.
     */
    @Test
    void defaultConfigurationHasNoOptions() {
        assertTrue(Configuration.defaultConfiguration().getOptions().isEmpty());
    }

    /**
     * Verifies: Configuration Options — addOptions returns a configuration with
     * the options added.
     */
    @Test
    void addOptionsAddsToConfiguration() {
        Configuration cfg = Configuration.defaultConfiguration().addOptions(Option.ALWAYS_RETURN_LIST);
        assertTrue(cfg.getOptions().contains(Option.ALWAYS_RETURN_LIST));
    }

    /**
     * Verifies: Configuration Options — the builder constructs a configuration
     * with the given options.
     */
    @Test
    void builderConstructsConfiguration() {
        Configuration cfg = Configuration.builder()
                .options(Option.SUPPRESS_EXCEPTIONS, Option.ALWAYS_RETURN_LIST).build();
        assertTrue(cfg.getOptions().contains(Option.SUPPRESS_EXCEPTIONS));
        assertTrue(cfg.getOptions().contains(Option.ALWAYS_RETURN_LIST));
        assertEquals(2, cfg.getOptions().size());
    }

    /**
     * Verifies: Configuration Options — ALWAYS_RETURN_LIST wraps a definite
     * result in a one-element list.
     */
    @Test
    void alwaysReturnListWrapsDefiniteResult() {
        Configuration cfg = Configuration.builder().options(Option.ALWAYS_RETURN_LIST).build();
        Object result = JsonPath.using(cfg).parse(Json.STORE).read("$.store.bicycle.color");
        assertEquals(List.of("red"), result);
    }

    /**
     * Verifies: Configuration Options — ALWAYS_RETURN_LIST leaves indefinite
     * results unchanged.
     */
    @Test
    void alwaysReturnListKeepsIndefiniteUnchanged() {
        Configuration cfg = Configuration.builder().options(Option.ALWAYS_RETURN_LIST).build();
        Object wrapped = JsonPath.using(cfg).parse(Json.STORE).read("$..author");
        assertEquals(Json.ALL_AUTHORS, wrapped);
    }

    /**
     * Verifies: Configuration Options — AS_PATH_LIST returns the normalized
     * path strings of the matches instead of their values.
     */
    @Test
    void asPathListReturnsNormalizedPaths() {
        Configuration cfg = Configuration.builder().options(Option.AS_PATH_LIST).build();
        List<String> paths = JsonPath.using(cfg).parse(Json.STORE).read("$..author");
        assertEquals(List.of(
                "$['store']['book'][0]['author']",
                "$['store']['book'][1]['author']",
                "$['store']['book'][2]['author']",
                "$['store']['book'][3]['author']"), paths);
    }

    /**
     * Verifies: Configuration Options — DEFAULT_PATH_LEAF_TO_NULL turns a
     * missing leaf on an existing parent into null instead of an error.
     */
    @Test
    void defaultPathLeafToNullYieldsNull() {
        Configuration cfg = Configuration.builder().options(Option.DEFAULT_PATH_LEAF_TO_NULL).build();
        assertNull(JsonPath.using(cfg).parse(Json.STORE).read("$.store.bicycle.nope"));
    }

    /**
     * Verifies: Configuration Options — SUPPRESS_EXCEPTIONS turns evaluation
     * failures into null.
     */
    @Test
    void suppressExceptionsYieldsNull() {
        Configuration cfg = Configuration.builder().options(Option.SUPPRESS_EXCEPTIONS).build();
        assertNull(JsonPath.using(cfg).parse(Json.STORE).read("$.store.nothing.here"));
    }

    /**
     * Verifies: Configuration Options — SUPPRESS_EXCEPTIONS combined with
     * ALWAYS_RETURN_LIST yields an empty list on failure.
     */
    @Test
    void suppressWithAlwaysListYieldsEmptyList() {
        Configuration cfg = Configuration.builder()
                .options(Option.SUPPRESS_EXCEPTIONS, Option.ALWAYS_RETURN_LIST).build();
        Object result = JsonPath.using(cfg).parse(Json.STORE).read("$.store.nothing.here");
        assertEquals(List.of(), result);
    }

    /**
     * Verifies: Configuration Options — REQUIRE_PROPERTIES raises
     * PathNotFoundException for a definite read of a missing property.
     */
    @Test
    void requirePropertiesRaisesOnMissingDefinite() {
        Configuration cfg = Configuration.builder().options(Option.REQUIRE_PROPERTIES).build();
        assertThrows(PathNotFoundException.class,
                () -> JsonPath.using(cfg).parse("{\"a\":{\"b\":1}}").read("$.a.missing"));
    }

    /**
     * Verifies: Configuration Options — REQUIRE_PROPERTIES raises when an
     * indefinite evaluation references a property missing from some element.
     */
    @Test
    void requirePropertiesRaisesOnIndefinite() {
        Configuration cfg = Configuration.builder().options(Option.REQUIRE_PROPERTIES).build();
        assertThrows(PathNotFoundException.class,
                () -> JsonPath.using(cfg).parse(Json.STORE).read("$.store.book[*].isbn"));
    }
}
