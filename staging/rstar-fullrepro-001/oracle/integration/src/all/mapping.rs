// Mapping workflows: payload-carrying trees, region enumeration across
// query families, construction-path and parameter equivalence pipelines.

type Station = GeomWithData<[f64; 2], &'static str>;

#[test]
fn generated_station_map_lifecycle() {
    let mut network = RTree::bulk_load(vec![
        Station::new([0.0, 0.0], "central"),
        Station::new([5.0, 5.0], "airport"),
        Station::new([2.0, 1.0], "harbor"),
    ]);
    assert_eq!(network.size(), 3);
    assert_eq!(network.nearest_neighbor(&[1.0, 1.0]).unwrap().data, "harbor");
    // rename a station in place through the mutable point-location view:
    network.locate_at_point_mut(&[5.0, 5.0]).unwrap().data = "airport-t2";
    assert_eq!(network.nearest_neighbor(&[6.0, 6.0]).unwrap().data, "airport-t2");
    // expansion: a new stop shifts the nearest answer
    network.insert(Station::new([0.5, 0.5], "museum"));
    assert_eq!(network.size(), 4);
    assert_eq!(network.nearest_neighbor(&[1.0, 1.0]).unwrap().data, "museum");
    // decommission by geometric position; the payload comes back out:
    let removed = network.remove_at_point(&[2.0, 1.0]).unwrap();
    assert_eq!(removed.data, "harbor");
    assert_eq!(network.size(), 3);
    let mut names: Vec<&str> = network.iter().map(|s| s.data).collect();
    names.sort();
    assert_eq!(names, vec!["airport-t2", "central", "museum"]);
}

#[test]
fn generated_region_enumeration_consistency() {
    let pts: Vec<[f64; 2]> = (0..5)
        .flat_map(|x| (0..5).map(move |y| [x as f64, y as f64]))
        .collect();
    let tree = RTree::bulk_load(pts);
    let region = AABB::from_corners([1.0, 1.0], [3.0, 3.0]);
    // fully-contained points of the 5x5 grid inside a 3x3 box:
    let contained = sorted(tree.locate_in_envelope(&region).copied().collect());
    assert_eq!(contained.len(), 9);
    // for zero-extent point envelopes, intersecting equals contained:
    let intersecting = sorted(tree.locate_in_envelope_intersecting(&region).copied().collect());
    assert_eq!(contained, intersecting);
    // the within-distance view around the region center agrees with the
    // nondecreasing neighbor iteration cut at the same bound:
    let center = [2.0, 2.0];
    let bound = 2.0;
    let by_filter = sorted(tree.locate_within_distance(center, bound).copied().collect());
    let by_iter = sorted(
        tree.nearest_neighbor_iter_with_distance_2(&center)
            .take_while(|(_, d)| *d <= bound)
            .map(|(p, _)| *p)
            .collect(),
    );
    assert_eq!(by_filter, by_iter);
    assert_eq!(by_filter.len(), 9); // center, 4 at d2=1, 4 at d2=2
}

#[test]
fn generated_bulk_vs_incremental_pipeline() {
    let elements: Vec<[f64; 2]> = (0..60)
        .map(|i| [((i * 13) % 23) as f64, ((i * 7) % 19) as f64])
        .collect();
    let bulk = RTree::bulk_load(elements.clone());
    let mut inc = RTree::new();
    for e in &elements {
        inc.insert(*e);
    }
    // set-valued queries agree as multisets:
    let region = AABB::from_corners([3.0, 2.0], [15.0, 11.0]);
    assert_eq!(
        sorted(bulk.locate_in_envelope(&region).copied().collect()),
        sorted(inc.locate_in_envelope(&region).copied().collect())
    );
    // distance-ordered queries agree as distance sequences:
    let q = [7.3, 9.1];
    let db: Vec<f64> = bulk.nearest_neighbor_iter_with_distance_2(&q).map(|(_, d)| d).collect();
    let di: Vec<f64> = inc.nearest_neighbor_iter_with_distance_2(&q).map(|(_, d)| d).collect();
    assert_eq!(db, di);
    // tie sets agree exactly:
    assert_eq!(
        sorted(bulk.nearest_neighbors(&q).into_iter().copied().collect()),
        sorted(inc.nearest_neighbors(&q).into_iter().copied().collect())
    );
    // and destructive draining pops the same distance schedule:
    let mut bulk = bulk;
    let mut inc = inc;
    for _ in 0..10 {
        let a = bulk.pop_nearest_neighbor(&q).unwrap();
        let b = inc.pop_nearest_neighbor(&q).unwrap();
        assert_eq!(a.distance_2(&q), b.distance_2(&q));
    }
    assert_eq!(bulk.size(), inc.size());
}

struct WideNodes;
impl RTreeParams for WideNodes {
    const MIN_SIZE: usize = 4;
    const MAX_SIZE: usize = 16;
    const REINSERTION_COUNT: usize = 5;
    type DefaultInsertionStrategy = RStarInsertionStrategy;
}

#[test]
fn generated_custom_params_pipeline() {
    let elements: Vec<[f64; 2]> = (0..50)
        .map(|i| [((i * 3) % 31) as f64, ((i * 17) % 29) as f64])
        .collect();
    let default_tree = RTree::bulk_load(elements.clone());
    let mut wide: RTree<[f64; 2], WideNodes> = RTree::bulk_load_with_params(elements);
    // a full query pipeline gives identical answers under both parameter sets:
    let region = AABB::from_corners([5.0, 5.0], [20.0, 20.0]);
    let base = sorted(default_tree.locate_in_envelope(&region).copied().collect());
    assert_eq!(sorted(wide.locate_in_envelope(&region).copied().collect()), base);
    let q = [12.0, 14.0];
    assert_eq!(
        wide.nearest_neighbor(&q).unwrap().distance_2(&q),
        default_tree.nearest_neighbor(&q).unwrap().distance_2(&q)
    );
    // mutation keeps the agreement:
    let victim = *default_tree.nearest_neighbor(&q).unwrap();
    wide.remove(&victim).unwrap();
    let mut default_tree = default_tree;
    default_tree.remove(&victim).unwrap();
    assert_eq!(wide.size(), default_tree.size());
    assert_eq!(
        wide.nearest_neighbor(&q).unwrap().distance_2(&q),
        default_tree.nearest_neighbor(&q).unwrap().distance_2(&q)
    );
}
