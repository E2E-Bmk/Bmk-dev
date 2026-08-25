<!-- INTERNAL
task_id: evalexpr-fullrepro-001
spec_version: v1
delta: initial version
source_boundary: README.md at v13.1.0 (operator table, builtin table, context
  semantics, value syntax, variable/function grammar, comments); docs.rs crate
  root docs (identical via cargo-sync-readme); src/lib.rs pub use surface;
  src/interface/mod.rs public functions; src/context/mod.rs context traits and
  context_map!/math_consts_context! macros; src/error/mod.rs variant names;
  behavior of edge cases confirmed by executing the pinned reference
  (92d99f4, tag v13.1.0)
-->

# Evalexpr Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`evalexpr` is an expression evaluator and tiny scripting language implemented
as a Rust library crate. It parses expression strings such as
`"a * 2 + min(4, b)"` into an operator tree, evaluates that tree against a
context holding variable and function bindings, and returns a typed value or a
typed error. Expressions support integer, float, string, boolean, tuple and
empty values, a fixed operator set with numeric precedences, variable reads and
writes, expression chaining, user-defined functions, and a builtin function
library.

The installable package name is `evalexpr`, and its Rust library crate is
imported as `evalexpr`. The crate exposes three cooperating groups of API: the
evaluation entry points (`eval` and its typed and context-taking variants),
the context types that hold bindings between evaluations, and the precompiled
operator tree (`Node`) that separates parsing from repeated evaluation. All
public value and error types are generic over a numeric type bundle; the
provided default bundle uses 64-bit signed integers and 64-bit floats.

## Non-Goals

- This specification does not require the optional `serde`, `regex`, or `rand`
  cargo features, the `str::regex_matches` and `str::regex_replace` builtin
  functions, or the `random` builtin function.
- This specification does not require a command-line binary; the crate is used
  as a library only.
- This specification does not require numeric type bundles other than the
  default one; the generic parameter must exist, but only the default bundle's
  behavior is specified.
- This specification does not require exact error-message text, `Display`
  formatting of error values, or `Debug` output of any public type.
- This specification does not require arbitrary-precision arithmetic; integer
  arithmetic is checked 64-bit arithmetic and float arithmetic is IEEE 754
  double precision.
- This specification does not define localization, I/O, networking, or any
  interaction with the process environment.

## Representative Workflows

### Workflow 1: Direct evaluation and typed shortcuts

```rust
use evalexpr::*;

fn main() -> EvalexprResult<()> {
    assert_eq!(eval("1 + 2 + 3"), Ok(Value::from_int(6)));
    assert_eq!(eval_int("1 + 2 + 3"), Ok(6));
    assert_eq!(eval("1.0 + 2 * 3"), Ok(Value::from_float(7.0)));
    assert_eq!(eval("true && 4 > 2"), Ok(Value::from(true)));
    // Type mismatches surface as typed errors:
    assert_eq!(
        eval_boolean("1 + 2"),
        Err(EvalexprError::ExpectedBoolean { actual: Value::Int(3) })
    );
    Ok(())
}
```

### Workflow 2: Scripts that assign into a persistent context

```rust
use evalexpr::*;

fn main() -> EvalexprResult<()> {
    let mut context = HashMapContext::<DefaultNumericTypes>::new();
    eval_empty_with_context_mut("hp = 1; max_hp = 5; heal = 3;", &mut context)?;
    // Assignments made by the script are visible through the context:
    assert_eq!(context.get_value("hp"), Some(&Value::from_int(1)));
    // The context feeds later evaluations:
    assert_eq!(
        eval_int_with_context_mut("hp = min(hp + heal, max_hp); hp", &mut context),
        Ok(4)
    );
    Ok(())
}
```

### Workflow 3: Precompile once, evaluate under changing bindings

```rust
use evalexpr::*;

fn main() -> EvalexprResult<()> {
    let precompiled = build_operator_tree::<DefaultNumericTypes>("a * b - c > 5")?;
    let mut context = context_map! {
        "a" => int 6,
        "b" => int 2,
        "c" => int 3,
    }?;
    assert_eq!(precompiled.eval_with_context(&context), Ok(Value::from(true)));
    context.set_value("c".into(), Value::from_int(8))?;
    assert_eq!(precompiled.eval_with_context(&context), Ok(Value::from(false)));
    assert_eq!(precompiled.eval_boolean_with_context(&context), Ok(false));
    Ok(())
}
```

