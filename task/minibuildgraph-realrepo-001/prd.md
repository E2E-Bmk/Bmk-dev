# MiniBuildGraph Public Product Packet

## Overview

Build `main.py`, a dependency-free Python tool for loading simplified build module definitions, constructing a directed dependency graph, and answering graph queries. It is inspired by build graph extraction tools and should feel like a small standard-library-friendly build dependency analyzer.

The program must be runnable from the solution directory:

```bash
python main.py
```

Use only the Python standard library.

The program reads newline-separated commands from standard input and writes deterministic output to standard output.

The program must not print an interactive prompt.

All command responses, including `OK` and `ERR ...` lines, are written to standard output. Standard error is not part of the public output contract.

## Feature Set

The product has six feature modules:

1. Build module parsing.
2. Mutable graph state and graph replacement.
3. Direct dependency and reverse dependency queries.
4. Transitive dependency traversal.
5. Cycle and unresolved dependency handling.
6. Error behavior and recovery.

These modules are intentionally state-dependent. Parsed module definitions feed graph construction; graph state feeds direct and reverse queries; direct edges feed transitive traversal; removed modules affect unresolved dependencies; cycles affect traversal and cycle checks; and failed loads should not corrupt the previously valid graph.

## Global Invariants

The following invariants define system correctness:

- Module names, module types, direct dependencies, unresolved dependencies, and reverse dependencies must remain distinct even when query output combines them.
- A successful `LOAD` replaces the entire current graph.
- A failed `LOAD` must preserve the previous graph unchanged.
- Dependency edges are directed from a module to the modules it depends on.
- Direct dependency queries and reverse dependency queries must be consistent views of the same graph.
- Transitive dependency queries must avoid duplicates and must terminate even when cycles exist.
- Removing a module must update `LIST`, dependency queries, reverse dependency queries, and unresolved dependency reporting consistently.
- Unresolved dependencies should be tracked as references, not silently discarded.
- All query outputs must be deterministic, usually lexicographic by module name.
- Malformed inputs should raise useful deterministic errors without poisoning later valid graph operations.
- Error output must remain line-oriented and deterministic.

## Command Input Model

The program reads commands from `stdin`.

Each line is one command.

Commands are executed sequentially.

Graph state persists across commands within a single run.

The program must not require network access, Docker, AOSP checkout, repository checkout, or external build tools.

## Module Definition Format

MiniBuildGraph loads module definitions from local text files.

Each module is written as one block:

```text
module NAME {
  type = TYPE
  deps = DEP1, DEP2, DEP3
}
```

Required behavior:

- `NAME` is the module name.
- `TYPE` is a string such as `binary`, `library`, `test`, or `tool`.
- `deps` is a comma-separated list of direct dependencies.
- `deps =` means the module has no direct dependencies.
- Whitespace around names, commas, braces, and equals signs is allowed.
- Module names are case-sensitive.
- Each module name must be unique in a loaded graph.
- Dependencies may refer to modules defined later in the same file.
- A dependency that is referenced but never defined is an unresolved dependency.

The parser only needs to support this simplified format. It does not need to support full Android Blueprint or Soong syntax.

## Commands

The tool must support the following commands:

1. `LOAD path`
2. `LIST`
3. `INFO name`
4. `DEPS name`
5. `RDEPS name`
6. `TRANSITIVE name`
7. `RTRANSITIVE name`
8. `CHECK_CYCLES`
9. `UNRESOLVED`
10. `REMOVE name`

## Loading

`LOAD path` loads module definitions from a local file.

`path` is a simple filesystem path token. Paths used by the benchmark contain no shell quoting, globbing, or environment-variable expansion.

If loading succeeds, the current graph is replaced by the newly loaded graph.

Successful output:

```text
OK
```

Loading fails with a deterministic `ERR ...` line if:

- the file does not exist
- the file has invalid syntax
- duplicate module names are found

If loading fails, the previous graph must remain unchanged.

Unresolved dependencies do not prevent loading.

## Listing Modules

`LIST` prints all loaded module names in lexicographic order, one per line.

If no graph is loaded or the graph has no modules, it prints no module lines.

## Module Info

`INFO name` prints information about one known module.

