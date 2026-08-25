# gix-status Specification

## Product Overview

`gix-status` is a Rust library that answers one question: how does a Git working
tree differ from the index that describes it?
The installable crate name is `gix-status`, the library name is `gix_status`, and
the two functions callers invoke are `index_as_worktree` and
`index_as_worktree_with_renames`.
The library is given an already-parsed index (`gix_index::State`), the absolute
path of a working-tree root, and an object database, and it reports one status
per index entry that is not identical to the file on disk.
Results are pushed to a caller-supplied visitor rather than returned as a
collection, so a caller that only wants to know whether the tree is dirty can stop
after the first change.
The library never writes to the index, never writes to the object database, and
never modifies the working tree; every stat refresh it discovers is reported to
the caller as data, and applying it is the caller's decision.
Speed is the reason this crate exists as a separate layer: the common case is a
tree in which almost nothing changed, so the implementation must decide "unchanged"
from cached `stat` data alone and must read file contents only for the entries
where `stat` data is inconclusive.
The second entry point, `index_as_worktree_with_renames`, merges that per-entry
status with a directory walk over untracked files and, optionally, with rename and
copy detection, so a caller obtains a single ordered stream describing modified
tracked files, untracked files, and renames together.

## Non-Goals

This specification does not define discovery of the repository, parsing of the
index file, or loading of configuration. The caller supplies an already-decoded
`gix_index::State`, an already-configured attribute stack, and an already-configured
filter pipeline.

This specification does not define a tree-to-index diff. Comparing a commit to the
index is performed by building an index from a tree and diffing two indices, which
is the responsibility of a different crate.

This specification does not define the directory-walk algorithm itself, the
rename-similarity algorithm itself, or the blob-diff algorithm itself. Those are
supplied by `gix-dir` and `gix-diff`; this library orchestrates them and defines
only how their results are merged and classified.

This specification does not define how the object database is populated. The
`objects` argument is any implementation of `gix_object::Find`, and for
`index_as_worktree_with_renames` also of `gix_object::FindHeader`.

This specification does not define index updating. `EntryStatus::NeedsUpdate` and
the `set_entry_stat_size_zero` field are advisory outputs; ignoring them changes
performance on the next run but never changes correctness.

This specification does not define Windows-specific metadata caching behavior. The
`fscache` option is accepted and stored, and on a platform without that cache it
must have no observable effect other than performance.

This specification does not require `serde` support, and does not define any
`Serialize` or `Deserialize` implementation.

## Representative Workflows

### Workflow 1 — Is the working tree dirty?

A caller holds a `gix_index::State`, the working-tree root, and an object database.
It builds a `Context` from an empty `gix_pathspec::Search`, an attribute stack, a
filter pipeline and an interrupt flag, then calls `index_as_worktree` with the
`FastEq` comparison delegate, a submodule delegate, and `Options::default()`.
Each index entry is examined in turn. For an entry whose recorded `stat` still
matches the file on disk and that is not racily clean, nothing is reported at all —
this is the fast path and it performs no read of file contents. For every other
entry the file is inspected and, if it really differs, the visitor receives an
`EntryStatus::Change`. If the visitor receives no status at all, the tracked part
of the working tree is clean.

### Workflow 2 — Refreshing stale stat data

A caller runs `index_as_worktree` over an index whose `stat` data is stale — for
example after the index was copied between machines. Entries whose contents are in
fact unchanged, but whose `stat` no longer matches, are reported as
`EntryStatus::NeedsUpdate(stat)` carrying the freshly observed `gix_index::entry::Stat`,
and `Outcome::entries_to_update` counts them. The caller writes each reported
`stat` into the corresponding index entry and saves the index. On the next run the
same entries take the fast path, report nothing, and `Outcome::worktree_files_read`
is zero.

### Workflow 3 — Status with untracked files and renames

A caller wants the output of `git status` including untracked files and rename
detection. It builds a `gix_diff::blob::Platform` as the `resource_cache`, a
`DirwalkContext` naming the real path of the git directory and the current
directory, and passes `Options` with `dirwalk: Some(..)`, `rewrites: Some(..)` and
`sorting: Some(Sorting::ByPathCaseSensitive)`. The visitor then receives one
`Entry` per finding: `Entry::Modification` for changed tracked files,
`Entry::DirectoryContents` for files found by the walk, and `Entry::Rewrite` where
a removed index entry and an untracked file on disk were matched. Calling
`summary()` on each entry collapses this into the familiar
`Removed`/`Added`/`Modified`/`TypeChange`/`Renamed`/`Copied` vocabulary.

## Entry Selection and Skipping

`index_as_worktree` visits the entries of the supplied index in the order in which
they appear in `gix_index::State::entries()`, which is the index's own sort order.

Three separate filters can remove an entry from consideration before its status is
computed, and each filter has its own counter on `Outcome`. The filters are
disjoint: an entry that is removed by an earlier filter is not counted by a later
one.

**Common-prefix skipping.** The pathspec search supplied in `Context::pathspec`
exposes a `common_prefix()`, and every index entry whose path does not start with
that prefix is skipped without any further work. WHEN an entry is skipped this way,
THEN `Outcome::entries_skipped_by_common_prefix` must be incremented and the entry
must not be reported to the visitor. `Outcome::entries_to_process` counts the
entries that survive this first filter, so it equals the number of index entries
minus `entries_skipped_by_common_prefix`.

**Pathspec exclusion.** An entry that survives the common-prefix filter is matched
against the full pathspec search. WHEN the pathspec search does not match an
entry's path, THEN `Outcome::entries_skipped_by_pathspec` must be incremented and
the entry must not be reported to the visitor. An entry rejected here still counts
towards `Outcome::entries_processed`, because reaching the decision required
processing it.

