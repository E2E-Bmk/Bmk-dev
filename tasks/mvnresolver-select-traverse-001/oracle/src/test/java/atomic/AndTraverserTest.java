package atomic;

import static fixtures.Deps.dep;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.eclipse.aether.collection.DependencyTraverser;
import org.junit.jupiter.api.Test;
import org.siftway.traverser.AndDependencyTraverser;
import org.siftway.traverser.StaticDependencyTraverser;

/** Single-owner checks for AndDependencyTraverser: the composite traverses only if all members do. */
class AndTraverserTest {

    @Test
    void aCompositeTraversesWhenEveryMemberTraverses() {
        DependencyTraverser t = new AndDependencyTraverser(
                new StaticDependencyTraverser(true), new StaticDependencyTraverser(true));
        assertTrue(t.traverseDependency(dep("g:a:1", "compile")));
    }

    @Test
    void aCompositeSkipsWhenAnyMemberSkips() {
        DependencyTraverser t = new AndDependencyTraverser(
                new StaticDependencyTraverser(true), new StaticDependencyTraverser(false));
        assertFalse(t.traverseDependency(dep("g:a:1", "compile")));
    }

    @Test
    void anEmptyCompositeTraverserTraversesEveryDependency() {
        assertTrue(new AndDependencyTraverser().traverseDependency(dep("g:a:1", "compile")));
    }

    @Test
    void newInstanceOfTwoEqualTraversersReturnsASingleTraverser() {
        DependencyTraverser t = AndDependencyTraverser.newInstance(
                new StaticDependencyTraverser(true), new StaticDependencyTraverser(true));
        assertEquals(new StaticDependencyTraverser(true), t);
    }
}
