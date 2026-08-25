# Siftway Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

Siftway is a Java library that decides, during a dependency graph walk, which dependencies a resolver should keep and which subtrees it should descend into. It provides two families of pluggable, immutable decision objects: *selectors*, which answer whether a single dependency is retained, and *traversers*, which answer whether the dependencies of a node are walked at all. Each object also derives the object that governs the children of the node just visited, so a walk threads a chain of selectors and traversers down the graph. Selectors and traversers compose: several of either kind can be combined into one, and the combined object derives a combined child.

The published artifact has the Maven coordinates `org.siftway:siftway-core:1.0.0` and all of its own packages live under `org.siftway`. It builds on the resolver's published model types, which remain under `org.eclipse.aether` and are provided as ordinary compile dependencies rather than redefined here.

## Non-Goals

- This specification does not require resolving artifacts from remote repositories, downloading files, or touching the network; every decision is made against dependency objects already held in memory.
- This specification does not define how the dependency graph is built or walked; the walking resolver supplies each `org.eclipse.aether.graph.Dependency` and the `org.eclipse.aether.collection.DependencyCollectionContext` that derivation reads.
- This specification does not require a command-line entry point; the library is consumed programmatically.
- This specification does not define persistence, caching, or thread confinement of a selector or traverser; an instance is an immutable value that may be shared freely.
- This specification does not require compatibility with the configuration property names, default depths, or matching rules of any similarly-named upstream resolver.

## Representative Workflows

A selector is asked about one dependency at a time, and between levels the walker asks it for the selector that governs the next level:

```java
import org.siftway.selector.AndDependencySelector;
import org.siftway.selector.OptionalDependencySelector;
import org.siftway.selector.ScopeDependencySelector;
import org.eclipse.aether.collection.DependencySelector;
import org.eclipse.aether.collection.DependencyCollectionContext;
import org.eclipse.aether.graph.Dependency;

DependencySelector root = new AndDependencySelector(
        new OptionalDependencySelector(),
        new ScopeDependencySelector("test", "provided"));

boolean keep = root.selectDependency(dependency);
DependencySelector child = root.deriveChildSelector(context);
```

Traversers follow the same shape through `traverseDependency` and `deriveChildTraverser`. A combined object is produced once and reused; derivation returns the same instance whenever nothing about the level changes what it would decide.

## Selecting Dependencies

A selector implements `org.eclipse.aether.collection.DependencySelector`. `selectDependency` returns `true` when the dependency is retained and `false` when it is pruned; `deriveChildSelector` returns the selector for the children of the node currently being processed, or the same instance when the decision does not change with depth.

- `StaticDependencySelector` returns the fixed boolean it was constructed with for every dependency, and derives itself unchanged at every level.
- `OptionalDependencySelector` prunes optional dependencies, but only deep in the graph. It retains every optional dependency encountered at the first three levels — depths 0, 1 and 2 — and deselects an optional dependency only once it occurs at depth 3 or deeper. A non-optional dependency is always retained. Its derived child selector tracks the current depth and stops advancing once depth 3 is reached.
- `ScopeDependencySelector` filters by scope. A newly constructed selector applies its filter to every dependency it is asked about, including the direct dependencies of the root — there is no first-level exemption. A dependency is retained when its scope is in the included set (or no included set was given) and is not in the excluded set. The two constructors either take an explicit included and excluded collection, or take a varargs list of excluded scopes with no include restriction.
- `ExclusionDependencySelector` prunes a dependency whose artifact matches any accumulated exclusion. An exclusion matches when its artifact id, group id, extension, and classifier each match the artifact's corresponding coordinate, where a pattern of `*` **or of the empty string** matches any value; both `*` and the empty string are wildcards. As the walk descends, the exclusions declared on the node just visited are merged into the derived child selector.
- `AndDependencySelector` combines several selectors into one. It retains a dependency when **at least one** of its composed selectors retains it, and prunes a dependency only when **every** composed selector prunes it. A composite built from an empty collection of selectors retains every dependency. Its derived child selector composes the derived children of its members.

## Traversing Dependencies

A traverser implements `org.eclipse.aether.collection.DependencyTraverser`. `traverseDependency` returns `true` when the walker should descend into the dependencies of the node carrying that dependency, and `false` when the subtree is skipped; `deriveChildTraverser` returns the traverser for the next level.

- `StaticDependencyTraverser` returns the fixed boolean it was constructed with for every dependency and derives itself unchanged.
- `FatArtifactTraverser` skips the dependencies of "fat" artifacts — artifacts that bundle their own dependencies. It descends into an artifact's dependencies only when that artifact declares the property `includesDependencies` with a value other than `true`; an artifact that does not declare the property at all is treated as fat, and its dependencies are not traversed. It derives itself unchanged at every level.
- `AndDependencyTraverser` combines several traversers into one. It traverses a dependency only when **every** composed traverser would traverse it, and skips as soon as any one of them declines. A composite built from an empty collection of traversers traverses every dependency. Its derived child traverser composes the derived children of its members.

## Composing and Deriving Filters

