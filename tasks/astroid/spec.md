# astroid Specification

## Product Overview

astroid provides a Python source analysis tree with richer behavior than the standard `ast` module. It parses source text, files, modules, classes, and selected live objects into `astroid.nodes.Module` roots whose descendants expose parent links, source positions, local bindings, scope/frame traversal, source rendering, structural rendering, and static inference.

The public contract has three projections over the same product state:

- The syntax projection returns `NodeNG` objects and concrete classes from `astroid.nodes`.
- The name and inference projection returns bindings, inferred values, `Instance` objects, and the `Uninferable` sentinel.
- The manager projection returns cached modules, import-derived modules, transform-extended modules, and failed-import hook results.

An operation that receives invalid Python source must raise `AstroidSyntaxError` or `ValueError` according to the operation described below. An operation that cannot resolve a module, attribute, parent, statement, or inference result must raise the astroid exception named for that failure. Name lookup must follow the return-value behavior described in the lookup section.

## Scope

This specification covers:

- source-string parsing with `parse`;
- node extraction with `extract_node`;
- public imports from `astroid`, `astroid.nodes`, and `astroid.exceptions`;
- `MANAGER` module building, cache, import, transform, module extender, and failed-import hook behavior;
- public node traversal, lookup, rendering, and inference methods;
- public exception classes and aliases;
- the `python -m astroid ast FILE` command.

This specification excludes non-public utility functions, private modules, exact object identities, memory addresses, and implementation choices for inference algorithms.

## Installable Surface

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

## Product State Model

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

## Public API

### Parsing and Extraction

`parse(code: str, module_name: str = "", path: str | None = None, apply_transforms: bool = True) -> astroid.nodes.Module`

- `parse` must dedent `code`, parse it as one module, and return an `astroid.nodes.Module`.
- The returned module must use `module_name` as its module name and `path` as its file path when those arguments are provided.
- `parse` must apply registered transforms when `apply_transforms` is `True`.
- `parse` must not apply registered transforms when `apply_transforms` is `False`.
- `parse` must raise `AstroidSyntaxError` when the source fails Python parsing.

`extract_node(code: str, module_name: str = "") -> NodeNG | list[NodeNG]`

- `extract_node` must dedent and parse `code` as a module.
- `extract_node` must return the statement on each line whose stripped text ends with `#@`.
- `extract_node` must return the expression inside each `__(...)` marker and must leave the returned node's parent tree shaped as if the wrapper call were absent.
- `extract_node` must return the last top-level statement when no `#@` line and no `__(...)` marker exists.
- `extract_node` must return the wrapped expression instead of the surrounding `Expr` statement when the selected node is an expression statement.
- `extract_node` must return a single `NodeNG` when exactly one selected node exists.
- `extract_node` must return a list of `NodeNG` objects when more than one selected node exists.
- `extract_node` must raise `ValueError` when the parsed module has no body.
- `extract_node` must raise `AstroidSyntaxError` when the source fails Python parsing.

### Nodes

All concrete node classes exported from `astroid.nodes` must inherit from `NodeNG` or a documented `NodeNG` subclass. Nodes created by parsing must expose:

- `lineno`, `col_offset`, `end_lineno`, and `end_col_offset` source positions when Python parsing provides those values;
- `parent` links from descendants to their containing node;
- `_astroid_fields`, `_other_fields`, and `_other_other_fields` tuples describing structural and non-structural public node attributes;
- `is_statement`, `is_function`, and `is_lambda` boolean classification flags where the class semantics require them.

`NodeNG.get_children()` must return child nodes in the order of the node's structural fields. It must skip `None` fields. It must flatten list and tuple child fields. It must return an empty iterator when the node has no child fields.

`NodeNG.node_ancestors()` must yield `parent`, grandparent, and successive ancestors until no parent exists. It must yield no values for a parentless root.

`NodeNG.statement()` must return the nearest ancestor or self marked as a statement. It must raise `StatementMissing` when no statement exists before the parent chain ends.

`NodeNG.frame()` must return the nearest `Module`, `FunctionDef`, `ClassDef`, or `Lambda` frame. It must return astroid's synthetic module root named `__astroid_synthetic` when called on a parentless non-frame node.

