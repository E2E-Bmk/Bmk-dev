# xpath Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`xpath` is a query engine library for Go that compiles XPath expressions
and evaluates them against any tree-shaped data a caller exposes through a
cursor interface. The engine never sees a concrete document format: callers
implement a `NodeNavigator` — a movable cursor reporting each node's type,
name, prefix, and string value — and the engine drives that cursor to
answer queries. One compiled expression works against any number of
documents and any number of navigator implementations.

An expression compiles once into an immutable `Expr` value. Selecting with
it yields a `NodeIterator` that walks matching nodes lazily; evaluating it
yields a typed Go value — a boolean, a number, a string, or a node
iterator — according to the expression's result type. The language covers
location paths over twelve axes, name and node-type tests, positional and
boolean predicates, arithmetic, comparison, and logical operators, node-set
union, and a thirty-one function library spanning node-set, string,
boolean, and numeric operations. Namespace-aware queries bind prefixes to
URIs at compile time through a separate entry point. The installable module
path is `github.com/antchfx/xpath`.

## Non-Goals

- This specification does not require an XML, HTML, or JSON parser; the
  engine consumes trees exclusively through the caller's navigator and
  never reads document text.
- This specification does not require XPath 2.0 sequence expressions;
  a parenthesized comma list such as `('a','b')` is not a valid function
  argument.
- This specification does not require variable bindings: expressions
  containing `$name` references must fail to compile.
- This specification does not require the `id`, `lang`, `key`, `current`,
  or `document` functions; compiling an expression that calls them must
  fail with the unsupported-function error given in Error Semantics.
- This specification does not require the `namespace` axis; expressions
  using it must fail to compile as described in Error Semantics.
- This specification does not require document mutation, node
  construction, or serialization of results back to markup.
- This specification does not define concurrency guarantees for a
  `NodeIterator`; each iterator is consumed by a single goroutine.

## Representative Workflows

**Selecting nodes with a compiled expression.** A caller compiles a path
expression once, then selects against a navigator positioned anywhere in a
document. The iterator repositions its navigator on each successful
advance; `Current` exposes the cursor at the matched node.

```go
// doc is a caller-built tree such as:
// <bookstore specialty="novel">
//   <book id="b1"><title>Everyday Italian</title><price>30.00</price></book>
//   <book id="b2"><title>Harry Potter</title><price>29.99</price></book>
// </bookstore>
// nav implements xpath.NodeNavigator over that tree, positioned at the root.

expr, err := xpath.Compile("//book[price > 29.99]/title")
if err != nil {
    log.Fatal(err)
}
iter := expr.Select(nav)
for iter.MoveNext() {
    fmt.Println(iter.Current().Value()) // "Everyday Italian"
}
```

**Evaluating typed results and namespace-aware queries.** `Evaluate`
returns a Go value whose dynamic type follows the expression: `float64`
for numeric expressions, `bool` for boolean ones, `string` for string
ones, and `*NodeIterator` for node-set ones. Prefixes in a query bind to
namespace URIs through `CompileWithNS`; matching then compares the
namespace URL reported by the navigator, not the literal prefix.

```go
count := xpath.MustCompile("count(//book)").Evaluate(nav).(float64)   // 2
first := xpath.MustCompile("string(//book/@id)").Evaluate(nav).(string) // "b1"
has := xpath.MustCompile("boolean(//book[3])").Evaluate(nav).(bool)   // false

nsExpr, err := xpath.CompileWithNS("//x:item",
    map[string]string{"x": "http://example.com/ns"})
if err != nil {
    log.Fatal(err)
}
it := nsExpr.Select(nav2) // matches items whose NamespaceURL() is the bound URI
```

## Expression Compilation and Reuse

Compilation turns an expression string into an immutable query object;
everything else in the library consumes compiled expressions. `Compile`
accepts an expression string and returns a pointer to an `Expr` and an
error. When the expression is well formed the error is nil; when it is not,
the returned expression is nil and the error carries one of the messages
catalogued in Error Semantics.

**Source text round trip.** The `String` method on `Expr` must return
exactly the source string the expression was compiled from, unchanged,
for expressions produced by `Compile`, `CompileWithNS`, and `MustCompile`
alike.

