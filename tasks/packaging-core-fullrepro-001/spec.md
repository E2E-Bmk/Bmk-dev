# Packaging Core Utilities Specification

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

- Do not implement a package installer, dependency resolver, wheel builder,
  index client, or network downloader.
- Do not access PyPI, Git, the local interpreter package database, or the
  filesystem except where an API explicitly accepts or returns a path-like
  value.
- Do not expose or rely on private modules whose names start with `_`.
- Do not implement platform-specific binary inspection helpers as public API.
- Do not require exact internal parser trees or private dataclass layouts beyond
  the public attributes and behavior described here.

## Package Shape

The import root is `packaging`.

The following public modules and names are part of the contract:

- `packaging.version`: `VERSION_PATTERN`, `InvalidVersion`, `Version`,
  `normalize_pre`, `parse`
- `packaging.specifiers`: `BaseSpecifier`, `InvalidSpecifier`, `Specifier`,
  `SpecifierSet`
- `packaging.markers`: `Environment`, `EvaluateContext`, `InvalidMarker`,
  `Marker`, `UndefinedComparison`, `UndefinedEnvironmentName`,
  `default_environment`
- `packaging.requirements`: `InvalidRequirement`, `Requirement`
- `packaging.tags`: `INTERPRETER_SHORT_NAMES`, `AppleVersion`, `InvalidTag`,
  `PythonVersion`, `Tag`, `UnsortedTagsError`, `android_platforms`,
  `compatible_tags`, `cpython_tags`, `create_compatible_tags_selector`,
  `generic_tags`, `interpreter_name`, `interpreter_version`, `ios_platforms`,
  `mac_platforms`, `parse_tag`, `platform_tags`, `sys_tags`
- `packaging.utils`: `BuildTag`, `InvalidName`, `InvalidSdistFilename`,
  `InvalidWheelFilename`, `NormalizedName`, `canonicalize_name`,
  `canonicalize_version`, `is_normalized_name`, `parse_sdist_filename`,
  `parse_wheel_filename`
- `packaging.metadata`: `ExceptionGroup`, `InvalidMetadata`, `Metadata`,
  `RFC822Message`, `RFC822Policy`, `RawMetadata`, `parse_email`
- `packaging.direct_url`: `ArchiveInfo`, `DirInfo`, `DirectUrl`,
  `DirectUrlValidationError`, `VcsInfo`
- `packaging.dependency_groups`: `CyclicDependencyGroup`,
  `DependencyGroupInclude`, `DependencyGroupResolver`, `DuplicateGroupNames`,
  `InvalidDependencyGroupObject`, `resolve_dependency_groups`
- `packaging.pylock`: `Package`, `PackageArchive`, `PackageDirectory`,
  `PackageSdist`, `PackageVcs`, `PackageWheel`, `Pylock`, `PylockSelectError`,
  `PylockUnsupportedVersionError`, `PylockValidationError`,
  `is_valid_pylock_path`
- `packaging.ranges`: `VersionRange`
- `packaging.errors`: `ExceptionGroup`
- `packaging.licenses`: `InvalidLicenseExpression`,
  `NormalizedLicenseExpression`, `canonicalize_license_expression`

Public exception classes should be catchable from their documented modules.
Public objects should have stable string, repr, equality, and hash behavior
where the docs present them as comparable, printable, set elements, or mapping
values.

## Version Handling

`Version(value)` parses one PEP 440 version string. `parse(value)` returns a
`Version`. Invalid version text raises `InvalidVersion`.

Versions compare according to PEP 440 ordering, not lexical string ordering.
They are hashable and can be sorted with normal Python comparison operators.
Pre-releases sort before the corresponding final release. Post-releases sort
after their base release. Development releases sort before the release they
develop toward. Epochs take precedence over release segments. Local versions
participate in ordering only where PEP 440 defines their comparison.

`repr(Version("1.0"))` uses the form `<Version('1.0')>`. `str(version)` returns
the normalized public version string.

A `Version` exposes:

- `epoch`
- `release`
- `pre`
- `post`
- `dev`
- `local`
- `public`
- `base_version`
- `is_prerelease`
- `is_postrelease`
- `is_devrelease`
- `major`
- `minor`
- `micro`

Missing pre/post/dev/local segments are represented as `None` where applicable.
The `release` tuple contains integer release components. `major`, `minor`, and
`micro` are derived from release components, with missing components treated as
zero for those convenience properties.

`normalize_pre(letter)` normalizes pre-release spellings to canonical PEP 440
phase names.

`VERSION_PATTERN` is a public regular-expression pattern for recognizing the
version grammar. It is a pattern string intended for callers that need to embed
the PEP 440 version grammar in a larger regular expression.

