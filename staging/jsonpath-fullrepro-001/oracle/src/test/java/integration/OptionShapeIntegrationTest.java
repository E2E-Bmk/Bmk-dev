package integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.jayway.jsonpath.Configuration;
import com.jayway.jsonpath.JsonPath;
import com.jayway.jsonpath.Option;
import com.jayway.jsonpath.PathNotFoundException;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import support.Json;

/**
 * Interactions between result-shape options and the queries they reshape:
 * path lists that must re-read to the same values, wrapping that must not
 * change match content, and suppression that must compose.
 */
class OptionShapeIntegrationTest {

    private static Configuration with(Option... options) {
        return Configuration.builder().options(options).build();
    }

    /**
     * Verifies: Cross-View Invariants — each AS_PATH_LIST path from a scan
     * query re-reads individually to the values the plain query returns, in
     * order.
     * Depends-On: asPathListReturnsNormalizedPaths, deepScanSelectsAllDepths.
     */
    @Test
    void pathListOfScanRereadsToPlainValues() {
        List<String> paths = JsonPath.using(with(Option.AS_PATH_LIST)).parse(Json.STORE).read("$..author");
        List<Object> reread = new ArrayList<>();
        for (String path : paths) {
            reread.add(JsonPath.read(Json.STORE, path));
        }
        assertEquals((Object) JsonPath.read(Json.STORE, "$..author"), reread);
    }

    /**
     * Verifies: Cross-View Invariants — each AS_PATH_LIST path from a filter
     * query re-reads individually to the filtered values.
     * Depends-On: asPathListReturnsNormalizedPaths, existenceFilterKeepsElementsWithProperty.
     */
    @Test
    void pathListOfFilterRereadsToFilteredValues() {
        String query = "$.store.book[?(@.isbn)].title";
        List<String> paths = JsonPath.using(with(Option.AS_PATH_LIST)).parse(Json.STORE).read(query);
        assertEquals(List.of(
                "$['store']['book'][2]['title']",
                "$['store']['book'][3]['title']"), paths);
        List<Object> reread = new ArrayList<>();
        for (String path : paths) {
            reread.add(JsonPath.read(Json.STORE, path));
        }
        assertEquals((Object) JsonPath.read(Json.STORE, query), reread);
    }

    /**
     * Verifies: Configuration Options — AS_PATH_LIST on a definite path returns
     * the one normalized path of its single match.
     * Depends-On: asPathListReturnsNormalizedPaths, dotFormReadsNestedProperty.
     */
    @Test
    void pathListOfDefinitePathNamesSingleMatch() {
        List<String> paths = JsonPath.using(with(Option.AS_PATH_LIST)).parse(Json.STORE)
                .read("$.store.bicycle.color");
        assertEquals(List.of("$['store']['bicycle']['color']"), paths);
    }

    /**
     * Verifies: Cross-View Invariants — ALWAYS_RETURN_LIST wraps a definite
     * result whose single element equals the unwrapped read.
     * Depends-On: alwaysReturnListWrapsDefiniteResult, indexAddressesElement.
     */
    @Test
    void wrappedDefiniteElementEqualsUnwrappedRead() {
        List<Object> wrapped = JsonPath.using(with(Option.ALWAYS_RETURN_LIST)).parse(Json.STORE)
                .read("$.store.book[0].title");
        assertEquals(1, wrapped.size());
        assertEquals((Object) JsonPath.read(Json.STORE, "$.store.book[0].title"), wrapped.get(0));
    }

    /**
     * Verifies: Cross-View Invariants — ALWAYS_RETURN_LIST leaves an indefinite
     * filter result equal to the default read.
     * Depends-On: alwaysReturnListKeepsIndefiniteUnchanged, existenceFilterKeepsElementsWithProperty.
     */
    @Test
    void wrappedIndefiniteResultEqualsDefaultRead() {
        String query = "$.store.book[?(@.isbn)].title";
        Object wrapped = JsonPath.using(with(Option.ALWAYS_RETURN_LIST)).parse(Json.STORE).read(query);
        assertEquals((Object) JsonPath.read(Json.STORE, query), wrapped);
    }

