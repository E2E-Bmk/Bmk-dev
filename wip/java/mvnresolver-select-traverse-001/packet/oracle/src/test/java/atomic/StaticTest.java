package atomic;

import static fixtures.Deps.dep;
import static fixtures.Deps.emptyCtx;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.eclipse.aether.collection.DependencySelector;
import org.eclipse.aether.collection.DependencyTraverser;
import org.junit.jupiter.api.Test;
import org.siftway.selector.StaticDependencySelector;
import org.siftway.traverser.StaticDependencyTraverser;

/** Native single-owner checks for the constant selector and traverser. */
class StaticTest {

    @Test
    void staticTrueSelectorSelectsAnyDependency() {
        assertTrue(new StaticDependencySelector(true).selectDependency(dep("g:a:1", "compile", true)));
    }

    @Test
    void staticFalseSelectorRejectsAnyDependency() {
        assertFalse(new StaticDependencySelector(false).selectDependency(dep("g:a:1", "compile")));
    }

    @Test
    void staticTrueTraverserTraversesAnyDependency() {
        assertTrue(new StaticDependencyTraverser(true).traverseDependency(dep("g:a:1", "compile")));
    }

    @Test
    void staticFalseTraverserSkipsAnyDependency() {
        assertFalse(new StaticDependencyTraverser(false).traverseDependency(dep("g:a:1", "compile")));
    }

    @Test
    void staticSelectorDerivesAnInstanceEqualToItself() {
        DependencySelector s = new StaticDependencySelector(true);
        assertEquals(s, s.deriveChildSelector(emptyCtx()));
    }

    @Test
    void staticTraverserDerivesAnInstanceEqualToItself() {
        DependencyTraverser t = new StaticDependencyTraverser(false);
        assertEquals(t, t.deriveChildTraverser(emptyCtx()));
    }

    @Test
    void staticSelectorsWithTheSameFlagAreEqual() {
        assertEquals(new StaticDependencySelector(true), new StaticDependencySelector(true));
    }
}
