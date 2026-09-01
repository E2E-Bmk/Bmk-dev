# RQ public contract — Draft B clean

This document is the sole candidate-visible authority for this draft. It
describes public behavior, not private Redis keys, Lua bodies, worker
internals, or hidden assessment structure.

## Product model

RQ stores callable work as durable `Job` identities. A named `Queue` owns the
order of ready jobs. A worker moves a job through execution. Registries,
result history, fresh `Job.fetch` objects, group views, and the documented
public helpers must describe the same state transitions.

A transition is complete only when every applicable public owner agrees. For
example, finished means the job is no longer ready or started, is present in
the finished registry while retained, exposes a successful result and return
value, and remains consistent after a fresh fetch. Failure, cancellation,
scheduling, dependency deferral, retry, and deletion follow the same
cross-view rule.

## Installed public surface

The installed `rq` distribution exposes its documented Queue, Job, Worker,
registry, Result, dependency, Retry, Repeat, Callback, RateLimit, Group,
serializer, command-helper, status, and exception families. Its installed
version and import origins agree with distribution metadata.

The console entries are `rq`, `rqinfo`, and `rqworker`. Their help routes
succeed, and `rq --version` reports the installed version. `python -m rq.cli`
is the supported module help route. The package has no `python -m rq` entry;
that invocation fails rather than silently choosing another command. Exact
help prose, whitespace, and rich formatting are not contractual.

## Connections and isolation

Queue, Job, Worker, registry, Group, scheduler, and command-helper operations
that address stored state require an explicit Redis-compatible connection
where their public signatures require one. Missing connections, missing
identities, invalid identifiers, and ineligible transitions use the public
exception boundary.

Queue names, job identifiers, worker names, group names, and connection
instances define state ownership. An operation on one identity must not
silently change an unrelated queue, job, worker, registry, group, result
history, or connection namespace.

## Queue and production

A Queue has a public name, with `default` as the default name. Its length,
count, job-id list, job list, position, and fetch operations are coherent views
of ready membership. Offset and length projections preserve ready order.
Removing a ready member removes only queue membership; it does not by itself
delete the persisted Job. Re-enqueueing that Job can restore ready membership
at the requested end.

Enqueueing a callable or dotted reference creates and persists one Job. The
Job retains its id, origin queue, callable reference, positional and keyword
arguments, metadata, serializer, and documented options. RQ control options
are not forwarded as target-callable arguments. Appending and `at_front=True`
select the corresponding ready and execution order.

Custom ids are strings containing only letters, numbers, underscores, and
dashes. An invalid id fails before creating a Job or ready member, and a later
corrected enqueue succeeds. A syntactically valid but non-importable dotted
callable is different: it may be persisted and queued, then becomes a normal
worker-visible failed Job when resolution fails. That failure is isolated
from valid siblings.

`Queue.prepare_data` and `Queue.enqueue_many` preserve returned-job input
order. A caller-supplied Queue batch pipeline owns commit: before `execute`,
the staged jobs and ready entries are absent; after execution they appear
together. If prepared data contains an invalid id, the batch leaves no partial
Job or ready member and can be corrected and retried.

`Queue.all(connection)` lists queues that currently own stored queue state.
`Queue.delete(delete_jobs=False)` removes that queue from the queue listing
and removes its ready list while retaining the Job records. It does not delete
sibling queues. Job-deleting queue operations that require Lua are outside
this contract.

## Job identity, metadata, and absence

`Job.create` makes an unsent Job, while enqueueing or explicit persistence
makes it fetchable. `Job.exists`, `Job.fetch`, `Job.fetch_many`, and
`Queue.fetch_job` agree on presence. `fetch_many` preserves input alignment and
uses `None` for a missing id. Removing a ready Job leaves it fetchable.

A Job's `JobStatus` value and Boolean status projections agree. Refresh reloads
stored values. The public metadata mapping can be changed and saved; a fresh
fetch exposes the saved metadata. Before execution, latest-result, result
history, return-value, and execution-record views report no invented outcome.

