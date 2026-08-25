// Editing pipelines: multi-step edit sessions checked against a flat-string
// model, split/append round trips, and reader/writer round trips.
mod editing {
    use ropey::{Rope, RopeBuilder};
    use std::io::Cursor;

    // Apply the same edit script to a Rope and to a String, comparing
    // content and metrics after every step.
    fn check_against_model(steps: &[(&str, usize, usize, &str)]) {
        let mut rope = Rope::new();
        let mut model = String::new();
        for &(op, a, b, text) in steps {
            match op {
                "insert" => {
                    rope.insert(a, text);
                    let byte_at = model
                        .char_indices()
                        .nth(a)
                        .map(|(i, _)| i)
                        .unwrap_or(model.len());
                    model.insert_str(byte_at, text);
                }
                "remove" => {
                    rope.remove(a..b);
                    let sb = model
                        .char_indices()
                        .nth(a)
                        .map(|(i, _)| i)
                        .unwrap_or(model.len());
                    let eb = model
                        .char_indices()
                        .nth(b)
                        .map(|(i, _)| i)
                        .unwrap_or(model.len());
                    model.replace_range(sb..eb, "");
                }
                other => panic!("unknown op {}", other),
            }
            assert_eq!(rope, model.as_str(), "content after {} {} {}", op, a, b);
            assert_eq!(rope.len_bytes(), model.len());
            assert_eq!(rope.len_chars(), model.chars().count());
            assert_eq!(rope.len_utf16_cu(), model.encode_utf16().count());
        }
    }

    #[test]
    fn generated_edit_session_matches_string_model() {
        check_against_model(&[
            ("insert", 0, 0, "the quick onyx goblin\n"),
            ("insert", 22, 0, "jumps over the lazy dwarf\n"),
            ("insert", 4, 0, "very "),
            ("remove", 0, 4, ""),
            ("insert", 0, 0, "A"),
            ("remove", 10, 20, ""),
            ("insert", 5, 0, "\u{1F680}\u{6771}\u{4eac}\u{e9} "),
            ("remove", 3, 9, ""),
            ("insert", 12, 0, "\r\nmid\r\n"),
            ("remove", 2, 3, ""),
        ]);
    }

    #[test]
    fn generated_edit_session_multibyte_boundaries() {
        check_against_model(&[
            ("insert", 0, 0, "\u{e9}\u{e9}\u{e9}\u{e9}"),
            ("insert", 2, 0, "\u{1F600}\u{1F601}"),
            ("remove", 1, 3, ""),
            ("insert", 0, 0, "\u{2028}"),
            ("insert", 5, 0, "tail"),
            ("remove", 0, 1, ""),
        ]);
    }

    #[test]
    fn generated_split_append_round_trip() {
        let original = Rope::from_str("harvest moon\nover the salt marsh\n");
        for split_at in [0, 5, 13, original.len_chars()] {
            let mut left = original.clone();
            let right = left.split_off(split_at);
            assert_eq!(
                left.len_chars() + right.len_chars(),
                original.len_chars()
            );
            left.append(right);
            assert_eq!(left, original);
        }
    }

    #[test]
    fn generated_builder_vs_edit_vs_reader_equivalence() {
        let target = "north field\nwest gate\nsouth wall\n";
        let direct = Rope::from_str(target);

        let mut b = RopeBuilder::new();
        b.append("north ");
        b.append("field\nwest ");
        b.append("gate\nsouth wall\n");
        let built = b.finish();

        let mut edited = Rope::from_str("north field\nsouth wall\n");
        edited.insert(12, "west gate\n");

        let read = Rope::from_reader(Cursor::new(target.as_bytes())).unwrap();

        assert_eq!(direct, built);
        assert_eq!(direct, edited);
        assert_eq!(direct, read);
        assert_eq!(built.len_lines(), 4);
        assert_eq!(edited.line(1), "west gate\n");
    }

    #[test]
    fn generated_io_round_trip_after_edits() {
        let mut rope = Rope::from_reader(Cursor::new(
            "config: alpha\nvalue: 12\n".as_bytes(),
        ))
        .unwrap();
        let line_start = rope.line_to_char(1);
        rope.remove(line_start + 7..rope.line_to_char(2) - 1);
        rope.insert(line_start + 7, "99");
        let mut out: Vec<u8> = Vec::new();
        rope.write_to(&mut out).unwrap();
        assert_eq!(
            std::str::from_utf8(&out).unwrap(),
            "config: alpha\nvalue: 99\n"
        );
        let reread = Rope::from_reader(Cursor::new(&out[..])).unwrap();
        assert_eq!(reread, rope);
    }

    #[test]
    fn generated_persistent_snapshots_across_session() {
        let mut doc = Rope::from_str("v1 content\n");
        let mut snapshots = vec![doc.clone()];
        doc.insert(doc.len_chars(), "v2 line\n");
        snapshots.push(doc.clone());
        doc.remove(0..3);
        snapshots.push(doc.clone());
        doc.insert_char(0, '#');
        assert_eq!(snapshots[0], "v1 content\n");
        assert_eq!(snapshots[1], "v1 content\nv2 line\n");
        assert_eq!(snapshots[2], "content\nv2 line\n");
        assert_eq!(doc, "#content\nv2 line\n");
        assert!(snapshots[1].is_instance(&snapshots[1].clone()));
        assert!(!snapshots[0].is_instance(&snapshots[2]));
    }

    #[test]
    fn generated_large_document_edit_consistency() {
        // Build a document large enough to require multiple chunks in any
        // reasonable implementation, then verify chunk/metric consistency.
        let mut model = String::new();
        for i in 0..300 {
            model.push_str(&format!("row {:03} of the ledger\u{e9}\n", i));
        }
        let mut rope = Rope::from_str(&model);
        assert_eq!(rope.len_lines(), 301);

        // Edit in the middle.
        let mid_line = rope.line_to_char(150);
        rope.insert(mid_line, "INSERTED HEADER\n");
        let mb = model
            .char_indices()
            .nth(mid_line)
            .map(|(i, _)| i)
            .unwrap();
        model.insert_str(mb, "INSERTED HEADER\n");
        assert_eq!(rope.len_lines(), 302);
        assert_eq!(rope, model.as_str());
        assert_eq!(rope.len_bytes(), model.len());
        assert_eq!(rope.len_chars(), model.chars().count());

        // Chunk reassembly still matches, and no chunk is empty.
        let concat: String = rope.chunks().collect();
        assert_eq!(concat, model);
        for chunk in rope.chunks() {
            assert!(!chunk.is_empty());
        }

        // Sampled conversion agreement with the flat model.
        let flat: Vec<char> = model.chars().collect();
        for &ci in &[0usize, 1, 149, 3000, flat.len()] {
            let bi = rope.char_to_byte(ci);
            let expected_bi = model
                .char_indices()
                .nth(ci)
                .map(|(i, _)| i)
                .unwrap_or(model.len());
            assert_eq!(bi, expected_bi);
            assert_eq!(rope.byte_to_char(bi), ci);
        }
    }
}