    /**
     * Verifies: Configuration Options — SUPPRESS_EXCEPTIONS yields null through
     * the context and the compiled entry points alike.
     * Depends-On: suppressExceptionsYieldsNull, compiledReadHonorsConfiguration.
     */
    @Test
    void suppressionAppliesAcrossEntryPoints() {
        Configuration suppress = with(Option.SUPPRESS_EXCEPTIONS);
        assertNull(JsonPath.using(suppress).parse(Json.STORE).read("$.store.nothing.here"));
        assertNull(JsonPath.compile("$.store.nothing.here").read(Json.STORE, suppress));
    }

    /**
     * Verifies: Configuration Options — suppression composed with list wrapping
     * turns the same failing query into an empty list.
     * Depends-On: suppressExceptionsYieldsNull, suppressWithAlwaysListYieldsEmptyList.
     */
    @Test
    void suppressionComposesWithListWrapping() {
        String query = "$.store.nothing.here";
        assertNull(JsonPath.using(with(Option.SUPPRESS_EXCEPTIONS)).parse(Json.STORE).read(query));
        Object asList = JsonPath.using(with(Option.SUPPRESS_EXCEPTIONS, Option.ALWAYS_RETURN_LIST))
                .parse(Json.STORE).read(query);
        assertEquals(List.of(), asList);
    }

    /**
     * Verifies: Configuration Options — DEFAULT_PATH_LEAF_TO_NULL changes only
     * the missing leaf: an existing leaf reads its value, a missing one reads
     * null, and without the option the same missing leaf raises.
     * Depends-On: defaultPathLeafToNullYieldsNull, missingPropertyRaisesPathNotFound.
     */
    @Test
    void leafToNullAffectsOnlyMissingLeaf() {
        Configuration leafNull = with(Option.DEFAULT_PATH_LEAF_TO_NULL);
        assertEquals("red", JsonPath.using(leafNull).parse(Json.STORE).read("$.store.bicycle.color"));
        assertNull(JsonPath.using(leafNull).parse(Json.STORE).read("$.store.bicycle.nope"));
        assertThrows(PathNotFoundException.class,
                () -> JsonPath.parse(Json.STORE).read("$.store.bicycle.nope"));
    }

    /**
     * Verifies: Configuration Options — REQUIRE_PROPERTIES flips the default
     * skip-missing behavior of the same indefinite query into a raise.
     * Depends-On: requirePropertiesRaisesOnIndefinite, indefiniteSkipsMissingProperties.
     */
    @Test
    void requirePropertiesFlipsSkipIntoRaise() {
        String query = "$.store.book[*].isbn";
        assertEquals(2, ((List<?>) JsonPath.read(Json.STORE, query)).size());
        assertThrows(PathNotFoundException.class,
                () -> JsonPath.using(with(Option.REQUIRE_PROPERTIES)).parse(Json.STORE).read(query));
    }

    /**
     * Verifies: Configuration Options — a configuration assembled through
     * addOptions behaves like one assembled through the builder.
     * Depends-On: addOptionsAddsToConfiguration, builderConstructsConfiguration.
     */
    @Test
    void addOptionsBehavesLikeBuilder() {
        Configuration viaAdd = Configuration.defaultConfiguration().addOptions(Option.ALWAYS_RETURN_LIST);
        Configuration viaBuilder = with(Option.ALWAYS_RETURN_LIST);
        assertEquals(viaBuilder.getOptions(), viaAdd.getOptions());
        Object a = JsonPath.using(viaAdd).parse(Json.STORE).read("$.store.bicycle.color");
        Object b = JsonPath.using(viaBuilder).parse(Json.STORE).read("$.store.bicycle.color");
        assertEquals(List.of("red"), a);
        assertEquals(a, b);
    }
}
