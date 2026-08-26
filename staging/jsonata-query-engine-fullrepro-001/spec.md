# jsonata Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`jsonata` is a query-and-transformation language engine for JSON. A source string compiles through the package's default export into an expression object; evaluating that expression against any JSON input navigates the structure with location paths, filters it with predicates, reshapes it with array/object constructors, grouping, sorting, and transform rules, and computes derived values through an operator algebra and a built-in function library covering strings, numbers, aggregation, arrays, objects, higher-order functions, regular expressions, and date-time conversion.

The engine has two cooperating layers over one compiled artifact: a parser that turns source text into an abstract syntax tree (exposed through `ast()`) and reports structured syntax errors, and an evaluator that walks that tree asynchronously under JSONata sequence semantics — where every intermediate result is a sequence, a one-item sequence is indistinguishable from the item itself, and an empty sequence is the absence of a result. Host programs extend the static environment with named values and functions before evaluation, and supply per-call bindings at evaluation time.

The installable package name is `jsonata`. All functionality is reachable through the package's default export.

## Non-Goals

- This specification does not require the parser's error-recovery mode (`recover` option) or pluggable regex engines; compilation options are not exercised.
- This specification does not require evaluation resource limits (timeouts, stack depth, or sequence-size caps).
- This specification does not require the callback form of `evaluate`; the promise form is the contract.
- This specification does not require remote or URL-based evaluation, file access, or any network behavior.
- This specification does not require the full date-time picture-string matrix; only the picture components described in Date And Time are required.
- This specification does not define a command-line interface.

## Representative Workflows

**Query a document with paths, predicates, and aggregation.** An expression compiles once and evaluates against any input; results follow sequence semantics:

```ts
import jsonata from "jsonata";

const data = {
  Account: {
    Order: [
      { OrderID: "o1", Product: [{ Name: "p1", Price: 10, Qty: 2 }, { Name: "p2", Price: 5, Qty: 1 }] },
      { OrderID: "o2", Product: [{ Name: "p3", Price: 100, Qty: 1 }] },
    ],
  },
};

const expr = jsonata("Account.Order.Product[Price > 8].Name");
await expr.evaluate(data);            // ["p1", "p3"]
await jsonata("$sum(Account.Order.Product.(Price * Qty))").evaluate(data); // 125
```

**Extend the environment and transform.** Host values and functions join the expression's environment; object constructors and grouping reshape the result:

```ts
const expr = jsonata("Account.Order.Product{ Name: Price * $rate }");
expr.assign("rate", 2);
await expr.evaluate(data);            // { p1: 20, p2: 10, p3: 200 }

const twice = jsonata("$twice(21)");
twice.registerFunction("twice", (n) => n * 2, "<n:n>");
await twice.evaluate({});             // 42
```

## Expression Compilation And Errors

Everything starts with the default export: calling `jsonata(source)` parses the source string and returns an expression object with `evaluate`, `assign`, `registerFunction`, and `ast` methods.

**Compilation.** WHEN the source is grammatical, THEN `jsonata(source)` returns the compiled expression without evaluating anything. WHEN the source is malformed, THEN `jsonata(source)` must throw an error value exposing a string `code` (an `S`-prefixed syntax code), a numeric `position` locating the offending character, and the offending `token`. Representative codes: an unclosed parenthesis reports `S0203` with token `"(end)"`; a path ending in a dangling dot reports `S0207`; `===` reports `S0211` on the stray `=`; there is no `**` power operator or `^` infix operator — both are syntax errors (`^` opens an order-by clause only after a path).

**Evaluation.** `evaluate(input, bindings?)` returns a promise. WHEN evaluation succeeds, THEN the promise resolves with the result value; an expression that selects nothing resolves with `undefined` (not `null`). WHEN evaluation fails, THEN the promise rejects with an error value exposing a string `code` (`T`- or `D`-prefixed), a numeric `position`, and the offending `token`. Thrown compile-time and rejected run-time error values expose these fields directly; error message wording is not part of this contract. The same compiled expression is reusable: repeated `evaluate` calls against different inputs are independent.

**AST.** `ast()` returns the parsed tree. A two-step path such as `Account.Name` reports type `"path"` with a `steps` array of `{ type: "name", value, position }` entries; a binary expression such as `1 + 2` reports type `"binary"` with `value` `"+"` and `lhs`/`rhs` operand nodes carrying their literal `type` and `value`.