**Entry-flag skipping.** WHEN an entry carries any of the flags
`gix_index::entry::Flags::UPTODATE`, `SKIP_WORKTREE`, `ASSUME_VALID` or
`FSMONITOR_VALID`, THEN the entry must be skipped, `Outcome::entries_skipped_by_entry_flags`
must be incremented, no `lstat` may be performed for it, and it must not be
reported to the visitor. These flags are the caller's assertion that the worktree
state is already known, and the library must trust them without verification.

`Outcome::skipped()` returns the sum of the three skip counters and nothing else.

`Outcome::symlink_metadata_calls` counts how many times the library asked the
operating system for the symlink-metadata of a worktree path. An entry removed by
any of the three filters must not contribute to this counter.

WHEN the `AtomicBool` referenced by `Context::should_interrupt` is observed to be
`true`, THEN processing must stop early and the partially filled `Outcome` must be
returned as `Ok`, which the caller detects by comparing `entries_processed` against
`entries_to_process`.

`Options::thread_limit` bounds the number of worker threads; `None` means the
implementation chooses, and `Some(0)` means no limit. The number of threads must
never change which statuses are reported, only how quickly they are produced.

## Per-Entry Status Determination

For an entry that survived all three filters, the library resolves the entry's
repository-relative path against the working-tree root without ever following a
symbolic link out of the tree, then requests symlink-metadata for it. The status is
then determined by the first of the following rules that applies.

**Symlinked component.** WHEN resolving the entry's path required stepping through
a symbolic link, THEN the entry's status is `Change::Removed`, because a path
reached through a symlink is not a path inside this working tree.

**Missing file.** WHEN the worktree path does not exist, THEN the entry's status is
`Change::Removed`.

**Directory in place of a file.** WHEN the worktree path is a directory and the
index entry is not a submodule, THEN the entry's status is `Change::Removed`.

**Submodule.** WHEN the index entry has mode `gix_index::entry::Mode::COMMIT` and
the worktree path is a directory, THEN the submodule delegate is consulted by
calling `SubmoduleStatus::status` with the entry and its path, and IF the delegate
returns `Some(value)` THEN the status is `Change::SubmoduleModification(value)`, and
IF the delegate returns `None` THEN nothing is reported for this entry.

**Intent to add.** WHEN an entry carries `gix_index::entry::Flags::INTENT_TO_ADD`
and the file exists, THEN the status is `EntryStatus::IntentToAdd`, no content
comparison is performed, and no `Change` is produced. Such an entry is a promise to
add a file whose content is not in the object database yet, so no comparison could
be meaningful.

**Type change.** The worktree file's mode is derived from its symlink-metadata: a
directory yields `Mode::DIR`, a symbolic link yields `Mode::SYMLINK`, and anything
else yields `Mode::FILE`, except that the executable bit is folded in as described
below. WHEN that derived mode differs from the entry's mode in a way that is not
merely a difference of the executable bit, THEN the status is
`Change::Type { worktree_mode }` carrying the derived mode, and no content
comparison is performed.

**Executable-bit change.** The executable bit is only considered when
`Options::fs.executable_bit` is `true`. WHEN an entry has mode `Mode::FILE` and the
file on disk is executable, or the entry has mode `Mode::FILE_EXECUTABLE` and the
file on disk is not, THEN this is an executable-bit change and it is reported
through the `executable_bit_changed` field of `Change::Modification`, never through
`Change::Type`.

**Stat comparison.** Otherwise the entry's recorded `gix_index::entry::Stat` is
compared against the freshly observed one under `Options::stat`. WHEN the two match
and the entry is not racily clean, THEN the entry is clean, nothing is reported to
the visitor, and no file content is read.

**Content comparison.** WHEN the stat data does not match, or the entry is racily
clean, THEN the content is compared by handing the entry to the `CompareBlobs`
delegate. IF the delegate reports a difference, THEN the status is
`Change::Modification`; IF the delegate reports no difference and the executable bit
did not change either, THEN the entry is unchanged after all and the status is
`EntryStatus::NeedsUpdate(stat)` carrying the freshly observed stat, and
`Outcome::entries_to_update` is incremented.

`Change::Modification` carries three fields. `executable_bit_changed` is `true` only
for the executable-bit change described above. `content_change` is `Some(output)`
with the `CompareBlobs` delegate's output when the content differed and `None` when
only the executable bit changed. `set_entry_stat_size_zero` is `true` only for a
racily-clean entry that turned out to be modified.

**Racy cleanliness.** An entry is racily clean when its recorded modification time
is not strictly older than the index's own timestamp, because a file written within
the same timestamp granularity as the index write cannot be distinguished from an
unmodified one by stat data alone. WHEN an entry is racily clean, THEN
`Outcome::racy_clean` must be incremented and the content must be compared even
though the stat data matches. WHEN a racily-clean entry turns out to be genuinely
modified, THEN `Change::Modification::set_entry_stat_size_zero` must be `true`, which
tells the caller it can set the entry's recorded size to zero so that the next run
detects the difference from stat data alone. WHEN the index timestamp is strictly
newer than the file's modification time and the stat data matches, THEN the entry is
not racily clean, `Outcome::racy_clean` is not incremented, and nothing is reported.

**Accounting.** `Outcome::worktree_files_read` counts files whose contents were read
from the working tree and `Outcome::worktree_bytes` sums their sizes.
`Outcome::odb_objects_read` counts objects fetched from the object database and
`Outcome::odb_bytes` sums their sizes. An entry that took the stat fast path
contributes to none of these four counters.

## Conflict Analysis

