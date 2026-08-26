# Expression Language Engine Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`commons-jexl3` is an embeddable expression-language engine for the JVM. Callers hand it expression or script source text; the engine parses it once into a reusable evaluable object and evaluates it against a context that supplies and receives variable values. The language offers literals over Java types, arithmetic with documented coercion rules, comparison and logical operators, string matching operators, collection literals, property and index navigation, method calls on values, and — in scripts — local variables, control flow, lambdas, and named parameters.

Engine construction is the single configuration point: a builder fixes the evaluation discipline (strict or lenient resolution, silent or throwing failure delivery, safe or unsafe null navigation) and produces an immutable engine. The same source text evaluated under different disciplines yields the documented different outcomes, which makes the discipline axes part of the observable contract.

The installable artifact is the Maven coordinate `org.apache.commons:commons-jexl3`.

## Non-Goals

- This specification does not require the template facility, reporting streams, or any two-language interpolation layer.
- This specification does not require sandboxing, permission control, or customized introspection of arbitrary Java classes.
- This specification does not require pluggable arithmetic, custom operators, namespace-function registration, or annotation processors.
- This specification does not require the JSR-223 scripting bridge.
- This specification does not require expression caching guarantees beyond the correctness of repeated evaluation.
- This specification does not define thread-safety guarantees for contexts; each evaluation uses its caller's context single-threadedly.

## Representative Workflows

**Evaluate expressions against context state.**

```java
JexlEngine jexl = new JexlBuilder().create();
JexlContext ctx = new MapContext();
ctx.set("x", 10);

JexlExpression e = jexl.createExpression("x + 5");
e.evaluate(ctx);                    // 15

jexl.createExpression("y = x * 2").evaluate(ctx);
ctx.get("y");                       // 20 — assignment wrote through
ctx.has("y");                       // true
```

**Run a parameterized script with control flow.**

```java
JexlEngine jexl = new JexlBuilder().create();
JexlScript script = jexl.createScript(
    "var total = 0; for (item : list) { total = total + item }; total");
JexlContext ctx = new MapContext();
ctx.set("list", List.of(1, 2, 3, 4));
script.execute(ctx);                // 10

JexlScript add = jexl.createScript("a + b", "a", "b");
add.execute(new MapContext(), 30, 12);   // 42
add.getParameters();                     // ["a", "b"]
```

## Expression Language

An expression is one formula that produces a value; its vocabulary of literals, operators, and navigation is shared verbatim by scripts.

**Literals.** An undecorated integer literal evaluates to `Integer`; an `l`-suffixed integer to `Long`; a literal with a decimal point to `Double`; single- and double-quoted text both to `String`; `true`/`false` to `Boolean`; `null` to null. The array literal `[1, 2, 3]` over integer elements evaluates to a Java `int[]`. The map literal `{'a': 1, 'b': 2}` evaluates to a `Map` with those entries. The set literal `{1, 2, 3}` evaluates to a `Set`.

**Arithmetic.** `+`, `-`, `*`, `/`, `%` operate numerically with these coercions: two integer operands produce an integer result; an integer result too large for `Integer` widens to `Long`; any floating-point operand makes the result a `Double`. Integer division truncates (`6 / 4` is 1, `7 / 2` is 3) while `6.0 / 4` is 1.5. When either operand of `+` is a non-numeric string, `+` concatenates the string forms; associativity is left-to-right, so `1 + 2 + 'x'` is `"3x"` and `'x' + 1 + 2` is `"x12"`. Unary minus negates.

**Comparison and equality.** `<`, `<=`, `>`, `>=` compare numerically. `==` and `!=` coerce across representations: `2 == 2.0` and `1 == '1'` are both true. The keyword forms `eq` and `ne` are aliases of `==` and `!=`.

**Logic and conditionals.** `&&`, `||`, `!` operate on the truthiness of their operands. Truthiness is: `false`, zero, the empty string, and null are false; other values are true. The ternary `cond ? a : b` selects by truthiness and treats a null condition as false. The elvis form `lhs ?: rhs` returns `lhs` when it is truthy and `rhs` otherwise — a false, zero, empty, null, or undefined left side yields the right side. The null-coalescing form `lhs ?? rhs` returns `lhs` unless it is null or undefined — a false or zero left side is kept. Both `?:` and `??` tolerate an undefined left-hand variable without error in every engine mode.

**Matching operators.** `str =~ pattern` is a regular-expression match when the right side is a string pattern, and containment (`in`) when the right side is a collection or array: `3 =~ [1, 2, 3]` is true. `!~` is its negation. `=^` tests string starts-with; `=$` tests string ends-with.

**Size and emptiness.** `size(value)` returns the length of a string, the element count of a collection, array, or map; `size(null)` is 0. `empty(value)` is true for null, the empty string, and empty collections, and false otherwise.