**Reuse and statelessness.** A compiled expression holds no evaluation
state. The same `Expr` must be usable against different navigators and
different documents in any order, and re-evaluating against an earlier
document must reproduce the earlier result. Each call to `Select` or
`Evaluate` starts an independent traversal.

**MustCompile.** `MustCompile` accepts an expression string and never
fails: when compilation succeeds it returns the same expression `Compile`
would return; when compilation fails it returns a non-nil no-op
expression instead of panicking. The no-op expression's `String` method
returns the original input string, its `Select` returns an iterator whose
first `MoveNext` returns false, and its `Evaluate` returns nil.

**Namespace binding.** `CompileWithNS` accepts an expression string and a
map from prefix strings to namespace URI strings, and returns the same
two values as `Compile`. Prefixes used by name tests in the expression
must be keys of the map; a prefix absent from the map is a compile error
(`prefix <p> not defined.`). The bound URIs change name-test matching as
described in Namespace-Aware Matching; they do not change the result of
`String`.

**Package-level Select.** The package exports a convenience function
`Select` accepting a navigator and an expression string. It must behave
exactly as compiling the string and selecting with it, and it must panic
when the string fails to compile. It exists for terse call sites; the
method form is the primary interface.

## The Navigator Contract

The engine reads documents through the `NodeNavigator` interface, a
mutable cursor the caller implements; this section states what the engine
requires of an implementation and how the engine treats the cursor it is
given.

**Node taxonomy.** `NodeType` is an integer enumeration with exactly five
public values in this order: `RootNode`, `ElementNode`, `AttributeNode`,
`TextNode`, `CommentNode`. A document is a tree rooted at a single
`RootNode`; elements own an ordered list of children (elements, text,
comments) and an ordered list of attributes reachable only through
`MoveToNextAttribute`.

**Interface methods.** A navigator must implement: `NodeType` returning
the current node's type; `LocalName` returning the current node's name
without prefix (empty for root, text, and comment nodes); `Prefix`
returning the namespace prefix (empty when the node has none); `Value`
returning the node's string value — for an element, the concatenation of
all descendant text; for an attribute, its value; for text and comment
nodes, their character data; `Copy` returning an independent navigator at
the same position; `MoveToRoot`; `MoveToParent`, `MoveToNextAttribute`,
`MoveToChild`, `MoveToFirst`, `MoveToNext`, `MoveToPrevious`, each
returning false without moving when no such position exists; and
`MoveTo`, which repositions this navigator to another navigator's
position and returns false when the other navigator belongs to a
different document or implementation.

**Optional namespace extension.** Where a navigator additionally
implements a `NamespaceURL() string` method, the engine must use it for
namespace-aware name tests and for the `namespace-uri` function as
described in Namespace-Aware Matching. The engine must discover the
method by type assertion at evaluation time; navigators without it remain
fully usable for prefix-literal matching.

**Cursor adoption.** `Expr.Select` must adopt the navigator it is given
rather than copying it: the returned iterator's `Current` returns that
same navigator, and each successful `MoveNext` repositions it in place
through `MoveTo`. When `MoveTo` returns false for a matched node, the
iterator must switch to a `Copy` of the matched navigator from then on.
Callers that need their original position afterwards pass a `Copy`.

## Selection, Evaluation, and Result Iteration

A compiled expression is consumed through two methods with different
result shapes; this section defines both and the iterator they share.

**Select.** `Expr.Select` accepts a navigator and returns a
`*NodeIterator` positioned before the first match. It must return an
iterator for every expression, including expressions whose result is not
a node set; for those, the iterator yields no nodes (`MoveNext` is
false on the first call).

**Evaluate.** `Expr.Evaluate` accepts a navigator and returns an
`interface{}` holding the result: `float64` for numeric expressions,
`bool` for boolean expressions, `string` for string expressions, and
`*NodeIterator` for node-set expressions (returned iterator not yet
advanced). Evaluating the no-op expression produced by `MustCompile` on
invalid input returns nil. For a node-set expression, the iterator
returned by `Evaluate` must yield exactly the nodes, in exactly the
order, that `Select` yields for the same expression and navigator.