## Path Navigation And Sequences

Location paths walk JSON structure left to right; every stage produces a sequence and the sequence rules decide the observable shape.

**Sequence rules.** A result sequence containing exactly one item is returned as that item; an empty sequence is returned as `undefined`; a sequence with several items is returned as an array. Navigating a step over an array maps the step over every element and flattens one level, so `Account.Order.Product.Name` over nested arrays yields one flat array of names. WHERE a step or a whole path carries an `[]` suffix, THEN the result stays an array even with zero or one item.

**Steps and context.** A name step selects that field of the context object. `$` denotes the current context (at the start of a path, the whole input) and `$$` always denotes the root input. Parenthesized step expressions map over the context sequence: `[1,2,3].($ * 2)` returns `[2,4,6]`, and `Product.(Price * Qty)` computes one value per product. The parent operator `%` inside a step refers to the enclosing object one path level up, so `Account.Order.Product.{ "p": Name, "order": %.OrderID }` pairs each product with its order's id. A step followed by `#$var` binds each item's zero-based position to `$var` for the rest of the path; an expression followed by `@$var` binds the context item itself.

**Predicates and indexes.** A bracketed expression after a step filters: WHEN the expression is numeric, THEN it selects by position — zero-based, with negative indexes counting from the end — and WHEN it is any other expression, THEN it keeps the items for which the effective boolean value is true. A filter that keeps one item returns the bare item, and a filter that keeps none returns `undefined`.

**Wildcards.** `*` selects all field values of the context object. `**` selects all values at any depth (descendant traversal), so `**.Price` collects every `Price` anywhere in the input.

## Operators

The operator algebra is total over defined operands and reports type errors through structured codes; an operand that is `undefined` makes the whole operation return `undefined` rather than fail.

**Arithmetic.** `+`, `-`, `*`, `/`, `%` operate on numbers, with unary minus; `(5 + 3 * 2 - 1) / 2` follows conventional precedence. If an operand is defined but not a number, then evaluation must reject with code `T2001` at the operator. Exponentiation is spelled `$power`, not an operator.

**Comparison.** `<`, `<=`, `>`, `>=` compare two numbers or two strings; if the operand types differ or are not comparable, then evaluation must reject with `T2009`. `=` and `!=` are deep structural equality over any JSON values — `[1,2] = [1,2]` and `{"a":1} = {"a":1}` are true — and never raise on mixed types (`"a" = 1` is `false`). `in` tests membership of a value in an array (a non-array right side is treated as a one-element sequence); it does not test substring containment, and it matches by primitive value only — an array or object left side never matches a structurally equal member (`[1,2] in [[1,2]]` is `false`).

**Ranges and strings.** `[a..b]` inside an array constructor expands to the inclusive integer sequence and composes with other items (`[1..3, 7..8]`); WHEN the lower bound exceeds the upper, THEN the range contributes nothing. `&` concatenates after casting both sides to their string forms, so `1 & 2` is `"12"`.

**Boolean logic and conditionals.** `and` and `or` combine effective boolean values (the same coercion `$boolean` applies: zero, empty string, empty array, and empty object are false; other numbers/strings and non-empty structures are true). The conditional `test ? then : else` returns the `else` value only when present; WHEN the test is false and no `else` exists, THEN the result is `undefined`. The default operator `lhs ?: rhs` returns `rhs` WHEN the effective boolean value of `lhs` is false; the coalescing operator `lhs ?? rhs` returns `rhs` only WHEN `lhs` is `undefined`, so `0 ?? "dflt"` is `0` while `0 ?: "dflt"` is `"dflt"`.

**Chaining.** `value ~> $fn(args...)` invokes `$fn` with `value` prepended to the argument list, and `value ~> $fn` invokes `$fn(value)`; chains compose left to right, so `'hello' ~> $uppercase ~> $length` is `5`.

## Constructors And Reshaping

Constructor syntax builds new structure from the evaluation context.

**Array and object constructors.** `[e1, e2, ...]` evaluates each item; nested arrays are preserved as written. `{k1: v1, k2: v2}` builds an object whose keys are string-valued expressions (`{'k' & 1: 'v'}` yields `{"k1":"v"}`). If two pairs of one object constructor or grouping produce the same key, then evaluation must reject with `D1009`.

