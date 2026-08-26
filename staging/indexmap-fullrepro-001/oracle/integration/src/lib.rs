// Oracle integration tests: end-to-end workflows over the
// order-preserving map and set.
#![cfg(test)]
#![allow(clippy::all)]

use indexmap::map::Entry;
use indexmap::{indexmap, IndexMap, IndexSet};
use std::hash::{Hash, Hasher};

/// Value with identity: equality and hashing use `id` only, `tag`
/// distinguishes instances so identity laws are observable end-to-end.
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

include!("all/registry.rs");
include!("all/aggregation.rs");
include!("all/dedupe.rs");
include!("all/editing.rs");