Deleting a Job removes its Job record plus ready and registry membership
without changing an unrelated sibling. Retained result history is stored
separately and is not deleted by this operation; after the same valid id is
reused by a new Job, public result history can therefore include results from
both incarnations, newest first.

## Scheduling and promotion

Absolute and relative scheduling persist a scheduled Job. It is absent from
the ready list, has scheduled status, belongs to the scheduled registry, and
has a public scheduled time. A future Job remains scheduled when a scheduler
checks before it is due.

`RQScheduler.enqueue_scheduled_jobs()` promotes due Jobs owned by its acquired
queue. Promotion moves the same identity to ready exactly once, changes it to
queued, and removes scheduled ownership, while a not-due sibling remains
scheduled. No wall-clock tolerance, polling cadence, background scheduler
process, or sleep is required.

## Worker lifecycle

A worker consumes ready Jobs from its configured queues. While a Job executes,
the public current-job context, Job status, worker name, live Worker listing,
started registry, and execution record identify the same Job. Completion
removes current/start/execution ownership, and graceful burst exit removes the
Worker from live listings.

A maximum-job boundary processes no more than requested and leaves remaining
ready work for a later worker. With multiple queues, default selection honors
queue priority. Round-robin selection rotates among nonempty queues; random
selection is assessed only by eventual bounded membership, never an exact
random sequence.

On success, a retained Job becomes finished, enters the finished registry,
records a successful Result, and exposes its return value after refresh and
fresh fetch. On exception, it becomes failed unless a retry policy applies,
enters the failed registry on terminal failure, records failure information,
and leaves no started residue. A valid sibling still executes, and a failed
Job may later be requeued and finish without stale terminal ownership.

The deterministic local worker mode is `SimpleWorker` with the documented
platform-appropriate `TimerDeathPenalty`. This contract does not require
forking, spawning, OS signals, heartbeats during a long task, or a live worker
subprocess.

## Results and retention

`job.latest_result()`, `job.results()`, `job.return_value()`, and fresh Job
fetches describe one execution history. Result history is newest first and is
bounded according to RQ's public retention policy. Result types include
successful, failed, stopped, retried, and maximum-retries-exceeded values.

A failed-to-requeued-to-successful Job retains newest-first successful then
failed Results while its current status and registries describe only the
successful terminal state. Exception information belongs only to the failed
Result and must not contaminate a successful sibling or later success.

With `result_ttl=0`, a successful execution stores no Result and removes the
persistent Job rather than fabricating a stale return value. This deletion is
limited to that Job. Retained results use the configured positive or
non-expiring TTL behavior.

## Registries, requeue, cancellation, and deletion

Queues expose their documented started, deferred, finished, failed, scheduled,
and canceled registries. Membership accepts the documented Job or id forms.
Each transition changes all applicable public owners once and leaves no
duplicate ready member.

Eligible requeue through `Job.requeue`, `FailedJobRegistry.requeue`, or the
public `requeue_job` function removes failed ownership and adds exactly one
ready member with queued status. Front placement is honored. Missing Jobs and
nonfailed Jobs refuse requeue through `NoSuchJobError` or
`InvalidJobOperation` without mutation.

Cancellation through `Job.cancel` or `cancel_job` removes ready membership,
sets canceled status, retains the Job for inspection, and adds canceled
registry membership. Repeating cancellation is invalid. A missing id does not
mutate siblings.

`send_stop_job_command` applies only to a currently executing Job. Calling it
for a merely queued Job raises `InvalidJobOperation`, preserves ready state,
and does not prevent a later worker from completing that Job. Active stop and
worker-shutdown signal lifecycles are outside this contract.

## Dependencies

`rq.job.Dependency` accepts one or more valid prerequisite Jobs or ids and the
documented `allow_failure` and `enqueue_at_front` options. Empty or invalid
input is rejected.

