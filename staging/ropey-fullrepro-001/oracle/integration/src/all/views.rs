// Views: slices composed with metrics, conversions, editing reassembly,
// and conversions out of views.
mod views {
    use ropey::{Rope, RopeSlice};

    #[test]
    fn generated_edit_agrees_with_slice_reassembly() {
        let base = Rope::from_str("granite steps\nlead to the cellar\n");
        let insert_at = 8;
        let mut edited = base.clone();
        edited.insert(insert_at, "! ");
        let reassembled = format!(
            "{}{}{}",
            String::from(base.slice(..insert_at)),
            "! ",
            String::from(base.slice(insert_at..))
        );
        assert_eq!(edited, reassembled.as_str());

        let (a, b) = (3, 11);
        let mut removed = base.clone();
        removed.remove(a..b);
        let reassembled2 = format!(
            "{}{}",
            String::from(base.slice(..a)),
            String::from(base.slice(b..))
        );
        assert_eq!(removed, reassembled2.as_str());
    }

    #[test]
    fn generated_nested_slices_compose_deeply() {
        let r = Rope::from_str("abcdefghijklmnopqrstuvwxyz");
        let s1 = r.slice(2..24); // c..x
        let s2 = s1.slice(3..18); // f..t
        let s3 = s2.slice(1..8); // g..m
        assert_eq!(s3, "ghijklm");
        assert_eq!(s3, r.slice(6..13));
        assert_eq!(s3.len_chars(), 7);
        // byte_slice composes with char slice on multibyte content.
        let m = Rope::from_str("x\u{e9}y\u{e9}z end");
        let bs = m.byte_slice(1..6); // "éyé"
        assert_eq!(bs, "\u{e9}y\u{e9}");
        assert_eq!(bs.slice(1..2), "y");
    }

    #[test]
    fn generated_slice_local_coordinates_full_surface() {
        let r = Rope::from_str("kiln\u{e9} fire\nash pit\nglaze\n");
        let start = r.line_to_char(1);
        let end = r.len_chars();
        let s = r.slice(start..end); // "ash pit\nglaze\n"
        assert_eq!(s, "ash pit\nglaze\n");
        assert_eq!(s.len_lines(), 3);
        assert_eq!(s.line(0), "ash pit\n");
        assert_eq!(s.line_to_byte(1), 8);
        assert_eq!(s.byte_to_line(9), 1);
        assert_eq!(s.char_to_utf16_cu(s.len_chars()), s.len_utf16_cu());
        // Chunk access through the slice reassembles the slice.
        let concat: String = s.chunks().collect();
        assert_eq!(concat, "ash pit\nglaze\n");
        let (chunk, cb, cc, cl) = s.chunk_at_byte(3);
        assert!(cb <= 3 && 3 < cb + chunk.len());
        assert_eq!(s.byte_to_char(cb), cc);
        assert_eq!(s.byte_to_line(cb), cl);
    }

    #[test]
    fn generated_str_backed_slice_matches_rope_backed() {
        let text = "parity check\nacross backings\n";
        let flat = RopeSlice::from(text);
        let rope = Rope::from_str(text);
        let ropey_slice = rope.slice(..);
        assert_eq!(flat, ropey_slice);
        assert_eq!(flat.len_lines(), ropey_slice.len_lines());
        assert_eq!(flat.line(1), ropey_slice.line(1));
        assert_eq!(
            flat.chars().collect::<String>(),
            ropey_slice.chars().collect::<String>()
        );
        assert_eq!(flat.byte_to_char(10), ropey_slice.byte_to_char(10));
        assert_eq!(flat.as_str(), Some(text));
    }

    #[test]
    fn generated_slice_conversion_round_trip() {
        let r = Rope::from_str("lantern\u{1F680} glow\nsecond\n");
        let s = r.slice(4..13);
        let as_string = String::from(s);
        let back = Rope::from(s);
        assert_eq!(back, as_string.as_str());
        assert_eq!(back.slice(..), s);
        assert_eq!(back.len_utf16_cu(), s.len_utf16_cu());
        // A rope built from a slice is independent storage.
        assert!(!back.is_instance(&r));
    }

    #[test]
    fn generated_get_slice_boundary_matrix() {
        let r = Rope::from_str("0123456789");
        let s = r.slice(2..8);
        // In-bounds nested forms succeed.
        assert!(s.get_slice(..).is_some());
        assert!(s.get_slice(0..6).is_some());
        assert!(s.get_slice(6..6).is_some());
        // Out-of-bounds and reversed nested forms fail as values.
        assert!(s.get_slice(0..7).is_none());
        assert!(s.get_slice(5..2).is_none());
        assert!(s.get_byte_slice(0..7).is_none());
        // Errors reported through the slice use slice-local lengths.
        match s.try_char_to_byte(9) {
            Err(ropey::Error::CharIndexOutOfBounds(idx, len)) => {
                assert_eq!((idx, len), (9, 6));
            }
            other => panic!("unexpected: {:?}", other),
        }
    }
}
