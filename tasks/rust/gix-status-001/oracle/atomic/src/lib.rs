//! Atomic layer: one documented behavior per test.
//!
//! Every test here makes a single call into the crate under specification and
//! asserts on one rule from the specification. There are no `mod` blocks: the
//! harness discovers tests by scanning this file for `#[test]`, and a nested
//! module changes the reported name without changing what is discovered.
//!
//! The fixtures come from `common`, which builds an index, an object database
//! and a working tree in memory. Nothing reads a fixture archive and nothing
//! shells out to `git`, so a failure here is always about this crate.
//!
//! Nothing in this file names `index_as_worktree_with_renames`. In Rust a
//! single wrong signature is a whole-binary compile error, and the renames
//! surface mentions nine foreign types; keeping it in `integration` means a
//! candidate that gets it wrong still gets measured on everything else.

use std::path::Path;

use common::{
    paths, pathspecs, run, run_delegating, run_interrupted, run_with, DirtySubmodules, Fixture,
    NoSubmodules, PAST,
};
use gix_index::entry::{Flags, Mode, Stage};
use gix_status::{
    index_as_worktree::{
        traits::{FastEq, HashEq},
        Change, Conflict, EntryStatus, Options,
    },
    SymlinkCheck,
};

/// The summary a run reports for a path conflicted at exactly `stages`.
///
/// Not a test itself. Each stage combination is a separate documented mapping,
/// so each gets its own `#[test]` below; this only removes the copy of the
/// fixture that would otherwise appear seven times.
fn conflict_summary(stages: &[u8]) -> Conflict {
    let mut fixture = Fixture::new();
    fixture.track_conflict("c.txt", stages);
    let fixture = fixture.finish();
    let (records, _outcome) = run(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
    );
    assert_eq!(
        paths(&records),
        ["c.txt"],
        "a conflicted path is reported exactly once, whatever its stages"
    );
    match &records[0].1 {
        EntryStatus::Conflict { summary, .. } => *summary,
        other => panic!("a conflicted entry must be reported as a conflict, got {other:?}"),
    }
}

// ── clean, modified, and what that costs ─────────────────────────────────

#[test]
fn a_clean_tracked_file_produces_no_status() {
    let mut fixture = Fixture::new();
    fixture.track_clean("a.txt", b"hello\n");
    let fixture = fixture.finish();

    let (records, outcome) = run(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
    );

    assert!(
        records.is_empty(),
        "an entry whose worktree state matches the index is not reported at all, got {records:?}"
    );
    assert_eq!(outcome.entries_to_process, 1);
    assert_eq!(outcome.entries_processed, 1);
    assert_eq!(outcome.entries_to_update, 0);
    assert_eq!(
        outcome.worktree_files_read, 0,
        "the stat fast path reads nothing"
    );
    assert_eq!(outcome.worktree_bytes, 0);
}

#[test]
fn changed_content_is_reported_as_a_modification() {
    let mut fixture = Fixture::new();
    fixture.track_modified("b.txt", b"one\n", b"two\n");
    let fixture = fixture.finish();

    let (records, _outcome) = run(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
    );

    assert_eq!(paths(&records), ["b.txt"]);
    assert_eq!(
        records[0].1,
        EntryStatus::Change(Change::Modification {
            executable_bit_changed: false,
            content_change: Some(()),
            set_entry_stat_size_zero: false,
        }),
        "only the content differs, so only `content_change` is set"
    );
}

#[test]
fn a_content_comparison_that_reads_the_file_counts_its_bytes() {
    let mut fixture = Fixture::new();
    // Same length on both sides, so the size fast path cannot decide and the
    // worktree file really is read.
    fixture.track_modified("b.txt", b"one\n", b"two\n");
    let fixture = fixture.finish();

    let (_records, outcome) = run(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
    );

    assert_eq!(outcome.worktree_files_read, 1);
    assert_eq!(
        outcome.worktree_bytes, 4,
        "`worktree_bytes` sums the sizes of the files that were read"
    );
    assert_eq!(
        outcome.odb_objects_read, 0,
        "comparing by hash needs the worktree side only"
    );
    assert_eq!(outcome.odb_bytes, 0);
}

