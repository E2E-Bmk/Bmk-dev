# Flit Project-to-Distribution Public Behavior Specification

## Product Overview
Flit maps a Python project described by `pyproject.toml` and a package source
tree into standard package metadata, wheels, editable wheels, and source
distributions. The supported behavior in this package is the documented Flit
4.0.0 build workflow through the PEP 517 backend and the `flit` command entry
point. The projections are deterministic for the same generated project and
fixed build inputs.

## Scope
The supported project model uses the standard `[project]` table and the
`flit_core.buildapi` backend. It covers static and dynamic version and
description metadata, README and license metadata, authors and maintainers,
dependencies and optional dependencies, project URLs, console and GUI
scripts, named entry-point groups, package data, external data, source
layouts, namespace packages, sdist include/exclude rules, editable wheels,
wheel `RECORD` entries, normalized permissions, and the `flit build` command.
The generated fixtures use the distribution `aurora-tools` at version
`1.2.3`, with import package `aurora_tools`, unless a case explicitly uses a
different project variant.

## Installable Surface
The documented backend import is `flit_core.buildapi`. It exposes the PEP 517
hooks `get_requires_for_build_wheel`,
`get_requires_for_build_editable`, `get_requires_for_build_sdist`,
`prepare_metadata_for_build_wheel`, `prepare_metadata_for_build_editable`,
`build_wheel`, `build_editable`, and `build_sdist`.

The documented command entry point is `flit.main`. Its `build` subcommand
accepts `--format wheel`, `--format sdist`, and `--no-use-vcs`. The public
`--help` output names both `build` and `publish`; the public `--version`
option exits successfully after printing `Flit 4.0.0`.

## Product State Model
For the static fixture, the prepared metadata directory is
`aurora_tools-1.2.3.dist-info`, and its metadata identifies the project as
`aurora-tools` version `1.2.3` with summary `Aurora static toolkit.`. The
README supplies Markdown content and the metadata declares
`Description-Content-Type: text/markdown`. Authors and maintainers preserve
their names and email addresses; dependencies preserve `tomli >= 2` and the
optional `cli` dependency `click >= 8`; project URLs preserve the
`Documentation` and `Source` values used by the fixture. The license metadata
uses the MIT expression and includes `LICENSE`.

The prepared entry-point file contains the `aurora.plugins` group,
`console_scripts`, and `gui_scripts` entries declared by the project. A
regular wheel is named `aurora_tools-1.2.3-py3-none-any.whl` and contains the
package Python files, `data.json`, and `nested/info.txt`, while excluding
`__pycache__` and `.pyc` files. External `data/share/config.ini` is projected
to `aurora_tools-1.2.3.data/data/share/config.ini`. The wheel is pure Python,
uses the `py3-none-any` tag, normalizes ordinary file permissions to `644` and
executable file permissions to `755`, and records every member in `RECORD`
with matching SHA-256 URL-safe digests and byte sizes.

An editable wheel has the same project metadata but contains
`aurora_tools.pth` with the absolute project root and does not copy the
regular package files. The editable metadata hook creates the same
`aurora_tools-1.2.3.dist-info` directory.

The source distribution is named `aurora_tools-1.2.3.tar.gz` with the single
root `aurora_tools-1.2.3`. It includes `pyproject.toml`, README and license
inputs, package files, external data, and `PKG-INFO`, while excluding bytecode.
Configured `docs/*.md` inclusion and `docs/skip.md` exclusion keep only
`docs/guide.md` in the rules fixture.

The source-layout fixture uses `src/actual_pkg` while retaining distribution
identity `src-distribution-1.2.3`. The namespace fixture preserves
`acme/widgets/__init__.py`, distribution identity `acme-widgets`, and the
corresponding import metadata. The dynamic fixture derives version `2.4.1`
and summary `Aurora dynamic toolkit.` from the package source. Inline README
and license tables serialize their supplied Markdown and license text.

## Error Semantics
The public behavior contract concerns successful projections and the
observable `SystemExit` status of the documented help and version options.
The package must not require callers to depend on private modules, private
attributes, or exact exception text. Upload failures, credential handling, and
network errors are outside this contract.

## Cross-View Invariants
Wheel metadata produced by `prepare_metadata_for_build_wheel` matches the
metadata embedded in the built wheel. Wheel metadata and sdist `PKG-INFO`
agree on project identity, summary, Python requirement, license expression,
and dependencies. The wheel `RECORD` covers license and external-data files,
and its package-file projection agrees with the wheel contents.

Regular and editable wheels share project metadata while differing in copied
package files and the editable path file. Prepared editable metadata matches
the metadata embedded in the built editable wheel. Passing a prepared metadata
directory to the wheel build hook preserves the resulting wheel metadata. An
sdist extracted into a clean directory can feed a second backend wheel with
the same member names and package bytes. Metadata, entry points, license
content, external data, normalized distribution names, and bytecode exclusions
agree across the relevant wheel, editable-wheel, sdist, prepared-metadata, and
command projections. With `SOURCE_DATE_EPOCH` fixed, repeated wheel and sdist
builds from the same generated project produce identical bytes; no particular
archive timestamp value is part of the contract.

## Representative Workflow
A client creates a temporary project tree, writes standard project metadata
and package files, calls the public backend hooks to prepare metadata and
build a wheel, editable wheel, and sdist, then inspects standard ZIP, TAR,
Core Metadata, `WHEEL`, entry-point, and `RECORD` content. The same project is
also built with `flit.main` using `--no-use-vcs` and a selected format. The
client compares the command and backend projections, extracts the sdist, and
builds a second wheel from the extracted project.

## Non-Goals
This package does not cover upload or publish execution, credentials, live
services, network access, VCS discovery, installation into a host environment,
machine-specific paths, private implementation modules or attributes, source
test modules, exact exception wording, or exact archive timestamp fields.
It does not require Docker, an external command, or a pre-installed Flit
package.

## Invocation Protocol
Install the packages listed in the accompanying requirements file, make the `flit` and
`flit_core` implementation importable, and run:

```bash
python -m pytest <test-directory> -q -W error
```

The tests create all project inputs under pytest temporary directories. A
checkout path may be supplied with the `--target-root` option or the
`TARGET_ROOT` environment variable; if neither is supplied, the
implementation must already be importable. Tests do not contact a service or
read a repository-specific test module.

## Environment
The intended evaluation environment is Linux with Python 3.11 and without network access during the test run. The target package is not pre-installed;
the implementation under evaluation must provide the public `flit` and
`flit_core` packages. The required test packages are `pytest`,
`docutils==0.21.2`, and `requests`.

## Evaluation Notes
The package contains 30 atomic cases and 30 integration cases. Integration
cases combine independently produced views such as prepared metadata,
regular or editable wheels, sdists, extracted source trees, and the public
command entry point. The tests use only documented public Flit entry points
and standard-library archive and metadata readers. They are designed to
distinguish a real project-to-distribution implementation from an import-only
or empty implementation without relying on upload, network, or timestamp
details.
