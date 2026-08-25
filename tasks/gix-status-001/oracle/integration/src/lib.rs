//! Integration layer: behaviors that only exist across more than one call.
//!
//! Every test here either runs the operation twice and relates the two runs, or
//! composes the two entry points, or checks a cross-view invariant that no
//! single assertion in `atomic` can express. Each names the atomic behaviors it
//! rests on in a `DependsOn` comment: when an atomic test and the integration
//! tests above it fail together, the atomic one is the report to read.
//!
//! This is the only file that names `index_as_worktree_with_renames`. Its
//! declared signatures mention `gix_dir` and `gix_diff` types, and a candidate
//! that reproduces them incorrectly fails to compile -- confined to this
//! binary, so `atomic` is still measured.

use std::path::Path;
use std::sync::atomic::AtomicBool;

use common::{paths, pathspecs, run, run_delegating, run_with, DirtySubmodules, Fixture, NoSubmodules, INDEX_TS};
use gix_index::entry::Flags;
use gix_status::{
    index_as_worktree::{
        traits::{FastEq, HashEq}, Change, Conflict, EntryStatus, Options, Outcome as TrackedOutcome,
    },
    index_as_worktree_with_renames::{
        Context, DirwalkContext, Options as RenameOptions, Outcome as RenameOutcome,
        Recorder as RenameRecorder, Sorting, Summary,
    },
};

/// The diff platform the renames entry point needs to compare a removed index
/// entry against an untracked worktree file.
fn resource_cache(root: &Path) -> gix_diff::blob::Platform {
    gix_diff::blob::Platform::new(
        Default::default(),
        gix_diff::blob::Pipeline::new(
            gix_diff::blob::pipeline::WorktreeRoots {
                old_root: None,
                new_root: Some(root.to_owned()),
            },
            gix_filter::Pipeline::default(),
            Vec::new(),
            Default::default(),
        ),
        gix_diff::blob::pipeline::Mode::ToGit,
        common::attr_stack(root),
    )
}

/// One reported entry of a renames run, reduced to what the specification talks
/// about: the summary, the source path and the destination path.
type Reduced = (Option<Summary>, String, String);

/// Run `index_as_worktree_with_renames` over `fixture` and reduce its report.
///
/// The `.git` directory is created because the dirwalk needs a real path to
/// exclude; nothing else in the oracle depends on a repository being there.
fn run_renames(
    fixture: &Fixture,
    dirwalk: bool,
    rewrites: Option<gix_diff::Rewrites>,
) -> (Vec<Reduced>, RenameOutcome) {
    let root = fixture.root();
    let git_dir = root.join(".git");
    std::fs::create_dir_all(&git_dir).expect("mkdir");
    let current_dir = std::env::current_dir().expect("a current directory");
    let interrupt = AtomicBool::default();
    let mut recorder: RenameRecorder<'_, (), ()> = RenameRecorder { records: Vec::new() };
    let mut progress = gix_features::progress::Discard;

    let outcome = gix_status::index_as_worktree_with_renames(
        &fixture.index,
        root,
        &mut recorder,
        FastEq,
        NoSubmodules,
        fixture.odb.clone(),
        &mut progress,
        Context {
            pathspec: common::all_paths(),
            resource_cache: resource_cache(root),
            should_interrupt: &interrupt,
            dirwalk: DirwalkContext {
                git_dir_realpath: &git_dir,
                current_dir: &current_dir,
                ignore_case_index_lookup: None,
            },
        },
        RenameOptions {
            sorting: Some(Sorting::ByPathCaseSensitive),
            object_hash: gix_hash::Kind::Sha1,
            tracked_file_modifications: Options::default(),
            fscache: false,
            dirwalk: dirwalk.then(gix_dir::walk::Options::default),
            rewrites,
        },
    )
    .expect("the fixtures never provoke an error");

    let reduced = recorder
        .records
        .iter()
        .map(|entry| {
            (
                entry.summary(),
                entry.source_rela_path().to_string(),
                entry.destination_rela_path().to_string(),
            )
        })
        .collect();
    (reduced, outcome)
}

// ── one run, many entries ────────────────────────────────────────────────

// DependsOn: a_clean_tracked_file_produces_no_status
// DependsOn: changed_content_is_reported_as_a_modification
// DependsOn: a_missing_worktree_file_is_reported_as_removed
// DependsOn: a_symlink_in_place_of_a_file_is_reported_as_a_type_change
// DependsOn: a_skip_worktree_entry_is_never_visited
// A single index holding one of every shape at once. Each entry has to get the
// status it would have got on its own, in path order, and the counters have to
// account for every entry in the index exactly once -- which is the part no
// atomic test can see, because each of them has only one entry to account for.
#[test]
fn a_mixed_index_reports_every_entry_once_and_accounts_for_all_of_them() {
    let mut fixture = Fixture::new();
    fixture.track_clean("clean.txt", b"unchanged\n");
    fixture.track_modified("modified.txt", b"one\n", b"two\n");
    fixture.track_absent("removed.txt", b"gone\n");
    fixture.track_flagged("skipped.txt", b"indexed\n", b"other\n", Flags::SKIP_WORKTREE);
    fixture.track_symlink_in_place_of_file("typechanged", "clean.txt");
    let fixture = fixture.finish();
    let entries_in_index = fixture.index.entries().len();

    let (records, outcome) = run(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
    );

    assert_eq!(
        paths(&records),
        ["modified.txt", "removed.txt", "typechanged"],
        "the clean entry and the skipped entry are the two that stay silent"
    );
    assert!(matches!(
        records[0].1,
        EntryStatus::Change(Change::Modification { .. })
    ));
    assert_eq!(records[1].1, EntryStatus::Change(Change::Removed));
    assert!(matches!(
        records[2].1,
        EntryStatus::Change(Change::Type { .. })
    ));

    assert_eq!(
        outcome.entries_to_process + outcome.entries_skipped_by_common_prefix,
        entries_in_index,
        "every index entry is either processed or skipped by the common prefix"
    );
    assert_eq!(outcome.entries_skipped_by_entry_flags, 1);
    assert_eq!(
        outcome.skipped(),
        outcome.entries_skipped_by_common_prefix
            + outcome.entries_skipped_by_pathspec
            + outcome.entries_skipped_by_entry_flags
    );
}

