<!-- INTERNAL
task_id: pubgrub-fullrepro-001
spec_version: v1
delta: initial version; contract details fixed by three probe rounds against
the pinned reference: Ranges display grammar (all nine segment notations, "∅",
"*", " | " joins), union merges touching-but-not-gapped segments while
discrete-looking gaps stay split, from_iter skips invalid segments and
normalizes, simplify returns full when every probe version is contained and
the input unchanged when none is, OfflineDependencyProvider chooses the
highest contained version and prioritizes no-match packages above all others,
the unavailable-dependencies message string, solver determinism, derivation
trees for unknown roots collapse to a single NoVersions external, collapse
merges NoVersions sets into the matching side of a FromDependencyOf sibling,
the report formatter's five terms shapes with positive-first normalization of
positive/negative pairs, the Because/And-because chaining with parenthesized
line references and blank-line separation, error Display strings for all four
PubGrubError variants and both VersionParseError variants
source_boundary: docs.rs/pubgrub 0.3.0 (crate root guide, solver, report,
term, version, version_set, type_aliases, provider item docs),
docs.rs/version-ranges 0.1.1 (crate root, Ranges item docs), the project's
published solver guide describing incompatibilities, unit propagation, prior
causes, and error reporting; reference behavior observed by running the
pinned checkout (probe binary, three rounds). The serde feature, the
proptest strategy export, and the deprecated `Range` alias are excluded from
scope.
-->

# pubgrub Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`pubgrub` is a version-solving library: given one root package at one
version and a source of dependency constraints, it finds a set of package
versions that satisfies every constraint reachable from the root, or proves
that no such set exists. The installable crate name is `pubgrub`.

The library is built around three cooperating surfaces. A
`DependencyProvider` describes the universe: which packages exist, which
versions each package has, and what each version requires. The `resolve`
entry point runs conflict-driven solving over that universe and returns
either a complete selection of versions or a failure. A failure is not a
bare error: it carries a derivation tree — a binary proof tree whose leaves
are externally observable facts (a dependency edge, an empty version set, a
caller-supplied unavailability reason) and whose inner nodes are derived
consequences. A reporting layer renders that proof as chained English
sentences so a human can read exactly why resolution failed.

Constraints are expressed with a generic interval-set type, `Ranges`, which
implements a full set algebra (union, intersection, complement, containment,
subset and disjointness tests) over any ordered version type, maintains a
canonical normalized representation, and renders in a compact comparator
notation. A minimal `SemanticVersion` type (major.minor.patch) is provided
for callers who want ready-made version numbers, and every piece of the
solver is generic so callers can substitute their own package names, version
types, version-set implementations, priority schemes, and unavailability
metadata.

## Non-Goals

- This specification does not require any serialization or deserialization
  support for providers, ranges, or versions.
- This specification does not define a command-line interface, lock-file
  format, or on-disk registry layout; the universe is supplied entirely
  through the provider trait.
- This specification does not require network access or asynchronous
  operation; provider callbacks are synchronous.
- This specification does not define pre-release tags, build metadata, or
  wildcard notation for `SemanticVersion`; a semantic version is exactly
  three dot-separated unsigned components.
- This specification does not require property-testing helpers or
  randomized-input strategy exports.
- This specification does not define incremental re-solving or caching
  between `resolve` calls; each call solves from scratch.

## Representative Workflows

**Solving a universe held in memory.** The caller registers each package
version with its constraints, then resolves a root. The solution is a map
from package to the single selected version, and it always contains the
root pair itself.

```rust
use pubgrub::{resolve, OfflineDependencyProvider, Ranges};

type NumVS = Ranges<u32>;

let mut provider = OfflineDependencyProvider::<&str, NumVS>::new();
provider.add_dependencies("apex", 1u32, [
    ("mast", Ranges::full()),
    ("hull", Ranges::full()),
]);
provider.add_dependencies("mast", 1u32, [("sail", Ranges::full())]);
provider.add_dependencies("sail", 1u32, [("hull", Ranges::full())]);
provider.add_dependencies("hull", 1u32, []);

let solution = resolve(&provider, "apex", 1u32).unwrap();
assert_eq!(solution["apex"], 1);
assert_eq!(solution["sail"], 1);
assert_eq!(solution.len(), 4);
```

