// Reordering and positioned insertion: move_index arithmetic,
// swap_indices, reverse, shift_insert vs insert_before laws.

#[test]
fn generated_move_index_forward() {
    let mut m = base();
    m.move_index(0, 3); // "a" ends at position 3
    assert_eq!(key_list(&m), ["b", "c", "d", "a", "e"]);
}

#[test]
fn generated_move_index_backward() {
    let mut m = base();
    m.move_index(4, 1); // "e" ends at position 1
    assert_eq!(key_list(&m), ["a", "e", "b", "c", "d"]);
}

#[test]
fn generated_move_index_panics_out_of_bounds() {
    assert!(catches(|| {
        let mut m = base();
        m.move_index(5, 0);
    }));
    assert!(catches(|| {
        let mut m = base();
        m.move_index(0, 5);
    }));
}

#[test]
fn generated_swap_indices_exchanges() {
    let mut m = base();
    m.swap_indices(0, 4);
    assert_eq!(key_list(&m), ["e", "b", "c", "d", "a"]);
    m.swap_indices(2, 2); // no-op when equal
    assert_eq!(key_list(&m), ["e", "b", "c", "d", "a"]);
}

#[test]
fn generated_swap_indices_panics_out_of_bounds() {
    assert!(catches(|| {
        let mut m = base();
        m.swap_indices(0, 5);
    }));
    assert!(catches(|| {
        let mut m = base();
        m.swap_indices(9, 1);
    }));
}

#[test]
fn generated_reverse_in_place() {
    let mut m = base();
    m.reverse();
    assert_eq!(key_list(&m), ["e", "d", "c", "b", "a"]);
    assert_eq!(m.get_index_of("a"), Some(4));
}

#[test]
fn generated_shift_insert_new_key() {
    let mut m = base();
    assert_eq!(m.shift_insert(2, "x", 9), None);
    assert_eq!(key_list(&m), ["a", "b", "x", "c", "d", "e"]);
    // a new key may go at index == len (append):
    let mut m = base();
    assert_eq!(m.shift_insert(5, "x", 9), None);
    assert_eq!(key_list(&m), ["a", "b", "c", "d", "e", "x"]);
}

#[test]
fn generated_shift_insert_existing_key_moves() {
    let mut m = base();
    assert_eq!(m.shift_insert(1, "e", 50), Some(5));
    assert_eq!(key_list(&m), ["a", "e", "b", "c", "d"]);
    assert_eq!(m.get("e"), Some(&50));
}

#[test]
fn generated_shift_insert_panics() {
    // index == len is invalid for an existing key:
    assert!(catches(|| {
        let mut m = base();
        m.shift_insert(5, "a", 0);
    }));
    // index > len is invalid for any key:
    assert!(catches(|| {
        let mut m = base();
        m.shift_insert(6, "zz", 0);
    }));
}

#[test]
fn generated_insert_before_new_key() {
    let mut m = base();
    assert_eq!(m.insert_before(2, "x", 9), (2, None));
    assert_eq!(key_list(&m), ["a", "b", "x", "c", "d", "e"]);
    // index == len means "at the end":
    let mut m = base();
    assert_eq!(m.insert_before(5, "x", 9), (5, None));
    assert_eq!(key_list(&m), ["a", "b", "c", "d", "e", "x"]);
}

#[test]
fn generated_insert_before_existing_key_positions() {
    // key currently before the target: final position is index - 1
    let mut m = base();
    assert_eq!(m.insert_before(3, "a", 10), (2, Some(1)));
    assert_eq!(key_list(&m), ["b", "c", "a", "d", "e"]);
    // key currently at/after the target: final position is index
    let mut m = base();
    assert_eq!(m.insert_before(1, "e", 50), (1, Some(5)));
    assert_eq!(key_list(&m), ["a", "e", "b", "c", "d"]);
}

#[test]
fn generated_insert_before_panics_past_len() {
    assert!(catches(|| {
        let mut m = base();
        m.insert_before(6, "x", 0);
    }));
}

#[test]
fn generated_insert_sorted_map() {
    let mut m = base(); // keys already sorted a..e
    assert_eq!(m.insert_sorted("cc", 35), (3, None));
    assert_eq!(key_list(&m), ["a", "b", "c", "cc", "d", "e"]);
    // existing key keeps its index, value changes:
    assert_eq!(m.insert_sorted("b", 20), (1, Some(2)));
    assert_eq!(m.get("b"), Some(&20));
    assert_eq!(m.len(), 6);
}
