# gix-ref Specification

> **Specification Authority.** This document is the complete and authoritative
> description of the required behavior. Where it states a name, a signature, an
> ordering, an error text or an on-disk effect, that statement is the contract.
> Behavior not described here is not required. Behavior described here is
> required in full, including every error path.

═══════════════════════════ Context Layer ═══════════════════════════

## Product Overview

`gix-ref` is a git reference-store library that changes references on disk
through two-phase transactions and records those changes in reference logs.

A git repository keeps its references — branches, tags, notes, `HEAD` and the
various worktree-private names — as one fact spread over three encodings inside
a git directory. A reference exists as a *loose* file at the path its name
spells out under the git directory, or as one line in a single *packed*
reference file, or as both at once. Every change to a reference is additionally
recorded in a *reference log*, an append-only text file under `logs/` whose path
mirrors the reference name.

This library owns the write path into that store. A caller describes a batch of
changes as a list of edits, hands the list to a transaction, and the transaction
runs in two phases. **Preparation** acquires one lock per affected resource,
reads the current value of every affected reference while holding its lock,
checks that value against the caller's expectation, and stages the new content
next to the lock without publishing it. **Commit** publishes the staged content,
writes the reference log entries, rewrites the packed reference file and removes
what the edits deleted. Between the two phases the caller holds a prepared
transaction that has changed nothing observable: dropping it or rolling it back
must leave the store byte-identical to what it was, including any directory the
preparation had to create.

The two phases carry different guarantees, and the difference is part of the
contract. Preparation is all-or-nothing: a failure during preparation must undo
everything preparation did. Commit is not all-or-nothing: a failure partway
through commit leaves the store in a state where some edits are applied and
others are not, and this library makes no attempt to undo the applied ones. The
store is still readable and still consistent in the sense that every reference
it reports is a reference that exists; it is the *batch* that is not atomic.

The expectation a caller attaches to an edit is the interesting part of
preparation. It ranges from "do not check" through "must exist", "must not
exist", "must exist and hold exactly this value" to "if it exists it must hold
exactly this value", and the transaction resolves it against what is actually on
disk under the lock. Whatever the caller asked for, the edits the transaction
hands back afterwards report the value that was actually found, so a caller that
supplied a loose expectation learns the precise previous value and is able to
log it, undo it or chain another change on it.

Reference logs are the second half of this library's write path and its only
read path. A log line pairs the previous and the new object id with the
committer signature and a message. Lines are read forward from the oldest entry
or backward from the newest, and reading backward is the common case: the n-th
entry counted from the end is what a caller asks for when it wants to know where
a branch pointed n changes ago.

## Non-Goals

- This specification does not define how a lock file is named, what bytes it
  contains, in what order the system calls that create and publish it are
  issued, how long a blocking lock acquisition waits between attempts, or
  whether and when data is flushed to durable storage. Those are the
  responsibility of the two lock and temporary-file libraries named in Appendix
  A, and an implementation must obtain them from those libraries rather than
  reimplement them.
- This specification does not require any bound on the number of file
  descriptors, locks or bytes of memory a transaction holds at one time, and
  does not define when a lock is released relative to any other lock beyond the
  orderings stated in the Behavior Layer. An implementation that holds one open
  descriptor per edit for the whole transaction satisfies this document.
- This specification does not define how a packed reference file is parsed,
  which header forms are accepted, whether an unsorted file is re-sorted, how a
  lookup inside it is performed, or at what size it is memory-mapped. It defines
  only what this library *writes* into that file, and requires that a buffer
  opened over a file this library wrote reports exactly the records that were
  written.
- This specification does not define the loose-versus-packed overlay iteration
  over the whole store, the three-way merge across a git directory, a common
  directory and the packed file, or prefix-filtered iteration.
- This specification does not define reference resolution: following a symbolic
  reference to its object, peeling an annotated tag chain, the depth limit on
  such a walk, or the cached peeled object id on a reference.
- This specification does not define linked-worktree layouts, the split between
  a git directory and a common directory, or which reference names are private
  to a worktree beyond the classification rules stated under Reference Names,
  Targets and the Store.
- This specification does not require reference-name validation to be
  implemented here; it must be obtained from the validation library named in
  Appendix A, and this document describes only which operations invoke it and
  what error surfaces when it rejects a name.
- This specification does not define serialization of any type to or from a
  data-interchange format. Apart from the hash-selection feature named in
  Appendix A, which the object-hash dependency requires before it compiles at
  all, no compilation feature is required to be turned on for the behavior
  described here to hold.
- This specification does not define behavior specific to Windows beyond one
  rule: the reserved-device-name check must run before a lock is acquired.

═══════════════════════════ Orientation Layer ═══════════════════════════

## Representative Workflows

### Workflow 1 — Create a branch, then move it, and read back what happened

A caller opens a store at a git directory, describes the creation of
`refs/heads/main` with the expectation that it must not exist yet, prepares the
transaction with immediate lock failure on both the loose refs and the packed
file, and commits it with a committer signature.

```rust
use gix_ref::{Target, file, transaction::{Change, LogChange, PreviousValue, RefEdit, RefLog}};

let store = file::Store::at(git_dir.to_owned(), gix_hash::Kind::Sha1);
let edits = store
    .transaction()
    .prepare(
        Some(RefEdit {
            change: Change::Update {
                log: LogChange { mode: RefLog::AndReference, force_create_reflog: false, message: "create".into() },
                expected: PreviousValue::MustNotExist,
                new: Target::Object(first_id),
            },
            name: "refs/heads/main".try_into()?,
            deref: false,
        }),
        gix_lock::acquire::Fail::Immediately,
        gix_lock::acquire::Fail::Immediately,
    )?
    .commit(committer.to_ref(&mut buf))?;
```

The commit returns one edit. Its `expected` is still `MustNotExist`, because
nothing was on disk to report. A loose file now holds the object id followed by
a newline, and because `refs/heads/` is one of the prefixes whose logs are
created automatically, a reference log now exists with one line whose previous
id is the null id.

The caller then moves the branch, this time expressing the expectation loosely
as `PreviousValue::Any`. The commit returns an edit whose `expected` has been
rewritten to `PreviousValue::MustExistAndMatch(Target::Object(first_id))` — the
value that was actually found under the lock. Reading the log backward yields
the newest line first: previous id `first_id`, new id `second_id`.

### Workflow 2 — Update `HEAD` with dereferencing, and observe the split

`HEAD` holds `ref: refs/heads/main`. A caller submits a single edit naming
`HEAD`, with `deref` set to true, whose new value is an object id.

Preparation replaces that one edit with two. The edit naming `HEAD` keeps
`HEAD`'s own name, has its `deref` flag cleared, has its log mode demoted so
that only a log entry is written and the symbolic reference itself is left
alone, and has its expectation relaxed to `PreviousValue::Any`. A second edit is
appended naming `refs/heads/main`, carrying the caller's original expectation
and the caller's original log mode, with `deref` set to true.

Commit therefore writes `refs/heads/main` to the new object id, writes a log
entry under `refs/heads/main`, and also writes a log entry under `HEAD` — with
the same previous and new object ids, because the previous object id of the
referent is propagated up the chain to every ancestor edit. `HEAD` itself still
holds `ref: refs/heads/main`.

If the same batch had also named `refs/heads/main` directly, preparation would
have failed before touching anything, because after splitting, two edits would
name one reference.

### Workflow 3 — Prepare, then abandon

A caller prepares a transaction that creates `refs/heads/a/b/c` in a store whose
git directory has no `refs/` directory at all. Preparation creates the
directories it needs and places a lock. The caller then drops the prepared
transaction without committing.

Afterwards the git directory must look exactly as it did before: no
`refs/heads/a/b/c`, no lock file beside it, and no `refs`, `refs/heads`,
`refs/heads/a` or `refs/heads/a/b` directory either. Calling `rollback()`
instead of dropping must have the same effect on disk, and additionally returns
the edits as preparation left them.

═══════════════════════════ Behavior Layer ═══════════════════════════

## Reference Names, Targets and the Store

A **reference name** is a byte string. `refs/heads/main`, `HEAD` and
`refs/tags/v1.0` are reference names. `FullName` owns such a name and
`FullNameRef` borrows one; `FullNameRef` is an unsized type that must be used
behind a reference and must be layout-transparent over its byte-string payload.
Converting a `&str`, `String`, `&BStr`, `BString` or `&BString` into a
`FullName`, or a `&str` or `&BStr` into a `&FullNameRef`, must validate the name
and must return the validation library's reference-name error when validation
fails. `PartialName` and `PartialNameRef` are the same pair for names that are
permitted to omit a category prefix; converting a `&FullNameRef` into a
`&PartialNameRef` must always succeed and must therefore use the never-failing
conversion type as its error.

A name that begins with a recognised prefix has a **category**.
`FullNameRef::category` returns the category, and
`FullNameRef::category_and_short_name` returns the category paired with the name
with that prefix removed. The twelve categories and their prefixes are:

| Category | Prefix | Worktree-private |
|---|---|---|
| `Tag` | `refs/tags/` | no |
| `LocalBranch` | `refs/heads/` | no |
| `RemoteBranch` | `refs/remotes/` | no |
| `Note` | `refs/notes/` | no |
| `MainPseudoRef` | `main-worktree/` | yes |
| `MainRef` | `main-worktree/refs/` | no |
| `PseudoRef` | (empty) | yes |
| `LinkedPseudoRef { name }` | `worktrees/` | yes |
| `LinkedRef { name }` | `worktrees/` | no |
| `Bisect` | `refs/bisect/` | yes |
| `Rewritten` | `refs/rewritten/` | yes |
| `WorktreePrivate` | `refs/worktree/` | yes |

`Category::prefix` returns the prefix from that table, and
`Category::is_worktree_private` returns the third column.

