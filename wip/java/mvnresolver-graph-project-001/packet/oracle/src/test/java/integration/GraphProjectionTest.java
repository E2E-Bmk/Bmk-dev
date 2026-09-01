package integration;

import static fixtures.Graphs.artifactIdFilter;
import static fixtures.Graphs.chain;
import static fixtures.Graphs.diamond;
import static fixtures.Graphs.mixed;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.File;

import org.eclipse.aether.graph.DependencyNode;
import org.junit.jupiter.api.Test;
import org.treeway.visitor.CloningDependencyVisitor;
import org.treeway.visitor.FilteringDependencyVisitor;
import org.treeway.visitor.PathRecordingDependencyVisitor;
import org.treeway.visitor.PostorderNodeListGenerator;
import org.treeway.visitor.PreorderNodeListGenerator;

/** Cross-owner checks: several projections over the same graph. */
class GraphProjectionTest {

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

    // Depends-On: atomic::ProjectionTest::classPathDoesNotUseThePathSeparator
    // MUTATED: F2_classpath_sep
    @Test
    void classPathAndFileListAgreeAndUseTheFileSeparator() {
        PreorderNodeListGenerator g = pre(chain());
        assertEquals(3, g.getFiles().size());
        assertFalse(g.getClassPath().contains(File.pathSeparator));
    }

    // Depends-On: atomic::ProjectionTest::getArtifactsTrueReturnsOnlyResolvedEntries
    // MUTATED: F1_artifacts_unresolved
    @Test
    void preorderKeepsBothChildrenButArtifactsTrueDropsTheUnresolved() {
        PreorderNodeListGenerator g = pre(mixed());
        assertEquals(2, g.getNodes().size());
        assertEquals(1, g.getArtifacts(true).size());
    }

    // Depends-On: atomic::ProjectionTest::preorderListsASharedNodeOncePerPath
    // MUTATED: F5_preorder_revisit
    @Test
    void preorderCountsASharedNodeTwiceWhilePostorderCountsItOnce() {
        assertEquals(4, pre(diamond()).getNodes().size());
        assertEquals(3, post(diamond()).getNodes().size());
    }

    // Depends-On: atomic::PathAndCloneTest::singleArgRecorderDescendsPastAMatchAndRecordsBoth
    // MUTATED: F3_pathrec_children
    @Test
    void aSingleArgRecorderOnAChainRecordsBothTheMatchAndItsDescendant() {
        PathRecordingDependencyVisitor v = new PathRecordingDependencyVisitor(
                (node, parents) -> node.getDependency() != null
                        && ("a".equals(node.getDependency().getArtifact().getArtifactId())
                            || "c".equals(node.getDependency().getArtifact().getArtifactId())));
        chain().accept(v);
        assertEquals(2, v.getPaths().size());
    }

    // Depends-On: atomic::PathAndCloneTest::aNullFilterRecordsNoPaths
    // MUTATED: F4_pathrec_nullfilter
    @Test
    void aNullFilterRecorderStaysEmptyEvenAsPreorderSeesEveryNode() {
        PathRecordingDependencyVisitor v = new PathRecordingDependencyVisitor(null);
        DependencyNode g = chain();
        g.accept(v);
        assertTrue(v.getPaths().isEmpty());
        assertEquals(3, pre(chain()).getNodes().size());
    }

    // Depends-On: atomic::ProjectionTest::preorderChainHasThreeNodes
    @Test
    void preorderAndPostorderCoverTheSameNodeSetForAChain() {
        assertEquals(pre(chain()).getNodes().size(), post(chain()).getNodes().size());
    }

    // Depends-On: atomic::ProjectionTest::preorderVisitsParentBeforeChild
    @Test
    void preorderStartsAtTheShallowestNode() {
        assertEquals("a", pre(chain()).getNodes().get(0).getDependency().getArtifact().getArtifactId());
    }

