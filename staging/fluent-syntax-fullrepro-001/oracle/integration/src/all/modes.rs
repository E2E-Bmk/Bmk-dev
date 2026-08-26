// The two parser entry points as projections of one grammar.
mod modes {
    use super::*;

    #[test]
    fn generated_modes_agree_commentfree() {
        let input = "hold = full\n-berth = North Slip\nload =\n    { $kg ->\n       *[other] { $kg } kg\n    }\n";
        let full = ok(input);
        let runtime = parse_runtime(input).expect("runtime parses cleanly");
        assert_eq!(full, runtime);
        assert_eq!(full.body.len(), 3);
    }

    #[test]
    fn generated_modes_agree_commentfree_errors() {
        let input = "ok = 1\n!oops\nfin = 2\n";
        let (full, full_errs) = bad(input);
        let (runtime, runtime_errs) =
            parse_runtime(input).expect_err("runtime reports the same junk");
        assert_eq!(full_errs, runtime_errs);
        assert_eq!(full.body, runtime.body);
        assert_eq!(full.body[1], Entry::Junk { content: "!oops\n" });
    }

    #[test]
    fn generated_runtime_projection() {
        let input = concat!(
            "### File header\n",
            "\n",
            "## Board section\n",
            "\n",
            "# attached note\n",
            "lane-a = open\n",
            "\n",
            "# floating note\n",
            "\n",
            "lane-b = shut\n",
        );
        let full = ok(input);
        let runtime = parse_runtime(input).expect("runtime parses cleanly");

        // Full mode: resource + group + message(attached) + comment + message.
        assert_eq!(full.body.len(), 5);
        assert!(matches!(full.body[0], Entry::ResourceComment(_)));
        assert!(matches!(full.body[1], Entry::GroupComment(_)));
        assert_eq!(
            msg(&full, 2).comment,
            Some(Comment { content: vec!["attached note"] }),
        );
        assert!(matches!(full.body[3], Entry::Comment(_)));

        // Runtime mode: exactly the two messages, comments nulled.
        assert_eq!(runtime.body.len(), 2);
        let expected: Vec<Entry<&str>> = full
            .body
            .iter()
            .filter_map(|e| match e {
                Entry::Message(m) => Some(Entry::Message(Message {
                    comment: None,
                    ..m.clone()
                })),
                _ => None,
            })
            .collect();
        assert_eq!(runtime.body, expected);
    }

    #[test]
    fn generated_malformed_comment_asymmetry() {
        let input = "#skiff\nrudder = trim\n";
        let (full, errs) = bad(input);
        assert_eq!(errs.len(), 1);
        assert_eq!(errs[0].kind, ErrorKind::ExpectedToken(' '));
        assert_eq!(full.body[0], Entry::Junk { content: "#skiff\n" });

        let runtime = parse_runtime(input).expect("runtime skips the malformed line");
        assert_eq!(runtime.body.len(), 1);
        assert_eq!(msg(&runtime, 0).id.name, "rudder");
    }

    #[test]
    fn generated_comment_attachment_roundtrip() {
        // Attached: survives serialize→reparse on the node.
        let attached = "# hull note\nhull = sound\n";
        let first = ok(attached);
        let rendered = serialize(&first);
        assert_eq!(rendered, attached);
        let again = parse(rendered.as_str()).expect("reparse");
        assert_eq!(again, first);
        assert_eq!(
            msg(&again, 0).comment,
            Some(Comment { content: vec!["hull note"] }),
        );

        // Standalone: gains its blank-line frame once, then stays stable.
        let standalone = "# drift\n\nhull = sound\n";
        let first = ok(standalone);
        assert_eq!(first.body[0], Entry::Comment(Comment { content: vec!["drift"] }));
        let rendered = serialize(&first);
        assert_eq!(rendered, "# drift\n\nhull = sound\n");
        let again = parse(rendered.as_str()).expect("reparse");
        assert_eq!(again, first);
    }
}
