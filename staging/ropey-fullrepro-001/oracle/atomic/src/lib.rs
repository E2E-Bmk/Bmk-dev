// Oracle atomic tests for the rope text storage library reconstruction task.
#![cfg(test)]
#![allow(clippy::all)]

use std::borrow::Cow;
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};
use std::io::Cursor;

use ropey::str_utils::{
    byte_to_char_idx, byte_to_line_idx, char_to_byte_idx, char_to_line_idx, line_to_byte_idx,
    line_to_char_idx,
};
use ropey::{Error, Rope, RopeBuilder, RopeSlice};

// Fresh fixture texts (not shared with any upstream test suite).
const PLAIN: &str = "silver otters swim\nunder the old bridge\nnear the mill\n";
const MIXED: &str = "caf\u{e9} \u{3b4}elta \u{6771}\u{4eac} \u{1f680} end";

fn hash_of<T: Hash>(v: &T) -> u64 {
    let mut h = DefaultHasher::new();
    v.hash(&mut h);
    h.finish()
}

// ---------------------------------------------------------------------------
// Construction and I/O
// ---------------------------------------------------------------------------

#[test]
fn generated_new_and_default_are_empty() {
    let a = Rope::new();
    let b = Rope::default();
    assert_eq!(a.len_bytes(), 0);
    assert_eq!(a.len_chars(), 0);
    assert_eq!(a.len_utf16_cu(), 0);
    assert_eq!(a.len_lines(), 1);
    assert_eq!(a, b);
    assert_eq!(String::from(&a), "");
}

#[test]
fn generated_from_str_content_and_display() {
    let r = Rope::from_str(PLAIN);
    assert_eq!(r, PLAIN);
    assert_eq!(format!("{}", r), PLAIN);
    assert_eq!(String::from(&r), PLAIN);
}

#[test]
fn generated_from_conversions_agree() {
    let a = Rope::from(MIXED);
    let b = Rope::from(String::from(MIXED));
    let c = Rope::from(Cow::Borrowed(MIXED));
    let d = Rope::from(a.slice(..));
    assert_eq!(a, b);
    assert_eq!(b, c);
    assert_eq!(c, d);
    assert_eq!(String::from(a), MIXED);
}

#[test]
fn generated_from_iterator_concatenates_in_order() {
    let pieces = ["gale ", "over ", "the ", "harbor"];
    let r: Rope = pieces.iter().copied().collect();
    assert_eq!(r, "gale over the harbor");
    let owned: Rope = pieces.iter().map(|p| p.to_string()).collect();
    assert_eq!(owned, r);
    let cows: Rope = pieces.iter().map(|p| Cow::Borrowed(*p)).collect();
    assert_eq!(cows, r);
}

#[test]
fn generated_builder_matches_from_str() {
    let mut b = RopeBuilder::new();
    b.append("pale ");
    b.append("");
    b.append("morning ");
    b.append("fog\nrolls in\n");
    let built = b.finish();
    let direct = Rope::from_str("pale morning fog\nrolls in\n");
    assert_eq!(built, direct);
    assert_eq!(built.len_lines(), direct.len_lines());
    let empty = RopeBuilder::default().finish();
    assert_eq!(empty, Rope::new());
}

#[test]
fn generated_from_reader_reads_all() {
    let r = Rope::from_reader(Cursor::new(PLAIN.as_bytes())).unwrap();
    assert_eq!(r, PLAIN);
}

#[test]
fn generated_from_reader_invalid_utf8_is_invalid_data() {
    let bad: &[u8] = &[0x70, 0x71, 0xFF, 0xFE, 0x72];
    let err = Rope::from_reader(Cursor::new(bad)).unwrap_err();
    assert_eq!(err.kind(), std::io::ErrorKind::InvalidData);
}

#[test]
fn generated_write_to_emits_exact_bytes() {
    let r = Rope::from_str(MIXED);
    let mut out: Vec<u8> = Vec::new();
    r.write_to(&mut out).unwrap();
    assert_eq!(out, MIXED.as_bytes());
}