**Navigation and calls.** `object.name` and `object['name']` both read a map entry or bean property; `sequence[index]` indexes lists and arrays from 0. A method call on a value invokes the underlying Java method (`'text'.toUpperCase()` is `"TEXT"`). Navigation on a null base follows the engine's safe axis (see Engines and Evaluation Modes).

**Assignment.** `name = value` assigns into the evaluation scope and yields the value. Evaluating an assignment for an unscoped name writes the variable into the context, visible afterwards through `JexlContext.get` and `has`. The compound form `name += value` reads, applies the operation, and writes back.

## Scripts and Control Flow

A script is a sequence of statements separated by `;`; its result is the value of the last evaluated statement unless a `return` delivers one earlier.

**Local variables.** `var name = value` declares a script-local variable. Locals are invisible to the context after execution; only undeclared (context) assignments write through. `for (item : collection) { ... }` iterates a collection, array, or integer range `lo .. hi` (inclusive); `while (cond) { ... }` loops on truthiness; `if (cond) a else b` selects statements. A `return value` statement ends the script with that value.

**Lambdas.** A lambda literal `(p) -> { body }` is a first-class value; assigned to a variable it is callable within the script as `f(arg)` with the argument bound to the parameter.

**Parameters.** `createScript(source, names...)` declares named parameters. `execute(context, args...)` binds each argument positionally to its parameter for that run, and `getParameters()` returns the declared names in order. Parameters are scoped to the run and do not write into the context. WHEN a parameter is declared but no argument is supplied for it under a strict engine, THEN evaluation must raise the undefined-variable error.

**Variable introspection.** `getVariables()` returns the set of context variable references the script reads, each reference a list of its navigation segments: for the script `a.b + c` the result contains `[a, b]` and `[c]`. Declared parameters and locals are not context variables and are excluded.

**Expression / script boundary.** `createExpression` accepts a single formula only: source containing statements (declarations, `;`-sequences, loops) must raise the parsing error. `createScript` accepts both statements and bare formulas.

## Engines and Evaluation Modes

A `JexlBuilder` configures and creates an immutable `JexlEngine`; `createExpression` and `createScript` parse source once into reusable `JexlExpression` / `JexlScript` objects evaluated many times against different contexts.

**Strict axis.** `strict(true)` — the default — makes unresolved names errors: evaluating a reference to an undefined variable raises the undefined-variable error naming the variable, and null operands in arithmetic raise the evaluation error (`null + 1` raises; `if (null)` raises). `strict(false)` (lenient) resolves undefined variables and null operands as neutral values: `und + 1` is 1, `null + 1` is 1, `if (null)` takes the false branch, and integer division by zero yields 0.0 instead of raising.

**Silent axis.** `silent(true)` converts evaluation-time errors into a null result (the incident is logged, not thrown): an undefined variable or a division by zero under a strict-silent engine evaluates to null. Parsing errors are not silenced.

**Safe axis.** `safe(true)` — the default — makes navigation on a null base yield null instead of raising: `nothing.field` is null when `nothing` is null. `safe(false)` makes the same navigation raise the undefined-variable error.

**Reuse.** A parsed expression or script carries no evaluation state: the same object evaluated against different contexts sees each context's values, and `getSourceText()` returns the source it was parsed from.

## Contexts

A context is the variable store an evaluation reads and writes. `JexlContext` declares `get(String name)`, `set(String name, Object value)`, and `has(String name)`; `has` distinguishes absent names from names set to null, and `get` of an absent name returns null.

**MapContext.** `MapContext()` starts empty. `MapContext(Map<String, Object> map)` wraps the given map: entries are visible as variables, and variables written by evaluation land in that same map, visible to the caller through the original reference.

## State Model

The engine is immutable configuration; the parsed expression or script is an immutable program; the context is the only mutable state. One evaluation reads variables from the context, computes under the engine's discipline, writes assignments back into the context, and returns the final value. The public projections are: the returned value, the mutated context (`get`/`has`), the declared parameters (`getParameters`), the referenced variables (`getVariables`), and the source text (`getSourceText`). Repeated evaluation of one parsed object against fresh contexts is independent run to run.

## Error Semantics

| Condition | Required result |
|---|---|
| Syntax error in `createExpression` or `createScript` | `JexlException.Parsing` at parse time |
| Statements passed to `createExpression` | `JexlException.Parsing` |
| Undefined variable read (strict engine) | `JexlException.Variable`; `getVariable()` names it |
| Null operand in arithmetic (strict engine) | `JexlException` |
| Integer division by zero (strict engine) | `JexlException` |
| `if` over a null condition (strict engine) | `JexlException` |
| Navigation on a null base with `safe(false)` | `JexlException.Variable` |
| Missing positional argument for a declared parameter (strict engine) | `JexlException.Variable` |
| Any of the above evaluation errors under `silent(true)` | evaluation returns null; nothing is thrown |