A **target** is what a reference holds. `Target::Object` holds an object id and
`Target::Symbolic` holds the full name of another reference; `TargetRef` is the
borrowed form of the same two shapes and must be copyable while `Target` must
not be. `Target::kind` and `Reference::kind` return `Kind::Object` or
`Kind::Symbolic` accordingly. `Target::try_id` returns the object id of an
object target and returns `None` for a symbolic target; `Target::id` returns the
object id of an object target and must panic for a symbolic target;
`Target::try_name` returns the referent of a symbolic target and returns `None`
for an object target; `Target::to_ref` returns the borrowed form. Displaying a
`Target` must produce the hexadecimal object id for an object target and the
five characters `ref: ` followed by the referent name for a symbolic target;
this rendering is observable in two error messages defined under Error
Semantics.

A **reference** as reported by a lookup is `Reference`, carrying its full name,
its target and an optional already-peeled object id. A reference as reported by
a loose-only lookup is `loose::Reference`, carrying only a full name and a
target. Conversion must exist in both directions between them, and from a packed
record into `Reference`.

A **store** is opened over a git directory. `file::Store::at` takes the git
directory and the hash kind and uses default options; `file::Store::at_opts`
takes the git directory, the hash kind and an options value carrying the reflog
write mode, the precomposed-unicode flag and the reserved-device-name flag. Four
fields of a store are public and must be assignable after construction:
`write_reflog`, `namespace`, `prohibit_windows_device_names` and
`precompose_unicode`. `file::Store::git_dir` returns the directory the store was
opened at.

`store::WriteReflog` has three modes and `Normal` must be its default:

- `Always` — every change writes a log entry, whatever the reference name.
- `Normal` — a change writes a log entry when a log already exists for that
  name, when the edit forces creation, or when the name matches the
  automatic-creation rule stated under Reference Logs.
- `Disable` — no change writes a log entry.

A store carries an optional **namespace**. `namespace::expand` turns a partial
name into a namespace by prefixing each of its slash-separated components:
expanding `foo` yields `refs/namespaces/foo/` and expanding `foo/bar` yields
`refs/namespaces/foo/refs/namespaces/bar/`, a repeated prefix rather than a
concatenation. When a store carries a namespace, every reference path and every
reference-log path a transaction touches must be prefixed with it, while the
edits the transaction returns must carry the caller's unprefixed names. A caller
that submits a namespaced batch must therefore be unable to observe the
namespace in the returned edits.

## Describing an Edit

A single change is a `RefEdit`: a `change`, a `name` and a `deref` flag. The
flag requests that a symbolic reference be followed and the change applied to
what it points at; the flag's effect is defined under Edit Preprocessing.

`Change` has exactly two shapes, both struct variants:

- `Change::Update { log, expected, new }` sets the reference to `new`.
- `Change::Delete { expected, log }` removes the reference.

`Change::new_value` returns the borrowed new target of an update and returns
`None` for a deletion. `Change::previous_value` returns the borrowed target
carried by the expectation when the expectation is `MustExistAndMatch` or
`ExistingMustMatch`, and returns `None` for the other three expectations and for
any change whose expectation carries no target.

`PreviousValue` states what the caller expects to find. Its five branches are:

- `Any` — impose no expectation.
- `MustExist` — a reference of any value must be there.
- `MustNotExist` — no reference must be there.
- `MustExistAndMatch(target)` — a reference must be there and must hold exactly
  `target`.
- `ExistingMustMatch(target)` — if a reference is there it must hold exactly
  `target`; absence is accepted.

`LogChange` carries the log `mode`, a `force_create_reflog` flag and a
`message`. Its default value must be mode `RefLog::AndReference`,
`force_create_reflog` false and an empty message; `RefLog` itself must not carry
a default. `RefLog::AndReference` requests that both the reference and its log
be written; `RefLog::Only` requests that only the log be written and that the
reference itself be left untouched. `Change::Delete` carries the same
enumeration directly: `AndReference` deletes both the reference and its log,
`Only` deletes only the log.

## Edit Preprocessing

`RefEditsExt` is implemented for `Vec<E>` where `E` borrows and mutably borrows
a `RefEdit`, and provides three operations.

**Duplicate detection.** `assure_one_name_has_one_edit` returns `Ok(())` when
every name in the list appears at most once. When some name appears more than
once it must return `Err` carrying that duplicated name as a byte string. The
check compares whole names for equality; two names that differ in any byte are
distinct.

**Symbolic splitting.** `extend_with_splits_of_symbolic_refs` takes a `find`
callback that maps a partial name to a target and a `make_entry` callback that
turns an index and a new edit into a list element. It scans the list for edits
whose `deref` flag is set, and for each such edit:

1. It must clear the edit's `deref` flag unconditionally, whether or not a split
   follows. An edit naming something that is not a symbolic reference, or naming
   something that does not exist, must therefore emerge with `deref` false and
   otherwise unchanged.
2. It calls `find` with the edit's name converted to a partial name. A split
   happens only when `find` returns a symbolic target; an object target and a
   missing entry both produce no split.
3. When a split happens, a new edit is appended naming the referent, with
   `deref` set to true, and the original edit is rewritten in place:
   - For `Change::Delete`, the new edit receives a clone of the original
     expectation and the original log mode, and the original edit's log mode
     becomes `RefLog::Only`.
   - For `Change::Update`, the new edit receives the original expectation and
     the original `LogChange`, and the original edit's `LogChange` becomes the
     same message and the same `force_create_reflog` flag with mode
     `RefLog::Only`, while the original edit's expectation becomes
     `PreviousValue::Any`.
4. The index passed to `make_entry` is the position of the edit that produced
   the split, so a caller is able to record parentage.

Splitting repeats over the newly appended edits, because a referent is itself
permitted to be symbolic. Each pass over the newly appended tail is one round.
When a round appends nothing, the operation returns `Ok(())`. When the round
counter reaches five and edits are still being appended, the operation must
return an I/O error of kind `WouldBlock` whose message is exactly
`Could not follow all splits after 5 rounds, assuming reference cycle`.

**Combined preprocessing.** `pre_process` runs splitting first and duplicate
detection second, and must have a default body that does exactly that. When
duplicate detection reports a name, `pre_process` must convert it into an I/O
error of kind `AlreadyExists` whose message is `A reference named '` followed by
the name, followed by `' has multiple edits`. Running the two steps in this
order is observable: a batch that names `HEAD` with `deref` set and also names
`HEAD`'s referent directly passes duplicate detection before splitting and fails
it after, and the reported name must be the referent's.

## Preparing a Transaction

`file::Store::transaction` returns a transaction bound to the store.
`Transaction::packed_refs` consumes the transaction and returns it with a packed
reference mode attached; the default mode is `PackedRefs::DeletionsOnly`.
`Transaction::prepare` consumes the transaction, takes the edits, a lock-failure
mode for the loose reference files and a separate lock-failure mode for the
packed reference file, and returns the prepared transaction. Calling `prepare`
more than once on one transaction must panic.

### Locking and Durability Delegation

The lock and temporary-file libraries named in Appendix A provide the lock
itself: the name and byte content of a lock file, the sequence of system calls
that creates it and publishes it over the resource, the retry behavior of a
blocking acquisition, the removal of lock files when a process exits, and any
flushing to durable storage. An implementation must obtain all of that from
those libraries and must not define it here.

What this library owns, and what this document therefore specifies in full, is:

- **which** resources are locked and **in what order** — one lock per edited
  reference, taken in the order the edits appear in the list after
  preprocessing, plus at most one lock over the packed reference file, taken
  before any reference lock;
- **the classification of an acquisition failure** — see below;
- **which name a lock failure is reported against** — see below;
- **the completeness of a rollback** — see Rolling Back a Prepared Transaction;
- **the compare-and-swap decision** — see below;
- **the order in which a commit publishes its parts** — see Committing a
  Transaction.

### Preparation Steps

Preparation runs the following steps in this order.

1. **Preprocess the edits.** The combined preprocessing of the previous section
   runs first, with a `find` callback that looks up existing references and
   never consults the packed reference file for a symbolic target. An error from
   preprocessing must be returned as
   `prepare::Error::PreprocessingFailed(<the io error>)`.

2. **Decide whether a packed transaction is needed, and prepare it.** A packed
   transaction must be started when the packed mode is one of the two update
   modes, or when a packed reference file exists, or when a lock over the packed
   reference file exists. Within that, each edit whose log mode is `RefLog::Only`
   is skipped entirely, and each remaining edit is classified by the packability
   of its name (see Packed Reference Updates). An edit whose name is not
   packable is skipped. Of the rest: in an update mode, an update to an object
   target becomes a packed edit under the possibly-shortened name; a deletion
   always becomes a packed edit under the possibly-shortened name; and an update
   whose expectation carries a target, or any other remaining shape, marks that
   the packed file must be consulted for current values. A packed transaction is
   started only when at least one packed edit exists or the packed file must be
   consulted. Failure to acquire the packed file's lock must be returned as
   `prepare::Error::PackedTransactionAcquire(<the acquisition error>)`, and
   failure to open the packed buffer must be returned as
   `prepare::Error::Packed(<the open error>)`.

3. **Process each edit in list order.** For each edit, in order:

   a. **Reject reserved device names first.** When the store's
      `prohibit_windows_device_names` flag is set and the name contains a
      reserved device name component, the edit must fail **before** its lock is
      acquired. This ordering is observable: the failure must be the
      device-name failure and no lock file must exist afterwards.

   b. **Acquire the lock** over the reference's path, using the loose
      lock-failure mode. For a deletion the lock is taken to hold the resource;
      for an update it is taken to update the resource.

   c. **Read the current value under the lock.** The current value is the loose
      file's content when a loose file exists, and otherwise the packed
      record's content when a packed buffer is in play, and otherwise absent. A
      loose file whose content fails to decode must be treated as absent rather
      than raising.

   d. **Evaluate the expectation** against what was read, as tabulated below.

   e. **Rewrite the expectation to the value that was found.** When a value was
      found, the edit's expectation must be replaced with
      `PreviousValue::MustExistAndMatch(<the value found>)`, regardless of what
      the caller supplied. When nothing was found, the caller's expectation must
      be left as it is. This rewrite happens on both updates and deletions, and
      is what the caller observes in the edits returned by commit or rollback.

   f. **Stage the new content** for an update, as described under Staging.