// DependsOn: changed_content_is_reported_as_a_modification
// DependsOn: a_missing_worktree_file_is_reported_as_removed
// DependsOn: a_clean_tracked_file_produces_no_status
// Two runs over the same inputs that differ only in `thread_limit`. The
// specification allows the thread count to change how fast the answer arrives
// and nothing else, so the reports have to be equal element by element --
// including their order, which is what a parallel implementation is most likely
// to get wrong.
#[test]
fn the_thread_limit_never_changes_what_is_reported() {
    let mut fixture = Fixture::new();
    for index in 0..12 {
        fixture.track_modified(
            &format!("dir{}/file{index}.txt", index % 3),
            b"one\n",
            b"two\n",
        );
        fixture.track_clean(&format!("dir{}/clean{index}.txt", index % 3), b"same\n");
    }
    fixture.track_absent("zz-removed.txt", b"gone\n");
    let fixture = fixture.finish();

    let mut reports = Vec::new();
    for thread_limit in [None, Some(1), Some(4)] {
        let (records, outcome) = run(
            &fixture.index,
            fixture.root(),
            fixture.odb.clone(),
            Options {
                thread_limit,
                ..Default::default()
            },
        );
        reports.push((records, outcome));
    }

    assert_eq!(reports[0].0.len(), 13);
    assert_eq!(
        reports[0].0, reports[1].0,
        "an unbounded run and a single-threaded run must agree"
    );
    assert_eq!(reports[1].0, reports[2].0);
    assert_eq!(reports[0].1, reports[1].1, "the counters agree as well");
    assert_eq!(reports[1].1, reports[2].1);
}

// DependsOn: all_three_stages_are_both_modified
// DependsOn: changed_content_is_reported_as_a_modification
// DependsOn: a_clean_tracked_file_produces_no_status
// A conflict occupies three index entries but produces one report, so an index
// that mixes conflicted and unconflicted paths is the case where a wrong stride
// through the entry array shows up: the entries after the conflict are either
// skipped or visited twice.
#[test]
fn a_conflict_does_not_disturb_the_entries_around_it() {
    let mut fixture = Fixture::new();
    fixture.track_modified("a-before.txt", b"one\n", b"two\n");
    fixture.track_conflict("m-conflicted.txt", &[1, 2, 3]);
    fixture.track_modified("z-after.txt", b"three\n", b"four\n");
    fixture.track_clean("z-clean.txt", b"same\n");
    let fixture = fixture.finish();

    let (records, outcome) = run(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
    );

    assert_eq!(
        paths(&records),
        ["a-before.txt", "m-conflicted.txt", "z-after.txt"]
    );
    let summary = match &records[1].1 {
        EntryStatus::Conflict { summary, .. } => *summary,
        other => panic!("expected a conflict in the middle, got {other:?}"),
    };
    assert_eq!(summary, Conflict::BothModified);
    assert_eq!(
        outcome.entries_to_process, 6,
        "three stages plus three ordinary entries"
    );
    assert_eq!(
        outcome.entries_processed, 4,
        "the three stages collapse into one processed entry"
    );
}

// ── run, apply, run again ────────────────────────────────────────────────

// DependsOn: identical_content_behind_a_stale_stat_asks_for_an_index_update
// DependsOn: a_clean_tracked_file_produces_no_status
// The `NeedsUpdate` report is a request, and the specification says what
// granting it achieves: a second run over an otherwise unchanged tree reports
// nothing and reads nothing. That is a claim about two runs, so it can only be
// checked here. An implementation that reports a stat it did not actually
// observe passes the atomic test and fails this one.
#[test]
fn applying_every_needs_update_stat_makes_the_next_run_silent() {
    let mut fixture = Fixture::new();
    fixture.track_stale_stat("one.txt", b"first\n");
    fixture.track_stale_stat("two.txt", b"second\n");
    fixture.track_clean("three.txt", b"third\n");
    let mut fixture = fixture.finish();

    let (records, outcome) = run(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
    );
    assert_eq!(paths(&records), ["one.txt", "two.txt"]);
    assert_eq!(
        outcome.entries_to_update,
        records.len(),
        "`entries_to_update` counts exactly the `NeedsUpdate` reports"
    );

    let fresh: Vec<_> = records
        .iter()
        .map(|(path, status)| match status {
            EntryStatus::NeedsUpdate(stat) => (path.clone(), *stat),
            other => panic!("expected a stat refresh request, got {other:?}"),
        })
        .collect();
    for (path, stat) in fresh {
        let position = fixture
            .index
            .entry_index_by_path(path.as_ref())
            .expect("every reported path is an index entry");
        fixture.index.entries_mut()[position].stat = stat;
    }

    let (records, outcome) = run(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
    );
    assert!(
        records.is_empty(),
        "granting the refresh leaves nothing to report: {records:?}"
    );
    assert_eq!(outcome.entries_to_update, 0);
    assert_eq!(
        outcome.worktree_files_read, 0,
        "and nothing left to read either"
    );
}

