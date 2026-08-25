package atomic;

import static fixtures.Graphs.artifactIdFilter;
import static fixtures.Graphs.chain;
import static fixtures.Graphs.children;
import static fixtures.Graphs.dep;
import static fixtures.Graphs.diamond;
import static fixtures.Graphs.root;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;

import org.eclipse.aether.graph.DependencyFilter;
import org.eclipse.aether.graph.DependencyNode;
import org.junit.jupiter.api.Test;
import org.treeway.visitor.CloningDependencyVisitor;
import org.treeway.visitor.PathRecordingDependencyVisitor;
import org.treeway.visitor.PreorderNodeListGenerator;

/** Single-owner checks for path recording and cloning. */
class PathAndCloneTest {

    private static DependencyFilter matchAny(final String... ids) {
        return (node, parents) -> {
            if (node.getDependency() == null) {
                return false;
            }
            String a = node.getDependency().getArtifact().getArtifactId();
            for (String id : ids) {
                if (id.equals(a)) {
                    return true;
                }
            }
            return false;
        };
    }

    // MUTATED: F3_pathrec_children
    @Test
    void singleArgRecorderDescendsPastAMatchAndRecordsBoth() {
        PathRecordingDependencyVisitor v = new PathRecordingDependencyVisitor(matchAny("a", "b"));
        chain().accept(v);
        assertEquals(2, v.getPaths().size());
    }

    // MUTATED: F3_pathrec_children
    @Test
    void singleArgRecorderRecordsADeeperPathBeneathAMatch() {
        PathRecordingDependencyVisitor v = new PathRecordingDependencyVisitor(matchAny("a", "c"));
        chain().accept(v);
        assertEquals(2, v.getPaths().size());
    }

    // MUTATED: F4_pathrec_nullfilter
    @Test
    void aNullFilterRecordsNoPaths() {
        PathRecordingDependencyVisitor v = new PathRecordingDependencyVisitor((DependencyFilter) null);
        chain().accept(v);
        assertTrue(v.getPaths().isEmpty());
    }

    // MUTATED: F4_pathrec_nullfilter
    @Test
    void aNullFilterWithExplicitModeAlsoRecordsNoPaths() {
        PathRecordingDependencyVisitor v = new PathRecordingDependencyVisitor((DependencyFilter) null, false);
        diamond().accept(v);
        assertTrue(v.getPaths().isEmpty());
    }

    @Test
    void aFilterMatchingOneNodeRecordsOnePath() {
        PathRecordingDependencyVisitor v = new PathRecordingDependencyVisitor(artifactIdFilter("c"));
        chain().accept(v);
        assertEquals(1, v.getPaths().size());
    }

    @Test
    void aRecordedPathTerminatesAtTheMatchedNode() {
        PathRecordingDependencyVisitor v = new PathRecordingDependencyVisitor(artifactIdFilter("c"));
        chain().accept(v);
        List<DependencyNode> path = v.getPaths().get(0);
        assertEquals("c", path.get(path.size() - 1).getDependency().getArtifact().getArtifactId());
    }

    @Test
    void aFilterMatchingNothingRecordsNoPaths() {
        PathRecordingDependencyVisitor v = new PathRecordingDependencyVisitor(artifactIdFilter("absent"));
        chain().accept(v);
        assertTrue(v.getPaths().isEmpty());
    }

    @Test
    void getFilterReturnsTheSuppliedFilter() {
        DependencyFilter f = artifactIdFilter("c");
        assertEquals(f, new PathRecordingDependencyVisitor(f).getFilter());
    }

    @Test
    void cloneRootIsNonNullAfterVisitingAGraph() {
        CloningDependencyVisitor v = new CloningDependencyVisitor();
        chain().accept(v);
        assertNotNull(v.getRootNode());
    }

    @Test
    void cloneRootIsNullBeforeAnyVisit() {
        assertNull(new CloningDependencyVisitor().getRootNode());
    }

    @Test
    void cloneReproducesThePreorderNodeCount() {
        DependencyNode g = chain();
        PreorderNodeListGenerator before = new PreorderNodeListGenerator();
        g.accept(before);
        CloningDependencyVisitor c = new CloningDependencyVisitor();
        g.accept(c);
        PreorderNodeListGenerator after = new PreorderNodeListGenerator();
        c.getRootNode().accept(after);
        assertEquals(before.getNodes().size(), after.getNodes().size());
    }

    @Test
    void cloneOfADiamondSharesTheSharedNode() {
        DependencyNode g = diamond();
        CloningDependencyVisitor c = new CloningDependencyVisitor();
        g.accept(c);
        DependencyNode clonedRoot = c.getRootNode();
        DependencyNode a = clonedRoot.getChildren().get(0);
        DependencyNode b = clonedRoot.getChildren().get(1);
        assertTrue(a.getChildren().get(0) == b.getChildren().get(0));
    }

    @Test
    void cloneIsADistinctObjectFromTheOriginalRoot() {
        DependencyNode g = children(root(), dep("g:a:1"));
        CloningDependencyVisitor c = new CloningDependencyVisitor();
        g.accept(c);
        assertTrue(c.getRootNode() != g);
    }
}
