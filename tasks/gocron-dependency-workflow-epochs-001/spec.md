# Dependency-Aware Workflow Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`gocron` is a Go scheduling library that registers functions as jobs and executes them through a shared scheduler. This extension adds named dependency workflows: a workflow stores a directed acyclic graph of scheduler-backed jobs, and every manual trigger creates an isolated execution epoch of that graph.

Each node remains an ordinary scheduler job. Scheduler concurrency limits, distributed locks, job listeners, limited-run policies, and singleton behavior therefore remain observable while dependency release is coordinated by the workflow.

## Non-Goals

- This specification does not require persistent workflow definitions or recovery after process restart.
- This specification does not require cron-triggered workflow epochs; epochs begin through `Workflow.RunNow`.
- This specification does not define conditional branches based on task return values other than success or error.
- This specification does not require mutation of a graph while an epoch is active.
- This specification does not define a console command or configuration-file format.

## Representative Workflows

A workflow is attached to an existing scheduler. Parents are registered before children, the scheduler is started, and a run handle observes the resulting epoch.

```go
scheduler, _ := gocron.NewScheduler()
flow, _ := gocron.NewWorkflow(scheduler, "release")

flow.Add("compile", gocron.NewTask(compile), nil)
flow.Add("unit", gocron.NewTask(unitTests), []string{"compile"})
flow.Add("lint", gocron.NewTask(lint), []string{"compile"})
flow.Add("publish", gocron.NewTask(publish), []string{"unit", "lint"})

scheduler.Start()
run, _ := flow.RunNow(context.Background())
result, err := run.Wait(context.Background())
```

The same workflow supports controlled replacement between epochs. The job identity returned by `Update` remains stable because the scheduler updates the existing registered job.

```go
job, _ := flow.Add("fetch", gocron.NewTask(fetchV1), nil)
updated, _ := flow.Update("fetch", gocron.NewTask(fetchV2), nil)
if job.ID() != updated.ID() {
	panic("workflow update changed job identity")
}
```

## Graph Registration and Mutation

Graph registration establishes the topology used by future epochs and binds every node to a scheduler job.

**Construction and identity.** `NewWorkflow` accepts a `Scheduler` and a non-empty `name`. `Name` returns that name unchanged. `Add` accepts a non-empty node name, a `Task`, a dependency-name slice, and job options. It returns the registered `Job`. `Nodes` returns nodes sorted by name, with dependency slices copied so caller mutation does not alter the graph.

**Dependency validation.** WHEN `Add` or `Update` receives a dependency name, THEN that dependency must already be registered. Duplicate dependency names must collapse to one edge. A node must not depend on itself. `Update` must reject any replacement that introduces a direct or transitive cycle, and a rejected mutation must leave the previous graph and job usable.

**Mutation boundaries.** `Update` replaces the task, dependencies, and job options of an existing node while preserving its job UUID. `Remove` deletes a node and its scheduler job. WHEN another node still depends on the removal target, THEN `Remove` must reject the operation without changing the graph. WHILE at least one epoch is active, `Add`, `Update`, and `Remove` must return `ErrWorkflowBusy` without partial mutation.

**Closure.** `Shutdown` marks the workflow closed and removes all workflow-owned jobs from the scheduler. Repeated `Shutdown` calls must return nil. WHILE closed, graph mutation and `RunNow` must return `ErrWorkflowClosed`.

## Epoch Scheduling and Dependency Release

An execution epoch is a snapshot of the graph, so its ordering decisions remain stable for the duration of the run.

**Starting an epoch.** `RunNow` requires a started scheduler and a non-empty workflow. It returns immediately with a `WorkflowRun`; it must not wait for task completion. `Epoch` returns a positive, monotonically increasing identifier unique within that workflow. Distinct active epochs must keep independent node results and task contexts.

**Ready-node execution.** At epoch start, every node with no dependencies becomes ready. A non-root node must start only after every direct dependency in the same epoch succeeds. Independent ready nodes must be eligible to execute concurrently. In a diamond graph, the join node must execute exactly once after both parents succeed, regardless of parent completion order.

**Scheduler integration.** Every released node must execute through its registered `Job.RunNow` path. Scheduler-wide `WithLimitConcurrentJobs`, workflow-node listeners, distributed job lockers, `WithLimitedRuns`, and the workflow's enforced wait-style singleton serialization must affect execution exactly as they affect ordinary jobs. A successful `RunNow` submission does not itself mark the node successful; terminal state follows the task or scheduler execution outcome.

**Task contexts.** WHEN a registered task's first parameter is `context.Context`, THEN the workflow must supply the epoch context, replacing any context originally supplied through `NewTask`. Other task parameters and error-return behavior must remain compatible with `NewTask` jobs.

## Results, Failures, and Cancellation

Run handles expose both live snapshots and a stable terminal result for each epoch.

