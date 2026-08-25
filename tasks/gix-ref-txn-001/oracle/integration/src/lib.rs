//! Integration layer: several declared operations composed over a real repository.
//!
//! Scope. A test belongs here when it needs one of the four scripted git
//! repositories, or when the claim only becomes visible by chaining operations
//! -- a transaction followed by a packed-refs read, a deletion followed by a
//! reflog lookup, an update whose effect is read back through a different entry
//! point than the one that wrote it.
//!
//! Every test carries a `// DependsOn:` line naming the atomic test that pins
//! the single behaviour this one builds on. When the atomic test fails too, the
//! failure here is a consequence rather than an independent finding.
//!
//! As in the atomic layer: variants and named fields, never rendered strings
//! (three documented exceptions, `filter/import_audit.md` §6); and nothing
//! reaches into gix-lock or gix-tempfile territory.
//!
//! Upstream sources this layer draws from:
//!   gix-ref/tests/refs/file/log.rs                                    -- `mod iter`
//!   gix-ref/tests/refs/file/store/reflog.rs
//!   gix-ref/tests/refs/file/transaction/prepare_and_commit/create_or_update/mod.rs
//!   gix-ref/tests/refs/file/transaction/prepare_and_commit/create_or_update/collisions.rs
//!   gix-ref/tests/refs/file/transaction/prepare_and_commit/delete.rs

use std::error::Error as _;

use common::{TimeBuf, committer, create_at, create_symbolic_at, delete_at, hex_to_id, log_line};
use gix_lock::acquire::Fail;
use gix_ref::{
    Target,
    bstr::ByteSlice,
    file::{
        ReferenceExt,
        transaction::{PackedRefs, prepare},
    },
    store::WriteReflog,
    transaction::{Change, LogChange, PreviousValue, RefEdit, RefLog},
};

// ── local helpers ────────────────────────────────────────────────────────────

/// The commit `refs/heads/main` and `refs/heads/old` hold in the reflog fixture.
const REFLOG_MAIN: &str = "02a7a22d90d7c02fb494ed25551850b868e634f0";
/// The value `refs/heads/newer-as-loose` holds loose in the overlay fixture,
/// while its packed record still says [`common::MAIN_COMMIT`].
const OVERLAY_LOOSE: &str = "9902e3c3e8f0c569b4ab295ddf473e6de763e1e7";
/// The annotated tag packed in the overlay fixture; it peels to `MAIN_COMMIT`.
const OVERLAY_TAG: &str = "b3109a7e51fc593f85b145a76c70ddd1d133fafd";

fn update_edit(name: &str, expected: PreviousValue, new: Target) -> RefEdit {
    RefEdit {
        change: Change::Update {
            log: LogChange::default(),
            expected,
            new,
        },
        name: name.try_into().expect("valid name"),
        deref: false,
    }
}

fn delete_edit(name: &str, expected: PreviousValue, log: RefLog, deref: bool) -> RefEdit {
    RefEdit {
        change: Change::Delete { expected, log },
        name: name.try_into().expect("valid name"),
        deref,
    }
}

fn commit_all(store: &gix_ref::file::Store, edits: impl IntoIterator<Item = RefEdit>) -> Vec<RefEdit> {
    store
        .transaction()
        .prepare(edits, Fail::Immediately, Fail::Immediately)
        .expect("preparation succeeds")
        .commit(committer().to_ref(&mut TimeBuf::default()))
        .expect("commit succeeds")
}

/// Create a reference under `name` holding `id`, with a log entry.
fn create_with_log(name: &str, id: &str, force_create_reflog: bool) -> RefEdit {
    RefEdit {
        change: Change::Update {
            log: LogChange {
                mode: RefLog::AndReference,
                force_create_reflog,
                message: "an entry".into(),
            },
            expected: PreviousValue::Any,
            new: Target::Object(hex_to_id(id)),
        },
        name: name.try_into().expect("valid name"),
        deref: false,
    }
}

/// An empty store holding two packed object references and one loose symbolic
/// one, produced by a single packing transaction.
///
/// This is the state four of the collision tests below start from; building it
/// through the public transaction API rather than by writing files means the
/// tests observe a store the implementation itself produced.
fn packed_and_symbolic_store() -> (common::TempDir, gix_ref::file::Store) {
    let (dir, store) = common::empty_store();
    store
        .transaction()
        .packed_refs(PackedRefs::DeletionsAndNonSymbolicUpdatesRemoveLooseSourceReference(
            Box::new(common::EmptyCommit),
        ))
        .prepare(
            [
                create_at("refs/a"),
                create_at("refs/b"),
                create_symbolic_at("refs/symbolic", "refs/heads/target"),
            ],
            Fail::Immediately,
            Fail::Immediately,
        )
        .expect("all three names are free")
        .commit(committer().to_ref(&mut TimeBuf::default()))
        .expect("commit succeeds");
    (dir, store)
}

// ── I1. Reading reference logs off a repository ──────────────────────────────

// DependsOn: reverse_log_iteration_rejects_a_zero_sized_buffer
#[test]
fn reflog_iteration_returns_none_for_a_missing_name_and_for_a_directory() {
    let store = common::reflog_store();

    let mut forward_buf = Vec::new();
    let mut reverse_buf = [0u8; 256];
    for name in ["FAILURE_NONEXISTING", "refs/heads"] {
        assert!(
            matches!(store.reflog_iter(name, &mut forward_buf), Ok(None)),
            "{name} has no log, which is not an error"
        );
        assert!(
            matches!(store.reflog_iter_rev(name, &mut reverse_buf), Ok(None)),
            "{name} has no log when read backwards either -- notably `refs/heads` is a \
             directory in the log tree, and a directory is not a log"
        );
    }
}

// DependsOn: log_line_round_trips_through_write_to
#[test]
fn reflog_iteration_yields_every_entry_of_head_and_of_main() {
    let store = common::reflog_store();
    let mut buf = Vec::new();

    for name in ["HEAD", "refs/heads/main"] {
        let log = store
            .reflog_iter(name, &mut buf)
            .expect("the log is readable")
            .unwrap_or_else(|| panic!("{name} has a log"));
        assert_eq!(
            log.filter_map(Result::ok).count(),
            5,
            "{name} records the five commits the fixture makes"
        );
    }
}

