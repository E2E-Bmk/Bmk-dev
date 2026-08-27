# Go Workflows Replay Receipt Specification

# Context

## Product Overview

`go-workflows` is a Go workflow library whose client, worker, deterministic workflow runtime, activities, timers, signals, and backend history form one local durable execution. The scoped system uses the in-process backend, the pure-Go SQLite backend, and the controlled workflow tester without any external service.

The product also exposes a replay-receipt package. A `ReplayPlan` selects one workflow execution or lineage and the public projections to retain. Callers assemble a `WorkflowReceipt` observation from client state, ordered backend history, worker-visible progress, terminal result, and backend identity. `CaptureWorkflow` binds that observation to the plan and returns a detached, validated receipt whose `HistoryDigest` remains stable across deterministic replay and supported backend transfer.

## Non-Goals

- This specification does not require Temporal, Cadence, Redis, MySQL, PostgreSQL, a remote queue, or a hosted workflow service.
- This specification does not define SQL table layouts, lock-row encodings, serializer internals, goroutine schedules, or tracing exporter behavior.
- This specification does not require nondeterministic workflow code, arbitrary wall-clock reads, network activities, or process-global workers.
- This specification does not define exact diagnostic prose when public state, error category, and history agree.

# Orientation

## Concepts and Terms

A **workflow lineage** is one logical workflow identity across its current execution and continue-as-new executions. **History** is the ordered public event sequence used for deterministic replay. An **activity attempt** is one scheduled execution governed by retry policy. A **workflow timer** advances only through the workflow clock. A **signal** is a named durable input routed to a workflow channel. A **task lock** is temporary backend ownership of pending worker work. A **last-good history generation** ends after the latest complete backend publication.

## Representative Workflows

### Workflow 1: Execute, retry, signal, and replay

1. Create an isolated backend, client, and worker; register a workflow and an activity.
2. Start a workflow whose first activity attempt fails retryably, waits through a timer, then succeeds.
3. Send ordered signals while the workflow selects between its signal channel and a timer.
4. Stop the worker after history publication, start a fresh worker, and finish the same workflow without repeating recorded side effects.
5. Build a `ReplayPlan` with `NewReplayPlan`, call `CaptureWorkflow`, and validate ordered events, attempts, signals, result, and `ReceiptStatus`.

### Workflow 2: Compare backends and lifecycle boundaries

1. Run the same registered workflow against isolated in-process and SQLite backends.
2. Close and reopen SQLite while one workflow task is pending, then start a fresh worker and complete it.
3. Continue another workflow as new and follow the logical lineage to its final result.
4. Cancel a workflow with pending activity work and verify that no canceled work later completes the instance.
5. Compare `WorkflowReceipt` values with `ReceiptDiff`, excluding backend-local storage facts while retaining history and lifecycle differences.

# Behavior

## Domain 1: Deterministic History and Replay

This domain defines workflow instances, public event history, deterministic decisions, side effects, and worker restart.

**Instances and execution.** `client.New` must bind a client to one `backend.Backend`. `CreateWorkflowInstance` must create one public `workflow.WorkflowInstance` or return `backend.ErrInstanceAlreadyExists`. A registered worker must poll the selected queue, execute workflow tasks, and publish ordered history plus state atomically. `GetWorkflowInstanceState`, `WaitForWorkflowInstance`, and `GetWorkflowResult` must describe the same current execution.

**Replay.** A fresh worker must rebuild deterministic workflow state from published history and execute only decisions absent from that history. Recorded activity results, timer firings, signal deliveries, and side-effect results must not repeat their external action during replay. Workflow code using `workflow.Now`, `SideEffect`, channels, selectors, and futures must receive replay-consistent values.

**History ownership.** `Backend.GetWorkflowInstanceHistory` must return public events in durable order. Each event type and serialized attributes must agree with the client-visible transition that it represents. A failed task completion, abandoned lock, or canceled context must not publish a partial event batch. A later valid worker owner must resume from the last-good history generation.

## Domain 2: Activities, Timers, and Signals

This domain defines activity attempts, retries, workflow time, channels, selectors, and durable signal input.

**Activities and retries.** `workflow.ExecuteActivity` must schedule the registered activity with converted input and return a future. Retryable failures must append one failed attempt and schedule the next attempt according to `workflow.RetryOptions`. Permanent errors and exhausted attempts must stop retrying. The final future value or error must agree with activity attempt history and client result decoding.

**Timers.** `workflow.ScheduleTimer` and `Sleep` must wait on workflow time, not direct wall-clock reads. Cancellation before firing must prevent successful timer completion. In `tester.WorkflowTester`, `ScheduleCallback` and the controlled clock must advance deterministically to eligible deadlines. Activity retry backoff and workflow timers must retain their relative deadline order.

