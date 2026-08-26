// Composite grammar: nesting, dedent, and references across entries, each
// checked on the AST and on the canonical text at once.
mod grammar_compose {
    use super::*;

    #[test]
    fn generated_nested_select_fixed_point() {
        let canonical = concat!(
            "verdict =\n",
            "    { $outer ->\n",
            "       *[x]\n",
            "            { $inner ->\n",
            "               *[y] deep\n",
            "            }\n",
            "    }\n",
        );
        let parsed = ok(canonical);
        assert_eq!(serialize(&parsed), canonical);

        // The inner select sits inside the outer default variant's pattern.
        let outer = match &msg(&parsed, 0).value.as_ref().unwrap().elements[0] {
            PatternElement::Placeable {
                expression: Expression::Select { variants, .. },
            } => variants,
            e => panic!("expected outer select, got {e:?}"),
        };
        assert!(outer[0].default);
        assert!(matches!(
            &outer[0].value.elements[0],
            PatternElement::Placeable { expression: Expression::Select { .. } },
        ));
    }

    #[test]
    fn generated_dedent_placeable_select_combo() {
        // One pattern mixing dedented text, an inline placeable, and a
        // trailing line; asserted as AST and as canonical text.
        let input = "briefing =\n    Winds { $knots } knots\n      gusting later\n    Ends\n";
        let parsed = ok(input);
        assert_eq!(
            msg(&parsed, 0).value.as_ref().unwrap().elements,
            vec![
                text("Winds "),
                var("knots"),
                text(" knots\n"),
                text("  gusting later\n"),
                text("Ends"),
            ],
        );
        assert_eq!(serialize(&parsed), input);
    }

    #[test]
    fn generated_attribute_select_multiline() {
        let canonical = concat!(
            "door = Airlock\n",
            "    .state =\n",
            "        { $sealed ->\n",
            "            [yes] Shut tight\n",
            "           *[no] Cycling\n",
            "        }\n",
        );
        let parsed = ok(canonical);
        assert_eq!(serialize(&parsed), canonical);

        let attr = &msg(&parsed, 0).attributes[0];
        assert_eq!(attr.id.name, "state");
        let (selector, variants) = match &attr.value.elements[0] {
            PatternElement::Placeable {
                expression: Expression::Select { selector, variants },
            } => (selector, variants),
            e => panic!("expected select in attribute, got {e:?}"),
        };
        assert_eq!(
            selector,
            &InlineExpression::VariableReference { id: Identifier { name: "sealed" } },
        );
        assert_eq!(variants.len(), 2);
        assert_eq!(variants[1].key, VariantKey::Identifier { name: "no" });
        assert!(variants[1].default);
    }

    #[test]
    fn generated_term_message_cross_references() {
        let canonical = concat!(
            "-carrier = Spur Line\n",
            "    .short = Spur\n",
            "route-full = Board the { -carrier } here\n",
            "route-note = See { route-full } and { route-full.other }\n",
        );
        let parsed = ok(canonical);
        assert_eq!(serialize(&parsed), canonical);

        // Term with attribute.
        let t = match &parsed.body[0] {
            Entry::Term(t) => t,
            e => panic!("expected term, got {e:?}"),
        };
        assert_eq!(t.id.name, "carrier");
        assert_eq!(t.attributes[0].id.name, "short");

        // Message referencing the term.
        assert_eq!(
            msg(&parsed, 1).value.as_ref().unwrap().elements[1],
            PatternElement::Placeable {
                expression: Expression::Inline(InlineExpression::TermReference {
                    id: Identifier { name: "carrier" },
                    attribute: None,
                    arguments: None,
                }),
            },
        );

        // Message referencing another message and its attribute.
        let elems = &msg(&parsed, 2).value.as_ref().unwrap().elements;
        assert_eq!(
            elems[1],
            PatternElement::Placeable {
                expression: Expression::Inline(InlineExpression::MessageReference {
                    id: Identifier { name: "route-full" },
                    attribute: None,
                }),
            },
        );
        assert_eq!(
            elems[3],
            PatternElement::Placeable {
                expression: Expression::Inline(InlineExpression::MessageReference {
                    id: Identifier { name: "route-full" },
                    attribute: Some(Identifier { name: "other" }),
                }),
            },
        );
    }

