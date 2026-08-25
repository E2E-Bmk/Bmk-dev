# Packaging Core Utilities Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

Build an installable Python package named `packaging`.

The package provides reusable Python APIs for packaging interoperability:
version parsing and ordering, version specifiers, dependency markers,
requirement strings, wheel tags, distribution metadata, direct URL records,
dependency groups, pylock files, SPDX license expressions, and filename/name
utilities.

The package is library-only. It has no required network access, database,
background service, CLI command, build backend, installer, or resolver.

## Non-Goals

- This specification does not require Package installers, dependency resolvers, wheel builders, index clients, or network downloaders.
- This specification does not require Access to remote package indexes, version-control hosts, the local interpreter package database, or the filesystem except where an API explicitly accepts or returns a path-like value.
- This specification does not require Private modules whose names start with `_`.
- This specification does not require Platform-specific binary inspection helpers as public API.
- This specification does not require Exact internal parser trees and private dataclass layouts beyond the public attributes or behavior described here.

## Representative Workflows

### Parse a requirement, check version membership, and evaluate markers

```python
from packaging.requirements import Requirement
from packaging.version import Version
from packaging.markers import default_environment

req = Requirement("requests[security]>=2.20.0; python_version>='3.8'")
assert req.name == "requests"
assert "security" in req.extras

candidate = Version("2.28.1")
assert candidate in req.specifier

env = default_environment()
env["python_version"] = "3.10"
assert req.marker.evaluate(env) is True
```

Parsing a dependency string into `Requirement` exposes the project name, extras, specifier set, and marker. A candidate `Version` participates in specifier membership checks. The marker evaluates against an explicit environment mapping, and the same requirement can appear in metadata, dependency groups, and pylock entries with consistent normalized behavior.

### Parse a wheel filename and compare tags

```python
from packaging.utils import parse_wheel_filename, canonicalize_name
from packaging.tags import parse_tag, Tag

name, version, build, tags = parse_wheel_filename(
    "requests-2.28.1-py3-none-any.whl"
)
assert canonicalize_name("Requests") == name
assert str(version) == "2.28.1"
assert Tag("py3", "none", "any") in tags

parsed_tags = parse_tag("py3-none-any")
assert tags == parsed_tags
```

`parse_wheel_filename` extracts the normalized distribution name, `Version`, build tag, and compatibility tags from a wheel filename. Those `Tag` objects compare consistently with tags returned by `parse_tag()` and interpreter tag generators. Malformed filenames raise `InvalidWheelFilename`, and unsorted tag groups raise `UnsortedTagsError` when order validation is enabled.

## Version Handling

Version parsing and comparison implement PEP 440 version semantics for Python packaging interoperability.

**Parsing and normalization.** Creating a `Version` from a version string must parse the string according to PEP 440 rules. The `parse` function must return a `Version` from a version string, so `parse("v1.0-rc1")` must produce the same object as `Version("1.0rc1")`. Passing invalid version text to either must raise `InvalidVersion`. The `str()` representation of a version must return the normalized public version string; for example, `str(Version("1!2.3rc1.post2.dev3+ABC"))` must produce `"1!2.3rc1.post2.dev3+abc"`.

**Ordering.** Versions must compare according to PEP 440 ordering, not lexical string ordering. Pre-releases must sort before the corresponding final release. Post-releases must sort after their base release. Development releases must sort before the release they develop toward. Epochs must take precedence over release segments. Local versions must participate in ordering only where PEP 440 defines their comparison. Versions must be hashable and sortable with normal Python comparison operators.

**Component access.** A `Version` must expose `epoch` as an integer, `release` as a tuple of integer release components, `pre` as a tuple of phase name and number or `None`, `post` as an integer or `None`, `dev` as an integer or `None`, and `local` as a normalized local version string or `None`. The `public` property must return the public version string without the local segment. The `base_version` property must return the version without pre, post, dev, or local suffixes. The `is_prerelease`, `is_postrelease`, and `is_devrelease` boolean properties must report whether the corresponding segment is present.

**Convenience properties.** The `major`, `minor`, and `micro` properties must be derived from release components, with missing components treated as zero. A version with a single release component such as `"7"` must report `major` as `7` and `minor` and `micro` as `0`.

