//! Shared fixtures for the `gix-status-001` oracle.
//!
//! No `#[test]` lives here: `RustRunner.discover` scans for `#[test]` and this
//! crate must stay invisible to it.
//!
//! Everything is built in memory. There is no on-disk Git repository, no
//! fixture archive and no `git` binary, so a test can only fail because the
//! candidate behaved differently from the specification.

use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::sync::atomic::AtomicBool;

use bstr::{BStr, BString};
use gix_hash::ObjectId;
use gix_index::entry::{Flags, Mode, Stage, Stat};
use gix_status::index_as_worktree::{
    traits::{FastEq, SubmoduleStatus},
    Context, EntryStatus, Options, Outcome, Recorder,
};

/// Worktree files are stamped with this fixed mtime.
///
/// Appendix B: timestamps are constants rather than the current clock, so
/// racy-clean behavior is chosen rather than raced.
pub const PAST: i64 = 1_600_000_000;

/// The index timestamp, strictly newer than [`PAST`] so fixtures are not racy
/// unless a test asks for it.
pub const INDEX_TS: i64 = 1_700_000_000;

// ---------------------------------------------------------------- object db

/// An in-memory object database over blob content.
#[derive(Clone, Default, Debug)]
pub struct Odb {
    objects: HashMap<ObjectId, Vec<u8>>,
}

impl Odb {
    pub fn new() -> Self {
        Self::default()
    }

    /// Hash `data` as a blob, store it, and return its id.
    pub fn insert_blob(&mut self, data: &[u8]) -> ObjectId {
        let id = gix_object::compute_hash(gix_hash::Kind::Sha1, gix_object::Kind::Blob, data)
            .expect("sha1 is available");
        self.objects.insert(id, data.to_owned());
        id
    }
}

impl gix_object::Find for Odb {
    fn try_find<'a>(
        &self,
        id: &gix_hash::oid,
        buffer: &'a mut Vec<u8>,
    ) -> Result<Option<gix_object::Data<'a>>, gix_object::find::Error> {
        match self.objects.get(id) {
            Some(data) => {
                buffer.clear();
                buffer.extend_from_slice(data);
                Ok(Some(gix_object::Data::new(
                    buffer,
                    gix_object::Kind::Blob,
                    gix_hash::Kind::Sha1,
                )))
            }
            None => Ok(None),
        }
    }
}

impl gix_object::FindHeader for Odb {
    fn try_header(
        &self,
        id: &gix_hash::oid,
    ) -> Result<Option<gix_object::Header>, gix_object::find::Error> {
        Ok(self.objects.get(id).map(|d| gix_object::Header {
            kind: gix_object::Kind::Blob,
            size: d.len() as u64,
        }))
    }
}

// -------------------------------------------------------- submodule delegates

/// A submodule delegate that never reports a modification.
#[derive(Clone, Copy, Default)]
pub struct NoSubmodules;

impl SubmoduleStatus for NoSubmodules {
    type Output = ();
    type Error = std::convert::Infallible;

    fn status(&mut self, _entry: &gix_index::Entry, _rela_path: &BStr) -> Result<Option<()>, Self::Error> {
        Ok(None)
    }
}

/// A submodule delegate that always reports a modification and records the
/// paths it was asked about.
#[derive(Clone, Default)]
pub struct DirtySubmodules {
    pub seen: std::sync::Arc<std::sync::Mutex<Vec<BString>>>,
}

impl SubmoduleStatus for DirtySubmodules {
    type Output = &'static str;
    type Error = std::convert::Infallible;

    fn status(
        &mut self,
        _entry: &gix_index::Entry,
        rela_path: &BStr,
    ) -> Result<Option<&'static str>, Self::Error> {
        self.seen.lock().expect("uncontended").push(rela_path.to_owned());
        Ok(Some("dirty"))
    }
}

// ------------------------------------------------------------------- context

/// An attribute stack rooted at `root` with no attribute sources configured.
pub fn attr_stack(root: &Path) -> gix_worktree::Stack {
    let attributes = gix_worktree::stack::state::Attributes::new(
        Default::default(),
        None,
        gix_worktree::stack::state::attributes::Source::WorktreeThenIdMapping,
        Default::default(),
    );
    gix_worktree::Stack::new(
        root.to_owned(),
        gix_worktree::stack::State::AttributesStack(attributes),
        gix_worktree::glob::pattern::Case::Sensitive,
        Vec::new(),
        Vec::new(),
    )
}

