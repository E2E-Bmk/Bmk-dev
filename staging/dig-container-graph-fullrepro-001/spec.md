# dig Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`dig` is a reflection-based dependency injection library for Go that resolves
a directed acyclic graph of typed values. Callers register constructor
functions with a container; each constructor declares its dependencies as
parameters and its products as results. When a caller invokes a function
against the container, the container instantiates exactly the values that
function requires — walking the dependency graph, calling each needed
constructor at most once, and reusing previously built values on later
requests.

The container is itself the root of a tree of scopes. A scope sees every
constructor registered in itself and its ancestors, but registrations made in
a child stay invisible to its parent and siblings unless explicitly exported.
Values with the same Go type are distinguished by optional string names, and
named value groups collect many values of one type. Decorators
layered on a scope replace the value a key resolves to within that scope and
its descendants without disturbing ancestors. The same graph state is
observable through several projections: invocation results, structured error
chains, a plain-text dump, and a DOT-format graph rendering.

The installable module path is `go.uber.org/dig`.

## Non-Goals

- This specification does not require hooks or callbacks around constructor,
  decorator, or invoked-function execution.
- This specification does not define a dry-run or no-op execution mode.
- This specification does not require introspection option types that copy
  constructor or invocation metadata into caller-supplied structs.
- This specification does not require support for overriding the reported
  source location of a constructor.
- This specification does not require removing or replacing a registered
  constructor; decorators are the only value-replacement mechanism.
- This specification does not require safe concurrent use of one container
  from multiple goroutines; callers serialize access.
- This specification does not define any graph rendering beyond DOT-format
  text output.

## Representative Workflows

**Wiring a small application graph.** Constructors are registered in any
order; dependencies are instantiated lazily and memoized when an invocation
demands them.

```go
type Config struct{ Verbose bool }
type Logger struct{ Cfg *Config }
type Server struct{ Log *Logger }

c := dig.New()
if err := c.Provide(func() *Config { return &Config{Verbose: true} }); err != nil { /* ... */ }
if err := c.Provide(func(cfg *Config) *Logger { return &Logger{Cfg: cfg} }); err != nil { /* ... */ }
if err := c.Provide(func(l *Logger) (*Server, error) { return &Server{Log: l}, nil }); err != nil { /* ... */ }

// Only *Server and its transitive dependencies are built.
err := c.Invoke(func(s *Server) {
    // use s
})
// A second Invoke reuses the same *Server instance.
```

**Scopes, named values, groups, and a decorator.** One container serves
multiple isolated units that share exported facts.

```go
type Conn struct{ Addr string }
type Handler struct{ Route string }

c := dig.New()
c.Provide(func() *Conn { return &Conn{Addr: "ro:5432"} }, dig.Name("ro"))
c.Provide(func() *Conn { return &Conn{Addr: "rw:5432"} }, dig.Name("rw"))
c.Provide(func() Handler { return Handler{Route: "/health"} }, dig.Group("routes"))
c.Provide(func() Handler { return Handler{Route: "/metrics"} }, dig.Group("routes"))

web := c.Scope("web")
web.Decorate(func(h []Handler) []Handler { return append(h, Handler{Route: "/debug"}) })

type ServerParams struct {
    dig.In
    RO       *Conn     `name:"ro"`
    Handlers []Handler `group:"routes"`
}
err := web.Invoke(func(p ServerParams) {
    // p.RO.Addr == "ro:5432"; p.Handlers holds every value sent to "routes"
})
```

## Containers and Scopes

This section defines the scope tree, registration visibility, and where built
values live; every other behavior in this document resolves keys against this
structure.

**Creating containers and scopes.** `New` constructs a `Container` and
accepts zero or more `Option` values. A `Container` is the root scope of a
scope tree. The `Scope` method on a `Container` or a `Scope` creates a child
scope with the given name and zero or more `ScopeOption` values; this
specification defines no `ScopeOption` implementations. A child scope must
observe every constructor and decorator its ancestors know at the time of use,
including ones registered on the ancestor after the child was created.

**Visibility.** When a constructor is registered on a scope, the registration
must be visible to that scope and all of its descendants, and must not be
visible to its ancestors or siblings. Where the `Export` provide-option is
given with a true value, the registration must instead be visible to every
scope in the container, regardless of which scope registered it. `Export`
with a false value leaves the default visibility unchanged.

**Value placement and reuse.** Each registration owns at most one built value
set per key it produces. When two scopes that both see one registration
demand the same key, they must observe the identical value instance; the
constructor must not run a second time. Distinct registrations of the same
key in sibling scopes are independent: each sibling builds and memoizes its
own instance.

