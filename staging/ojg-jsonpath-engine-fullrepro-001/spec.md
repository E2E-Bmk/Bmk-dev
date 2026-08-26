# jp Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`jp` is a JSONPath engine for Go that evaluates path expressions directly
against native Go values — maps, slices, primitives, and structs with
exported fields — without requiring a document to be parsed from JSON
text first. A path expression is a value of type `Expr`, a sequence of
fragments obtained either by parsing path text or by chaining builder
calls in code. One expression value serves every operation: it renders a
canonical string form, selects matching values, reports the normalized
locations of matches, mutates the data at the matched locations, and
tests whether a concrete location falls under a path pattern.

Expressions cover the full dialect: root and current-element anchors,
dot and bracket children, array indexes, wildcards, recursive descent,
slices with steps, unions, and filters. Filters embed a small predicate
language with comparison, logical, arithmetic, membership, emptiness,
existence, and regular-expression operators plus `length`, `count`,
`match`, and `search` functions, and they reach both the element under
test (`@`) and the document root (`$`). The same predicate language is
exposed on its own through the `Script` and `Filter` types and through a
composable `Equation` builder, so a predicate written once serves both
standalone matching and path filtering. The installable module path is
`github.com/ohler55/ojg`; this document specifies the `jp` package,
imported as `github.com/ohler55/ojg/jp`.

## Non-Goals

- This specification does not require parsing or serializing JSON text;
  every operation consumes and returns native Go values supplied by the
  caller.
- This specification does not require support for typed node documents:
  the `GetNodes` and `FirstNode` operations over generic node trees are
  not part of this contract.
- This specification does not require streaming token handlers or
  incremental match handlers; matching operates on fully materialized
  values.
- This specification does not require procedure scripts (the `[( ... )]`
  bracket notation), a script compiler hook, or registries of custom
  script functions.
- This specification does not require support for caller-defined
  collection interfaces; the data model is limited to Go maps, slices,
  arrays, primitives, and structs reached through reflection as
  described in Selecting Values from Data.
- This specification does not require mutation of struct-typed data;
  write operations are defined over maps and slices only, and a write
  step that reaches a struct leaves the struct unchanged.
- This specification does not define concurrency guarantees; expressions
  are immutable values, and callers coordinate concurrent mutation of
  their own data.

## Representative Workflows

**Select, inspect, and read back.** A caller parses a path once, reuses
it across operations, and switches between the value view (`Get`), the
existence view (`Has`), and the location view (`Locate`).

```go
data := map[string]any{
    "inventory": []any{
        map[string]any{"sku": "A1", "qty": 3},
        map[string]any{"sku": "B2", "qty": 0},
        map[string]any{"sku": "C3", "qty": 9},
    },
}
x := jp.MustParseString("$.inventory[?(@.qty > 0)].sku")

skus := x.Get(data)          // []any{"A1", "C3"} in element order
found := x.Has(data)         // true
locs := x.Locate(data, 0)    // normalized paths, e.g. $.inventory[0].sku
first := x.First(data)       // "A1"
fmt.Println(x.String())      // $.inventory[?(@.qty > 0)].sku
```

**Build a path in code, mutate, and verify.** Builder calls produce the
same expression values as the parser, and mutation operations report
results through the ordinary selection views.

```go
data := map[string]any{"cfg": map[string]any{}}

set := jp.R().Child("cfg").Child("retry").Child("limit")
if err := set.Set(data, 3); err != nil {      // creates cfg.retry.limit
    log.Fatal(err)
}
jp.MustParseString("$.cfg.retry.limit").MustSet(data, 5)

check := jp.MustParseString("$..limit")
fmt.Println(check.Get(data))                  // []any{5}

if _, err := jp.MustParseString("$.cfg.retry").Remove(data); err != nil {
    log.Fatal(err)
}
fmt.Println(check.Has(data))                  // false
```

**Walk a document and match locations against patterns.** The walker
reports every node with its normalized path; `PathMatch` classifies each
reported path against a target pattern without re-evaluating data.

```go
target := jp.MustParseString("$..price")
jp.Walk(doc, func(path jp.Expr, value any) {
    if jp.PathMatch(target, path) {
        fmt.Printf("%s = %v\n", path, value)
    }
})
```

