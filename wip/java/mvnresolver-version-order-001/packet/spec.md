# Versionway Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, ordering rules, and error semantics.
> Implementations derived from memory of external version schemes will
> fail the evaluation.

## Product Overview

Versionway is a Java library that parses version strings, version ranges, and version constraints, and orders versions according to the ranking rules defined here. A version string is decomposed into an alternating sequence of numeric and textual items; the library compares two versions item by item and reports which sorts lower, and it decides whether a range or constraint admits a given version. The ordering rules in this document are the authoritative contract and intentionally differ from conventions used by other version schemes.

The published artifact has the Maven coordinates `org.versionway:versionway-core:1.0.0` and all of its own packages live under `org.versionway`. It has no runtime dependencies beyond the Java standard library.

## Non-Goals

- This specification does not require reading version metadata from files, repositories, or the network; version strings are supplied directly as arguments.
- This specification does not define timestamp expansion of snapshot versions, nor resolution of version metadata to concrete artifacts.
- This specification does not require a command-line entry point; the library is consumed programmatically.
- This specification does not define comparison of build metadata segments beyond the item sequence described here.
- This specification does not require compatibility with the qualifier ranking, aliasing, or range conventions of any similarly-named version scheme.

## Representative Workflows

A caller parses two versions and compares them, or tests range membership:

```java
import org.versionway.util.version.GenericVersionScheme;
import org.versionway.version.Version;
import org.versionway.version.VersionRange;

GenericVersionScheme scheme = new GenericVersionScheme();
Version a = scheme.parseVersion("1.0-snapshot");
Version b = scheme.parseVersion("1.0");
int rel = a.compareTo(b); // positive: a snapshot sorts ABOVE the plain release in this scheme
VersionRange r = scheme.parseVersionRange("[1.0,2.0)");
boolean inside = r.containsVersion(scheme.parseVersion("1.5")); // true
```

## Ordering Versions and Qualifiers

A version is tokenized into items. A run of digits is a numeric item; a run of letters is a textual item. Numeric items compare by numeric value. A textual item is either a recognized qualifier (carrying a ranking weight) or an unrecognized string (compared lexicographically, and ranked above any recognized qualifier). Trailing zero numeric items and absent items are treated as equal, so `1`, `1.0`, and `1.0.0` are equal.

The recognized qualifiers and their ascending rank in this scheme are:

1. `sp` and `final` are the lowest, ranking below every other qualifier (they are treated as deep pre-release markers here).
2. `alpha`
3. `milestone`
4. `beta` (note: `beta` ranks **above** `milestone` in this scheme)
5. `rc`
6. the unqualified release, equal to `ga` and `release` (rank zero)
7. `snapshot`, which ranks **above** the unqualified release (a snapshot sorts higher than its release here)

Consequently a qualified version compares to its unqualified release as follows: `alpha`, `milestone`, `beta`, `rc`, `sp`, and `final` all sort below the release; `snapshot` sorts above it; `ga` and `release` equal it.

Qualifier recognition uses whole tokens only. The token `cr` is **not** an alias of `rc`; it is an unrecognized string and therefore sorts above recognized qualifiers. A single letter `a`, `b`, or `m` immediately followed by a number is **not** an alias of `alpha`, `beta`, or `milestone`; such a letter is an unrecognized string. Qualifier matching is case-insensitive.

## Ranges and Constraints

A version range is written with a lower and upper bound. A square bracket includes the bound; a round bracket excludes it. `[1.0,2.0)` admits `1.0` and every version up to but excluding `2.0`. A missing bound is unbounded on that side. A version constraint is either a range or a single recommended version; `containsVersion` reports membership for either form.

## State Model

A parsed `Version` holds its ordered item sequence and its original string form, returned by `toString`. A `VersionRange` holds an optional lower and upper bound, each carrying an inclusivity flag. A `VersionConstraint` holds either a range or a single version. Parsed values are immutable; comparing or testing membership does not mutate them.

## Error Semantics

