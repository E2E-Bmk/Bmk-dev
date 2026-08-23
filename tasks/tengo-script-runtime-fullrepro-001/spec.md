# Tengo Script Runtime Reimplementation Specification

## Product Overview

Tengo is an embeddable scripting language for Go. The retained compiler/runtime surface lets callers evaluate expressions, inject Go values and functions, compile and rerun scripts, inspect and replace globals, import in-memory modules, and cancel execution. The module path must be `github.com/d5/tengo/v2`, and the root package name must be `tengo`.

## Scope

The required surface is the root `tengo` package and the language behavior documented here. It includes expression and statement execution, functions and closures, collection mutation and iteration, Go value conversion, reusable compiled programs, in-memory modules, allocation/constant limits, and context cancellation. Exact bytecode, instruction formatting, parser node types, standard-library modules, filesystem imports, and command-line tools are excluded.

## Representative Workflows

**Evaluate one expression.** A caller invokes `Eval` with a context, source expression, and string-keyed Go parameters. The returned Go value reflects the expression result, or the call returns a compile/runtime/context error.

**Compile and reuse.** A caller creates a `Script`, adds input globals, compiles it, runs it, reads output variables, changes an existing global through `Compiled.Set`, and runs again. Each run uses the current globals while preserving the compiled program.

**Fork execution state.** A caller clones a compiled program, changes clone inputs, and runs the original and clone independently. Collection and scalar globals in one instance must not be mutated by execution of the other.

**Import modules.** A caller builds a `ModuleMap`, adds a builtin-object module or a Tengo source module, assigns it to a script, and imports it by name. Module functions and values participate in ordinary expressions.

**Bound and cancel work.** A caller configures allocation or constant-object limits, or supplies a cancellable context. Limit exhaustion and cancellation stop execution with a non-nil error instead of hanging or returning a successful partial result.

## Language Behavior

### Values and expressions

Integer literals produce signed 64-bit integer values and decimal literals produce `float64`. String literals are UTF-8 strings, character literals produce runes, byte literals/values remain byte slices, booleans are `true` and `false`, and `undefined` is the absent value. Array literals preserve element order. Map literals have string keys and support both `m.key` and `m["key"]` selection.

Arithmetic supports `+`, `-`, `*`, `/`, `%`, unary `-`, and parentheses. Integer arithmetic returns integers except division follows Tengo integer division for integer operands; mixed numeric arithmetic returns a float when required. `+` concatenates strings. Comparisons `==`, `!=`, `<`, `<=`, `>`, and `>=` return booleans for compatible values. Bitwise `&`, `|`, `^`, `&^`, `<<`, and `>>` operate on integers.

Logical `&&` and `||` short-circuit and return booleans according to truthiness; `!` negates truthiness. False, zero numeric values, empty strings/bytes/arrays/maps, `undefined`, and false are falsy. A conditional expression `condition ? a : b` evaluates only the selected branch.

Indexing arrays, strings, and bytes is zero-based. An out-of-range or incompatible index produces `undefined` where Tengo defines a missing lookup rather than a runtime failure. Slices `value[low:high]` use a half-open range and permit omitted bounds. Map and array elements are assignable when the collection is mutable. Immutable collections reject element assignment.

### Variables, statements, and control flow

`name := value` defines a variable in the current scope; `name = value` replaces an existing assignable value. `if`/`else` chooses a block. `for condition { ... }` repeats while its condition is truthy; `for { ... }` repeats until `break`, `return`, error, limit, or cancellation. `for key, value in iterable { ... }` iterates arrays and strings by increasing index, and maps over all entries without a promised key order. `continue` advances to the next iteration and `break` exits the nearest loop.

The prefix and postfix forms of `++` and `--` update assignable numeric values. Block-local variables do not replace an outer variable unless assignment targets the outer binding. A `return` exits the current function, and a top-level return ends the script.

### Functions and closures

