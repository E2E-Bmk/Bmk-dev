# Treeway Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

Treeway is a Java library that reads a resolved dependency graph and produces ordered projections of it. Given a tree of dependency nodes, it walks the graph in preorder, postorder, or level order, and exposes the visited nodes as node lists, artifact lists, file lists, and a joined class-path string; it records the root-to-node paths that match a filter; it produces a deep clone of the graph; and it wraps another visitor to filter the nodes that reach it. Every projection is a pure read over an existing graph — the library never resolves, downloads, or mutates artifacts.

The published artifact has the Maven coordinates `org.treeway:treeway-core:1.0.0` and all of its own packages live under `org.treeway`. It builds on the resolver's published model types, which remain under `org.eclipse.aether` and are provided as an ordinary compile dependency rather than redefined here.

## Non-Goals

- This specification does not require resolving artifacts, downloading files, or touching the network; every projection is read from an in-memory graph.
- This specification does not define how the dependency graph is constructed; a graph of `org.eclipse.aether.graph.DependencyNode` is taken as input.
- This specification does not require a command-line entry point; the library is consumed programmatically.
- This specification does not define persistence, caching, or concurrency of a projection; one visitor instance reads one graph per walk.
- This specification does not require compatibility with the ordering, separators, or filtering defaults of any similarly-named upstream resolver.

## Representative Workflows

A graph is walked by accepting a visitor at its root; the visitor then exposes its projection:

```java
import org.treeway.visitor.PreorderNodeListGenerator;
import org.eclipse.aether.graph.DependencyNode;

DependencyNode root = /* a resolved graph */;
PreorderNodeListGenerator gen = new PreorderNodeListGenerator();
root.accept(gen);
String classpath = gen.getClassPath();
```

The consumer-style visitors instead forward each node to a supplied `java.util.function.Consumer` in the chosen order.

## Reading the Graph as Lists

`NodeListGenerator` is a `java.util.function.Consumer<DependencyNode>` that collects the nodes handed to it and derives four projections over the nodes that carry a dependency: the node list, the dependency list, the artifact list, and the file list, plus a joined class-path string. `PreorderNodeListGenerator` and `PostorderNodeListGenerator` are `DependencyVisitor`s that walk a graph and build the same projections.

- The artifact and dependency projections take an `includeUnresolved` flag. **When `includeUnresolved` is `true`, only resolved entries — those whose artifact has a non-null path — are returned; when it is `false`, every entry is returned regardless of resolution.**
- The file projection returns the non-null files of the resolved nodes, in visitation order.
- **The class-path string joins the absolute paths of the resolved nodes with the platform file separator (`java.io.File.separator`)**, in visitation order.
- `PreorderNodeListGenerator` records each node the first time it is entered, before its children. **It does not de-duplicate: a node reachable along more than one path is recorded once for each path that reaches it.** `PostorderNodeListGenerator` records each node after its children and, in contrast, records a shared node only once.

## Walking and Recording Paths

`PathRecordingDependencyVisitor` records the root-to-node paths whose terminal node is accepted by a supplied `org.eclipse.aether.graph.DependencyFilter`. It has two constructors: one taking a filter and a boolean, and one taking only a filter.

- **The single-argument constructor sets the "exclude children of matches" mode to `false`: once a node matches, the walk continues into that node's children and may record longer matching paths beneath it.**
- **A `null` filter records no paths at all**; only an explicit filter that accepts a node causes its path to be recorded.
- A path is recorded as the list of nodes from the root down to the accepted node, root first. The walk still stops descending into a node that already appears on the current path, to break cycles.

## Cloning and Filtering

`CloningDependencyVisitor` produces a deep copy of the graph: each distinct node is cloned once, a node reached again along another path reuses its first clone rather than being copied twice, and the clone's children mirror the original's edges. `getRootNode` returns the clone of the graph root.

`FilteringDependencyVisitor` wraps another `DependencyVisitor` and a filter, forwarding only the nodes the filter accepts to the wrapped visitor while still descending the whole graph. `TreeDependencyVisitor` wraps another visitor and drives a depth-first walk through it. The consumer visitors `PreorderDependencyNodeConsumerVisitor`, `PostorderDependencyNodeConsumerVisitor`, and `LevelOrderDependencyNodeConsumerVisitor` each carry a public `NAME` constant and forward every node (optionally filtered) to a supplied consumer in their namesake order.

## State Model

A generator or visitor accumulates state during a single walk:

1. `NodeListGenerator` holds the ordered list of accepted nodes; its projections are derived on demand.
2. `PreorderNodeListGenerator` and `PostorderNodeListGenerator` hold the ordered node list and a set of already-visited nodes (identity-based); preorder ignores that set for recording while postorder honours it.
3. `PathRecordingDependencyVisitor` holds the filter, the exclude-children flag, the stack of parent nodes on the current path, and the accumulated list of recorded paths.
4. `CloningDependencyVisitor` holds the map from original node to its single clone, the stack of clone parents, and the cloned root.

