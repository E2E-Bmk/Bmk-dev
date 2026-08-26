// Oracle integration tests for the ignore rules and directory walking library
#![cfg(test)]
#![allow(clippy::all)]

use std::fs;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::{Arc, Mutex};

use ignore::{Match, WalkBuilder, WalkState};

static NEXT_FIXTURE: AtomicUsize = AtomicUsize::new(0);

/// A unique temporary directory tree, removed on drop.
struct TreeFixture {
    root: PathBuf,
}

impl TreeFixture {
    fn new(tag: &str) -> TreeFixture {
        let n = NEXT_FIXTURE.fetch_add(1, Ordering::SeqCst);
        let root = std::env::temp_dir()
            .join(format!("oracle_ig_i_{}_{}_{}", tag, std::process::id(), n));
        let _ = fs::remove_dir_all(&root);
        fs::create_dir_all(&root).unwrap();
        TreeFixture { root }
    }

    fn file(&self, rel: &str, contents: &str) -> &Self {
        let p = self.root.join(rel);
        if let Some(parent) = p.parent() {
            fs::create_dir_all(parent).unwrap();
        }
        fs::write(p, contents).unwrap();
        self
    }

    fn dir(&self, rel: &str) -> &Self {
        fs::create_dir_all(self.root.join(rel)).unwrap();
        self
    }

    fn path(&self) -> &Path {
        &self.root
    }
}

impl Drop for TreeFixture {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.root);
    }
}

fn rel_name(root: &Path, p: &Path) -> String {
    let s = p
        .strip_prefix(root)
        .expect("entry outside root")
        .to_string_lossy()
        .replace('\\', "/");
    if s.is_empty() {
        ".".to_string()
    } else {
        s
    }
}

/// Collect the serial walk as sorted root-relative names ("." for the root).
fn walk_sorted(wb: &WalkBuilder, root: &Path) -> Vec<String> {
    let mut out: Vec<String> = wb
        .build()
        .map(|r| r.expect("unexpected walk error"))
        .map(|e| rel_name(root, e.path()))
        .collect();
    out.sort();
    out
}

/// Collect the parallel walk as sorted root-relative names.
fn parallel_sorted(wb: &WalkBuilder, root: &Path) -> Vec<String> {
    let got: Arc<Mutex<Vec<String>>> = Arc::new(Mutex::new(Vec::new()));
    let rootbuf = root.to_path_buf();
    wb.build_parallel().run(|| {
        let got = Arc::clone(&got);
        let rootbuf = rootbuf.clone();
        Box::new(move |result| {
            let entry = result.expect("unexpected walk error");
            got.lock().unwrap().push(rel_name(&rootbuf, entry.path()));
            WalkState::Continue
        })
    });
    let mut v = got.lock().unwrap().clone();
    v.sort();
    v
}

fn names(v: &[&str]) -> Vec<String> {
    let mut out: Vec<String> = v.iter().map(|s| s.to_string()).collect();
    out.sort();
    out
}

/// Collapse a verdict to a comparable kind: 0 = none, 1 = ignore, 2 = whitelist.
fn kind<T>(m: &Match<T>) -> u8 {
    if m.is_ignore() {
        1
    } else if m.is_whitelist() {
        2
    } else {
        0
    }
}

include!("all/precedence.rs");
include!("all/matcher_walk.rs");
include!("all/override_types.rs");
include!("all/parallel.rs");
include!("all/limits_sorting.rs");
