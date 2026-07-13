# MiniPackaging Public Product Packet

## Overview

Build `minipackaging.py`, a dependency-free Python module for parsing and evaluating a practical subset of Python package metadata. The task is inspired by `pypa/packaging` and the PEP 440 / PEP 508 behavior that package installers rely on, but it is intentionally scoped as a compact benchmark implementation.

The module must be importable from the solution directory:

```python
from minipackaging import (
    Version,
    InvalidVersion,
    SpecifierSet,
    InvalidSpecifier,
    Requirement,
    InvalidRequirement,
    Marker,
    InvalidMarker,
    UndefinedEnvironmentName,
    default_environment,
    is_requirement_satisfied,
    MetadataIndex,
    resolve_metadata,
)
```

Use only the Python standard library.

## Feature Set

The product has eight feature modules:

1. Version parsing, normalization, and ordering.
2. Version specifier parsing and membership checks.
3. Requirement string parsing and canonical serialization.
4. Environment marker parsing and evaluation.
5. Environment dictionary construction and validation.
6. Requirement satisfaction across installed version, markers, and requested extras.
7. Local candidate metadata resolution and projection.
8. Persistent local metadata indexing across candidate add, update, remove, export/import, reverse-query, and lock replay workflows.

These modules are intentionally state-dependent. Requirement strings embed specifiers, markers, URLs, and extras in one grammar. Specifier checks operate on normalized version objects. Marker comparisons may compare version-valued environment fields with PEP 440 ordering. Extras are normalized in both requirement parsing and marker evaluation. The satisfaction helper must compose all parsed pieces without changing their individual meanings.

The public `resolve_metadata()` API assembles local candidate metadata from these public objects to check dependency resolution invariants. A candidate record names one distribution version and its outgoing requirement strings. Selected versions, dependency edges, reverse dependents, requested extras, active requirements, and excluded candidate versions must all be derivable from the same parsed requirement, marker, extras, specifier, and version semantics. Resolver and projection checks compare those semantic fields directly: normalized names, extras, markers, selected versions, specifier membership, dependency edges, reverse dependents, requested extras, active requirement facts, exclusions, and permutation-invariant results. Full requirement string formatting is a separate serialization concern and is not the identity of a resolver edge or constraint. Requirement equality/hash behavior and invalid direct URL plus specifier rejection are public unit-level contracts; system cases count them only when the defect changes downstream selected versions, dependency edges, reverse dependents, requested extras, active requirements, exclusions, marker applicability, extras propagation, atomic recovery, or permutation equality. These derived views must agree even when root requirements and candidate records are supplied in different orders.

The public `MetadataIndex` API keeps that same candidate metadata in a revisioned local fact table. It is a small, persistent metadata cache rather than a one-shot resolver. Adding, updating, removing, exporting, importing, resolving, reverse-querying, producing local lock snapshots, and applying those lock snapshots must all project from the same normalized candidate table. This lifecycle is intentionally local: it does not download packages, write installer lockfiles, or implement pip backtracking. Its purpose is to ensure the resolver graph, reverse dependents, requested extras, excluded versions, local locks, and replayed exported state stay consistent as metadata changes over time.

## Global Invariants

The following invariants define system correctness:

- Every public path that accepts a version string must apply the same version normalization and ordering rules.
- Requirement parsing must keep package name, extras, URL, specifier, and marker fields distinct even when they are serialized back into one requirement string.
- Requirement equality and hashing must use normalized semantic fields: normalized name, sorted normalized extras, semantic specifier clauses, URL, and marker semantics. Equivalent constraint spellings must not remain distinct merely because their input whitespace, release zeros, name punctuation, extras order, or specifier clause order differed. This primitive identity behavior is tested once directly and is not multiplied into system failures unless a downstream metadata projection diverges.
- Canonical `Requirement.__str__` output is public serialization behavior, but resolver, projection, and graph invariants use parsed fields rather than whitespace-sensitive full requirement strings.
- Direct URL requirements can appear in the same dependency metadata as extras and environment markers. URL edges still participate in marker applicability, extras propagation, dependency-edge projection, and reverse-dependent projection, while remaining distinct from version specifier constraints.
- Extras must be normalized consistently across requirement extras, requested extras, and the `extra` marker variable.
- Marker evaluation must use the environment supplied by the caller and must not silently invent missing variables.
- Version-valued marker comparisons must use the same ordering semantics as `Version` and `SpecifierSet`.
- Resolution must be deterministic under candidate-order and root-requirement-order permutation. When multiple candidate versions satisfy all active constraints for one normalized project name, the highest `Version` wins.
- Multiple equivalent requirement spellings for the same project must converge to one semantic constraint set before graph projections are derived. Multiple non-equivalent active constraints for the same project are conjunctive, whether they came from roots or transitive dependency metadata.
- Dependency edges and reverse dependents must be bidirectional projections of the same applicable requirement facts.
- `selected`, `excluded`, `edges`, `dependents`, `requested_extras`, and `requirements` returned by `resolve_metadata()` must be projections of one shared metadata fact source, not independently recomputed summaries that can disagree.
- `MetadataIndex.resolve()` must return the same semantic resolver projections plus its current `revision` and deterministic stored `index` projection. The convenience `resolve_metadata()` function preserves the resolver-only projection shape for callers that do not need lifecycle metadata.
- `MetadataIndex.resolve_lock()` must freeze a JSON-safe lock snapshot from the same resolver facts returned by `resolve()`: revision, roots, selected versions, dependency edges, reverse dependents, requested extras, active requirements, exclusions, and the stored-candidate projection used to produce them.
- `MetadataIndex.apply_lock(lock, ...)` must replay a public lock snapshot against the current index without changing the index. It returns resolver-style projections constrained to the locked selected versions when the stored metadata still supports the locked active requirement graph, and raises `ValueError` when a selected candidate is missing, its applicable dependency metadata no longer matches the lock, or the caller environment/requested extras would activate a different graph. Exact message text is not public.
- `MetadataIndex.add_candidate()`, `remove_candidate()`, `resolve_lock()`, `apply_lock()`, and `apply()` must copy caller metadata before storing or replaying it. Later caller mutations to candidate dictionaries, `requires` lists, lock dictionaries, or lock lists must not change the index or replay result.
- `MetadataIndex.apply(changes)` is atomic. If any change is invalid, the revision, stored candidates, exported state, and later resolver projections must remain unchanged.
- `MetadataIndex.export_state()` and `MetadataIndex.import_state(state)` must round-trip the public semantic state: stored candidates, revision, later resolver snapshots, reverse dependent queries, and lock replay behavior.
- `MetadataIndex.dependents_of(name, roots=None, transitive=False, **resolve_options)` must be a reverse projection of the same active dependency graph used by `resolve()`.
- Cached or indexed projections must be invalidated after every successful add, update, remove, import, or batch apply. No later `resolve()`, `resolve_lock()`, `apply_lock()`, `dependents_of()`, `index()`, or `export_state()` call may expose stale candidate metadata, stale dependency edges, stale exclusions, stale requested extras, or stale reverse dependents.
- Excluded candidate versions must be disjoint from selected versions and must be computed from the same normalized name, version, specifier, marker, and extras semantics as selection.
- Conflicting root and transitive constraints must exclude the same candidate versions in every candidate-order and root-order permutation, and reverse dependents must still identify the packages whose applicable dependency metadata introduced the child constraint.
- Environment-sensitive metadata must be evaluated consistently across markers embedded in root requirements, candidate dependency requirements, and requirement satisfaction checks.
- Optional dependency markers involving `extra` must use the requested extras for the distribution whose candidate declared that dependency; dependency requirements with extras request those extras from the child distribution.
- Failed parsing or failed evaluation must not corrupt already-created `Version`, `SpecifierSet`, `Requirement`, or `Marker` objects, caller-owned environment dictionaries, or candidate metadata lists. Invalid dependency metadata such as a requirement that combines a direct URL with a version specifier must be rejected by the requirement parser. System atomicity checks focus on whether the failed or tolerated parse corrupts caller inputs or prevents a later valid evaluation from producing the correct projections.
- Requirement satisfaction is true only when all applicable pieces agree: the requirement can be parsed, its marker is applicable in the provided environment and requested extras, and the installed version satisfies the specifier.

