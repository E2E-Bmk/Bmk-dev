
# Rhai Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`rhai` is an embedded scripting engine for Rust that parses script text, evaluates scripts against host-owned state, exposes Rust functions and modules to scripts, and projects script results through Rust values and errors.

The primary runtime value is `Dynamic`; scripts operate on integers, booleans, strings, arrays, maps, functions, and host-registered custom values. An `Engine` owns language options, registered native functions, registered modules, event callbacks, limits, and compilation settings. A `Scope` supplies mutable or constant variables across evaluations, while a compiled `AST` holds parsed script code for repeated runs.

When the `grain` feature is enabled, `rhai::grain` provides an experimental bytecode path. A `Compiler` lowers an `AST` into a `Program`, and a `Vm` runs the `Program` against the same `Engine`, `Scope`, `Dynamic`, native function, and error model as ordinary AST evaluation.

## Non-Goals

- This specification does not require private module layout, private helper functions, or exact internal storage for `Engine`, `Scope`, `Module`, `Dynamic`, `AST`, `Program`, or `Vm`.
- This specification does not define internals-feature AST node variants, parser state structures, tokenizer state, bytecode instruction encodings, disassembly output, or exact debug formatting.
- This specification does not require exact error message text, exact display formatting, exact source snippets printed by tools, or exact `Debug` output for public types.
- This specification does not require procedural macro expansion details from `rhai_codegen`; public macros only need to support the documented registration workflows they expose.
- This specification does not require optional feature combinations beyond the default library surface plus the `serde`, `metadata`, and `grain` surfaces named in the environment.
- This specification does not require command-line binaries, interactive shells, debugger command loops, terminal history behavior, process exit-code behavior, or command help text.
- This specification does not define network access, external package download behavior, online playground behavior, editor plug-ins, or documentation-site generation.

## Representative Workflows

```rust
use rhai::{Engine, EvalAltResult, Scope};

fn main() -> Result<(), Box<EvalAltResult>> {
    let engine = Engine::new();
    let mut scope = Scope::new();
    scope.push("x", 40_i64);

    let value: i64 = engine.eval_with_scope(&mut scope, "x += 2; x")?;
    assert_eq!(value, 42);
    assert_eq!(scope.get_value::<i64>("x"), Some(42));

    Ok(())
}
```

When a caller evaluates script text with `eval_with_scope`, the engine must parse the script, execute it with the provided `Scope`, return the final expression converted to the requested Rust type, and preserve scope mutations made by the script. If parsing, evaluation, or result conversion fails, then the call must return a boxed `EvalAltResult` through the public result type instead of panicking; parse failures must use `EvalAltResult::ErrorParsing`.

```rust
use rhai::{Engine, EvalAltResult, Scope};

fn main() -> Result<(), Box<EvalAltResult>> {
    let mut engine = Engine::new();
    engine.register_fn("add", |x: i64, y: i64| x + y);

    let ast = engine.compile("fn double(x) { add(x, x) }")?;
    let mut scope = Scope::new();
    let value: i64 = engine.call_fn(&mut scope, &ast, "double", (21_i64,))?;
    assert_eq!(value, 42);

    Ok(())
}
```

When a caller registers a native Rust function, compiles a script defining a script function, and calls that script function through `call_fn`, the engine must make the native function visible to the script, evaluate the `AST` as needed for module setup, dispatch by script function name and argument arity, and return the called function's result converted to the requested Rust type. If the function is missing, argument resolution fails, or output conversion fails, then the call must return `EvalAltResult`.

```rust
use rhai::grain::{Compiler, Program, Vm};
use rhai::{Engine, EvalAltResult, Scope};

fn main() -> Result<(), Box<EvalAltResult>> {
    let engine = Engine::new();
    let ast = engine.compile("let total = 0; for n in 0..10 { total += n; } total")?;
    let program = Compiler::new().compile(&ast);

    let mut scope = Scope::new();
    let value = Vm::new(&engine).eval_with_scope(&mut scope, &program)?;
    assert_eq!(value.as_int().unwrap(), 45);

    if program.residual_count() == 0 {
        let bytes = program.write().unwrap();
        let loaded = Program::read(&bytes).unwrap();
        let again = Vm::new(&engine).eval(&loaded)?;
        assert_eq!(again.as_int().unwrap(), 45);
    }

    Ok(())
}
```