## Expression Syntax and Literals

This section defines what the tokenizer and parser must accept, because every
other behavior is defined over the resulting tree.

**Integer literals.** Decimal digit sequences lex as integer values. Radix
prefixes are supported: `0x` followed by hexadecimal digits, `0b` followed by
binary digits, and `0o` followed by octal digits (for example `0xFF`, `0b0101`
and `0o377` all evaluate to the integer 255, and a leading `-` negates them).
When a radix prefix is not followed by valid digits of that radix (such as
`0x`, `0b2` or `0o8`), the token is not an integer literal: it lexes as an
identifier, and evaluating it must return
`EvalexprError::VariableIdentifierNotFound` carrying that token text.

**Float literals.** A numeric token containing a decimal point or an exponent
lexes as a float: `3.`, `.35`, `1.00`, `23e4`, `-2e-3`, `3.54e+2` and `1e0`
are all floats. A token with an exponent is a float even without a decimal
point, so `10e3` evaluates to the float 10000.0 and `10e-3` to 0.01.

**String literals.** Strings are delimited by double quotes. The escape
sequences `\"` (double quote) and `\\` (backslash) must be supported inside
string literals. If a string contains any other escape sequence, evaluation
must return `EvalexprError::IllegalEscapeSequence` carrying the offending
sequence as written. If a string literal is opened but the closing double
quote is missing, evaluation must return `EvalexprError::UnmatchedDoubleQuote`.

**Boolean literals and identifiers.** `true` and `false` lex as boolean
values. Any other bare word lexes as an identifier; whether an identifier is a
variable read, a variable write, or a function call is determined by its
syntactic position (a write when it is the left side of an assignment, a
function call when it is directly followed by an argument expression, a
variable read otherwise). Evaluating a variable read that no binding resolves
must return `EvalexprError::VariableIdentifierNotFound` carrying the
identifier.

**Whitespace and comments.** Whitespace separates tokens and is otherwise
insignificant; expressions spanning multiple lines are valid. End-of-line
comments start with `//` and run to the end of the line. Inline comments are
delimited by `/*` and `*/` and are permitted between any two tokens. When an inline
comment is opened and never closed, evaluation must return an error (the
`EvalexprError::CustomMessage` variant).

**Parentheses.** Parentheses group subexpressions and construct tuples (see
the aggregation operator). `()` is the empty value literal. A parenthesized
group directly adjacent to a value literal (such as `123(1*2)` or `1()`) is
not a call; evaluating it must return
`EvalexprError::MissingOperatorOutsideOfBrace`. An unmatched `(` must produce
`EvalexprError::UnmatchedLBrace` and an unmatched `)` must produce
`EvalexprError::UnmatchedRBrace`.

**Partial operator tokens.** A character that only begins a multi-character
operator (for example a single `&` or a single `|`) is a partial token; when
it cannot be completed, evaluation must return
`EvalexprError::UnmatchedPartialToken`, which carries the partial token and
the optional following token that failed to complete it.

## Operators and Type Rules

This section defines the operator set, the precedence order that drives tree
construction, and the numeric typing rules that decide whether a result is an
integer or a float.

**Binary operators and precedence.** Higher precedence binds first. The
operators and their precedences are: `^` exponentiation (120); `*` product,
`/` division, `%` modulo (100); `+` sum or string concatenation, `-`
difference (95); `<`, `>`, `<=`, `>=`, `==`, `!=` comparisons (80); `&&`
logical and (75); `||` logical or (70); `=` assignment and the
operator-assignments `+=`, `-=`, `*=`, `/=`, `%=`, `^=`, `&&=`, `||=` (50);
`,` aggregation (40); `;` expression chaining (0). Variables and values have
precedence 200 and function literals 190. Operators of equal precedence
evaluate left to right, so `3.0 - 3.0 - 3.0 - 3.0` equals -6.0 and
`3.0 / 3.0 / 3.0 / 3.0` equals `((3.0/3.0)/3.0)/3.0`.

