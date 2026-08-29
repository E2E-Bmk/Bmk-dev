package atomic;

import java.util.Arrays;
import java.util.Iterator;
import java.util.List;
import java.util.NoSuchElementException;

import org.jboss.modules.IterableModuleFinder;
import org.jboss.modules.ModuleFinder;
import org.jboss.modules.ModuleLoader;
import org.jboss.modules.ModuleSpec;
import org.jboss.modules.Version;
import org.jboss.modules.filter.PathFilter;
import org.jboss.modules.filter.PathFilters;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

public class RewrittenUpstreamAtomicTest {
    /** Verifies: JMOD-VER-001, JMOD-VER-002, JMOD-VER-003. */
    @Test
    public void parsesAcceptedFormsAndRejectsMalformedForms() {
        assertEquals("1_1a.1993-12-31", Version.parse("1_1a.1993-12-31").toString());
        assertEquals("1a", Version.parse("1a").toString());
        assertThrows(IllegalArgumentException.class, () -> Version.parse("."));
        assertThrows(IllegalArgumentException.class, () -> Version.parse("1."));
        assertThrows(IllegalArgumentException.class, () -> Version.parse(".1"));
    }

    /** Verifies: JMOD-VER-004, JMOD-VER-005, JMOD-VER-006. */
    @Test
    public void comparesTokenSequencesInDocumentedOrder() {
        assertEquals(0, Version.parse("1.0").compareTo(Version.parse("1.0")));
        assertTrue(Version.parse("1.0").compareTo(Version.parse("1.0.0")) < 0);
        assertTrue(Version.parse("5u1").compareTo(Version.parse("5")) > 0);
        assertTrue(Version.parse("5u1").compareTo(Version.parse("5.1")) < 0);
    }

    /** Verifies: JMOD-VER-007. */
    @Test
    public void equalityAndHashingAgreeWithComparison() {
        Version left = Version.parse("10.20-alpha");
        Version right = Version.parse("10.20-alpha");
        assertEquals(0, left.compareTo(right));
        assertEquals(left, right);
        assertFalse(left.equals(Version.parse("10.020-alpha")));
    }

    /** Verifies: JMOD-VER-008, JMOD-VER-009, JMOD-VER-010, JMOD-VER-011, JMOD-VER-012. */
    @Test
    public void iteratorProjectsPartsSeparatorsAndTypedValues() {
        Version.Iterator iterator = Version.parse("12a+3").iterator();
        iterator.next();
        assertTrue(iterator.isNumberPart());
        assertEquals(2, iterator.length());
        iterator.next(); assertTrue(iterator.isEmptySeparator());
        iterator.next(); assertTrue(iterator.isAlphaPart()); assertEquals(1, iterator.length());
        iterator.next(); assertTrue(iterator.isNonEmptySeparator()); assertEquals(1, iterator.length());
        iterator.next(); assertTrue(iterator.isNumberPart()); assertEquals(1, iterator.length());
        assertFalse(iterator.hasNext());
        assertThrows(NoSuchElementException.class, iterator::next);
    }

    /** Verifies: JMOD-FILT-017, JMOD-FILT-018. */
    @Test
    public void globFiltersMatchPathsAndDescendants() {
        PathFilter recursive = PathFilters.match("foo/**");
        assertFalse(recursive.accept("foo"));
        assertTrue(recursive.accept("foo/bar"));
        assertTrue(recursive.accept("foo/bar/baz"));
        PathFilter exactAndDescendants = PathFilters.match("foo");
        assertTrue(exactAndDescendants.accept("foo"));
        assertTrue(exactAndDescendants.accept("foo/bar"));
    }

    /** Verifies: JMOD-LOAD-010, JMOD-LOAD-011. */
    @Test
    public void moduleIterationPreservesIterableFinderOrder() {
        IterableModuleFinder finder = new IterableModuleFinder() {
            public Iterator<String> iterateModules(String baseName, boolean recursive, ModuleLoader delegateLoader) { return Arrays.asList("alpha", "beta").iterator(); }
            public ModuleSpec findModule(String name, ModuleLoader delegateLoader) { return null; }
        };
        ModuleLoader loader = new ModuleLoader(new ModuleFinder[] { finder });
        Iterator<String> iterator = loader.iterateModules(null, true);
        List<String> names = Arrays.asList(iterator.next(), iterator.next());
        assertEquals(Arrays.asList("alpha", "beta"), names);
        assertFalse(iterator.hasNext());
        assertThrows(NoSuchElementException.class, iterator::next);
        assertThrows(UnsupportedOperationException.class, iterator::remove);
    }
}