4. **Propagate the referent's previous object id upward.** After an edit
   produced by splitting has been processed, if its expectation now carries an
   object target, that object id must be recorded on every edit up the parentage
   chain that produced it. This is what allows a `HEAD` log entry to name the
   object ids of the branch `HEAD` points at.

### The Compare-and-Swap Decision

For `Change::Update`, with `found` being the value read under the lock:

| Expectation | `found` is absent | `found` is present |
|---|---|---|
| `Any` | accept | accept |
| `MustExist` | `Error::MustExist { full_name, expected: Target::Object(<null id of the store's hash kind>) }` | accept |
| `MustNotExist` | accept | accept when the found value equals `new`; otherwise `Error::MustNotExist { full_name, actual: <found>, new }` |
| `MustExistAndMatch(p)` | `Error::MustExist { full_name, expected: p }` | accept when `p` equals the found value; otherwise `Error::ReferenceOutOfDate { full_name, expected: p, actual: <found> }` |
| `ExistingMustMatch(p)` | accept | accept when `p` equals the found value; otherwise `Error::ReferenceOutOfDate { full_name, expected: p, actual: <found> }` |

The `MustNotExist`-with-a-present-value cell is deliberate: re-creating a
reference with the value it already holds must succeed rather than raise.

For `Change::Delete`:

| Expectation | `found` is absent | `found` is present |
|---|---|---|
| `Any` | accept | accept |
| `MustExist` | `Error::DeleteReferenceMustExist { full_name }` | accept |
| `MustNotExist` | panic — the combination is a programming error | panic |
| `MustExistAndMatch(p)` | `Error::DeleteReferenceMustExist { full_name }` | accept when `p` equals the found value; otherwise `Error::ReferenceOutOfDate { full_name, expected: p, actual: <found> }` |
| `ExistingMustMatch(p)` | accept | accept when `p` equals the found value; otherwise `Error::ReferenceOutOfDate { full_name, expected: p, actual: <found> }` |

Comparison is equality of whole targets: an object target equals an object
target with the same id, a symbolic target equals a symbolic target with the
same referent name, and an object target never equals a symbolic target.

### Staging

An update is **effective** when the new target differs from the value found, and
is effective unconditionally when nothing was found. An update is **symbolic**
when its new target is symbolic, or when nothing was found and the new target is
symbolic.

The loose file must be written into the lock, without publishing it, when the
update is effective and the update is not being routed into the packed file, and
also whenever the update is symbolic — a symbolic target must always be written
to a loose file, because the packed file holds no symbolic records. The content
written is the hexadecimal object id followed by a newline for an object target,
and `ref: ` followed by the referent name followed by a newline for a symbolic
target.

When the update is routed into the packed file and its new target is an object,
the lock must be retained even though nothing is written into it, because the
loose file it covers is deleted at commit time.

A deletion writes nothing during preparation; its lock exists only to hold the
resource.

### Classification and Attribution of Lock Failures

An acquisition failure that is an underlying I/O error must be returned as
`prepare::Error::Io(<that io error>)`. Every other acquisition failure must be
returned as `prepare::Error::LockAcquire { source, full_name }`. This split is
observable and is not a detail: when a reference named `a` exists as a file and
an edit names `a/b`, the attempt to place `a/b`'s lock fails because `a` is not
a directory, and the failure must surface as `Io` carrying an error of kind
`NotADirectory` — never as `LockAcquire`. `LockAcquire` is reserved for a lock
that is genuinely held by someone else.

When a `LockAcquire` failure arises on an edit that splitting produced, the
`full_name` reported must be the name of the **original** edit at the root of
the parentage chain, not the name of the edit that failed. An attempt to update
`HEAD` with dereferencing, when `HEAD`'s referent is already locked, must
therefore report `HEAD`.

## Rolling Back a Prepared Transaction

`Transaction::rollback` consumes a prepared transaction and returns the edits.
It must not return a result type: rolling back must not fail.

Dropping a prepared transaction without committing must have exactly the same
effect on disk as calling `rollback`. Both must leave no trace of the
preparation:

- every lock file placed during preparation must be gone;
- every directory created during preparation to hold a lock must be gone, up to
  and including the topmost one that preparation created — a store that had no
  `refs` directory before preparation must have no `refs` directory after;
- no loose reference file, packed reference file or reference log must have been
  created, modified or removed.

The edits `rollback` returns are the edits as preparation left them: split into
their referents, with `deref` flags cleared on the originating edits, and with
expectations rewritten to the values found on disk. They are not the edits the
caller submitted.

Preparation itself rolls back the same way on failure. When `prepare` returns an
error, the store must be in the state it was in before `prepare` was called.

## Committing a Transaction

`Transaction::commit` consumes a prepared transaction, takes a committer
signature reference or nothing, and returns the edits. The committer parameter
accepts anything convertible into an optional signature reference, so passing a
signature reference directly and passing `None` must both compile.

An edit whose `deref` flag is still set at commit time is a programming error
and must panic; preparation clears every such flag, so this state is
unreachable through the public interface.

Commit runs four phases, in this exact order. The order is observable, and a
failure in an earlier phase must leave the later phases unrun.

### Phase 1 — Apply updates

For each edit that is a `Change::Update`, in list order:

- With log mode `RefLog::Only`, the reference itself must not be written and
  only the log entry is produced.
- With log mode `RefLog::AndReference`, the log entry is produced **first**, and
  the reference is then published by committing its lock.

The log entry for an update is determined by the new target:

- **New target is symbolic.** No log entry is written, unless the edit's
  expectation is exactly `PreviousValue::ExistingMustMatch(Target::Object(id))`,
  in which case one entry is written whose previous object id is the null id of
  that id's hash kind and whose new object id is `id`.
- **New target is an object.** The previous object id is the object id carried
  by the expectation when the expectation is
  `PreviousValue::MustExistAndMatch(Target::Object(id))`, and is otherwise the
  object id propagated up from the referent during preparation, and is otherwise
  absent. An entry is written only when that previous object id differs from the
  new object id; an update that does not change the object id must write no log
  entry.

Publishing the reference is committing its lock over the reference's path. When
that commit fails because the path is occupied by a directory, the directory
must be removed depth-first while it is empty and the commit retried once. Any
other failure, and a failure of the retry, must be returned as
`commit::Error::LockCommit { source, full_name }`.

### Phase 2 — Remove reference logs for deletions

For each edit that is a `Change::Delete`, the reference log file at the log path
for that name must be removed. A removal that fails because the file is not
there must be treated as success; any other failure must be returned as
`commit::Error::DeleteReflog { full_name, source }`.

After removing a log, every directory that became empty must be removed,
walking upward and stopping at the reference-log root. The reference-log root
itself must never be removed.

### Phase 3 — Commit the packed reference file

When a packed transaction was prepared, it is committed here. A failure must be
returned as `commit::Error::PackedTransactionCommit(<the packed commit error>)`.
After a successful packed commit, the store's cached view of the packed file
must be refreshed so that a lookup performed immediately afterwards observes the
new content; a failure to refresh must be ignored rather than raised.

### Phase 4 — Remove loose reference files

Loose files are removed last, and only when phase 3 either succeeded or was not
needed. For each edit, in list order:

- A `Change::Update` whose log mode is `RefLog::AndReference` and whose new
  target is an object has its loose file removed **only** when the update was
  routed into the packed file. This is what makes a packed update remove the
  loose file that used to shadow it.
- A `Change::Delete` whose log mode is `RefLog::AndReference` has its loose file
  removed.
- Every other edit removes nothing.

A removal that fails because the file is not there must be treated as success;
any other failure must be returned as
`commit::Error::DeleteReference { full_name, err }`.

The consequence of phases 3 and 4 together is the deletion guarantee: deleting a
reference that exists both as a loose file and as a packed record must remove
both, and a subsequent lookup must report that the reference is gone.

### What commit returns

Commit returns the edits, in the order preparation left them, with the
expectations preparation rewrote. A caller that submitted one edit naming a
symbolic reference with dereferencing receives two edits. A caller that
submitted an edit with `PreviousValue::Any` against an existing reference
receives an edit whose expectation is
`PreviousValue::MustExistAndMatch(<the previous value>)`.

## Packed Reference Updates

`PackedRefs` selects how a transaction treats the packed reference file. Its
three modes are:

- `DeletionsOnly` — deletions are applied to the packed file; no update is ever
  written into it. This is the default.
- `DeletionsAndNonSymbolicUpdates(Box<dyn gix_object::Find + 'a>)` — deletions
  are applied, and updates whose new target is an object are written into the
  packed file as well, with each such object peeled through its annotated-tag
  chain using the supplied object database.
- `DeletionsAndNonSymbolicUpdatesRemoveLooseSourceReference(Box<dyn gix_object::Find + 'a>)` —
  as above, and additionally each loose file whose reference was written into
  the packed file is removed at commit time.

A reference name is **packable** according to its category. A name whose
category is `Bisect`, `Rewritten`, `WorktreePrivate`, `LinkedPseudoRef`,
`PseudoRef` or `MainPseudoRef` must never be written into the packed file and
must never be looked for in it. A name whose category is `Tag`, `LocalBranch`,
`RemoteBranch` or `Note` is packable under its own full name. A name whose
category is `MainRef` or `LinkedRef` is packable under its **shortened** name —
the name with the category prefix removed — and only when that shortened name's
own category is not worktree-private. A name with no recognised category is
packable under its own full name.

Preparing the packed side of a transaction applies, in this order: unicode
precomposition of each name when the store's precompose flag is set; the store's
namespace prefix; the packability rule above. It then drops every deletion whose
name is not present in the packed file, because deleting what is not there
writes nothing. For each update whose new target is an object, in an update
mode, the object is peeled: the object is looked up, and while it is an
annotated tag its target is followed, so the peeled id is the first non-tag
object reached. When the first object looked up is not a tag, the record carries
no peeled id. An object that the database does not contain must produce
`packed::transaction::prepare::Error::Resolve` whose message is `Couldn't find
object with id ` followed by the hexadecimal id.

When the prepared packed edit list is empty, the packed transaction must close
its lock without publishing anything, leaving the packed file untouched.

