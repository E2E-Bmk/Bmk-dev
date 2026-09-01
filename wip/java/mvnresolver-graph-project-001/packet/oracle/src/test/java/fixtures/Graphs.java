package fixtures;

import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import org.eclipse.aether.artifact.Artifact;
import org.eclipse.aether.artifact.DefaultArtifact;
import org.eclipse.aether.graph.DefaultDependencyNode;
import org.eclipse.aether.graph.Dependency;
import org.eclipse.aether.graph.DependencyFilter;
import org.eclipse.aether.graph.DependencyNode;

/** Fixtures for the treeway oracle: build dependency graphs and filters, read projections. */
public final class Graphs {

    private Graphs() {}

    public static Artifact resolved(String coords) {
        String[] p = coords.split(":");
        return new DefaultArtifact(coords).setPath(Paths.get("/repo/" + p[1] + "-" + p[p.length - 1] + ".jar"));
    }

    public static Artifact unresolved(String coords) {
        return new DefaultArtifact(coords);
    }

    /** A dependency node whose artifact is resolved (has a path). */
    public static DefaultDependencyNode dep(String coords) {
        return new DefaultDependencyNode(new Dependency(resolved(coords), "compile"));
    }

    /** A dependency node whose artifact is unresolved (no path). */
    public static DefaultDependencyNode unresolvedDep(String coords) {
        return new DefaultDependencyNode(new Dependency(unresolved(coords), "compile"));
    }

    /** A root node that carries no dependency (the project itself). */
    public static DefaultDependencyNode root() {
        return new DefaultDependencyNode(new DefaultArtifact("root:root:1"));
    }

    public static DefaultDependencyNode children(DefaultDependencyNode node, DependencyNode... kids) {
        node.setChildren(new ArrayList<>(Arrays.asList(kids)));
        return node;
    }

    /** root -> a -> b -> c, all resolved compile dependencies. */
    public static DependencyNode chain() {
        DefaultDependencyNode c = dep("g:c:1");
        DefaultDependencyNode b = children(dep("g:b:1"), c);
        DefaultDependencyNode a = children(dep("g:a:1"), b);
        return children(root(), a);
    }

    /** root -> {a, b}; a -> shared; b -> shared (the same node object reachable twice). */
    public static DependencyNode diamond() {
        DefaultDependencyNode shared = dep("g:shared:1");
        DefaultDependencyNode a = children(dep("g:a:1"), shared);
        DefaultDependencyNode b = children(dep("g:b:1"), shared);
        return children(root(), a, b);
    }

    /** root -> {resolved r, unresolved u}. */
    public static DependencyNode mixed() {
        return children(root(), dep("g:r:1"), unresolvedDep("g:u:1"));
    }

    /** A filter matching a single artifactId at the terminal node. */
    public static DependencyFilter artifactIdFilter(final String artifactId) {
        return new DependencyFilter() {
            public boolean accept(DependencyNode node, List<DependencyNode> parents) {
                return node.getDependency() != null
                        && artifactId.equals(node.getDependency().getArtifact().getArtifactId());
            }
        };
    }
}