**Signals and channels.** `client.SignalWorkflow` must append a named signal to the selected workflow instance. `workflow.NewSignalChannel` must receive signals for that name exactly once and in publication order. Buffered and unbuffered workflow channels must preserve send/receive ordering. `workflow.Select` must choose only ready cases and must not consume a losing case.

## Domain 3: Backends and Workflow Lifecycles

This domain defines backend equivalence, SQLite recovery, continue-as-new, cancellation, locks, removal, and close.

**Backend equivalence.** The in-process and SQLite backends must support equivalent create, signal, task completion, state, result, cancellation, and removal outcomes for supported workflows. SQLite additionally must recover public history and pending tasks after close and reopen. Differences in SQL identifiers, lock bytes, and storage layout have no public meaning.

**Continue-as-new.** `workflow.ContinueAsNew` must complete the current execution and create the next execution with converted input under the same logical workflow lineage. Client waiting must follow that lineage to its terminal result. History for each execution must remain separately ordered, while the lineage projection preserves predecessor and successor ownership.

**Cancellation and lock recovery.** `client.CancelWorkflowInstance` must publish cancellation to the targeted live execution. Pending timers and activities must not later complete the canceled execution. If a worker abandons a task and its backend lock expires, a later worker must acquire and execute that task once. Removal of a finished instance must make later state and result lookup return `backend.ErrInstanceNotFound`; removal of a live instance must follow the documented error.

## Domain 4: Replay Plans and Workflow Receipts

This domain defines a product-specific coordination API over client, backend history, worker progress, and deterministic results.

**Replay plans.** `NewReplayPlan` must return an empty immutable `ReplayPlan`. `ReplayPlan.Select` must accept one `WorkflowSelection` containing nonblank instance and execution identities plus optional lineage traversal. `IncludeHistory`, `IncludeAttempts`, `IncludeSignals`, `IncludeTimers`, and `IncludeResult` must return updated plans without changing preceding plan values. Invalid selection must return an error and retain the preceding plan.

**Capture.** `CaptureWorkflow` accepts a plan and a caller-owned observation. It must reject an unselected plan, attach an independent copy of the plan, copy every slice-backed projection, validate the result, and return the detached `WorkflowReceipt`. Later mutation of the plan input or observation storage must not change the captured value. `BackendProjection` may describe the producing backend, but its kind, path, and process identity are local facts rather than workflow semantics.

**Validation and digest.** A receipt must carry a selected plan and a positive stable generation. History event identities use the ordered `event-NNN` receipt sequence and must be nonempty, unique, and contiguous. Activity attempts start at one and remain contiguous; timer values are nonnegative and nondecreasing; signal names and lineage execution identities are nonblank and unique. Status is running, completed, or cancelled. A completed receipt that selects its result must contain one, while a cancelled receipt must retain neither a completion result nor a task lock. `HistoryDigest` must cover the selection, normalized events, attempts, timers, signals, lineage, terminal state, generation, and result while ignoring backend-local identity.

**Comparison.** `ReceiptDiff` must compare two valid receipts by selected workflow semantics. Deterministically replayed receipts before and after worker restart must compare equal. Supported in-process and SQLite executions with the same logical decisions must compare equal when backend identity is excluded by plan. A retry-count, signal-order, timer, cancellation, continuation, result, or history change selected by the plan must produce a nonempty diff.

# Contract

## State Model

A workflow execution is **created**, **active**, **continued**, **completed**, **failed**, **canceled**, or **removed**. A workflow or activity task is **pending**, **locked**, **completed**, **abandoned**, or **recovered**. An activity attempt is **scheduled**, **running**, **failed-retryable**, **failed-terminal**, or **completed**. A timer is **scheduled**, **fired**, or **canceled**. A signal is **published**, **recorded**, or **consumed**. A receipt is **captured**, **valid**, or **invalid**.

Backend publication advances only by complete event and state transitions. Replay consumes published history without republishing completed actions. Continue-as-new closes one execution and creates its successor. Cancellation prevents later success publication for canceled pending work. A receipt remains detached from later backend progress.

## Error Semantics

| Condition | Required result |
|---|---|
| Workflow instance already exists | Creation must return `backend.ErrInstanceAlreadyExists` without replacing history. |
| Workflow instance is absent or removed | State, result, signal, or cancellation must return `backend.ErrInstanceNotFound`. |
| Activity error is permanent or attempts are exhausted | Retry must stop and the future must expose the terminal error. |
| Worker task lock expires | A later worker must recover last-good history without duplicate completion. |
| Workflow is canceled | Pending work must not publish a successful terminal result. |
| Backend closes or SQLite reopen fails | Operations must return an error without inventing a complete history generation. |
| Replay plan is invalid | The plan operation must return an error and retain the preceding immutable plan. |
| Receipt history or lifecycle is inconsistent | `WorkflowReceipt.Validate` must return an error without backend effects. |

