// Oracle atomic tests for the text wrapping library
#![cfg(test)]
#![allow(clippy::all)]

use std::borrow::Cow;
use textwrap::core::{break_words, display_width, Fragment, Word};
use textwrap::word_splitters::split_words;
use textwrap::wrap_algorithms::{wrap_first_fit, wrap_optimal_fit, OverflowError, Penalties};
use textwrap::{
    dedent, fill, fill_inplace, indent, refill, unfill, wrap, wrap_columns, LineEnding, Options,
    WordSeparator, WordSplitter, WrapAlgorithm,
};

// ---------------------------------------------------------------------------
// Wrapping and filling
// ---------------------------------------------------------------------------

#[test]
fn generated_wrap_plain_width_exact_lines() {
    let lines = wrap("kestrel bramble otter", 7);
    assert_eq!(lines, vec!["kestrel", "bramble", "otter"]);
}

#[test]
fn generated_wrap_empty_string_one_empty_line() {
    assert_eq!(wrap("", 10), vec![""]);
}

#[test]
fn generated_wrap_lone_newline_two_empty_lines() {
    assert_eq!(wrap("\n", 10), vec!["", ""]);
}

#[test]
fn generated_wrap_preserves_paragraph_break() {
    let lines = wrap("elm ash\n\noak fir", 8);
    assert_eq!(lines, vec!["elm ash", "", "oak fir"]);
}

#[test]
fn generated_wrap_leading_whitespace_kept() {
    let lines = wrap("  lead kept   \nnext", 20);
    assert_eq!(lines, vec!["  lead kept", "next"]);
}

#[test]
fn generated_wrap_trailing_break_whitespace_dropped() {
    let lines = wrap("heron   perch", 6);
    assert_eq!(lines, vec!["heron", "perch"]);
    assert!(lines.iter().all(|l| !l.ends_with(' ')));
}

#[test]
fn generated_wrap_interword_spaces_kept_on_same_line() {
    let lines = wrap("fen   moor", 12);
    assert_eq!(lines, vec!["fen   moor"]);
}

#[test]
fn generated_wrap_initial_and_subsequent_indents() {
    let lines = wrap(
        "crag fen moor peat bog heath",
        Options::new(12).initial_indent("* ").subsequent_indent("  "),
    );
    assert_eq!(lines, vec!["* crag fen", "  moor peat", "  bog heath"]);
}

#[test]
fn generated_wrap_indent_applied_to_empty_output_line() {
    let lines = wrap(
        "first paragraph line\n\nsecond",
        Options::new(12).initial_indent("- ").subsequent_indent("  "),
    );
    assert_eq!(lines, vec!["- first", "  paragraph", "  line", "  ", "  second"]);
}

#[test]
fn generated_wrap_indent_counts_toward_width() {
    let lines = wrap("alpha beta gamma", Options::new(10).subsequent_indent("...."));
    assert_eq!(lines, vec!["alpha beta", "....gamma"]);
    assert!(lines.iter().all(|l| display_width(l) <= 10));
}

#[test]
fn generated_wrap_break_words_chunks_long_word() {
    assert_eq!(wrap("extraordinarily", 6), vec!["extrao", "rdinar", "ily"]);
}

#[test]
fn generated_wrap_no_break_words_overflows() {
    let lines = wrap("hyperextraordinary word", Options::new(6).break_words(false));
    assert_eq!(lines, vec!["hyperextraordinary", "word"]);
}

#[test]
fn generated_wrap_width_zero_one_word_per_line() {
    assert_eq!(wrap("ab", 0), vec!["a", "b"]);
    assert_eq!(wrap("x y", 0), vec!["x", "y"]);
}

#[test]
fn generated_wrap_carriage_return_is_content() {
    let lines = wrap("gull bay\r\ncove", 5);
    assert_eq!(lines, vec!["gull", "bay\r", "cove"]);
}

#[test]
fn generated_wrap_borrows_without_indent() {
    let text = "plain borrowed line";
    let out = wrap(text, 30);
    assert_eq!(out, vec!["plain borrowed line"]);
    assert!(matches!(out[0], Cow::Borrowed(_)));
    let broken = wrap("unbreakable", 4);
    assert!(broken.iter().all(|l| matches!(l, Cow::Borrowed(_))));
}

#[test]
fn generated_wrap_owns_with_indent() {
    let out = wrap("plain line", Options::new(20).initial_indent("> "));
    assert_eq!(out, vec!["> plain line"]);
    assert!(matches!(out[0], Cow::Owned(_)));
}

