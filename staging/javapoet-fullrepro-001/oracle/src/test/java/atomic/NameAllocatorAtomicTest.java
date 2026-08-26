package atomic;

import static org.junit.jupiter.api.Assertions.*;

import com.squareup.javapoet.NameAllocator;
import org.junit.jupiter.api.Test;

/** Atomic tests for name allocation. */
class NameAllocatorAtomicTest {

    /** Verifies: Name Allocation — keyword suffixing. */
    @Test void keywordSuggestionGetsUnderscoreSuffix() {
        assertEquals("public_", new NameAllocator().newName("public"));
    }

    /** Verifies: Name Allocation — collision suffixing on repeated suggestions. */
    @Test void duplicateSuggestionGetsSuffix() {
        NameAllocator allocator = new NameAllocator();
        assertEquals("foo", allocator.newName("foo"));
        assertEquals("foo_", allocator.newName("foo"));
    }

    /** Verifies: Name Allocation — illegal characters replaced with underscores. */
    @Test void illegalCharactersAreReplaced() {
        assertEquals("a_b", new NameAllocator().newName("a-b"));
    }

    /** Verifies: Name Allocation — leading digit prefixed with underscore. */
    @Test void leadingDigitIsPrefixed() {
        assertEquals("_1st", new NameAllocator().newName("1st"));
    }

    /** Verifies: Name Allocation — tag registration and lookup. */
    @Test void tagRegistrationRoundTrips() {
        NameAllocator allocator = new NameAllocator();
        String allocated = allocator.newName("value", 1);
        assertEquals(allocated, allocator.get(1));
    }

    /** Verifies: Name Allocation — clone yields an independent allocator with same registrations. */
    @Test void cloneCarriesRegistrationsIndependently() {
        NameAllocator allocator = new NameAllocator();
        allocator.newName("x", "tag");
        NameAllocator copy = allocator.clone();
        assertEquals(allocator.get("tag"), copy.get("tag"));
        assertEquals("x_", copy.newName("x"));
    }
}