/// An empty pathspec search, i.e. one that matches every path.
pub fn all_paths() -> gix_pathspec::Search {
    gix_pathspec::Search::from_specs(None, None, Path::new("")).expect("no specs is valid")
}

/// A pathspec search built from `patterns`.
pub fn pathspecs(patterns: &[&str]) -> gix_pathspec::Search {
    let parsed: Vec<_> = patterns
        .iter()
        .map(|p| gix_pathspec::parse(p.as_bytes(), Default::default()).expect("valid pathspec"))
        .collect();
    gix_pathspec::Search::from_specs(parsed, None, Path::new("")).expect("valid search")
}

/// A `Context` over `root` that matches every path.
pub fn ctx<'a>(root: &Path, interrupt: &'a AtomicBool) -> Context<'a> {
    ctx_with(root, interrupt, all_paths())
}

/// A `Context` over `root` restricted by `pathspec`.
pub fn ctx_with<'a>(root: &Path, interrupt: &'a AtomicBool, pathspec: gix_pathspec::Search) -> Context<'a> {
    Context {
        pathspec,
        stack: attr_stack(root),
        filter: gix_filter::Pipeline::default(),
        should_interrupt: interrupt,
    }
}

// ------------------------------------------------------------------- running

/// One reported status, reduced to the path and the status itself.
pub type Reported<T = (), U = ()> = (BString, EntryStatus<T, U>);

/// Run `index_as_worktree` with `FastEq` and `NoSubmodules`, returning the
/// reported statuses sorted by path together with the outcome.
pub fn run(index: &gix_index::State, root: &Path, odb: Odb, options: Options) -> (Vec<Reported>, Outcome) {
    run_with(index, root, odb, options, all_paths())
}

/// Like [`run`], but with an explicit pathspec search.
pub fn run_with(
    index: &gix_index::State,
    root: &Path,
    odb: Odb,
    options: Options,
    pathspec: gix_pathspec::Search,
) -> (Vec<Reported>, Outcome) {
    let interrupt = AtomicBool::default();
    let mut recorder: Recorder<'_, (), ()> = Recorder { records: Vec::new() };
    let mut progress = gix_features::progress::Discard;
    let outcome = gix_status::index_as_worktree(
        index,
        root,
        &mut recorder,
        FastEq,
        NoSubmodules,
        odb,
        &mut progress,
        ctx_with(root, &interrupt, pathspec),
        options,
    )
    .expect("the fixtures never provoke an error");
    (sorted(recorder), outcome)
}

/// Run `index_as_worktree` with a caller-chosen comparison and submodule
/// delegate.
pub fn run_delegating<T, U, E>(
    index: &gix_index::State,
    root: &Path,
    odb: Odb,
    options: Options,
    compare: impl gix_status::index_as_worktree::traits::CompareBlobs<Output = T> + Send + Clone,
    submodule: impl SubmoduleStatus<Output = U, Error = E> + Send + Clone,
) -> (Vec<Reported<T, U>>, Outcome)
where
    T: Send,
    U: Send,
    E: std::error::Error + Send + Sync + 'static,
{
    let interrupt = AtomicBool::default();
    let mut recorder: Recorder<'_, T, U> = Recorder { records: Vec::new() };
    let mut progress = gix_features::progress::Discard;
    let outcome = gix_status::index_as_worktree(
        index,
        root,
        &mut recorder,
        compare,
        submodule,
        odb,
        &mut progress,
        ctx(root, &interrupt),
        options,
    )
    .expect("the fixtures never provoke an error");
    (sorted(recorder), outcome)
}

/// Run `index_as_worktree` with `Context::should_interrupt` already set, so the
/// operation is asked to stop before it has looked at anything.
pub fn run_interrupted(
    index: &gix_index::State,
    root: &Path,
    odb: Odb,
    options: Options,
) -> (Vec<Reported>, Outcome) {
    let interrupt = AtomicBool::new(true);
    let mut recorder: Recorder<'_, (), ()> = Recorder { records: Vec::new() };
    let mut progress = gix_features::progress::Discard;
    let outcome = gix_status::index_as_worktree(
        index,
        root,
        &mut recorder,
        FastEq,
        NoSubmodules,
        odb,
        &mut progress,
        ctx(root, &interrupt),
        options,
    )
    .expect("an interrupt is not an error");
    (sorted(recorder), outcome)
}

