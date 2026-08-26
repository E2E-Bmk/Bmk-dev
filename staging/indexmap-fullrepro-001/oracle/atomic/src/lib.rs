// Oracle atomic tests for the order-preserving map and set
#![cfg(test)]
#![allow(clippy::all)]

use indexmap::map::Entry;
use indexmap::{indexmap, indexset, Equivalent, IndexMap, IndexSet};
use std::hash::{Hash, Hasher};

fn base() -> IndexMap<&'static str, i32> {
    [("a", 1), ("b", 2), ("c", 3), ("d", 4), ("e", 5)]
        .into_iter()
        .collect()
}

fn key_list(m: &IndexMap<&'static str, i32>) -> Vec<&'static str> {
    m.keys().copied().collect()
}

fn catches<F: FnOnce() + std::panic::UnwindSafe>(f: F) -> bool {
    let hook = std::panic::take_hook();
    std::panic::set_hook(Box::new(|_| {}));
    let r = std::panic::catch_unwind(f).is_err();
    std::panic::set_hook(hook);
    r
}

/// Value with identity: equality and hashing use `id` only, `tag`
/// distinguishes instances so identity laws are observable.
#[derive(Debug, Clone, Copy)]
struct Ver {
    id: u8,
    tag: u8,
}
impl PartialEq for Ver {
    fn eq(&self, other: &Self) -> bool {
        self.id == other.id
    }
}
impl Eq for Ver {}
impl Hash for Ver {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.id.hash(state);
    }
}
fn ver(id: u8, tag: u8) -> Ver {
    Ver { id, tag }
}

include!("parts/construction.rs");
include!("parts/lookup.rs");
include!("parts/removal.rs");
include!("parts/reorder.rs");
include!("parts/bulk.rs");
include!("parts/sorting.rs");
include!("parts/slices.rs");
include!("parts/entry.rs");
include!("parts/set_basic.rs");
include!("parts/set_algebra.rs");
include!("parts/iteration.rs");