`func(a, b) { return expression }` creates a callable function. Calls bind positional arguments; missing parameters become `undefined`, and extra arguments are ignored for a non-variadic function. A variadic function declares its final parameter with `...` and receives remaining arguments as an array. Call spread `fn(array...)` supplies array elements as individual arguments.

Functions capture lexical variables. A closure observes and is permitted to update captured mutable bindings after the outer function returns. Functions support recursion, returned functions, and function values passed as arguments. Each invocation has an independent local scope. Runtime call errors and stack exhaustion return non-nil errors.

### Collections and builtins

`len` returns the UTF-8 byte length for strings and element count for arrays, maps, and bytes. `append(array, values...)` returns an array containing the original elements followed by the supplied values. `delete(map, key)` removes a key and returns `undefined`; deleting a missing key is harmless. `splice(array, start, deleteCount, items...)` mutates the input array and returns the removed elements. `range(stop)`, `range(start, stop)`, and `range(start, stop, step)` return integer arrays excluding `stop`; a zero step is invalid.

Conversions `string`, `int`, `float`, `bool`, `char`, `bytes`, and `time` accept the compatible scalar forms documented by their names and return an error object or `undefined` for unsupported values according to Tengo behavior. Type predicates and `type_name` report stable lowercase names such as `int`, `float`, `string`, `bool`, `char`, `bytes`, `array`, `map`, `immutable-array`, `immutable-map`, `time`, `error`, `function`, and `undefined`.

`immutable(value)` recursively returns an immutable array/map projection. Iteration and lookup remain available, but mutation of an immutable collection fails. `error(value)` creates an error object whose observable value is available through its `value` field/index. `is_error` recognizes error objects.

## Go Value and Object Conversion

`FromInterface` must accept nil, Tengo `Object` values, signed and unsigned Go integers within `int64`, floats, strings, booleans, runes, byte slices, `time.Time`, `[]interface{}`, `map[string]interface{}`, and compatible nested combinations. It returns an error for unsupported Go values or unsigned integers that overflow `int64`. Composite inputs are recursively converted. A byte-slice object retains the supplied byte-slice storage, while compiled-state cloning provides the execution-state isolation described below.

`ToInterface` converts Tengo scalars to `int64`, `float64`, `string`, `bool`, `rune`, `[]byte`, or `time.Time`; arrays and maps convert recursively; `undefined` converts to nil; error objects convert to Go errors. `ToString`, `ToInt`, `ToInt64`, `ToFloat64`, `ToBool`, `ToRune`, `ToByteSlice`, and `ToTime` return a value plus a success flag and implement the compatible conversions declared by their names. Failed conversions return the zero value and `false`.

`CountObjects` returns one for a scalar and one plus the recursive counts of array/map/immutable/error children for a compound object.

## Script and Compiled State

`NewScript` retains the supplied source. `Script.Add` converts and installs or replaces a named input; unsupported values return an error. `Remove` returns true only when a name existed. Added names are globals visible to compilation and execution.

`Compile` parses and compiles without executing. `Run` compiles then executes. `RunContext` does the same under a context. A syntax error, unresolved identifier, invalid assignment, invalid call, import failure, or configured limit violation returns a non-nil error and no successful result.

`Compiled.Run` supports repeated calls. `Set` changes an already-declared global and returns an error for an unknown name or unsupported Go value. `Get` always returns a `Variable`; an unknown name produces an undefined variable. `IsDefined` is false for unknown or undefined values. `GetAll` returns every known global without promising order.

`Clone` returns an independently mutable execution state sharing only immutable compiled instructions. Changing or running a clone must not change scalar globals, mutable collection contents, or later results in the original. `Compiled` serializes simultaneous calls on the same instance and supports concurrent runs of distinct clones.

`SetMaxConstObjects` rejects compilation whose constant object graph exceeds a nonnegative limit; a negative value disables the limit. `SetMaxAllocs` stops a run after it exceeds a nonnegative allocation budget; a negative value disables the limit.