**Unary operators.** `-` negation and `!` logical not have precedence 110. A
chain of negations is permitted (`----3` evaluates to 3). `!` requires a
boolean operand and must return `EvalexprError::ExpectedBoolean` otherwise;
`-` requires a numeric operand and must return
`EvalexprError::ExpectedNumber` otherwise.

**Integer/float typing.** When both operands of `+`, `-`, `*`, `/` or `%` are
integers, the operation is integer arithmetic and returns an integer; `1 / 2`
evaluates to the integer 0 and `1 % 4` to 1. When at least one operand is a
float, the other operand is converted and the result is a float; `1.0 / 2`
evaluates to 0.5. Exponentiation `^` always converts both operands and
returns a float; `2^2` evaluates to the float 4.0, and `2^0.5` to the square
root of 2. Integer arithmetic is checked: overflow of addition, subtraction,
multiplication or negation, integer division by zero, and integer modulo by
zero must return an error rather than wrapping or panicking.

**Sum and concatenation.** When both operands of `+` are strings, `+`
concatenates them. When one operand of `+` is neither a number nor a string,
the operation must return `EvalexprError::ExpectedNumberOrString` carrying
that operand. Mixing a string and a number in `+` must return a type error
(the `EvalexprError::WrongTypeCombination` variant).

**Comparisons.** The ordering comparisons `<`, `>`, `<=`, `>=` accept two
numbers, including one integer and one float (`1 < 2.0` is true, `1 >= 2.0`
is false); a non-numeric operand must produce an error. `==` and `!=` accept
any two values and never produce a type error: values of different types
compare unequal, and an integer never equals a float (`1 == 1.0` is false).

**Boolean operators.** `&&` and `||` require boolean operands and must return
`EvalexprError::ExpectedBoolean` carrying the offending value otherwise.

**Aggregation.** The `,` operator aggregates values into a tuple. It is
n-ary: `1, 2, 3` is one three-element tuple, not nested pairs. Parentheses
create nested tuples: `1, 2, (true, "b")` is a three-element tuple whose last
element is a two-element tuple. A tuple holds values of mixed types.

## Assignment, Chaining, and Scripts

This section defines how expressions write to a context and how multiple
statements combine, because these two features together make expressions into
small scripts.

**Assignment.** `identifier = expression` stores the expression's value under
the identifier in the context and itself evaluates to the empty value. When
the target expression of an assignment is not an identifier, tree
construction fails. When an assignment is evaluated against an immutable
context entry point (`eval_with_context` and the typed variants without
`_mut`), the evaluation must return `EvalexprError::ContextNotMutable`.

**Operator-assignments.** For every binary operator there is an assignment
form: `a += 2` is equivalent to `a = a + 2`, and likewise for `-=`, `*=`,
`/=`, `%=`, `^=`, `&&=`, `||=`. The identifier must already hold a value (a
read of an unset identifier fails with
`EvalexprError::VariableIdentifierNotFound`), and the combined operation
follows the same typing rules as the underlying operator, including the
`HashMapContext` type-safety rule below (so `a ^= 5` on an integer `a` fails,
because `^` produces a float).

**Expression chaining.** `;` chains expressions and evaluates to the value of
the last expression in the chain: `1;2;3;4` evaluates to 4. When the chain
ends with a trailing `;`, the whole expression evaluates to the empty value:
`1;2;3;4;` is empty. Assignments earlier in a chain are visible to later
expressions in the same chain.

**Implicit context.** The context-free entry points (`eval` and the typed
variants without `_with_context`) evaluate against a fresh temporary mutable
context. Assignments therefore succeed inside a single call —
`eval("a = 2 + 4 * 2; b = -5 + 3 * 5; a == b")` evaluates to true — but the
temporary context is discarded, so a following call `eval("a")` must return
`EvalexprError::VariableIdentifierNotFound`.

## Contexts and Bindings

This section defines the context types and traits, because contexts are the
single state store connecting evaluations, code-side bindings, and builtin
function availability.

**Context traits.** Read access is defined by the `Context` trait: it
provides `get_value` returning an optional reference to the value bound to a
name, `call_function` for invoking a bound function by name, and the builtin
switch accessors described below. Write access is split into
`ContextWithMutableVariables`, providing `set_value` taking an owned name and
value, and `ContextWithMutableFunctions`, providing `set_function` taking an
owned name and a `Function`. Variable iteration is defined by
`IterateVariablesContext`, providing `iter_variables` yielding owned
name/value pairs and `iter_variable_names` yielding owned names.

