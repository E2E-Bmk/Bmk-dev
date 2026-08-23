# Expr Rule Engine Reimplementation Specification

## Product Overview

`expr` is an embeddable Go expression engine that compiles a restricted expression language into reusable programs and evaluates those programs against map or struct environments. The implementation must expose the public compilation, evaluation, configuration, and AST-extension contracts described here while remaining free to choose its parser, checker, optimizer, and execution internals.

The module path must be `github.com/expr-lang/expr`. The primary package is `github.com/expr-lang/expr`; the public AST package is `github.com/expr-lang/expr/ast`. `Compile` returns an opaque `*vm.Program` from `github.com/expr-lang/expr/vm`.

## Scope

This specification covers the installable expression engine, its documented public packages, observable evaluation behavior, and the extension points listed below. Features excluded from the required surface are listed under Non-Goals.

## Context and Orientation

### Core Concepts

An expression is source text. Compilation parses the source, checks it against options and an optional environment shape, applies configured AST visitors, and returns a reusable program. Running a program supplies concrete environment values and returns either a value or an error. `Eval` is the one-shot path that parses, compiles, and runs without explicit compile options.

An environment is either a string-keyed map or a struct value. It supplies variables and callable functions. A compiled program is immutable from a caller's perspective and must be reusable with multiple compatible environment values.

## Representative Workflows

**Compile once and run repeatedly.** A caller compiles an expression using `Env` to establish types, then runs the returned program with different values of the same shape. Each run must use its own supplied values and must not retain results from an earlier run.

**Configure a typed rule.** A caller combines `Env` with a return-kind option such as `AsBool`. Compilation must reject a statically incompatible expression; a successful run must return the requested Go kind, including the documented numeric conversions.

**Extend the language.** A caller registers a function or an operator overload, or supplies an AST visitor through `Patch`. Compilation must incorporate that extension and running the program must observe the transformed behavior.

**Inspect a program.** A caller obtains the program's original source and compiled AST projection. Walking or finding nodes must expose public node types without requiring access to compiler internals.

## Behavior

### Literals and Core Operators

The language must evaluate deterministic scalar and collection literals. Integer literals return Go `int`; decimal literals return `float64`; quoted strings return `string`; `true`, `false`, and `nil` return their corresponding values. Array literals return an ordered slice, and map literals return a string-keyed map with recursively evaluated values.

Arithmetic must support `+`, `-`, `*`, `/`, `%`, and exponentiation `**` for compatible numeric operands. `+` must also concatenate strings. Parentheses determine grouping. Unary `-` negates numbers and `not`/`!` negates booleans. Comparisons `==`, `!=`, `<`, `<=`, `>`, and `>=` return booleans. Boolean `and`/`&&` and `or`/`||` must use short-circuit evaluation unless `DisableShortCircuit` is supplied.

`in` tests membership in arrays, maps, and strings as appropriate; `not in` negates it. `a ?? b` returns `a` when it is non-nil and otherwise returns `b`. Optional member access `value?.field` returns nil rather than failing when the receiver is nil. Indexing and slicing use zero-based indexes; omitted slice bounds mean the beginning or end. An inclusive integer range `a..b` produces each integer from `a` through `b`.

### Variables, Environments, and Calls

`Env` must make map keys available as variables and infer their types from the supplied values. For a struct environment, exported fields are variables, an `expr` tag renames a field, exported methods are callable functions, and promoted exported fields and methods from embedded structs remain accessible.

Unknown top-level variables must make `Compile` fail by default when an environment shape is supplied. `AllowUndefinedVariables` must permit compilation and resolve a missing runtime variable as nil. Accessing a missing key on a `map[string]any` must return nil; accessing an unknown field on a statically known struct must fail compilation.

`let name = value; expression` binds a local name and returns the final expression. Multiple statements separated by semicolons execute in order, and only the last value is returned. `$env` refers to the complete runtime environment. Function calls must accept environment functions and struct methods using their declared Go argument and result types.

### Predicate and Collection Operations

Predicate builtins use `{...}` with `#` for the current item and `#index` for its zero-based index. The abbreviated `.` member form denotes a member of the current item.

