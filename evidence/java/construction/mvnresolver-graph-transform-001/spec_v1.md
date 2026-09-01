<!-- INTERNAL
task_id: mvnresolver-graph-transform-001
spec_version: v1
delta: v1 born describing the mutated system (AGENTS rule 6a); seven mutation families registered in ROOT-MAP.json (audit valid).
mutation_families:
  F1_winner_policy: clauses=[GRAPH-WINNER-DEFAULT]. upstream-intuitive: the default version-selection strategy is nearest-wins, Maven's canonical rule. mutated: the default strategy is highest-version-wins.
  F2_scope_derive: clauses=[GRAPH-SCOPE-DERIVE]. upstream-intuitive: the standard Maven scope-derivation table (parent compile + child provided => provided). mutated: one derivation cell inverted (parent compile + child provided => compile).
  F3_optional_prop: clauses=[GRAPH-OPTIONAL-PROP]. upstream-intuitive: an artifact's derived optionality is the logical-AND across surviving paths (optional only if every contributing path is optional). mutated: logical-OR (optional if any contributing path is optional).
  F4_depmgmt_depth: clauses=[GRAPH-DEPMGMT-DEPTH]. upstream-intuitive: classic dependency management applies starting at depth 2 (the root's own direct dependencies are not managed by the root), mimicking Maven 2.x. mutated: management applies starting at depth 1.
  F7_dumper_format: clauses=[GRAPH-DUMPER-FORMAT]. upstream-intuitive: the tree dump marks the last child of a parent with a distinct connector from earlier children. mutated: every child uses the same connector.
source_boundary: maven-resolver 2.0.22 maven-resolver-util carve org.eclipse.aether.util.graph (transformer, manager, visitor); maven.apache.org/resolver docs; api_surface.md.
-->

# Graphway Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

Graphway is a Java library that post-processes a resolved dependency graph. Given a tree of dependency nodes produced by an upstream resolver, it identifies which nodes describe the same artifact, decides which version of each such group survives, derives the effective scope and optionality of every surviving node, applies dependency management, and exposes the transformed graph through several read projections: a flattened class path, a depth-ordered node list, a textual tree, and a set of matching paths. The transformation rewrites the graph in place through the standard graph-transformer contract, and the projections are pure readers over the resulting tree.

The published artifact has the Maven coordinates `org.graphway:graphway-core:1.0.0` and all of its own packages live under `org.graphway`. It builds on the resolver's published model types, which remain under `org.eclipse.aether` and are provided as ordinary compile dependencies rather than redefined here.

## Non-Goals

- This specification does not require resolving artifacts from remote repositories, downloading files, or touching the network; every operation is performed against an in-memory dependency graph.
- This specification does not define the construction of the initial dependency graph; a graph of `org.eclipse.aether.graph.DependencyNode` is taken as input.
- This specification does not require a command-line entry point; the library is consumed programmatically.
- This specification does not define persistence, caching, or concurrency of the transformation; a transformer instance processes one graph per call.
- This specification does not require compatibility with the versioned data keys, configuration property names, or selection strategies of any similarly-named upstream resolver.

## Representative Workflows

The transformers implement `org.eclipse.aether.collection.DependencyGraphTransformer`, whose single method rewrites the graph and returns its (possibly new) root. A typical pipeline marks conflict groups, sorts them, then resolves conflicts:

```java
import org.graphway.transformer.ConflictMarker;
import org.graphway.transformer.ConflictIdSorter;
import org.graphway.transformer.ConflictResolver;
import org.graphway.transformer.NearestVersionSelector;
import org.graphway.transformer.JavaScopeSelector;
import org.graphway.transformer.JavaScopeDeriver;
import org.graphway.transformer.SimpleOptionalitySelector;
import org.eclipse.aether.collection.DependencyGraphTransformationContext;
import org.eclipse.aether.graph.DependencyNode;

DependencyNode root = /* an existing resolved graph */;
DependencyGraphTransformationContext ctx = /* session-backed context */;

new ConflictMarker().transformGraph(root, ctx);
new ConflictIdSorter().transformGraph(root, ctx);
ConflictResolver resolver = new ConflictResolver(
        new NearestVersionSelector(), new JavaScopeSelector(),
        new SimpleOptionalitySelector(), new JavaScopeDeriver());
resolver.transformGraph(root, ctx);
```

After resolution, a projection reads the surviving graph. The preorder generator flattens it into a class path in which each artifact file appears once:

```java
import org.graphway.visitor.PreorderNodeListGenerator;

PreorderNodeListGenerator gen = new PreorderNodeListGenerator();
root.accept(gen);
String classpath = gen.getClassPath();      // File.pathSeparator-joined, first occurrence wins
java.util.List<org.eclipse.aether.artifact.Artifact> artifacts = gen.getArtifacts(false);
```

## Marking and Sorting Conflict Groups

A conflict group is a set of nodes whose dependencies describe the same artifact coordinate up to version. `ConflictMarker` walks the graph and stores, in the transformation context under the key `org.graphway.transformer.TransformationContextKeys.CONFLICT_IDS`, a mapping from each node to a conflict-id object. `ConflictIdSorter` reads that mapping and stores, under `SORTED_CONFLICT_IDS`, the topologically ordered list of conflict ids, plus `CYCLIC_CONFLICT_IDS` for ids that participate in a cycle and `STATS` for timing counters. When a graph contains no dependencies, both transformers must return the same root unchanged and must not create conflict ids.

## Resolving Version, Scope and Optionality

`ConflictResolver` consumes the sorted conflict ids and, for each group, selects one surviving node and prunes the rest. It delegates four independent decisions to pluggable strategies supplied at construction:

- A **version selector** chooses the winner within a group. `NearestVersionSelector` picks the node at the least depth (nearest-wins), breaking ties by declaration order. `ConfigurableVersionSelector` chooses between named strategies; **the default selection strategy is `HIGHEST_SELECTION_STRATEGY`** — when no strategy is configured, the node carrying the highest version in the group wins.
- A **scope selector** assigns each surviving node its effective scope. `JavaScopeSelector` derives the scope from the winning path.
- A **scope deriver** computes a child's scope from its parent's scope. `JavaScopeDeriver` follows the Java scope table with one deviation: **a `provided` dependency of a `compile`-scoped parent is derived as `compile`.**
- An **optionality selector** assigns each surviving node its effective optionality. `SimpleOptionalitySelector` sets a node optional when **any contributing path is optional**; a direct dependency's own optional flag takes precedence.

When conflict resolution runs in verbose mode, each pruned (loser) node retains data keys recording the outcome: `ConflictResolver.NODE_DATA_WINNER` holds the winning node, `NODE_DATA_ORIGINAL_SCOPE` holds the loser's own scope before resolution, and `NODE_DATA_ORIGINAL_OPTIONALITY` holds the loser's own pre-resolution optionality.

## Applying Dependency Management

A dependency manager overrides version, scope, optionality and exclusions of nodes below a managing node. `ClassicDependencyManager` **applies management starting at depth 1** — the direct dependencies of the root are managed by the root's own management section. `TransitiveDependencyManager` continues applying inherited management at every depth. `DefaultDependencyManager` applies management from the root at all depths. `NoopDependencyManager` applies nothing. A manager is immutable; `deriveChildManager` returns the manager that governs the children of a given node.

## Reading the Transformed Graph

`NodeListGenerator` is the read contract shared by the ordered projections. `PreorderNodeListGenerator` visits parents before children; `PostorderNodeListGenerator` visits children first. Both expose the surviving nodes as a node list, an artifact list, a file list, a dependency list, and a joined class-path string. The class path is built in visitation order; each node is visited once, so when the same node is reachable by more than one path only its first visit contributes and its subtree is not revisited.

`PathRecordingDependencyVisitor` records every root-to-node path whose terminal node matches a supplied node filter. `CloningDependencyVisitor` produces a deep copy of the graph. `DependencyGraphDumper` renders the graph as an indented text tree; **every child line, including the last child of a parent, is introduced by the connector `+- `**, and deeper levels are indented by the continuation prefix.

## State Model

The core state is a single `org.eclipse.aether.graph.DependencyNode` graph and the side-channel entries a transformer leaves in the `DependencyGraphTransformationContext`. Its public projections are:

1. The transformed graph structure — which nodes survive, their parent/child edges, and each surviving node's version, scope and optionality.
2. The context keys `CONFLICT_IDS`, `SORTED_CONFLICT_IDS`, `CYCLIC_CONFLICT_IDS` and `STATS`.
3. The verbose loser-node data keys `conflict.winner`, `conflict.originalScope`, `conflict.originalOptionality`.
4. The ordered node/artifact/file/dependency lists and the class-path string from a `NodeListGenerator`.
5. The path set from `PathRecordingDependencyVisitor` and the clone from `CloningDependencyVisitor`.
6. The text tree from `DependencyGraphDumper`.

A transformer must leave the graph and context self-consistent: a projection read after transformation reflects exactly the decisions the resolver made.

## Error Semantics

- If a version conflict cannot be solved under the active constraints, the version selector must raise `org.eclipse.aether.RepositoryException` (specifically an unsolvable-version-conflict exception).
- If `ConflictIdSorter` runs before `ConflictMarker` has populated `CONFLICT_IDS`, the resolver must raise `org.eclipse.aether.RepositoryException` rather than silently producing an empty result.
- A `NodeListGenerator` must return empty projections (never null) when applied to a graph whose root has no children.
- A dependency manager must return `null` from `deriveChildManager` when it would manage nothing further, so callers can stop descending.

## Cross-View Invariants

1. A node present in the transformed graph structure must appear in the preorder node list, and its artifact must appear in the artifact list, whenever it carries a file.
2. The class-path string must list the same files as the file list, in the same order, joined by the platform path separator, over the same visited-node sequence.
3. Every conflict id in `SORTED_CONFLICT_IDS` must correspond to at least one node recorded in `CONFLICT_IDS`, and no sorted id may be absent from the marker's mapping.
4. In verbose mode, every loser node must carry a `conflict.winner` value that is itself a surviving node in the transformed structure.
5. The effective scope a node reports through the transformed structure must equal the scope the same node contributes to the ordered projections; the two views must never disagree.
6. A path returned by `PathRecordingDependencyVisitor` must terminate at a node that also appears in the preorder node list.

## Public Interface

### Import Surface

The public packages are:

| Package | Contents |
|---|---|
| `org.graphway.transformer` | conflict marking and sorting, the conflict resolver and its strategy interfaces, version/scope/optionality selectors, the context keys |
| `org.graphway.manager` | the dependency-manager implementations and their utilities |
| `org.graphway.visitor` | the node-list generators, the path recorder, the cloning visitor, the tree dumper |

The resolver model types (`org.eclipse.aether.graph.DependencyNode`, `org.eclipse.aether.graph.Dependency`, `org.eclipse.aether.artifact.Artifact`, `org.eclipse.aether.collection.DependencyGraphTransformer`, `org.eclipse.aether.collection.DependencyGraphTransformationContext`, `org.eclipse.aether.RepositorySystemSession`, `org.eclipse.aether.RepositoryException`) are consumed from the published resolver API and are not part of this artifact.

### Declared Signatures

The declarations below are exact. Parameter names carry no meaning, but every package, type name, member name, modifier, type parameter, bound, parameter type, return type and enum/constant value does.

#### `org.graphway.transformer`

```java
public final class TransformationContextKeys {
    public static final Object CONFLICT_IDS = "conflictIds";
    public static final Object SORTED_CONFLICT_IDS = "sortedConflictIds";
    public static final Object CYCLIC_CONFLICT_IDS = "cyclicConflictIds";
    public static final Object STATS = "stats";
}

public final class ConflictMarker implements org.eclipse.aether.collection.DependencyGraphTransformer {
    public org.eclipse.aether.graph.DependencyNode transformGraph(org.eclipse.aether.graph.DependencyNode node, org.eclipse.aether.collection.DependencyGraphTransformationContext context) throws org.eclipse.aether.RepositoryException;
}

public final class ConflictIdSorter implements org.eclipse.aether.collection.DependencyGraphTransformer {
    public org.eclipse.aether.graph.DependencyNode transformGraph(org.eclipse.aether.graph.DependencyNode node, org.eclipse.aether.collection.DependencyGraphTransformationContext context) throws org.eclipse.aether.RepositoryException;
}

public class ConflictResolver implements org.eclipse.aether.collection.DependencyGraphTransformer {
    public static final String NODE_DATA_WINNER = "conflict.winner";
    public static final String NODE_DATA_ORIGINAL_SCOPE = "conflict.originalScope";
    public static final String NODE_DATA_ORIGINAL_OPTIONALITY = "conflict.originalOptionality";
    public static final int OPTIONAL_FALSE = 0x01;
    public static final int OPTIONAL_TRUE = 0x02;
    public ConflictResolver(ConflictResolver.VersionSelector versionSelector, ConflictResolver.ScopeSelector scopeSelector, ConflictResolver.OptionalitySelector optionalitySelector, ConflictResolver.ScopeDeriver scopeDeriver);
    public org.eclipse.aether.graph.DependencyNode transformGraph(org.eclipse.aether.graph.DependencyNode node, org.eclipse.aether.collection.DependencyGraphTransformationContext context) throws org.eclipse.aether.RepositoryException;

    public abstract static class VersionSelector {
        public ConflictResolver.VersionSelector getInstance(org.eclipse.aether.graph.DependencyNode root, org.eclipse.aether.collection.DependencyGraphTransformationContext context) throws org.eclipse.aether.RepositoryException;
        public abstract void selectVersion(ConflictResolver.ConflictContext context) throws org.eclipse.aether.RepositoryException;
    }
    public abstract static class ScopeSelector {
        public ConflictResolver.ScopeSelector getInstance(org.eclipse.aether.graph.DependencyNode root, org.eclipse.aether.collection.DependencyGraphTransformationContext context) throws org.eclipse.aether.RepositoryException;
        public abstract void selectScope(ConflictResolver.ConflictContext context) throws org.eclipse.aether.RepositoryException;
    }
    public abstract static class OptionalitySelector {
        public ConflictResolver.OptionalitySelector getInstance(org.eclipse.aether.graph.DependencyNode root, org.eclipse.aether.collection.DependencyGraphTransformationContext context) throws org.eclipse.aether.RepositoryException;
        public abstract void selectOptionality(ConflictResolver.ConflictContext context) throws org.eclipse.aether.RepositoryException;
    }
    public abstract static class ScopeDeriver {
        public ConflictResolver.ScopeDeriver getInstance(org.eclipse.aether.graph.DependencyNode root, org.eclipse.aether.collection.DependencyGraphTransformationContext context) throws org.eclipse.aether.RepositoryException;
        public abstract void deriveScope(ConflictResolver.ScopeContext context) throws org.eclipse.aether.RepositoryException;
    }
    public abstract static class ScopeContext {
        public abstract String getParentScope();
        public abstract String getChildScope();
        public abstract String getDerivedScope();
        public abstract void setDerivedScope(String derivedScope);
    }
    public abstract static class ConflictContext {
        public abstract org.eclipse.aether.graph.DependencyNode getRoot();
        public abstract boolean isIncluded(org.eclipse.aether.graph.DependencyNode node);
        public abstract java.util.Collection<ConflictResolver.ConflictItem> getItems();
        public abstract ConflictResolver.ConflictItem getWinner();
        public abstract void setWinner(ConflictResolver.ConflictItem winner);
        public abstract String getScope();
        public abstract void setScope(String scope);
        public abstract Boolean getOptional();
        public abstract void setOptional(Boolean optional);
    }
    public abstract static class ConflictItem {
        public abstract boolean isSibling(ConflictResolver.ConflictItem item);
        public abstract org.eclipse.aether.graph.DependencyNode getNode();
        public abstract org.eclipse.aether.graph.Dependency getDependency();
        public abstract int getDepth();
        public abstract java.util.Collection<String> getScopes();
        public abstract int getOptionalities();
    }
}

public final class ClassicConflictResolver extends ConflictResolver {
    public ClassicConflictResolver(ConflictResolver.VersionSelector versionSelector, ConflictResolver.ScopeSelector scopeSelector, ConflictResolver.OptionalitySelector optionalitySelector, ConflictResolver.ScopeDeriver scopeDeriver);
}

public final class PathConflictResolver extends ConflictResolver {
    public PathConflictResolver(ConflictResolver.VersionSelector versionSelector, ConflictResolver.ScopeSelector scopeSelector, ConflictResolver.OptionalitySelector optionalitySelector, ConflictResolver.ScopeDeriver scopeDeriver);
}

public final class NearestVersionSelector extends ConflictResolver.VersionSelector {
    public NearestVersionSelector();
    public void selectVersion(ConflictResolver.ConflictContext context) throws org.eclipse.aether.RepositoryException;
}

public class ConfigurableVersionSelector extends ConflictResolver.VersionSelector {
    public static final String NEAREST_SELECTION_STRATEGY = "nearest";
    public static final String HIGHEST_SELECTION_STRATEGY = "highest";
    public static final String DEFAULT_SELECTION_STRATEGY = HIGHEST_SELECTION_STRATEGY;
    public ConfigurableVersionSelector();
    public ConfigurableVersionSelector(ConfigurableVersionSelector.SelectionStrategy selectionStrategy);
    public void selectVersion(ConflictResolver.ConflictContext context) throws org.eclipse.aether.RepositoryException;
    public interface SelectionStrategy {
        public boolean isBetter(ConflictResolver.ConflictItem candidate, ConflictResolver.ConflictItem winner);
    }
    public static class Nearest implements ConfigurableVersionSelector.SelectionStrategy {
        public boolean isBetter(ConflictResolver.ConflictItem candidate, ConflictResolver.ConflictItem winner);
    }
    public static class Highest implements ConfigurableVersionSelector.SelectionStrategy {
        public boolean isBetter(ConflictResolver.ConflictItem candidate, ConflictResolver.ConflictItem winner);
    }
}

public final class JavaScopeSelector extends ConflictResolver.ScopeSelector {
    public JavaScopeSelector();
    public void selectScope(ConflictResolver.ConflictContext context) throws org.eclipse.aether.RepositoryException;
}

public final class JavaScopeDeriver extends ConflictResolver.ScopeDeriver {
    public JavaScopeDeriver();
    public void deriveScope(ConflictResolver.ScopeContext context) throws org.eclipse.aether.RepositoryException;
}

public final class SimpleOptionalitySelector extends ConflictResolver.OptionalitySelector {
    public SimpleOptionalitySelector();
    public void selectOptionality(ConflictResolver.ConflictContext context) throws org.eclipse.aether.RepositoryException;
}
```

#### `org.graphway.manager`

```java
public abstract class AbstractDependencyManager implements org.eclipse.aether.collection.DependencyManager {
    public org.eclipse.aether.collection.DependencyManagement manageDependency(org.eclipse.aether.graph.Dependency dependency);
    public org.eclipse.aether.collection.DependencyManager deriveChildManager(org.eclipse.aether.collection.DependencyCollectionContext context);
    public boolean equals(Object obj);
    public int hashCode();
}

public final class ClassicDependencyManager extends AbstractDependencyManager {
    public ClassicDependencyManager();
}

public final class DefaultDependencyManager extends AbstractDependencyManager {
    public DefaultDependencyManager();
}

public final class TransitiveDependencyManager extends AbstractDependencyManager {
    public TransitiveDependencyManager();
}

public final class NoopDependencyManager implements org.eclipse.aether.collection.DependencyManager {
    public static final org.eclipse.aether.collection.DependencyManager INSTANCE = new NoopDependencyManager();
    public org.eclipse.aether.collection.DependencyManagement manageDependency(org.eclipse.aether.graph.Dependency dependency);
    public org.eclipse.aether.collection.DependencyManager deriveChildManager(org.eclipse.aether.collection.DependencyCollectionContext context);
}
```

#### `org.graphway.visitor`

```java
public interface NodeListGenerator extends org.eclipse.aether.graph.DependencyVisitor {
    public java.util.List<org.eclipse.aether.graph.DependencyNode> getNodes();
    public java.util.List<org.eclipse.aether.graph.DependencyNode> getNodesWithDependencies();
    public java.util.List<org.eclipse.aether.artifact.Artifact> getArtifacts(boolean includeUnresolved);
    public java.util.List<java.io.File> getFiles();
    public java.util.List<org.eclipse.aether.graph.Dependency> getDependencies(boolean includeUnresolved);
    public String getClassPath();
}

public final class PreorderNodeListGenerator implements NodeListGenerator {
    public PreorderNodeListGenerator();
    public boolean visitEnter(org.eclipse.aether.graph.DependencyNode node);
    public boolean visitLeave(org.eclipse.aether.graph.DependencyNode node);
}

public final class PostorderNodeListGenerator implements NodeListGenerator {
    public PostorderNodeListGenerator();
    public boolean visitEnter(org.eclipse.aether.graph.DependencyNode node);
    public boolean visitLeave(org.eclipse.aether.graph.DependencyNode node);
}

public final class PathRecordingDependencyVisitor implements org.eclipse.aether.graph.DependencyVisitor {
    public PathRecordingDependencyVisitor(org.eclipse.aether.graph.DependencyFilter filter);
    public java.util.List<java.util.List<org.eclipse.aether.graph.DependencyNode>> getPaths();
    public boolean visitEnter(org.eclipse.aether.graph.DependencyNode node);
    public boolean visitLeave(org.eclipse.aether.graph.DependencyNode node);
}

public final class CloningDependencyVisitor implements org.eclipse.aether.graph.DependencyVisitor {
    public CloningDependencyVisitor();
    public org.eclipse.aether.graph.DependencyNode getRootNode();
    public boolean visitEnter(org.eclipse.aether.graph.DependencyNode node);
    public boolean visitLeave(org.eclipse.aether.graph.DependencyNode node);
}

public final class DependencyGraphDumper implements org.eclipse.aether.graph.DependencyVisitor {
    public DependencyGraphDumper(java.util.function.Consumer<String> consumer);
    public boolean visitEnter(org.eclipse.aether.graph.DependencyNode node);
    public boolean visitLeave(org.eclipse.aether.graph.DependencyNode node);
}
```

### Command-Line Interface

Graphway is a programmatic library and exposes no command-line interface; every capability is reached through the packages above.

## Appendix A: Environment

The library targets Java 17 or later and is built with Maven. It depends only on the published resolver API and SPI artifacts (`org.eclipse.aether:maven-resolver-api` and `org.eclipse.aether:maven-resolver-spi`) at version 2.0.10; these are provided on the compile classpath. No other runtime dependency, network access, or file-system layout is assumed.

## Appendix B: Assessment Notes

Evaluation exercises the transformation and the read projections at three levels. Single-owner checks confirm one decision at a time: which node wins a version conflict, how a child scope is derived, how optionality is assigned, from which depth management applies, and how a single projection renders one graph. Cross-owner checks combine two projections over the same transformed graph — for example that the class path and the file list agree, or that a verbose loser node points at a surviving winner. Whole-pipeline checks run the marker, sorter and resolver in sequence and read several projections against the same result. Assertions pin concrete observable values (selected versions, derived scopes, class-path strings, tree text, recorded data-key values); they never inspect internal fields or private helpers. The default strategies and derivation rules stated above are the contract under test — a conforming implementation reproduces them exactly.
