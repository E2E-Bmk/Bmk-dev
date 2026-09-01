//! Shared fixtures and helpers for the `gix-ref` transaction/reflog oracle.
//!
//! Everything the two suites need that is not itself under specification lives
//! here: the deterministic git-repository fixtures, the edit constructors the
//! upstream suite keeps in a test-module preamble, and the small
//! object-database stand-in that the packed-refs peeling rules need.
//!
//! Nothing in this file declares a `#[test]`, so the crate is invisible to
//! `RustRunner.discover` and to nextest.

use std::{
    collections::HashMap,
    path::{Path, PathBuf},
    process::Command,
    sync::atomic::{AtomicU64, Ordering},
};

pub use tempfile::TempDir;

use gix_hash::ObjectId;
use gix_object::bstr::BString;
use gix_ref::{
    Target,
    file,
    transaction::{Change, LogChange, PreviousValue, RefEdit, RefLog},
};

/// The hash the fixtures and every expected object id in this oracle are
/// written for.
///
/// Appendix A: the crate exposes `sha1`, `sha256`, `serde` and `parallel`, and
/// "the `sha1` feature is the one under test". Upstream reaches this value
/// through `gix_testtools::object_hash()`, which reads an environment variable
/// and can hand back `Sha256`; there is no such variable here and no SHA-256
/// fixture, so the constant is written out.
pub const HASH_KIND: gix_hash::Kind = gix_hash::Kind::Sha1;

// ── object ids ───────────────────────────────────────────────────────────────

/// Parse 40 hex characters into a SHA-1 object id.
pub fn sha1_hex_to_id(hex: &str) -> ObjectId {
    ObjectId::from_hex(hex.as_bytes()).expect("40 bytes of hex")
}

/// The name the upstream suite uses. Identical to [`sha1_hex_to_id`] here.
///
/// Upstream's `hex_to_id` branches on `gix_testtools::object_hash()` and, for
/// SHA-256, looks the argument up in a hard-coded translation table. With the
/// hash pinned by Appendix A that branch is dead code and the table with it.
pub fn hex_to_id(hex: &str) -> ObjectId {
    sha1_hex_to_id(hex)
}

/// The all-zero id, which a reflog line uses for "no previous value" and for
/// "the reference is being deleted".
pub fn null_id() -> ObjectId {
    ObjectId::null(HASH_KIND)
}

/// The commit every scripted fixture's `main` points at.
pub const MAIN_COMMIT: &str = "134385f6d781b7e97062102c6a483440bfda2a03";
/// The annotated tag object `refs/tags/dt1` in `make_ref_repository.sh`.
pub const ANNOTATED_TAG: &str = "4c3f4cce493d7beb45012e478021b5f65295e5a3";
/// The empty blob, which upstream's [`create_at`] uses as a stand-in target.
pub const EMPTY_BLOB: &str = "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391";

// ── repository fixtures ──────────────────────────────────────────────────────

/// The fixture scripts themselves, as `const &str` in Rust source.
///
/// They are not read from disk. An oracle that loaded its test data from a
/// sibling directory would be scoring the candidate against whatever happened
/// to travel with the crate; carrying the bytes in source removes that degree
/// of freedom, and makes the cache key in [`fixture_read_only`] a hash over
/// something the compiler has already fixed.
pub mod scripts;

fn script_body(name: &str) -> &'static str {
    match name {
        "make_ref_repository.sh" => scripts::MAKE_REF_REPOSITORY,
        "make_packed_ref_repository.sh" => scripts::MAKE_PACKED_REF_REPOSITORY,
        "make_packed_ref_repository_for_overlay.sh" => {
            scripts::MAKE_PACKED_REF_REPOSITORY_FOR_OVERLAY
        }
        "make_repo_for_reflog.sh" => scripts::MAKE_REPO_FOR_REFLOG,
        other => panic!("no fixture script named {other:?} is embedded in this crate"),
    }
}

