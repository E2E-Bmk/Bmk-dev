package atomic;

import static fixtures.Deps.dep;
import static fixtures.Deps.deriveN;
import static fixtures.Deps.emptyCtx;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.eclipse.aether.collection.DependencySelector;
import org.junit.jupiter.api.Test;
import org.siftway.selector.OptionalDependencySelector;

/** Single-owner checks for OptionalDependencySelector: depth-based pruning of optional dependencies. */
class OptionalTest {

    // MUTATED: F1_optional_depth
    @Test
    void optionalDependencyIsRetainedAtDepthTwo() {
        assertTrue(deriveN(new OptionalDependencySelector(), 2).selectDependency(dep("g:a:1", "compile", true)));
    }

    // MUTATED: F1_optional_depth
    @Test
    void theOptionalSelectorStillAdvancesToADeeperLevelAtDepthTwo() {
        DependencySelector atTwo = deriveN(new OptionalDependencySelector(), 2);
        assertNotEquals(atTwo, atTwo.deriveChildSelector(emptyCtx()));
    }

    @Test
    void aNonOptionalDependencyIsRetainedAtDepthTwo() {
        assertTrue(deriveN(new OptionalDependencySelector(), 2).selectDependency(dep("g:a:1", "compile", false)));
    }

    @Test
    void anOptionalDependencyIsRetainedAtTheRoot() {
        assertTrue(new OptionalDependencySelector().selectDependency(dep("g:a:1", "compile", true)));
    }

    @Test
    void anOptionalDependencyIsRetainedAtDepthOne() {
        assertTrue(deriveN(new OptionalDependencySelector(), 1).selectDependency(dep("g:a:1", "compile", true)));
    }
}