**HashMapContext.** `HashMapContext` is the general-purpose map-backed
context; `HashMapContext::new` creates an empty one, and the type implements
`Clone`, `Default`, and all four traits above. Beyond the traits it provides
`remove_value`, which removes a variable binding and returns the previously
bound value (or nothing when the name was unbound), and three erasure
methods: `clear` removes all variables and functions, `clear_variables`
removes only variables, and `clear_functions` removes only functions.

**Type safety.** `HashMapContext` is type safe: once a name holds a value of
one type, `set_value` (whether called from code or through an assignment
expression) must reject a value of a different type with the `Expected…`
error matching the currently stored type, carrying the rejected value as
`actual`. Rebinding with a value of the same type overwrites. Removing the
binding removes the type constraint with it.

**Builtin function switch.** Contexts expose
`set_builtin_functions_disabled`, taking a boolean, and
`are_builtin_functions_disabled` returning one. On `HashMapContext` builtin
functions start enabled and the switch is freely settable. `EmptyContext` is
a context with no bindings and builtin functions permanently disabled:
calling `set_builtin_functions_disabled(false)` on it must return
`EvalexprError::BuiltinFunctionsCannotBeEnabled`, and every function call
against it must return `EvalexprError::FunctionIdentifierNotFound`.
`EmptyContextWithBuiltinFunctions` has builtin functions permanently enabled:
`set_builtin_functions_disabled(true)` must return
`EvalexprError::BuiltinFunctionsCannotBeDisabled`. Both empty context types
implement `Default`, return no value for any `get_value` call, and iterate
zero variables. When builtin functions are disabled on a context, calling a
builtin by name must return `EvalexprError::FunctionIdentifierNotFound`
carrying the name; user-defined functions bound in the context must keep
resolving regardless of the switch.

**The context_map! macro.** The `context_map!` macro builds a
`HashMapContext` from `"name" => entry` pairs and returns it inside a
`Result` (an error surfaces if any insertion fails, for example a type-safety
violation between duplicate keys). Three entry forms exist: `"k" => int expr`
and `"k" => float expr` insert integer and float variables;
`"k" => Function::new(...)` inserts a function; and a bare `"k" => expr`
inserts any value convertible into a `Value`.

**The math_consts_context! macro.** The `math_consts_context!` macro builds a
`HashMapContext` whose variables are float mathematical constants. Called
with no arguments it binds the standard `f64` constants under their Rust
names (`PI`, `TAU`, `E`, `SQRT_2`, `LN_2`, `LN_10`, `LOG2_E`, `LOG10_E` and
the other `core::f64::consts` names); called with a list of constant names it
binds exactly those.

## Functions: Builtin and User-Defined

This section defines function call syntax and the two function sources,
because function resolution is where the tokenizer, the context, and the
builtin library meet.

**Call syntax.** A function is called by juxtaposition: an identifier
directly followed by an argument expression is a call, with or without
parentheses, so `f 5`, `f(5)`, `f five` and `f(five)` are all calls. Function
application has precedence 190, directly below values. Multiple arguments are
passed as one tuple argument: `avg(2, 4)` passes the tuple `(2, 4)`. Chained
juxtaposition applies right to left: `a b 4` calls `b` with 4 and then `a`
with the result. A value followed by a value (such as `5 b`, `12 3`, or a
call followed by a value) is not a valid call and must fail to evaluate.

**Function resolution.** When a call names a function bound in the context,
the bound function is invoked. When the name is not bound and builtin
functions are enabled, the builtin with that name is invoked. When neither
resolves, evaluation must return `EvalexprError::FunctionIdentifierNotFound`
carrying the name. A user-defined function whose name shadows a builtin wins
over the builtin.

**User-defined functions.** A `Function` wraps a closure that receives a
reference to the evaluated argument value and returns a `Result` of value or
error. `Function::new` constructs one from such a closure. The closure
receives the single argument value; a call with an argument list receives the
tuple of arguments and inspects it itself (for example through `as_tuple` or
`as_fixed_len_tuple`). Errors returned by the closure propagate to the
evaluation result unchanged. `Function` values are set into a context with
`set_function` or the `context_map!` macro, and a cloned context invokes the
same functions as the original.

