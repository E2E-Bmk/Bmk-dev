# cmp Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`cmp` is a semantic-equality library for Go values, designed as a safer and
more expressive alternative to reflective deep comparison in tests. Given two
values of any type, it renders a single judgement — equal or not — by
recursively descending both value trees in lockstep and applying a fixed rule
ladder at every node: user-supplied options first, then a type's own `Equal`
method, then kind-wise structural rules.

The judgement is configurable through a small option language. Fundamental
options (`Ignore`, `Comparer`, `Transformer`) change what equality means at a
node; filter combinators (`FilterPath`, `FilterValues`) scope where those
options apply. The same traversal that produces the boolean verdict also
powers two other projections: a human-readable difference report, and a
machine-consumable reporter protocol that streams every traversal step and
per-leaf verdict with its cause. The library deliberately panics — rather
than silently guessing — when a comparison is ambiguous or would touch
unexported state without permission.

The installable module path is `github.com/google/go-cmp`; the package import
path is `github.com/google/go-cmp/cmp`.

## Non-Goals

- This specification does not require any helper-option collections beyond
  the fundamental options and filters described in this document.
- This specification does not define a stable byte-level layout for
  difference reports; only the properties stated in Difference Reporting are
  contractual.
- This specification does not define the order in which map entries are
  traversed or reported.
- This specification does not require comparing unexported struct fields by
  default; touching them without permission is a defined panic.
- This specification does not require production-grade performance; the
  library targets test code.
- This specification does not require a console interface of any kind.

## Representative Workflows

**Judging equality with a tolerance option.** Options change what equality
means; the report stays consistent with the verdict.

```go
type Reading struct {
    Sensor string
    Value  float64
}

near := cmp.Comparer(func(x, y float64) bool {
    d := x - y
    return d < 0.01 && d > -0.01
})

a := Reading{Sensor: "t1", Value: 1.000}
b := Reading{Sensor: "t1", Value: 1.005}

cmp.Equal(a, b)        // false: 1.000 != 1.005 under ==
cmp.Equal(a, b, near)  // true: the Comparer decides float64 leaves
cmp.Diff(a, b, near)   // "" — empty exactly because Equal is true
```

**Collecting difference locations with a Reporter.** The reporter observes
the same traversal the verdict is computed from.

```go
type pathCollector struct {
    path  cmp.Path
    diffs []string
}

func (c *pathCollector) PushStep(ps cmp.PathStep) { c.path = append(c.path, ps) }
func (c *pathCollector) PopStep()                 { c.path = c.path[:len(c.path)-1] }
func (c *pathCollector) Report(r cmp.Result) {
    if !r.Equal() {
        c.diffs = append(c.diffs, c.path.GoString())
    }
}

var c pathCollector
cmp.Equal(x, y, cmp.Reporter(&c))
// c.diffs now names every leaf where x and y disagree.
```

## Equality Judgement

This section defines the core verdict: how `Equal` decides whether two values
are the same, applying one rule ladder at every node of the value tree.

**The rule ladder.** `Equal` takes two values and zero or more `Option`
values, and reports whether the values are equal. At each node it must apply
these rules in order. First, let S be the set of `Ignore`, `Transformer`, and
`Comparer` options that survive all path and value filters at this node. If S
contains at least one `Ignore`, the node is ignored and counts as equal. If S
contains two or more `Transformer`/`Comparer` options, `Equal` must panic
with a message containing `ambiguous set of applicable options`. If S holds
exactly one `Transformer`, both values are transformed and the outputs are
compared recursively; if S holds exactly one `Comparer`, that function's
verdict decides the node. Second, when no option applied and the type has a
method of the form `Equal(T) bool` (or `Equal(I) bool` with T assignable to
I), the node's verdict must be the result of `x.Equal(y)`, even when either
value is nil. Third, kind-wise structural rules decide.

