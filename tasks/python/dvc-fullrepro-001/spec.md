# DVC durable repository workflow contract

Implement a repository-oriented `dvc` package with the ordinary public DVC
surface and the durable workflow facilities described below.  The contract is
behavioral.  Callers may reopen any durable owner by constructing it again for
the same repository root; private file names, encodings, and helper layout are
not part of the API.

## Ordinary repository surface

The package exposes non-empty version metadata, `dvc.repo.Repo`, the public
data filesystem API, repository and remote error categories, and a working
`python -m dvc` command.  A repository can be initialized without source
control, presents a canonical root, and supports normal stage declarations,
output-conflict validation, freeze and unfreeze, stage listing, reproduction,
lock publication, and structured status.  Successful dependency pipelines
align their declarations, lock state, cache-backed outputs, workspace files,
and clean status.

## Durable receipts

`dvc.durable` exposes the classes and error categories in this document.
Durable operations return plain mapping receipts.  A receipt identifies its
owning facility, phase, and relevant public identity, and carries an integrity
token.  A downstream facility accepts only a valid receipt from the required
upstream phase.  Receipts survive reopening but cannot be invented, altered,
or substituted across owners.  A rejected prerequisite leaves the receiving
owner unchanged.

The public error base is `DurableError`.  `FenceConflict`, `ReceiptError`,
`StaleReplay`, and `PublicationError` are distinct subclasses used for stale
declaration fences, invalid prerequisite receipts, stale cached results, and
interrupted publication respectively.

## Declaration generations

`GraphDeclarations(root)` owns an append-only declaration history.  Its
`declare(name, command, *, deps=(), outs=())` operation normalizes dependency
and output collections, publishes the next generation, and returns a graph
generation receipt.  Names are not replaced implicitly.

`replace(name, command, *, expected_generation, deps=(), outs=())` succeeds
only when the named declaration exists and the supplied fence is the current
generation.  A stale fence raises `FenceConflict` without changing the current
view or history.  `view()` returns the current generation, declarations, and
ordered generation events.  `receipt()` returns the most recently published
generation receipt.

## Execution transaction journal

`ExecutionJournal(root)` owns execution transaction state independently of the
declaration store.  `begin(transaction_id, graph_receipt)` durably prepares a
unique transaction against one graph generation.  `record(transaction_id,
step, payload="")` appends a step.  `commit(transaction_id)` and
`abort(transaction_id)` publish terminal receipts with an outcome.

`crash(transaction_id)` represents an interrupted owner lifetime.  After the
journal is reopened, `adopt(transaction_id, graph_receipt)` may adopt only an
interrupted transaction under the same graph receipt.  Adoption advances its
owner epoch; a changed graph or a non-interrupted transaction is rejected.
`status(transaction_id)` returns the durable transaction projection.

## Content lineage

`ContentLineage(root)` separates object `prepare`, `publish`, and
`acknowledge` phases.  `prepare(data, execution_receipt)` accepts only a
committed execution terminal receipt and returns a prepared content receipt.
`publish(prepared_receipt)` makes that exact object addressable and returns a
published receipt.  `acknowledge(published_receipt)` closes the lineage and
returns an acknowledgement receipt.  Aborted execution cannot stage content,
and unpublished content cannot be acknowledged.

`read(receipt)` reads published or acknowledged bytes, and `phase(digest)`
reports the durable phase.  Content identity is derived from bytes, while
execution provenance remains part of the lineage.

## Run-cache result identity

`RunCacheResults(root)` owns replay results.  `store(identity,
content_receipt, graph_receipt, result)` accepts an acknowledged content
receipt and the graph generation that produced the result.  Identity is
matched by value rather than object identity.  `replay(identity,
graph_receipt)` returns both result bytes and a replay receipt.

Replay requires an exact identity and the original graph generation.  An
unknown identity is a receipt failure.  A known identity under a later or
different graph generation raises `StaleReplay` and does not publish output or
refresh the old entry.

## Remote transfer outbox

`RemoteOutbox(root)` owns transfer intent separately from content and remote
storage.  `enqueue(content_receipt, payload)` accepts acknowledged content and
returns an outbox receipt.  `deliver(enqueued_receipt, remote_root)` writes the
payload to the selected local remote and returns a delivered receipt.  Delivery
is retryable after reopening and does not by itself remove the pending item.

`acknowledge(delivered_receipt)` closes that exact delivery and returns a
remote acknowledgement receipt.  `pending()` lists unacknowledged item
identities in stable order.  Acknowledging one item never closes a peer item.

## Atomic workspace publication

`WorkspacePublisher(root)` owns final workspace visibility.
`prepare(publication_id, files, prerequisite_receipt)` stages a mapping of
relative paths to bytes or text.  Its prerequisite is either a remote
acknowledgement or a current run-cache replay receipt.  Publication identities
are unique.

`publish(prepared_receipt)` makes the complete staged set visible and returns a
published workspace receipt.  For recovery testing it also accepts the
keyword-only `interrupt_after` limit; when interrupted, it raises
`PublicationError` before the visibility marker is committed.
`recover(publication_id)` reopens a prepared or interrupted publication,
restores the complete prior workspace projection, and returns a recovery
receipt.  `visible()` is `None` before a successful terminal publication and
otherwise describes the single visible publication and its complete file set.

## Cross-owner lifecycle rules

A complete durable production flows from a graph generation through an
execution terminal, content acknowledgement, optional run-cache replay,
remote delivery acknowledgement, and workspace publication.  Each transition
uses the preceding owner's receipt; durable files or coincidentally matching
payloads are not substitutes.

Owner lifetimes are independent.  Reopening any owner must preserve its public
state and receipt validity.  Failure propagates forward without fabricating
downstream state: aborted execution cannot create content, stale replay cannot
open a workspace publication, delivered-but-unacknowledged transfer cannot
become visible, and interrupted workspace publication is recoverable without
a mixed old/new file set.  Independent transactions and outbox items retain
independent terminal status.

The implementation may choose any internal architecture that preserves these
rules.  Callers may vary repository paths, names, graph generations, operation
orders, payloads, interruptions, reopen points, and remote roots.

