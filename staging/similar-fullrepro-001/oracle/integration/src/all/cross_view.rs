// Cross-view invariants: op streams, changes, text layer, similarity,
// remapping, and deadlines must agree with each other.

mod cross_view {
    use similar::algorithms::{Capture, Compact, IdentifyDistinct, Replace};
    use similar::utils::TextDiffRemapper;
    use similar::{
        capture_diff_deadline, capture_diff_slices, capture_diff_slices_deadline,
        get_diff_ratio, Algorithm, ChangeTag, DiffOp, DiffTag, TextDiff,
    };

    /// Applies an op stream to the old/new sequences: returns the
    /// reconstructed new sequence and checks the old-side partition.
    fn apply_ops<T: Clone + PartialEq + std::fmt::Debug>(
        ops: &[DiffOp],
        old: &[T],
        new: &[T],
    ) -> Vec<T> {
        let mut rebuilt: Vec<T> = Vec::new();
        let mut old_cursor = 0usize;
        for op in ops {
            let (tag, old_range, new_range) = op.as_tag_tuple();
            match tag {
                DiffTag::Equal => {
                    assert_eq!(old_range.start, old_cursor);
                    assert_eq!(&old[old_range.clone()], &new[new_range.clone()]);
                    rebuilt.extend_from_slice(&old[old_range.clone()]);
                    old_cursor = old_range.end;
                }
                DiffTag::Delete => {
                    assert_eq!(old_range.start, old_cursor);
                    old_cursor = old_range.end;
                }
                DiffTag::Insert => {
                    rebuilt.extend_from_slice(&new[new_range.clone()]);
                }
                DiffTag::Replace => {
                    assert_eq!(old_range.start, old_cursor);
                    old_cursor = old_range.end;
                    rebuilt.extend_from_slice(&new[new_range.clone()]);
                }
            }
        }
        assert_eq!(old_cursor, old.len(), "old ranges must partition the old sequence");
        rebuilt
    }

    #[test]
    fn generated_reconstruction_all_algorithms() {
        let old: Vec<&str> = "the swift umber vixen hops over the idle hound"
            .split(' ')
            .collect();
        let new: Vec<&str> = "the swift umber wolf hops far over an idle hound"
            .split(' ')
            .collect();
        for alg in [Algorithm::Myers, Algorithm::Patience, Algorithm::Lcs] {
            let ops = capture_diff_slices(alg, &old, &new);
            assert_eq!(apply_ops(&ops, &old, &new), new, "algorithm {:?}", alg);
        }
        let old_nums: Vec<u16> = vec![3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5];
        let new_nums: Vec<u16> = vec![3, 1, 4, 2, 7, 9, 2, 6, 5, 8];
        for alg in [Algorithm::Myers, Algorithm::Patience, Algorithm::Lcs] {
            let ops = capture_diff_slices(alg, &old_nums, &new_nums);
            assert_eq!(apply_ops(&ops, &old_nums, &new_nums), new_nums);
        }
    }

    #[test]
    fn generated_text_vs_generic_ops_small() {
        use similar::DiffableStr;
        let old = "north\neast\nsouth\nwest\n";
        let new = "north\nEAST\nsouth\nwest\ncenter\n";
        let diff = TextDiff::from_lines(old, new);
        let tokens_old = old.tokenize_lines();
        let tokens_new = new.tokenize_lines();
        let generic = capture_diff_slices(Algorithm::Myers, &tokens_old, &tokens_new);
        assert_eq!(diff.ops(), &generic[..]);
    }

    #[test]
    fn generated_text_vs_generic_ops_large() {
        use similar::DiffableStr;
        // More than 100 tokens per side: the text layer must still produce
        // the same op stream as the generic capture over the same tokens.
        let old: String = (0..130).map(|i| format!("row number {}\n", i)).collect();
        let new: String = (0..130)
            .map(|i| {
                if i % 37 == 5 {
                    format!("row NUMBER {}\n", i)
                } else {
                    format!("row number {}\n", i)
                }
            })
            .collect();
        let diff = TextDiff::from_lines(old.as_str(), new.as_str());
        let tokens_old = old.as_str().tokenize_lines();
        let tokens_new = new.as_str().tokenize_lines();
        let generic = capture_diff_slices(Algorithm::Myers, &tokens_old, &tokens_new);
        assert_eq!(diff.ops(), &generic[..]);
        assert_eq!(
            apply_ops(diff.ops(), &tokens_old, &tokens_new),
            tokens_new
        );
    }

    #[test]
    fn generated_iter_all_changes_equals_flat_map() {
        let diff = TextDiff::from_words("piano forte organ", "piano viola organ harp");
        let all: Vec<_> = diff.iter_all_changes().collect();
        let flat: Vec<_> = diff
            .ops()
            .iter()
            .flat_map(|op| diff.iter_changes(op))
            .collect();
        assert_eq!(all, flat);
        assert!(!all.is_empty());
    }

    #[test]
    fn generated_ratio_equals_get_diff_ratio() {
        let diff = TextDiff::from_chars("kitten", "sitting");
        assert_eq!(
            diff.ratio(),
            get_diff_ratio(diff.ops(), diff.old_slices().len(), diff.new_slices().len())
        );
        // Sanity: kitten/sitting share 4 matched characters ("itt" + "n")
        // -> 2*4/13.
        assert_eq!(diff.ratio(), 2.0 * 4.0 / 13.0);
    }