**Kind rules.** Booleans, integers, floats, complex numbers, strings, and
channels compare with the semantics of the Go `==` operator; a floating-point
NaN therefore never equals another NaN under the default rules. Function
values are equal only when both are nil; two non-nil functions are never
equal, not even the same function value. Structs are equal when every field
compares equal recursively. Slices are equal when both are nil or both are
non-nil with equal lengths and pairwise-equal elements; a nil slice must not
equal an empty non-nil slice, and the same nil/non-nil rule holds for maps.
Maps are equal when they hold the same key set (keys matched via `==`) and
recursively equal values per key. Pointers are equal when both are nil, or
both are non-nil and their pointees compare equal. Interfaces are equal when
both are nil, or both are non-nil with the identical concrete type and equal
underlying values; differing concrete types make the node unequal. Two
top-level arguments of different types are unequal, never a panic on type
mismatch alone.

**Cycle rule.** Before descending through a pointer, slice element, or map
value, the traversal must track visited address pairs on the current path.
When both sides revisit an address pair at the same step, the node counts as
equal by cycle; two cyclic structures with different cycle lengths must
compare unequal rather than loop forever.

**Nil roots.** When both arguments are untyped nil, `Equal` returns true.

## Options and Filters

Options form a small language for overriding equality; filters decide where
in the tree each option speaks.

**Fundamental options.** `Ignore` returns an option that marks matched nodes
ignored (ignored nodes count as equal). An `Ignore` passed to `Equal` without
any filter must cause a panic with a message containing
`cannot use an unfiltered option`. `Comparer` takes a function of the form
`func(T, T) bool` and decides equality for values assignable to T; passing
anything else must panic with a message containing
`invalid comparer function`. `Transformer` takes a name and a function of the
form `func(T) R`; matched values of type T are replaced by the transformed R
values and compared recursively. The name must be a Go identifier or
qualified identifier: an invalid name must panic with a message containing
`invalid name`; an empty name is replaced by an arbitrary placeholder. To
stop a transformer whose output type feeds its own input type from recursing
forever, a transformer must not re-apply while that same transformer is
already the latest transform step on the current path.

**Filters.** `FilterPath` wraps an option with a predicate over the current
`Path`; the option applies only where the predicate reports true. The wrapped
option is evaluated even when a slice element or map entry exists on only one
side, so a path filter is the way to ignore additions and removals.
`FilterValues` wraps an option with a symmetric predicate of the form
`func(T, T) bool`; the option applies only when both current values are
assignable to T and the predicate reports true, and never applies when either
value is invalid. Both filters accept an `Ignore`, `Comparer`, `Transformer`,
an `Options` list, or an already-filtered option.

**Option lists.** `Options` is a slice of `Option` that itself satisfies
`Option`. Passing an `Options` value is equivalent to passing its elements
individually, and filtering an `Options` filters every element. Its `String`
method describes the held options.

**Unexported fields.** When the traversal reaches an unexported field of a
struct type, `Equal` must panic with a message containing
`cannot handle unexported field`, unless that node is ignored or the struct
type is admitted by an exporter. `Exporter` takes a predicate
`func(reflect.Type) bool`; types the predicate admits have their unexported
fields compared normally. `AllowUnexported` takes example struct values and
admits exactly those listed types.

## Difference Reporting

`Diff` renders the judgement as text for humans; its contract is structural,
not byte-exact.

**Emptiness contract.** `Diff` takes the same arguments as `Equal` and
returns an empty string if and only if `Equal` reports true for the same
values and options. Any difference — including a top-level type mismatch —
yields a non-empty report.

**Report shape.** The report is pseudo-Go syntax describing y minus x. A line
beginning with a `-` prefix marks content present in x and absent from y; a
`+` prefix marks content present in y and absent from x; unprefixed lines are
common context. When a transformer participated in the compared subtree, the
report must mention the transformer's name. Every other aspect of the layout
is unstable by design: consumers needing machine-readable differences must
use a `Reporter` instead of parsing this text.

## Traversal Reporting

A reporter observes the exact traversal the verdict is computed from, step by
step, and receives the per-leaf verdicts with their causes.

**Reporter protocol.** `Reporter` wraps a value implementing three methods
into an option. During `Equal`, the traversal must call `PushStep` when
descending into a node, `PopStep` when ascending out, and `Report` exactly
once per leaf node, between that leaf's push and pop. The first `PushStep` of
a run carries an operation-less step that only identifies the root type and
values. Push and pop calls must balance exactly over a run.

