// Iteration: sequence order across every view, double-ended and
// exact-size contracts, consuming iterators.

#[test]
fn generated_iteration_orders() {
    let m = base();
    assert_eq!(
        m.iter().collect::<Vec<_>>(),
        [(&"a", &1), (&"b", &2), (&"c", &3), (&"d", &4), (&"e", &5)]
    );
    assert_eq!(m.keys().collect::<Vec<_>>(), [&"a", &"b", &"c", &"d", &"e"]);
    assert_eq!(m.values().collect::<Vec<_>>(), [&1, &2, &3, &4, &5]);
    let by_ref: Vec<_> = (&m).into_iter().map(|(k, _)| *k).collect();
    assert_eq!(by_ref, ["a", "b", "c", "d", "e"]);
    let s: IndexSet<i32> = [9, 7, 8].into_iter().collect();
    assert_eq!(s.iter().collect::<Vec<_>>(), [&9, &7, &8]);
}

#[test]
fn generated_mutable_iteration() {
    let mut m = base();
    for (_, v) in m.iter_mut() {
        *v *= 2;
    }
    for v in m.values_mut() {
        *v += 1;
    }
    assert_eq!(m.values().collect::<Vec<_>>(), [&3, &5, &7, &9, &11]);
}

#[test]
fn generated_consuming_iterators() {
    let keys: Vec<_> = base().into_keys().collect();
    assert_eq!(keys, ["a", "b", "c", "d", "e"]);
    let vals: Vec<_> = base().into_values().collect();
    assert_eq!(vals, [1, 2, 3, 4, 5]);
    let pairs: Vec<_> = base().into_iter().collect();
    assert_eq!(pairs[0], ("a", 1));
    assert_eq!(pairs[4], ("e", 5));
    let s: IndexSet<i32> = [9, 7].into_iter().collect();
    let sv: Vec<_> = s.into_iter().collect();
    assert_eq!(sv, [9, 7]);
}

#[test]
fn generated_double_ended_iteration() {
    let m = base();
    let mut it = m.iter();
    assert_eq!(it.next(), Some((&"a", &1)));
    assert_eq!(it.next_back(), Some((&"e", &5)));
    assert_eq!(it.next_back(), Some((&"d", &4)));
    assert_eq!(it.next(), Some((&"b", &2)));
    let mut keys = m.keys();
    assert_eq!(keys.next_back(), Some(&"e"));
    let rev: Vec<_> = m.values().rev().collect();
    assert_eq!(rev, [&5, &4, &3, &2, &1]);
    let s: IndexSet<i32> = [9, 7, 8].into_iter().collect();
    assert_eq!(s.iter().next_back(), Some(&8));
}

#[test]
fn generated_exact_size_and_fused() {
    let m = base();
    let mut it = m.iter();
    assert_eq!(it.len(), 5);
    it.next();
    assert_eq!(it.len(), 4);
    let mut short = m.iter().skip(4);
    assert!(short.next().is_some());
    assert_eq!(short.next(), None);
    assert_eq!(short.next(), None); // still None after exhaustion
    let mut ks = m.keys();
    for _ in 0..5 {
        ks.next();
    }
    assert_eq!(ks.next(), None);
    assert_eq!(ks.next(), None);
}
