package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;

import com.jayway.jsonpath.JsonPath;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import support.Json;

/** Path grammar constructs and their read evaluation on the store document. */
class PathGrammarAtomicTest {

    /**
     * Verifies: Path Grammar and Read Evaluation — dot form addresses nested
     * properties.
     */
    @Test
    void dotFormReadsNestedProperty() {
        assertEquals("red", JsonPath.read(Json.STORE, "$.store.bicycle.color"));
    }

    /**
     * Verifies: Path Grammar and Read Evaluation — bracket form addresses the
     * same value as dot form.
     */
    @Test
    void bracketFormEqualsDotForm() {
        Object dot = JsonPath.read(Json.STORE, "$.store.bicycle.color");
        Object bracket = JsonPath.read(Json.STORE, "$['store']['bicycle']['color']");
        assertEquals(dot, bracket);
    }

    /**
     * Verifies: Path Grammar and Read Evaluation — an index addresses one array
     * element.
     */
    @Test
    void indexAddressesElement() {
        assertEquals("Sayings of the Century", JsonPath.read(Json.STORE, "$.store.book[0].title"));
    }

    /**
     * Verifies: Path Grammar and Read Evaluation — a negative index counts from
     * the end of the array.
     */
    @Test
    void negativeIndexCountsFromEnd() {
        assertEquals("The Lord of the Rings", JsonPath.read(Json.STORE, "$.store.book[-1].title"));
        assertEquals("Moby Dick", JsonPath.read(Json.STORE, "$.store.book[-2].title"));
    }

    /**
     * Verifies: Path Grammar and Read Evaluation — a slice is half-open.
     */
    @Test
    void sliceIsHalfOpen() {
        List<String> titles = JsonPath.read(Json.STORE, "$.store.book[1:3].title");
        assertEquals(Arrays.asList("Sword of Honour", "Moby Dick"), titles);
    }

    /**
     * Verifies: Path Grammar and Read Evaluation — a slice with an open start
     * begins at index zero.
     */
    @Test
    void sliceOpenStartBeginsAtZero() {
        List<String> titles = JsonPath.read(Json.STORE, "$.store.book[:2].title");
        assertEquals(Arrays.asList("Sayings of the Century", "Sword of Honour"), titles);
    }

    /**
     * Verifies: Path Grammar and Read Evaluation — a slice with an open end runs
     * to the last element.
     */
    @Test
    void sliceOpenEndRunsToLast() {
        List<String> titles = JsonPath.read(Json.STORE, "$.store.book[2:].title");
        assertEquals(Arrays.asList("Moby Dick", "The Lord of the Rings"), titles);
    }

    /**
     * Verifies: Path Grammar and Read Evaluation — an index union selects the
     * listed indexes in the listed order.
     */
    @Test
    void indexUnionSelectsListedOrder() {
        List<String> titles = JsonPath.read(Json.STORE, "$.store.book[0,2].title");
        assertEquals(Arrays.asList("Sayings of the Century", "Moby Dick"), titles);
    }

    /**
     * Verifies: Path Grammar and Read Evaluation — a property union projects the
     * named properties into an ordered map result.
     */
    @Test
    void propertyUnionProjectsOrderedMap() {
        Map<String, Object> projection = JsonPath.read(Json.STORE, "$.store.book[0]['title','price']");
        assertEquals(Arrays.asList("title", "price"), List.copyOf(projection.keySet()));
        assertEquals("Sayings of the Century", projection.get("title"));
        assertEquals(8.95, projection.get("price"));
    }

    /**
     * Verifies: Path Grammar and Read Evaluation — the property union preserves
     * the listed property order, not the document order.
     */
    @Test
    void propertyUnionUsesListedOrder() {
        Map<String, Object> projection = JsonPath.read(Json.STORE, "$.store.book[0]['price','title']");
        assertEquals(Arrays.asList("price", "title"), List.copyOf(projection.keySet()));
    }

    /**
     * Verifies: Path Grammar and Read Evaluation — a wildcard over an array
     * selects every element.
     */
    @Test
    void wildcardOverArraySelectsAll() {
        List<String> authors = JsonPath.read(Json.STORE, "$.store.book[*].author");
        assertEquals(Json.ALL_AUTHORS, authors);
    }

    /**
     * Verifies: Path Grammar and Read Evaluation — a wildcard over an object
     * selects every member value.
     */
    @Test
    void wildcardOverObjectSelectsMemberValues() {
        List<Object> values = JsonPath.read(Json.STORE, "$.store.bicycle.*");
        assertEquals(Arrays.asList("red", 19.95), values);
    }

    /**
     * Verifies: Path Grammar and Read Evaluation — deep scan selects matching
     * descendants at any depth in document order.
     */
    @Test
    void deepScanSelectsAllDepths() {
        List<String> authors = JsonPath.read(Json.STORE, "$..author");
        assertEquals(Json.ALL_AUTHORS, authors);
    }

    /**
     * Verifies: Path Grammar and Read Evaluation — deep scan returns a list even
     * when only one descendant matches.
     */
    @Test
    void deepScanReturnsListForSingleMatch() {
        List<String> colors = JsonPath.read(Json.STORE, "$..bicycle.color");
        assertEquals(List.of("red"), colors);
    }

    /**
     * Verifies: Path Grammar and Read Evaluation — deep scan under a prefix
     * collects descendants of that subtree in document order.
     */
    @Test
    void deepScanUnderPrefixCollectsSubtree() {
        List<Object> prices = JsonPath.read(Json.STORE, "$.store..price");
        assertEquals(Arrays.asList(8.95, 12.99, 8.99, 22.99, 19.95), prices);
    }

    /**
     * Verifies: Path Grammar and Read Evaluation — under default options a
     * definite path evaluates to the value itself and an indefinite path to a
     * list of matches.
     */
    @Test
    void definiteYieldsValueIndefiniteYieldsList() {
        assertInstanceOf(String.class, JsonPath.read(Json.STORE, "$.store.book[-1].title"));
        assertInstanceOf(List.class, JsonPath.read(Json.STORE, "$.store.book[*].title"));
    }

    /**
     * Verifies: Path Grammar and Read Evaluation — an indefinite evaluation
     * skips elements missing the referenced property under default options.
     */
    @Test
    void indefiniteSkipsMissingProperties() {
        List<String> isbns = JsonPath.read(Json.STORE, "$.store.book[*].isbn");
        assertEquals(Arrays.asList("0-553-21311-3", "0-395-19395-8"), isbns);
    }
}
