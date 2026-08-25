# Griffe Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

This package extracts the public structure of Python code into a semantic object graph. A package, module, class, function, attribute, type alias, import alias, parameter, decorator, and docstring becomes a navigable model object rather than remaining only source text. The same graph supports static source analysis, runtime inspection, JSON serialization, API compatibility checks, extensions, and command-line output.

This specification covers local files, local packages, installed modules, and temporary local Git repositories. Remote package indexes and remote repository access are not covered.

## Non-Goals

- This specification does not require Remote package download or installation through `load_pypi`.
- This specification does not require Cloning or contacting remote Git repositories.
- This specification does not require Exact support for every remote hosting service or remote URL form.
- This specification does not require Low-level AST node helpers or direct construction of the full expression-node family.
- This specification does not require Exact source-code rendering, `repr` strings, log messages, ANSI colors, or exception message text.
- This specification does not require Logger configuration or logger-patching helpers.
- This specification does not require Tree-rendering or temporary test-construction helpers.
- This specification does not require Finder, importer, merger, statistics, or agent internals beyond the public workflows described above.
- This specification does not require Exhaustive support for every docstring element subtype or parser warning.
- This specification does not require Return-type or attribute-type compatibility inference.
- This specification does not require Stubs-only package discovery beyond accepting or forwarding the documented option.
- This specification does not require Live network services, package indexes, or remote credentials.

## Representative Workflows

### Load, navigate, and serialize

```python
from griffe import load, Module, Function, Parameters

pkg = load("mypkg", search_paths=["src"], docstring_parser="google")
method = pkg["mypkg.MyClass.my_method"]
assert isinstance(method, Function)
assert "param1" in [p.name for p in method.parameters]

json_str = pkg.as_json()
reconstructed = Module.from_json(json_str)
same_method = reconstructed["mypkg.MyClass.my_method"]
assert same_method.name == method.name
```

Loading a local package populates the object graph. Navigating via a dot-separated path returns the `Function` with its parameters and annotations. `as_json()` serializes the graph to JSON, and `from_json` reconstructs a navigable graph preserving the same members.

### Compare two local API versions

```python
from griffe import load, find_breaking_changes, ObjectRemovedBreakage, ParameterChangedDefaultBreakage, ParameterAddedRequiredBreakage

old_pkg = load("mypkg", search_paths=["old_src"])
new_pkg = load("mypkg", search_paths=["new_src"])

breakages = list(find_breaking_changes(old_pkg, new_pkg))
breakage_kinds = {type(b) for b in breakages}
assert ObjectRemovedBreakage in breakage_kinds
assert ParameterChangedDefaultBreakage in breakage_kinds
assert ParameterAddedRequiredBreakage in breakage_kinds
```

When the new version removes a public object, changes a parameter default, and adds a required parameter, `find_breaking_changes` yields the corresponding concrete breakage types. The equivalent `griffe check` CLI returns exit code `1` when breakage is found.

### Extend and dump

```python
from griffe import load, Extension, Extensions, load_extensions

class LabelExtension(Extension):
    def on_package(self, *, pkg, loader, **kwargs):
        pkg.labels.add("custom-label")

extensions = Extensions(LabelExtension())
pkg = load("mypkg", search_paths=["src"], extensions=extensions)
assert "custom-label" in pkg.labels

json_str = pkg.as_json()
assert "custom-label" in json_str
```

Defining an `Extension` subclass with `on_package` allows graph mutation during loading. The added label is visible through navigation and persists in the serialized JSON output.

## Loading And Analysis

Loading populates the object graph from Python source or runtime inspection, supporting import names, dotted paths, module files, and package directories.

**The load function.** `load` accepts an object specifier that may be an import name, a dotted object path, a module file, or a package directory. When `submodules` is true, loading includes submodules. When `search_paths` is provided, it controls where import names are resolved. When `docstring_parser` is set, parsed docstrings use that parser style. When `extensions` is supplied, extension hooks run during loading. Additional options include `lines_collection`, `modules_collection`, `allow_inspection`, `force_inspection`, `store_source`, `find_stubs_package`, `resolve_aliases`, `resolve_external`, and `resolve_implicit`.

When `objspec` names a nested object, Griffe must load the containing package and return the requested object from that graph. When `objspec` explicitly identifies a relative filesystem path and `try_relative_path` is true, Griffe must accept that path as a load target. When `try_relative_path` is false, Griffe must treat `objspec` as an import-style name resolved through the configured search paths and import environment. An explicit `search_paths` entry governs import-name lookup; this specification does not assign current-directory precedence over that entry.

When source is available and `force_inspection` is false, loading must use static analysis. When source is unavailable and `allow_inspection` is true, loading must inspect the runtime object. When `force_inspection` is true, loading must inspect the runtime object even when source exists. Every loaded object must expose `analysis` as `"static"` or `"dynamic"` according to the analysis that produced it.

When source is unavailable and `allow_inspection` is false, loading must raise `ModuleNotFoundError` rather than importing the object. A request that cannot be found or imported must fail rather than return an empty graph.