**Builtin functions.** The following builtins must exist with these
signatures and semantics (argument counts are enforced; a wrong argument
count or type must produce an error):

| Identifier | Arguments | Semantics |
|---|---|---|
| `min` | one or more numbers | smallest argument; integer if all arguments are integers, float otherwise |
| `max` | one or more numbers | largest argument; integer if all arguments are integers, float otherwise |
| `len` | one string or tuple | character length of the string, or number of elements of the tuple (integer) |
| `floor` | one number | largest integer value less than or equal to the argument, as a float |
| `round` | one number | nearest integer value, half-way cases away from zero, as a float |
| `ceil` | one number | smallest integer value greater than or equal to the argument, as a float |
| `if` | boolean, any, any | second argument when the boolean is true, third otherwise; exactly three arguments |
| `contains` | tuple, non-tuple value | true when the value occurs in the tuple |
| `contains_any` | tuple, tuple of non-tuple values | true when any value of the second tuple occurs in the first |
| `typeof` | any | the strings `"string"`, `"float"`, `"int"`, `"boolean"`, `"tuple"`, or `"empty"` |
| `math::is_nan`, `math::is_finite`, `math::is_infinite`, `math::is_normal` | one number | float classification predicates returning booleans |
| `math::ln`, `math::log2`, `math::log10` | one number | natural, base-2, base-10 logarithm (float) |
| `math::log` | two numbers | logarithm of the first argument with the base given by the second (float) |
| `math::exp`, `math::exp2` | one number | e or 2 raised to the argument (float) |
| `math::pow` | two numbers | first argument raised to the second (float) |
| `math::cos`, `math::sin`, `math::tan` | one number | trigonometric functions in radians (float) |
| `math::acos`, `math::asin`, `math::atan` | one number | inverse trigonometric functions (float) |
| `math::atan2` | two numbers | four-quadrant arctangent (float) |
| `math::cosh`, `math::sinh`, `math::tanh`, `math::acosh`, `math::asinh`, `math::atanh` | one number | hyperbolic and inverse hyperbolic functions (float) |
| `math::sqrt`, `math::cbrt` | one number | square and cube root (float) |
| `math::hypot` | two numbers | length of the hypotenuse of the right triangle with the two legs (float) |
| `math::abs` | one number | absolute value; integer for an integer argument, float for a float argument |
| `str::to_lowercase`, `str::to_uppercase`, `str::trim` | one string | case-mapped or whitespace-trimmed copy |
| `str::from` | any | the argument rendered as a string |
| `str::substring` | string, int, int | substring from the first index (inclusive) to the second (exclusive) |
| `bitand`, `bitor`, `bitxor` | two integers | bitwise and, or, xor |
| `bitnot` | one integer | bitwise not |
| `shl`, `shr` | two integers | left and right shift of the first argument by the second |

`if` with fewer or more than three arguments, or with a non-boolean first
argument, must return an error rather than picking a branch.

## Precompiled Expressions and Tree Introspection

This section defines the operator tree, because precompilation and
introspection are projections of the same parse result that direct evaluation
uses.

**Construction.** `build_operator_tree` parses an expression string and
returns a `Node` (or the same parse errors that direct evaluation would
produce). A `Node` owns its children and an `Operator` describing what it
computes; the tree returned by `build_operator_tree` is wrapped in a root
node whose operator is `Operator::RootNode` and which evaluates to the value
of its last child. `children` returns the child slice, `children_mut` a
mutable child vector reference, `operator` the node's operator, and
`operator_mut` a mutable reference to it. Manually growing a tree through
mutable access follows the same rule as parsing: a node whose operator takes
no children (a value or identifier leaf) rejects appended children with
`EvalexprError::AppendedToLeafNode`.

**Evaluation family.** A `Node` provides the full evaluation family mirroring
the free functions: `eval` (fresh temporary context), `eval_with_context`,
`eval_with_context_mut`, and for every result type T in int, float, number,
string, boolean, tuple, empty the shortcuts `eval_int`, `eval_int_with_context`,
`eval_int_with_context_mut` and so on. Every family member must agree with
re-parsing and evaluating the same string through the corresponding free
function, and the typed members apply the same `Expected…` conversion errors.

