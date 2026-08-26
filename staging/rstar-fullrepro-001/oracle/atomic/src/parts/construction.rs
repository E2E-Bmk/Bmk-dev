// Tree construction and population: constructors, size/iter/contains
// bookkeeping, duplicate accounting, parameter verification panics,
// dimension verification, construction-path equivalence.

#[test]
fn generated_new_tree_is_empty() {
    let tree: RTree<[f64; 2]> = RTree::new();
    assert_eq!(tree.size(), 0);
    assert_eq!(tree.iter().count(), 0);
    assert_eq!(tree.nearest_neighbor(&[0.0, 0.0]), None);
    let by_default: RTree<[f64; 2]> = RTree::default();
    assert_eq!(by_default.size(), 0);
}

#[test]
fn generated_bulk_load_exact_content() {
    let elements = vec![[0.0, 0.0], [1.0, 2.0], [3.0, 1.0], [1.0, 2.0]];
    let tree = RTree::bulk_load(elements.clone());
    assert_eq!(tree.size(), 4); // duplicates included
    let mut seen: Vec<[f64; 2]> = tree.iter().copied().collect();
    seen.sort_by(|a, b| a.partial_cmp(b).unwrap());
    assert_eq!(seen, sorted(elements));
}

#[test]
fn generated_bulk_load_empty_vector() {
    let tree: RTree<[f64; 2]> = RTree::bulk_load(Vec::new());
    assert_eq!(tree.size(), 0);
    assert_eq!(tree.iter().count(), 0);
}

#[test]
fn generated_insert_increments_and_duplicates_accumulate() {
    let mut tree = RTree::new();
    tree.insert([1.0, 1.0]);
    assert_eq!(tree.size(), 1);
    tree.insert([1.0, 1.0]);
    tree.insert([1.0, 1.0]);
    assert_eq!(tree.size(), 3);
    assert_eq!(tree.locate_all_at_point(&[1.0, 1.0]).count(), 3);
}

#[test]
fn generated_contains_by_equality() {
    let tree = RTree::bulk_load(vec![[0.0, 0.0], [2.0, 2.0]]);
    assert!(tree.contains(&[2.0, 2.0]));
    assert!(!tree.contains(&[2.0, 2.0001]));
}

#[test]
fn generated_iteration_by_ref_and_by_value() {
    let elements = vec![[0.0, 1.0], [2.0, 3.0], [4.0, 5.0]];
    let tree = RTree::bulk_load(elements.clone());
    let by_ref: Vec<[f64; 2]> = (&tree).into_iter().copied().collect();
    assert_eq!(sorted(by_ref), sorted(elements.clone()));
    let by_value: Vec<[f64; 2]> = tree.into_iter().collect();
    assert_eq!(sorted(by_value), sorted(elements));
}

#[test]
fn generated_iter_mut_updates_payload() {
    type Tagged = GeomWithData<[f64; 2], u32>;
    let mut tree = RTree::bulk_load(vec![
        Tagged::new([0.0, 0.0], 1),
        Tagged::new([5.0, 5.0], 2),
    ]);
    for item in tree.iter_mut() {
        item.data *= 10;
    }
    let mut tags: Vec<u32> = tree.iter().map(|t| t.data).collect();
    tags.sort();
    assert_eq!(tags, vec![10, 20]);
}

struct SmallNodes;
impl RTreeParams for SmallNodes {
    const MIN_SIZE: usize = 2;
    const MAX_SIZE: usize = 4;
    const REINSERTION_COUNT: usize = 1;
    type DefaultInsertionStrategy = RStarInsertionStrategy;
}