`all` returns true when every item satisfies the predicate, including an empty input. `any` returns true when at least one item satisfies it. `none` is the negation of `any`; `one` returns true only for exactly one matching item. `filter` retains matching items in input order. `map` transforms every item in input order. `count` returns the collection length without a predicate and the number of matches with one. `find` returns the first match or nil, and `findIndex` returns its index or `-1`. `groupBy` returns groups keyed by the predicate result.

`concat` appends arrays in argument order. `flatten` removes one level of nesting. `uniq` retains the first occurrence of each value. `join` converts items to text and inserts the delimiter. `reduce` exposes `#acc` and returns the accumulated value, using an explicit initial value when supplied. `sum`, `mean`, and `median` compute their conventional numeric results. `first` and `last` return nil for an empty array. `take` returns at most the requested number of leading elements. `reverse` returns reverse order. `sort` and `sortBy` return deterministic ascending order by default and descending order when requested. `keys` and `values` project a map; tests must compare these projections without depending on Go map iteration order.

### Deterministic Builtins

String builtins must implement `trim`, `trimPrefix`, `trimSuffix`, `upper`, `lower`, `split`, `splitAfter`, `replace`, `repeat`, `indexOf`, `lastIndexOf`, `hasPrefix`, and `hasSuffix` with their conventional Go string meanings. `len` returns the length of strings, arrays, and maps. `get` returns the indexed/keyed value and must return nil rather than panic for an unavailable position.

Number builtins must implement `max`, `min`, `abs`, `ceil`, `floor`, and `round`. Conversion builtins `int`, `float`, and `string` return the corresponding Go representation for supported scalar inputs; `type` returns a stable lowercase category such as `int`, `float`, `string`, `bool`, `array`, `map`, or `nil`. Base64 encode/decode must round-trip UTF-8 strings. `toPairs` converts a map to key/value pair objects and `fromPairs` reconstructs the map; tests must not depend on pair ordering.

Bitwise builtins must implement `bitand`, `bitor`, `bitxor`, `bitnand`, `bitnot`, `bitshl`, `bitshr`, and unsigned right shift `bitushr` for integer operands.

### Compilation and Execution Options

`AsBool`, `AsInt`, `AsInt64`, `AsFloat64`, and `AsKind` must require or convert to the requested result kind. `AsAny` accepts any result. `WarnOnAny` is valid only together with a concrete return-kind option and must reject a statically `any` result rather than silently accepting it.

`Optimize(false)` must preserve observable results while disabling optimizer rewrites. `DisableShortCircuit` must force both operands of boolean operators to be evaluated. `MaxNodes(n)` must reject expressions whose AST exceeds a positive limit; `MaxNodes(0)` disables this limit.

`Function` registers a named function backed by `func(params ...any) (any, error)`. Optional Go function signatures define accepted argument and return types for compile-time checking. A returned function error must propagate from `Run`.

`Operator` redirects a named binary operator to one of the registered or environment functions when its signature matches the operands. The overload result must participate in surrounding expressions.

`ConstExpr` must evaluate a named environment function during compilation when all its arguments are compile-time constants. Calls with nonconstant arguments remain runtime calls. `DisableBuiltin` removes one builtin during compilation. `DisableAllBuiltins` removes all builtins, while a later `EnableBuiltin` restores the named builtin.

`WithContext(name)` must inject the named environment value as the first argument for functions whose first parameter implements `context.Context`; ordinary functions remain callable normally. `Timezone(name)` must use the named location for `date` expressions that omit an explicit timezone and must panic when the location name cannot be loaded.

### AST Visitors and Patching

`ast.Node` must expose `Type`, `SetType`, `Location`, and `Nature` methods compatible with the signatures in Appendix A. The public node structs in the API catalog must carry their documented exported value, operator, child, argument, or collection fields.

`ast.Walk` must visit every reachable node exactly once in post-order: children before their parent. A nil node produces no visit. `ast.Find` must return a matching node when one exists and nil otherwise. Callers must not rely on which match is returned when several nodes satisfy the predicate.

`ast.Patch` replaces the node referenced by the supplied pointer. `expr.Patch(visitor)` must run the visitor during compilation before bytecode generation, so a replacement affects both the program's node projection and its runtime result. A newly constructed replacement that participates in further type-sensitive transformation must honor a caller-supplied `SetType` value.

### Program Projections

`Compile` must retain the original source string in `Program.Source().String()`. `Program.Node()` returns the compiled program's public AST projection after configured patching and optimization. These projections must describe the same program that `Run` executes.

