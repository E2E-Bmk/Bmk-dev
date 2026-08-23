# gojq Query Engine Specification

This specification defines a compatible implementation of the retained library surface from `github.com/itchyny/gojq`. It describes observable parsing, execution, iteration, configuration, module loading, comparison, and encoding behavior. Parser organization, bytecode design, optimization, concrete iterator types, and source layout are not prescribed.

## Product Overview

The module parses jq-like query text, evaluates it against JSON-shaped Go values, and streams zero or more results through an iterator. A query supports one-time compilation and safe reuse with variables, custom functions, environment values, an auxiliary input stream, or modules.

Accepted runtime values are `nil`, `bool`, `int`, `float64`, `*big.Int`, `json.Number`, `string`, `[]any`, and `map[string]any`. Results and custom-function values use the same domain. Unsupported Go values are errors where reached by query evaluation, or panics only in the value helper functions where this specification explicitly says so.

## Representative Workflows

### Parse and stream

Parse a query containing field selection, array iteration, filtering, and projection. Run it against a JSON-shaped map, consume every iterator item in order, and handle any emitted error value without changing the input.

### Compile and reuse

Parse once, compile with declared variables and a custom function, and run the resulting code against multiple independent inputs. Each run binds its own values and produces an independent iterator; cancellation of one contextual run leaves later runs usable.

### Local modules

Create jq and JSON module files in a search directory, configure a module loader, compile imports, and combine imported functions/data with the primary input. Missing files and parse failures return compilation errors without network access.

## Non-Goals

CLI flags and process exit, YAML, colored output, debug traces, exact bytecode, optimizer choice, exported AST layout, exact error strings, and compatibility with arbitrary structs, typed slices, or typed maps are outside scope. A conforming implementation need not reproduce undocumented parser recovery or resource exhaustion behavior.

## Parsing and Query Values

`Parse` must accept whitespace, comments, literals, identity `.`, field and index access, pipes, commas, parentheses, arrays, objects, arithmetic and comparison operators, boolean operators, conditionals, `try`/`catch`, variable binding, reductions, function definitions, imports, and the retained built-ins used below.

Successful parsing returns a non-nil reusable `*Query`. Invalid syntax returns nil and an error assignable to `*ParseError`. `ParseError.Offset` is a byte offset after scanning the offending input and `Token` is the offending token, or empty at end of input. UTF-8 before an error must therefore affect byte offset rather than rune count. Exact `Error()` wording is not required, but it must be non-empty.

`Query.String` must return valid query text which parses successfully and is behaviorally equivalent to the original query for the same inputs. It must preserve string literal contents, operator grouping, function definitions, imports, and object keys. Whitespace and equivalent parenthesization are not prescribed.

## Iterator Contract

`Iter.Next` returns `(value, true)` for each emitted item in order, including values that implement `error`. After exhaustion it returns `(_, false)` on every later call. An emitted error is data in the stream and does not use a separate error return.

`NewIter()` is immediately exhausted. `NewIter(v)` emits `v` once. `NewIter(a, b, c)` emits all supplied values in order. Different iterators have independent positions, and exhaustion never repeats the last value.

## Basic Evaluation and Streaming

Identity emits its input unchanged. Literal `null`, booleans, strings, integer numbers, arrays, and objects emit their corresponding JSON-shaped Go values. A comma expression emits all left results followed by all right results. A pipe feeds every upstream result into the downstream filter in order. `empty` emits no value.

Object field lookup returns the matching value and returns `nil` for a missing field. Optional lookup suppresses the associated type/index error. Array indices are zero based; a negative index counts from the end; an out-of-range index returns `nil`. Array and string slices use half-open bounds and support omitted bounds. Iteration over an array emits elements in order and over an object emits values in lexicographically sorted key order.

Array construction collects every inner result into one `[]any`. Object construction evaluates its value filters and emits multiple objects when a value filter emits multiple alternatives. Object keys in emitted maps are strings.

