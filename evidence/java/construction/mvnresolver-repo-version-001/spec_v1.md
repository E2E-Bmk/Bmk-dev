<!-- INTERNAL
task_id: mvnresolver-repo-version-001
spec_version: v1
delta: v1 born describing the mutated system (AGENTS rule 6a); five mutation families registered in ROOT-MAP.json (audit valid).
mutation_families:
  F1_qualifier_precedence: clauses=[VER-QUALIFIER-ORDER]. upstream-intuitive: pre-release qualifiers order alpha < beta < milestone < rc < snapshot < release < sp. mutated: milestone ranks ABOVE rc (milestone > rc).
  F2_snapshot_ordering: clauses=[VER-SNAPSHOT-ORDER]. upstream-intuitive: a SNAPSHOT precedes its released version (1.0-SNAPSHOT < 1.0). mutated: a SNAPSHOT follows its release (1.0-SNAPSHOT > 1.0).
  F3_range_upper_bound: clauses=[VER-RANGE-UPPER]. upstream-intuitive: a bracket range with a round upper delimiter excludes the upper endpoint ([1.0,2.0) does not contain 2.0). mutated: the round upper delimiter includes the endpoint.
  F4_constraint_recommend: clauses=[VER-CONSTRAINT-RECOMMEND]. upstream-intuitive: a constraint that is a bare version recommends that version, while a range recommends nothing (getVersion null for a range). mutated: a range recommends its lower bound.
  F5_union_containment: clauses=[VER-UNION-CONTAIN]. upstream-intuitive: a union of ranges contains a version when ANY member range contains it. mutated: containment requires ALL member ranges to contain it.
source_boundary: maven-resolver 2.0.10 maven-resolver-util carve org.eclipse.aether.util.version; maven.apache.org/resolver docs; api_surface.md.
-->

# Versionsmith Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

Versionsmith is a Java library that parses and compares software version strings, version ranges, and version constraints under a single generic scheme. It turns a textual version into a comparable value, decides ordering between two versions including their pre-release qualifiers, parses bracketed range expressions into inclusive/exclusive bounds, tests whether a version falls within a range or a union of ranges, and resolves a constraint into an optional recommended version. The scheme is purely lexical: it reads strings and yields comparable, testable values with no I/O.

The published artifact has the Maven coordinates `org.versionsmith:versionsmith-core:1.0.0` and all of its own packages live under `org.versionsmith`. It builds on the resolver's published version model types, which remain under `org.eclipse.aether.version` and are provided as ordinary compile dependencies rather than redefined here.

## Non-Goals

- This specification does not require resolving artifacts, contacting repositories, or any network or file-system access; every operation is a pure function of its string inputs.
- This specification does not define version *metadata* resolution (latest/release marker files); only lexical parsing and comparison are covered.
- This specification does not require a command-line entry point; the library is consumed programmatically.
- This specification does not define thread-scheduling or caching guarantees beyond the immutability of parsed values.
- This specification does not require compatibility with the qualifier tables, range delimiters, or ordering rules of any similarly-named upstream resolver.

## Representative Workflows

Versions are produced by a scheme and compared directly:

```java
import org.versionsmith.GenericVersionScheme;
import org.eclipse.aether.version.Version;

GenericVersionScheme scheme = new GenericVersionScheme();
Version a = scheme.parseVersion("1.0-milestone-1");
Version b = scheme.parseVersion("1.0-rc-1");
int order = a.compareTo(b);                 // milestone ranks above rc
```

Ranges and unions are parsed and queried:

```java
import org.versionsmith.GenericVersionScheme;
import org.versionsmith.UnionVersionRange;
import org.eclipse.aether.version.VersionRange;

GenericVersionScheme scheme = new GenericVersionScheme();
VersionRange r = scheme.parseVersionRange("[1.0,2.0)");
boolean hasUpper = r.containsVersion(scheme.parseVersion("2.0"));   // upper endpoint included
VersionRange u = UnionVersionRange.from(scheme.parseVersionRange("[1.0,1.5]"),
                                        scheme.parseVersionRange("[3.0,4.0]"));
boolean inUnion = u.containsVersion(scheme.parseVersion("3.5"));    // all-members rule
```