## Contract

## State Model

A program transitions from source text to a successfully compiled immutable value or to a compile error. A successful program supports zero or more runs. Run-specific environment values and errors must not mutate the program or affect later runs.

## Error Semantics

Malformed syntax, unknown statically checked names, incompatible operators, invalid calls, incompatible requested return kinds, disabled builtins, and positive node-budget violations must return a non-nil compile error and a nil program. Tests must require the error condition, not exact diagnostic text or caret formatting.

Runtime lookup/type failures and errors returned by custom functions must produce a non-nil run error. A failed run must not poison subsequent runs of the same program.

`Eval` must return an error if its second argument is an `Option`; callers pass the environment value directly. Options documented to panic on invalid configuration (`WarnOnAny` without a concrete kind, an invalid `Function` signature descriptor, and an unknown `Timezone`) must panic before successful compilation.

## Cross-View Invariants

- `Eval(source, env)` and `Compile(source, Env(env))` followed by `Run(program, env)` must agree for expressions valid under both paths.
- A compiled program's runtime result must reflect its post-patch `Program.Node()` projection while `Program.Source()` retains the unmodified source.
- Reusing one program with different compatible environments must produce results from the current environment only.
- Disabling optimization must not change successful observable values or error conditions.
- Return-kind options must agree with the concrete Go type returned by `Run`.
- Collection transformations must preserve the order documented by their public result even when the input environment is reused.

### Concurrency and Isolation

Successfully compiled programs must be safe for concurrent read-only use by multiple goroutines with independent compatible environments. Results must not contain state accumulated by another run. The specification does not require concurrent mutation of environment objects to be safe.

## Public Interface

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `expr.Option` | type | Configures compilation. |
| `expr.Env` | function | Declares the compile-time environment shape. |
| `expr.AllowUndefinedVariables` | function | Relaxes unknown-variable checking. |
| `expr.AsAny`, `AsKind`, `AsBool`, `AsInt`, `AsInt64`, `AsFloat64` | functions | Configure the expected result kind. |
| `expr.WarnOnAny` | function | Rejects an unresolved `any` result under a concrete expectation. |
| `expr.Optimize`, `DisableShortCircuit`, `MaxNodes` | functions | Configure compilation and evaluation strategy. |
| `expr.Function`, `Operator`, `ConstExpr` | functions | Register custom callable and operator behavior. |
| `expr.DisableAllBuiltins`, `DisableBuiltin`, `EnableBuiltin` | functions | Configure builtin availability. |
| `expr.WithContext`, `Timezone` | functions | Configure contextual calls and default date location. |
| `expr.Patch` | function | Registers an AST visitor for compilation. |
| `expr.Compile`, `Run`, `Eval` | functions | Compile and execute expressions. |
| `ast.Node`, `ast.Visitor` | interfaces | Represent and visit public syntax nodes. |
| `ast.Walk`, `Find`, `Patch` | functions | Traverse, locate, and replace AST nodes. |
| public `ast.*Node` structs | structs | Represent literal, operator, call, member, conditional, binding, sequence, array, and map nodes. |
| `conf.Config` | struct | Opaque configuration value used by the `Option` function type. |
| `file.Location`, `file.Source` | structs | Public source-location and source-text values used by AST and program projections. |
| `nature.Nature` | struct | Opaque public type descriptor returned by AST nodes. |
| `vm.Program` | struct | Opaque reusable compiled program with source and AST projections. |

### CLI Entry Points

There is no console script or command-line entry point required by this specification.

### Dependencies

The implementation must use the Go standard library only. The submitted `go.mod` must declare module `github.com/expr-lang/expr` and must not require the pinned reference module or another expression-language implementation.

## Reference and Acceptance

### Acceptance Basis

Acceptance tests use only the public packages and symbols listed above. They compare returned values, Go types, errors, panics explicitly promised here, repeated-run isolation, and cross-view behavior. They do not inspect private fields, bytecode layouts, optimizer choices, or exact diagnostic strings.

### Compatibility Target

The behavioral reference is `expr-lang/expr` at commit `4b31df3a2e0eefec04c017a82a00e0f08541d3e4`. Where this specification narrows the upstream project, this document is authoritative for the task.

## Meta