`RunContext` must return promptly with a non-nil error when the context is already canceled or becomes canceled during a running loop. A canceled or failed run must not corrupt the compiled program; a clone or a later run with valid inputs remains usable.

## Modules

`ModuleMap` stores named `Importable` values. `Add`, `Remove`, `Get`, `GetBuiltinModule`, `GetSourceModule`, `Len`, `Copy`, and `AddMap` provide the documented map lifecycle. A copied map has independent membership, while contained immutable module objects are permitted to be shared.

`AddBuiltinModule` creates a module whose exported attributes are the supplied Tengo objects and are immutable to script code. `AddSourceModule` creates a module from Tengo source. Source modules export values using `export {name: value}` and support imports of other registered modules. Importing an unknown module, a cyclic source-module dependency, or invalid module source returns a non-nil compile error.

## State Model

A script transitions from source plus configured inputs/modules/limits to either a compile error or a reusable `Compiled` value. A compiled value contains a fixed program and mutable globals. Each run transitions from its starting globals to completed globals or an error. A clone begins with a deep-enough copy of globals that later execution state is independent.

Module-map membership is mutable before compilation. Compiled module results are part of that compiled program; later membership changes do not retroactively rewrite existing compiled instructions.

## Error Semantics

Ordinary syntax, name, type, call, index-assignment, import, conversion, limit, and cancellation failures return non-nil errors and must not panic. Exact diagnostic wording, source caret formatting, bytecode offsets, and stack-trace layout are not required.

`Eval` returns an error for an empty expression, statements used where an expression is required, the reserved name `__res__`, invalid parameters, compilation failure, runtime failure, or context cancellation. A Go `CallableFunc` error propagates as a run error. Error objects created inside the language remain values unless explicitly raised by a failing operation.

## Cross-View Invariants

- `Eval(ctx, expr, params)` must agree with running a script that assigns the same expression to a global and reading that global.
- `Variable.Value`, typed accessors, `Object`, and `ToInterface` must describe the same underlying value.
- `Compiled.Get`, `GetAll`, and `IsDefined` must agree on every known global after a successful run.
- A `Compiled.Set` followed by `Run` must affect dependent outputs while leaving the fixed program unchanged.
- Original and cloned compiled programs must remain independent after scalar and nested collection updates.
- Builtin and source module values must agree whether accessed directly from the module map or through a script import.
- A failed or canceled run must not make a later valid run or clone observe a successful partial result.

## Public Interface

The installable module and import path are `github.com/d5/tengo/v2`. The required root-package surface is:

