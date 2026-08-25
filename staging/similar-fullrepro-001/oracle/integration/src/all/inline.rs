// Inline emphasis over line diffs: tags, indices, coverage, and rendering.

mod inline {
    use similar::{ChangeTag, TextDiff};

    #[test]
    fn test_line_ops_inline() {
        let diff = TextDiff::from_lines(
            "Hello World\nsome stuff here\nsome more stuff here\n\nAha stuff here\nand more stuff",
            "Stuff\nHello World\nsome amazing stuff here\nsome more stuff here\n",
        );
        assert!(diff.newline_terminated());
        let changes: Vec<_> = diff
            .ops()
            .iter()
            .flat_map(|op| diff.iter_inline_changes(op))
            .collect();

        // Tag/index skeleton of the inline stream.
        let skeleton: Vec<_> = changes
            .iter()
            .map(|c| (c.tag(), c.old_index(), c.new_index()))
            .collect();
        assert_eq!(
            skeleton,
            vec![
                (ChangeTag::Insert, None, Some(0)),
                (ChangeTag::Equal, Some(0), Some(1)),
                (ChangeTag::Delete, Some(1), None),
                (ChangeTag::Insert, None, Some(2)),
                (ChangeTag::Equal, Some(2), Some(3)),
                (ChangeTag::Delete, Some(3), None),
                (ChangeTag::Delete, Some(4), None),
                (ChangeTag::Delete, Some(5), None),
            ]
        );

        // Concatenated segment values reproduce each underlying line.
        let concat: Vec<String> = changes
            .iter()
            .map(|c| c.values().iter().map(|(_, v)| *v).collect())
            .collect();
        assert_eq!(
            concat,
            vec![
                "Stuff\n",
                "Hello World\n",
                "some stuff here\n",
                "some amazing stuff here\n",
                "some more stuff here\n",
                "\n",
                "Aha stuff here\n",
                "and more stuff",
            ]
        );

        // The replaced pair is similar, so the inserted line carries an
        // emphasized segment covering exactly the inserted word.
        let inserted = &changes[3];
        assert!(inserted.values().iter().any(|(e, _)| *e));
        let emphasized: String = inserted
            .values()
            .iter()
            .filter(|(e, _)| *e)
            .map(|(_, v)| *v)
            .collect();
        assert_eq!(emphasized.trim(), "amazing");
        // Newline-only segments are never emphasized.
        for c in &changes {
            for (emphasized, value) in c.values() {
                if value.chars().all(|ch| ch == '\r' || ch == '\n') {
                    assert!(!emphasized);
                }
            }
        }
        // The final line is missing its newline.
        assert!(changes.last().unwrap().missing_newline());
        assert!(!changes[0].missing_newline());
    }

    #[test]
    fn generated_inline_simple_word_replace() {
        let diff = TextDiff::from_lines("foo bar baz\n", "foo bor baz\n");
        assert_eq!(diff.ops().len(), 1);
        let inline: Vec<_> = diff.iter_inline_changes(&diff.ops()[0]).collect();
        assert_eq!(inline.len(), 2);

        assert_eq!(inline[0].tag(), ChangeTag::Delete);
        assert_eq!(inline[0].old_index(), Some(0));
        let del_emph: String = inline[0]
            .values()
            .iter()
            .filter(|(e, _)| *e)
            .map(|(_, v)| *v)
            .collect();
        assert_eq!(del_emph, "bar");
        assert_eq!(inline[0].to_string(), "foo -bar- baz\n");

        assert_eq!(inline[1].tag(), ChangeTag::Insert);
        assert_eq!(inline[1].new_index(), Some(0));
        let ins_emph: String = inline[1]
            .values()
            .iter()
            .filter(|(e, _)| *e)
            .map(|(_, v)| *v)
            .collect();
        assert_eq!(ins_emph, "bor");
        assert_eq!(inline[1].to_string(), "foo +bor+ baz\n");
    }

    #[test]
    fn generated_inline_coverage_invariant() {
        let old = "alpha one\nbeta two\ngamma three\n";
        let new = "alpha one\nbeta twelve\ngamma three\nextra four\n";
        let diff = TextDiff::from_lines(old, new);
        for op in diff.ops() {
            let plain: String = diff.iter_changes(op).map(|c| c.value().to_string()).collect();
            let inline: String = diff
                .iter_inline_changes(op)
                .flat_map(|ic| {
                    ic.values()
                        .iter()
                        .map(|(_, v)| v.to_string())
                        .collect::<Vec<_>>()
                })
                .collect();
            assert_eq!(plain, inline);
        }
    }

    #[test]
    fn generated_inline_deadline_variant_agrees() {
        let diff = TextDiff::from_lines("red green blue\n", "red grain blue\n");
        let op = diff.ops()[0];
        let with_default: Vec<_> = diff.iter_inline_changes(&op).collect();
        let with_none: Vec<_> = diff.iter_inline_changes_deadline(&op, None).collect();
        assert_eq!(with_default, with_none);
        assert!(with_default.iter().any(|c| c.values().iter().any(|(e, _)| *e)));
    }
}