**Iterator protocol.** `NodeIterator` exposes `Current`, returning the
navigator at the current match, and `MoveNext`, advancing to the next
match and returning whether one exists. Before the first `MoveNext`,
`Current` must return the navigator at the position selection started
from. After `MoveNext` returns false the iterator is exhausted: further
`MoveNext` calls must keep returning false, and `Current` must remain at
the last matched position. Matches are produced lazily; a caller that
stops calling `MoveNext` early performs no further traversal work.

## Location Paths, Axes, and Node Tests

Location paths select nodes by walking axes step by step; each step names
an axis, a node test, and zero or more predicates. A path starting with
`/` starts at the document root regardless of the navigator's position; a
relative path starts at the navigator's current node. The step separator
`/` chains steps; the abbreviation `//` between steps (or at the start)
walks the `descendant-or-self` axis before the next step.

**Supported axes.** The engine must support exactly these named axes:
`ancestor`, `ancestor-or-self`, `attribute`, `child`, `descendant`,
`descendant-or-self`, `following`, `following-sibling`, `parent`,
`preceding`, `preceding-sibling`, and `self`. Abbreviations: omitting the
axis means `child`; `@` means `attribute`; `.` means `self::node()`;
`..` means `parent::node()`. An unknown axis name is a compile error.
Forward axes yield nodes in document order; `following` yields every node
after the context node's subtree including descendants of later siblings,
and `preceding` yields nodes before the context node excluding its
ancestors.

**Node tests.** A name test matches elements (or attributes, on the
attribute axis) by name as defined in Namespace-Aware Matching; the
wildcard `*` matches any element regardless of name or prefix (`@*`
matches any attribute). The type tests `node()`, `text()`, and
`comment()` match respectively any node, text nodes, and comment nodes.
`node()` on the child axis includes element, text, and comment children.

**Multiple context nodes and duplicates.** Steps evaluate independently
for each context node, concatenating results in context order. The
`parent` axis does not merge duplicates: a step such as `book/..`
reports the shared parent once per child context. Chained descendant
steps (`//a//b`) do not deduplicate either: a node reachable from
several context nodes appears once per context. The `ancestor` and
`ancestor-or-self` axes are the exception: within one step evaluation
they track already-reported nodes and report each distinct ancestor only
once, ordered nearest-first for each context node — a shared ancestor is
reported only for the first context that reaches it. Applying a numeric
predicate to an ancestor step disables that sharing: `ancestor::*[k]`
selects the k-th nearest ancestor of every context node independently,
reporting a shared ancestor once per context.

**Attribute parents.** From an attribute node, `..` must reach the owning
element.

## Namespace-Aware Matching

Name tests resolve differently depending on how the expression was
compiled and what the navigator exposes; this section defines both modes.

**Prefix-literal mode.** For an expression compiled with `Compile` — or
with `CompileWithNS` where the test's prefix is not in the map (only
possible for the empty prefix) — a name test `p:local` matches a node
when the navigator's `Prefix()` equals `p` and `LocalName()` equals
`local`, both as literal strings. An unprefixed test `local` therefore
matches only nodes whose `Prefix()` is empty: `//child` must not match an
element carrying prefix `ns`, while `//ns:child` must match it.

**URI mode.** When the expression was compiled with `CompileWithNS` and
the test's prefix is bound in the map, and the navigator implements
`NamespaceURL() string`, the test must match a node when `LocalName()`
equals the test's local part and `NamespaceURL()` equals the URI bound to
the prefix — the node's own prefix string is irrelevant. Navigators
without the method fall back to prefix-literal matching.

**The namespace-uri function.** `namespace-uri(ns)` must return, for the
first node of the node-set (or the context node when called without
arguments), the navigator's `NamespaceURL()` value when the navigator
implements the method, and the navigator's `Prefix()` value when it does
not. For an empty node-set the function returns the empty string.

**Name functions with prefixes.** `name()` must return the qualified name
`prefix:local` when the node's prefix is non-empty and the bare local
name otherwise; `local-name()` always returns the local part. Both return
the empty string for root, text, and comment nodes.

## Predicates and Position

Predicates filter the nodes of a step or of a parenthesized node-set,
with positional semantics that depend on the predicate's value type.