#[test]
fn generated_is_instance_distinguishes_clone_from_equal() {
    let orig = Rope::from_str("shared storage");
    let clone = orig.clone();
    let separate = Rope::from_str("shared storage");
    assert!(orig.is_instance(&clone));
    assert!(!orig.is_instance(&separate));
    assert_eq!(orig, separate);
}

#[test]
fn generated_capacity_and_shrink_preserve_content() {
    let mut r = Rope::from_str(PLAIN);
    assert!(r.capacity() >= r.len_bytes());
    let before = r.capacity();
    r.shrink_to_fit();
    assert!(r.capacity() <= before);
    assert!(r.capacity() >= r.len_bytes());
    assert_eq!(r, PLAIN);
}

#[test]
fn generated_string_and_cow_conversions() {
    let r = Rope::from_str("plain run");
    let s1: String = String::from(&r);
    let s2: String = String::from(r.clone());
    assert_eq!(s1, "plain run");
    assert_eq!(s2, "plain run");
    let c: Cow<str> = Cow::from(&r);
    assert_eq!(c.as_ref(), "plain run");
}

// ---------------------------------------------------------------------------
// Metrics
// ---------------------------------------------------------------------------

#[test]
fn generated_len_metrics_ascii() {
    let r = Rope::from_str(PLAIN);
    assert_eq!(r.len_bytes(), PLAIN.len());
    assert_eq!(r.len_chars(), PLAIN.chars().count());
    assert_eq!(r.len_utf16_cu(), PLAIN.encode_utf16().count());
    assert_eq!(r.len_lines(), 4); // three breaks + final empty line
}

#[test]
fn generated_len_metrics_mixed_width() {
    let r = Rope::from_str(MIXED);
    assert_eq!(r.len_bytes(), MIXED.len());
    assert_eq!(r.len_chars(), MIXED.chars().count());
    assert_eq!(r.len_utf16_cu(), MIXED.encode_utf16().count());
    // "café δelta 東京 🚀 end": the rocket is a supplementary-plane char,
    // so UTF-16 length is char count + 1.
    assert_eq!(r.len_utf16_cu(), r.len_chars() + 1);
    assert_eq!(r.len_lines(), 1);
}

// ---------------------------------------------------------------------------
// Coordinate conversions
// ---------------------------------------------------------------------------

#[test]
fn generated_byte_to_char_boundaries_and_interior() {
    let r = Rope::from_str("a\u{e9}z"); // a(1) é(2) z(1) -> 4 bytes, 3 chars
    assert_eq!(r.byte_to_char(0), 0);
    assert_eq!(r.byte_to_char(1), 1);
    assert_eq!(r.byte_to_char(2), 1); // interior of é floors to its char
    assert_eq!(r.byte_to_char(3), 2);
    assert_eq!(r.byte_to_char(4), 3); // one-past-the-end maps to one-past-the-end
}

#[test]
fn generated_char_to_byte_positions() {
    let r = Rope::from_str("a\u{e9}z");
    assert_eq!(r.char_to_byte(0), 0);
    assert_eq!(r.char_to_byte(1), 1);
    assert_eq!(r.char_to_byte(2), 3);
    assert_eq!(r.char_to_byte(3), 4);
}

#[test]
fn generated_line_conversions() {
    let r = Rope::from_str("aa\nbb\ncc");
    assert_eq!(r.byte_to_line(0), 0);
    assert_eq!(r.byte_to_line(3), 1);
    assert_eq!(r.byte_to_line(r.len_bytes()), 2); // one-past-end -> last line
    assert_eq!(r.char_to_line(4), 1);
    assert_eq!(r.char_to_line(r.len_chars()), 2);
    assert_eq!(r.line_to_byte(0), 0);
    assert_eq!(r.line_to_byte(1), 3);
    assert_eq!(r.line_to_byte(2), 6);
    assert_eq!(r.line_to_byte(3), r.len_bytes()); // len_lines() accepted
    assert_eq!(r.line_to_char(3), r.len_chars());
}