    // Depends-On: atomic::ProjectionTest::postorderVisitsChildBeforeParent
    @Test
    void postorderStartsAtTheDeepestNode() {
        assertEquals("c", post(chain()).getNodes().get(0).getDependency().getArtifact().getArtifactId());
    }

    // Depends-On: atomic::ProjectionTest::filesListForAResolvedChainHasThreeEntries
    @Test
    void classPathListsAsManyFilesAsTheFileList() {
        PreorderNodeListGenerator g = pre(chain());
        int files = g.getFiles().size();
        String cp = g.getClassPath();
        long occurrences = (cp.length() - cp.replace(".jar", "").length()) / ".jar".length();
        assertEquals(files, occurrences);
    }

    // Depends-On: atomic::PathAndCloneTest::cloneReproducesThePreorderNodeCount
    @Test
    void aCloneReproducesThePreorderProjectionOfAChain() {
        DependencyNode g = chain();
        int before = pre(g).getNodes().size();
        CloningDependencyVisitor c = new CloningDependencyVisitor();
        g.accept(c);
        assertEquals(before, pre(c.getRootNode()).getNodes().size());
    }

    // Depends-On: atomic::PathAndCloneTest::cloneReproducesThePreorderNodeCount
    @Test
    void aCloneOfADiamondReproducesThePreorderCount() {
        DependencyNode g = diamond();
        int before = pre(g).getNodes().size();
        CloningDependencyVisitor c = new CloningDependencyVisitor();
        g.accept(c);
        assertEquals(before, pre(c.getRootNode()).getNodes().size());
    }

    // Depends-On: atomic::ProjectionTest::postorderListsASharedNodeOnlyOnce
    @Test
    void aCloneOfADiamondReproducesThePostorderCount() {
        DependencyNode g = diamond();
        int before = post(g).getNodes().size();
        CloningDependencyVisitor c = new CloningDependencyVisitor();
        g.accept(c);
        assertEquals(before, post(c.getRootNode()).getNodes().size());
    }

    // Depends-On: atomic::PathAndCloneTest::aFilterMatchingOneNodeRecordsOnePath
    @Test
    void aRecordedPathTerminatesAtANodeThatAppearsInThePreorderList() {
        PathRecordingDependencyVisitor v = new PathRecordingDependencyVisitor(artifactIdFilter("c"));
        DependencyNode g = chain();
        g.accept(v);
        DependencyNode terminal = v.getPaths().get(0).get(v.getPaths().get(0).size() - 1);
        assertTrue(pre(chain()).getNodes().stream()
                .anyMatch(n -> n.getDependency().getArtifact().getArtifactId()
                        .equals(terminal.getDependency().getArtifact().getArtifactId())));
    }

    // Depends-On: atomic::ProjectionTest::filesListCoversResolvedNodesOnly
    @Test
    void aFilteringVisitorForwardsOnlyAcceptedNodesToAPreorderGenerator() {
        PreorderNodeListGenerator inner = new PreorderNodeListGenerator();
        FilteringDependencyVisitor f = new FilteringDependencyVisitor(inner, artifactIdFilter("b"));
        chain().accept(f);
        assertEquals(1, inner.getNodes().size());
    }

    // Depends-On: atomic::ProjectionTest::filesListCoversResolvedNodesOnly
    @Test
    void aFilteringVisitorWithAMatchAllForwardsEveryDependencyNode() {
        PreorderNodeListGenerator inner = new PreorderNodeListGenerator();
        FilteringDependencyVisitor f = new FilteringDependencyVisitor(inner, (n, p) -> true);
        chain().accept(f);
        assertEquals(3, inner.getNodes().size());
    }

    // Depends-On: atomic::ProjectionTest::getArtifactsTrueReturnsOnlyResolvedEntries
    // MUTATED: F1_artifacts_unresolved
    @Test
    void artifactsTrueIsASublistOfArtifactsFalseOnAMixedGraph() {
        PreorderNodeListGenerator g = pre(mixed());
        assertTrue(g.getArtifacts(false).containsAll(g.getArtifacts(true)));
    }

