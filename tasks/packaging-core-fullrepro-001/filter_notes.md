# packaging-core-fullrepro-001 Stage 1 Filter Notes

## Candidate

- Source repo: `repo-pool/pypa__packaging`
- Upstream: `pypa/packaging`
- Commit: `0019d113dfc2db08c80e5ee73100ff6cab1dfe92`
- Package: `packaging`
- Domain: Python packaging interoperability utilities.

## Hard Gates

- Pure Python: pass. The project is a Python package under `src/packaging` with
  no service dependency and no runtime network requirement.
- Non-test Python LOC: about 10,031 non-empty non-comment lines across 39
  non-test Python files.
- Tests: 1,194 AST-counted `test_*` functions across 30 test files.
- Public docs: pass. `README.rst` points to local API docs under `docs/`.
  Local docs cover version handling, specifiers, markers, requirements, tags,
  metadata, direct URL, dependency groups, licenses, errors, utilities, ranges,
  and pylock.
- Independent public projections: pass. Candidate projections include:
  `Version` parsing/comparison, `Specifier` and `SpecifierSet` membership,
  marker parsing/evaluation, requirement parsing, tag generation/parsing,
  metadata parsing/validation, direct-url JSON round-trips, dependency group
  expansion, and pylock validation.

## Public Agreement Surface

The central contract is that all packaging grammars and normalized objects agree
across parsing, string/repr output, equality/hash behavior, membership
evaluation, and composition:

- requirement strings compose names, extras, URL references, version specifiers,
  and environment markers into one normalized requirement object;
- markers evaluate against environment mappings and compose with `&` / `|`
  while preserving normalized string and equality semantics;
- specifier sets accept/reject `Version` values and can be projected into range
  algebra;
- tags compare and sort according to interpreter, ABI, and platform
  compatibility;
- metadata and pylock parsers validate structured package metadata using the
  same version, specifier, marker, requirement, tag, and URL semantics.

## Initial Test-Surface Audit

Tests mostly import documented public modules:

- `packaging.version`
- `packaging.specifiers`
- `packaging.markers`
- `packaging.requirements`
- `packaging.tags`
- `packaging.utils`
- `packaging.metadata`
- `packaging.direct_url`
- `packaging.dependency_groups`
- `packaging.pylock`
- `packaging.errors`

Known file-level risks for Stage 3:

- `tests/test_elffile.py` imports `packaging._elffile`.
- `tests/test_manylinux.py` imports `packaging._manylinux`.
- `tests/test_musllinux.py` imports `packaging._musllinux`.
- `tests/test_markers.py` imports `packaging._parser` for some helper-level
  assertions.
- `tests/test_ranges.py` imports `packaging._ranges`.
- `tests/test_tags.py` imports private platform helpers for some rows.
- `tests/test_version.py` imports `packaging._structures`.
- `tests/test_licenses.py` imports `packaging.licenses._spdx`.

Stage 3 must apply file-level import provenance before keeping nodeids. Rows
from files with top-level private imports are unsafe unless the whole file can
be excluded or the verifier setup can be rewritten around documented public
imports.

## Risks

- Known-pattern saturation: PEP 440, PEP 508, wheel tags, core metadata, and
  direct-url specs are widely known. A strong model may solve a large fraction
  from prior knowledge, so Gate A may retire this candidate as too easy.
- Exact standard compliance can become checklist-like if the spec simply copies
  exhaustive grammars. Stage 2 should emphasize cross-projection invariants and
  documented API behavior instead of enumerating every fixture value.
- Some tests are property-based or private-module/platform-focused. Stage 3
  should begin with deterministic public docs-backed tests and exclude
  `property` marked tests unless they can be bounded deterministically.

## Stage 1 Decision

Proceed to Stage 2.

This candidate satisfies the normal hard gates without LOC exceptions and has a
docs-backed public Python API surface. The main open question is not solvability
but whether the filtered public subset remains difficult enough after excluding
private import carriers and high-saturation standard-checklist rows.
