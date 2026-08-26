// Nearest-neighbor queries: single results, tie sets, nondecreasing
// distance iteration, per-element distance agreement, destructive popping.

#[test]
fn generated_nearest_neighbor_basic_and_empty() {
    let tree = RTree::bulk_load(vec![[0.0, 0.0], [2.0, 0.0], [5.0, 5.0]]);
    assert_eq!(tree.nearest_neighbor(&[4.0, 4.0]), Some(&[5.0, 5.0]));
    assert_eq!(tree.nearest_neighbor(&[0.1, 0.0]), Some(&[0.0, 0.0]));
    let empty: RTree<[f64; 2]> = RTree::new();
    assert_eq!(empty.nearest_neighbor(&[0.0, 0.0]), None);
}

#[test]
fn generated_nearest_neighbor_tie_returns_member() {
    let ring = vec![[1.0, 0.0], [-1.0, 0.0], [0.0, 1.0], [0.0, -1.0]];
    let tree = RTree::bulk_load(ring.clone());
    let hit = *tree.nearest_neighbor(&[0.0, 0.0]).unwrap();
    assert!(ring.contains(&hit));
}

#[test]
fn generated_nearest_neighbors_full_tie_set() {
    let mut elements = vec![[1.0, 0.0], [-1.0, 0.0], [0.0, 1.0], [0.0, -1.0]];
    elements.push([3.0, 3.0]); // farther, must not appear
    let tree = RTree::bulk_load(elements);
    let ties = sorted(tree.nearest_neighbors(&[0.0, 0.0]).into_iter().copied().collect());
    assert_eq!(ties, vec![[-1.0, 0.0], [0.0, -1.0], [0.0, 1.0], [1.0, 0.0]]);
    let empty: RTree<[f64; 2]> = RTree::new();
    assert!(empty.nearest_neighbors(&[0.0, 0.0]).is_empty());
}

#[test]
fn generated_nearest_neighbors_construction_independent() {
    let elements = vec![[2.0, 0.0], [0.0, 2.0], [-2.0, 0.0], [5.0, 5.0]];
    let bulk = RTree::bulk_load(elements.clone());
    let mut incremental = RTree::new();
    for e in &elements {
        incremental.insert(*e);
    }
    let from_bulk = sorted(bulk.nearest_neighbors(&[0.0, 0.0]).into_iter().copied().collect());
    let from_inc =
        sorted(incremental.nearest_neighbors(&[0.0, 0.0]).into_iter().copied().collect());
    assert_eq!(from_bulk, from_inc);
    assert_eq!(from_bulk, vec![[-2.0, 0.0], [0.0, 2.0], [2.0, 0.0]]);
}

#[test]
fn generated_nearest_neighbor_iter_nondecreasing() {
    let tree = RTree::bulk_load(vec![[3.0, 4.0], [1.0, 1.0], [0.0, 2.0], [5.0, 0.0]]);
    let distances: Vec<f64> = tree
        .nearest_neighbor_iter_with_distance_2(&[0.0, 0.0])
        .map(|(_, d)| d)
        .collect();
    assert_eq!(distances, vec![2.0, 4.0, 25.0, 25.0]);
    // every stored element appears exactly once:
    assert_eq!(tree.nearest_neighbor_iter(&[0.0, 0.0]).count(), 4);
}

#[test]
fn generated_nearest_neighbor_iter_distance_agrees() {
    let tree = RTree::bulk_load(vec![[1.0, 2.0], [4.0, 4.0], [-3.0, 1.0]]);
    let query = [1.0, 0.0];
    for (element, reported) in tree.nearest_neighbor_iter_with_distance_2(&query) {
        assert_eq!(reported, element.distance_2(&query));
    }
    // first yielded distance matches the single-result query:
    let first = tree.nearest_neighbor_iter_with_distance_2(&query).next().unwrap();
    assert_eq!(first.1, tree.nearest_neighbor(&query).unwrap().distance_2(&query));
}

#[test]
fn generated_deprecated_distance_alias_same_contract() {
    let tree = RTree::bulk_load(vec![[0.0, 3.0], [0.0, 1.0], [0.0, 2.0]]);
    #[allow(deprecated)]
    let distances: Vec<f64> = tree
        .nearest_neighbor_iter_with_distance(&[0.0, 0.0])
        .map(|(_, d)| d)
        .collect();
    assert_eq!(distances, vec![1.0, 4.0, 9.0]);
}

#[test]
fn generated_pop_nearest_neighbor_removes_in_order() {
    let mut tree = RTree::bulk_load(vec![[0.0, 1.0], [0.0, 3.0], [0.0, 2.0]]);
    let first = tree.pop_nearest_neighbor(&[0.0, 0.0]).unwrap();
    assert_eq!(first, [0.0, 1.0]);
    assert_eq!(tree.size(), 2);
    assert!(!tree.contains(&[0.0, 1.0]));
    let second = tree.pop_nearest_neighbor(&[0.0, 0.0]).unwrap();
    assert_eq!(second, [0.0, 2.0]);
    let third = tree.pop_nearest_neighbor(&[0.0, 0.0]).unwrap();
    assert_eq!(third, [0.0, 3.0]);
    assert_eq!(tree.pop_nearest_neighbor(&[0.0, 0.0]), None);
    assert_eq!(tree.size(), 0);
}

#[test]
fn generated_pop_nearest_neighbor_tie_removes_one() {
    let mut tree = RTree::bulk_load(vec![[1.0, 0.0], [-1.0, 0.0], [0.0, 6.0]]);
    let popped = tree.pop_nearest_neighbor(&[0.0, 0.0]).unwrap();
    assert!(popped == [1.0, 0.0] || popped == [-1.0, 0.0]);
    assert_eq!(tree.size(), 2);
    // the other tie member is still present:
    let other = if popped == [1.0, 0.0] { [-1.0, 0.0] } else { [1.0, 0.0] };
    assert!(tree.contains(&other));
}