/// Run one embedded fixture script with `bash` inside `cwd`.
///
/// The environment is what makes the resulting object ids reproducible, and
/// each entry earns its place:
///
/// * the author and committer identity and date are fixed, because a commit's
///   id is a hash over both;
/// * system and global config are disabled, so a container's `/etc/gitconfig`
///   cannot inject a `commit.gpgsign` or a different `init.defaultBranch`;
/// * `init.defaultBranch=main` is set anyway, because the scripts assume it;
/// * signing is off, because a signature embeds a timestamp and a key;
/// * `GIT_DEFAULT_HASH=sha1` matches [`HASH_KIND`];
/// * the `GIT_DIR` family is removed, so a repository the harness itself is run
///   from cannot capture the fixture.
///
/// Verified inside `spec2repo-rust:latest`: the scripts reproduce
/// `refs/heads/main = 134385f6d781b7e97062102c6a483440bfda2a03`,
/// `refs/tags/dt1 = 4c3f4cce493d7beb45012e478021b5f65295e5a3`, a five-entry
/// `HEAD` reflog and a 581-entry `refs/heads/old` reflog.
fn run_script(name: &str, args: &[&str], cwd: &Path) {
    let mut cmd = Command::new("bash");
    // `bash -c BODY NAME ARGS...` puts NAME in `$0` and ARGS in `$1..`.
    cmd.arg("-c").arg(script_body(name)).arg(name);
    cmd.args(args);
    cmd.current_dir(cwd);

    for (key, value) in [
        ("GIT_CONFIG_NOSYSTEM", "1"),
        ("GIT_CONFIG_GLOBAL", "/dev/null"),
        ("GIT_TERMINAL_PROMPT", "false"),
        ("GIT_AUTHOR_DATE", "2000-01-01 00:00:00 +0000"),
        ("GIT_AUTHOR_EMAIL", "author@example.com"),
        ("GIT_AUTHOR_NAME", "author"),
        ("GIT_COMMITTER_DATE", "2000-01-02 00:00:00 +0000"),
        ("GIT_COMMITTER_EMAIL", "committer@example.com"),
        ("GIT_COMMITTER_NAME", "committer"),
        ("GIT_DEFAULT_HASH", "sha1"),
        ("GIT_CONFIG_COUNT", "6"),
        ("GIT_CONFIG_KEY_0", "commit.gpgsign"),
        ("GIT_CONFIG_VALUE_0", "false"),
        ("GIT_CONFIG_KEY_1", "tag.gpgsign"),
        ("GIT_CONFIG_VALUE_1", "false"),
        ("GIT_CONFIG_KEY_2", "init.defaultBranch"),
        ("GIT_CONFIG_VALUE_2", "main"),
        ("GIT_CONFIG_KEY_3", "protocol.file.allow"),
        ("GIT_CONFIG_VALUE_3", "always"),
        ("GIT_CONFIG_KEY_4", "maintenance.auto"),
        ("GIT_CONFIG_VALUE_4", "false"),
        ("GIT_CONFIG_KEY_5", "gc.auto"),
        ("GIT_CONFIG_VALUE_5", "0"),
    ] {
        cmd.env(key, value);
    }
    cmd.env("XDG_CONFIG_HOME", cwd.join(".xdg"));
    for key in [
        "GIT_DIR",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_WORK_TREE",
        "GIT_COMMON_DIR",
        "GIT_ASKPASS",
        "SSH_ASKPASS",
    ] {
        cmd.env_remove(key);
    }

    let out = cmd
        .output()
        .unwrap_or_else(|err| panic!("the evaluation image must provide `bash` and `git`: {err}"));
    assert!(
        out.status.success(),
        "fixture script {name} {args:?} failed with {}\n--- stdout ---\n{}\n--- stderr ---\n{}",
        out.status,
        String::from_utf8_lossy(&out.stdout),
        String::from_utf8_lossy(&out.stderr),
    );
}

/// Marker written into a fixture directory once its script has finished.
///
/// Presence of this file is the only signal that a cached directory is
/// complete; it is written before the directory is moved into place, so a
/// reader either sees the whole fixture or none of it.
const READY: &str = ".oracle-fixture-ready";

