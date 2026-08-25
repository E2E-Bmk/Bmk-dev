# astroid Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

astroid provides a Python source analysis tree with richer behavior than the standard `ast` module. It parses source text, files, modules, classes, and selected live objects into `astroid.nodes.Module` roots whose descendants expose parent links, source positions, local bindings, scope/frame traversal, source rendering, structural rendering, and static inference.

The public contract has three projections over the same product state:

- The syntax projection returns `NodeNG` objects and concrete classes from `astroid.nodes`.
- The name and inference projection returns bindings, inferred values, `Instance` objects, and the `Uninferable` sentinel.
- The manager projection returns cached modules, import-derived modules, transform-extended modules, and failed-import hook results.

An operation that receives invalid Python source must raise `AstroidSyntaxError` or `ValueError` according to the operation described below. An operation that cannot resolve a module, attribute, parent, statement, or inference result must raise the astroid exception named for that failure. Name lookup must follow the return-value behavior described in the lookup section.

## Non-Goals

- astroid does not promise byte-for-byte source-code round-tripping.
- astroid does not promise complete execution of Python programs.
- astroid does not promise that every dynamic Python construct has a definite inferred value.
- astroid does not promise compatibility between `NodeNG` instances and CPython `_ast` node instances.
- astroid does not promise stable memory addresses, object ids, or exact `repr()` addresses.
- astroid does not require applications to use private modules or non-public utilities.
- astroid does not promise to import arbitrary third-party C extensions unless manager settings allow that import path.

This specification excludes non-public utility functions, private modules, exact object identities, memory addresses, and implementation choices for inference algorithms.

## Representative Workflows

```python
import astroid
from astroid import MANAGER, inference_tip, register_module_extender
from astroid import nodes

module = astroid.parse("""
def func(first, second):
    return first + second

arg_1 = 2
arg_2 = 3
func(arg_1, arg_2)
""")

call_expr = module.body[-1].value
inferred = next(call_expr.infer())
assert isinstance(inferred, nodes.Const)
assert inferred.value == 5

selected = astroid.extract_node("""
a = 1 #@
b = __(a + 2)
""")
assert isinstance(selected, list)

def fake_module():
    return astroid.parse("class Provided: pass")

register_module_extender(MANAGER, "my_dynamic_module", fake_module)
extended = MANAGER.ast_from_module_name("my_dynamic_module")
assert "Provided" in extended.public_names()
```

This workflow must parse source, infer a constant result, extract marked nodes, register an extender, and expose extender-provided names through the returned module. It must raise the errors described above when source parsing, inference, or import resolution fails.

## Parsing and Node Extraction

Parsing converts Python source text into astroid module trees, and extraction selects marked nodes for targeted analysis.

**Parsing source text.** `parse` must dedent the provided code, parse it as one module, and return an `astroid.nodes.Module`. The returned module must use `module_name` as its `name` attribute and `path` as its `file` attribute when those arguments are provided. When `apply_transforms` is `True`, `parse` must apply registered transforms to the resulting tree. When `apply_transforms` is `False`, transforms must be skipped. Invalid Python source must raise `AstroidSyntaxError`. The module `body` must contain the parsed statement nodes in source order, and each child's `as_string` must render the original source-like text.

**Extracting marked nodes.** `extract_node` must dedent and parse the supplied code as a module. It must return the statement on each line whose stripped text ends with `#@`. It must return the expression inside each `__(...)` marker and must leave the returned node's parent tree shaped as if the wrapper call were absent. When the selected node is an expression statement, it must return the wrapped expression instead of the surrounding `Expr` statement. When no `#@` line and no `__(...)` marker exists, it must return the last top-level statement. When exactly one selected node exists, `extract_node` must return a single `NodeNG`. When more than one selected node exists, it must return a list of `NodeNG` objects. An empty module body must raise `ValueError`, and invalid source must raise `AstroidSyntaxError`.

## Node Traversal and Rendering

All nodes in an astroid tree support traversal through parent chains, child iteration, scope/frame lookup, source rendering, and structural introspection.