## Path Expressions and Parsing

An expression is parsed from text by `Parse` (byte slice input) or
`ParseString` (string input), each returning an `Expr` and an error.
`MustParse` and `MustParseString` return only the `Expr` and panic with
the corresponding parse-error message when parsing fails. Parsing an
empty input returns an empty expression with a nil error.

**Fragments.** An `Expr` is a slice of `Frag` values. The parser
produces fragments of these kinds: `Root` (written `$`), `At` (written
`@`), `Child` (a string key), `Nth` (an integer index), `Wildcard`
(written `*`), `Descent` (written `..`), `Slice` (written with colons),
`Union` (a bracketed comma list), and `Filter` (a bracketed predicate).
A leading `$` or `@` is optional: a path such as `a.b` parses to child
fragments only and evaluates against the same data root as `$.a.b`.

**Dot notation.** After a dot, a name token accepts ASCII letters,
digits, underscores, and all non-ASCII characters. A token consisting
only of digits is still a `Child` key, never an index: `a.0.b` holds the
string key `0`. When any other character is required in a key — spaces,
hyphens, quotes, dots — the key must be written in bracket notation;
`$.k-2` fails to parse, and a quote directly after a dot fails with the
fragment-start error given in Error Semantics.

**Bracket notation.** A bracketed fragment holds a single-quoted or
double-quoted key, an integer, a wildcard `[*]`, a slice, a union, or a
filter. Whitespace directly inside the brackets and around union commas
is accepted and discarded. Backslash escapes inside quoted keys are
preserved as key content. Integer tokens accept leading zeros and
negative signs; `[01]` is the index 1.

**Slices.** A slice fragment holds start, end, and step, each optional:
`[2:]`, `[:2]`, `[1:3]`, `[1:3:2]`, `[::-1]`, and `[-2:-1]` all parse. A
fourth colon-separated part fails with the invalid-slice error.

**Unions.** A union is a comma list of quoted string keys and integer
indexes in one bracket pair, in any mix and order. Any other member kind
fails with the invalid-union error.

**Filters.** A filter fragment is written `[?( predicate )]`; the
predicate grammar is given in Filters and Scripts. The parser normalizes
predicate spacing, quoting, and operator spelling at parse time, so the
rendered form of a parsed filter is canonical regardless of input
spacing.

**Descent.** `..` before a name token parses to a `Descent` fragment
followed by a `Child` fragment. A trailing `..` at the end of the path
is accepted. `..` directly before a bracketed fragment is accepted on
input; its rendered form is irregular, as described in Canonical String
Forms.

**Failure paths.** Every malformed input listed in Error Semantics must
produce the exact error text shown there, and each parse error names the
byte position and the full input text.

## Building Expressions in Code

Expressions are also assembled without a parser. Package-level
constructors start an expression and methods on `Expr` append one
fragment each, returning the extended expression so calls chain.

**Constructors and appenders.** `R()` starts with a root fragment, `A()`
with an at fragment, `C(key)` with a child, `N(n)` with an index, `W()`
with a wildcard, `D()` with a descent, `S(start, ...)` with a slice,
`U(keys...)` with a union, `F(equation)` with a filter, `B()` with a
bracket display flag, and `X()` starts an empty expression. Each has an
equivalent `Expr` method: the short forms `A`, `B`, `C`, `D`, `F`, `N`,
`R`, `S`, `U`, `W` and the spelled-out forms `At`, `Child`, `Descent`,
`Filter`, `Nth`, `Root`, `Slice`, `Union`, `Wildcard`. A built
expression must be indistinguishable from a parsed one in every
operation of this document.

**Slice arguments.** `S` takes a start and up to two more integers for
end and step. The constant `SliceNotSet` marks an absent bound: `S(2)`
and `S(0, SliceNotSet)` render `[2:]` and `[0:]` respectively.
`NewSlice()` returns a `Slice` value with all three parts unset.

**Union arguments.** `U` and `NewUnion` accept string and int keys.
When any argument is of another type, `NewUnion` returns a nil `Union`.

**Bracket flag.** The `B` fragment carries no matching behavior; it
switches the expression's default rendering to bracket form as described
in Canonical String Forms, and it does not affect `Normal`.