#[test]
fn generated_wrap_accepts_width_options_and_reference() {
    let by_width = wrap("mole vole shrew", 9);
    let opts = Options::new(9);
    let by_ref = wrap("mole vole shrew", &opts);
    let by_owned = wrap("mole vole shrew", opts);
    assert_eq!(by_width, vec!["mole vole", "shrew"]);
    assert_eq!(by_width, by_ref);
    assert_eq!(by_width, by_owned);
}

#[test]
fn generated_fill_joins_with_lf() {
    assert_eq!(fill("kestrel bramble otter", 7), "kestrel\nbramble\notter");
}

#[test]
fn generated_fill_joins_with_crlf() {
    let filled = fill("ant bee", Options::new(3).line_ending(LineEnding::CRLF));
    assert_eq!(filled, "ant\r\nbee");
}

#[test]
fn generated_fill_keeps_empty_lines() {
    assert_eq!(fill("one two\n\nthree", 5), "one\ntwo\n\nthree");
}

#[test]
fn generated_fill_inplace_greedy() {
    let mut s = String::from("wren jay owl hawk crow lark");
    fill_inplace(&mut s, 12);
    assert_eq!(s, "wren jay owl\nhawk crow\nlark");
}

#[test]
fn generated_fill_inplace_replaces_last_space_of_run() {
    let mut s = String::from("aaa  bbb ccc");
    fill_inplace(&mut s, 3);
    assert_eq!(s, "aaa \nbbb\nccc");
}

#[test]
fn generated_fill_inplace_never_breaks_words() {
    let mut s = String::from("overlong tiny");
    fill_inplace(&mut s, 4);
    assert_eq!(s, "overlong\ntiny");
}

// ---------------------------------------------------------------------------
// Wrapping configuration
// ---------------------------------------------------------------------------

#[test]
fn generated_options_new_defaults() {
    let opts = Options::new(28);
    assert_eq!(opts.width, 28);
    assert_eq!(opts.line_ending, LineEnding::LF);
    assert_eq!(opts.initial_indent, "");
    assert_eq!(opts.subsequent_indent, "");
    assert!(opts.break_words);
    assert_eq!(opts.word_splitter, WordSplitter::HyphenSplitter);
    assert_eq!(opts.word_separator, WordSeparator::UnicodeBreakProperties);
    assert_eq!(opts.wrap_algorithm, WrapAlgorithm::new());
    assert_eq!(opts.wrap_algorithm, WrapAlgorithm::OptimalFit(Penalties::new()));
}

#[test]
fn generated_options_builder_methods_chain() {
    let opts = Options::new(11)
        .width(13)
        .line_ending(LineEnding::CRLF)
        .initial_indent(">> ")
        .subsequent_indent(" ")
        .break_words(false)
        .word_separator(WordSeparator::AsciiSpace)
        .word_splitter(WordSplitter::NoHyphenation)
        .wrap_algorithm(WrapAlgorithm::FirstFit);
    assert_eq!(opts.width, 13);
    assert_eq!(opts.line_ending, LineEnding::CRLF);
    assert_eq!(opts.initial_indent, ">> ");
    assert_eq!(opts.subsequent_indent, " ");
    assert!(!opts.break_words);
    assert_eq!(opts.word_separator, WordSeparator::AsciiSpace);
    assert_eq!(opts.word_splitter, WordSplitter::NoHyphenation);
    assert_eq!(opts.wrap_algorithm, WrapAlgorithm::FirstFit);
}

#[test]
fn generated_options_fields_directly_assignable() {
    let mut opts = Options::new(5);
    opts.width = 9;
    opts.break_words = false;
    opts.initial_indent = "@";
    assert_eq!(wrap("mole vole shrew", &opts), vec!["@mole", "vole", "shrew"]);
}

#[test]
fn generated_options_from_usize() {
    let opts: Options = 42usize.into();
    assert_eq!(opts.width, 42);
    assert_eq!(opts.line_ending, LineEnding::LF);
    assert!(opts.break_words);
}

#[test]
fn generated_options_from_reference_copies() {
    let base = Options::new(8).initial_indent("~ ");
    let copy: Options = (&base).into();
    assert_eq!(copy.width, 8);
    assert_eq!(copy.initial_indent, "~ ");
    assert_eq!(wrap("dune reed", &base), wrap("dune reed", copy));
}

#[test]
fn generated_line_ending_as_str() {
    assert_eq!(LineEnding::LF.as_str(), "\n");
    assert_eq!(LineEnding::CRLF.as_str(), "\r\n");
}