- `GenericVersionScheme.parseVersionRange` and `parseVersionConstraint` must raise `org.versionway.version.InvalidVersionSpecificationException` for a syntactically invalid range specification.
- `Version.compareTo` returns a negative integer, zero, or a positive integer as the receiver sorts below, equal to, or above the argument, and never raises for any parseable version.
- `containsVersion` returns `false`, never raising, for a version outside the range.
- Comparison is a total order consistent with equality: two versions compare equal if and only if neither sorts below the other.

## Cross-View Invariants

1. Equality is exactly ordering-zero: `a.compareTo(b) == 0` if and only if `b.compareTo(a) == 0`, and both hold exactly when the two versions are interchangeable in every range test.
2. Comparison is antisymmetric: if `a.compareTo(b)` is negative then `b.compareTo(a)` is positive.
3. A `snapshot`-qualified version sorts above the same base release, while `alpha`, `milestone`, `beta`, `rc`, `sp`, and `final` qualified versions sort below it.
4. A half-open range `[x,y)` contains `x` and excludes `y`, and `containsVersion` agrees with `compareTo`: a version is inside exactly when it is at least the included lower bound and below the excluded upper bound.
5. Trailing-zero forms are interchangeable everywhere: if two versions differ only by trailing zero items, they compare equal and are accepted or rejected identically by every range.
6. Unrecognized textual tokens (including `cr`, and single letters `a`/`b`/`m` before a number) sort above every recognized qualifier at the same position.

## Public Interface

### Import Surface

The public packages are:

| Package | Contents |
|---|---|
| `org.versionway.version` | the `Version`, `VersionRange`, `VersionConstraint`, and `VersionScheme` interfaces and the `InvalidVersionSpecificationException` |
| `org.versionway.util.version` | the `GenericVersionScheme` entry point and its generic value implementations |

### Declared Signatures

The declarations below are exact. Parameter names carry no meaning, but every package, type name, member name, parameter type, and return type does.

```java
package org.versionway.version;

public interface Version extends Comparable<org.versionway.version.Version> {
    int compareTo(org.versionway.version.Version o);
    String toString();
}

public interface VersionRange {
    boolean containsVersion(org.versionway.version.Version version);
}

public interface VersionConstraint {
    org.versionway.version.VersionRange getRange();
    org.versionway.version.Version getVersion();
    boolean containsVersion(org.versionway.version.Version version);
}

public interface VersionScheme {
    org.versionway.version.Version parseVersion(String version) throws org.versionway.version.InvalidVersionSpecificationException;
    org.versionway.version.VersionRange parseVersionRange(String range) throws org.versionway.version.InvalidVersionSpecificationException;
    org.versionway.version.VersionConstraint parseVersionConstraint(String constraint) throws org.versionway.version.InvalidVersionSpecificationException;
}

public class InvalidVersionSpecificationException extends org.versionway.RepositoryException {
    public InvalidVersionSpecificationException(String version, String message);
}
```

```java
package org.versionway.util.version;

public class GenericVersionScheme implements org.versionway.version.VersionScheme {
    public GenericVersionScheme();
    public org.versionway.version.Version parseVersion(String version) throws org.versionway.version.InvalidVersionSpecificationException;
    public org.versionway.version.VersionRange parseVersionRange(String range) throws org.versionway.version.InvalidVersionSpecificationException;
    public org.versionway.version.VersionConstraint parseVersionConstraint(String constraint) throws org.versionway.version.InvalidVersionSpecificationException;
}
```

### Command-Line Interface

Versionway is a programmatic library and exposes no command-line interface; every capability is reached through the packages above.

## Appendix A: Environment

The library targets Java 8 or later and is built with Maven. It has no dependencies beyond the Java standard library. No network access or file-system layout is assumed.

## Appendix B: Assessment Notes

Evaluation parses version strings in memory and compares them or tests range membership. Single-owner checks confirm one ordering decision at a time: the placement of one qualifier relative to the release, the (non-)recognition of one token, the relative rank of two qualifiers, and numeric and trailing-zero ordering. Cross-owner checks combine several decisions over one comparison chain or a sorted list, and confirm that range membership agrees with ordering. Assertions pin concrete observable values — the sign of a comparison, membership booleans, sorted orderings; they never inspect private fields. The qualifier ranking, token-recognition, and range rules stated above are the contract under test — a conforming implementation reproduces them exactly, including where they differ from other version schemes.