`GriffeLoader` accepts the same extension, search-path, parser, collection, inspection, and source-storage configuration. Reusing one loader must reuse its `modules_collection`; objects loaded by separate calls through that loader must be addressable through the same collection, which permits aliases to resolve across loaded packages.

`visit(module_name, filepath, code, ...)` must statically analyze the supplied code and return a `Module` whose name, members, line data, docstrings, imports, exports, and annotations reflect that code. `inspect(module_name, ...)` must import and inspect the runtime module and return a `Module` with `analysis == "dynamic"`.

## Graph Models And Navigation

The graph model represents Python code as a navigable tree of typed objects with members, parameters, annotations, and relationships.

**Object fundamentals.** Every `Object` has a declared `name`, optional `parent`, `members`, optional `docstring`, `labels`, `imports`, optional `exports`, `runtime`, `public`, `deprecated`, `extra`, and `analysis`. A top-level module has no parent. A regular object's `path` and `canonical_path` must be its dotted location from the top-level module.

**Kind hierarchy.** `Module`, `Class`, `Function`, `Attribute`, and `TypeAlias` must report their corresponding `Kind` and boolean kind predicates (`is_module`, `is_class`, `is_function`, `is_attribute`, `is_type_alias`). `Function` must expose ordered `parameters`, a return annotation through `returns`, decorators, overloads, and type parameters. `Attribute` must expose its annotation and value. `Class` must expose bases, decorators, type parameters, and constructor parameters when an initializer is present. `TypeAlias` must expose its assigned value and type parameters.

**Member access.** An object's `members` mapping contains declared members. Item access must accept a single member name, a dot-separated path, or a tuple of path parts. These forms must reach the same object. Missing member access must raise `KeyError`.

**Member mutation.** Assigning a model through item assignment or `set_member` must update the inserted object's parent. Deleting through item deletion or `del_member` must remove the declared member. Direct mutation of the raw `members` dictionary is not required to repair parent or alias bookkeeping.

**Inheritance.** For a class, `inherited_members` must expose inherited members as `Alias` objects whose `inherited` value is true. `all_members` must combine declared and inherited members, with declared members taking the name when a subclass overrides an inherited name. If a base cannot be resolved from loaded packages, it must be omitted from resolved inheritance results rather than replaced with a fabricated class.

**Visibility.** Module-level visibility must follow explicit exports when a module defines `__all__`. Without `__all__`, a module-level object must be public when its name is not private and it was not imported from another module. A class-level member must be public when its name is not private and it was not imported. Setting an object's `public` value must override the inferred public result.

**Parameters.** `Parameters` is an ordered container. It must support iteration, length, membership by parameter name, lookup by integer index, and lookup by name. Name lookup must ignore leading `*` or `**`. Setting an unknown name must append the supplied parameter; setting a known name or index must replace it. Deleting an unknown name must raise `KeyError`. `add` must raise `ValueError` when the same parameter name is already present. `Parameter.required` must be true exactly when the parameter has no default. `ParameterKind` must expose the values `positional-only`, `positional or keyword`, `variadic positional`, `keyword-only`, and `variadic keyword`.

## Alias Resolution

An `Alias` retains its own `name`, parent, import line information, and `target_path`. Before resolution, `resolved` must be false. When the target is available in the shared modules collection, accessing target-backed public metadata or calling `resolve_target()` must resolve the alias and set `resolved` to true.

The alias `path` must remain the dotted location where the alias appears. Its `canonical_path` must be the final target's defining path after successful resolution. The `target` property must return the next target object, while `final_target` must follow an alias chain to the final non-alias object.

When no target is found in the modules collection, target-dependent access must raise `AliasResolutionError`. When an alias chain forms a cycle, resolution must raise `CyclicAliasError`. An attempted chain resolution must not leave a prefix of the chain marked resolved when the final target cannot be resolved.

## Docstrings

Docstrings capture the documentation text attached to code objects, providing structured parsing, caching, and style detection.

**Construction and normalization.** A `Docstring` must store its value after Python-style dedenting and removal of trailing whitespace. It accepts the raw docstring text, optional line number information through `lineno` and `endlineno`, an optional `parent` object, an optional `parser` for default parsing, and optional `parser_options`. Its `lines` projection must equal the cleaned value split on newline boundaries.

**Parsing.** `Docstring.parse` must use the parser passed to the call if present, otherwise the parser stored on the docstring, otherwise it must return a single `DocstringSectionText` containing the full text. Explicit call options must be used for that parse; stored `parser_options` must be used when explicit options are absent.

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

## State Model

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

## Public Interface

### Import Surface

The distribution is installed as `griffe`. The Python library is imported as `griffe`, and its supported API is exposed directly from that top-level module. The CLI support package is importable as `griffecli`; its callable entry points are also re-exported by `griffe` when the CLI package is installed.