#[test]
fn fast_eq_reports_a_size_difference_without_reading_the_file() {
    let mut fixture = Fixture::new();
    fixture.track_modified("b.txt", b"short\n", b"a considerably longer body\n");
    let fixture = fixture.finish();

    let (records, outcome) = run(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
    );

    assert_eq!(
        records[0].1,
        EntryStatus::Change(Change::Modification {
            executable_bit_changed: false,
            content_change: Some(()),
            set_entry_stat_size_zero: false,
        })
    );
    assert_eq!(
        outcome.worktree_files_read, 0,
        "the recorded size already settles the question"
    );
    assert_eq!(outcome.worktree_bytes, 0);
}

// ── the worktree disagrees about what is there ───────────────────────────

#[test]
fn a_missing_worktree_file_is_reported_as_removed() {
    let mut fixture = Fixture::new();
    fixture.track_absent("gone.txt", b"gone\n");
    let fixture = fixture.finish();

    let (records, _outcome) = run(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
    );

    assert_eq!(paths(&records), ["gone.txt"]);
    assert_eq!(records[0].1, EntryStatus::Change(Change::Removed));
}

#[test]
fn a_directory_in_place_of_a_file_is_reported_as_removed() {
    let mut fixture = Fixture::new();
    fixture.track_dir_in_place_of_file("dir.txt", b"was a file\n");
    let fixture = fixture.finish();

    let (records, _outcome) = run(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
    );

    assert_eq!(paths(&records), ["dir.txt"]);
    assert_eq!(
        records[0].1,
        EntryStatus::Change(Change::Removed),
        "a directory is not a type change, it is the absence of the tracked file"
    );
}

#[test]
fn a_path_reached_through_a_symlink_is_reported_as_removed() {
    let mut fixture = Fixture::new();
    std::fs::create_dir_all(fixture.root().join("sub")).expect("mkdir");
    fixture.write("sub/file", b"real\n");
    std::os::unix::fs::symlink("sub", fixture.root().join("link")).expect("symlink");
    let id = fixture.odb.insert_blob(b"real\n");
    fixture.push("link/file", Default::default(), id, Flags::empty(), Mode::FILE);
    let fixture = fixture.finish();

    let (records, _outcome) = run(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
    );

    assert_eq!(paths(&records), ["link/file"]);
    assert_eq!(
        records[0].1,
        EntryStatus::Change(Change::Removed),
        "the bytes are reachable, but not without leaving the working tree"
    );
}

#[test]
fn a_symlink_in_place_of_a_file_is_reported_as_a_type_change() {
    let mut fixture = Fixture::new();
    fixture.track_symlink_in_place_of_file("link", "a.txt");
    let fixture = fixture.finish();

    let (records, _outcome) = run(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
    );

    assert_eq!(paths(&records), ["link"]);
    assert_eq!(
        records[0].1,
        EntryStatus::Change(Change::Type {
            worktree_mode: Mode::SYMLINK
        }),
        "the reported mode is the one derived from the worktree, not the index"
    );
}

// ── entry flags ──────────────────────────────────────────────────────────

#[test]
fn a_skip_worktree_entry_is_never_visited() {
    let mut fixture = Fixture::new();
    fixture.track_flagged("s.txt", b"indexed\n", b"different\n", Flags::SKIP_WORKTREE);
    let fixture = fixture.finish();

    let (records, outcome) = run(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
    );

    assert!(
        records.is_empty(),
        "the flag is the caller's assertion that the worktree state is known"
    );
    assert_eq!(outcome.entries_skipped_by_entry_flags, 1);
    assert_eq!(
        outcome.symlink_metadata_calls, 0,
        "a skipped entry costs no `lstat`"
    );
}

#[test]
fn an_intent_to_add_entry_is_reported_without_a_content_comparison() {
    let mut fixture = Fixture::new();
    fixture.track_flagged("i.txt", b"indexed\n", b"different\n", Flags::INTENT_TO_ADD);
    let fixture = fixture.finish();

    let (records, outcome) = run(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
    );

    assert_eq!(paths(&records), ["i.txt"]);
    assert_eq!(
        records[0].1,
        EntryStatus::IntentToAdd,
        "the promised content is not in the database yet, so no comparison is meaningful"
    );
    assert_eq!(outcome.worktree_files_read, 0);
}