## Canonical String Forms

Every expression renders deterministic text through three entry points,
and rendering is the inverse of parsing for the forms identified below.

**String.** The `String` method renders the dot-preferred canonical
form. A root renders `$`, an at renders `@`, and an index renders
`[n]`. A wildcard keeps the spelling it was created with: parsed from
the dot form or built with `W` it renders `*` at the start of the text
and `.*` elsewhere, and parsed from the bracket form `[*]` it renders
`[*]` in `String` as well. A child renders in dot form exactly when
every character of the key is
an ASCII letter, an ASCII digit, an underscore, or a non-ASCII
character; otherwise the child renders bracketed and single-quoted with
backslash escapes for embedded quotes. Slices, unions, and filters
render bracketed. Union string members render single-quoted; numbers in
slices and unions render in minimal decimal form. Filter predicates
render with canonical spacing (one space around binary operators), the
canonical operator spelling given in Filters and Scripts, and
single-quoted strings.

**BracketString.** The `BracketString` method renders every child key
bracketed and quoted, every index bracketed, a wildcard as `[*]`, and a
descent as `[..]`. The `[..]` form and a trailing `[..].` sequence are
output-only: bracket-form descent text must fail to reparse with the
`parse error` text of Error Semantics.

**Append.** The `Append` method appends the rendering to a caller
buffer and returns the extended buffer, preserving existing buffer
content. It takes an optional boolean; passing true selects the bracket
form, and omitting it selects the same form `String` uses. When the
expression contains a `B` fragment, `String` and the no-argument
`Append` render the bracket form.

**Descent rendering.** In dot-preferred form a descent renders `..`
when followed by a dot-form child and collapses to a single `.` when
directly followed by a bracketed fragment: parsing `$..[1]` yields a
three-fragment expression whose `String` is `$.[1]`, and that rendered
text itself fails to reparse. Round-trip stability therefore holds
exactly for expressions in which every descent fragment is immediately
followed by a dot-form child (or is the final fragment rendered through
`String` as a trailing `..`).

**AppendString.** The package-level `AppendString(buf, s, delim)`
appends the string `s` to `buf` quoted with the given delimiter byte,
escaping embedded single and double quotes with a backslash, rendering
control characters as `\t`, `\n`, and `\u00XX` escapes, and passing
non-ASCII characters through unescaped. It returns the extended buffer.

**Normal.** The `Normal` method returns true exactly when every
fragment is a root, an at, a child, an index, or the bracket display
flag. Wildcards, descents, slices, unions, and filters make it false.

## Selecting Values from Data

Selection evaluates an expression against caller data and never mutates
it. Four views exist: `Get` returns the slice of all matched values,
`First` returns one matched value or nil, `FirstFound` returns a matched
value plus a boolean that distinguishes a stored nil from no match, and
`Has` returns whether any match exists. A stored nil value is a real
match: `Has` returns true and `FirstFound` returns (nil, true) for it.
When nothing matches, `Get` returns an empty result, `First` returns
nil, `FirstFound` returns (nil, false), and `Has` returns false. An
empty expression matches nothing on every view.

**Anchors.** `Root` and `At` fragments both refer to the data value
passed to the call; an expression consisting only of `$` (or `@`)
matches exactly that value, including when the value is a scalar or nil.

**Containers.** A child key steps into `map[string]any` by key lookup
and into other Go map kinds with string keys through reflection. An
index steps into `[]any`, typed slices, and arrays through reflection;
negative indexes count from the end; an index outside the bounds
matches nothing. A child applied to a slice, an index applied to a map
or a string, and any step applied to a scalar match nothing — strings
are not indexable containers. A wildcard matches every element of a map
or slice. A slice fragment matches the elements selected by start, end,
and step with Go-style clamping: a positive step walks start toward end
ascending, a negative step walks descending, and unset parts default to
the start (or end) of the array. A union matches the concatenation of
its members' matches in member order, and a member matching the same
element twice yields the value twice. A filter matches the elements of
a map or slice for which its predicate holds. A descent fragment
matches recursively: with fragments after it, it applies them at every
depth; as the final fragment it matches the element reached by the
preceding fragments and every element beneath it.

