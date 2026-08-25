package atomic;

import static fixtures.Deps.dep;
import static fixtures.Deps.deriveN;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;
import java.util.Collections;

import org.junit.jupiter.api.Test;
import org.siftway.selector.ScopeDependencySelector;

/** Single-owner checks for ScopeDependencySelector: scope include/exclude filtering. */
class ScopeTest {

    // MUTATED: F2_scope_root
    @Test
    void aFreshScopeSelectorExcludesADirectTestScopedDependency() {
        assertFalse(new ScopeDependencySelector("test").selectDependency(dep("g:a:1", "test")));
    }

    // MUTATED: F2_scope_root
    @Test
    void aFreshScopeSelectorAppliesItsIncludeFilterToADirectDependency() {
        ScopeDependencySelector s =
                new ScopeDependencySelector(Arrays.asList("compile"), Collections.<String>emptyList());
        assertFalse(s.selectDependency(dep("g:a:1", "test")));
    }

    @Test
    void aTransitiveScopeSelectorExcludesTheTestScope() {
        assertFalse(deriveN(new ScopeDependencySelector("test"), 1).selectDependency(dep("g:a:1", "test")));
    }

    @Test
    void aTransitiveScopeSelectorKeepsTheCompileScope() {
        assertTrue(deriveN(new ScopeDependencySelector("test"), 1).selectDependency(dep("g:a:1", "compile")));
    }

    @Test
    void scopeSelectorsWithTheSameConfigurationAreEqual() {
        assertEquals(new ScopeDependencySelector("test"), new ScopeDependencySelector("test"));
    }
}