**Snapshots and waiting.** `Snapshot` returns the current epoch ID, timestamps, and a copied map keyed by node name. Mutating the returned map must not affect later snapshots. `Wait` blocks until the epoch is terminal or the wait context ends. A wait-context deadline must return the current snapshot and that context error without canceling the epoch. Repeated waits after completion must return equivalent terminal data.

**Node outcomes.** Every node begins as `pending`, becomes `running` when released, and ends as `succeeded`, `failed`, `blocked`, or `canceled`. Terminal nodes have a non-zero completion time. A task-returned error, panic recovered by the scheduler, before-listener rejection, distributed-lock acquisition error, or `Job.RunNow` submission error must mark that node failed.

**Failure propagation.** WHEN a node fails, THEN all of its not-yet-started descendants must become `blocked` with `ErrWorkflowDependencyFailed` and must not invoke their task functions. Unrelated branches must continue. `Wait` must return `ErrWorkflowFailed` if any result is failed or blocked.

**Cancellation.** Canceling the context passed to `RunNow`, or calling `WorkflowRun.Cancel`, must cancel that epoch only. Unreleased nodes become canceled and context-aware running tasks observe the canceled epoch context. `Workflow.Stop` cancels every active epoch and waits for their handles to become terminal, bounded by the supplied stop context. A canceled epoch's `Wait` returns the epoch context error unless the epoch already contains a failed or blocked result.

## Scheduler Interactions and Lifecycle

Workflow lifecycle operations coordinate with the retained scheduler without taking ownership of the scheduler itself.

**Job visibility.** Jobs returned by `Add` and `Update` must appear through `Scheduler.Jobs` until removed or the workflow is shut down. Workflow-created jobs use a dormant one-time schedule; ordinary scheduled time must not create an epoch or run a node independently.

**Listeners and locks.** User event listeners must still fire for their documented scheduler outcome. `AfterJobRuns` accompanies workflow success, `AfterJobRunsWithError` accompanies a returned error, `AfterJobRunsWithPanic` accompanies a recovered panic, and `AfterLockError` accompanies lock acquisition failure. Workflow completion tracking must not suppress these listeners or call a node task after a lock failure.

**Limits and singleton behavior.** Scheduler `LimitModeWait` must bound concurrently executing ready nodes without losing them. The same workflow node must execute serially across overlapping epochs. Node results must remain associated with the epoch that submitted them even when singleton or global limits delay execution.

**Stop and shutdown ordering.** `Workflow.Shutdown` must not call `Scheduler.Shutdown`; other scheduler jobs remain registered. Calling workflow lifecycle methods after scheduler shutdown must return rather than leak goroutines. A caller that needs graceful task cancellation must stop or shut down workflows before stopping the scheduler.

## State Model

The workflow's durable in-memory definition consists of its name, closed flag, registered node names, dependency edges, and scheduler job identities. `Name`, `Nodes`, and `Scheduler.Jobs` are public projections of that definition.

Each call to `RunNow` snapshots the definition into an epoch containing an ID, start and completion times, per-node state, and an epoch context. `Snapshot` and `Wait` are public projections of this epoch state. Graph mutations affect later epochs only and are rejected while any snapshot is executing.

## Error Semantics

| Condition | Error |
|---|---|
| nil scheduler passed to `NewWorkflow` | `ErrWorkflowSchedulerRequired` |
| empty workflow name | `ErrWorkflowNameRequired` |
| empty node name | `ErrWorkflowNodeNameRequired` |
| duplicate node name | `ErrWorkflowNodeExists` |
| update or removal target absent | `ErrWorkflowNodeNotFound` |
| dependency absent | `ErrWorkflowDependencyNotFound` |
| self-edge or transitive cycle | `ErrWorkflowCycle` |
| removing a node that still has dependents | `ErrWorkflowNodeHasDependents` |
| starting an empty workflow | `ErrWorkflowEmpty` |
| mutation during an active epoch | `ErrWorkflowBusy` |
| operation after workflow shutdown | `ErrWorkflowClosed` |
| `RunNow` before scheduler start | `ErrWorkflowSchedulerStopped` |
| at least one failed or blocked node | `ErrWorkflowFailed` from `Wait` |
| descendant prevented by dependency failure | `ErrWorkflowDependencyFailed` in the node result |

Wrapped errors must support `errors.Is` against the corresponding sentinel. Existing scheduler errors returned by `NewJob`, `Update`, `RemoveJob`, or `Job.RunNow` must remain discoverable with `errors.Is`.

## Cross-View Invariants