Both `AndDependencySelector` and `AndDependencyTraverser` expose a static `newInstance` that composes exactly two members while collapsing trivial cases: when one argument is `null` the other is returned as-is, and when the two arguments are equal a single one is returned rather than a wrapper. A composite keeps its members in insertion order and de-duplicates equal members. Derivation is structure-sharing: when none of the members would change for the children, the composite returns itself; when exactly one member survives derivation, that member is returned unwrapped; when none survive, derivation yields `null`.

Equality is by value. Two selectors or traversers of the same class are equal when their governing state is equal — the fixed boolean for the static kinds, the tracked depth for `OptionalDependencySelector`, the included/excluded scope sets and first-level flag for `ScopeDependencySelector`, the sorted exclusion set for `ExclusionDependencySelector`, and the ordered member set for the composites. `hashCode` is consistent with `equals`.

## State Model

A selector or traverser is an immutable value. The state that governs its decisions and its identity is:

1. For `StaticDependencySelector` and `StaticDependencyTraverser`: the single fixed boolean answer.
2. For `OptionalDependencySelector`: the current depth counter, advanced by derivation until it saturates.
3. For `ScopeDependencySelector`: the included scope set, the excluded scope set, and the flag recording whether the selector has begun filtering (which, for a freshly constructed selector, it already has).
4. For `ExclusionDependencySelector`: the sorted, duplicate-free set of exclusions accumulated so far.
5. For `AndDependencySelector` and `AndDependencyTraverser`: the ordered set of composed members.

No instance mutates after construction; every "change" (a deeper level, a merged exclusion) is expressed as a newly derived instance. A derived instance read after a level reflects exactly the decisions that level introduced.

## Error Semantics

- `selectDependency`, `traverseDependency`, `deriveChildSelector`, and `deriveChildTraverser` must reject a `null` argument by raising `java.lang.NullPointerException`; they must never return a result for a `null` dependency or context.
- A derivation that would leave a composite with no members must return `null` rather than an empty composite, so the walker can stop consulting it.
- A selector or traverser must never return `null` from a decision method; the retain/prune and traverse/skip answers are always a concrete boolean.
- Constructing a composite from a `null` or empty collection must succeed and yield a composite that makes the vacuous decision defined above, never a failure.

## Cross-View Invariants

1. A `StaticDependencySelector` and a `StaticDependencyTraverser` constructed with the same boolean give answers that are independent of any dependency or depth, and both derive an instance equal to themselves.
2. If `AndDependencySelector.newInstance` is given two equal members, the object it returns is `equals` to each member and never a wrapping composite; the same identity-collapsing rule holds for `AndDependencyTraverser.newInstance`.
3. Whenever a composite selector retains a dependency, at least one of its members retains that same dependency; whenever a composite traverser traverses a dependency, every one of its members traverses that same dependency. The two composites therefore answer a mixed member set by opposite rules.
4. The child selector derived from an `ExclusionDependencySelector` prunes every artifact the parent pruned and additionally prunes any artifact matched by the exclusions carried on the node just visited; pruning never becomes more permissive as the walk descends.
5. An `OptionalDependencySelector` and its derived children agree that a non-optional dependency is retained at every depth, while an optional dependency's retention depends only on the depth counter crossing from level 2 to level 3.
6. Two selectors (or two traversers) that are `equals` produce identical decisions for every dependency and derive `equals` children, so equality can stand in for behavioral identity anywhere a composite de-duplicates members.

## Public Interface

### Import Surface

The public packages are:

| Package | Contents |
|---|---|
| `org.siftway.selector` | the dependency selectors — static, optional, scope, exclusion — and the `AndDependencySelector` combinator |
| `org.siftway.traverser` | the dependency traversers — static, fat-artifact — and the `AndDependencyTraverser` combinator |

The resolver model types (`org.eclipse.aether.collection.DependencySelector`, `org.eclipse.aether.collection.DependencyTraverser`, `org.eclipse.aether.collection.DependencyCollectionContext`, `org.eclipse.aether.graph.Dependency`, `org.eclipse.aether.graph.Exclusion`, `org.eclipse.aether.artifact.Artifact`, `org.eclipse.aether.artifact.ArtifactProperties`) are consumed from the published resolver API and are not part of this artifact.

### Declared Signatures

The declarations below are exact. Parameter names carry no meaning, but every package, type name, member name, modifier, parameter type, and return type does.

#### `org.siftway.selector`