#[test]
fn generated_custom_params_do_not_change_answers() {
    let elements: Vec<[f64; 2]> = (0..30).map(|i| [(i % 6) as f64, (i / 6) as f64]).collect();
    let default_tree = RTree::bulk_load(elements.clone());
    let custom_tree: RTree<[f64; 2], SmallNodes> =
        RTree::bulk_load_with_params(elements.clone());
    let mut incremental: RTree<[f64; 2], SmallNodes> = RTree::new_with_params();
    for e in &elements {
        incremental.insert(*e);
    }
    let probe = AABB::from_corners([1.0, 1.0], [4.0, 3.0]);
    let base = sorted(default_tree.locate_in_envelope(&probe).copied().collect());
    assert_eq!(sorted(custom_tree.locate_in_envelope(&probe).copied().collect()), base);
    assert_eq!(sorted(incremental.locate_in_envelope(&probe).copied().collect()), base);
    assert_eq!(custom_tree.size(), 30);
    assert_eq!(
        custom_tree.nearest_neighbor(&[10.0, 10.0]),
        default_tree.nearest_neighbor(&[10.0, 10.0])
    );
}

struct MaxTooSmall;
impl RTreeParams for MaxTooSmall {
    const MIN_SIZE: usize = 1;
    const MAX_SIZE: usize = 3;
    const REINSERTION_COUNT: usize = 1;
    type DefaultInsertionStrategy = RStarInsertionStrategy;
}

#[test]
#[should_panic]
fn generated_params_panic_max_below_four() {
    let _tree: RTree<[f64; 2], MaxTooSmall> = RTree::new_with_params();
}

struct MinZero;
impl RTreeParams for MinZero {
    const MIN_SIZE: usize = 0;
    const MAX_SIZE: usize = 6;
    const REINSERTION_COUNT: usize = 1;
    type DefaultInsertionStrategy = RStarInsertionStrategy;
}

#[test]
#[should_panic]
fn generated_params_panic_min_zero() {
    let _tree: RTree<[f64; 2], MinZero> = RTree::new_with_params();
}

struct MinTooBig;
impl RTreeParams for MinTooBig {
    const MIN_SIZE: usize = 4;
    const MAX_SIZE: usize = 6;
    const REINSERTION_COUNT: usize = 1;
    type DefaultInsertionStrategy = RStarInsertionStrategy;
}

#[test]
#[should_panic]
fn generated_params_panic_min_above_half_max() {
    let _tree: RTree<[f64; 2], MinTooBig> = RTree::new_with_params();
}

struct ReinsertionTooBig;
impl RTreeParams for ReinsertionTooBig {
    const MIN_SIZE: usize = 3;
    const MAX_SIZE: usize = 6;
    const REINSERTION_COUNT: usize = 3;
    type DefaultInsertionStrategy = RStarInsertionStrategy;
}

#[test]
#[should_panic]
fn generated_params_panic_reinsertion_count() {
    let _tree: RTree<[f64; 2], ReinsertionTooBig> = RTree::new_with_params();
}

#[derive(Clone, Copy, PartialEq, Debug)]
struct OneD(f64);

impl rstar::Point for OneD {
    type Scalar = f64;
    const DIMENSIONS: usize = 1;
    fn generate(mut generator: impl FnMut(usize) -> Self::Scalar) -> Self {
        OneD(generator(0))
    }
    fn nth(&self, _index: usize) -> Self::Scalar {
        self.0
    }
    fn nth_mut(&mut self, _index: usize) -> &mut Self::Scalar {
        &mut self.0
    }
}

#[test]
#[should_panic]
fn generated_dimension_below_two_panics() {
    let _tree: RTree<OneD> = RTree::new();
}

#[test]
fn generated_construction_path_equivalence() {
    let elements: Vec<[f64; 2]> =
        (0..40).map(|i| [((i * 7) % 13) as f64, ((i * 5) % 11) as f64]).collect();
    let bulk = RTree::bulk_load(elements.clone());
    let mut one_by_one = RTree::new();
    for e in &elements {
        one_by_one.insert(*e);
    }
    assert_eq!(bulk.size(), one_by_one.size());
    assert_eq!(
        sorted(bulk.iter().copied().collect()),
        sorted(one_by_one.iter().copied().collect())
    );
    let query = [3.5, 4.5];
    let d_bulk: Vec<f64> =
        bulk.nearest_neighbor_iter_with_distance_2(&query).map(|(_, d)| d).collect();
    let d_inc: Vec<f64> =
        one_by_one.nearest_neighbor_iter_with_distance_2(&query).map(|(_, d)| d).collect();
    assert_eq!(d_bulk, d_inc); // identical distance sequences
}