An index in a conflicted state stores up to three entries for the same path, at
stages 1, 2 and 3, and no entry at stage 0. Stage 1 is the common ancestor, stage 2
is "ours", and stage 3 is "theirs".

WHEN the entries at a path form a conflict, THEN the library must report exactly one
`EntryStatus::Conflict` for the whole group rather than one status per stage, and
must then continue after the last stage entry of the group.

The reported `EntryStatus::Conflict` carries a `summary` derived only from which
stages are present, and an `entries` array of three slots holding the stage-1,
stage-2 and stage-3 entries at indices 0, 1 and 2, with `None` in the slot of any
stage that is absent. Each present slot holds a `ConflictIndexEntry`, which is the
index entry stripped of its disk metadata, retaining only `id`, `flags` and `mode`.

The summary is derived from the set of present stages exactly as follows.

| stages present | `Conflict` variant |
|---|---|
| 1 only | `Conflict::BothDeleted` |
| 2 only | `Conflict::AddedByUs` |
| 1 and 2 | `Conflict::DeletedByThem` |
| 3 only | `Conflict::AddedByThem` |
| 1 and 3 | `Conflict::DeletedByUs` |
| 2 and 3 | `Conflict::BothAdded` |
| 1, 2 and 3 | `Conflict::BothModified` |

`Conflict::try_from_entry` exposes that derivation directly. Given the index
entries, the index's path backing store, the position at which to start looking, and
the path expected at that position, it returns `None` if the entry at that position
is not part of a conflict, and otherwise `Some((summary, consumed, stages))` where
`consumed` is the number of *additional* entries the conflict group occupies beyond
the first, and `stages` holds borrowed references to the stage entries in the same
stage-1-to-stage-3 slot order. For a full three-stage conflict `consumed` is
therefore `2`.

`Outcome::entries_to_process` counts every stage entry individually, because the
count is taken before conflicts are recognized, but `Outcome::entries_processed`
counts a conflict group once.

## Content Comparison Delegates

Content comparison is delegated so that a caller can choose how much work to do and
what to learn from it. `CompareBlobs::compare_blobs` receives the index entry, the
size of the worktree file, a `ReadData` handle giving access to both sides, and a
scratch buffer, and returns `Ok(None)` when the two sides are equal and
`Ok(Some(output))` when they differ.

`ReadData` is the access handle. `read_blob` yields the entry's content as stored in
the object database, and `stream_worktree_file` yields the worktree file's content
already converted to the form Git would store, which is what makes the comparison
correct in the presence of filters such as end-of-line conversion. A `ReadData`
implementation is produced by the library while it walks entries; the type
`read_data::Stream` it hands out has no public constructor, so `ReadData` is
implementable only from inside this crate, while `CompareBlobs` is implementable by
anyone.

`read_data::Stream` either exposes the whole converted content as one byte slice
through `as_bytes`, or must be read as a stream through its `std::io::Read`
implementation; `as_bytes` returns `None` in the latter case. `size` returns the
converted length when it is known in advance and `None` otherwise. Every byte
obtained through either route is accounted for in `Outcome::worktree_bytes`, so
`as_bytes` must be called at most once per stream.

Two delegates are provided. `FastEq` has `Output = ()` and compares only sizes when
that is conclusive: WHEN the worktree file's converted size is known and differs
from the size recorded in the index entry, THEN `FastEq` reports a difference
without reading either side's content. `HashEq` has `Output = gix_hash::ObjectId`,
always hashes the worktree content, and reports the resulting object id as its
output when it differs from the entry's id, which makes the id reusable by the
caller.

Both `FastEq` and `HashEq` are unit structs and both are `Clone`, because the
implementation clones the delegate once per worker thread.

## Symlink-Safe Path Resolution

`SymlinkCheck` turns a repository-relative path into an absolute path while
guaranteeing that no component of the path traversed a symbolic link. It is built
from the working-tree root with `SymlinkCheck::new`, and its `inner` field exposes
the underlying `gix_fs::Stack` so that the root can be queried.

The type is a stack rather than a function because it caches the components it has
already verified: WHEN paths are queried in sorted order, THEN each directory
component is checked at most once.

`verified_path` returns the absolute path of an existing entry.
WHEN any component of the requested path is a symbolic link, THEN `verified_path`
must fail with an `std::io::Error` of kind `std::io::ErrorKind::Other` whose message
is `Cannot step through symlink to perform an lstat`.
WHEN the requested path simply does not exist, THEN `verified_path` must fail with
an `std::io::Error` of kind `std::io::ErrorKind::NotFound`.

`verified_path_allow_nonexisting` takes a slash-separated `BStr` path and differs in
exactly one respect: WHEN the requested path does not exist, THEN it must succeed
and return the path it would have had. It still rejects a symlinked component with
the same `ErrorKind::Other` error, because the guarantee it provides is about
symlinks, not about existence.

## Rename and Copy Tracking

`index_as_worktree_with_renames` is available when the crate feature
`worktree-rewrites` is enabled, and that feature is on by default.

The function performs up to three activities and merges their results into a single
stream of `Entry` values delivered to a `VisitEntry` visitor. First, the tracked-file
status of `index_as_worktree` is computed using `Options::tracked_file_modifications`
and reported as `Entry::Modification`, whose five fields mirror the arguments of the
non-renaming visitor. Second, IF `Options::dirwalk` is `Some(options)`, THEN a
directory walk is performed and its findings are reported as
`Entry::DirectoryContents`. Third, IF `Options::rewrites` is `Some(rewrites)`, THEN
removed index entries and untracked walk results are matched against each other and
each match is reported as a single `Entry::Rewrite` instead of the separate removal
and addition it was assembled from.