#[test]
fn generated_utf16_conversions() {
    let r = Rope::from_str("ab\u{1F600}cd"); // 5 chars, 6 utf16 units
    assert_eq!(r.len_utf16_cu(), 6);
    let expected_c2u = [0usize, 1, 2, 4, 5, 6];
    for (c, u) in expected_c2u.iter().enumerate() {
        assert_eq!(r.char_to_utf16_cu(c), *u);
    }
    let expected_u2c = [0usize, 1, 2, 2, 3, 4, 5];
    for (u, c) in expected_u2c.iter().enumerate() {
        // an offset interior to the surrogate pair resolves to its char
        assert_eq!(r.utf16_cu_to_char(u), *c);
    }
}

#[test]
fn generated_try_conversions_match_panicking_twins() {
    let r = Rope::from_str(PLAIN);
    assert_eq!(r.try_byte_to_char(7).unwrap(), r.byte_to_char(7));
    assert_eq!(r.try_char_to_byte(7).unwrap(), r.char_to_byte(7));
    assert_eq!(r.try_byte_to_line(21).unwrap(), r.byte_to_line(21));
    assert_eq!(r.try_char_to_line(21).unwrap(), r.char_to_line(21));
    assert_eq!(r.try_line_to_byte(2).unwrap(), r.line_to_byte(2));
    assert_eq!(r.try_line_to_char(2).unwrap(), r.line_to_char(2));
    assert_eq!(r.try_char_to_utf16_cu(5).unwrap(), r.char_to_utf16_cu(5));
    assert_eq!(r.try_utf16_cu_to_char(5).unwrap(), r.utf16_cu_to_char(5));
}

#[test]
fn generated_try_conversion_error_payloads() {
    let r = Rope::from_str("abc");
    assert!(matches!(
        r.try_byte_to_char(9),
        Err(Error::ByteIndexOutOfBounds(9, 3))
    ));
    assert!(matches!(
        r.try_char_to_byte(7),
        Err(Error::CharIndexOutOfBounds(7, 3))
    ));
    assert!(matches!(
        r.try_line_to_byte(4),
        Err(Error::LineIndexOutOfBounds(4, 1))
    ));
    assert!(matches!(
        r.try_utf16_cu_to_char(11),
        Err(Error::Utf16IndexOutOfBounds(11, 3))
    ));
}

#[test]
fn generated_error_display_names_index_and_length() {
    let r = Rope::from_str("abc");
    let err = r.try_byte_to_char(9).unwrap_err();
    let msg = format!("{}", err);
    assert!(msg.contains('9'));
    assert!(msg.contains('3'));
    let dbg = format!("{:?}", err);
    assert!(dbg.contains('9'));
    assert!(dbg.contains('3'));
    // Error is Copy + Clone and implements std::error::Error.
    let copied = err;
    let _clone = copied.clone();
    let as_std: &dyn std::error::Error = &err;
    assert!(as_std.source().is_none());
}

// ---------------------------------------------------------------------------
// str_utils flat-string helpers
// ---------------------------------------------------------------------------

#[test]
fn generated_str_utils_byte_char_clamp() {
    let s = "a\u{e9}\u{2028}z"; // bytes: 1 + 2 + 3 + 1 = 7; chars: 4
    assert_eq!(byte_to_char_idx(s, 0), 0);
    assert_eq!(byte_to_char_idx(s, 2), 1); // interior of é
    assert_eq!(byte_to_char_idx(s, 99), 4); // clamps to one-past-the-end
    assert_eq!(char_to_byte_idx(s, 2), 3);
    assert_eq!(char_to_byte_idx(s, 99), 7);
}

#[test]
fn generated_str_utils_line_conversions() {
    let s = "a\u{e9}\u{2028}z"; // LS is a line break under default features
    assert_eq!(byte_to_line_idx(s, 0), 0);
    assert_eq!(byte_to_line_idx(s, 6), 1);
    assert_eq!(byte_to_line_idx(s, 99), 1); // clamps to last line index
    assert_eq!(line_to_byte_idx(s, 0), 0);
    assert_eq!(line_to_byte_idx(s, 1), 6);
    assert_eq!(line_to_byte_idx(s, 99), 7); // clamps to one-past-the-end
    assert_eq!(char_to_line_idx(s, 3), 1);
    assert_eq!(line_to_char_idx(s, 1), 3);
    assert_eq!(line_to_char_idx(s, 99), 4);
}