**Pre-release normalization.** `normalize_pre` must normalize pre-release spellings to canonical PEP 440 phase names. For example, passing `"preview"` must return `"rc"`.

**Version pattern.** `VERSION_PATTERN` must be a public regular-expression pattern string for recognizing the PEP 440 version grammar, suitable for embedding in larger regular expressions.

## Specifiers

Specifiers represent version constraints that determine whether a candidate version is acceptable.

**Parsing.** A `Specifier` must be created from a single version constraint string. A `SpecifierSet` must be created from a comma-separated string of constraints. Invalid specifier text must raise `InvalidSpecifier`. Supported operators must include `~=`, `==`, `!=`, `<=`, `>=`, `<`, `>`, and arbitrary equality `===`.

**Comparison and hashing.** Specifier and specifier-set objects must compare and hash by their normalized semantic content. They must be printable and repr-able in normalized form.

**Membership testing.** Specifier and specifier-set objects must support membership tests with `Version` objects and version strings using the `in` operator. The `contains` method must accept a version and optional `prereleases` and `installed` overrides.

**Pre-release handling.** Pre-release handling must follow PEP 440: pre-releases must be normally excluded unless the specifier explicitly admits them, the caller enables them via `prereleases`, or no final release candidate from the input can satisfy the set. A `Specifier` created with `prereleases` set to `True` must include pre-release versions in membership tests. The compatible release operator `~=` must accept versions within the compatible release range and reject versions outside it; for example, `~=1.4` must accept `"1.9"` but reject `"2.0"`.

**Filtering.** The `filter` method must yield items from an iterable whose versions satisfy the specifier set. When `key` is provided, it must extract a version string or `Version` from each item before filtering. Filtering must preserve input item type where possible; a string version that passes may be yielded as the original string rather than converted to a `Version`.

**Combination and iteration.** `SpecifierSet` must support `&` and `&=` combination with another specifier set or a specifier string. Iterating over a `SpecifierSet` must yield individual `Specifier` objects. A combined set must enforce both original and added constraints.

**Unsatisfiability.** `is_unsatisfiable()` must return `True` when the constraint set cannot be satisfied, such as `">=2,<1"`, and `False` otherwise.

**Range conversion.** `to_range()` must return a `VersionRange` view of the accepted versions.

## Version Ranges

`VersionRange` provides set-algebra operations on the version space accepted by a specifier set.

**Creation.** Callers normally create a `VersionRange` via `SpecifierSet(...).to_range()`. Static constructors `empty`, `full`, and `singleton` must create the corresponding degenerate ranges.

**Membership.** Membership tests with `Version` objects and version strings must be supported via `in` and `contains`. When `prereleases` is provided, it must override the range's pre-release policy.

**Filtering.** The `filter` method must yield items whose versions fall within the range, accepting optional `prereleases` and `key` parameters with the same semantics as `SpecifierSet.filter`.

**Set operations.** Intersection with `&` and `intersection` must return a range accepting only versions in both operands. Union with `|` and `union` must accept versions in either operand. Complement with `~` and `complement()` must accept versions rejected by the original. Difference with `-` and `difference` must accept versions in the left operand but not in the right, preserving the pre-release admission policy of the left operand.

**Set relations.** `is_empty` must be `True` for unsatisfiable ranges such as those from `SpecifierSet(">=2,<1").to_range()`. `is_subset` must report whether all accepted versions are also accepted by the other range. `is_superset` must report the reverse. `is_disjoint` must report whether the two ranges share no accepted versions.

**Equality.** Ranges must compare by canonical range behavior and must preserve pre-release policy as part of equality.

## Markers

Markers represent environment marker expressions that control conditional dependency applicability.

**Parsing and validation.** A `Marker` must be created from an environment marker string following the dependency specifier grammar. Invalid marker text must raise `InvalidMarker`. Undefined marker variable names must raise `InvalidMarker` at parse time. Undefined comparisons must raise `UndefinedComparison` at evaluation time.

**String representation.** `str(marker)` must return normalized marker text. `repr(marker)` must return `<Marker('...')>`. Markers must compare and hash by normalized marker semantics and must be usable as set elements and mapping keys.