`NodeNG.scope()` must return the nearest scope node, including `Module`, `FunctionDef`, `ClassDef`, `Lambda`, and generator-expression scopes. It must raise `ParentMissingError` when called on a parentless non-scope node.

`NodeNG.root()` must return the module root for any node in a parsed tree. It must return itself when called on a `Module` root.

`NodeNG.nodes_of_class(klass, skip_klass=None)` must yield `self` and descendants whose class matches `klass`. It must skip descent into nodes matching `skip_klass` when `skip_klass` is provided.

`NodeNG.as_string()` must return source-like Python text for the represented node. It must raise the visitor or node error used by the renderer when the node class has no supported rendering.

`NodeNG.repr_tree(ids=False, include_linenos=False, ast_state=False, indent="   ", max_depth=0, max_width=80)` must return a stable structural text representation of the node tree. It must include object ids when `ids` is `True`, source positions when `include_linenos` is `True`, derived locals/global state when `ast_state` is `True`, and depth truncation when `max_depth` is greater than zero. It must format with `indent` and attempt to respect positive `max_width`.

`NodeNG.infer(context=None)` must return a generator of possible inferred values. It must create a fresh inference context when `context` is `None`. It must use an explicit inference function installed on the node before the default inference path. It must fall back to default inference when the explicit inference function raises `UseInferenceDefault`. It must yield `Uninferable` when the manager's maximum inference count or the context's maximum inference count is exceeded.

`NodeNG.inferred()` must return `list(self.infer())`.

`NodeNG.instantiate_class()` must return `self` for non-class nodes. `ClassDef.instantiate_class()` must return an `Instance` representing an instance of that class.

`Module.public_names()` must return local names that do not start with `_`.

`Module.wildcard_import_names()` must return names exported by wildcard import. It must return string values from an explicit list or tuple assigned to `__all__` when astroid infers that assignment successfully. It must return local names that do not start with `_` when `__all__` is absent or cannot be inferred as a list or tuple of string values.

`Module.getattr(name, context=None, ignore_locals=False)` must return matching attribute nodes from module locals, special module attributes, or package-relative imports. It must raise `AttributeInferenceError` when `name` is empty or no attribute is found.

`Module.igetattr(name, context=None)` must return inferred values for `Module.getattr`. It must raise `InferenceError` when `Module.getattr` raises `AttributeInferenceError`.

`Module.fully_defined()` must return `True` for modules built from a `.py` file and `False` for stub, namespace, synthetic, or introspection-only modules without a `.py` file.

### Lookup and Inference

`lookup(name)` on a node that participates in lookup must return a pair `(scope, statements)` where `scope` is the scope that owns the binding and `statements` are the assignment nodes visible from the lookup node's position. It must return the builtins module scope and matching builtin statements when the name is found only in builtins. It must return the builtins module scope and an empty statements list when the name cannot be resolved from local, enclosing, global, or builtin bindings.

`ilookup(name)` must infer the statements returned by `lookup(name)` and must return an iterator over inferred values.

Inference must yield `Const` nodes for supported constant expressions, `Instance` objects for inferred instances of known classes, `ExceptionInstance` objects for inferred exception instances, and `Uninferable` when astroid reaches a supported boundary without a definite value.

`Uninferable` must be a singleton-style sentinel value that callers compare by identity or receive as an inference result. It must not be raised as an exception.

### Manager, Imports, and Cache

`MANAGER` must be an `AstroidManager` instance with the standard brain transforms registered. Direct `AstroidManager()` construction must share the same manager state for caches, transforms, failed-import hooks, and settings.

`MANAGER.ast_from_string(data, modname="", filepath=None)` must return a `Module` parsed from `data`, cache it under `modname`, and set the module path from `filepath` when provided. It must raise `AstroidSyntaxError` for invalid source.

`MANAGER.ast_from_file(filepath, modname=None, fallback=True, source=False)` must return a `Module` for a Python source file. It must infer `modname` from the file path when `modname` is `None` and path-to-module resolution succeeds. It must return a cached module when the cache already contains the same module name and file path. It must raise `AstroidBuildingError` when the file cannot be loaded and no fallback result is available.

