# Fx Lifecycle and Application Receipts

## Product Overview

Fx Lifecycle is a Go dependency-injection system that assembles typed constructors, resolves named and grouped values, scopes modules and decorators, runs application lifecycle hooks, projects startup failures, and coordinates shutdown. The installable module name is go.uber.org/fx.

The supported system is fully in process. App, Option, Provide, Supply, Replace, Decorate, Module, Invoke, Populate, Lifecycle, Shutdowner, DotGraph, ErrorHandler, and fxevent.Logger operate over caller-owned Go functions and memory state without a server or external service.

## Non-Goals

- This specification does not require HTTP, databases, message brokers, operating-system services, containers, or remote resources.
- This specification does not define a command-line application.
- This specification does not require constructors or lifecycle hooks to open listeners or start background services.
- This specification does not define application-specific dependency types, module names, hook effects, or logging backends.
- This specification does not require exact wall-clock duration, default log text, stack traces, or DOT statement order.

## Representative Workflows

The first workflow provides one lazy component, invokes it, records lifecycle order, starts the app, requests shutdown, and stops in reverse order.

~~~go
var order []string
app := fx.New(
    fx.Provide(func(lc fx.Lifecycle) *Component {
        lc.Append(fx.Hook{
            OnStart: func(context.Context) error {
                order = append(order, "start")
                return nil
            },
            OnStop: func(context.Context) error {
                order = append(order, "stop")
                return nil
            },
        })
        return &Component{}
    }),
    fx.Invoke(func(*Component) {}),
)
if err := app.Err(); err != nil {
    panic(err)
}
if err := app.Start(context.Background()); err != nil {
    panic(err)
}
if err := app.Stop(context.Background()); err != nil {
    panic(err)
}
~~~

The second workflow creates a named value and a value group, decorates them inside one module, and observes the resolved results through Invoke.

~~~go
type Inputs struct {
    fx.In
    Primary string   `name:"primary"`
    Parts   []string `group:"parts"`
}

app := fx.New(
    fx.Provide(
        fx.Annotate(func() string { return "base" }, fx.ResultTags(`name:"primary"`)),
        fx.Annotate(func() string { return "left" }, fx.ResultTags(`group:"parts"`)),
        fx.Annotate(func() string { return "right" }, fx.ResultTags(`group:"parts"`)),
    ),
    fx.Module("consumer",
        fx.Decorate(func(in Inputs) Inputs {
            in.Primary = "decorated:" + in.Primary
            return in
        }),
        fx.Invoke(func(in Inputs) { _ = in }),
    ),
)
if err := app.Err(); err != nil {
    panic(err)
}
~~~

The third workflow creates a `receipt.GraphPlan`, selects one logical application and module scope, enables resolution, lifecycle, event, and shutdown projections, records fresh observations in a caller-owned `receipt.AppJournal`, and captures one coherent `receipt.AppReceipt`. A later generation is compared without treating constructor duration, hook duration, or operating-system signal numbers as semantic graph differences.

## Dependency Resolution and Laziness

Dependency resolution connects Option registration, constructor demand, singleton reuse, invocation, population, supply, and replacement.

**Constructor registration.** Provide must accept constructor functions whose parameters are dependencies and whose results are provided values plus an optional final error. Constructor registration order must not affect resolution. Duplicate untagged values of the same type must make App.Err non-nil unless grouping or replacement semantics make them distinct.

**Laziness and reuse.** A provided constructor must run only when Invoke, Populate, another demanded constructor, a decorator, or logger construction requires one of its results. Each demanded constructor must run at most once per App, and every consumer of the same key must receive the cached result.

**Invoke.** Invoke functions must run during New after providers and decorators are registered. Their dependencies must resolve before the function call. Invokes must run in supplied order, and a failing invoke must prevent later invokes from running and must become App.Err.

**Supply, Replace, and Populate.** Supply must provide each value by its concrete type without calling a constructor. Replace must substitute the selected graph value for consumers while preserving unrelated keys. Populate must assign resolved values into non-nil pointer targets during New and must demand the same cached instances observed by Invoke.

**Validation.** ValidateApp must report invalid constructors, missing dependencies, cycles, annotation errors, and invalid targets without running application invokes or lifecycle hooks.

**Application options.** StartTimeout and StopTimeout configure the corresponding duration reported by an App. Error attaches one or more causes to application construction, and App.Err must preserve each attached cause.

