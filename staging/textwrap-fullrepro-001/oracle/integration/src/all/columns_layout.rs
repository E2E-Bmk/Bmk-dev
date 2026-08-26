// Column layout as a projection of the same wrapping run.
mod columns_layout {
    use textwrap::core::display_width;
    use textwrap::{wrap, wrap_columns, Options, WordSeparator, WordSplitter, WrapAlgorithm};

    // Reproduce the documented column arithmetic and distribution.
    fn manual_columns(
        text: &str,
        columns: usize,
        options: Options<'_>,
        left_gap: &str,
        middle_gap: &str,
        right_gap: &str,
    ) -> Vec<String> {
        let mut options = options;
        let inner_width = options
            .width
            .saturating_sub(display_width(left_gap))
            .saturating_sub(display_width(right_gap))
            .saturating_sub(display_width(middle_gap) * (columns - 1));
        let column_width = std::cmp::max(inner_width / columns, 1);
        options.width = column_width;
        let last_padding = " ".repeat(inner_width % column_width);
        let wrapped = wrap(text, options);
        let per_col = wrapped.len() / columns + usize::from(wrapped.len() % columns > 0);
        let mut rows = Vec::new();
        for row in 0..per_col {
            let mut line = String::from(left_gap);
            for col in 0..columns {
                match wrapped.get(row + col * per_col) {
                    Some(cell) => {
                        line.push_str(cell);
                        line.push_str(&" ".repeat(column_width - display_width(cell)));
                    }
                    None => line.push_str(&" ".repeat(column_width)),
                }
                if col == columns - 1 {
                    line.push_str(&last_padding);
                } else {
                    line.push_str(middle_gap);
                }
            }
            line.push_str(right_gap);
            rows.push(line);
        }
        rows
    }

    #[test]
    fn generated_columns_match_manual_distribution() {
        let text = "mint sage rue dill leek anise chive basil";
        for (cols, total) in [(2usize, 24usize), (3, 30), (4, 41)] {
            let actual = wrap_columns(text, cols, total, "|", " ", "|");
            let expected = manual_columns(text, cols, Options::new(total), "|", " ", "|");
            assert_eq!(actual, expected, "cols={} total={}", cols, total);
        }
    }

    #[test]
    fn generated_columns_respect_caller_options() {
        // The wrap algorithm carried by the options changes the distribution.
        let text = "some tiny words feel unnecessarily long here";
        let opts = Options::new(34)
            .wrap_algorithm(WrapAlgorithm::FirstFit)
            .word_separator(WordSeparator::AsciiSpace)
            .word_splitter(WordSplitter::NoHyphenation);
        let actual = wrap_columns(text, 2, &opts, "[", "][", "]");
        let expected = manual_columns(text, 2, (&opts).into(), "[", "][", "]");
        assert_eq!(actual, expected);
        let default_rows = wrap_columns(text, 2, 34, "[", "][", "]");
        assert_ne!(actual, default_rows);
    }

    #[test]
    fn generated_columns_uniform_width_and_gaps() {
        let rows = wrap_columns("mint sage rue dill leek anise", 3, 30, "|", " ", "|");
        assert!(!rows.is_empty());
        assert!(rows.iter().all(|r| display_width(r) == 30));
        assert!(rows.iter().all(|r| r.starts_with('|') && r.ends_with('|')));
    }

    #[test]
    fn generated_columns_width_floor_of_one() {
        // Gaps consume the whole budget; column width bottoms out at 1.
        let rows = wrap_columns("uvw", 2, 10, "==> ", " ## ", " <==");
        assert_eq!(rows, vec!["==> u ## w <==", "==> v ##   <=="]);
    }

    #[test]
    fn generated_columns_of_empty_text_single_blank_row() {
        let rows = wrap_columns("", 2, 13, "( ", " | ", " )");
        assert_eq!(rows.len(), 1);
        assert!(rows[0].starts_with("( ") && rows[0].ends_with(" )"));
        assert_eq!(display_width(&rows[0]), 13);
    }
}
