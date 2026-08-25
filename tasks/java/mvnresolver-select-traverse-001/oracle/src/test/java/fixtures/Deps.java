package fixtures;

import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.eclipse.aether.RepositorySystemSession;
import org.eclipse.aether.artifact.Artifact;
import org.eclipse.aether.artifact.ArtifactProperties;
import org.eclipse.aether.artifact.DefaultArtifact;
import org.eclipse.aether.collection.DependencyCollectionContext;
import org.eclipse.aether.collection.DependencySelector;
import org.eclipse.aether.collection.DependencyTraverser;
import org.eclipse.aether.graph.Dependency;
import org.eclipse.aether.graph.Exclusion;

/** Shared fixtures for the siftway oracle: build dependencies, exclusions, contexts, derive chains. */
public final class Deps {

    private Deps() {}

    public static Artifact art(String coords) {
        return new DefaultArtifact(coords);
    }

    /** An artifact carrying the includesDependencies property set to the given value. */
    public static Artifact artFat(String coords, String includesDependencies) {
        Map<String, String> p = new HashMap<>();
        p.put(ArtifactProperties.INCLUDES_DEPENDENCIES, includesDependencies);
        return new DefaultArtifact(coords, p);
    }

    /** An artifact carrying only an unrelated property (no includesDependencies). */
    public static Artifact artLanguage(String coords) {
        Map<String, String> p = new HashMap<>();
        p.put(ArtifactProperties.LANGUAGE, "java");
        return new DefaultArtifact(coords, p);
    }

    public static Dependency dep(String coords, String scope) {
        return new Dependency(art(coords), scope);
    }

    public static Dependency dep(String coords, String scope, boolean optional) {
        return new Dependency(art(coords), scope, optional);
    }

    public static Dependency depExcl(String coords, String scope, Exclusion... exclusions) {
        return new Dependency(art(coords), scope, Boolean.FALSE, Arrays.asList(exclusions));
    }

    /** A compile dependency whose artifact explicitly declares includesDependencies. */
    public static Dependency fatDep(String coords, String includesDependencies) {
        return new Dependency(artFat(coords, includesDependencies), "compile");
    }

    /** A compile dependency whose artifact declares no includesDependencies property at all. */
    public static Dependency plainDep(String coords) {
        return new Dependency(art(coords), "compile");
    }

    public static Exclusion excl(String groupId, String artifactId) {
        return new Exclusion(groupId, artifactId, "*", "*");
    }

    public static Exclusion excl(String groupId, String artifactId, String classifier, String extension) {
        return new Exclusion(groupId, artifactId, classifier, extension);
    }

    /** A minimal collection context: siftway derive methods only read getDependency(). */
    public static DependencyCollectionContext ctx(final Dependency dependency) {
        return new DependencyCollectionContext() {
            public RepositorySystemSession getSession() {
                return null;
            }

            public Artifact getArtifact() {
                return dependency == null ? null : dependency.getArtifact();
            }

            public Dependency getDependency() {
                return dependency;
            }

            public List<Dependency> getManagedDependencies() {
                return Collections.emptyList();
            }
        };
    }

    public static DependencyCollectionContext emptyCtx() {
        return ctx(dep("g:seed:1", "compile"));
    }

    /** Derive a selector n times through empty-dependency contexts. */
    public static DependencySelector deriveN(DependencySelector selector, int n) {
        DependencySelector current = selector;
        for (int i = 0; i < n; i++) {
            current = current.deriveChildSelector(emptyCtx());
        }
        return current;
    }

    /** Derive a traverser n times through empty-dependency contexts. */
    public static DependencyTraverser deriveN(DependencyTraverser traverser, int n) {
        DependencyTraverser current = traverser;
        for (int i = 0; i < n; i++) {
            current = current.deriveChildTraverser(emptyCtx());
        }
        return current;
    }
}