// ---------------------------------------------------------------------------
// Element and chunk accessors
// ---------------------------------------------------------------------------

#[test]
fn generated_byte_and_char_accessors() {
    let r = Rope::from_str(MIXED);
    assert_eq!(r.byte(0), b'c');
    assert_eq!(r.char(0), 'c');
    assert_eq!(r.char(3), '\u{e9}');
    let last = r.len_chars() - 1;
    assert_eq!(r.char(last), 'd');
    assert_eq!(r.get_byte(r.len_bytes()), None);
    assert_eq!(r.get_char(r.len_chars()), None);
    assert_eq!(r.get_char(3), Some('\u{e9}'));
}

#[test]
fn generated_line_accessor_includes_terminator() {
    let r = Rope::from_str(PLAIN);
    assert_eq!(r.line(0), "silver otters swim\n");
    assert_eq!(r.line(1), "under the old bridge\n");
    assert_eq!(r.line(2), "near the mill\n");
    assert_eq!(r.line(3), ""); // trailing break -> empty last line
    assert_eq!(r.get_line(4), None);
    let no_trail = Rope::from_str("aa\nbb");
    assert_eq!(no_trail.line(1), "bb");
}

#[test]
fn generated_chunk_at_byte_invariants() {
    let r = Rope::from_str(PLAIN);
    for &b in &[0usize, 7, 20, PLAIN.len() - 1, PLAIN.len()] {
        let (chunk, cb, cc, cl) = r.chunk_at_byte(b);
        assert!(cb <= b);
        // The chunk starts at the reported coordinates...
        assert_eq!(r.byte_to_char(cb), cc);
        assert_eq!(r.byte_to_line(cb), cl);
        // ...and contains the queried byte (or is the last chunk at the end).
        if b < r.len_bytes() {
            assert!(b < cb + chunk.len());
            assert_eq!(chunk.as_bytes()[b - cb], PLAIN.as_bytes()[b]);
        }
        // The chunk text is a slice of the content at its offset.
        assert_eq!(&PLAIN[cb..cb + chunk.len()], chunk);
    }
}

#[test]
fn generated_chunk_at_char_and_line_break() {
    let r = Rope::from_str(PLAIN);
    let (chunk, cb, cc, _cl) = r.chunk_at_char(10);
    assert_eq!(r.char_to_byte(cc), cb);
    assert_eq!(&PLAIN[cb..cb + chunk.len()], chunk);

    // Beginning and end count as breaks for chunk_at_line_break indexing.
    let (first, fb, ..) = r.chunk_at_line_break(0);
    assert_eq!(fb, 0);
    assert!(first.as_bytes()[0] == PLAIN.as_bytes()[0]);
    let (last, lb, ..) = r.chunk_at_line_break(r.len_lines());
    assert_eq!(&PLAIN[lb..lb + last.len()], last);
    assert!(lb + last.len() == PLAIN.len());
    assert!(r.get_chunk_at_line_break(r.len_lines() + 1).is_none());
}

#[test]
fn generated_chunk_accessor_fallible_twins() {
    let r = Rope::from_str("abc");
    assert!(r.get_chunk_at_byte(4).is_none());
    assert!(r.get_chunk_at_char(4).is_none());
    let s = r.slice(..);
    assert!(matches!(
        s.try_chunk_at_byte(9),
        Err(Error::ByteIndexOutOfBounds(9, 3))
    ));
    assert!(s.try_chunk_at_byte(3).is_ok());
    assert!(s.get_chunk_at_char(1).is_some());
}

