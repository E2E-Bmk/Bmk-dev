// Insertion and lookup: append-or-update law, key-instance preservation,
// the lookup family, positional reads, indexing panics.

#[test]
fn generated_insert_appends_and_updates() {
    let mut m = IndexMap::new();
    assert_eq!(m.insert("a", 1), None);
    assert_eq!(m.insert("b", 2), None);
    assert_eq!(m.insert("a", 10), Some(1)); // update returns the old value
    assert_eq!(m.len(), 2);
    assert_eq!(m.keys().collect::<Vec<_>>(), [&"a", &"b"]); // position kept
    assert_eq!(m.get("a"), Some(&10));
}

#[test]
fn generated_insert_full_reports_index() {
    let mut m = base();
    assert_eq!(m.insert_full("f", 6), (5, None));
    assert_eq!(m.insert_full("a", 10), (0, Some(1)));
}

#[test]
fn generated_insert_keeps_stored_key_instance() {
    let mut m: IndexMap<Ver, i32> = IndexMap::new();
    m.insert(ver(7, 1), 100);
    m.insert(ver(7, 2), 200); // equal key, different tag
    let (k, v) = m.get_key_value(&ver(7, 0)).unwrap();
    assert_eq!(k.tag, 1); // original key instance survives
    assert_eq!(*v, 200); // value updated
}

#[test]
fn generated_lookup_family_agrees() {
    let m = base();
    assert_eq!(m.get("c"), Some(&3));
    assert_eq!(m.get_key_value("c"), Some((&"c", &3)));
    assert_eq!(m.get_full("c"), Some((2, &"c", &3)));
    assert_eq!(m.get_index_of("c"), Some(2));
    assert!(m.contains_key("c"));
    assert_eq!(m.get("zz"), None);
    assert_eq!(m.get_full("zz"), None);
    assert_eq!(m.get_index_of("zz"), None);
    assert!(!m.contains_key("zz"));
}

#[test]
fn generated_mutable_lookups() {
    let mut m = base();
    *m.get_mut("b").unwrap() += 100;
    assert_eq!(m.get("b"), Some(&102));
    let (i, k, v) = m.get_full_mut("c").unwrap();
    assert_eq!((i, *k), (2, "c"));
    *v += 100;
    assert_eq!(m.get("c"), Some(&103));
    assert_eq!(m.get_mut("zz"), None);
}

#[test]
fn generated_positional_reads() {
    let m = base();
    assert_eq!(m.get_index(0), Some((&"a", &1)));
    assert_eq!(m.get_index(4), Some((&"e", &5)));
    assert_eq!(m.get_index(5), None);
    assert_eq!(m.first(), Some((&"a", &1)));
    assert_eq!(m.last(), Some((&"e", &5)));
    let mut m = base();
    *m.get_index_mut(1).unwrap().1 = 20;
    *m.first_mut().unwrap().1 += 1;
    *m.last_mut().unwrap().1 += 1;
    assert_eq!(m.values().collect::<Vec<_>>(), [&2, &20, &3, &4, &6]);
}

#[test]
fn generated_indexing_operators() {
    let m = base();
    assert_eq!(m["d"], 4); // by borrowed key
    assert_eq!(m[2], 3); // by position
    assert_eq!(m.keys()[2], "c"); // Keys supports position indexing
    assert!(catches(std::panic::AssertUnwindSafe(|| {
        let _ = m["zz"];
    })));
    assert!(catches(std::panic::AssertUnwindSafe(|| {
        let _ = m[9];
    })));
}
