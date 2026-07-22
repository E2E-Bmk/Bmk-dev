# Griffe Specification

## Product Overview

Griffe extracts the public structure of Python code into a semantic object graph. A package, module, class, function, attribute, type alias, import alias, parameter, decorator, and docstring becomes a navigable model object rather than remaining only source text. The same graph supports static source analysis, runtime inspection, JSON serialization, API compatibility checks, extensions, and command-line output.

This specification covers local files, local packages, installed modules, and temporary local Git repositories. Network package downloads and remote repository access are outside the supported scope.

## Scope

The covered feature areas are:

- loading a local module or package by import name or filesystem path;
- loading a dotted object path while retaining the graph for its containing package;
- static analysis, forced runtime inspection, and controlled fallback from static analysis to inspection;
- modules collections shared by a reusable loader;
- semantic models for modules, classes, functions, attributes, type aliases, aliases, decorators, parameters, type parameters, and docstrings;
- graph navigation, object paths, object kinds, visibility, imports, exports, and inherited members;
- alias target resolution and alias-chain behavior;
- minimal and full dictionary or JSON serialization with model reconstruction;
- Google, NumPy, Sphinx, and automatically detected docstring parsing;
- API breakage detection between two already loaded object graphs;
- extension loading and graph mutation through documented extension hooks;
- the `griffe` command with `dump` and `check` subcommands over local inputs.

## Installable Surface

The distribution is installed as `griffe`. The Python library is imported as `griffe`, and its supported API is exposed directly from that top-level module. The CLI support package is importable as `griffecli`; its callable entry points are also re-exported by `griffe` when the CLI package is installed.

The primary graph types are `Object`, `Module`, `Class`, `Function`, `Attribute`, `TypeAlias`, `Alias`, `Decorator`, `Parameter`, `Parameters`, `TypeParameter`, and `TypeParameters`. Their public kind values are represented by `Kind`, `ObjectKind`, and `ParameterKind`. Shared graph state is represented by `ModulesCollection` and `LinesCollection`.

The loading surface is `load`, `GriffeLoader`, `visit`, and `inspect`. The serialization surface is `JSONEncoder` and `json_decoder`, together with the model methods `as_dict`, `as_json`, and `from_json`.

The docstring surface is `Docstring`, `DocstringStyle`, `Parser`, `DocstringOptions`, `parse`, `parse_auto`, `parse_google`, `parse_numpy`, `parse_sphinx`, and `infer_docstring_style`. The retained structured result types are `DocstringElement`, `DocstringNamedElement`, `DocstringParameter`, `DocstringReturn`, `DocstringRaise`, `DocstringYield`, `DocstringAdmonition`, `DocstringAttribute`, `DocstringDeprecated`, `DocstringSection`, `DocstringSectionText`, `DocstringSectionParameters`, `DocstringSectionReturns`, `DocstringSectionRaises`, `DocstringSectionYields`, `DocstringSectionExamples`, `DocstringSectionAttributes`, `DocstringSectionAdmonition`, and `DocstringSectionDeprecated`.

The API compatibility surface is `find_breaking_changes`, `Breakage`, `BreakageKind`, `ExplanationStyle`, `ParameterMovedBreakage`, `ParameterRemovedBreakage`, `ParameterChangedKindBreakage`, `ParameterChangedDefaultBreakage`, `ParameterChangedRequiredBreakage`, `ParameterAddedRequiredBreakage`, `ObjectRemovedBreakage`, `ObjectChangedKindBreakage`, `AttributeChangedValueBreakage`, and `ClassRemovedBaseBreakage`. `ReturnChangedTypeBreakage`, `AttributeChangedTypeBreakage`, and their corresponding kind values remain importable, but type-compatibility detection is not promised in this scope.

The extension surface is `Extension`, `Extensions`, `load_extensions`, `DataclassesExtension`, and `UnpackTypedDictExtension`. The relevant exception hierarchy is `GriffeError`, `LoadingError`, `NameResolutionError`, `AliasResolutionError`, `CyclicAliasError`, `UnimportableModuleError`, `ExtensionError`, and `ExtensionNotLoadedError`.

The command-line entry point is `griffe`. Calling `python -m griffe` is supported and invokes the same command dispatcher. The callable CLI surface is `get_parser`, `dump`, `check`, and `main` from both `griffe` and `griffecli`.

