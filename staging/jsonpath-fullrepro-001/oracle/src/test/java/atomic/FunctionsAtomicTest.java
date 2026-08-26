package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;

import com.jayway.jsonpath.JsonPath;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import org.junit.jupiter.api.Test;
import support.Json;

/** Aggregate path functions applied to the addressed value. */
class FunctionsAtomicTest {

    /**
     * Verifies: Functions — length() on an array yields its size as Integer.
     */
    @Test
    void lengthYieldsArraySize() {
        Object length = JsonPath.read(Json.STORE, "$.store.book.length()");
        assertInstanceOf(Integer.class, length);
        assertEquals(4, length);
    }

    /**
     * Verifies: Functions — min() over a numeric sequence yields the smallest
     * value as Double.
     */
    @Test
    void minYieldsSmallestValue() {
        Object min = JsonPath.read(Json.STORE, "$..book[*].price.min()");
        assertInstanceOf(Double.class, min);
        assertEquals(8.95, min);
    }

    /**
     * Verifies: Functions — max() over a numeric sequence yields the largest
     * value as Double.
     */
    @Test
    void maxYieldsLargestValue() {
        Object max = JsonPath.read(Json.STORE, "$..book[*].price.max()");
        assertInstanceOf(Double.class, max);
        assertEquals(22.99, max);
    }

    /**
     * Verifies: Functions — sum() over a numeric sequence yields the total as
     * Double.
     */
    @Test
    void sumYieldsTotal() {
        Object sum = JsonPath.read(Json.STORE, "$..book[*].price.sum()");
        assertInstanceOf(Double.class, sum);
        assertEquals(53.92, (Double) sum, 1e-9);
    }

    /**
     * Verifies: Functions — avg() over a numeric sequence yields the mean as
     * Double.
     */
    @Test
    void avgYieldsMean() {
        Object avg = JsonPath.read(Json.STORE, "$..book[*].price.avg()");
        assertInstanceOf(Double.class, avg);
        assertEquals(13.48, (Double) avg, 1e-9);
    }

    /**
     * Verifies: Functions — keys() on an object yields its key set in document
     * order.
     */
    @Test
    void keysYieldsKeySetInDocumentOrder() {
        Collection<?> keys = JsonPath.read(Json.STORE, "$.store.bicycle.keys()");
        assertEquals(Arrays.asList("color", "price"), new ArrayList<>(keys));
    }
}
