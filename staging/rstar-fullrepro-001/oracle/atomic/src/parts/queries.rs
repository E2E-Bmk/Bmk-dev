// Spatial queries: point location (exact equality for bare points), box
// containment vs intersection, inclusive metric filter, internal iteration
// with ControlFlow, custom selection functions, cross-tree candidates.

fn corners_tree() -> RTree<[f64; 2]> {
    RTree::bulk_load(vec![
        [0.0, 0.0], [2.0, 0.0], [0.0, 2.0], [2.0, 2.0], [1.0, 1.0], [5.0, 5.0],
    ])
}

#[test]
fn generated_locate_at_point_exact_equality() {
    let tree = corners_tree();
    assert_eq!(tree.locate_at_point(&[1.0, 1.0]), Some(&[1.0, 1.0]));
    // A numerically distinct query point matches nothing:
    assert_eq!(tree.locate_at_point(&[1.0, 1.0001]), None);
    assert_eq!(tree.locate_at_point(&[0.5, 0.5]), None);
}

#[test]
fn generated_locate_all_at_point_with_duplicates() {
    let mut tree = corners_tree();
    tree.insert([1.0, 1.0]);
    tree.insert([1.0, 1.0]);
    assert_eq!(tree.locate_all_at_point(&[1.0, 1.0]).count(), 3);
    assert_eq!(tree.locate_all_at_point(&[9.0, 9.0]).count(), 0);
}

#[test]
fn generated_locate_at_point_mut_updates_payload() {
    type Cell = GeomWithData<[f64; 2], &'static str>;
    let mut tree = RTree::bulk_load(vec![
        Cell::new([0.0, 0.0], "old"),
        Cell::new([3.0, 3.0], "other"),
    ]);
    tree.locate_at_point_mut(&[0.0, 0.0]).unwrap().data = "new";
    assert_eq!(tree.locate_at_point(&[0.0, 0.0]).unwrap().data, "new");
    assert_eq!(tree.locate_at_point(&[3.0, 3.0]).unwrap().data, "other");
}

#[test]
fn generated_locate_in_envelope_inclusive_corners() {
    let tree = corners_tree();
    let unit = AABB::from_corners([0.0, 0.0], [2.0, 2.0]);
    // all four corner points and the center are contained; [5,5] is not
    assert_eq!(tree.locate_in_envelope(&unit).count(), 5);
    let shifted = AABB::from_corners([0.5, 0.5], [2.0, 2.0]);
    let found = sorted(tree.locate_in_envelope(&shifted).copied().collect());
    assert_eq!(found, vec![[1.0, 1.0], [2.0, 2.0]]);
}

#[test]
fn generated_locate_in_envelope_intersecting_includes_touch() {
    let lines = vec![
        Line::new([0.0, 0.0], [2.0, 2.0]),
        Line::new([2.0, 2.0], [4.0, 4.0]),
        Line::new([5.0, 5.0], [6.0, 6.0]),
    ];
    let tree = RTree::bulk_load(lines);
    let probe = AABB::from_corners([0.0, 0.0], [2.0, 2.0]);
    // fully inside counts, touching at [2,2] counts, disjoint does not:
    assert_eq!(tree.locate_in_envelope_intersecting(&probe).count(), 2);
    assert_eq!(tree.locate_in_envelope(&probe).count(), 1);
}

#[test]
fn generated_locate_within_distance_inclusive() {
    let tree = corners_tree();
    // squared distances from origin: 0, 4, 4, 8, 2, 50
    assert_eq!(tree.locate_within_distance([0.0, 0.0], 2.0).count(), 2);
    assert_eq!(tree.locate_within_distance([0.0, 0.0], 4.0).count(), 4); // boundary in
    assert_eq!(tree.locate_within_distance([0.0, 0.0], 3.9999).count(), 2);
    let hits = sorted(tree.locate_within_distance([0.0, 0.0], 2.0).copied().collect());
    assert_eq!(hits, vec![[0.0, 0.0], [1.0, 1.0]]);
}