#[test]
fn generated_empty_rope_chunks() {
    let r = Rope::new();
    assert_eq!(r.chunks().count(), 0);
    let (chunk, b, c, l) = r.chunk_at_byte(0);
    assert_eq!((chunk, b, c, l), ("", 0, 0, 0));
}

// ---------------------------------------------------------------------------
// Editing
// ---------------------------------------------------------------------------

#[test]
fn generated_insert_positions() {
    let mut r = Rope::from_str("lighthouse");
    r.insert(0, ">> ");
    assert_eq!(r, ">> lighthouse");
    r.insert(r.len_chars(), " <<");
    assert_eq!(r, ">> lighthouse <<");
    r.insert(3, "old ");
    assert_eq!(r, ">> old lighthouse <<");
}

#[test]
fn generated_insert_empty_and_char() {
    let mut r = Rope::from_str("dune");
    r.insert(2, "");
    assert_eq!(r, "dune");
    r.insert_char(4, '!');
    assert_eq!(r, "dune!");
    r.insert_char(0, '\u{1F680}');
    assert_eq!(r, "\u{1F680}dune!");
    assert_eq!(r.len_chars(), 6);
}

#[test]
fn generated_remove_range_forms() {
    let mut r = Rope::from_str("abcdefgh");
    r.remove(1..=3); // inclusive form
    assert_eq!(r, "aefgh");
    r.remove(2..2); // empty range no-op
    assert_eq!(r, "aefgh");
    r.remove(..2);
    assert_eq!(r, "fgh");
    r.remove(1..);
    assert_eq!(r, "f");
    r.remove(..);
    assert_eq!(r, "");
    assert_eq!(r.len_lines(), 1);
}

#[test]
fn generated_split_off_boundaries() {
    let mut r = Rope::from_str("first!second");
    let tail = r.split_off(6);
    assert_eq!(r, "first!");
    assert_eq!(tail, "second");

    let mut all = Rope::from_str("whole");
    let moved = all.split_off(0);
    assert_eq!(all, "");
    assert_eq!(moved, "whole");

    let mut none = Rope::from_str("keep");
    let empty = none.split_off(none.len_chars());
    assert_eq!(none, "keep");
    assert_eq!(empty, "");
}

#[test]
fn generated_append_cases() {
    let mut r = Rope::from_str("tide");
    r.append(Rope::from_str(" pool"));
    assert_eq!(r, "tide pool");
    r.append(Rope::new());
    assert_eq!(r, "tide pool");
    let mut e = Rope::new();
    e.append(Rope::from_str("late start"));
    assert_eq!(e, "late start");
}

#[test]
fn generated_edit_error_payloads() {
    let mut r = Rope::from_str("abc");
    assert!(matches!(
        r.try_insert(9, "x"),
        Err(Error::CharIndexOutOfBounds(9, 3))
    ));
    assert!(matches!(
        r.try_insert_char(9, 'x'),
        Err(Error::CharIndexOutOfBounds(9, 3))
    ));
    assert!(matches!(
        r.try_remove(3..1),
        Err(Error::CharRangeInvalid(3, 1))
    ));
    assert!(matches!(
        r.try_remove(5..),
        Err(Error::CharRangeOutOfBounds(Some(5), None, 3))
    ));
    assert!(matches!(
        r.try_split_off(7),
        Err(Error::CharIndexOutOfBounds(7, 3))
    ));
    assert_eq!(r, "abc"); // failed edits leave content untouched
}

#[test]
fn generated_clone_is_independent_of_edits() {
    let mut r = Rope::from_str("stable base");
    let snapshot = r.clone();
    r.insert(6, "wide ");
    r.remove(0..2);
    assert_eq!(snapshot, "stable base");
    assert_ne!(r, snapshot);
}

// ---------------------------------------------------------------------------
// Slicing
// ---------------------------------------------------------------------------

#[test]
fn generated_slice_basicforms() {
    let r = Rope::from_str(PLAIN);
    assert_eq!(r.slice(..), r);
    let s = r.slice(19..39);
    assert_eq!(s, "under the old bridge");
    assert_eq!(s.len_chars(), 20);
    let empty = r.slice(4..4);
    assert_eq!(empty, "");
    assert_eq!(empty.len_lines(), 1);
}

