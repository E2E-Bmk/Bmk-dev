// Slices and indexed views: obtaining slices, the slice API, and the
// order-sensitive value semantics that containers do not have.

#[test]
fn generated_as_slice_and_get_range() {
    let m = base();
    let sl = m.as_slice();
    assert_eq!(sl.len(), 5);
    assert!(!sl.is_empty());
    let mid = m.get_range(1..3).unwrap();
    assert_eq!(mid.keys().collect::<Vec<_>>(), [&"b", &"c"]);
    // reversed range and overlong range answer None:
    #[allow(clippy::reversed_empty_ranges)]
    let none = m.get_range(3..2);
    assert!(none.is_none());
    assert!(m.get_range(2..9).is_none());
}

#[test]
fn generated_range_indexing_and_panics() {
    let m = base();
    let sl = &m.as_slice()[1..3];
    assert_eq!(sl.keys().collect::<Vec<_>>(), [&"b", &"c"]);
    let sl2 = &m[1..3]; // containers index by range directly
    assert_eq!(sl2, sl);
    let s: IndexSet<i32> = [7, 8, 9].into_iter().collect();
    let ss = &s[0..2];
    assert_eq!(ss.iter().collect::<Vec<_>>(), [&7, &8]);
    assert!(catches(std::panic::AssertUnwindSafe(|| {
        let _ = &m[2..9];
    })));
}

#[test]
fn generated_slice_positional_reads() {
    let m = base();
    let sl = m.as_slice();
    assert_eq!(sl.get_index(1), Some((&"b", &2)));
    assert_eq!(sl.get_index(5), None);
    assert_eq!(sl.first(), Some((&"a", &1)));
    assert_eq!(sl.last(), Some((&"e", &5)));
    assert_eq!(sl[2], 3); // usize indexing yields the value
    assert!(catches(std::panic::AssertUnwindSafe(|| {
        let _ = sl[9];
    })));
    let s: IndexSet<i32> = [7, 8].into_iter().collect();
    assert_eq!(s.as_slice()[1], 8);
}

#[test]
fn generated_slice_split_family() {
    let m = base();
    let sl = m.as_slice();
    let (left, right) = sl.split_at(2);
    assert_eq!(left.keys().collect::<Vec<_>>(), [&"a", &"b"]);
    assert_eq!(right.keys().collect::<Vec<_>>(), [&"c", &"d", &"e"]);
    let (first, rest) = sl.split_first().unwrap();
    assert_eq!(first, (&"a", &1));
    assert_eq!(rest.len(), 4);
    let (last, rest) = sl.split_last().unwrap();
    assert_eq!(last, (&"e", &5));
    assert_eq!(rest.len(), 4);
}

#[test]
fn generated_slice_iterators_and_mutation() {
    let mut m = base();
    {
        let sl = m.as_slice();
        assert_eq!(sl.iter().next(), Some((&"a", &1)));
        assert_eq!(sl.keys().collect::<Vec<_>>(), [&"a", &"b", &"c", &"d", &"e"]);
        assert_eq!(sl.values().collect::<Vec<_>>(), [&1, &2, &3, &4, &5]);
    }
    let msl = m.as_mut_slice();
    for v in msl.values_mut() {
        *v += 10;
    }
    for (_, v) in msl.iter_mut() {
        *v += 100;
    }
    assert_eq!(m.values().collect::<Vec<_>>(), [&111, &112, &113, &114, &115]);
    let range = m.get_range_mut(0..2).unwrap();
    *range.get_index_mut(0).unwrap().1 = 0;
    assert_eq!(m[0], 0);
}

#[test]
fn generated_slice_search() {
    let m = base();
    let sl = m.as_slice();
    assert_eq!(sl.binary_search_keys(&"d"), Ok(3));
    assert_eq!(sl.binary_search_keys(&"aa"), Err(1));
    assert_eq!(sl.binary_search_by(|_, v| v.cmp(&2)), Ok(1));
    assert_eq!(sl.binary_search_by_key(&5, |_, v| *v), Ok(4));
    assert_eq!(sl.partition_point(|_, v| *v < 3), 2);
}

#[test]
fn generated_slice_equality_is_order_sensitive() {
    let m1: IndexMap<&str, i32> = [("a", 1), ("b", 2)].into_iter().collect();
    let m2: IndexMap<&str, i32> = [("b", 2), ("a", 1)].into_iter().collect();
    assert_eq!(m1, m2); // containers compare order-insensitively
    assert_ne!(m1.as_slice(), m2.as_slice()); // slices do not
    let m3: IndexMap<&str, i32> = [("a", 1), ("b", 2)].into_iter().collect();
    assert_eq!(m1.as_slice(), m3.as_slice());
}

#[test]
fn generated_slice_ord_lexicographic() {
    let m1: IndexMap<&str, i32> = [("a", 1), ("b", 2)].into_iter().collect();
    let m2: IndexMap<&str, i32> = [("a", 1), ("b", 3)].into_iter().collect();
    let m3: IndexMap<&str, i32> = [("a", 1)].into_iter().collect();
    assert!(m1.as_slice() < m2.as_slice());
    assert!(m3.as_slice() < m1.as_slice()); // prefix compares less
}

#[test]
fn generated_slice_hash_and_debug() {
    use std::collections::hash_map::DefaultHasher;
    let m1: IndexMap<&str, i32> = [("a", 1), ("b", 2)].into_iter().collect();
    let m2: IndexMap<&str, i32> = [("a", 1), ("b", 2)].into_iter().collect();
    let h = |sl: &indexmap::map::Slice<&str, i32>| {
        let mut hasher = DefaultHasher::new();
        sl.hash(&mut hasher);
        hasher.finish()
    };
    assert_eq!(h(m1.as_slice()), h(m2.as_slice()));
    assert_eq!(format!("{:?}", m1.as_slice()), r#"[("a", 1), ("b", 2)]"#);
    let s: IndexSet<i32> = [3, 1].into_iter().collect();
    assert_eq!(format!("{:?}", s.as_slice()), "[3, 1]");
}

#[test]
fn generated_into_boxed_slice() {
    let m = base();
    let boxed = m.into_boxed_slice();
    assert_eq!(boxed.len(), 5);
    assert_eq!(boxed.get_index(0), Some((&"a", &1)));
    let keys: Vec<_> = boxed.into_keys().collect();
    assert_eq!(keys, ["a", "b", "c", "d", "e"]);
    let vals: Vec<_> = base().into_boxed_slice().into_values().collect();
    assert_eq!(vals, [1, 2, 3, 4, 5]);
    let s: IndexSet<i32> = [9, 7].into_iter().collect();
    let bs = s.into_boxed_slice();
    assert_eq!(bs.get_index(1), Some(&7));
}