**Grouping.** A path followed by `{ key: value }` groups the context sequence: each item evaluates the key and value, items sharing a key aggregate their values into an array (singletons stay bare), so `Product{ Name: Price }` maps every distinct name to a price or price array.

**Sorting.** A path followed by `^(term, ...)` sorts the sequence: each term is an expression evaluated per item, ascending by default, `>` prefix for descending, later terms breaking ties. Terms must evaluate to all-numbers or all-strings; if the values mix types, then evaluation must reject with `T2007`.

**Transform.** The transform operator `~> |location|update|` (with an optional `, deletions` list: `~> |location|update, [names]|`) returns a deep copy of its input in which every object matched by `location` is merged with the `update` object and stripped of the listed field names; the original input is not modified.

## Variables, Blocks, And Functions

The language binds names with `:=` and treats functions as first-class values.

**Variables and blocks.** `$name := value` binds a variable and yields the value, so a block whose last statement is an assignment returns that value. A block `(e1; e2; ...)` evaluates statements in order in a child scope and returns the last value; WHEN an inner block rebinds a name, THEN the outer binding is unchanged after the block. Referencing an unbound variable yields `undefined` — except in call position: if a call target is not a function (unbound `$name(...)`, or a non-function value such as `5(3)`), then evaluation must reject with `T1006`.

**Lambdas and closures.** `function($a, $b){ body }` creates a function value; functions close over their definition scope, recursion through the bound name works (`$fact := function($n){ $n <= 1 ? 1 : $n * $fact($n - 1) }`), and functions returning functions support curried application (`$add(2)(3)`).

**Signatures.** A lambda or registered function accepts an optional signature string of the form `<params:return>` using type codes (`s` string, `n` number, `b` boolean, `a` array, `o` object, `f` function, `j` any JSON, `x` any) with modifiers (`?` optional, `+`/`-` array variants). WHEN a call violates the declared signature — wrong type or wrong arity — evaluation must reject with `T0410` positioned at the function name. Built-in library functions enforce their own signatures the same way (`$length('a','b','c')` rejects with `T0410`).

## Function Library

Built-in functions are bound as `$name` in every environment and follow signature validation and sequence semantics.

**Strings.** `$string(value)` renders JSON text for structures, bare text for strings, and 15-significant-digit decimal for numbers (`$string(1/3)` is `"0.333333333333333"`); `$string` of no value is `undefined`. `$length` counts characters, `$substring(str, start, length?)` slices with negative starts counting from the end, `$substringBefore`/`$substringAfter` split at the first separator occurrence (missing separator returns the whole string / empty tail respectively — `$substringBefore("abc","x")` is `"abc"`), `$uppercase`, `$lowercase`, `$trim` (collapses internal whitespace runs to single spaces), and `$pad(str, width, char?)` pads right for positive widths and left for negative. `$contains(str, pattern)` accepts a substring or a regex literal. `$split(str, separator, limit?)` accepts string or regex separators. `$join(array, separator?)` concatenates. `$match(str, regex)` returns match records `{ match, index, groups }` (one record or an array of them), `$replace(str, pattern, replacement, limit?)` accepts string or regex patterns, `$N` group references in string replacements, and a per-match replacement function receiving the match record. `$base64encode`/`$base64decode` and `$encodeUrlComponent`/`$decodeUrlComponent` convert encodings. `$eval(source, context?)` parses and evaluates a JSONata source string against the optional context value.

**Numbers.** `$number` converts numeric strings (including hex forms like `"0x1F"`) and booleans; if the argument is unconvertible, then it must reject with `D3030`. `$abs`, `$floor`, `$ceil` behave conventionally. `$round(value, precision?)` applies banker's rounding — round-half-to-even, so `$round(2.5)` is `2` and `$round(3.5)` is `4`. `$power(base, exp)` and `$sqrt(value)` compute powers and roots; `$sqrt` of a negative must reject with `D3060`. `$formatNumber(value, picture)` applies decimal pictures (`"#,##0.00"`, percent pictures such as `"0.0%"`), `$formatBase(value, radix?)` renders integer digits (default radix 10), `$formatInteger(value, picture)` and `$parseInteger(string, picture)` convert integers to and from spelled-out or formatted forms (picture `"w"` is number words). `$random()` returns a number at least 0 and below 1.