**Plain-text dump.** The `String` method on `Container` and `Scope` returns a
description of that scope containing a `nodes:` block with one entry per
registered constructor (its result keys, dependencies, and function type) and
a `values:` block with one entry per value already built in that scope.
Values that have not been built yet must not appear in the `values:` block.

## Providing Constructors

Registration is where the graph is declared and most static validation
happens; this section defines what a constructor is and how `Provide` accepts
or rejects one.

**Constructor shape.** `Provide` on a `Container` or `Scope` accepts a
function with zero or more parameters and one or more results, plus zero or
more `ProvideOption` values. If the final result is of type `error`, that
result reports construction failure and is not a produced value. The
constructor must produce at least one non-error value: if every result is an
error or the function has no results, `Provide` returns an error containing
`must provide at least one non-error type`. If the argument is not a
function, `Provide` returns an error containing
`must provide constructor function`. Variadic parameters are ignored: the
constructor is treated as if the variadic parameter list were absent and is
called with no variadic arguments.

**Lazy, at-most-once execution.** Registering a constructor must not call it.
The container calls a constructor only when an invocation demands one of its
keys, and on success at most once per registration: all values it produced
are stored and reused for every later demand through any scope that sees the
registration. When a constructor returns a non-nil error, its results must
not be memoized, and a later invocation that demands the same key must call
the constructor again.

**Keys and duplicates.** Every produced value is registered under a key: its
Go type, optionally qualified by a name or a group. Registering a second
constructor for a key already registered in the same visibility (same type
and same name, neither in a group) must fail with an error containing
`already provided`, and the failed call must leave the container unchanged
(the earlier registration keeps working). Values with different names, and
values in groups, do not conflict.

**Cycle detection.** By default every `Provide` call verifies that the graph
remains acyclic. A registration that would close a dependency cycle must be
rejected with an error containing `this function introduces a cycle`,
followed by a rendering of the cycle path, and must leave the container
unchanged. Where the container was built with the
`DeferAcyclicVerification` option, `Provide` must skip this check and
`Invoke` must verify the whole graph instead: while a cycle exists anywhere
in the graph, every `Invoke` must fail with an error containing
`cycle detected in dependency graph`, even when the demanded keys do not
touch the cycle. `IsCycleDetected` returns true exactly for errors produced
by either form of cycle rejection.

**Naming and grouping options.** The `Name` provide-option registers every
value the constructor produces under the given name. The `Group`
provide-option sends every value the constructor produces into the named
value group. The group string accepts a `,flatten` suffix: with `flatten`,
the constructor result must be a slice and each element is sent to the group
individually; applying `flatten` to a non-slice result is rejected with an
error containing `flatten can be applied to slices only`. Combining the
`Name` and `Group` options in one `Provide` call is rejected with an error
containing `cannot use named values with value groups`. Neither option is
usable with a constructor returning a result object: `Provide` fails with an
error containing `cannot specify a name for result objects` or
`cannot specify a group for result objects` respectively.

**Interface registration with As.** The `As` provide-option takes one or more
pointers to interfaces. The constructor's concrete result is registered under
each interface type instead of its own type: the interfaces become resolvable
keys and the concrete type does not. If an argument to `As` is not a pointer
to an interface, `Provide` fails with an error containing
`argument must be a pointer to an interface`. If the constructor's result
type does not implement one of the interfaces, `Provide` fails with an error
containing `does not implement`. `As` combined with `Name` registers the
interface keys under that name. `As` cannot be used with a constructor
returning a result object.

## Parameter and Result Objects

Struct embedding turns plain structs into dependency lists and product lists;
this tag mini-language is interpreted by reflection and validated eagerly.

**Parameter objects.** A struct that embeds `In` (directly, or through a
field whose own struct type embeds `In`, recursively) is a parameter object.
When a constructor parameter or an invoked-function parameter is a parameter
object, each exported field of the struct becomes a dependency, resolved by
the field's type plus its tags; the struct itself is not a dependency.
`IsIn` reports whether a value or `reflect.Type` qualifies as a parameter
object. A parameter object must be taken by value: a function parameter that
is a pointer to a parameter object is rejected with an error containing
`cannot depend on a pointer to a parameter object`. An unexported,
non-embedded field in a parameter object is rejected with an error containing
`unexported fields not allowed in dig.In`. A constructor must not return a
parameter object: `Provide` fails with an error containing
`cannot provide parameter objects`.