## Product State Model

Griffe exposes one semantic state through three public projections:

1. The input projection is Python source or an importable runtime object.
2. The graph projection is a tree of model objects connected by parent, member, collection, and alias relationships.
3. The output projection is JSON or dictionaries, breakage objects, extension-modified graph state, and CLI output derived from that graph.

The graph is the shared fact source. Loading or inspection must establish the graph before serialization, breakage detection, or CLI output derives another view.

The following state invariants apply throughout the package:

- An object returned for a dotted request must be the same logical object reachable from the loaded package graph at that dotted path.
- A member inserted through public graph assignment must report the assigned parent and must be reachable through both `members` and item access.
- A resolved alias must expose the canonical path and public metadata of its final target while retaining its own import path.
- A graph reconstructed from minimal JSON must preserve object kinds, names, member relationships, parameters, aliases, and annotations required for navigation and breakage detection.
- A docstring parsed during loading must expose the same structured sections as parsing that `Docstring` directly with the same parser and options.
- A breakage reported by the Python API must cause the local `griffe check` workflow over the same two versions to return a nonzero breakage result.
- An extension mutation completed during loading must be visible through graph navigation and subsequent serialization.
- A package emitted by `griffe dump` must describe the same top-level name, kinds, members, and public paths as the Python graph loaded with equivalent options.

## Loading And Analysis

`load(objspec=None, /, *, submodules=True, try_relative_path=True, extensions=None, search_paths=None, docstring_parser=None, docstring_options=None, lines_collection=None, modules_collection=None, allow_inspection=True, force_inspection=False, store_source=True, find_stubs_package=False, resolve_aliases=False, resolve_external=None, resolve_implicit=False)` loads an import name, dotted object path, module file, or package directory.

When `objspec` names a nested object, Griffe must load the containing package and return the requested object from that graph. When `objspec` explicitly identifies a relative filesystem path and `try_relative_path` is true, Griffe must accept that path as a load target. When `try_relative_path` is false, Griffe must treat `objspec` as an import-style name resolved through the configured search paths and import environment. An explicit `search_paths` entry governs import-name lookup; this specification does not assign current-directory precedence over that entry.

When source is available and `force_inspection` is false, loading must use static analysis. When source is unavailable and `allow_inspection` is true, loading must inspect the runtime object. When `force_inspection` is true, loading must inspect the runtime object even when source exists. Every loaded object must expose `analysis` as `"static"` or `"dynamic"` according to the analysis that produced it.

When source is unavailable and `allow_inspection` is false, loading must raise `ModuleNotFoundError` rather than importing the object. A request that cannot be found or imported must fail rather than return an empty graph.

`GriffeLoader` accepts the same extension, search-path, parser, collection, inspection, and source-storage configuration. Reusing one loader must reuse its `modules_collection`; objects loaded by separate calls through that loader must be addressable through the same collection, which permits aliases to resolve across loaded packages.

`visit(module_name, filepath, code, ...)` must statically analyze the supplied code and return a `Module` whose name, members, line data, docstrings, imports, exports, and annotations reflect that code. `inspect(module_name, ...)` must import and inspect the runtime module and return a `Module` with `analysis == "dynamic"`.

## Graph Models And Navigation

Every `Object` has a declared `name`, optional `parent`, `members`, optional `docstring`, `labels`, `imports`, optional `exports`, `runtime`, `public`, `deprecated`, `extra`, and `analysis`. A top-level module has no parent. A regular object's `path` and `canonical_path` must be its dotted location from the top-level module.

`Module`, `Class`, `Function`, `Attribute`, and `TypeAlias` must report their corresponding `Kind` and boolean kind predicates. `Function` must expose ordered `parameters`, a return annotation through `returns`, decorators, overloads, and type parameters. `Attribute` must expose its annotation and value. `Class` must expose bases, decorators, type parameters, and constructor parameters when an initializer is present. `TypeAlias` must expose its assigned value and type parameters.

An object's `members` mapping contains declared members. Item access must accept a single member name, a dot-separated path, or a tuple of path parts. These forms must reach the same object. Missing member access must raise `KeyError`.

Assigning a model through item assignment or `set_member` must update the inserted object's parent. Deleting through item deletion or `del_member` must remove the declared member. Direct mutation of the raw `members` dictionary is not required to repair parent or alias bookkeeping.