**Evaluation.** The `evaluate` method must evaluate the marker against an environment mapping. When no `environment` is supplied, evaluation must use the current default environment. Supplying `environment` must override selected environment keys. Version-like marker comparisons must prefer PEP 440 version comparison when both sides can be interpreted as versions. String operators such as `in` and `not in` must use marker string semantics.

**Extra normalization.** Marker evaluation must normalize extras for comparisons involving `extra`, `extras`, or `dependency_groups`. When the marker references `extra` with a value like `"PDF-Export"`, evaluating with `extra` set to `"pdf_export"` must match. Evaluating with a non-matching extra value such as `"docs"` must not match. Values for `extra`, `extras`, and `dependency_groups` must be supplied through the environment mapping.

**Boolean composition.** Markers must support combination with `&` (and) and `|` (or). A composed marker must evaluate as the logical conjunction or disjunction of its parts against the supplied environment. For example, composing a Python-version constraint and an OS-name constraint with `&` must require both conditions to hold.

**Default environment.** `default_environment()` must return a mapping containing standard environment values including at least `python_version`, `python_full_version`, `os_name`, `sys_platform`, `platform_machine`, `platform_python_implementation`, `platform_release`, `platform_system`, `platform_version`, `implementation_name`, and `implementation_version`. A marker evaluated against the default environment with matching values must return `True`.

**Public typing surfaces.** `Environment` and `EvaluateContext` must be available as public typing surfaces for marker environment data and evaluation contexts.

## Requirements

Requirement parsing turns dependency strings into structured objects used by metadata, dependency groups, and lock files.

**Parsing.** A `Requirement` must be created from a dependency requirement string. Invalid requirement text must raise `InvalidRequirement`. A requirement string may contain a project name, extras in square brackets, version specifiers (optionally parenthesized), a direct URL after `@`, and an environment marker after `;`. URL requirements must not combine the URL with a version specifier.

**Attributes.** A parsed `Requirement` must expose `name` as a string, `extras` as a set of extra names, `specifier` as a `SpecifierSet`, `marker` as a `Marker` or `None`, and `url` as a string or `None`. When no extras are specified, `extras` must be an empty set. When empty extras brackets `"name[]"` are parsed, `extras` must be an empty set. When no specifier is given or an empty specifier `"name()"` is parsed, `specifier` must represent an empty constraint set. When no URL is provided, `url` must be `None`. When no marker is provided, `marker` must be `None`.

**String representation and normalization.** `str(requirement)` must return a normalized requirement string. Extra names appearing in marker comparisons must be normalized in the string representation, so a marker condition referencing `"mariadb_connector"` must be represented as `"mariadb-connector"`. Equivalent requirements differing only in whitespace, extra casing, or trailing version zeros must produce equal `Requirement` objects.

**Equality and hashing.** Requirement equality and hashing must use normalized name and extras plus the normalized specifier, URL, and marker. Requirements with equivalent but differently formatted strings must compare as equal and produce the same hash. Requirements with different specifiers, versions, markers, or names must compare as unequal and produce different hashes. Comparing a `Requirement` with a non-`Requirement` object such as a plain string must return not-equal.

**URL requirements.** Requirements with `@` URL syntax must store the URL in the `url` attribute. File URLs such as `file:///absolute/path`, `file://.`, `file:.`, and `file:/.` must be accepted. Various URL schemes including `https://`, `ssh://`, `git+ssh://`, `git+https://`, and `gopher://` must be accepted.

**Pickling.** Requirement objects must be safe to pickle and reload. A pickled and restored `Requirement` must compare equal to the original and produce the same string representation.

## Tags

Tags represent wheel compatibility markers that determine whether a wheel is installable on a given interpreter and platform.

**Tag creation.** A `Tag` must be created from an interpreter, ABI, and platform string. Tags must be immutable, hashable, comparable for equality, and printable as `interpreter-abi-platform`. Two `Tag` objects created with the same interpreter, ABI, and platform must be equal.

