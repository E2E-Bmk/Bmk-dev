// Cross-view invariants: one text state observed through metrics,
// conversions, iterators, slices, comparison, ordering, and hashing.
mod cross_view {
    use ropey::{Rope, RopeBuilder};
    use std::collections::hash_map::DefaultHasher;
    use std::hash::{Hash, Hasher};

    fn hash_of<T: Hash>(v: &T) -> u64 {
        let mut h = DefaultHasher::new();
        v.hash(&mut h);
        h.finish()
    }

    #[test]
    fn generated_counts_match_iterators_everywhere() {
        let docs = [
            "",
            "solo",
            "pair\nlines\n",
            "\u{e9}\u{1F680}\u{6771}\r\nmixed\u{2028}widths",
        ];
        for doc in docs {
            let r = Rope::from_str(doc);
            assert_eq!(r.bytes().count(), r.len_bytes(), "{:?}", doc);
            assert_eq!(r.chars().count(), r.len_chars(), "{:?}", doc);
            assert_eq!(r.lines().count(), r.len_lines(), "{:?}", doc);
            let s = r.slice(..);
            assert_eq!(s.bytes().count(), s.len_bytes());
            assert_eq!(s.chars().count(), s.len_chars());
            assert_eq!(s.lines().count(), s.len_lines());
        }
    }

    #[test]
    fn generated_conversion_round_trips() {
        let r = Rope::from_str("orchard\u{e9}\nrows of \u{1F34E}\napples\u{2029}fall\n");
        for ci in 0..=r.len_chars() {
            assert_eq!(r.byte_to_char(r.char_to_byte(ci)), ci);
            assert_eq!(r.utf16_cu_to_char(r.char_to_utf16_cu(ci)), ci);
        }
        for li in 0..r.len_lines() {
            assert_eq!(r.byte_to_line(r.line_to_byte(li)), li);
            assert_eq!(r.char_to_line(r.line_to_char(li)), li);
        }
    }

    #[test]
    fn generated_segment_projections_reassemble() {
        let text = "weir\u{0085}gate\nlock\u{000C}pond";
        let r = Rope::from_str(text);
        let via_chunks: String = r.chunks().collect();
        let via_lines: String = r.lines().map(String::from).collect();
        let via_chars: String = r.chars().collect();
        let via_string = String::from(&r);
        assert_eq!(via_chunks, text);
        assert_eq!(via_lines, text);
        assert_eq!(via_chars, text);
        assert_eq!(via_string, text);
    }

    #[test]
    fn generated_content_determines_all_projections() {
        let a = Rope::from_str("same facts\nby different roads\n");
        let mut builder = RopeBuilder::new();
        for piece in ["same", " facts\nby", " ", "different roads\n"] {
            builder.append(piece);
        }
        let b = builder.finish();
        let mut c = Rope::from_str("same facts\nby other roads\n");
        c.remove(14..19);
        c.insert(14, "different");

        for other in [&b, &c] {
            assert_eq!(a, *other);
            assert_eq!(a.len_bytes(), other.len_bytes());
            assert_eq!(a.len_utf16_cu(), other.len_utf16_cu());
            assert_eq!(a.line_to_char(1), other.line_to_char(1));
            assert_eq!(a.char(12), other.char(12));
            assert_eq!(
                a.chars().collect::<String>(),
                other.chars().collect::<String>()
            );
            assert_eq!(
                a.lines().map(String::from).collect::<Vec<_>>(),
                other.lines().map(String::from).collect::<Vec<_>>()
            );
            assert_eq!(hash_of(&a), hash_of(other));
            assert_eq!(a.cmp(other), std::cmp::Ordering::Equal);
        }
        assert!(!a.is_instance(&b));
    }

    #[test]
    fn generated_ordering_sorts_like_strings() {
        let words = ["pearl", "Pebble", "\u{e9}clair", "pear", "", "pebble"];
        let mut ropes: Vec<Rope> = words.iter().map(|w| Rope::from_str(w)).collect();
        let mut strings: Vec<&str> = words.to_vec();
        ropes.sort();
        strings.sort();
        let sorted: Vec<String> = ropes.iter().map(String::from).collect();
        assert_eq!(sorted, strings);
        // Slice ordering agrees with rope ordering.
        let s1 = ropes[1].slice(..);
        let s2 = ropes[2].slice(..);
        assert_eq!(s1.cmp(&s2), std::cmp::Ordering::Less);
    }

    #[test]
    fn generated_hash_agreement_rope_and_slices() {
        let r = Rope::from_str("ledger page one\nledger page two\n");
        assert_eq!(hash_of(&r), hash_of(&r.slice(..)));
        let sub = r.slice(7..15);
        let standalone = Rope::from_str("page one");
        assert_eq!(sub, standalone.slice(..));
        assert_eq!(hash_of(&sub), hash_of(&standalone.slice(..)));
    }

    #[test]
    fn generated_utf16_cursor_mapping_workflow() {
        // A host editor tracks cursors in UTF-16; the document mixes widths.
        let doc = Rope::from_str("plan \u{1F5FA} route\nvia \u{6771}\u{4eac}\n");
        // Map every UTF-16 offset to a char and back; positions inside a
        // surrogate pair floor to the pair's char.
        for u in 0..=doc.len_utf16_cu() {
            let c = doc.utf16_cu_to_char(u);
            let back = doc.char_to_utf16_cu(c);
            assert!(back <= u);
            assert!(u == doc.len_utf16_cu() || doc.char_to_utf16_cu(c + 1) > u);
        }
        // A cursor after the map emoji: chars "plan " = 5, emoji = 1 char.
        let after_emoji_char = 6;
        let u16_pos = doc.char_to_utf16_cu(after_emoji_char);
        assert_eq!(u16_pos, 7); // 5 + surrogate pair
        // Editing at the mapped char position keeps both systems aligned.
        let mut edited = doc.clone();
        edited.insert(after_emoji_char, "!");
        assert_eq!(edited.char_to_utf16_cu(after_emoji_char + 1), u16_pos + 1);
        assert_eq!(edited.line(0), "plan \u{1F5FA}! route\n");
    }

    #[test]
    fn generated_workflow_replace_word_across_views() {
        // End-to-end: locate by line, edit chars, verify through bytes,
        // lines, slices, and comparison.
        let mut doc = Rope::from_str("One morning\nthe cat sat\n");
        let line_start = doc.line_to_char(1);
        doc.remove(line_start + 4..line_start + 7);
        doc.insert(line_start + 4, "heron");
        assert_eq!(doc, "One morning\nthe heron sat\n");
        assert_eq!(doc.line(1), "the heron sat\n");
        assert_eq!(doc.len_lines(), 3);
        assert_eq!(doc.byte_to_line(doc.len_bytes() - 1), 1);
        let tail = doc.slice(doc.line_to_char(1)..);
        assert_eq!(tail, "the heron sat\n");
        let mut out: Vec<u8> = Vec::new();
        doc.write_to(&mut out).unwrap();
        assert_eq!(out, b"One morning\nthe heron sat\n");
    }
}