**Result objects.** A struct that embeds `Out` is a result object. When a
constructor result is a result object, each exported field becomes a produced
value keyed by the field's type plus its tags; the struct itself is not
produced. `IsOut` reports whether a value or `reflect.Type` qualifies as a
result object. An unexported, non-embedded field is rejected with an error
containing `unexported fields not allowed in dig.Out`. A function must not
take a result object as a parameter: the call is rejected with an error
containing `cannot depend on result objects`.

**Field tags on parameter objects.** The `name` tag requests the value
registered under that name and type. The `optional` tag with value `"true"`
marks the dependency optional: when no visible registration produces the key,
the field is filled with the zero value of its type and resolution continues.
An optional dependency whose registration exists but whose constructor fails
must still fail the invocation — `optional` tolerates absence, not failure.
The `group` tag requests a value group: the field must be a slice, filled
with every value sent to that group by visible registrations, in unspecified
order. A group field that is not a slice is rejected with an error containing
`value groups may be consumed as slices only`. Combining `name` and `group`
tags on one field is rejected with an error containing
`cannot use named values with value groups`. Combining `optional` with
`group` is rejected with an error containing
`value groups cannot be optional`. The group tag accepts a `,soft` suffix:
a soft group field must be filled with only the values whose providing
constructors have already run because some other demand required them —
consuming a soft group must not itself trigger any group provider, and an
untouched group yields an empty slice.

**Field tags on result objects.** The `name` tag registers the field's value
under the given name. The `group` tag sends the field's value into the named
group; with a `,flatten` suffix the field must be a slice whose elements are
sent individually, and a non-slice flatten field is rejected with an error
containing `flatten can be applied to slices only`.

## Invocation and Resolution

Invocation is the demand side of the graph: it triggers construction, applies
memoization and decoration, and converts failures into structured errors.

**Invoke semantics.** `Invoke` on a `Container` or `Scope` accepts a function
with zero or more parameters and zero or more `InvokeOption` values; this
specification defines no `InvokeOption` implementations. Each parameter
(expanded through parameter objects) is a demanded key. The container
instantiates all demanded keys and their transitive dependencies, in
unspecified order, then calls the function. If the argument is not a
function, `Invoke` returns an error containing `can't invoke non-function`.
If the invoked function's final result is an `error`, that error is returned
to the caller unchanged; other results of the invoked function are ignored.

**Resolution failures.** When a demanded key has no visible registration and
is not optional, `Invoke` must fail without calling the invoked function,
with an error containing `missing type:` followed by the rendered key. Keys
render as the Go type string, with named keys annotated as
`[name="the-name"]` and group keys annotated as `[group="the-group"]`. When
a constructor in the demanded subgraph returns a non-nil error, `Invoke`
must fail with an error chain that contains
`received non-nil error from function` and wraps the constructor's own error;
a failing group provider fails the whole group demand the same way.

**Error chain contract.** Every error originating in the container — from
`Provide`, `Invoke`, `Decorate`, or resolution — must implement the `Error`
interface, which embeds the standard `error`. `RootCause` walks a chain of
wrapped errors and returns the first error that does not implement `Error`;
if every error in the chain implements `Error`, it returns the bottom-most
one. An error returned by a user constructor or invoked function must be
reachable from the returned chain via `RootCause` unchanged.

**Panic recovery.** By default a panic inside a constructor or invoked
function propagates to the `Invoke` caller as a panic. Where the container
was built with the `RecoverFromPanics` option, such a panic must instead be
captured as a `PanicError` and returned as an error from `Invoke`.
`PanicError` is a struct whose exported `Panic` field holds the recovered
value; its message begins with `panic:` and includes the panic value.
`PanicError` must not implement the `Error` interface, so `RootCause` returns
it when it terminates a chain.

## Decorators

Decorators rewrite what a key resolves to inside one subtree of the scope
tree, and are the only sanctioned way to alter an existing registration.

**Decorate semantics.** `Decorate` on a `Container` or `Scope` accepts a
function and zero or more `DecorateOption` values; this specification defines
no `DecorateOption` implementations. The decorator's parameters are demanded
keys and its results replace the values of those same keys, as seen by the
decorated scope and its descendants. A decorator parameter of the same key
as one of its results receives the undecorated value. Ancestor scopes and
scopes outside the decorated subtree must continue to observe the
undecorated value. Decorating on the root `Container` affects every scope.

**Execution and lifecycle.** A decorator runs lazily, the first time a
demanded key it produces is resolved in the decorated scope or a descendant,
and at most once per scope; its results are memoized like constructor
results. A decorator whose own dependencies cannot be resolved must not fail
at `Decorate` time; the failure surfaces when an invocation demands the
decorated key. Registering a second decorator for a key already decorated in
the same scope must fail with an error containing `already decorated`; the
same key remains decoratable independently in other scopes.