**Structs.** A child key steps into an exported struct field when the
key equals the field name ignoring ASCII case (`$.ageYear`, `$.ageyear`,
and `$.AgeYear` all reach the field `AgeYear`; `$.age_year` does not).
Unexported fields are invisible to every fragment kind. Struct values
and pointers to structs both work, and wildcards and descents traverse
exported fields.

**Result order.** Values derived from slice traversal — indexes,
slices, wildcards over slices, and filters over slices — arrive in
element order (descending for negative-step slices), and union results
arrive in member order. The order of values produced by wildcards or
filters over maps and by every descent traversal is unspecified, and
repeated calls return the same set in possibly different orders. `First` and `FirstFound` return the first value in
element order when every branching fragment traverses slices only;
which value they return through map traversal is unspecified.

## Filters and Scripts

A filter predicate is a boolean expression over the element under test.
Inside a predicate, `@` anchors paths at the element being tested and
`$` anchors paths at the data value the operation was invoked with, so
one filter compares elements against document-level values.

**Operators.** Binary comparisons are `==`, `!=`, `<`, `<=`, `>`, `>=`.
Numeric operands compare across int and float representations (`1` and
`1.0` are equal); string operands compare lexicographically; boolean
operands compare for equality. Comparisons between values of different
kinds — a string and a number, a boolean and a number — are false, and
ordering comparisons on missing values are false. Logical composition
uses `&&`, `||`, parentheses, and prefix `!`. Arithmetic uses `+`, `-`,
`*`, `/` with multiplication and division binding tighter than addition
and subtraction, which bind tighter than comparisons, which bind
tighter than `&&`, which binds tighter than `||`.

**Literals.** Predicates accept integer literals (exponent forms
normalize: `1e2` renders `100`), decimal literals, single- or
double-quoted strings (canonical rendering is single-quoted), `true`,
`false`, `null`, the constant `Nothing`, regular expressions written
`/pattern/`, and bracketed lists of literals for membership tests. The
bare word `nil` is not a literal and fails to parse with the
not-a-value error.

**Existence and missing values.** A bare path used as a predicate,
`[?(@.x)]`, holds exactly when the path matches — a stored `false`,
`0`, or nil still satisfies it, and `!@.x` holds when the path matches
nothing. The `exists` and `has` operators take a path on the left and a
boolean literal on the right and hold when the path's existence equals
the literal; `[?(@.x has true)]` is the same predicate as `[?(@.x)]`.
Comparing a path against `Nothing` with `==` holds exactly when the
path matches nothing. Comparing against `null` matches only a stored
nil value — a missing key is not equal to `null`.

**Membership, emptiness, and patterns.** `in` holds when the left value
equals a member of the right-hand list literal. `empty` takes a boolean
right side and holds when emptiness of the left string, slice, or map
equals it. `~=` applies a regular expression: the right side is a
`/pattern/` literal or a string, and the predicate holds when the
pattern finds a match anywhere in the left string. The spelling `=~` is
accepted on input and renders canonically as `~=`.

**Functions.** `length(path)` returns the length of the matched string,
slice, or map and returns no value when the path matches nothing (a
comparison against it is then false). `count(path)` returns the number
of matches for the path. `match(left, pattern)` holds when the pattern
matches the entire left string; `search(left, pattern)` holds when the
pattern matches anywhere in the left string.

**Script and Filter values.** `NewScript` parses a predicate — with or
without one pair of surrounding parentheses — into a `Script`;
`MustNewScript` panics on the same inputs `NewScript` rejects. A
script's `String` renders the predicate wrapped in parentheses. The
`Match` method evaluates the script against one data value as the
element under test and returns the boolean outcome; `Match` on nil data
returns false. `NewFilter` requires the full bracketed form beginning
`[?` and ending `]` and returns the wrapped-form error otherwise;
`MustNewFilter` panics with that error. A `Filter` renders its `String`
in the full `[?( ... )]` form. `Filter` embeds `Script`, so a filter
value also exposes `Match`.

## Building and Parsing Equations

An `Equation` is a predicate assembled from constructors instead of
text, for building filters that never risk a parse error.