// DependsOn: a_racy_entry_whose_content_changed_is_reported_and_counted
// DependsOn: a_fresh_index_timestamp_makes_the_same_entry_clean
// The racy rule exists so that a second run still sees a difference the first
// run could only find by reading the file. Following the hint -- zeroing the
// recorded size -- must make the difference visible from stat data alone, so
// the second run reports the same modification while reading nothing.
#[test]
fn zeroing_the_recorded_size_keeps_a_racy_modification_visible() {
    let mut fixture = Fixture::new();
    fixture.track_racy("racy.txt", b"one\n", b"two\n");
    let mut fixture = fixture.finish_racy();

    let (records, outcome) = run(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
    );
    let zero_the_size = match &records[0].1 {
        EntryStatus::Change(Change::Modification {
            set_entry_stat_size_zero,
            ..
        }) => *set_entry_stat_size_zero,
        other => panic!("expected a modification, got {other:?}"),
    };
    assert!(zero_the_size, "the first run has to ask for the zeroing");
    assert_eq!(outcome.racy_clean, 1);
    assert_eq!(outcome.worktree_files_read, 1);

    fixture.index.entries_mut()[0].stat.size = 0;
    let (records, outcome) = run(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
    );

    assert_eq!(paths(&records), ["racy.txt"]);
    assert!(
        matches!(
            records[0].1,
            EntryStatus::Change(Change::Modification {
                content_change: Some(()),
                ..
            })
        ),
        "the difference is still reported after the hint was followed"
    );
    assert_eq!(
        outcome.racy_clean, 0,
        "and it is no longer the racy rule that finds it"
    );
}

// DependsOn: a_pathspec_prefix_skips_entries_before_the_pathspec_is_consulted
// DependsOn: changed_content_is_reported_as_a_modification
// DependsOn: a_missing_worktree_file_is_reported_as_removed
// Narrowing the run with a pathspec must change which entries are looked at and
// nothing about the answers given for the ones that survive. Comparing a narrow
// run against the corresponding slice of a full run is the only way to state
// that, and it catches an implementation that lets the pathspec leak into the
// status computation.
#[test]
fn a_pathspec_changes_which_entries_are_seen_and_not_what_is_said_about_them() {
    let mut fixture = Fixture::new();
    fixture.track_modified("a/one.txt", b"one\n", b"two\n");
    fixture.track_absent("a/two.txt", b"gone\n");
    fixture.track_clean("a/three.txt", b"same\n");
    fixture.track_modified("b/four.txt", b"three\n", b"four\n");
    let fixture = fixture.finish();

    let (everything, full) = run(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
    );
    let (narrowed, narrow) = run_with(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
        pathspecs(&["a/"]),
    );

    assert_eq!(paths(&everything), ["a/one.txt", "a/two.txt", "b/four.txt"]);
    assert_eq!(paths(&narrowed), ["a/one.txt", "a/two.txt"]);
    let expected: Vec<_> = everything
        .iter()
        .filter(|(path, _)| path.to_string().starts_with("a/"))
        .cloned()
        .collect();
    assert_eq!(
        narrowed, expected,
        "the surviving entries get the same status they got in the full run"
    );
    assert_eq!(full.entries_skipped_by_common_prefix, 0);
    assert_eq!(narrow.entries_skipped_by_common_prefix, 1);
    assert_eq!(
        narrow.worktree_files_read, 1,
        "the excluded entry's file is never opened"
    );
}

// DependsOn: changed_content_is_reported_as_a_modification
// DependsOn: identical_content_behind_a_stale_stat_asks_for_an_index_update
// The operation answers questions and changes nothing. Checking that needs a
// before-and-after picture of the working tree, the index and the object
// database around a run that has every reason to want to write: a stale stat it
// would like refreshed and a modification it had to read the file for.
#[test]
fn a_run_leaves_the_working_tree_the_index_and_the_database_alone() {
    let mut fixture = Fixture::new();
    fixture.track_modified("modified.txt", b"one\n", b"two\n");
    fixture.track_stale_stat("stale.txt", b"content\n");
    let fixture = fixture.finish();

    let before_tree = snapshot(fixture.root());
    let before_entries: Vec<_> = fixture
        .index
        .entries()
        .iter()
        .map(|entry| (entry.id, entry.stat, entry.mode, entry.flags))
        .collect();
    let before_timestamp = fixture.index.timestamp();

    let (records, _outcome) = run(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
    );
    assert_eq!(records.len(), 2, "the run did have something to report");

    assert_eq!(
        snapshot(fixture.root()),
        before_tree,
        "no file was created, rewritten or restamped"
    );
    let after_entries: Vec<_> = fixture
        .index
        .entries()
        .iter()
        .map(|entry| (entry.id, entry.stat, entry.mode, entry.flags))
        .collect();
    assert_eq!(
        after_entries, before_entries,
        "the refresh was reported, not applied"
    );
    assert_eq!(fixture.index.timestamp(), before_timestamp);
    assert_eq!(before_timestamp.unix_seconds(), INDEX_TS);
}