**Aggregation.** `$sum`, `$max`, `$min`, `$average` reduce numeric arrays; a bare number is its own aggregate, `$sum([])` is `0`, and if a member is not a number, then aggregation must reject with `T0412`. `$count` returns array length, `1` for a bare value, and `0` for no value.

**Arrays.** `$append(a, b)` concatenates treating non-arrays as singletons. `$sort(array, comparator?)` sorts (default ordering; comparator returns whether the pair is out of order), `$reverse`, `$shuffle`, `$distinct` (deep-equality dedup), `$zip(a, b, ...)` transposes to the shortest input. Higher-order: `$map(array, fn)` (callback receives value, index, whole array), `$filter(array, fn)`, `$reduce(array, fn, init?)`, `$each(object, fn)` (value, key), `$sift(object, fn)` keeps matching entries, `$single(array, fn)` returns the unique match and must reject with `D3139` when no single match exists.

**Objects, types, and diagnostics.** `$keys` lists keys (over an array of objects: the union of keys), `$lookup(object-or-array, key)` reads a key across an array, `$merge([o1, o2, ...])` merges left to right with later keys winning, `$spread` explodes an object into single-pair objects. `$type` returns one of `"null"`, `"number"`, `"string"`, `"boolean"`, `"array"`, `"object"`, `"function"`. `$exists` distinguishes absence from `null` (`$exists(null)` is true). `$boolean` applies the effective-boolean rules above; `$not` negates them. `$error(message?)` must reject with `D3137`; `$assert(condition, message?)` must reject with `D3141` WHEN the condition is false and yield `undefined` otherwise.

## Date And Time

Millisecond timestamps convert to and from textual forms.

**Conversion.** `$fromMillis(ms)` renders ISO 8601 UTC with milliseconds (`"2018-03-23T10:33:36.617Z"`). `$fromMillis(ms, picture, timezone?)` applies a picture string of bracketed components — `[Y0001]` four-digit year, `[M01]` two-digit month, `[D01]` two-digit day, `[H01]` two-digit 24-hour, `[m01]` minutes, `[P]` am/pm marker — with an optional `±HHMM` timezone offset. `$toMillis(text)` parses ISO 8601; `$toMillis(text, picture)` parses according to the picture; if the text does not match, then it must reject with `D3110`.

**Clock.** `$now()` renders the evaluation timestamp (optionally with picture and timezone arguments), `$millis()` returns it as a number; within one evaluation both observe the same instant, so `$toMillis($now()) = $millis()` holds.

## Bindings And Host Integration

Host programs inject values and functions into the expression environment at three layers.

**Evaluation bindings.** The second argument of `evaluate(input, bindings)` is an object whose entries become `$name` variables for that call only.

**Expression bindings.** `assign(name, value)` binds `$name` in the expression's own environment, persisting across evaluations of that expression. WHEN both layers bind one name, THEN the evaluation-time binding wins.

**Registered functions.** `registerFunction(name, implementation, signature?)` binds a host function as `$name`. WHERE a signature string is given, THEN calls are validated against it (violations reject with `T0410`). A host function returning a promise is awaited and its resolution used as the call result. Inside the call, `this` exposes the evaluation focus: `this.environment.timestamp` is the evaluation's `Date`, and `this.input` is the evaluation input.

## State Model

The core state is one compiled expression per source string:

- **Compiled expression** — the parsed syntax tree plus a static environment holding the built-in function library and any host bindings added through `assign`/`registerFunction`.

Each `evaluate` call derives a dynamic environment (evaluation bindings layered over the static one, plus a fixed timestamp) and projects the tree over the input. Public projections of that state:

1. **Evaluation** — promise-based results under sequence semantics.
2. **AST** — `ast()` structural view of the parsed source.
3. **Bindings** — `assign`, `registerFunction`, and evaluate-time bindings feeding `$name` lookups.
4. **Error channel** — structured `code`/`position`/`token` values from both compile and run time.

Every projection reads the same compiled tree: what the AST shows is exactly what evaluation executes; what a binding layer defines is exactly what `$name` resolves to; what the error channel reports locates the token the parser recorded.

## Error Semantics