WHEN `Options::dirwalk` is `None`, THEN no directory walk is performed, no
`Entry::DirectoryContents` is produced, and `Outcome::dirwalk` is `None`. WHEN
`Options::rewrites` is `None`, THEN no rename detection is performed, no
`Entry::Rewrite` is produced, and `Outcome::rewrites` is `None`. Rename detection
therefore requires the directory walk, because the destination of a rename can only
be discovered by walking the disk.

`Options::sorting` controls output order. WHEN it is `Some(Sorting::ByPathCaseSensitive)`,
THEN all entries are collected before any is emitted and the stream is ordered by
the byte value of the destination path. WHEN it is `None`, THEN entries are emitted
as they are produced and the order is unspecified and may differ between runs;
because rename detection depends on the order in which candidates are presented, a
caller that wants reproducible rewrites must enable sorting.

`Options::object_hash` selects the hash used when the walk hashes an untracked file
to compare it against a removed entry.

`Entry::Rewrite` carries the `source` it was matched from, the `dirwalk_entry` that
is its destination, the `dirwalk_entry_id` that the destination content hashes to,
an optional `diff` with similarity statistics, and a `copy` flag. `diff` is `None`
when source and destination hashed to the same id, because exact identity makes a
similarity computation unnecessary. `copy` is `true` for a copy and `false` for a
rename; a rename's source is always an index entry that disappeared from disk,
since only the index can testify that something was removed.

`RewriteSource` distinguishes those two origins. `RewriteSource::RewriteFromIndex`
describes a source that the index knows about and that is missing on disk, and its
`rela_path` is the index path. `RewriteSource::CopyFromDirectoryEntry` describes a
source that is itself a walk result, which can only happen for copies.

`Entry::summary` collapses an entry into a `Summary`, and returns `None` for the two
cases that are not a user-visible change: a `Entry::Modification` whose status is
`EntryStatus::NeedsUpdate`, and a `Entry::DirectoryContents` whose walk status is
not `gix_dir::entry::Status::Untracked`. Otherwise the mapping is as follows.

| entry | `Summary` |
|---|---|
| `Modification` with `EntryStatus::Conflict` | `Summary::Conflict` |
| `Modification` with `EntryStatus::IntentToAdd` | `Summary::IntentToAdd` |
| `Modification` with `Change::Removed` | `Summary::Removed` |
| `Modification` with `Change::Type` | `Summary::TypeChange` |
| `Modification` with `Change::Modification` | `Summary::Modified` |
| `Modification` with `Change::SubmoduleModification` | `Summary::Modified` |
| `DirectoryContents` with an untracked walk status | `Summary::Added` |
| `Rewrite` with `copy == false` | `Summary::Renamed` |
| `Rewrite` with `copy == true` | `Summary::Copied` |

`Entry::source_rela_path` and `Entry::destination_rela_path` return the same path for
every variant except `Entry::Rewrite`, where the source is the path the content came
from and the destination is where it now lives.

`Outcome` for this function is a composition rather than a new set of counters: its
`tracked_file_modification` field is the `index_as_worktree` outcome, its `dirwalk`
field is the walk's own outcome when a walk ran, and its `rewrites` field is the
rewrite tracker's own outcome when tracking ran.

## State Model

Neither entry point owns mutable state that survives the call. `index_as_worktree`
borrows the index immutably for the lifetime `'index` and every reference handed to
the visitor — the entry slice, the entry, and the path — borrows from that same
index, which is why `VisitEntry` is parameterized by `'index` and why a `Recorder`
can accumulate records without copying.

The visitor is the only stateful participant. `Recorder` is the provided
implementation and accumulates one `Record` per reported status into its public
`records` field. `Record` carries the entry, the entry's index in the input slice,
the entry's path, and the status.

`Recorder` derives `Default`, which means a `Recorder<T, U>` can be default-constructed
only when both `T` and `U` are `Default`; a recorder over a non-`Default` output type
such as `gix_hash::ObjectId` must be constructed with an explicit empty `records`
field.

The two type parameters carried through the whole API are the two delegate outputs.
`T` is `CompareBlobs::Output` and appears as `VisitEntry::ContentChange`, and `U` is
`SubmoduleStatus::Output` and appears as `VisitEntry::SubmoduleStatus`. Both default
to `()` wherever a default is allowed.

`Options` is plain data: it derives `Clone`, `Default`, `Debug`, `PartialEq`, `Eq`
and `Hash`, and `Options::default()` yields `fs` and `stat` at their own defaults,
`thread_limit` at `None`, and `fscache` at `false`.

`Outcome` is plain data with a total order: it derives `Clone`, `Debug`, `Default`,
`Eq`, `PartialEq`, `Ord` and `PartialOrd`, and `Outcome::default()` has every counter
at zero.

`Context` is a bundle of borrowed and owned resources that the operation consumes;
it is destructured on entry, so a caller must rebuild it for a second call.

## Error Semantics

Both entry points return `Result<Outcome, Error>` with a distinct `Error` type per
module, and both error types implement `std::error::Error`, `Debug` and `Display`.

An interrupt is not an error. WHEN the operation stops because
`Context::should_interrupt` became `true`, THEN it must return `Ok` with a partially
filled `Outcome`.

A file that cannot be found in the working tree is not an error either; it is
`Change::Removed`. Only failures that make the answer unknowable are errors.

