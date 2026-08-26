// Bulk-surgery workflows: splice editing sessions, partial drains,
// sorted-ledger maintenance, and cross-view consistency.

#[test]
fn generated_splice_editor_session() {
    let mut doc: IndexMap<&str, &str> = [
        ("l1", "alpha"),
        ("l2", "beta"),
        ("l3", "gamma"),
        ("l4", "delta"),
    ]
    .into_iter()
    .collect();

    // replace the middle two lines with three new ones
    let cut: Vec<_> = doc
        .splice(1..3, [("l2a", "beta-a"), ("l2b", "beta-b"), ("l2c", "beta-c")])
        .collect();
    assert_eq!(cut, [("l2", "beta"), ("l3", "gamma")]);
    assert_eq!(
        doc.keys().collect::<Vec<_>>(),
        [&"l1", &"l2a", &"l2b", &"l2c", &"l4"]
    );

    // a replacement key living outside the range updates in place
    let cut2: Vec<_> = doc.splice(1..2, [("l4", "DELTA")]).collect();
    assert_eq!(cut2, [("l2a", "beta-a")]);
    assert_eq!(doc.keys().collect::<Vec<_>>(), [&"l1", &"l2b", &"l2c", &"l4"]);
    assert_eq!(doc["l4"], "DELTA");

    // a key removed by the range re-enters at the splice position
    let cut3: Vec<_> = doc.splice(0..1, [("l1", "ALPHA")]).collect();
    assert_eq!(cut3, [("l1", "alpha")]);
    assert_eq!(doc.get_full("l1"), Some((0, &"l1", &"ALPHA")));
    assert_eq!(doc.len(), 4);
}

#[test]
fn generated_partial_drain_bookkeeping() {
    let mut m: IndexMap<&str, i32> = [
        ("a", 1),
        ("b", 2),
        ("c", 3),
        ("d", 4),
        ("e", 5),
        ("f", 6),
    ]
    .into_iter()
    .collect();

    {
        let mut d = m.drain(2..5);
        assert_eq!(d.next(), Some(("c", 3)));
        // dropped here with two entries never consumed
    }

    // the whole range is gone regardless
    assert_eq!(m.keys().collect::<Vec<_>>(), [&"a", &"b", &"f"]);
    assert_eq!(m.len(), 3);
    assert_eq!(m.as_slice().len(), 3);
    assert_eq!(m.get_index(2), Some((&"f", &6)));
    assert_eq!(m.get_index_of("f"), Some(2));
    assert_eq!(m.values().collect::<Vec<_>>(), [&1, &2, &6]);
}

#[test]
fn generated_sorted_ledger_maintenance() {
    let mut ledger: IndexMap<&str, i32> = IndexMap::new();
    for (k, v) in [("m", 3), ("d", 1), ("t", 5), ("f", 2)] {
        ledger.insert_sorted(k, v);
    }
    assert_eq!(ledger.keys().collect::<Vec<_>>(), [&"d", &"f", &"m", &"t"]);
    assert_eq!(ledger.binary_search_keys(&"m"), Ok(2));
    assert_eq!(ledger.binary_search_keys(&"g"), Err(2));

    assert_eq!(ledger.insert_sorted("p", 4), (3, None));
    assert_eq!(
        ledger.keys().collect::<Vec<_>>(),
        [&"d", &"f", &"m", &"p", &"t"]
    );

    // archive everything from "p" onward
    let cut = ledger.partition_point(|k, _| *k < "p");
    assert_eq!(cut, 3);
    let archive = ledger.split_off(cut);
    assert_eq!(ledger.keys().collect::<Vec<_>>(), [&"d", &"f", &"m"]);
    assert_eq!(archive.keys().collect::<Vec<_>>(), [&"p", &"t"]);
    assert_eq!(archive["t"], 5);
}

#[test]
fn generated_cross_view_consistency() {
    let mut m: IndexMap<&str, i32> = [("a", 1), ("b", 2), ("c", 3)].into_iter().collect();
    m.insert("d", 4);
    m.move_index(3, 0); // [d, a, b, c]
    m.swap_remove("a"); // c back-fills: [d, c, b]
    match m.entry("e") {
        Entry::Vacant(v) => {
            v.insert(5);
        }
        Entry::Occupied(_) => panic!("expected vacant"),
    }
    m.reverse(); // [e, b, c, d]

    let expected = [("e", 5), ("b", 2), ("c", 3), ("d", 4)];
    let from_iter: Vec<_> = m.iter().map(|(k, v)| (*k, *v)).collect();
    let from_slice: Vec<_> = m.as_slice().iter().map(|(k, v)| (*k, *v)).collect();
    assert_eq!(from_iter, expected);
    assert_eq!(from_slice, expected);

    for (i, (k, v)) in expected.iter().enumerate() {
        assert_eq!(m.get_index_of(k), Some(i));
        assert_eq!(m.get_index(i), Some((k, v)));
        assert_eq!(m[i], *v);
    }

    let boxed = m.clone().into_boxed_slice();
    assert_eq!(boxed.len(), 4);
    assert_eq!(boxed.into_keys().collect::<Vec<_>>(), ["e", "b", "c", "d"]);
}