#[test]
fn generated_slice_error_twins() {
    let r = Rope::from_str("abcdef");
    assert!(r.get_slice(4..2).is_none()); // reversed
    assert!(r.get_slice(2..9).is_none()); // out of bounds
    assert!(r.get_slice(2..4).is_some());
}

#[test]
fn generated_byte_slice_and_boundaries() {
    let r = Rope::from_str("a\u{e9}z rest");
    assert_eq!(r.byte_slice(0..4), "a\u{e9}z");
    assert!(r.get_byte_slice(1..2).is_none()); // start ok, end interior? no: 2 is interior of é
    assert!(r.get_byte_slice(2..4).is_none()); // start interior to é
    assert!(r.get_byte_slice(0..99).is_none()); // out of bounds
    assert!(r.get_byte_slice(4..1).is_none()); // reversed
    assert_eq!(r.byte_slice(..), r.slice(..));
}

#[test]
fn generated_slice_of_slice_composes() {
    let r = Rope::from_str("0123456789");
    let outer = r.slice(2..9); // "2345678"
    let inner = outer.slice(1..4); // "345"
    assert_eq!(inner, "345");
    assert_eq!(inner, r.slice(3..6));
}

#[test]
fn generated_ropeslice_from_str_backed() {
    let s = RopeSlice::from("flat backing text");
    assert_eq!(s.len_chars(), 17);
    assert_eq!(s.as_str(), Some("flat backing text"));
    assert_eq!(s.line(0), "flat backing text");
    let sub = s.slice(5..12);
    assert_eq!(sub, "backing");
    let r = Rope::from_str("x");
    assert_eq!(r.slice(0..0).as_str(), Some(""));
}

#[test]
fn generated_slice_conversions_out() {
    let r = Rope::from_str("harbor lights");
    let s = r.slice(7..13);
    assert_eq!(String::from(s), "lights");
    let c: Cow<str> = Cow::from(s);
    assert_eq!(c.as_ref(), "lights");
    let back: Rope = Rope::from(s);
    assert_eq!(back, "lights");
    assert!(!back.is_instance(&r));
}

#[test]
fn generated_slice_read_surface_local_coords() {
    let r = Rope::from_str("aa\nbb\ncc\ndd");
    let s = r.slice(3..8); // "bb\ncc"
    assert_eq!(s.len_bytes(), 5);
    assert_eq!(s.len_lines(), 2);
    assert_eq!(s.byte_to_line(4), 1);
    assert_eq!(s.line_to_char(1), 3);
    assert_eq!(s.char(0), 'b');
    assert_eq!(s.line(0), "bb\n");
    assert_eq!(s.line(1), "cc");
    assert!(matches!(
        s.try_char_to_byte(9),
        Err(Error::CharIndexOutOfBounds(9, 5))
    ));
}

// ---------------------------------------------------------------------------
// Line semantics
// ---------------------------------------------------------------------------

#[test]
fn generated_line_partition_rules() {
    assert_eq!(Rope::from_str("alpha\nbeta").len_lines(), 2);
    assert_eq!(Rope::from_str("alpha\nbeta\n").len_lines(), 3);
    assert_eq!(Rope::from_str("").len_lines(), 1);
    let r = Rope::from_str("alpha\nbeta\n");
    assert_eq!(r.line(0), "alpha\n");
    assert_eq!(r.line(1), "beta\n");
    assert_eq!(r.line(2), "");
}

#[test]
fn generated_unicode_line_breaks_recognized() {
    // VT, FF, NEL, LS, PS, lone CR, CRLF, LF
    let doc = Rope::from_str("a\u{000B}b\u{000C}c\u{0085}d\u{2028}e\u{2029}f\rg\r\nh\nend");
    assert_eq!(doc.len_lines(), 9);
    assert_eq!(doc.line(0), "a\u{000B}");
    assert_eq!(doc.line(2), "c\u{0085}");
    assert_eq!(doc.line(3), "d\u{2028}");
    assert_eq!(doc.line(5), "f\r");
    assert_eq!(doc.line(6), "g\r\n");
    assert_eq!(doc.line(8), "end");
}