fn fnv1a(bytes: &[u8]) -> u64 {
    let mut hash: u64 = 0xcbf2_9ce4_8422_2325;
    for byte in bytes {
        hash ^= u64::from(*byte);
        hash = hash.wrapping_mul(0x1000_0000_01b3);
    }
    hash
}

static SERIAL: AtomicU64 = AtomicU64::new(0);

/// Materialise a read-only repository fixture, reusing a cached copy.
///
/// nextest runs every test in its own process, so a fixture shared by a dozen
/// tests would otherwise be rebuilt a dozen times -- and `make_repo_for_reflog.sh`
/// is 111 KB of heredoc. The cache key includes a hash of the script body, so
/// editing a script invalidates it rather than silently serving a stale
/// repository.
///
/// The build happens in a private staging directory and is published with a
/// single `rename`, which is atomic on the same filesystem. When two processes
/// race, the loser's `rename` fails because the destination already exists;
/// that is the expected outcome and the loser simply uses the winner's copy.
pub fn fixture_read_only(script_name: &str) -> PathBuf {
    let key = format!(
        "{}__{:016x}",
        script_name.trim_end_matches(".sh"),
        fnv1a(script_body(script_name).as_bytes()),
    );
    let root = std::env::temp_dir().join("gix-ref-txn-oracle-fixtures");
    let target = root.join(&key);
    if target.join(READY).is_file() {
        return target;
    }

    std::fs::create_dir_all(&root).expect("the temporary directory is writable");
    let staging = root.join(format!(
        ".staging__{key}__{}__{}",
        std::process::id(),
        SERIAL.fetch_add(1, Ordering::Relaxed),
    ));
    let _ = std::fs::remove_dir_all(&staging);
    std::fs::create_dir_all(&staging).expect("the temporary directory is writable");

    run_script(script_name, &[], &staging);
    std::fs::write(staging.join(READY), b"").expect("the staging directory is writable");

    if std::fs::rename(&staging, &target).is_err() {
        // Another process published the same fixture first; keep theirs.
        let _ = std::fs::remove_dir_all(&staging);
    }
    assert!(
        target.join(READY).is_file(),
        "fixture {key} was neither published by this process nor by another",
    );
    target
}

fn copy_tree(from: &Path, to: &Path) {
    std::fs::create_dir_all(to).expect("the temporary directory is writable");
    for entry in std::fs::read_dir(from).expect("the cached fixture is readable") {
        let entry = entry.expect("the cached fixture is readable");
        let kind = entry.file_type().expect("the cached fixture is readable");
        let target = to.join(entry.file_name());
        if kind.is_dir() {
            copy_tree(&entry.path(), &target);
        } else if kind.is_symlink() {
            // None of these fixtures contains a symlink; if one appears, copying
            // the link's target is still the behaviour a test would expect.
            std::fs::copy(entry.path(), &target).expect("the temporary directory is writable");
        } else {
            std::fs::copy(entry.path(), &target).expect("the temporary directory is writable");
        }
    }
}

/// Materialise a repository fixture the caller is going to modify.
///
/// Built by copying the cached read-only fixture rather than by re-running the
/// script: roughly a dozen tests want a writable repository, and re-running
/// `git` for each of them dominates the suite's wall time. Relocating a
/// repository this way is safe for these four fixtures specifically -- all are
/// plain `git init` repositories with no worktree, no alternates and no
/// absolute path anywhere in `.git/config`.
///
/// The returned guard must be held for as long as the directory is used.
pub fn fixture_writable(script_name: &str) -> (TempDir, PathBuf) {
    let source = fixture_read_only(script_name);
    let dir = tempfile::tempdir().expect("the temporary directory is writable");
    copy_tree(&source, dir.path());
    let _ = std::fs::remove_file(dir.path().join(READY));
    let path = dir.path().to_owned();
    (dir, path)
}

// ── stores ───────────────────────────────────────────────────────────────────

/// A read-only store over the repository the named script builds.
pub fn store_at(script_name: &str) -> file::Store {
    file::Store::at(fixture_read_only(script_name).join(".git"), HASH_KIND)
}

/// The all-loose repository: `make_ref_repository.sh`.
pub fn store() -> file::Store {
    store_at("make_ref_repository.sh")
}