**Numeric predicates.** A predicate whose expression is a numeric literal
selects by position, counting from 1 in the step's emission order. A
fractional literal truncates toward zero before the comparison: `[1.9]`
and `[1.2]` select position 1, `[2.5]` selects position 2. Zero,
negative, and out-of-range positions select nothing. On the reverse axes
`ancestor`, `ancestor-or-self`, `preceding`, and `preceding-sibling`,
position counts outward from the context node: `preceding-sibling::a[1]`
is the nearest preceding sibling named `a`.

**position() and last().** Inside a predicate, `position()` is the
context node's 1-based position in the step's emission order and
`last()` is the total count, so `[last()]` selects the final node and
`[position() < 3]` the first two. Evaluated as a top-level expression
against a navigator, both `position()` and `last()` must return 1.

**Boolean and string predicates.** A predicate whose value is not a bare
numeric literal filters by the boolean conversion of its value under the
rules in Operators and Type Coercion: an element-existence test
(`[title]`), an attribute comparison (`[@id='b1']`), a content comparison
(`[price > 30]` or `[author='Per Bothner']`), a nested function call
(`[count(author) = 2]`), or a constant (`['x']`, which keeps every node).

**Stacked predicates.** Each successive predicate filters the list
produced by the one before it, with positions recomputed: `[year=2005][2]`
selects the second of the nodes that passed the first predicate, and
`[1][2]` selects nothing because the first predicate leaves one node.

**Attribute positions.** The attribute axis exposes no cross-attribute
positions: every attribute is evaluated at position 1, so `@*[1]` keeps
every attribute of the element and `@*[2]` (or any higher index, or
`[position()=2]`) selects nothing.

**Parenthesized node-sets.** Wrapping a path in parentheses re-bases
positions over the whole result: `(//author)[2]` is the second author in
the document, and `(//author)[last()]` the final one.

## Operators and Type Coercion

Expressions combine with arithmetic, comparison, logical, and union
operators over four value types — node-set, number (float64), string,
and boolean — with coercions applied per operator family.

**Arithmetic.** The binary operators `+`, `-`, `*`, `div`, and `mod` and
unary minus operate on numbers; non-number operands convert first: a
string parses as a number under the `number` function's rules (an
unparsable string yields NaN, so `'a' + 1` is NaN), and a node-set
contributes its first node's value parsed the same way. Multiplicative
operators bind tighter than additive ones, operators of one level
associate left, and parentheses group. `div` by zero yields `+Inf` or
`-Inf` by the dividend's sign, and `0 div 0` yields NaN; `mod` takes the
dividend's sign (`-3 mod 2` is `-1`, `10 mod 3` is `1`). The `*` token
must be recognized as multiplication immediately after a closing
parenthesis with no whitespace, as in `count(//book)*2`.

**Equality.** `=` and `!=` compare by operand types. Two strings compare
lexically. A string and a number compare numerically (`'1' = 1` is
true). When one side is a node-set, the comparison is existential: it is
true when some node's string value makes the comparison true — a
node-set equals a string when some node has exactly that value, equals a
number when some node's value parses to that number, and `!=` is true
when some node's value differs, so a multi-node set satisfies `= v` and
`!= v` simultaneously. Two node-sets are equal when any value from one
equals any value from the other.

**Relational.** `<`, `<=`, `>`, and `>=` always compare numerically:
both operands convert to numbers first, and a comparison involving NaN
is false (`'b' > 'a'` is false because neither parses; `'3' < 4` is
true; `'10' < '9'` is false numerically). Node-set operands compare
existentially as with equality (`//price > 40` is true when any price
exceeds 40).

**Logical.** `and` and `or` convert both operands with the boolean
conversion below; `and` binds tighter than `or` (`1 = 1 or 2 = 3 and
4 = 5` is true).

**Union.** The `|` operator concatenates two node-set operands: all
nodes of the left operand in their own order, then the nodes of the
right operand not already present. It performs no document-order merge
(`//price | //book` yields the three prices before the three books) and
removes duplicates (`//title | //title` yields each title once). An
operand that is not a node-set contributes no nodes (`//book | 'x'`
yields exactly the books, and `1 | 2` yields nothing).

