# Source Repo: BGraph

- Repository: `quarkslab/bgraph`
- URL: https://github.com/quarkslab/bgraph
- Reference status: archived read-only repository, archived by owner on 2025-09-19
- Source language: Python
- Source surface: Android.bp-style build dependency graph extraction and querying
- Benchmark case: `minibuildgraph-realrepo-001`

## Selected Surface

This task extracts a simplified build graph system from BGraph. The benchmark focuses on parsing small blueprint-like module definitions, constructing a directed dependency graph, querying direct and transitive dependencies, detecting cycles, and producing deterministic text output.

The source README describes BGraph as a tool designed to generate dependency graphs from `Android.bp` Soong files. It also describes the project as building and using dependency graphs for AOSP by parsing and linking modules defined in the Android build system. The benchmark keeps the stateful graph-construction and query surface while removing AOSP checkout, repo/git operations, Docker, Soong evaluation, and full Blueprint syntax.

## Source Evidence

Verified source facts from https://github.com/quarkslab/bgraph:

- The repository page marks the project as archived and read-only as of 2025-09-19.
- The README describes BGraph as a tool for generating dependency graphs from `Android.bp` Soong files.
- The README says the project builds and queries build graphs from blueprints in AOSP.
- The README lists graph generation and graph query commands, plus repo/git/Docker/AOSP-related setup that this benchmark intentionally excludes.

## Rationale

Build dependency graphs are stateful system surfaces: parsing, graph construction, dependency resolution, cycle handling, and query output must work together correctly. Individual components may pass unit tests, while system-level tests can expose failures in transitive dependency propagation, graph invariants, operation ordering, and error recovery.

## Benchmark Environment

The benchmark version does not require AOSP, repo, git checkout, Docker, or network access. It should run on small local input files with deterministic outputs.

## Benchmark Simplifications

- The benchmark uses `python main.py` with standard input commands instead of the original `bgraph` CLI.
- The module definition format is a small `module NAME { type = TYPE; deps = ... }`-style text format, not full Android Blueprint.
- The benchmark models dependency graph loading, replacement, querying, unresolved references, cycle detection, and removal.
- Output is deterministic line-oriented text; exact parse-error wording is not part of the public API.

## Non-Fabrication Notes

- No reference score is claimed in this packet.
- No candidate score or unit/system gap is claimed in this packet.
- The original BGraph CLI and AOSP integration are not copied or required.
- The benchmark is an abstraction of the source repository's build-graph state surface, not a line-by-line port.