Arithmetic supports numeric addition, subtraction, multiplication, division, remainder, and unary negation. Addition also concatenates strings and arrays and merges objects. Numeric operations preserve exact integral results as `int` or `*big.Int` when necessary and use `float64` for non-integral results. Invalid operand combinations emit errors rather than silently coercing strings.

Equality and ordering use jq value semantics. `==` and `!=` compare recursively. The total type order is null, false, true, numbers, strings, arrays, objects. Arrays compare lexicographically. Objects first compare their sorted key sets and then the corresponding values. `and` and `or` use jq truthiness, where only `false` and `nil` are false, and must short-circuit branches whose values are not needed.

`if ... then ... elif ... else ... end` selects branches using jq truthiness. `select(f)` emits its input exactly when `f` is truthy. `map(f)` applies `f` to each array element and collects all results. `length` returns zero for null, rune count for a string, and element/key count for arrays/objects. `keys` returns sorted object keys or integer array indices. `has(k)` tests object keys or valid array indices.

The retained aggregation and sequence built-ins include `add`, `any`, `all`, `min`, `max`, `sort`, `unique`, `range`, `first`, `last`, `limit`, `until`, and `while`. They must compose as jq filters and preserve documented stream order. Empty aggregations follow jq conventions: `add` yields null, `any` is false, and `all` is true.

String built-ins retained by this contract include `ascii_downcase`, `ascii_upcase`, `startswith`, `endswith`, `ltrimstr`, `rtrimstr`, `split`, `join`, `explode`, `implode`, `tostring`, and `tonumber`. Regular-expression behavior is retained for `test`, `match`, `capture`, `scan`, `sub`, and `gsub`, including named captures and global replacement.

Path and update behavior includes `path`, `getpath`, `setpath`, `delpaths`, assignment `=`, update assignment `|=`, arithmetic update operators, and `del`. Updates must rebuild only the selected logical paths and must not mutate caller-owned input maps or slices.

## Functions, Variables, and Control Flow

Query-defined functions support zero or more filter parameters, lexical variable binding with `as`, recursion, and multiple emitted values. Local bindings must not leak outside their scope. `reduce` and `foreach` must process upstream results in order and apply their initializer/update/extract filters with the documented jq scoping.

`try f catch g` must feed the caught error value into `g`; `f?` suppresses ordinary evaluation errors. The built-ins `error`, `halt`, and `halt_error` emit error values. A halting error must be assignable to `*HaltError`; `Value()` exposes its jq value and `ExitCode()` exposes its code. `halt` uses a nil value and zero exit code. `halt_error(n)` uses the current input as its value and the supplied integer code.

## Compilation and Reuse

Compiling a valid non-nil query returns reusable `*Code`. Passing a nil query is outside scope. `Query.Run` is behaviorally equivalent to compiling without options and calling `Code.Run`; their result sequences, including emitted errors, must agree.

The same parsed query and compiled code support concurrent calls from multiple goroutines with independent inputs. Calls must not share iterator position, variables, cancellation state, or intermediate results. This concurrency guarantee excludes configurations that deliberately share a stateful caller-owned `Iter` through `WithInputIter`.

`RunWithContext` behaves like `Run` while the context is active. If the context is already canceled or becomes canceled during an otherwise continuing computation, iteration must promptly emit or expose a cancellation error and terminate without leaking execution. One canceled call must not poison later calls on the same query or code.

## Compiler Options

`WithVariables(names)` declares variables in exactly that order. Names must be valid jq variables beginning with `$`; an invalid name makes `Compile` fail. Repeated names are outside scope. `Code.Run(input, values...)` binds values positionally. Too few or too many values produce an emitted error and no successful query result.

`WithFunction` registers a single-result internal function for every arity in the inclusive range. The callback receives the current input and evaluated argument values. Its returned value is emitted; if it returns an error, that error is emitted and remains catchable. Multiple registrations of the same name with disjoint arities coexist. An invalid name or an overlap with an incompatible definition makes compilation fail where applicable.

`WithIterFunction` has the same dispatch rules, but the callback's iterator emits zero, one, or many values and errors. Defining iterator and non-iterator variants with the same name must panic. For both option constructors, arities outside `0 <= minarity <= maxarity <= 30` must panic immediately.