`index_as_worktree::Error` has five variants. `IllformedUtf8` reports a path that
could not be converted to UTF-8 and displays as `Could not convert path to UTF8`.
`Time` wraps a `std::time::SystemTimeError` and displays as
`The clock was off when reading file related metadata after updating a file on disk`.
`Io` wraps a `gix_hash::io::Error` and displays as
`IO error while writing blob or reading file metadata or changing filetype`.
`Find` wraps a `gix_object::find::existing_object::Error` and displays as
`Failed to obtain blob from object database`. `SubmoduleStatus` carries the
`rela_path` of the submodule and the boxed error the delegate returned, and displays
as `Could not determine status for submodule at '<rela_path>'`.

The submodule delegate's error type is therefore erased: `SubmoduleStatus::Error` is
constrained to `std::error::Error + Send + Sync + 'static` so that it can be boxed
into that variant. A delegate that cannot fail declares
`type Error = std::convert::Infallible`.

`index_as_worktree_with_renames::Error` has nine variants. `TrackedFileModifications`
wraps `index_as_worktree::Error` transparently, and `DirWalk`, `HashFile`,
`ConvertToGit` and `RewriteTracker` likewise display their wrapped error
transparently. `SpawnThread` wraps the `std::io::Error` from failing to start a
worker and is also transparent. The three variants with their own message are
`SetAttributeContext`, which displays as
`Failed to change the context for querying gitattributes to the respective path`,
`OpenWorktreeFile`, which displays as `Could not open worktree file for reading`, and
`ReadLink`, which displays as `Could not read worktree link content`.

## Cross-View Invariants

**INV-1 — Skip counters partition the index.** For any run,
`entries_to_process + entries_skipped_by_common_prefix` equals the number of entries
in the input index, and `skipped()` equals the sum of the three skip counters. No
entry is counted by two skip counters.

**INV-2 — Silence means clean.** An index entry that is reported to the visitor with
no status at all is one whose worktree state matches the index. Conversely, every
entry for which the library produced any `EntryStatus` differs from the index, needs
a stat refresh, or is an intent-to-add placeholder. A clean tree therefore produces
an empty `Recorder::records`.

**INV-3 — Reading implies inconclusive stat data.** `worktree_files_read` never
exceeds the number of entries whose stat comparison failed or that were racily
clean, so a run over an index whose stat data is fully accurate and non-racy has
`worktree_files_read == 0` and `worktree_bytes == 0`.

**INV-4 — `entries_to_update` counts exactly the `NeedsUpdate` reports.** The number
of `EntryStatus::NeedsUpdate` statuses delivered to the visitor equals
`Outcome::entries_to_update`, and applying every reported `Stat` to its entry and
re-running the operation on an otherwise unchanged tree yields
`entries_to_update == 0` and reports no status for those entries.

**INV-5 — Racy accounting brackets the zeroing hint.** `Outcome::racy_clean` is
greater than or equal to the number of `Change::Modification` statuses whose
`set_entry_stat_size_zero` is `true`, because that field can only be set for an entry
that was counted as racily clean.

**INV-6 — Conflicts are reported once.** For a path with `n` stage entries in a
conflict, the visitor receives exactly one `EntryStatus::Conflict`, its `entries`
array has exactly `n` occupied slots, and `Conflict::try_from_entry` invoked at the
first of those entries returns the same summary with `consumed == n - 1`.

**INV-7 — Determinism.** Two runs of `index_as_worktree` over the same index, the
same working tree and the same `Options` deliver the same statuses in the same order
regardless of `Options::thread_limit`.

**INV-8 — Composition.** For the same index, working tree and object database, a run
of `index_as_worktree_with_renames` with `dirwalk: None` and `rewrites: None` reports
exactly the statuses that `index_as_worktree` reports with the same
`tracked_file_modifications` options, each wrapped in `Entry::Modification`, and its
`Outcome::tracked_file_modification` equals the `Outcome` of that run.

**INV-9 — Rewrites conserve entries.** Enabling `rewrites` never invents content: a
finding reported as `Entry::Rewrite` replaces exactly one removal of the source path
and one directory-content entry for the destination path that would otherwise have
been reported separately, so `source_rela_path` names a path present in the index and
`destination_rela_path` names a path present on disk.

**INV-10 — The library is read-only.** No call to either entry point creates,
modifies or deletes any file in the working tree, any object in the database, or any
entry in the index.

## Public Interface

### Import Surface

Every path below is publicly reachable and must resolve in a default build of the
crate. An item that is missing, renamed, or reachable only behind a non-default
cargo feature is a build failure for any consumer of this crate. The surface is
written as the `use` statements a consumer would write, so that a build against
it either resolves or does not; the parenthetical notes distinguish the two cases
where a function and a module share a name.

```rust
use gix_status::SymlinkCheck;
use gix_status::index_as_worktree;              // the function and the module
use gix_status::index_as_worktree_with_renames; // the function and the module

use gix_status::index_as_worktree::{
    Change, Conflict, ConflictIndexEntry, Context, EntryStatus, Error, Options, Outcome,
    Record, Recorder, VisitEntry,
};
use gix_status::index_as_worktree::traits;
use gix_status::index_as_worktree::traits::{
    CompareBlobs, FastEq, HashEq, ReadData, SubmoduleStatus,
};
use gix_status::index_as_worktree::traits::read_data;
use gix_status::index_as_worktree::traits::read_data::Stream;

use gix_status::index_as_worktree_with_renames::{
    Context, DirwalkContext, Entry, Error, Options, Outcome, Recorder, RewriteSource, Sorting,
    Summary, VisitEntry,
};
```

The two `index_as_worktree` names and the two `index_as_worktree_with_renames`
names are each a function and a module sharing an identifier, which Rust permits
because they live in different namespaces. Both must exist.

### API Catalog

#### `gix_status` — crate root

