# Kedro Local Pipelines and Durable Run State

## Scope

Implement a Python package named `kedro` that provides local pipeline composition, in-memory data handling, configuration loading, sequential execution, and durable run-state coordination. All behavior is local and deterministic. Network services, telemetry, parallel scheduling, distributed locks, cloud storage, notebook support, and plugin discovery are outside this contract.

The durable API stores its state beneath a caller-supplied directory. A new object opened on the same directory must observe committed state written by an earlier object. Public values returned by the API are immutable value records.

## Pipeline surface

The following canonical imports are required:

```python
from kedro.pipeline import Node, Pipeline, node, pipeline
from kedro.pipeline.pipeline import OutputNotUniqueError, CircularDependencyError
from kedro.io import DataCatalog, MemoryDataset, DatasetError, DatasetNotFoundError
from kedro.config import OmegaConfigLoader
from kedro.runner import SequentialRunner
```

`node(func, inputs, outputs, *, name=None, tags=None, confirms=None, namespace=None, preview_fn=None)` creates a `Node`. Inputs may be one dataset name, an ordered list of names, or a mapping from callable argument names to dataset names. Outputs may be absent, one name, an ordered list, or a mapping from returned keys to dataset names. `Node.run()` binds values according to that declaration and returns a name-to-value mapping.

`Pipeline` orders nodes by dataset dependency. Its `inputs()`, `outputs()`, `datasets()`, and `node_dependencies` views must agree with that order. Duplicate produced names raise `OutputNotUniqueError`; cycles raise `CircularDependencyError`. Selection by tags and namespace creates a new graph. The `pipeline()` factory may apply a namespace while explicitly exposed inputs and parameter names remain external.

`DataCatalog` is a mutable registry of datasets. Raw assignment wraps the value in `MemoryDataset`; reassignment replaces the former dataset. Named load, save, release, and existence operations share the same registry view. Missing required names raise `DatasetNotFoundError`. A memory dataset supports `deepcopy`, `copy`, and `assign` modes; release restores its empty state and an empty load raises `DatasetError`.

`OmegaConfigLoader` reads YAML, YML, and JSON configuration from a base environment and an optional selected environment. Runtime parameters merge last. `DataCatalog.from_config()` materializes catalog declarations. `SequentialRunner.run()` loads free inputs, executes the selected graph topologically, saves produced values into the same catalog, propagates execution failures, and returns terminal dataset objects under the pipeline output names.

## Durable run-state imports

The module `kedro.run_state` exports:

```python
from kedro.run_state import (
    WorkflowError, IntegrityError, OwnershipError,
    StaleGenerationError, IncompleteWorkflowError,
    OwnerReceipt, TaskDefinitionSnapshot, SelectionPlan, TaskAttempt,
    TargetSnapshot, LifecycleObligation, PublicationBatch,
    TaskDefinitionCatalog, SelectionPlanRegistry, TaskResultJournal,
    TargetArtifactIndex, LifecycleObligationLedger, ReporterOutbox,
    TaskWorkflowCoordinator,
)
```

The five error classes form a public hierarchy: the latter four derive from `WorkflowError`, and `StaleGenerationError` also derives from `OwnershipError`.

Every durable component accepts `path` as its first constructor argument. Mutating operations accept a caller-chosen `operation_id`. Reusing that identity with the same logical request returns the previously stored value; reusing it for a different request raises `WorkflowError`. State-changing records carry `owner`, `generation`, `state`, and a receipt. Generations are monotonic per logical entity. Receipts carry `kind`, `task`, `operation_id`, `generation`, `owner`, `digest`, `state`, and an ordered tuple of prerequisite digests. Their digest is deterministic for their complete logical content.

## Definitions and selections

`TaskDefinitionCatalog` provides:

```text
prepare(name, definition, *, owner, operation_id) -> OwnerReceipt
commit(receipt) -> TaskDefinitionSnapshot
get(name) -> TaskDefinitionSnapshot
recover(operation_id, *, owner) -> OwnerReceipt | TaskDefinitionSnapshot
```

A definition is a mapping and may declare ordered `deps` and `artifacts` name sequences. Preparation is not visibility: `get()` continues to expose the last committed revision. Commitment atomically publishes one immutable snapshot. Dependency names must refer to committed definitions or to the definition being revised; self-dependency, missing parents, cycles, repeated dependencies, and repeated artifact names are invalid. An invalid revision never replaces the prior committed value.

`SelectionPlanRegistry` provides:

```text
acquire(invocation_id, requested, graph, *, owner, operation_id) -> SelectionPlan
handoff(plan, *, new_owner, operation_id) -> SelectionPlan
release(plan, *, operation_id) -> SelectionPlan
current(invocation_id) -> SelectionPlan
recover(operation_id, *, owner) -> SelectionPlan
```