// DependsOn: reverse_log_iteration_yields_two_lines_newest_first
#[test]
fn reverse_reflog_iteration_yields_every_entry_of_head_and_of_main() {
    let store = common::reflog_store();
    let mut buf = [0u8; 256];

    for name in ["HEAD", "refs/heads/main"] {
        let log = store
            .reflog_iter_rev(name, &mut buf)
            .expect("the log is readable")
            .unwrap_or_else(|| panic!("{name} has a log"));
        assert_eq!(
            log.filter_map(Result::ok).count(),
            5,
            "reading backwards finds the same five entries as reading forwards, \
             through a fixed 256-byte window rather than the whole file"
        );
    }
}

// DependsOn: log_line_round_trips_through_write_to
#[test]
fn forward_log_iteration_reads_the_oldest_entry_first() {
    let log = common::reflog_bytes("HEAD");
    assert_eq!(
        gix_ref::file::log::iter::forward(&log).count(),
        5,
        "the fixture's HEAD log has a known number of entries"
    );

    let mut iter = gix_ref::file::log::iter::forward(&log);
    let first = iter.next().expect("five entries").expect("it parses");
    assert_eq!(
        first.previous_oid(),
        common::null_id(),
        "the first entry a reference ever gets comes from nothing"
    );
    assert_eq!(first.new_oid(), hex_to_id(common::MAIN_COMMIT));
    assert_eq!(first.message, "commit (initial): c1".as_bytes().as_bstr());
    assert!(iter.all(|line| line.is_ok()), "every remaining line parses too");
}

// DependsOn: log_line_parse_keeps_angle_brackets_in_the_message
#[test]
fn forward_log_iteration_continues_after_a_broken_line() {
    // A real log with one unparsable line spliced in front of it.
    let mut log: Vec<u8> = b"0000000000000000000000000000000000000000 134385fbroken7062102c6a483440bfda2a03 \
committer <committer@example.com> 946771200 +0000\tcommit\n"
        .to_vec();
    log.extend_from_slice(&common::reflog_bytes("HEAD"));

    let mut iter = gix_ref::file::log::iter::forward(&log);
    let err = iter
        .next()
        .expect("the broken line is still yielded")
        .expect_err("but it does not parse");

    // Exception E3 (`filter/import_audit.md` §6): `decode::Error` has no public
    // variants. The prefix is asserted because the line number, and the fact
    // that forward iteration counts from the start rather than from the end, is
    // a specified behaviour; the quoted line body that follows is not.
    assert!(
        err.to_string().starts_with("In line 1: "),
        "the failure locates the offending line by its position from the start, got {err}"
    );

    assert_eq!(
        iter.filter(Result::is_ok).count(),
        5,
        "one bad line does not abort iteration -- the five good entries behind it are all delivered"
    );
}

// DependsOn: reverse_log_iteration_rejects_a_zero_sized_buffer
#[test]
fn reverse_log_iteration_reports_a_line_that_does_not_fit_and_then_stops() {
    let mut buf = [0u8; 128];
    let bare: Vec<u8> = b"0000000000000000000000000000000000000000 134385f6d781b7e97062102c6a483440bfda2a03 \
committer <committer@example.com> 946771200 +0000\tcommit (initial): c1"
        .to_vec();
    let terminated = {
        let mut l = bare.clone();
        l.push(b'\n');
        l
    };

    for log in [bare, terminated] {
        let mut iter = gix_ref::file::log::iter::reverse(std::io::Cursor::new(&log), &mut buf)
            .expect("a 128-byte buffer is not zero-sized, so it is accepted up front");
        let err = iter
            .next()
            .expect("the oversized line is reported rather than skipped")
            .expect_err("128 bytes cannot hold this line");

        // Exception E2 (`filter/import_audit.md` §6): the wrapped type has no
        // public variants either. Only the prefix is pinned; the tail is a
        // debug rendering of however much of the line happened to fit.
        assert!(
            err.source()
                .expect("the buffer failure is the cause")
                .to_string()
                .starts_with("buffer too small for line size, got until "),
            "the failure has to say the buffer was the problem, got {err}"
        );
        assert!(
            iter.next().is_none(),
            "and iteration stops there rather than looping on the same line"
        );
    }
}

// DependsOn: reverse_log_iteration_yields_two_lines_newest_first
#[test]
fn reverse_log_iteration_reads_a_realistic_log_completely_at_every_buffer_size() {
    let log = common::reflog_bytes("refs/heads/old");
    let mut buf = Vec::with_capacity(16 * 1024);

    for size in [2048usize, 3000, 4096, 8192, 16384] {
        buf.resize(size, 0);
        let count = gix_ref::file::log::iter::reverse(std::io::Cursor::new(&*log), &mut buf)
            .expect("the buffer is not zero-sized")
            .filter_map(Result::ok)
            .count();
        assert_eq!(
            count, 581,
            "with a {size}-byte window every one of the log's entries must still be \
             delivered -- the window slides backwards over the file, it does not have to hold it"
        );
    }
}

// DependsOn: log_line_round_trips_through_write_to
#[test]
fn entries_read_from_a_repository_render_back_to_the_bytes_they_were_read_from() {
    let log = common::reflog_bytes("HEAD");

    for line in gix_ref::file::log::iter::forward(&log) {
        let line = line.expect("every recorded line parses");
        let owned = line.to_owned();
        let mut rendered = Vec::new();
        owned.write_to(&mut rendered).expect("a recorded line is writable");

        let reparsed = gix_ref::file::log::LineRef::from_bytes(&rendered)
            .expect("what was rendered parses")
            .to_owned();
        assert_eq!(
            reparsed, owned,
            "the codec round trips over entries git itself wrote, not just over synthetic ones"
        );
    }
}

// ── I2. Compare-and-swap over a repository that already has references ───────

// DependsOn: must_exist_on_a_missing_reference_fails_preparation
#[test]
fn an_update_whose_expected_value_does_not_match_is_refused() {
    let (_keep, store) = common::store_writable("make_repo_for_reflog.sh");
    let target = store.find_loose("HEAD").expect("HEAD exists").target;

    let err = store
        .transaction()
        .prepare(
            Some(update_edit(
                "HEAD",
                PreviousValue::MustExistAndMatch(Target::Object(hex_to_id(
                    "28ce6a8b26aa170e1de65536fe8abe1832bd3242",
                ))),
                Target::Object(common::null_id()),
            )),
            Fail::Immediately,
            Fail::Immediately,
        )
        .err()
        .expect("HEAD does not hold that id");

    match err {
        prepare::Error::ReferenceOutOfDate { full_name, actual, .. } => {
            assert_eq!(full_name, "HEAD");
            assert_eq!(
                actual, target,
                "the value that was actually found is handed back, so a caller can retry"
            );
        }
        other => panic!("expected an out-of-date failure, got {other:?}"),
    }
}