`JexlException.Variable` and `JexlException.Parsing` are subclasses of `JexlException`. Lenient engines substitute neutral values instead of raising: undefined and null read as zero-like values, and division by zero yields 0.0.

## Cross-View Invariants

1. Assignment and the context must agree: after evaluating `name = value` for an unscoped name, `context.has(name)` must be true and `context.get(name)` must equal the evaluation's returned value.
2. A wrapped backing map and the context must present one store: entries put in the map before construction must read as variables, and variables assigned during evaluation must appear in the same map object afterwards.
3. The strict and lenient disciplines must diverge exactly as documented on the same source and context: where strict raises the undefined-variable error, lenient must produce the neutral-value result, and `silent(true)` must convert the strict engine's raise into a null return for the same input.
4. A parsed script's introspection must agree with its evaluation: every context variable whose absence makes strict evaluation raise must appear in `getVariables()`, and `getParameters()` must list exactly the names bound by positional arguments in `execute`.
5. Expression and script evaluation must agree on shared language: a bare formula must produce the same value through `createExpression().evaluate(ctx)` and `createScript().execute(ctx)` over equal contexts.
6. One parsed object must be reusable: evaluating it against two different contexts must produce results determined by each context alone, in either order.
7. Truthiness must be uniform across `if`, `while`, the ternary condition, `&&`/`||`/`!`, and the elvis left side: a value classified false in one construct must be classified false in all of them.
8. `size` and `empty` must agree: `empty(v)` must be true exactly when `size(v)` is 0 for strings, collections, arrays, and maps, with null reporting `size` 0 and `empty` true.

## Public Interface

### Import Surface

```java
import org.apache.commons.jexl3.JexlBuilder;
import org.apache.commons.jexl3.JexlContext;
import org.apache.commons.jexl3.JexlEngine;
import org.apache.commons.jexl3.JexlException;
import org.apache.commons.jexl3.JexlExpression;
import org.apache.commons.jexl3.JexlScript;
import org.apache.commons.jexl3.MapContext;
```

### Public Members

| Type | Public members in scope |
|---|---|
| `JexlBuilder` | `JexlBuilder()`; `JexlBuilder strict(boolean flag)`; `JexlBuilder silent(boolean flag)`; `JexlBuilder safe(boolean flag)`; `JexlEngine create()` |
| `JexlEngine` | `JexlExpression createExpression(String expression)`; `JexlScript createScript(String source)`; `JexlScript createScript(String source, String... names)` |
| `JexlExpression` | `Object evaluate(JexlContext context)`; `String getSourceText()` |
| `JexlScript` | `Object execute(JexlContext context)`; `Object execute(JexlContext context, Object... args)`; `String[] getParameters()`; `Set<List<String>> getVariables()`; `String getSourceText()` |
| `JexlContext` | `Object get(String name)`; `void set(String name, Object value)`; `boolean has(String name)` |
| `MapContext` | `MapContext()`; `MapContext(Map<String, Object> map)` |
| `JexlException` | unchecked; base of all engine errors |
| `JexlException.Variable` | undefined/null variable errors; `String getVariable()` |
| `JexlException.Parsing` | syntax errors at parse time |

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `JexlBuilder` | class | Engine configuration and factory. |
| `JexlEngine` | class | Parses source into evaluable objects. |
| `JexlExpression` | interface | One parsed formula. |
| `JexlScript` | interface | One parsed script with parameters. |
| `JexlContext` | interface | Variable store contract. |
| `MapContext` | class | Map-backed context. |
| `JexlException` | exception | Evaluation error base. |
| `JexlException.Variable` | exception | Undefined or null variable. |
| `JexlException.Parsing` | exception | Syntax error. |

### CLI Entry Points

There is no console script for this package. Java callers use the library through Maven dependencies and Java imports.

## Appendix A: Environment

The working environment runs Java 17 on Linux without network access. The Java standard library is available; the target artifact's own declared dependencies resolve through Maven. The assessment environment provides the same JDK and offline execution policy.

The project must provide a Maven `pom.xml` at its root with coordinate `org.apache.commons:commons-jexl3`. Source must compile through the standard Maven lifecycle using locally available artifacts.

## Appendix B: Assessment Notes

Assessment exercises the documented behaviors through the public API: literal and operator semantics with their coercion rules, script statements and scoping, parameter binding and introspection, the strict/silent/safe discipline axes including their documented divergences on identical inputs, context write-through, and the declared error taxonomy. Tests build engines through `JexlBuilder`, evaluate inline source strings against `MapContext` instances, and observe returned values, context state, and raised exception types. Both single behaviors and multi-step scenarios are measured.