// ── stat data that is merely stale ───────────────────────────────────────

#[test]
fn identical_content_behind_a_stale_stat_asks_for_an_index_update() {
    let mut fixture = Fixture::new();
    fixture.track_stale_stat("s.txt", b"content\n");
    let fixture = fixture.finish();

    let (records, outcome) = run(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
    );

    assert_eq!(paths(&records), ["s.txt"]);
    let fresh = match &records[0].1 {
        EntryStatus::NeedsUpdate(stat) => *stat,
        other => panic!("unchanged content behind stale stat data is not a change: {other:?}"),
    };
    assert_eq!(
        fresh.mtime.secs, PAST as u32,
        "the reported stat is the freshly observed one, not the recorded one"
    );
    assert_eq!(fresh.size, b"content\n".len() as u32);
    assert_eq!(outcome.entries_to_update, 1);
}

#[test]
fn a_flipped_executable_bit_is_a_modification_without_a_content_change() {
    let mut fixture = Fixture::new();
    fixture.track_executable_flip("x.sh", b"#!/bin/sh\n");
    let fixture = fixture.finish();

    let (records, _outcome) = run(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
    );

    assert_eq!(paths(&records), ["x.sh"]);
    assert_eq!(
        records[0].1,
        EntryStatus::Change(Change::Modification {
            executable_bit_changed: true,
            content_change: None,
            set_entry_stat_size_zero: false,
        }),
        "an executable-bit change is never a `Change::Type`"
    );
}

// ── racy cleanliness ─────────────────────────────────────────────────────

#[test]
fn a_racy_entry_whose_content_changed_is_reported_and_counted() {
    let mut fixture = Fixture::new();
    fixture.track_racy("racy.txt", b"one\n", b"two\n");
    let fixture = fixture.finish_racy();

    let (records, outcome) = run(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
    );

    assert_eq!(paths(&records), ["racy.txt"]);
    assert_eq!(
        records[0].1,
        EntryStatus::Change(Change::Modification {
            executable_bit_changed: false,
            content_change: Some(()),
            set_entry_stat_size_zero: true,
        }),
        "the stat matched, so only the racy rule could have found this difference"
    );
    assert_eq!(outcome.racy_clean, 1);
}

#[test]
fn a_fresh_index_timestamp_makes_the_same_entry_clean() {
    let mut fixture = Fixture::new();
    // Byte-for-byte the fixture above, differing only in the index timestamp.
    fixture.track_racy("racy.txt", b"one\n", b"two\n");
    let fixture = fixture.finish();

    let (records, outcome) = run(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
    );

    assert!(
        records.is_empty(),
        "with a strictly newer index timestamp, matching stat data is conclusive: {records:?}"
    );
    assert_eq!(outcome.racy_clean, 0);
    assert_eq!(outcome.worktree_files_read, 0);
}

#[test]
fn an_interrupt_stops_the_walk_without_making_it_an_error() {
    let mut fixture = Fixture::new();
    fixture.track_modified("a.txt", b"one\n", b"two\n");
    fixture.track_absent("b.txt", b"gone\n");
    let fixture = fixture.finish();

    let (records, outcome) = run_interrupted(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
    );

    assert!(
        records.is_empty(),
        "the flag was already set, so nothing was ever looked at: {records:?}"
    );
    assert_eq!(outcome.entries_to_process, 2);
    assert_eq!(
        outcome.entries_processed, 0,
        "the caller detects the early stop by comparing these two counters"
    );
}

// ── pathspec and prefix filtering ────────────────────────────────────────

#[test]
fn a_pathspec_prefix_skips_entries_before_the_pathspec_is_consulted() {
    let mut fixture = Fixture::new();
    fixture.track_modified("a/one.txt", b"1\n", b"x\n");
    fixture.track_modified("a/two.txt", b"2\n", b"y\n");
    fixture.track_modified("b/three.txt", b"3\n", b"z\n");
    let fixture = fixture.finish();

    let (records, outcome) = run_with(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
        pathspecs(&["a/"]),
    );

    assert_eq!(paths(&records), ["a/one.txt", "a/two.txt"]);
    assert_eq!(
        outcome.entries_skipped_by_common_prefix, 1,
        "`b/three.txt` cannot match a pathspec whose common prefix is `a`"
    );
    assert_eq!(outcome.entries_skipped_by_pathspec, 0);
    assert_eq!(outcome.entries_to_process, 2);
}

