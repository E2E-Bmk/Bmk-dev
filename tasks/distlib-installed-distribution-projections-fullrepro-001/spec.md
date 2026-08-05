# distlib Installed Distribution Projections Specification

## Product Overview

`distlib` is a Python packaging library that exposes installed distribution
metadata, distribution file records, package resources, source manifests, and
wheel archives through public Python APIs. The durable facts are local
filesystem trees and wheel archive members. The public behavior covered here
checks how those facts are projected through `DistributionPath`,
`InstalledDistribution`, `Metadata`, `Manifest`, resource finders, and `Wheel`.

The covered behavior is deterministic and uses local files created during the
run. It does not require a package index, remote service, subprocess-managed
server, credential, or persistent global environment.

## Scope

This specification covers:

- Discovery of `.dist-info` installed distributions from explicit search
  paths.
- Case-insensitive distribution lookup, project name normalization, requested
  state, provided distribution aliases, and requirement matching.
- Reading and writing metadata files including `METADATA` and `pydist.json`.
- Reading `RECORD`, `RESOURCES`, `pydist-exports.json`, `SHARED`, and related
  files through public installed-distribution methods.
- Manifest file discovery and directive processing over a local source tree.
- Resource finder behavior over directories, imported filesystem packages, and
  imported zip packages.
- Wheel filename parsing, wheel metadata access, `RECORD` verification,
  mounting, unmounting, shebang normalization, and content hashing.

## Public Import Surface

The package import name is `distlib`. The covered public imports are:

```python
from distlib.database import DistributionPath, InstalledDistribution
from distlib.manifest import Manifest
from distlib.metadata import Metadata
from distlib.resources import finder, finder_for_path
from distlib.wheel import Wheel
```

No private module import is part of the covered contract.

## Product State Model

An installed-distribution environment is a list of filesystem directories.
Each directory may contain import packages and metadata directories named like
`normalized_name-version.dist-info`. A metadata directory may contain:

- `METADATA`, with legacy package metadata fields.
- `pydist.json`, with JSON metadata fields.
- `RECORD`, with installed file paths, hashes, and sizes.
- `REQUESTED`, indicating user-requested installation.
- `RESOURCES`, mapping logical resource names to concrete files.
- `pydist-exports.json`, defining exported entry points.
- `SHARED`, recording shared installation locations.

A manifest state is a root directory plus the discovered `allfiles` set and
the selected `files` set. Manifest directives transform only the selected set.

A resource state is either a container or a file-like resource addressed by a
logical resource name. Directory-backed and zip-backed resources expose names,
container status, child resource names, byte content, and stream access.

A wheel state is a wheel filename and zip archive. Its public projections
include name, version, compatibility tags, metadata, wheel info, archive
membership, mounted import path state, normalized script content, and hashes.

## Installed Distribution Behavior

`DistributionPath.distinfo_dirname(name, version)` SHALL normalize dashes in
the project name to underscores and append the version and `.dist-info`
suffix.

`DistributionPath(paths).get_distributions()` SHALL discover installed
distributions located under those explicit paths and return public
distribution objects. `get_distribution(name)` SHALL find distributions
case-insensitively.

An installed distribution SHALL expose `name`, `version`,
`name_and_version`, and string form based on public metadata. A distribution
with a `REQUESTED` file SHALL report `requested` as true.

`list_installed_files()` SHALL read `RECORD` rows as `(path, hash, size)`
triples. `list_distinfo_files()` SHALL list files belonging to the metadata
directory and not ordinary package files. `get_distinfo_file(name)` SHALL
resolve paths under that metadata directory. `get_distinfo_resource(name)`
SHALL return a resource whose bytes and size match the metadata file.

`check_installed_files()` SHALL return an empty list when recorded file hashes
and sizes match the local files. After a recorded file changes, it SHALL
report a mismatch for that file.

`write_installed_files(paths, prefix=...)` SHALL rebuild `RECORD` from the
supplied paths plus the `RECORD` row itself. `write_shared_locations(paths)`
SHALL write `SHARED`, and a newly loaded distribution SHALL expose the same
shared locations through `shared_locations`.

## Metadata Projection

`Metadata(mapping=...)` SHALL expose common fields such as `name`, `version`,
`summary`, `license`, and `name_and_version`. `todict()` and `dictionary`
SHALL provide the public dictionary projection.

Assigning a keyword string SHALL expose keywords as a list split on
whitespace. `get_requirements(run_requires, extras=[...])` SHALL include
base requirements and requirements for selected extras, while omitting
requirements for unselected extras.