// ---------------------------------------------------------------------------
// Refilling
// ---------------------------------------------------------------------------

#[test]
fn generated_unfill_joins_and_reports_width() {
    let (text, opts) = unfill("tide pool\ncrab shell\nkelp");
    assert_eq!(text, "tide pool crab shell kelp");
    assert_eq!(opts.width, 10);
    assert_eq!(opts.line_ending, LineEnding::LF);
}

#[test]
fn generated_unfill_infers_list_item_prefixes() {
    let (text, opts) = unfill("+ first entry\n  second\n  third");
    assert_eq!(text, "first entry second third");
    assert_eq!(opts.initial_indent, "+ ");
    assert_eq!(opts.subsequent_indent, "  ");
}

#[test]
fn generated_unfill_comment_prefix_and_trailing_ending() {
    let (text, opts) = unfill("# tide pool\n# crab\n");
    assert_eq!(text, "tide pool crab\n");
    assert_eq!(opts.initial_indent, "# ");
    assert_eq!(opts.subsequent_indent, "# ");
    assert_eq!(opts.width, 11);
}

#[test]
fn generated_unfill_narrows_common_prefix() {
    let (text, opts) = unfill("  aa\n    bb\n  cc");
    assert_eq!(text, "aa   bb cc");
    assert_eq!(opts.initial_indent, "  ");
    assert_eq!(opts.subsequent_indent, "  ");
}

#[test]
fn generated_unfill_detects_crlf() {
    let (text, opts) = unfill("gull\r\nreef\r\n");
    assert_eq!(text, "gull reef\r\n");
    assert_eq!(opts.line_ending, LineEnding::CRLF);
}

#[test]
fn generated_unfill_mixed_endings_report_lf() {
    let (text, opts) = unfill("gull\r\nreef\nrock");
    assert_eq!(text, "gull reef rock");
    assert_eq!(opts.line_ending, LineEnding::LF);
}

#[test]
fn generated_refill_rewraps_with_inferred_prefix() {
    let quoted = "> one two\n> three four\n> five\n";
    assert_eq!(refill(quoted, 40), "> one two three four five\n");
    assert_eq!(refill(quoted, 12), "> one two\n> three four\n> five\n");
}

#[test]
fn generated_refill_converts_line_endings() {
    let opts = Options::new(5).line_ending(LineEnding::CRLF);
    assert_eq!(refill("ant\nbee\n", opts), "ant\r\nbee\r\n");
    let opts = Options::new(5).line_ending(LineEnding::LF);
    assert_eq!(refill("ant\r\nbee\r\n", opts), "ant\nbee\n");
}

// ---------------------------------------------------------------------------
// Indentation
// ---------------------------------------------------------------------------

#[test]
fn generated_indent_adds_prefix() {
    assert_eq!(indent("first\nsecond\n", "  "), "  first\n  second\n");
}

#[test]
fn generated_indent_trims_prefix_on_empty_lines() {
    assert_eq!(indent("first\n\nsecond\n", "# "), "# first\n#\n# second\n");
}

#[test]
fn generated_indent_whitespace_prefix_keeps_empty_lines_empty() {
    assert_eq!(indent("aa\n\nbb\n", "  "), "  aa\n\n  bb\n");
}

#[test]
fn generated_indent_keeps_line_content_and_no_invented_newline() {
    assert_eq!(indent(" \t padded   ", "->"), "-> \t padded   ");
    assert_eq!(indent("one\ntwo", "."), ".one\n.two");
}

#[test]
fn generated_dedent_removes_common_prefix() {
    assert_eq!(dedent("    a\n      b\n    c\n"), "a\n  b\nc\n");
}

#[test]
fn generated_dedent_whitespace_only_lines_emptied() {
    assert_eq!(dedent("  a\n \n  b\n"), "a\n\nb\n");
    assert_eq!(dedent("  a\n\n    b\n"), "a\n\n  b\n");
}

#[test]
fn generated_dedent_no_trailing_newline_invented() {
    assert_eq!(dedent("  just one"), "just one");
}

// ---------------------------------------------------------------------------
// Column layout
// ---------------------------------------------------------------------------

#[test]
fn generated_wrap_columns_layout() {
    let rows = wrap_columns("mint sage rue dill leek anise", 3, 30, "|", " ", "|");
    assert_eq!(
        rows,
        vec!["|mint     rue dill anise     |", "|sage     leek               |"]
    );
}

