// The entry interface: Entry, OccupiedEntry, VacantEntry, IndexedEntry.

#[test]
fn generated_entry_variants_and_index() {
    let mut m = base();
    match m.entry("c") {
        Entry::Occupied(e) => {
            assert_eq!(e.index(), 2);
            assert_eq!(e.key(), &"c");
            assert_eq!(e.get(), &3);
        }
        Entry::Vacant(_) => panic!("expected occupied"),
    }
    match m.entry("x") {
        Entry::Vacant(e) => {
            // a vacant entry's index is the position it would occupy
            assert_eq!(e.index(), 5);
            assert_eq!(e.key(), &"x");
        }
        Entry::Occupied(_) => panic!("expected vacant"),
    }
    assert_eq!(m.entry("a").index(), 0);
    assert_eq!(m.entry("zz").index(), 5);
}

#[test]
fn generated_or_insert_family() {
    let mut m = base();
    *m.entry("x").or_insert(9) += 1; // vacant: inserts, returns &mut
    assert_eq!(m.get("x"), Some(&10));
    *m.entry("a").or_insert(0) += 100; // occupied: keeps stored value
    assert_eq!(m.get("a"), Some(&101));
    assert_eq!(*m.entry("y").or_insert_with(|| 7), 7);
    assert_eq!(*m.entry("zzz").or_insert_with_key(|k| k.len() as i32), 3);
    assert_eq!(*m.entry("w").or_default(), 0);
    assert_eq!(key_list(&m), ["a", "b", "c", "d", "e", "x", "y", "zzz", "w"]);
}

#[test]
fn generated_and_modify_chain() {
    let mut m = base();
    m.entry("b").and_modify(|v| *v *= 10).or_insert(0);
    assert_eq!(m.get("b"), Some(&20)); // modified, not re-inserted
    m.entry("x").and_modify(|v| *v *= 10).or_insert(7);
    assert_eq!(m.get("x"), Some(&7)); // vacant: closure never ran
}

#[test]
fn generated_entry_insert_entry() {
    let mut m = base();
    let e = m.entry("x").insert_entry(9);
    assert_eq!(e.index(), 5);
    assert_eq!(e.get(), &9);
    let e = m.entry("a").insert_entry(100); // replace on occupied
    assert_eq!(e.index(), 0);
    assert_eq!(e.get(), &100);
}

#[test]
fn generated_occupied_accessors() {
    let mut m = base();
    if let Entry::Occupied(mut e) = m.entry("c") {
        *e.get_mut() += 1;
        assert_eq!(e.insert(30), 4); // swap in, old value back
        let v: &mut i32 = e.into_mut();
        *v += 1;
    } else {
        panic!("expected occupied");
    }
    assert_eq!(m.get("c"), Some(&31));
}

#[test]
fn generated_occupied_removals() {
    let mut m = base();
    if let Entry::Occupied(e) = m.entry("c") {
        assert_eq!(e.swap_remove(), 3);
    }
    assert_eq!(key_list(&m), ["a", "b", "e", "d"]); // swap law
    let mut m = base();
    if let Entry::Occupied(e) = m.entry("b") {
        assert_eq!(e.shift_remove_entry(), ("b", 2));
    }
    assert_eq!(key_list(&m), ["a", "c", "d", "e"]); // shift law
    let mut m = base();
    if let Entry::Occupied(e) = m.entry("b") {
        assert_eq!(e.swap_remove_entry(), ("b", 2));
    }
    assert_eq!(key_list(&m), ["a", "e", "c", "d"]);
    let mut m = base();
    if let Entry::Occupied(e) = m.entry("b") {
        assert_eq!(e.shift_remove(), 2);
    }
    assert_eq!(key_list(&m), ["a", "c", "d", "e"]);
}

#[test]
fn generated_occupied_reorder() {
    let mut m = base();
    if let Entry::Occupied(e) = m.entry("c") {
        e.move_index(0);
    }
    assert_eq!(key_list(&m), ["c", "a", "b", "d", "e"]);
    let mut m = base();
    if let Entry::Occupied(e) = m.entry("a") {
        e.swap_indices(4);
    }
    assert_eq!(key_list(&m), ["e", "b", "c", "d", "a"]);
}

#[test]
fn generated_vacant_operations() {
    let mut m = base();
    if let Entry::Vacant(e) = m.entry("x") {
        assert_eq!(e.into_key(), "x");
    }
    assert_eq!(m.len(), 5); // into_key inserts nothing
    if let Entry::Vacant(e) = m.entry("x") {
        let v = e.insert(9);
        *v += 1;
    }
    assert_eq!(m.get_full("x"), Some((5, &"x", &10)));
    if let Entry::Vacant(e) = m.entry("y") {
        let oe = e.insert_entry(7);
        assert_eq!(oe.index(), 6);
    }
    assert_eq!(m.get("y"), Some(&7));
}

#[test]
fn generated_vacant_positioned_inserts() {
    let mut m = base();
    if let Entry::Vacant(e) = m.entry("x") {
        let v = e.shift_insert(0, 9);
        assert_eq!(*v, 9);
    }
    assert_eq!(key_list(&m), ["x", "a", "b", "c", "d", "e"]);
    let mut m = base(); // sorted keys
    if let Entry::Vacant(e) = m.entry("cc") {
        let (i, v) = e.insert_sorted(35);
        assert_eq!((i, *v), (3, 35));
    }
    assert_eq!(key_list(&m), ["a", "b", "c", "cc", "d", "e"]);
}

#[test]
fn generated_indexed_entry_reads_and_writes() {
    let mut m = base();
    assert!(m.get_index_entry(9).is_none());
    {
        let mut e = m.get_index_entry(2).unwrap();
        assert_eq!(e.index(), 2);
        assert_eq!(e.key(), &"c");
        assert_eq!(e.get(), &3);
        *e.get_mut() += 1;
        assert_eq!(e.insert(30), 4); // replace value, old one back
    }
    assert_eq!(m.get("c"), Some(&30));
    let v = m.get_index_entry(0).unwrap().into_mut();
    *v += 100;
    assert_eq!(m.get("a"), Some(&101));
}

#[test]
fn generated_indexed_entry_removals_and_moves() {
    let mut m = base();
    assert_eq!(m.get_index_entry(1).unwrap().swap_remove(), 2);
    assert_eq!(key_list(&m), ["a", "e", "c", "d"]);
    let mut m = base();
    assert_eq!(m.get_index_entry(1).unwrap().shift_remove_entry(), ("b", 2));
    assert_eq!(key_list(&m), ["a", "c", "d", "e"]);
    let mut m = base();
    assert_eq!(m.get_index_entry(1).unwrap().swap_remove_entry(), ("b", 2));
    let mut m = base();
    assert_eq!(m.get_index_entry(1).unwrap().shift_remove(), 2);
    let mut m = base();
    m.get_index_entry(0).unwrap().move_index(4);
    assert_eq!(key_list(&m), ["b", "c", "d", "e", "a"]);
    let mut m = base();
    m.get_index_entry(0).unwrap().swap_indices(4);
    assert_eq!(key_list(&m), ["e", "b", "c", "d", "a"]);
}

#[test]
fn generated_first_and_last_entry() {
    let mut m = base();
    assert_eq!(m.first_entry().unwrap().key(), &"a");
    assert_eq!(m.last_entry().unwrap().key(), &"e");
    let mut empty: IndexMap<&str, i32> = IndexMap::new();
    assert!(empty.first_entry().is_none());
    assert!(empty.last_entry().is_none());
}
