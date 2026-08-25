package atomic;

import static fixtures.Deps.dep;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;

import org.eclipse.aether.graph.Exclusion;
import org.junit.jupiter.api.Test;
import org.siftway.selector.ExclusionDependencySelector;

/** Single-owner checks for ExclusionDependencySelector: exclusion coordinate matching. */
class ExclusionTest {

    // MUTATED: F3_exclusion_wildcard
    @Test
    void anEmptyGroupIdInAnExclusionMatchesAnyGroup() {
        ExclusionDependencySelector s =
                new ExclusionDependencySelector(Arrays.asList(new Exclusion("", "lib", "*", "*")));
        assertFalse(s.selectDependency(dep("com.x:lib:1", "compile")));
    }

    // MUTATED: F3_exclusion_wildcard
    @Test
    void anEmptyArtifactIdInAnExclusionMatchesAnyArtifact() {
        ExclusionDependencySelector s =
                new ExclusionDependencySelector(Arrays.asList(new Exclusion("com.x", "", "*", "*")));
        assertFalse(s.selectDependency(dep("com.x:lib:1", "compile")));
    }

    @Test
    void anExplicitCoordinateExclusionPrunesTheMatchingDependency() {
        ExclusionDependencySelector s =
                new ExclusionDependencySelector(Arrays.asList(new Exclusion("com.x", "lib", "*", "*")));
        assertFalse(s.selectDependency(dep("com.x:lib:1", "compile")));
    }

    @Test
    void aStarGroupWildcardPrunesRegardlessOfGroup() {
        ExclusionDependencySelector s =
                new ExclusionDependencySelector(Arrays.asList(new Exclusion("*", "lib", "*", "*")));
        assertFalse(s.selectDependency(dep("other.grp:lib:1", "compile")));
    }

    @Test
    void anExclusionThatMatchesNoCoordinateKeepsTheDependency() {
        ExclusionDependencySelector s =
                new ExclusionDependencySelector(Arrays.asList(new Exclusion("com.x", "other", "*", "*")));
        assertTrue(s.selectDependency(dep("com.x:lib:1", "compile")));
    }
}