Committing the packed side writes a whole new file, never a patch. Its first
line must be exactly:

```
# pack-refs with: peeled fully-peeled sorted 
```

— including the trailing space before the newline. The remaining lines are the
existing records and the edits merged by name in ascending byte order: where an
existing record sorts before the next edit it is copied through; where an edit
sorts before or equal to the next existing record the edit is written and, on
equality, the existing record is dropped. A deletion writes nothing, which is
how it removes the record. An update writes the hexadecimal object id, a space,
the name and a newline, followed — when a peeled id exists — by a line
consisting of `^`, the hexadecimal peeled id and a newline. A symbolic target
must never reach this writer.

When the merge writes no record at all, the packed file must be removed from
disk rather than published as an empty or header-only file.

A buffer opened over a packed file this library wrote must report exactly the
records that were written: each record's name, its target as the hexadecimal
text of the object id, and its object as the hexadecimal text of the peeled id
where one was written and nothing otherwise.

## Reference Logs

A reference log lives at `logs/` followed by the reference's name, under the
store's git directory, with the store's namespace applied to the name.

### Line format

`log::Line` owns one entry and `file::log::LineRef` borrows one. Both carry the
previous object id, the new object id, the signature and the message in four
public fields of those names. The owned form holds two `ObjectId`s, a
`gix_actor::Signature` and a `BString`. The borrowed form holds the two object
ids **as their undecoded hexadecimal text** — each a `&BStr`, not a decoded id —
together with a `gix_actor::SignatureRef` and a `&BStr` message, and it must be
copyable. `LineRef::previous_oid` and `LineRef::new_oid` decode those two fields
and return owned object ids; both must panic if the field is not valid
hexadecimal, which decoding a line makes unreachable. `LineRef::to_owned`
produces the owned form, and a conversion from `LineRef` into `Line` must exist
and must perform the same decoding.

`LineRef::from_bytes` decodes one line. It parses **only up to the first
newline**; bytes after that newline are ignored rather than rejected. The
accepted shape is the hexadecimal previous id, a space, the hexadecimal new id,
a space, the committer signature, and, when a message is present, a tab
followed by the message.
Absence of the tab yields an empty message. Trailing bytes that are neither a
tab nor a newline after the signature must be rejected. A line that does not
match must produce a decode error carrying the offending input — the first line
of it, without its newline — in a public `input` field of type `BString`, whose
display is the debug rendering of that input followed by ` did not match
'<old-hexsha> <new-hexsha> <name> <<email>> <timestamp> <tz>\t<message>'`. The
module holding that error type must not be exported, so the type is reachable
only as the error of this operation and is never named by a caller; the display
text is what a caller observes.

`Line::write_to` writes the previous id, a space, the new id, a space, the
signature, and then always a tab, the message and a newline — the tab and the
newline are written even when the message is empty. A message containing a
newline must be rejected with an I/O error whose message is exactly `Messages
must not contain newlines (\n)`, and nothing must be written in that case.

### Appending an entry

Appending happens as part of a commit and is governed by the store's reflog
mode. With mode `Disable`, nothing is written and the operation succeeds. With
mode `Always`, the entry is written and its log file is created if missing,
whatever the name. With mode `Normal`, the file is created if missing only when
the edit forces creation or the name qualifies for automatic creation; otherwise
the entry is appended only if the file already exists, and its absence is not an
error.

A name qualifies for automatic creation when it begins with `refs/heads/`,
`refs/remotes/`, `refs/notes/` or `refs/worktree/`, or when it is exactly
`HEAD`. No other name qualifies.

Creating a log file creates the directories leading to it; a failure must be
returned as `file::log::create_or_update::Error::CreateLeadingDirectories {
source, reflog_directory }`. When opening the file fails because a directory
occupies its path, that directory must be removed depth-first while empty and
the open retried once; any other failure, and a failure of the retry, must be
returned as `file::log::create_or_update::Error::Append { source, reflog_path }`.

The bytes appended are the previous object id — or the null id of the new id's
hash kind when no previous id is known — a space, the new object id, a space,
the committer signature with surrounding whitespace trimmed from its name and
email, and then, when the message is non-empty, a tab, the message and a
newline, and when the message is empty, a newline alone. Appending an entry with
no committer must return
`file::log::create_or_update::Error::MissingCommitter`, and a message containing
a newline must return
`file::log::create_or_update::Error::MessageWithNewlines`.

### Reading forward

`file::log::iter::forward` takes the bytes of a whole log and returns an
iterator yielding each line, oldest first, as
`Result<file::log::LineRef<'_>, file::log::iter::decode::Error>`. A malformed
line yields an error carrying its one-based line number counted from the
beginning, and the error's display is `In line `, the number, `: ` and the
underlying decode error.

### Reading backward

`file::log::iter::reverse` takes a value that reads and seeks, plus a mutable
buffer, and returns an iterator yielding lines newest first as
`Result<log::Line, file::log::iter::reverse::Error>`. It seeks to the end and
reads backward in buffer-sized blocks.

The buffer is a contract, not an implementation detail:

- A zero-sized buffer must be rejected before any read, with an I/O error whose
  message is exactly `Zero sized buffers are not allowed, use 256 bytes or more
  for typical logs`.
- A buffer too small to hold one whole line must produce an I/O error whose
  message is `buffer too small for line size, got until ` followed by the debug
  rendering of the bytes that were read. The failure surfaces when the
  oversized line is reached, not before, so a small buffer that happens to fit
  every line must work.

A malformed line yields
`file::log::iter::reverse::Error::Decode(<the decode error>)`, whose line
numbering counts from the end: the newest line is `1 from the end`, so the
display of an error on the newest line ends with `In line 1 from the end: `
followed by the underlying decode error. A read failure yields
`file::log::iter::reverse::Error::Io(<the io error>)`.

### Access through the store

`file::Store::reflog_exists` takes anything convertible into a `&FullNameRef`
and returns whether the log file exists, as `Result<bool, E>` where `E` is the
name-conversion error — this operation reports no other failure.

`file::Store::reflog_iter` takes a name and a mutable byte vector, fills the
vector with the whole log and returns a forward iterator over it, or `None`. It
must return `None` both when the log file does not exist and when a directory
occupies its path.

`file::Store::reflog_iter_rev` takes a name and a mutable byte slice and returns
a reverse iterator over the log, or `None`, with the same two `None` conditions.
The buffer rules of the previous section apply.

Both return `file::log::Error::RefnameValidation` when the name is invalid and
`file::log::Error::Io` for any other read failure.

A `file::loose::Reference` reaches its own log through three methods of its own,
each taking the store to read from as an argument: `log_exists` reports whether
the log file exists, `log_iter_rev` returns a reverse iterator over the log or
`None`, and `log_iter` returns a forward iterator over the log or `None`. The
three are the delegating form of the three store operations above — each must
pass the reference's own name to `file::Store::reflog_exists`,
`file::Store::reflog_iter_rev` and `file::Store::reflog_iter` respectively and
must report exactly what that operation reports, including both `None`
conditions and the buffer rules of the previous section.

The delegating form narrows the error. A name held by a `file::loose::Reference`
has already been validated, so the name-validation arm of the store's error is
unreachable from these three methods: `log_exists` returns a bare `bool` rather
than a result, and the two iterator methods return `std::io::Error` rather than
`file::log::Error`. An implementation must panic if the name-validation arm is
nevertheless reached from one of these three methods, and must never convert it
into an I/O error.

`ReferenceExt::log_iter` returns a `file::log::iter::Platform` borrowing the
reference's name and the store, and `ReferenceExt::log_exists` reports whether
the log exists. The platform's `buf` field is public and holds the bytes.
`Platform::all` clears the buffer and returns a forward iterator or `None`;
`Platform::rev` clears the buffer, resizes it to 4096 zero bytes and returns a
reverse iterator or `None`. The platform must be marked such that discarding it
without use is diagnosed.

═══════════════════════════ Contract Layer ═══════════════════════════

## State Model

The store on disk holds one logical fact — the current target of every
reference — encoded in up to three places at once, plus a side record of how
each reference got where it is.

**Loose encoding.** One file per reference, at the reference's name under the
git directory. Its content must be a hexadecimal object id and a newline, or
`ref: `, a referent name and a newline, and nothing else.

**Packed encoding.** One file, `packed-refs`, whose first line must be the
header this document fixes and whose remaining lines must be records sorted by
name in ascending byte order. A record holds an object id and a name, followed
by a peeled-object line when a peeled id was written for it. A record must never
be symbolic.

**Log encoding.** One append-only file per reference, under `logs/` at the
reference's name. Each line records a transition from a previous object id to a
new object id together with who made it and why, and a line once written must
never be rewritten or removed except by deleting the whole file.

**Lock state.** A resource under change carries a lock, which is transient. A
lock must exist only between preparation and commit or rollback of one
transaction, and no lock must survive either outcome.

A transaction moves through three states. **Unprepared** — created from a store,
given a packed-refs mode or left at the default one, has taken no lock and
changed nothing.
**Prepared** — holds every lock it needs, has read and checked every current
value, and has staged content that is not published; while a transaction is
prepared the store must be unchanged as observed by any reader. **Concluded** —
either committed, meaning the staged content is published and the logs are
written, or rolled back, meaning every lock and every directory preparation
created is gone.

The transitions must be one-way: an unprepared transaction goes only to
prepared, a prepared transaction goes only to concluded, and both `commit` and
`rollback` must consume the transaction, so a concluded transaction must not be
reachable again.

## Error Semantics

Every error type below is a public enumeration deriving `Debug` and
implementing `std::error::Error` and `Display`; the display text of each variant
is given as the doc-attribute-style string beside it and is part of the
contract, because it is what a caller renders. Every `#[from]` conversion listed
must exist.

**Preparation.**