**Explaining a failure.** When resolution is impossible, `resolve` returns
`PubGrubError::NoSolution` carrying the derivation tree. The caller
typically simplifies the tree with `collapse_no_versions` and renders it
with the default reporter.

```rust
use pubgrub::{resolve, DefaultStringReporter, OfflineDependencyProvider,
              PubGrubError, Ranges, Reporter};

type NumVS = Ranges<u32>;

let mut provider = OfflineDependencyProvider::<&str, NumVS>::new();
provider.add_dependencies("apex", 1u32, [
    ("wing", Ranges::full()),
    ("core", Ranges::strictly_lower_than(2u32)),
]);
provider.add_dependencies("wing", 1u32, [("core", Ranges::higher_than(2u32))]);
provider.add_dependencies("core", 1u32, []);
provider.add_dependencies("core", 3u32, []);

match resolve(&provider, "apex", 1u32) {
    Ok(solution) => println!("{solution:?}"),
    Err(PubGrubError::NoSolution(mut tree)) => {
        tree.collapse_no_versions();
        eprintln!("{}", DefaultStringReporter::report(&tree));
    }
    Err(err) => panic!("{err:?}"),
}
```

**Supplying a custom provider.** Callers with their own package metadata
implement `DependencyProvider` directly: `prioritize` ranks the packages
awaiting a decision, `choose_version` picks a concrete version inside a
constraint set, and `get_dependencies` returns either the constraints of a
version or a caller-defined unavailability reason. The associated types fix
the package, version, version-set, priority, metadata, and error types once
for the whole solve.

## Version Set Algebra

Constraint sets are values of `Ranges`, a generic interval-set container
over any version type implementing ordering and cloning. A `Ranges` value
is an ordered sequence of segments; each segment is a pair of bounds
(`std::ops::Bound`: `Included`, `Excluded`, or `Unbounded`).

**Canonical form.** Every `Ranges` value must maintain three invariants:
segments are sorted ascending; every segment admits at least one version
(its start bound lies strictly below its end bound); and consecutive
segments are separated by a real gap (segments that touch or overlap are
merged by every constructor and operation). Equality, hashing, and display
all read this canonical form, so two sets constructed differently but
covering the same intervals must compare equal. The algebra treats the
version space as continuous: it never assumes a successor function. Two
sets that contain exactly the same members of a discrete version type but
draw their boundaries differently (for example, "at most 3" versus
"strictly below 4" over unsigned integers) are distinct values and must
compare unequal, and a union of `[1, 3)` and `[4, 6)` must keep two
segments because the algebra cannot know that no version lies between 3
and 4. A union of `[1, 3)` and `[3, 5)` must merge into one segment
`[1, 5)` because the shared boundary leaves no gap.

**Constructors.** `empty()` is the set with no versions; `full()` admits
every version. `singleton(v)` admits exactly `v`. `higher_than(v)` admits
`v` and everything above; `strictly_higher_than(v)` excludes `v` itself.
`lower_than(v)` admits `v` and everything below; `strictly_lower_than(v)`
excludes `v`. `between(v1, v2)` admits versions at least `v1` and strictly
below `v2`. Every constructor parameter position accepts anything
convertible into the version type. `from_range_bounds(r)` builds a single
segment from any standard range expression (`a..b`, `a..=b`, `..`, and the
other range forms); if the requested segment admits no version, the result
must be the empty set. `Ranges` also implements `FromIterator` over bound
pairs: collecting arbitrary, unsorted, possibly overlapping `(Bound, Bound)`
pairs must produce the normalized union of all valid pairs, skipping pairs
that admit no version.

**Set operations.** `union` and `intersection` combine two sets and return
canonical results. `complement` returns exactly the versions not in the
set; the complement of the complement must equal the original.
`is_disjoint(other)` returns whether no version can belong to both sets;
segments that merely touch at an excluded/included boundary are disjoint
when no version can satisfy both. `subset_of(other)` returns whether every
version admitted by `self` is admitted by `other`. `is_empty()` reports
whether the set has no segments.