## Data Model

### Version

`Version(text)` parses a PEP 440 style version string. The implementation must support:

- optional epoch with `!`;
- release segments separated by dots;
- pre-release spellings `a`, `alpha`, `b`, `beta`, `rc`, `c`, `pre`, and `preview`;
- post-release spellings `post`, `rev`, and `r`;
- dev releases using `dev`;
- local version labels after `+`, split on `.`, `_`, or `-`;
- case-insensitive parsing with canonical lower-case serialization.

Release trailing zeros are ignored for equality and ordering. Canonical string output omits redundant release trailing zeros except when a single zero release remains. Pre-release spellings normalize to `a`, `b`, or `rc`; post-release spellings normalize to `post`; local labels normalize to lower-case dot-separated components.

Ordering must follow the practical PEP 440 sequence for the supported subset: epoch, release tuple, dev release, pre-release, final release, post-release, and then local label. Local labels affect ordering only when the public version is otherwise equal. Numeric local components sort after non-numeric local components at the same position; numeric components compare numerically and text components lexicographically.

Invalid version strings raise `InvalidVersion`, a `ValueError` subclass.

### SpecifierSet

`SpecifierSet(text)` parses a comma-separated set of specifier clauses. Supported operators are:

- `==`
- `!=`
- `>=`
- `<=`
- `>`
- `<`
- `~=`

Whitespace around clauses is ignored. Each non-wildcard clause contains a supported `Version`. `==` and `!=` may also use a trailing `.*` wildcard against release prefixes. `~=` means compatible release: the lower bound is inclusive at the given version and the upper bound is exclusive at the next appropriate release segment.

`specifier.contains(version, prereleases=None)` returns whether a version string or `Version` object satisfies all clauses. Unless `prereleases` is true, pre-release and dev-release candidates are excluded when the candidate would otherwise satisfy only final-release bounds. If `prereleases` is false, they are always excluded. If `prereleases` is true, they are considered normally.

`str(specifier)` returns a comma-separated canonical representation of the clauses in their input order. Invalid specifiers raise `InvalidSpecifier`, a `ValueError` subclass.

### Requirement

`Requirement(text)` parses a PEP 508 style requirement string. It must expose:

- `name`, the original distribution name text normalized by replacing underscores with hyphens and lowercasing;
- `extras`, a `set[str]` of normalized extra names;
- `specifier`, a `SpecifierSet`;
- `url`, a string or `None`;
- `marker`, a `Marker` or `None`.

Supported requirement forms include a distribution name, optional extras in square brackets, optional version specifiers, optional direct URL introduced by `@`, and optional marker introduced by `;`.

Names and extras accept ASCII letters, digits, `.`, `_`, and `-`, but must start and end with an ASCII letter or digit. Extras are comma-separated and normalized like names. A requirement cannot contain both a direct URL and a version specifier. Invalid requirement strings raise `InvalidRequirement`, a `ValueError` subclass.

`str(requirement)` returns a canonical requirement string: normalized name, sorted extras, canonical specifier or URL if present, and canonical marker if present.

### Marker

`Marker(text)` parses and evaluates environment marker expressions. Supported variables are:

- `python_version`
- `python_full_version`
- `os_name`
- `sys_platform`
- `platform_machine`
- `platform_system`
- `platform_release`
- `platform_version`
- `platform_python_implementation`
- `implementation_name`
- `implementation_version`
- `extra`

Supported operators are `==`, `!=`, `<`, `<=`, `>`, `>=`, `in`, and `not in`. Single-quoted and double-quoted string literals are supported. Parentheses, `and`, and `or` are supported with the usual precedence: parentheses first, then `and`, then `or`.

`marker.evaluate(environment=None, requested_extras=None)` returns a boolean. When no environment is supplied, it uses `default_environment()`. The supplied environment is copied before evaluation. Missing variables raise `UndefinedEnvironmentName`, a `ValueError` subclass. Syntax errors raise `InvalidMarker`, a `ValueError` subclass.