## Modules, Decoration, and Tagged Values

Modules connect visibility, scoped transformations, named keys, value groups, and consumers.

**Module scope.** Module must group its options under the supplied name. Provide or Supply combined with Private must expose its values to the declaring module and its contained modules, but not to a parent or sibling module. Non-private provided values must remain visible to descendants and eligible parent consumers.

**Decoration.** Decorate must transform an existing graph key and must not introduce an otherwise absent key. A decorator in the top-level App must affect every eligible consumer. A decorator inside a module must affect that module and its descendants while consumers outside that module continue to receive the undecorated value.

**Decoration chain.** Applicable decorators must run after the original constructor and before invokes that consume the result. Nested decorators must compose from broader scope to narrower scope, each must receive the prior value, and the final result must remain cached for consumers in that scope.

**Named values.** Annotated with Name or Annotate with ResultTags must create a named result key, while ParamTags must request the corresponding named parameter. A named value and an untagged value of the same Go type must remain distinct.

**Value groups.** ResultTags with a group tag or an Out field with a group tag must contribute a value to that group. A matching In slice must receive every contributed value exactly once; group element order is unspecified. A decorator of a group must receive and return the complete group slice for its scope.

## Lifecycle Start, Rollback, and Stop

Lifecycle behavior connects materialized values, Hook registration, App.Start, failure rollback, App.Stop, and event records.

**Hook registration.** Lifecycle.Append must retain Hook values in append order. Only constructors that are demanded append hooks. A Hook with a nil OnStart or OnStop must contribute no call for that phase.

**Start order.** App.Start must run OnStart callbacks in append order with the supplied context. It must stop at the first non-nil error and return that cause. A hook whose OnStart was not reached must never have its OnStop called for that failed start.

**Rollback.** When OnStart fails after earlier hooks succeeded, App.Start must call OnStop for the successfully started hooks in reverse order. The returned error must preserve the start failure, and rollback errors must be combined without hiding that cause. fxevent.Logger must receive OnStartExecuting and OnStartExecuted records, followed by RollingBack and RolledBack around rollback.

**Stop order.** After a successful start, App.Stop must call non-nil OnStop callbacks in reverse successful-start order. It must continue after an OnStop error, return the combined stop errors, and emit OnStopExecuting, OnStopExecuted, and Stopped records that agree with callback outcomes.

**Context boundaries.** Start and Stop must pass the supplied context to every reached hook. A context error must be returned when it prevents completion, and callbacks not reached before cancellation must not be reported as successfully executed.

**Fresh lifecycle.** A new App must own an independent lifecycle. Starting, rolling back, or stopping one App must not reuse hook state or event records from another App.

## Failure Projections and Shutdown

Failure and shutdown behavior connects App.Err, ErrorHandler, DotGraph, fxevent.Logger, Shutdowner, Wait, Done, and explicit Stop.

**Construction failure.** New must retain registration, decoration, and invoke failures in App.Err. A failing invoke must be sent to each ErrorHandler registered with ErrorHook. When graph visualization is available, DotGraph and VisualizeError must expose a nonempty dependency graph associated with the same failure.

**Event logging.** WithLogger must resolve one fxevent.Logger and route graph, invoke, lifecycle, rollback, start, stop, and logger-initialization records through Logger.LogEvent. Event values must preserve their documented function names and errors. A logger construction failure must appear in App.Err without silently discarding the original application failure.

**Shutdown signal.** Shutdowner.Shutdown must broadcast one ShutdownSignal to current App.Wait receivers and the corresponding operating-system signal to App.Done receivers. ExitCode must set ShutdownSignal.ExitCode. Shutdown must not call lifecycle OnStop itself; the owner must call App.Stop after receiving the signal.

**Receiver behavior.** Wait must return a channel of ShutdownSignal, and Done must return a channel of operating-system signals. Multiple receivers registered before Shutdown must each receive the same terminal broadcast. A later duplicate shutdown must not invent a different exit code for an already delivered signal.

**Terminal closure.** App.Stop after a shutdown signal must execute the normal reverse lifecycle and stop signal receivers. A fresh App must expose new Done and Wait channels and must not receive a prior App's shutdown signal or exit code.

## Graph Plans, Journals, and Application Receipts

The public `go.uber.org/fx/receipt` package binds dependency resolution, module scope, constructor demand, lifecycle hooks, event outcomes, and shutdown into one application generation.