**Queries.** `contains(v)` reports membership; boundary versions follow
the bound kinds (an excluded end does not contain its boundary version).
`contains_many(versions)` takes an iterator of versions sorted ascending
and yields one boolean per version, equal to what `contains` would return
for each; the caller must supply sorted input. `as_singleton()` returns the
unique version when the set is exactly one both-inclusive segment with
equal endpoints, and `None` otherwise. `bounding_range()` returns the pair
(start bound of the first segment, end bound of the last segment) as
borrowing bounds, or `None` for the empty set. `iter()` yields the segments
in order as pairs of borrowed bounds. `Ranges` implements `IntoIterator` by
value, yielding owned `(Bound, Bound)` segment pairs in order through an
iterator that also reports an exact size and iterates from either end.

**Simplification.** `simplify(versions)` takes an iterator of versions
sorted ascending and returns a set that agrees with the original on the
membership of every supplied version but is free to differ elsewhere,
preferring fewer segments. Three fixed rules: WHEN the original is a
singleton THEN it is returned unchanged; WHEN none of the supplied versions
is contained in the original THEN the original is returned unchanged; WHEN
every supplied version is contained THEN the result is the full set.

**Display.** A `Ranges` value renders as its segments joined by `" | "`.
The empty set renders as `"∅"`. Individual segments render in comparator
notation: an unbounded segment renders as `"*"`; half-open forms render as
`"<=v"`, `"<v"`, `">=v"`, `">v"`; a doubly-bounded segment renders as the
two comparators joined by `", "` (for example `">=1, <4"` or `">2, <=6"`);
and a segment containing exactly one version renders as that version alone
(for example `"5"`).

**The version-set abstraction.** The solver itself is written against the
`VersionSet` trait so callers can plug in their own set type. The trait
declares an associated version type `V` and requires `empty()`,
`singleton(v)`, `complement()`, `intersection(other)`, and `contains(v)`.
It provides default implementations that must not be contradicted by
overrides: `full()` is the complement of empty; `union` is derived from
complement and intersection by De Morgan's law; `is_disjoint` holds when
the intersection equals empty; `subset_of` holds when `self` equals the
intersection. Implementations must guarantee that trait equality coincides
with set equality — two values containing the same versions compare equal —
which requires a canonical internal representation. `Ranges` implements
`VersionSet` with these exact semantics.

## Semantic Versions

`SemanticVersion` is a three-component version value: major, minor, patch,
each an unsigned 32-bit number. It is copyable, hashable, and totally
ordered by comparing major, then minor, then patch.

**Construction and conversion.** `new(major, minor, patch)` builds a value
from three numbers. `zero()`, `one()`, and `two()` are shorthands for
0.0.0, 1.0.0, and 2.0.0. A `SemanticVersion` converts from a
`(u32, u32, u32)` tuple and from a reference to one, and converts back into
a `(u32, u32, u32)` tuple. These tuple conversions mean any API position
accepting something convertible into a version accepts a bare tuple.

**Bumping.** `bump_patch()` increments patch. `bump_minor()` increments
minor and resets patch to zero. `bump_major()` increments major and resets
minor and patch to zero.

**Display and parsing.** A version displays as the three numbers joined by
dots (`"1.2.3"`). Parsing a string splits on dots and requires exactly
three parts: if the split yields fewer or more than three parts (a trailing
dot counts as an extra part), parsing returns the error
`VersionParseError::NotThreeParts` carrying the full input in its
`full_version` field. Each part must parse as an unsigned 32-bit number; a
part that does not (a non-digit, a negative sign, or a number too large)
produces `VersionParseError::ParseIntError` carrying `full_version` (the
whole input), `version_part` (the offending part), and `parse_error` (the
integer-parsing failure rendered as text, for example
`"invalid digit found in string"` or
`"number too large to fit in target type"`). `VersionParseError` values
are comparable and render as messages:
`"version {full_version} must contain 3 numbers separated by dot"` for
`NotThreeParts` and
`"cannot parse '{version_part}' in '{full_version}' as u32: {parse_error}"`
for `ParseIntError`. Parsing the display of any version must return the
original value.

## Dependency Universes and Providers