// DependsOn: non_existing_can_be_deleted_with_the_existing_must_match_constraint
#[test]
fn the_existing_must_match_constraint_creates_a_reference_that_is_not_there_yet() {
    let (_keep, store) = common::store_writable("make_repo_for_reflog.sh");
    let expected = PreviousValue::ExistingMustMatch(Target::Object(gix_hash::ObjectId::empty_tree(common::HASH_KIND)));
    let new = Target::Object(common::null_id());

    let edits = commit_all(
        &store,
        [update_edit("refs/heads/new", expected.clone(), new.clone())],
    );

    assert_eq!(
        edits,
        vec![update_edit("refs/heads/new", expected, new)],
        "nothing was there to compare against, so the caller's expectation is returned unchanged"
    );
    assert!(
        store.try_find_loose("refs/heads/new").expect("readable").is_some(),
        "and the reference was created"
    );
}

// DependsOn: must_exist_on_a_missing_reference_fails_preparation
#[test]
fn the_existing_must_match_constraint_still_refuses_a_mismatch() {
    let (_keep, store) = common::store_writable("make_repo_for_reflog.sh");
    let target = store.find_loose("HEAD").expect("HEAD exists").target;

    let err = store
        .transaction()
        .prepare(
            Some(update_edit(
                "HEAD",
                PreviousValue::ExistingMustMatch(Target::Object(hex_to_id(
                    "28ce6a8b26aa170e1de65536fe8abe1832bd3242",
                ))),
                Target::Object(common::null_id()),
            )),
            Fail::Immediately,
            Fail::Immediately,
        )
        .err()
        .expect("tolerating absence is not tolerating a different value");

    match err {
        prepare::Error::ReferenceOutOfDate { full_name, actual, .. } => {
            assert_eq!(full_name, "HEAD");
            assert_eq!(actual, target);
        }
        other => panic!("expected an out-of-date failure, got {other:?}"),
    }
}

// DependsOn: must_exist_on_a_missing_reference_fails_preparation
#[test]
fn must_not_exist_is_refused_when_the_reference_is_already_there() {
    let (_keep, store) = common::store_writable("make_repo_for_reflog.sh");
    let target = store.find_loose("HEAD").expect("HEAD exists").target;

    let err = store
        .transaction()
        .prepare(Some(create_at("HEAD")), Fail::Immediately, Fail::Immediately)
        .err()
        .expect("HEAD exists and the new value differs from it");

    match err {
        prepare::Error::MustNotExist { full_name, actual, .. } => {
            assert_eq!(full_name, "HEAD");
            assert_eq!(actual, target, "the value that made the constraint fail is reported");
        }
        other => panic!("expected a must-not-exist failure, got {other:?}"),
    }
}

// DependsOn: committing_without_a_signature_fails_when_a_reflog_must_be_written
#[test]
fn must_exist_accepts_whatever_value_is_there_and_appends_a_log_entry() {
    let (_keep, store) = common::store_writable("make_repo_for_reflog.sh");
    let target = store.find_loose("HEAD").expect("HEAD exists").target;
    let before = common::reflog_lines(&store, "HEAD").len();
    let new = Target::Object(gix_hash::ObjectId::empty_tree(common::HASH_KIND));

    let edits = commit_all(&store, [update_edit("HEAD", PreviousValue::MustExist, new.clone())]);

    assert_eq!(
        edits,
        vec![update_edit("HEAD", PreviousValue::MustExistAndMatch(target), new)],
        "the bare must-exist expectation is replaced by the value that was found"
    );
    assert_eq!(
        common::reflog_lines(&store, "HEAD").len(),
        before + 1,
        "a real change appends exactly one entry"
    );
}

// DependsOn: symbolic_head_created_then_referent_updated_with_normal_reflog
#[test]
fn must_not_exist_tolerates_a_reference_that_already_holds_the_new_value() {
    let (_keep, store) = common::store_writable("make_repo_for_reflog.sh");
    let target = store.find_loose("HEAD").expect("HEAD exists").target;
    let before = common::reflog_lines(&store, "HEAD").len();

    let edits = commit_all(
        &store,
        [update_edit("HEAD", PreviousValue::MustNotExist, target.clone())],
    );

    assert_eq!(
        edits,
        vec![update_edit(
            "HEAD",
            PreviousValue::MustExistAndMatch(target.clone()),
            target
        )],
        "writing the value that is already there is not a violation of must-not-exist"
    );
    assert_eq!(
        common::reflog_lines(&store, "HEAD").len(),
        before,
        "and because nothing changed, no entry is appended"
    );
}

// DependsOn: symbolic_head_created_then_referent_updated_with_normal_reflog
#[test]
fn updating_the_referent_directly_leaves_heads_own_log_alone() {
    let (_keep, store) = common::store_writable("make_repo_for_reflog.sh");
    let head = store.find_loose("HEAD").expect("HEAD exists");
    assert_eq!(
        head.target.to_ref().try_name().map(gix_ref::FullNameRef::as_bstr),
        Some("refs/heads/main".as_bytes().as_bstr()),
        "the fixture's HEAD is symbolic and points at main"
    );
    let head_log_before = common::reflog_lines(&store, "HEAD");

    let new_id = hex_to_id("01dd4e2a978a9f5bd773dae6da7aa4a5ac1cdbbc");
    let log = LogChange {
        mode: RefLog::AndReference,
        force_create_reflog: false,
        message: "".into(),
    };
    let edits = commit_all(
        &store,
        [RefEdit {
            change: Change::Update {
                log: log.clone(),
                expected: PreviousValue::MustExist,
                new: Target::Object(new_id),
            },
            name: "refs/heads/main".try_into().expect("valid name"),
            deref: false,
        }],
    );

    assert_eq!(
        edits,
        vec![RefEdit {
            change: Change::Update {
                log,
                expected: PreviousValue::MustExistAndMatch(Target::Object(hex_to_id(REFLOG_MAIN))),
                new: Target::Object(new_id),
            },
            name: "refs/heads/main".try_into().expect("valid name"),
            deref: false,
        }],
        "only the one reference named by the caller is edited; HEAD is not dragged along"
    );
    assert_eq!(
        common::reflog_lines(&store, "HEAD"),
        head_log_before,
        "writing the reference HEAD points at does not append to HEAD's own log, even though \
         that would arguably keep the two consistent"
    );
    assert_eq!(
        common::reflog_lines(&store, "refs/heads/main")
            .last()
            .expect("at least one entry"),
        &log_line(hex_to_id(REFLOG_MAIN), new_id, ""),
        "the referent's newest entry records the transition that just happened"
    );
}