**Tag parsing.** `parse_tag` must parse a compressed tag string into a frozenset of `Tag` objects. Compressed components must expand as the wheel tag specification defines; for example, `"py2.py3-none-any"` must produce a frozenset containing tags for both `py2` and `py3`. Empty components must raise `InvalidTag`. When `validate_order` is `True`, unsorted compressed tag sets must raise `UnsortedTagsError`; by default, unsorted tags must be accepted without error.

**System tags.** `sys_tags()` must yield the running interpreter's supported tags in preference order. Each tag must be a `Tag` instance, and the sequence must contain no duplicates.

**Compatible tag selection.** `create_compatible_tags_selector()` must create a selector that can rank or choose compatible wheel tags according to a supported-tag order.

**Low-level tag functions.** The public functions `cpython_tags`, `generic_tags`, `compatible_tags`, `mac_platforms`, `ios_platforms`, `android_platforms`, `platform_tags`, `interpreter_name`, and `interpreter_version` must generate tags or platform strings for specific interpreter and platform inputs. `INTERPRETER_SHORT_NAMES` must map interpreter names to wheel abbreviation codes. `PythonVersion` and `AppleVersion` must be available as public type aliases.

## Utilities

Utility functions provide name normalization and filename parsing shared by requirements, metadata, tags, and lock files.

**Name normalization.** `canonicalize_name` must normalize Python distribution names by collapsing runs of `-`, `_`, and `.` to `-` and lowercasing letters. The return value must be typed as `NormalizedName`. When `validate` is `True`, invalid names such as those starting with `_` or containing newlines must raise `InvalidName`; without validation, such names must still be normalized without raising. `is_normalized_name` must report whether a name is already in normalized form; a normalized name must return `True`, and a non-normalized variant of the same name must return `False`.

**Version normalization.** `canonicalize_version` must return a normalized version string with trailing release zeros stripped by default. For example, `"1.4.0"` must become `"1.4"` and `"1.0"` must become `"1"`. Invalid versions must be returned unchanged. When `strip_trailing_zero` is `False`, release trailing zeros must be preserved. Both `Version` objects and version strings must be accepted as input.

**Wheel filename parsing.** `parse_wheel_filename` must parse a wheel filename and return a tuple of `(name, version, build, tags)` where `name` is a `NormalizedName`, `version` is a `Version`, `build` is a build tag tuple or empty tuple, and `tags` is a frozenset of `Tag` objects. Invalid wheel filenames must raise `InvalidWheelFilename`. By default, unsorted tag groups must be accepted; when `validate_order` is `True`, unsorted tag groups must raise `InvalidWheelFilename`.

**Source distribution filename parsing.** `parse_sdist_filename` must parse a source distribution filename and return `(name, version)`. Supported extensions must be `.tar.gz` and `.zip`. Invalid filenames must raise `InvalidSdistFilename`.

## Metadata

Metadata parsing reads RFC 822 style package core metadata into structured, validated objects.

**Raw parsing.** `parse_email` must parse RFC 822 style package core metadata from `str` or `bytes`. It must return `(raw, unparsed)` where `raw` is a `RawMetadata` mapping with normalized field names and parsed values, and `unparsed` maps unrecognized or invalid raw fields to their original values. When all fields are recognized and valid, `unparsed` must be an empty mapping. Fields such as `name`, `version`, and `requires_dist` must be accessible by their normalized underscore-separated key names in the raw mapping.

**Validated metadata construction.** `Metadata.from_raw` must construct a typed `Metadata` object from a raw metadata mapping. When `validate` is `True`, missing required fields or invalid field values must raise `InvalidMetadata` or an `ExceptionGroup` containing multiple metadata errors. A raw mapping missing required fields such as `metadata_version` must trigger a validation error. `Metadata.from_email` must parse email metadata and then validate it in one step.

**Typed field access.** A `Metadata` object must expose typed core metadata fields including at least `metadata_version`, `name`, `version`, `dynamic`, `platforms`, `supported_platforms`, `summary`, `description`, `keywords`, `home_page`, `download_url`, `author`, `author_email`, `maintainer`, `maintainer_email`, `license`, `license_expression`, `license_files`, `classifiers`, `requires_dist`, `requires_python`, `requires_external`, `project_urls`, `provides_extra`, `provides_dist`, and `obsoletes_dist`. The `name` field must preserve the original name string. The `version` field must be a `Version` object. The `requires_dist` field must be a list of `Requirement` objects, so metadata containing `"dep>=2"` in its requirements must produce a list where each element is a `Requirement`.