```rust
// gix_ref::file::transaction::prepare::Error
pub enum Error {
    /// "The packed ref buffer could not be loaded"
    Packed(#[from] crate::packed::buffer::open::Error),
    /// "The lock for the packed-ref file could not be obtained"
    PackedTransactionAcquire(#[source] gix_lock::acquire::Error),
    /// "The packed transaction could not be prepared"
    PackedTransactionPrepare(#[from] crate::packed::transaction::prepare::Error),
    /// "The packed ref file could not be parsed"
    PackedFind(#[from] crate::packed::find::Error),
    /// "Edit preprocessing failed with an error"
    PreprocessingFailed(#[source] std::io::Error),
    /// "A lock could not be obtained for reference {full_name:?}"
    LockAcquire { source: gix_lock::acquire::Error, full_name: gix_object::bstr::BString },
    /// "An IO error occurred while applying an edit"
    Io(#[from] std::io::Error),
    /// "The reference {full_name:?} for deletion did not exist or could not be parsed"
    DeleteReferenceMustExist { full_name: gix_object::bstr::BString },
    /// "Reference {full_name:?} was not supposed to exist when writing it with value {new:?}, but actual content was {actual:?}"
    MustNotExist { full_name: gix_object::bstr::BString, actual: crate::Target, new: crate::Target },
    /// "Reference {full_name:?} was supposed to exist with value {expected}, but didn't."
    MustExist { full_name: gix_object::bstr::BString, expected: crate::Target },
    /// "The reference {full_name:?} should have content {expected}, actual content was {actual}"
    ReferenceOutOfDate { full_name: gix_object::bstr::BString, expected: crate::Target, actual: crate::Target },
    /// "Could not read reference"
    ReferenceDecode(#[from] crate::file::loose::reference::decode::Error),
}
```

`MustExist`, `MustNotExist` and `ReferenceOutOfDate` render their targets: the
debug rendering for `MustNotExist`'s two targets, and the display rendering — a
hexadecimal id, or `ref: ` and a name — for `MustExist`'s `expected` and
`ReferenceOutOfDate`'s `expected` and `actual`.

**Commit.**

```rust
// gix_ref::file::transaction::commit::Error
pub enum Error {
    /// "The packed-ref transaction could not be committed"
    PackedTransactionCommit(#[source] crate::packed::transaction::commit::Error),
    /// "Edit preprocessing failed with error"
    PreprocessingFailed { source: std::io::Error },
    /// "The change for reference {full_name:?} could not be committed"
    LockCommit { source: std::io::Error, full_name: gix_object::bstr::BString },
    /// "The reference {full_name} could not be deleted"
    DeleteReference { full_name: gix_object::bstr::BString, err: std::io::Error },
    /// "The reflog of reference {full_name:?} could not be deleted"
    DeleteReflog { full_name: gix_object::bstr::BString, source: std::io::Error },
    /// "The reflog could not be created or updated"
    CreateOrUpdateRefLog(#[from] crate::file::log::create_or_update::Error),
}
```

`DeleteReference` renders its name without quotes; the other three name-carrying
variants render theirs with the debug rendering, which quotes them.

**Packed transaction.**

```rust
// gix_ref::packed::transaction::prepare::Error
pub enum Error {
    /// "Could not close a lock which won't ever be committed"
    CloseLock(#[from] std::io::Error),
    /// "The lookup of an object failed while peeling it"
    Resolve(#[from] Box<dyn std::error::Error + Send + Sync + 'static>),
}

// gix_ref::packed::transaction::commit::Error
pub enum Error {
    /// "Changes to the resource could not be committed"
    Commit(#[from] gix_lock::commit::Error<gix_lock::File>),
    /// "Some references in the packed refs buffer could not be parsed"
    Iteration(#[from] crate::packed::iter::Error),
    /// "Failed to write a ref line to the packed ref file"
    Io(#[from] std::io::Error),
}
```

**Reference logs.**

```rust
// gix_ref::file::log::create_or_update::Error
pub enum Error {
    /// "Could create one or more directories in {reflog_directory:?} to contain reflog file"
    CreateLeadingDirectories { source: std::io::Error, reflog_directory: std::path::PathBuf },
    /// "Could not open reflog file at {reflog_path:?} for appending"
    Append { source: std::io::Error, reflog_path: std::path::PathBuf },
    /// "reflog message must not contain newlines"
    MessageWithNewlines,
    /// "reflog messages need a committer which isn't set"
    MissingCommitter,
}

// gix_ref::file::log::Error
pub enum Error {
    /// "The reflog name or path is not a valid ref name"
    RefnameValidation(#[from] crate::name::Error),
    /// "The reflog file could not read"
    Io(#[from] std::io::Error),
}

// the error of LineRef::from_bytes — its module is NOT exported, so this type
// is reachable only as that operation's error type and is never named by a caller
pub struct Error { pub input: gix_object::bstr::BString }   // derives Debug; impl Display + std::error::Error
// Display: "{input:?} did not match '<old-hexsha> <new-hexsha> <name> <<email>> <timestamp> <tz>\t<message>'"

// gix_ref::file::log::iter::decode::Error   (fields private; derives Debug; impl Display + std::error::Error)
// Display: "In line {line}: {inner}"  where {line} renders as "N" for a forward
//   iterator and "N from the end" for a reverse iterator, N being one-based.

// gix_ref::file::log::iter::reverse::Error
pub enum Error {
    /// "The buffer could not be filled to make more lines available"
    Io(#[from] std::io::Error),
    /// "Could not decode log line"
    Decode(#[from] crate::file::log::iter::decode::Error),
}
```

**Lookup, as far as this document requires it.**

```rust
// gix_ref::file::find::Error
pub enum Error {
    /// "The ref name or path is not a valid ref name"
    RefnameValidation(#[from] crate::name::Error),
    /// "The ref file {path:?} could not be read in full"
    ReadFileContents { source: std::io::Error, path: std::path::PathBuf },
    /// "The reference at \"{relative_path}\" could not be instantiated"
    ReferenceCreation { source: crate::file::loose::reference::decode::Error, relative_path: std::path::PathBuf },
    /// "A packed ref lookup failed"
    PackedRef(#[from] crate::packed::find::Error),
    /// "Could not open the packed refs buffer when trying to find references."
    PackedOpen(#[from] crate::packed::buffer::open::Error),
}
// impl From<std::convert::Infallible> for Error

// gix_ref::file::find::existing::Error
pub enum Error {
    /// "An error occurred while trying to find a reference"
    Find(#[from] crate::file::find::Error),
    /// "The ref partially named {name:?} could not be found"
    NotFound { name: std::path::PathBuf },
}

// gix_ref::file::loose::reference::decode::Error
pub enum Error {
    /// "{content:?} could not be parsed"
    Parse { content: gix_object::bstr::BString },
    /// "The path {path:?} to a symbolic reference within a ref file is invalid"
    RefnameValidation { source: gix_validate::reference::name::Error, path: gix_object::bstr::BString },
}

// gix_ref::packed::find::Error
pub enum Error {
    /// "The ref name or path is not a valid ref name"
    RefnameValidation(#[from] crate::name::Error),
    /// "The reference could not be parsed"
    Parse,
}
// impl From<std::convert::Infallible> for Error

// gix_ref::packed::iter::Error
pub enum Error {
    /// "The header existed but could not be parsed: {invalid_first_line:?}"
    Header { invalid_first_line: gix_object::bstr::BString },
    /// "Invalid reference in line {line_number}: {invalid_line:?}"
    Reference { invalid_line: gix_object::bstr::BString, line_number: usize },
}

// gix_ref::packed::buffer::open::Error
pub enum Error {
    /// "The packed-refs file did not have a header or wasn't sorted and could not be iterated"
    Iter(#[from] crate::packed::iter::Error),
    /// "The header could not be parsed, even though first line started with '#'"
    HeaderParsing,
    /// "The buffer could not be opened or read"
    Io(#[from] std::io::Error),
}
```

Two failures are **panics** rather than errors, because they are programming
errors that a caller is unable to trigger through a correct sequence of calls:
calling `prepare` twice on one transaction, and submitting a deletion whose
expectation is `PreviousValue::MustNotExist`.

## Cross-View Invariants

**INV-1 — Deletion clears every encoding.** After a committed transaction that
deletes a reference with log mode `RefLog::AndReference`, no loose file exists
for that name, no packed record exists for that name, and no reference log file
exists for that name. A reference that existed in two encodings must not survive
in either.

**INV-2 — The returned expectation states what was on disk.** For every edit a
transaction returns from `commit` or from `rollback`, if a value existed for
that reference under the lock during preparation, the edit's expectation is
`PreviousValue::MustExistAndMatch` carrying exactly that value. This holds
whatever the caller supplied, and it holds for deletions as well as updates. If
no value existed, the caller's expectation is returned unchanged.

**INV-3 — A rollback is indistinguishable from never having prepared.** After
`rollback`, and equally after dropping a prepared transaction, the set of files
and directories under the git directory is exactly what it was before `prepare`
was called: no lock file, no reference file, no packed file, no log file, and no
directory that preparation created — including the topmost one. The same holds
after a failed `prepare`.

**INV-4 — A log entry accompanies exactly the object changes that happened.**
For every reference whose object id a committed transaction changed, whose log
mode was not `RefLog::Only`-with-no-log, and whose store reflog mode permitted
writing, the log gained exactly one line whose previous id is the id the
reference held before the transaction and whose new id is the id it holds after.
An update that left the object id unchanged added no line. A symbolic target
added no line, except in the one case named under Committing a Transaction.

**INV-5 — Splitting preserves the caller's intent and distributes it.** After
preparation of a batch containing one dereferencing edit, the returned edits
name the original reference and its referent; the referent's edit carries the
caller's expectation and the caller's log mode, the original's edit carries
`PreviousValue::Any` for an update and a log-only mode for both shapes, and no
edit anywhere in the returned list has `deref` still set. The object ids
recorded in the original's log entry are the referent's previous and new object
ids.

**INV-6 — The namespace is invisible to the caller.** When a store carries a
namespace, every path a transaction reads or writes — loose file, packed record
and log file alike — is under that namespace, while every name in every edit the
transaction returns is the unprefixed name the caller submitted. Two stores over
the same git directory with different namespaces must therefore be unable to
observe each other's references.

**INV-7 — What the packed writer wrote is what the packed reader reads.** A
buffer opened over a packed file this library committed reports one record per
edit that survived preparation, under the same name, with the same object id,
and with a peeled id exactly where the peeling step produced one. When
preparation left no record at all, no packed file exists.