#[test]
fn generated_wrap_columns_equal_row_widths() {
    let rows = wrap_columns("mint sage rue dill leek anise", 3, 30, "|", " ", "|");
    assert!(rows.iter().all(|r| display_width(r) == 30));
}

#[test]
fn generated_wrap_columns_empty_text_blank_row() {
    assert_eq!(wrap_columns("", 1, 10, "[ ", "", " ]"), vec!["[        ]"]);
}

#[test]
fn generated_wrap_columns_zero_columns_panics() {
    // Positive direction first, then the panic contract.
    assert_eq!(wrap_columns("fig", 1, 9, "", "", "").len(), 1);
    let outcome = std::panic::catch_unwind(|| wrap_columns("fig", 0, 9, "", "", ""));
    assert!(outcome.is_err());
}

// ---------------------------------------------------------------------------
// Text model: display width
// ---------------------------------------------------------------------------

#[test]
fn generated_display_width_ascii_cjk_emoji() {
    assert_eq!(display_width("otter"), 5);
    assert_eq!(display_width("山川"), 4);
    assert_eq!(display_width("🦀"), 2);
    assert_eq!(display_width("x🦀y"), 4);
}

#[test]
fn generated_display_width_combining_mark_zero() {
    assert_eq!(display_width("Cafe\u{301}"), 4);
}

#[test]
fn generated_display_width_skips_csi_sequences() {
    assert_eq!(display_width("\u{1b}[32mfern\u{1b}[0m"), 4);
}

#[test]
fn generated_display_width_skips_osc_hyperlinks() {
    assert_eq!(
        display_width("\u{1b}]8;;http://x\u{1b}\\link\u{1b}]8;;\u{1b}\\"),
        4
    );
}

// ---------------------------------------------------------------------------
// Text model: words and fragments
// ---------------------------------------------------------------------------

#[test]
fn generated_word_from_splits_trailing_whitespace() {
    let w = Word::from("tail-end  ");
    assert_eq!(w.word, "tail-end");
    assert_eq!(w.whitespace, "  ");
    assert_eq!(w.penalty, "");
}

#[test]
fn generated_word_derefs_to_content() {
    let w = Word::from("marsh ");
    assert_eq!(&*w, "marsh");
    assert!(w.starts_with("mar"));
}

#[test]
fn generated_word_fragment_measurement() {
    let w = Word::from("mole ");
    assert_eq!(w.width(), 4.0);
    assert_eq!(w.whitespace_width(), 1.0);
    assert_eq!(w.penalty_width(), 0.0);
}

#[test]
fn generated_word_break_apart_pieces() {
    let w = Word::from("tail-end  ");
    let pieces: Vec<(&str, &str, &str)> = w
        .break_apart(3)
        .map(|p| (p.word, p.whitespace, p.penalty))
        .collect();
    assert_eq!(pieces, vec![("tai", "", ""), ("l-e", "", ""), ("nd", "  ", "")]);
}

#[test]
fn generated_break_words_only_overlong() {
    let words = break_words(WordSeparator::AsciiSpace.find_words("tiny colossal"), 5);
    let contents: Vec<&str> = words.iter().map(|w| w.word).collect();
    assert_eq!(contents, vec!["tiny", "colos", "sal"]);
}

// ---------------------------------------------------------------------------
// Text model: word separators
// ---------------------------------------------------------------------------

#[test]
fn generated_ascii_space_attaches_runs() {
    let words: Vec<(&str, &str)> = WordSeparator::AsciiSpace
        .find_words("tab\there  end")
        .map(|w| (w.word, w.whitespace))
        .collect();
    assert_eq!(words, vec![("tab\there", "  "), ("end", "")]);
}

#[test]
fn generated_unicode_separator_splits_cjk() {
    let words: Vec<(&str, &str)> = WordSeparator::UnicodeBreakProperties
        .find_words("peak 山川")
        .map(|w| (w.word, w.whitespace))
        .collect();
    assert_eq!(words, vec![("peak", " "), ("山", ""), ("川", "")]);
}

#[test]
fn generated_unicode_separator_splits_emoji_run() {
    let words: Vec<&str> = WordSeparator::UnicodeBreakProperties
        .find_words("ok 🦀🦞")
        .map(|w| w.word)
        .collect();
    assert_eq!(words, vec!["ok", "🦀", "🦞"]);
}

#[test]
fn generated_unicode_separator_no_break_at_hyphen() {
    let words: Vec<&str> = WordSeparator::UnicodeBreakProperties
        .find_words("moss-grown stone")
        .map(|w| w.word)
        .collect();
    assert_eq!(words, vec!["moss-grown", "stone"]);
}