**Node base contract.** All concrete node classes exported from `astroid.nodes` must inherit from `NodeNG` or a documented `NodeNG` subclass. Nodes created by parsing must expose `lineno`, `col_offset`, `end_lineno`, and `end_col_offset` source positions when Python parsing provides those values, `parent` links from descendants to their containing node, and `_astroid_fields`, `_other_fields`, and `_other_other_fields` tuples describing structural and non-structural attributes.

**Children and ancestors.** `get_children` must return child nodes in the order of the node's structural fields, skipping `None` fields and flattening list and tuple child fields. It must return an empty iterator when the node has no child fields. `node_ancestors` must yield `parent`, grandparent, and successive ancestors until no parent exists.

**Statement, frame, scope, and root.** `statement` must return the nearest ancestor or self marked as a statement and must raise `StatementMissing` when no statement exists before the parent chain ends. `frame` must return the nearest `Module`, `FunctionDef`, `ClassDef`, or `Lambda` frame. `scope` must return the nearest scope node and must raise `ParentMissingError` when called on a parentless non-scope node. `root` must return the module root for any node in a parsed tree and must return itself when called on a `Module` root.

**Descendant search.** `nodes_of_class` must yield `self` and descendants whose class matches the requested class. When `skip_klass` is provided, it must skip descent into nodes matching that class.

**Source rendering.** `as_string` must return source-like Python text for the represented node. `repr_tree` must return a stable structural text representation of the node tree. When `include_linenos` is `True`, source positions must be included. When `max_depth` is greater than zero, the tree must be depth-truncated. The representation with line numbers must be longer than without them.

**Inference.** `infer` must return a generator of possible inferred values. It must create a fresh inference context when none is supplied. It must use an explicit inference function installed on the node before the default inference path, and must fall back to default inference when the explicit inference function raises `UseInferenceDefault`. `inferred` must return a list from `infer`.

**Instantiation.** `instantiate_class` must return `self` for non-class nodes. On a `ClassDef`, it must return an `Instance` representing an instance of that class.

**Module queries.** `public_names` must return local names that do not start with `_`. `wildcard_import_names` must return string values from an explicit `__all__` assignment when astroid infers it successfully, and must return public local names when `__all__` is absent or cannot be inferred. `getattr` on a `Module` must return matching attribute nodes from module locals and must raise `AttributeInferenceError` when the name is empty or no attribute is found. `igetattr` must return inferred values for `getattr` results and must raise `InferenceError` when `getattr` raises `AttributeInferenceError`. `fully_defined` must return `True` for modules built from a `.py` file and `False` for string-parsed, stub, namespace, or introspection-only modules.

## Name Resolution and Inference

Name resolution connects identifiers to their defining scopes, and inference computes the possible values of expressions.

**Name lookup.** `lookup` on a node must return a pair `(scope, statements)` where `scope` is the scope that owns the binding and `statements` are the assignment nodes visible from the lookup node's position. When the name is found only in builtins, it must return the builtins module scope and matching builtin statements. When the name cannot be resolved from local, enclosing, global, or builtin bindings, it must return the builtins module scope and an empty statements list.

**Inferred lookup.** `ilookup` must infer the statements returned by `lookup` and must return an iterator over inferred values.

**Inference results.** Inference must yield `Const` nodes for supported constant expressions, `Instance` objects for inferred instances of known classes, `ExceptionInstance` objects for inferred exception instances, and `Uninferable` when astroid reaches a supported boundary without a definite value. When a name cannot be resolved during inference, a `NameInferenceError` must be raised.

**The Uninferable sentinel.** `Uninferable` must be a singleton-style sentinel value that callers compare by identity or receive as an inference result. It must not be raised as an exception and must not be an instance of `BaseException`.

## Module Management and Transforms

The manager provides module building, caching, transforms, module extenders, and failed-import hooks for enriching the astroid analysis graph.