**Path steps.** A `Path` is the slice of `PathStep` values from the root to
the current node. `PathStep` is a closed union: `StructField` (field access,
with `Name` and `Index` accessors), `SliceIndex` (element access, with `Key`
returning the index or -1 when the sides diverge, and `SplitKeys` returning
the per-side indexes, -1 marking a missing element), `MapIndex` (entry
access, with `Key` returning the map key), `Indirect` (pointer dereference),
`TypeAssertion` (descent into an interface's concrete value), and `Transform`
(a transformer application, with `Name`, `Func`, and `Option` accessors,
where `Option` returns the originally constructed option so `==` identifies
it). Every step reports its resulting `Type` and its pair of `Values`. When
structs embed structs, the embedded struct is always entered as its own field
step before its fields; an embedded struct's field is never presented as a
direct field of the outer struct.

**Path renderings.** `Path.String` returns the simplified path holding only
struct-field accesses joined with dots (for example `P.Y`). `Path.GoString`
returns the full path in Go syntax, including the braced root type,
indirections, indexes, and type assertions (for example
`{mypkg.Nested}.P.Y`). `Last` returns the final step, and `Index` returns the
ith step with negative indexes counting from the tail; an out-of-range index
returns a non-nil step whose `Type` is nil.

**Leaf verdicts.** `Report` receives a `Result`. `Result.Equal` reports the
leaf verdict, with ignored leaves counting as equal. `ByIgnore` reports that
an `Ignore` option consumed the leaf and never reports true alongside a false
`Equal`. `ByMethod` reports that an `Equal` method decided the leaf. `ByFunc`
reports that a `Comparer` function decided the leaf. `ByCycle` reports that
the cycle rule closed the leaf.

## State Model

One judgement run owns three pieces of state, and every public projection is
a view of the same run:

- **Option table**: the flattened set of fundamental options with their
  filter chains, fixed at the start of the run; at each node the table is
  queried for the surviving set S.
- **Traversal state**: the current `Path` (a stack of steps) and the set of
  visited address pairs used by the cycle rule.
- **Leaf verdicts**: one `Result` per leaf, each carrying its cause flags.

Projections: (1) `Equal` folds all leaf verdicts into one boolean — true
exactly when every leaf is equal or ignored; (2) `Diff` renders unequal
leaves as `-`/`+` lines and returns empty exactly when the fold is true;
(3) `Reporter` streams the traversal and the per-leaf `Result`s as they are
decided; (4) panics abort the run for ambiguity, malformed options, or
forbidden unexported access.

## Error Semantics

The library signals misuse by panicking; comparisons themselves never return
errors. Message fragments below are contractual ("contains" means the panic
value's rendering includes the fragment).

| Condition | Result |
|---|---|
| Traversal reaches an unexported field not admitted by an exporter and not ignored | panic containing `cannot handle unexported field` |
| Two or more `Comparer`/`Transformer` options survive filtering at one node | panic containing `ambiguous set of applicable options` |
| `Ignore` passed to `Equal`/`Diff` with no filter | panic containing `cannot use an unfiltered option` |
| `Comparer` called with a non-function or a function not of shape `func(T, T) bool` | panic containing `invalid comparer function` |
| `Transformer` called with a name that is not a Go (qualified) identifier | panic containing `invalid name` |
| Mismatched top-level argument types | not a panic: `Equal` returns false, `Diff` returns a non-empty report |
| Both arguments untyped nil | not a panic: `Equal` returns true |

## Cross-View Invariants

1. For any pair of values and any valid option set, `Diff` must return an
   empty string exactly when `Equal` returns true — including when equality
   was produced by options, `Equal` methods, or ignored nodes.
2. In every run observed through a `Reporter`, `PushStep` and `PopStep`
   calls must balance, the first push must carry the root step, and `Equal`'s
   returned verdict must equal the conjunction of all reported leaf verdicts.
3. A `Result` must set `ByFunc` only on leaves a `Comparer` decided, and
   `ByMethod` only on leaves an `Equal` method decided; under purely
   structural comparison both flags must stay false on every leaf.
4. A leaf consumed by a filtered `Ignore` must report `ByIgnore` true with
   `Equal` true, and the same input without the ignore option must flip the
   overall verdict exactly when that leaf's values differ.
5. The path a `Reporter` accumulates for a leaf must render consistently
   across projections: `GoString` embeds the root type in braces and every
   step's own `String`, while `String` keeps only the struct-field steps of
   the same path.
6. Cyclic inputs that `Equal` judges equal must set `ByCycle` on the closing
   leaf and must produce an empty `Diff`; cyclic inputs judged unequal must
   terminate with a non-empty `Diff` rather than diverge.
7. Filter scoping must be projection-independent: an option wrapped in
   `FilterPath` or `FilterValues` must change `Equal`, `Diff`, and reported
   `Result` flags on exactly the nodes its predicate admits and on no others.

## Public Interface

### Import Surface

```go
import "github.com/google/go-cmp/cmp"
```

Exported identifiers: `Equal`, `Diff`, `Option`, `Options`, `Ignore`,
`Comparer`, `Transformer`, `FilterPath`, `FilterValues`, `Exporter`,
`AllowUnexported`, `Reporter`, `Result`, `Path`, `PathStep`, `StructField`,
`SliceIndex`, `MapIndex`, `Indirect`, `TypeAssertion`, `Transform`.

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Equal` | function | Judge two values equal under an option set |
| `Diff` | function | Render the differences as human-readable text |
| `Option` | interface | Configuration accepted by `Equal` and `Diff` |
| `Options` | slice type | List of options usable as one option |
| `Ignore` | function | Option: mark matched nodes ignored (requires a filter) |
| `Comparer` | function | Option: custom equality function for a type |
| `Transformer` | function | Option: named value transformation before comparing |
| `FilterPath` | function | Scope an option by a path predicate |
| `FilterValues` | function | Scope an option by a value-pair predicate |
| `Exporter` | function | Admit unexported fields of predicate-approved struct types |
| `AllowUnexported` | function | Admit unexported fields of the listed struct types |
| `Reporter` | function | Option: stream traversal steps and leaf results |
| `Result` | struct | Leaf verdict with cause flags (`Equal`, `ByIgnore`, `ByMethod`, `ByFunc`, `ByCycle`) |
| `Path` | slice type | Steps from root to a node; `String`, `GoString`, `Index`, `Last` |
| `PathStep` | interface | One traversal operation; `String`, `Type`, `Values` |
| `StructField` | struct | Path step: field access (`Name`, `Index`) |
| `SliceIndex` | struct | Path step: slice/array element (`Key`, `SplitKeys`) |
| `MapIndex` | struct | Path step: map entry (`Key`) |
| `Indirect` | struct | Path step: pointer dereference |
| `TypeAssertion` | struct | Path step: interface concrete-value descent |
| `Transform` | struct | Path step: transformer application (`Name`, `Func`, `Option`) |

### CLI Entry Points

There is no console script for this module. Use is through the Go package
API only.

## Appendix A: Environment

The working environment runs Go 1.21 or newer on Linux without network
access. The module under construction must declare the module path
`github.com/google/go-cmp` in its `go.mod`, with the described package at
`github.com/google/go-cmp/cmp`, so consuming builds wire it in with a
standard `replace` directive. No third-party libraries are available or
required; the implementation uses only the Go standard library.

## Appendix B: Assessment Notes

Functional coverage is verified by compiled test suites that import
`github.com/google/go-cmp/cmp` and exercise the documented public surface
only. One suite checks focused single-behavior contracts (kind rules, option
construction and panic conditions, `Equal`-method dispatch, path-step
accessors); another checks multi-step workflows (filter composition across
projections, reporter protocols over nested values, cycle handling, and
agreement between `Equal`, `Diff` emptiness, and reported `Result` flags).
Difference-report assertions rely only on the emptiness and prefix contracts,
never on layout. Panic expectations are asserted by message fragment. Scoring
counts each passing test function; partial credit accrues per test, so a
correct subset of behaviors earns its share even when other areas are
incomplete.