`receipt.NewGraphPlan` must create an immutable empty plan. `receipt.GraphPlan.SelectApp` must return a new plan with stable logical application and module identities and reject an empty application identity without changing the prior plan. `receipt.GraphPlan.IncludeResolution`, `receipt.GraphPlan.IncludeLifecycle`, `receipt.GraphPlan.IncludeEvents`, and `receipt.GraphPlan.IncludeShutdown` must return new plans retaining earlier selections. A lifecycle or shutdown projection without an application selection is invalid.

`receipt.ConstructorFact` must bind constructor identity, scope, demand, result keys, and terminal error class. `receipt.ResolutionFact` must bind named and grouped keys, decoration ownership, and consumer resolution. `receipt.HookFact`, `receipt.EventFact`, and `receipt.ShutdownFact` must bind registration and execution order, rollback and stop outcome, event graph identity, and shutdown result. `receipt.Capture` must return a complete `receipt.AppReceipt` only after every requested projection reaches a coherent boundary; constructor, invoke, hook, or shutdown failure must return its documented error with no contradictory partial receipt.

`receipt.NewAppJournal` must create an empty journal. `receipt.AppJournal.Record` must append one observation with a strictly increasing sequence and isolate caller-owned values. `receipt.AppJournal.Entries` must return an ordered caller-owned snapshot; modifying inputs or returned slices must not affect the journal or an earlier receipt.

`receipt.AppReceipt.Validate` must reject an undemanded constructor represented as run, an unresolved or multiply resolved ordinary key, group order inconsistent with contribution order, decoration crossing its module scope, lifecycle execution inconsistent with registration and rollback rules, event outcomes inconsistent with graph facts, and shutdown facts inconsistent with wait completion. `Digest` and `Equivalent` must cover logical graph keys, module scopes, demand, resolution, constructor outcomes, hook order, rollback, reverse stop, events, and shutdown result. They must ignore only constructor and hook durations and operating-system signal numbers. `receipt.Diff` must return a `receipt.ChangeReceipt` deterministically ordered by projection and logical identity; equivalent receipts produce no changes.

## State Model

The product exposes seven connected projections:

1. Graph state: options, constructor keys, dependency edges, decorators, invokes, and cached values.
2. Scope state: module ancestry, private visibility, named keys, groups, and scoped decorated values.
3. Application state: construction error, start phase, successful hooks, stop phase, and terminal state.
4. Lifecycle state: appended hooks, start order, rollback set, stop order, callback errors, and contexts.
5. Failure state: returned error, ErrorHandler notifications, DotGraph, and VisualizeError output.
6. Event state: provider, invoke, start, rollback, stop, and logger initialization records.
7. Shutdown state: current receivers, ShutdownSignal, operating-system signal, exit code, and subsequent stop completion.

Every accepted transition must leave these projections consistent with the invariants below.

## Error Semantics

| Condition | Required result |
|---|---|
| A constructor target is not a valid function | App.Err is non-nil and no dependent invoke runs |
| A demanded dependency is absent | App.Err describes the missing type or tagged key |
| Two constructors provide the same ungrouped key | App.Err reports a duplicate provision |
| A demanded constructor returns an error | App.Err preserves that cause and no dependent invoke runs |
| A decorator returns an error | App.Err preserves that cause and affected invokes do not run |
| An invoke returns an error | App.Err preserves the cause and ErrorHandler receives it |
| An OnStart callback fails | Start returns its cause and rolls back prior successful hooks |
| An OnStop callback fails | Stop continues remaining reverse-order callbacks and returns combined errors |
| ValidateApp receives an invalid graph | It returns an error without running invokes or hooks |
| VisualizeError receives an error without a graph | It returns an unable-to-visualize error |
| Shutdown cannot reach registered receivers | Shutdown returns its broadcast error |

## Cross-View Invariants

1. Every resolved dependency key must agree across Provide or Supply, decorator input, Invoke parameters, Populate targets, and cached constructor identity.
2. A private value must remain visible within its module subtree and absent from parent and sibling resolution.
3. Named and grouped annotations must agree between producer result tags, In or ParamTags consumers, decorators, and invokes.
4. Only demanded constructors append lifecycle hooks, and every demanded constructor must run at most once per App.
5. Start success order must equal hook append order, while rollback and normal stop order must be the reverse of successfully started hooks.
6. Lifecycle callback results must agree across returned App errors, fxevent records, and the set of callbacks eligible for later Stop.
7. A construction or invoke failure must agree across App.Err, ErrorHandler notification, DotGraph when available, and fxevent.Logger records.
8. ShutdownSignal and Done delivery must describe one shutdown request, while lifecycle closure occurs only through the subsequent App.Stop.
9. ExitCode must agree across Shutdowner options and every Wait receiver for that broadcast.
10. A fresh App must own independent constructor caches, module scopes, lifecycle state, event records, receivers, and shutdown metadata.

