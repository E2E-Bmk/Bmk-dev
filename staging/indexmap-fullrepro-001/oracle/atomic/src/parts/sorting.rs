// Sorting and ordered search: stable/unstable families, binary search,
// partition_point, and the set mirror.

fn shuffled() -> IndexMap<&'static str, i32> {
    [("d", 4), ("b", 2), ("e", 5), ("a", 1), ("c", 3)]
        .into_iter()
        .collect()
}

#[test]
fn generated_sort_keys_in_place() {
    let mut m = shuffled();
    m.sort_keys();
    assert_eq!(key_list(&m), ["a", "b", "c", "d", "e"]);
    assert_eq!(m.values().collect::<Vec<_>>(), [&1, &2, &3, &4, &5]);
}

#[test]
fn generated_sort_by_is_stable() {
    let mut m = base(); // values 1..5 in key order a..e
    // group evens before odds; ties keep their relative order
    m.sort_by(|_, v1, _, v2| (v1 % 2).cmp(&(v2 % 2)));
    assert_eq!(key_list(&m), ["b", "d", "a", "c", "e"]);
}

#[test]
fn generated_sort_by_cached_key() {
    let mut m = shuffled();
    m.sort_by_cached_key(|_, v| std::cmp::Reverse(*v));
    assert_eq!(key_list(&m), ["e", "d", "c", "b", "a"]);
}

#[test]
fn generated_sorted_by_consumes() {
    let m = shuffled();
    let pairs: Vec<_> = m.sorted_by(|k1, _, k2, _| k1.cmp(k2)).collect();
    assert_eq!(
        pairs,
        [("a", 1), ("b", 2), ("c", 3), ("d", 4), ("e", 5)]
    );
}

#[test]
fn generated_unstable_sorts_same_multiset() {
    // keys are distinct, so the unstable result is fully determined
    let mut m = shuffled();
    m.sort_unstable_keys();
    assert_eq!(key_list(&m), ["a", "b", "c", "d", "e"]);
    let mut m = shuffled();
    m.sort_unstable_by(|_, v1, _, v2| v2.cmp(v1));
    assert_eq!(key_list(&m), ["e", "d", "c", "b", "a"]);
    let m = shuffled();
    let pairs: Vec<_> = m.sorted_unstable_by(|k1, _, k2, _| k1.cmp(k2)).collect();
    assert_eq!(pairs[0], ("a", 1));
    assert_eq!(pairs.len(), 5);
}

#[test]
fn generated_binary_search_keys() {
    let m = base(); // sorted by key
    assert_eq!(m.binary_search_keys(&"c"), Ok(2));
    assert_eq!(m.binary_search_keys(&"cc"), Err(3));
    assert_eq!(m.binary_search_keys(&"zz"), Err(5));
}

#[test]
fn generated_binary_search_by_forms() {
    let m = base(); // values 1..5 ascending
    assert_eq!(m.binary_search_by(|_, v| v.cmp(&4)), Ok(3));
    assert_eq!(m.binary_search_by_key(&3, |_, v| *v), Ok(2));
    assert_eq!(m.binary_search_by_key(&99, |_, v| *v), Err(5));
}

#[test]
fn generated_partition_point() {
    let m = base(); // values 1..5 ascending
    assert_eq!(m.partition_point(|_, v| *v < 4), 3);
    assert_eq!(m.partition_point(|_, _| false), 0);
    assert_eq!(m.partition_point(|_, _| true), 5);
}

#[test]
fn generated_set_sort_family() {
    let mut s: IndexSet<i32> = [4, 2, 5, 1, 3].into_iter().collect();
    s.sort();
    assert_eq!(s.iter().collect::<Vec<_>>(), [&1, &2, &3, &4, &5]);
    assert_eq!(s.binary_search(&3), Ok(2));
    assert_eq!(s.binary_search(&6), Err(5));
    assert_eq!(s.partition_point(|v| *v < 3), 2);
    s.reverse();
    assert_eq!(s.iter().collect::<Vec<_>>(), [&5, &4, &3, &2, &1]);
    let mut s2: IndexSet<i32> = [4, 2, 5].into_iter().collect();
    s2.sort_by(|a, b| b.cmp(a));
    assert_eq!(s2.iter().collect::<Vec<_>>(), [&5, &4, &2]);
    let s3: IndexSet<i32> = [4, 2, 5].into_iter().collect();
    let v: Vec<_> = s3.sorted_by(|a, b| a.cmp(b)).collect();
    assert_eq!(v, [2, 4, 5]);
    let mut s4: IndexSet<i32> = [4, 2, 5].into_iter().collect();
    s4.sort_unstable();
    assert_eq!(s4.iter().collect::<Vec<_>>(), [&2, &4, &5]);
    assert_eq!(s4.binary_search_by(|v| v.cmp(&4)), Ok(1));
    assert_eq!(s4.binary_search_by_key(&5, |v| *v), Ok(2));
}