## Specifiers

`Specifier(spec="", prereleases=None)` represents one version constraint.
`SpecifierSet(specifiers="", prereleases=None)` represents a comma-separated
set of constraints. Invalid specifier text raises `InvalidSpecifier`.

Supported specifier operators include `~=`, `==`, `!=`, `<=`, `>=`, `<`, `>`,
and arbitrary equality `===`.

Specifier and specifier-set objects:

- are printable and repr-able in normalized form;
- compare and hash by their normalized semantic content;
- support membership tests with `Version` objects and version strings;
- expose and honor a `prereleases` policy override;
- provide `contains(version, prereleases=None, installed=None)` behavior;
- provide `filter(iterable, prereleases=None, key=None)` behavior, where `key`
  extracts a version string or `Version` from each item before filtering.

`SpecifierSet` supports:

- implicit combination from comma-separated text;
- iteration over individual `Specifier` objects;
- `&` and `&=` combination with another specifier set or a specifier string;
- `is_unsatisfiable()`;
- `to_range()`, returning a `VersionRange` view.

Filtering preserves input item type where possible. A string version that
passes a filter may be yielded as the original string rather than converted to a
`Version`.

Pre-release handling follows PEP 440: pre-releases are normally excluded unless
the specifier explicitly admits them, the caller enables them, or no final
release candidate from the input can satisfy the set.

## Version Ranges

`VersionRange` is a set-algebra view of versions accepted by a specifier set.
Callers normally create it via `SpecifierSet(...).to_range()`.

A range supports:

- membership with `Version` and version strings;
- `contains(version, prereleases=None, installed=None)`;
- `filter(iterable, prereleases=None, key=None)`;
- intersection with `&` and `intersection(other)`;
- union with `|` and `union(other)`;
- complement with `~` and `complement()`;
- difference with `-` and `difference(other)`;
- `empty(prereleases=None)`;
- `full(admit_arbitrary=True, prereleases=None)`;
- `singleton(version, prereleases=None)`;
- equality and repr based on canonical range behavior;
- `is_empty`;
- `is_subset(other)`;
- `is_superset(other)`;
- `is_disjoint(other)`.

`SpecifierSet(">=2.0,<1.0").to_range().is_empty` is true. Ranges preserve
pre-release policy as part of equality. Set relations such as subset and
disjointness compare accepted version sets rather than relying on textual
specifier equality.

For difference, `a - b` means versions accepted by `a` but not by `b`; the
operation keeps the pre-release admission policy of `a`.

## Markers

`Marker(marker_string)` parses an environment marker expression from the
dependency specifier grammar. Invalid marker text raises `InvalidMarker`.

Markers support:

- `str(marker)` as normalized marker text;
- `repr(marker)` as `<Marker('...')>`;
- equality and hash by normalized marker semantics;
- set membership use through hashing;
- `evaluate(environment=None, context="metadata")`;
- combination with `&` and `|`.

`Marker("python_version>'2'").evaluate()` evaluates against the current default
environment. Supplying `environment` overrides selected environment keys.

`default_environment()` returns a mapping containing environment values such as
Python version, full Python version, implementation, operating system,
platform, and extra-related values used by marker evaluation.

Marker variables include the standard dependency-specifier variables such as
`python_version`, `python_full_version`, `os_name`, `sys_platform`,
`platform_machine`, `platform_python_implementation`, `platform_release`,
`platform_system`, `platform_version`, `implementation_name`,
`implementation_version`, `extra`, `extras`, and `dependency_groups`.

Version-like marker comparisons prefer PEP 440 version comparison when both
sides can be interpreted as versions. String operators such as `in` and
`not in` use marker string semantics. Undefined marker variables raise
`UndefinedEnvironmentName`. Undefined comparisons raise `UndefinedComparison`.

Marker evaluation normalizes extras for comparisons involving `extra`, `extras`,
or `dependency_groups`. Values for `extra`, `extras`, and `dependency_groups`
are supplied through the environment mapping.

`Environment` and `EvaluateContext` are public typing surfaces for marker
environment data and evaluation contexts.

## Requirements

`Requirement(requirement_string)` parses one dependency requirement string.
Invalid requirement text raises `InvalidRequirement`.

Requirement strings may contain:

- a project name;
- extras in square brackets;
- version specifiers;
- a direct URL after `@`;
- an environment marker after `;`.

`Requirement("name")` exposes:

- `name`
- `url`
- `extras`
- `specifier`
- `marker`

`extras` is a set of extra names. `specifier` is a `SpecifierSet`. `marker` is
a `Marker` or `None`. URL requirements may not combine the URL with a version
specifier. Requirement equality and hashing use normalized name and extras plus
the normalized specifier, URL, and marker. Requirement objects are safe to
pickle and reload.

