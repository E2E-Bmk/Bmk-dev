// Envelopes and AABB arithmetic: construction/normalization, inclusive
// containment and intersection, merge laws, measures, point distances,
// and value semantics.

#[test]
fn generated_from_point_zero_extent() {
    let b = AABB::from_point([2.0, 3.0]);
    assert_eq!(b.lower(), [2.0, 3.0]);
    assert_eq!(b.upper(), [2.0, 3.0]);
    assert_eq!(b.area(), 0.0);
    assert!(b.contains_point(&[2.0, 3.0]));
    assert!(!b.contains_point(&[2.0, 3.1]));
}

#[test]
fn generated_from_corners_normalizes_in_any_order() {
    let a = AABB::from_corners([3.0, -1.0], [1.0, 4.0]);
    let b = AABB::from_corners([1.0, 4.0], [3.0, -1.0]);
    assert_eq!(a.lower(), [1.0, -1.0]);
    assert_eq!(a.upper(), [3.0, 4.0]);
    assert_eq!(a, b);
}

#[test]
fn generated_from_points_folds_smallest_box() {
    let pts = [[1.0, 1.0], [4.0, 5.0], [2.0, -2.0]];
    let b = AABB::<[f64; 2]>::from_points(pts.iter());
    assert_eq!(b.lower(), [1.0, -2.0]);
    assert_eq!(b.upper(), [4.0, 5.0]);
}

#[test]
fn generated_from_points_empty_equals_new_empty() {
    let none: [[f64; 2]; 0] = [];
    let b = AABB::<[f64; 2]>::from_points(none.iter());
    assert_eq!(b, AABB::<[f64; 2]>::new_empty());
}

#[test]
fn generated_new_empty_merge_identity() {
    let empty = AABB::<[f64; 2]>::new_empty();
    assert_eq!(empty.area(), 0.0);
    assert!(!empty.contains_point(&[0.0, 0.0]));
    let b = AABB::from_corners([-2.0, 1.0], [5.0, 3.0]);
    assert_eq!(empty.merged(&b), b);
}

#[test]
fn generated_contains_point_inclusive_boundaries() {
    let b = AABB::from_corners([0.0, 0.0], [2.0, 2.0]);
    assert!(b.contains_point(&[1.0, 1.0])); // interior
    assert!(b.contains_point(&[2.0, 2.0])); // corner
    assert!(b.contains_point(&[0.0, 1.0])); // face
    assert!(!b.contains_point(&[2.1, 1.0]));
}

#[test]
fn generated_contains_envelope_boundaries_included() {
    let outer = AABB::from_corners([0.0, 0.0], [4.0, 4.0]);
    let shared_face = AABB::from_corners([1.0, 1.0], [4.0, 4.0]);
    let sticking_out = AABB::from_corners([1.0, 1.0], [5.0, 3.0]);
    assert!(outer.contains_envelope(&shared_face));
    assert!(!outer.contains_envelope(&sticking_out));
    assert!(outer.contains_envelope(&outer));
}

#[test]
fn generated_intersects_inclusive_touch() {
    let b = AABB::from_corners([0.0, 0.0], [2.0, 2.0]);
    assert!(b.intersects(&AABB::from_corners([2.0, 2.0], [3.0, 3.0]))); // corner touch
    assert!(b.intersects(&AABB::from_corners([2.0, 0.0], [4.0, 2.0]))); // face touch
    assert!(b.intersects(&AABB::from_corners([1.0, 1.0], [3.0, 3.0]))); // overlap
    assert!(!b.intersects(&AABB::from_corners([2.5, 2.5], [3.0, 3.0])));
}