// ── I3. Deletion over a repository with logs ─────────────────────────────────

// DependsOn: delete_a_broken_reference_may_be_deleted_even_in_deref_mode
#[test]
fn deleting_a_symbolic_reference_without_deref_takes_its_log_and_leaves_the_referent() {
    let (_keep, store) = common::store_writable("make_repo_for_reflog.sh");
    let head = store.find_loose("HEAD").expect("HEAD exists");
    assert!(head.log_exists(&store), "the fixture gives HEAD a log");

    let edits = commit_all(
        &store,
        [delete_edit("HEAD", PreviousValue::MustExist, RefLog::AndReference, false)],
    );

    assert_eq!(
        edits,
        vec![delete_edit(
            "HEAD",
            PreviousValue::MustExistAndMatch(Target::Symbolic("refs/heads/main".try_into().expect("valid name"))),
            RefLog::AndReference,
            false,
        )],
        "the bare must-exist expectation is replaced by the symbolic value that was found"
    );
    assert!(
        store
            .reflog_iter_rev("HEAD", &mut [0u8; 128])
            .expect("readable")
            .is_none(),
        "HEAD's log went with it"
    );
    assert!(store.try_find_loose("HEAD").expect("readable").is_none(), "so did HEAD");
    assert!(
        store.try_find_loose("main").expect("readable").is_some(),
        "but without deref the referent is untouched"
    );
}

// DependsOn: delete_a_reference_which_is_gone_but_must_exist_fails
#[test]
fn a_deletion_with_a_mismatching_expectation_is_attributed_to_the_referent() {
    let (_keep, store) = common::store_writable("make_repo_for_reflog.sh");

    // HEAD is symbolic and deref is on, so the constraint is checked against
    // refs/heads/main -- which holds an object, not the symbolic value asked for.
    let err = store
        .transaction()
        .prepare(
            Some(delete_edit(
                "HEAD",
                PreviousValue::MustExistAndMatch(Target::Symbolic("refs/heads/main".try_into().expect("valid name"))),
                RefLog::Only,
                true,
            )),
            Fail::Immediately,
            Fail::Immediately,
        )
        .err()
        .expect("the referent does not hold a symbolic value");

    match err {
        prepare::Error::ReferenceOutOfDate { full_name, actual, .. } => {
            assert_eq!(
                full_name, "refs/heads/main",
                "after dereferencing, the constraint belongs to the referent and the failure names it"
            );
            assert_eq!(actual, Target::Object(hex_to_id(REFLOG_MAIN)));
        }
        other => panic!("expected an out-of-date failure, got {other:?}"),
    }

    assert!(
        store.find_loose("HEAD").expect("still there").log_exists(&store),
        "a failed preparation changes nothing"
    );
    assert!(store.find_loose("main").expect("still there").log_exists(&store));
}

// DependsOn: delete_a_reference_which_is_gone_succeeds
#[test]
fn deleting_only_the_log_of_a_symbolic_reference_keeps_the_referents_log() {
    let (_keep, store) = common::store_writable("make_repo_for_reflog.sh");
    assert!(store.find_loose("HEAD").expect("HEAD exists").log_exists(&store));

    let edits = commit_all(
        &store,
        [delete_edit(
            "HEAD",
            PreviousValue::MustExistAndMatch(Target::Symbolic("refs/heads/main".try_into().expect("valid name"))),
            RefLog::Only,
            false,
        )],
    );

    assert_eq!(edits.len(), 1, "without deref there is nothing to split");
    let head = store.find_loose("HEAD").expect("the reference itself survives");
    assert!(!head.log_exists(&store), "but its log is gone");

    let main = store.find_loose("main").expect("the referent survives");
    assert!(main.log_exists(&store), "and so does the referent's log");
    assert_eq!(
        head.target.to_ref().try_name().map(gix_ref::FullNameRef::as_bstr),
        Some(main.name.as_bstr()),
        "HEAD still points at main"
    );
}

// DependsOn: delete_a_reference_which_is_gone_succeeds
#[test]
fn deleting_the_log_of_a_symbolic_reference_with_deref_takes_both_logs() {
    let (_keep, store) = common::store_writable("make_repo_for_reflog.sh");
    assert!(store.find_loose("HEAD").expect("HEAD exists").log_exists(&store));

    let edits = commit_all(
        &store,
        [delete_edit("HEAD", PreviousValue::MustExist, RefLog::Only, true)],
    );

    assert_eq!(edits.len(), 2, "the edit was split into HEAD and its referent");
    let head = store.find_loose("HEAD").expect("the reference itself survives");
    assert!(!head.log_exists(&store));

    let main = store.find_loose("main").expect("the referent survives");
    assert!(!main.log_exists(&store), "this time the referent's log goes too");
    assert_eq!(
        head.target.to_ref().try_name().map(gix_ref::FullNameRef::as_bstr),
        Some(main.name.as_bstr()),
        "and neither reference moved"
    );
}