A Job with unmet dependencies is deferred, absent from ready membership, and
present in the deferred registry. Ordinary dependencies promote only after all
parents finish successfully. A dependency with `allow_failure=True` may
promote after a parent fails; an ordinary sibling remains deferred. Promotion
removes deferred ownership once and never duplicates the child.

With multiple parents, the child remains deferred after only some parents
finish. When the last parent completes, an `enqueue_at_front` child appears
exactly once at the front. Canceling a single parent with
`enqueue_dependents=True` cancels that parent and promotes its eligible child
once.

Dependency promotion composes with execution policy: a child may become
ready, fail once under an immediate exception Retry, and then finish, while
parent, child, registries, result, and metadata views retain their separate
identities.

## Retry, repeat, and callbacks

`Retry` validates a positive maximum, nonnegative integer interval or interval
sequence, and its front-placement option. `Repeat` validates positive repeat
count and nonnegative interval values. `Callback` accepts a public callable or
dotted reference and parses its timeout.

An exception-based Retry may immediately requeue a failed attempt and later
finish, or become terminally failed after exhaustion. Exception retries do not
promise an intermediate `RETRIED` Result; the final successful or failed
Result, status, retry counters, registries, and cleanup are authoritative.

A callable may instead return a `Retry`. Each nonterminal returned Retry
records a `RETRIED` Result. Later success records a newer successful Result;
exhaustion records a newer `MAX_RETRIES_EXCEEDED` Result and failed status.

An interval-zero Repeat immediately re-enqueues the same Job identity. The
initial execution plus the requested repeats produce ordered successful
Results; the repeat counter reaches zero and no ready, scheduled, or started
residue remains.

Success and failure callbacks receive the matching Job, connection, and public
outcome arguments. Their changes to that Job's metadata persist. If a success
callback raises, that Job becomes failed with the callback exception, while an
independent sibling can still finish. Stopped-callback timing and active stop
delivery are outside this contract.

`RateLimit` validates a nonempty key and concurrency of at least one and
retains those values. Rate-limit admission, promotion, release, cleanup, and
all other Lua-backed execution are outside this contract.

## Serialization

`JSONSerializer` round-trips JSON-compatible values and raises on unsupported
values when called directly. A Queue and Worker configured with the same JSON
serializer preserve callable arguments and compatible result values.

If a successfully executed callable returns a value that the configured
serializer cannot encode, RQ keeps the Job successful and stores the public
fallback string `Unserializable return value` instead of the original value.
That fallback is visible through both latest Result and Job return-value views;
it does not fail or corrupt a compatible sibling.

## Synchronous queues

With `is_async=False`, enqueue executes in the producer process while
persisting the same public Job, Result, status, and registry meaning as worker
execution. Success records finished state and its return value; exception
records failed state and failure information without escaping as an
unpersisted operation. A later corrected synchronous Job succeeds without
rewriting the earlier failure. `result_ttl=0` follows the deletion behavior
described above.

## Groups and batches

A Group tracks a set of member Job identities; no member order is promised by
`Group.get_jobs()`. Group enqueue returns Jobs in input order, and each Job's
`group_id` and a fresh `Group.fetch` agree on membership.

Members retain independent queue, lifecycle, registry, and result state. A
mixed batch may contain one finished and one failed member. Requeueing and
correcting the failed member changes only that Job while Group membership and
the successful sibling remain stable. Deleting one member removes it from the
Group view without deleting another member.

## Cross-surface laws

1. Job id and origin are stable across Queue, Job, Worker, Registry, Result,
   Group, scheduler, and public helper projections.
2. A Job occupies only the ready/live/terminal owners allowed by its current
   status; stale ready, started, scheduled, deferred, failed, or canceled
   membership is removed.
3. Execution Result, current terminal status, registry, metadata, history, and a
   fresh fetch agree.
4. Dependency promotion, retry, repeat, cancellation, requeue, and deletion
   change owned views exactly once and never duplicate a Job.
