// fill/unfill/refill as projections of one wrapping run.
mod fill_refill {
    use textwrap::{fill, fill_inplace, refill, unfill, wrap, LineEnding, Options, WordSeparator, WordSplitter, WrapAlgorithm};

    #[test]
    fn generated_fill_equals_wrap_joined() {
        let texts = ["heron perch reed", "one two\n\nthree", "  lead kept   \nnext"];
        for text in texts {
            for width in [5usize, 9, 30] {
                let opts = Options::new(width);
                let joined = wrap(text, &opts).join("\n");
                assert_eq!(fill(text, &opts), joined, "text={:?} width={}", text, width);

                let crlf = Options::new(width).line_ending(LineEnding::CRLF);
                let joined_crlf = wrap(text, &crlf).join("\r\n");
                assert_eq!(fill(text, &crlf), joined_crlf);
            }
        }
    }

    #[test]
    fn generated_fill_equals_wrap_joined_with_indents() {
        let opts = Options::new(12).initial_indent("- ").subsequent_indent("  ");
        let text = "juniper rowan alder hazel";
        assert_eq!(fill(text, &opts), wrap(text, &opts).join("\n"));
    }

    #[test]
    fn generated_unfill_fill_roundtrip() {
        let texts = [
            "kestrel bramble otter marsh",
            "pike carp roach bream tench dace",
        ];
        for text in texts {
            for width in [8usize, 12, 100] {
                let (recovered, _opts) = unfill(&fill(text, width));
                assert_eq!(recovered, text, "width={}", width);
            }
        }
    }

    #[test]
    fn generated_refill_equals_fresh_fill() {
        let text = "granite slate flint chalk marl clay";
        for (w1, w2) in [(9usize, 16usize), (20, 7), (11, 11)] {
            let refilled = refill(&fill(text, w1), w2);
            assert_eq!(refilled, fill(text, w2), "w1={} w2={}", w1, w2);
        }
    }

    #[test]
    fn generated_fill_then_unfill_recovers_list_prefixes() {
        let filled = fill(
            "juniper rowan alder hazel birch",
            Options::new(14).initial_indent("- ").subsequent_indent("  "),
        );
        assert_eq!(filled, "- juniper\n  rowan alder\n  hazel birch");
        let (recovered, opts) = unfill(&filled);
        assert_eq!(recovered, "juniper rowan alder hazel birch");
        assert_eq!(opts.initial_indent, "- ");
        assert_eq!(opts.subsequent_indent, "  ");
        // Refilling wider keeps the inferred prefixes.
        assert_eq!(refill(&filled, 40), "- juniper rowan alder hazel birch");
    }

    #[test]
    fn generated_unfill_width_reports_widest_line() {
        let filled = fill("wren jay owl hawk crow lark", 12);
        let widest = filled.lines().map(|l| l.len()).max().unwrap();
        let (_text, opts) = unfill(&filled);
        assert_eq!(opts.width, widest);
        assert!(opts.width <= 12);
    }

    #[test]
    fn generated_fill_inplace_matches_restricted_fill() {
        let text = "pike carp roach bream tench dace";
        let opts = Options::new(11)
            .wrap_algorithm(WrapAlgorithm::FirstFit)
            .word_separator(WordSeparator::AsciiSpace)
            .word_splitter(WordSplitter::NoHyphenation);
        let filled = fill(text, opts);
        let mut inplace = String::from(text);
        fill_inplace(&mut inplace, 11);
        assert_eq!(filled, "pike carp\nroach bream\ntench dace");
        assert_eq!(inplace, filled);
    }

    #[test]
    fn generated_refill_line_ending_swap_roundtrip() {
        let text = "> tide pool\n> crab shell\n";
        let crlf = refill(text, Options::new(12).line_ending(LineEnding::CRLF));
        assert_eq!(crlf, "> tide pool\r\n> crab shell\r\n");
        let back = refill(&crlf, Options::new(12).line_ending(LineEnding::LF));
        assert_eq!(back, text);
    }
}