// DependsOn: implicit_rollback_removes_intermediate_directories
#[test]
fn renaming_a_reference_below_itself_is_reported_as_a_path_collision() {
    let (_keep, store) = common::store_writable("make_repo_for_reflog.sh");
    let old = store.find_loose("old").expect("the fixture has refs/heads/old");

    let err = store
        .transaction()
        .prepare(
            [
                delete_edit(
                    "refs/heads/old",
                    PreviousValue::MustExist,
                    RefLog::AndReference,
                    true,
                ),
                RefEdit {
                    change: Change::Update {
                        log: LogChange::default(),
                        expected: PreviousValue::MustNotExist,
                        new: old.target.clone(),
                    },
                    name: "refs/heads/old/new".try_into().expect("valid name"),
                    deref: true,
                },
            ],
            Fail::Immediately,
            Fail::Immediately,
        )
        .err()
        .expect("refs/heads/old cannot be a file and a directory at once");

    match err {
        prepare::Error::Io(err) => assert_eq!(
            err.kind(),
            std::io::ErrorKind::NotADirectory,
            "the clash between a reference and a path prefix is reported as such, and early -- \
             not as a lock-acquisition failure"
        ),
        other => panic!("expected a plain I/O failure, got {other:?}"),
    }

    // The same rename does work when it is split across two transactions, which
    // is what makes the failure above a statement about one transaction rather
    // than about the rename.
    let edits = commit_all(
        &store,
        [delete_edit(
            "refs/heads/old",
            PreviousValue::MustExist,
            RefLog::AndReference,
            true,
        )],
    );
    assert_eq!(edits.len(), 1, "first delete, to make room");

    let edits = commit_all(
        &store,
        [RefEdit {
            change: Change::Update {
                log: LogChange::default(),
                expected: PreviousValue::MustNotExist,
                new: old.target,
            },
            name: "refs/heads/old/new".try_into().expect("valid name"),
            deref: true,
        }],
    );
    assert_eq!(edits.len(), 1, "then create, where the old one used to be");
    assert!(
        store.try_find_loose("refs/heads/old/new").expect("readable").is_some(),
        "the new reference is there"
    );
}

// DependsOn: symbolic_head_created_then_referent_updated_with_normal_reflog
#[test]
fn a_log_only_deletion_removes_the_log_when_writing_logs_is_enabled() {
    log_only_deletion_ignores_the_write_mode(WriteReflog::Normal);
}

// DependsOn: symbolic_head_created_then_referent_updated_with_reflog_disabled
#[test]
fn a_log_only_deletion_removes_the_log_when_writing_logs_is_disabled() {
    log_only_deletion_ignores_the_write_mode(WriteReflog::Disable);
}

/// The store-wide reflog mode governs *writing* entries. Deleting a log is an
/// explicit instruction and is carried out either way; upstream runs this as a
/// two-arm loop, and the arms take different paths through the writer.
fn log_only_deletion_ignores_the_write_mode(mode: WriteReflog) {
    let (_keep, store) = common::store_writable_with("make_repo_for_reflog.sh", mode);
    assert!(store.find_loose("HEAD").expect("HEAD exists").log_exists(&store));
    assert!(
        store.open_packed_buffer().expect("readable").is_none(),
        "the fixture has no packed file"
    );

    let edits = commit_all(
        &store,
        [delete_edit("HEAD", PreviousValue::Any, RefLog::Only, false)],
    );

    assert_eq!(edits.len(), 1);
    assert!(
        !store.find_loose("HEAD").expect("still there").log_exists(&store),
        "the log was deleted under {mode:?} all the same"
    );
    assert!(
        store.open_packed_buffer().expect("readable").is_none(),
        "and no packed file was invented along the way"
    );
}

// ── I4. Packed references ────────────────────────────────────────────────────

// DependsOn: non_conflicting_concurrent_transactions_both_commit
#[test]
fn a_packed_record_supplies_the_previous_value_while_the_update_goes_loose() {
    let (_keep, store) = common::store_writable("make_packed_ref_repository.sh");
    assert!(
        store.try_find_loose("main").expect("readable").is_none(),
        "main exists only as a packed record in this fixture"
    );

    let new_id = hex_to_id("0000000000000000000000000000000000000001");
    let old_id = hex_to_id(common::MAIN_COMMIT);
    let edits = commit_all(
        &store,
        [RefEdit {
            change: Change::Update {
                log: LogChange {
                    mode: RefLog::AndReference,
                    force_create_reflog: false,
                    message: "for pack".into(),
                },
                expected: PreviousValue::MustExistAndMatch(Target::Object(old_id)),
                new: Target::Object(new_id),
            },
            name: "refs/heads/main".try_into().expect("valid name"),
            deref: false,
        }],
    );
    assert_eq!(edits.len(), 1, "one edit, in the loose store");

    let packed = store
        .open_packed_buffer()
        .expect("readable")
        .expect("the packed file is still there");
    assert_eq!(
        packed.find("main").expect("still packed").target(),
        old_id,
        "an ordinary transaction does not rewrite the packed file; the loose reference \
         it writes shadows the packed record of the same name"
    );
    assert_eq!(
        store
            .find_loose("main")
            .expect("now there is a loose one")
            .target
            .try_id()
            .map(ToOwned::to_owned),
        Some(new_id),
    );
    assert_eq!(
        common::loose_ref_content(store.git_dir(), "refs/heads/main").expect("the file exists"),
        format!("{}\n", new_id.to_hex()),
        "and on disk it is the full object id followed by a newline"
    );
}

// DependsOn: delete_a_reference_which_is_gone_succeeds
#[test]
fn deleting_a_packed_only_reference_removes_its_record() {
    let (_keep, store) = common::store_writable("make_packed_ref_repository.sh");
    assert!(
        store.try_find_loose("main").expect("readable").is_none(),
        "main is packed only"
    );

    let edits = commit_all(
        &store,
        [delete_edit(
            "refs/heads/main",
            PreviousValue::MustExistAndMatch(Target::Object(hex_to_id(common::MAIN_COMMIT))),
            RefLog::AndReference,
            false,
        )],
    );

    assert_eq!(edits.len(), 1, "the packed file supplied the value to compare against");
    let packed = store
        .open_packed_buffer()
        .expect("readable")
        .expect("other records remain");
    assert!(
        packed.try_find("main").expect("readable").is_none(),
        "the record is gone from the packed file"
    );
}

// DependsOn: delete_a_reference_which_is_gone_succeeds
#[test]
fn deleting_a_loose_reference_that_shadows_an_outdated_record_clears_both() {
    let (_keep, store) = common::store_writable("make_packed_ref_repository_for_overlay.sh");
    let packed = store
        .open_packed_buffer()
        .expect("readable")
        .expect("the fixture has a packed file");
    let loose_id = hex_to_id(OVERLAY_LOOSE);
    assert_eq!(
        packed.find("newer-as-loose").expect("packed too").target(),
        hex_to_id(common::MAIN_COMMIT),
        "the packed record still holds the older value"
    );
    assert_ne!(packed.find("newer-as-loose").expect("packed").target(), loose_id);
    drop(packed);

    let edits = commit_all(
        &store,
        [delete_edit(
            "refs/heads/newer-as-loose",
            PreviousValue::MustExistAndMatch(Target::Object(loose_id)),
            RefLog::AndReference,
            false,
        )],
    );

    assert_eq!(
        edits.len(),
        1,
        "one edit, even though two places on disk had to change"
    );
    assert!(
        store.try_find("newer-as-loose").expect("readable").is_none(),
        "the reference is gone from the loose store and from the packed file alike -- \
         deleting only the loose one would have resurrected the older packed value"
    );
}