**Boolean conversion.** A node-set converts to true exactly when it is
non-empty. A string converts to true exactly when it is non-empty — so
`'false'` and `'0'` are both true. A number converts to false exactly
when it equals zero; every other number including NaN converts to true
(`boolean(0 div 0)` is true).

**Number conversion.** A string is trimmed of surrounding whitespace and
parsed as a decimal floating-point number, accepting exponent notation
(`'1e2'` is 100), a leading sign, and bare-dot forms (`'-.5'`, `'12.'`);
an empty or unparsable string yields NaN. A boolean converts to 1 or 0.
A node-set converts through its first node's string value; an empty
node-set yields NaN.

**String conversion.** A number renders in plain decimal notation with
the shortest digit string that reproduces the value — never exponent
notation (`0.0000001` renders as `"0.0000001"`, and the sum `0.1 + 0.2`
renders as `"0.30000000000000004"`); integral values render without a
decimal point (`12.0` renders `"12"`); negative zero renders `"0"`;
infinities render `"Infinity"` and `"-Infinity"`; NaN renders `"NaN"`.
A boolean renders `"true"` or `"false"`. A node-set renders as the first
node's string value, or the empty string when the set is empty.

## Function Library

The engine supports exactly thirty-one functions; calling any other name
is the compile error given in Error Semantics. Arity is checked at
compilation, with the errors catalogued in Error Semantics. Arguments
convert to the parameter's expected type under the conversions above.

**Node-set functions.** `count(ns)` returns the number of nodes in the
set as a float64. `sum(ns)` adds the values of the nodes whose string
value parses as a floating-point number under strict parsing; a node
whose value does not parse contributes nothing, so a sum over
non-numeric nodes is 0, as is a sum over an empty set. `sum` also
accepts a number argument and returns it unchanged; evaluating `sum`
over a non-numeric string argument panics. `reverse(ns)` returns the
node-set in reverse emission order, composable with other node-set
consumers (`string-join(reverse(//book/@id), '<')` joins ids last to
first). `position()` and `last()` are described under Predicates and
Position. `name(ns?)`, `local-name(ns?)`, and `namespace-uri(ns?)` are
described under Namespace-Aware Matching; called with an argument they
apply to the set's first node and return the empty string on an empty
set, and called without arguments they apply to the context node.

**Boolean functions.** `true()` and `false()` return the constants.
`not(x)` returns the negated boolean conversion of its argument.
`boolean(x)` applies the boolean conversion.

**Numeric functions.** `number(x)` applies the number conversion.
`floor(x)` and `ceiling(x)` round down and up respectively. `round(x)`
rounds half toward positive infinity: `round(2.5)` is 3, `round(-2.5)`
is -2, `round(1.5)` is 2, `round(-2.6)` is -3; `round` of NaN is NaN.

**String functions.** `string(x)` applies the string conversion; with no
argument it returns the context node's value. `concat(a, b, ...)`
accepts two or more arguments and concatenates their string conversions.
`starts-with(s, p)`, `ends-with(s, p)`, and `contains(s, sub)` test
affix and substring relationships; the empty string is a prefix and a
substring of every string. `substring(s, start)` and
`substring(s, start, length)` extract by 1-based character position:
`start` and `length` round half-up to integers before use
(`substring('12345', 1.5, 2.6)` is `"234"`), a start at or below zero is
clamped to the string's beginning (a start of negative infinity returns
the whole string), a start past the end returns the empty string, and a
zero or negative length returns the empty string.
`substring-before(s, sep)` and `substring-after(s, sep)` return the text
before or after the first occurrence of `sep`, and the empty string when
`sep` does not occur or is empty. `string-length(s)` returns the
character count of the string conversion of its argument; it requires an
argument. `normalize-space(s?)` trims leading and trailing whitespace
and collapses internal whitespace runs (spaces, tabs, newlines) to
single spaces; with no argument it normalizes the context node's value.
`translate(s, from, to)` replaces each character of `s` found in `from`
with the character at the same index in `to`, deleting characters whose
index exceeds the length of `to`; an empty `from` returns `s` unchanged.
`lower-case(s)` lowercases the string. `matches(s, pattern)` reports
whether the regular expression `pattern` finds a match anywhere in `s`;
a pattern given as a literal that does not compile as a regular
expression is a compile-time error. `replace(s, pattern, repl)` replaces
every match of the regular expression `pattern` in `s` with `repl`;
evaluating `replace` with an invalid pattern panics.
`string-join(ns, sep)` joins the string values of a node-set's nodes in
emission order with the separator; both arguments are required and the
first must be a node-set expression.