Comparisons involving version-valued variables use `Version` ordering when both sides can be parsed as versions. Other comparisons use string comparison for equality and membership. The `extra` variable is special: when `requested_extras` is omitted or empty, it evaluates as an empty string; when one or more requested extras are supplied, a marker expression involving `extra` is true if it is true for at least one normalized requested extra.

`str(marker)` returns a canonical expression preserving the parsed boolean structure with normalized variable names and normalized extra literals.

### Environment

`default_environment()` returns a dictionary containing every supported marker variable except `extra`. Values must be strings. The function may derive values from `sys`, `os`, and `platform`, but callers can override any variable by passing an environment dictionary to marker evaluation or requirement satisfaction.

### Requirement Satisfaction

`is_requirement_satisfied(requirement, installed_version, environment=None, requested_extras=None, prereleases=None)` returns a boolean. `requirement` may be a requirement string or a `Requirement` object. `installed_version` may be a version string or a `Version` object.

The helper evaluates the requirement marker first. If the marker is present and not applicable in the environment and requested extras, the requirement is considered satisfied because it does not apply. If the marker applies, the installed version must satisfy the requirement's specifier. Requirement extras do not by themselves change version satisfaction; they are preserved as part of the parsed requirement target. Requested extras are used only for marker expressions involving `extra`.

Invalid requirement strings, invalid versions, invalid markers, and missing marker environment variables should raise the same public exception types as their underlying feature modules.

### Dependency Metadata Invariants

The public API includes a local metadata resolver:

```python
resolve_metadata(roots, candidates, environment=None, requested_extras=None, prereleases=None)
```

`roots` is an iterable of requirement strings or `Requirement` objects. `candidates` is an iterable of mapping objects. Each candidate mapping must contain `name` and `version`; it may also contain `requires`, an iterable of outgoing requirement strings. The function must not mutate the caller's root objects, environment dictionary, candidate mappings, or candidate `requires` lists.

The resolver is deterministic and metadata-only. It does not download packages, query indexes, choose build artifacts, emit lockfiles, or implement installer backtracking. It repeatedly applies active root and dependency requirements to the supplied candidate records until no new applicable dependency facts appear. For each active normalized project name, all active specifiers are conjunctive, and the selected candidate is the highest supplied `Version` satisfying every active specifier. If an active project has no satisfying candidate, the function raises `ValueError` or a documented public parse/evaluation exception from the primitive that failed; exact message text is not public.

The return value is a dictionary containing these public semantic projections:

- `selected`: mapping from normalized project name to canonical selected version string.
- `excluded`: mapping from active normalized project name to sorted canonical version strings for supplied candidates that were not selected. Projects with no excluded versions may be omitted.
- `edges`: a deterministic list of active dependency edge mappings. Each edge contains `parent`, `name`, `extras`, `specifier`, `url`, `marker`, `marker_applicable`, and `specifier_matches`. `parent` and `name` are normalized project names; `extras` is sorted normalized extras requested on the child; `specifier` is the canonical specifier string; `url` and `marker` are strings or `None`; `marker_applicable` is `True` for active edges; `specifier_matches` is a deterministic list of `(version, matches)` pairs for supplied candidate versions of the child project.
- `dependents`: mapping from child normalized project name to sorted unique parent names, derived from `edges`.
- `requested_extras`: mapping from every active normalized project name to sorted normalized extras requested for that project by roots or dependency edges.
- `requirements`: a deterministic list of active requirement fact mappings. Each fact contains `source`, `parent`, `name`, `extras`, `specifier`, `url`, `marker`, and `marker_applicable`. Root facts use `source == "root"` and `parent is None`; dependency facts use the normalized parent project name for both `source` and `parent`.

Lists and tuples are both acceptable for sequence-valued fields, but their semantic contents must be deterministic. Callers should be able to compare the normalized fields above without inspecting private objects or exact whitespace in requirement strings.

For such metadata, the following semantics are part of the public contract:

- candidate names normalize exactly like `Requirement.name`;
- candidate versions compare exactly like `Version`;
- root requirement markers use the caller environment and top-level requested extras;
- outgoing dependency markers use the caller environment and the requested extras of the parent distribution;
- extras on an applicable dependency requirement become requested extras for the child distribution;
- active specifiers and exclusions for the same normalized project are conjunctive;
- among satisfying candidates for one normalized project, the highest `Version` is the deterministic selection;
- dependency edges, reverse dependents, requested extras, active requirements, and excluded candidate versions are projections of the same active requirement facts.

These semantics are intentionally local and metadata-only. They do not require network access, package downloads, lockfile output, or full installer backtracking.

### Persistent Metadata Index

The public API also includes a local metadata index:

```python
idx = MetadataIndex(candidates=())
idx.add_candidate({"name": "demo", "version": "1.0", "requires": ["dep>=1"]})
idx.remove_candidate("demo", "1.0")
idx.apply([{"action": "add", "candidate": {...}}, {"action": "remove", "name": "old", "version": "1"}])
snapshot = idx.resolve(["demo"])
parents = idx.dependents_of("dep", roots=["demo"], transitive=True)
lock = idx.resolve_lock(["demo"])
locked_snapshot = idx.apply_lock(lock)
state = idx.export_state()
idx2 = MetadataIndex.import_state(state)
```

Candidate mappings use the same `name`, `version`, and optional `requires` fields as `resolve_metadata()`. `add_candidate()` adds or replaces one normalized name/version record and increments `revision`. `remove_candidate()` removes one normalized name/version record and increments `revision`. `apply(changes)` applies a batch atomically and increments `revision` once when it succeeds. Supported change actions are:

- `{"action": "add", "candidate": candidate_mapping}`
- `{"action": "update", "candidate": candidate_mapping}`
- `{"action": "remove", "name": name, "version": version}`

`update` replaces an existing normalized name/version record and is invalid when that record does not already exist. `add` may insert a new record or replace an existing one. `remove` is invalid when the normalized name/version record is absent. Invalid candidate mappings, invalid dependency requirements, unknown change actions, missing update/remove targets, and invalid lock snapshots raise `ValueError` or the documented primitive parse/evaluation exception that rejected the data. Exact message text is not public. Failed single-candidate mutations and failed batches must leave the revision, stored candidates, exported state, and later resolver projections unchanged.

`idx.index()` returns a deterministic plain-data projection of stored candidates grouped by normalized project name. The projection is a dictionary whose keys are normalized project names and whose values are lists of candidate dictionaries sorted by `Version` ascending. Each candidate dictionary contains canonical `name`, canonical `version`, and `requires`, where `requires` is a copied list of the stored requirement strings in their declared order. Projects with no stored candidates are omitted.

`idx.resolve(...)` returns the resolver projections documented above plus:

- `revision`: the current integer revision of the index.
- `index`: the deterministic stored-candidate projection returned by `idx.index()`.

`idx.dependents_of(name, roots=None, transitive=False, **resolve_options)` resolves the active graph and returns sorted normalized parent project names that depend on `name`. If `roots` is omitted, every stored project name is considered a root. With `transitive=True`, parents of parents are included.

`resolve_lock(roots, environment=None, requested_extras=None, prereleases=None)` returns a JSON-safe dictionary containing the current `revision`, canonical root requirement facts, resolver projections, and stored-candidate projection needed to replay the selected graph. The lock is a local semantic snapshot, not a pip-compatible lockfile. Applying the same lock to the same exported/imported index must produce the same selected versions, dependency edges, reverse dependents, requested extras, active requirements, and exclusions. Applying the lock after unrelated candidate additions must keep the locked selected versions. Applying the lock after a selected candidate is removed or its applicable dependency metadata changes must raise `ValueError` without changing the index.

`apply_lock(lock, environment=None, requested_extras=None, prereleases=None)` validates and replays a lock snapshot against the current index. The returned dictionary contains the resolver projections for the locked graph plus `revision`, `lock_revision`, and `index`. It must use the caller environment and requested extras consistently with marker evaluation; a lock created for one environment must not silently reuse stale marker decisions in another environment.