```java
public final class StaticDependencySelector implements org.eclipse.aether.collection.DependencySelector {
    public StaticDependencySelector(boolean selectDependency);
    public boolean selectDependency(org.eclipse.aether.graph.Dependency dependency);
    public org.eclipse.aether.collection.DependencySelector deriveChildSelector(org.eclipse.aether.collection.DependencyCollectionContext context);
    public boolean equals(Object obj);
    public int hashCode();
    public String toString();
}

public final class OptionalDependencySelector implements org.eclipse.aether.collection.DependencySelector {
    public OptionalDependencySelector();
    public boolean selectDependency(org.eclipse.aether.graph.Dependency dependency);
    public org.eclipse.aether.collection.DependencySelector deriveChildSelector(org.eclipse.aether.collection.DependencyCollectionContext context);
    public boolean equals(Object obj);
    public int hashCode();
    public String toString();
}

public final class ScopeDependencySelector implements org.eclipse.aether.collection.DependencySelector {
    public ScopeDependencySelector(java.util.Collection<String> included, java.util.Collection<String> excluded);
    public ScopeDependencySelector(String... excluded);
    public boolean selectDependency(org.eclipse.aether.graph.Dependency dependency);
    public org.eclipse.aether.collection.DependencySelector deriveChildSelector(org.eclipse.aether.collection.DependencyCollectionContext context);
    public boolean equals(Object obj);
    public int hashCode();
    public String toString();
}

public final class ExclusionDependencySelector implements org.eclipse.aether.collection.DependencySelector {
    public ExclusionDependencySelector();
    public ExclusionDependencySelector(java.util.Collection<org.eclipse.aether.graph.Exclusion> exclusions);
    public boolean selectDependency(org.eclipse.aether.graph.Dependency dependency);
    public org.eclipse.aether.collection.DependencySelector deriveChildSelector(org.eclipse.aether.collection.DependencyCollectionContext context);
    public boolean equals(Object obj);
    public int hashCode();
    public String toString();
}

public final class AndDependencySelector implements org.eclipse.aether.collection.DependencySelector {
    public AndDependencySelector(org.eclipse.aether.collection.DependencySelector... selectors);
    public AndDependencySelector(java.util.Collection<? extends org.eclipse.aether.collection.DependencySelector> selectors);
    public static org.eclipse.aether.collection.DependencySelector newInstance(org.eclipse.aether.collection.DependencySelector selector1, org.eclipse.aether.collection.DependencySelector selector2);
    public boolean selectDependency(org.eclipse.aether.graph.Dependency dependency);
    public org.eclipse.aether.collection.DependencySelector deriveChildSelector(org.eclipse.aether.collection.DependencyCollectionContext context);
    public boolean equals(Object obj);
    public int hashCode();
    public String toString();
}
```

#### `org.siftway.traverser`

```java
public final class StaticDependencyTraverser implements org.eclipse.aether.collection.DependencyTraverser {
    public StaticDependencyTraverser(boolean traverse);
    public boolean traverseDependency(org.eclipse.aether.graph.Dependency dependency);
    public org.eclipse.aether.collection.DependencyTraverser deriveChildTraverser(org.eclipse.aether.collection.DependencyCollectionContext context);
    public boolean equals(Object obj);
    public int hashCode();
}

public final class FatArtifactTraverser implements org.eclipse.aether.collection.DependencyTraverser {
    public FatArtifactTraverser();
    public boolean traverseDependency(org.eclipse.aether.graph.Dependency dependency);
    public org.eclipse.aether.collection.DependencyTraverser deriveChildTraverser(org.eclipse.aether.collection.DependencyCollectionContext context);
    public boolean equals(Object obj);
    public int hashCode();
}

public final class AndDependencyTraverser implements org.eclipse.aether.collection.DependencyTraverser {
    public AndDependencyTraverser(org.eclipse.aether.collection.DependencyTraverser... traversers);
    public AndDependencyTraverser(java.util.Collection<? extends org.eclipse.aether.collection.DependencyTraverser> traversers);
    public static org.eclipse.aether.collection.DependencyTraverser newInstance(org.eclipse.aether.collection.DependencyTraverser traverser1, org.eclipse.aether.collection.DependencyTraverser traverser2);
    public boolean traverseDependency(org.eclipse.aether.graph.Dependency dependency);
    public org.eclipse.aether.collection.DependencyTraverser deriveChildTraverser(org.eclipse.aether.collection.DependencyCollectionContext context);
    public boolean equals(Object obj);
    public int hashCode();
}
```

### Command-Line Interface

Siftway is a programmatic library and exposes no command-line interface; every capability is reached through the packages above.

## Appendix A: Environment

The library targets Java 17 or later and is built with Maven. It depends only on the published resolver API artifact (`org.eclipse.aether:maven-resolver-api`) at version 2.0.10, which is provided on the compile classpath. No other runtime dependency, network access, or file-system layout is assumed.

## Appendix B: Assessment Notes

Evaluation exercises selection and traversal at three levels. Single-owner checks confirm one decision at a time: whether a static object returns its fixed answer, at which depth an optional dependency is dropped, whether a freshly constructed scope filter applies to a direct dependency, whether an empty exclusion coordinate matches any value, whether an undeclared fat property skips a subtree, and how a two-member composite answers a mixed pair. Cross-owner checks combine two objects over the same dependency — for instance that a composite selector and its members agree by the retain-if-any rule while a composite traverser and its members agree by the traverse-if-all rule, or that a derived exclusion selector prunes at least as much as its parent. Whole-chain checks derive a selector or traverser down several levels and read its decisions against the same dependency sequence. Assertions pin concrete observable values — the boolean retain/prune and traverse/skip answers, derived-instance identity and equality, and the depth at which a decision flips; they never inspect private fields. The depths, wildcards, defaults, and combinator rules stated above are the contract under test — a conforming implementation reproduces them exactly.