**Constructors.** Leaf constructors are `ConstBool`, `ConstInt`
(int64), `ConstFloat` (float64), `ConstString`, `ConstNil`,
`ConstNothing`, `ConstRegex`, `ConstList` (a list of literal values
whose int64, float64, string, bool, and nil members render in literal
form), and `Get`, which wraps an `Expr` to be evaluated as a path.
Binary constructors are `Eq`, `Neq`, `Lt`, `Lte`, `Gt`, `Gte`, `Add`,
`Sub`, `Multiply`, `Divide`, `And`, `Or`, `Has`, `Exists`, `In`,
`Empty`, `Regex`, `Match`, `Search`; the unary constructor is `Not`;
`Length` and `Count` wrap an `Expr` into the corresponding function
call.

**Rendering.** An equation's `String` wraps the rendered predicate in
one pair of outer parentheses — `Eq(Get(jp.A().C("x")), ConstInt(3))`
renders `(@.x == 3)` — except that `Length`, `Count`, `Match`, and
`Search` render as bare function calls such as `count(@.l)` and
`match(@.s, '^a')`. Nested groupings of the binary operators render
parentheses where precedence requires them; the rendering of a
predicate that applies `!` to a parenthesized group followed by further
operators is unspecified. Numbers render minimally: `ConstFloat(2.0)`
renders `(2)`. `ConstNil` renders `null`, `ConstNothing` renders
`Nothing`, and `ConstRegex` renders the `/pattern/` form.

**Parsing and conversion.** `MustParseEquation` parses predicate text
into an `Equation` and panics with the equation error of Error
Semantics when the text is malformed. The `Filter` method returns the
equation as a `*Filter`, and the `Script` method returns it as a
`*Script`; both behave identically to values built from text with the
same predicate.

## Mutating Data

Write operations evaluate the expression against caller data, change
the matched locations, and return errors for expression shapes that are
not writable. Maps are changed in place; a slice whose length must
change is replaced in its parent, and the operations that return the
data root return the replacement when the root itself was replaced. Each operation has an `-One`
variant that stops after the first affected match and a `Must-` variant
that panics with the same message the error-returning form returns.
When an expression matches nothing to write, every operation returns a
nil error (or does not panic) and leaves the data unchanged — including
writes into nil data and child keys applied to slices.

**Set and SetOne.** `Set(data, value)` stores the value at every match;
`SetOne` stores at the first match. Both create missing structure on
normal paths: a missing map key followed by another child creates a
`map[string]any`, and a missing map key followed by an index `n`
creates a `[]any` of length n+1 filled with nils. Creation applies to
missing map keys only — an index beyond the bounds of an existing slice
returns the out-of-bounds error, and stepping through a just-created
nil element returns the follow-nil error while leaving the created
containers in place. Wildcard, union, filter, slice, and descent
fragments in a non-final position write through every element they
select. As the final fragment, wildcard and union store at each
selected existing location, and a descent stores the value at the named
key in every map the descent visits — the data root, nested maps, and
maps inside slices — creating the key where it is missing. Set returns an error when the
expression is empty or ends in a root, filter, or slice fragment, and
when a step lands on a scalar (the follow errors of Error Semantics
name the kind of value that blocked the step and the normalized path
prefix that reached it).

**Del and DelOne.** `Del(data)` clears every match; `DelOne` clears the
first. Deleting a map child removes the key; deleting a slice element
by index, wildcard, or union stores nil at the position without
shortening the slice; a final descent removes every existing matching
map key. Del returns an error when the expression is empty or ends in a
root, filter, or slice fragment.

**Remove and RemoveOne.** `Remove(data)` returns the possibly replaced
data root along with an error; `MustRemove` returns only the root.
Removing a slice element excises it — later elements shift down and the
slice shortens — and removing a map child removes the key. Wildcard,
union, slice, and filter final fragments remove every (or, for
`RemoveOne`, the first) selected element. The returned root is the same
object that was passed in unless the data root itself is a slice whose
length changed. Remove returns an error when the final fragment is a
root or a descent.

**Modify and ModifyOne.** `Modify(data, modifier)` calls the modifier
function on every matched element; the modifier returns the replacement
value and a boolean, and the element is replaced only when the boolean
is true. `ModifyOne` stops after the first replacement. The modified
root is returned like `Remove` returns it, so a caller replaces a
top-level slice by targeting it through its parent or root. Root and
descent expressions are accepted: a root expression calls the modifier
once with the whole data value.