No projection mutates the input graph; a projection read after a walk reflects exactly the nodes that walk visited.

## Error Semantics

- `NodeListGenerator.accept`, every `visitEnter`, and every `visitLeave` must reject a `null` node by raising `java.lang.NullPointerException`.
- A projection read before any walk must return an empty list (never `null`), and an empty class-path string.
- `getRootNode` on a `CloningDependencyVisitor` that has not visited any graph must return `null`.
- A `PathRecordingDependencyVisitor` constructed with a `null` filter must complete a walk without error and expose an empty path list.

## Cross-View Invariants

1. The file list and the class-path string cover the same resolved nodes in the same visitation order; the class-path is those files' absolute paths joined by the file separator.
2. `getArtifacts(false)` lists an artifact for every node that carries a dependency, while `getArtifacts(true)` lists only those whose artifact has a non-null path; the second list is therefore a sublist of the first.
3. Every node in a preorder or postorder projection carries a dependency, and every recorded path from `PathRecordingDependencyVisitor` terminates at a node that the supplied filter accepts.
4. A clone produced by `CloningDependencyVisitor` reproduces the preorder node sequence of the original graph, node for node, and a node shared in the original is shared in the clone.
5. A node reachable by two distinct paths contributes two entries to a preorder projection but a single clone in `CloningDependencyVisitor` and a single entry in a postorder projection.
6. `FilteringDependencyVisitor` forwards to its wrapped visitor exactly the nodes its filter accepts, so the wrapped projection over a filtered walk is a sublist of the same projection over the unfiltered walk.

## Public Interface

### Import Surface

The public package is:

| Package | Contents |
|---|---|
| `org.treeway.visitor` | the node-list generators, the consumer-style order visitors, the path recorder, the cloning visitor, and the filtering/tree wrappers |

The resolver model types (`org.eclipse.aether.graph.DependencyNode`, `org.eclipse.aether.graph.Dependency`, `org.eclipse.aether.graph.DependencyVisitor`, `org.eclipse.aether.graph.DependencyFilter`, `org.eclipse.aether.artifact.Artifact`) are consumed from the published resolver API and are not part of this artifact.

### Declared Signatures

The declarations below are exact. Parameter names carry no meaning, but every package, type name, member name, modifier, parameter type, and return type does.

#### `org.treeway.visitor`

