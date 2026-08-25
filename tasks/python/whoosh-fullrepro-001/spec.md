# Whoosh indexes and recoverable search workflows

## Overview

Whoosh is a Python library for defining analyzed fields, writing durable
indexes, constructing queries, and projecting search results. This package
also exposes `whoosh.workflow`, a filesystem-local coordination layer for
applications that must move document batches through recipe validation,
index publication, snapshot pinning, paged search, and result delivery without
losing ownership or recovery information.

The workflow layer stores JSON-compatible public values. Mapping keys are
ordered canonically for identity and digest purposes; user-facing sequences
retain their order. Every successful state change is durable before it is
reported. Reopening an owner on the same directory reconstructs the same
committed public view.

## Fields, analysis, and index state

A `Schema` names the only fields accepted by a writer. Text fields analyze a
value into independently searchable terms, identifier fields keep a complete
value as one term, and keyword fields apply their configured delimiter and
case normalization. Stored values remain available through hits; values that
are indexed but not stored do not appear in the stored-field mapping.

Index creation makes a recognizable named index in a directory. Named indexes
in one directory are independent. A writer publishes additions, updates, and
deletions only on commit; cancellation retains the previously committed
generation. Unique-field updates replace the matching committed document,
while ordinary additions may preserve duplicates. An already-open searcher
retains its generation as later commits become visible to newly opened
searchers.

Term, phrase, prefix, range, and compound queries operate on analyzed terms.
Parsers assign unqualified text to their configured fields. Search limits,
filtering, masking, sorting, grouping, and paging are projections of the same
match set. Results expose stored fields and, when requested, matched terms.
Facet groups and ordered hits remain consistent with the selected sort and
filter rules.

## Durable receipts and failures

`whoosh.workflow` exports immutable records `OwnerReceipt`,
`AnalysisRecipe`, `IngestBatch`, `IndexSnapshot`, `SearchSession`,
`ExportBatch`, and `WorkflowRun`. Receipts carry a kind, logical key,
operation identifier, monotonic generation, owner, content digest, state, and
prerequisite digests.

The module exports `WorkflowError`, `IntegrityError`, `OwnershipError`,
`StaleGenerationError`, and `IncompleteWorkflowError`. An unknown receipt,
wrong owner, stale generation, conflicting reuse of an operation identifier,
malformed durable state, or incomplete transition raises the corresponding
workflow error without changing the last committed public view. Repeating an
operation with identical normalized inputs is idempotent; reusing its
operation identifier with different inputs is rejected.

## Analysis recipe catalog

`AnalysisRecipeCatalog(path)` owns named analyzer configurations.

- `prepare(name, config, *, deps=(), owner, operation_id)` validates a
  tentative recipe and returns a prepared receipt.
- `commit(receipt)` makes that exact generation current.
- `get(name)` returns the committed recipe, and `recover(operation_id, *,
  owner)` reconstructs an existing tentative or committed operation.

Dependencies refer to committed recipes, are unique, and form an acyclic
graph. Recipe identity includes normalized configuration and dependency order.
Preparing is not visibility: readers continue to observe the previous
committed generation until commit succeeds.

## Document ingest journal

`DocumentIngestJournal(path)` tracks a batch from declaration through a
complete checkpoint to commit.

- `begin(batch_id, documents, *, owner, operation_id, prerequisites=())`
  records the ordered documents as a tentative batch.
- `checkpoint(receipt, *, accepted, rejected, operation_id)` records a
  disjoint, complete disposition of document keys.
- `commit(receipt)` publishes only a fully checkpointed batch.
- `current(batch_id)` and `recover(operation_id, *, owner)` expose durable
  committed and operational views.

Document keys in a batch are unique. Accepted order follows input order;
rejections retain their supplied reason. An incomplete, overlapping, or
foreign checkpoint cannot publish a partial batch.

## Snapshot registry and leases

`IndexSnapshotRegistry(path)` publishes immutable index generations and pins
them for active readers.

- `prepare(name, manifest, *, owner, operation_id, prerequisites=())` creates
  a tentative generation whose digest covers the normalized manifest and
  lineage.
- `publish(receipt)` advances the current generation atomically.
- `acquire(name, *, owner, operation_id)` returns a lease pinned to the
  current generation; `release(lease, *, operation_id)` releases only that
  lease generation.
- `current(name)`, `recover(operation_id, *, owner)`, `verify(snapshot,
  manifest)`, and `retire(snapshot, *, operation_id)` expose lifecycle state.

A newer publication does not move existing leases. Retirement is forbidden
for the current snapshot or a generation with a live lease. Verification
rejects missing, changed, or extra manifest facts.

## Search sessions and cursors

`SearchSessionRegistry(path)` binds a normalized query and ordered hit
projection to one snapshot generation.

- `open(session_id, snapshot, query, hits, *, owner, operation_id,
  prerequisites=())` creates the current session generation.
- `page(session, *, cursor=None, size)` returns a page and an opaque next
  cursor.
- `handoff(session, *, new_owner, operation_id)` advances ownership and
  fences the previous generation; `close(session, *, operation_id)` closes
  the current owner generation.
- `current(session_id)` and `recover(operation_id, *, owner)` reconstruct
  durable session state.

Cursors are scoped to the session digest and generation. Page boundaries
preserve hit order, do not duplicate items, and terminate with no next cursor.
A cursor from another session or generation is rejected.

## Result export outbox

`ResultExportOutbox(path)` separates result persistence from delivery.
`prepare(batch_id, rows, *, owner, operation_id, prerequisites=())` stores an
ordered tentative export. `publish(receipt)` makes it pending. `claim(batch,
*, owner, operation_id)` transfers one pending generation to a delivery owner.
`acknowledge(claim, *, operation_id)` removes only that claimed generation
from `pending()`. `rows()`, `current()`, and `recover()` retain exact order,
normalized values, ownership, and lineage across reopen. A claim is not an
acknowledgement, and a prepared batch is not pending.

## Coordinated recovery

`SearchWorkflowCoordinator(path)` coordinates all five owners as one
publication closure.

`plan(recipe, documents, query, *, workflow_id, owner, operation_id)` records
the recipe, ingest declaration, and intended query without changing the
published workflow. `execute(receipt, *, runner=None)` completes ingest,
publishes a manifest snapshot, creates a pinned ordered search session, and
publishes an export batch. A runner maps the committed documents and query to
an ordered sequence of result rows. `publish(receipt, *, owner,
operation_id)` verifies every prerequisite digest and lifecycle state before
advancing `current(workflow_id)`.

`recover(operation_id, *, owner, runner=None)` resumes the next missing phase
without duplicate generations or exports. `handoff(receipt, *, new_owner,
operation_id)` transfers only an unpublished workflow and fences the old
owner. `views(workflow_id)` and `verify(receipt)` show that the recipe,
committed ingest, snapshot, session, export, and current workflow agree on
lineage and generation. Corruption, incomplete ingest, stale ownership,
unverified snapshot facts, an unclosed result projection, or premature export
acknowledgement leaves the previous published workflow current.

## Scope

Storage is local and process-safe for ordinary independent reopens; it is not
a distributed consensus service. The specification does not constrain private
helpers, codec file names, relevance score constants, source layout, or object
identity across processes.