#[test]
fn generated_internal_iteration_break_and_continue() {
    let tree = corners_tree();
    let unit = AABB::from_corners([0.0, 0.0], [2.0, 2.0]);
    // Continue through every selected element:
    let mut visited = 0;
    let flow: ControlFlow<()> = tree.locate_in_envelope_int(&unit, |_| {
        visited += 1;
        ControlFlow::Continue(())
    });
    assert_eq!(flow, ControlFlow::Continue(()));
    assert_eq!(visited, 5);
    // Break stops the traversal and carries the value out:
    let mut seen_before_break = 0;
    let flow = tree.locate_in_envelope_int(&unit, |p| {
        seen_before_break += 1;
        if p == &[1.0, 1.0] || seen_before_break == 3 {
            ControlFlow::Break(*p)
        } else {
            ControlFlow::Continue(())
        }
    });
    assert!(matches!(flow, ControlFlow::Break(_)));
    assert!(seen_before_break <= 3);
}

#[test]
fn generated_locate_at_point_int_returns_option() {
    let tree = corners_tree();
    assert_eq!(tree.locate_at_point_int(&[5.0, 5.0]), Some(&[5.0, 5.0]));
    assert_eq!(tree.locate_at_point_int(&[4.0, 4.0]), None);
}

struct LeftOf {
    limit: f64,
}

impl SelectionFunction<[f64; 2]> for LeftOf {
    fn should_unpack_parent(&self, envelope: &AABB<[f64; 2]>) -> bool {
        envelope.lower()[0] <= self.limit
    }
    fn should_unpack_leaf(&self, leaf: &[f64; 2]) -> bool {
        leaf[0] <= self.limit
    }
}

#[test]
fn generated_custom_selection_function() {
    let tree = corners_tree();
    let found = sorted(
        tree.locate_with_selection_function(LeftOf { limit: 1.0 }).copied().collect(),
    );
    assert_eq!(found, vec![[0.0, 0.0], [0.0, 2.0], [1.0, 1.0]]);
}

#[test]
fn generated_custom_selection_function_mut() {
    type Cell = GeomWithData<[f64; 2], u32>;
    struct All;
    impl SelectionFunction<Cell> for All {
        fn should_unpack_parent(&self, _envelope: &AABB<[f64; 2]>) -> bool {
            true
        }
    }
    let mut tree = RTree::bulk_load(vec![
        Cell::new([0.0, 0.0], 1),
        Cell::new([4.0, 4.0], 2),
    ]);
    // Default leaf hook accepts every leaf; mutate all payloads:
    for cell in tree.locate_with_selection_function_mut(All) {
        cell.data += 100;
    }
    let mut tags: Vec<u32> = tree.iter().map(|c| c.data).collect();
    tags.sort();
    assert_eq!(tags, vec![101, 102]);
}

#[test]
fn generated_intersection_candidates_same_type() {
    let a = RTree::bulk_load(vec![[0.0, 0.0], [1.0, 1.0], [9.0, 9.0]]);
    let b = RTree::bulk_load(vec![[1.0, 1.0], [9.0, 9.0], [4.0, 4.0]]);
    // Point envelopes are zero-extent, so pairs form only on exact matches:
    let pairs: Vec<([f64; 2], [f64; 2])> = a
        .intersection_candidates_with_other_tree(&b)
        .map(|(x, y)| (*x, *y))
        .collect();
    let mut pairs = pairs;
    pairs.sort_by(|p, q| p.partial_cmp(q).unwrap());
    assert_eq!(pairs, vec![([1.0, 1.0], [1.0, 1.0]), ([9.0, 9.0], [9.0, 9.0])]);
}

#[test]
fn generated_intersection_candidates_cross_type() {
    let points = RTree::bulk_load(vec![[0.5, 0.5], [3.5, 3.5]]);
    let rects = RTree::bulk_load(vec![
        Rectangle::from_corners([0.0, 0.0], [1.0, 1.0]),
        Rectangle::from_corners([2.0, 2.0], [3.0, 3.0]),
    ]);
    // Trees over different element types cooperate when they share an
    // envelope type; only [0.5, 0.5] lands inside a rectangle envelope.
    let pairs: Vec<[f64; 2]> = points
        .intersection_candidates_with_other_tree(&rects)
        .map(|(p, _r)| *p)
        .collect();
    assert_eq!(pairs, vec![[0.5, 0.5]]);
}
