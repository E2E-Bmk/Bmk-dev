//! Atomic layer: one documented behaviour per test, in isolation.
//!
//! Scope. A test belongs here when it exercises a single declared operation
//! against either no store at all or a store that starts out empty. Edit
//! preprocessing (specification section *Edit Preprocessing*), the reflog line
//! codec and the reverse iterator's buffer contract (*Reference Logs*), and the
//! prepare/rollback/commit contract over a store this test itself populates
//! (*Preparing a Transaction*, *Rollback*, *Committing*) all qualify. A test
//! that needs one of the scripted git repositories, or that has to chain a
//! packed-refs read onto a transaction to observe anything, lives in the
//! integration layer instead.
//!
//! Every test lives at the crate root, so the reported node id is
//! `atomic::<fn>`. A `mod` here would become part of both the id and the
//! nextest filter expression, and of the `// DependsOn:` names the integration
//! layer refers to.
//!
//! Upstream sources this layer draws from:
//!   gix-ref/tests/refs/transaction.rs
//!   gix-ref/tests/refs/file/log.rs                                    -- `mod line`, `mod iter::backward`
//!   gix-ref/tests/refs/file/transaction/prepare_and_commit/create_or_update/mod.rs
//!   gix-ref/tests/refs/file/transaction/prepare_and_commit/create_or_update/collisions.rs
//!   gix-ref/tests/refs/file/transaction/prepare_and_commit/delete.rs
//!
//! Two conventions hold throughout, both from the carve brief:
//!
//! * **Variants, not rendered text.** A failing call is matched on its error
//!   variant and the fields the specification names, never on a formatted
//!   message. The three exceptions are recorded in `filter/import_audit.md` §6
//!   and all concern error types with no public variants at all.
//! * **Nothing reaches into the locking crates.** No test inspects a lock
//!   file's bytes, the order of syscalls, or retry timing. What *is* asserted is
//!   which reference name a lock failure is attributed to, and whether a lock
//!   was taken at all -- both are `gix-ref`'s own decisions.

use std::{cell::RefCell, collections::BTreeMap, io::Cursor};

use common::{TimeBuf, committer, create_at, create_symbolic_at, delete_at, hex_to_id, log_line, null_id};
use gix_lock::acquire::Fail;
use gix_ref::{
    Kind, PartialNameRef, Target,
    bstr::{BString, ByteSlice},
    file::transaction::{PackedRefs, commit, prepare},
    store::WriteReflog,
    transaction::{Change, LogChange, PreviousValue, RefEdit, RefEditsExt, RefLog},
};

// ── local helpers ────────────────────────────────────────────────────────────
//
// These stay here rather than in `common` because only the preprocessing tests
// need them: `RefEditsExt` is a trait over plain `Vec<RefEdit>` and has no
// store behind it, so its "store" is a `BTreeMap` that yields each target once.

#[derive(Default)]
struct MockStore {
    targets: RefCell<BTreeMap<BString, Target>>,
}

