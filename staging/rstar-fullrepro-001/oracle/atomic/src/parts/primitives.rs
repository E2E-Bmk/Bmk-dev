// Geometric primitives: Line, Rectangle, GeomWithData, PointWithData,
// CachedEnvelope, ObjectRef, custom objects with custom metrics, and
// PointDistance defaults.

#[test]
fn generated_line_fields_length_envelope() {
    let line = Line::new([3.0, 1.0], [0.0, 2.0]);
    assert_eq!(line.from, [3.0, 1.0]);
    assert_eq!(line.to, [0.0, 2.0]);
    assert_eq!(line.length_2(), 10.0); // 9 + 1
    let env = line.envelope();
    assert_eq!(env.lower(), [0.0, 1.0]);
    assert_eq!(env.upper(), [3.0, 2.0]);
}

#[test]
fn generated_line_nearest_point_projection() {
    let line = Line::new([0.0, 0.0], [4.0, 0.0]);
    // perpendicular foot inside the segment:
    assert_eq!(line.nearest_point(&[2.0, 3.0]), [2.0, 0.0]);
    assert_eq!(line.distance_2(&[2.0, 3.0]), 9.0);
    // foot outside: clamps to the nearer endpoint
    assert_eq!(line.nearest_point(&[-2.0, 1.0]), [0.0, 0.0]);
    assert_eq!(line.distance_2(&[-2.0, 1.0]), 5.0); // 4 + 1
    assert_eq!(line.nearest_point(&[7.0, 0.0]), [4.0, 0.0]);
    assert_eq!(line.distance_2(&[7.0, 0.0]), 9.0);
}

#[test]
fn generated_rectangle_corners_and_conversions() {
    let r = Rectangle::from_corners([2.0, 3.0], [0.0, 1.0]);
    assert_eq!(r.lower(), [0.0, 1.0]);
    assert_eq!(r.upper(), [2.0, 3.0]);
    let aabb = AABB::from_corners([0.0, 1.0], [2.0, 3.0]);
    assert_eq!(Rectangle::from_aabb(aabb), r);
    let via_from: Rectangle<[f64; 2]> = aabb.into();
    assert_eq!(via_from, r);
    assert_eq!(r.envelope(), aabb);
}

#[test]
fn generated_rectangle_nearest_point_and_distance() {
    let r = Rectangle::from_corners([0.0, 1.0], [2.0, 3.0]);
    // contained query: the point itself at distance zero
    assert_eq!(r.nearest_point(&[1.0, 2.0]), [1.0, 2.0]);
    assert_eq!(r.distance_2(&[1.0, 2.0]), 0.0);
    // outside: componentwise clamp
    assert_eq!(r.nearest_point(&[4.0, 0.0]), [2.0, 1.0]);
    assert_eq!(r.distance_2(&[4.0, 0.0]), 5.0); // 4 + 1
}

#[test]
fn generated_geom_with_data_forwards_geometry() {
    type Station = GeomWithData<[f64; 2], &'static str>;
    let s = Station::new([2.0, 2.0], "central");
    assert_eq!(s.data, "central");
    assert_eq!(s.geom(), &[2.0, 2.0]);
    assert_eq!(s.envelope(), AABB::from_point([2.0, 2.0]));
    assert_eq!(s.distance_2(&[2.0, 5.0]), 9.0);
    let tree = RTree::bulk_load(vec![
        Station::new([0.0, 0.0], "a"),
        Station::new([5.0, 5.0], "b"),
    ]);
    assert_eq!(tree.nearest_neighbor(&[1.0, 1.0]).unwrap().data, "a");
}

#[test]
fn generated_geom_with_data_line_geometry() {
    type Road = GeomWithData<Line<[f64; 2]>, u32>;
    let road = Road::new(Line::new([0.0, 0.0], [4.0, 0.0]), 66);
    assert_eq!(road.data, 66);
    assert_eq!(road.distance_2(&[2.0, 3.0]), 9.0);
    let tree = RTree::bulk_load(vec![road]);
    assert_eq!(tree.nearest_neighbor(&[1.0, 1.0]).unwrap().data, 66);
}

#[test]
#[allow(deprecated)]
fn generated_point_with_data_deprecated_predecessor() {
    let p = PointWithData::new("tag", [1.0, 2.0]);
    assert_eq!(p.data, "tag");
    assert_eq!(p.position(), &[1.0, 2.0]);
    let tree = RTree::bulk_load(vec![p]);
    assert_eq!(tree.nearest_neighbor(&[0.0, 0.0]).unwrap().data, "tag");
}