## Walking, Locating, and Path Matching

Three operations expose locations rather than values, and one relates
locations to patterns.

**Package-level Walk.** `Walk(data, cb)` visits every node of the data
— the root first, then containers before their contents — and calls
the callback with the node's normalized path (rooted at `$`) and its
value. Slice children are visited in index order; map children are
visited in unspecified order. Passing the optional trailing boolean as
true restricts callbacks to leaves: scalars and empty values stored in
containers. An empty map or slice child produces no leaf callback of
its own. The `Expr` passed to the callback reuses one backing array
across calls, so a callback that retains a path must copy it first.

**Expr.Walk.** `x.Walk(data, cb)` visits only the elements matching
`x`. The callback receives the match's normalized path without a
leading root fragment and the chain of values from the data root down
to the matched element inclusive, so the last chain entry is the
matched value.

**Locate.** `x.Locate(data, max)` returns the normalized paths of
matches as a slice of expressions built from root, child, and index
fragments (a leading root appears exactly when `x` is rooted). A `max`
greater than zero caps the number of returned paths; zero or a negative
`max` returns all. Paths derived from slice traversal arrive in element
order; the order of paths through map traversal and filters is
unspecified.

**PathMatch.** `PathMatch(target, path)` reports whether a normalized
path — fragments limited to root, at, child, and index — falls under a
target pattern. Leading root and at fragments on either side are
interchangeable and an absent leader matches a present one. A child in
the target matches an equal key; an index matches an equal index (no
length information exists, so a negative target index only matches the
equal negative path index); a wildcard matches any single fragment; a
union matches a fragment equal to any member; a slice matches any index
fragment regardless of bounds; a filter matches any single fragment,
since no data is available; and a descent matches a run of zero or more
fragments before the rest of the target continues matching. A target
that is exhausted before the path returns true (prefix semantics); a
path that is exhausted while target fragments remain returns false.

## State Model

The engine holds no state of its own: the single fact source is the
expression value, an immutable fragment sequence, and every operation
is a pure function of the expression plus the caller's data. The public
projections of one expression are: (1) the canonical text forms
(`String`, `BracketString`, `Append`) and the `Normal` classification;
(2) the selection views `Get`, `First`, `FirstFound`, `Has`; (3) the
location views `Locate` and both `Walk` operations; (4) the mutation
operations `Set`, `Del`, `Remove`, `Modify` and their variants, whose
effects are observable through the selection views afterward; (5) the
pattern relation `PathMatch` over normalized paths; and (6) for the
predicate sublanguage, the `Script`, `Filter`, and `Equation` views
that render and evaluate the same predicate. Builder calls extend an
expression by returning a new value; no operation modifies an existing
expression, so one expression is safely reused across data values and
operations in any order.

## Error Semantics

Parse errors carry the byte position and the complete input. Mutation
errors name the operation and the blocking fragment kind; follow errors
name the value kind and the normalized path prefix that reached it.
`Must`-prefixed forms panic with exactly the message the corresponding
error-returning form returns.