```java
public final class NodeListGenerator implements java.util.function.Consumer<org.eclipse.aether.graph.DependencyNode> {
    public NodeListGenerator();
    public void accept(org.eclipse.aether.graph.DependencyNode node);
    public java.util.List<org.eclipse.aether.graph.DependencyNode> getNodes();
    public java.util.List<org.eclipse.aether.graph.DependencyNode> getNodesWithDependencies();
    public java.util.List<org.eclipse.aether.graph.Dependency> getDependencies(boolean includeUnresolved);
    public java.util.List<org.eclipse.aether.artifact.Artifact> getArtifacts(boolean includeUnresolved);
    public java.util.List<java.io.File> getFiles();
    public java.util.List<java.nio.file.Path> getPaths();
    public String getClassPath();
}

public final class PreorderNodeListGenerator implements org.eclipse.aether.graph.DependencyVisitor {
    public PreorderNodeListGenerator();
    public boolean visitEnter(org.eclipse.aether.graph.DependencyNode node);
    public boolean visitLeave(org.eclipse.aether.graph.DependencyNode node);
    public java.util.List<org.eclipse.aether.graph.DependencyNode> getNodes();
    public java.util.List<org.eclipse.aether.graph.Dependency> getDependencies(boolean includeUnresolved);
    public java.util.List<org.eclipse.aether.artifact.Artifact> getArtifacts(boolean includeUnresolved);
    public java.util.List<java.io.File> getFiles();
    public String getClassPath();
}

public final class PostorderNodeListGenerator implements org.eclipse.aether.graph.DependencyVisitor {
    public PostorderNodeListGenerator();
    public boolean visitEnter(org.eclipse.aether.graph.DependencyNode node);
    public boolean visitLeave(org.eclipse.aether.graph.DependencyNode node);
    public java.util.List<org.eclipse.aether.graph.DependencyNode> getNodes();
    public java.util.List<org.eclipse.aether.graph.Dependency> getDependencies(boolean includeUnresolved);
    public java.util.List<org.eclipse.aether.artifact.Artifact> getArtifacts(boolean includeUnresolved);
    public java.util.List<java.io.File> getFiles();
    public String getClassPath();
}

public final class PathRecordingDependencyVisitor implements org.eclipse.aether.graph.DependencyVisitor {
    public PathRecordingDependencyVisitor(org.eclipse.aether.graph.DependencyFilter filter);
    public PathRecordingDependencyVisitor(org.eclipse.aether.graph.DependencyFilter filter, boolean excludeChildrenOfMatches);
    public org.eclipse.aether.graph.DependencyFilter getFilter();
    public java.util.List<java.util.List<org.eclipse.aether.graph.DependencyNode>> getPaths();
    public boolean visitEnter(org.eclipse.aether.graph.DependencyNode node);
    public boolean visitLeave(org.eclipse.aether.graph.DependencyNode node);
}

public class CloningDependencyVisitor implements org.eclipse.aether.graph.DependencyVisitor {
    public CloningDependencyVisitor();
    public final org.eclipse.aether.graph.DependencyNode getRootNode();
    public final boolean visitEnter(org.eclipse.aether.graph.DependencyNode node);
    public final boolean visitLeave(org.eclipse.aether.graph.DependencyNode node);
}

public final class FilteringDependencyVisitor implements org.eclipse.aether.graph.DependencyVisitor {
    public FilteringDependencyVisitor(org.eclipse.aether.graph.DependencyVisitor visitor, org.eclipse.aether.graph.DependencyFilter filter);
    public org.eclipse.aether.graph.DependencyVisitor getVisitor();
    public org.eclipse.aether.graph.DependencyFilter getFilter();
    public boolean visitEnter(org.eclipse.aether.graph.DependencyNode node);
    public boolean visitLeave(org.eclipse.aether.graph.DependencyNode node);
}

public final class TreeDependencyVisitor implements org.eclipse.aether.graph.DependencyVisitor {
    public TreeDependencyVisitor(org.eclipse.aether.graph.DependencyVisitor visitor);
    public boolean visitEnter(org.eclipse.aether.graph.DependencyNode node);
    public boolean visitLeave(org.eclipse.aether.graph.DependencyNode node);
}

public final class PreorderDependencyNodeConsumerVisitor extends org.treeway.visitor.AbstractDependencyNodeConsumerVisitor {
    public static final String NAME;
    public PreorderDependencyNodeConsumerVisitor(java.util.function.Consumer<org.eclipse.aether.graph.DependencyNode> nodeConsumer);
    public PreorderDependencyNodeConsumerVisitor(java.util.function.Consumer<org.eclipse.aether.graph.DependencyNode> nodeConsumer, org.eclipse.aether.graph.DependencyFilter filter);
}

public final class PostorderDependencyNodeConsumerVisitor extends org.treeway.visitor.AbstractDependencyNodeConsumerVisitor {
    public static final String NAME;
    public PostorderDependencyNodeConsumerVisitor(java.util.function.Consumer<org.eclipse.aether.graph.DependencyNode> nodeConsumer);
    public PostorderDependencyNodeConsumerVisitor(java.util.function.Consumer<org.eclipse.aether.graph.DependencyNode> nodeConsumer, org.eclipse.aether.graph.DependencyFilter filter);
}

public final class LevelOrderDependencyNodeConsumerVisitor extends org.treeway.visitor.AbstractDependencyNodeConsumerVisitor {
    public static final String NAME;
    public LevelOrderDependencyNodeConsumerVisitor(java.util.function.Consumer<org.eclipse.aether.graph.DependencyNode> nodeConsumer);
    public LevelOrderDependencyNodeConsumerVisitor(java.util.function.Consumer<org.eclipse.aether.graph.DependencyNode> nodeConsumer, org.eclipse.aether.graph.DependencyFilter filter);
}
```

### Command-Line Interface

Treeway is a programmatic library and exposes no command-line interface; every capability is reached through the package above.

## Appendix A: Environment

The library targets Java 17 or later and is built with Maven. It depends only on the published resolver API artifact (`org.eclipse.aether:maven-resolver-api`) at version 2.0.10, which is provided on the compile classpath. No other runtime dependency, network access, or file-system layout is assumed.

## Appendix B: Assessment Notes

Evaluation exercises the projections at three levels. Single-owner checks confirm one decision at a time: the preorder and postorder order of a small tree; whether `getArtifacts(true)` drops an unresolved entry while `getArtifacts(false)` keeps it; the separator the class-path string uses; whether the single-argument path recorder descends past a match; whether a null filter records anything; and whether a preorder walk re-lists a shared node. Cross-owner checks combine two projections over the same graph — that the file list and class-path agree, that a clone reproduces the preorder sequence, that a shared node yields two preorder entries but one postorder entry and one clone. Whole-graph checks run a walk over a diamond or a deep chain and read several projections against the same result. Assertions pin concrete observable values — list sizes and element identity, the class-path string, recorded path shapes; they never inspect private fields. The orders, separators, defaults, and de-duplication rules stated above are the contract under test — a conforming implementation reproduces them exactly.