/// The all-packed repository: `make_packed_ref_repository.sh`.
pub fn store_with_packed_refs() -> file::Store {
    store_at("make_packed_ref_repository.sh")
}

/// A writable copy of the repository the named script builds.
///
/// The guard must be held for as long as the store is used.
pub fn store_writable(script_name: &str) -> (TempDir, file::Store) {
    let (guard, root) = fixture_writable(script_name);
    let store = file::Store::at(root.join(".git"), HASH_KIND);
    (guard, store)
}

/// A writable copy of the named repository, opened with an explicit reflog mode.
pub fn store_writable_with(script_name: &str, write_reflog: gix_ref::store::WriteReflog) -> (TempDir, file::Store) {
    let (guard, root) = fixture_writable(script_name);
    let store = file::Store::at_opts(
        root.join(".git"),
        HASH_KIND,
        gix_ref::store::init::Options {
            write_reflog,
            ..Default::default()
        },
    );
    (guard, store)
}

/// The reflog fixture, opened read-only with reflog writing disabled.
///
/// Reading a log must not depend on the store's *write* mode; upstream pins
/// that by opening this fixture with `WriteReflog::Disable` and reading anyway.
pub fn reflog_store() -> file::Store {
    file::Store::at_opts(
        fixture_read_only("make_repo_for_reflog.sh").join(".git"),
        HASH_KIND,
        gix_ref::store::init::Options {
            write_reflog: gix_ref::store::WriteReflog::Disable,
            ..Default::default()
        },
    )
}

/// The raw bytes of `.git/logs/<name>` in the reflog fixture.
pub fn reflog_bytes(name: &str) -> Vec<u8> {
    let path = fixture_read_only("make_repo_for_reflog.sh")
        .join(".git")
        .join("logs")
        .join(name);
    std::fs::read(&path).unwrap_or_else(|err| panic!("the fixture writes {}: {err}", path.display()))
}

/// A store whose git directory is an empty temporary directory.
///
/// Matches upstream's `empty_store`: the store is rooted at the temporary
/// directory itself, not at a `.git` inside it, so every reference the test
/// creates is the only thing in the tree and directory-entry counts are exact.
pub fn empty_store() -> (TempDir, file::Store) {
    let dir = tempfile::tempdir().expect("the temporary directory is writable");
    let store = file::Store::at(dir.path().into(), HASH_KIND);
    (dir, store)
}

/// [`empty_store`] with an explicit reflog mode.
pub fn empty_store_with(write_reflog: gix_ref::store::WriteReflog) -> (TempDir, file::Store) {
    let dir = tempfile::tempdir().expect("the temporary directory is writable");
    let store = file::Store::at_opts(
        dir.path().into(),
        HASH_KIND,
        gix_ref::store::init::Options {
            write_reflog,
            ..Default::default()
        },
    );
    (dir, store)
}

// ── signatures, log lines and edits ──────────────────────────────────────────

/// The committer every transaction in this oracle commits as.
///
/// Upstream reaches `parse_header` through `gix-date`; `gix-actor` re-exports
/// that crate as `gix_actor::date`, so the value is identical without adding a
/// crate Appendix A does not list.
pub fn committer() -> gix_actor::Signature {
    gix_actor::Signature {
        name: "committer".into(),
        email: "committer@example.com".into(),
        time: gix_actor::date::parse_header("1234 +0800").expect("valid header time"),
    }
}

/// A borrowed form of [`committer`], for `Transaction::commit`.
///
/// The `TimeBuf` has to outlive the borrow, so callers keep one on the stack:
/// `commit(common::committer().to_ref(&mut buf))`.
pub type TimeBuf = gix_actor::date::parse::TimeBuf;

/// A reflog line as [`committer`] would write it.
pub fn log_line(previous: ObjectId, new: ObjectId, message: impl Into<BString>) -> gix_ref::log::Line {
    gix_ref::log::Line {
        previous_oid: previous,
        new_oid: new,
        signature: committer(),
        message: message.into(),
    }
}