**Group decoration.** A decorator taking a parameter-object field tagged
`group:"g"` and returning a result-object field tagged `group:"g"` replaces
the entire content of group `g` for the decorated subtree with the returned
slice.

## Graph Introspection

The graph must be renderable as DOT text so that external tooling displays
what the container knows.

**Visualize.** The `Visualize` function takes a `*Container`, an `io.Writer`,
and zero or more `VisualizeOption` values, and writes a DOT-format directed
graph of the container to the writer, returning any write error. The output
must begin with `digraph` and must mention the type string of every value key
the container's constructors produce. The `VisualizeError` option takes an
error previously returned by `Provide` or `Invoke` and includes information
about that error in the rendering; passing an error that carries no
renderable graph information leaves the output a valid DOT graph.

## State Model

The container's core state is a scope tree in which every node holds three
tables, and all public behavior projects this state:

- **Registrations**: constructor function plus produce-keys (type, optional
  name or group) and dependency keys, tagged with the scope that owns them
  and whether they are exported.
- **Built values**: for each registration, the memoized results of its single
  successful run; absent until first demanded, absent again never (success is
  permanent), never present after a failed run.
- **Decorations**: at most one decorator per key per scope, with its own
  memoized results per scope.

Public projections of this state: (1) `Invoke` observes resolved values;
(2) `Provide`/`Invoke`/`Decorate` errors observe validation and resolution
failures as `Error` chains; (3) `String` dumps registrations and built
values of one scope; (4) `Visualize` renders registrations as DOT;
(5) `IsIn`/`IsOut`/`IsCycleDetected`/`RootCause` classify structs and errors.
A key resolves in scope S by searching the registrations visible to S
(S and its ancestors, plus exported registrations), then layering the
nearest enclosing decoration for that key on the result.

## Error Semantics

All errors below implement the `Error` interface unless stated otherwise.
"Contains" means the rendered message includes the quoted fragment.

| Condition | Result |
|---|---|
| `Provide` with a non-function argument | error containing `must provide constructor function` |
| Constructor with no non-error results | error containing `must provide at least one non-error type` |
| Duplicate registration of a non-group key visible at the same place | error containing `already provided` |
| Registration closing a cycle (default verification) | error containing `this function introduces a cycle`; `IsCycleDetected` true |
| First `Invoke` finding a cycle (deferred verification) | error containing `cycle detected in dependency graph`; `IsCycleDetected` true |
| `Invoke` with a non-function argument | error containing `can't invoke non-function` |
| Demanded key with no visible registration | error containing `missing type:` and the rendered key |
| Constructor returned non-nil error during resolution | error containing `received non-nil error from function`; `RootCause` returns the constructor's error |
| Invoked function returned non-nil error | that error returned unchanged |
| Unexported field in parameter object | error containing `unexported fields not allowed in dig.In` |
| Unexported field in result object | error containing `unexported fields not allowed in dig.Out` |
| Pointer to parameter object as function parameter | error containing `cannot depend on a pointer to a parameter object` |
| Result object used as function parameter | error containing `cannot depend on result objects` |
| Parameter object returned by a constructor | error containing `cannot provide parameter objects` |
| `Name` option with a result-object constructor | error containing `cannot specify a name for result objects` |
| `Group` option with a result-object constructor | error containing `cannot specify a group for result objects` |
| `Name` and `Group` options combined, or `name` and `group` tags combined | error containing `cannot use named values with value groups` |
| `optional` tag on a group field | error containing `value groups cannot be optional` |
| Group field or flatten result that is not a slice | error containing `value groups may be consumed as slices only` / `flatten can be applied to slices only` |
| `As` argument not a pointer to an interface | error containing `argument must be a pointer to an interface` |
| `As` interface not implemented by the result | error containing `does not implement` |
| Second decorator for a key in one scope | error containing `already decorated` |
| Panic in user function, `RecoverFromPanics` set | `PanicError` returned; message begins `panic:`; not an `Error`; `RootCause` returns it |
| Panic in user function, option not set | panic propagates to the caller |

## Cross-View Invariants

1. A key demanded repeatedly through any scopes that see one registration
   must yield the identical value instance every time, and the registration's
   constructor must run at most once across all of those demands.
2. A key registered with a name or group must render in every error message
   that mentions it with the same annotation syntax (`[name="…"]`,
   `[group="…"]`) regardless of whether the error arose at registration or
   at resolution time.