#[test]
fn generated_crlf_is_single_break() {
    let r = Rope::from_str("one\r\ntwo\r\n");
    assert_eq!(r.len_lines(), 3);
    assert_eq!(r.line(0), "one\r\n");
    assert_eq!(r.byte_to_line(4), 0); // the LF of the pair still ends line 0
    assert_eq!(r.line_to_byte(1), 5);
}

// ---------------------------------------------------------------------------
// Iterators
// ---------------------------------------------------------------------------

#[test]
fn generated_bytes_iter_and_len() {
    let r = Rope::from_str(MIXED);
    let collected: Vec<u8> = r.bytes().collect();
    assert_eq!(collected, MIXED.as_bytes());
    let mut it = r.bytes();
    assert_eq!(it.len(), MIXED.len());
    it.next();
    assert_eq!(it.len(), MIXED.len() - 1);
}

#[test]
fn generated_chars_iter_and_len() {
    let r = Rope::from_str(MIXED);
    let collected: String = r.chars().collect();
    assert_eq!(collected, MIXED);
    assert_eq!(r.chars().len(), MIXED.chars().count());
}

#[test]
fn generated_lines_iter_matches_line_accessor() {
    let r = Rope::from_str(PLAIN);
    let seq: Vec<String> = r.lines().map(String::from).collect();
    let expected: Vec<String> = (0..r.len_lines()).map(|i| String::from(r.line(i))).collect();
    assert_eq!(seq, expected);
    assert_eq!(r.lines().len(), r.len_lines());
}

#[test]
fn generated_chunks_concat_is_content() {
    let r = Rope::from_str(PLAIN);
    let concat: String = r.chunks().collect();
    assert_eq!(concat, PLAIN);
}

#[test]
fn generated_positioned_iterators() {
    let r = Rope::from_str("stone\ncairn\n");
    let mut b = r.bytes_at(6);
    assert_eq!(b.next(), Some(b'c'));
    let mut c = r.chars_at(6);
    assert_eq!(c.next(), Some('c'));
    let mut l = r.lines_at(1);
    assert_eq!(l.next().map(String::from).as_deref(), Some("cairn\n"));
    // At-the-end constructors yield None on next().
    assert_eq!(r.bytes_at(r.len_bytes()).next(), None);
    assert_eq!(r.chars_at(r.len_chars()).next(), None);
    assert_eq!(r.lines_at(r.len_lines()).next(), None);
    // Fallible twins.
    assert!(r.get_bytes_at(r.len_bytes() + 1).is_none());
    assert!(r.get_chars_at(r.len_chars() + 1).is_none());
    assert!(r.get_lines_at(r.len_lines() + 1).is_none());
}

#[test]
fn generated_prev_walks_backward() {
    let r = Rope::from_str("dog");
    let mut it = r.chars_at(r.len_chars());
    assert_eq!(it.prev(), Some('g'));
    assert_eq!(it.prev(), Some('o'));
    assert_eq!(it.prev(), Some('d'));
    assert_eq!(it.prev(), None);
    // next/prev are inverses.
    let mut mid = r.chars_at(1);
    assert_eq!(mid.next(), Some('o'));
    assert_eq!(mid.prev(), Some('o'));
    assert_eq!(mid.prev(), Some('d'));
}

#[test]
fn generated_reverse_and_reversed() {
    let r = Rope::from_str("walnut");
    let mut it = r.chars_at(r.len_chars());
    it.reverse();
    let backward: String = it.collect();
    assert_eq!(backward, "tunlaw");
    let backward2: String = r.chars_at(r.len_chars()).reversed().collect();
    assert_eq!(backward2, backward);
    // Reversing twice restores direction.
    let mut fwd = r.chars();
    fwd.reverse();
    fwd.reverse();
    let forward: String = fwd.collect();
    assert_eq!(forward, "walnut");
}

