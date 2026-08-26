// Custom-extension workflows: caller-defined objects and metrics,
// caller-defined selection functions, and non-float scalars, each driving
// several projections at once.

struct Sensor {
    origin: [f64; 2],
    radius: f64,
    id: u32,
}

impl RTreeObject for Sensor {
    type Envelope = AABB<[f64; 2]>;
    fn envelope(&self) -> Self::Envelope {
        AABB::from_corners(
            [self.origin[0] - self.radius, self.origin[1] - self.radius],
            [self.origin[0] + self.radius, self.origin[1] + self.radius],
        )
    }
}

impl PointDistance for Sensor {
    fn distance_2(&self, point: &[f64; 2]) -> f64 {
        let dx = self.origin[0] - point[0];
        let dy = self.origin[1] - point[1];
        let gap = ((dx * dx + dy * dy).sqrt() - self.radius).max(0.0);
        gap * gap
    }
}

#[test]
fn generated_sensor_coverage_workflow() {
    let mut grid = RTree::bulk_load(vec![
        Sensor { origin: [0.0, 0.0], radius: 2.0, id: 1 },
        Sensor { origin: [6.0, 0.0], radius: 1.0, id: 2 },
        Sensor { origin: [0.0, 8.0], radius: 3.0, id: 3 },
    ]);
    // a probe point inside a sensor's disc is "covered" (custom metric zero):
    assert_eq!(grid.locate_at_point(&[1.0, 0.0]).unwrap().id, 1);
    assert_eq!(grid.locate_at_point(&[0.0, 6.0]).unwrap().id, 3);
    assert!(grid.locate_at_point(&[3.5, 0.0]).is_none()); // gap between discs
    // nearest coverage is measured to the disc boundary, not the center:
    // from [4, 0]: gap to sensor 1 = 2, gap to sensor 2 = 1
    assert_eq!(grid.nearest_neighbor(&[4.0, 0.0]).unwrap().id, 2);
    // sensors whose boundary is within 2 units (squared bound 4, inclusive):
    let reachable: Vec<u32> =
        grid.locate_within_distance([4.0, 0.0], 4.0).map(|s| s.id).collect();
    let mut reachable = reachable;
    reachable.sort();
    assert_eq!(reachable, vec![1, 2]);
    // decommission the nearest sensor and re-ask:
    let popped = grid.pop_nearest_neighbor(&[4.0, 0.0]).unwrap();
    assert_eq!(popped.id, 2);
    assert_eq!(grid.size(), 2);
    assert_eq!(grid.nearest_neighbor(&[4.0, 0.0]).unwrap().id, 1);
}

struct InDisc {
    center: [f64; 2],
    radius_2: f64,
}

impl SelectionFunction<[f64; 2]> for InDisc {
    fn should_unpack_parent(&self, envelope: &AABB<[f64; 2]>) -> bool {
        envelope.distance_2(&self.center) <= self.radius_2
    }
    fn should_unpack_leaf(&self, leaf: &[f64; 2]) -> bool {
        leaf.distance_2(&self.center) <= self.radius_2
    }
}

#[test]
fn generated_selection_function_maintenance() {
    let mut tree = RTree::bulk_load(vec![
        [0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [5.0, 5.0], [6.0, 5.0],
    ]);
    let disc = || InDisc { center: [0.0, 0.0], radius_2: 2.0 };
    // the custom search and the built-in metric filter agree:
    assert_eq!(
        sorted(tree.locate_with_selection_function(disc()).copied().collect()),
        sorted(tree.locate_within_distance([0.0, 0.0], 2.0).copied().collect())
    );
    assert_eq!(tree.locate_with_selection_function(disc()).count(), 3);
    // remove through the same predicate, one element per call:
    assert!(tree.remove_with_selection_function(disc()).is_some());
    assert_eq!(tree.size(), 4);
    assert_eq!(tree.locate_with_selection_function(disc()).count(), 2);
    // drain the rest of the disc; the far pair is untouched:
    let drained = tree.drain_with_selection_function(disc()).count();
    assert_eq!(drained, 2);
    assert_eq!(tree.size(), 2);
    assert_eq!(tree.locate_with_selection_function(disc()).count(), 0);
    assert!(tree.contains(&[5.0, 5.0]));
    assert!(tree.contains(&[6.0, 5.0]));
}

#[test]
fn generated_integer_grid_workflow() {
    let cells: Vec<[i32; 2]> = (0..6)
        .flat_map(|x| (0..4).map(move |y| [x * 10, y * 10]))
        .collect();
    let mut board: RTree<[i32; 2]> = RTree::bulk_load(cells);
    assert_eq!(board.size(), 24);
    // integer envelope query:
    let quad = AABB::from_corners([0, 0], [20, 20]);
    assert_eq!(board.locate_in_envelope(&quad).count(), 9);
    // integer squared distances drive the neighbor schedule:
    assert_eq!(board.nearest_neighbor(&[12, 9]), Some(&[10, 10]));
    let d: Vec<i32> = board
        .nearest_neighbor_iter_with_distance_2(&[12, 9])
        .take(3)
        .map(|(_, d)| d)
        .collect();
    assert_eq!(d, vec![5, 65, 85]);
    // editing keeps the views consistent:
    assert_eq!(board.remove_at_point(&[10, 10]), Some([10, 10]));
    assert_eq!(board.size(), 23);
    assert_eq!(board.nearest_neighbor(&[12, 9]), Some(&[20, 10]));
    assert_eq!(
        board.root().envelope(),
        AABB::from_corners([0, 0], [50, 30])
    );
}
