// Round trips binding the parser, the serializer, and the AST to one
// document.
mod round_trip {
    use super::*;

    #[test]
    fn generated_canonical_fixed_point_document() {
        let canonical = concat!(
            "### Harbor strings\n",
            "\n",
            "-quay-name = Long Reach\n",
            "# Shown on the main board.\n",
            "arrivals = Serving { -quay-name }\n",
            "    .short = Arrivals\n",
            "tonnage =\n",
            "    { $tons ->\n",
            "        [one] One ton\n",
            "       *[other] { $tons } tons\n",
            "    }\n",
        );
        let parsed = ok(canonical);
        assert_eq!(serialize(&parsed), canonical);

        // Reparsing the rendered text reproduces the same tree.
        let rendered = serialize(&parsed);
        let reparsed = parse(rendered.as_str()).expect("canonical text parses cleanly");
        assert_eq!(reparsed, parsed);

        // The attached comment survived the trip on the message node.
        assert_eq!(
            msg(&reparsed, 2).comment,
            Some(Comment { content: vec!["Shown on the main board."] }),
        );
    }

    #[test]
    fn generated_normalization_idempotence() {
        let messy_inputs = [
            "pier=docked\n",
            "quay =    spaced   \n",
            "deck =\n  low indent\n  second line\n",
            "cargo = head\n    tail\n",
            "report = {$n} of {NOW()}\n",
            "gap =\n    first\n\n    last\n",
        ];
        for input in messy_inputs {
            let n = serialize(&ok(input));
            let n2 = serialize(&ok(n.as_str()));
            assert_eq!(n2, n, "serialize∘parse not idempotent for {input:?}");
        }

        // One normalization pinned exactly: spacing, indent width, and the
        // newline form all change while the content survives.
        assert_eq!(
            serialize(&ok("deck =\n  low indent\n  second line\n")),
            "deck =\n    low indent\n    second line\n",
        );
    }

    #[test]
    fn generated_handbuilt_serialize_reparse() {
        let built: Resource<&str> = Resource {
            body: vec![
                Entry::Term(Term {
                    id: Identifier { name: "line-name" },
                    value: Pattern { elements: vec![text("Outer Belt")] },
                    attributes: vec![],
                    comment: None,
                }),
                Entry::Message(Message {
                    id: Identifier { name: "greeting" },
                    value: Some(Pattern {
                        elements: vec![text("Ride the "), var("route"), text(" line")],
                    }),
                    attributes: vec![Attribute {
                        id: Identifier { name: "short" },
                        value: Pattern { elements: vec![text("Ride")] },
                    }],
                    comment: Some(Comment { content: vec!["voice line"] }),
                }),
            ],
        };
        let rendered = serialize(&built);
        assert_eq!(
            rendered,
            "-line-name = Outer Belt\n# voice line\ngreeting = Ride the { $route } line\n    .short = Ride\n",
        );
        let reparsed = parse(rendered.as_str()).expect("rendered tree parses");
        assert_eq!(reparsed, built);
    }

    #[test]
    fn generated_reparse_equality_messy() {
        // Non-canonical inputs whose parse trees survive one render→reparse
        // trip element-for-element.
        let inputs = [
            "pier=docked\n",
            "note = head\n    tail\n",
            "gap =\n    first\n\n    last\n",
            "sel = { $n ->\n   *[other] fine\n}\n",
        ];
        for input in inputs {
            let first = ok(input);
            let rendered = serialize(&first);
            let second = parse(rendered.as_str()).expect("rendered parses");
            assert_eq!(second, first, "reparse changed the tree for {input:?}");
        }
    }

    #[test]
    fn generated_junk_fidelity() {
        let input = "sound = on\n%static burst\n\nsignal = clear\n";
        let (parsed, errors) = bad(input);

        // The error's slice range extracts exactly the junk content.
        assert_eq!(errors.len(), 1);
        let slice = errors[0].slice.clone().expect("reported errors carry a slice");
        let junk_text = &input[slice];
        assert_eq!(junk_text, "%static burst\n\n");
        assert_eq!(parsed.body[1], Entry::Junk { content: junk_text });

        // With-junk serialization embeds it verbatim; without, only the
        // clean entries render.
        assert_eq!(
            serialize_with_options(&parsed, Options { with_junk: true }),
            "sound = on\n%static burst\n\nsignal = clear\n",
        );
        assert_eq!(serialize(&parsed), "sound = on\nsignal = clear\n");
    }

    #[test]
    fn generated_crlf_lf_equivalence() {
        let lf = "# board note\nlanes = two\nwide =\n    aa\n    bb\n";
        let crlf = lf.replace('\n', "\r\n");
        let from_lf = ok(lf);
        let from_crlf = parse(crlf.as_str()).expect("CRLF parses cleanly");

        // Entry structure and comment content agree.
        assert_eq!(from_lf.body.len(), from_crlf.body.len());
        assert_eq!(msg(&from_lf, 0).comment, msg(&from_crlf, 0).comment);
        assert_eq!(msg(&from_lf, 1).id.name, msg(&from_crlf, 1).id.name);

        // Pattern text concatenation agrees even though the element split
        // differs; the serialized output is identical LF text.
        assert_eq!(
            flat_text(msg(&from_lf, 1).value.as_ref().unwrap()),
            flat_text(msg(&from_crlf, 1).value.as_ref().unwrap()),
        );
        assert_eq!(serialize(&from_lf), serialize(&from_crlf));
        assert_eq!(serialize(&from_crlf), lf);
    }

    #[test]
    fn generated_literal_raw_roundtrip() {
        let canonical = "probe = { \"\\u0394 shift\" }\n";
        let parsed = ok(canonical);

        // Parser keeps the escape raw…
        let raw = match &msg(&parsed, 0).value.as_ref().unwrap().elements[0] {
            PatternElement::Placeable {
                expression: Expression::Inline(InlineExpression::StringLiteral { value }),
            } => *value,
            e => panic!("expected string literal, got {e:?}"),
        };
        assert_eq!(raw, "\\u0394 shift");

        // …the serializer reproduces it verbatim…
        assert_eq!(serialize(&parsed), canonical);

        // …and the unescaper decodes it.
        assert_eq!(unescape_unicode_to_string(raw), "Δ shift");
    }
}