**Manager identity.** `MANAGER` must be an `AstroidManager` instance with the standard brain transforms registered. Direct `AstroidManager()` construction must share the same manager state for caches, transforms, failed-import hooks, and settings. The `astroid_cache` attribute must expose the module cache as a dictionary keyed by module name.

**Building from strings.** `MANAGER.ast_from_string` must return a `Module` parsed from the supplied data, cache it under the given module name, and set the module `file` from the filepath when provided. Invalid source must raise `AstroidSyntaxError`.

**Building from files.** `MANAGER.ast_from_file` must return a `Module` for a Python source file. When the module name is not supplied, it must be inferred from the file path. A module built from a `.py` file must report `fully_defined` as `True`. When the cache already contains the same module name, the cached module must be returned. When the file cannot be loaded and `fallback` is `False`, it must raise `AstroidBuildingError`.

**Building from module names.** `MANAGER.ast_from_module_name` must return a module graph for an importable module name. When the module name is `None`, it must raise `AstroidBuildingError`. It must return a stub module for `__main__`. When `use_cache` is `True` and the cache contains the module name, the cached module must be returned. It must call registered failed-import hooks after normal import building fails.

**Building from live objects.** `MANAGER.ast_from_module` must return a module graph for a live Python module, using the module's `__name__` when a module name is not supplied. `MANAGER.ast_from_class` must return the `ClassDef` for the given class, using the class's `__module__` to locate the containing module.

**Caching.** `MANAGER.cache_module` must keep the first cached module for a module name and must not replace it with later modules with the same name. `MANAGER.clear_cache` must clear module and import caches, clear inference-tip and inference-context caches, bootstrap builtins, and re-register standard brain transforms.

**Transforms.** `MANAGER.register_transform` must register a transform for nodes of a given class. When no predicate is supplied, the transform must apply to all subsequently built matching nodes. When a predicate is supplied, the transform must apply only when the predicate returns `True` for the node. Transforms registered on `MANAGER` must affect subsequently built matching nodes when transforms are enabled, and must not affect a `parse` call whose `apply_transforms` argument is `False`.

**Inference tips.** `inference_tip` must return a transform function suitable for `MANAGER.register_transform`. The returned transform must install the supplied inference function as the explicit inference path for the target node and must return the node. When `raise_on_overwrite` is `True` and the node already has a different explicit inference function, it must raise `InferenceOverwriteError`. An inference function installed through `inference_tip` must return an iterator of inference results. Raising `UseInferenceDefault` must cause the node to fall back to its default inference behavior.

**Module extenders.** `register_module_extender` must register a transform for a named module. The extender callable must return an `astroid.nodes.Module`. The extender must copy the extension module's locals into the target module and must reparent copied objects. The extended module must expose the extender's public names through `public_names`, `getattr`, and inference of attributed names.

**Failed-import hooks.** `MANAGER.register_failed_import_hook` must append a hook to the failed-import hook chain. The hook must return an `astroid.nodes.Module` when it resolves the missing import, and must raise `AstroidBuildingError` when it does not. A hook result must behave like a normal module graph for `getattr`, `igetattr`, `lookup`, and manager cache interactions.

**Compatibility aliases.** The top-level `astroid` module must continue to resolve documented node classes such as `astroid.Call`, `astroid.Const`, and `astroid.FunctionDef` through the compatibility alias path. Resolving such an alias must emit `DeprecationWarning` and return the corresponding `astroid.nodes` class. `UnresolvableName` must be the same class as `NameInferenceError`, and `NotFoundError` must be the same class as `AttributeInferenceError`. Resolving an unknown top-level attribute must raise `AttributeError`.

## State Model

An astroid session consists of source inputs, a manager, a module cache, transform registrations, failed-import hooks, and node graphs returned from parsing or importing. The public state has these projections:

- The module graph projection consists of `Module` roots and `NodeNG` descendants reachable through `get_children`, `parent`, `root`, `frame`, `scope`, and concrete node attributes.
- The binding and inference projection consists of `locals`, `lookup`, `ilookup`, `getattr`, `igetattr`, `infer`, `inferred`, `Instance`, `ExceptionInstance`, and `Uninferable`.
- The manager projection consists of `MANAGER` and direct `AstroidManager` instances, their caches, transform registrations, failed-import hooks, and import/build methods.