| Condition | Error text |
|---|---|
| input ends inside a fragment, e.g. `$[`, `a.`, `[?`, `$.a[` | `not terminated at 3 in $[` (position and source vary) |
| filter predicate ends at an operand, e.g. `[?(` | `'' is not a value or function at 4 in [?(` |
| `nil` used as a literal, e.g. `[?(@.n == nil)]` | `'nil' is not a value or function at 11 in [?(@.n == nil)]` |
| unknown operator token, e.g. `a[?(@.x @ 3)]` | `'' is not a valid operation at 9 in a[?(@.x @ 3)]` |
| unterminated integer bracket, e.g. `$[1` | `expected a number at 4 in $[1` |
| bracket not closed after quoted key, e.g. `['a'` | `invalid bracket fragment at 5 in ['a'` |
| unterminated quote in bracket, e.g. `$['a]` | `invalid bracket fragment at 6 in $['a]` |
| four-part slice `a[1:2:3:4]` | `invalid slice syntax at 9 in a[1:2:3:4]` |
| non-key union member, e.g. `$['a',{}]` | `invalid union syntax at 8 in $['a',{}]` |
| bare word in bracket `a[b]`; `=` in bracket; `!` or other stray token in dot context; bracket-form descent input | `parse error at 3 in a[b]` (position and source vary) |
| quote directly after a dot, e.g. `$.'x y'` | `an expression fragment can not start with a ''' at 4 in $.'x y'` |
| bracketed fragment directly after a single dot, e.g. `$.[1]` | `an expression fragment can not start with a '[' at 4 in $.[1]` |
| `Set`/`SetOne` with an expression ending in a root | `can not set with an expression ending with a Root` |
| `Set`/`SetOne` with an expression ending in a filter | `can not set with an expression ending with a Filter` |
| `Set`/`SetOne` with an expression ending in a slice | `can not set with an expression ending with a Slice` |
| `Set`/`SetOne` with an empty expression | `can not set with an empty expression` |
| `Del`/`DelOne` ending in a root / filter / slice | `can not delete with an expression ending with a Root` (fragment name varies) |
| `Del`/`DelOne` with an empty expression | `can not delete with an empty expression` |
| `Remove`/`RemoveOne` ending in a root | `can not remove with an expression where the last fragment is a Root` |
| `Remove`/`RemoveOne` ending in a descent | `can not modify with an expression where the last fragment is a Descent` |
| write step through an index beyond an existing slice's bounds | `can not follow out of bounds array index at '$.a[5]'` (path varies) |
| write step through a scalar, e.g. a string | `can not follow a string at '$.c'` (kind and path vary) |
| write step through a nil element | `can not follow a <nil> at '$.m.list[1]'` (path varies) |
| `NewFilter`/`MustNewFilter` input not in `[?( ... )]` form | `a filter must start with a '[?' and end with ']'` |
| equation text ends at an operand, e.g. `@.x ==` | `equation not terminated at 7 in @.x ==` |

## Cross-View Invariants

1. For every expression parsed from text in which each descent fragment
   is immediately followed by a dot-form child or is the final
   fragment, parsing the `String` rendering must return an expression
   whose `String` rendering is byte-identical — the canonical form is a
   parse fixpoint.
2. For every expression without a descent fragment, the `String` form
   and the `BracketString` form must reparse to expressions that return
   equal results from `Get` on the same data as the original.
3. An expression assembled with builder constructors must render the
   same `String` as parsing that rendering, and `Get`, `Locate`,
   `Set`, and `PathMatch` must treat the built and the parsed value
   identically.
4. `Has(data)` must equal whether `Get(data)` is non-empty, and
   `FirstFound(data)` must report found exactly when `Has` is true —
   including when the stored value is nil.
5. For any expression and data, `Locate(data, 0)` must return exactly
   one path per `Get(data)` result, every returned path must satisfy
   `Normal()`, evaluating each path against the same data must yield
   exactly one value, and the multiset of those values must equal the
   multiset of `Get` results.
6. Every path reported by the package-level `Walk` must, when evaluated
   against the walked data, return exactly the value the callback
   received, and every path returned by `Locate` for a target without
   negative index fragments must satisfy `PathMatch` with that
   expression as the target (a negative target index cannot match the
   non-negative indexes of normalized paths, per PathMatch).
7. After a `Set(data, v)` that returns nil on a rooted normal path,
   `Get(data)` on that path must return exactly `[v]`; after a `Del` or
   `Remove` of a map-child path that returns nil, `Has(data)` on that
   path must return false.
8. A predicate must behave identically through all three carriers: a
   filter parsed inside a path, the same predicate built as an
   `Equation` and attached with `F`, and the same predicate's `Script`
   evaluated per element with `Match` must select the same elements
   from the same slice, and their rendered forms must agree as given in
   Building and Parsing Equations.

## Public Interface

### Import Surface

```go
import "github.com/ohler55/ojg/jp"
```

