// Set algebra with deterministic order, containment predicates, and
// the order-insensitive container equality.

fn alg_a() -> IndexSet<i32> {
    [3, 1, 4, 2].into_iter().collect()
}

fn alg_b() -> IndexSet<i32> {
    [4, 5, 3, 6].into_iter().collect()
}

#[test]
fn generated_intersection_order() {
    let (a, b) = (alg_a(), alg_b());
    // self's elements also in other, in self's order
    assert_eq!(a.intersection(&b).collect::<Vec<_>>(), [&3, &4]);
    assert_eq!(b.intersection(&a).collect::<Vec<_>>(), [&4, &3]);
}

#[test]
fn generated_difference_order() {
    let (a, b) = (alg_a(), alg_b());
    assert_eq!(a.difference(&b).collect::<Vec<_>>(), [&1, &2]);
    assert_eq!(b.difference(&a).collect::<Vec<_>>(), [&5, &6]);
}

#[test]
fn generated_union_order() {
    let (a, b) = (alg_a(), alg_b());
    // all of self in order, then other's exclusives in other's order
    assert_eq!(a.union(&b).collect::<Vec<_>>(), [&3, &1, &4, &2, &5, &6]);
    assert_eq!(b.union(&a).collect::<Vec<_>>(), [&4, &5, &3, &6, &1, &2]);
}

#[test]
fn generated_symmetric_difference_order() {
    let (a, b) = (alg_a(), alg_b());
    // self's exclusives first, then other's exclusives
    assert_eq!(a.symmetric_difference(&b).collect::<Vec<_>>(), [&1, &2, &5, &6]);
    assert_eq!(b.symmetric_difference(&a).collect::<Vec<_>>(), [&5, &6, &1, &2]);
}

#[test]
fn generated_operators_match_iterators() {
    let (a, b) = (alg_a(), alg_b());
    let and: IndexSet<i32> = &a & &b;
    assert_eq!(and.iter().collect::<Vec<_>>(), [&3, &4]);
    let or: IndexSet<i32> = &a | &b;
    assert_eq!(or.iter().collect::<Vec<_>>(), [&3, &1, &4, &2, &5, &6]);
    let xor: IndexSet<i32> = &a ^ &b;
    assert_eq!(xor.iter().collect::<Vec<_>>(), [&1, &2, &5, &6]);
    let sub: IndexSet<i32> = &a - &b;
    assert_eq!(sub.iter().collect::<Vec<_>>(), [&1, &2]);
}

#[test]
fn generated_containment_predicates() {
    let a = alg_a();
    let small: IndexSet<i32> = [4, 1].into_iter().collect();
    let other: IndexSet<i32> = [7, 8].into_iter().collect();
    assert!(small.is_subset(&a));
    assert!(!a.is_subset(&small));
    assert!(a.is_superset(&small));
    assert!(a.is_disjoint(&other));
    assert!(!a.is_disjoint(&small));
    assert!(a.is_subset(&a));
}

#[test]
fn generated_map_equality_order_insensitive() {
    let m1 = indexmap! {"a" => 1, "b" => 2};
    let m2 = indexmap! {"b" => 2, "a" => 1};
    assert_eq!(m1, m2); // same associations, different order
    let m3 = indexmap! {"a" => 1, "b" => 99};
    assert_ne!(m1, m3);
    let m4 = indexmap! {"a" => 1};
    assert_ne!(m1, m4);
}

#[test]
fn generated_set_equality_order_insensitive() {
    let s1 = indexset! {1, 2, 3};
    let s2 = indexset! {3, 2, 1};
    assert_eq!(s1, s2);
    let s3 = indexset! {1, 2};
    assert_ne!(s1, s3);
}

#[test]
fn generated_clone_and_debug() {
    let m = indexmap! {"a" => 1, "b" => 2};
    let c = m.clone();
    assert_eq!(c.keys().collect::<Vec<_>>(), [&"a", &"b"]); // order kept
    assert_eq!(format!("{:?}", m), r#"{"a": 1, "b": 2}"#);
    let s = indexset! {3, 1};
    let cs = s.clone();
    assert_eq!(cs.iter().collect::<Vec<_>>(), [&3, &1]);
    assert_eq!(format!("{:?}", s), "{3, 1}");
}
