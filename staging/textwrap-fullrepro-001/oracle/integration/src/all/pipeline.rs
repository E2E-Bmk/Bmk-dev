// The manual fragment pipeline must agree with the high-level projections.
mod pipeline {
    use textwrap::core::{break_words, Word};
    use textwrap::word_splitters::split_words;
    use textwrap::wrap_algorithms::{wrap_first_fit, wrap_optimal_fit, Penalties};
    use textwrap::{wrap, Options, WordSeparator, WordSplitter, WrapAlgorithm};

    // Render one chosen line of fragments the way `wrap` renders it: words
    // joined by their trailing whitespace, whitespace dropped at the break.
    fn render(line: &[Word<'_>]) -> String {
        let mut out = String::new();
        for (i, word) in line.iter().enumerate() {
            out.push_str(word.word);
            if i + 1 < line.len() {
                out.push_str(word.whitespace);
            } else {
                out.push_str(word.penalty);
            }
        }
        out
    }

    #[test]
    fn generated_first_fit_pipeline_matches_wrap() {
        let texts = [
            "bat cat rat newt frog",
            "granite slate flint chalk marl clay",
            "a bb ccc dddd eeeee ffffff",
        ];
        for text in texts {
            for width in [6usize, 9, 14] {
                let opts = Options::new(width)
                    .wrap_algorithm(WrapAlgorithm::FirstFit)
                    .word_separator(WordSeparator::AsciiSpace)
                    .word_splitter(WordSplitter::NoHyphenation);
                let high: Vec<String> =
                    wrap(text, opts).iter().map(|l| l.to_string()).collect();

                let words = WordSeparator::AsciiSpace.find_words(text);
                let broken = break_words(words, width);
                let manual: Vec<String> = wrap_first_fit(&broken, &[width as f64])
                    .iter()
                    .map(|line| render(line))
                    .collect();
                assert_eq!(high, manual, "text={:?} width={}", text, width);
            }
        }
    }

    #[test]
    fn generated_optimal_fit_pipeline_matches_wrap() {
        let text = "some tiny words feel unnecessarily long here";
        let width = 15usize;
        let opts = Options::new(width)
            .word_separator(WordSeparator::AsciiSpace)
            .word_splitter(WordSplitter::NoHyphenation);
        let high: Vec<String> = wrap(text, opts).iter().map(|l| l.to_string()).collect();

        let words = WordSeparator::AsciiSpace.find_words(text);
        let broken = break_words(words, width);
        let manual: Vec<String> = wrap_optimal_fit(&broken, &[width as f64], &Penalties::new())
            .unwrap()
            .iter()
            .map(|line| render(line))
            .collect();
        assert_eq!(high, manual);
    }

    #[test]
    fn generated_hyphen_splitter_pipeline_matches_wrap() {
        let text = "over-the-wall leap";
        let width = 6usize;
        let opts = Options::new(width)
            .wrap_algorithm(WrapAlgorithm::FirstFit)
            .word_separator(WordSeparator::AsciiSpace)
            .word_splitter(WordSplitter::HyphenSplitter);
        let high: Vec<String> = wrap(text, opts).iter().map(|l| l.to_string()).collect();

        let words = WordSeparator::AsciiSpace.find_words(text);
        let split: Vec<Word> =
            split_words(words, &WordSplitter::HyphenSplitter).collect();
        let broken = break_words(split.into_iter(), width);
        let manual: Vec<String> = wrap_first_fit(&broken, &[width as f64])
            .iter()
            .map(|line| render(line))
            .collect();
        assert_eq!(high, manual);
    }

    #[test]
    fn generated_hanging_indent_width_slices() {
        // wrap with unequal indents feeds the algorithm per-line widths;
        // reproduce with WrapAlgorithm::wrap and explicit width slices.
        let text = "gnat moth wasp flea midge tick mite";
        let wrapped = wrap(
            text,
            Options::new(12)
                .initial_indent("* ")
                .subsequent_indent("... ")
                .wrap_algorithm(WrapAlgorithm::FirstFit)
                .word_separator(WordSeparator::AsciiSpace)
                .word_splitter(WordSplitter::NoHyphenation),
        );
        assert_eq!(
            wrapped,
            vec!["* gnat moth", "... wasp", "... flea", "... midge", "... tick", "... mite"]
        );

        let words: Vec<Word> = WordSeparator::AsciiSpace.find_words(text).collect();
        let lines = WrapAlgorithm::FirstFit.wrap(&words, &[10, 8]);
        let manual: Vec<String> = lines.iter().map(|line| render(line)).collect();
        let stripped: Vec<&str> = wrapped
            .iter()
            .map(|l| l.trim_start_matches(['*', '.', ' ']))
            .collect();
        assert_eq!(stripped, manual.iter().map(|s| s.as_str()).collect::<Vec<_>>());
    }

    #[test]
    fn generated_custom_algorithm_drives_wrap() {
        let one_per_line = WrapAlgorithm::Custom(|words, _widths| {
            words.chunks(1).collect()
        });
        let lines = wrap("ivy oak elm", Options::new(8).wrap_algorithm(one_per_line));
        assert_eq!(lines, vec!["ivy", "oak", "elm"]);
    }

    #[test]
    fn generated_custom_separator_drives_wrap() {
        let comma_sep = WordSeparator::Custom(|line| {
            Box::new(line.split_inclusive(',').map(Word::from))
        });
        let lines = wrap(
            "fig,date,plum",
            Options::new(5)
                .word_separator(comma_sep)
                .word_splitter(WordSplitter::NoHyphenation),
        );
        assert_eq!(lines, vec!["fig,", "date,", "plum"]);
    }
}