The solver learns about packages exclusively through the
`DependencyProvider` trait. A provider fixes six associated types: `P`, the
package name type (any type that is cloneable, hashable, comparable, and
printable satisfies the `Package` trait automatically — the trait has a
blanket implementation and no methods of its own); `V`, the version type
(ordered, cloneable, printable); `VS`, the version-set type (a `VersionSet`
whose associated version type is `V`); `Priority`, an ordered cloneable
rank type; `M`, the unavailability-metadata type (comparable, cloneable,
printable); and `Err`, the provider's error type.

**Provider callbacks.** `prioritize(package, range, statistics)` returns a
priority; the solver always decides the package with the greatest priority
among those still undecided, and WHEN two packages tie THEN the solver
biases toward the package discovered earlier (breadth-first). The
`statistics` argument is a `PackageResolutionStatistics` for that package;
its `conflict_count()` method returns how many conflicts the package has
been involved in so far (a fresh, default-constructed statistics value
reports zero). Priorities are cached between constraint changes: the
solver re-asks only after the constraint on the package narrows or the
package's conflict statistics change. `choose_version(package,
range)` returns `Ok(Some(v))` to select a version inside `range`,
`Ok(None)` to declare that no version of the package satisfies `range`, or
`Err` to abort the solve. WHEN `choose_version` returns a version not
contained in `range` THEN the solver panics, naming the offending package
and version. `get_dependencies(package, version)` returns either
`Dependencies::Available(constraints)` — a `DependencyConstraints` map from
each required package to the version set it must satisfy, where an empty
map is the known fact "this version has no dependencies" — or
`Dependencies::Unavailable(reason)` with a caller-defined `M` value meaning
the dependencies of this version cannot be determined; the solver then
avoids that version and records the reason in the failure proof.
`should_cancel()` is polled once per decision cycle; returning an error
terminates the solve. Each version's dependencies are fetched at most once
per solve: WHEN the solver revisits a package version it has already
queried THEN it must not call `get_dependencies` for that pair again.

**Collection aliases.** The library's map and set aliases, `Map` and
`Set`, are the hash map and hash set from the `rustc-hash` crate (a
deterministic, unseeded hasher). `DependencyConstraints<P, VS>` is an alias
for `Map<P, VS>`, and `SelectedDependencies<DP>` — the solution type — is
an alias for `Map<DP::P, DP::V>`.

**The in-memory provider.** `OfflineDependencyProvider<P, VS>` implements
the trait over a registry held in memory. `new()` (and the `Default`
implementation) create an empty registry. `add_dependencies(package,
version, dependencies)` registers a package version together with its
complete constraint list in one call; the version parameter accepts
anything convertible into the version type, and the dependencies parameter
is any iterable of (package, version-set) pairs. Registering the same
package version again replaces its previous constraint list entirely.
`packages()` iterates the registered package names (no ordering
guarantee). `versions(package)` returns the registered versions of a
package sorted ascending, or `None` when the package is unknown.

The in-memory provider's strategy is fixed: `choose_version` returns the
highest registered version of the package contained in the given range
(`None` when the package is unknown or no registered version matches);
`get_dependencies` returns `Available` for every registered pair and
`Unavailable` with the exact message string
`"its dependencies could not be determined"` for every unregistered pair
(its metadata type `M` is `String` and its error type is infallible); and
`prioritize` ranks packages so that a package whose current constraint
matches none of its registered versions outranks every other package, and
otherwise packages with more recorded conflicts come first, with ties
broken so that fewer matching versions outrank more matching versions. Its
priority type is the pair `(u32, std::cmp::Reverse<usize>)`.

## Resolution

`resolve(provider, package, version)` solves the universe reachable from
the given root; the version argument accepts anything convertible into the
provider's version type.

**Success.** The result is a `SelectedDependencies` map holding exactly one
version per package. It must contain the root package at the requested
version, and for every entry it must contain every package required by that
entry's dependencies, each at a version contained in the requesting
constraint set. Packages never reached from the root must not appear.
Dependency cycles among packages are solvable normally, and a package
version whose constraints include the package itself is valid as long as
the selected version satisfies that self-constraint. One version serves
all dependents: WHEN two dependents constrain the same package THEN the
selected version must lie in the intersection of both sets, and WHEN the
provider's preferred (highest) version of one package contradicts another
requirement THEN the solver must backtrack and select a lower version that
removes the contradiction rather than fail.

**Determinism.** Repeated calls with the same universe, the same root, and
a deterministic provider must return the same solution or the same failure
proof, sentence for sentence.

**Failure.** WHEN the constraints cannot be satisfied THEN `resolve`
returns `PubGrubError::NoSolution` carrying a derivation tree (the type
alias `NoSolutionError` names the tree type for a given provider). WHEN
the root package/version pair itself is unknown to the provider THEN the
tree is the single external fact "no version of the root inside the
singleton set of the requested version".

**Provider-raised failures.** Errors from provider callbacks abort the
solve wrapped in a variant naming the callback: an error from
`choose_version` becomes `ErrorChoosingVersion` carrying the `package` and
the provider error as `source`; an error from `get_dependencies` becomes
`ErrorRetrievingDependencies` carrying `package`, `version`, and `source`;
an error from `should_cancel` becomes `ErrorInShouldCancel` carrying the
provider error. The error type displays fixed messages per variant:
`"There is no solution"` for `NoSolution`,
`"Choosing a version for {package} failed"` for `ErrorChoosingVersion`,
`"Retrieving dependencies of {package} {version} failed"` for
`ErrorRetrievingDependencies`, and `"The solver was cancelled"` for
`ErrorInShouldCancel`. Debug formatting renders the variant name with its
fields. A derivation tree converts into the error type via `From`,
producing the `NoSolution` variant.

**Solving discipline.** The solver works with incompatibilities — sets of
package terms that cannot all be true together. A `Term` is `Positive(set)`
(the package must be selected, at a version in the set) or `Negative(set)`
(the package must either be unselected or at a version in the set); terms
are cloneable, comparable, and display as the set itself for positive and
`"Not ( {set} )"` for negative. External incompatibilities enter the store
from provider facts: each dependency edge contributes "version set S of
package p requires package q in set T", an exhausted `choose_version`
contributes "no version of p in S", and an `Unavailable` answer
contributes the caller's reason. The solver alternates unit propagation
(deriving forced assignments from incompatibilities) with decisions
(selecting the chosen version of the highest-priority package). WHEN
propagation finds an incompatibility fully satisfied by the current
assignment THEN the solver resolves it against the incompatibility that
caused the last contributing assignment, producing a derived
incompatibility, and backtracks to the earliest level where that derived
incompatibility forces a new assignment. WHEN a derived incompatibility
with a positive term for the root package and no other term becomes
satisfied THEN solving has failed, and the chain of resolutions that
produced that incompatibility — each derived node holding its two causes —
is returned as the derivation tree.

## Failure Proofs: Derivation Trees

A derivation tree is a binary proof. `DerivationTree` has two variants:
`External`, a leaf holding an externally observable fact, and `Derived`, an
inner node holding a `Derived` record. Both the tree and its parts are
cloneable and debug-printable.

**External facts.** `External` has four variants. `NotRoot(package,
version)` states that solving is rooted at this package version (it
displays as `"we are solving dependencies of {package} {version}"` and is
available for callers building trees by hand; solver-produced trees do not
contain it). `NoVersions(package, set)` states that no version of
`package` exists inside `set`. `FromDependencyOf(p, s, q, t)` states that
every version of `p` in `s` requires `q` in `t`. `Custom(package, set,
metadata)` states that the versions of `package` in `set` are unusable for
the caller-supplied reason `metadata`.

**Displaying external facts.** `NoVersions` displays as
`"there is no available version for {package}"` WHEN its set is the full
set, and `"there is no version of {package} in {set}"` otherwise.
`Custom` displays as
`"dependencies of {package} are unavailable {metadata}"` WHEN its set is
the full set, and
`"dependencies of {package} at version {set} are unavailable {metadata}"`
otherwise. `FromDependencyOf(p, s, q, t)` displays by dropping full sets:
`"{p} depends on {q}"` when both sets are full,
`"{p} depends on {q} {t}"` when only `s` is full,
`"{p} {s} depends on {q}"` when only `t` is full, and
`"{p} {s} depends on {q} {t}"` when neither is.

**Derived nodes.** A `Derived` record has four public fields: `terms`, the
map from package to `Term` stating what this node proves impossible
together; `shared_id`, an optional numeric marker present when the same
derived incompatibility appears at several places in one tree (equal
markers identify the same node); and `cause1` and `cause2`, reference-
counted child trees. The terms of a derived node are the resolvent of its
two causes: the union of both causes' terms with the package resolved
between them eliminated (term union and intersection follow the positive/
negative semantics of `Term`).

**Whole-tree queries.** `packages()` returns the set of every package
named anywhere in the tree — both endpoints of each dependency fact, the
subject of each other external, and every package in each derived node's
terms. `collapse_no_versions()` simplifies the tree in place for callers
who know the provider saw every existing version: WHEN a derived node has
a `NoVersions` leaf as one cause THEN the node is replaced by the other
cause, first collapsed itself, with the `NoVersions` set folded into the
replacement when the replacement is a dependency fact — the set is unioned
into the fact's subject-package side when the packages match and into its
target-package side otherwise. A replacement that is itself a `NoVersions`
or a `Custom` leaf cannot absorb the set, and the original derived node is
kept unchanged in that case. External leaves and derived nodes without a
`NoVersions` cause collapse their children recursively.

## Failure Reports

The reporting layer turns a derivation tree into text.

**Traits.** `Reporter` declares an output type and two associated
functions: `report(tree)` renders with the default formatter, and
`report_with_formatter(tree, formatter)` renders with a caller-supplied
one; both must produce identical output when given the same formatting
rules. `ReportFormatter` is the sentence-level abstraction: it formats one
external fact (`format_external`), one terms map (`format_terms`), and the
five explanation shapes the reporter emits (`explain_both_external`,
`explain_both_ref`, `explain_ref_and_external`, `and_explain_external`,
`and_explain_ref`, `and_explain_prior_and_external`).

**The default formatter.** `DefaultStringReportFormatter` produces
strings. `format_external` is the external fact's display form.
`format_terms` renders a terms map by shape: an empty map renders as
`"version solving failed"`; a single positive term renders as
`"{package} {set} is forbidden"`; a single negative term renders as
`"{package} {set} is mandatory"`; a map of exactly one positive and one
negative term renders as the dependency sentence of "positive package in
its set requires the negative package in the negative term's set", in
that normalized order regardless of map order; any other map renders each
entry as `"{package} {term}"` joined by `", "` and suffixed
`" are incompatible"`. The explanation shapes produce:
`"Because {cause} and {cause}, {conclusion}."` for two fresh causes, and
`"And because {cause}, {conclusion}."` /
`"And because {cause} and {cause}, {conclusion}."` for continuation lines,
where an already-explained derived cause is cited as its terms rendering
followed by a parenthesized line reference (for example
`"mast 1.0.0 is forbidden (1)"`).

**The default reporter.** `DefaultStringReporter` renders a whole tree as
one string. WHEN the tree is a single external fact THEN the report is
exactly that fact's formatted form. Otherwise the reporter walks the proof
and joins its lines with newlines: two external causes produce one
`"Because … and …, …."` line; a derived cause chains with
`"And because …"` lines, folding a derived cause's own external prior
cause into the same line when possible; WHEN both causes are derived and
unreferenced THEN the reporter explains the first sub-proof, appends a
parenthesized reference number `" ({n})"` to its concluding line, emits an
empty line, explains the second sub-proof, and closes with an
`"And because … ({n}), …."` line citing the reference; and WHEN a derived
node carries a `shared_id` already assigned a reference THEN it is cited by
number instead of being re-explained. Reference numbers count up from 1 in
order of assignment within one report.

## State Model

The durable state of one solve is the pair (universe, fact store). The
universe is owned by the caller's provider and is read-only to the solver:
it is the map from package versions to constraint maps, exposed by
`OfflineDependencyProvider` through `packages`, `versions`, and its
`DependencyProvider` implementation. The fact store is the solver's growing
set of incompatibilities: seeded from the root, extended by provider
answers (dependency edges, exhausted ranges, unavailability reasons), and
closed under resolution when conflicts arise.

Public projections of that state: (1) the solution map returned on
success — one version per reachable package, consistent with every
constraint; (2) the derivation tree returned on failure — the resolution
sub-proof that ends in the root's impossibility, queryable via `packages`
and simplifiable via `collapse_no_versions`; (3) the report — a
deterministic text rendering of the tree through the formatter templates;
(4) the provider observation stream — the sequence of `prioritize`,
`choose_version`, `get_dependencies`, and `should_cancel` calls the solver
makes, whose call discipline (caching, at-most-once dependency fetches per
pair, per-cycle cancellation polls) is part of the contract; and (5) the
range algebra values exchanged everywhere, whose canonical form makes
equality and display stable across all other projections.

## Error Semantics

| Condition | Result |
|---|---|
| Constraints unsatisfiable | `PubGrubError::NoSolution(tree)`; error displays `"There is no solution"` |
| Root package/version unknown to provider | `NoSolution` whose tree is the single external `NoVersions(root, {version})` |
| `choose_version` returns `Err` | `PubGrubError::ErrorChoosingVersion { package, source }`; displays `"Choosing a version for {package} failed"` |
| `get_dependencies` returns `Err` | `PubGrubError::ErrorRetrievingDependencies { package, version, source }`; displays `"Retrieving dependencies of {package} {version} failed"` |
| `should_cancel` returns `Err` | `PubGrubError::ErrorInShouldCancel(source)`; displays `"The solver was cancelled"` |
| `choose_version` returns a version outside the given range | panic naming the package and version |
| Version string with more or fewer than three dot-separated parts | `VersionParseError::NotThreeParts { full_version }` |
| Version part not an unsigned 32-bit number | `VersionParseError::ParseIntError { full_version, version_part, parse_error }` |
| `contains_many`/`simplify` given unsorted versions | contract violation; results are unreliable (debug builds assert sortedness) |

## Cross-View Invariants

1. For every successful solve, every entry of the solution map satisfies
   the provider view: the root pair is present, and for each selected
   version, every package in its constraint map is selected at a version
   the constraint set `contains`.
2. On failure, the report must mention only packages returned by the
   tree's `packages()` query, and every package in `packages()` of a
   solver-produced tree appears in the report text.
3. Range algebra and display agree: two `Ranges` values compare equal
   exactly when their canonical segment sequences are identical, and equal
   values render identical display strings across every context (bare,
   inside external facts, inside terms, inside reports).
4. Version display and parsing are inverse: `SemanticVersion` parsing of
   any version's display returns the original value, and the display of
   parsed input equals the input for every valid three-part version
   string.
5. `collapse_no_versions` preserves the proof's conclusion: the collapsed
   tree of a solver failure still proves the same root impossibility, its
   report still names the root package, and collapsing removes only
   `NoVersions` sentences that were folded into surviving dependency
   facts.
6. Solver determinism spans projections: repeated solves of one universe
   yield identical solution maps on success, and identical derivation
   trees (up to shared reference numbering) with character-identical
   reports on failure.
7. Provider strategy is visible in solutions: with the in-memory provider,
   the selected version of every package is the highest registered version
   satisfying the intersection of all constraint sets that requested that
   package in the final solution.

## Public Interface

### Import Surface

```rust
use pubgrub::{
    // solving
    resolve, DependencyProvider, Dependencies, PackageResolutionStatistics,
    OfflineDependencyProvider,
    // packages, versions, sets
    Package, VersionSet, Ranges, SemanticVersion, VersionParseError,
    // aliases
    Map, Set, DependencyConstraints, SelectedDependencies, NoSolutionError,
    // failure model
    PubGrubError, Term, DerivationTree, Derived, External,
    // reporting
    Reporter, ReportFormatter, DefaultStringReporter,
    DefaultStringReportFormatter,
};
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `resolve` | function | Solve a universe from a root package/version; returns the solution map or a `PubGrubError` |
| `DependencyProvider` | trait | Caller-implemented universe: associated types `P`, `V`, `VS`, `Priority`, `M`, `Err`; methods `prioritize`, `choose_version`, `get_dependencies`, `should_cancel` |
| `Dependencies` | enum | Answer of `get_dependencies`: `Available(constraints)` or `Unavailable(reason)` |
| `PackageResolutionStatistics` | struct | Per-package conflict counters passed to `prioritize`; `conflict_count()` |
| `OfflineDependencyProvider` | struct | In-memory provider: `new`, `add_dependencies`, `packages`, `versions`, fixed highest-version/fewest-candidates strategy |
| `Package` | trait | Marker for package name types; blanket-implemented over clone/hash/eq/debug/display types |
| `VersionSet` | trait | Set-algebra abstraction over versions; `empty`, `singleton`, `complement`, `intersection`, `contains`, with derived `full`, `union`, `is_disjoint`, `subset_of` |
| `Ranges` | struct | Canonical interval-set implementation of `VersionSet` with constructors, algebra, queries, simplification, iteration, and comparator-notation display |
| `SemanticVersion` | struct | major.minor.patch version value; constructors, bumps, tuple conversions, parse/display |
| `VersionParseError` | enum | Version-string parse failure: `NotThreeParts`, `ParseIntError` |
| `Map` | type alias | Deterministic hash map used across the API |
| `Set` | type alias | Deterministic hash set used across the API |
| `DependencyConstraints` | type alias | Map from package to required version set |
| `SelectedDependencies` | type alias | Solution map from package to selected version |
| `NoSolutionError` | type alias | Derivation tree type of a provider's failure proof |
| `PubGrubError` | enum | Solve failure: `NoSolution`, `ErrorRetrievingDependencies`, `ErrorChoosingVersion`, `ErrorInShouldCancel` |
| `Term` | enum | `Positive(set)` / `Negative(set)` statement about one package |
| `DerivationTree` | enum | Failure proof node: `External` leaf or `Derived` inner node; `packages`, `collapse_no_versions` |
| `Derived` | struct | Inner proof node: `terms`, `shared_id`, `cause1`, `cause2` |
| `External` | enum | Leaf fact: `NotRoot`, `NoVersions`, `FromDependencyOf`, `Custom`; sentence-form display |
| `Reporter` | trait | Tree-to-output rendering entry: `report`, `report_with_formatter` |
| `ReportFormatter` | trait | Sentence-level formatting hooks used by the reporter |
| `DefaultStringReporter` | struct | Default reporter producing chained-sentence `String` reports with line references |
| `DefaultStringReportFormatter` | struct | Default sentence formatter (`format_external`, `format_terms`, explanation templates) |