// DependsOn: delete_a_reference_which_is_gone_succeeds
#[test]
fn deleting_every_record_removes_the_packed_file_under_a_must_exist_constraint() {
    deleting_every_packed_record(true);
}

// DependsOn: non_existing_can_be_deleted_with_the_existing_must_match_constraint
#[test]
fn deleting_every_record_removes_the_packed_file_under_a_may_exist_constraint() {
    deleting_every_packed_record(false);
}

/// The two constraints take different paths through the compare-and-swap check,
/// which is why upstream's two-arm loop becomes two tests.
fn deleting_every_packed_record(must_exist: bool) {
    let (_keep, store) = common::store_writable("make_packed_ref_repository.sh");

    let edits: Vec<RefEdit> = {
        let packed = store
            .open_packed_buffer()
            .expect("readable")
            .expect("the fixture has a packed file");
        packed
            .iter()
            .expect("the packed file parses")
            .map(|r| {
                let r = r.expect("every record parses");
                let target = Target::Object(r.target());
                RefEdit {
                    change: Change::Delete {
                        expected: if must_exist {
                            PreviousValue::MustExistAndMatch(target)
                        } else {
                            PreviousValue::ExistingMustMatch(target)
                        },
                        log: RefLog::AndReference,
                    },
                    name: r.name.into(),
                    deref: false,
                }
            })
            .collect()
    };
    assert_eq!(edits.len(), 11, "the fixture packs a known number of references");

    let edits = commit_all(&store, edits);

    assert!(
        !store.packed_refs_path().is_file(),
        "with no record left, the packed file itself is removed rather than left as a header"
    );
    assert!(
        store.open_packed_buffer().expect("readable").is_none(),
        "and re-opening does not invent one"
    );
    for edit in edits {
        assert!(
            store.try_find(&edit.name).expect("readable").is_none(),
            "{} is gone",
            edit.name.as_bstr()
        );
    }
}

// DependsOn: an_ongoing_packed_transaction_forces_a_packed_refs_lock_elsewhere
#[test]
fn packing_in_prune_mode_removes_the_loose_sources_and_writes_the_documented_file() {
    let (_keep, store) = common::store_writable("make_ref_repository.sh");
    assert!(
        store.open_packed_buffer().expect("readable").is_none(),
        "the fixture starts out entirely loose"
    );

    // The eleven object-valued references the fixture creates, in the order the
    // packed file has to end up in. `refs/broken` holds a non-hex value and
    // never decodes; the six symbolic references cannot be packed at all.
    let packable: [(&str, &str); 11] = [
        ("refs/d1", common::MAIN_COMMIT),
        ("refs/heads/A", common::MAIN_COMMIT),
        ("refs/heads/d1", common::MAIN_COMMIT),
        ("refs/heads/dt1", common::MAIN_COMMIT),
        ("refs/heads/main", common::MAIN_COMMIT),
        ("refs/prefix/feature-suffix", common::MAIN_COMMIT),
        ("refs/prefix/feature/sub/dir/algo", common::MAIN_COMMIT),
        ("refs/remotes/origin/main", common::MAIN_COMMIT),
        ("refs/remotes/origin/multi-link-target3", common::MAIN_COMMIT),
        ("refs/tags/dt1", common::ANNOTATED_TAG),
        ("refs/tags/t1", common::MAIN_COMMIT),
    ];

    // Only `refs/tags/dt1` names a tag object, so it is the only record that can
    // carry a peeled line.
    let objects = common::Mem::with_tag_chain(common::ANNOTATED_TAG, common::MAIN_COMMIT);

    let edits = store
        .transaction()
        .packed_refs(PackedRefs::DeletionsAndNonSymbolicUpdatesRemoveLooseSourceReference(
            Box::new(objects),
        ))
        .prepare(
            packable
                .iter()
                .map(|(name, id)| common::repack_edit(name, Target::Object(hex_to_id(id)))),
            Fail::Immediately,
            Fail::Immediately,
        )
        .expect("every name exists with the value given")
        .commit(committer().to_ref(&mut TimeBuf::default()))
        .expect("commit succeeds");
    assert_eq!(edits.len(), 11);

    assert_eq!(
        common::loose_ref_names(store.git_dir()),
        vec![
            "refs/broken",
            "refs/heads/multi-link-target1",
            "refs/loop-a",
            "refs/loop-b",
            "refs/multi-link",
            "refs/remotes/origin/HEAD",
            "refs/tags/multi-link-target2",
        ],
        "in prune mode the loose file each packed record came from is removed; what is left \
         is the six symbolic references, which cannot be packed, and the one file that does \
         not decode as a reference and was therefore never offered for packing"
    );

    // Derived from the specified format rather than diffed against git's own
    // file: a fixed header ending in a space, records sorted by name in byte
    // order, and a `^`-prefixed peeled line directly after the tag it belongs to.
    let mut expected = String::from("# pack-refs with: peeled fully-peeled sorted \n");
    for (name, id) in packable {
        expected.push_str(&format!("{id} {name}\n"));
        if id == common::ANNOTATED_TAG {
            expected.push_str(&format!("^{}\n", common::MAIN_COMMIT));
        }
    }
    assert_eq!(
        std::fs::read_to_string(store.packed_refs_path()).expect("the packed file was written"),
        expected,
    );
}