3. After a set of successful `Provide` calls, `String` on the providing scope
   must list every registered constructor under `nodes:`, and `Visualize` on
   the container must emit a DOT `digraph` mentioning every produced type;
   a value must appear under `values:` only after an `Invoke` has built it.
4. An `Invoke` in a scope with a decoration for key K must observe the
   decorator's output while an `Invoke` in an ancestor scope observes the
   undecorated value, and both observations must remain stable when repeated.
5. For any error returned by `Provide` or `Invoke`: `errors.As` against the
   `Error` interface must succeed exactly when the failure originated in
   container logic, and `RootCause` must return the user function's own error
   exactly when a user function caused the failure.
6. The multiset of values a group field receives must equal the multiset of
   values sent to that group by all visible registrations — regardless of
   provider registration order, flatten usage, or which scope demands the
   group — except that a `,soft` field receives only values from providers
   that had already run for another demand.
7. Cycle rejection must classify identically under `IsCycleDetected` whether
   it fired at `Provide` time (default) or at `Invoke` time
   (`DeferAcyclicVerification`); under default verification the rejected
   registration leaves the container unchanged and usable, while under
   deferred verification every `Invoke` must keep failing as long as the
   cycle remains in the graph.

## Public Interface

### Import Surface

```go
import "go.uber.org/dig"
```

Exported identifiers: `New`, `Container`, `Scope`, `In`, `Out`, `Option`,
`DeferAcyclicVerification`, `RecoverFromPanics`, `ProvideOption`, `Name`,
`Group`, `As`, `Export`, `InvokeOption`, `DecorateOption`, `ScopeOption`,
`Error`, `PanicError`, `RootCause`, `IsCycleDetected`, `IsIn`, `IsOut`,
`Visualize`, `VisualizeOption`, `VisualizeError`.

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `New` | function | Construct a root `Container` with options |
| `Container` | struct | Root scope of a dependency graph; has `Provide`, `Invoke`, `Decorate`, `Scope`, `String` |
| `Scope` | struct | Named child scope; has `Provide`, `Invoke`, `Decorate`, `Scope`, `String` |
| `In` | struct | Embed to mark a struct as a parameter object |
| `Out` | struct | Embed to mark a struct as a result object |
| `Option` | interface | Configuration accepted by `New` |
| `DeferAcyclicVerification` | function | Option: postpone cycle checks to first `Invoke` |
| `RecoverFromPanics` | function | Option: convert user-function panics into `PanicError` |
| `ProvideOption` | interface | Configuration accepted by `Provide` |
| `Name` | function | ProvideOption: register produced values under a name |
| `Group` | function | ProvideOption: send produced values into a value group |
| `As` | function | ProvideOption: register the result as one or more interfaces |
| `Export` | function | ProvideOption: make a scoped registration visible to all scopes |
| `InvokeOption` | interface | Configuration accepted by `Invoke`; none defined |
| `DecorateOption` | interface | Configuration accepted by `Decorate`; none defined |
| `ScopeOption` | interface | Configuration accepted by `Scope`; none defined |
| `Error` | interface | Implemented by every container-originated error |
| `PanicError` | struct | Recovered panic with exported `Panic` field |
| `RootCause` | function | Unwrap to the first non-container error |
| `IsCycleDetected` | function | Report whether an error is a cycle rejection |
| `IsIn` | function | Report whether a struct qualifies as a parameter object |
| `IsOut` | function | Report whether a struct qualifies as a result object |
| `Visualize` | function | Write the container graph as DOT text |
| `VisualizeOption` | interface | Configuration accepted by `Visualize` |
| `VisualizeError` | function | VisualizeOption: include a returned error in the rendering |

### CLI Entry Points

There is no console script for this module. Use is through the Go package
API only.

## Appendix A: Environment

The working environment runs Go 1.21 or newer on Linux without network
access. The module under construction must declare the module path
`go.uber.org/dig` in its `go.mod` so that consuming builds wire it in with a
standard `replace` directive. No third-party libraries are
available or required at runtime; the implementation uses only the Go
standard library.

## Appendix B: Assessment Notes

Functional coverage is verified by compiled test suites that import
`go.uber.org/dig` and exercise the documented public surface only. One suite
checks focused single-behavior contracts (registration validation, tag
parsing, error phrases, predicate functions); another checks multi-step
workflows (scope trees with exports and decorators, value groups across
scopes, deferred cycle verification, memoization across invocations, and
agreement between invocation results, error chains, `String`, and
`Visualize` output). Group-value assertions are order-insensitive. Scoring
counts each passing test function; partial credit accrues per test, so a
correct subset of behaviors earns its share even when other areas are
incomplete.