#[test]
fn an_exclude_pathspec_skips_an_entry_the_prefix_admitted() {
    let mut fixture = Fixture::new();
    fixture.track_modified("a/one.txt", b"1\n", b"x\n");
    fixture.track_modified("a/two.txt", b"2\n", b"y\n");
    fixture.track_modified("b/three.txt", b"3\n", b"z\n");
    let fixture = fixture.finish();

    let (records, outcome) = run_with(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
        pathspecs(&["a/", ":(exclude)a/two.txt"]),
    );

    assert_eq!(paths(&records), ["a/one.txt"]);
    assert_eq!(outcome.entries_skipped_by_common_prefix, 1);
    assert_eq!(
        outcome.entries_skipped_by_pathspec, 1,
        "the prefix let `a/two.txt` through, the pathspec itself rejected it"
    );
    assert_eq!(outcome.entries_processed, 2);
}

#[test]
fn pathspecs_without_a_common_prefix_skip_nothing_by_prefix() {
    let mut fixture = Fixture::new();
    fixture.track_modified("a/one.txt", b"1\n", b"x\n");
    fixture.track_modified("a/two.txt", b"2\n", b"y\n");
    fixture.track_modified("b/three.txt", b"3\n", b"z\n");
    let fixture = fixture.finish();

    let (records, outcome) = run_with(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
        pathspecs(&["a/one.txt", "b/three.txt"]),
    );

    assert_eq!(paths(&records), ["a/one.txt", "b/three.txt"]);
    assert_eq!(
        outcome.entries_skipped_by_common_prefix, 0,
        "two specs in different directories share no prefix to skip by"
    );
    assert_eq!(outcome.entries_skipped_by_pathspec, 1);
    assert_eq!(outcome.entries_to_process, 3);
}

#[test]
fn skipped_sums_the_three_skip_counters() {
    let mut fixture = Fixture::new();
    fixture.track_modified("a/one.txt", b"1\n", b"x\n");
    fixture.track_modified("a/two.txt", b"2\n", b"y\n");
    fixture.track_flagged(
        "a/three.txt",
        b"indexed\n",
        b"different\n",
        Flags::SKIP_WORKTREE,
    );
    fixture.track_modified("b/four.txt", b"4\n", b"w\n");
    let fixture = fixture.finish();

    let (_records, outcome) = run_with(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
        pathspecs(&["a/", ":(exclude)a/two.txt"]),
    );

    assert_eq!(outcome.entries_skipped_by_common_prefix, 1);
    assert_eq!(outcome.entries_skipped_by_pathspec, 1);
    assert_eq!(outcome.entries_skipped_by_entry_flags, 1);
    assert_eq!(
        outcome.skipped(),
        3,
        "`skipped()` is the sum of the three skip counters and nothing else"
    );
}

// ── conflict summaries ───────────────────────────────────────────────────

#[test]
fn a_base_stage_on_its_own_is_both_deleted() {
    assert_eq!(conflict_summary(&[1]), Conflict::BothDeleted);
}

#[test]
fn an_ours_stage_on_its_own_is_added_by_us() {
    assert_eq!(conflict_summary(&[2]), Conflict::AddedByUs);
}

#[test]
fn a_base_and_an_ours_stage_are_deleted_by_them() {
    assert_eq!(conflict_summary(&[1, 2]), Conflict::DeletedByThem);
}

#[test]
fn a_theirs_stage_on_its_own_is_added_by_them() {
    assert_eq!(conflict_summary(&[3]), Conflict::AddedByThem);
}

#[test]
fn a_base_and_a_theirs_stage_are_deleted_by_us() {
    assert_eq!(conflict_summary(&[1, 3]), Conflict::DeletedByUs);
}

#[test]
fn an_ours_and_a_theirs_stage_are_both_added() {
    assert_eq!(conflict_summary(&[2, 3]), Conflict::BothAdded);
}