1. A node name and job UUID returned by `Add` must agree with the corresponding entries from both `Workflow.Nodes` and `Scheduler.Jobs`.
2. A successful `Update` must preserve the job UUID across `Update`, `Workflow.Nodes`, `Scheduler.Jobs`, and later epoch results.
3. A successful `Remove` or `Workflow.Shutdown` must remove the same job UUID from both workflow and scheduler projections.
4. A node marked `succeeded` by `Snapshot` or `Wait` must have completed its task and success listener before any dependent node begins.
5. A node marked `blocked` by `Wait` must have a failed ancestor in the same epoch and must have no task side effect in that epoch.
6. A diamond join's single task invocation, listener calls, and terminal result must all belong to the same epoch and occur after both parent results are successful.
7. Across overlapping epochs, each run's epoch ID, task context, node errors, and terminal timestamps must remain isolated even when scheduler limits serialize the same jobs.
8. After `Workflow.Stop` returns nil, every run that was active when stopping began must return a terminal result from `Wait`.

## Public Interface

### Import Surface

The package import path is:

```go
import "github.com/go-co-op/gocron/v2"
```

The retained scheduler identifiers used by this feature are `Scheduler`, `NewScheduler`, `Job`, `Task`, `NewTask`, `JobOption`, `WithName`, `WithLimitedRuns`, `WithSingletonMode`, `WithEventListeners`, `BeforeJobRuns`, `BeforeJobRunsSkipIfBeforeFuncErrors`, `AfterJobRuns`, `AfterJobRunsWithError`, `AfterJobRunsWithPanic`, `AfterLockError`, `WithDistributedJobLocker`, `WithLimitConcurrentJobs`, `LimitMode`, `LimitModeWait`, `LimitModeReschedule`, `Locker`, `Lock`, `ErrJobNotFound`, `ErrJobRunNowFailed`, and `ErrPanicRecovered`.

The workflow identifiers are `Workflow`, `WorkflowRun`, `WorkflowNode`, `WorkflowResult`, `WorkflowNodeResult`, `WorkflowNodeStatus`, all six `WorkflowNode*` status constants, `NewWorkflow`, and every `ErrWorkflow*` sentinel listed in Error Semantics.

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `NewWorkflow` | function | Attaches a named dependency workflow to a scheduler. |
| `Workflow` | interface | Registers, mutates, runs, stops, and closes a DAG. |
| `WorkflowRun` | interface | Observes and cancels one execution epoch. |
| `WorkflowNode` | struct | Projects a registered node, dependencies, and scheduler job. |
| `WorkflowResult` | struct | Projects one epoch and its copied node-result map. |
| `WorkflowNodeResult` | struct | Projects one node's status, job identity, timestamps, and error. |
| `WorkflowNodeStatus` | string type | Enumerates observable per-epoch node states. |
| `WorkflowNodePending` | constant | Marks a node not yet released. |
| `WorkflowNodeRunning` | constant | Marks a released node awaiting completion. |
| `WorkflowNodeSucceeded` | constant | Marks successful task completion. |
| `WorkflowNodeFailed` | constant | Marks an execution failure. |
| `WorkflowNodeBlocked` | constant | Marks dependency-failure suppression. |
| `WorkflowNodeCanceled` | constant | Marks epoch cancellation. |
| `ErrWorkflowSchedulerRequired` | error | Reports missing scheduler construction input. |
| `ErrWorkflowNameRequired` | error | Reports an empty workflow name. |
| `ErrWorkflowNodeNameRequired` | error | Reports an empty node name. |
| `ErrWorkflowNodeExists` | error | Reports duplicate node registration. |
| `ErrWorkflowNodeNotFound` | error | Reports an absent mutation target. |
| `ErrWorkflowDependencyNotFound` | error | Reports an absent dependency. |
| `ErrWorkflowCycle` | error | Reports a cyclic graph mutation. |
| `ErrWorkflowNodeHasDependents` | error | Reports unsafe removal of a referenced node. |
| `ErrWorkflowEmpty` | error | Reports a run request with no nodes. |
| `ErrWorkflowBusy` | error | Reports graph mutation during an active epoch. |
| `ErrWorkflowClosed` | error | Reports use after workflow shutdown. |
| `ErrWorkflowSchedulerStopped` | error | Reports a run request before scheduler start. |
| `ErrWorkflowFailed` | error | Reports a terminal epoch containing failure. |
| `ErrWorkflowDependencyFailed` | error | Explains a blocked descendant result. |

### CLI Entry Points

There is no console script for this package. Programmatic use is through Go imports.

## Appendix A: Environment

The working environment runs Go 1.22 or newer on Linux without network access during assessment. The module already declares its retained dependencies, including `github.com/google/uuid`, `github.com/jonboulle/clockwork`, and `github.com/robfig/cron/v3`. The project must keep a valid `go.mod` at the module root, and all required modules must be available before offline execution begins.

## Appendix B: Assessment Notes

Behavior is checked through independent calls covering graph validation, lifecycle transitions, task invocation, errors, copying, and epoch state. Integrated workflows cover chains, forks, diamonds, overlapping epochs, listener and locker outcomes, scheduler limits, update/removal identity, cancellation, and shutdown. Each named test contributes one result; task timing is bounded to prevent a stalled implementation from blocking the suite.