/// Path, length and modification time of every file under `root`, sorted.
fn snapshot(root: &Path) -> Vec<(String, u64, i64)> {
    fn walk(dir: &Path, root: &Path, out: &mut Vec<(String, u64, i64)>) {
        for entry in std::fs::read_dir(dir).expect("readable directory") {
            let entry = entry.expect("readable entry");
            let path = entry.path();
            let meta = std::fs::symlink_metadata(&path).expect("lstat");
            let rela = path
                .strip_prefix(root)
                .expect("under the root")
                .to_string_lossy()
                .into_owned();
            if meta.is_dir() {
                out.push((rela, 0, 0));
                walk(&path, root, out);
            } else {
                let mtime = filetime::FileTime::from_last_modification_time(&meta);
                out.push((rela, meta.len(), mtime.unix_seconds()));
            }
        }
    }
    let mut out = Vec::new();
    walk(root, root, &mut out);
    out.sort();
    out
}

// ── composing the two entry points ───────────────────────────────────────

// DependsOn: changed_content_is_reported_as_a_modification
// DependsOn: a_clean_tracked_file_produces_no_status
// DependsOn: a_missing_worktree_file_is_reported_as_removed
// With neither a directory walk nor rewrite tracking configured, the renames
// entry point is the tracked-file scan and nothing else. That has to be exactly
// true: the same statuses in the same order, each wrapped in
// `Entry::Modification`, and the same `Outcome` carried through unchanged.
#[test]
fn without_a_dirwalk_or_rewrites_the_renames_entry_point_is_the_plain_scan() {
    let mut fixture = Fixture::new();
    fixture.track_clean("clean.txt", b"same\n");
    fixture.track_modified("modified.txt", b"one\n", b"two\n");
    fixture.track_absent("removed.txt", b"gone\n");
    fixture.write("untracked.txt", b"not in the index\n");
    let fixture = fixture.finish();

    let (plain_records, plain_outcome) = run(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
    );
    let (reduced, outcome) = run_renames(&fixture, false, None);

    assert_eq!(
        reduced,
        vec![
            (
                Some(Summary::Modified),
                "modified.txt".to_owned(),
                "modified.txt".to_owned()
            ),
            (
                Some(Summary::Removed),
                "removed.txt".to_owned(),
                "removed.txt".to_owned()
            ),
        ],
        "the untracked file is invisible without a directory walk"
    );
    assert_eq!(paths(&plain_records), ["modified.txt", "removed.txt"]);
    assert!(
        outcome.dirwalk.is_none(),
        "no walk was configured, so none was run"
    );
    assert!(outcome.rewrites.is_none());
    assert_eq!(
        tracked_outcome_fields(&outcome.tracked_file_modification),
        tracked_outcome_fields(&plain_outcome),
        "the tracked outcome is carried through unchanged"
    );
}

/// The `Outcome` of a tracked scan as a comparable tuple.
///
/// `index_as_worktree::Outcome` is `PartialEq`, but spelling the fields out
/// names what the composition has to preserve.
fn tracked_outcome_fields(outcome: &TrackedOutcome) -> (usize, usize, usize, usize, usize, u64) {
    (
        outcome.entries_to_process,
        outcome.entries_processed,
        outcome.entries_skipped_by_common_prefix,
        outcome.entries_skipped_by_pathspec,
        outcome.worktree_files_read,
        outcome.worktree_bytes,
    )
}

// DependsOn: changed_content_is_reported_as_a_modification
// DependsOn: a_clean_tracked_file_produces_no_status
// Turning the directory walk on adds untracked worktree files to the same
// report, as `Entry::DirectoryContents` summarising to `Added`, without
// disturbing the tracked entries that were already there. Two runs over one
// fixture is the only way to show that it adds rather than replaces.
#[test]
fn a_directory_walk_adds_untracked_files_to_the_tracked_report() {
    let mut fixture = Fixture::new();
    fixture.track_clean("clean.txt", b"same\n");
    fixture.track_modified("modified.txt", b"one\n", b"two\n");
    fixture.write("untracked.txt", b"brand new\n");
    let fixture = fixture.finish();

    let (without_walk, _) = run_renames(&fixture, false, None);
    let (with_walk, outcome) = run_renames(&fixture, true, None);

    assert_eq!(
        without_walk,
        vec![(
            Some(Summary::Modified),
            "modified.txt".to_owned(),
            "modified.txt".to_owned()
        )]
    );
    assert_eq!(
        with_walk,
        vec![
            (
                Some(Summary::Modified),
                "modified.txt".to_owned(),
                "modified.txt".to_owned()
            ),
            (
                Some(Summary::Added),
                "untracked.txt".to_owned(),
                "untracked.txt".to_owned()
            ),
        ],
        "the walk adds the untracked file and leaves the tracked report alone"
    );
    assert!(
        outcome.dirwalk.is_some(),
        "a configured walk reports its own outcome"
    );
    assert!(outcome.rewrites.is_none());
}