The following cross-view invariants belong to the state model:

1. A module returned by `parse` must be the same root returned by `root()` from every descendant in that parse tree.
2. A name binding created in source text must appear through the relevant scope's `locals` view and must be returned by `lookup` from descendant nodes that see that binding.
3. A value inferred from a `Name` node must come from the statements returned by that node's lookup path or must return `Uninferable` when the inference limit or supported semantics are exhausted.
4. A transform registered on `MANAGER` must affect subsequently built matching nodes when transforms are enabled and must not affect a `parse` call whose `apply_transforms` argument is `False`.
5. A module built through `MANAGER.ast_from_string` or `MANAGER.ast_from_file` must be cached under its module name and must be returned from the cache on a later compatible manager lookup.
6. A module extender registered for a module name must expose the extender module's public locals through the target module's lookup and attribute views.

## Error Semantics

All astroid exceptions derived from `AstroidError` must accept a message and keyword fields. `str(error)` must format the message with the exception's stored fields and must return the raw message when formatting fails.

- `AstroidBuildingError` must represent failures to build an astroid representation from a module, file, class, or object.
- `AstroidImportError` must represent import-specific build failures.
- `TooManyLevelsError` must represent a relative import beyond the top level and must store `level` and `name`.
- `AstroidSyntaxError` must represent Python parsing or source encoding failures and must store source/module/path/error context.
- `NoDefault` must be raised by function default-value lookup when the requested argument has no default.
- `ResolveError` must be the base astroid resolution error and must store inference context when provided.
- `InferenceError` must be raised when a node or statement cannot be inferred.
- `NameInferenceError` must be raised by name-inference paths that report unresolved names as errors and must store `name`, `scope`, and `context`.
- `AttributeInferenceError` must be raised when attribute lookup fails and must store `target`, `attribute`, and `context`.
- `MroError`, `DuplicateBasesError`, and `InconsistentMroError` must represent class method-resolution failures.
- `SuperError` and `SuperArgumentTypeError` must represent invalid `super()` resolution.
- `AstroidIndexError`, `AstroidTypeError`, and `AstroidValueError` must represent static-analysis analogues of Python `IndexError`, `TypeError`, and `ValueError`.
- `ParentMissingError` must be raised when an operation requires a parent chain and none exists.
- `StatementMissing` must be raised when `statement()` cannot find a statement node.
- `InferenceOverwriteError` must be raised by inference-tip registration when overwrite protection is enabled and a different explicit inference already exists.
- `UseInferenceDefault` must be raised by custom inference functions to request default inference handling.
- `UnresolvableName` must be the same public error category as `NameInferenceError`.
- `NotFoundError` must be the same public error category as `AttributeInferenceError`.

## Cross-View Invariants

1. A module produced by `parse`, `extract_node`, `MANAGER.ast_from_string`, or `MANAGER.ast_from_file` must expose the same descendants through `repr_tree`, `get_children`, `nodes_of_class`, and parent traversal.
2. A node returned by `extract_node` must retain a valid parent chain to the parsed module root except for user-created nodes that were never attached to a tree.
3. A selected expression returned by `extract_node` must render through `as_string()` as the selected expression and must not render the marker wrapper.
4. A name found by `lookup` must infer through `ilookup` to values derived from the returned statements or to `Uninferable` when inference reaches an unsupported boundary.
5. A module returned from the manager cache must expose the same locals, lookup results, and transform effects as the originally cached module object.
6. A failed-import hook result must behave like a normal module graph for `getattr`, `igetattr`, `lookup`, `repr_tree`, and manager cache interactions.
7. A module extender result must be visible through module locals, `public_names`, `getattr`, and inference of imported or attributed names from that module.
8. A top-level compatibility node alias must return the same class object as the corresponding `astroid.nodes` import and must emit a deprecation warning before returning it.
9. A CLI AST rendering for a valid Python file must match the `repr_tree()` projection of parsing that file's UTF-8 text.