```python
import griffe
import griffecli
from griffe import (
    Object, Module, Class, Function, Attribute, TypeAlias, Alias,
    Decorator, Parameter, Parameters, TypeParameter, TypeParameters,
    Kind, ObjectKind, ParameterKind,
    ModulesCollection, LinesCollection,
    load, GriffeLoader, visit, inspect,
    JSONEncoder, json_decoder,
    Docstring, DocstringStyle, Parser, DocstringOptions,
    parse, parse_auto, parse_google, parse_numpy, parse_sphinx,
    infer_docstring_style,
    DocstringElement, DocstringNamedElement, DocstringParameter,
    DocstringReturn, DocstringRaise, DocstringYield, DocstringAdmonition,
    DocstringAttribute, DocstringDeprecated, DocstringSection,
    DocstringSectionText, DocstringSectionParameters, DocstringSectionReturns,
    DocstringSectionRaises, DocstringSectionYields, DocstringSectionExamples,
    DocstringSectionAttributes, DocstringSectionAdmonition,
    DocstringSectionDeprecated,
    find_breaking_changes, Breakage, BreakageKind, ExplanationStyle,
    ParameterMovedBreakage, ParameterRemovedBreakage,
    ParameterChangedKindBreakage, ParameterChangedDefaultBreakage,
    ParameterChangedRequiredBreakage, ParameterAddedRequiredBreakage,
    ObjectRemovedBreakage, ObjectChangedKindBreakage,
    AttributeChangedValueBreakage, ClassRemovedBaseBreakage,
    ReturnChangedTypeBreakage, AttributeChangedTypeBreakage,
    Extension, Extensions, load_extensions,
    DataclassesExtension, UnpackTypedDictExtension,
    GriffeError, LoadingError, NameResolutionError, AliasResolutionError,
    CyclicAliasError, UnimportableModuleError, ExtensionError,
    ExtensionNotLoadedError,
    get_parser, dump, check, main,
)
from griffecli import get_parser, dump, check, main
```

`ReturnChangedTypeBreakage`, `AttributeChangedTypeBreakage`, and their corresponding kind values remain importable, but type-compatibility detection is not promised in this scope.

The command-line entry point is `griffe`. Calling `python -m griffe` is supported and invokes the same command dispatcher.

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `load` | function | Loads an import name, path, or package into the graph |
| `GriffeLoader` | class | Reusable loader with shared module collections |
| `visit` | function | Statically analyzes supplied source code |
| `inspect` | function | Inspects a runtime module into the graph |
| `Object` | class | Base graph object with members and metadata |
| `Module` | class | Top-level or nested module object |
| `Class` | class | Class object with bases and members |
| `Function` | class | Function or method with parameters and return annotation |
| `Attribute` | class | Attribute with annotation and value |
| `TypeAlias` | class | Type alias with assigned value |
| `Alias` | class | Import alias with target resolution |
| `Parameter` | class | One callable parameter |
| `Parameters` | class | Ordered parameter container |
| `Docstring` | class | Parsed and unparsed docstring state |
| `find_breaking_changes` | function | Compares two graphs for public API incompatibilities |
| `Breakage` | class | One reported incompatibility |
| `Extension` | class | Load hook base class |
| `Extensions` | class | Configured extension dispatch container |
| `load_extensions` | function | Loads extension instances or classes by name |
| `DataclassesExtension` | class | Adds dataclass constructor parameters to classes |
| `UnpackTypedDictExtension` | class | Expands unpacked typed-dictionary parameters |
| `JSONEncoder` | class | Encodes graph objects to JSON |
| `json_decoder` | function | Decodes Griffe JSON into graph objects |
| `dump` | function | Serializes one or more packages to JSON |
| `check` | function | CLI helper for local API breakage checks |
| `get_parser` | function | Builds the CLI argument parser |
| `main` | function | CLI dispatcher |
| `GriffeError` | exception | Base Griffe error |
| `AliasResolutionError` | exception | Missing alias target |
| `CyclicAliasError` | exception | Cyclic alias chain |
| `ExtensionError` | exception | Extension loading or dispatch failure |

Behavioral details for loading options, alias resolution, docstring parsing, serialization, breakage detection, and extension hooks are defined in the behavior sections above.

### CLI Entry Points

The installed console command is `griffe`. `python -m griffe` is supported and must invoke the same dispatcher. The separately installed `griffecli` command is outside the primary invocation contract.

| Situation | Exit code |
|---|---:|
| `dump` loads and emits every requested package | 0 |
| `dump` misses at least one package or cannot load extensions | 1 |
| `check` finds no breakage | 0 |
| `check` finds at least one breakage | 1 |
| `check` cannot resolve the local repository or Git reference | 2 |
| invalid command syntax | nonzero |

## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Appendix B: Assessment Notes

Compatibility covers importability, individual model and container behavior, static and dynamic loading, alias errors, docstring parsing, serialization round-trips, extension mutation, API breakage classification, and complete local CLI workflows. The upstream module layout, private helpers, exact diagnostic wording, exact JSON key order, exact explanation formatting, and a particular parser implementation are not required.