#[test]
fn generated_cached_envelope_forwards() {
    let cached = CachedEnvelope::new(Line::new([0.0, 0.0], [4.0, 0.0]));
    assert_eq!(cached.envelope(), AABB::from_corners([0.0, 0.0], [4.0, 0.0]));
    assert_eq!(cached.distance_2(&[2.0, 3.0]), 9.0);
    // Deref exposes the inner object:
    assert_eq!(cached.length_2(), 16.0);
    assert_eq!(cached.from, [0.0, 0.0]);
}

#[test]
fn generated_object_ref_forwards() {
    let lines = vec![
        Line::new([0.0, 0.0], [1.0, 0.0]),
        Line::new([5.0, 5.0], [6.0, 5.0]),
    ];
    let tree: RTree<ObjectRef<Line<[f64; 2]>>> =
        RTree::bulk_load(lines.iter().map(ObjectRef::new).collect());
    assert_eq!(tree.size(), 2);
    let nearest = tree.nearest_neighbor(&[0.0, 1.0]).unwrap();
    assert_eq!(nearest.envelope(), lines[0].envelope());
    // Deref exposes the referent:
    assert_eq!(nearest.to, [1.0, 0.0]);
}

struct Circle {
    origin: [f64; 2],
    radius: f64,
}

impl RTreeObject for Circle {
    type Envelope = AABB<[f64; 2]>;
    fn envelope(&self) -> Self::Envelope {
        AABB::from_corners(
            [self.origin[0] - self.radius, self.origin[1] - self.radius],
            [self.origin[0] + self.radius, self.origin[1] + self.radius],
        )
    }
}

impl PointDistance for Circle {
    fn distance_2(&self, point: &[f64; 2]) -> f64 {
        let dx = self.origin[0] - point[0];
        let dy = self.origin[1] - point[1];
        let gap = (dx * dx + dy * dy).sqrt() - self.radius;
        let gap = gap.max(0.0);
        gap * gap
    }
}

#[test]
fn generated_custom_object_custom_metric() {
    let tree = RTree::bulk_load(vec![
        Circle { origin: [0.0, 0.0], radius: 1.0 },
        Circle { origin: [10.0, 0.0], radius: 2.0 },
    ]);
    // [7, 0]: gap to first circle is 6, to second is 1 — the custom metric decides
    assert_eq!(tree.nearest_neighbor(&[7.0, 0.0]).unwrap().origin, [10.0, 0.0]);
    assert_eq!(tree.nearest_neighbor(&[7.0, 0.0]).unwrap().distance_2(&[7.0, 0.0]), 1.0);
    // within-distance honors the same metric inclusively:
    assert_eq!(tree.locate_within_distance([7.0, 0.0], 1.0).count(), 1);
    assert_eq!(tree.locate_within_distance([7.0, 0.0], 0.9).count(), 0);
}

#[test]
fn generated_point_distance_defaults() {
    let c = Circle { origin: [0.0, 0.0], radius: 1.0 };
    // default contains_point: distance_2(point) <= 0
    assert!(c.contains_point(&[0.5, 0.0])); // inside: gap clamps to zero
    assert!(c.contains_point(&[1.0, 0.0])); // on the boundary
    assert!(!c.contains_point(&[2.0, 0.0]));
    // default distance_2_if_less_or_equal: Some within the bound, None above
    assert_eq!(c.distance_2_if_less_or_equal(&[3.0, 0.0], 4.0), Some(4.0));
    assert_eq!(c.distance_2_if_less_or_equal(&[3.0, 0.0], 3.9), None);
}

#[test]
fn generated_custom_object_point_location() {
    let tree = RTree::bulk_load(vec![
        Circle { origin: [0.0, 0.0], radius: 1.0 },
        Circle { origin: [10.0, 0.0], radius: 2.0 },
    ]);
    // locate_at_point goes through contains_point, hence the custom metric:
    assert_eq!(tree.locate_at_point(&[0.5, 0.0]).unwrap().origin, [0.0, 0.0]);
    assert_eq!(tree.locate_at_point(&[9.0, 0.0]).unwrap().origin, [10.0, 0.0]);
    assert!(tree.locate_at_point(&[5.0, 0.0]).is_none());
}

#[test]
fn generated_integer_and_tuple_points() {
    let tree: RTree<[i32; 2]> = RTree::bulk_load(vec![[0, 0], [3, 4], [10, 0]]);
    assert_eq!(tree.nearest_neighbor(&[1, 1]), Some(&[0, 0]));
    let mut hits: Vec<[i32; 2]> =
        tree.locate_within_distance([0, 0], 25).copied().collect();
    hits.sort();
    assert_eq!(hits, vec![[0, 0], [3, 4]]); // 25 is inclusive
    // fixed-arity tuples of one scalar type are points too:
    let tuple_tree: RTree<(f64, f64)> = RTree::bulk_load(vec![(0.0, 0.0), (2.0, 2.0)]);
    assert_eq!(tuple_tree.nearest_neighbor(&(1.9, 1.9)), Some(&(2.0, 2.0)));
}
