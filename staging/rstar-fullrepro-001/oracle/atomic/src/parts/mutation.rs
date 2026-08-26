// Mutation and removal: one-of-many removal semantics, size bookkeeping,
// the drain family, and drain laziness.

#[test]
fn generated_remove_one_of_many() {
    let mut tree = RTree::bulk_load(vec![[1.0, 1.0], [1.0, 1.0], [1.0, 1.0], [4.0, 4.0]]);
    assert_eq!(tree.remove(&[1.0, 1.0]), Some([1.0, 1.0]));
    assert_eq!(tree.size(), 3);
    assert_eq!(tree.locate_all_at_point(&[1.0, 1.0]).count(), 2);
    assert_eq!(tree.remove(&[1.0, 1.0]), Some([1.0, 1.0]));
    assert_eq!(tree.remove(&[1.0, 1.0]), Some([1.0, 1.0]));
    assert_eq!(tree.remove(&[1.0, 1.0]), None); // exhausted
    assert_eq!(tree.size(), 1);
}

#[test]
fn generated_remove_no_match_leaves_tree_unchanged() {
    let mut tree = RTree::bulk_load(vec![[0.0, 0.0], [2.0, 2.0]]);
    assert_eq!(tree.remove(&[9.0, 9.0]), None);
    assert_eq!(tree.size(), 2);
    assert!(tree.contains(&[0.0, 0.0]));
    assert!(tree.contains(&[2.0, 2.0]));
}

#[test]
fn generated_remove_at_point() {
    let mut tree = RTree::bulk_load(vec![[0.0, 0.0], [2.0, 2.0]]);
    assert_eq!(tree.remove_at_point(&[2.0, 2.0]), Some([2.0, 2.0]));
    assert_eq!(tree.remove_at_point(&[2.0, 2.0]), None);
    assert_eq!(tree.size(), 1);
}

#[test]
fn generated_remove_with_selection_function() {
    let mut tree = RTree::bulk_load(vec![[0.0, 0.0], [1.0, 0.0], [8.0, 8.0]]);
    let removed = tree.remove_with_selection_function(LeftOf { limit: 2.0 }).unwrap();
    assert!(removed == [0.0, 0.0] || removed == [1.0, 0.0]);
    assert_eq!(tree.size(), 2);
    // nothing right of the limit matches:
    let mut only_right = RTree::bulk_load(vec![[8.0, 8.0]]);
    assert_eq!(only_right.remove_with_selection_function(LeftOf { limit: 2.0 }), None);
}

#[test]
fn generated_drain_everything() {
    let mut tree = RTree::bulk_load(vec![[0.0, 1.0], [2.0, 3.0], [4.0, 5.0]]);
    let drained = sorted(tree.drain().collect());
    assert_eq!(drained, vec![[0.0, 1.0], [2.0, 3.0], [4.0, 5.0]]);
    assert_eq!(tree.size(), 0);
}

#[test]
fn generated_drain_in_envelope_only_contained() {
    let mut tree = RTree::bulk_load(vec![[0.0, 0.0], [1.0, 1.0], [2.0, 2.0], [5.0, 5.0]]);
    let unit = AABB::from_corners([0.0, 0.0], [2.0, 2.0]);
    let drained = sorted(tree.drain_in_envelope(unit).collect());
    assert_eq!(drained, vec![[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]]);
    assert_eq!(tree.size(), 1);
    assert!(tree.contains(&[5.0, 5.0]));
}

#[test]
fn generated_drain_in_envelope_intersecting() {
    let mut tree = RTree::bulk_load(vec![
        Line::new([0.0, 0.0], [1.0, 1.0]),
        Line::new([2.0, 2.0], [4.0, 4.0]), // touches the box corner
        Line::new([5.0, 5.0], [6.0, 6.0]),
    ]);
    let probe = AABB::from_corners([0.0, 0.0], [2.0, 2.0]);
    let drained = tree.drain_in_envelope_intersecting(probe).count();
    assert_eq!(drained, 2);
    assert_eq!(tree.size(), 1);
}

#[test]
fn generated_drain_within_distance_inclusive() {
    let mut tree = RTree::bulk_load(vec![[0.0, 0.0], [2.0, 0.0], [0.0, 2.0], [3.0, 3.0]]);
    // squared distances: 0, 4, 4, 18 — the boundary at 4 is drained too
    let drained = tree.drain_within_distance([0.0, 0.0], 4.0).count();
    assert_eq!(drained, 3);
    assert_eq!(tree.size(), 1);
    assert!(tree.contains(&[3.0, 3.0]));
}

#[test]
fn generated_drain_is_lazy() {
    let mut tree = RTree::bulk_load(vec![[0.0, 0.0], [1.0, 0.0], [2.0, 0.0], [9.0, 9.0]]);
    let selected = AABB::from_corners([0.0, 0.0], [2.0, 0.0]);
    let drained_first;
    {
        let mut it = tree.drain_in_envelope(selected);
        drained_first = it.next();
        // iterator dropped here after yielding exactly one element
    }
    let first = drained_first.unwrap();
    assert_eq!(tree.size(), 3);
    assert!(!tree.contains(&first));
    // the other two selected elements survived the partial drain:
    assert_eq!(tree.locate_in_envelope(&selected).count(), 2);
    assert!(tree.contains(&[9.0, 9.0]));
}

#[test]
fn generated_drain_with_selection_function() {
    let mut tree = RTree::bulk_load(vec![[0.0, 0.0], [1.0, 5.0], [7.0, 0.0], [8.0, 8.0]]);
    let drained = sorted(tree.drain_with_selection_function(LeftOf { limit: 1.0 }).collect());
    assert_eq!(drained, vec![[0.0, 0.0], [1.0, 5.0]]);
    assert_eq!(tree.size(), 2);
}