## Cross-View Invariants

1. Backend history, instance state, worker progress, client waiting, and decoded result must describe one complete execution generation.
2. Replay must reproduce recorded decisions without repeating completed activities, side effects, timers, or signal consumption.
3. Activity attempt history, retry policy, timer backoff, future completion, and final result must share one attempt lineage.
4. Signal publication order, history order, workflow channel delivery, selector choice, and receipt order must agree.
5. In-process and SQLite backends must expose equivalent supported lifecycle results; SQLite reopen must retain public durable state.
6. Continue-as-new input, predecessor completion, successor identity, lineage waiting, and terminal receipt must reconcile.
7. Cancellation, abandoned-lock recovery, pending task state, later worker execution, and terminal state must prevent duplicate completion.
8. A valid `WorkflowReceipt` must bind one immutable plan to one stable public history generation and remain detached from later progress.
9. `HistoryDigest` and `ReceiptDiff` must preserve plan-selected workflow semantics while excluding backend-local nondeterminism.

# Reference

## Public Interface

### Import Surface

- `github.com/cschleiden/go-workflows/backend`: `Backend`, `ActivityTask`, `WorkflowTask`, `Stats`, `ErrInstanceAlreadyExists`, `ErrInstanceNotFound`, `ErrInstanceNotFinished`
- `github.com/cschleiden/go-workflows/backend/monoprocess`: `NewMonoprocessBackend`
- `github.com/cschleiden/go-workflows/backend/sqlite`: `NewInMemoryBackend`, `NewSqliteBackend`, `NewSqliteBackendWithDB`
- `github.com/cschleiden/go-workflows/client`: `Client`, `New`, `WorkflowInstanceOptions`
- `github.com/cschleiden/go-workflows/worker`: `Worker`, `New`, `RegisterWorkflow`, `RegisterActivity`
- `github.com/cschleiden/go-workflows/workflow`: `WorkflowInstance`, `ExecuteActivity`, `RetryOptions`, `ScheduleTimer`, `Sleep`, `NewSignalChannel`, `NewChannel`, `Select`, `SideEffect`, `ContinueAsNew`
- `github.com/cschleiden/go-workflows/tester`: `WorkflowTester`, `NewWorkflowTester`, `ScheduleCallback`
- `github.com/cschleiden/go-workflows/receipt`: `ReplayPlan`, `NewReplayPlan`, `WorkflowSelection`, `WorkflowReceipt`, `CaptureWorkflow`, `HistoryDigest`, `ReceiptDiff`, `ReceiptStatus`, `BackendProjection`

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Backend`, `ActivityTask`, `WorkflowTask`, `Stats` | interface and types | Own durable workflow history, tasks, locks, state, and backend statistics. |
| Public backend `Err...` values | error values | Distinguish duplicate, absent, and live-instance lifecycle errors. |
| `NewMonoprocessBackend`, SQLite constructors | functions | Create isolated in-process or SQLite backend implementations. |
| `Client`, `client.New`, `WorkflowInstanceOptions` | type and functions | Create, signal, cancel, wait for, inspect, and remove workflow instances. |
| `Worker`, `worker.New`, registration functions | type and functions | Register and execute workflow and activity tasks. |
| Workflow execution functions and types | functions and types | Express deterministic activities, retries, timers, channels, signals, selectors, side effects, and continuation. |
| `WorkflowTester`, `NewWorkflowTester`, `ScheduleCallback` | type and functions | Run workflows with a controlled local clock and callbacks. |
| `ReplayPlan`, `NewReplayPlan` | type and function | Build an immutable workflow lineage and projection plan. |
| `WorkflowSelection` | type | Identifies an execution and optional continue-as-new lineage traversal. |
| `CaptureWorkflow` | function | Binds a plan to a detached, validated public workflow observation. |
| `WorkflowReceipt`, `ReceiptStatus` | types | Store normalized history, attempts, signals, timers, result, and terminal state. |
| `BackendProjection` | type | Describes supported backend semantics without private storage identity. |
| `HistoryDigest` | function | Digests selected normalized workflow history semantics. |
| `ReceiptDiff` | function | Compares two valid workflow receipts under their plan. |

### CLI Entry Points

There is no command-line entry point for the scoped package. Programmatic use is through the Go import paths listed above.
