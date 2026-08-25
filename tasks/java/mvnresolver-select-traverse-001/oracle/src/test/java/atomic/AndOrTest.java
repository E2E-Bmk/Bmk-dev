package atomic;

import static fixtures.Deps.dep;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.eclipse.aether.collection.DependencySelector;
import org.junit.jupiter.api.Test;
import org.siftway.selector.AndDependencySelector;
import org.siftway.selector.StaticDependencySelector;

/** Single-owner checks for AndDependencySelector: how a composite combines its members' answers. */
class AndOrTest {

    // MUTATED: F5_and_or
    @Test
    void aCompositeSelectsWhenOnlyItsFirstMemberSelects() {
        DependencySelector s = new AndDependencySelector(
                new StaticDependencySelector(true), new StaticDependencySelector(false));
        assertTrue(s.selectDependency(dep("g:a:1", "compile")));
    }

    // MUTATED: F5_and_or
    @Test
    void aCompositeSelectsWhenOnlyItsLastOfThreeMembersSelects() {
        DependencySelector s = new AndDependencySelector(
                new StaticDependencySelector(false),
                new StaticDependencySelector(false),
                new StaticDependencySelector(true));
        assertTrue(s.selectDependency(dep("g:a:1", "compile")));
    }

    @Test
    void aCompositeSelectsWhenEveryMemberSelects() {
        DependencySelector s = new AndDependencySelector(
                new StaticDependencySelector(true), new StaticDependencySelector(true));
        assertTrue(s.selectDependency(dep("g:a:1", "compile")));
    }

    @Test
    void aCompositeRejectsWhenEveryMemberRejects() {
        DependencySelector s = new AndDependencySelector(
                new StaticDependencySelector(false), new StaticDependencySelector(false));
        assertFalse(s.selectDependency(dep("g:a:1", "compile")));
    }

    @Test
    void newInstanceOfTwoEqualSelectorsReturnsASingleSelector() {
        DependencySelector s = AndDependencySelector.newInstance(
                new StaticDependencySelector(true), new StaticDependencySelector(true));
        assertEquals(new StaticDependencySelector(true), s);
    }
}