```rust
pub struct SymlinkCheck {
    pub inner: gix_fs::Stack,
}

impl SymlinkCheck {
    pub fn new(root: std::path::PathBuf) -> Self;
    pub fn verified_path(
        &mut self,
        relative_path: impl gix_fs::stack::ToNormalPathComponents,
    ) -> std::io::Result<&std::path::Path>;
    pub fn verified_path_allow_nonexisting(
        &mut self,
        relative_path: &bstr::BStr,
    ) -> std::io::Result<std::borrow::Cow<'_, std::path::Path>>;
}
```

#### `gix_status::index_as_worktree`

```rust
#[derive(Debug, thiserror::Error)]
pub enum Error {
    #[error("Could not convert path to UTF8")]
    IllformedUtf8,
    #[error("The clock was off when reading file related metadata after updating a file on disk")]
    Time(#[from] std::time::SystemTimeError),
    #[error("IO error while writing blob or reading file metadata or changing filetype")]
    Io(#[from] gix_hash::io::Error),
    #[error("Failed to obtain blob from object database")]
    Find(#[from] gix_object::find::existing_object::Error),
    #[error("Could not determine status for submodule at '{rela_path}'")]
    SubmoduleStatus {
        rela_path: bstr::BString,
        source: Box<dyn std::error::Error + Send + Sync + 'static>,
    },
}

#[derive(Clone, Default, Debug, PartialEq, Eq, Hash)]
pub struct Options {
    pub fs: gix_fs::Capabilities,
    pub thread_limit: Option<usize>,
    pub stat: gix_index::entry::stat::Options,
    pub fscache: bool,
}

#[derive(Clone)]
pub struct Context<'a> {
    pub pathspec: gix_pathspec::Search,
    pub stack: gix_worktree::Stack,
    pub filter: gix_filter::Pipeline,
    pub should_interrupt: &'a std::sync::atomic::AtomicBool,
}

#[derive(Clone, Debug, Default, Eq, PartialEq, Ord, PartialOrd)]
pub struct Outcome {
    pub entries_to_process: usize,
    pub entries_processed: usize,
    pub entries_skipped_by_common_prefix: usize,
    pub entries_skipped_by_pathspec: usize,
    pub entries_skipped_by_entry_flags: usize,
    pub symlink_metadata_calls: usize,
    pub entries_to_update: usize,
    pub racy_clean: usize,
    pub worktree_bytes: u64,
    pub worktree_files_read: usize,
    pub odb_bytes: u64,
    pub odb_objects_read: usize,
}

impl Outcome {
    pub fn skipped(&self) -> usize;
}

#[derive(Clone, PartialEq, Eq, PartialOrd, Ord, Debug)]
pub enum Change<T = (), U = ()> {
    Removed,
    Type {
        worktree_mode: gix_index::entry::Mode,
    },
    Modification {
        executable_bit_changed: bool,
        content_change: Option<T>,
        set_entry_stat_size_zero: bool,
    },
    SubmoduleModification(U),
}

#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub struct ConflictIndexEntry {
    pub id: gix_hash::ObjectId,
    pub flags: gix_index::entry::Flags,
    pub mode: gix_index::entry::Mode,
}

impl From<&gix_index::Entry> for ConflictIndexEntry {
    fn from(value: &gix_index::Entry) -> Self;
}

#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub enum EntryStatus<T = (), U = ()> {
    Conflict {
        summary: Conflict,
        entries: Box<[Option<ConflictIndexEntry>; 3]>,
    },
    Change(Change<T, U>),
    NeedsUpdate(gix_index::entry::Stat),
    IntentToAdd,
}

impl<T, U> From<Change<T, U>> for EntryStatus<T, U> {
    fn from(value: Change<T, U>) -> Self;
}

#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Debug)]
pub enum Conflict {
    BothDeleted,
    AddedByUs,
    DeletedByThem,
    AddedByThem,
    DeletedByUs,
    BothAdded,
    BothModified,
}

impl Conflict {
    pub fn try_from_entry<'entry>(
        entries: &'entry [gix_index::Entry],
        path_backing: &gix_index::PathStorageRef,
        start_index: usize,
        entry_path: &bstr::BStr,
    ) -> Option<(Self, usize, [Option<&'entry gix_index::Entry>; 3])>;
}

pub trait VisitEntry<'index> {
    type ContentChange;
    type SubmoduleStatus;
    fn visit_entry(
        &mut self,
        entries: &'index [gix_index::Entry],
        entry: &'index gix_index::Entry,
        entry_index: usize,
        rela_path: &'index bstr::BStr,
        status: EntryStatus<Self::ContentChange, Self::SubmoduleStatus>,
    );
}

#[derive(Debug, Clone)]
pub struct Record<'index, T, U> {
    pub entry: &'index gix_index::Entry,
    pub entry_index: usize,
    pub relative_path: &'index bstr::BStr,
    pub status: EntryStatus<T, U>,
}

#[derive(Debug, Default)]
pub struct Recorder<'index, T = (), U = ()> {
    pub records: Vec<Record<'index, T, U>>,
}

impl<'index, T: Send, U: Send> VisitEntry<'index> for Recorder<'index, T, U> {
    type ContentChange = T;
    type SubmoduleStatus = U;
}

pub fn index_as_worktree<'index, T, U, Find, E>(
    index: &'index gix_index::State,
    worktree: &std::path::Path,
    collector: &mut impl VisitEntry<'index, ContentChange = T, SubmoduleStatus = U>,
    compare: impl traits::CompareBlobs<Output = T> + Send + Clone,
    submodule: impl traits::SubmoduleStatus<Output = U, Error = E> + Send + Clone,
    objects: Find,
    progress: &mut dyn gix_features::progress::Progress,
    context: Context<'_>,
    options: Options,
) -> Result<Outcome, Error>
where
    T: Send,
    U: Send,
    E: std::error::Error + Send + Sync + 'static,
    Find: gix_object::Find + Send + Clone;
```