// DependsOn: a_missing_worktree_file_is_reported_as_removed
// The point of rewrite tracking: the same tree that is reported as one removal
// plus one addition becomes one rename. The pair of runs is the assertion --
// with rewrites off the two halves must both be there, and with rewrites on
// they must both be gone, replaced by a single `Entry::Rewrite` naming the index
// path as source and the worktree path as destination.
#[test]
fn rewrite_tracking_replaces_a_removal_and_an_addition_with_one_rename() {
    let body = b"the quick brown fox jumps over the lazy dog\nline two\nline three\n";
    let mut fixture = Fixture::new();
    fixture.track_absent("old.txt", body);
    fixture.write("new.txt", body);
    let fixture = fixture.finish();

    let (separately, _) = run_renames(&fixture, true, None);
    let (as_rename, outcome) = run_renames(
        &fixture,
        true,
        Some(gix_diff::Rewrites {
            copies: None,
            percentage: Some(0.5),
            limit: 0,
            track_empty: false,
        }),
    );

    assert_eq!(
        separately,
        vec![
            (
                Some(Summary::Added),
                "new.txt".to_owned(),
                "new.txt".to_owned()
            ),
            (
                Some(Summary::Removed),
                "old.txt".to_owned(),
                "old.txt".to_owned()
            ),
        ],
        "without rewrite tracking the move is two unrelated findings"
    );
    assert_eq!(
        as_rename,
        vec![(
            Some(Summary::Renamed),
            "old.txt".to_owned(),
            "new.txt".to_owned()
        )],
        "with it, the two findings are one rename from the index path to the disk path"
    );
    assert!(
        outcome.rewrites.is_some(),
        "configured rewrite tracking reports its own outcome"
    );
}

// ── batch 1: cross-entry behaviors in a single run ──────────────────────

// DependsOn: a_clean_tracked_file_produces_no_status
// An index with several clean entries, not just one, should produce an
// empty report and zero `entries_to_update`. A single-entry atomic test
// cannot show that the "no report" guarantee scales, because a loop that
// accidentally breaks after the first entry would pass it.
#[test]
fn an_all_clean_index_produces_an_empty_report_and_zero_updates() {
    let mut fixture = Fixture::new();
    fixture.track_clean("alpha.txt", b"aaa\n");
    fixture.track_clean("beta.txt", b"bbb\n");
    fixture.track_clean("gamma.txt", b"ccc\n");
    fixture.track_clean("delta.txt", b"ddd\n");
    let fixture = fixture.finish();

    let (records, outcome) = run(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
    );

    assert!(
        records.is_empty(),
        "every entry is clean, so nothing is reported: {records:?}"
    );
    assert_eq!(outcome.entries_to_process, 4);
    assert_eq!(outcome.entries_processed, 4);
    assert_eq!(outcome.entries_to_update, 0);
    assert_eq!(outcome.worktree_files_read, 0);
    assert_eq!(outcome.worktree_bytes, 0);
}

// DependsOn: a_content_comparison_that_reads_the_file_counts_its_bytes
// INV-3: when every index entry has accurate stat data, the implementation
// must not open any worktree file. Verifying this with several entries
// in one run (rather than one at a time) catches an implementation that
// reads the first file to "prime" some shared state.
#[test]
fn stat_accurate_entries_are_never_read_from_disk() {
    let mut fixture = Fixture::new();
    fixture.track_clean("a.txt", b"data-a\n");
    fixture.track_clean("b.txt", b"data-b\n");
    fixture.track_clean("c.txt", b"data-c\n");
    fixture.track_absent("gone.txt", b"removed\n");
    let fixture = fixture.finish();

    let (records, outcome) = run(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
    );

    assert_eq!(
        paths(&records),
        ["gone.txt"],
        "only the absent entry is reported"
    );
    assert_eq!(
        outcome.worktree_files_read, 0,
        "the absent entry has no file to read, and the clean entries had accurate stat data"
    );
    assert_eq!(outcome.worktree_bytes, 0);
}

// DependsOn: all_three_stages_are_both_modified
// DependsOn: a_base_stage_on_its_own_is_both_deleted
// Two different conflict shapes in one run. Each must get the summary
// dictated by its own stages, not by its neighbour's stages. This catches
// an implementation that leaks state from one conflict to the next.
#[test]
fn multiple_conflict_shapes_coexist_in_one_run() {
    let mut fixture = Fixture::new();
    fixture.track_conflict("a-both-modified.txt", &[1, 2, 3]);
    fixture.track_conflict("b-both-deleted.txt", &[1]);
    fixture.track_conflict("c-added-by-us.txt", &[2]);
    let fixture = fixture.finish();

    let (records, outcome) = run(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
    );

    assert_eq!(
        paths(&records),
        ["a-both-modified.txt", "b-both-deleted.txt", "c-added-by-us.txt"]
    );
    let summaries: Vec<_> = records
        .iter()
        .map(|(_, status)| match status {
            EntryStatus::Conflict { summary, .. } => *summary,
            other => panic!("expected a conflict, got {other:?}"),
        })
        .collect();
    assert_eq!(
        summaries,
        [Conflict::BothModified, Conflict::BothDeleted, Conflict::AddedByUs],
        "each conflict gets the summary dictated by its own stages"
    );
    assert_eq!(
        outcome.entries_to_process, 5,
        "3 stages + 1 stage + 1 stage"
    );
    assert_eq!(
        outcome.entries_processed, 3,
        "each conflict collapses into one processed entry"
    );
}