For a class, `inherited_members` must expose inherited members as `Alias` objects whose `inherited` value is true. `all_members` must combine declared and inherited members, with declared members taking the name when a subclass overrides an inherited name. If a base cannot be resolved from loaded packages, it must be omitted from resolved inheritance results rather than replaced with a fabricated class.

Module-level visibility must follow explicit exports when a module defines `__all__`. Without `__all__`, a module-level object must be public when its name is not private and it was not imported from another module. A class-level member must be public when its name is not private and it was not imported. Setting an object's `public` value must override the inferred public result.

`Parameters` is an ordered container. It must support iteration, length, membership by parameter name, lookup by integer index, and lookup by name. Name lookup must ignore leading `*` or `**`. Setting an unknown name must append the supplied parameter; setting a known name or index must replace it. Deleting an unknown name must raise `KeyError`. `add` must raise `ValueError` when the same parameter name is already present.

`Parameter.required` must be true exactly when the parameter has no default. `ParameterKind` must expose the values `positional-only`, `positional or keyword`, `variadic positional`, `keyword-only`, and `variadic keyword`.

## Alias Resolution

An `Alias` retains its own `name`, parent, import line information, and `target_path`. Before resolution, `resolved` must be false. When the target is available in the shared modules collection, accessing target-backed public metadata or calling `resolve_target()` must resolve the alias and set `resolved` to true.

The alias `path` must remain the dotted location where the alias appears. Its `canonical_path` must be the final target's defining path after successful resolution. The `target` property must return the next target object, while `final_target` must follow an alias chain to the final non-alias object.

When no target is found in the modules collection, target-dependent access must raise `AliasResolutionError`. When an alias chain forms a cycle, resolution must raise `CyclicAliasError`. An attempted chain resolution must not leave a prefix of the chain marked resolved when the final target cannot be resolved.

## Docstrings

`Docstring(value, *, lineno=None, endlineno=None, parent=None, parser=None, parser_options=None)` must store `value` after Python-style dedenting and removal of trailing whitespace. Its `lines` projection must equal the cleaned value split on newline boundaries.

`Docstring.parse(parser=None, **options)` must use the parser passed to the call, otherwise the parser stored on the docstring, otherwise it must return a single `DocstringSectionText`. Explicit call options must be used for that parse; stored `parser_options` must be used when explicit options are absent.

The `parse`, `parse_google`, `parse_numpy`, and `parse_sphinx` functions must return ordered `DocstringSection` instances. Text, parameters, returns, raises, yields, examples, attributes, admonitions, and deprecated blocks must use their corresponding retained section types. Parameter-like section elements must expose their documented name, annotation, description, and default information when present.

When a docstring is attached to a `Function`, Google, NumPy, and Sphinx parsing must use the parent function's parameter or return annotations when the docstring omits those types and the style permits that inference. An unknown parameter mentioned by a docstring must remain representable; enabling warnings must not turn the parse into an exception.

`parse_auto` and `infer_docstring_style` must support `auto`, `google`, `numpy`, and `sphinx` parser identifiers. With default heuristic detection, `infer_docstring_style` must return the selected parser and `None` when a style is detected or a default is supplied; when no style is selected it must return `(None, None)`. `parse_auto` must use the selected parser and return the parsed sections.

The `parsed` property must cache its first parsed result. Changing `parser` or `parser_options` after `parsed` has been accessed must not silently replace the cached sections. Calling `parse(...)` directly with another parser must still return a fresh result for that call.

Requesting `Docstring.source` without a parent, without usable line numbers, or from a namespace-package parent must raise `ValueError`.

## Serialization

Every retained graph model must provide `as_dict`. `Object` and `Alias` must provide `as_json` and `from_json`. Minimal serialization must contain the fields required to reconstruct the supported graph; full serialization must include additional derived and descriptive fields without changing the meaning of the minimal fields.

`as_json(full=False, **json_options)` must encode the minimal dictionary with `JSONEncoder`. `as_json(full=True, **json_options)` must encode the full dictionary. JSON options such as indentation and key sorting must be forwarded to the JSON encoder.

`from_json` and `json_decoder` must reconstruct retained model objects, parameters, type parameters, aliases, annotations, docstrings, and nested members from valid Griffe JSON. A reconstructed graph must support normal item navigation, kind checks, parameter lookup, alias resolution when its targets are present, docstring access, and breakage detection.

