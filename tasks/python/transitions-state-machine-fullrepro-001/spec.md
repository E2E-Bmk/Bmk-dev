# Transitions Durable Workflow and Publication Coordinator

Implement a dependency-free Python package named `transitions`. It combines the
ordinary synchronous flat-state machine API with durable owners for transition
history, delayed delivery, topology, model attachment, and acknowledged
publication. Each durable owner persists independently and can be reconstructed
in a later process.

## Synchronous state machines

The package root exports `Machine`, `State`, `MachineError`, and a non-empty
string `__version__`. States, transitions, conditions, callbacks, transition
queries, model-local state, event helpers, internal and reflexive transitions,
and dispatch follow the ordinary synchronous `transitions` contract. Successful
and blocked calls keep the model attribute, predicates, queries, callbacks and
return value mutually consistent. Models attached to one machine retain
independent state and each invocation receives fresh event data.

## Durable transition journal

`TransitionJournal(path)` owns an append-only log. It provides `prepare`,
`commit`, `abort`, `history`, `pending`, `replay`, and `snapshot`. A preparation
uses entity, event, source, destination, expected revision, idempotency key and
optional payload. The expected revision is compared with committed history.
Preparations survive reopen but do not affect replay until committed.

An idempotency key identifies the complete request across process lifetimes.
Repeating identical work returns the existing preparation or commit; conflicting
reuse raises `IdempotencyConflict`. Commit advances an entity revision once and
returns a stable receipt. Aborted or pending records never advance replay.
Snapshots require the current committed revision.

## Lease scheduler

`LeaseScheduler(path)` durably owns delayed delivery. It provides `schedule`,
`claim`, `ack`, `retry`, `cancel`, and `get`. A due item is claimed with a fenced
token, worker identity, expiry and monotonically increasing attempt. Expiry
permits another worker to claim the same delivery with a new token. Superseded
tokens cannot acknowledge or retry. Due time, attempts, errors, terminal state,
receipts and idempotency decisions survive reopen.

## Versioned topology

`TopologyRegistry(path)` publishes immutable workflow generations through
`create` and compare-and-set `migrate`. States, transition declarations and
generation-scoped aliases are validated before publication. Receipts contain a
content digest linked to the preceding generation. Historical generations stay
queryable and receipt verification recomputes stored content rather than
trusting fields supplied by callers.

## Persistent attachment ownership

`AttachmentStore(path)` owns model binding, helper identity and process-owner
generation. It provides `attach`, `detach`, `rebind`, `current`, `update_state`,
`claim_owner`, `helper_token`, `validate_helper`, `replace_helper`, and
`helper_owner`.

Attachment generations fence detach and rebind. `claim_owner(model_id,
process_id, *, expected_attachment_generation)` transfers execution ownership
and advances a separate owner generation; repeating the same active claim is
idempotent. State updates, helper use and replay require both the current
attachment and owner generations. Tokens issued before detach, rebind, topology
adoption, or owner transfer are stale. User-replaced helpers remain recorded as
user-owned rather than silently reclaimed.

## Acknowledged publication outbox

`PublicationOutbox(path)` independently owns external visibility. It provides
`stage(journal_receipt, topology_receipt, attachment, *, idempotency_key,
payload=None)`, `claim(worker, *, now, lease_seconds)`, `ack(publication_id,
lease_token, external_receipt)`, `retry(publication_id, lease_token, *, due_at,
reason)`, `get(publication_id)`, and `visible(entity_id)`.

Only a committed journal receipt may be staged. A staged publication binds the
journal identity and revision, topology digest and generation, attachment
generation and process-owner generation. Staging does not make the transition
externally visible. Visibility begins only after acknowledgement by the current
publication lease and survives reopen. Expired leases are redelivered with a
new fenced token; stale tokens cannot acknowledge or retry. Idempotency covers
the complete bound envelope, so neither duplicate commits nor duplicate
delivery can create a second visible publication.

## Coordinated workflows

`DurableMachine(journal, scheduler, topology, attachments, outbox)` coordinates
the five owners. `transition` prepares and commits an allowed transition,
updates the currently owned attachment, and stages its publication. It returns
linked journal, topology, attachment and publication receipts; it does not
claim external visibility.

`schedule` records delayed intent. `run_due` claims one scheduled item and
performs the transition only if its lease, topology generation, attachment
generation and owner generation remain current. Recoverable conflicts retry the
delivery without committing or publishing partial work. `publish_due` claims
one staged publication and acknowledges the supplied external receipt.

`recover` completes a prepared transition only after a later process acquires
the expired scheduler lease and current attachment ownership. It commits at
most one revision, acknowledges the same journal receipt, and stages exactly one
publication. A topology migration interleaved with queued or prepared work does
not silently reinterpret its source generation: the old intent is either
reconciled through an explicit alias in the current generation and a current
rebind, or retried without commit. Reopen, retry and duplicate delivery must
converge on one journal revision and one acknowledged external publication.

## Errors and scope

The root exports `RevisionConflict`, `IdempotencyConflict`, `LeaseError`,
`GenerationConflict`, `StaleHelperError`, `DetachedModelError`, and
`PublicationError`. Paths may be initially absent and parent directories are
created as needed. Returned mappings are detached from persisted state.

Hierarchical states, asynchronous callbacks, graph rendering, remote databases,
distributed consensus, background threads, wall-clock acquisition and transport
implementation are outside scope. Callers supply logical time and external
publication receipts.
