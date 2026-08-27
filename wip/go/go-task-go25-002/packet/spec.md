# Task Execution Receipt Specification

# Context

## Product Overview

`task` is a Go package and local command runner that discovers Taskfiles, compiles includes and variables into a dependency graph, executes commands and deferred commands, evaluates status conditions, and persists successful source fingerprints. The scoped system reads only local Taskfiles and runs deterministic local commands in caller-owned directories.

The product also exposes an execution-receipt extension. A `ReceiptPlan` selects a task, variable inputs, execution mode, and observation boundaries. `CaptureRun` executes that plan through an `Executor` and returns a `RunReceipt` whose ordered `ReceiptEvent` values reconcile compiled task identity, command outcomes, workspace changes, and cache publication.

## Non-Goals

- This specification does not require remote Taskfiles, update checks, telemetry, network commands, or a long-running service.
- This specification does not define YAML decoder internals, template implementation details, cache-file bytes, goroutine schedules, or shell process internals.
- This specification does not require Make, another task runner, containers, remote caches, or globally installed helper programs.
- This specification does not define exact diagnostic prose when the documented error category and exit status agree.

# Orientation

## Concepts and Terms

A **compiled task identity** is the namespaced name produced after local discovery and include composition. A **variable frame** is one precedence layer contributing values before template expansion. A **task call** is one scheduled invocation with its own variable frame. A **successful fingerprint** records that selected sources, generated targets, status commands, and a completed task agree. A **last-good cache generation** is the fingerprint state after the latest successful non-dry execution. A **receipt plan** is an immutable description of one requested run and its observations.

## Typical Use

Applications configure an `Executor` for a local Taskfile, build an immutable
`ReceiptPlan`, and call `CaptureRun` when they need a detached account of a task
execution. Plans may select variables, dry rendering, workspace paths, and status
observations. The resulting receipt is suitable for logging, comparison, and
cache-aware orchestration without exposing private compiler or scheduler state.

Receipts are especially useful when a workflow spans included Taskfiles,
dependency calls, conditions, deferred cleanup, and freshness decisions. The same
model applies to ordinary completion, current-task skips, dry rendering, and
failures; consumers can compare any two valid receipts with `ReceiptDiff`.

# Behavior

## Domain 1: Taskfile Composition and Variable Frames

This domain defines local discovery, includes, namespace ownership, task selection, variable precedence, and template expansion.

**Discovery and includes.** `Executor` must resolve an explicitly selected Taskfile or discover the nearest supported local Taskfile from its working directory. Required local includes must resolve relative to their declaring Taskfile; a missing required include must return an error. A missing optional include must contribute no tasks. Namespaced includes must prefix their task names, flattened includes must contribute unprefixed names, and collisions must return an error instead of silently replacing a task. Included tasks must retain their included directory for commands and sources.

**Variables and templates.** Variable resolution must apply command-line, task-call, task, include, root, environment, and default frames in documented precedence order. Dynamic variables must execute only when their value is demanded and must feed the same template frame as static values. Template expansion must preserve a variable's selected value across command, source, generated, status, and precondition fields. Missing required variables or failed dynamic variables must return an error before the affected command runs.

**Selection.** `Call` and `TaskSelection` must identify one compiled task by its final namespaced name and arguments. An unknown task must return an error without executing another task. Listing and summary projections must describe the same compiled identities and dependencies used by execution.

## Domain 2: Dependency, Command, and Failure Lifecycles

This domain defines graph scheduling, task-call frames, commands, deferred commands, status gates, and failure ownership.

**Dependency scheduling.** Dependencies must complete before their parent command sequence. One shared dependency node with the same effective call frame must execute once within one run. Distinct task-call frames must remain distinct executions. A skipped dependency counts as successfully satisfied; a failed dependency prevents its dependent parent command from starting. Cycles must return an error before any cyclic command publishes effects.

**Commands and defers.** Ordinary commands must run in declaration order using the selected working directory, environment, and streams. Deferred commands registered by a started task must run in reverse registration order after ordinary success or failure. An ignored command error must remain visible in its event while permitting the sequence to continue. A nonignored command error must determine the run failure even when a later deferred command also fails.

**Conditions and modes.** Preconditions must run before the gated command and must return `ErrPreconditionFailed` on failure. Status commands and source fingerprints must jointly decide whether a task is current. Dry mode must render the selected graph and commands without running commands, changing caller files, or publishing successful fingerprints. Silent mode must suppress command echo while retaining command output.

## Domain 3: Sources, Generated Files, and Fingerprints

This domain defines freshness decisions and publication of isolated successful cache state.

**Source observations.** Source globs must resolve below the task's effective directory. Checksum mode must change when selected source bytes or selected generated-file existence changes. Timestamp mode must compare the latest selected source with the earliest selected generated target under stable filesystem timestamps. Empty required source or generated selections must follow the declared task policy rather than reuse an unrelated cache entry.

**Cache ownership.** Cache keys must include the compiled task identity and relevant call frame so included or differently parameterized tasks do not collide. Only a successful non-dry task must publish a new fingerprint. A failed command, failed deferred command, failed precondition, dry run, or incomplete generated output must retain the preceding successful fingerprint.