When the Grain feature is enabled, compiling an `AST` to a `Program` and running it with `Vm` must preserve the observable result and scope effects of `Engine::eval_ast_with_scope`. If the program still contains residual AST fragments, then `Program::write` must reject serialization while `Vm` must continue to execute by delegating those residual fragments to the engine.

## Script Evaluation And Compilation

This section covers how an `Engine` turns script text, files, and precompiled `AST` values into Rust results and scope mutations.

**Engine creation and one-shot helpers.** The `Engine::new` constructor must create an engine with the standard packages, language features, limits, module resolver, callbacks, and optimization behavior enabled for the active Cargo feature set. The `Engine::new_raw` constructor must create an engine without the standard package registrations. The free functions `rhai::eval` and `rhai::run` must create a fresh `Engine` and evaluate the supplied script through the matching engine method. If parsing, execution, or output conversion fails, then these helpers must return the same public error kinds as the corresponding `Engine` methods.

**Script text evaluation.** When `eval` receives script text, the engine must execute the script in a fresh `Scope` and return the final expression converted to the requested Rust type. When `eval_with_scope` receives script text and a mutable `Scope`, the engine must compile against that scope, execute against the same scope, and leave mutations to visible scope variables in that scope. When `run` or `run_with_scope` receives script text, the engine must execute it for side effects and return unit on success. If the script contains invalid syntax, then text-based evaluation and run calls must return boxed `EvalAltResult::ErrorParsing`; if runtime execution fails, then they must return boxed `EvalAltResult`; if the final value does not convert to the requested Rust type, then they must return `EvalAltResult::ErrorMismatchOutputType`.

**Expression-only evaluation.** When `eval_expression` or `eval_expression_with_scope` receives script text, the engine must parse it as one global expression rather than as a full statement script. The expression evaluation methods must read variables from the provided scope when a scope is supplied and must not preserve declarations because declarations are not valid expression bodies. If the input is not a valid expression, then these methods must return boxed `EvalAltResult::ErrorParsing`; if the expression result does not convert to the requested Rust type, then they must return `EvalAltResult::ErrorMismatchOutputType`.

**Compiled AST reuse.** When `compile` receives script text, the engine must return an `AST` that represents the script and is reusable for later `eval_ast`, `eval_ast_with_scope`, `run_ast`, `run_ast_with_scope`, and `call_fn` calls. When `compile_expression` receives script text, the engine must return an `AST` containing an expression. When `compile_with_scope`, `compile_expression_with_scope`, or `compile_scripts_with_scope` receives a scope, the engine must use constant entries in that scope for constant propagation when optimization is enabled. If compilation fails, then these methods must return `ParseError`.

**Script segment compilation.** When `compile_scripts_with_scope` receives multiple script segments, the engine must concatenate the segments in order without inserting separators and compile the combined stream. If a caller needs separators, then the caller must include them inside the supplied segments. If the combined stream is not valid script text, then compilation must return `ParseError`.

**Self-contained module compilation.** When `compile_into_self_contained` receives a scope and script text, the engine must compile the script and eagerly resolve literal-string imports through the current `ModuleResolver`, recursively embedding resolved modules into the resulting `AST`. When that self-contained `AST` is evaluated later, the engine must use the embedded modules and must not require the current resolver to resolve those already embedded imports again. If any eager module resolution fails, then `compile_into_self_contained` must return the resolver's `EvalAltResult`.

**File-based execution.** When `compile_file`, `eval_file`, or `run_file` receives a path, the engine must read the file as UTF-8 script text, remove a leading shebang line, set the `AST` source to the path for compiled-file calls, and then use the same parsing and execution behavior as text-based methods. When the file cannot be opened or read, these methods must return `EvalAltResult::ErrorSystem`. File APIs are absent under `no_std` and unsupported WASM targets.

**Operators and direct calls.** When `eval_binary_op` receives an operator name and two operands, the engine must dispatch that operator through the registered function/operator resolution path and convert the result to the requested Rust type. When `eval_fn_call` receives a function name, optional `this_ptr`, and arguments, the engine must dispatch the named native function or operator through the engine's registered function namespace. If the operator or function is not found, then the call must return `EvalAltResult::ErrorFunctionNotFound`; if output conversion fails, then it must return `EvalAltResult::ErrorMismatchOutputType`.

## Scope And Values

This section covers `Scope` as the public variable projection shared between Rust and script runs.

