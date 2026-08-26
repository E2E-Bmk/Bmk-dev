// Error recovery bound to the surviving tree and the input byte ranges.
mod recovery {
    use super::*;

    #[test]
    fn generated_multi_error_order() {
        let input = "good-a = 1\nbroken 2\ngood-b = 3\n%stray\ngood-c = 4\n";
        let (parsed, errors) = bad(input);

        assert_eq!(errors.len(), 2);
        assert_eq!(errors[0].kind, ErrorKind::ExpectedToken('='));
        assert_eq!(
            errors[1].kind,
            ErrorKind::ExpectedCharRange { range: "a-zA-Z".to_string() },
        );
        // Errors arrive in input order: slices must be ascending.
        let s0 = errors[0].slice.clone().unwrap();
        let s1 = errors[1].slice.clone().unwrap();
        assert!(s0.end <= s1.start);

        // The sandwiched and trailing entries all survive.
        assert_eq!(parsed.body.len(), 5);
        assert_eq!(msg(&parsed, 0).id.name, "good-a");
        assert_eq!(parsed.body[1], Entry::Junk { content: "broken 2\n" });
        assert_eq!(msg(&parsed, 2).id.name, "good-b");
        assert_eq!(parsed.body[3], Entry::Junk { content: "%stray\n" });
        assert_eq!(msg(&parsed, 4).id.name, "good-c");
    }

    #[test]
    fn generated_error_positions() {
        // Missing `=`: pos points at the byte where `=` was required.
        let input = "flow = up\nvent 9\nseal = ok\n";
        let (_, errors) = bad(input);
        assert_eq!(
            errors[0],
            ParserError {
                pos: 15..16,
                slice: Some(10..17),
                kind: ErrorKind::ExpectedToken('='),
            },
        );
        assert_eq!(&input[10..17], "vent 9\n");

        // Entry-start failure: pos is the offending byte at the line start.
        let input = "calm = 1\n\n4loud = 2\n";
        let (_, errors) = bad(input);
        assert_eq!(
            errors[0],
            ParserError {
                pos: 10..11,
                slice: Some(10..20),
                kind: ErrorKind::ExpectedCharRange { range: "a-zA-Z".to_string() },
            },
        );
    }

    #[test]
    fn generated_mid_entry_error_junks_whole() {
        // The selector error happens lines into the entry; the whole entry
        // (including its later lines) becomes one junk span, and the next
        // entry parses.
        let input = "plan =\n    { chart ->\n       *[x] y\n    }\nnext = fine\n";
        let (parsed, errors) = bad(input);
        assert_eq!(errors.len(), 1);
        assert_eq!(errors[0].kind, ErrorKind::MessageReferenceAsSelector);
        assert_eq!(
            parsed.body[0],
            Entry::Junk { content: "plan =\n    { chart ->\n       *[x] y\n    }\n" },
        );
        assert_eq!(msg(&parsed, 1).id.name, "next");
    }

    #[test]
    fn generated_missing_field_recovery() {
        let input = "cargo =\n\nnext = ok\n";
        let (parsed, errors) = bad(input);
        assert_eq!(
            errors[0],
            ParserError {
                pos: 0..9,
                slice: Some(0..9),
                kind: ErrorKind::ExpectedMessageField { entry_id: "cargo".to_string() },
            },
        );
        assert_eq!(parsed.body[0], Entry::Junk { content: "cargo =\n\n" });
        assert_eq!(msg(&parsed, 1).id.name, "next");
    }

    #[test]
    fn generated_junk_reconstruction() {
        // Every junk entry's content is recoverable from the input through
        // its error's slice, and the non-junk remainder serializes cleanly.
        let input = "tide = high\n?first bad\nswell = low\n!second bad\ncalm = yes\n";
        let (parsed, errors) = bad(input);
        assert_eq!(errors.len(), 2);

        let junk_contents: Vec<&str> = parsed
            .body
            .iter()
            .filter_map(|e| match e {
                Entry::Junk { content } => Some(*content),
                _ => None,
            })
            .collect();
        let sliced: Vec<&str> = errors
            .iter()
            .map(|e| &input[e.slice.clone().unwrap()])
            .collect();
        assert_eq!(junk_contents, sliced);
        assert_eq!(junk_contents, vec!["?first bad\n", "!second bad\n"]);

        assert_eq!(serialize(&parsed), "tide = high\nswell = low\ncalm = yes\n");
    }
}
