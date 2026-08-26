// Bulk rewrites: truncate, split_off, drain, splice collision laws,
// append/extend merging, retain.

#[test]
fn generated_truncate_keeps_prefix() {
    let mut m = base();
    m.truncate(3);
    assert_eq!(key_list(&m), ["a", "b", "c"]);
    m.truncate(10); // no-op past the length
    assert_eq!(m.len(), 3);
    m.truncate(0);
    assert!(m.is_empty());
}

#[test]
fn generated_split_off_returns_tail() {
    let mut m = base();
    let tail = m.split_off(2);
    assert_eq!(key_list(&m), ["a", "b"]);
    assert_eq!(key_list(&tail), ["c", "d", "e"]);
    assert_eq!(tail.get("d"), Some(&4));
}

#[test]
fn generated_split_off_panics_past_len() {
    assert!(catches(|| {
        let mut m = base();
        let _ = m.split_off(6);
    }));
}

#[test]
fn generated_drain_yields_in_order() {
    let mut m = base();
    let out: Vec<_> = m.drain(1..3).collect();
    assert_eq!(out, [("b", 2), ("c", 3)]);
    assert_eq!(key_list(&m), ["a", "d", "e"]);
    let mut m = base();
    let all: Vec<_> = m.drain(..).collect();
    assert_eq!(all.len(), 5);
    assert!(m.is_empty());
}

#[test]
fn generated_drain_removes_even_if_dropped() {
    let mut m = base();
    drop(m.drain(1..4)); // iterator dropped before being consumed
    assert_eq!(key_list(&m), ["a", "e"]);
}

#[test]
fn generated_drain_panics_bad_range() {
    assert!(catches(|| {
        let mut m = base();
        let _ = m.drain(1..9);
    }));
    assert!(catches(|| {
        let mut m = base();
        #[allow(clippy::reversed_empty_ranges)]
        let _ = m.drain(3..2);
    }));
}

#[test]
fn generated_splice_replaces_range() {
    let mut m = base();
    let removed: Vec<_> = m.splice(1..3, [("x", 9), ("y", 8)]).collect();
    assert_eq!(removed, [("b", 2), ("c", 3)]);
    assert_eq!(key_list(&m), ["a", "x", "y", "d", "e"]);
}

#[test]
fn generated_splice_outside_key_keeps_position() {
    let mut m = base();
    // "e" already exists outside the range: it keeps its position and
    // only its value updates; it is not inserted into the range.
    let removed: Vec<_> = m.splice(1..3, [("x", 9), ("e", 50)]).collect();
    assert_eq!(removed, [("b", 2), ("c", 3)]);
    assert_eq!(key_list(&m), ["a", "x", "d", "e"]);
    assert_eq!(m.get("e"), Some(&50));
}

#[test]
fn generated_splice_inside_key_reinserted() {
    let mut m = base();
    // "b" is inside the removed range: it comes out of the iterator with
    // its old value and is inserted at the splice position like new.
    let removed: Vec<_> = m.splice(1..3, [("b", 99)]).collect();
    assert_eq!(removed, [("b", 2), ("c", 3)]);
    assert_eq!(key_list(&m), ["a", "b", "d", "e"]);
    assert_eq!(m.get_full("b"), Some((1, &"b", &99)));
}

#[test]
fn generated_append_moves_everything() {
    let mut m1: IndexMap<&str, i32> = [("a", 1), ("b", 2), ("c", 3)].into_iter().collect();
    let mut m2: IndexMap<&str, i32> = [("b", 20), ("x", 9)].into_iter().collect();
    m1.append(&mut m2);
    assert!(m2.is_empty());
    assert_eq!(key_list(&m1), ["a", "b", "c", "x"]); // "b" kept its position
    assert_eq!(m1.get("b"), Some(&20)); // ... with the incoming value
    assert_eq!(m1.get("x"), Some(&9));
}

#[test]
fn generated_extend_per_pair_law() {
    let mut m = base();
    m.extend([("b", 20), ("x", 9)]);
    assert_eq!(key_list(&m), ["a", "b", "c", "d", "e", "x"]);
    assert_eq!(m.get("b"), Some(&20));
}

#[test]
fn generated_retain_preserves_order() {
    let mut m = base();
    m.retain(|_, v| {
        let keep = *v % 2 == 1;
        if keep {
            *v *= 10; // mutable value access during filtering
        }
        keep
    });
    assert_eq!(key_list(&m), ["a", "c", "e"]);
    assert_eq!(m.values().collect::<Vec<_>>(), [&10, &30, &50]);
}
