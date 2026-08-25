# Dateparser reliable ingestion specification

## Overview

Dateparser converts localized date and time text into Python temporal values.
This distribution retains its established parsing and search interfaces and
adds local durable primitives for ingestion systems that must preserve source
provenance, publish acknowledged search projections, rotate timezone data,
recover message delivery, and resume replay after process replacement.

The package version is `1.4.1`.  The additional API is exported from
`dateparser.reliable`.  Owners accept `str` or `pathlib.Path` locations and
persist enough public state for a new object at the same location to continue
the protocol.  Each location has a stable `owner_id`.  All operations are
synchronous and local; they do not start workers or use a network.

## Existing parsing behavior

`parse`, `DateDataParser.get_date_data`, and `search_dates` retain Dateparser's
public behavior for absolute and relative text, explicit formats, language and
locale selection, settings, timestamps, embedded timezones, precision, and no
match results.  Explicit formats are considered in caller order, explicit
languages bypass detection, relative forms use the complete `RELATIVE_BASE`,
and timezone conversion preserves the represented instant.  Search results
remain ordered by source position.  These interfaces do not publish reliable
workflow state by themselves.

## Receipts and errors

`Receipt(owner, kind, revision, token, dependencies=None)` is a detached value
with public attributes of the same names.  `issue`, `chain`, `as_dict`, and
`from_dict` provide deterministic creation and detached wire round-trips.
`verify()` checks intrinsic integrity and `depends_on(other)` checks an exact
owner-to-token dependency.

The module exports `RevisionConflict`, `ReceiptError`, `StaleGenerationError`,
`DeliveryStateError`, and `ClosedOwnerError`.  Ownership, revision, fencing,
and transition failures happen before partial durable publication.

## Source provenance ledger

`SourceLedger(path)` owns append-only source events and per-source generations.
`advance(source_id, generation, expected_generation)` installs a strictly newer
generation and returns a `source.generation` receipt.  The expected generation
must match current durable state.  Older generation receipts remain historical
evidence but cannot authorize new appends after a fence advances.

`append(event_id, source_id, text, generation_receipt, expected_position)` adds
one event at the next global position.  Event identifiers are durable and
unique.  The receipt binds the exact generation.  `acknowledge(appended)` moves
that exact event to acknowledged state and is idempotent.  `event(receipt)`
returns a detached event only for a retained acknowledgement.  Snapshots expose
ordered immutable history, including status and generation, and survive reopen.

## Acknowledged index projection

`AcknowledgedIndex(path)` owns its source projection, hit identities, revision
history, and dependency receipts independently from the provenance ledger.
`project(source, acknowledged, expected_revision)` accepts only an exact
acknowledged source event verified by the supplied `SourceLedger`.  It replaces
that source's projected text as one revision, recognizes ISO-style calendar
dates, and returns an `index.projected` receipt that binds the source
acknowledgement.  Reusing the same acknowledgement is exactly-once.

Prepared or merely appended source events never appear in the index.  Historical
snapshots retain sources, ordered hits, and their source acknowledgement tokens.
The index must not reconstruct missing acknowledgement history from current
source text.

## Timezone generations and retirement

`TimezoneStore(path)` owns offset generations and decision history.
`publish(label, offsets, expected_generation)` creates the next active
generation.  A generation maps public zone names to signed UTC offset minutes.
`retire(generation, replacement)` retires an older generation only when the
replacement is a newer active generation owned by the same store.

`resolve(key, local, input_zone, display_zone, generation, prerequisites=())`
records a prepared decision and carries every prerequisite receipt.  New
decisions require the current active generation.  `acknowledge(prepared)` pins
the decision.  `retry(key)` recomputes an unacknowledged decision under the
current generation after rotation, while an acknowledged decision remains
pinned to its accepted projection and provider label.  Generation, retirement,
decision, and acknowledgement history survive reopen.

## Schedule and delivery outbox

`DeliveryOutbox(path)` owns schedule revisions and a durable message state
machine.  `publish_schedule(schedule_id, intervals, expected_revision)`
publishes non-empty half-open datetime intervals as one revision and returns an
`outbox.schedule` receipt.

`prepare(message_id, payload, due, schedule, prerequisites=())` validates the
current schedule receipt and membership, records the message invisibly, and
returns `outbox.prepared`.  `make_visible(prepared)` commits it to the visible
queue.  `deliver(visible, delivery_id, prerequisites=())` records a durable
delivery attempt and returns `outbox.delivered`.  `acknowledge(delivered)` is a
separate idempotent transition that returns `outbox.acknowledged`.

Reopening preserves every state.  Prepared messages remain invisible, visible
messages remain eligible, delivered-but-unacknowledged messages remain
recoverable, and acknowledged messages are never redelivered.  A delivery
attempt identifier is exactly-once for its message.  Snapshots are detached and
distinguish preparation, visibility, delivery, and acknowledgement.

## Replay ownership and cursors

`ReplayLedger(path)` owns protocol leases and cursors separately from all
product owners.  `acquire(stream, holder, generation, expected_generation)`
installs a strictly newer lease generation.  `advance(stream, lease,
prerequisites, expected_cursor)` advances exactly one cursor position and
returns a `replay.cursor` receipt binding every prerequisite owner and token.

Only the current lease may advance.  A later takeover permanently fences an
older lease, even if its expected cursor is otherwise current.  Cursor and
lease state survive reopen; repeated use of the same closed prerequisite set is
idempotent, while altered or tampered prerequisites fail before cursor change.

## Complete ingestion

`ReliablePipeline(source, index, timezone, outbox, replay)` coordinates without
merging the five owners.  Its `process(...)` operation follows this public law:

1. append and acknowledge a source event under a current source generation;
2. publish the acknowledged event to the independent index;
3. resolve and acknowledge the timezone decision under an active generation;
4. prepare, make visible, deliver, and acknowledge one scheduled message; and
5. advance the independently leased replay cursor.

The returned `workflow.closed` receipt directly binds the final receipt from
all five owners.  `verify(receipt)` succeeds only when the receipt belongs to
that owner set and each independently reopened owner still recognizes its exact
token.

Failures after an earlier successful workflow do not invalidate that closed
receipt.  A stale source generation cannot create a new indexed projection; a
retired timezone generation cannot publish a new delivery; and an unacknowledged
delivery cannot advance replay.  Recovery resumes from the last durable public
transition rather than treating visibility or delivery as acknowledgement.

## Ownership and non-goals

Caller mappings, sequences, temporal values, receipts, snapshots, and returned
events are detached.  Implementations may choose any local durable layout that
preserves atomic replacement, histories, fencing, transition order, and reopen
behavior.  This layer is not a distributed consensus system, timezone database
format, search replacement, scheduling optimizer, or transport implementation.
It does not prescribe files, tables, locks, serializers, helper names, or
internal algorithms.