**Cross-module validation.** Metadata validation must compose with other public modules: names must use `canonicalize_name`, versions must use `Version`, version constraints must use `SpecifierSet`, requirements must use `Requirement`, and license expressions must use `canonicalize_license_expression`.

**Lower-level surfaces.** `RFC822Message` and `RFC822Policy` must be available as public lower-level surfaces for the email metadata parser. `RawMetadata` must be a public typed mapping surface for parsed raw metadata keys.

## Direct URL Records

Direct URL records describe how a package was obtained and installed, following the `direct_url.json` format.

**Record structure.** A `DirectUrl` must be created with a `url` and exactly one info object describing the URL kind. The three info types are `VcsInfo` for version-control sources, `ArchiveInfo` for archive downloads, and `DirInfo` for local directories.

**VCS records.** A `VcsInfo` must carry a `vcs` field naming the version control system, a `commit_id`, and an optional `requested_revision`. A `DirectUrl` with `VcsInfo` must round-trip through `to_dict()` and `from_dict()` preserving all fields including `requested_revision`.

**Archive records.** An `ArchiveInfo` must carry an optional `hashes` mapping from algorithm name to digest value. Direct-url JSON data may contain a legacy single `hash` string in the form `algorithm=value`; parsing must convert it to the public `hashes` representation. A `DirectUrl` with `ArchiveInfo` containing `hashes` must round-trip through serialization and deserialization preserving the URL and hash values.

**Directory records.** A `DirInfo` must carry an optional `editable` boolean indicating whether the package is installed in editable mode. A `DirectUrl` with a `file://` URL and `DirInfo(editable=True)` must serialize to a dict containing the URL and `dir_info` with `editable` set to `True`, and must reconstruct from that dict as an equal object.

**Serialization and validation.** `DirectUrl.from_dict` must validate and build a `DirectUrl` from a JSON-style mapping. `to_dict()` must serialize to a JSON-style mapping. Round-tripping through `to_dict()` and `from_dict()` must produce an equal `DirectUrl`. `validate()` must raise `DirectUrlValidationError` when required fields are missing, fields have the wrong type, more than one info object is supplied, or an info object is incompatible with the URL scheme. Constructing from a dict that contains only a URL and no info section must raise `DirectUrlValidationError`.

**Credential handling.** Callers may choose whether credentials in URLs should be stripped. URL credential stripping must keep safe environment variable placeholders where appropriate.

## Dependency Groups

Dependency group APIs expand the `[dependency-groups]` table shape used in `pyproject.toml` into resolved requirements.

**Group table structure.** A group table maps group names to lists. A list item may be a requirement string or a mapping with exactly `{"include-group": "<group name>"}`. `DependencyGroupInclude` must represent one include directive and must expose the `include_group` attribute containing the referenced group name.

**Resolver construction.** `DependencyGroupResolver` must accept a mapping of group names to group lists. Group names must be normalized for lookup, so requesting `"Test"` must find a group declared as `"test"`. Duplicate normalized group names must raise `DuplicateGroupNames`.

**Non-recursive lookup.** `resolver.lookup` must parse one group without recursively expanding included groups, returning a tuple containing `Requirement` objects and `DependencyGroupInclude` objects in their original list order. When a group contains an include directive to a cyclically-referencing group, `lookup` must return the `DependencyGroupInclude` without raising a cyclic error, because cycle detection only applies during recursive resolution.

**Recursive resolution.** `resolver.resolve` must recursively expand includes and return a tuple of `Requirement` objects. Cyclic includes must raise `CyclicDependencyGroup`. Include-group references must use normalized group names, so `"foo-bar"`, `"foo_bar"`, and `"foo..bar"` must all resolve to the same declared group. Invalid group data, malformed include objects, or invalid requirement strings must raise `InvalidDependencyGroupObject` or the relevant requirement error.

