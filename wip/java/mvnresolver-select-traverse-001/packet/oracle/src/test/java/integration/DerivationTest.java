package integration;

import static fixtures.Deps.dep;
import static fixtures.Deps.deriveN;
import static fixtures.Deps.fatDep;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.eclipse.aether.collection.DependencySelector;
import org.eclipse.aether.collection.DependencyTraverser;
import org.junit.jupiter.api.Test;
import org.siftway.selector.AndDependencySelector;
import org.siftway.selector.ExclusionDependencySelector;
import org.siftway.selector.OptionalDependencySelector;
import org.siftway.selector.ScopeDependencySelector;
import org.siftway.selector.StaticDependencySelector;
import org.siftway.traverser.AndDependencyTraverser;
import org.siftway.traverser.FatArtifactTraverser;
import org.siftway.traverser.StaticDependencyTraverser;

/** Whole-chain checks: derive a selector or traverser down several levels and read its decisions. */
class DerivationTest {

    // Depends-On: atomic::StaticTest::staticSelectorDerivesAnInstanceEqualToItself
    @Test
    void aDeepStaticSelectorDerivationIsStable() {
        assertTrue(deriveN(new StaticDependencySelector(true), 4).selectDependency(dep("g:a:1", "compile")));
    }

    // Depends-On: atomic::StaticTest::staticTraverserDerivesAnInstanceEqualToItself
    @Test
    void aDeepStaticTraverserDerivationIsStable() {
        assertFalse(deriveN(new StaticDependencyTraverser(false), 4).traverseDependency(dep("g:a:1", "compile")));
    }

    // Depends-On: atomic::OptionalTest::aNonOptionalDependencyIsRetainedAtDepthTwo
    @Test
    void aDerivedOptionalSelectorKeepsANonOptionalDependencyAtDepthTwo() {
        assertTrue(deriveN(new OptionalDependencySelector(), 2).selectDependency(dep("g:a:1", "compile", false)));
    }

    // Depends-On: atomic::OptionalTest::aNonOptionalDependencyIsRetainedAtDepthTwo
    @Test
    void aDerivedOptionalSelectorKeepsANonOptionalDependencyAtDepthThree() {
        assertTrue(deriveN(new OptionalDependencySelector(), 3).selectDependency(dep("g:a:1", "compile", false)));
    }

    // Depends-On: atomic::ScopeTest::aTransitiveScopeSelectorExcludesTheTestScope
    @Test
    void aDerivedScopeSelectorExcludesTheTestScopeTransitively() {
        assertFalse(deriveN(new ScopeDependencySelector("test"), 1).selectDependency(dep("g:a:1", "test")));
    }

    // Depends-On: atomic::ScopeTest::aTransitiveScopeSelectorKeepsTheCompileScope
    @Test
    void aDerivedScopeSelectorKeepsTheCompileScopeTransitively() {
        assertTrue(deriveN(new ScopeDependencySelector("test"), 1).selectDependency(dep("g:a:1", "compile")));
    }

    // Depends-On: atomic::ScopeTest::aTransitiveScopeSelectorExcludesTheTestScope
    @Test
    void aDerivedScopeSelectorStillExcludesTheTestScopeAtADeeperLevel() {
        assertFalse(deriveN(new ScopeDependencySelector("test"), 2).selectDependency(dep("g:a:1", "test")));
    }

    // Depends-On: atomic::FatTest::anArtifactExplicitlyMarkedFatIsNotTraversed
    @Test
    void aDerivedFatTraverserSkipsAnExplicitlyFatArtifact() {
        assertFalse(deriveN(new FatArtifactTraverser(), 1).traverseDependency(fatDep("g:a:1", "true")));
    }

    // Depends-On: atomic::FatTest::anArtifactExplicitlyMarkedNonFatIsTraversed
    @Test
    void aDerivedFatTraverserTraversesAnExplicitlyNonFatArtifact() {
        assertTrue(deriveN(new FatArtifactTraverser(), 1).traverseDependency(fatDep("g:a:1", "false")));
    }

    // Depends-On: atomic::AndOrTest::aCompositeSelectsWhenEveryMemberSelects
    @Test
    void aDerivedCompositeOfKeepingStaticsStillKeeps() {
        DependencySelector s = new AndDependencySelector(
                new StaticDependencySelector(true), new StaticDependencySelector(true));
        assertTrue(deriveN(s, 1).selectDependency(dep("g:a:1", "compile")));
    }

    // Depends-On: atomic::AndTraverserTest::aCompositeSkipsWhenAnyMemberSkips
    @Test
    void aDerivedTraverserCompositeStillSkipsWhenAMemberSkips() {
        DependencyTraverser t = new AndDependencyTraverser(
                new StaticDependencyTraverser(true), new StaticDependencyTraverser(false));
        assertFalse(deriveN(t, 1).traverseDependency(dep("g:a:1", "compile")));
    }

    // Depends-On: atomic::ExclusionTest::anExclusionThatMatchesNoCoordinateKeepsTheDependency
    @Test
    void anEmptyExclusionSelectorKeepsEverythingAfterDerivation() {
        assertTrue(deriveN(new ExclusionDependencySelector(), 1).selectDependency(dep("com.x:lib:1", "compile")));
    }
}