## Tags

`Tag(interpreter, abi, platform)` represents one wheel compatibility tag. Tags
are immutable, hashable, comparable for equality, and printable as
`interpreter-abi-platform`.

`parse_tag(tag, validate_order=False)` parses a compressed tag string into a
frozenset of `Tag` objects. Compressed interpreter, ABI, and platform
components expand as the wheel tag specification defines. Empty components
raise `InvalidTag`. When order validation is requested, unsorted compressed tag
sets raise `UnsortedTagsError`.

`sys_tags()` yields the running interpreter's supported tags in preference
order. `create_compatible_tags_selector()` creates a selector that can rank or
choose compatible wheel tags according to a supported-tag order.

High-level callers normally use `Tag`, `parse_tag`, `sys_tags`, and
`create_compatible_tags_selector`.

The low-level public tag functions generate tags or platform strings for
specific interpreter/platform inputs:

- `cpython_tags`
- `generic_tags`
- `compatible_tags`
- `mac_platforms`
- `ios_platforms`
- `android_platforms`
- `platform_tags`
- `interpreter_name`
- `interpreter_version`

`INTERPRETER_SHORT_NAMES` maps interpreter names to wheel abbreviation codes.
`PythonVersion` and `AppleVersion` are public type aliases for version tuples.

## Utilities

`canonicalize_name(name, validate=False)` normalizes Python distribution names
according to the package name normalization rules: runs of `-`, `_`, and `.` are
collapsed to `-`, and letters are lowercased. With `validate=True`, invalid
names raise `InvalidName`. The return value is typed as `NormalizedName`.

`is_normalized_name(name)` reports whether a name is already normalized.

`canonicalize_version(version, strip_trailing_zero=True)` returns a normalized
version string. Invalid versions are returned unchanged. With
`strip_trailing_zero=False`, release trailing zeros are preserved where the
version grammar allows.

`parse_wheel_filename(filename, validate_order=False)` parses a wheel filename
and returns `(name, version, build, tags)`, where `name` is `NormalizedName`,
`version` is `Version`, `build` is a build tag tuple or empty tuple, and `tags`
is a frozenset of `Tag` objects. Invalid wheel filenames raise
`InvalidWheelFilename`.

`parse_sdist_filename(filename)` parses a source distribution filename and
returns `(name, version)`. Supported source distribution extensions are
`.tar.gz` and `.zip`. Invalid source distribution filenames raise
`InvalidSdistFilename`.

## Metadata

`parse_email(data)` parses RFC 822 style package core metadata from `str` or
`bytes`. It returns `(raw, unparsed)`, where `raw` is a `RawMetadata` mapping
with normalized field names and parsed values, and `unparsed` maps unrecognized
or invalid raw fields to their original values.

`Metadata.from_raw(raw, validate=True)` constructs a typed `Metadata` object
from raw metadata. Invalid field values raise `InvalidMetadata`; multiple
validation problems may be reported through `ExceptionGroup`.

`Metadata.from_email(data, validate=True)` parses email metadata and then
validates it as metadata.

`Metadata` exposes typed core metadata fields, including at least:

- `metadata_version`
- `name`
- `version`
- `dynamic`
- `platforms`
- `supported_platforms`
- `summary`
- `description`
- `keywords`
- `home_page`
- `download_url`
- `author`
- `author_email`
- `maintainer`
- `maintainer_email`
- `license`
- `license_expression`
- `license_files`
- `classifiers`
- `requires_dist`
- `requires_python`
- `requires_external`
- `project_urls`
- `provides_extra`
- `provides_dist`
- `obsoletes_dist`

Metadata validation composes with other public modules: names use
`canonicalize_name`, versions use `Version`, version constraints use
`SpecifierSet`, requirements use `Requirement`, and license expressions use
`canonicalize_license_expression`.

`RFC822Message` and `RFC822Policy` are public lower-level surfaces for the email
metadata parser. `RawMetadata` is a public typed mapping surface for parsed raw
metadata keys.

## Direct URL Records

Direct URL APIs parse, validate, serialize, and deserialize `direct_url.json`
records.

`DirectUrl(*, url, archive_info=None, vcs_info=None, dir_info=None,
subdirectory=None)` represents one direct URL record. Exactly one info object
should describe the URL kind:

- `VcsInfo(*, vcs, commit_id, requested_revision=None)`
- `ArchiveInfo(*, hashes=None)`
- `DirInfo(*, editable=None)`

