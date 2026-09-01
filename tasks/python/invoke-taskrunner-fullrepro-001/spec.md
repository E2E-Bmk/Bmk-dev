# Invoke task runner with recoverable task-state workflows

Implement a source-only Python package named `invoke`. It provides the public
Invoke 3.0.3 task-runner surface together with a durable workflow API for
callers that coordinate task generations across process restarts. Filesystem
state is deterministic UTF-8 data and is safe to reopen from a fresh Python
process.

## Existing public task-runner surface

The package root exports `Task`, `Call`, `task`, `call`, `Collection`,
`Config`, `Context`, `Executor`, `Runner`, `Result`, `Program`, and
`ParseResult`. `ParseResult` is deliberately part of the root contract: code
must not need a private parser import to construct the parser result passed to
`Call.make_context`. The package reports version `3.0.3` and supports
`python -m invoke`.

`@task` preserves the decorated function's name and documentation, requires a
`Context` first argument, and supports declared names, aliases, defaults,
positional arguments, optional-value flags, iterable values, incrementable
flags, and pre/post tasks. `call(task, *args, **kwargs)` creates a `Call` that
retains task identity and arguments. Cloning a call changes only explicitly
replaced fields. A call creates a Context using the supplied Config and a
parser result's remainder.

A `Collection` resolves primary task names, aliases, defaults, nested
collections and per-collection configuration to the same logical task.
Configuration merges nested mappings without losing lower-precedence sibling
keys; cloned configuration and per-execution Context values are detached from
later executions.

`Executor` expands pre/post dependencies, deduplicates the same call under the
active policy, excludes unrelated branches, and creates the correctly scoped
Context for each selected task. `Program` accepts string or argument-list
forms and projects the same Collection through listing, aliases, defaults and
task dispatch. A handled task or parser failure does not corrupt reusable
Collection or Config state.

## Durable workflow records

`invoke.workflow` exports `WorkflowError`, `IntegrityError`, `OwnershipError`,
`StaleGenerationError`, and `IncompleteWorkflowError`. It also exports
immutable value records `OwnerReceipt`, `TaskDefinitionSnapshot`,
`SelectionPlan`, `TaskAttempt`, `TargetSnapshot`, `LifecycleObligation`, and
`PublicationBatch`. Returned mappings and sequences are detached snapshots.

Every `OwnerReceipt` exposes `kind`, `task`, `operation_id`, `generation`,
`owner`, `digest`, `state`, and immutable prerequisite identities. Its digest
binds the complete semantic record and dependency set. Reads reject missing
fields, altered records, unknown prerequisites, duplicate owners, cycles and
digest mismatches with `IntegrityError`, without changing current state.

## Definition revisions

`TaskDefinitionCatalog(path)` owns normalized task definitions and graph
revisions. `prepare(name, definition, *, owner, operation_id)` creates or
resumes an invisible operation. `commit(receipt)` publishes a new
`TaskDefinitionSnapshot`; `get(name)` returns the current snapshot, and
`recover(operation_id, *, owner)` resumes prepared or committed work.
Equivalent operation replay is idempotent. Conflicting operation reuse,
duplicate targets, unresolved required dependencies and graph cycles fail
atomically. A rejected revision never replaces the last runnable one.

## Invocation-local selection plans

`SelectionPlanRegistry(path)` owns monotonic invocation generations.
`acquire(invocation_id, requested, graph, *, owner, operation_id)` resolves a
deduplicated canonical dependency closure and returns a `SelectionPlan`.
`handoff(plan, *, new_owner, operation_id)` transfers prepared work without
changing the closure; `release(plan, *, operation_id)` closes it.
`current(invocation_id)` and `recover(operation_id, *, owner)` return detached
state. Every mutation validates the exact owner and generation. Stale owners
raise `StaleGenerationError`. Plans never inherit a prior invocation's
selection merely because both use the same task catalog.

## Task result journal

`TaskResultJournal(path)` owns transactional attempts. `begin(task, *, owner,
operation_id, prerequisites=())` returns a prepared `TaskAttempt`.
`complete(attempt, *, result=None, values=None)` records terminal success;
`fail(attempt, *, category, detail="")` records failure or error;
`acknowledge(receipt, *, owner, operation_id)` publishes only a successful
terminal attempt. `current(task)` returns the last acknowledged task result,
and `recover(operation_id, *, owner)` resumes prepared,
completed-unacknowledged, failed, or acknowledged work. Result/value and
freshness state become visible together. A failed attempt cannot preserve or
publish a tentative replacement value.

## Target artifacts

`TargetArtifactIndex(path)` owns immutable exact-byte task targets.
`prepare(task, targets, *, owner, operation_id, prerequisites=())` records an
invisible mapping from target paths to bytes or UTF-8 text. `publish(receipt)`
atomically returns a `TargetSnapshot`; `seal(...)` performs both phases.
`read(task, target)`, `verify(snapshot)`, `current(task)`, and
`recover(operation_id, *, owner)` expose verified detached state. Equivalent
content converges. No current manifest may name absent or partial content,
and corruption fails before success publication.

## Lifecycle obligations

`LifecycleObligationLedger(path)` owns setup/body/teardown progress.
`open(task, setups, teardowns, *, owner, operation_id, prerequisites=())`
returns a prepared `LifecycleObligation`. `setup(obligation, name)`,
`body(obligation, outcome)`, and `teardown(obligation, name)` record ordered
progress. Only setup frames that actually ran are owed; teardown order is the
reverse of setup order. `close(obligation)` closes a fully discharged
success or failure, while `recover(operation_id, *, owner)` exposes the next
owed action. Fresh invocation stacks do not reuse in-memory frames.

## Reporter publication

`ReporterOutbox(path)` owns ordered, exactly-once observable events.
`prepare(batch_id, events, *, owner, operation_id, prerequisites=())` creates
an invisible `PublicationBatch`; `publish(receipt)` makes it pending.
`claim(batch_id, *, owner, operation_id)` transfers pending delivery to one
owner, `acknowledge(batch, *, owner, operation_id)` closes it, and
`recover(operation_id, *, owner)` resumes prepared, published, claimed or
acknowledged work. `pending()` and `events(batch_id)` are detached views.
Failed delivery preserves pending events; acknowledged event identities are
not emitted again. Stale publishers cannot claim or acknowledge.

## Cross-owner task workflow

`TaskWorkflowCoordinator(path)` composes the six owners without replacing
their independent state. `plan(definitions, requested, *, invocation_id,
owner, operation_id)` returns a prepared workflow receipt.
`execute(receipt, *, runner=None)` runs or simulates the selected canonical
tasks and records target and lifecycle results. A runner callable may return
an integer status or `(status, result, values, targets, events)`.
`publish(receipt, *, owner, operation_id)` publishes only a complete success,
and `recover(operation_id, *, owner, runner=None)` resumes interrupted work.
`handoff(operation_id, *, current_owner, new_owner,
transfer_operation_id)` transfers prepared work. `current(task)` returns the
last acknowledged task workflow, `verify(receipt)` validates reachable
receipt closure, and `owner_generations(task)` reports the six represented
owner generations.

A successful generation has an acyclic closure reaching its committed
definition revision, current selection, acknowledged result, verified target
snapshot, discharged lifecycle and acknowledged reporter batch. Failure or
corruption preserves the previous acknowledged generation. Completion before
acknowledgement is recoverable exactly once. Equivalent concurrent operations
converge; conflicting operations have one winner and no loser partial state.

The implementation must not use the network, sleeps, wall-clock races,
process-ID ownership, platform-specific process discovery, hidden evaluator
knowledge, or delegation to another installed `invoke` package.