**Functional interface.** `resolve_dependency_groups` must accept a groups mapping and one or more group names, and must return requirement strings as a tuple after include expansion. An empty group must return an empty tuple. Multiple group names must combine the resolved requirements. Group name lookup must be case-insensitive through normalization.

## Pylock Files

Pylock APIs parse, validate, serialize, and select from `pylock.toml` lock file data.

**Path validation.** `is_valid_pylock_path` must return `True` for valid pylock filenames such as `"pylock.toml"` and `"pylock.spam.toml"`, and `False` for invalid names such as `"pylock.json"` or `"pylock..toml"`.

**Lock file parsing.** `Pylock.from_dict` must validate and build a `Pylock` from a TOML-style mapping. A `Pylock` must expose `lock_version` as a `Version`, `created_by` as a string, and optional fields `requires_python` as a `SpecifierSet`, `environments` as a list of `Marker` objects, `extras`, `dependency_groups`, `default_groups`, `packages`, and `tool`. Supported lock versions must include `"1.0"` and `"1.1"`; unsupported versions outside the supported range must raise `PylockUnsupportedVersionError`.

**Serialization round-trip.** `to_dict()` must serialize a `Pylock` to a TOML-style mapping. Round-tripping a pylock file through `from_dict` followed by `to_dict()` must produce an equivalent mapping that serializes identically to the original TOML content.

**Validation.** `validate()` must raise a `PylockValidationError` subclass when the lock data is structurally invalid. A valid `Pylock` must pass validation without raising.

**Package records.** A `Package` must expose a normalized `name`, optional `version` as a `Version`, optional `marker` as a `Marker`, optional `requires_python` as a `SpecifierSet`, optional `dependencies`, and source descriptors including `vcs`, `directory`, `archive`, `sdist`, and `wheels`. The `tool` field must carry per-package tool metadata. The `is_direct` property must return `True` when the package has a `directory`, `vcs`, or `archive` source, and `False` when it has only index-sourced wheel or sdist artifacts.

**Artifact entries and filenames.** `PackageWheel` and `PackageSdist` must support construction from `name`, `path`, or `url` along with `hashes`. The `filename` property must return the artifact filename, preferring `name` when present, then deriving from `path` (stripping leading `./` or `.\\` path prefixes), then from `url`. When both `name` and `path` or `url` are provided, `name` must take precedence. When `url` and `path` are both provided without `name`, `path` must take precedence. `PackageVcs` must carry `type`, `url`, and `commit_id`. `PackageDirectory` must carry `path` and optional `editable`. `PackageArchive` must carry `path` or `url` along with `hashes`, and an optional `subdirectory`.

**Selection.** `select` must yield `(package, artifact)` pairs installable for the requested environment. When `environment` is supplied, packages whose marker does not match must be excluded. When `tags` is supplied, wheel selection must prefer compatible wheels and fall back to sdist when no compatible wheel exists. When no selection filters are applied, all packages and their available artifacts must be yielded. When `extras` or `dependency_groups` are supplied, only packages matching the selected extras or groups must be included, respecting `default_groups` when `dependency_groups` is `None`. Selection errors must raise `PylockSelectError`.

**Python pre-release handling.** `requires_python` on both `Pylock` and `Package` must tolerate Python pre-release version strings that are not strictly PEP 440 compliant, allowing selection to proceed for pre-release Python interpreters.

## License Expressions

License expression canonicalization normalizes SPDX license identifiers for PEP 639 metadata.

**Canonicalization.** `canonicalize_license_expression` must normalize SPDX license IDs to their canonical casing, normalize `AND`, `OR`, and `WITH` operators, normalize exception names, preserve `LicenseRef-*` forms, and preserve parenthesized grouping. The return value must be typed as `NormalizedLicenseExpression`. For example, `"mit or apache-2.0"` must become `"MIT OR Apache-2.0"`, `"(mit and apache-2.0) or LicenseRef-Custom"` must become `"(MIT AND Apache-2.0) OR LicenseRef-Custom"`, and `"gpl-2.0-only with classpath-exception-2.0"` must become `"GPL-2.0-only WITH Classpath-exception-2.0"`.

**Error handling.** Invalid syntax, unknown license identifiers, unknown exceptions, invalid `LicenseRef` forms, and malformed grouping must raise `InvalidLicenseExpression`.

