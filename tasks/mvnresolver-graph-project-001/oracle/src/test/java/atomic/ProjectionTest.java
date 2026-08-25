package atomic;

import static fixtures.Graphs.chain;
import static fixtures.Graphs.children;
import static fixtures.Graphs.dep;
import static fixtures.Graphs.diamond;
import static fixtures.Graphs.mixed;
import static fixtures.Graphs.root;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.File;

import org.eclipse.aether.graph.DependencyNode;
import org.junit.jupiter.api.Test;
import org.treeway.visitor.PostorderNodeListGenerator;
import org.treeway.visitor.PreorderNodeListGenerator;

/** Single-owner checks for the list projections. */
class ProjectionTest {

    private static PreorderNodeListGenerator pre(DependencyNode g) {
        PreorderNodeListGenerator p = new PreorderNodeListGenerator();
        g.accept(p);
        return p;
    }

    private static PostorderNodeListGenerator post(DependencyNode g) {
        PostorderNodeListGenerator p = new PostorderNodeListGenerator();
        g.accept(p);
        return p;
    }

    // MUTATED: F1_artifacts_unresolved
    @Test
    void getArtifactsTrueReturnsOnlyResolvedEntries() {
        assertEquals(1, pre(mixed()).getArtifacts(true).size());
    }

    // MUTATED: F1_artifacts_unresolved
    @Test
    void getArtifactsFalseReturnsEveryEntry() {
        assertEquals(2, pre(mixed()).getArtifacts(false).size());
    }

    // MUTATED: F2_classpath_sep
    @Test
    void classPathDoesNotUseThePathSeparator() {
        assertFalse(pre(chain()).getClassPath().contains(File.pathSeparator));
    }

    // MUTATED: F2_classpath_sep
    @Test
    void classPathJoinsEntriesWithTheFileSeparator() {
        String cp = pre(chain()).getClassPath();
        assertTrue(cp.contains(".jar" + File.separator + "/repo"));
    }

    // MUTATED: F5_preorder_revisit
    @Test
    void preorderListsASharedNodeOncePerPath() {
        assertEquals(4, pre(diamond()).getNodes().size());
    }

    // MUTATED: F5_preorder_revisit
    @Test
    void preorderArtifactCountCountsSharedNodeTwice() {
        assertEquals(4, pre(diamond()).getArtifacts(false).size());
    }

    @Test
    void preorderVisitsParentBeforeChild() {
        assertEquals("a", pre(chain()).getNodes().get(0).getDependency().getArtifact().getArtifactId());
    }

    @Test
    void preorderChainHasThreeNodes() {
        assertEquals(3, pre(chain()).getNodes().size());
    }

    @Test
    void postorderVisitsChildBeforeParent() {
        assertEquals("c", post(chain()).getNodes().get(0).getDependency().getArtifact().getArtifactId());
    }

    @Test
    void postorderChainHasThreeNodes() {
        assertEquals(3, post(chain()).getNodes().size());
    }

    @Test
    void postorderListsASharedNodeOnlyOnce() {
        assertEquals(3, post(diamond()).getNodes().size());
    }

    @Test
    void filesListCoversResolvedNodesOnly() {
        assertEquals(1, pre(mixed()).getFiles().size());
    }

    @Test
    void filesListForAResolvedChainHasThreeEntries() {
        assertEquals(3, pre(chain()).getFiles().size());
    }

    // MUTATED: F1_artifacts_unresolved
    @Test
    void dependenciesTrueReturnsOnlyResolved() {
        assertEquals(1, pre(mixed()).getDependencies(true).size());
    }

    // MUTATED: F1_artifacts_unresolved
    @Test
    void dependenciesFalseReturnsAll() {
        assertEquals(2, pre(mixed()).getDependencies(false).size());
    }

    @Test
    void nodesListExcludesTheDependencylessRoot() {
        assertEquals(3, pre(chain()).getNodes().size());
    }

    @Test
    void emptyGraphYieldsEmptyNodeList() {
        assertTrue(pre(root()).getNodes().isEmpty());
    }

    @Test
    void emptyGraphYieldsEmptyClassPath() {
        assertEquals("", pre(root()).getClassPath());
    }

    @Test
    void classPathContainsEachResolvedFileName() {
        String cp = pre(chain()).getClassPath();
        assertTrue(cp.contains("a-1.jar") && cp.contains("b-1.jar") && cp.contains("c-1.jar"));
    }

    @Test
    void singleResolvedDependencyClassPathHasNoSeparator() {
        DependencyNode g = children(root(), dep("g:only:1"));
        assertFalse(pre(g).getClassPath().contains(File.pathSeparator));
    }

    @Test
    void preorderNodesEachCarryADependency() {
        assertTrue(pre(chain()).getNodes().stream().allMatch(n -> n.getDependency() != null));
    }

    @Test
    void postorderNodesEachCarryADependency() {
        assertTrue(post(chain()).getNodes().stream().allMatch(n -> n.getDependency() != null));
    }

    @Test
    void artifactsTrueOnAResolvedChainMatchesFileCount() {
        assertEquals(pre(chain()).getFiles().size(), pre(chain()).getArtifacts(true).size());
    }

    @Test
    void mixedGraphNodesIncludeBothChildren() {
        assertEquals(2, pre(mixed()).getNodes().size());
    }

    @Test
    void postorderMixedGraphKeepsBothChildren() {
        assertEquals(2, post(mixed()).getNodes().size());
    }

    @Test
    void artifactsTrueOnAllResolvedChainReturnsThree() {
        assertEquals(3, pre(chain()).getArtifacts(true).size());
    }

    @Test
    void artifactsFalseOnAllResolvedChainReturnsThree() {
        assertEquals(3, pre(chain()).getArtifacts(false).size());
    }

    @Test
    void postorderArtifactsFalseOnDiamondCountsSharedOnce() {
        assertEquals(3, post(diamond()).getArtifacts(false).size());
    }

    // MUTATED: F5_preorder_revisit
    @Test
    void classPathForDiamondListsSharedFileTwiceInPreorder() {
        String cp = pre(diamond()).getClassPath();
        int i = cp.indexOf("shared-1.jar");
        assertTrue(i >= 0 && cp.indexOf("shared-1.jar", i + 1) > i);
    }

    @Test
    void nodeListGeneratorConsumerCollectsFedNodes() {
        org.treeway.visitor.NodeListGenerator g = new org.treeway.visitor.NodeListGenerator();
        g.accept(dep("g:x:1"));
        g.accept(dep("g:y:1"));
        assertEquals(2, g.getNodes().size());
    }

    // MUTATED: F2_classpath_sep
    @Test
    void nodeListGeneratorClassPathHasNoPathSeparatorForTwoResolved() {
        org.treeway.visitor.NodeListGenerator g = new org.treeway.visitor.NodeListGenerator();
        g.accept(dep("g:x:1"));
        g.accept(dep("g:y:1"));
        assertFalse(g.getClassPath().contains(File.pathSeparator));
    }

    @Test
    void preorderChainClassPathContainsThreeFileNames() {
        assertEquals(3, pre(chain()).getFiles().size());
    }

    @Test
    void postorderRootlessCountMatchesPreorderForChain() {
        assertEquals(pre(chain()).getNodes().size(), post(chain()).getNodes().size());
    }
}
