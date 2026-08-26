package atomic;

import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.jayway.jsonpath.InvalidJsonException;
import com.jayway.jsonpath.InvalidModificationException;
import com.jayway.jsonpath.InvalidPathException;
import com.jayway.jsonpath.JsonPath;
import com.jayway.jsonpath.JsonPathException;
import com.jayway.jsonpath.PathNotFoundException;
import org.junit.jupiter.api.Test;
import support.Json;

/** Required exception classes for the specified failure conditions. */
class ErrorsAtomicTest {

    /**
     * Verifies: Error Semantics — a definite path addressing a missing property
     * raises PathNotFoundException naming the normalized path.
     */
    @Test
    void missingPropertyRaisesPathNotFound() {
        PathNotFoundException ex = assertThrows(PathNotFoundException.class,
                () -> JsonPath.read(Json.STORE, "$.store.nothing"));
        assertTrue(ex.getMessage().contains("$['store']['nothing']"));
    }

    /**
     * Verifies: Error Semantics — an out-of-range index raises
     * PathNotFoundException naming the normalized path.
     */
    @Test
    void outOfRangeIndexRaisesPathNotFound() {
        PathNotFoundException ex = assertThrows(PathNotFoundException.class,
                () -> JsonPath.read(Json.STORE, "$.store.book[99]"));
        assertTrue(ex.getMessage().contains("$['store']['book'][99]"));
    }

    /**
     * Verifies: Error Semantics — descending into a scalar raises
     * PathNotFoundException.
     */
    @Test
    void descendingIntoScalarRaisesPathNotFound() {
        assertThrows(PathNotFoundException.class,
                () -> JsonPath.read(Json.STORE, "$.store.book[0].title.nope"));
    }

    /**
     * Verifies: Error Semantics — unparseable path text raises
     * InvalidPathException.
     */
    @Test
    void unparseablePathRaisesInvalidPath() {
        assertThrows(InvalidPathException.class, () -> JsonPath.compile("this is bad"));
    }

    /**
     * Verifies: Error Semantics — a null path raises IllegalArgumentException.
     */
    @Test
    void nullPathRaisesIllegalArgument() {
        assertThrows(IllegalArgumentException.class, () -> JsonPath.compile(null));
    }

    /**
     * Verifies: Error Semantics — an empty path raises
     * IllegalArgumentException.
     */
    @Test
    void emptyPathRaisesIllegalArgument() {
        assertThrows(IllegalArgumentException.class, () -> JsonPath.compile(""));
    }

    /**
     * Verifies: Error Semantics — input that is not valid JSON raises
     * InvalidJsonException on parse.
     */
    @Test
    void invalidJsonRaisesInvalidJson() {
        assertThrows(InvalidJsonException.class, () -> JsonPath.parse("{not json"));
    }

    /**
     * Verifies: Error Semantics — add targeting a value that is not an array
     * raises InvalidModificationException.
     */
    @Test
    void addToNonArrayRaisesInvalidModification() {
        assertThrows(InvalidModificationException.class,
                () -> JsonPath.parse("[1]").add("$[0]", 5));
    }

    /**
     * Verifies: Error Semantics — the library failures are subclasses of
     * JsonPathException.
     */
    @Test
    void libraryFailuresAreJsonPathExceptions() {
        Exception notFound = assertThrows(Exception.class, () -> JsonPath.read(Json.STORE, "$.nope"));
        assertInstanceOf(JsonPathException.class, notFound);
        Exception badPath = assertThrows(Exception.class, () -> JsonPath.compile("this is bad"));
        assertInstanceOf(JsonPathException.class, badPath);
        Exception badJson = assertThrows(Exception.class, () -> JsonPath.parse("{not json"));
        assertInstanceOf(JsonPathException.class, badJson);
        Exception badWrite = assertThrows(Exception.class, () -> JsonPath.parse("[1]").add("$[0]", 5));
        assertInstanceOf(JsonPathException.class, badWrite);
    }
}
