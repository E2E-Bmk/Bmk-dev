// Indentation utilities composed with wrapping and with each other.
mod indent_dedent {
    use textwrap::core::display_width;
    use textwrap::{dedent, fill, indent, Options};

    #[test]
    fn generated_indent_dedent_roundtrip() {
        let texts = [
            "Silt.\nGravel banks.\nShoal.",
            "Silt.\nGravel banks.\n\nShoal.",
            "\nSilt.\nGravel banks.\nShoal.\n",
        ];
        for pad in ["    ", "\t\t", " \t  \t "] {
            for text in texts {
                assert_eq!(dedent(&indent(text, pad)), text, "pad={:?}", pad);
            }
        }
    }

    #[test]
    fn generated_indent_empty_prefix_identity() {
        let texts = [
            "Silt.\nGravel banks.\nShoal.",
            "Silt.\r\nGravel banks.\r\nShoal.",
            "Silt.\r\nGravel banks.\n\r\nShoal.\r\n\n",
        ];
        for text in texts {
            assert_eq!(indent(text, ""), text);
        }
    }

    #[test]
    fn generated_fill_with_indents_equals_indent_of_fill() {
        let text = "kestrel bramble otter marsh heath";
        for prefix in ["> ", "   "] {
            let width = 18usize;
            let direct = fill(
                text,
                Options::new(width)
                    .initial_indent(prefix)
                    .subsequent_indent(prefix),
            );
            let composed = indent(&fill(text, width - display_width(prefix)), prefix);
            assert_eq!(direct, composed, "prefix={:?}", prefix);
        }
    }

    #[test]
    fn generated_dedent_then_reindent_shifts_margin() {
        let nested = "    fn body() {\n        call();\n    }\n";
        let flattened = dedent(nested);
        assert_eq!(flattened, "fn body() {\n    call();\n}\n");
        let shifted = indent(&flattened, "  ");
        assert_eq!(shifted, "  fn body() {\n      call();\n  }\n");
    }

    #[test]
    fn generated_indent_marker_then_dedent_partial() {
        // A non-whitespace marker prefix is not removable by dedent: dedent
        // only strips whitespace, so the marker survives.
        let text = "north\nsouth\n";
        let marked = indent(text, "@@ ");
        assert_eq!(marked, "@@ north\n@@ south\n");
        assert_eq!(dedent(&marked), marked);
    }
}