`WithInputIter` enables `input` and `inputs`. Without it, compiling a query that invokes either returns an error. `input` consumes one auxiliary value per invocation; `inputs` emits the remaining values. Auxiliary iterator exhaustion is handled as an evaluation error for `input` and ordinary end of stream for `inputs`.

`WithEnvironLoader` supplies `KEY=value` strings to `env` and `$ENV`. Without the option the visible environment is empty. Duplicate keys use the last supplied value, entries without `=` are ignored, and the operating-system environment must never be read implicitly.

## Module Loading

`WithModuleLoader` enables `include`, jq module imports, JSON imports, and optional initialization modules using the method shapes in the public API catalog. Compilation must return loader and module parse errors. Import aliases isolate module functions; JSON imports bind the decoded value to the declared variable.

`NewModuleLoader(paths)` searches non-empty base paths in order. It resolves `name.jq` or `name/name.jq` for jq modules and the analogous `.json` forms for JSON data. A metadata `search` path takes precedence. JSON decoding must preserve JSON numbers rather than unnecessarily converting every number to `float64`, and multiple top-level JSON values are returned as an array of values.

An unreadable or missing requested module returns an error. Loading is local filesystem behavior only and must not use the network. Tests use temporary directories and do not rely on the current user's home or executable path.

## Value Comparison

`Compare` returns exactly -1, 0, or 1. It implements the total type order defined above, recursively compares arrays and objects, sorts object keys before comparison, and treats supported numeric representations (`int`, `float64`, `*big.Int`, `json.Number`) by numeric value rather than concrete Go type. Equal map content must compare equal regardless of insertion order.

Within floating-point values, NaN sorts before every number, including another NaN; `Compare(NaN, NaN)` therefore returns -1. Positive and negative zero compare equal. Inputs outside the supported jq value domain sort in the implementation's pre-null category; no more detailed ordering among unsupported values is required.

## Encoding, Type Names, and Preview

`Marshal` produces compact jq-flavored JSON with lexicographically sorted object keys. It supports exactly the jq value domain, preserves arbitrary-size integers and `json.Number` text, encodes NaN as `null`, clamps infinities to signed `math.MaxFloat64`, uses JSON escaping including `\b` and `\f`, and does not HTML-escape `<`, `>`, `&`, U+2028, or U+2029. Unsupported values panic; for supported values the returned error is nil.

`TypeOf` returns `null`, `boolean`, `number`, `string`, `array`, or `object` for the corresponding supported values and panics for an unsupported type.

`Preview` is a compact jq-flavored encoding suitable for error messages. Untruncated primitive values match `Marshal`. Long results are UTF-8 safely truncated to approximately 30 bytes and end with a type-appropriate marker containing `...`; exact future-adjustable width is not required. It panics for unsupported types only if evaluation reaches the value before truncation finishes.

## Product State Model and Error Semantics

Evaluation must not mutate caller-provided values. Returned arrays and objects from update or construction operations must not alias writable intermediate containers across separate runs. Iterators are stateful but parsed queries and compiled code are reusable.

Syntax errors and compile-time errors are returned by `Parse` and `Compile`. Runtime failures are emitted by `Iter`. Exact error strings and private concrete error types are not prescribed. Public operations must not panic for malformed query text, missing fields, out-of-range lookup, ordinary type errors, missing modules, canceled contexts, variable count mismatch, or iterator exhaustion.

## Cross-View Invariants

- Direct `Query.Run` and option-free compiled execution produce equivalent streams.
- Parsing `Query.String()` produces an equivalent query.
- A value produced by supported query evaluation is valid input to `TypeOf`, `Marshal`, `Preview`, and `Compare` without conversion.
- Update expressions do not change the original input observed by a later run.
- Custom functions, variables, modules, environment values, and auxiliary input compose in one compiled query without losing their scopes.
- A caught runtime error becomes a jq value; an uncaught error remains an iterator item.
- Context cancellation and concurrent reuse do not corrupt later executions.