### CLI Entry Points

There is no console script for this crate. Programmatic use is through the
Rust library API.

## Appendix A: Environment

- Language: Rust, edition 2021 (toolchain 1.83; the crate's declared
  minimum supported Rust version must not exceed it).
- The crate must build as `pubgrub` with its default configuration
  providing every behavior described here; the assessment suite depends on
  the crate as `pubgrub = { version = "*" }`.
- The version-set container described in Version Set Algebra must be
  reachable at the crate root as `pubgrub::Ranges` regardless of where it
  is implemented.
- Tests are run with cargo-nextest; each test runs in its own process.
- No network access at test time.

## Appendix B: Assessment Notes

The assessment exercises the public API through its documented behavior.
Dimensions covered:

- Range algebra: constructors, canonical normalization and equality, set
  operations and their laws, membership and bulk membership, singleton and
  bounding queries, simplification rules, segment iteration, and the
  display grammar.
- Versions: construction, ordering, bumping, tuple conversions, display,
  and both parse-failure classes with their payload fields and messages.
- Providers: the in-memory registry (registration replacement, package and
  sorted-version listings), its fixed selection strategy, its
  unavailability message, priority ordering relations, and the callback
  and error contracts of custom providers.
- Resolution: solution-map correctness across chains, diamonds, cycles,
  self-constraints, backtracking universes, and version-intersection
  scenarios; determinism; wrapped provider errors; cancellation.
- Failure proofs: derivation tree structure (external variants, derived
  records, shared markers), package queries, collapse semantics, and
  external sentence forms.
- Reports: terms-map formatting shapes, explanation templates, sentence
  chaining, line references, blank-line separation, and end-to-end report
  text for probed failure universes.

Scoring runs the full test suite against the delivered crate; each test
carries equal weight within its layer. Integration tests combine at least
two behavior domains (for example, solving plus report rendering, or range
algebra plus provider strategy).