**INV-8 — Preparation never publishes and commit never checks.** No observation
made between `prepare` returning and `commit` being called reports any change to
any reference, and no compare-and-swap decision is made during commit — every
expectation was resolved under a lock during preparation.

═══════════════════════════ Reference Layer ═══════════════════════════

## Public Interface

The library is delivered as one Rust library crate whose package name is
`gix-ref` and whose library name is `gix_ref`. Every path below is a path a
dependent crate resolves against that name. Every signature below is the
declared signature: a divergence in a name, a module path, a parameter order, a
lifetime, a generic bound, an ownership form or a return type is a divergence in
the contract, whatever the runtime behavior.

### Import Surface

```rust
gix_ref::{FullName, FullNameRef, PartialName, PartialNameRef, Namespace,
          Kind, Category, Target, TargetRef, Reference}
gix_ref::bstr                     // a re-export of gix_object::bstr
gix_ref::name                     // module
gix_ref::namespace                // module
gix_ref::transaction              // module
gix_ref::log                      // module
gix_ref::file                     // module
gix_ref::packed                   // module
gix_ref::store                    // module
```

The two modules `gix_ref::file` and `gix_ref::packed` must be re-exports from a
private module, so their inner path is not part of the surface.

### API Catalog

#### `gix_ref` — names

```rust
#[derive(PartialEq, Eq, Debug, Hash, Ord, PartialOrd, Clone)]
pub struct FullName(/* private */);

#[derive(Hash, Debug, PartialEq, Eq, Ord, PartialOrd)]
#[repr(transparent)]
pub struct FullNameRef(/* private, unsized */);

#[derive(PartialEq, Eq, Debug, Hash, Ord, PartialOrd, Clone)]
pub struct PartialName(/* private */);

#[derive(PartialEq, Eq, Debug, Hash, Ord, PartialOrd)]
#[repr(transparent)]
pub struct PartialNameRef(/* private, unsized */);

#[derive(PartialEq, Eq, Debug, Hash, Ord, PartialOrd, Clone)]
pub struct Namespace(/* private */);

impl FullName {
    pub fn to_path(&self) -> &std::path::Path;
    pub fn into_inner(self) -> gix_object::bstr::BString;
    pub fn as_bstr(&self) -> &gix_object::bstr::BStr;
    pub fn prefix_namespace(&mut self, namespace: &Namespace) -> &mut Self;
    pub fn strip_namespace(&mut self, namespace: &Namespace) -> &mut Self;
    pub fn shorten(&self) -> &gix_object::bstr::BStr;
    pub fn category(&self) -> Option<Category<'_>>;
    pub fn category_and_short_name(&self) -> Option<(Category<'_>, &gix_object::bstr::BStr)>;
}

impl FullNameRef {
    pub fn as_partial_name(&self) -> &PartialNameRef;
    pub fn to_path(&self) -> &std::path::Path;
    pub fn as_bstr(&self) -> &gix_object::bstr::BStr;
    pub fn shorten(&self) -> &gix_object::bstr::BStr;
    pub fn category(&self) -> Option<Category<'_>>;
    pub fn category_and_short_name(&self) -> Option<(Category<'_>, &gix_object::bstr::BStr)>;
    pub fn file_name(&self) -> &gix_object::bstr::BStr;
}

impl PartialName {
    pub fn join(self, component: &gix_object::bstr::BStr) -> Result<Self, gix_ref::name::Error>;
}

impl PartialNameRef {
    pub fn to_partial_path(&self) -> &std::path::Path;
    pub fn as_bstr(&self) -> &gix_object::bstr::BStr;
}

// conversions into FullName
impl TryFrom<&str>     for FullName { type Error = gix_validate::reference::name::Error; }
impl TryFrom<String>   for FullName { type Error = gix_validate::reference::name::Error; }
impl TryFrom<&gix_object::bstr::BStr>     for FullName { type Error = gix_validate::reference::name::Error; }
impl TryFrom<gix_object::bstr::BString>   for FullName { type Error = gix_validate::reference::name::Error; }
impl TryFrom<&gix_object::bstr::BString>  for FullName { type Error = gix_validate::reference::name::Error; }
impl From<FullName> for gix_object::bstr::BString;
impl<'a> From<&'a FullNameRef> for &'a gix_object::bstr::BStr;
impl<'a> From<&'a FullNameRef> for FullName;
impl std::fmt::Display for FullName;
impl std::fmt::Display for FullNameRef;
impl std::borrow::Borrow<FullNameRef> for FullName;
impl AsRef<FullNameRef> for FullName;
impl ToOwned for FullNameRef { type Owned = FullName; }

// conversions into &FullNameRef
impl<'a> TryFrom<&'a gix_object::bstr::BStr> for &'a FullNameRef { type Error = gix_validate::reference::name::Error; }
impl<'a> TryFrom<&'a str>                    for &'a FullNameRef { type Error = gix_validate::reference::name::Error; }
impl<'a> TryFrom<&'a String>                 for &'a FullNameRef { type Error = gix_validate::reference::name::Error; }

// conversions into PartialName / &PartialNameRef
impl<'a> From<&'a FullNameRef>               for &'a PartialNameRef { }            // infallible
impl<'a> TryFrom<&'a FullName>               for &'a PartialNameRef { type Error = std::convert::Infallible; }
impl<'a> TryFrom<&'a PartialName>            for &'a PartialNameRef { type Error = gix_validate::reference::name::Error; }
impl<'a> TryFrom<&'a gix_object::bstr::BStr>    for &'a PartialNameRef { type Error = gix_validate::reference::name::Error; }
impl<'a> TryFrom<&'a gix_object::bstr::BString> for &'a PartialNameRef { type Error = gix_validate::reference::name::Error; }
impl<'a> TryFrom<&'a str>                    for &'a PartialNameRef { type Error = gix_validate::reference::name::Error; }
impl<'a> TryFrom<&'a String>                 for &'a PartialNameRef { type Error = gix_validate::reference::name::Error; }
impl<'a> TryFrom<&'a std::ffi::OsStr>        for &'a PartialNameRef { type Error = gix_validate::reference::name::Error; }
impl<'a> TryFrom<&'a str>                    for PartialName { type Error = gix_validate::reference::name::Error; }
impl TryFrom<String>                         for PartialName { type Error = gix_validate::reference::name::Error; }
impl TryFrom<gix_object::bstr::BString>      for PartialName { type Error = gix_validate::reference::name::Error; }
impl std::borrow::Borrow<PartialNameRef> for PartialName;
impl AsRef<PartialNameRef> for PartialName;
impl ToOwned for PartialNameRef { type Owned = PartialName; }
impl std::fmt::Display for PartialName;
impl std::fmt::Display for PartialNameRef;
```

```rust
pub mod name {
    pub type Error = gix_validate::reference::name::Error;
}

impl Category<'_> {
    pub fn prefix(&self) -> &gix_object::bstr::BStr;
    pub fn is_worktree_private(&self) -> bool;
    pub fn is_remote_tracking_branch(&self) -> bool;
    pub fn to_full_name<'a>(&self, short_name: impl Into<&'a gix_object::bstr::BStr>)
        -> Result<FullName, gix_ref::name::Error>;
}

pub mod namespace {
    pub fn expand<'a, Name, E>(namespace: Name)
        -> Result<crate::Namespace, gix_validate::reference::name::Error>
    where
        Name: TryInto<&'a crate::PartialNameRef, Error = E>,
        gix_validate::reference::name::Error: From<E>;
}

impl Namespace {
    pub fn into_bstring(self) -> gix_object::bstr::BString;
    pub fn as_bstr(&self) -> &gix_object::bstr::BStr;
    pub fn to_path(&self) -> &std::path::Path;
}
```

#### `gix_ref` — kinds, categories and targets

```rust
#[derive(PartialEq, Eq, Debug, Hash, Ord, PartialOrd, Clone, Copy)]
pub enum Kind { Object, Symbolic }

#[derive(PartialEq, Eq, Debug, Hash, Ord, PartialOrd, Clone, Copy)]
pub enum Category<'a> {
    Tag,
    LocalBranch,
    RemoteBranch,
    Note,
    PseudoRef,
    MainPseudoRef,
    MainRef,
    LinkedPseudoRef { name: &'a gix_object::bstr::BStr },
    LinkedRef { name: &'a gix_object::bstr::BStr },
    Bisect,
    Rewritten,
    WorktreePrivate,
}

#[derive(PartialEq, Eq, Debug, Hash, Ord, PartialOrd, Clone)]
pub enum Target {
    Object(gix_hash::ObjectId),
    Symbolic(FullName),
}

#[derive(PartialEq, Eq, Debug, Hash, Ord, PartialOrd, Clone, Copy)]
pub enum TargetRef<'a> {
    Object(&'a gix_hash::oid),
    Symbolic(&'a FullNameRef),
}

impl Target {
    pub fn kind(&self) -> Kind;
    pub fn is_null(&self) -> bool;
    pub fn to_ref(&self) -> TargetRef<'_>;
    pub fn try_id(&self) -> Option<&gix_hash::oid>;
    pub fn id(&self) -> &gix_hash::oid;                    // panics on Symbolic
    pub fn into_id(self) -> gix_hash::ObjectId;            // panics on Symbolic
    pub fn try_into_id(self) -> Result<gix_hash::ObjectId, Self>;
    pub fn try_name(&self) -> Option<&FullNameRef>;
}

impl TargetRef<'_> {
    pub fn kind(&self) -> Kind;
    pub fn try_id(&self) -> Option<&gix_hash::oid>;
    pub fn id(&self) -> &gix_hash::oid;                    // panics on Symbolic
    pub fn try_name(&self) -> Option<&FullNameRef>;
    pub fn into_owned(self) -> Target;
}

impl<'a> From<TargetRef<'a>> for Target;
impl<'a> PartialEq<TargetRef<'a>> for Target;
impl From<gix_hash::ObjectId> for Target;
impl TryFrom<Target> for gix_hash::ObjectId { type Error = Target; }
impl From<FullName> for Target;
impl std::fmt::Display for Target;   // hex id, or "ref: <name>"
```