#[test]
fn all_three_stages_are_both_modified() {
    assert_eq!(conflict_summary(&[1, 2, 3]), Conflict::BothModified);
}

#[test]
fn a_conflict_carries_the_index_entry_of_every_stage_present() {
    let mut fixture = Fixture::new();
    let ids = fixture.track_conflict("c.txt", &[1, 3]);
    let fixture = fixture.finish();

    let (records, _outcome) = run(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
    );

    let entries = match &records[0].1 {
        EntryStatus::Conflict { entries, .. } => entries.clone(),
        other => panic!("expected a conflict, got {other:?}"),
    };
    assert!(
        entries[0].is_some() && entries[1].is_none() && entries[2].is_some(),
        "a slot is occupied only for a stage that is present, indexed by stage number"
    );
    let base = entries[0].as_ref().expect("stage 1 is present");
    let theirs = entries[2].as_ref().expect("stage 3 is present");
    assert_eq!(base.id, ids[0]);
    assert_eq!(theirs.id, ids[1]);
    assert_eq!(base.mode, Mode::FILE);
    assert_eq!(base.flags, Flags::from_stage(Stage::Base));
    assert_eq!(theirs.flags, Flags::from_stage(Stage::Theirs));
}

#[test]
fn try_from_entry_summarizes_the_stages_it_consumes() {
    let mut fixture = Fixture::new();
    fixture.track_conflict("x", &[1, 2, 3]);
    let fixture = fixture.finish();

    let (summary, consumed, seen) = Conflict::try_from_entry(
        fixture.index.entries(),
        fixture.index.path_backing(),
        0,
        "x".into(),
    )
    .expect("the entry at index 0 carries a conflict stage");

    assert_eq!(summary, Conflict::BothModified);
    assert_eq!(
        consumed, 2,
        "the count excludes the entry the search started at"
    );
    assert_eq!(seen.iter().filter(|entry| entry.is_some()).count(), 3);
}

#[test]
fn try_from_entry_declines_an_unconflicted_entry() {
    let mut fixture = Fixture::new();
    fixture.track_clean("y", b"plain\n");
    let fixture = fixture.finish();

    let got = Conflict::try_from_entry(
        fixture.index.entries(),
        fixture.index.path_backing(),
        0,
        "y".into(),
    );

    assert!(
        got.is_none(),
        "an entry at stage 0 has no conflict to describe"
    );
}

#[test]
fn a_multi_stage_conflict_counts_as_one_processed_entry() {
    let mut fixture = Fixture::new();
    fixture.track_conflict("c.txt", &[1, 2, 3]);
    let fixture = fixture.finish();

    let (records, outcome) = run(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
    );

    assert_eq!(records.len(), 1);
    assert_eq!(
        outcome.entries_to_process, 3,
        "every stage is an index entry that has to be looked at"
    );
    assert_eq!(
        outcome.entries_processed, 1,
        "the three of them resolve to one reported conflict"
    );
}

// ── comparison and submodule delegates ───────────────────────────────────

#[test]
fn hash_eq_reports_the_object_id_of_the_worktree_content() {
    let mut fixture = Fixture::new();
    fixture.track_modified("m.txt", b"a\n", b"bb\n");
    let fixture = fixture.finish();
    let expected = gix_object::compute_hash(gix_hash::Kind::Sha1, gix_object::Kind::Blob, b"bb\n")
        .expect("sha1 is available");

    let (records, outcome) = run_delegating(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
        HashEq,
        NoSubmodules,
    );

    assert_eq!(paths(&records), ["m.txt"]);
    assert_eq!(
        records[0].1,
        EntryStatus::Change(Change::Modification {
            executable_bit_changed: false,
            content_change: Some(expected),
            set_entry_stat_size_zero: false,
        }),
        "the delegate's output is the worktree blob's id, which the caller can reuse"
    );
    assert_eq!(
        outcome.odb_objects_read, 0,
        "hashing the worktree side does not require fetching the indexed side"
    );
}