Output format:

```text
name=<NAME>
type=<TYPE>
deps=<comma-separated direct deps in lexicographic order>
```

If the module has no dependencies, print:

```text
deps=
```

Unknown modules should produce a deterministic error.

## Direct Dependencies

`DEPS name` prints the direct dependencies of `name`, one per line, in lexicographic order.

If the module has no dependencies, it prints no dependency lines.

Unknown modules should produce a deterministic error.

## Reverse Dependencies

`RDEPS name` prints modules that directly depend on `name`, one per line, in lexicographic order.

If no module directly depends on `name`, it prints no module lines.

A name may appear in `RDEPS` even if it is unresolved, as long as loaded modules refer to it.

If the name is neither a known module nor an unresolved referenced dependency, the command should produce a deterministic unknown-module error.

## Transitive Dependencies

`TRANSITIVE name` prints all recursive dependencies of `name`, one per line, in lexicographic order.

The result includes direct dependencies and dependencies reachable through any number of dependency edges.

Each dependency name must appear at most once.

Traversal must terminate safely even when the graph contains cycles.

The starting module itself should not be printed solely because a cycle reaches it again.

Unknown modules should produce a deterministic error.

## Transitive Reverse Dependencies

`RTRANSITIVE name` prints all recursive reverse dependencies of `name`, one per line, in lexicographic order.

The result includes modules that directly or indirectly depend on `name`.

Each module name must appear at most once.

A name may be used as a reverse-dependency target even if it is unresolved, as long as loaded modules refer to it.

The starting target itself should not be printed solely because a reverse traversal cycle reaches it again.

If the name is neither a known module nor an unresolved referenced dependency, the command should produce a deterministic unknown-module error.

## Cycle Detection

`CHECK_CYCLES` checks whether the current graph contains at least one dependency cycle.

If a cycle exists, output:

```text
CYCLE
```

If no cycle exists, output:

```text
ACYCLIC
```

Unresolved dependencies do not by themselves count as cycles.

## Unresolved Dependencies

`UNRESOLVED` prints unresolved dependency names in lexicographic order, one per line.

An unresolved dependency is a dependency name referenced by at least one module but not defined as a module.

If there are no unresolved dependencies, it prints no dependency lines.

## Removing Modules

`REMOVE name` removes a known module from the graph.

After removal:

- the removed module no longer appears in `LIST`
- dependencies from the removed module disappear
- other modules that depended on the removed module now refer to it as an unresolved dependency
- direct dependency, reverse dependency, transitive dependency, cycle, and unresolved queries must reflect the updated graph

Successful output:

```text
OK
```

If the module is unknown, the command should fail and the graph must remain unchanged.

## Error Behavior and Recovery

Invalid commands should output:

```text
ERR invalid command
```

Queries for unknown modules should output:

```text
ERR unknown module
```

Failed `LOAD` commands must not replace or partially mutate the current graph.

Failed `REMOVE` commands must not mutate the graph.

Invalid syntax in an input file must not partially update the graph.

Exact parse-error message text is not public API, but errors must be deterministic and distinguishable from successful output.

For load failures, implementations may use a stable message such as `ERR load failed`.

## Non-Goals

Do not implement full Android Blueprint syntax.

Do not implement:

- Soong evaluation
- variables or macros
- conditional build logic
- file globbing
- package visibility rules
- actual compilation
- build execution
- network access
- repository checkout
- Docker-based execution
- parallel execution
- persistent storage across program runs

The goal is a practical compatibility subset with robust parsing, graph construction, dependency traversal, mutation, and recovery behavior.

## Evaluation Style

Hidden tests are split into two scores:

- Unit tests exercise one feature module at a time with short command sequences and small input files.
- System tests exercise interactions across at least two modules. They inspect final graph state, direct and reverse dependency consistency, transitive traversal, cycle behavior, unresolved dependency reporting, mutation after removal, graph replacement after loading, and recovery after failed operations.

System tests are labeled by dimension:

- `cross_feature_dataflow`
- `state_accumulation`
- `global_invariant`
- `error_atomicity`
- `operation_order_sensitivity`
- `boundary_crossing`

The benchmark does not inspect private implementation details.