`MANAGER.ast_from_module_name(modname, context_file=None, use_cache=True)` must return a module graph for an importable module name. It must raise `AstroidBuildingError` when `modname` is `None`. It must raise `AstroidImportError` when `modname` is denied or a compiled module cannot be represented. It must return a cached module when `use_cache` is `True` and the cache contains `modname`. It must return a stub module for `__main__`. It must call registered failed-import hooks after normal import building fails.

`MANAGER.ast_from_module(module, modname=None)` must return a module graph for a live Python module. It must use `module.__name__` when `modname` is `None`. It must return a cached module when one exists for the resolved name. It must build from source when the module has a Python source file and must otherwise build an introspection-based partial module.

`MANAGER.ast_from_class(klass, modname=None)` must return the `ClassDef` for `klass`. It must use `klass.__module__` when `modname` is `None`. It must raise `AstroidBuildingError` when the module or class name cannot be obtained or loaded.

`MANAGER.infer_ast_from_something(obj, context=None)` must infer a class object or the class of an instance-like object. It must yield the class inference result for type objects and instantiated inference results for non-type objects. It must raise `AstroidBuildingError` or `AstroidImportError` when type, module, name, or import resolution fails.

`MANAGER.cache_module(module)` must keep the first cached module for a module name and must not replace it with later modules with the same name.

`MANAGER.clear_cache()` must clear module and import caches, clear inference-tip and inference-context caches, bootstrap builtins, and re-register standard brain transforms.

### Transforms and Extenders

`MANAGER.register_transform(node_class, transform, predicate=None)` must register a transform for nodes of `node_class`. It must apply `transform(node)` to subsequently built matching nodes when `predicate` is absent. It must apply `transform(node)` only when `predicate(node)` returns `True` when a predicate is supplied.

`inference_tip(infer_function, raise_on_overwrite=False)` must return a transform function suitable for `MANAGER.register_transform`. The returned transform must install `infer_function(node, context=None)` as the explicit inference path for the target node and must return the node. It must raise `InferenceOverwriteError` when `raise_on_overwrite` is `True` and the node already has a different explicit inference function.

An inference function installed through `inference_tip` must return an iterator of inference results. It must raise `UseInferenceDefault` to request the node's default inference behavior.

`register_module_extender(manager, module_name, get_extension_mod)` must register a transform on `manager` for a module named `module_name`. `get_extension_mod` must return an `astroid.nodes.Module`. The extender must copy the extension module's locals into the target module and must reparent copied objects whose parent was the extension module. It must raise the transform's exception when `get_extension_mod` fails or returns an invalid object.

`MANAGER.register_failed_import_hook(hook)` must append `hook` to the failed-import hook chain. `hook(modname)` must return an `astroid.nodes.Module` when it resolves the missing import. It must raise `AstroidBuildingError` when it does not resolve the import.

### Deprecated Top-Level Node Aliases

The top-level `astroid` module must continue to resolve documented node classes such as `astroid.Call`, `astroid.JoinedStr`, `astroid.FormattedValue`, `astroid.Const`, and `astroid.FunctionDef` through the compatibility alias path. Resolving such an alias must emit `DeprecationWarning` and return the corresponding `astroid.nodes` class. Resolving an unknown top-level attribute must raise `AttributeError`.

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

## Representative Workflow

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

## Non-Goals

- astroid does not promise byte-for-byte source-code round-tripping.
- astroid does not promise complete execution of Python programs.
- astroid does not promise that every dynamic Python construct has a definite inferred value.
- astroid does not promise compatibility between `NodeNG` instances and CPython `_ast` node instances.
- astroid does not promise stable memory addresses, object ids, or exact `repr()` addresses.
- astroid does not require applications to use private modules or non-public utilities.
- astroid does not promise to import arbitrary third-party C extensions unless manager settings allow that import path.

## Evaluation Notes

Evaluation checks the public behavior described here through importability, parsing, extraction, node traversal, source rendering, structural rendering, lookup, inference, manager cache behavior, transform behavior, module extenders, failed-import hooks, exception classes, and CLI exit behavior.

Scoring rewards implementations that satisfy the public contract across independent workflows. It does not require a particular internal representation, non-public utility name, algorithm sequence, or dependency layout. Failures are evaluated by observable public results: returned object categories, yielded inference values, raised exception classes, warning categories, rendered strings, cache-visible behavior, and command exit codes.