// DependsOn: an_ongoing_packed_transaction_forces_a_packed_refs_lock_elsewhere
#[test]
fn packing_in_leave_mode_keeps_the_loose_references_and_refreshes_the_record() {
    let (_keep, store) = common::store_writable("make_packed_ref_repository_for_overlay.sh");
    let loose_id = hex_to_id(OVERLAY_LOOSE);

    let branch = store.find("newer-as-loose").expect("it is there, loose");
    let entries_before = branch
        .log_iter(&store)
        .all()
        .expect("readable")
        .expect("the fixture gives it a log")
        .count();
    let records_before = store
        .open_packed_buffer()
        .expect("readable")
        .expect("the fixture has a packed file")
        .iter()
        .expect("it parses")
        .filter_map(Result::ok)
        .count();
    assert_eq!(records_before, 7, "the fixture packs a known number of references");

    let edits = store
        .transaction()
        .packed_refs(PackedRefs::DeletionsAndNonSymbolicUpdates(Box::new(common::EmptyCommit)))
        .prepare(
            [
                common::repack_edit("refs/heads/newer-as-loose", Target::Object(loose_id)),
                common::repack_edit(
                    "refs/remotes/origin/HEAD",
                    Target::Symbolic("refs/remotes/origin/main".try_into().expect("valid name")),
                ),
            ],
            Fail::Immediately,
            Fail::Immediately,
        )
        .expect("both loose references hold the values given")
        .commit(committer().to_ref(&mut TimeBuf::default()))
        .expect("commit succeeds");
    assert_eq!(
        edits.len(),
        2,
        "both edits are reported, even though only one of them can reach the pack"
    );

    assert_eq!(
        common::loose_ref_names(store.git_dir()),
        vec!["refs/heads/newer-as-loose", "refs/remotes/origin/HEAD"],
        "this mode leaves the loose sources in place, and a symbolic one among them is not a problem"
    );
    assert_eq!(
        branch
            .log_iter(&store)
            .all()
            .expect("readable")
            .expect("log")
            .count(),
        entries_before,
        "no value changed, so nothing is appended to the log"
    );

    let packed = store
        .open_packed_buffer()
        .expect("readable")
        .expect("the packed file is still there");
    assert_eq!(
        packed.iter().expect("it parses").filter_map(Result::ok).count(),
        records_before,
        "the packed record was replaced, not added to"
    );
    assert_eq!(
        packed.find("newer-as-loose").expect("packed").target(),
        loose_id,
        "and it now agrees with the loose reference that was shadowing it"
    );
    assert_eq!(
        packed.find("tag-object").expect("packed").target(),
        hex_to_id(OVERLAY_TAG),
        "records the transaction did not touch are carried over verbatim, peeled line and all"
    );
}

// DependsOn: an_ongoing_packed_transaction_forces_a_packed_refs_lock_elsewhere
#[test]
fn a_deletion_in_a_packing_transaction_removes_the_record() {
    let (_keep, store) = common::store_writable("make_packed_ref_repository.sh");
    assert!(
        store.try_find_loose("refs/heads/d1").expect("readable").is_none(),
        "d1 is packed only"
    );

    // `Mem::empty()` answers no lookup at all. A deletion never peels, so a
    // database that knows nothing is enough -- and if the implementation did
    // consult it, this test would fail rather than quietly pass.
    let edits = store
        .transaction()
        .packed_refs(PackedRefs::DeletionsAndNonSymbolicUpdates(Box::new(common::Mem::empty())))
        .prepare(
            [delete_edit(
                "refs/heads/d1",
                PreviousValue::MustExistAndMatch(Target::Object(hex_to_id(common::MAIN_COMMIT))),
                RefLog::AndReference,
                false,
            )],
            Fail::Immediately,
            Fail::Immediately,
        )
        .expect("the packed record supplies the value to compare against")
        .commit(committer().to_ref(&mut TimeBuf::default()))
        .expect("commit succeeds");
    assert_eq!(edits.len(), 1);

    let packed = store
        .open_packed_buffer()
        .expect("readable")
        .expect("other records remain");
    assert!(
        packed.try_find("refs/heads/d1").expect("readable").is_none(),
        "the record was removed from the packed file"
    );
}

// ── I5. Loose and packed storage side by side ────────────────────────────────

// DependsOn: an_ongoing_packed_transaction_forces_a_packed_refs_lock_elsewhere
#[test]
fn object_references_are_packed_while_symbolic_ones_stay_loose() {
    let (_keep, store) = packed_and_symbolic_store();

    assert_eq!(
        store
            .open_packed_buffer()
            .expect("readable")
            .expect("the transaction created one")
            .iter()
            .expect("it parses")
            .count(),
        2,
        "both object references went into the pack"
    );
    assert_eq!(
        common::loose_ref_names(store.git_dir()),
        vec!["refs/symbolic"],
        "and only the symbolic one is left on disk, because a packed record cannot hold a name"
    );

    assert!(store.reflog_exists("refs/a").expect("a valid name"));
    assert!(store.reflog_exists("refs/b").expect("a valid name"));
    assert!(
        !store.reflog_exists("refs/symbolic").expect("a valid name"),
        "a symbolic write records no entry of its own"
    );
}

// DependsOn: an_ongoing_packed_transaction_forces_a_packed_refs_lock_elsewhere
#[test]
fn an_ongoing_transaction_forces_a_packed_refs_lock_once_a_packed_file_exists() {
    let (_keep, store) = packed_and_symbolic_store();

    // Neither of these two transactions asks for packed refs, and neither names
    // a reference the other does.
    let _ongoing = store
        .transaction()
        .prepare([create_at("refs/new")], Fail::Immediately, Fail::Immediately)
        .expect("the name is free");

    let err = store
        .transaction()
        .prepare(
            [create_at("refs/non-conflicting")],
            Fail::Immediately,
            Fail::Immediately,
        )
        .err()
        .expect("the first transaction holds the packed-refs lock");

    assert!(
        matches!(err, prepare::Error::PackedTransactionAcquire(_)),
        "once a packed file is present every transaction has to lock it, because every \
         transaction has to read it to resolve a previous value, got {err:?}"
    );
}

// DependsOn: a_symbolic_reference_gets_a_reflog_when_an_object_is_the_expected_previous_value
#[test]
fn writing_a_symbolic_target_over_a_packed_reference_creates_a_loose_overlay() {
    let (_keep, store) = packed_and_symbolic_store();
    assert_eq!(common::loose_ref_names(store.git_dir()), vec!["refs/symbolic"]);

    commit_all(
        &store,
        [update_edit(
            "refs/a",
            PreviousValue::Any,
            Target::Symbolic("refs/heads/does-not-matter".try_into().expect("valid name")),
        )],
    );

    assert_eq!(
        common::loose_ref_names(store.git_dir()),
        vec!["refs/a", "refs/symbolic"],
        "a name cannot become symbolic inside the pack, so a loose file appears to overlay it"
    );
    assert_eq!(
        store
            .open_packed_buffer()
            .expect("readable")
            .expect("still there")
            .find("refs/a")
            .expect("still packed")
            .target(),
        hex_to_id(common::EMPTY_BLOB),
        "the packed record is left exactly as it was, now shadowed"
    );
    assert_eq!(
        store
            .find("refs/a")
            .expect("it resolves")
            .target
            .to_ref()
            .try_name()
            .map(gix_ref::FullNameRef::as_bstr),
        Some("refs/heads/does-not-matter".as_bytes().as_bstr()),
        "and a lookup sees the loose overlay, not the record beneath it"
    );
}