#### `gix_status::index_as_worktree::traits`

```rust
pub trait CompareBlobs {
    type Output;
    fn compare_blobs<'a, 'b>(
        &mut self,
        entry: &gix_index::Entry,
        worktree_blob_size: u64,
        data: impl ReadData<'a>,
        buf: &mut Vec<u8>,
    ) -> Result<Option<Self::Output>, super::Error>;
}

pub trait SubmoduleStatus {
    type Output;
    type Error: std::error::Error + Send + Sync + 'static;
    fn status(
        &mut self,
        entry: &gix_index::Entry,
        rela_path: &bstr::BStr,
    ) -> Result<Option<Self::Output>, Self::Error>;
}

pub trait ReadData<'a> {
    fn read_blob(self) -> Result<&'a [u8], super::Error>;
    fn stream_worktree_file(self) -> Result<read_data::Stream<'a>, super::Error>;
}

pub mod read_data {
    pub struct Stream<'a> { /* private fields */ }

    impl<'a> Stream<'a> {
        pub fn as_bytes(&self) -> Option<&'a [u8]>;
        pub fn size(&self) -> Option<u64>;
    }

    impl std::io::Read for Stream<'_> {
        fn read(&mut self, buf: &mut [u8]) -> std::io::Result<usize>;
    }
}

#[derive(Clone)]
pub struct FastEq;

impl CompareBlobs for FastEq {
    type Output = ();
}

#[derive(Clone)]
pub struct HashEq;

impl CompareBlobs for HashEq {
    type Output = gix_hash::ObjectId;
}
```

#### `gix_status::index_as_worktree_with_renames`

```rust
#[derive(Debug, thiserror::Error)]
pub enum Error {
    #[error(transparent)]
    TrackedFileModifications(#[from] crate::index_as_worktree::Error),
    #[error(transparent)]
    DirWalk(gix_dir::walk::Error),
    #[error(transparent)]
    SpawnThread(std::io::Error),
    #[error("Failed to change the context for querying gitattributes to the respective path")]
    SetAttributeContext(std::io::Error),
    #[error("Could not open worktree file for reading")]
    OpenWorktreeFile(std::io::Error),
    #[error(transparent)]
    HashFile(gix_hash::io::Error),
    #[error("Could not read worktree link content")]
    ReadLink(std::io::Error),
    #[error(transparent)]
    ConvertToGit(#[from] gix_filter::pipeline::convert::to_git::Error),
    #[error(transparent)]
    RewriteTracker(#[from] gix_diff::rewrites::tracker::emit::Error),
}

#[derive(Clone, Copy, Default, Debug, Eq, PartialEq, PartialOrd, Ord, Hash)]
pub enum Sorting {
    #[default]
    ByPathCaseSensitive,
}

#[derive(Clone, Debug, Default)]
pub struct Outcome {
    pub tracked_file_modification: crate::index_as_worktree::Outcome,
    pub dirwalk: Option<gix_dir::walk::Outcome>,
    pub rewrites: Option<gix_diff::rewrites::Outcome>,
}

#[derive(Clone, Debug)]
pub enum RewriteSource<'index, ContentChange, SubmoduleStatus> {
    RewriteFromIndex {
        index_entries: &'index [gix_index::Entry],
        source_entry: &'index gix_index::Entry,
        source_entry_index: usize,
        source_rela_path: &'index bstr::BStr,
        source_status: crate::index_as_worktree::EntryStatus<ContentChange, SubmoduleStatus>,
    },
    CopyFromDirectoryEntry {
        source_dirwalk_entry: gix_dir::Entry,
        source_dirwalk_entry_collapsed_directory_status: Option<gix_dir::entry::Status>,
        source_dirwalk_entry_id: gix_hash::ObjectId,
    },
}

impl<ContentChange, SubmoduleStatus> RewriteSource<'_, ContentChange, SubmoduleStatus> {
    pub fn rela_path(&self) -> &bstr::BStr;
}

#[derive(Clone, Debug)]
pub enum Entry<'index, ContentChange, SubmoduleStatus> {
    Modification {
        entries: &'index [gix_index::Entry],
        entry: &'index gix_index::Entry,
        entry_index: usize,
        rela_path: &'index bstr::BStr,
        status: crate::index_as_worktree::EntryStatus<ContentChange, SubmoduleStatus>,
    },
    DirectoryContents {
        entry: gix_dir::Entry,
        collapsed_directory_status: Option<gix_dir::entry::Status>,
    },
    Rewrite {
        source: RewriteSource<'index, ContentChange, SubmoduleStatus>,
        dirwalk_entry: gix_dir::Entry,
        dirwalk_entry_collapsed_directory_status: Option<gix_dir::entry::Status>,
        dirwalk_entry_id: gix_hash::ObjectId,
        diff: Option<gix_diff::blob::DiffLineStats>,
        copy: bool,
    },
}

impl<ContentChange, SubmoduleStatus> Entry<'_, ContentChange, SubmoduleStatus> {
    pub fn summary(&self) -> Option<Summary>;
    pub fn source_rela_path(&self) -> &bstr::BStr;
    pub fn destination_rela_path(&self) -> &bstr::BStr;
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, PartialOrd, Ord, Hash)]
pub enum Summary {
    Removed,
    Added,
    Modified,
    TypeChange,
    Renamed,
    Copied,
    IntentToAdd,
    Conflict,
}

#[derive(Clone, Default)]
pub struct Options<'a> {
    pub sorting: Option<Sorting>,
    pub object_hash: gix_hash::Kind,
    pub tracked_file_modifications: crate::index_as_worktree::Options,
    pub fscache: bool,
    pub dirwalk: Option<gix_dir::walk::Options<'a>>,
    pub rewrites: Option<gix_diff::Rewrites>,
}

pub struct Context<'a> {
    pub pathspec: gix_pathspec::Search,
    pub resource_cache: gix_diff::blob::Platform,
    pub should_interrupt: &'a std::sync::atomic::AtomicBool,
    pub dirwalk: DirwalkContext<'a>,
}

pub struct DirwalkContext<'a> {
    pub git_dir_realpath: &'a std::path::Path,
    pub current_dir: &'a std::path::Path,
    pub ignore_case_index_lookup: Option<&'a gix_index::AccelerateLookup<'a>>,
}

pub trait VisitEntry<'a> {
    type ContentChange;
    type SubmoduleStatus;
    fn visit_entry(&mut self, entry: Entry<'a, Self::ContentChange, Self::SubmoduleStatus>);
}

#[derive(Debug, Default)]
pub struct Recorder<'index, T = (), U = ()> {
    pub records: Vec<Entry<'index, T, U>>,
}

impl<'index, T: Send, U: Send> VisitEntry<'index> for Recorder<'index, T, U> {
    type ContentChange = T;
    type SubmoduleStatus = U;
}

pub fn index_as_worktree_with_renames<'index, T, U, Find, E>(
    index: &'index gix_index::State,
    worktree: &std::path::Path,
    collector: &mut impl VisitEntry<'index, ContentChange = T, SubmoduleStatus = U>,
    compare: impl crate::index_as_worktree::traits::CompareBlobs<Output = T> + Send + Clone,
    submodule: impl crate::index_as_worktree::traits::SubmoduleStatus<Output = U, Error = E> + Send + Clone,
    objects: Find,
    progress: &mut dyn gix_features::progress::Progress,
    ctx: Context<'_>,
    options: Options<'_>,
) -> Result<Outcome, Error>
where
    T: Send + Clone,
    U: Send + Clone,
    E: std::error::Error + Send + Sync + 'static,
    Find: gix_object::Find + gix_object::FindHeader + Send + Clone;
```

