// Collision workflows: solid rectangles, cross-tree joins, line networks,
// and wrapper transparency across whole query pipelines.

#[test]
fn generated_rectangle_field_collision() {
    let mut field = RTree::bulk_load(vec![
        Rectangle::from_corners([0.0, 0.0], [2.0, 2.0]),
        Rectangle::from_corners([1.0, 1.0], [3.0, 3.0]),
        Rectangle::from_corners([5.0, 5.0], [6.0, 6.0]),
    ]);
    // point containment goes through the solid-box geometry:
    assert_eq!(field.locate_all_at_point(&[1.5, 1.5]).count(), 2);
    assert_eq!(field.locate_all_at_point(&[2.5, 2.5]).count(), 1);
    assert_eq!(field.locate_all_at_point(&[4.0, 4.0]).count(), 0);
    // a probe region touching a box counts as intersecting:
    let probe = AABB::from_corners([3.0, 3.0], [5.0, 5.0]);
    assert_eq!(field.locate_in_envelope_intersecting(&probe).count(), 2);
    // clear everything that intersects the probe; only the first box survives
    let removed = field.drain_in_envelope_intersecting(probe).count();
    assert_eq!(removed, 2);
    assert_eq!(field.size(), 1);
    assert_eq!(field.locate_all_at_point(&[1.5, 1.5]).count(), 1);
    assert_eq!(
        field.root().envelope(),
        AABB::from_corners([0.0, 0.0], [2.0, 2.0])
    );
}

#[test]
fn generated_cross_tree_candidate_join() {
    let sensors = RTree::bulk_load(vec![
        [0.5, 0.5], [2.5, 0.5], [0.5, 2.5], [4.5, 4.5], [3.0, 3.0],
    ]);
    let zones = RTree::bulk_load(vec![
        Rectangle::from_corners([0.0, 0.0], [1.0, 1.0]),
        Rectangle::from_corners([2.0, 0.0], [3.0, 1.0]),
        Rectangle::from_corners([3.0, 3.0], [4.0, 4.0]),
    ]);
    // the candidate join yields exactly the envelope-intersecting pairs the
    // nested-loop comparison finds:
    let mut joined: Vec<([f64; 2], [f64; 2])> = sensors
        .intersection_candidates_with_other_tree(&zones)
        .map(|(p, r)| (*p, r.lower()))
        .collect();
    joined.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let mut expected = Vec::new();
    for p in sensors.iter() {
        for r in zones.iter() {
            if p.envelope().intersects(&r.envelope()) {
                expected.push((*p, r.lower()));
            }
        }
    }
    expected.sort_by(|a, b| a.partial_cmp(b).unwrap());
    assert_eq!(joined, expected);
    // [3, 3] touches the corner of the third zone — inclusive intersection:
    assert!(joined.contains(&([3.0, 3.0], [3.0, 3.0])));
    assert_eq!(joined.len(), 3);
}

#[test]
fn generated_line_network_routing() {
    let roads = RTree::bulk_load(vec![
        Line::new([0.0, 0.0], [4.0, 0.0]),
        Line::new([4.0, 0.0], [4.0, 4.0]),
        Line::new([0.0, 2.0], [2.0, 2.0]),
    ]);
    // the nearest road is decided by segment distance, not endpoint distance:
    let nearest = roads.nearest_neighbor(&[1.0, 1.5]).unwrap();
    assert_eq!((nearest.from, nearest.to), ([0.0, 2.0], [2.0, 2.0]));
    assert_eq!(nearest.distance_2(&[1.0, 1.5]), 0.25);
    assert_eq!(nearest.nearest_point(&[1.0, 1.5]), [1.0, 2.0]);
    // roads reachable within half a unit (squared bound 0.25, inclusive):
    assert_eq!(roads.locate_within_distance([1.0, 1.5], 0.25).count(), 1);
    // widening the bound picks up the horizontal axis road at d2 = 2.25:
    assert_eq!(roads.locate_within_distance([1.0, 1.5], 2.25).count(), 2);
    // full nondecreasing schedule across the network:
    let d: Vec<f64> = roads
        .nearest_neighbor_iter_with_distance_2(&[1.0, 1.5])
        .map(|(_, d)| d)
        .collect();
    assert_eq!(d, vec![0.25, 2.25, 9.0]);
}

#[test]
fn generated_wrapper_transparency() {
    let lines = vec![
        Line::new([0.0, 0.0], [2.0, 0.0]),
        Line::new([3.0, 1.0], [3.0, 5.0]),
        Line::new([-1.0, -1.0], [-1.0, -3.0]),
    ];
    let plain = RTree::bulk_load(lines.clone());
    let cached = RTree::bulk_load(lines.iter().cloned().map(CachedEnvelope::new).collect());
    let by_ref: RTree<ObjectRef<Line<[f64; 2]>>> =
        RTree::bulk_load(lines.iter().map(ObjectRef::new).collect());
    let q = [1.0, 1.0];
    let d_plain = plain.nearest_neighbor(&q).unwrap().distance_2(&q);
    let d_cached = cached.nearest_neighbor(&q).unwrap().distance_2(&q);
    let d_ref = by_ref.nearest_neighbor(&q).unwrap().distance_2(&q);
    assert_eq!(d_plain, 1.0);
    assert_eq!(d_cached, d_plain);
    assert_eq!(d_ref, d_plain);
    // envelope queries agree across all three storage strategies:
    let probe = AABB::from_corners([-2.0, -4.0], [3.0, 2.0]);
    let n = plain.locate_in_envelope(&probe).count();
    assert_eq!(n, 2);
    assert_eq!(cached.locate_in_envelope(&probe).count(), n);
    assert_eq!(by_ref.locate_in_envelope(&probe).count(), n);
    // and the distance schedules coincide element-for-element:
    let sp: Vec<f64> = plain.nearest_neighbor_iter_with_distance_2(&q).map(|(_, d)| d).collect();
    let sc: Vec<f64> = cached.nearest_neighbor_iter_with_distance_2(&q).map(|(_, d)| d).collect();
    let sr: Vec<f64> = by_ref.nearest_neighbor_iter_with_distance_2(&q).map(|(_, d)| d).collect();
    assert_eq!(sp, sc);
    assert_eq!(sp, sr);
}