#[test]
fn generated_unicode_separator_word_joiner_suppresses_break() {
    let words: Vec<&str> = WordSeparator::UnicodeBreakProperties
        .find_words("go 🦀\u{2060}🦞 now")
        .map(|w| w.word)
        .collect();
    assert_eq!(words, vec!["go", "🦀\u{2060}🦞", "now"]);
}

#[test]
fn generated_custom_separator_delegates() {
    let sep = WordSeparator::Custom(|line| {
        Box::new(line.split_inclusive(',').map(Word::from))
    });
    let words: Vec<&str> = sep.find_words("a,b,c").map(|w| w.word).collect();
    assert_eq!(words, vec!["a,", "b,", "c"]);
}

#[test]
fn generated_separator_equality() {
    assert_eq!(WordSeparator::AsciiSpace, WordSeparator::AsciiSpace);
    assert_eq!(
        WordSeparator::UnicodeBreakProperties,
        WordSeparator::UnicodeBreakProperties
    );
    assert_ne!(WordSeparator::AsciiSpace, WordSeparator::UnicodeBreakProperties);
    let a = WordSeparator::Custom(|_| Box::new(std::iter::empty()));
    let b = WordSeparator::Custom(|_| Box::new(std::iter::empty()));
    assert_ne!(a, b);
}

// ---------------------------------------------------------------------------
// Text model: word splitters
// ---------------------------------------------------------------------------

#[test]
fn generated_hyphen_splitter_offsets() {
    assert_eq!(WordSplitter::HyphenSplitter.split_points("over-the-wall"), vec![5, 9]);
}

#[test]
fn generated_hyphen_splitter_needs_alphanumerics() {
    assert!(WordSplitter::HyphenSplitter.split_points("--flag").is_empty());
    assert_eq!(WordSplitter::HyphenSplitter.split_points("x-1 -a a- 3-4"), vec![2, 12]);
}

#[test]
fn generated_no_hyphenation_never_splits() {
    assert!(WordSplitter::NoHyphenation.split_points("over-the-wall").is_empty());
    assert!(WordSplitter::NoHyphenation.split_points("plain").is_empty());
}

#[test]
fn generated_custom_splitter_delegates() {
    let splitter = WordSplitter::Custom(|word| vec![word.len() / 2]);
    assert_eq!(splitter.split_points("windmill"), vec![4]);
}

#[test]
fn generated_splitter_equality() {
    assert_eq!(WordSplitter::HyphenSplitter, WordSplitter::HyphenSplitter);
    assert_ne!(WordSplitter::HyphenSplitter, WordSplitter::NoHyphenation);
    let a = WordSplitter::Custom(|_| vec![]);
    let b = WordSplitter::Custom(|_| vec![]);
    assert_ne!(a, b);
}

#[test]
fn generated_split_words_assigns_hyphen_penalty() {
    let words = WordSeparator::AsciiSpace.find_words("lantern glow");
    let split: Vec<(&str, &str, &str)> =
        split_words(words, &WordSplitter::Custom(|_| vec![3]))
            .map(|w| (w.word, w.whitespace, w.penalty))
            .collect();
    assert_eq!(
        split,
        vec![("lan", "", "-"), ("tern", " ", ""), ("glo", "", "-"), ("w", "", "")]
    );
}

#[test]
fn generated_split_words_hyphen_pieces_no_extra_penalty() {
    let words = WordSeparator::AsciiSpace.find_words("over-the-wall leap");
    let split: Vec<(&str, &str, &str)> =
        split_words(words, &WordSplitter::HyphenSplitter)
            .map(|w| (w.word, w.whitespace, w.penalty))
            .collect();
    assert_eq!(
        split,
        vec![("over-", "", ""), ("the-", "", ""), ("wall", " ", ""), ("leap", "", "")]
    );
}

// ---------------------------------------------------------------------------
// Line-breaking algorithms
// ---------------------------------------------------------------------------

#[test]
fn generated_wrap_algorithm_constructors_and_equality() {
    assert_eq!(WrapAlgorithm::new(), WrapAlgorithm::new_optimal_fit());
    assert_eq!(WrapAlgorithm::new_optimal_fit(), WrapAlgorithm::OptimalFit(Penalties::new()));
    assert_eq!(WrapAlgorithm::FirstFit, WrapAlgorithm::FirstFit);
    assert_ne!(WrapAlgorithm::FirstFit, WrapAlgorithm::new_optimal_fit());
    let a = WrapAlgorithm::Custom(|words, _| vec![words]);
    let b = WrapAlgorithm::Custom(|words, _| vec![words]);
    assert_ne!(a, b);
}

