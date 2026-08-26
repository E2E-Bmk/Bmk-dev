package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNull;

import com.jayway.jsonpath.JsonPath;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import support.Json;

/** Runtime types of the loaded document model. */
class DocumentModelAtomicTest {

    /**
     * Verifies: Path Grammar and Read Evaluation — whole numbers load as
     * Integer.
     */
    @Test
    void wholeNumberLoadsAsInteger() {
        Object value = JsonPath.read(Json.STORE, "$.expensive");
        assertInstanceOf(Integer.class, value);
        assertEquals(10, value);
    }

    /**
     * Verifies: Path Grammar and Read Evaluation — decimal numbers load as
     * Double.
     */
    @Test
    void decimalNumberLoadsAsDouble() {
        Object value = JsonPath.read(Json.STORE, "$.store.bicycle.price");
        assertInstanceOf(Double.class, value);
        assertEquals(19.95, value);
    }

    /**
     * Verifies: Path Grammar and Read Evaluation — objects load as
     * insertion-ordered maps.
     */
    @Test
    void objectLoadsAsInsertionOrderedMap() {
        Map<String, Object> bicycle = JsonPath.read(Json.STORE, "$.store.bicycle");
        assertEquals(Arrays.asList("color", "price"), List.copyOf(bicycle.keySet()));
        assertEquals("red", bicycle.get("color"));
    }

    /**
     * Verifies: Path Grammar and Read Evaluation — true/false load as Boolean
     * and null loads as null.
     */
    @Test
    void booleanAndNullLoadAsModelValues() {
        assertEquals(Boolean.TRUE, JsonPath.read("{\"t\":true,\"n\":null}", "$.t"));
        assertNull(JsonPath.read("{\"t\":true,\"n\":null}", "$.n"));
    }

    /**
     * Verifies: Path Grammar and Read Evaluation — arrays load as lists.
     */
    @Test
    void arrayLoadsAsList() {
        Object books = JsonPath.read(Json.STORE, "$.store.book");
        assertInstanceOf(List.class, books);
        assertEquals(4, ((List<?>) books).size());
    }
}