`export_state()` returns a JSON-safe dictionary containing `revision` and stored candidate records. `MetadataIndex.import_state(state)` reconstructs an index that produces the same `index()`, resolver snapshots, reverse dependent queries, and lock replay behavior. Export/import must not rely on private Python object identity.

## Commands / API

The public API is class-based and function-based:

- `Version(text)`
- `SpecifierSet(text="")`
- `SpecifierSet.contains(version, prereleases=None)`
- `Requirement(text)`
- `Marker(text)`
- `Marker.evaluate(environment=None, requested_extras=None)`
- `default_environment()`
- `is_requirement_satisfied(requirement, installed_version, environment=None, requested_extras=None, prereleases=None)`
- `MetadataIndex(candidates=())`
- `MetadataIndex.index()`
- `MetadataIndex.add_candidate(candidate)`
- `MetadataIndex.remove_candidate(name, version)`
- `MetadataIndex.apply(changes)`
- `MetadataIndex.resolve(roots, environment=None, requested_extras=None, prereleases=None)`
- `MetadataIndex.dependents_of(name, roots=None, transitive=False, **resolve_options)`
- `MetadataIndex.resolve_lock(roots, environment=None, requested_extras=None, prereleases=None)`
- `MetadataIndex.apply_lock(lock, environment=None, requested_extras=None, prereleases=None)`
- `MetadataIndex.export_state()`
- `MetadataIndex.import_state(state)`
- `resolve_metadata(roots, candidates, environment=None, requested_extras=None, prereleases=None)`

Objects must be reusable. Calling `contains()`, `evaluate()`, `is_requirement_satisfied()`, `resolve_metadata()`, `MetadataIndex.resolve()`, `dependents_of()`, `resolve_lock()`, `apply_lock()`, or `export_state()` must not mutate parsed objects, lock dictionaries, or caller-owned metadata. `MetadataIndex` mutation methods must mutate only the index's own copied fact table.

## Error Behavior

Invalid input raises the documented public exception class for the feature that rejected it. Exact message text is not public API.

Parsing failures must be atomic: a failed parse must not alter existing objects or module-level state. Evaluation failures caused by missing environment keys must not alter the caller's environment dictionary or any parsed marker object. Failed `MetadataIndex` add, update, remove, batch apply, and lock apply operations must leave the stored candidates, revision, export output, and later resolver projections unchanged.

## Non-Goals

Do not implement the entire `packaging` project. Do not implement wheel tags, metadata validation, license parsing, dependency groups, canonical project URLs, pip-compatible lockfile generation, network index access, download behavior, build isolation, backtracking heuristics, or full installer behavior. The goal is a practical, deterministic subset of package version, specifier, requirement, marker, extras, environment, and local candidate metadata semantics with a local JSON-safe lock snapshot lifecycle.

## Evaluation Style

Hidden tests are split into two scores:

- Unit tests exercise one feature module at a time. Unit setup for a feature uses only that feature's public operations or direct construction of the object under test.
- System tests exercise interactions across at least two modules through the public `resolve_metadata()` and `MetadataIndex` APIs. They inspect invariant relationships among parsed names, extras, markers, specifier membership, selected versions, dependency edges, reverse dependents, requested extras, active requirements, excluded versions, object reuse, incremental updates, atomic rollback, export/import replay, and recovery after errors. Canonical requirement-string assertions, primitive requirement equality/hash checks, and bare invalid-syntax rejection belong in unit tests or a narrow serialization/round-trip case, not as repeated checks inside resolver and graph projections. A system test should not be passable by hard-coding one final boolean without preserving the shared metadata projections, and it should fail only when an actual downstream projection diverges.

System tests are labeled by dimension:

- `cross_feature_dataflow`
- `projection_consistency`
- `state_accumulation`
- `global_invariant`
- `error_atomicity`
- `operation_order_sensitivity`
- `ordering_invariance`
- `bidirectional_consistency`
- `boundary_crossing`

The benchmark does not inspect private implementation details.