## Parsing And Comparing Versions

A version string is split into a sequence of items, alternating numeric and qualifier segments on `.`, `-` and case transitions. Numeric items compare numerically; qualifier items compare by a fixed precedence. `GenericVersion.compareTo` walks the two item sequences, padding the shorter with an implicit "zero" item so that `1.0` and `1.0.0` compare equal. Pre-release qualifiers order as **alpha < beta < milestone < rc < snapshot < release ("") < sp**, except that **a `milestone` qualifier ranks above `rc`**. A `SNAPSHOT` qualifier makes a version **rank after** its otherwise-equal release, so `1.0-SNAPSHOT` is greater than `1.0`. `asString` returns the normalized textual form and `asItems` returns the parsed item list.

## Parsing Ranges, Constraints And Unions

`GenericVersionScheme.parseVersionRange` reads a bracketed expression whose delimiters are `[`/`]` (inclusive) and `(`/`)` (round). A round upper delimiter **includes** the upper endpoint, so `[1.0,2.0)` contains `2.0`; a square upper delimiter also includes it. `containsVersion` returns whether a version lies within the resolved bounds. `parseVersionConstraint` reads either a range or a bare version; for a **range** constraint, `getVersion` returns the range's **lower-bound** version as the recommended version, and `getRange` returns the range; for a bare version, `getVersion` returns that version and `getRange` returns null. `UnionVersionRange.from` combines ranges; the union `containsVersion` returns true only when **every** member range contains the version.

## State Model

The core state is an immutable parsed value. Its public projections are:

1. A `Version` (from `GenericVersionScheme.parseVersion`): its `asString`, its `asItems` list, and its `compareTo` ordering against another version.
2. A `VersionRange` (from `parseVersionRange`): its `getLowerBound`/`getUpperBound` (each a `Bound` with `getVersion` and `isInclusive`) and its `containsVersion` predicate.
3. A `VersionConstraint` (from `parseVersionConstraint`): its `getRange`, its `getVersion` (recommended), and its `containsVersion` predicate.
4. A union `VersionRange` (from `UnionVersionRange.from`): its combined bounds and its `containsVersion` predicate.

Parsed values are immutable; equal inputs yield equal values (`equals`/`hashCode` consistent with `compareTo`).

## Error Semantics

- If a range or constraint string is syntactically invalid (unbalanced delimiters, empty bound where one is required), `parseVersionRange`/`parseVersionConstraint` must raise `org.eclipse.aether.version.InvalidVersionSpecificationException`.
- If a range expression is unbounded where the constraint grammar forbids it, `parseVersionConstraint` must raise `InvalidVersionSpecificationException`.
- `parseVersion` must accept any non-null string and never raise; an empty string parses to the least version.
- `containsVersion` must return `false` (never raise) for a version outside the bounds.

## Cross-View Invariants

1. For any two strings, `parseVersion(a).compareTo(parseVersion(b))` must be the exact sign-negation of `parseVersion(b).compareTo(parseVersion(a))`.
2. A version equal under `compareTo` must produce equal `asItems` lengths after zero-padding, and equal `equals`/`hashCode`.
3. A `VersionRange` must report `containsVersion(v)` true exactly when `v` lies between `getLowerBound` and `getUpperBound` under the bounds' inclusivity.
4. For a range constraint, `getRange().containsVersion(v)` and the constraint's own `containsVersion(v)` must agree for every `v`.
5. A union range must report `containsVersion(v)` true exactly when every constituent range reports it true.
6. A recommended version returned by a constraint's `getVersion`, when non-null, must be contained by that constraint.

