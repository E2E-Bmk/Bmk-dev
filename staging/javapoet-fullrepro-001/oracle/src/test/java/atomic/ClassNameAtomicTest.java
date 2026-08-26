package atomic;

import static org.junit.jupiter.api.Assertions.*;

import com.squareup.javapoet.ClassName;
import org.junit.jupiter.api.Test;

/** Atomic tests for ClassName construction and navigation. */
class ClassNameAtomicTest {

    /** Verifies: Type Name Model — get with package and simple name. */
    @Test void getBuildsFromPackageAndSimpleName() {
        ClassName name = ClassName.get("com.acme", "Widget");
        assertEquals("com.acme", name.packageName());
        assertEquals("Widget", name.simpleName());
        assertEquals("com.acme.Widget", name.toString());
    }

    /** Verifies: Type Name Model — bestGuess splits package and nesting chain. */
    @Test void bestGuessSplitsPackageAndNestedClasses() {
        ClassName entry = ClassName.bestGuess("java.util.Map.Entry");
        assertEquals("java.util", entry.packageName());
        assertEquals("Entry", entry.simpleName());
        assertEquals("java.util.Map.Entry", entry.canonicalName());
    }

    /** Verifies: Cross-View Invariants — reflectionName uses $ between class segments. */
    @Test void reflectionNameUsesDollarForNesting() {
        assertEquals("java.util.Map$Entry",
                ClassName.bestGuess("java.util.Map.Entry").reflectionName());
        assertEquals("java.lang.String", ClassName.get(String.class).reflectionName());
    }

    /** Verifies: Cross-View Invariants — topLevelClassName is the head of the chain. */
    @Test void topLevelClassNameIsChainHead() {
        assertEquals(ClassName.get("java.util", "Map"),
                ClassName.bestGuess("java.util.Map.Entry").topLevelClassName());
    }

    /** Verifies: Cross-View Invariants — nestedClass then enclosingClassName returns receiver. */
    @Test void nestedClassEnclosingRoundTrip() {
        ClassName outer = ClassName.get("com.acme", "Outer");
        ClassName inner = outer.nestedClass("Inner");
        assertEquals("com.acme.Outer.Inner", inner.canonicalName());
        assertEquals(outer, inner.enclosingClassName());
        assertNull(outer.enclosingClassName());
    }

    /** Verifies: Type Name Model — peerClass names a sibling. */
    @Test void peerClassNamesSibling() {
        assertEquals("com.acme.Sibling",
                ClassName.get("com.acme", "Outer").peerClass("Sibling").toString());
    }

    /** Verifies: Type Name Model — default package uses empty package name. */
    @Test void defaultPackageRendersBareName() {
        ClassName bare = ClassName.get("", "NoPkg");
        assertEquals("", bare.packageName());
        assertEquals("NoPkg", bare.toString());
    }

    /** Verifies: Type Name Model — value equality and comparability. */
    @Test void equalChainsAreEqualAndComparable() {
        assertEquals(ClassName.get("a.b", "C"), ClassName.get("a.b", "C"));
        assertEquals(0, ClassName.get("a.b", "C").compareTo(ClassName.get("a.b", "C")));
        assertTrue(ClassName.get("a.b", "C").compareTo(ClassName.get("a.b", "D")) < 0);
    }

    /** Verifies: Error Semantics — bestGuess with no class segment throws. */
    @Test void bestGuessWithoutClassSegmentThrows() {
        assertThrows(IllegalArgumentException.class, () -> ClassName.bestGuess("com.example."));
        assertThrows(IllegalArgumentException.class, () -> ClassName.bestGuess("com.example"));
    }
}