## Public Interface

### Import Surface

~~~go
import (
    "context"

    "go.uber.org/fx"
    "go.uber.org/fx/fxevent"
    "go.uber.org/fx/receipt"
)
~~~

### API Catalog

| Name | Kind | Role |
|---|---|---|
| receipt.GraphPlan, receipt.NewGraphPlan | type and function | Build an immutable multi-view application graph plan. |
| receipt.GraphPlan.SelectApp, receipt.GraphPlan.IncludeResolution, receipt.GraphPlan.IncludeLifecycle, receipt.GraphPlan.IncludeEvents, receipt.GraphPlan.IncludeShutdown | methods | Select logical graph identities and enable coherent receipt projections. |
| receipt.ConstructorFact, receipt.ResolutionFact, receipt.HookFact, receipt.EventFact, receipt.ShutdownFact | types | Represent coherent graph, lifecycle, event, and shutdown facts. |
| receipt.AppJournal, receipt.NewAppJournal | type and function | Own ordered application observations. |
| receipt.AppJournal.Record, receipt.AppJournal.Entries | methods | Append an isolated observation and return a caller-owned snapshot. |
| receipt.AppReceipt, receipt.Capture | type and function | Publish one complete application generation. |
| receipt.AppReceipt.Validate, receipt.AppReceipt.Digest, receipt.AppReceipt.Equivalent | methods | Validate, identify, and compare application generations. |
| receipt.ChangeReceipt, receipt.Diff | type and function | Report deterministic semantic changes between application generations. |
| fx.New | function | Constructs an App and executes demanded invokes. |
| fx.App | type | Owns dependency graph, lifecycle, errors, and signals. |
| fx.App.Err | method | Returns construction or invoke failure. |
| fx.App.Start | method | Executes start hooks with rollback on failure. |
| fx.App.Stop | method | Executes stop hooks in reverse order. |
| fx.App.Done | method | Returns an operating-system-signal receiver. |
| fx.App.Wait | method | Returns a ShutdownSignal receiver. |
| fx.Option | interface | Applies configuration to an App or Module. |
| fx.Options | function | Combines multiple options. |
| fx.Provide | function | Registers lazy constructor functions. |
| fx.Supply | function | Registers existing values. |
| fx.Replace | function | Replaces existing values by type or annotation. |
| fx.Decorate | function | Registers graph transformations. |
| fx.Invoke | function | Registers eager consumer functions. |
| fx.Populate | function | Assigns resolved values to pointer targets. |
| fx.Module | function | Creates a named option scope. |
| fx.Private | variable | Restricts provision visibility to a module subtree. |
| fx.ValidateApp | function | Validates graph construction without invokes. |
| fx.In | type | Marks a parameter object. |
| fx.Out | type | Marks a result object. |
| fx.Annotated | type | Associates a target with name or group tags. |
| fx.Annotate | function | Applies annotations to a function or value. |
| fx.ParamTags | function | Annotates function parameters with tags. |
| fx.ResultTags | function | Annotates function results with tags. |
| fx.Lifecycle | interface | Accepts application hooks. |
| fx.Hook | type | Pairs optional start and stop callbacks. |
| fx.StartHook | function | Adapts a supported function into a start Hook. |
| fx.StopHook | function | Adapts a supported function into a stop Hook. |
| fx.StartStopHook | function | Adapts paired functions into one Hook. |
| fx.ErrorHandler | interface | Receives application invoke failures. |
| fx.ErrorHook | function | Registers ErrorHandler values. |
| fx.DotGraph | type | Carries a DOT dependency graph. |
| fx.VisualizeError | function | Extracts an attached dependency graph. |
| fx.WithLogger | function | Selects an fxevent.Logger constructor. |
| fx.Printer | interface | Receives fallback formatted output. |
| fx.Shutdowner | interface | Broadcasts application shutdown requests. |
| fx.ShutdownSignal | type | Carries a signal and exit code. |
| fx.ExitCode | function | Sets exit metadata for Shutdowner. |
| fxevent.Logger | interface | Receives structured Fx events. |
| fxevent.Event | interface | Marks structured Fx event values. |
| fxevent.Provided | type | Reports constructor registration. |
| fxevent.Invoking | type | Reports invoke entry. |
| fxevent.Invoked | type | Reports invoke completion. |
| fxevent.OnStartExecuting | type | Reports start-hook entry. |
| fxevent.OnStartExecuted | type | Reports start-hook completion. |
| fxevent.OnStopExecuting | type | Reports stop-hook entry. |
| fxevent.OnStopExecuted | type | Reports stop-hook completion. |
| fxevent.RollingBack | type | Reports rollback entry. |
| fxevent.RolledBack | type | Reports rollback completion. |
| fxevent.Started | type | Reports App.Start completion. |
| fxevent.Stopped | type | Reports App.Stop completion. |
| context.Context | interface | Carries hook cancellation and deadlines. |

