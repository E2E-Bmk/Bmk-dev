// Set membership, value-identity laws, removal families, and the
// mirrored positional/bulk surface.

fn sbase() -> IndexSet<&'static str> {
    ["a", "b", "c", "d", "e"].into_iter().collect()
}

fn slist(s: &IndexSet<&'static str>) -> Vec<&'static str> {
    s.iter().copied().collect()
}

#[test]
fn generated_set_insert_keeps_original_instance() {
    let mut s: IndexSet<Ver> = IndexSet::new();
    assert!(s.insert(ver(1, 1)));
    assert!(!s.insert(ver(1, 2))); // equal value: refused
    assert_eq!(s.get(&ver(1, 0)).unwrap().tag, 1); // original survives
    assert_eq!(s.insert_full(ver(2, 1)), (1, true));
    assert_eq!(s.insert_full(ver(1, 3)), (0, false));
}

#[test]
fn generated_set_replace_swaps_instance() {
    let mut s: IndexSet<Ver> = [ver(1, 1), ver(2, 1)].into_iter().collect();
    let old = s.replace(ver(1, 9)).unwrap();
    assert_eq!(old.tag, 1); // old instance handed back
    assert_eq!(s.get(&ver(1, 0)).unwrap().tag, 9); // new instance stored
    assert_eq!(s.get_index_of(&ver(1, 0)), Some(0)); // position kept
    assert_eq!(s.replace(ver(3, 1)), None); // absent: appended
    assert_eq!(s.get_index_of(&ver(3, 0)), Some(2));
    let (i, old) = s.replace_full(ver(2, 7));
    assert_eq!((i, old.unwrap().tag), (1, 1));
}

#[test]
fn generated_set_positioned_insertions() {
    let mut s = sbase();
    assert_eq!(s.insert_before(2, "x"), (2, true));
    assert_eq!(slist(&s), ["a", "b", "x", "c", "d", "e"]);
    let mut s = sbase();
    assert_eq!(s.insert_before(3, "a"), (2, false)); // moved from before
    assert_eq!(slist(&s), ["b", "c", "a", "d", "e"]);
    let mut s = sbase();
    assert!(s.shift_insert(1, "x"));
    assert_eq!(slist(&s), ["a", "x", "b", "c", "d", "e"]);
    assert!(!s.shift_insert(0, "e")); // existing value moved
    assert_eq!(slist(&s), ["e", "a", "x", "b", "c", "d"]);
    let mut s = sbase(); // sorted
    assert_eq!(s.insert_sorted("cc"), (3, true));
    assert_eq!(s.insert_sorted("b"), (1, false));
}

#[test]
fn generated_set_membership_reads() {
    let s = sbase();
    assert!(s.contains("c"));
    assert!(!s.contains("zz"));
    assert_eq!(s.get("c"), Some(&"c"));
    assert_eq!(s.get_full("c"), Some((2, &"c")));
    assert_eq!(s.get_index_of("c"), Some(2));
    assert_eq!(s.get_index(0), Some(&"a"));
    assert_eq!(s.get_index(9), None);
    assert_eq!(s.first(), Some(&"a"));
    assert_eq!(s.last(), Some(&"e"));
    assert_eq!(s[1], "b");
    assert!(catches(std::panic::AssertUnwindSafe(|| {
        let _ = s[9];
    })));
}

#[test]
fn generated_set_swap_and_shift_remove() {
    let mut s = sbase();
    assert!(s.swap_remove("b"));
    assert_eq!(slist(&s), ["a", "e", "c", "d"]); // swap law
    assert!(!s.swap_remove("zz"));
    let mut s = sbase();
    assert!(s.shift_remove("b"));
    assert_eq!(slist(&s), ["a", "c", "d", "e"]); // shift law
    assert!(!s.shift_remove("zz"));
}

#[test]
fn generated_set_take_family() {
    let mut s: IndexSet<Ver> = [ver(1, 1), ver(2, 2), ver(3, 3)].into_iter().collect();
    let got = s.swap_take(&ver(1, 0)).unwrap();
    assert_eq!(got.tag, 1); // stored instance comes back
    assert_eq!(s.get_index_of(&ver(3, 0)), Some(0)); // last filled the slot
    let mut s: IndexSet<Ver> = [ver(1, 1), ver(2, 2), ver(3, 3)].into_iter().collect();
    let got = s.shift_take(&ver(1, 0)).unwrap();
    assert_eq!(got.tag, 1);
    assert_eq!(s.get_index_of(&ver(2, 0)), Some(0)); // order preserved
    assert!(s.swap_take(&ver(9, 0)).is_none());
    assert!(s.shift_take(&ver(9, 0)).is_none());
}

#[test]
fn generated_set_full_and_index_removals() {
    let mut s = sbase();
    assert_eq!(s.swap_remove_full("b"), Some((1, "b")));
    assert_eq!(slist(&s), ["a", "e", "c", "d"]);
    let mut s = sbase();
    assert_eq!(s.shift_remove_full("b"), Some((1, "b")));
    assert_eq!(slist(&s), ["a", "c", "d", "e"]);
    let mut s = sbase();
    assert_eq!(s.swap_remove_index(1), Some("b"));
    assert_eq!(slist(&s), ["a", "e", "c", "d"]);
    assert_eq!(s.swap_remove_index(10), None);
    let mut s = sbase();
    assert_eq!(s.shift_remove_index(1), Some("b"));
    assert_eq!(slist(&s), ["a", "c", "d", "e"]);
    assert_eq!(s.shift_remove_index(10), None);
}

#[test]
#[allow(deprecated)]
fn generated_set_deprecated_aliases() {
    let mut s = sbase();
    assert!(s.remove("b")); // alias of swap_remove
    assert_eq!(slist(&s), ["a", "e", "c", "d"]);
    let mut s = sbase();
    assert_eq!(s.take("b"), Some("b")); // alias of swap_take
    assert_eq!(slist(&s), ["a", "e", "c", "d"]);
}

#[test]
fn generated_set_pop_and_clear() {
    let mut s = sbase();
    assert_eq!(s.pop(), Some("e"));
    assert_eq!(s.len(), 4);
    s.clear();
    assert!(s.is_empty());
    assert_eq!(s.pop(), None);
}

#[test]
fn generated_set_bulk_mirror() {
    let mut s = sbase();
    s.truncate(3);
    assert_eq!(slist(&s), ["a", "b", "c"]);
    let mut s = sbase();
    let tail = s.split_off(3);
    assert_eq!(slist(&s), ["a", "b", "c"]);
    assert_eq!(slist(&tail), ["d", "e"]);
    assert!(catches(|| {
        let mut s = sbase();
        let _ = s.split_off(9);
    }));
    let mut s = sbase();
    s.retain(|v| *v != "c");
    assert_eq!(slist(&s), ["a", "b", "d", "e"]);
    let mut s = sbase();
    s.reverse();
    assert_eq!(slist(&s), ["e", "d", "c", "b", "a"]);
    let mut s = sbase();
    s.move_index(0, 3);
    assert_eq!(slist(&s), ["b", "c", "d", "a", "e"]);
    s.swap_indices(0, 4);
    assert_eq!(slist(&s), ["e", "c", "d", "a", "b"]);
}

#[test]
fn generated_set_drain_splice_append() {
    let mut s: IndexSet<i32> = [1, 2, 3, 4, 5].into_iter().collect();
    let out: Vec<_> = s.drain(1..3).collect();
    assert_eq!(out, [2, 3]);
    assert_eq!(s.iter().collect::<Vec<_>>(), [&1, &4, &5]);
    // splice: a replacement equal to a value outside the range keeps
    // that value's position instead of entering the range
    let mut s: IndexSet<i32> = [1, 2, 3, 4, 5].into_iter().collect();
    let removed: Vec<_> = s.splice(1..3, [9, 5]).collect();
    assert_eq!(removed, [2, 3]);
    assert_eq!(s.iter().collect::<Vec<_>>(), [&1, &9, &4, &5]);
    // append: duplicates keep their position, the rest arrive in order
    let mut s1: IndexSet<i32> = [1, 2].into_iter().collect();
    let mut s2: IndexSet<i32> = [2, 7, 8].into_iter().collect();
    s1.append(&mut s2);
    assert!(s2.is_empty());
    assert_eq!(s1.iter().collect::<Vec<_>>(), [&1, &2, &7, &8]);
    let mut s3: IndexSet<i32> = [1].into_iter().collect();
    s3.extend([1, 6]);
    assert_eq!(s3.iter().collect::<Vec<_>>(), [&1, &6]);
}
