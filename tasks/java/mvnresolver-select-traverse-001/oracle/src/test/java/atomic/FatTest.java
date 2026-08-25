package atomic;

import static fixtures.Deps.dep;
import static fixtures.Deps.emptyCtx;
import static fixtures.Deps.fatDep;
import static fixtures.Deps.plainDep;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.eclipse.aether.artifact.ArtifactProperties;
import org.eclipse.aether.artifact.DefaultArtifact;
import org.eclipse.aether.collection.DependencyTraverser;
import org.eclipse.aether.graph.Dependency;
import org.junit.jupiter.api.Test;
import org.siftway.traverser.FatArtifactTraverser;

/** Single-owner checks for FatArtifactTraverser: descend unless an artifact bundles its dependencies. */
class FatTest {

    // MUTATED: F4_fat_default
    @Test
    void anArtifactWithoutTheFatPropertyIsNotTraversed() {
        assertFalse(new FatArtifactTraverser().traverseDependency(plainDep("g:a:1")));
    }

    // MUTATED: F4_fat_default
    @Test
    void anArtifactDeclaringOnlyAnUnrelatedPropertyIsNotTraversed() {
        java.util.Map<String, String> props = new java.util.HashMap<>();
        props.put(ArtifactProperties.LANGUAGE, "java");
        Dependency d = new Dependency(new DefaultArtifact("g:a:1", props), "compile");
        assertFalse(new FatArtifactTraverser().traverseDependency(d));
    }

    @Test
    void anArtifactExplicitlyMarkedFatIsNotTraversed() {
        assertFalse(new FatArtifactTraverser().traverseDependency(fatDep("g:a:1", "true")));
    }

    @Test
    void anArtifactExplicitlyMarkedNonFatIsTraversed() {
        assertTrue(new FatArtifactTraverser().traverseDependency(fatDep("g:a:1", "false")));
    }

    @Test
    void theFatTraverserDerivesAnInstanceEqualToItself() {
        DependencyTraverser t = new FatArtifactTraverser();
        assertEquals(t, t.deriveChildTraverser(emptyCtx()));
    }
}