Serializing multiple packages through `dump` must produce a JSON object whose keys are package names and whose values are serialized top-level modules. Writing to one output stream or file must produce that combined object. When the output string contains a `{package}` placeholder, one file per package must be written with the placeholder replaced by the package name.

## API Change Detection

`find_breaking_changes(old_obj, new_obj)` must recursively compare the public API rooted at two graphs and yield `Breakage` objects. Each breakage must expose its related object, kind, old value, new value, and an explanation through the requested `ExplanationStyle`.

The comparison must report these library-specific incompatibilities when they affect public objects:

- moving a positional parameter;
- removing a parameter that is not accepted by an appropriate variadic parameter;
- changing a parameter kind incompatibly;
- changing a parameter default;
- changing a parameter from optional to required;
- adding a required parameter that is not absorbed by a variadic parameter;
- removing a public object;
- changing a public object between module, class, function, attribute, or type-alias kinds;
- changing the value of a public attribute;
- removing a base from a public class.

Removing or changing a non-public object must not produce an API breakage. Return-type and attribute-type compatibility checks are not required even though their breakage classes remain importable.

The `Breakage.kind` value and concrete breakage class must agree. `ExplanationStyle.ONE_LINE`, `VERBOSE`, `MARKDOWN`, `GITHUB`, and `AZURE_DEVOPS` must select the documented output family. Exact wording, ANSI coloring, file formatting, and whitespace are not part of this contract; the explanation must identify the affected public path and the kind of incompatibility.

## Extensions

An extension is an `Extension` subclass whose documented hook methods receive model objects during analysis or after loading. `Extension.on_package(*, pkg, loader, **kwargs)` is the public completed-package hook: `pkg` is the loaded package graph, `loader` is the active loader, and the hook must run before `load` returns and before serialization or dump derives output from the graph. `Extensions` must preserve the configured extension instances and dispatch a named hook to extensions that implement it.

`load_extensions` must accept extension instances, extension classes, importable extension names, and configured extension mappings. It must return an `Extensions` container. A name that cannot be imported or a loaded object that is not a valid extension must raise `ExtensionNotLoadedError` or another `ExtensionError` rather than being ignored.

Graph mutations made by load hooks must be visible when `load` returns. If an extension inserts, removes, relabels, or updates an object through public graph operations, navigation and later serialization must reflect that mutation.

`DataclassesExtension` must identify supported dataclasses during loading and expose their generated constructor parameters through the class model. `UnpackTypedDictExtension` must expand an unpacked typed-dictionary keyword parameter into the represented keyword parameters when sufficient static information is present. Unsupported or unresolved inputs must leave the graph usable rather than fabricating members.

## Command-Line Workflows

`griffe dump PACKAGE...` must load each requested local package and write JSON to standard output by default. `--output` must select a file or a `{package}` file template. `--full`, `--docstyle`, `--docopts`, `--resolve-aliases`, `--resolve-implicit`, `--resolve-external`, `--no-resolve-external`, `--search`, `--sys-path`, `--no-inspection`, `--force-inspection`, and `--find-stubs-packages` must map to the corresponding loading or serialization behavior.

The callable `dump(packages, ...)` and the CLI subcommand must return `0` when all requested packages were loaded and emitted. They must return `1` when at least one requested package could not be loaded or an extension configuration failed. Successfully loaded packages must remain serializable even when another requested package fails.

`griffe check PACKAGE --against REF` must compare a local package with the selected older local Git reference. `--base-ref` must select a local Git reference for the new side instead of the working tree. The callable `check` must support an explicit local `against_path`. `--format` and `--verbose` must select the explanation style without changing which breakages are found.

The check workflow must return `0` when no breakages are found, `1` when one or more breakages are found, and `2` when the local repository or requested Git reference cannot be resolved. Breakage explanations must be written to standard error. Invalid command syntax must produce a nonzero command result.

`get_parser()` must return an argument parser with required `dump` and `check` subcommands. `main(args=None)` must dispatch the supplied argument list, or process command-line arguments when `args` is omitted, and return the selected subcommand's exit code.

## Error Semantics