// DependsOn: hash_eq_reports_the_object_id_of_the_worktree_content
// With `HashEq`, every changed file carries its worktree blob id. Running
// this across several files in one pass shows that the delegate is invoked
// per entry and each returned id matches the content that is actually on
// disk, not the neighbour's.
#[test]
fn hash_eq_reports_every_changed_file_in_one_pass() {
    let mut fixture = Fixture::new();
    fixture.track_modified("one.txt", b"idx-1\n", b"wt-1\n");
    fixture.track_modified("two.txt", b"idx-2\n", b"wt-2\n");
    fixture.track_clean("three.txt", b"same\n");
    let fixture = fixture.finish();

    let expected_1 = gix_object::compute_hash(
        gix_hash::Kind::Sha1,
        gix_object::Kind::Blob,
        b"wt-1\n",
    )
    .expect("sha1");
    let expected_2 = gix_object::compute_hash(
        gix_hash::Kind::Sha1,
        gix_object::Kind::Blob,
        b"wt-2\n",
    )
    .expect("sha1");

    let (records, _outcome) = run_delegating(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
        HashEq,
        NoSubmodules,
    );

    assert_eq!(paths(&records), ["one.txt", "two.txt"]);
    let ids: Vec<_> = records
        .iter()
        .map(|(_, status)| match status {
            EntryStatus::Change(Change::Modification {
                content_change: Some(id),
                ..
            }) => *id,
            other => panic!("expected a modification with id, got {other:?}"),
        })
        .collect();
    assert_eq!(ids[0], expected_1, "the first file's worktree hash");
    assert_eq!(ids[1], expected_2, "the second file's worktree hash");
}

// DependsOn: a_submodule_entry_is_delegated_and_its_answer_is_reported
// DependsOn: changed_content_is_reported_as_a_modification
// A submodule and a plain file change in the same run must both be reported
// and neither must interfere with the other's status. The submodule delegate
// is asked only about the submodule, not about the file.
#[test]
fn a_submodule_and_a_file_change_are_reported_independently() {
    let mut fixture = Fixture::new();
    fixture.track_modified("file.txt", b"one\n", b"two\n");
    fixture.track_submodule("submod");
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

    assert_eq!(paths(&records), ["file.txt", "submod"]);
    assert!(
        matches!(
            records[0].1,
            EntryStatus::Change(Change::Modification { .. })
        ),
        "the plain file gets its modification status"
    );
    assert_eq!(
        records[1].1,
        EntryStatus::Change(Change::SubmoduleModification("dirty")),
        "the submodule gets its delegate-provided status"
    );
    let seen: Vec<String> = delegate
        .seen
        .lock()
        .expect("uncontended")
        .iter()
        .map(ToString::to_string)
        .collect();
    assert_eq!(
        seen, ["submod"],
        "the delegate was only asked about the submodule, not the plain file"
    );
}

// ── batch 2: two-run comparisons and invariants ─────────────────────────

// DependsOn: hash_eq_reports_the_object_id_of_the_worktree_content
// DependsOn: changed_content_is_reported_as_a_modification
// Switching the comparison delegate changes `T` (the content_change output
// type) without changing which paths are visited or what shape of status
// they receive. Two runs over the same fixture — one with FastEq, one with
// HashEq — must find the same paths; only the `content_change` differs.
#[test]
fn a_delegate_switch_changes_the_output_type_but_not_which_paths_are_seen() {
    let mut fixture = Fixture::new();
    fixture.track_modified("a.txt", b"one\n", b"two\n");
    fixture.track_clean("b.txt", b"same\n");
    fixture.track_absent("c.txt", b"gone\n");
    let fixture = fixture.finish();

    let (fast_records, _) = run(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
    );
    let (hash_records, _) = run_delegating(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
        HashEq,
        NoSubmodules,
    );

    assert_eq!(
        paths(&fast_records),
        paths(&hash_records),
        "both delegates see the same paths"
    );
    assert_eq!(paths(&fast_records), ["a.txt", "c.txt"]);
}

// DependsOn: a_flipped_executable_bit_is_a_modification_without_a_content_change
// DependsOn: changed_content_is_reported_as_a_modification
// `executable_bit_changed` and `content_change` are independent axes: one
// entry can have only a bit change, another only a content change, and a
// third both. This test puts all three shapes in one run to prove that the
// two flags are never coupled.
#[test]
fn an_executable_bit_change_and_a_content_change_are_independent_axes() {
    let mut fixture = Fixture::new();
    fixture.track_executable_flip("bit-only.sh", b"#!/bin/sh\n");
    fixture.track_modified("content-only.txt", b"one\n", b"two\n");
    // Both: different content AND executable bit. We must set up the index
    // entry with the right stat for this to be detected.
    let path = fixture.write("both.sh", b"new-content\n");
    let id = fixture.odb.insert_blob(b"old-content\n");
    std::fs::set_permissions(
        &path,
        std::os::unix::fs::PermissionsExt::from_mode(0o755),
    )
    .expect("chmod");
    fixture.stamp("both.sh");
    let mut stat = fixture.stat_of("both.sh");
    stat.size = b"old-content\n".len() as u32;
    stat.mtime.secs = (common::PAST - 100) as u32;
    fixture.push("both.sh", stat, id, Flags::empty(), gix_index::entry::Mode::FILE);
    let fixture = fixture.finish();

    let (records, _outcome) = run(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
    );

    assert_eq!(paths(&records), ["bit-only.sh", "both.sh", "content-only.txt"]);
    assert_eq!(
        records[0].1,
        EntryStatus::Change(Change::Modification {
            executable_bit_changed: true,
            content_change: None,
            set_entry_stat_size_zero: false,
        }),
        "bit-only: executable changed, content unchanged"
    );
    assert!(
        matches!(
            records[1].1,
            EntryStatus::Change(Change::Modification {
                executable_bit_changed: true,
                content_change: Some(()),
                ..
            })
        ),
        "both: executable changed AND content changed"
    );
    assert_eq!(
        records[2].1,
        EntryStatus::Change(Change::Modification {
            executable_bit_changed: false,
            content_change: Some(()),
            set_entry_stat_size_zero: false,
        }),
        "content-only: only content changed"
    );
}