### Receipt Package Signatures

The receipt package exposes the following signature-complete surface. Fact slices and the values returned by `Entries` are caller-owned copies.

~~~go
package receipt

type GraphPlan struct { /* immutable selection */ }

func NewGraphPlan() GraphPlan
func (GraphPlan) SelectApp(appID, module string) (GraphPlan, error)
func (GraphPlan) IncludeResolution() (GraphPlan, error)
func (GraphPlan) IncludeLifecycle() (GraphPlan, error)
func (GraphPlan) IncludeEvents() (GraphPlan, error)
func (GraphPlan) IncludeShutdown() (GraphPlan, error)

type ConstructorFact struct {
    ID         string
    Scope      string
    Demanded   bool
    Ran        bool
    ResultKeys []string
    ErrorClass string
}

type ResolutionFact struct {
    Key            string
    Name           string
    Group          string
    ProviderScope  string
    ConsumerScope  string
    DecoratorScope string
    Consumer       string
    Contribution   int
    Optional       bool
    Resolved       bool
}

type HookFact struct {
    ID           string
    Owner        string
    Phase        string
    Registration int
    Execution    int
    Succeeded    bool
    Rollback     bool
    ErrorClass   string
}

type EventFact struct {
    Kind       string
    Operation  string
    Scope      string
    Sequence   uint64
    Succeeded  bool
    ErrorClass string
}

type ShutdownFact struct {
    Requested     bool
    Receivers     int
    Delivered     int
    ExitCode      int
    WaitCompleted bool
    StopCompleted bool
}

type AppJournal struct { /* ordered isolated observations */ }

func NewAppJournal() *AppJournal
func (*AppJournal) Record(sequence uint64, fact any) error
func (*AppJournal) Entries() []any

type AppReceipt struct {
    AppID        string
    Module       string
    Constructors []ConstructorFact
    Resolutions  []ResolutionFact
    Hooks        []HookFact
    Events       []EventFact
    Shutdown     *ShutdownFact
}

func Capture(plan GraphPlan, journal *AppJournal) (AppReceipt, error)
func (AppReceipt) Validate() error
func (AppReceipt) Digest() string
func (AppReceipt) Equivalent(AppReceipt) bool

type ChangeReceipt struct {
    Changes []string
}

func Diff(before, after AppReceipt) ChangeReceipt
~~~

`AppJournal.Record` accepts only the five documented fact types, either as values or non-nil pointers. Sequence numbers begin at one and increase by exactly one. `Capture` includes constructor facts for every selected application, adds resolution, lifecycle, event, and shutdown facts only when the corresponding plan method selected that projection, and rejects facts that cannot form one coherent application generation.

Hook phases are `start`, `rollback`, and `stop`. Result keys, logical scopes, consumers, operation identities, event kinds, and error classes are nonempty whenever their fact uses them. Receipt digests and change lists are deterministic; `ChangeReceipt.Changes` uses projection-qualified logical identities and is lexically ordered.

### CLI Entry Points

There is no console command for this module. Direct execution with go run is not supported. Programmatic use is through Go imports.

## Appendix A: Environment

The working environment runs Go 1.25 on Linux without network access. The standard library and the dependency graph recorded by the delivered go.mod and go.sum are available from the local module cache. The delivered module must keep the module path go.uber.org/fx and must build without fetching additional packages.

All dependencies, scopes, constructor effects, lifecycle observations, event records, and shutdown receivers must remain in memory. Constructors and hooks used here do not open system listeners or contact external resources.