**Fresh process behavior.** A later process using the same isolated cache and workspace must reach the same current/stale decision from public sources, generated files, status commands, and successful fingerprint state. Editing a source, deleting a generated target, or changing a cache-owning task identity must invalidate the appropriate task without invalidating unrelated tasks.

## Domain 4: Execution Plans and Run Receipts

This domain defines the product-specific API that coordinates one Task execution with stable plan-visible evidence.

**Receipt plans.** `NewReceiptPlan` must return an empty immutable `ReceiptPlan`. `ReceiptPlan.Select` must accept one `TaskSelection`; `WithVariables`, `WithDryRun`, `ObserveWorkspace`, and `ObserveStatus` must return updated plans without modifying earlier values. Observation names must be nonempty and unique. Repeating a name must replace its selector without changing plan order. Invalid task names, variable names, or observation paths must return an error and retain the prior plan.

**Capture.** `CaptureRun` must apply a plan to the supplied `Executor` as one run. It must capture the final compiled task identity, normalized variable frame, dependency and command events, deferred events, exit ownership, status decision, selected workspace digests, and fingerprint publication into one `RunReceipt`. Receipt bytes, maps, and slices must be caller-owned. Events must use deterministic dependency-respecting order; parallel siblings with no ordering relation must be normalized by compiled task identity.

**Receipt status and validation.** `ReceiptStatus` must distinguish completed, skipped-current, rendered-dry, failed-precondition, failed-command, and failed-deferred outcomes. `RunReceipt.Validate` must reject missing parents, duplicate event identities, impossible lifecycle order, workspace publication during dry mode, successful fingerprint publication after failure, or a terminal status inconsistent with events. Validation must not execute commands or read current workspace state.

The corresponding status constants are `ReceiptCompleted`, `ReceiptSkippedCurrent`, `ReceiptRenderedDry`, `ReceiptFailedPrecondition`, `ReceiptFailedCommand`, and `ReceiptFailedDeferred`. A receipt exposes `Task`, `Variables`, ordered `Events`, named `Workspace` digests, `Status`, and `Fingerprint`. Each `ReceiptEvent` exposes `ID`, `Parent`, `Kind`, `Task`, `Value`, and `Outcome`; event kinds are `task`, `dependency`, `command`, `defer`, and `status`, and outcomes use the lifecycle terms defined by the State Model.

**Comparison.** `ReceiptDiff` must compare two valid receipts by plan-visible compiled identities, variable values, event outcomes, workspace digests, status decisions, and fingerprint digests. It must ignore temporary directory prefixes, process identifiers, wall-clock timestamps, and unordered sibling scheduling. Equal successful receipts across fresh processes must produce an empty diff; a source edit, variable change, failure, or dry-mode change affecting the plan must produce a nonempty diff.

# Contract

## State Model

An executor is **configured**, **compiling**, **running**, or **finished** for one call. A task is **pending**, **skipped-current**, **running**, **failed**, or **completed**. A command event is **planned**, **started**, **failed**, **ignored**, **completed**, or **deferred**. A fingerprint is **absent**, **current**, **stale**, or **published**. A receipt plan is immutable, and a receipt is **captured**, **valid**, or **invalid**.

Failed compilation starts no commands. Failed dependencies prevent parent execution. Started tasks unwind registered defers. Only completed non-dry tasks advance successful fingerprint state. Each `CaptureRun` returns a fresh receipt detached from later executor, filesystem, and cache changes.

## Error Semantics

| Condition | Required result |
|---|---|
| Taskfile is missing, malformed, or has an include collision | Compilation must return an error and start no command. |
| Required include, task, or variable is missing | The request must return an error without substituting another identity. |
| Dependency cycle exists | Scheduling must return an error before cyclic commands run. |
| Precondition fails | The task must return `ErrPreconditionFailed`, run no gated command, and publish no fingerprint. |
| Nonignored command fails | The run must retain that failure status, unwind registered defers, and publish no successful fingerprint. |
| Dry run is requested | The run must return rendered events with no command, workspace, or cache publication. |
| Receipt plan contains an invalid selector | The plan operation must return an error and retain the preceding immutable plan. |
| Receipt event graph or terminal status is inconsistent | `RunReceipt.Validate` must return an error without external effects. |

## Cross-View Invariants

1. Discovery, task listing, summaries, dependency selection, and `RunReceipt` identities must describe the same compiled task registry.
2. Variable precedence, template expansion, task-call frames, command environment, and receipt variables must agree for every executed task.
3. Dependency events, command effects, deferred events, and exit status must form one dependency-respecting lifecycle.
4. Status commands, source observations, generated files, skip decisions, and successful fingerprints must agree across fresh processes.
5. A failed or dry run must leave workspace and last-good successful fingerprint projections unchanged.
6. Namespaced and flattened includes must preserve task identity, effective directory, cache ownership, and receipt identity without collisions.
7. A valid `RunReceipt` must bind one immutable plan to one execution and must remain unchanged after later workspace or cache changes.
8. `ReceiptDiff` must report every plan-visible semantic change and must ignore process-local nondeterminism.