// DependsOn: a_racy_entry_whose_content_changed_is_reported_and_counted
// Multiple racy entries in one run: `racy_clean` must equal the number of
// entries that were racily clean, not just 1. This catches an implementation
// that treats racy-clean as a once-per-run flag.
#[test]
fn racy_clean_count_matches_the_number_of_entries_that_were_racy() {
    let mut fixture = Fixture::new();
    fixture.track_racy("a.txt", b"one\n", b"two\n");
    fixture.track_racy("b.txt", b"three\n", b"four\n");
    fixture.track_racy("c.txt", b"five\n", b"six\n");
    let fixture = fixture.finish_racy();

    let (records, outcome) = run(
        &fixture.index,
        fixture.root(),
        fixture.odb.clone(),
        Options::default(),
    );

    assert_eq!(paths(&records), ["a.txt", "b.txt", "c.txt"]);
    assert_eq!(
        outcome.racy_clean, 3,
        "every entry was racily clean, so all three are counted"
    );
    for (path, status) in &records {
        assert!(
            matches!(
                status,
                EntryStatus::Change(Change::Modification {
                    set_entry_stat_size_zero: true,
                    ..
                })
            ),
            "each racy entry must ask for the size zeroing: {path}"
        );
    }
}

// DependsOn: an_intent_to_add_entry_is_reported_without_a_content_comparison
// An intent-to-add entry in the renames report: its summary must be
// `Summary::IntentToAdd`, not `None` and not `Summary::Added`. This is a
// composition test because `summary()` is only defined on `Entry`, which
// only the renames entry point produces.
#[test]
fn an_intent_to_add_entry_has_its_own_summary_in_the_renames_report() {
    let mut fixture = Fixture::new();
    fixture.track_flagged("ita.txt", b"indexed\n", b"different\n", Flags::INTENT_TO_ADD);
    fixture.track_modified("changed.txt", b"one\n", b"two\n");
    let fixture = fixture.finish();

    let (reduced, _outcome) = run_renames(&fixture, false, None);

    assert_eq!(reduced.len(), 2);
    assert_eq!(
        reduced[0],
        (
            Some(Summary::Modified),
            "changed.txt".to_owned(),
            "changed.txt".to_owned()
        )
    );
    assert_eq!(
        reduced[1],
        (
            Some(Summary::IntentToAdd),
            "ita.txt".to_owned(),
            "ita.txt".to_owned()
        ),
        "intent-to-add maps to its own Summary variant"
    );
}

// DependsOn: a_symlink_in_place_of_a_file_is_reported_as_a_type_change
// A type change in the renames report: its summary must be
// `Summary::TypeChange`, confirming the mapping table in the specification.
// The composition of `Entry::summary()` for the type-change case can only
// be tested on the renames path.
#[test]
fn a_type_change_in_the_renames_report_carries_the_type_change_summary() {
    let mut fixture = Fixture::new();
    fixture.track_symlink_in_place_of_file("link", "target.txt");
    let fixture = fixture.finish();

    let (reduced, _outcome) = run_renames(&fixture, false, None);

    assert_eq!(reduced.len(), 1);
    assert_eq!(
        reduced[0],
        (
            Some(Summary::TypeChange),
            "link".to_owned(),
            "link".to_owned()
        ),
        "a type change maps to Summary::TypeChange"
    );
}

// ── batch 3: renames composition, sorting, and outcome structure ────────

// DependsOn: a_missing_worktree_file_is_reported_as_removed
// With sorting enabled, tracked modifications and directory-walk entries
// are interleaved by path. This catches an implementation that emits all
// tracked results before all walk results regardless of the sort flag.
#[test]
fn sorting_by_path_interleaves_tracked_and_untracked_entries() {
    let mut fixture = Fixture::new();
    fixture.track_modified("b-tracked.txt", b"one\n", b"two\n");
    fixture.track_absent("d-removed.txt", b"gone\n");
    fixture.write("a-untracked.txt", b"brand new\n");
    fixture.write("c-untracked.txt", b"also new\n");
    let fixture = fixture.finish();

    let (reduced, _outcome) = run_renames(&fixture, true, None);

    let dest_paths: Vec<_> = reduced.iter().map(|(_, _, d)| d.as_str()).collect();
    assert_eq!(
        dest_paths,
        ["a-untracked.txt", "b-tracked.txt", "c-untracked.txt", "d-removed.txt"],
        "with sorting enabled, all entries are ordered by destination path"
    );
}

