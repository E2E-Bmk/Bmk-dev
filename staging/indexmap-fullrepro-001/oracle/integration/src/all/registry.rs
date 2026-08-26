// Configuration-registry workflows: entry-driven overrides, layered
// merges, priority surgery, snapshot/rollback with set-algebra diffs.

#[test]
fn generated_config_registry_lifecycle() {
    let mut reg: IndexMap<&str, &str> = IndexMap::new();
    reg.insert("host", "localhost");
    reg.insert("port", "8080");
    reg.insert("tls", "off");
    reg.insert("log", "info");

    // entry-driven override and addition
    reg.entry("tls").and_modify(|v| *v = "on").or_insert("on");
    reg.entry("retries").or_insert("3");
    assert_eq!(reg.get_index_of("retries"), Some(4));
    assert_eq!(reg["tls"], "on");

    // promote tls to the front of the report
    let i = reg.get_index_of("tls").unwrap();
    reg.move_index(i, 0);
    assert_eq!(
        reg.keys().collect::<Vec<_>>(),
        [&"tls", &"host", &"port", &"log", &"retries"]
    );

    // retire a key without disturbing the rest of the order
    assert_eq!(reg.shift_remove("log"), Some("info"));
    assert_eq!(
        reg.keys().collect::<Vec<_>>(),
        [&"tls", &"host", &"port", &"retries"]
    );

    // paginate by positional ranges
    let page1 = reg.get_range(0..2).unwrap();
    assert_eq!(page1.keys().collect::<Vec<_>>(), [&"tls", &"host"]);
    let page2 = reg.get_range(2..4).unwrap();
    assert_eq!(page2.keys().collect::<Vec<_>>(), [&"port", &"retries"]);
    assert!(reg.get_range(4..6).is_none());

    // both indexing views stay coherent
    assert_eq!(reg[1], "localhost");
    assert_eq!(reg["port"], "8080");
}

#[test]
fn generated_layered_override_merge() {
    let mut effective: IndexMap<&str, i32> =
        [("a", 1), ("b", 2), ("c", 3)].into_iter().collect();
    let mut layer: IndexMap<&str, i32> = [("b", 20), ("d", 40)].into_iter().collect();

    effective.append(&mut layer);
    assert!(layer.is_empty());
    assert_eq!(
        effective.keys().collect::<Vec<_>>(),
        [&"a", &"b", &"c", &"d"]
    );
    assert_eq!(effective["b"], 20); // overridden in place

    effective.extend([("e", 50), ("a", 100)]);
    assert_eq!(
        effective.keys().collect::<Vec<_>>(),
        [&"a", &"b", &"c", &"d", &"e"]
    );
    assert_eq!(effective["a"], 100);

    // container equality ignores order; the slice view does not
    let expected = indexmap! {"e" => 50, "d" => 40, "c" => 3, "b" => 20, "a" => 100};
    assert_eq!(effective, expected);
    assert_ne!(effective.as_slice(), expected.as_slice());
}

#[test]
fn generated_priority_reorder_audit() {
    let mut q: IndexMap<&str, i32> =
        [("t1", 5), ("t2", 3), ("t3", 9), ("t4", 1)].into_iter().collect();

    // bump t4 (currently after the target) before position 1
    assert_eq!(q.insert_before(1, "t4", 2), (1, Some(1)));
    assert_eq!(q.keys().collect::<Vec<_>>(), [&"t1", &"t4", &"t2", &"t3"]);

    // an urgent new task lands exactly at the front
    assert_eq!(q.shift_insert(0, "t0", 8), None);
    assert_eq!(
        q.keys().collect::<Vec<_>>(),
        [&"t0", &"t1", &"t4", &"t2", &"t3"]
    );

    // stable sort by priority, descending
    q.sort_by(|_, a, _, b| b.cmp(a));
    assert_eq!(
        q.keys().collect::<Vec<_>>(),
        [&"t3", &"t0", &"t1", &"t2", &"t4"]
    );

    // switch to key order for binary-searchable lookups
    q.sort_keys();
    assert_eq!(q.binary_search_keys(&"t3"), Ok(3));
    assert_eq!(q.binary_search_keys(&"t9"), Err(5));
    assert_eq!(q.partition_point(|k, _| *k < "t2"), 2);
}

#[test]
fn generated_registry_snapshot_and_rollback() {
    let mut live = indexmap! {"x" => 1, "y" => 2, "z" => 3};
    let snapshot = live.clone();

    live.insert("w", 4);
    live.swap_remove("x"); // w back-fills position 0
    *live.get_mut("y").unwrap() = 20;
    assert_eq!(live.keys().collect::<Vec<_>>(), [&"w", &"y", &"z"]);
    assert_ne!(live, snapshot);

    // diff the key sets deterministically
    let live_keys: IndexSet<&str> = live.keys().copied().collect();
    let snap_keys: IndexSet<&str> = snapshot.keys().copied().collect();
    assert_eq!(live_keys.difference(&snap_keys).collect::<Vec<_>>(), [&"w"]);
    assert_eq!(snap_keys.difference(&live_keys).collect::<Vec<_>>(), [&"x"]);

    // rollback restores content and order
    live = snapshot.clone();
    assert_eq!(live, snapshot);
    assert_eq!(live.as_slice(), snapshot.as_slice());
}