    #[test]
    fn generated_call_args_in_selector() {
        let canonical = concat!(
            "window =\n",
            "    { COMPARE($eta, unit: \"min\") ->\n",
            "        [0] Now\n",
            "       *[other] Soon\n",
            "    }\n",
        );
        let parsed = ok(canonical);
        assert_eq!(serialize(&parsed), canonical);

        let (selector, _) = match &msg(&parsed, 0).value.as_ref().unwrap().elements[0] {
            PatternElement::Placeable {
                expression: Expression::Select { selector, variants },
            } => (selector, variants),
            e => panic!("expected select, got {e:?}"),
        };
        assert_eq!(
            selector,
            &InlineExpression::FunctionReference {
                id: Identifier { name: "COMPARE" },
                arguments: CallArguments {
                    positional: vec![InlineExpression::VariableReference {
                        id: Identifier { name: "eta" },
                    }],
                    named: vec![NamedArgument {
                        name: Identifier { name: "unit" },
                        value: InlineExpression::StringLiteral { value: "min" },
                    }],
                },
            },
        );
    }

    #[test]
    fn generated_document_kind_census() {
        let input = concat!(
            "### Manifest\n",
            "\n",
            "## Cargo block\n",
            "\n",
            "# attached\n",
            "crates = 40\n",
            "-vessel = Kestrel\n",
            "&bad line\n",
            "tail = end\n",
        );
        let (parsed, errors) = bad(input);
        assert_eq!(errors.len(), 1);

        let kinds: Vec<&str> = parsed
            .body
            .iter()
            .map(|e| match e {
                Entry::ResourceComment(_) => "resource",
                Entry::GroupComment(_) => "group",
                Entry::Comment(_) => "comment",
                Entry::Message(_) => "message",
                Entry::Term(_) => "term",
                Entry::Junk { .. } => "junk",
            })
            .collect();
        assert_eq!(
            kinds,
            vec!["resource", "group", "message", "term", "junk", "message"],
        );

        // Junk round-trips verbatim among canonical neighbors. Between the
        // two free comments the trailing frame of the first and the leading
        // frame of the second compose into two blank lines.
        let with_junk = serialize_with_options(&parsed, Options { with_junk: true });
        assert_eq!(
            with_junk,
            concat!(
                "### Manifest\n",
                "\n",
                "\n",
                "## Cargo block\n",
                "\n",
                "# attached\n",
                "crates = 40\n",
                "-vessel = Kestrel\n",
                "&bad line\n",
                "tail = end\n",
            ),
        );
        let reparsed = parse(with_junk.as_str())
            .expect_err("junk survives the round trip")
            .0;
        assert_eq!(reparsed, parsed);
    }

    #[test]
    fn generated_owned_string_parse() {
        // The same grammar runs over owned strings; the trees agree
        // structurally and serialize identically.
        let text_input = "berth = clear\nload = net { $kg } kg\n";
        let borrowed = ok(text_input);
        let owned: Resource<String> =
            parse(text_input.to_string()).expect("owned parse is clean");

        assert_eq!(owned.body.len(), borrowed.body.len());
        match (&owned.body[1], &borrowed.body[1]) {
            (Entry::Message(o), Entry::Message(b)) => {
                assert_eq!(o.id.name, b.id.name);
                assert_eq!(o.value.as_ref().unwrap().elements.len(), 3);
            }
            other => panic!("expected messages, got {other:?}"),
        }
        assert_eq!(serialize(&owned), serialize(&borrowed));
    }

    #[test]
    fn generated_empty_document_projections() {
        let empty = ok("");
        assert_eq!(empty.body.len(), 0);
        assert_eq!(serialize(&empty), "");

        let blank: Resource<&str> = parse_runtime("\n   \n\n").expect("blanks are clean");
        assert_eq!(blank.body.len(), 0);
        assert_eq!(serialize(&blank), "");
    }
}