#[test]
fn generated_merge_grows_in_place_and_by_copy() {
    let mut a = AABB::from_corners([0.0, 0.0], [1.0, 1.0]);
    let b = AABB::from_corners([2.0, 2.0], [3.0, 3.0]);
    let grown = a.merged(&b);
    assert_eq!(grown.lower(), [0.0, 0.0]);
    assert_eq!(grown.upper(), [3.0, 3.0]);
    // merged did not mutate:
    assert_eq!(a.upper(), [1.0, 1.0]);
    a.merge(&b);
    assert_eq!(a, grown);
}

#[test]
fn generated_area_and_intersection_area() {
    let b = AABB::from_corners([1.0, -1.0], [3.0, 4.0]);
    assert_eq!(b.area(), 10.0); // 2 * 5
    let unit = AABB::from_corners([0.0, 0.0], [2.0, 2.0]);
    let overlap = AABB::from_corners([1.0, 1.0], [3.0, 3.0]);
    assert_eq!(unit.intersection_area(&overlap), 1.0);
    // touching boxes overlap with zero area:
    assert_eq!(unit.intersection_area(&AABB::from_corners([2.0, 0.0], [3.0, 2.0])), 0.0);
    // disjoint boxes clamp to zero:
    assert_eq!(unit.intersection_area(&AABB::from_corners([5.0, 5.0], [6.0, 6.0])), 0.0);
}

#[test]
fn generated_center_and_perimeter_value() {
    let b = AABB::from_corners([1.0, -1.0], [3.0, 4.0]);
    assert_eq!(b.center(), [2.0, 1.5]);
    assert_eq!(b.perimeter_value(), 7.0); // 2 + 5
}

#[test]
fn generated_min_point_clamps_and_distance_2() {
    let b = AABB::from_corners([0.0, 0.0], [2.0, 2.0]);
    assert_eq!(b.min_point(&[3.0, 5.0]), [2.0, 2.0]);
    assert_eq!(b.distance_2(&[3.0, 5.0]), 10.0); // 1 + 9
    // contained point: min_point is the point itself, distance zero
    assert_eq!(b.min_point(&[1.0, 1.0]), [1.0, 1.0]);
    assert_eq!(b.distance_2(&[1.0, 1.0]), 0.0);
    // clamp on one axis only
    assert_eq!(b.min_point(&[1.0, -3.0]), [1.0, 0.0]);
    assert_eq!(b.distance_2(&[1.0, -3.0]), 9.0);
}

#[test]
fn generated_min_max_dist_matches_corner_distance() {
    let b = AABB::from_corners([0.0, 0.0], [2.0, 2.0]);
    // min-max corner seen from [3, 3] is [2, 0] (or symmetrically [0, 2]):
    assert_eq!(b.min_max_dist_2(&[3.0, 3.0]), 10.0); // 1 + 9
    let wide = AABB::from_corners([0.0, 0.0], [4.0, 2.0]);
    // clamping x to its near face (x=4) and taking y's far corner (y=0):
    assert_eq!(wide.min_max_dist_2(&[5.0, 5.0]), 26.0); // 1 + 25
}

#[test]
fn generated_value_semantics_eq_ord_hash() {
    // Corner-order-insensitive equality over float coordinates:
    let fa = AABB::from_corners([0.0, 0.0], [1.0, 1.0]);
    let fa2 = AABB::from_corners([1.0, 1.0], [0.0, 0.0]);
    assert_eq!(fa, fa2);
    assert_ne!(fa, AABB::from_corners([2.0, 2.0], [3.0, 3.0]));
    // Order and hashing over an orderable/hashable scalar:
    let a = AABB::from_corners([0, 0], [1, 1]);
    let a2 = AABB::from_corners([1, 1], [0, 0]);
    let b = AABB::from_corners([2, 2], [3, 3]);
    let mut set = std::collections::HashSet::new();
    set.insert(a);
    set.insert(a2);
    set.insert(b);
    assert_eq!(set.len(), 2);
    let mut boxes = vec![b, a, a2];
    boxes.sort(); // Ord is implemented; equal boxes sort adjacent
    assert_eq!(boxes[0], boxes[1]);
}