**Creation and size.** `Scope::new` must create an empty scope, and `Scope::with_capacity` must create an empty scope with storage prepared for the requested number of entries. `len` returns the number of entries, and `is_empty` returns whether the scope contains no entries. When `clear` is called, the scope must remove all names, values, and aliases and return itself for chaining.

**Pushing values.** When `push` receives a name and clonable Rust value, the scope must append a read-write variable. When `push_dynamic` receives a `Dynamic`, the scope must append it using that dynamic value's access mode. When `push_constant` or `push_constant_dynamic` receives a name and value, the scope must append a read-only variable. If a later entry reuses an earlier name, then lookup must treat the later entry as the visible one while preserving the earlier shadowed entry.

**Removing and rewinding.** When `pop` is called on a non-empty scope, the scope must remove the last entry. If `pop` is called on an empty scope, then it must panic. When `rewind` receives a size, the scope must truncate entries and aliases to that size. If `rewind` receives a size greater than the current length, then it must leave the scope unchanged according to standard vector truncation behavior.

**Lookup and mutation.** `contains` returns whether any entry with the name exists. `get_value`, `get_value_ref`, `get_value_mut`, `get`, and `get_mut` must search from the last entry backward. `get_value` must return a cloned typed value when the visible value converts to the requested type, otherwise `None`. `get` must return the visible `Dynamic` by reference or `None`. `get_mut` must return a mutable `Dynamic` reference only for a visible read-write entry. `is_constant` must return `Some(true)` for a visible read-only entry, `Some(false)` for a visible read-write entry, and `None` when the name is absent.

**Setting and deleting.** When `set_or_push` receives a name and value, the scope must update the visible read-write entry if one exists; otherwise it must append a new read-write entry. If the visible entry is constant, then `set_or_push` must append a new shadowing read-write entry instead of mutating the constant. When `set_value` receives a name and value, the scope must update the visible read-write entry, append a new entry if the name is absent, and panic if the visible entry is constant. When `remove` receives a name, the scope must remove the visible entry and return it converted to the requested type, or return `None` when the name is absent or conversion fails.

**Aliases and iteration.** When module support is present and `set_alias` receives a name and alias, the scope must attach the alias to the visible matching entry; an empty alias must mean the variable's own name. If the name is absent, then `set_alias` must leave the scope unchanged. `clone_visible` must return a scope containing only the visible instance of each name and must preserve each retained entry's access mode and aliases. `iter` returns entries in insertion order as `(name, is_constant, value)` triples with shared values flattened into owned `Dynamic` values, while `iter_raw` returns `(name, is_constant, value)` triples from last to first without flattening shared values.

## Native Functions And Script Function Calls

This section covers registration of Rust functions and invocation of script-defined functions from Rust.

**Function registration.** When `register_fn` receives a script-visible name and a Rust function or closure, the engine must register it in the global namespace, assume it is pure except for property and index setters, and make it available to scripts by name with overload resolution based on name, arity, argument types, and receiver type. If no registered overload matches a script call, then execution must return `EvalAltResult::ErrorFunctionNotFound`.

**Raw function registration.** When `register_raw_fn` receives a name, argument `TypeId` list, and callback, the engine must call the callback with `NativeCallContext` and mutable `Dynamic` arguments after argument types have matched the supplied list. The callback must return a Rhai result, and errors returned by the callback must propagate as evaluation errors. If the callback consumes an argument by taking it from `Dynamic`, then that mutation must affect the argument passed to the raw callback.

**Custom type registration.** When `register_type` receives a Rust type, the engine must make the type usable as a Rhai custom type and use Rust's type name for `type_of`. When `register_type_with_name` receives a Rust type and display name, the engine must use that display name for script-visible type naming. If a script requests a function, property, method, or operator for a custom type that has not been registered, then evaluation must return the appropriate missing function, missing property, missing indexer, or mismatched type error.

**Properties and indexers.** When getter, setter, getter-setter, index-getter, index-setter, or index-getter-setter functions are registered on a `Module` or via the engine builder APIs, the engine must expose them through property access, property assignment, indexing, or index assignment respectively. Getter and index-getter functions must be callable on constants when registered as pure. Setter and index-setter functions must be non-pure, and attempts to mutate constants through them must return `EvalAltResult::ErrorAssignmentToConstant` or `EvalAltResult::ErrorNonPureMethodCallOnConstant`.