// DependsOn: delete_a_reference_which_is_gone_succeeds
#[test]
fn deleting_a_loose_overlay_and_the_records_beneath_empties_the_store() {
    let (_keep, store) = packed_and_symbolic_store();
    commit_all(
        &store,
        [update_edit(
            "refs/a",
            PreviousValue::Any,
            Target::Symbolic("refs/heads/does-not-matter".try_into().expect("valid name")),
        )],
    );

    commit_all(
        &store,
        [delete_at("refs/a"), delete_at("refs/b"), delete_at("refs/symbolic")],
    );

    for name in ["refs/a", "refs/b", "refs/symbolic"] {
        assert!(
            store.try_find(name).expect("readable").is_none(),
            "{name} is gone -- for refs/a that means both the loose overlay and the record it hid"
        );
    }
    assert!(
        common::loose_ref_names(store.git_dir()).is_empty(),
        "nothing is left on the loose side"
    );
    assert!(
        !store.packed_refs_path().is_file(),
        "and the packed file went with its last record"
    );
    assert!(!store.reflog_exists("refs/a").expect("a valid name"));
    assert!(!store.reflog_exists("refs/b").expect("a valid name"));
}

// ── I6. Reference-log creation rules ─────────────────────────────────────────

// DependsOn: committing_without_a_signature_succeeds_when_no_reflog_is_written
#[test]
fn logs_are_created_automatically_only_for_the_documented_categories() {
    let (_keep, store) = common::store_writable("make_ref_repository.sh");

    let automatic = [
        "refs/heads/auto",
        "refs/remotes/origin/auto",
        "refs/notes/auto",
        "refs/worktree/auto",
    ];
    let manual = ["refs/tags/auto", "refs/auto", "refs/stash-like/auto"];

    let edits: Vec<RefEdit> = automatic
        .iter()
        .chain(manual.iter())
        .map(|name| create_with_log(name, common::MAIN_COMMIT, false))
        .collect();
    commit_all(&store, edits);

    for name in automatic {
        assert!(
            store.reflog_exists(name).expect("a valid name"),
            "{name} is in a category that gets a log without being asked"
        );
    }
    for name in manual {
        assert!(
            !store.reflog_exists(name).expect("a valid name"),
            "{name} is not, so writing it records nothing"
        );
    }
}

// DependsOn: committing_without_a_signature_succeeds_when_no_reflog_is_written
#[test]
fn forcing_a_log_creates_one_for_a_category_that_would_not_get_one() {
    let (_keep, store) = common::store_writable("make_ref_repository.sh");

    commit_all(&store, [create_with_log("refs/tags/forced", common::MAIN_COMMIT, true)]);

    assert!(
        store.reflog_exists("refs/tags/forced").expect("a valid name"),
        "the per-edit flag overrides the category rule"
    );
    assert_eq!(
        common::reflog_lines(&store, "refs/tags/forced"),
        vec![log_line(
            common::null_id(),
            hex_to_id(common::MAIN_COMMIT),
            "an entry"
        )],
        "and the entry that gets written is the ordinary one"
    );
}

// DependsOn: symbolic_head_created_then_referent_updated_with_reflog_always
#[test]
fn the_always_write_mode_creates_a_log_without_being_asked() {
    let (_keep, store) = common::store_writable_with("make_ref_repository.sh", WriteReflog::Always);

    commit_all(&store, [create_with_log("refs/tags/always", common::MAIN_COMMIT, false)]);

    assert!(
        store.reflog_exists("refs/tags/always").expect("a valid name"),
        "the store-wide mode overrides the category rule just as the per-edit flag does"
    );
}

// DependsOn: symbolic_head_created_then_referent_updated_with_reflog_disabled
#[test]
fn the_disabled_write_mode_creates_no_log_even_when_one_is_forced() {
    let (_keep, store) = common::store_writable_with("make_ref_repository.sh", WriteReflog::Disable);

    commit_all(
        &store,
        [
            create_with_log("refs/heads/disabled", common::MAIN_COMMIT, true),
            create_with_log("refs/tags/disabled", common::MAIN_COMMIT, true),
        ],
    );

    for name in ["refs/heads/disabled", "refs/tags/disabled"] {
        assert!(
            !store.reflog_exists(name).expect("a valid name"),
            "{name} gets no log: switching logging off outranks both the category rule and \
             the per-edit flag"
        );
    }
    assert!(
        store.try_find_loose("refs/heads/disabled").expect("readable").is_some(),
        "the references themselves are written as usual"
    );
}

// DependsOn: symbolic_head_created_then_referent_updated_with_normal_reflog
#[test]
fn each_log_entry_records_the_value_the_previous_entry_left_behind() {
    let (_keep, store) = common::store_writable("make_ref_repository.sh");
    let first = hex_to_id(common::MAIN_COMMIT);
    let second = hex_to_id(common::ANNOTATED_TAG);
    let third = hex_to_id(common::EMPTY_BLOB);

    for id in [first, second, third] {
        commit_all(
            &store,
            [RefEdit {
                change: Change::Update {
                    log: LogChange {
                        mode: RefLog::AndReference,
                        force_create_reflog: false,
                        message: "an entry".into(),
                    },
                    expected: PreviousValue::Any,
                    new: Target::Object(id),
                },
                name: "refs/heads/chain".try_into().expect("valid name"),
                deref: false,
            }],
        );
    }

    assert_eq!(
        common::reflog_lines(&store, "refs/heads/chain"),
        vec![
            log_line(common::null_id(), first, "an entry"),
            log_line(first, second, "an entry"),
            log_line(second, third, "an entry"),
        ],
        "entries accumulate oldest first, and each one's previous value is the value the \
         entry before it wrote -- the first starting from nothing"
    );
}