Exported names covered by this specification: the types `Expr`, `Frag`,
`Root`, `At`, `Child`, `Nth`, `Wildcard`, `Descent`, `Slice`, `Union`,
`Bracket`, `Filter`, `Script`, `Equation`; the parse and build
functions `Parse`, `ParseString`, `MustParse`, `MustParseString`, `A`,
`B`, `C`, `D`, `F`, `N`, `R`, `S`, `U`, `W`, `X`, `NewSlice`,
`NewUnion`, `NewFilter`, `MustNewFilter`, `NewScript`, `MustNewScript`,
`MustParseEquation`; the equation constructors `Add`, `And`,
`ConstBool`, `ConstFloat`, `ConstInt`, `ConstList`, `ConstNil`,
`ConstNothing`, `ConstRegex`, `ConstString`, `Count`, `Divide`,
`Empty`, `Eq`, `Exists`, `Get`, `Gt`, `Gte`, `Has`, `In`, `Length`,
`Lt`, `Lte`, `Match`, `Multiply`, `Neq`, `Not`, `Or`, `Regex`,
`Search`, `Sub`; the package-level operations `Walk`, `PathMatch`,
`AppendString`; and the values `SliceNotSet` and `Nothing`.

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Expr` | type | a path expression as a fragment sequence; carries all parse, render, select, mutate, walk, and locate methods |
| `Frag` | interface | the element type of `Expr`; implemented by every fragment kind |
| `Root` | type | the `$` fragment |
| `At` | type | the `@` fragment |
| `Child` | type | a string-key fragment |
| `Nth` | type | an integer-index fragment |
| `Wildcard` | type | the `*` fragment |
| `Descent` | type | the `..` fragment |
| `Slice` | type | a start/end/step fragment |
| `Union` | type | a multi-key fragment |
| `Bracket` | type | the bracket display flag fragment |
| `Filter` | type | a predicate fragment usable in paths; embeds `Script` |
| `Script` | type | a standalone predicate with `Match` and `String` |
| `Equation` | type | a composable predicate tree with `String`, `Filter`, and `Script` conversions |
| `Parse`, `ParseString` | function | parse path text into an `Expr` with an error |
| `MustParse`, `MustParseString` | function | parse path text; panic on malformed input |
| `A`, `B`, `C`, `D`, `F`, `N`, `R`, `S`, `U`, `W`, `X` | function | start an expression with one fragment (or empty for `X`) |
| `NewSlice` | function | a `Slice` value with all parts unset |
| `NewUnion` | function | build a `Union` from string and int keys |
| `NewFilter`, `MustNewFilter` | function | parse a `[?( ... )]` filter |
| `NewScript`, `MustNewScript` | function | parse a predicate into a `Script` |
| `MustParseEquation` | function | parse predicate text into an `Equation`; panic on malformed input |
| `Add` … `Sub` (equation constructors) | function | build equation nodes for the corresponding operators, literals, and functions |
| `Walk` | function | visit every node of a data value with normalized paths |
| `PathMatch` | function | test a normalized path against a target pattern |
| `AppendString` | function | append a quoted, escaped string to a buffer |
| `SliceNotSet` | constant | the unset marker for slice bounds |
| `Nothing` | variable | the no-value constant for predicate comparisons |

### CLI Entry Points

There is no console script for this package. Programmatic use is
through Go imports of `github.com/ohler55/ojg/jp`.

## Appendix A: Environment

The working environment runs Go 1.25 or newer on Linux without network
access beyond the Go module proxy. The delivery must be a Go module
with module path `github.com/ohler55/ojg` providing the package
`github.com/ohler55/ojg/jp` so that callers import it as shown in this
document. No third-party runtime dependencies are required; the
standard library (including `regexp` for pattern operators and
`reflect` for typed containers and structs) suffices.

## Appendix B: Assessment Notes

Assessment exercises the package through its public API only. Atomic
checks cover each section of this document in isolation: parse
acceptance and canonical rendering, builder equivalence, selection over
maps, slices, typed containers, and structs, filter and equation
semantics, mutation effects and error returns, walking and locating,
and path matching, plus the exact error and panic messages of Error
Semantics. Integration checks compose multiple projections in one
scenario following the Cross-View Invariants — for example parsing,
rendering, reparsing, and selecting; or mutating and then re-reading
through selection and location views. Where this document leaves result
order unspecified (map wildcards, descents, filters over maps), checks
compare order-insensitively; where order is specified, checks assert
it. Data fixtures are ordinary Go literals constructed in the checks
themselves; no fixture files or external services are involved.