## Non-Goals

- This specification does not require reproducing internal parser, checker, optimizer, compiler, or virtual-machine package layouts.
- This specification does not require byte-for-byte bytecode, disassembly, AST dumps, or diagnostic messages.
- This specification does not require every upstream builtin, date-format edge case, regular-expression edge case, or JSON formatting detail.
- This specification does not define performance equivalence with the reference implementation.
- This specification does not require a CLI, debugger, REPL, documentation generator, or compatibility with upstream internal packages.

### Implementation Freedom

Any architecture is acceptable when it satisfies the public imports, signatures, and observable contracts. A tree-walking interpreter is acceptable; producing reference bytecode is not required.

## Environment

The submission must be a Go module with module path `github.com/expr-lang/expr`, must use only the Go standard library, and must build and test offline on Linux with the configured Go toolchain.

## Assessment Notes

Acceptance checks use only the documented public surface and compare observable values, Go types, errors, panics, program reuse, and cross-view behavior. Private implementation details and exact diagnostic wording are outside the contract.

## Appendix A — Required Go Signatures

```go
// package expr
type Option func(c *conf.Config)
func Env(env any) Option
func AllowUndefinedVariables() Option
func Operator(operator string, fn ...string) Option
func ConstExpr(fn string) Option
func AsAny() Option
func AsKind(kind reflect.Kind) Option
func AsBool() Option
func AsInt() Option
func AsInt64() Option
func AsFloat64() Option
func WarnOnAny() Option
func Optimize(enabled bool) Option
func DisableShortCircuit() Option
func Patch(visitor ast.Visitor) Option
func Function(name string, fn func(params ...any) (any, error), types ...any) Option
func DisableAllBuiltins() Option
func DisableBuiltin(name string) Option
func EnableBuiltin(name string) Option
func WithContext(name string) Option
func Timezone(name string) Option
func MaxNodes(n uint) Option
func Compile(input string, options ...Option) (*vm.Program, error)
func Run(program *vm.Program, env any) (any, error)
func Eval(input string, env any) (any, error)

// package ast
type Node interface {
    Location() file.Location
    SetLocation(file.Location)
    Type() reflect.Type
    Nature() *nature.Nature
    SetNature(nature.Nature)
    SetType(reflect.Type)
    String() string
}
type Visitor interface { Visit(node *Node) }
func Walk(node *Node, visitor Visitor)
func Find(node Node, predicate func(Node) bool) Node
func Patch(node *Node, replacement Node)

// package vm
func (program *Program) Source() file.Source
func (program *Program) Node() ast.Node

// package file
type Location struct { From int; To int }
func NewSource(contents string) Source
func (source Source) String() string
func (source Source) Snippet(line int) (string, bool)
```

`Option` necessarily mentions the public `conf.Config` type in its Go definition, but callers are not required to construct or inspect that configuration type. `Node` necessarily mentions the public `file.Location` and `checker/nature.Nature` return types; acceptance tests treat nature values as opaque.

## Appendix B — Required AST Fields

All concrete nodes implement `ast.Node`. Besides their shared node methods, the following exported fields are required:

```go
type NilNode struct{}
type IdentifierNode struct { Value string }
type IntegerNode struct { Value int }
type FloatNode struct { Value float64 }
type BoolNode struct { Value bool }
type StringNode struct { Value string }
type BytesNode struct { Value []byte }
type ConstantNode struct { Value any }
type UnaryNode struct { Operator string; Node Node }
type BinaryNode struct { Operator string; Left Node; Right Node }
type ChainNode struct { Node Node }
type MemberNode struct { Node Node; Property Node; Optional bool; Method bool }
type SliceNode struct { Node Node; From Node; To Node }
type CallNode struct { Callee Node; Arguments []Node }
type BuiltinNode struct { Name string; Arguments []Node; Throws bool; Map Node; Threshold *int }
type PredicateNode struct { Node Node }
type PointerNode struct { Name string }
type ConditionalNode struct { Ternary bool; Cond Node; Exp1 Node; Exp2 Node }
type VariableDeclaratorNode struct { Name string; Value Node; Expr Node }
type SequenceNode struct { Nodes []Node }
type ArrayNode struct { Nodes []Node }
type MapNode struct { Pairs []Node }
type PairNode struct { Key Node; Value Node }
```