**Calling script functions.** When `call_fn` receives a scope, `AST`, function name, and arguments, the engine must evaluate the `AST` first to load required modules and declarations, call the script-defined function matching the name and arity, rewind temporary declarations after the call, and convert the return value to the requested Rust type. If the function is missing, then it must return `EvalAltResult::ErrorFunctionNotFound`; if conversion fails, then it must return `EvalAltResult::ErrorMismatchOutputType`.

**Call options.** When `call_fn_with_options` receives `CallFnOptions`, `bind_this_ptr` must bind the provided `Dynamic` as `this`, `with_tag` must provide run-local custom state overriding the engine default tag, `eval_ast(false)` must skip pre-call AST evaluation, `rewind_scope(false)` must preserve variables declared while evaluating or calling, and `in_all_namespaces(true)` must search registered native and module namespaces as well as the script functions in the `AST`. If the selected option combination makes required declarations unavailable, then the call must return the same missing-variable, missing-module, or missing-function error that script evaluation would return.

## Modules And Module Resolution

This section covers public module state, global module registration, static module namespaces, and import resolution.

**Module identity and variables.** `Module::new` must create an indexed empty module. `set_id` must set the module ID, while an empty ID must clear it; `clear_id` must remove it. `set_var` must store a `Dynamic` value under a name, `contains_var` must report whether that name exists, `get_var` must return a cloned `Dynamic`, and `get_var_value` must return the value converted to the requested Rust type or `None` when absent or not convertible. `clear` must remove module variables, functions, submodules, type mappings, type iterators, and metadata.

**Function and type entries.** When `set_native_fn` receives a name and Rust function, the module must store it in the internal namespace, replace an existing function with the same public call key, and return the native function hash. When `contains_fn` receives a hash returned from registration, it must report whether the module contains that function. When custom type display names are set, `get_custom_type_display` and `get_custom_type_display_by_name` must return them by Rust type or Rust type-name string respectively.

**Submodules and composition.** When `set_sub_module` receives a name and shared module, the module must make the submodule reachable under that name. `contains_sub_module` and `get_sub_module` must reflect the stored tree. When `combine` consumes another module, root variables, functions, submodules, and iterators from the other module must be merged into the receiver. When `combine_flatten` consumes another module, nested submodule contents from the other module must be flattened into the receiver root. When `fill_with` receives another module, only missing names in the receiver must be copied. When `merge` receives another module, the receiver must clone and merge all public entries from it.

**Indexing and qualified access.** When a module has been modified after indexing, `is_indexed` must return false until `build_index` runs. `build_index` must prepare variables, functions, and submodules for namespace-qualified access and return the module for chaining. When qualified names are registered through `register_static_module`, the engine must split paths by the namespace separator, build intermediate modules as needed, index modules before storage, and make calls such as `foo::bar::name()` resolve through the static module tree. If a qualified module or function is missing, then evaluation must return `EvalAltResult::ErrorModuleNotFound` or `EvalAltResult::ErrorFunctionNotFound`.

**Global modules.** When `register_global_module` receives a shared module, the engine must expose that module's functions and type iterators without namespace qualification, ignore its submodules and variables for global registration, and prefer modules registered later during global function search. When `register_static_module` receives a path and shared module, the engine must expose the module under that namespace path while also exposing functions marked for the global namespace without qualification.

**Resolvers.** `DummyModuleResolver::new` must create a resolver whose `resolve` always returns `EvalAltResult::ErrorModuleNotFound`. `StaticModuleResolver::new` must create an empty resolver; `insert` must store an indexed module under a path and assign the path as ID when the module has no ID; `remove`, `contains_path`, `iter`, `iter_mut`, `paths`, `values`, `clear`, `is_empty`, `len`, and `merge` must project that path-to-module map. If `StaticModuleResolver::resolve` receives an absent path, then it must return `EvalAltResult::ErrorModuleNotFound`.

## Grain Bytecode Programs

This section covers the public `rhai::grain` feature surface for lowering, running, serializing, and comparing bytecode programs.

**Compilation equivalence.** `Compiler::new` must create a default compiler. When `Compiler::compile` receives an `AST`, it must return a `Program` that owns or references everything needed to execute the script except the `Engine`. For every script accepted by `Engine::compile`, evaluating the compiled `Program` with `Vm::eval_with_scope` must return the same success value or public `EvalAltResult` variant family as `Engine::eval_ast_with_scope`, and it must leave the caller's `Scope` with the same visible variables, values, and constant flags.