/// Every reflog entry recorded for `name`, oldest first.
pub fn reflog_lines(store: &file::Store, name: &str) -> Vec<gix_ref::log::Line> {
    let mut buf = Vec::new();
    store
        .reflog_iter(name, &mut buf)
        .expect("the reflog is readable")
        .expect("a reflog exists for this reference")
        .map(|line| line.map(gix_ref::log::Line::from))
        .collect::<Result<Vec<_>, _>>()
        .expect("every recorded line parses")
}

/// How many reflog entries `name` has, or `None` when it has no log at all.
pub fn reflog_line_count(store: &file::Store, name: &str) -> Option<usize> {
    let mut buf = Vec::new();
    store
        .reflog_iter(name, &mut buf)
        .expect("the reflog is readable")
        .map(|iter| iter.filter_map(Result::ok).count())
}

/// Upstream's edit constructor: create `name` at the empty blob, forcing a log.
pub fn create_at(name: &str) -> RefEdit {
    RefEdit {
        change: Change::Update {
            log: LogChange {
                mode: RefLog::AndReference,
                force_create_reflog: true,
                message: "log peeled".into(),
            },
            expected: PreviousValue::MustNotExist,
            new: Target::Object(hex_to_id(EMPTY_BLOB)),
        },
        name: name.try_into().expect("valid"),
        deref: false,
    }
}

/// Upstream's edit constructor: create `name` pointing at `symbolic_target`.
pub fn create_symbolic_at(name: &str, symbolic_target: &str) -> RefEdit {
    RefEdit {
        change: Change::Update {
            log: LogChange::default(),
            expected: PreviousValue::MustNotExist,
            new: Target::Symbolic(symbolic_target.try_into().expect("valid target name")),
        },
        name: name.try_into().expect("valid"),
        deref: false,
    }
}

/// Upstream's edit constructor: delete `name` and its log, whatever it holds.
pub fn delete_at(name: &str) -> RefEdit {
    RefEdit {
        change: Change::Delete {
            expected: PreviousValue::Any,
            log: RefLog::AndReference,
        },
        name: name.try_into().expect("valid name"),
        deref: false,
    }
}

/// Turn a reference into the edit that re-writes it to its own current value.
///
/// This is the shape the packed-refs modes are exercised with: a no-op update
/// whose only effect is to move the record from loose storage into the pack.
pub fn repack_edit(name: &str, target: Target) -> RefEdit {
    RefEdit {
        change: Change::Update {
            log: LogChange::default(),
            expected: PreviousValue::MustExistAndMatch(target.clone()),
            new: target,
        },
        name: name.try_into().expect("valid name"),
        deref: false,
    }
}

// ── filesystem observation ───────────────────────────────────────────────────
//
// `file::Store::loose_iter` and `file::Store::iter` are outside this carve's
// declared surface, so tests that upstream writes against them observe the
// loose layer directly instead. The spec's Storage Model states the on-disk
// shape -- one file per reference under `refs/`, holding either 40 hex
// characters or `ref: <name>` -- so reading it back is observation, not a
// second implementation of lookup.

fn collect_files(dir: &Path, prefix: &str, out: &mut Vec<String>) {
    let entries = match std::fs::read_dir(dir) {
        Ok(entries) => entries,
        Err(_) => return,
    };
    for entry in entries.flatten() {
        let name = entry.file_name().to_string_lossy().into_owned();
        let joined = if prefix.is_empty() {
            name
        } else {
            format!("{prefix}/{name}")
        };
        match entry.file_type() {
            Ok(kind) if kind.is_dir() => collect_files(&entry.path(), &joined, out),
            Ok(_) => out.push(joined),
            Err(_) => {}
        }
    }
}

/// Every file under `<git_dir>/refs`, as a sorted list of full reference names.
pub fn loose_ref_names(git_dir: &Path) -> Vec<String> {
    let mut out = Vec::new();
    collect_files(&git_dir.join("refs"), "refs", &mut out);
    out.sort();
    out
}

/// The contents of the loose reference file `name`, if there is one.
pub fn loose_ref_content(git_dir: &Path, name: &str) -> Option<String> {
    std::fs::read_to_string(git_dir.join(name)).ok()
}

