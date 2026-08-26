// Line engine: the full recognized break set exercised through metrics,
// accessors, conversions, iterators, and slices together.
mod lines_engine {
    use ropey::Rope;

    const BREAKS: &[&str] = &[
        "\n", "\u{000B}", "\u{000C}", "\r", "\r\n", "\u{0085}", "\u{2028}", "\u{2029}",
    ];

    #[test]
    fn generated_every_break_partitions_identically() {
        for brk in BREAKS {
            let text = format!("one{b}two{b}three", b = brk);
            let r = Rope::from_str(&text);
            assert_eq!(r.len_lines(), 3, "break {:?}", brk);
            assert_eq!(String::from(r.line(0)), format!("one{}", brk));
            assert_eq!(String::from(r.line(1)), format!("two{}", brk));
            assert_eq!(String::from(r.line(2)), "three");
            // Conversions agree with the partition.
            assert_eq!(r.line_to_char(1), 3 + brk.chars().count());
            assert_eq!(r.char_to_line(r.line_to_char(1)), 1);
            // Iterator agrees with the accessor.
            let via_iter: Vec<String> = r.lines().map(String::from).collect();
            let via_access: Vec<String> =
                (0..r.len_lines()).map(|i| String::from(r.line(i))).collect();
            assert_eq!(via_iter, via_access);
        }
    }

    #[test]
    fn generated_lines_reassemble_document() {
        let text = "alpha\nbravo\r\ncharlie\u{0085}delta\u{2029}echo";
        let r = Rope::from_str(text);
        assert_eq!(r.len_lines(), 5);
        let concat: String = r.lines().map(String::from).collect();
        assert_eq!(concat, text);
        assert_eq!(r.lines().count(), r.len_lines());
    }

    #[test]
    fn generated_crlf_break_and_slice_split() {
        let r = Rope::from_str("head\r\ntail");
        assert_eq!(r.len_lines(), 2);
        // Slicing between CR and LF is a legal char boundary...
        let left = r.slice(..5); // "head\r"
        let right = r.slice(5..); // "\ntail"
        // ...and each side counts breaks over its own visible text.
        assert_eq!(left.len_lines(), 2);
        assert_eq!(right.len_lines(), 2);
        assert_eq!(String::from(left.line(0)), "head\r");
        assert_eq!(String::from(right.line(0)), "\n");
    }

    #[test]
    fn generated_line_edits_move_breaks() {
        let mut r = Rope::from_str("first\nsecond\nthird\n");
        // Join lines 0 and 1 by removing the first break.
        let brk = r.line_to_char(1) - 1;
        r.remove(brk..brk + 1);
        assert_eq!(r, "firstsecond\nthird\n");
        assert_eq!(r.len_lines(), 3);
        // Split the joined line with a CRLF pair.
        r.insert(5, "\r\n");
        assert_eq!(r.len_lines(), 4);
        assert_eq!(String::from(r.line(0)), "first\r\n");
        assert_eq!(String::from(r.line(1)), "second\n");
        // Line conversions track the edits.
        assert_eq!(r.line_to_byte(1), 7);
        assert_eq!(r.byte_to_line(7), 1);
    }

    #[test]
    fn generated_lines_at_bidirectional_sweep() {
        let text = "q0\nq1\nq2\nq3";
        let r = Rope::from_str(text);
        for start in 0..=r.len_lines() {
            let forward: Vec<String> = r.lines_at(start).map(String::from).collect();
            let expected: Vec<String> = (start..r.len_lines())
                .map(|i| String::from(r.line(i)))
                .collect();
            assert_eq!(forward, expected, "forward from {}", start);
            let mut backward = Vec::new();
            let mut it = r.lines_at(start);
            while let Some(line) = it.prev() {
                backward.push(String::from(line));
            }
            let mut expected_back: Vec<String> =
                (0..start).map(|i| String::from(r.line(i))).collect();
            expected_back.reverse();
            assert_eq!(backward, expected_back, "backward from {}", start);
        }
    }
}
