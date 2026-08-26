package integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.jayway.jsonpath.Configuration;
import com.jayway.jsonpath.Criteria;
import com.jayway.jsonpath.DocumentContext;
import com.jayway.jsonpath.Filter;
import com.jayway.jsonpath.JsonPath;
import com.jayway.jsonpath.Option;
import java.util.List;
import org.junit.jupiter.api.Test;
import support.Json;

/**
 * Agreement between the static, compiled, and context entry points, and the
 * predictions isDefinite and getPath make about evaluation.
 */
class CrossEntryPointIntegrationTest {

    /**
     * Verifies: Cross-View Invariants — static read, compiled read, and context
     * read agree on a definite path.
     * Depends-On: dotFormReadsNestedProperty, compiledReadEqualsStaticRead, parseReturnsReadableContext.
     */
    @Test
    void entryPointsAgreeOnDefinitePath() {
        String path = "$.store.book[-1].title";
        Object statics = JsonPath.read(Json.STORE, path);
        Object compiled = JsonPath.compile(path).read(Json.STORE);
        Object context = JsonPath.parse(Json.STORE).read(path);
        assertEquals("The Lord of the Rings", statics);
        assertEquals(statics, compiled);
        assertEquals(statics, context);
    }

    /**
     * Verifies: Cross-View Invariants — static read, compiled read, and context
     * read agree on an indefinite scan path.
     * Depends-On: deepScanSelectsAllDepths, staticReadEqualsParseThenRead.
     */
    @Test
    void entryPointsAgreeOnIndefinitePath() {
        String path = "$..author";
        Object statics = JsonPath.read(Json.STORE, path);
        Object compiled = JsonPath.compile(path).read(Json.STORE);
        Object context = JsonPath.parse(Json.STORE).read(path);
        assertEquals(Json.ALL_AUTHORS, statics);
        assertEquals(statics, compiled);
        assertEquals(statics, context);
    }

    /**
     * Verifies: Cross-View Invariants — static read, compiled read, and context
     * read agree on an inline filter path.
     * Depends-On: numericLessThanFilter, compiledReadEqualsStaticRead.
     */
    @Test
    void entryPointsAgreeOnFilterPath() {
        String path = "$.store.book[?(@.price < 10)].title";
        Object statics = JsonPath.read(Json.STORE, path);
        Object compiled = JsonPath.compile(path).read(Json.STORE);
        Object context = JsonPath.parse(Json.STORE).read(path);
        assertEquals(List.of("Sayings of the Century", "Moby Dick"), statics);
        assertEquals(statics, compiled);
        assertEquals(statics, context);
    }

    /**
     * Verifies: Cross-View Invariants — the normalized form from getPath
     * re-evaluates to the same result as the original definite path text.
     * Depends-On: getPathNormalizesToBracketForm, indexAddressesElement.
     */
    @Test
    void normalizedDefinitePathReEvaluatesSame() {
        JsonPath compiled = JsonPath.compile("$.store.book[0].title");
        String normalized = compiled.getPath();
        assertEquals("$['store']['book'][0]['title']", normalized);
        assertEquals((Object) JsonPath.read(Json.STORE, "$.store.book[0].title"),
                JsonPath.read(Json.STORE, normalized));
    }

    /**
     * Verifies: Cross-View Invariants — the normalized form of a scan path
     * re-evaluates to the same match list.
     * Depends-On: getPathNormalizesToBracketForm, deepScanSelectsAllDepths.
     */
    @Test
    void normalizedScanPathReEvaluatesSame() {
        String normalized = JsonPath.compile("$..author").getPath();
        assertEquals((Object) JsonPath.read(Json.STORE, "$..author"),
                JsonPath.read(Json.STORE, normalized));
    }

    /**
     * Verifies: Cross-View Invariants — isDefinite true predicts a bare value
     * result under default options.
     * Depends-On: isDefiniteTrueForPlainPath, decimalNumberLoadsAsDouble.
     */
    @Test
    void isDefiniteTruePredictsBareValue() {
        String path = "$.store.bicycle.price";
        assertTrue(JsonPath.compile(path).isDefinite());
        Object result = JsonPath.read(Json.STORE, path);
        assertFalse(result instanceof List);
        assertEquals(19.95, result);
    }

    /**
     * Verifies: Cross-View Invariants — isDefinite false predicts a list result
     * under default options.
     * Depends-On: isDefiniteFalseForIndefiniteConstructs, sliceIsHalfOpen.
     */
    @Test
    void isDefiniteFalsePredictsListResult() {
        String path = "$.store.book[1:3].title";
        assertFalse(JsonPath.compile(path).isDefinite());
        assertInstanceOf(List.class, JsonPath.read(Json.STORE, path));
    }

    /**
     * Verifies: State Model — reads never mutate: repeated evaluation of a path
     * yields equal results and leaves the serialized document unchanged.
     * Depends-On: parseReturnsReadableContext, jsonStringSerializesModelState.
     */
    @Test
    void repeatedReadsLeaveDocumentUnchanged() {
        DocumentContext ctx = JsonPath.parse(Json.STORE);
        String before = ctx.jsonString();
        Object first = ctx.read("$..author");
        Object second = ctx.read("$..author");
        assertEquals(first, second);
        assertEquals(before, ctx.jsonString());
    }

    /**
     * Verifies: Cross-View Invariants — the same configuration produces the
     * same result through the context and the compiled entry points.
     * Depends-On: alwaysReturnListWrapsDefiniteResult, compiledReadHonorsConfiguration.
     */
    @Test
    void configurationAppliesEquallyAcrossEntryPoints() {
        Configuration cfg = Configuration.builder().options(Option.ALWAYS_RETURN_LIST).build();
        Object viaContext = JsonPath.using(cfg).parse(Json.STORE).read("$.store.bicycle.color");
        Object viaCompiled = JsonPath.compile("$.store.bicycle.color").read(Json.STORE, cfg);
        assertEquals(List.of("red"), viaContext);
        assertEquals(viaContext, viaCompiled);
    }

    /**
     * Verifies: Cross-View Invariants — a [?] placeholder bound to a
     * programmatic filter selects exactly what the equivalent inline text
     * selects.
     * Depends-On: criteriaLtSelectsBelowBound, numericLessThanFilter.
     */
    @Test
    void placeholderFilterEqualsInlineFilterText() {
        Filter cheap = Filter.filter(Criteria.where("price").lt(10));
        Object viaPlaceholder = JsonPath.read(Json.STORE, "$.store.book[?].title", cheap);
        Object viaInline = JsonPath.read(Json.STORE, "$.store.book[?(@.price < 10)].title");
        assertEquals(viaInline, viaPlaceholder);
    }

    /**
     * Verifies: Cross-View Invariants — the rendered toString of a filter,
     * embedded as inline path text, selects the same elements as the filter
     * object itself.
     * Depends-On: filterToStringRendersInlineForm, criteriaLtSelectsBelowBound.
     */
    @Test
    void filterToStringRoundTripsThroughPathText() {
        Filter cheap = Filter.filter(Criteria.where("price").lt(10));
        Object viaObject = JsonPath.read(Json.STORE, "$.store.book[?].title", cheap);
        Object viaRendered = JsonPath.read(Json.STORE, "$.store.book" + cheap + ".title");
        assertEquals(viaObject, viaRendered);
    }
}