    #[test]
    fn generated_close_matches_agree_with_char_ratio() {
        let word = "spinach";
        let candidates = ["spinner", "spindle", "spinach!", "squash", "peach"];
        let matches = similar::get_close_matches(word, &candidates[..], 5, 0.6);
        let mut last_ratio = f32::INFINITY;
        for m in &matches {
            let ratio = TextDiff::from_chars(word, m).ratio();
            assert!(ratio >= 0.6, "{} below cutoff", m);
            assert!(ratio <= last_ratio, "ordering must be non-increasing");
            last_ratio = ratio;
        }
        assert!(matches.contains(&"spinach!"));
        for c in &candidates {
            if !matches.contains(c) {
                assert!(TextDiff::from_chars(word, *c).ratio() < 0.6);
            }
        }
    }

    #[test]
    fn generated_deadline_still_valid_script() {
        use std::time::Instant;
        let old: Vec<u32> = (0..300).map(|i| i * 3 % 271).collect();
        let new: Vec<u32> = (0..300).map(|i| i * 7 % 269).collect();
        // An already-expired deadline forces the approximation path; the
        // result must still be a valid edit script.
        let ops = capture_diff_slices_deadline(
            Algorithm::Myers,
            &old,
            &new,
            Some(Instant::now()),
        );
        assert_eq!(apply_ops(&ops, &old, &new), new);
        let ops = capture_diff_slices_deadline(
            Algorithm::Patience,
            &old,
            &new,
            Some(Instant::now()),
        );
        assert_eq!(apply_ops(&ops, &old, &new), new);
    }

    #[test]
    fn generated_identify_distinct_equivalence() {
        let old: Vec<&str> = vec!["jade", "onyx", "opal", "ruby", "onyx"];
        let new: Vec<&str> = vec!["jade", "opal", "ruby", "topaz"];
        let ih = IdentifyDistinct::<u32>::new(&old[..], 0..old.len(), &new[..], 0..new.len());
        let via_tokens = capture_diff_deadline(
            Algorithm::Myers,
            ih.old_lookup(),
            ih.old_range(),
            ih.new_lookup(),
            ih.new_range(),
            None,
        );
        let direct = capture_diff_slices(Algorithm::Myers, &old, &new);
        assert_eq!(via_tokens, direct);
    }

    #[test]
    fn generated_manual_stack_equals_capture_diff() {
        let a: Vec<i64> = vec![9, 8, 7, 7, 6, 5, 5, 4];
        let b: Vec<i64> = vec![9, 8, 1, 7, 6, 2, 5, 4, 3];
        for alg in [Algorithm::Myers, Algorithm::Lcs, Algorithm::Patience] {
            let mut d = Compact::new(Replace::new(Capture::new()), &a[..], &b[..]);
            similar::algorithms::diff(alg, &mut d, &a[..], 0..a.len(), &b[..], 0..b.len())
                .unwrap();
            let manual = d.into_inner().into_inner().into_ops();
            assert_eq!(manual, capture_diff_slices(alg, &a, &b), "{:?}", alg);
        }
    }

    #[test]
    fn generated_utils_concat_covers_inputs() {
        use similar::utils::{diff_chars, diff_graphemes, diff_words};
        let old = "grüne Äpfel schmecken   säuerlich";
        let new = "grüne Birnen schmecken oft  süß";
        for changes in [
            diff_chars(Algorithm::Myers, old, new),
            diff_words(Algorithm::Myers, old, new),
            diff_graphemes(Algorithm::Myers, old, new),
        ] {
            let old_rebuilt: String = changes
                .iter()
                .filter(|(tag, _)| *tag != ChangeTag::Insert)
                .map(|(_, v)| *v)
                .collect();
            let new_rebuilt: String = changes
                .iter()
                .filter(|(tag, _)| *tag != ChangeTag::Delete)
                .map(|(_, v)| *v)
                .collect();
            assert_eq!(old_rebuilt, old);
            assert_eq!(new_rebuilt, new);
        }
    }

    #[test]
    fn generated_remapper_iter_slices_cover() {
        let old = "carbon silicon nitrogen";
        let new = "carbon helium nitrogen argon";
        let diff = TextDiff::from_words(old, new);
        let remapper = TextDiffRemapper::from_text_diff(&diff, old, new);
        let changes: Vec<_> = diff
            .ops()
            .iter()
            .flat_map(|op| remapper.iter_slices(op))
            .collect();
        let old_rebuilt: String = changes
            .iter()
            .filter(|(tag, _)| *tag != ChangeTag::Insert)
            .map(|(_, v)| *v)
            .collect();
        let new_rebuilt: String = changes
            .iter()
            .filter(|(tag, _)| *tag != ChangeTag::Delete)
            .map(|(_, v)| *v)
            .collect();
        assert_eq!(old_rebuilt, old);
        assert_eq!(new_rebuilt, new);
        // Remapped values are maximal connected slices of the originals.
        assert!(changes.contains(&(ChangeTag::Delete, "silicon")));
        assert!(changes.contains(&(ChangeTag::Insert, "helium")));
    }

    #[test]
    fn generated_workflow_line_diff_signs() {
        let diff = TextDiff::from_lines("1\n2\n3\n", "1\n99\n3\n");
        let mut output = String::new();
        for change in diff.iter_all_changes() {
            let sign = match change.tag() {
                ChangeTag::Delete => "-",
                ChangeTag::Insert => "+",
                ChangeTag::Equal => " ",
            };
            output.push_str(&format!("{}{}", sign, change));
        }
        assert_eq!(output, " 1\n-2\n+99\n 3\n");
    }
}