/// The names under `<git_dir>/refs` whose file holds a symbolic target.
pub fn loose_symbolic_ref_names(git_dir: &Path) -> Vec<String> {
    loose_ref_names(git_dir)
        .into_iter()
        .filter(|name| {
            loose_ref_content(git_dir, name)
                .is_some_and(|content| content.starts_with("ref: "))
        })
        .collect()
}

/// Whether the filesystem under `dir` distinguishes `x` from `X`.
///
/// Upstream asks `gix_fs::Capabilities::probe`, which is not part of this
/// carve's import surface; the probe itself is three lines.
pub fn is_case_sensitive(dir: &Path) -> bool {
    let lower = dir.join(".oracle-case-probe");
    std::fs::write(&lower, b"").expect("the temporary directory is writable");
    let upper_exists = dir.join(".ORACLE-CASE-PROBE").exists();
    let _ = std::fs::remove_file(&lower);
    !upper_exists
}

// ── object databases ─────────────────────────────────────────────────────────

/// An in-memory object database.
///
/// The packed-refs modes take a `Box<dyn gix_object::Find>` and use it for one
/// thing only: following a chain of tag objects down to the first non-tag, so
/// that a packed record can carry its `^peeled` line. A `HashMap` answers that
/// in twelve lines, which is why this carve needs no object-database crate.
///
/// Unknown ids deliberately answer `Ok(None)` rather than inventing an object:
/// the spec makes a missing object a `packed::transaction::prepare::Error`
/// case, and a catch-all default would make that clause untestable.
#[derive(Default, Clone)]
pub struct Mem {
    objects: HashMap<ObjectId, (gix_object::Kind, Vec<u8>)>,
}

impl Mem {
    /// A database in which every lookup misses.
    pub fn empty() -> Self {
        Self::default()
    }

    /// Register `id` as a commit, which stops peeling.
    pub fn with_commit(mut self, id: &str) -> Self {
        self.objects
            .insert(hex_to_id(id), (gix_object::Kind::Commit, Vec::new()));
        self
    }

    /// Register `id` as an annotated tag whose target is `target`.
    ///
    /// The body is a real tag object, because the peel loop parses it with
    /// `gix_object::TagRefIter` rather than trusting the reported kind.
    pub fn with_tag(mut self, id: &str, target: &str) -> Self {
        let body = format!(
            "object {target}\ntype commit\ntag oracle\ntagger committer <committer@example.com> 1234 +0800\n\nan annotated tag\n"
        );
        self.objects
            .insert(hex_to_id(id), (gix_object::Kind::Tag, body.into_bytes()));
        self
    }

    /// `tag` peels to `target`, and `target` is a commit.
    pub fn with_tag_chain(tag: &str, target: &str) -> Self {
        Self::empty().with_tag(tag, target).with_commit(target)
    }
}

impl gix_object::Find for Mem {
    fn try_find<'a>(
        &self,
        id: &gix_hash::oid,
        buffer: &'a mut Vec<u8>,
    ) -> Result<Option<gix_object::Data<'a>>, gix_object::find::Error> {
        match self.objects.get(id) {
            Some((kind, data)) => {
                buffer.clear();
                buffer.extend_from_slice(data);
                Ok(Some(gix_object::Data {
                    kind: *kind,
                    object_hash: id.kind(),
                    data: buffer,
                }))
            }
            None => Ok(None),
        }
    }
}

/// An object database that answers every lookup with an empty commit.
///
/// Peeling stops at the first non-tag object, so a database that reports
/// `Commit` for everything makes the packed writer emit no `^peeled` line at
/// all -- without needing to know which ids the fixture holds. Kept verbatim
/// from the upstream suite.
pub struct EmptyCommit;

impl gix_object::Find for EmptyCommit {
    fn try_find<'a>(
        &self,
        id: &gix_hash::oid,
        _buffer: &'a mut Vec<u8>,
    ) -> Result<Option<gix_object::Data<'a>>, gix_object::find::Error> {
        Ok(Some(gix_object::Data {
            kind: gix_object::Kind::Commit,
            object_hash: id.kind(),
            data: &[],
        }))
    }
}