**Residual coverage.** When the compiler cannot lower a construct to bytecode, the `Program` must retain a residual AST fragment and `residual_count` or `residual_nodes` must report remaining walker-backed work. `first_unsupported` must return the first named unsupported construct and its script position when one is present, otherwise `None`. Residual fragments must preserve runtime behavior through `Vm`, but they must prevent artifact writing.

**Program projections.** `Program::code` returns the encoded instruction bytes, `functions` returns compiled script-function descriptors, `main` returns the main chunk, `max_stack` returns the declared operand-stack requirement, `switches` returns switch tables, `position` maps an instruction address to a script `Position`, `positions` returns the positions table, and `debug_id` returns the diagnostics identity for sidecar matching. `makes_fn_pointers` must return true when the program contains function-pointer creation that requires callback wrappers and must return the same answer before and after serialization.

**Ownership and sharing.** When `into_owned` is called on a borrowed program, the returned program must no longer borrow artifact bytes. When `into_shared` is called on an owned program, it must return a shared program suitable for `Vm::eval_with_callbacks`. If a program still borrows bytes, then the caller must use `into_owned` before converting to a shared program.

**Verification and artifacts.** `verify` must return success for internally consistent compiled chunks and an error for invalid bytecode structure. When `residual_count` is zero, `write` must serialize a program to bytes that `Program::read` accepts in the same ABI and hashing environment. When residual fragments remain, `write` must return `WriteError`. When `write_stripped` succeeds, it must return a `Stripped` value containing an artifact without positions and a `Sidecar` containing position data. When `Program::read` receives bytes with an incompatible ABI, corrupted structure, or mismatched hashing probe, it must return `ReadError`.

**Virtual machine execution.** `Vm::new` must bind a VM to an `Engine` and reuse runtime caches across calls on that VM. `Vm::eval`, `eval_with_scope`, `run`, and `run_with_scope` must execute a `Program` with a fresh or provided scope following the same result and scope mutation rules as engine AST evaluation. `call_function` must call a compiled function by function table identity, while `call_fn` and `call_fn_with_options` must mirror `Engine::call_fn` and `Engine::call_fn_with_options` for name-based calls. If a VM run fails, `fault_pc` must return the innermost failing instruction address when known, and `fault_trace` must return frames that a `Sidecar` resolves to source sites when position data was stripped.

## State Model

The public state consists of these projections:

1. The `Engine` projection contains registered native functions, custom type names, global modules, static module namespaces, module resolver, callbacks, limits, optimization level, disabled symbols, default tag, and feature-gated services.
2. The `Scope` projection contains an ordered stack of named `Dynamic` values, each with read-write or read-only access, plus module export aliases when module support is present.
3. The `AST` projection contains parsed script statements or expressions, script-defined functions, embedded self-contained modules, source identity, and metadata when enabled.
4. The `Module` projection contains ID, documentation when enabled, variables, functions, submodules, custom type names, iterator registrations, and indexed qualified lookup tables.
5. The `Dynamic` projection contains the runtime value, type identity, access mode, and conversion behavior used by scripts, scopes, modules, native callbacks, and serde support.
6. The `Program` projection contains Grain bytecode, compiled function descriptors, constants, names, source positions or stripped-position identity, residual AST fragments, and optional callback support data.
7. The `Vm` projection contains a borrowed `Engine`, runtime caches, operand stack, fault trace, and execution state for running one or more `Program` values.

## Error Semantics