`DirectUrl.from_dict(mapping)` validates and builds a `DirectUrl` from a JSON
style mapping. `to_dict()` serializes to a JSON style mapping. `validate()`
raises `DirectUrlValidationError` when required fields are missing, fields have
the wrong type, more than one info object is supplied, or an info object is
incompatible with the URL scheme.

`ArchiveInfo` stores a modern `hashes` mapping. Direct-url JSON data may contain
a legacy single `hash` string in the form `algorithm=value`; parsing converts it
to the public archive information and serialization can emit JSON-compatible
fields. Callers may choose whether credentials in URLs should be stripped. URL
credential stripping keeps safe environment variable placeholders where
appropriate.

## Dependency Groups

Dependency group APIs expand the `[dependency-groups]` table shape used in
`pyproject.toml`.

A group table maps group names to lists. A list item may be:

- a requirement string;
- a mapping with exactly `{"include-group": "<group name>"}`.

`DependencyGroupInclude(group)` represents one include directive.

`DependencyGroupResolver(groups)` accepts a mapping of group names to group
lists. Group names are normalized for lookup. Duplicate normalized group names
raise `DuplicateGroupNames`.

`resolver.lookup(group)` parses one group without recursively expanding
included groups, returning a tuple containing `Requirement` objects and
`DependencyGroupInclude` objects.

`resolver.resolve(group)` recursively expands includes and returns a tuple of
`Requirement` objects. Cyclic includes raise `CyclicDependencyGroup`. Invalid
group data, malformed include objects, or invalid requirement strings raise
`InvalidDependencyGroupObject` or the relevant requirement error collected by
the resolver.

`resolve_dependency_groups(groups, *group_names)` is the functional interface.
It returns requirement strings after include expansion.

## Pylock Files

Pylock APIs parse, validate, serialize, and select from `pylock.toml` data.

`is_valid_pylock_path(path)` returns true for valid pylock filenames.

`Pylock.from_dict(mapping)` validates and builds a `Pylock` from a TOML-style
mapping. `to_dict()` serializes to a TOML-style mapping. `validate()` raises a
`PylockValidationError` subclass when the lock data is structurally invalid.
`select(environment=None, extras=None, dependency_groups=None, tags=None)` yields
packages and selected artifacts installable for the requested environment.

The public frozen keyword-only data classes represent the pylock file structure:

- `Pylock(*, lock_version, environments=None, requires_python=None,
  extras=None, dependency_groups=None, default_groups=None, created_by,
  packages, tool=None)`
- `Package(*, name, version=None, marker=None, requires_python=None,
  dependencies=None, vcs=None, directory=None, archive=None, index=None,
  sdist=None, wheels=None, attestation_identities=None, tool=None)`
- `PackageWheel(*, name=None, upload_time=None, url=None, path=None,
  size=None, hashes)`
- `PackageSdist(*, name=None, upload_time=None, url=None, path=None,
  size=None, hashes)`
- `PackageArchive(*, url=None, path=None, size=None, upload_time=None,
  hashes, subdirectory=None)`
- `PackageVcs(*, type, url=None, path=None, requested_revision=None,
  commit_id, subdirectory=None)`
- `PackageDirectory(*, path, editable=None, subdirectory=None)`

`Pylock` includes fields such as lock version, environments, extras,
dependency groups, default groups, created-by metadata, and package entries.
`Package` includes normalized name, version, marker, requires-python,
dependencies, source descriptors, artifact entries, attestation identities, and
tool metadata.

Artifact entries may identify wheel, sdist, archive, VCS, or directory sources.
File names and package names are validated with the public utilities:
`parse_wheel_filename`, `parse_sdist_filename`, and `is_normalized_name`.
Package versions use `Version`; markers use `Marker`; requirements use
`Requirement`; wheel compatibility uses `Tag`.

Unsupported lock versions raise `PylockUnsupportedVersionError`. Selection
errors raise `PylockSelectError`.

## License Expressions

`canonicalize_license_expression(raw_license_expression)` canonicalizes an SPDX
license expression as used by PEP 639 metadata. It normalizes SPDX license IDs,
exceptions, `LicenseRef-*` forms, `AND`, `OR`, `WITH`, and parentheses. The
return value is typed as `NormalizedLicenseExpression`.

Invalid syntax, unknown license identifiers, unknown exceptions, invalid
`LicenseRef` forms, and malformed grouping raise `InvalidLicenseExpression`.

## Error Helpers

`packaging.errors.ExceptionGroup(message, exceptions)` is a public compatibility
surface for Python exception groups. It exposes:

- `message`
- `exceptions`

On Python versions with a standard `ExceptionGroup`, this name may re-export or
mirror the standard behavior.

## Cross-Component Invariants

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