impl MockStore {
    fn with(targets: impl IntoIterator<Item = (&'static str, Target)>) -> Self {
        MockStore {
            targets: RefCell::new(targets.into_iter().map(|(k, v)| (BString::from(k), v)).collect()),
        }
    }

    /// Removes on lookup, so a second lookup of the same name misses. That is
    /// what makes `assert_empty` a statement about which names were consulted.
    fn find_existing(&self, name: &PartialNameRef) -> Option<Target> {
        self.targets.borrow_mut().remove(name.as_bstr())
    }

    fn assert_empty(self) {
        assert_eq!(
            self.targets.borrow().len(),
            0,
            "every mocked target should have been looked up exactly once"
        );
    }
}

fn delete_edit(name: &str, expected: PreviousValue, log: RefLog, deref: bool) -> RefEdit {
    RefEdit {
        change: Change::Delete { expected, log },
        name: name.try_into().expect("valid name"),
        deref,
    }
}

fn update_edit(name: &str, expected: PreviousValue, new: Target, deref: bool) -> RefEdit {
    RefEdit {
        change: Change::Update {
            log: LogChange::default(),
            expected,
            new,
        },
        name: name.try_into().expect("valid name"),
        deref,
    }
}

fn symbolic(name: &str) -> Target {
    Target::Symbolic(name.try_into().expect("valid target name"))
}

/// The id every one-off update in this file writes; its value carries no
/// meaning beyond being a well-formed object id that differs from the null id.
fn some_id() -> gix_hash::ObjectId {
    hex_to_id("28ce6a8b26aa170e1de65536fe8abe1832bd3242")
}

// ── Edit Preprocessing ───────────────────────────────────────────────────────

#[test]
fn assure_one_name_has_one_edit_accepts_unique_names() {
    let one = vec![delete_edit("HEAD", PreviousValue::Any, RefLog::AndReference, false)];
    assert!(
        one.assure_one_name_has_one_edit().is_ok(),
        "a single edit cannot collide with itself"
    );

    let two = vec![
        delete_edit("refs/foo", PreviousValue::Any, RefLog::AndReference, false),
        delete_edit("HEAD", PreviousValue::Any, RefLog::AndReference, false),
    ];
    assert!(
        two.assure_one_name_has_one_edit().is_ok(),
        "distinct names are accepted regardless of the order they arrive in"
    );
}

#[test]
fn assure_one_name_has_one_edit_reports_the_duplicate_name() {
    let edits = vec![
        delete_edit("HEAD", PreviousValue::Any, RefLog::AndReference, false),
        delete_edit("refs/heads/main", PreviousValue::Any, RefLog::AndReference, false),
        delete_edit("HEAD", PreviousValue::Any, RefLog::AndReference, false),
    ];
    let duplicate = edits
        .assure_one_name_has_one_edit()
        .expect_err("two edits name HEAD");
    assert_eq!(
        duplicate, "HEAD",
        "the duplicated name itself is returned, not a rendered message"
    );
}

#[test]
fn pre_process_rejects_a_duplicate_introduced_by_a_split() {
    // `HEAD` is symbolic and dereferenced, so preprocessing adds an edit for
    // `refs/heads/main` -- which the caller also asked for directly.
    let edits = || {
        vec![
            delete_edit("HEAD", PreviousValue::Any, RefLog::AndReference, true),
            delete_edit("refs/heads/main", PreviousValue::Any, RefLog::AndReference, false),
        ]
    };

    let store = MockStore::with(Some(("HEAD", symbolic("refs/heads/main"))));
    let err = edits()
        .pre_process(&mut |n| store.find_existing(n), &mut |_, e| e)
        .expect_err("the split introduces a second edit for refs/heads/main");
    assert_eq!(
        err.kind(),
        std::io::ErrorKind::AlreadyExists,
        "the duplicate is reported as an already-existing entry"
    );

    // The name carried by that failure is the referent's, not the symbolic
    // reference the caller wrote down. `assure_one_name_has_one_edit` hands the
    // name back as a value, so the claim can be pinned without reading the
    // rendered message.
    let store = MockStore::with(Some(("HEAD", symbolic("refs/heads/main"))));
    let mut split = edits();
    split
        .extend_with_splits_of_symbolic_refs(&mut |n| store.find_existing(n), &mut |_, e| e)
        .expect("splitting alone succeeds");
    assert_eq!(
        split
            .assure_one_name_has_one_edit()
            .expect_err("the duplicate only exists after the split"),
        "refs/heads/main",
        "the collision is named after the referent that the split produced"
    );
}

#[test]
fn splits_are_skipped_for_non_symbolic_refs_and_clear_the_deref_flag() {
    let store = MockStore::with(Some((
        "refs/heads/anything-but-not-symbolic",
        Target::Object(null_id()),
    )));
    let mut edits = vec![
        delete_edit(
            "SYMBOLIC_PROBABLY_BUT_DEREF_IS_FALSE_SO_IGNORED",
            PreviousValue::Any,
            RefLog::AndReference,
            false,
        ),
        delete_edit(
            "refs/heads/anything-but-not-symbolic",
            PreviousValue::Any,
            RefLog::AndReference,
            true,
        ),
        delete_edit(
            "refs/heads/does-not-exist-and-deref-is-ignored",
            PreviousValue::Any,
            RefLog::AndReference,
            true,
        ),
    ];

    edits
        .extend_with_splits_of_symbolic_refs(&mut |n| store.find_existing(n), &mut |_, _| {
            panic!("no entry may be manufactured when nothing is symbolic")
        })
        .expect("nothing to split is not a failure");

    assert_eq!(edits.len(), 3, "no edit was added");
    assert!(
        edits.iter().all(|e| !e.deref),
        "preprocessing clears the flag on every edit it has considered, \
         including one whose name does not resolve at all"
    );
    store.assert_empty();
}

#[test]
fn splitting_an_empty_edit_list_is_ok() {
    let store = MockStore::default();
    Vec::<RefEdit>::new()
        .extend_with_splits_of_symbolic_refs(&mut |n| store.find_existing(n), &mut |_, e| e)
        .expect("an empty list has nothing to split and cannot fail");
}

#[test]
fn splitting_a_symbolic_cycle_stops_after_five_rounds() {
    // A store that answers every lookup with a symbolic target, alternating
    // between two names, so following the chain never terminates.
    struct Cycler {
        next: std::cell::Cell<bool>,
    }
    impl Cycler {
        fn find_existing(&self, _name: &PartialNameRef) -> Option<Target> {
            let flip = self.next.get();
            self.next.set(!flip);
            Some(symbolic(if flip {
                "heads/refs/next"
            } else {
                "heads/refs/previous"
            }))
        }
    }

    let mut edits = vec![
        delete_edit("refs/heads/delete-symbolic-1", PreviousValue::Any, RefLog::AndReference, true),
        RefEdit {
            change: Change::Update {
                log: LogChange {
                    mode: RefLog::AndReference,
                    force_create_reflog: true,
                    message: "the log message".into(),
                },
                expected: PreviousValue::MustNotExist,
                new: Target::Object(null_id()),
            },
            name: "refs/heads/update-symbolic-1".try_into().expect("valid name"),
            deref: true,
        },
    ];

    let store = Cycler {
        next: std::cell::Cell::new(false),
    };
    let err = edits
        .extend_with_splits_of_symbolic_refs(&mut |n| store.find_existing(n), &mut |_, e| e)
        .expect_err("the chain never bottoms out");
    assert_eq!(
        err.kind(),
        std::io::ErrorKind::WouldBlock,
        "the round limit is reported as a would-block condition rather than by looping forever"
    );
}

#[test]
fn symbolic_refs_are_split_into_referents_recursively() {
    let store = MockStore::with(vec![
        ("refs/heads/delete-symbolic-1", symbolic("refs/heads/delete-symbolic-2")),
        ("refs/heads/delete-symbolic-2", symbolic("refs/heads/delete-symbolic-3")),
        (
            "refs/heads/delete-symbolic-3",
            Target::Object(hex_to_id(common::EMPTY_BLOB)),
        ),
        ("refs/heads/update-symbolic-1", symbolic("refs/heads/update-symbolic-2")),
        ("refs/heads/update-symbolic-2", symbolic("refs/heads/update-symbolic-3")),
        (
            "refs/heads/update-symbolic-3",
            Target::Object(hex_to_id(common::EMPTY_BLOB)),
        ),
    ]);
    let log = LogChange {
        mode: RefLog::AndReference,
        force_create_reflog: true,
        message: "the log message".into(),
    };
    let log_only = LogChange {
        mode: RefLog::Only,
        ..log.clone()
    };

    let mut edits = vec![
        delete_edit("refs/heads/delete-symbolic-1", PreviousValue::Any, RefLog::AndReference, true),
        RefEdit {
            change: Change::Update {
                log: log.clone(),
                expected: PreviousValue::MustNotExist,
                new: Target::Object(null_id()),
            },
            name: "refs/heads/update-symbolic-1".try_into().expect("valid name"),
            deref: true,
        },
    ];

    let mut indices = Vec::new();
    edits
        .extend_with_splits_of_symbolic_refs(
            &mut |n| store.find_existing(n),
            &mut |parent, e| {
                indices.push(parent);
                e
            },
        )
        .expect("the chain terminates at an object target");

    assert_eq!(
        indices,
        vec![0, 1, 2, 3],
        "each produced entry is told which edit it descends from"
    );
    assert_eq!(
        edits,
        vec![
            RefEdit {
                change: Change::Delete {
                    expected: PreviousValue::Any,
                    log: RefLog::Only,
                },
                name: "refs/heads/delete-symbolic-1".try_into().expect("valid name"),
                deref: false,
            },
            RefEdit {
                change: Change::Update {
                    log: log_only.clone(),
                    expected: PreviousValue::Any,
                    new: Target::Object(null_id()),
                },
                name: "refs/heads/update-symbolic-1".try_into().expect("valid name"),
                deref: false,
            },
            RefEdit {
                change: Change::Delete {
                    expected: PreviousValue::Any,
                    log: RefLog::Only,
                },
                name: "refs/heads/delete-symbolic-2".try_into().expect("valid name"),
                deref: false,
            },
            RefEdit {
                change: Change::Update {
                    log: log_only,
                    expected: PreviousValue::Any,
                    new: Target::Object(null_id()),
                },
                name: "refs/heads/update-symbolic-2".try_into().expect("valid name"),
                deref: false,
            },
            RefEdit {
                change: Change::Delete {
                    expected: PreviousValue::Any,
                    log: RefLog::AndReference,
                },
                name: "refs/heads/delete-symbolic-3".try_into().expect("valid name"),
                deref: false,
            },
            RefEdit {
                change: Change::Update {
                    log,
                    expected: PreviousValue::MustNotExist,
                    new: Target::Object(null_id()),
                },
                name: "refs/heads/update-symbolic-3".try_into().expect("valid name"),
                deref: false,
            },
        ],
        "intermediate links keep the reference itself untouched and log only, \
         the leaf keeps the caller's log mode and expectation, and every deref flag is cleared"
    );
}

#[test]
fn change_reports_its_new_and_previous_values() {
    let previous = Target::Object(hex_to_id(common::MAIN_COMMIT));
    let new = Target::Object(some_id());

    let update = Change::Update {
        log: LogChange::default(),
        expected: PreviousValue::MustExistAndMatch(previous.clone()),
        new: new.clone(),
    };
    assert_eq!(
        update.new_value().map(Into::<Target>::into),
        Some(new),
        "an update reports the value it is about to write"
    );
    assert_eq!(
        update.previous_value().map(Into::<Target>::into),
        Some(previous.clone()),
        "an expectation that carries a target reports it as the previous value"
    );

    let delete = Change::Delete {
        expected: PreviousValue::ExistingMustMatch(previous.clone()),
        log: RefLog::AndReference,
    };
    assert_eq!(delete.new_value(), None, "a deletion writes no value");
    assert_eq!(
        delete.previous_value().map(Into::<Target>::into),
        Some(previous),
        "the may-exist expectation carries a target too"
    );

    let unconstrained = Change::Delete {
        expected: PreviousValue::Any,
        log: RefLog::AndReference,
    };
    assert_eq!(
        unconstrained.previous_value(),
        None,
        "expectations without a target report no previous value"
    );
}

#[test]
fn log_change_default_logs_the_reference_without_forcing() {
    assert_eq!(
        LogChange::default(),
        LogChange {
            mode: RefLog::AndReference,
            force_create_reflog: false,
            message: BString::default(),
        },
        "the default writes both the reference and its log, creates no log that \
         would not be created anyway, and carries an empty message"
    );

    // The structural assertion above is satisfied by a `Default` derive over
    // the right field order, so on its own it observes a type declaration
    // rather than a behaviour. Each of the three fields is therefore also read
    // back through a commit that uses nothing but the default: `AndReference`
    // by the reference existing afterwards, the empty message by the line the
    // log carries, and `force_create_reflog: false` by the second name -- which
    // is in no category that qualifies for automatic creation -- getting no log
    // at all.
    let (_keep, store) = common::empty_store_with(WriteReflog::Normal);
    let new = Target::Object(hex_to_id(common::MAIN_COMMIT));
    let with_default = |name: &str| RefEdit {
        change: Change::Update {
            log: LogChange::default(),
            expected: PreviousValue::MustNotExist,
            new: new.clone(),
        },
        name: name.try_into().expect("a valid full name"),
        deref: false,
    };

    store
        .transaction()
        .prepare(
            [with_default("refs/heads/main"), with_default("refs/onlyhere")],
            Fail::Immediately,
            Fail::Immediately,
        )
        .expect("both names are free")
        .commit(committer().to_ref(&mut TimeBuf::default()))
        .expect("commit succeeds");

    assert_eq!(
        store
            .try_find_loose("refs/heads/main")
            .expect("readable")
            .expect("mode AndReference writes the reference itself, not only its log")
            .target,
        gix_ref::Target::Object(hex_to_id(common::MAIN_COMMIT)),
    );
    assert_eq!(
        common::reflog_lines(&store, "refs/heads/main"),
        vec![log_line(null_id(), hex_to_id(common::MAIN_COMMIT), "")],
        "mode AndReference writes the log too, and the default message is empty"
    );
    assert_eq!(
        common::reflog_line_count(&store, "refs/onlyhere"),
        None,
        "with force_create_reflog false, a name outside the automatic categories gets no log"
    );
}

// ── Reference Logs: the line codec and the reverse iterator's buffer ─────────
//
// Held to six tests on purpose. The reflog line format is documented outside
// this specification, so tests that only parse or render a line are cheap
// signal; the integration layer spends its budget on the parts that are not
// public knowledge. See `filter/import_audit.md` §10.

#[test]
fn log_line_round_trips_through_write_to() {
    for message in ["commit (initial): c1", ""] {
        let line = log_line(null_id(), hex_to_id(common::MAIN_COMMIT), message);
        let mut buf = Vec::new();
        line.write_to(&mut buf).expect("a message without newlines is writable");
        assert_eq!(
            buf.last(),
            Some(&b'\n'),
            "every rendered line is terminated, including one with an empty message"
        );

        let parsed = gix_ref::file::log::LineRef::from_bytes(&buf)
            .expect("what write_to produced must parse")
            .to_owned();
        assert_eq!(parsed, line, "the round trip is lossless");
    }
}

#[test]
fn log_line_parse_keeps_angle_brackets_in_the_message() {
    let line = gix_ref::file::log::LineRef::from_bytes(
        b"7b114132d03c468a9cd97836901553658c9792de 306cdbab5457c323d1201aa8a59b3639f600a758 \
First Last <first.last@example.com> 1727013187 +0200\trebase (pick): Replace Into<Range<u32>> by From<LineRange>",
    )
    .expect("the message's angle brackets must not be mistaken for the email delimiters");

    assert_eq!(line.signature.name, "First Last");
    assert_eq!(line.signature.email, "first.last@example.com");
    assert_eq!(line.signature.seconds(), 1_727_013_187);
    assert_eq!(
        line.message,
        "rebase (pick): Replace Into<Range<u32>> by From<LineRange>".as_bytes().as_bstr(),
        "the message is everything after the tab, verbatim"
    );
}

#[test]
fn log_line_write_to_rejects_a_message_with_a_newline() {
    let line = log_line(
        null_id(),
        hex_to_id(common::MAIN_COMMIT),
        "and here come\nthe newline",
    );
    let mut written = Vec::new();
    let err = line
        .write_to(&mut written)
        .expect_err("a newline would split one entry into two");

    // The wrapping type is an `std::io::Error` around a private error, so there
    // is no variant to match on. The specification states the rendered text
    // exactly ("an I/O error whose message is exactly ..."), so the text is
    // derivable from the specification alone and is what is pinned here.
    assert_eq!(
        err.to_string(),
        r"Messages must not contain newlines (\n)",
        "the failure has to say what is wrong with the message"
    );

    // The same specification sentence ends "and nothing must be written in that
    // case" (line 776). That half has no assertion on purpose: the reference
    // writes the two ids and the signature to the sink and only then inspects
    // the message (upstream `store/file/log/line.rs:34-38`), so it leaves 121
    // bytes behind. Pinning the specified behaviour fails the reference gate and
    // pinning the observed behaviour contradicts the specification, so the
    // clause goes back to the spec owner as defect D14.
}

#[test]
fn reverse_log_iteration_rejects_a_zero_sized_buffer() {
    let mut buf = [0u8; 0];
    assert!(
        gix_ref::file::log::iter::reverse(Cursor::new(b"won't matter".as_ref()), &mut buf).is_err(),
        "a zero-sized sliding window can never hold a line and is refused up front, \
         rather than at the first call to next()"
    );
}

#[test]
fn reverse_log_iteration_yields_a_single_line_with_or_without_trailing_newline() {
    let bare: Vec<u8> = b"0000000000000000000000000000000000000000 134385f6d781b7e97062102c6a483440bfda2a03 \
committer <committer@example.com> 946771200 +0000\tcommit (initial): c1"
        .to_vec();
    let terminated = {
        let mut l = bare.clone();
        l.push(b'\n');
        l
    };

    let mut buf = [0u8; 1024];
    for log in [bare, terminated] {
        let mut iter = gix_ref::file::log::iter::reverse(Cursor::new(&log), &mut buf)
            .expect("the buffer is large enough for the whole file");
        let gix_ref::log::Line {
            previous_oid,
            new_oid,
            signature: _,
            message,
        } = iter.next().expect("one line is present").expect("it parses");

        assert_eq!(previous_oid, null_id());
        assert_eq!(new_oid, hex_to_id(common::MAIN_COMMIT));
        assert_eq!(message, "commit (initial): c1");
        assert!(
            iter.next().is_none(),
            "a trailing newline does not manufacture an extra empty entry"
        );
    }
}

#[test]
fn reverse_log_iteration_yields_two_lines_newest_first() {
    let bare: Vec<u8> = b"1000000000000000000000000000000000000000 234385f6d781b7e97062102c6a483440bfda2a03 \
committer <committer@example.com> 946771200 +0000\tcommit (initial): c2\n\
0000000000000000000000000000000000000000 134385f6d781b7e97062102c6a483440bfda2a03 \
committer <committer@example.com> 946771200 +0000\tcommit (initial): c1"
        .to_vec();
    let terminated = {
        let mut l = bare.clone();
        l.push(b'\n');
        l
    };
    let logs = [bare, terminated];

    // 1024 holds the whole file; 256 does not, so the second size also exercises
    // the refill that slides the window backwards over the file.
    for buf_size in [1024usize, 256] {
        let mut buf = vec![0u8; buf_size];
        for log in &logs {
            let mut iter = gix_ref::file::log::iter::reverse(Cursor::new(log), &mut buf)
                .expect("both sizes are large enough for a single line");

            let newest = iter.next().expect("two lines are present").expect("it parses");
            assert_eq!(newest.message, "commit (initial): c1", "iteration starts at the end");
            assert_eq!(newest.previous_oid, null_id());
            assert_eq!(newest.new_oid, hex_to_id(common::MAIN_COMMIT));

            let oldest = iter.next().expect("two lines are present").expect("it parses");
            assert_eq!(oldest.message, "commit (initial): c2");
            assert_eq!(
                oldest.previous_oid,
                hex_to_id("1000000000000000000000000000000000000000")
            );
            assert_eq!(oldest.new_oid, hex_to_id("234385f6d781b7e97062102c6a483440bfda2a03"));

            assert!(iter.next().is_none(), "iterator depleted");
        }
    }
}

/// Specification lines 836-841. The reverse iterator numbers a malformed line
/// *from the end*, which is the one place its error differs from the forward
/// iterator's on the same input. Asserted on the rendered prefix rather than a
/// variant because `decode` is not a public module -- exception E2/E3 in
/// `filter/import_audit.md` §6.
#[test]
fn reverse_log_iteration_numbers_a_malformed_line_from_the_end() {
    let log: Vec<u8> = b"0000000000000000000000000000000000000000 134385f6d781b7e97062102c6a483440bfda2a03 \
committer <committer@example.com> 946771200 +0000\tcommit (initial): c1\n\
not a reflog line at all\n"
        .to_vec();

    let mut buf = vec![0u8; 1024];
    let mut iter =
        gix_ref::file::log::iter::reverse(Cursor::new(log), &mut buf).expect("the buffer is large enough");

    let err = iter
        .next()
        .expect("the malformed line is still yielded")
        .expect_err("but it does not parse");

    // The numbering lives in the *payload*, not in the variant: specification
    // lines 1047-1049 fix `decode::Error`'s display as `"In line {line}: {inner}"`
    // while `reverse::Error::Decode`'s own text (line 1056) is the fixed
    // "Could not decode log line". Asserting on the outer string would pin the
    // wrong sentence and would pass for a forward-numbered implementation too.
    let decode = match err {
        gix_ref::file::log::iter::reverse::Error::Decode(inner) => inner,
        other => panic!("a malformed line is a decode failure, got {other:?}"),
    };
    let rendered = decode.to_string();
    assert!(
        rendered.starts_with("In line 1 from the end: "),
        "the newest line is numbered 1 counting from the end, got {rendered:?}"
    );

    let second = iter
        .next()
        .expect("the well-formed line follows")
        .expect("and it parses");
    assert_eq!(second.message, "commit (initial): c1");
}

// ── Rollback ─────────────────────────────────────────────────────────────────

#[test]
fn implicit_rollback_removes_intermediate_directories() {
    let (dir, store) = common::empty_store();
    let transaction = store
        .transaction()
        .prepare(
            [create_at("refs/heads/a/b/ref"), create_at("refs/heads/a/c/ref")],
            Fail::Immediately,
            Fail::Immediately,
        )
        .expect("both names are free");

    assert!(
        dir.path().join("refs/heads/a/b").exists(),
        "preparation creates the directories its lock files live in"
    );
    assert!(dir.path().join("refs/heads/a/c").exists());

    drop(transaction);

    assert!(!dir.path().join("refs/heads").exists(), "the tree is unwound again");
    assert!(
        !dir.path().join("refs").exists(),
        "unwinding goes all the way up to the directory the transaction created first"
    );
}

#[test]
fn explicit_rollback_removes_intermediate_directories() {
    let (dir, store) = common::empty_store();
    let transaction = store
        .transaction()
        .prepare(
            [create_at("refs/heads/a/b/ref"), create_at("refs/heads/a/c/ref")],
            Fail::Immediately,
            Fail::Immediately,
        )
        .expect("both names are free");

    let edits = transaction.rollback();

    assert_eq!(edits.len(), 2, "rollback hands the prepared edits back to the caller");
    assert!(!dir.path().join("refs/heads").exists());
    assert!(
        !dir.path().join("refs").exists(),
        "an explicit rollback cleans up exactly as dropping the transaction does"
    );
}

#[test]
fn cancellation_after_preparation_leaves_no_change() {
    let (dir, store) = common::empty_store();
    let transaction = store.transaction();
    assert_eq!(
        std::fs::read_dir(dir.path()).expect("readable").count(),
        0,
        "obtaining a transaction touches nothing"
    );

    let transaction = transaction
        .prepare(
            Some(create_symbolic_at("HEAD", "refs/heads/main")),
            Fail::Immediately,
            Fail::Immediately,
        )
        .expect("HEAD is free");
    assert_eq!(
        std::fs::read_dir(dir.path()).expect("readable").count(),
        1,
        "preparation puts a lock in place, and nothing else"
    );

    drop(transaction);
    assert_eq!(
        std::fs::read_dir(dir.path()).expect("readable").count(),
        0,
        "everything vanished"
    );
}

// ── Preparing a Transaction ──────────────────────────────────────────────────

#[test]
fn a_reference_can_be_created_where_an_empty_directory_is_in_the_way() {
    let (dir, store) = common::empty_store();
    std::fs::create_dir_all(dir.path().join("HEAD").join("a").join("b").join("also-empty"))
        .expect("the temporary directory is writable");

    let mut buf = TimeBuf::default();
    let edits = store
        .transaction()
        .prepare(
            Some(update_edit(
                "HEAD",
                PreviousValue::MustNotExist,
                symbolic("refs/heads/main"),
                false,
            )),
            Fail::Immediately,
            Fail::Immediately,
        )
        .expect("a directory does not count as an existing reference")
        .commit(committer().to_ref(&mut buf))
        .expect("committing removes the empty directory tree and puts the file there");

    assert!(
        store
            .try_find_loose(edits[0].name.as_ref())
            .expect("readable")
            .is_some(),
        "HEAD was created despite a tree of empty directories being in the way"
    );
}

#[test]
fn a_reference_cannot_be_committed_where_a_non_empty_directory_is_in_the_way() {
    let (dir, store) = common::empty_store();
    let head_dir = dir.path().join("HEAD");
    std::fs::create_dir_all(head_dir.join("a").join("b").join("also-empty"))
        .expect("the temporary directory is writable");
    std::fs::write(head_dir.join("file.ext"), b"").expect("the temporary directory is writable");

    let mut buf = TimeBuf::default();
    let err = store
        .transaction()
        .prepare(
            Some(update_edit(
                "HEAD",
                PreviousValue::MustNotExist,
                symbolic("refs/heads/main"),
                false,
            )),
            Fail::Immediately,
            Fail::Immediately,
        )
        .expect("preparation still succeeds -- the clash only shows when the file is put in place")
        .commit(committer().to_ref(&mut buf))
        .expect_err("a directory holding a file cannot be replaced by that file");

    // The `source` here is a libc message surfaced through the locking crate,
    // which is delegated territory; only the variant and the name it blames are
    // this crate's own decision.
    match err {
        commit::Error::LockCommit { full_name, .. } => {
            assert_eq!(full_name, "HEAD", "the failure names the reference that could not land");
        }
        other => panic!("expected the commit of a single lock to fail, got {other:?}"),
    }
}

#[test]
fn must_exist_on_a_missing_reference_fails_preparation() {
    let (_keep, store) = common::empty_store();

    // `new` must not be the null id. Specification line 496 gives this cell as
    // `expected: Target::Object(<null id of the store's hash kind>)` -- the
    // reported expectation is a property of the *store*, not an echo of what
    // the caller asked to write. With `new` set to the null id an assertion
    // here cannot tell those two rules apart, so it is set to a real id and the
    // assertion names the null id directly.
    let new = Target::Object(some_id());

    let err = store
        .transaction()
        .prepare(
            Some(update_edit("HEAD", PreviousValue::MustExist, new.clone(), false)),
            Fail::Immediately,
            Fail::Immediately,
        )
        .err()
        .expect("nothing exists in an empty store");

    match err {
        prepare::Error::MustExist { full_name, expected } => {
            assert_eq!(full_name, "HEAD");
            assert_eq!(
                expected,
                Target::Object(null_id()),
                "with no value to name, the expectation is reported as the store's null id"
            );
            assert_ne!(expected, new, "and not as the value that was to be written");
        }
        other => panic!("expected a must-exist failure, got {other:?}"),
    }
}

/// Specification line 498: the `MustExistAndMatch(p)` / absent cell of the
/// update table. It shares the `MustExist` error with the row above it but
/// reports `p` rather than the null id, which is the whole content of the rule.
#[test]
fn must_exist_and_match_on_a_missing_reference_reports_the_supplied_target() {
    let (_keep, store) = common::empty_store();
    let wanted = Target::Object(hex_to_id(common::MAIN_COMMIT));

    let err = store
        .transaction()
        .prepare(
            Some(update_edit(
                "refs/heads/main",
                PreviousValue::MustExistAndMatch(wanted.clone()),
                Target::Object(some_id()),
                false,
            )),
            Fail::Immediately,
            Fail::Immediately,
        )
        .err()
        .expect("nothing exists in an empty store");

    match err {
        prepare::Error::MustExist { full_name, expected } => {
            assert_eq!(full_name, "refs/heads/main");
            assert_eq!(
                expected, wanted,
                "the supplied target is named back, not the store's null id"
            );
            assert_ne!(
                expected,
                Target::Object(null_id()),
                "which is what distinguishes this cell from the `MustExist` one above it"
            );
        }
        other => panic!("expected a must-exist failure, got {other:?}"),
    }
}

/// Specification line 511: the `MustExistAndMatch(p)` / absent cell of the
/// delete table. A deletion reports a *different* variant from an update in the
/// same situation, and carries no expectation with it.
#[test]
fn must_exist_and_match_deleting_a_missing_reference_fails() {
    let (_keep, store) = common::empty_store();

    let err = store
        .transaction()
        .prepare(
            Some(delete_edit(
                "refs/heads/main",
                PreviousValue::MustExistAndMatch(Target::Object(hex_to_id(common::MAIN_COMMIT))),
                RefLog::AndReference,
                false,
            )),
            Fail::Immediately,
            Fail::Immediately,
        )
        .err()
        .expect("nothing exists in an empty store");

    match err {
        prepare::Error::DeleteReferenceMustExist { full_name } => {
            assert_eq!(full_name, "refs/heads/main");
        }
        other => panic!("a deletion reports its own variant, got {other:?}"),
    }
}

/// Specification line 511, the present-and-matching half of the same cell. The
/// suite otherwise only ever applies `MustExistAndMatch` to a deletion that is
/// expected to fail, so without this the accepting arm is unpinned.
#[test]
fn must_exist_and_match_deletes_a_reference_that_holds_the_named_value() {
    let (_keep, store) = common::empty_store_with(WriteReflog::Normal);
    let held = Target::Object(hex_to_id(common::MAIN_COMMIT));

    store
        .transaction()
        .prepare(
            Some(update_edit(
                "refs/heads/main",
                PreviousValue::MustNotExist,
                held.clone(),
                false,
            )),
            Fail::Immediately,
            Fail::Immediately,
        )
        .expect("the name is free")
        .commit(committer().to_ref(&mut TimeBuf::default()))
        .expect("commit succeeds");

    let edits = store
        .transaction()
        .prepare(
            Some(delete_edit(
                "refs/heads/main",
                PreviousValue::MustExistAndMatch(held.clone()),
                RefLog::AndReference,
                false,
            )),
            Fail::Immediately,
            Fail::Immediately,
        )
        .expect("the held value matches the expectation")
        .commit(committer().to_ref(&mut TimeBuf::default()))
        .expect("commit succeeds");

    assert_eq!(edits.len(), 1);
    assert!(
        store.try_find_loose("refs/heads/main").expect("readable").is_none(),
        "the reference is gone"
    );
    assert_eq!(
        common::reflog_line_count(&store, "refs/heads/main"),
        None,
        "and `RefLog::AndReference` took its log with it"
    );
}

#[test]
fn namespaced_edits_are_not_observable_in_the_returned_edits() {
    let (_keep, mut store) = common::empty_store();
    store.namespace = gix_ref::namespace::expand("foo").expect("a valid partial name").into();

    let requested = vec![
        delete_at("refs/for/deletion"),
        create_symbolic_at("HEAD", "refs/heads/hello"),
    ];
    let edits = store
        .transaction()
        .prepare(requested.clone(), Fail::Immediately, Fail::Immediately)
        .expect("both names are free inside the namespace")
        .commit(committer().to_ref(&mut TimeBuf::default()))
        .expect("commit succeeds");

    assert_eq!(
        edits, requested,
        "the namespace is applied to the paths on disk and stripped again on the way out"
    );
    assert!(
        store.git_dir().join("refs/namespaces/foo").exists(),
        "the namespace really was applied -- the edits above are not simply echoed back"
    );
}

#[test]
fn windows_device_names_are_rejected_when_protection_is_enabled() {
    let (_keep, mut store) = common::empty_store();
    store.prohibit_windows_device_names = true;
    let git_dir = store.git_dir().to_owned();

    for invalid in ["refs/heads/CON", "refs/CON/still-invalid"] {
        let err = store
            .transaction()
            .prepare(
                Some(update_edit(
                    invalid,
                    PreviousValue::Any,
                    Target::Object(some_id()),
                    false,
                )),
                Fail::Immediately,
                Fail::Immediately,
            )
            .err()
            .unwrap_or_else(|| panic!("{invalid} names a reserved device and must be refused"));

        assert!(
            !matches!(err, prepare::Error::LockAcquire { .. }),
            "the name is rejected on its own terms, not by failing to lock it, got {err:?}"
        );
        assert!(
            !git_dir.join(format!("{invalid}.lock")).exists(),
            "no lock file may be left behind for a name that was never accepted"
        );
    }

    assert!(
        !git_dir.join("refs").exists(),
        "the check also runs when the previous value does not matter, so not even a \
         directory is created for the rejected names"
    );
}

#[test]
fn windows_device_names_are_accepted_when_protection_is_disabled() {
    let (_keep, mut store) = common::empty_store();
    store.prohibit_windows_device_names = false;

    let edits = store
        .transaction()
        .prepare(
            Some(update_edit(
                "refs/heads/CON",
                PreviousValue::Any,
                Target::Object(some_id()),
                false,
            )),
            Fail::Immediately,
            Fail::Immediately,
        )
        .expect("the flag is off, so the name is just a name")
        .commit(committer().to_ref(&mut TimeBuf::default()))
        .expect("commit succeeds");

    assert_eq!(edits.len(), 1);
    assert_eq!(
        store
            .find_loose("refs/heads/CON")
            .expect("it was written")
            .target
            .try_id()
            .map(ToOwned::to_owned),
        Some(some_id()),
        "the reference is readable again under the name it was written with"
    );
}

#[test]
fn the_windows_device_name_check_runs_before_lock_acquisition() {
    let (_keep, mut store) = common::empty_store();
    store.prohibit_windows_device_names = true;
    let git_dir = store.git_dir().to_owned();

    // Occupy the lock the transaction would take. If locking happened first the
    // failure below would be a lock-acquisition failure instead.
    let refs_heads = git_dir.join("refs").join("heads");
    std::fs::create_dir_all(&refs_heads).expect("the temporary directory is writable");
    std::fs::write(refs_heads.join("CON.lock"), b"").expect("the temporary directory is writable");

    let err = store
        .transaction()
        .prepare(
            Some(update_edit(
                "refs/heads/CON",
                PreviousValue::Any,
                Target::Object(some_id()),
                false,
            )),
            Fail::Immediately,
            Fail::Immediately,
        )
        .err()
        .expect("the name is still refused");

    assert!(
        !matches!(err, prepare::Error::LockAcquire { .. }),
        "validation must short-circuit before the lock is attempted; the pre-existing \
         lock file would otherwise surface as a lock-acquisition failure, got {err:?}"
    );
    assert!(
        refs_heads.join("CON.lock").exists(),
        "the lock file that was already there is left exactly as it was found"
    );
}

#[test]
fn a_lock_failure_on_a_referent_is_attributed_to_the_symbolic_reference() {
    let (_keep, store) = common::empty_store();
    let git_dir = store.git_dir().to_owned();
    std::fs::write(git_dir.join("HEAD"), b"ref: refs/heads/main\n").expect("writable");
    std::fs::create_dir_all(git_dir.join("refs/heads")).expect("writable");
    std::fs::write(git_dir.join("refs/heads/main.lock"), b"").expect("writable");

    let err = store
        .transaction()
        .prepare(
            Some(update_edit(
                "HEAD",
                PreviousValue::Any,
                Target::Object(some_id()),
                true,
            )),
            Fail::Immediately,
            Fail::Immediately,
        )
        .err()
        .expect("the referent's lock is already held");

    match err {
        prepare::Error::LockAcquire { full_name, .. } => assert_eq!(
            full_name, "HEAD",
            "the caller wrote down HEAD, so that is the name the failure is reported against, \
             even though the lock that could not be taken belongs to refs/heads/main"
        ),
        other => panic!("expected a lock-acquisition failure, got {other:?}"),
    }
}

#[test]
fn delete_a_reference_which_is_gone_succeeds() {
    let (_keep, store) = common::empty_store();
    let edits = store
        .transaction()
        .prepare(
            Some(delete_edit(
                "DOES_NOT_EXIST",
                PreviousValue::Any,
                RefLog::AndReference,
                false,
            )),
            Fail::Immediately,
            Fail::Immediately,
        )
        .expect("an unconstrained deletion of a missing reference is not an error")
        .commit(committer().to_ref(&mut TimeBuf::default()))
        .expect("commit succeeds");

    assert_eq!(edits.len(), 1, "the edit is still reported to the caller");
    assert_eq!(
        edits[0].change,
        Change::Delete {
            expected: PreviousValue::Any,
            log: RefLog::AndReference,
        },
        "with nothing found, the caller's expectation is left as it was"
    );
}

#[test]
fn delete_a_reference_which_is_gone_but_must_exist_fails() {
    let (_keep, store) = common::empty_store();
    let err = store
        .transaction()
        .prepare(
            Some(delete_edit(
                "DOES_NOT_EXIST",
                PreviousValue::MustExist,
                RefLog::AndReference,
                false,
            )),
            Fail::Immediately,
            Fail::Immediately,
        )
        .err()
        .expect("the reference has to exist for this deletion");

    match err {
        prepare::Error::DeleteReferenceMustExist { full_name } => assert_eq!(full_name, "DOES_NOT_EXIST"),
        other => panic!("expected a must-exist deletion failure, got {other:?}"),
    }
}

#[test]
fn delete_a_broken_reference_that_must_exist_fails() {
    let (_keep, store) = common::empty_store();
    std::fs::write(store.git_dir().join("HEAD"), b"broken").expect("writable");
    assert!(
        store.try_find_loose("HEAD").is_err(),
        "the file is there but is not a reference"
    );

    let err = store
        .transaction()
        .prepare(
            Some(delete_edit("HEAD", PreviousValue::MustExist, RefLog::AndReference, true)),
            Fail::Immediately,
            Fail::Immediately,
        )
        .err()
        .expect("a file that does not decode does not satisfy must-exist");

    match err {
        prepare::Error::DeleteReferenceMustExist { full_name } => assert_eq!(
            full_name, "HEAD",
            "content that fails to decode is treated as absent rather than as a decode failure"
        ),
        other => panic!("expected a must-exist deletion failure, got {other:?}"),
    }
}

#[test]
fn delete_a_broken_reference_may_be_deleted_even_in_deref_mode() {
    let (_keep, store) = common::empty_store();
    std::fs::write(store.git_dir().join("HEAD"), b"broken").expect("writable");
    assert!(store.try_find_loose("HEAD").is_err(), "the ref is truly broken");

    let edits = store
        .transaction()
        .prepare(
            Some(delete_edit("HEAD", PreviousValue::Any, RefLog::AndReference, true)),
            Fail::Immediately,
            Fail::Immediately,
        )
        .expect("an unconstrained deletion does not have to read the value")
        .commit(committer().to_ref(&mut TimeBuf::default()))
        .expect("commit succeeds");

    assert!(
        store.try_find_loose("HEAD").expect("readable").is_none(),
        "the unreadable file was removed"
    );
    assert_eq!(
        edits,
        vec![delete_edit("HEAD", PreviousValue::Any, RefLog::AndReference, false)],
        "the deref flag is cleared and no split was produced, because nothing resolved"
    );
}

#[test]
fn non_existing_can_be_deleted_with_the_existing_must_match_constraint() {
    let (_keep, store) = common::empty_store();
    let expected = PreviousValue::ExistingMustMatch(Target::Object(hex_to_id(common::MAIN_COMMIT)));

    let edits = store
        .transaction()
        .prepare(
            Some(delete_edit(
                "refs/heads/not-there",
                expected.clone(),
                RefLog::AndReference,
                true,
            )),
            Fail::Immediately,
            Fail::Immediately,
        )
        .expect("the may-exist constraint tolerates absence")
        .commit(committer().to_ref(&mut TimeBuf::default()))
        .expect("commit succeeds");

    assert_eq!(
        edits,
        vec![delete_edit(
            "refs/heads/not-there",
            expected,
            RefLog::AndReference,
            false
        )],
        "nothing was found, so the caller's expectation is returned unchanged"
    );
}

#[test]
fn deleting_with_a_must_not_exist_expectation_panics() {
    let (_keep, store) = common::empty_store();

    // A correct transaction first. This is what separates the panic below from
    // a store that simply cannot do anything.
    store
        .transaction()
        .prepare(
            [create_at("refs/heads/present")],
            Fail::Immediately,
            Fail::Immediately,
        )
        .expect("the name is free")
        .commit(committer().to_ref(&mut TimeBuf::default()))
        .expect("commit succeeds");

    let previous_hook = std::panic::take_hook();
    std::panic::set_hook(Box::new(|_| {}));
    let outcome = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
        store.transaction().prepare(
            Some(delete_edit(
                "refs/heads/present",
                PreviousValue::MustNotExist,
                RefLog::AndReference,
                false,
            )),
            Fail::Immediately,
            Fail::Immediately,
        )
    }));
    std::panic::set_hook(previous_hook);

    assert!(
        outcome.is_err(),
        "asking for a deletion whose expectation is that the reference does not exist is a \
         programming error, and must panic rather than return an error a caller could handle"
    );
    assert!(
        store.try_find_loose("refs/heads/present").expect("readable").is_some(),
        "the aborted transaction changed nothing"
    );
}

