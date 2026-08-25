# Astroid analysis graphs and durable workflows

## Overview

Astroid builds rich Python analysis graphs. It parses source into nodes with
parent, scope, local-binding, rendering, and inference views, and its manager
builds and caches modules. This distribution also provides
`astroid.workflow`, a local durable workflow layer for analysis pipelines that
must survive interruption between planning, inference, artifact publication,
and reporting.

The workflow layer uses ordinary directories and JSON state. It requires no
network service. Public records are immutable dataclasses; mappings are
normalized into deterministic tuples, text artifacts are encoded as UTF-8,
and binary artifacts retain their exact bytes.

## Core analysis behavior

`astroid.parse(code, module_name="", path=None, apply_transforms=True)` dedents
and parses one module. The returned `Module` preserves the requested name and
path, statement order, source positions, parent/frame relations, local
bindings, and source-like rendering. Invalid Python raises
`AstroidSyntaxError`.

`astroid.extract_node(code, module_name="")` returns the node or nodes marked
for extraction. Node lookup follows lexical ownership, while `infer()` yields
Astroid values for supported expressions. Module `public_names()`,
`wildcard_import_names()`, `getattr()`, and `igetattr()` are consistent with
the module's local bindings. `AstroidManager.ast_from_string()` and
`ast_from_module_name()` participate in the manager cache when caching is
enabled.

Resolution error synonyms retain identity: `UnresolvableName` is
`NameInferenceError`, and `NotFoundError` is `AttributeInferenceError`.

## Durable records and failures

`astroid.workflow` exports `WorkflowError`, `IntegrityError`,
`OwnershipError`, `StaleGenerationError`, and `IncompleteWorkflowError`.
Operations reject an unknown receipt, a stale generation, a wrong owner, a
conflicting reuse of an operation identifier, malformed durable state, or an
incomplete transition without replacing the last committed value.

`OwnerReceipt` contains `kind`, `task`, `operation_id`, `generation`, `owner`,
`digest`, `state`, and prerequisite receipt digests. Digests cover normalized
public content and lineage. Repeating an operation identifier with identical
inputs is idempotent; reusing it for different inputs raises `WorkflowError`.

The module also exports immutable snapshots for definitions, selections,
attempts, artifacts, lifecycle obligations, and reporter batches.

## Definition catalog

`TaskDefinitionCatalog(path)` manages named analysis definitions.

- `prepare(name, definition, *, owner, operation_id)` validates and durably
  records a tentative definition, returning a prepared receipt.
- `commit(receipt)` makes that exact definition current and returns a
  `TaskDefinitionSnapshot`.
- `get(name)` returns the current committed snapshot.
- `recover(operation_id, *, owner)` returns the durable prepared or committed
  value for that owner.

A definition may contain `deps`, an ordered sequence of other definition
names. Dependencies must exist, duplicates are rejected, and the complete
graph must remain acyclic. A prepared value is not visible through `get`.
Commits advance generations monotonically and preserve the previous committed
snapshot when validation or publication fails.

`RoutePolicyCatalog` and `RoutePolicySnapshot` are public synonyms for this
catalog and snapshot.

## Invocation selection

`SelectionPlanRegistry(path)` owns canonical dependency closures.

- `acquire(invocation_id, requested, graph, *, owner, operation_id)` returns a
  `SelectionPlan` whose `selected` names are unique and dependency ordered.
- `current(invocation_id)` returns the current plan.
- `handoff(plan, *, new_owner, operation_id)` transfers ownership and advances
  its generation.
- `release(plan, *, operation_id)` releases only the current generation.

Unknown requested names, cycles, conflicting operations, and stale owners fail
without adding unrelated definitions to the selection. `CapacityLeaseRegistry`
and `CapacityLease` are synonyms.

## Result journal

`TaskResultJournal(path)` records one analysis attempt per operation.
`begin(task, *, owner, operation_id, prerequisites=())` creates a prepared
attempt. `complete(attempt, *, result=None, values=None)` records tentative
success values, while `fail(attempt, *, category, detail="")` records terminal
failure. `acknowledge(attempt, *, owner, operation_id)` makes only a completed
attempt current. `recover()` returns the durable operation state and
`current(task)` returns the acknowledged attempt. Failure is never promoted to
current success. `ExchangeJournal` and `ExchangeAttempt` are synonyms.

## Artifact index

`TargetArtifactIndex(path)` publishes exact analysis products.
`prepare(task, targets, *, owner, operation_id, prerequisites=())` writes a
tentative manifest. `publish(receipt)` atomically makes it current.
`seal(...)` performs those two steps as one convenience operation.
`recover()` resumes a tentative publication; `current()`, `read()`, and
`verify()` expose and validate the current generation. Missing, changed, or
extra named bytes fail verification. `WireArtifactIndex` and
`WireArtifactSnapshot` are synonyms.

## Lifecycle obligations

`LifecycleObligationLedger(path)` records entered resources and required
cleanup. `open(task, setups, teardowns, *, owner, operation_id,
prerequisites=())` starts an obligation. `setup()`, `body()`, and `teardown()`
advance it. Completed setup steps are owed in reverse order; `close()` succeeds
only after a terminal body outcome and every owed teardown. `recover()`
returns the next durable state. `RetirementObligationLedger` and
`RetirementObligation` are synonyms.

## Reporter outbox

`ReporterOutbox(path)` separates event persistence from delivery.
`prepare(batch_id, events, *, owner, operation_id, prerequisites=())` creates a
prepared receipt. `publish()` makes the batch pending, `claim()` transfers one
pending batch to a delivery owner, and `acknowledge()` removes it from
`pending()`. `events()` preserves event order and normalized values across
reopen. `ExchangeEventOutbox` and `ExchangeEventBatch` are synonyms.

## Coordinated workflow

`TaskWorkflowCoordinator(path)` combines all six owners. `plan(definitions,
requested, *, invocation_id, owner, operation_id)` commits definitions and a
canonical selection but publishes no result. `execute(receipt, *, runner=None)`
records each selected task's journal state, lifecycle closure, exact artifacts,
and ordered events. A runner returns `(status, result, values, targets,
events)`. `publish(receipt, *, owner, operation_id)` verifies the closure,
acknowledges results and events, and updates current task views.

`recover(operation_id, *, owner, runner=None)` resumes the next missing phase
without duplicate publication. `handoff()` transfers only a prepared workflow
and fences its previous owner. `current(task)`, `verify(receipt)`, and
`owner_generations(task)` expose the published cross-owner closure. A failure,
corrupt receipt, missing cleanup, stale owner, or unverified artifact leaves
the previous published workflow current. `RecoverableExchangeCoordinator` is
a public synonym.

## Scope

The package does not execute arbitrary Python to make uncertain inference
definite. Workflow storage is local and process-safe for ordinary independent
reopens; it is not a distributed consensus service. No guarantee is made for
private attributes, byte-for-byte source formatting, object memory identity,
or platform-specific filesystem metadata.