    // Depends-On: atomic::ProjectionTest::preorderChainHasThreeNodes
    @Test
    void everyPreorderNodeOfAChainCarriesADependency() {
        assertTrue(pre(chain()).getNodes().stream().allMatch(n -> n.getDependency() != null));
    }

    // Depends-On: atomic::ProjectionTest::classPathContainsEachResolvedFileName
    @Test
    void theClassPathOfAChainListsEveryResolvedFile() {
        String cp = pre(chain()).getClassPath();
        assertTrue(cp.contains("a-1.jar") && cp.contains("b-1.jar") && cp.contains("c-1.jar"));
    }

    // Depends-On: atomic::PathAndCloneTest::aFilterMatchingNothingRecordsNoPaths
    @Test
    void aFilterMatchingNoNodeLeavesPathsEmptyWhilePreorderIsNonEmpty() {
        PathRecordingDependencyVisitor v = new PathRecordingDependencyVisitor(artifactIdFilter("absent"));
        chain().accept(v);
        assertTrue(v.getPaths().isEmpty());
        assertFalse(pre(chain()).getNodes().isEmpty());
    }

    // Depends-On: atomic::PathAndCloneTest::cloneOfADiamondSharesTheSharedNode
    @Test
    void aClonedDiamondStillSharesItsSharedNode() {
        DependencyNode g = diamond();
        CloningDependencyVisitor c = new CloningDependencyVisitor();
        g.accept(c);
        DependencyNode r = c.getRootNode();
        assertTrue(r.getChildren().get(0).getChildren().get(0) == r.getChildren().get(1).getChildren().get(0));
    }

    // Depends-On: atomic::ProjectionTest::filesListForAResolvedChainHasThreeEntries
    @Test
    void filesAndArtifactsTrueHaveTheSameSizeOnAChain() {
        PreorderNodeListGenerator g = pre(chain());
        assertEquals(g.getFiles().size(), g.getArtifacts(true).size());
    }

    // Depends-On: atomic::ProjectionTest::mixedGraphNodesIncludeBothChildren
    @Test
    void postorderOfAMixedGraphStillIncludesBothChildren() {
        assertEquals(2, post(mixed()).getNodes().size());
    }

    // Depends-On: atomic::ProjectionTest::preorderChainHasThreeNodes
    // MUTATED: F2_classpath_sep
    @Test
    void aChainClassPathContainsNoPathSeparatorAcrossThreeEntries() {
        assertFalse(pre(chain()).getClassPath().contains(File.pathSeparator));
    }

    // Depends-On: atomic::ProjectionTest::artifactsTrueOnAllResolvedChainReturnsThree
    @Test
    void aFullyResolvedChainHasEqualArtifactCountsForBothFlags() {
        PreorderNodeListGenerator g = pre(chain());
        assertEquals(g.getArtifacts(true).size(), g.getArtifacts(false).size());
    }

    // Depends-On: atomic::PathAndCloneTest::aRecordedPathTerminatesAtTheMatchedNode
    @Test
    void aDeepMatchRecordsAPathThatStartsAtTheRootChild() {
        PathRecordingDependencyVisitor v = new PathRecordingDependencyVisitor(artifactIdFilter("c"));
        chain().accept(v);
        java.util.List<DependencyNode> path = v.getPaths().get(0);
        assertEquals("a", path.get(1).getDependency().getArtifact().getArtifactId());
    }

    // Depends-On: atomic::ProjectionTest::postorderChainHasThreeNodes
    @Test
    void preorderAndPostorderAgreeOnArtifactCountForAChain() {
        assertEquals(pre(chain()).getArtifacts(false).size(), post(chain()).getArtifacts(false).size());
    }
}