// ── Committing ───────────────────────────────────────────────────────────────

#[test]
fn committing_without_a_signature_succeeds_when_no_reflog_is_written() {
    let (_keep, store) = common::empty_store();

    // A tag is not one of the categories a log is created for, and the edit does
    // not force one, so no log file is ever opened and no signature is needed.
    let edits = store
        .transaction()
        .prepare(
            Some(update_edit(
                "refs/tags/v1",
                PreviousValue::MustNotExist,
                Target::Object(some_id()),
                false,
            )),
            Fail::Immediately,
            Fail::Immediately,
        )
        .expect("the name is free")
        .commit(None::<gix_actor::SignatureRef<'_>>)
        .expect("no signature is required when nothing is logged");

    assert_eq!(edits.len(), 1);
    assert!(
        !store.reflog_exists("refs/tags/v1").expect("a valid name"),
        "no log was created for a category that does not get one automatically"
    );
}

#[test]
fn committing_without_a_signature_fails_when_a_reflog_must_be_written() {
    let (_keep, store) = common::empty_store();

    // A local branch does get a log automatically, so the missing signature
    // surfaces the moment the entry is about to be appended.
    let err = store
        .transaction()
        .prepare(
            Some(update_edit(
                "refs/heads/main",
                PreviousValue::MustNotExist,
                Target::Object(some_id()),
                false,
            )),
            Fail::Immediately,
            Fail::Immediately,
        )
        .expect("the name is free")
        .commit(None::<gix_actor::SignatureRef<'_>>)
        .expect_err("a log entry cannot be written without a committer");

    assert!(
        matches!(
            err,
            commit::Error::CreateOrUpdateRefLog(gix_ref::file::log::create_or_update::Error::MissingCommitter)
        ),
        "the failure is the missing committer, surfaced through the reflog stage, got {err:?}"
    );
}

// The sibling arm of the rule this test pins -- specification lines 803-806,
// "a message containing a newline must return
// `file::log::create_or_update::Error::MessageWithNewlines`" -- has no test on
// purpose. The reference implementation never constructs that variant:
// `reflog_create_or_append` (upstream `store/file/loose/reflog.rs:150-180`)
// checks the committer and then writes the message through `writeln!` with no
// inspection of its bytes, and `MessageWithNewlines` appears nowhere in the
// crate but its own declaration. A test asserting the specified behaviour fails
// the reference gate; a test asserting the observed behaviour contradicts the
// specification. Both are wrong, so the clause is carried back to the spec
// owner as defect D13 instead. The codec-level rejection this was likely
// conflated with -- `Line::write_to` refusing a newline, specification lines
// 774-776 -- is real and is pinned by
// `log_line_write_to_rejects_a_message_with_a_newline`.

/// Specification lines 799-803. The append writer and `Line::write_to` disagree
/// on purpose: `write_to` always emits a tab (lines 772-774), while an appended
/// entry with an empty message ends in a bare newline with no tab at all. Every
/// other reflog assertion in this suite parses first, and a parser cannot see
/// the difference -- so this one reads the bytes the library actually wrote.
#[test]
fn an_appended_entry_with_an_empty_message_ends_without_a_tab() {
    let (dir, store) = common::empty_store_with(WriteReflog::Always);
    let new = Target::Object(some_id());

    store
        .transaction()
        .prepare(
            Some(update_edit("refs/heads/main", PreviousValue::MustNotExist, new, false)),
            Fail::Immediately,
            Fail::Immediately,
        )
        .expect("the name is free")
        .commit(committer().to_ref(&mut TimeBuf::default()))
        .expect("commit succeeds");

    let written = std::fs::read(dir.path().join("logs").join("refs").join("heads").join("main"))
        .expect("the log was created");
    let written = written.as_bstr();

    assert_eq!(
        written,
        format!(
            "{} {} committer <committer@example.com> 1234 +0800\n",
            null_id(),
            some_id()
        )
        .as_bytes()
        .as_bstr(),
        "an empty message contributes a newline and nothing else"
    );
    assert!(
        !written.contains(&b'\t'),
        "in particular no tab, which is where the append writer parts ways with `Line::write_to`"
    );
}

// ── Committing: a symbolic HEAD and its referent, once per reflog mode ───────

/// Create `HEAD` pointing at a referent that does not exist, then update it
/// with dereferencing on, and check what each store-wide reflog mode records.
///
/// Upstream runs this as one test with a three-arm loop. The arms take
/// different paths through the reflog writer, so they are three tests here.
fn symbolic_head_then_referent(mode: WriteReflog) {
    let (_keep, store) = common::empty_store_with(mode);
    let referent = "refs/heads/alt-main";
    assert!(
        store.try_find_loose(referent).expect("readable").is_none(),
        "the referent does not exist yet"
    );

    let log_ignored = LogChange {
        mode: RefLog::AndReference,
        force_create_reflog: false,
        message: "ignored".into(),
    };
    let head_value = symbolic(referent);
    let mut buf = TimeBuf::default();

    let edits = store
        .transaction()
        .prepare(
            Some(RefEdit {
                change: Change::Update {
                    log: log_ignored.clone(),
                    expected: PreviousValue::MustNotExist,
                    new: head_value.clone(),
                },
                name: "HEAD".try_into().expect("valid name"),
                deref: false,
            }),
            Fail::Immediately,
            Fail::Immediately,
        )
        .expect("HEAD is free")
        .commit(committer().to_ref(&mut buf))
        .expect("commit succeeds");

    assert_eq!(
        edits,
        vec![RefEdit {
            change: Change::Update {
                log: log_ignored,
                expected: PreviousValue::MustNotExist,
                new: head_value.clone(),
            },
            name: "HEAD".try_into().expect("valid name"),
            deref: false,
        }],
        "a symbolic write whose referent is missing produces no split"
    );

    let head = store.find_loose("HEAD").expect("it was written");
    assert_eq!(head.kind(), Kind::Symbolic);
    assert_eq!(
        std::fs::read_to_string(store.git_dir().join("HEAD")).expect("readable"),
        "ref: refs/heads/alt-main\n",
        "note the newline: symbolic references are written the way git writes them"
    );
    assert!(
        !head.log_exists(&store),
        "writing a symbolic reference records no log entry of its own"
    );
    assert!(
        store.try_find_loose(referent).expect("readable").is_none(),
        "the referent was not brought into existence"
    );

    let new_oid = some_id();
    let log = LogChange {
        mode: RefLog::AndReference,
        force_create_reflog: false,
        message: "an actual change".into(),
    };
    let edits = store
        .transaction()
        .prepare(
            Some(RefEdit {
                change: Change::Update {
                    log: log.clone(),
                    expected: PreviousValue::Any,
                    new: Target::Object(new_oid),
                },
                name: "HEAD".try_into().expect("valid name"),
                deref: true,
            }),
            Fail::Immediately,
            Fail::Immediately,
        )
        .expect("HEAD resolves to a name that can be written")
        .commit(committer().to_ref(&mut buf))
        .expect("commit succeeds");

    assert_eq!(
        edits,
        vec![
            RefEdit {
                change: Change::Update {
                    log: LogChange {
                        mode: RefLog::Only,
                        ..log.clone()
                    },
                    expected: PreviousValue::MustExistAndMatch(head_value),
                    new: Target::Object(new_oid),
                },
                name: "HEAD".try_into().expect("valid name"),
                deref: false,
            },
            RefEdit {
                change: Change::Update {
                    log,
                    // The referent had no value, so there is nothing to require.
                    expected: PreviousValue::Any,
                    new: Target::Object(new_oid),
                },
                name: referent.try_into().expect("valid name"),
                deref: false,
            },
        ],
        "the split leaves HEAD symbolic and log-only, and writes the object into the referent"
    );

    let head = store.find_loose("HEAD").expect("still there");
    assert_eq!(head.kind(), Kind::Symbolic, "HEAD was not detached");
    assert_eq!(
        head.target.to_ref().try_name().map(gix_ref::FullNameRef::as_bstr),
        Some(referent.as_bytes().as_bstr()),
        "and it still points at the same referent"
    );
    assert_eq!(
        store
            .find_loose(referent)
            .expect("now it exists")
            .target
            .try_id()
            .map(ToOwned::to_owned),
        Some(new_oid),
        "the referent holds the new object"
    );

    let mut read_buf = Vec::new();
    for name in ["HEAD", referent] {
        match mode {
            WriteReflog::Normal | WriteReflog::Always => assert_eq!(
                common::reflog_lines(&store, name),
                vec![log_line(null_id(), new_oid, "an actual change")],
                "{name} records the object ids of the leaf referent, from the null id upwards"
            ),
            WriteReflog::Disable => assert!(
                store.reflog_iter(name, &mut read_buf).expect("readable").is_none(),
                "{name} has no log at all when logging is switched off"
            ),
        }
    }
}

#[test]
fn symbolic_head_created_then_referent_updated_with_normal_reflog() {
    symbolic_head_then_referent(WriteReflog::Normal);
}

#[test]
fn symbolic_head_created_then_referent_updated_with_reflog_disabled() {
    symbolic_head_then_referent(WriteReflog::Disable);
}

#[test]
fn symbolic_head_created_then_referent_updated_with_reflog_always() {
    symbolic_head_then_referent(WriteReflog::Always);
}

#[test]
fn a_symbolic_reference_gets_a_reflog_when_an_object_is_the_expected_previous_value() {
    let (_keep, store) = common::empty_store();
    let referent = "refs/heads/alt-main";
    assert!(
        store.try_find_loose(referent).expect("readable").is_none(),
        "the referent does not exist"
    );

    let edits = store
        .transaction()
        .prepare(
            Some(RefEdit {
                change: Change::Update {
                    log: LogChange {
                        mode: RefLog::AndReference,
                        force_create_reflog: false,
                        message: "message".into(),
                    },
                    expected: PreviousValue::ExistingMustMatch(Target::Object(some_id())),
                    new: symbolic(referent),
                },
                name: "refs/heads/symbolic".try_into().expect("valid name"),
                deref: false,
            }),
            Fail::Immediately,
            Fail::Immediately,
        )
        .expect("the name is free and the may-exist constraint tolerates that")
        .commit(committer().to_ref(&mut TimeBuf::default()))
        .expect("commit succeeds");

    assert_eq!(edits.len(), 1, "no split was performed");
    let written = store.find_loose(&edits[0].name).expect("it was written");
    assert_eq!(written.name.as_bstr(), "refs/heads/symbolic");
    assert_eq!(written.kind(), Kind::Symbolic);
    assert_eq!(
        written.target.to_ref().try_name().map(gix_ref::FullNameRef::as_bstr),
        Some(referent.as_bytes().as_bstr())
    );
    assert!(
        written.log_exists(&store),
        "an object id supplied as the expected previous value is worth logging even for a \
         symbolic write -- this is what gets a peeled id into the log during a clone"
    );
    assert!(
        store.try_find_loose(referent).expect("readable").is_none(),
        "the referent still was not created"
    );
}

// ── Collisions and concurrency, over a store this test populates ─────────────

#[test]
fn conflicting_creation_of_names_differing_only_in_case() {
    let (dir, store) = common::empty_store();
    let case_sensitive = common::is_case_sensitive(dir.path());

    let result = store.transaction().prepare(
        [create_at("refs/a"), create_at("refs/A")],
        Fail::Immediately,
        Fail::Immediately,
    );

    match result {
        Ok(transaction) => {
            assert!(
                case_sensitive,
                "two names differing only in case cannot both be locked on a filesystem \
                 that does not tell them apart"
            );
            let edits = transaction
                .commit(committer().to_ref(&mut TimeBuf::default()))
                .expect("commit succeeds");
            assert_eq!(edits.len(), 2, "both references were created");
        }
        Err(err) => {
            assert!(
                !case_sensitive,
                "this filesystem tells the two names apart, so both should have been \
                 lockable, got {err:?}"
            );
            match err {
                prepare::Error::LockAcquire { full_name, .. } => assert_eq!(
                    full_name, "refs/A",
                    "the second of the two names is the one that could not be locked"
                ),
                other => panic!("expected a lock-acquisition failure, got {other:?}"),
            }
        }
    }
}

#[test]
fn non_conflicting_concurrent_transactions_both_commit() {
    let (_keep, store) = common::empty_store();
    let ongoing = store
        .transaction()
        .prepare([create_at("refs/new")], Fail::Immediately, Fail::Immediately)
        .expect("the name is free");

    let second = store
        .transaction()
        .prepare(
            [create_at("refs/non-conflicting")],
            Fail::Immediately,
            Fail::Immediately,
        )
        .expect("a transaction over a different name is unaffected by the ongoing one");

    let mut buf = TimeBuf::default();
    second.commit(committer().to_ref(&mut buf)).expect("commit succeeds");
    ongoing
        .commit(committer().to_ref(&mut buf))
        .expect("the first transaction can still be committed afterwards");

    assert!(store.reflog_exists("refs/new").expect("a valid name"));
    assert!(store.reflog_exists("refs/non-conflicting").expect("a valid name"));
}

#[test]
fn an_ongoing_packed_transaction_forces_a_packed_refs_lock_elsewhere() {
    let (_keep, store) = common::empty_store();
    let _ongoing = store
        .transaction()
        .packed_refs(PackedRefs::DeletionsAndNonSymbolicUpdatesRemoveLooseSourceReference(
            Box::new(common::EmptyCommit),
        ))
        .prepare([create_at("refs/a")], Fail::Immediately, Fail::Immediately)
        .expect("the packed file is about to be created");

    let err = store
        .transaction()
        .prepare([delete_at("refs/a")], Fail::Immediately, Fail::Immediately)
        .err()
        .expect("the packed-refs lock is already held");

    assert!(
        matches!(err, prepare::Error::PackedTransactionAcquire(_)),
        "once a packed file may come into existence, every other transaction has to take its \
         lock as well or risk missing what the first one writes, got {err:?}"
    );
}