#### `gix_ref::Reference` and `gix_ref::file::loose::Reference`

```rust
#[derive(PartialEq, Eq, Debug, Hash, Ord, PartialOrd, Clone)]
pub struct Reference {
    pub name: FullName,
    pub target: Target,
    pub peeled: Option<gix_hash::ObjectId>,
}

impl Reference {
    pub fn kind(&self) -> Kind;
    pub fn name_without_namespace(&self, namespace: &Namespace) -> Option<&FullNameRef>;
    pub fn strip_namespace(&mut self, namespace: &Namespace) -> &mut Self;
}

impl From<Reference> for gix_ref::file::loose::Reference;
impl From<gix_ref::file::loose::Reference> for Reference;
impl<'p> From<gix_ref::packed::Reference<'p>> for Reference;

// gix_ref::file::loose
#[derive(Debug, PartialOrd, PartialEq, Ord, Eq, Hash, Clone)]
pub struct Reference {
    pub name: crate::FullName,
    pub target: crate::Target,
}
impl Reference { pub fn kind(&self) -> crate::Kind; }

impl Reference {
    pub fn log_exists(&self, store: &crate::file::Store) -> bool;
    pub fn log_iter_rev<'b>(&self, store: &crate::file::Store, buf: &'b mut [u8])
        -> std::io::Result<Option<crate::file::log::iter::Reverse<'b, std::fs::File>>>;
    pub fn log_iter<'a, 'b: 'a>(&'a self, store: &crate::file::Store, buf: &'b mut Vec<u8>)
        -> std::io::Result<Option<impl Iterator<Item = Result<crate::file::log::LineRef<'b>, crate::file::log::iter::decode::Error>> + 'a>>;
}
```

#### `gix_ref::transaction`

```rust
#[derive(PartialEq, Eq, Debug, Hash, Ord, PartialOrd, Clone)]
pub struct LogChange {
    pub mode: RefLog,
    pub force_create_reflog: bool,
    pub message: gix_object::bstr::BString,
}
impl Default for LogChange;   // AndReference, false, empty

#[derive(PartialEq, Eq, Debug, Hash, Ord, PartialOrd, Clone)]
pub enum PreviousValue {
    Any,
    MustExist,
    MustNotExist,
    MustExistAndMatch(crate::Target),
    ExistingMustMatch(crate::Target),
}

#[derive(PartialEq, Eq, Debug, Hash, Ord, PartialOrd, Clone)]
pub enum Change {
    Update { log: LogChange, expected: PreviousValue, new: crate::Target },
    Delete { expected: PreviousValue, log: RefLog },
}

impl Change {
    pub fn new_value(&self) -> Option<crate::TargetRef<'_>>;
    pub fn previous_value(&self) -> Option<crate::TargetRef<'_>>;
}

#[derive(PartialEq, Eq, Debug, Hash, Ord, PartialOrd, Clone)]
pub struct RefEdit {
    pub change: Change,
    pub name: crate::FullName,
    pub deref: bool,
}

#[derive(PartialEq, Eq, Debug, Hash, Ord, PartialOrd, Clone, Copy)]
pub enum RefLog { AndReference, Only }   // no Default

pub trait RefEditsExt<T>
where
    T: std::borrow::Borrow<RefEdit> + std::borrow::BorrowMut<RefEdit>,
{
    fn assure_one_name_has_one_edit(&self) -> Result<(), gix_object::bstr::BString>;

    fn extend_with_splits_of_symbolic_refs(
        &mut self,
        find: &mut dyn FnMut(&crate::PartialNameRef) -> Option<crate::Target>,
        make_entry: &mut dyn FnMut(usize, RefEdit) -> T,
    ) -> Result<(), std::io::Error>;

    fn pre_process(
        &mut self,
        find: &mut dyn FnMut(&crate::PartialNameRef) -> Option<crate::Target>,
        make_entry: &mut dyn FnMut(usize, RefEdit) -> T,
    ) -> Result<(), std::io::Error>;
}

impl<E> RefEditsExt<E> for Vec<E>
where
    E: std::borrow::Borrow<RefEdit> + std::borrow::BorrowMut<RefEdit>;
```

`pre_process` must have a default body in the trait that runs
`extend_with_splits_of_symbolic_refs` and then `assure_one_name_has_one_edit`,
so an implementor supplies only the other two.

#### `gix_ref::store` and `gix_ref::file::Store`

```rust
pub mod store {
    pub mod init {
        #[derive(Debug, Copy, Clone, Default)]
        pub struct Options {
            pub write_reflog: super::WriteReflog,
            pub precompose_unicode: bool,
            pub prohibit_windows_device_names: bool,
        }
    }
    #[derive(Default, Debug, PartialOrd, PartialEq, Ord, Eq, Hash, Clone, Copy)]
    pub enum WriteReflog { Always, #[default] Normal, Disable }
}

// gix_ref::file
#[derive(Debug, Clone)]
pub struct Store {
    pub write_reflog: crate::store::WriteReflog,
    pub namespace: Option<crate::Namespace>,
    pub prohibit_windows_device_names: bool,
    pub precompose_unicode: bool,
    /* remaining fields private */
}

impl Store {
    pub fn at(git_dir: std::path::PathBuf, object_hash: gix_hash::Kind) -> Self;
    pub fn at_opts(
        git_dir: std::path::PathBuf,
        object_hash: gix_hash::Kind,
        opts: crate::store::init::Options,
    ) -> Self;
    pub fn git_dir(&self) -> &std::path::Path;
    pub fn packed_refs_path(&self) -> std::path::PathBuf;
    pub fn open_packed_buffer(&self)
        -> Result<Option<crate::packed::Buffer>, crate::packed::buffer::open::Error>;
    pub fn force_refresh_packed_buffer(&self)
        -> Result<(), crate::packed::buffer::open::Error>;
}
```

#### `gix_ref::file` — lookup, as far as this document requires it

```rust
impl Store {
    pub fn try_find<'a, Name, E>(&self, partial: Name)
        -> Result<Option<crate::Reference>, find::Error>
    where Name: TryInto<&'a crate::PartialNameRef, Error = E>, find::Error: From<E>;

    pub fn try_find_loose<'a, Name, E>(&self, partial: Name)
        -> Result<Option<loose::Reference>, find::Error>
    where Name: TryInto<&'a crate::PartialNameRef, Error = E>, find::Error: From<E>;

    pub fn try_find_packed<'a, Name, E>(&self, partial: Name, packed: Option<&crate::packed::Buffer>)
        -> Result<Option<crate::Reference>, find::Error>
    where Name: TryInto<&'a crate::PartialNameRef, Error = E>, find::Error: From<E>;

    pub fn find<'a, Name, E>(&self, partial: Name)
        -> Result<crate::Reference, find::existing::Error>
    where Name: TryInto<&'a crate::PartialNameRef, Error = E>, crate::name::Error: From<E>;

    pub fn find_loose<'a, Name, E>(&self, partial: Name)
        -> Result<loose::Reference, find::existing::Error>
    where Name: TryInto<&'a crate::PartialNameRef, Error = E>, crate::name::Error: From<E>;

    pub fn find_packed<'a, Name, E>(&self, partial: Name, packed: Option<&crate::packed::Buffer>)
        -> Result<crate::Reference, find::existing::Error>
    where Name: TryInto<&'a crate::PartialNameRef, Error = E>, crate::name::Error: From<E>;
}
```

#### `gix_ref::file` — transactions

```rust
pub struct Transaction<'s, 'p> { /* private */ }
impl std::fmt::Debug for Transaction<'_, '_>;   // "Transaction" { store, edits: Option<usize> }, non-exhaustive

impl Store {
    pub fn transaction(&self) -> Transaction<'_, '_>;
}

impl<'p> Transaction<'_, 'p> {
    pub fn packed_refs(self, packed_refs: transaction::PackedRefs<'p>) -> Self;
}

impl<'s, 'p> Transaction<'s, 'p> {
    pub fn prepare(
        self,
        edits: impl IntoIterator<Item = crate::transaction::RefEdit>,
        ref_files_lock_fail_mode: gix_lock::acquire::Fail,
        packed_refs_lock_fail_mode: gix_lock::acquire::Fail,
    ) -> Result<Self, transaction::prepare::Error>;

    pub fn rollback(self) -> Vec<crate::transaction::RefEdit>;

    pub fn commit<'a>(
        self,
        committer: impl Into<Option<gix_actor::SignatureRef<'a>>>,
    ) -> Result<Vec<crate::transaction::RefEdit>, transaction::commit::Error>;
}

// gix_ref::file::transaction
#[derive(Default)]
pub enum PackedRefs<'a> {
    #[default]
    DeletionsOnly,
    DeletionsAndNonSymbolicUpdates(Box<dyn gix_object::Find + 'a>),
    DeletionsAndNonSymbolicUpdatesRemoveLooseSourceReference(Box<dyn gix_object::Find + 'a>),
}
```

`PackedRefs` derives only `Default`; it must not derive `Debug`, because it
holds a trait object.

#### `gix_ref::packed`

```rust
#[derive(Debug)]
pub struct Buffer { /* private */ }

impl Buffer {
    pub fn open(
        path: std::path::PathBuf,
        use_memory_map_if_larger_than_bytes: u64,
        object_hash: gix_hash::Kind,
    ) -> Result<Self, buffer::open::Error>;

    pub fn from_bytes(bytes: &[u8], object_hash: gix_hash::Kind) -> Result<Self, buffer::open::Error>;

    pub fn iter(&self) -> Result<Iter<'_>, iter::Error>;
    pub fn iter_prefixed(&self, prefix: gix_object::bstr::BString) -> Result<Iter<'_>, iter::Error>;

    pub fn try_find<'a, Name, E>(&self, name: Name) -> Result<Option<Reference<'_>>, find::Error>
    where Name: TryInto<&'a crate::PartialNameRef, Error = E>, find::Error: From<E>;

    pub fn find<'a, Name, E>(&self, name: Name) -> Result<Reference<'_>, find::existing::Error>
    where Name: TryInto<&'a crate::PartialNameRef, Error = E>, find::Error: From<E>;
}
impl AsRef<[u8]> for Buffer;

#[derive(Debug, PartialEq, Eq)]
pub struct Reference<'a> {
    pub name: &'a crate::FullNameRef,
    pub target: &'a gix_object::bstr::BStr,
    pub object: Option<&'a gix_object::bstr::BStr>,
}

impl Reference<'_> {
    pub fn target(&self) -> gix_hash::ObjectId;
    pub fn object(&self) -> gix_hash::ObjectId;   // the peeled id, or the target when absent
}

pub struct Iter<'a> { /* private */ }
impl<'a> Iterator for Iter<'a> { type Item = Result<Reference<'a>, iter::Error>; }
```