| Condition | Outcome |
|---|---|
| Malformed source (unclosed group, dangling dot, unknown operator sequence) | `jsonata()` throws, `code` `S0203`/`S0207`/`S0211` per case, with `position` and `token` |
| Arithmetic operand defined but not a number | rejects with `T2001` |
| Order comparison across types or non-comparable types | rejects with `T2009` |
| Order-by terms of mixed types | rejects with `T2007` |
| Call target is not a function (including unbound `$name(...)`) | rejects with `T1006` |
| Call violates a declared or built-in signature (type or arity) | rejects with `T0410` |
| Aggregation over a non-numeric array member | rejects with `T0412` |
| Duplicate key produced in an object constructor or grouping | rejects with `D1009` |
| `$number` on an unconvertible argument | rejects with `D3030` |
| `$sqrt` of a negative number | rejects with `D3060` |
| `$toMillis` text not matching ISO 8601 or the picture | rejects with `D3110` |
| `$error(...)` | rejects with `D3137` |
| `$assert(false, ...)` | rejects with `D3141` |
| `$single` without exactly one match | rejects with `D3139` |
| Selecting nothing, or an operator with an `undefined` operand | resolves with `undefined`, no rejection |

Error values expose `code`, `position`, and `token` as own fields; message wording is not part of this contract.

## Cross-View Invariants

1. Sequence-rule consistency: every projection that yields a sequence — path steps, predicates, wildcards, grouping values, and library functions — must return a bare item for one-item sequences, `undefined` for empty ones, and an array otherwise, with `[]` forcing the array form in paths.
2. Error-structure consistency: every compile-time throw and run-time rejection must expose a string `code`, a numeric `position`, and the offending `token`, regardless of which subsystem (parser, operator algebra, function library, date-time) produced it.
3. Truthiness agreement: `and`/`or`, conditionals, predicates, the default operator `?:`, and `$boolean` must apply one effective-boolean rule to every JSON value.
4. Binding equivalence: a name bound through `:=`, `assign`, or evaluate-time bindings must be indistinguishable at lookup, and WHEN both `assign` and evaluate-time bindings define one name, THEN evaluation must observe the evaluate-time value.
5. Deep-equality agreement: `=`/`!=` and `$distinct` must apply one structural-equality judgement to arrays and objects. (`in` is not part of this family: it matches members by primitive value only, so an array or object never matches a structurally equal member.)
6. Chain equivalence: `value ~> $fn(a, b)` must produce the same result as `$fn(value, a, b)` for every library and user function.
7. AST fidelity: WHEN `jsonata(source)` compiles, THEN `ast()` must describe the same expression evaluation executes — path steps in navigation order with their `position`s, operator nodes carrying their operator in `value`.

## Public Interface

### Import Surface

```ts
import jsonata from "jsonata";
// jsonata(source) -> expression object with:
//   evaluate(input, bindings?) -> Promise
//   assign(name, value)
//   registerFunction(name, implementation, signature?)
//   ast() -> parsed tree
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `jsonata` | function (default export) | Compile a source string into an expression object; throws structured syntax errors |
| `evaluate` | method | Evaluate against a JSON input with optional per-call bindings; returns a promise |
| `assign` | method | Bind a `$name` value in the expression environment |
| `registerFunction` | method | Bind a host function (optionally signature-validated) as `$name` |
| `ast` | method | Return the parsed syntax tree |

### CLI Entry Points

There is no console script for this package. Programmatic use is through TypeScript/JavaScript imports.

## Appendix A: Environment

The working environment runs Node.js 22 on Linux without network access. The test toolchain is `vitest` with TypeScript; tests import the package under test by its package name `jsonata` (default export). No other third-party runtime packages are available or needed.

The project must declare its packaging metadata in a standard `package.json` at the project root, exposing the package's public entry point under the name `jsonata`, so the test suite can resolve `import jsonata from 'jsonata'`. TypeScript type declarations for the public surface must be included so the test suite type-checks.

## Appendix B: Assessment Notes

Assessment exercises the public surface described in this document across several dimensions: compilation and structured syntax errors; path navigation with predicates, wildcards, descendants, parent/positional binds, and the sequence rules; the operator algebra including type-error codes and `undefined` propagation; constructors, grouping, order-by, and transform; variables, blocks, closures, and signature validation; the function library including regex forms and error codes; date-time conversion; and the three binding layers with `ast()` output. Tests are split into an atomic tier, each verifying a single behavior, and an integration tier composing several projections against shared inputs. Expected values in tests were produced by executing this specification's reference behavior — matching the letter of this document is the only reliable strategy.
