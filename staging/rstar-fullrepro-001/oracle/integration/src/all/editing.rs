// Editing workflows: cross-view bookkeeping through insert/remove
// sequences, partial drains, failed removals, and destructive scheduling.

fn count_leaves(node: &rstar::ParentNode<[f64; 2]>) -> usize {
    node.children()
        .iter()
        .map(|c| match c {
            rstar::RTreeNode::Leaf(_) => 1,
            rstar::RTreeNode::Parent(p) => count_leaves(p),
        })
        .sum()
}

#[test]
fn generated_insert_remove_lifecycle_consistency() {
    let mut tree = RTree::new();
    // size, external iteration, and the structural leaf count must agree
    // after every step of an editing session:
    let check = |tree: &RTree<[f64; 2]>, expected: usize| {
        assert_eq!(tree.size(), expected);
        assert_eq!(tree.iter().count(), expected);
        assert_eq!(count_leaves(tree.root()), expected);
    };
    check(&tree, 0);
    for i in 0..12 {
        tree.insert([(i % 4) as f64, (i / 4) as f64]);
    }
    check(&tree, 12);
    tree.insert([1.0, 1.0]); // duplicate of an existing grid point
    check(&tree, 13);
    assert_eq!(tree.remove(&[1.0, 1.0]), Some([1.0, 1.0]));
    check(&tree, 12);
    assert_eq!(tree.remove_at_point(&[3.0, 2.0]), Some([3.0, 2.0]));
    check(&tree, 11);
    let drained = tree.drain_in_envelope(AABB::from_corners([0.0, 0.0], [1.0, 2.0])).count();
    assert_eq!(drained, 6);
    check(&tree, 5);
    // every remaining element is still individually locatable:
    for p in tree.iter().copied().collect::<Vec<_>>() {
        assert_eq!(tree.locate_at_point(&p), Some(&p));
    }
}

#[test]
fn generated_partial_drain_bookkeeping() {
    let mut tree = RTree::bulk_load(vec![
        [0.0, 0.0], [1.0, 0.0], [2.0, 0.0], [3.0, 0.0], [10.0, 10.0],
    ]);
    let strip = AABB::from_corners([0.0, 0.0], [3.0, 0.0]);
    let mut yielded = Vec::new();
    {
        let mut it = tree.drain_in_envelope(strip);
        yielded.push(it.next().unwrap());
        yielded.push(it.next().unwrap());
        // dropped after two of four selected elements
    }
    assert_eq!(tree.size(), 3);
    for p in &yielded {
        assert!(!tree.contains(p));
    }
    // the two selected-but-unyielded elements survived:
    assert_eq!(tree.locate_in_envelope(&strip).count(), 2);
    assert!(tree.contains(&[10.0, 10.0]));
    // finishing the drain later removes exactly the remainder:
    let rest: Vec<[f64; 2]> = tree.drain_in_envelope(strip).collect();
    assert_eq!(rest.len(), 2);
    assert_eq!(tree.size(), 1);
    let mut all = yielded;
    all.extend(rest);
    assert_eq!(
        sorted(all),
        vec![[0.0, 0.0], [1.0, 0.0], [2.0, 0.0], [3.0, 0.0]]
    );
}

#[test]
fn generated_failed_removal_leaves_state() {
    let elements = vec![[0.0, 0.0], [2.0, 2.0], [4.0, 4.0]];
    let mut tree = RTree::bulk_load(elements.clone());
    let before_iter = sorted(tree.iter().copied().collect());
    let before_envelope = tree.root().envelope();
    let q = [1.0, 1.0];
    let before_schedule: Vec<f64> =
        tree.nearest_neighbor_iter_with_distance_2(&q).map(|(_, d)| d).collect();
    // three failing removals through three different entry points:
    assert_eq!(tree.remove(&[9.0, 9.0]), None);
    assert_eq!(tree.remove_at_point(&[1.0, 3.0]), None);
    struct Nothing;
    impl SelectionFunction<[f64; 2]> for Nothing {
        fn should_unpack_parent(&self, _e: &AABB<[f64; 2]>) -> bool {
            false
        }
    }
    assert_eq!(tree.remove_with_selection_function(Nothing), None);
    // every projection is unchanged:
    assert_eq!(tree.size(), 3);
    assert_eq!(sorted(tree.iter().copied().collect()), before_iter);
    assert_eq!(tree.root().envelope(), before_envelope);
    let after_schedule: Vec<f64> =
        tree.nearest_neighbor_iter_with_distance_2(&q).map(|(_, d)| d).collect();
    assert_eq!(after_schedule, before_schedule);
}

#[test]
fn generated_pop_drain_schedule() {
    let mut tree = RTree::bulk_load(vec![
        [1.0, 0.0], [0.0, 2.0], [3.0, 0.0], [0.0, 4.0], [5.0, 0.0],
    ]);
    let q = [0.0, 0.0];
    let mut schedule = Vec::new();
    while let Some(popped) = tree.pop_nearest_neighbor(&q) {
        schedule.push(popped.distance_2(&q));
    }
    assert_eq!(schedule, vec![1.0, 4.0, 9.0, 16.0, 25.0]);
    assert_eq!(tree.size(), 0);
    assert_eq!(tree.root().envelope(), AABB::new_empty());
    assert_eq!(tree.pop_nearest_neighbor(&q), None);
}
