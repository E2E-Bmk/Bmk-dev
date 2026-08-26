// Iterator consistency: positioned constructors, bidirectional movement,
// reversal, and chunk-iterator coordinates checked against accessors.
mod iter_consistency {
    use ropey::Rope;

    #[test]
    fn generated_positioned_sweep_bytes_chars() {
        let r = Rope::from_str("mica\u{e9} vein\u{1F680}ore");
        let content = String::from(&r);
        for start in 0..=r.len_chars() {
            let tail: String = r.chars_at(start).collect();
            let expected: String = content.chars().skip(start).collect();
            assert_eq!(tail, expected, "chars_at({})", start);
        }
        for start in [0, 1, 4, 7, r.len_bytes()] {
            let tail: Vec<u8> = r.bytes_at(start).collect();
            assert_eq!(tail, content.as_bytes()[start..].to_vec());
        }
    }

    #[test]
    fn generated_reverse_walk_equals_forward_reversed() {
        let r = Rope::from_str("t\u{2028}racing\nlamps\u{e9}");
        let forward: Vec<char> = r.chars().collect();
        let mut rev_it = r.chars_at(r.len_chars());
        rev_it.reverse();
        let backward: Vec<char> = rev_it.collect();
        let mut expected = forward.clone();
        expected.reverse();
        assert_eq!(backward, expected);

        let fwd_bytes: Vec<u8> = r.bytes().collect();
        let backward_bytes: Vec<u8> = r.bytes_at(r.len_bytes()).reversed().collect();
        let mut expected_bytes = fwd_bytes.clone();
        expected_bytes.reverse();
        assert_eq!(backward_bytes, expected_bytes);
    }

    #[test]
    fn generated_next_prev_alternation_is_stable() {
        let r = Rope::from_str("ab\u{1F600}cd");
        let mut it = r.chars_at(2);
        for _ in 0..3 {
            let n = it.next();
            let p = it.prev();
            assert_eq!(n, p);
            assert_eq!(n, Some('\u{1F600}'));
        }
        let three = Rope::from_str("x\ny\nz");
        let mut lines = three.lines_at(1);
        let n = lines.next().map(String::from);
        let p = lines.prev().map(String::from);
        assert_eq!(n, p);
        assert_eq!(n.as_deref(), Some("y\n"));
    }

    #[test]
    fn generated_exact_size_tracks_direction() {
        let r = Rope::from_str("granular");
        let mut it = r.chars();
        assert_eq!(it.len(), 8);
        it.next();
        it.next();
        assert_eq!(it.len(), 6);
        it.reverse();
        assert_eq!(it.len(), 2); // two items remain behind the cursor
        it.next();
        assert_eq!(it.len(), 1);
        let abc = Rope::from_str("a\nb\nc\n");
        let mut lines = abc.lines();
        assert_eq!(lines.len(), 4);
        lines.next();
        assert_eq!(lines.len(), 3);
    }

    #[test]
    fn generated_chunks_at_walk_agrees_with_chunk_at() {
        // Large content so several chunks exist in any implementation.
        let mut text = String::new();
        for i in 0..200 {
            text.push_str(&format!("seam {:03}\u{e9}\n", i));
        }
        let r = Rope::from_str(&text);
        for &b in &[0usize, 17, 900, text.len() / 2, text.len() - 1] {
            let (chunk, cb, cc, cl) = r.chunk_at_byte(b);
            let (mut it, ib, ic, il) = r.chunks_at_byte(b);
            assert_eq!((ib, ic, il), (cb, cc, cl));
            assert_eq!(it.next(), Some(chunk));
        }
        // Walking the chunk iterator from zero reassembles the text and
        // visits chunks whose start coordinates match chunk_at_byte.
        let mut pos = 0usize;
        let (mut it, ..) = r.chunks_at_byte(0);
        while let Some(chunk) = it.next() {
            let (direct, cb, ..) = r.chunk_at_byte(pos);
            assert_eq!(cb, pos);
            assert_eq!(direct, chunk);
            pos += chunk.len();
        }
        assert_eq!(pos, r.len_bytes());
    }

    #[test]
    fn generated_chunks_prev_walks_back_to_start() {
        let mut text = String::new();
        for i in 0..150 {
            text.push_str(&format!("panel {:02}\n", i));
        }
        let r = Rope::from_str(&text);
        let (mut it, b, c, l) = r.chunks_at_byte(r.len_bytes());
        assert_eq!(b, r.len_bytes());
        assert_eq!(c, r.len_chars());
        assert_eq!(l, r.len_lines() - 1);
        let mut rebuilt_rev: Vec<String> = Vec::new();
        while let Some(chunk) = it.prev() {
            rebuilt_rev.push(chunk.to_string());
        }
        rebuilt_rev.reverse();
        assert_eq!(rebuilt_rev.concat(), text);
    }

    #[test]
    fn generated_iterators_agree_between_rope_and_slice() {
        let r = Rope::from_str("frame one\nframe two\nframe three\n");
        let s = r.slice(r.line_to_char(1)..);
        let from_slice: String = s.chars().collect();
        let from_rope: String = r.chars_at(r.line_to_char(1)).collect();
        assert_eq!(from_slice, from_rope);
        let slice_lines: Vec<String> = s.lines().map(String::from).collect();
        let rope_lines: Vec<String> = r.lines_at(1).map(String::from).collect();
        assert_eq!(slice_lines, rope_lines);
    }
}