## Appendix A: Environment

The crate is named `gix-status`, its library target is `gix_status`, it is built
with Rust edition 2024 against a minimum supported Rust version of 1.85, and the
library target sets `doctest = false`.

The crate declares `#![deny(missing_docs, unsafe_code)]`: every publicly reachable
item carries a documentation comment and the crate contains no `unsafe` code.

The dependency set is exactly the following, and each entry is required.

| crate | version | notes |
|---|---|---|
| `gix-index` | `^0.54.0` | `State`, `Entry`, `entry::{Flags, Mode, Stat, stat::Options}`, `PathStorageRef`, `AccelerateLookup` |
| `gix-worktree` | `^0.55.0` | `Stack` for attribute lookup; feature `attributes`, no default features |
| `gix-filter` | `^0.33.0` | `Pipeline` for worktree-to-git conversion |
| `gix-pathspec` | `^0.19.0` | `Search` and its `common_prefix()` |
| `gix-object` | `^0.63.0` | `Find`, `FindHeader`, `find::existing_object::Error` |
| `gix-hash` | `^0.26.0` | `ObjectId`, `Kind`, `io::Error` |
| `gix-fs` | `^0.22.0` | `Capabilities`, `Stack`, `stack::ToNormalPathComponents` |
| `gix-features` | `^0.49.0` | `progress::Progress` and threading; feature `progress` |
| `gix-path` | `^0.12.3` | path conversion between `BStr` and `Path` |
| `gix-dir` | `^0.28.0` | the directory walk, for `worktree-rewrites` |
| `gix-diff` | `^0.66.0` | `blob::Platform`, `Rewrites`; feature `blob`, no default features |
| `bstr` | `1.12.0` | `BStr`, `BString`; no default features |
| `filetime` | `0.2.29` | file timestamp handling |
| `thiserror` | `2.0.18` | error derives |

The crate declares these cargo features:

| feature | effect |
|---|---|
| `parallel` | forwards to `gix-features/parallel` |
| `sha1` | forwards to `gix-hash/sha1` |
| `sha256` | forwards to `gix-hash/sha256` |
| `worktree-rewrites` | enables the `gix-dir` and `gix-diff` dependencies and the `index_as_worktree_with_renames` module |

The default feature set must be exactly `["sha1", "worktree-rewrites"]`, so that
every item in the API Catalog is reachable in a plain `cargo build` with no feature
flags and so that `gix-hash` has an object-hash implementation available. Additional
features may exist, but no item listed in the Import Surface may be gated behind a
feature that is off by default.

## Appendix B: Assessment Notes

The behavior described here is observable on a case-sensitive filesystem that
supports symbolic links and the executable bit; that is the environment in which
conformance is assessed. `gix_fs::Capabilities::default()` reports
`executable_bit: true` and `symlink: true` there, and `Options::default()` therefore
enables both checks.

Assessment drives the library through its public entry points with a hand-built
`gix_index::State` and a hand-built in-memory object database implementing
`gix_object::Find` and `gix_object::FindHeader`, so no on-disk Git repository is
required and no `git` binary is invoked.

Counters on `Outcome` are part of the contract and are asserted directly, because
they are the only externally visible evidence that the fast path was taken. In
particular a run that reports no status but read files from disk is a conformance
failure even though its statuses are correct.

Timestamps in the assessment fixtures are fixed constants rather than the current
clock, so racy-clean behavior is exercised deterministically by choosing the index
timestamp relative to the recorded file modification time rather than by racing the
filesystem.