| Condition | Public result |
|---|---|
| Script text passed to `eval`, `eval_with_scope`, `run`, `run_with_scope`, `eval_expression`, or `eval_expression_with_scope` has invalid lexical or parse syntax | Boxed `EvalAltResult::ErrorParsing` containing `ParseErrorType` or `LexError` |
| Script text passed to `compile`, `compile_with_scope`, `compile_expression`, `compile_expression_with_scope`, or `compile_scripts_with_scope` has invalid lexical or parse syntax | `ParseError` containing `ParseErrorType` or `LexError` |
| A full-script method returns a value that does not convert to the requested Rust type | `EvalAltResult::ErrorMismatchOutputType` |
| Runtime data has the wrong type for an operation | `EvalAltResult::ErrorMismatchDataType` |
| Arithmetic evaluation fails because an operation such as division, remainder, exponentiation, shift, or numeric conversion cannot produce a valid result | `EvalAltResult::ErrorArithmetic` |
| A variable is read and no scope, resolver, or callback supplies it | `EvalAltResult::ErrorVariableNotFound` |
| A function/operator call has no matching script or native overload | `EvalAltResult::ErrorFunctionNotFound` |
| A module import or static module path is unavailable | `EvalAltResult::ErrorModuleNotFound` |
| Assignment tries to mutate a constant variable | `EvalAltResult::ErrorAssignmentToConstant` |
| A non-pure method, property setter, or index setter is called on a constant receiver | `EvalAltResult::ErrorNonPureMethodCallOnConstant` or constant-assignment error |
| Array, string, bit-field, map, or custom index access is invalid | `EvalAltResult::ErrorArrayBounds`, `ErrorStringBounds`, `ErrorBitFieldBounds`, `ErrorIndexNotFound`, or `ErrorIndexingType` |
| A configured safety limit is exceeded | `EvalAltResult::ErrorTooManyOperations`, `ErrorTooManyVariables`, `ErrorTooManyModules`, `ErrorStackOverflow`, or `ErrorDataTooLarge` |
| File opening or reading fails | `EvalAltResult::ErrorSystem` |
| A native callback returns an error | That boxed `EvalAltResult` propagates through the caller |
| `Scope::pop` is called on an empty scope or `Scope::set_value` mutates a constant | Panic |
| Grain artifact writing is attempted with residual AST fragments | `grain::format::WriteError::HasResiduals` |
| Grain artifact reading receives incompatible or invalid bytes | `grain::format::ReadError` |
| Grain VM execution fails | Boxed `EvalAltResult` plus VM fault address trace when available |

## Cross-View Invariants

1. Evaluating script text through `Engine::eval_with_scope`, evaluating an `AST` through `Engine::eval_ast_with_scope`, and evaluating an equivalent Grain `Program` through `Vm::eval_with_scope` must produce the same public success value or public error variant family for the same engine and starting scope.
2. A variable changed by script execution must be visible through `Scope::get_value`, `Scope::get`, `Scope::iter`, and later evaluations using the same `Scope`.
3. A constant inserted through `Scope::push_constant` or `push_constant_dynamic` must be visible to compilation for constant propagation and must reject runtime assignment through engine, module, and Grain VM execution paths.
4. A native function registered through `Engine::register_fn`, `Engine::register_raw_fn`, `Module::set_native_fn`, or a global module must resolve consistently from script text, compiled `AST` calls, `Engine::eval_fn_call`, and Grain VM execution when the function is in scope.
5. A module registered through `StaticModuleResolver`, `register_static_module`, or a self-contained `AST` must expose the same public variables and functions through namespace-qualified script access and module inspection APIs.
6. A custom type display name registered on an engine or module must be used consistently by `type_of`, mismatch errors, native call resolution, and metadata/signature projections where those projections are enabled.
7. A Grain `Program` written with `write` and read with `Program::read` must evaluate with the same result, scope mutations, function-pointer capability, and public error semantics as the original program in the same engine environment.
8. When positions are stripped from a Grain artifact, VM runtime errors must omit direct script positions while `fault_trace` and the retained `Sidecar` must resolve instruction addresses back to source sites.

## Public Interface

### Import Surface

```rust
use rhai::{
    Array, Blob, CallFnOptions, CustomType, Dynamic, Engine, EvalAltResult,
    FLOAT, FnAccess, FnNamespace, FnPtr, FuncArgs, FuncRegistration,
    ImmutableString, INT, LexError, Map, Module, ModuleResolver,
    NativeCallContext, OptimizationLevel, ParseError, ParseErrorType,
    Position, RhaiNativeFunc, Scope, TypeBuilder, VarDefInfo, AST,
    OP_CONTAINS, OP_EQUALS, FUNC_TO_DEBUG, FUNC_TO_STRING,
    eval, eval_file, run, run_file, format_map_as_json,
};
```

```rust
use rhai::module_resolvers::{
    DummyModuleResolver, FileModuleResolver, ModuleResolversCollection,
    StaticModuleResolver,
};
```

```rust
use rhai::serde::{from_dynamic, to_dynamic, DynamicDeserializer, DynamicSerializer};
```