`packed::find::existing::Error` is analogous to the file store's:

```rust
// gix_ref::packed::find::existing::Error
pub enum Error {
    /// "The find operation failed"
    Find(#[from] crate::packed::find::Error),
    /// "The reference did not exist even though that was expected"
    NotFound,
}
```

#### `gix_ref::log` and `gix_ref::file::log`

```rust
// gix_ref::log
#[derive(PartialEq, Eq, Debug, Hash, Ord, PartialOrd, Clone)]
pub struct Line {
    pub previous_oid: gix_hash::ObjectId,
    pub new_oid: gix_hash::ObjectId,
    pub signature: gix_actor::Signature,
    pub message: gix_object::bstr::BString,
}

impl Line {
    pub fn write_to(&self, out: &mut dyn std::io::Write) -> std::io::Result<()>;
}

// gix_ref::file::log
#[derive(PartialEq, Eq, Debug, Hash, Ord, PartialOrd, Clone, Copy)]
pub struct LineRef<'a> {
    pub previous_oid: &'a gix_object::bstr::BStr,
    pub new_oid: &'a gix_object::bstr::BStr,
    pub signature: gix_actor::SignatureRef<'a>,
    pub message: &'a gix_object::bstr::BStr,
}

impl LineRef<'_> {
    pub fn previous_oid(&self) -> gix_hash::ObjectId;
    pub fn new_oid(&self) -> gix_hash::ObjectId;
    pub fn to_owned(&self) -> crate::log::Line;
}
impl<'a> LineRef<'a> {
    // the error type's module is not exported; it is nameable only through this signature
    pub fn from_bytes(input: &'a [u8]) -> Result<LineRef<'a>, /* decode error */>;
}
impl<'a> From<LineRef<'a>> for crate::log::Line;

// gix_ref::file::log::iter
pub fn forward(lines: &[u8]) -> Forward<'_>;

pub struct Forward<'a> { /* private */ }
impl<'a> Iterator for Forward<'a> { type Item = Result<crate::file::log::LineRef<'a>, decode::Error>; }

pub fn reverse<F>(log: F, buf: &mut [u8]) -> std::io::Result<Reverse<'_, F>>
where F: std::io::Read + std::io::Seek;

pub struct Reverse<'a, F> { /* private */ }
impl<F> Iterator for Reverse<'_, F>
where F: std::io::Read + std::io::Seek
{ type Item = Result<crate::log::Line, reverse::Error>; }

#[must_use = "Iterators should be obtained from this platform"]
pub struct Platform<'a, 's> {
    pub store: &'s crate::file::Store,
    pub name: &'a crate::FullNameRef,
    pub buf: Vec<u8>,
}

impl Platform<'_, '_> {
    pub fn rev(&mut self) -> std::io::Result<Option<Reverse<'_, std::fs::File>>>;
    pub fn all(&mut self) -> std::io::Result<Option<Forward<'_>>>;
}

// gix_ref::file::log::iter::decode
#[derive(Debug)]
pub struct Error { /* private */ }
```

The `decode::Error` declared above is the item error of the forward iterator and
the payload of `reverse::Error::Decode`; its fields are private and its display
text, fixed under Error Semantics, is the only thing a caller observes of it.

#### `gix_ref::file::Store` — reference logs

```rust
impl Store {
    pub fn reflog_exists<'a, Name, E>(&self, name: Name) -> Result<bool, E>
    where Name: TryInto<&'a crate::FullNameRef, Error = E>, crate::name::Error: From<E>;

    pub fn reflog_iter<'a, 'b, Name, E>(&self, name: Name, buf: &'b mut Vec<u8>)
        -> Result<Option<log::iter::Forward<'b>>, log::Error>
    where Name: TryInto<&'a crate::FullNameRef, Error = E>, crate::name::Error: From<E>;

    pub fn reflog_iter_rev<'a, 'b, Name, E>(&self, name: Name, buf: &'b mut [u8])
        -> Result<Option<log::iter::Reverse<'b, std::fs::File>>, log::Error>
    where Name: TryInto<&'a crate::FullNameRef, Error = E>, crate::name::Error: From<E>;
}
```

`reflog_exists` is the one operation in this document whose error type is the
name-conversion error itself rather than an enumeration.

#### `gix_ref::file::ReferenceExt`

```rust
// in a module that is NOT exported
pub trait Sealed {}
impl Sealed for crate::Reference {}

pub trait ReferenceExt: Sealed {
    fn log_iter<'a, 's>(&'a self, store: &'s crate::file::Store)
        -> crate::file::log::iter::Platform<'a, 's>;
    fn log_exists(&self, store: &crate::file::Store) -> bool;
    /* further methods outside the scope of this document */
}

impl ReferenceExt for crate::Reference;
```

Only `ReferenceExt` is re-exported, as `gix_ref::file::ReferenceExt`. The
supertrait it is bounded by must live in a module that is not exported, so a
caller is able to import and call the trait but no type outside this crate is
able to implement it.

### CLI Entry Points

This library exposes no executable, no binary target and no command-line
interface. Everything described in this document is reached through the Rust
interface above.

═══════════════════════════ Meta Layer ═══════════════════════════

## Appendix A: Environment

The delivery is a single Rust library crate whose manifest declares the package
name `gix-ref`, resolved by dependents through a source replacement, so the
package name and the library name `gix_ref` are both part of the contract. The
crate targets edition 2024 and a minimum Rust version of 1.85, builds on Linux
without network access, and declares `[lib] doctest = false`.

The manifest must declare the cargo features `sha1`, `sha256` and `parallel`,
defined as `sha1 = ["gix-hash/sha1"]`, `sha256 = ["gix-hash/sha256"]` and
`parallel = ["gix-features/parallel"]`, and must declare no feature as a
default. **`sha1` is the feature this document is exercised under**, and the
consuming crate turns it on through its dependency declaration. `gix-hash`
carries no hash by default: with neither `sha1` nor `sha256` turned on its
`Kind` enumeration has no variants and that crate itself fails to compile, so a
build with no feature at all fails inside `gix-hash` rather than inside this
crate. Every behavior in this document must be reachable with `sha1` alone; no
behavior here is permitted to require `sha256`, `parallel` or any other feature.

The dependencies available are exactly these, at these version requirements, and
no others:

| Crate | Version | Why it is needed here |
|---|---|---|
| `gix-features` | `^0.49.0`, feature `walkdir` | directory traversal helpers |
| `gix-fs` | `^0.22.0` | filesystem capability handling |
| `gix-path` | `^0.12.4` | conversion between byte strings and paths |
| `gix-hash` | `^0.26.0` | `ObjectId`, `oid`, `Kind` and the null id |
| `gix-object` | `^0.63.0` | the `Find` trait, tag peeling, and the `bstr` re-export |
| `gix-utils` | `^0.3.5` | unicode precomposition |
| `gix-validate` | `^0.11.3` | reference-name validation and its error type |
| `gix-actor` | `^0.41.2` | `Signature` and `SignatureRef` in log lines |
| `gix-lock` | `^24.0.0` | the lock file, `acquire::Fail`, `File`, `Marker` and their errors |
| `gix-tempfile` | `^24.0.0`, default features off | signal-safe temporary files and depth-first empty-directory removal |
| `thiserror` | `1.0` or `2.0` | error derivation |
| `memmap2` | `^0.9.11` | memory-mapping a large packed reference file |

Two of these carry part of the transaction guarantee and the split is stated
here as well as in the Behavior Layer, because it decides what belongs in this
delivery. **`gix-lock` and `gix-tempfile` provide** the lock file's name and
byte content, the create-and-rename sequence that publishes a locked resource,
the retry and backoff behavior of `gix_lock::acquire::Fail::AfterDurationWithBackoff`
versus `Fail::Immediately`, the removal of lock files and temporary files when
the process exits or is signalled, depth-first removal of an empty directory
tree, and whatever flushing to durable storage those crates perform. **This
delivery provides** which resources are locked and in what order, how an
acquisition failure is classified between an I/O failure and a contended lock,
which reference name a lock failure is attributed to, that a rollback and a drop
each remove every lock and every directory preparation created, the whole
compare-and-swap matrix together with the commit-time rewriting of the
expectation, and the order in which a commit publishes references, deletes logs,
writes the packed file and deletes loose files.

The file-descriptor cost of a transaction is not part of this contract: no
statement is made about how many locks or open files a transaction holds at
once.

Reading and writing goes to the git directory the store was opened at. No
network access, no subprocess, and no external `git` installation is used.

## Appendix B: Assessment Notes

The implementation is assessed by compiling a separate crate that depends on
this library and running its tests, so the names, module paths, parameter order,
ownership, lifetimes, generic bounds, derived traits and return types given in
the Reference Layer are load-bearing: a divergence in any of them prevents the
dependent crate from compiling at all, independently of whether the behavior is
right. The same applies to the trait implementations listed — the conversions,
the `Display` and `Debug` renderings, the `Default` values and the iterator item
types are each relied on by callers.

The error display strings quoted in the Contract Layer are compared as text. A
paraphrase is a divergence.

Behavior is observed through the public interface and through the bytes on disk:
the content of a loose reference file, the content of the packed reference file
including its header line and its ordering, the content of a reference log file,
and the presence or absence of files and directories after a rollback. Internal
data structures, the number of allocations, memory layout, and the identity of
private modules are not observed.