## State Model

The engine's single fact source is the compiled query held inside an
`Expr`; everything observable is a projection of running that query
against a caller-supplied navigator:

- **Compile** (text to query): `Compile`, `CompileWithNS`,
  `MustCompile` — validation, arity checking, prefix binding, and error
  reporting happen here; the result is immutable.
- **Select** (query × navigator to node stream): `Expr.Select` and the
  package-level `Select`, producing a lazy `NodeIterator` that adopts
  and repositions the navigator.
- **Evaluate** (query × navigator to typed value): `Expr.Evaluate`,
  producing `float64`, `bool`, `string`, or `*NodeIterator` by the
  expression's result type.
- **Reference** (query to text): `Expr.String`, returning the original
  source.

Documents live entirely on the caller's side of the `NodeNavigator`
interface; the engine holds no document state, and iterators hold the
only evaluation state (current position and progress).

## Error Semantics

Compilation reports failures as non-nil errors; evaluation failures for
the two regular-expression cases below are panics. The messages are part
of the contract.

| Condition | Result | Message |
|---|---|---|
| `Compile("")` or `CompileWithNS("", m)` | error | `expr expression is nil` |
| Malformed expression (`///`, `book[`, `@`, `child::`, dangling operator such as `1 +` or `1 = `, stray `)`) | error | `expression must evaluate to a node-set` |
| Unknown function name `f` (including `id`, `lang`, `current`, `key`, `document`) | error | `not yet support this function f()` |
| Unknown axis name `a` | error | `unknown axe type: a` |
| Variable reference or `namespace` axis in expression `E` | error | `undeclared variable in XPath expression: E` |
| Unclosed string literal | error | `xpath: scanString got unclosed string` |
| `CompileWithNS` with a test prefix `p` missing from the map | error | `prefix p not defined.` |
| `count()` with no argument | error | `xpath: count(node-sets) function must with have parameters node-sets` |
| `sum()` with no argument | error | `xpath: sum(node-sets) function must with have parameters node-sets` |
| `reverse()` with no argument | error | `xpath: reverse(node-sets) function must with have parameters node-sets` |
| `floor()`, `ceiling()`, or `round()` with no argument | error | `xpath: ceiling(node-sets) function must with have parameters node-sets` |
| `substring` with fewer than two arguments | error | `xpath: substring function must have at least two parameter` |
| `substring-before` or `substring-after` with one argument | error | `xpath: substring-before function must have two parameters` |
| `translate` with an argument count other than three | error | `xpath: translate function must have three parameters` |
| `concat` with fewer than two arguments | error | `xpath: concat() must have at least two arguments` |
| `not()` with no argument | error | `xpath: not function must have at least one parameter` |
| `string-length()` with no argument | error | `xpath: string-length function must have at least one parameter` |
| `number` with two or more arguments | error | `xpath: number function must have at most one parameter` |
| `string` with two or more arguments | error | `xpath: string function must have at most one parameter` |
| `name` with two or more arguments | error | `xpath: name function must have at most one parameter` |
| `matches` with an argument count other than two | error | `xpath: matches function must have two parameters` |
| `replace` with an argument count other than three | error | `xpath: replace function must have three parameters` |
| `string-join` with one argument | error | `xpath: string-join(node-sets, separator) function requires node-set and argument` |
| `starts-with`, `ends-with`, or `contains` with one argument | error | (message unspecified; the error must be non-nil) |
| `matches` with an invalid literal regular expression | error | (message names the regular-expression parse failure) |
| Package-level `Select` with an uncompilable expression | panic | (the compile error) |
| Evaluating `replace` with an invalid pattern | panic | (message names the invalid pattern) |
| Evaluating `sum` over a non-numeric string argument | panic | `sum() function argument type must be a node-set or number` |

`MustCompile` never returns an error or panics: on any compile failure it
returns the no-op expression described in Expression Compilation and
Reuse.

## Cross-View Invariants

