package integration;

import static fixtures.Deps.ctx;
import static fixtures.Deps.dep;
import static fixtures.Deps.depExcl;
import static fixtures.Deps.deriveN;
import static fixtures.Deps.plainDep;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;

import org.eclipse.aether.collection.DependencySelector;
import org.eclipse.aether.collection.DependencyTraverser;
import org.eclipse.aether.graph.Exclusion;
import org.junit.jupiter.api.Test;
import org.siftway.selector.AndDependencySelector;
import org.siftway.selector.ExclusionDependencySelector;
import org.siftway.selector.OptionalDependencySelector;
import org.siftway.selector.ScopeDependencySelector;
import org.siftway.selector.StaticDependencySelector;
import org.siftway.traverser.AndDependencyTraverser;
import org.siftway.traverser.FatArtifactTraverser;
import org.siftway.traverser.StaticDependencyTraverser;

/** Cross-owner checks: composites, derivation and the interplay of two owners over one dependency. */
class CompositionTest {

    private static ExclusionDependencySelector excludes(String g, String a) {
        return new ExclusionDependencySelector(Arrays.asList(new Exclusion(g, a, "*", "*")));
    }

    // Depends-On: atomic::OptionalTest::anOptionalDependencyIsRetainedAtTheRoot
    // MUTATED: F5_and_or
    @Test
    void aCompositeKeepsADependencyThatOnlyTheOptionalMemberKeeps() {
        DependencySelector s = new AndDependencySelector(new OptionalDependencySelector(), excludes("com.x", "lib"));
        assertTrue(s.selectDependency(dep("com.x:lib:1", "compile", true)));
    }

    // Depends-On: atomic::OptionalTest::optionalDependencyIsRetainedAtDepthTwo
    // MUTATED: F1_optional_depth
    @Test
    void aCompositeWithAnOptionalMemberKeepsTheOptionalDependencyAtDepthTwo() {
        DependencySelector s = new AndDependencySelector(
                new OptionalDependencySelector(), new StaticDependencySelector(false));
        assertTrue(deriveN(s, 2).selectDependency(dep("g:a:1", "compile", true)));
    }

    // Depends-On: atomic::OptionalTest::optionalDependencyIsRetainedAtDepthTwo
    // MUTATED: F1_optional_depth
    @Test
    void aCompositeOfOptionalAndExclusionKeepsAnExcludedOptionalAtDepthTwo() {
        DependencySelector s = new AndDependencySelector(new OptionalDependencySelector(), excludes("com.x", "lib"));
        assertTrue(deriveN(s, 2).selectDependency(dep("com.x:lib:1", "compile", true)));
    }

    // Depends-On: atomic::AndOrTest::aCompositeSelectsWhenOnlyItsFirstMemberSelects
    // MUTATED: F5_and_or
    @Test
    void newInstanceOfTwoDifferingSelectorsKeepsWhenEitherKeeps() {
        DependencySelector s = AndDependencySelector.newInstance(
                new StaticDependencySelector(true), new StaticDependencySelector(false));
        assertTrue(s.selectDependency(dep("g:a:1", "compile")));
    }

    // Depends-On: atomic::FatTest::anArtifactWithoutTheFatPropertyIsNotTraversed
    // MUTATED: F4_fat_default
    @Test
    void aTraverserCompositeSkipsAnUndeclaredArtifact() {
        DependencyTraverser t = new AndDependencyTraverser(
                new FatArtifactTraverser(), new StaticDependencyTraverser(true));
        assertFalse(t.traverseDependency(plainDep("g:a:1")));
    }

    // Depends-On: atomic::ScopeTest::aFreshScopeSelectorExcludesADirectTestScopedDependency
    // MUTATED: F2_scope_root
    @Test
    void aScopeSelectorFiltersADirectDependencyAndThenItsTransitiveChild() {
        ScopeDependencySelector root = new ScopeDependencySelector("test");
        assertFalse(root.selectDependency(dep("g:a:1", "test")));
        DependencySelector child = root.deriveChildSelector(ctx(dep("g:parent:1", "compile")));
        assertFalse(child.selectDependency(dep("g:a:1", "test")));
    }

    // Depends-On: atomic::ExclusionTest::anEmptyGroupIdInAnExclusionMatchesAnyGroup
    // MUTATED: F3_exclusion_wildcard
    @Test
    void aDerivedExclusionSelectorAppliesAnEmptyWildcardFromANodeExclusion() {
        ExclusionDependencySelector base = new ExclusionDependencySelector();
        DependencySelector child = base.deriveChildSelector(
                ctx(depExcl("g:carrier:1", "compile", new Exclusion("", "lib", "*", "*"))));
        assertFalse(child.selectDependency(dep("com.x:lib:1", "compile")));
    }

    // Depends-On: atomic::ScopeTest::aFreshScopeSelectorAppliesItsIncludeFilterToADirectDependency
    @Test
    void aCompositeRejectsADependencyEveryMemberRejectsUnderScope() {
        DependencySelector s = new AndDependencySelector(
                new ScopeDependencySelector("test"), new StaticDependencySelector(false));
        assertFalse(s.selectDependency(dep("g:a:1", "test")));
    }

    // Depends-On: atomic::AndOrTest::aCompositeSelectsWhenEveryMemberSelects
    @Test
    void aCompositeOfTwoKeepingStaticsKeeps() {
        DependencySelector s = new AndDependencySelector(
                new StaticDependencySelector(true), new StaticDependencySelector(true));
        assertTrue(s.selectDependency(dep("g:a:1", "compile")));
    }

    // Depends-On: atomic::AndOrTest::aCompositeRejectsWhenEveryMemberRejects
    @Test
    void aCompositeOfTwoRejectingStaticsRejects() {
        DependencySelector s = new AndDependencySelector(
                new StaticDependencySelector(false), new StaticDependencySelector(false));
        assertFalse(s.selectDependency(dep("g:a:1", "compile")));
    }

    // Depends-On: atomic::AndTraverserTest::aCompositeTraversesWhenEveryMemberTraverses
    @Test
    void aTraverserCompositeTraversesWhenBothMembersTraverse() {
        DependencyTraverser t = new AndDependencyTraverser(
                new StaticDependencyTraverser(true), new StaticDependencyTraverser(true));
        assertTrue(t.traverseDependency(dep("g:a:1", "compile")));
    }

    // Depends-On: atomic::AndTraverserTest::aCompositeSkipsWhenAnyMemberSkips
    @Test
    void aTraverserCompositeSkipsWhenOneMemberSkips() {
        DependencyTraverser t = new AndDependencyTraverser(
                new StaticDependencyTraverser(true), new StaticDependencyTraverser(false));
        assertFalse(t.traverseDependency(dep("g:a:1", "compile")));
    }

    // Depends-On: atomic::OptionalTest::aNonOptionalDependencyIsRetainedAtDepthTwo
    @Test
    void aCompositeKeepsANonOptionalDependencyThroughBothMembers() {
        DependencySelector s = new AndDependencySelector(
                new OptionalDependencySelector(), new StaticDependencySelector(true));
        assertTrue(s.selectDependency(dep("g:a:1", "compile", false)));
    }

    // Depends-On: atomic::ExclusionTest::anExclusionThatMatchesNoCoordinateKeepsTheDependency
    @Test
    void aCompositeKeepsADependencyNoMemberPrunes() {
        DependencySelector s = new AndDependencySelector(excludes("com.x", "other"), new StaticDependencySelector(true));
        assertTrue(s.selectDependency(dep("com.x:lib:1", "compile")));
    }
}