**Identifier iteration.** A `Node` reports the identifiers appearing in its
subtree in source order through five iterators: `iter_identifiers` yields
every variable and function identifier; `iter_variable_identifiers` yields
only variable identifiers (reads and writes); `iter_read_variable_identifiers`
yields identifiers read by the expression; `iter_write_variable_identifiers`
yields identifiers written by assignments; `iter_function_identifiers` yields
function call names. Each identifier occurrence is yielded as a string slice.
`iter` traverses the nodes of the tree itself.

## Values, Types, and Conversions

This section defines the value model shared by every projection.

**The Value enum.** `Value` has six variants: `String` holding an owned
string, `Float` holding a float, `Int` holding an integer, `Boolean` holding
a bool, `Tuple` holding a vector of values (the `TupleType` alias), and
`Empty` holding nothing (the `EmptyType` alias is the unit type, and the
`EMPTY_VALUE` constant is the unit value). Equality between `Value`s is
structural per variant, and values of different variants are unequal.

**Construction.** `Value::from_int` and `Value::from_float` build numeric
values. `Value` conversions exist from string slices, owned strings, bools,
tuples (vectors of values) and the unit type through the standard `From`
trait, so `"def".into()` is a string value and `().into()` is empty.

**Inspection and typed extraction.** For each variant there is an extraction
method returning a `Result`: `as_string`, `as_float`, `as_int`, `as_boolean`,
`as_tuple`, `as_empty`, plus `as_number`, which accepts an int or a float and
returns a float, and `as_fixed_len_tuple`, which takes a length and accepts
only a tuple of exactly that length. On mismatch these return the matching
`Expected…` error carrying the actual value: `as_int` on a float returns
`ExpectedInt`, `as_number` on a boolean returns `ExpectedNumber`,
`as_fixed_len_tuple(3)` on a two-element tuple returns
`ExpectedFixedLengthTuple` carrying the expected length and the actual value.
The standard `TryFrom<Value>` conversions exist for owned strings, ints,
floats, bools, tuples and unit, returning the same errors as the matching
`as_…` methods.

**ValueType.** `ValueType` is the value-kind enum with variants `String`,
`Float`, `Int`, `Boolean`, `Tuple`, `Empty`; a `ValueType` is obtained from a
`&Value` through `From`, and equal kinds compare equal regardless of payload.

**Numeric type bundle.** The public types are generic over a bundle
implementing `EvalexprNumericTypes`, which defines the associated types `Int`
and `Float` and conversion/arithmetic hooks through the `EvalexprInt` and
`EvalexprFloat` traits. The provided `DefaultNumericTypes` bundle sets `Int`
to `i64` and `Float` to `f64` and is the default generic argument everywhere,
so `Value::<DefaultNumericTypes>::Int(4)` and plain `Value::Int(4)` are the
same type.

## State Model

The system maintains two kinds of state. The first is the operator tree
produced by parsing an expression string; it is immutable under evaluation
and is observable through three projections that must agree: evaluation
results (the whole `eval` family), identifier iteration (the five
`iter_…identifiers` iterators), and structural access (`children`,
`operator`). The second is the binding state held by a context: a map from
names to values, a map from names to functions, and the builtin-enablement
switch. Context state is observable through `get_value`, `iter_variables`,
`iter_variable_names`, and through the outcome of evaluations that read
variables or call functions. Evaluation with a mutable context is the only
operation that transfers state from an expression into a context; code-side
`set_value`/`set_function`/`remove_value`/`clear…` calls modify it directly.
A `HashMapContext` clone is an independent copy: mutations of the original
after cloning must not be visible through the clone.

## Error Semantics

Every fallible operation returns the crate's error enum; the required
conditions and variants are:

| Condition | Required error variant |
|---|---|
| Read of an unbound variable | `VariableIdentifierNotFound` (carries the name) |
| Call of an unresolvable function; builtin call with builtins disabled | `FunctionIdentifierNotFound` (carries the name) |
| Typed extraction/shortcut on a value of the wrong variant | `ExpectedString`, `ExpectedInt`, `ExpectedFloat`, `ExpectedBoolean`, `ExpectedTuple`, `ExpectedEmpty` (each carries `actual`) |
| Numeric extraction on a non-number | `ExpectedNumber` (carries `actual`) |
| `+` operand neither number nor string | `ExpectedNumberOrString` (carries `actual`) |
| Fixed-length tuple extraction with wrong length | `ExpectedFixedLengthTuple` (carries `expected_length` and `actual`) |
| Assignment through an immutable-context entry point | `ContextNotMutable` |
| Enabling builtins on `EmptyContext` | `BuiltinFunctionsCannotBeEnabled` |
| Disabling builtins on `EmptyContextWithBuiltinFunctions` | `BuiltinFunctionsCannotBeDisabled` |
| Unmatched `(`, `)`, or `"` | `UnmatchedLBrace`, `UnmatchedRBrace`, `UnmatchedDoubleQuote` |
| Incompletable partial operator token | `UnmatchedPartialToken` |
| Value adjacent to a braced group without an operator | `MissingOperatorOutsideOfBrace` |
| Illegal string escape sequence | `IllegalEscapeSequence` (carries the sequence) |
| Child appended to a leaf node | `AppendedToLeafNode` |
| Operator applied to mismatched operand type pair | `WrongTypeCombination` (carries the operator and the actual types) |
| Operator constructed with wrong operand count | `WrongOperatorArgumentAmount` |
| Function called with wrong argument count | `WrongFunctionArgumentAmount` |
| Unclosed inline comment and other tokenizer-internal failures | `CustomMessage` |
| Integer overflow, integer division by zero, integer modulo by zero | an error (variant carrying the operation) |

For every `Expected…` variant there is a snake_case constructor helper on the
error enum taking the actual value (`expected_int`, `expected_number`,
`expected_string`, `expected_boolean`, `expected_tuple`, `expected_empty`,
`expected_float`, and `expected_fixed_len_tuple` taking the length first);
`type_error` constructs a `TypeError` from an actual value and the list of
expected `ValueType`s, and `wrong_type_combination` constructs
`WrongTypeCombination` from an operator and the operand types. Exact error
message strings are not part of the contract.

## Cross-View Invariants

1. For any expression string and context, `eval_with_context` and
   `build_operator_tree` followed by `Node::eval_with_context` on the same
   context must produce equal results, including equal error variants; the
   typed shortcut of each entry point must equal the untyped result converted
   through the matching `as_…` extraction.
2. After `eval_with_context_mut` evaluates an assignment successfully, the
   assigned value must be returned by `Context::get_value` under the assigned
   name, must appear in `iter_variables`/`iter_variable_names`, and must be
   readable by a subsequent evaluation against the same context.
3. Re-evaluating one precompiled `Node` against a context whose variable was
   changed through `set_value` must reflect the new binding, and the typed
   and untyped `Node` evaluation families must agree with each other on every
   evaluation.
4. Every identifier yielded by `iter_read_variable_identifiers` of a tree
   must either be bound in the context at evaluation time or cause the whole
   evaluation to return `VariableIdentifierNotFound`; identifiers yielded by
   `iter_write_variable_identifiers` are exactly those the evaluation would
   assign. `iter_variable_identifiers` yields exactly the union of reads and
   writes in source order, and `iter_identifiers` additionally includes
   function names in source order.
5. Disabling builtin functions on a context must flip function resolution
   observed through evaluation — a builtin name stops resolving with
   `FunctionIdentifierNotFound` — while `get_value`, bound user functions,
   and variable bindings observed through the same context are unaffected;
   re-enabling restores the builtin.
6. A `HashMapContext` clone must evaluate every expression to the same result
   as the original at the moment of cloning: same variable reads, same
   user-function results, same builtin switch state.

## Public Interface

### Import Surface

```rust
// crate root re-exports
use evalexpr::{
    // evaluation entry points
    eval, eval_string, eval_int, eval_float, eval_number, eval_boolean,
    eval_tuple, eval_empty,
    eval_with_context, eval_string_with_context, eval_int_with_context,
    eval_float_with_context, eval_number_with_context,
    eval_boolean_with_context, eval_tuple_with_context,
    eval_empty_with_context,
    eval_with_context_mut, eval_string_with_context_mut,
    eval_int_with_context_mut, eval_float_with_context_mut,
    eval_number_with_context_mut, eval_boolean_with_context_mut,
    eval_tuple_with_context_mut, eval_empty_with_context_mut,
    build_operator_tree,
    // values and types
    Value, ValueType, TupleType, EmptyType, EMPTY_VALUE,
    // tree
    Node, Operator,
    // contexts
    Context, ContextWithMutableVariables, ContextWithMutableFunctions,
    IterateVariablesContext, HashMapContext, EmptyContext,
    EmptyContextWithBuiltinFunctions,
    // functions
    Function,
    // numeric type bundle
    DefaultNumericTypes, EvalexprNumericTypes, EvalexprInt, EvalexprFloat,
    // errors
    EvalexprError, EvalexprResult,
    // tokens
    PartialToken,
};
// the error module is also reachable as a module path
use evalexpr::error::*;
```