#[test]
fn a_submodule_entry_is_delegated_and_its_answer_is_reported() {
    let mut fixture = Fixture::new();
    fixture.track_submodule("sm");
    let fixture = fixture.finish();
    let delegate = DirtySubmodules::default();

    let (records, _outcome) = run_delegating(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
        FastEq,
        delegate.clone(),
    );

    assert_eq!(paths(&records), ["sm"]);
    assert_eq!(
        records[0].1,
        EntryStatus::Change(Change::SubmoduleModification("dirty"))
    );
    let seen: Vec<String> = delegate
        .seen
        .lock()
        .expect("uncontended")
        .iter()
        .map(ToString::to_string)
        .collect();
    assert_eq!(
        seen,
        ["sm"],
        "the delegate is asked about the submodule by its repository-relative path"
    );
}

#[test]
fn a_submodule_delegate_that_reports_nothing_produces_no_status() {
    let mut fixture = Fixture::new();
    fixture.track_submodule("sm");
    let fixture = fixture.finish();

    let (records, _outcome) = run(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
    );

    assert!(
        records.is_empty(),
        "only the delegate can decide a submodule changed, and this one said no: {records:?}"
    );
}

// ── symlink-safe path resolution ─────────────────────────────────────────

#[test]
fn verified_path_returns_the_absolute_path_of_an_existing_file() {
    let dir = tempfile::tempdir().expect("a writable temporary directory");
    std::fs::create_dir_all(dir.path().join("sub")).expect("mkdir");
    std::fs::write(dir.path().join("sub/file"), b"x").expect("write");
    let mut check = SymlinkCheck::new(dir.path().to_owned());

    let got = check
        .verified_path(Path::new("sub/file"))
        .expect("no component of `sub/file` is a symlink");

    assert_eq!(got, dir.path().join("sub/file"));
}

#[test]
fn verified_path_refuses_to_step_through_a_symlink() {
    let dir = tempfile::tempdir().expect("a writable temporary directory");
    std::fs::create_dir_all(dir.path().join("sub")).expect("mkdir");
    std::fs::write(dir.path().join("sub/file"), b"x").expect("write");
    std::os::unix::fs::symlink("sub", dir.path().join("link")).expect("symlink");
    let mut check = SymlinkCheck::new(dir.path().to_owned());

    let err = check
        .verified_path(Path::new("link/file"))
        .expect_err("`link` is a symlink, so the path leaves the working tree");

    assert_eq!(err.kind(), std::io::ErrorKind::Other);
    assert_eq!(
        err.to_string(),
        "Cannot step through symlink to perform an lstat"
    );
}

#[test]
fn verified_path_reports_a_missing_path_as_not_found() {
    let dir = tempfile::tempdir().expect("a writable temporary directory");
    let mut check = SymlinkCheck::new(dir.path().to_owned());

    let err = check
        .verified_path(Path::new("missing/file"))
        .expect_err("nothing was created under this root");

    assert_eq!(err.kind(), std::io::ErrorKind::NotFound);
}

#[test]
fn verified_path_allow_nonexisting_accepts_a_path_that_does_not_exist() {
    let dir = tempfile::tempdir().expect("a writable temporary directory");
    let mut check = SymlinkCheck::new(dir.path().to_owned());

    let got = check
        .verified_path_allow_nonexisting("missing/file".into())
        .expect("absence is not a symlink");

    assert_eq!(
        got.as_ref(),
        dir.path().join("missing/file"),
        "the path it would have had is returned"
    );
}

#[test]
fn verified_path_allow_nonexisting_still_refuses_a_symlinked_component() {
    let dir = tempfile::tempdir().expect("a writable temporary directory");
    std::fs::create_dir_all(dir.path().join("sub")).expect("mkdir");
    std::os::unix::fs::symlink("sub", dir.path().join("link")).expect("symlink");
    let mut check = SymlinkCheck::new(dir.path().to_owned());

    let err = check
        .verified_path_allow_nonexisting("link/file".into())
        .expect_err("the guarantee is about symlinks, not about existence");

    assert_eq!(err.kind(), std::io::ErrorKind::Other);
}

#[test]
fn symlink_check_exposes_the_working_tree_root() {
    let dir = tempfile::tempdir().expect("a writable temporary directory");
    let check = SymlinkCheck::new(dir.path().to_owned());

    assert_eq!(
        check.inner.root(),
        dir.path(),
        "`inner` is public so the root it was built from can be queried"
    );
}