```go
func Eval(context.Context, string, map[string]interface{}) (interface{}, error)
func NewScript([]byte) *Script
func (s *Script) Add(string, interface{}) error
func (s *Script) Remove(string) bool
func (s *Script) SetImports(ModuleGetter)
func (s *Script) SetMaxAllocs(int64)
func (s *Script) SetMaxConstObjects(int)
func (s *Script) Compile() (*Compiled, error)
func (s *Script) Run() (*Compiled, error)
func (s *Script) RunContext(context.Context) (*Compiled, error)

func (c *Compiled) Run() error
func (c *Compiled) RunContext(context.Context) error
func (c *Compiled) Clone() *Compiled
func (c *Compiled) IsDefined(string) bool
func (c *Compiled) Get(string) *Variable
func (c *Compiled) GetAll() []*Variable
func (c *Compiled) Set(string, interface{}) error

func NewVariable(string, interface{}) (*Variable, error)
func (v *Variable) Name() string
func (v *Variable) Value() interface{}
func (v *Variable) ValueType() string
func (v *Variable) Int() int
func (v *Variable) Int64() int64
func (v *Variable) Float() float64
func (v *Variable) Char() rune
func (v *Variable) Bool() bool
func (v *Variable) Array() []interface{}
func (v *Variable) Map() map[string]interface{}
func (v *Variable) String() string
func (v *Variable) Bytes() []byte
func (v *Variable) Error() error
func (v *Variable) Object() Object
func (v *Variable) IsUndefined() bool

type Importable interface { Import(string) (interface{}, error) }
type ModuleGetter interface { Get(string) Importable }
func NewModuleMap() *ModuleMap
func (m *ModuleMap) Add(string, Importable)
func (m *ModuleMap) AddBuiltinModule(string, map[string]Object)
func (m *ModuleMap) AddSourceModule(string, []byte)
func (m *ModuleMap) Remove(string)
func (m *ModuleMap) Get(string) Importable
func (m *ModuleMap) GetBuiltinModule(string) *BuiltinModule
func (m *ModuleMap) GetSourceModule(string) *SourceModule
func (m *ModuleMap) Copy() *ModuleMap
func (m *ModuleMap) Len() int
func (m *ModuleMap) AddMap(*ModuleMap)

type CallableFunc = func(args ...Object) (Object, error)
type SourceModule struct { Src []byte }
type BuiltinModule struct { Attrs map[string]Object }
type BuiltinFunction struct { ObjectImpl; Name string; Value CallableFunc }
type UserFunction struct { ObjectImpl; Name string; Value CallableFunc }

type Object interface {
    TypeName() string
    String() string
    BinaryOp(token.Token, Object) (Object, error)
    Copy() Object
    IsFalsy() bool
    Equals(Object) bool
    IndexGet(Object) (Object, error)
    IndexSet(Object, Object) error
    Iterate() Iterator
    CanIterate() bool
    Call(...Object) (Object, error)
    CanCall() bool
}

type Int struct { ObjectImpl; Value int64 }
type Float struct { ObjectImpl; Value float64 }
type String struct { ObjectImpl; Value string }
type Char struct { ObjectImpl; Value rune }
type Bytes struct { ObjectImpl; Value []byte }
type Array struct { ObjectImpl; Value []Object }
type Map struct { ObjectImpl; Value map[string]Object }
type ImmutableArray struct { ObjectImpl; Value []Object }
type ImmutableMap struct { ObjectImpl; Value map[string]Object }
type Time struct { ObjectImpl; Value time.Time }
type Error struct { ObjectImpl; Value Object }
type Undefined struct { ObjectImpl }

var TrueValue *Bool
var FalseValue *Bool
var UndefinedValue *Undefined

func FromInterface(interface{}) (Object, error)
func ToInterface(Object) interface{}
func ToString(Object) (string, bool)
func ToInt(Object) (int, bool)
func ToInt64(Object) (int64, bool)
func ToFloat64(Object) (float64, bool)
func ToBool(Object) (bool, bool)
func ToRune(Object) (rune, bool)
func ToByteSlice(Object) ([]byte, bool)
func ToTime(Object) (time.Time, bool)
func CountObjects(Object) int
```

The public `token.Token` parameter comes from `github.com/d5/tengo/v2/token`. Additional upstream-compatible declarations are permitted, but tests require only the root-package behavior and signatures listed above.

## Non-Goals

- Exact parser AST, bytecode, opcode values, instruction text, compiler traces, or source-position formatting.
- The `parser`, `stdlib`, `require`, `token` behavior beyond the token type needed by `Object`, or any command-line program.
- Local file imports, OS/environment access, random values, regular-expression details, JSON formatting, or network behavior.
- Exact performance, allocation counts below configured limits, tail-call optimization, or internal stack/frame layout.
- Compatibility with undocumented private fields, internal caches, or upstream test helpers.

## Environment

The submission must be a Go module with module path `github.com/d5/tengo/v2`. It must build and test on Linux with Go 1.26.6 without network access and without external module dependencies.

## Assessment Notes

Checks use only the declared public packages and compare Go values, errors, state transitions, module results, cancellation, clone isolation, and cross-view relationships. Collection-map ordering and exact diagnostic strings are not compared. Temporary contexts and in-memory modules are used; no external service or filesystem fixture is required.