The macros `context_map!` and `math_consts_context!` are exported at the
crate root. The glob import `use evalexpr::*;` must provide all names above.

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `eval` (+ 7 typed variants) | function | Parse and evaluate a string against a fresh temporary context |
| `eval_with_context` (+ 7 typed variants) | function | Parse and evaluate against an immutable context reference |
| `eval_with_context_mut` (+ 7 typed variants) | function | Parse and evaluate against a mutable context reference |
| `build_operator_tree` | function | Parse a string into a reusable operator tree |
| `Value` | enum | Evaluation result: String, Float, Int, Boolean, Tuple, Empty |
| `ValueType` | enum | Kind of a `Value` without payload |
| `TupleType` | type alias | Vector of values backing `Value::Tuple` |
| `EmptyType` | type alias | Unit type backing `Value::Empty` |
| `EMPTY_VALUE` | constant | The unit value of `EmptyType` |
| `Node` | struct | Precompiled operator tree with evaluation and iteration families |
| `Operator` | enum | The operation computed by one tree node (includes `RootNode`) |
| `Context` | trait | Read access to bindings and the builtin switch |
| `ContextWithMutableVariables` | trait | `set_value` write access |
| `ContextWithMutableFunctions` | trait | `set_function` write access |
| `IterateVariablesContext` | trait | Variable iteration access |
| `HashMapContext` | struct | Map-backed type-safe context with erasure methods |
| `EmptyContext` | struct | Bindingless context, builtins permanently disabled |
| `EmptyContextWithBuiltinFunctions` | struct | Bindingless context, builtins permanently enabled |
| `Function` | struct | User-defined function wrapping a closure |
| `DefaultNumericTypes` | struct | Default numeric bundle: i64 integers, f64 floats |
| `EvalexprNumericTypes` | trait | Numeric bundle contract (associated Int and Float) |
| `EvalexprInt`, `EvalexprFloat` | traits | Behavior required of bundle integer and float types |
| `EvalexprError` | enum | Error taxonomy of parsing, typing, and evaluation |
| `EvalexprResult` | type alias | Result specialized to `EvalexprError` |
| `PartialToken` | enum | Incomplete operator token reported by tokenizer errors |
| `context_map!` | macro | Build a `HashMapContext` from `name => entry` pairs |
| `math_consts_context!` | macro | Build a `HashMapContext` of float math constants |

### CLI Entry Points

There is no console entry point in this deliverable. Programmatic use is
through the Rust library API only.

## Appendix A: Environment

The working environment runs Rust stable (1.83 or newer, edition 2021) with
Cargo on Linux. The deliverable is one Cargo package named `evalexpr` whose
library crate is imported as `evalexpr`, with its packaging metadata in
`Cargo.toml` at the project root so the crate builds and resolves through a
patched crates.io registry. The core feature set must build with no required
dependencies; the optional `serde`, `regex`, and `rand` features and their
dependencies are not exercised. Test execution uses Cargo metadata and
`cargo-nextest`.

## Appendix B: Assessment Notes

The assessment compiles Rust tests against the public API listed in the
Public Interface section and asserts the behaviors stated in this
specification: literal and operator semantics with exact result values and
result types, the error variant produced by each failure condition, context
state observed through `get_value` and the iteration methods after script
evaluation, agreement between direct evaluation, typed shortcuts, and
precompiled tree evaluation, identifier iteration order, and the builtin
function library's results. Tests assert produced values, variants, and state
transitions; they do not assert error message text, `Debug`/`Display`
formatting beyond values stated here, or any private structure. Behavior is
asserted through the public API in all cases.
