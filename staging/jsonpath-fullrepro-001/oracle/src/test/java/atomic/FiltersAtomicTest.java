package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.jayway.jsonpath.Criteria;
import com.jayway.jsonpath.Filter;
import com.jayway.jsonpath.JsonPath;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import support.Json;

/** Inline filter expressions and the programmatic Criteria/Filter builders. */
class FiltersAtomicTest {

    /**
     * Verifies: Filters and Criteria — an existence filter keeps elements that
     * have the property.
     */
    @Test
    void existenceFilterKeepsElementsWithProperty() {
        List<String> titles = JsonPath.read(Json.STORE, "$.store.book[?(@.isbn)].title");
        assertEquals(Arrays.asList("Moby Dick", "The Lord of the Rings"), titles);
    }

    /**
     * Verifies: Filters and Criteria — a less-than comparison against a numeric
     * literal.
     */
    @Test
    void numericLessThanFilter() {
        List<String> titles = JsonPath.read(Json.STORE, "$.store.book[?(@.price < 10)].title");
        assertEquals(Arrays.asList("Sayings of the Century", "Moby Dick"), titles);
    }

    /**
     * Verifies: Filters and Criteria — a greater-than comparison against a
     * numeric literal.
     */
    @Test
    void numericGreaterThanFilter() {
        List<String> titles = JsonPath.read(Json.STORE, "$.store.book[?(@.price > 20)].title");
        assertEquals(List.of("The Lord of the Rings"), titles);
    }

    /**
     * Verifies: Filters and Criteria — string equality against a quoted
     * literal.
     */
    @Test
    void stringEqualityFilter() {
        List<String> titles = JsonPath.read(Json.STORE, "$.store.book[?(@.category == 'fiction')].title");
        assertEquals(Arrays.asList("Sword of Honour", "Moby Dick", "The Lord of the Rings"), titles);
    }

    /**
     * Verifies: Filters and Criteria — the right side of a comparison may
     * reference the document root.
     */
    @Test
    void rootReferenceComparison() {
        List<String> titles = JsonPath.read(Json.STORE, "$.store.book[?(@.price > $.expensive)].title");
        assertEquals(Arrays.asList("Sword of Honour", "The Lord of the Rings"), titles);
    }

    /**
     * Verifies: Filters and Criteria — a slash-delimited regular expression
     * matches with the =~ operator.
     */
    @Test
    void regexFilterMatches() {
        List<String> titles = JsonPath.read(Json.STORE, "$.store.book[?(@.author =~ /.*Tolkien/)].title");
        assertEquals(List.of("The Lord of the Rings"), titles);
    }

    /**
     * Verifies: Filters and Criteria — membership with the in operator.
     */
    @Test
    void membershipInFilter() {
        List<String> titles = JsonPath.read(Json.STORE, "$.store.book[?(@.category in ['reference'])].title");
        assertEquals(List.of("Sayings of the Century"), titles);
    }

    /**
     * Verifies: Filters and Criteria — a filter matching nothing yields an
     * empty list under default options.
     */
    @Test
    void filterMatchingNothingYieldsEmptyList() {
        List<Object> none = JsonPath.read(Json.STORE, "$.store.book[?(@.price > 100)].title");
        assertTrue(none.isEmpty());
    }

    /**
     * Verifies: Filters and Criteria — Criteria.where(...).is(...) selects by
     * equality through the [?] placeholder.
     */
    @Test
    void criteriaWhereIsSelectsByEquality() {
        Filter reference = Filter.filter(Criteria.where("category").is("reference"));
        List<String> titles = JsonPath.read(Json.STORE, "$.store.book[?].title", reference);
        assertEquals(List.of("Sayings of the Century"), titles);
    }

    /**
     * Verifies: Filters and Criteria — lt constrains a criteria numerically.
     */
    @Test
    void criteriaLtSelectsBelowBound() {
        Filter cheap = Filter.filter(Criteria.where("price").lt(10));
        List<Map<String, Object>> books = JsonPath.read(Json.STORE, "$.store.book[?]", cheap);
        assertEquals(2, books.size());
        assertEquals("Sayings of the Century", books.get(0).get("title"));
        assertEquals("Moby Dick", books.get(1).get("title"));
    }

    /**
     * Verifies: Filters and Criteria — and(...) chains a further constraint on
     * another property.
     */
    @Test
    void criteriaAndChainsConstraints() {
        Filter expensiveFiction = Filter.filter(Criteria.where("category").is("fiction").and("price").gt(20));
        List<String> titles = JsonPath.read(Json.STORE, "$.store.book[?].title", expensiveFiction);
        assertEquals(List.of("The Lord of the Rings"), titles);
    }

    /**
     * Verifies: Filters and Criteria — a filter's toString renders the
     * equivalent inline form.
     */
    @Test
    void filterToStringRendersInlineForm() {
        Filter cheap = Filter.filter(Criteria.where("price").lt(10));
        assertEquals("[?(@['price'] < 10)]", cheap.toString());
    }
}