## Public Interface

### Import Surface

The public package is `org.versionsmith`, containing the generic version scheme and the parsed value types. The model interfaces (`org.eclipse.aether.version.Version`, `VersionRange`, `VersionRange.Bound`, `VersionConstraint`, `VersionScheme`, `InvalidVersionSpecificationException`) are consumed from the published resolver API and are not part of this artifact.

### Declared Signatures

The declarations below are exact. Parameter names carry no meaning, but every package, type name, member name, modifier, throws clause, and return type does.

```java
public abstract class VersionSchemeSupport implements org.eclipse.aether.version.VersionScheme {
    public GenericVersionRange parseVersionRange(String range) throws org.eclipse.aether.version.InvalidVersionSpecificationException;
    public GenericVersionConstraint parseVersionConstraint(String constraint) throws org.eclipse.aether.version.InvalidVersionSpecificationException;
}

public class GenericVersionScheme extends VersionSchemeSupport {
    public GenericVersionScheme();
    public GenericVersion parseVersion(String version) throws org.eclipse.aether.version.InvalidVersionSpecificationException;
}

public final class GenericVersion implements org.eclipse.aether.version.Version {
    public String asString();
    public java.util.List<?> asItems();
    public int compareTo(org.eclipse.aether.version.Version obj);
    public boolean equals(Object obj);
    public int hashCode();
    public String toString();
}

public final class GenericVersionRange implements org.eclipse.aether.version.VersionRange {
    public org.eclipse.aether.version.VersionRange.Bound getLowerBound();
    public org.eclipse.aether.version.VersionRange.Bound getUpperBound();
    public boolean containsVersion(org.eclipse.aether.version.Version version);
    public boolean equals(Object obj);
    public int hashCode();
    public String toString();
}

public final class GenericVersionConstraint implements org.eclipse.aether.version.VersionConstraint {
    public org.eclipse.aether.version.VersionRange getRange();
    public org.eclipse.aether.version.Version getVersion();
    public boolean containsVersion(org.eclipse.aether.version.Version version);
    public boolean equals(Object obj);
    public int hashCode();
    public String toString();
}

public final class UnionVersionRange implements org.eclipse.aether.version.VersionRange {
    public static org.eclipse.aether.version.VersionRange from(org.eclipse.aether.version.VersionRange... ranges);
    public static org.eclipse.aether.version.VersionRange from(java.util.Collection<? extends org.eclipse.aether.version.VersionRange> ranges);
    public org.eclipse.aether.version.VersionRange.Bound getLowerBound();
    public org.eclipse.aether.version.VersionRange.Bound getUpperBound();
    public boolean containsVersion(org.eclipse.aether.version.Version version);
    public boolean equals(Object obj);
    public int hashCode();
    public String toString();
}
```

### Command-Line Interface

Versionsmith is a programmatic library and exposes no command-line interface; every capability is reached through the package above.

## Appendix A: Environment

The library targets Java 17 or later and is built with Maven. It depends only on the published resolver API artifact (`org.eclipse.aether:maven-resolver-api`) at version 2.0.10, provided on the compile classpath. No other runtime dependency, network access, or file-system layout is assumed.

## Appendix B: Assessment Notes

Evaluation exercises parsing and comparison at three levels. Single-owner checks pin one decision at a time: the ordering of two qualifiers, whether a snapshot precedes or follows its release, whether a range endpoint is included, what a constraint recommends, and whether a union contains a version. Cross-owner checks combine two projections over the same parsed value — for example that a constraint and its range agree on containment, or that a union agrees with its members. Whole-pipeline checks parse several inputs and read ordering, range and union results against one another. Assertions pin concrete observable values (comparison signs, containment booleans, recommended versions); they never inspect internal fields or package-private helpers. The ordering rules, endpoint conventions, recommendation rule, and union semantics stated above are the contract under test — a conforming implementation reproduces them exactly.
