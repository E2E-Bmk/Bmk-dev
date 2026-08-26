// The unescaping helpers bound to parsed literals and to the parser's own
// escape validation.
mod unicode_binding {
    use super::*;

    #[test]
    fn generated_parse_unescape_pipeline() {
        let canonical = "salute = { \"\\U01F680 lift\" } and { \"bay \\u0041\" }\n";
        let parsed = ok(canonical);

        // Collect the raw literal values off the tree.
        let raws: Vec<&str> = msg(&parsed, 0)
            .value
            .as_ref()
            .unwrap()
            .elements
            .iter()
            .filter_map(|e| match e {
                PatternElement::Placeable {
                    expression: Expression::Inline(InlineExpression::StringLiteral { value }),
                } => Some(*value),
                _ => None,
            })
            .collect();
        assert_eq!(raws, vec!["\\U01F680 lift", "bay \\u0041"]);

        // The serializer emits them raw; the unescaper decodes them.
        assert_eq!(serialize(&parsed), canonical);
        assert_eq!(unescape_unicode_to_string(raws[0]), "🚀 lift");
        let mut second = String::new();
        unescape_unicode(&mut second, raws[1]).expect("write to String cannot fail");
        assert_eq!(second, "bay A");

        // Escape-free literals stay borrowed all the way through.
        let plain = ok("flat = { \"no escapes\" }\n");
        let raw = match &msg(&plain, 0).value.as_ref().unwrap().elements[0] {
            PatternElement::Placeable {
                expression: Expression::Inline(InlineExpression::StringLiteral { value }),
            } => *value,
            e => panic!("expected literal, got {e:?}"),
        };
        assert!(matches!(unescape_unicode_to_string(raw), Cow::Borrowed(_)));
    }

    #[test]
    fn generated_parser_vs_unescaper_asymmetry() {
        // `\{` passes the parser and serializes verbatim, but the unescaper
        // treats it as unknown and substitutes U+FFFD.
        let canonical = "brace = { \"open \\{ here\" }\n";
        let parsed = ok(canonical);
        assert_eq!(serialize(&parsed), canonical);
        let raw = match &msg(&parsed, 0).value.as_ref().unwrap().elements[0] {
            PatternElement::Placeable {
                expression: Expression::Inline(InlineExpression::StringLiteral { value }),
            } => *value,
            e => panic!("expected literal, got {e:?}"),
        };
        assert_eq!(raw, "open \\{ here");
        assert_eq!(unescape_unicode_to_string(raw), "open \u{FFFD} here");

        // `\p` fails the parser outright — the same text the unescaper would
        // map to U+FFFD never reaches a literal node.
        let (r, errs) = bad("brace = { \"open \\p here\" }\n");
        assert!(matches!(errs[0].kind, ErrorKind::UnknownEscapeSequence(_)));
        assert!(matches!(r.body[0], Entry::Junk { .. }));
        assert_eq!(unescape_unicode_to_string("open \\p here"), "open \u{FFFD} here");
    }
}