fn sorted<T, U>(recorder: Recorder<'_, T, U>) -> Vec<Reported<T, U>> {
    let mut out: Vec<_> = recorder
        .records
        .into_iter()
        .map(|record| (record.relative_path.to_owned(), record.status))
        .collect();
    out.sort_by(|a, b| a.0.cmp(&b.0));
    out
}

/// The paths of the reported statuses, in order.
pub fn paths<T, U>(reported: &[Reported<T, U>]) -> Vec<String> {
    reported.iter().map(|(p, _)| p.to_string()).collect()
}

// ------------------------------------------------------------------- fixture

/// A temporary working tree plus the index and object database describing it.
pub struct Fixture {
    pub dir: tempfile::TempDir,
    pub odb: Odb,
    pub index: gix_index::State,
}

impl Default for Fixture {
    fn default() -> Self {
        Self::new()
    }
}

impl Fixture {
    pub fn new() -> Self {
        Fixture {
            dir: tempfile::tempdir().expect("a writable temporary directory"),
            odb: Odb::new(),
            index: gix_index::State::new(gix_hash::Kind::Sha1),
        }
    }

    pub fn root(&self) -> &Path {
        self.dir.path()
    }

    /// Write `content` to the worktree at `rela` and stamp it with [`PAST`].
    pub fn write(&self, rela: &str, content: &[u8]) -> PathBuf {
        let path = self.root().join(rela);
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent).expect("mkdir");
        }
        std::fs::write(&path, content).expect("write");
        self.stamp(rela);
        path
    }

    /// Reset the mtime of an existing worktree file to [`PAST`].
    pub fn stamp(&self, rela: &str) {
        filetime::set_file_mtime(
            self.root().join(rela),
            filetime::FileTime::from_unix_time(PAST, 0),
        )
        .expect("set mtime");
    }

    /// The symlink-metadata of a worktree path as an index `Stat`.
    pub fn stat_of(&self, rela: &str) -> Stat {
        let metadata = gix_index::fs::Metadata::from_path_no_follow(&self.root().join(rela))
            .expect("the path exists");
        Stat::from_fs(&metadata).expect("stat fits into the index representation")
    }

    /// A tracked file whose worktree content equals its index content: clean.
    pub fn track_clean(&mut self, rela: &str, content: &[u8]) -> ObjectId {
        self.write(rela, content);
        let id = self.odb.insert_blob(content);
        let stat = self.stat_of(rela);
        self.push(rela, stat, id, Flags::empty(), Mode::FILE);
        id
    }

    /// A tracked file recorded as `index_content` but holding
    /// `worktree_content` on disk.
    ///
    /// The recorded stat describes the *index* content: capturing the on-disk
    /// stat after writing the worktree content would make the entry look clean
    /// and silently defeat the test.
    pub fn track_modified(&mut self, rela: &str, index_content: &[u8], worktree_content: &[u8]) -> ObjectId {
        self.write(rela, worktree_content);
        let id = self.odb.insert_blob(index_content);
        self.odb.insert_blob(worktree_content);
        let mut stat = self.stat_of(rela);
        stat.size = index_content.len() as u32;
        stat.mtime.secs = (PAST - 100) as u32;
        self.push(rela, stat, id, Flags::empty(), Mode::FILE);
        id
    }

    /// A tracked file that is missing from the worktree entirely.
    pub fn track_absent(&mut self, rela: &str, content: &[u8]) -> ObjectId {
        let id = self.odb.insert_blob(content);
        self.push(rela, Stat::default(), id, Flags::empty(), Mode::FILE);
        id
    }

    /// A tracked file whose recorded stat is accurate but stale in `mtime`, so
    /// the entry is neither clean by stat nor actually modified.
    pub fn track_stale_stat(&mut self, rela: &str, content: &[u8]) -> ObjectId {
        self.write(rela, content);
        let id = self.odb.insert_blob(content);
        let mut stat = self.stat_of(rela);
        stat.mtime.secs = (PAST - 500) as u32;
        self.push(rela, stat, id, Flags::empty(), Mode::FILE);
        id
    }

    /// A tracked file that is racily clean: the index timestamp is not newer
    /// than the file's mtime, so stat data alone cannot decide.
    ///
    /// The caller must finish the fixture with [`Fixture::finish_racy`].
    pub fn track_racy(&mut self, rela: &str, index_content: &[u8], worktree_content: &[u8]) -> ObjectId {
        self.write(rela, worktree_content);
        let id = self.odb.insert_blob(index_content);
        self.odb.insert_blob(worktree_content);
        // The stat matches what is on disk, so only the racy rule can force a
        // content comparison.
        let stat = self.stat_of(rela);
        self.push(rela, stat, id, Flags::empty(), Mode::FILE);
        id
    }

    /// A tracked path whose index entry describes a file but whose worktree
    /// holds a directory of that name.
    pub fn track_dir_in_place_of_file(&mut self, rela: &str, index_content: &[u8]) -> ObjectId {
        std::fs::create_dir_all(self.root().join(rela)).expect("mkdir");
        let id = self.odb.insert_blob(index_content);
        self.push(rela, Stat::default(), id, Flags::empty(), Mode::FILE);
        id
    }

    /// A tracked path whose index entry describes a file but whose worktree
    /// holds a symbolic link of that name.
    pub fn track_symlink_in_place_of_file(&mut self, rela: &str, target: &str) -> ObjectId {
        std::os::unix::fs::symlink(target, self.root().join(rela)).expect("symlink");
        let id = self.odb.insert_blob(target.as_bytes());
        self.push(rela, Stat::default(), id, Flags::empty(), Mode::FILE);
        id
    }

    /// A tracked file whose content is byte-identical to the index but whose
    /// executable bit is set on disk while the index records a plain file.
    ///
    /// The stat is captured after the `chmod` so that nothing but the mode can
    /// account for a difference.
    pub fn track_executable_flip(&mut self, rela: &str, content: &[u8]) -> ObjectId {
        let path = self.write(rela, content);
        let id = self.odb.insert_blob(content);
        std::fs::set_permissions(&path, std::os::unix::fs::PermissionsExt::from_mode(0o755))
            .expect("chmod");
        self.stamp(rela);
        let stat = self.stat_of(rela);
        self.push(rela, stat, id, Flags::empty(), Mode::FILE);
        id
    }

    /// A tracked file carrying `flags`, whose worktree content differs from the
    /// index content so that anything other than a skip is observable.
    pub fn track_flagged(
        &mut self,
        rela: &str,
        index_content: &[u8],
        worktree_content: &[u8],
        flags: Flags,
    ) -> ObjectId {
        self.write(rela, worktree_content);
        let id = self.odb.insert_blob(index_content);
        self.push(rela, Stat::default(), id, flags, Mode::FILE);
        id
    }

    /// A submodule entry: `Mode::COMMIT` in the index with a directory on disk.
    pub fn track_submodule(&mut self, rela: &str) -> ObjectId {
        std::fs::create_dir_all(self.root().join(rela)).expect("mkdir");
        let id = self.odb.insert_blob(b"");
        self.push(rela, Stat::default(), id, Flags::empty(), Mode::COMMIT);
        id
    }

    /// A conflicted path with one index entry per stage in `stages`, where `1`
    /// is the merge base, `2` is ours and `3` is theirs.
    ///
    /// The worktree holds a plain file at that path, so the conflict -- not a
    /// missing file -- is what the run has to report.
    pub fn track_conflict(&mut self, rela: &str, stages: &[u8]) -> Vec<ObjectId> {
        self.write(rela, b"conflicting\n");
        stages
            .iter()
            .map(|raw| {
                let id = self.odb.insert_blob(format!("stage{raw}\n").as_bytes());
                let stage = match raw {
                    1 => Stage::Base,
                    2 => Stage::Ours,
                    _ => Stage::Theirs,
                };
                self.push(rela, Stat::default(), id, Flags::from_stage(stage), Mode::FILE);
                id
            })
            .collect()
    }

    /// Push a raw entry.
    pub fn push(&mut self, rela: &str, stat: Stat, id: ObjectId, flags: Flags, mode: Mode) {
        self.index.dangerously_push_entry(stat, id, flags, mode, rela.into());
    }

    /// Sort the entries and stamp the index with [`INDEX_TS`].
    pub fn finish(mut self) -> Self {
        self.index.sort_entries();
        self.index
            .set_timestamp(filetime::FileTime::from_unix_time(INDEX_TS, 0));
        self
    }

    /// Sort the entries and stamp the index with [`PAST`], which is exactly the
    /// mtime of every fixture file, making every entry racily clean.
    pub fn finish_racy(mut self) -> Self {
        self.index.sort_entries();
        self.index
            .set_timestamp(filetime::FileTime::from_unix_time(PAST, 0));
        self
    }
}