```rust
use rhai::grain::{Compiler, Fault, Program, Sidecar, Stripped, Vm};
use rhai::grain::format::{Abi, AbiMismatch, ReadError, WriteError};
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Engine` | class | Owns parser, evaluator, registered native API, modules, callbacks, limits, and runtime options. |
| `AST` | class | Holds compiled script or expression form for repeated evaluation and function calls. |
| `Scope` | class | Stores ordered script variables and constants shared between Rust and script execution. |
| `Dynamic` | class | Stores a runtime Rhai value with type identity, access mode, and conversion helpers. |
| `Module` | class | Stores script-visible variables, native functions, custom type metadata, submodules, and indexes. |
| `ModuleResolver` | trait | Resolves script import paths to shared modules and optional ASTs. |
| `StaticModuleResolver` | class | Resolves imports from an in-memory path-to-module map. |
| `DummyModuleResolver` | class | Rejects every module path with a module-not-found error. |
| `ModuleResolversCollection` | class | Chains multiple resolvers and resolves through them in order. |
| `FileModuleResolver` | class | Resolves modules from script files when filesystem APIs are available. |
| `CallFnOptions` | class | Configures Rust-to-script function calls, including `this`, tags, pre-evaluation, scope rewind, and namespace search. |
| `FuncRegistration` | class | Builds detailed native function registration metadata for modules and engines. |
| `FnNamespace` | enum | Describes whether a function is visible globally or only inside module namespaces. |
| `FnAccess` | enum | Describes public versus private script function access. |
| `NativeCallContext` | class | Exposes engine, call source, tag, and callback helpers to raw native functions. |
| `RhaiNativeFunc` | trait | Adapts Rust functions and closures for Rhai native registration. |
| `FuncArgs` | trait | Converts Rust argument tuples into dynamic call arguments. |
| `CustomType` | trait | Supplies custom type metadata through derive or builder registration. |
| `TypeBuilder` | class | Registers custom type properties, indexers, methods, and iterable behavior. |
| `FnPtr` | class | Represents script function pointers and curried arguments. |
| `ImmutableString` | class | Represents script strings using the engine's immutable string type. |
| `Array` | type | Alias for a vector of `Dynamic` values when indexing support is enabled. |
| `Blob` | type | Alias for a byte vector when indexing support is enabled. |
| `Map` | type | Alias for a string-keyed map of `Dynamic` values when object support is enabled. |
| `INT` | type | System integer type selected by feature flags. |
| `FLOAT` | type | System floating-point type selected by feature flags when floating point support is enabled. |
| `EvalAltResult` | exception | Public runtime and evaluation error enum. |
| `ParseError` | exception | Public parse error with position. |
| `ParseErrorType` | exception | Public parse error category enum. |
| `LexError` | exception | Public lexical error category enum. |
| `Position` | class | Public script source position value. |
| `OptimizationLevel` | enum | Selects no, simple, or full AST optimization when optimization support is enabled. |
| `VarDefInfo` | class | Describes variable definitions passed to variable-definition callbacks. |
| `eval` | function | Evaluates script text through a fresh engine and returns a typed result. |
| `run` | function | Runs script text through a fresh engine for side effects. |
| `eval_file` | function | Evaluates a script file through a fresh engine when filesystem APIs are available. |
| `run_file` | function | Runs a script file through a fresh engine when filesystem APIs are available. |
| `format_map_as_json` | function | Formats a Rhai map as JSON text when object support is enabled. |
| `from_dynamic` | function | Deserializes a `Dynamic` into a serde-compatible Rust value when serde support is enabled. |
| `to_dynamic` | function | Serializes a serde-compatible Rust value into `Dynamic` when serde support is enabled. |
| `DynamicDeserializer` | class | Implements serde deserialization from `Dynamic`. |
| `DynamicSerializer` | class | Implements serde serialization into `Dynamic`. |
| `Compiler` | class | Lowers `AST` values into Grain `Program` values. |
| `Program` | class | Holds a Grain bytecode artifact plus metadata and residual fallback fragments. |
| `Vm` | class | Executes Grain `Program` values against an `Engine`. |
| `Fault` | class | Describes a Grain VM failed instruction address and chain slot. |
| `Sidecar` | class | Resolves stripped Grain fault addresses back to source positions. |
| `Stripped` | class | Holds a stripped Grain artifact and its sidecar. |
| `Abi` | class | Describes the Grain artifact ABI used for compatibility checks. |
| `AbiMismatch` | exception | Reports Grain artifact ABI incompatibility. |
| `ReadError` | exception | Reports Grain artifact read failures. |
| `WriteError` | exception | Reports Grain artifact write failures. |
| `OP_CONTAINS` | constant | Public operator name for containment. |
| `OP_EQUALS` | constant | Public operator name for equality. |
| `FUNC_TO_STRING` | constant | Public function name used for string conversion. |
| `FUNC_TO_DEBUG` | constant | Public function name used for debug-string conversion. |

