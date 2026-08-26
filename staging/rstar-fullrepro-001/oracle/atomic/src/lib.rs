// Oracle atomic tests for the R*-tree spatial index
#![cfg(test)]
#![allow(clippy::all)]

use rstar::primitives::{CachedEnvelope, GeomWithData, Line, ObjectRef, PointWithData, Rectangle};
use rstar::{
    Envelope, PointDistance, RStarInsertionStrategy, RTree, RTreeObject, RTreeParams,
    SelectionFunction, AABB,
};
use std::ops::ControlFlow;

/// Sorts a set of 2-d float points into a canonical order for multiset
/// comparison (query iteration order is unspecified).
fn sorted(mut pts: Vec<[f64; 2]>) -> Vec<[f64; 2]> {
    pts.sort_by(|a, b| a.partial_cmp(b).unwrap());
    pts
}

include!("parts/aabb.rs");
include!("parts/construction.rs");
include!("parts/queries.rs");
include!("parts/neighbors.rs");
include!("parts/mutation.rs");
include!("parts/primitives.rs");
include!("parts/inspection.rs");