## Public Interface

### Import Surface

The package must expose these top-level imports:

```python
from astroid import (
    MANAGER,
    parse,
    extract_node,
    inference_tip,
    register_module_extender,
    BaseInstance,
    Instance,
    ExceptionInstance,
    Uninferable,
)
from astroid import (
    AstroidError,
    AstroidBuildingError,
    AstroidImportError,
    AstroidSyntaxError,
    InferenceError,
    NameInferenceError,
    AttributeInferenceError,
    NoDefault,
    ParentMissingError,
    StatementMissing,
    UseInferenceDefault,
)
from astroid import nodes
from astroid.exceptions import AstroidError, InferenceError
```

The `astroid.nodes` namespace must expose the documented concrete node classes:

```python
from astroid.nodes import (
    AnnAssign, Arguments, Assert, Assign, AssignAttr, AssignName,
    AsyncFor, AsyncFunctionDef, AsyncWith, Attribute, AugAssign, Await,
    BaseContainer, BinOp, BoolOp, Break, Call, ClassDef, Compare,
    Comprehension, ComprehensionScope, Const, Continue, Decorators,
    DelAttr, DelName, Delete, Dict, DictComp, DictUnpack, EmptyNode,
    EvaluatedObject, ExceptHandler, Expr, For, FormattedValue,
    FunctionDef, GeneratorExp, Global, If, IfExp, Import, ImportFrom,
    Interpolation, JoinedStr, Keyword, Lambda, List, ListComp,
    LocalsDictNodeNG, Match, MatchAs, MatchCase, MatchClass,
    MatchMapping, MatchOr, MatchSequence, MatchSingleton, MatchStar,
    MatchValue, Module, Name, NamedExpr, NodeNG, Nonlocal, ParamSpec,
    Pass, Raise, Return, Set, SetComp, Slice, Starred, Subscript,
    TemplateStr, Try, TryStar, Tuple, TypeAlias, TypeVar,
    TypeVarTuple, UnaryOp, Unknown, While, With, Yield, YieldFrom,
)
```

The command line entry point must accept:

```bash
python -m astroid ast FILE
```

It must return exit code `0` after printing `repr_tree()` for a `.py` or `.pyi` file that exists and parses successfully. It must print an error message and return exit code `1` when `FILE` does not exist or does not end in `.py` or `.pyi`. It must print help and return exit code `2` when no subcommand is supplied.

### API Catalog

| Name | Kind | Role |
|---|---|---|
| parse | function | Parse Python source into an astroid Module node |
| extract_node | function | Extract marked nodes from Python source |
| NodeNG | class | Base class for all AST nodes |
| Module | class | Root node representing a Python module |
| ClassDef | class | Node representing a class definition |
| FunctionDef | class | Node representing a function definition |
| Const | class | Node representing a constant value |
| MANAGER | instance | Shared AstroidManager with standard brain transforms |
| AstroidManager | class | Manager for building, caching, and transforming modules |
| inference_tip | function | Create a transform installing a custom inference function |
| register_module_extender | function | Register a transform extending a module's locals |
| Instance | class | Inferred instance of a class |
| ExceptionInstance | class | Inferred instance of an exception class |
| BaseInstance | class | Base for inferred class instances |
| Uninferable | sentinel | Sentinel for unknown inference results |

### CLI Entry Points

There is no console script for this package. `python -m astroid` is not supported. Programmatic use is through Python imports.


## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Appendix B: Assessment Notes

Validation covers public imports, parsing and extraction, node traversal and rendering, lookup and inference, manager caching and imports, transforms and module extenders, compatibility aliases, documented errors, CLI behavior, and cross-view invariants. Checks use local Python source, files, and modules and assess independently observable public behavior. Private implementation details, exact object identities, and unsupported dynamic inference are not considered unless explicitly required.