#[test]
fn generated_chunks_at_byte_positions() {
    let r = Rope::from_str(PLAIN);
    let (mut it, b, c, l) = r.chunks_at_byte(r.len_bytes());
    assert_eq!(it.next(), None);
    assert_eq!((b, c, l), (r.len_bytes(), r.len_chars(), r.len_lines() - 1));
    let (mut it0, b0, c0, l0) = r.chunks_at_byte(0);
    assert_eq!((b0, c0, l0), (0, 0, 0));
    let first = it0.next().unwrap();
    assert_eq!(&PLAIN[..first.len()], first);
    // get twins
    assert!(r.get_chunks_at_byte(r.len_bytes() + 1).is_none());
    assert!(r.get_chunks_at_char(r.len_chars() + 1).is_none());
    assert!(r.get_chunks_at_line_break(r.len_lines() + 1).is_none());
}

#[test]
fn generated_iterators_on_slices() {
    let r = Rope::from_str("aa\nbb\ncc");
    let s = r.slice(3..8); // "bb\ncc"
    let chars: String = s.chars().collect();
    assert_eq!(chars, "bb\ncc");
    let lines: Vec<String> = s.lines().map(String::from).collect();
    assert_eq!(lines, vec!["bb\n".to_string(), "cc".to_string()]);
    let bytes: Vec<u8> = s.bytes().collect();
    assert_eq!(bytes, b"bb\ncc");
    let concat: String = s.chunks().collect();
    assert_eq!(concat, "bb\ncc");
}

#[test]
fn generated_lines_at_end_prev_returns_last_line() {
    let r = Rope::from_str("quartz\nlamp\n");
    let mut la = r.lines_at(r.len_lines());
    assert_eq!(la.next(), None);
    assert_eq!(la.prev().map(String::from).as_deref(), Some(""));
    let r2 = Rope::from_str("quartz\nlamp");
    let mut la2 = r2.lines_at(r2.len_lines());
    assert_eq!(la2.prev().map(String::from).as_deref(), Some("lamp"));
}

// ---------------------------------------------------------------------------
// Comparison, ordering, hashing
// ---------------------------------------------------------------------------

#[test]
fn generated_eq_matrix() {
    let r = Rope::from_str("match me");
    let s = r.slice(..);
    assert!(r == "match me");
    assert!("match me" == r);
    assert!(r == String::from("match me"));
    assert!(String::from("match me") == r);
    assert!(r == Cow::Borrowed("match me"));
    assert!(s == "match me");
    assert!("match me" == s);
    assert!(r == s);
    assert!(s == r);
    assert!(r != "match mе"); // Cyrillic е
    let t = Rope::from_str("match mf");
    assert!(r != t);
}

#[test]
fn generated_ord_is_bytewise_lexicographic() {
    let a = Rope::from_str("azz");
    let b = Rope::from_str("\u{e9}"); // multibyte leading 0xC3 sorts after ASCII
    assert_eq!(a.cmp(&b), std::cmp::Ordering::Less);
    assert_eq!(a.cmp(&b), "azz".cmp("\u{e9}"));
    assert!(a < b);
    let sa = a.slice(..);
    let sb = b.slice(..);
    assert_eq!(sa.cmp(&sb), std::cmp::Ordering::Less);
    assert!(a.partial_cmp(&b) == Some(std::cmp::Ordering::Less));
}

#[test]
fn generated_hash_ignores_construction_path() {
    let direct = Rope::from_str("hash target text\nsecond line\n");
    let mut b = RopeBuilder::new();
    for piece in ["hash ", "target ", "text\n", "second", " line\n"] {
        b.append(piece);
    }
    let built = b.finish();
    let mut edited = Rope::from_str("hash target THE text\nsecond line\n");
    edited.remove(12..16);
    assert_eq!(direct, built);
    assert_eq!(direct, edited);
    assert_eq!(hash_of(&direct), hash_of(&built));
    assert_eq!(hash_of(&direct), hash_of(&edited));
    assert_eq!(hash_of(&direct), hash_of(&direct.slice(..)));
}