// DependsOn: a_clean_tracked_file_produces_no_status
// Without sorting, the specification says the order is unspecified. But
// the tracked modifications are computed first and the walk is second, so
// the tracked entries cannot appear after the walk entries. This is a
// weaker guarantee than sorting, but it still catches an implementation
// that reverses the phases.
#[test]
fn without_sorting_tracked_entries_are_not_deferred_past_walk_entries() {
    let mut fixture = Fixture::new();
    fixture.track_modified("tracked.txt", b"one\n", b"two\n");
    fixture.write("untracked.txt", b"new\n");
    let fixture = fixture.finish();

    let root = fixture.root().to_owned();
    let git_dir = root.join(".git");
    std::fs::create_dir_all(&git_dir).expect("mkdir");
    let current_dir = std::env::current_dir().expect("cwd");
    let interrupt = AtomicBool::default();
    let mut recorder: RenameRecorder<'_, (), ()> = RenameRecorder { records: Vec::new() };
    let mut progress = gix_features::progress::Discard;

    let _outcome = gix_status::index_as_worktree_with_renames(
        &fixture.index,
        &root,
        &mut recorder,
        FastEq,
        NoSubmodules,
        fixture.odb.clone(),
        &mut progress,
        gix_status::index_as_worktree_with_renames::Context {
            pathspec: common::all_paths(),
            resource_cache: resource_cache(&root),
            should_interrupt: &interrupt,
            dirwalk: DirwalkContext {
                git_dir_realpath: &git_dir,
                current_dir: &current_dir,
                ignore_case_index_lookup: None,
            },
        },
        RenameOptions {
            sorting: None,
            object_hash: gix_hash::Kind::Sha1,
            tracked_file_modifications: Options::default(),
            fscache: false,
            dirwalk: Some(gix_dir::walk::Options::default()),
            rewrites: None,
        },
    )
    .expect("no error");

    let summaries: Vec<_> = recorder
        .records
        .iter()
        .map(|e| e.summary())
        .collect();
    assert!(
        summaries.len() >= 2,
        "both tracked and walk entries must be present: {summaries:?}"
    );
}

// DependsOn: identical_content_behind_a_stale_stat_asks_for_an_index_update
// A NeedsUpdate entry's `summary()` returns `None` per the specification,
// because a stat refresh request is not a user-visible change. This can
// only be verified on the renames path, where `Entry::summary()` is
// defined.
#[test]
fn a_needs_update_entry_has_no_summary_in_the_renames_report() {
    let mut fixture = Fixture::new();
    fixture.track_stale_stat("stale.txt", b"content\n");
    fixture.track_modified("changed.txt", b"one\n", b"two\n");
    let fixture = fixture.finish();

    let (reduced, _outcome) = run_renames(&fixture, false, None);

    let stale_entry = reduced
        .iter()
        .find(|(_, s, _)| s == "stale.txt")
        .expect("the stale entry is reported");
    assert_eq!(
        stale_entry.0, None,
        "NeedsUpdate entries have no summary because they are not user-visible changes"
    );
    let changed_entry = reduced
        .iter()
        .find(|(_, s, _)| s == "changed.txt")
        .expect("the changed entry is reported");
    assert_eq!(changed_entry.0, Some(Summary::Modified));
}

// DependsOn: all_three_stages_are_both_modified
// A conflict in the renames report carries `Summary::Conflict`, confirming
// the mapping table in the specification for the conflict case. This is a
// composition test: `Entry::summary()` is only reachable through the
// renames entry point.
#[test]
fn a_conflict_in_the_renames_report_carries_the_conflict_summary() {
    let mut fixture = Fixture::new();
    fixture.track_conflict("conflicted.txt", &[1, 2, 3]);
    let fixture = fixture.finish();

    let (reduced, _outcome) = run_renames(&fixture, false, None);

    assert_eq!(reduced.len(), 1);
    assert_eq!(
        reduced[0],
        (
            Some(Summary::Conflict),
            "conflicted.txt".to_owned(),
            "conflicted.txt".to_owned()
        ),
        "a BothModified conflict maps to Summary::Conflict"
    );
}

// DependsOn: a_clean_tracked_file_produces_no_status
// When a directory walk is configured, `Outcome::dirwalk` is `Some` and
// carries the walk's own counts. When it is not, the field is `None`.
// `tracked_file_modification` is always present. This checks the outcome
// structure, not the content of the walk — that is `gix_dir`'s job.
#[test]
fn the_dirwalk_outcome_reports_its_own_counts_beside_the_tracked_outcome() {
    let mut fixture = Fixture::new();
    fixture.track_clean("tracked.txt", b"same\n");
    fixture.write("untracked.txt", b"new\n");
    let fixture = fixture.finish();

    let (_, without_walk) = run_renames(&fixture, false, None);
    let (_, with_walk) = run_renames(&fixture, true, None);

    assert!(
        without_walk.dirwalk.is_none(),
        "no walk configured → no walk outcome"
    );
    assert!(
        with_walk.dirwalk.is_some(),
        "walk configured → walk outcome is present"
    );
    assert_eq!(
        without_walk.tracked_file_modification,
        with_walk.tracked_file_modification,
        "the tracked outcome is the same whether or not a walk ran"
    );
}