## Error Helpers

The error helpers module provides a compatibility surface for exception groups used by metadata validation and other multi-error scenarios.

**Exception group.** `ExceptionGroup` from `packaging.errors` must accept a `message` string and a list of `exceptions`. The `message` attribute must be accessible on the resulting object and must appear in the string representation. The `exceptions` attribute must return the list of contained exceptions in their original order. The group must preserve the types of contained exceptions, so a group containing an `InvalidVersion` and an `InvalidRequirement` must expose both through `exceptions` with their original types intact. On Python versions with a standard `ExceptionGroup`, this name may re-export or mirror the standard behavior.

## State Model

Packaging data moves through three public projections: source text such as a requirement or metadata field, parsed value objects such as `Version`, `Requirement`, `Marker`, and `Tag`, and compound records such as metadata, dependency groups, direct URLs, and pylock packages. These projections must share the same normalization and validation rules.

A normalized project name must compare consistently whether it came from a requirement, filename, metadata record, dependency group, or pylock package. A parsed version must keep the same ordering and specifier-membership behavior wherever a higher-level record carries it. A marker evaluated directly must make the same decision when attached to a requirement, metadata dependency, dependency group, or lock entry.

## Error Semantics

The package should raise public exceptions instead of returning partial objects
for invalid parse or validation inputs:

- invalid versions raise `InvalidVersion`;
- invalid specifiers raise `InvalidSpecifier`;
- invalid markers raise `InvalidMarker`, `UndefinedComparison`, or
  `UndefinedEnvironmentName`;
- invalid requirements raise `InvalidRequirement`;
- invalid tags raise `InvalidTag` or `UnsortedTagsError`;
- invalid names and filenames raise `InvalidName`, `InvalidWheelFilename`, or
  `InvalidSdistFilename`;
- invalid metadata raises `InvalidMetadata` or an `ExceptionGroup` containing
  metadata errors;
- invalid direct URLs raise `DirectUrlValidationError`;
- invalid dependency groups raise `DuplicateGroupNames`,
  `CyclicDependencyGroup`, or `InvalidDependencyGroupObject`;
- invalid pylock data raises `PylockValidationError`,
  `PylockUnsupportedVersionError`, or `PylockSelectError`;
- invalid license expressions raise `InvalidLicenseExpression`.

## Cross-View Invariants

1. Requirement parsing, metadata validation, dependency group expansion, and
   pylock validation all use the same `Requirement`, `SpecifierSet`, `Marker`,
   and `Version` semantics.
2. Name normalization is consistent across requirement names, metadata project
   names, dependency group references, pylock package names, and filename
   parsers.
3. Version ordering is consistent across `Version`, specifier membership,
   specifier filtering, range algebra, metadata versions, pylock versions, and
   wheel/sdist filename parsing.
4. Marker evaluation uses the same environment keys and extra normalization in
   standalone `Marker` evaluation, requirement markers, metadata requirements,
   dependency groups, and pylock selection.
5. Wheel tags produced by `parse_tag`, `parse_wheel_filename`, `sys_tags`, and
   pylock artifact selection compare as the same `Tag` objects.
6. Direct URL and pylock serialization round trips produce and accept equivalent
   public objects with the same validation behavior.
7. Invalid user input raises the documented public exception for the module
   whose API accepted the input; invalid lower-level values should not silently
   become valid higher-level objects.

## Public Interface

### Import Surface

The import root is `packaging`.