## Public Interface

### Import Surface

The required module import and complete retained symbol catalog are included below. Extra API is permitted but evaluation does not require it.

### API Catalog

The retained catalog covers parsing, query and compiled execution, iterators, compiler options, module loading, runtime errors, comparison, encoding, type names, and preview behavior.

### Normative Symbol Catalog

### Public API Surface — gojq Query Engine

This task targets module and package `github.com/itchyny/gojq`. The catalog below is the complete public surface required by the specification and evaluation.

#### Required import

```go
import "github.com/itchyny/gojq"
```

Evaluation code may additionally import Go standard-library packages only.

#### Parsing and execution

```go
type Query struct { /* fields and internal AST layout are implementation-defined */ }

func Parse(src string) (*Query, error)
func (q *Query) Run(v any) Iter
func (q *Query) RunWithContext(ctx context.Context, v any) Iter
func (q *Query) String() string

type ParseError struct {
	Offset int
	Token  string
}
func (e *ParseError) Error() string
```

#### Compilation and configuration

```go
type Code struct { /* implementation-defined */ }
type CompilerOption func(/* implementation-private compiler */)

func Compile(q *Query, options ...CompilerOption) (*Code, error)
func (c *Code) Run(v any, values ...any) Iter
func (c *Code) RunWithContext(ctx context.Context, v any, values ...any) Iter

func WithVariables(variables []string) CompilerOption
func WithFunction(name string, minarity, maxarity int, f func(any, []any) any) CompilerOption
func WithIterFunction(name string, minarity, maxarity int, f func(any, []any) Iter) CompilerOption
func WithInputIter(inputIter Iter) CompilerOption
func WithEnvironLoader(environLoader func() []string) CompilerOption
func WithModuleLoader(moduleLoader ModuleLoader) CompilerOption
```

The concrete parameter of `CompilerOption` may remain unnameable outside the package, as in the reference API. Callers only pass option values to `Compile`.

#### Iterators and runtime errors

```go
type Iter interface {
	Next() (any, bool)
}

func NewIter[T any](values ...T) Iter

type ValueError interface {
	error
	Value() any
}

type HaltError struct { /* implementation-defined */ }
func (e *HaltError) Error() string
func (e *HaltError) Value() any
func (e *HaltError) ExitCode() int
```

#### Module loading

```go
type ModuleLoader any

func NewModuleLoader(paths []string) ModuleLoader
```

`WithModuleLoader` must accept user-defined values implementing any of these optional method sets:

```go
LoadInitModules() ([]*Query, error)
LoadModule(string) (*Query, error)
LoadModuleWithMeta(string, map[string]any) (*Query, error)
LoadJSON(string) (any, error)
LoadJSONWithMeta(string, map[string]any) (any, error)
```

#### Value helpers

```go
func Compare(l, r any) int
func Marshal(v any) ([]byte, error)
func TypeOf(v any) string
func Preview(v any) string
```

#### Explicit exclusions

Exported AST node fields and node types other than `Query`, exact canonical formatting beyond the `Query.String` guarantees in the specification, CLI behavior, YAML input, color output, debug output, source-code layout, optimizer strategy, concrete iterator types, and exact error text are outside scope.

Evaluation does not inspect private state, rely on concrete types returned by `NewIter` or `NewModuleLoader`, import internal packages, or require network access.


## CLI Entry Points

There is no console script for this package. Programmatic use is through the Go import listed in the public interface.

## Environment

The submission must be a Go module with module path `github.com/itchyny/gojq`. It must build and test on Linux in offline mode. The implementation must vendor, replace, or avoid every non-standard dependency needed by submitted source. Filesystem tests use fresh temporary directories; tests do not depend on wall-clock timing, locale, host environment variables, or network access.

## Assessment Notes

Evaluation exercises public imports and symbols only. It compares complete finite streams, stops deliberately bounded infinite queries through context cancellation, and does not inspect private fields or optimizer output. Exact error wording, source layout, and whitespace from `Query.String` are not graded.