#[test]
fn generated_wrap_algorithm_wrap_repeats_last_width() {
    let words: Vec<Word> = WordSeparator::AsciiSpace
        .find_words("red fox digs deep den now")
        .collect();
    let lines = WrapAlgorithm::FirstFit.wrap(&words, &[12, 6]);
    let contents: Vec<Vec<&str>> = lines
        .iter()
        .map(|l| l.iter().map(|w| w.word).collect())
        .collect();
    assert_eq!(
        contents,
        vec![vec!["red", "fox", "digs"], vec!["deep"], vec!["den"], vec!["now"]]
    );
}

#[test]
fn generated_wrap_first_fit_greedy() {
    let words: Vec<Word> = WordSeparator::AsciiSpace
        .find_words("bat cat rat newt frog")
        .collect();
    let lines = wrap_first_fit(&words, &[9.0]);
    let contents: Vec<Vec<&str>> = lines
        .iter()
        .map(|l| l.iter().map(|w| w.word).collect())
        .collect();
    assert_eq!(contents, vec![vec!["bat", "cat"], vec!["rat", "newt"], vec!["frog"]]);
}

#[test]
fn generated_wrap_first_fit_custom_fragment_type() {
    #[derive(Debug)]
    struct Block(f64);
    impl Fragment for Block {
        fn width(&self) -> f64 {
            self.0
        }
        fn whitespace_width(&self) -> f64 {
            1.0
        }
        fn penalty_width(&self) -> f64 {
            0.0
        }
    }
    let blocks = [Block(3.0), Block(3.0), Block(3.0), Block(3.0)];
    let lines = wrap_first_fit(&blocks, &[7.0]);
    let sizes: Vec<usize> = lines.iter().map(|l| l.len()).collect();
    assert_eq!(sizes, vec![2, 2]);
}

#[test]
fn generated_optimal_fit_evens_lines() {
    let text = "some tiny words feel unnecessarily long here";
    let first = wrap(text, Options::new(15).wrap_algorithm(WrapAlgorithm::FirstFit));
    let optimal = wrap(text, Options::new(15).wrap_algorithm(WrapAlgorithm::new_optimal_fit()));
    assert_eq!(
        first,
        vec!["some tiny words", "feel", "unnecessarily", "long here"]
    );
    assert_eq!(
        optimal,
        vec!["some tiny", "words feel", "unnecessarily", "long here"]
    );
}

#[test]
fn generated_optimal_fit_short_last_line_penalty() {
    let text = "Here is a look at the short last row effect.";
    let default_layout = wrap(text, Options::new(37).wrap_algorithm(WrapAlgorithm::new_optimal_fit()));
    assert_eq!(
        default_layout,
        vec!["Here is a look at the short last", "row effect."]
    );
    let mut penalties = Penalties::new();
    penalties.short_last_line_fraction = 10;
    let narrowed = wrap(text, Options::new(37).wrap_algorithm(WrapAlgorithm::OptimalFit(penalties)));
    assert_eq!(
        narrowed,
        vec!["Here is a look at the short last row", "effect."]
    );
    let mut disabled = Penalties::new();
    disabled.short_last_line_penalty = 0;
    let plain = wrap(text, Options::new(37).wrap_algorithm(WrapAlgorithm::OptimalFit(disabled)));
    assert_eq!(plain, vec!["Here is a look at the short last row", "effect."]);
}

#[test]
fn generated_optimal_fit_overflow_error() {
    let words: Vec<Word> = WordSeparator::AsciiSpace.find_words("ash elm oak").collect();
    let result = wrap_optimal_fit(&words, &[f64::MAX], &Penalties::new());
    assert_eq!(result, Err(OverflowError));
    // Sane widths succeed.
    let ok = wrap_optimal_fit(&words, &[7.0], &Penalties::new()).unwrap();
    assert_eq!(ok.len(), 2);
}

#[test]
fn generated_penalties_defaults() {
    let p = Penalties::new();
    assert_eq!(p.nline_penalty, 1000);
    assert_eq!(p.overflow_penalty, 2500);
    assert_eq!(p.short_last_line_fraction, 4);
    assert_eq!(p.short_last_line_penalty, 25);
    assert_eq!(p.hyphen_penalty, 25);
    assert_eq!(Penalties::default(), p);
}