```python
from packaging.version import (
    VERSION_PATTERN, InvalidVersion, Version, normalize_pre, parse,
)
from packaging.specifiers import (
    BaseSpecifier, InvalidSpecifier, Specifier, SpecifierSet,
)
from packaging.markers import (
    Environment, EvaluateContext, InvalidMarker, Marker,
    UndefinedComparison, UndefinedEnvironmentName, default_environment,
)
from packaging.requirements import InvalidRequirement, Requirement
from packaging.tags import (
    INTERPRETER_SHORT_NAMES, AppleVersion, InvalidTag, PythonVersion, Tag,
    UnsortedTagsError, android_platforms, compatible_tags, cpython_tags,
    create_compatible_tags_selector, generic_tags, interpreter_name,
    interpreter_version, ios_platforms, mac_platforms, parse_tag,
    platform_tags, sys_tags,
)
from packaging.utils import (
    BuildTag, InvalidName, InvalidSdistFilename, InvalidWheelFilename,
    NormalizedName, canonicalize_name, canonicalize_version,
    is_normalized_name, parse_sdist_filename, parse_wheel_filename,
)
from packaging.metadata import (
    ExceptionGroup, InvalidMetadata, Metadata, RFC822Message, RFC822Policy,
    RawMetadata, parse_email,
)
from packaging.direct_url import (
    ArchiveInfo, DirInfo, DirectUrl, DirectUrlValidationError, VcsInfo,
)
from packaging.dependency_groups import (
    CyclicDependencyGroup, DependencyGroupInclude, DependencyGroupResolver,
    DuplicateGroupNames, InvalidDependencyGroupObject, resolve_dependency_groups,
)
from packaging.pylock import (
    Package, PackageArchive, PackageDirectory, PackageSdist, PackageVcs,
    PackageWheel, Pylock, PylockSelectError, PylockUnsupportedVersionError,
    PylockValidationError, is_valid_pylock_path,
)
from packaging.ranges import VersionRange
from packaging.errors import ExceptionGroup
from packaging.licenses import (
    InvalidLicenseExpression, NormalizedLicenseExpression,
    canonicalize_license_expression,
)
```

Public exception classes should be catchable from their documented modules. Public objects must preserve documented string, equality, and hash behavior where callers use them as comparable values, set elements, or mapping keys.

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Version` | class | PEP 440 version value with ordering and components |
| `parse` | function | Parses a version string into `Version` |
| `normalize_pre` | function | Normalizes pre-release phase spellings |
| `VERSION_PATTERN` | constant | Public regex fragment for version grammar |
| `Specifier` | class | One version constraint |
| `SpecifierSet` | class | Comma-separated constraint set |
| `VersionRange` | class | Set-algebra view of accepted versions |
| `Marker` | class | Environment marker expression |
| `default_environment` | function | Default marker evaluation environment |
| `Requirement` | class | Parsed dependency requirement |
| `Tag` | class | One wheel compatibility tag |
| `parse_tag` | function | Parses compressed tag strings |
| `sys_tags` | function | Yields running interpreter tags in preference order |
| `create_compatible_tags_selector` | function | Builds a compatible-tag selector |
| `canonicalize_name` | function | Normalizes distribution names |
| `canonicalize_version` | function | Normalizes version strings |
| `parse_wheel_filename` | function | Parses wheel filenames |
| `parse_sdist_filename` | function | Parses source-distribution filenames |
| `Metadata` | class | Typed core metadata object |
| `parse_email` | function | Parses RFC 822 metadata into raw fields |
| `DirectUrl` | class | Direct URL record for installed packages |
| `DependencyGroupResolver` | class | Expands dependency group tables |
| `resolve_dependency_groups` | function | Functional dependency-group resolver |
| `Pylock` | class | Parsed pylock file record |
| `is_valid_pylock_path` | function | Validates pylock filename shape |
| `canonicalize_license_expression` | function | Canonicalizes SPDX license expressions |
| `ExceptionGroup` | class | Public grouped-exception compatibility surface |

Detailed parsing, validation, serialization, and error behavior for each module are defined in the behavior sections above.

### CLI Entry Points

`packaging` is a library-only package. It provides no console script, and `python -m packaging` is not a supported interface. Callers use the documented Python imports; import and API failures surface as ordinary Python exceptions.

## Appendix A: Environment

The implementation may use third-party packages available on PyPI. Runtime dependencies must be declared in a standard `requirements.txt` or `pyproject.toml` at the project root and are installed before use. The covered APIs must not require network access, a package index, or a background service.

## Appendix B: Assessment Notes

Compatibility is determined through parsing, normalization, ordering, set membership, serialization round trips, validation errors, and agreement among requirements, metadata, dependency groups, direct URLs, tags, filenames, licenses, and pylock records. Equivalent parser structure and internal data layout are acceptable.