- Loading an unavailable object with inspection disabled must raise `ModuleNotFoundError`.
- Resolving a missing alias target must raise `AliasResolutionError`.
- Resolving a cyclic alias chain must raise `CyclicAliasError`.
- Looking up or deleting an absent member or parameter by name must raise `KeyError`.
- Adding a duplicate parameter name through `Parameters.add` must raise `ValueError`.
- Requesting unavailable original docstring source must raise `ValueError`.
- Loading an invalid extension must raise `ExtensionNotLoadedError` or `ExtensionError`.
- A malformed serialized payload must raise a parsing or reconstruction exception; it must not return a partially valid top-level object.
- CLI package-load or extension failures must return the documented nonzero status rather than report success.

Exception message wording is not part of the public contract.

## Cross-View Invariants

- Static `load` and direct `visit` over the same source must return graphs with the same declared object names, kinds, parent paths, parameters, annotations, imports, exports, and docstring values.
- Forced `inspect` and static `load` over a simple importable module must return the same public member names and compatible kinds even when source locations or expression detail differ.
- Dotted item access, tuple item access, and repeated member access must return the same logical graph object.
- An alias path must describe the import location, while its canonical path and serialized target path must describe the defining location.
- Minimal JSON round-trip must preserve every fact used by navigation and `find_breaking_changes`.
- Full JSON must add information without changing names, kinds, paths, parameter order, alias targets, or docstring meaning from the minimal projection.
- Parser selection during loading and direct parsing of the attached `Docstring` with the same style must return equivalent section kinds and element values.
- An extension mutation must be visible through `members`, item access, JSON, and CLI dump output.
- A public incompatibility found by `find_breaking_changes` must make the equivalent local check workflow return `1`; no incompatibility must make it return `0`.
- Dumping a package through the callable API and through the CLI with equivalent options must produce JSON describing the same semantic graph.

## Representative Workflows

### Load, navigate, and serialize

Create a local package containing a module, a class, a method, an imported alias, annotations, parameters, and docstrings. Load the package with a search path and a docstring parser. Navigate to the method through a dot-separated item path, inspect its parameter and return annotations, resolve the imported alias, serialize the package to minimal JSON, reconstruct it with `from_json`, and navigate to the same method and alias in the reconstructed graph.

### Compare two local API versions

Create old and new local package trees. Load both graphs. The new version removes one public object, changes one public function parameter default, and adds one required parameter. `find_breaking_changes` must return the corresponding concrete breakage types. A local `griffe check` workflow over equivalent Git versions must return `1`. When the new tree preserves the old public contract, both the iterator and CLI workflow must report no breakage.

### Extend and dump

Define an `Extension` that adds a documented label or member in a load hook. Load a local package with that extension, verify the graph mutation through navigation, and dump the package. The JSON output must contain the extension-modified state.

## Non-Goals

- downloading or installing packages from PyPI through `load_pypi`;
- cloning or contacting remote Git repositories;
- exact support for every Git hosting service or remote URL form;
- low-level AST node helpers and direct construction of the full expression-node family;
- exact source-code rendering, `repr` strings, log messages, ANSI colors, or exception message text;
- logger configuration and logger-patching helpers;
- tree-rendering and temporary test-construction helpers;
- finder, importer, merger, statistics, and agent internals beyond the public workflows described above;
- exhaustive support for every docstring element subtype or parser warning;
- return-type and attribute-type compatibility inference;
- stubs-only package discovery beyond accepting and forwarding the documented option;
- live network services, package indexes, or remote credentials.

## Invocation Protocol

The installed console command is `griffe`. `python -m griffe` is supported and must invoke the same dispatcher. The separately installed `griffecli` command is outside the primary invocation contract.

| Situation | Exit code |
|---|---:|
| `dump` loads and emits every requested package | 0 |
| `dump` misses at least one package or cannot load extensions | 1 |
| `check` finds no breakage | 0 |
| `check` finds at least one breakage | 1 |
| `check` cannot resolve the local repository or Git reference | 2 |
| invalid command syntax | nonzero |

## Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Implementation Guidance

Compatibility covers importability, individual model and container behavior, static and dynamic loading, alias errors, docstring parsing, serialization round-trips, extension mutation, API breakage classification, and complete local CLI workflows. The upstream module layout, private helpers, exact diagnostic wording, exact JSON key order, exact explanation formatting, and a particular parser implementation are not required.