Writing JSON metadata and loading it again SHALL round-trip the metadata
dictionary. Writing legacy metadata and reading it with the legacy scheme
SHALL preserve public fields and requirement data.

## Manifest Projection

`Manifest(root).findall()` SHALL discover regular local files under `root`,
including hidden files. `include`, `recursive-include`, `recursive-exclude`,
`graft`, and `prune` directives SHALL update the selected file set according
to their documented path and pattern meanings.

`add_many()` SHALL accept relative file paths. `sorted(wantdirs=True)` SHALL
include required parent directories in deterministic order. `clear()` SHALL
empty both selected and discovered file collections.

## Resource Projection

`finder_for_path(path)` SHALL locate resources in a directory tree. Containers
SHALL report `is_container` as true and list child resources. File resources
SHALL report `is_container` as false and expose their bytes.

`finder(package_name)` SHALL locate resources for an imported package. The
same public operations SHALL work for packages imported from a filesystem
directory and packages imported from a zip archive.

## Wheel Projection

`Wheel(filename)` SHALL expose the wheel name, version, filename, and
compatibility tags from the wheel filename. It SHALL read `WHEEL`,
`METADATA`, and `RECORD` from the archive through public wheel properties.

`verify()` SHALL accept an archive whose `RECORD` entries match all archive
members. `mount()` SHALL add the wheel archive to the import path so package
resources can be imported and read. `unmount()` SHALL remove that path.

`process_shebang()` SHALL normalize an existing Python interpreter shebang to
`#!python` while preserving options, and SHALL add a Python shebang to script
content that lacks one. `get_hash(bytes)` SHALL return a named digest using
the wheel hash algorithm.

## Error Semantics

Installed file integrity checks report mismatches as public tuples rather
than mutating the file tree. A size or hash mismatch SHALL identify the
changed file.

Manifest directives operate on the selected file set; excluding or pruning a
path SHALL remove matching selections without deleting local files.

Wheel verification SHALL be based on public archive metadata and content. The
covered valid wheel archive SHALL verify without warning or mutation.

## Cross-View Invariants

Metadata loaded through `DistributionPath` SHALL agree with metadata loaded
directly from the serialized metadata file.

`RECORD`, metadata-directory listings, and installed-file integrity checks
SHALL describe the same installed distribution. Resource paths in `RESOURCES`
and directory resource finders SHALL read the same bytes.

Exports exposed directly by an installed distribution SHALL match exports
looked up from the surrounding distribution path. Requirement matching and
provided distribution lookup SHALL agree on aliases from metadata.

Manifest selections SHALL match the filesystem projection for the same root.
Resource finders SHALL read files selected by manifest operations.

Wheel metadata SHALL be usable as public metadata for an installed
distribution projection. Metadata written to a wheel archive SHALL round-trip
through the wheel reader.

## Representative Workflow

A typical workflow creates a local site-packages tree containing a package,
its `.dist-info` directory, metadata files, resources, export definitions, and
`RECORD`. A `DistributionPath` discovers that distribution, reads metadata,
checks file integrity, resolves resources, and exposes exports. The same run
may select files from a source tree using `Manifest`, then read equivalent
files through a resource finder. A local wheel archive can then be inspected,
verified, mounted, used for package resource access, and unmounted.

## Non-Goals

The covered behavior excludes online package index lookup, publication,
download, signing workflows, installer command execution, platform launcher
generation, and private cache internals.

The covered behavior does not require exact wording for exception messages,
remote resource behavior, or compatibility with packages outside the local
fixtures created for a run.

## Invocation Protocol

The verifier SHALL run the provided pytest files against an implementation
root supplied by `--target-root` or by the `TARGET_ROOT` environment variable.
That root must contain the `distlib` package. The implementation root is added
to the front of `sys.path` before the checks run.

The run command may use:

```bash
python -m pytest <test-directory> -q --target-root <implementation-root>
```

JSON reporting may be enabled with `pytest-json-report` when local evidence is
being recorded.

## Environment

The target environment is Linux with Python 3.11, without network access. The
target package is not pre-installed; the implementation root is supplied at
runtime.

Required local packages:

- `pytest`
- `pytest-json-report`

The checks create temporary local files and zip archives under pytest-managed
temporary directories. They do not rely on wall-clock timing, background
services, network access, Docker, or credentials.

## Evaluation Notes

All covered behavior is public library behavior reachable through documented
imports. The test data uses local synthetic package names and local archives
to keep filesystem facts deterministic.

The checks intentionally combine independent views of the same facts:
installed distribution metadata, serialized metadata files, `RECORD`, resource
finder output, manifest output, and wheel archive records.