# Reference

## Public Interface

### Import Surface

- `github.com/go-task/task/v3`: `Executor`, `ExecutorOption`, `NewExecutor`, `TempDir`, `WithDir`, `WithEntrypoint`, `WithTempDir`, `WithOffline`, `WithVersionCheck`, `WithStdin`, `WithStdout`, `WithStderr`, `WithDry`, `WithSilent`, `WithVerbose`, `WithSummary`, `Call`, `Setup`, `Run`, `RunTask`, `Status`, `GetTaskList`, `ListOptions`, `NewListOptions`, `ListTasks`, `ListTaskNames`, `ErrPreconditionFailed`, `ReceiptPlan`, `NewReceiptPlan`, `TaskSelection`, `RunReceipt`, `CaptureRun`, `ReceiptDiff`, `ReceiptEvent`, `ReceiptStatus`, `ReceiptCompleted`, `ReceiptSkippedCurrent`, `ReceiptRenderedDry`, `ReceiptFailedPrecondition`, `ReceiptFailedCommand`, `ReceiptFailedDeferred`
- `github.com/go-task/task/v3/taskfile/ast`: `Taskfile`, `Task`, `Cmd`, `Dep`, `Include`, `Vars`, `NewVars`, `Vars.Set`, `Var`, `Precondition`

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Executor`, `ExecutorOption`, `NewExecutor`, `TempDir` | types and function | Configure one local Taskfile executor and its isolated fingerprint and remote temporary directories. |
| `TempDir.Remote`, `TempDir.Fingerprint` | fields | Bind remote-include and fingerprint state to caller-owned isolated directories. |
| `WithDir`, `WithEntrypoint`, `WithTempDir`, `WithOffline`, `WithVersionCheck` | option functions | Select local discovery, explicit Taskfile, isolated cache roots, offline mode, and disabled version checks. |
| `WithStdin`, `WithStdout`, `WithStderr`, `WithDry`, `WithSilent`, `WithVerbose`, `WithSummary` | option functions | Configure caller-owned streams and documented execution/reporting modes. |
| `Call`, `Setup`, `Run`, `RunTask`, `Status` | type, method, and functions | Compile, select, execute, or inspect a compiled task. |
| `Call.Task`, `Call.Vars` | fields | Select the public task identity and explicit variable frame for one call. |
| `GetTaskList`, `ListOptions`, `NewListOptions`, `ListTasks`, `ListTaskNames` | methods, type, and function | Project the compiled registry for human and JSON listings and summaries. |
| `ErrPreconditionFailed` | error value | Identifies a failed precondition boundary. |
| `Taskfile`, `Task`, `Cmd`, `Dep`, `Include` | types | Describe Taskfile composition and graph declarations. |
| `Vars`, `NewVars`, `Vars.Set`, `Var`, `Precondition` | types, function, and method | Construct explicit task-call variable frames and execution gates. |
| `Var.Value` | field | Supplies a detached public scalar value to a task-call variable frame. |
| `ReceiptPlan`, `NewReceiptPlan` | type and function | Build an immutable task execution and observation plan. |
| `ReceiptPlan.Select`, `WithVariables`, `WithDryRun`, `ObserveWorkspace`, `ObserveStatus` | methods | Select a task, overlay run variables, choose dry mode, and add ordered named observations. |
| `TaskSelection.Name`, `TaskSelection.Variables` | fields | Select one final compiled identity and its call-variable frame. |
| `CaptureRun` | function | Executes one plan and returns a detached run receipt. |
| `RunReceipt.Task`, `Variables`, `Events`, `Workspace`, `Status`, `Fingerprint` | fields | Record normalized task, variable, event, workspace, terminal, and last-good cache projections. |
| `RunReceipt.Validate`, `RunReceipt.Digest` | methods | Validate detached cross-view consistency and derive deterministic semantic identity. |
| `ReceiptEvent.ID`, `Parent`, `Kind`, `Task`, `Value`, `Outcome` | fields | Record one uniquely owned dependency, command, defer, task, or status lifecycle event. |
| `ReceiptStatus`, `ReceiptCompleted`, `ReceiptSkippedCurrent`, `ReceiptRenderedDry`, `ReceiptFailedPrecondition`, `ReceiptFailedCommand`, `ReceiptFailedDeferred` | type and constants | Classify the terminal run outcome without relying on diagnostic wording. |
| `ReceiptDiff` | function | Returns an empty string slice for equivalent valid receipts and a nonempty semantic-category slice for plan-visible differences. |

### CLI Entry Points

The `task` command accepts local Taskfile selection, task names, variables, list, summary, status, dry-run, silent, directory, and offline options. CLI behavior and the Go receipt API must share the same compiled graph and execution owners.

# Environment

The supported environment is Linux amd64 with a Go 1.25 toolchain and an offline,
preloaded module closure. Each process receives isolated working, cache, home, and
temporary directories. The module path remains `github.com/go-task/task/v3`, and
the locally built `task` command is the only task runner available.
