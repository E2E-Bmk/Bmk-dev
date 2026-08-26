// Removal: the swap back-fill law, the shift closure law, deprecated
// aliases, pop, and failed removals.

#[test]
fn generated_swap_remove_backfill() {
    let mut m = base();
    assert_eq!(m.swap_remove("c"), Some(3));
    // the last entry (e) moved into c's slot:
    assert_eq!(key_list(&m), ["a", "b", "e", "d"]);
    assert_eq!(m.get_index_of("e"), Some(2));
}

#[test]
fn generated_swap_remove_last_moves_nothing() {
    let mut m = base();
    assert_eq!(m.swap_remove("e"), Some(5));
    assert_eq!(key_list(&m), ["a", "b", "c", "d"]);
}

#[test]
fn generated_swap_remove_variants() {
    let mut m = base();
    assert_eq!(m.swap_remove_entry("b"), Some(("b", 2)));
    assert_eq!(key_list(&m), ["a", "e", "c", "d"]);
    let mut m = base();
    assert_eq!(m.swap_remove_full("b"), Some((1, "b", 2)));
    let mut m = base();
    assert_eq!(m.swap_remove_index(1), Some(("b", 2)));
    assert_eq!(key_list(&m), ["a", "e", "c", "d"]);
    assert_eq!(m.swap_remove_index(10), None);
}

#[test]
fn generated_shift_remove_preserves_order() {
    let mut m = base();
    assert_eq!(m.shift_remove("b"), Some(2));
    assert_eq!(key_list(&m), ["a", "c", "d", "e"]);
    // indices after the hole shifted down:
    assert_eq!(m.get_index_of("c"), Some(1));
    assert_eq!(m.get_index_of("e"), Some(3));
}

#[test]
fn generated_shift_remove_variants() {
    let mut m = base();
    assert_eq!(m.shift_remove_entry("b"), Some(("b", 2)));
    assert_eq!(key_list(&m), ["a", "c", "d", "e"]);
    let mut m = base();
    assert_eq!(m.shift_remove_full("b"), Some((1, "b", 2)));
    let mut m = base();
    assert_eq!(m.shift_remove_index(2), Some(("c", 3)));
    assert_eq!(key_list(&m), ["a", "b", "d", "e"]);
    assert_eq!(m.shift_remove_index(10), None);
}

#[test]
#[allow(deprecated)]
fn generated_deprecated_aliases_swap() {
    let mut m = base();
    assert_eq!(m.remove("c"), Some(3));
    assert_eq!(key_list(&m), ["a", "b", "e", "d"]); // swap law
    let mut m = base();
    assert_eq!(m.remove_entry("c"), Some(("c", 3)));
    assert_eq!(key_list(&m), ["a", "b", "e", "d"]);
}

#[test]
fn generated_pop_removes_last() {
    let mut m = base();
    assert_eq!(m.pop(), Some(("e", 5)));
    assert_eq!(m.len(), 4);
    let mut empty: IndexMap<&str, i32> = IndexMap::new();
    assert_eq!(empty.pop(), None);
}

#[test]
fn generated_failed_removals_leave_map() {
    let mut m = base();
    assert_eq!(m.swap_remove("zz"), None);
    assert_eq!(m.shift_remove("zz"), None);
    assert_eq!(m.swap_remove_full("zz"), None);
    assert_eq!(key_list(&m), ["a", "b", "c", "d", "e"]);
    assert_eq!(m.len(), 5);
}

#[test]
fn generated_single_entry_removal() {
    let mut m: IndexMap<&str, i32> = [("only", 1)].into_iter().collect();
    assert_eq!(m.swap_remove("only"), Some(1));
    assert!(m.is_empty());
}