### CLI Entry Points

This specification does not require command-line entry points. Programmatic use is through the Rust crate imports listed above.

## Appendix A: Environment

The working environment runs Rust `1.97.1` and Cargo `1.97.1` on Linux without network access. The crate declares minimum Rust `1.66.0`.

The provided Cargo manifest and lockfile make these non-target crates available: `ahash 0.8.4`, `allocator-api2 0.2.21`, `arbitrary 1.3.2`, `arrayvec 0.7.6`, `autocfg 1.4.0`, `base-x 0.2.11`, `bitflags 2.3.3`, `bumpalo 3.17.0`, `byteorder 1.5.0`, `cfg-if 1.0.0`, `clipboard-win 5.4.0`, `const-random 0.1.18`, `const-random-macro 0.1.16`, `core-error 0.0.0`, `crunchy 0.2.3`, `derive_arbitrary 1.4.1`, `discard 1.0.4`, `document-features 0.2.0`, `endian-type 0.1.2`, `equivalent 1.0.2`, `errno 0.3.10`, `error-code 3.3.1`, `fd-lock 4.0.3`, `foldhash 0.1.4`, `getrandom 0.2.7`, `glob 0.3.2`, `hashbrown 0.15.0`, `home 0.5.11`, `instant 0.1.13`, `itoa 0.4.8`, `js-sys 0.3.77`, `libc 0.2.171`, `libm 0.2.0`, `linux-raw-sys 0.4.15`, `log 0.4.26`, `memchr 2.7.4`, `nibble_vec 0.1.0`, `nix 0.27.1`, `no-std-compat 0.4.1`, `num-traits 0.2.14`, `once_cell 1.20.1`, `paste 1.0.15`, `portable-atomic 1.11.0`, `proc-macro2 1.0.94`, `quote 1.0.40`, `radix_trie 0.2.1`, `rhai_codegen 3.2.0` from the workspace path, `rmp 0.8.14`, `rmp-serde 1.1.1`, `rust_decimal 1.24.0`, `rustc_version 0.2.3`, `rustix 0.38.8`, `rustversion 1.0.20`, `rustyline 15.0.0`, `ryu 1.0.20`, `semver 0.9.0`, `semver-parser 0.7.0`, `serde 1.0.136`, `serde_derive 1.0.136`, `serde_json 1.0.45`, `sha1 0.6.1`, `sha1_smol 1.0.1`, `smallvec 1.7.0`, `smartstring 1.0.0`, `spin 0.7.1`, `static_assertions 1.1.0`, `stdweb 0.4.20`, `stdweb-derive 0.5.3`, `stdweb-internal-macros 0.2.9`, `stdweb-internal-runtime 0.1.5`, `syn 1.0.109`, `syn 2.0.100`, `termcolor 1.4.1`, `thin-vec 0.2.13`, `tiny-keccak 2.0.2`, `toml 0.5.11`, `trybuild 1.0.64`, `unicode-ident 1.0.18`, `unicode-segmentation 1.12.0`, `unicode-width 0.1.14`, `unicode-xid 0.2.0`, `utf8parse 0.2.2`, `version_check 0.9.5`, `wasi 0.11.0+wasi-snapshot-preview1`, `wasm-bindgen 0.2.100`, `wasm-bindgen-backend 0.2.100`, `wasm-bindgen-macro 0.2.100`, `wasm-bindgen-macro-support 0.2.100`, `wasm-bindgen-shared 0.2.100`, `web-sys 0.3.77`, `winapi-util 0.1.9`, Windows support crates named in the lockfile, `zerocopy 0.7.35`, and `zerocopy-derive 0.7.35`.

The project must declare its packaging metadata in `Cargo.toml` at the project root so the library crate builds through Cargo.

## Appendix B: Assessment Notes

Assessment covers public Rust API behavior across engine creation, script parsing, text and AST evaluation, scope mutation, constants, script function calls, native function registration, custom type registration, module variables, static modules, module resolvers, file execution, serde conversion, public error categories, and Grain compile/run/serialize equivalence.

Checks compare public return values, public error variants, scope state, module state, resolver behavior, serialization round trips, and command exit behavior. They do not depend on private AST node layout, bytecode instruction layout, exact diagnostic wording, or private fixture organization.