5. Serializer, callable reference, and arguments retain one meaning from
   producer through execution, subject only to the documented unserializable
   result fallback.
6. Worker live registration is scoped to the Worker lifecycle and is clean
   after a graceful burst.
7. A failure may leave its documented Job and Result state, but it cannot
   create cross-job contamination or prevent corrected eligible work.

## Out of scope

Private Redis keys, Lua bodies, unique-enqueue scripts, rate-limit execution,
`Queue.empty`, Job-deleting Queue deletion, internal maintenance algorithms,
undocumented imports, exact logs or help prose, webhook delivery,
worker-pool/process-manager/dashboard behavior, live CLI mutation of queue
state, arbitrary remote Redis or network behavior, active stop/shutdown signal
delivery, spawned/forked workers, scheduler background processes, exhaustive
enum catalogs, wall-clock performance, sleeps, polling races, and
platform-specific signal behavior are not required.

## Recoverable job workflow API

`rq.workflow` provides a filesystem-backed coordination API for applications
that need to publish an RQ job generation across fresh processes. It exports
`WorkflowError`, `IntegrityError`, `OwnershipError`,
`StaleGenerationError`, and `IncompleteWorkflowError`; immutable records
`OwnerReceipt`, `TaskDefinitionSnapshot`, `SelectionPlan`, `TaskAttempt`,
`TargetSnapshot`, `LifecycleObligation`, and `PublicationBatch`; the six
independent owners below; and `TaskWorkflowCoordinator`. Returned mappings
and sequences are detached snapshots.

`TaskDefinitionCatalog(path)` owns normalized job definitions and dependency
graph revisions. `prepare(name, definition, *, owner, operation_id)` creates
an invisible operation and `commit(receipt)` publishes it. Equivalent replay
is idempotent. Conflicting operation reuse, unresolved dependencies,
duplicate targets, cycles, and record corruption fail atomically without
replacing the last committed definition.

`SelectionPlanRegistry(path)` owns run-local queue selection. `acquire`
resolves a canonical, deduplicated dependency closure; `handoff` transfers a
prepared plan; `release` closes it; and `recover` resumes it. Owner and
generation fencing apply to every change, and unrelated jobs never enter a
selection merely because an earlier run selected them.

`TaskResultJournal(path)` owns prepared, terminal, and acknowledged attempts.
Result values become current only after successful terminal completion and
acknowledgement. Failure cannot publish a tentative replacement. Recovery
distinguishes prepared, completed-unacknowledged, failed, and acknowledged
states.

`TargetArtifactIndex(path)` owns immutable exact-byte job outputs. Prepare is
invisible, publish is atomic, and `seal` performs both phases. Reads and
`verify` validate the complete manifest and reject absent, partial, or
corrupted content before exposing success.

`LifecycleObligationLedger(path)` owns setup, body, and teardown progress for
one worker execution. It records only setup frames that actually ran,
requires their reverse-order teardown, and exposes the next owed action after
reopen. A generation closes only after all obligations are discharged on
success or failure.

`ReporterOutbox(path)` owns ordered job publication events. Prepare is
invisible; publish makes a batch pending; claim transfers it to one delivery
owner; and acknowledgement closes it. Failed or interrupted delivery remains
pending, while acknowledged event identities are never emitted twice.

`TaskWorkflowCoordinator(path)` composes rather than replaces these owners.
`plan`, `execute`, `publish`, `recover`, and `handoff` coordinate one job-run
generation. A published generation has an acyclic, digest-verified closure
reaching the committed definition, current selection, acknowledged result,
verified artifacts, discharged lifecycle, and acknowledged outbox. Failure
or corruption preserves the previous acknowledged generation. Equivalent
concurrent operations converge; conflicting operations have one winner and
no loser partial state.

Workflow files are deterministic UTF-8 data. This API does not rely on the
network, sleeps, wall-clock races, process-ID ownership, hidden evaluator
knowledge, or delegation to another installed `rq` package.
