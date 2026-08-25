// Cross-view width discipline, conversions, and end-to-end composition.
mod consistency {
    use textwrap::core::display_width;
    use textwrap::{fill, unfill, wrap, LineEnding, Options};

    #[test]
    fn generated_width_bound_matrix() {
        let texts = [
            "kestrel bramble otter marsh heath fen moor",
            "a bb ccc dddd eeeee ffffff ggggggg",
            "supercalifragilistic expialidocious",
        ];
        for text in texts {
            for width in [2usize, 5, 9, 17, 33] {
                for line in wrap(text, width) {
                    assert!(
                        display_width(&line) <= width,
                        "line={:?} width={}",
                        line,
                        width
                    );
                }
            }
        }
    }

    #[test]
    fn generated_cjk_width_discipline() {
        // Ideographs are two columns wide; a width of 4 holds two of them.
        assert_eq!(wrap("山川水火土金", 4), vec!["山川", "水火", "土金"]);
        for line in wrap("山川水火土金", 5) {
            assert!(display_width(&line) <= 5);
        }
    }

    #[test]
    fn generated_ansi_sequences_consume_no_width() {
        let plain = wrap("red fox digs den", 8);
        let colored = wrap("\u{1b}[31mred\u{1b}[0m fox digs den", 8);
        assert_eq!(plain, vec!["red fox", "digs den"]);
        assert_eq!(colored.len(), plain.len());
        assert_eq!(colored[1], plain[1]);
        assert!(colored[0].contains("fox"));
    }

    #[test]
    fn generated_options_conversion_equivalence() {
        let text = "granite slate flint chalk";
        let opts = Options::new(11);
        let from_width = wrap(text, 11);
        let from_ref = wrap(text, &opts);
        let from_owned = wrap(text, opts);
        assert_eq!(from_width, from_ref);
        assert_eq!(from_ref, from_owned);
        assert_eq!(fill(text, 11), fill(text, Options::new(11)));
    }

    #[test]
    fn generated_line_ending_only_affects_fill() {
        let text = "tide pool crab shell kelp";
        let lf = Options::new(10);
        let crlf = Options::new(10).line_ending(LineEnding::CRLF);
        let wrapped_lf = wrap(text, &lf);
        let wrapped_crlf = wrap(text, &crlf);
        assert_eq!(wrapped_lf, wrapped_crlf);
        assert!(wrapped_crlf.iter().all(|l| !l.contains('\r')));
        assert_eq!(fill(text, &crlf), wrapped_crlf.join("\r\n"));
    }

    #[test]
    fn generated_break_words_false_full_pipeline() {
        // Hyphen splitting still applies; the unsplittable middle piece
        // overflows on its own line instead of being chunked.
        let lines = wrap(
            "anti-disestablishment mood",
            Options::new(6).break_words(false),
        );
        assert_eq!(lines, vec!["anti-", "disestablishment", "mood"]);
    }

    #[test]
    fn generated_hyphenated_wrap_end_to_end() {
        let lines = wrap("well-known copper-plated kettle", 12);
        assert_eq!(lines, vec!["well-known", "copper-", "plated", "kettle"]);
        assert!(lines.iter().all(|l| display_width(l) <= 12));
    }

    #[test]
    fn generated_wrap_indent_unfill_family() {
        // A wrapped list item read back through unfill recovers the flat text.
        let filled = fill(
            "crag fen moor peat bog heath",
            Options::new(12).initial_indent("* ").subsequent_indent("  "),
        );
        assert_eq!(filled, "* crag fen\n  moor peat\n  bog heath");
        let (recovered, opts) = unfill(&filled);
        assert_eq!(recovered, "crag fen moor peat bog heath");
        assert_eq!(opts.initial_indent, "* ");
        assert_eq!(opts.subsequent_indent, "  ");
    }
}