1. For every expression accepted by `Compile` or `CompileWithNS`, and for
   every result of `MustCompile`, the `String` method must return the
   exact source string the expression was built from.
2. For every node-set expression, the `*NodeIterator` returned by
   `Evaluate` must yield the same nodes in the same order as the iterator
   returned by `Select` on the same navigator, and `count()` over the
   same path must equal the number of successful `MoveNext` calls.
3. For every node-set expression `E`, `boolean(E)` must be true exactly
   when `Select` on `E` yields at least one node, and `string(E)` must
   equal the `Value()` of the first yielded node — the empty string when
   none is yielded.
4. A compiled expression evaluated against document A, then document B,
   then document A again must return identical results for the two A
   evaluations; no state crosses evaluations.
5. After each `MoveNext` that returns true on an iterator whose
   navigator repositioning succeeds via `MoveTo`, `Current` must return
   the same navigator instance that `Select` adopted, positioned at the
   match; the caller observes its own navigator move.
6. For any node-set expression `E`, the union `E | E` must yield exactly
   the nodes of `E` once each, in the same order.
7. `string-join(reverse(P), sep)` must equal the values of `Select(P)`
   joined with `sep` in reverse order, for every path `P` over attribute
   or element nodes.
8. For every element node reached by a path, `name()` must equal
   `local-name()` when `Prefix()` is empty and must equal the prefix,
   a colon, and `local-name()` otherwise — regardless of whether the
   expression was compiled with or without a namespace map.

## Public Interface

### Import Surface

```go
import "github.com/antchfx/xpath"
```

The package exports: the functions `Compile`, `CompileWithNS`,
`MustCompile`, and `Select`; the types `Expr` (methods `Evaluate`,
`Select`, `String`), `NodeIterator` (methods `Current`, `MoveNext`),
`NodeNavigator` (interface, thirteen methods as given in The Navigator
Contract), and `NodeType`; and the `NodeType` constants `RootNode`,
`ElementNode`, `AttributeNode`, `TextNode`, and `CommentNode`.

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Compile` | function | Compiles an expression string into an `*Expr` or returns a compile error. |
| `CompileWithNS` | function | Compiles with a prefix-to-URI map for namespace-aware name tests. |
| `MustCompile` | function | Compiles, returning a no-op expression instead of an error on failure. |
| `Select` | function | Compiles and selects in one call; panics on compile failure. |
| `Expr` | type | An immutable compiled expression; evaluates and selects against navigators. |
| `NodeIterator` | type | Lazy cursor over the nodes matched by a node-set expression. |
| `NodeNavigator` | interface | Caller-implemented document cursor the engine drives. |
| `NodeType` | type | Integer enumeration of the five node kinds. |
| `RootNode` | constant | Node type of a document root. |
| `ElementNode` | constant | Node type of an element. |
| `AttributeNode` | constant | Node type of an attribute. |
| `TextNode` | constant | Node type of character data. |
| `CommentNode` | constant | Node type of a comment. |

### CLI Entry Points

There is no command-line executable in this module. All functionality is
reached through the Go import path.

## Appendix A: Environment

The working environment runs Go 1.25 or newer on Linux without network
access beyond the Go module proxy. The delivery must be a Go module with
module path `github.com/antchfx/xpath` so that callers import
`github.com/antchfx/xpath` as shown in this document. No third-party
runtime dependencies are required; the standard library (including
`regexp` for the pattern functions) suffices.

## Appendix B: Assessment Notes

Correctness is exercised through compiled Go test programs that import the
module by its public path and drive it through small in-memory documents
exposed via test-owned `NodeNavigator` implementations — one implementing
the optional `NamespaceURL` method and one without it. Tests are grouped
in two suites: one asserts single behaviors in isolation (one compile
error, one axis traversal, one predicate rule, one function result, one
coercion case), the other drives multi-step workflows spanning several
projections (compile, select, evaluate, iterate, and re-use together) and
checks the cross-view invariants above. Expected values in tests come from
this document's stated behavior; error-message assertions use the exact
shapes given in Error Semantics, and node expectations are stated in terms
of each test's own document structure. Documents used by tests are
self-contained in-memory trees — no fixture files and no XML parsing.