Acquisition computes a deterministic, dependency-before-dependent closure of the requested names, removes duplicate reachability, and includes no unrelated name. Unknown names and cycles are invalid. Handoff preserves the closure but transfers ownership. Once ownership changes, a stale plan cannot release or replace the current plan.

## Results and targets

`TaskResultJournal` provides:

```text
begin(task, *, owner, operation_id, prerequisites=()) -> TaskAttempt
complete(attempt, *, result=None, values=None) -> TaskAttempt
fail(attempt, *, category, detail="") -> TaskAttempt
acknowledge(attempt_or_receipt, *, owner, operation_id) -> TaskAttempt
current(task) -> TaskAttempt
recover(operation_id, *, owner) -> TaskAttempt
```

An attempt begins in `prepared`. Completion and failure are distinct terminal outcomes. Only a completed attempt may be acknowledged and become current. Tentative or failed values never replace the current acknowledged attempt. Transitions require the current receipt and owner; stale or foreign transitions fail closed.

`TargetArtifactIndex` provides:

```text
prepare(task, targets, *, owner, operation_id, prerequisites=()) -> OwnerReceipt
publish(receipt) -> TargetSnapshot
seal(task, targets, *, owner, operation_id, prerequisites=()) -> TargetSnapshot
read(task, target) -> bytes
verify(snapshot) -> bool
current(task) -> TargetSnapshot
recover(operation_id, *, owner) -> OwnerReceipt | TargetSnapshot
```

Target values accept text or bytes. Preparation does not alter the visible snapshot. Publication atomically exposes the complete named set, with text encoded as UTF-8. Verification checks receipt integrity and every exact named byte value. Replacing one task advances only that task's generation; corrupt closure data must not disturb an already verified sibling.

## Lifecycle and reporting

`LifecycleObligationLedger` provides:

```text
open(task, setups, teardowns, *, owner, operation_id, prerequisites=()) -> LifecycleObligation
setup(item, name) -> LifecycleObligation
body(item, outcome) -> LifecycleObligation
teardown(item, name) -> LifecycleObligation
close(item) -> LifecycleObligation
recover(operation_id, *, owner) -> LifecycleObligation
```

Setup actions occur in declaration order. The body is allowed only after all setups. Cleanup is owed for every entered setup and occurs in reverse order. Closure is allowed only after a body outcome and all owed cleanup. Reopening the ledger exposes the next durable obligation without replaying completed work.

`ReporterOutbox` provides:

```text
prepare(batch_id, events, *, owner, operation_id, prerequisites=()) -> OwnerReceipt
publish(receipt) -> PublicationBatch
claim(batch_id, *, owner, operation_id) -> PublicationBatch
acknowledge(batch, *, owner, operation_id) -> PublicationBatch
recover(operation_id, *, owner) -> OwnerReceipt | PublicationBatch
pending() -> tuple[PublicationBatch, ...]
events(batch_id) -> tuple[dict, ...]
```

Events retain input order. Preparation, publication, claim, and acknowledgement are distinct durable states. Publication makes a batch available but does not acknowledge delivery. A claim establishes the current delivery owner; only that owner may acknowledge it. Published or claimed batches remain pending after reopen, and acknowledged batches do not.

## Coordinated workflow

`TaskWorkflowCoordinator(path)` owns definition, selection, result, target, lifecycle, and reporting components beneath its storage directory. It provides:

```text
plan(definitions, requested, *, invocation_id, owner, operation_id) -> OwnerReceipt
execute(receipt, *, runner=None) -> OwnerReceipt
publish(receipt, *, owner, operation_id) -> OwnerReceipt
recover(operation_id, *, owner, runner=None) -> OwnerReceipt
handoff(operation_id, *, current_owner, new_owner, transfer_operation_id) -> OwnerReceipt
current(task) -> OwnerReceipt
verify(receipt) -> bool
owner_generations(task) -> dict[str, int]
```

Planning commits the supplied definitions and persists one dependency closure. Before execution, a planned workflow may be transferred to a new owner, which fences the former owner. Execution processes the selected tasks in dependency order. When supplied, `runner(task_name, definition)` may return `(status, result, values, targets, events)`; a nonzero status records failure and stops dependent work. The default runner produces a local successful outcome.

Publishing is allowed only after successful execution. It acknowledges completed results and delivery-owned event batches, then makes one workflow receipt current for each selected task. A failed workflow cannot publish. Recovery continues a prepared or executed workflow from its durable boundary and converges on the same published state. Verification requires an intact published receipt closure spanning every component. Corruption, incomplete cleanup, stale ownership, or a broken prerequisite chain fails closed and preserves the last current workflow.

## Cross-view guarantees

Pipeline names, catalog names, and runner output names refer to the same datasets. Durable definition names and selection names refer to the same task identities. A current task result must be backed by its producing definition, selected plan, verified targets, closed lifecycle, and acknowledged report delivery. Reopening any component must not duplicate a transition, skip ownership fencing, or expose prepared data as committed data.
