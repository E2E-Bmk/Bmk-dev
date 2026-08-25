// Grouping across the capture layer, the free function, and TextDiff.

mod grouping {
    use similar::algorithms::{diff_slices, Capture, Replace};
    use similar::{group_diff_ops, Algorithm, DiffOp, DiffTag, TextDiff};

    #[test]
    fn test_capture_hook_grouping() {
        let rng = (1..100).collect::<Vec<i32>>();
        let mut rng_new = rng.clone();
        rng_new[10] = 1000;
        rng_new[13] = 1000;
        rng_new[16] = 1000;
        rng_new[34] = 1000;

        let mut d = Replace::new(Capture::new());
        diff_slices(Algorithm::Myers, &mut d, &rng, &rng_new).unwrap();
        let groups = d.into_inner().into_grouped_ops(3);

        assert_eq!(
            groups,
            vec![
                vec![
                    DiffOp::Equal { old_index: 7, new_index: 7, len: 3 },
                    DiffOp::Replace { old_index: 10, old_len: 1, new_index: 10, new_len: 1 },
                    DiffOp::Equal { old_index: 11, new_index: 11, len: 2 },
                    DiffOp::Replace { old_index: 13, old_len: 1, new_index: 13, new_len: 1 },
                    DiffOp::Equal { old_index: 14, new_index: 14, len: 2 },
                    DiffOp::Replace { old_index: 16, old_len: 1, new_index: 16, new_len: 1 },
                    DiffOp::Equal { old_index: 17, new_index: 17, len: 3 },
                ],
                vec![
                    DiffOp::Equal { old_index: 31, new_index: 31, len: 3 },
                    DiffOp::Replace { old_index: 34, old_len: 1, new_index: 34, new_len: 1 },
                    DiffOp::Equal { old_index: 35, new_index: 35, len: 3 },
                ],
            ]
        );
        // Interior equal runs longer than 2n split groups with n context
        // items on each side; boundary equals are trimmed to n.
        for group in &groups {
            assert_eq!(group.first().unwrap().tag(), DiffTag::Equal);
            assert_eq!(group.last().unwrap().tag(), DiffTag::Equal);
            assert!(group.first().unwrap().old_range().len() <= 3);
            assert!(group.last().unwrap().old_range().len() <= 3);
        }
    }

    #[test]
    fn generated_grouped_ops_matches_free_function() {
        let old = "q\nw\ne\nr\nt\ny\nu\ni\no\np\na\ns\nd\nf\ng\n";
        let new = "q\nw\nE\nr\nt\ny\nu\ni\no\np\na\ns\nD\nf\ng\n";
        let diff = TextDiff::from_lines(old, new);
        assert_eq!(
            diff.grouped_ops(2),
            group_diff_ops(diff.ops().to_vec(), 2)
        );
        assert_eq!(diff.grouped_ops(2).len(), 2);
    }

    #[test]
    fn generated_into_grouped_ops_matches_group_diff_ops() {
        let a: Vec<u32> = (0..30).collect();
        let mut b = a.clone();
        b[5] = 500;
        b[25] = 500;
        let mut d = Replace::new(Capture::new());
        diff_slices(Algorithm::Myers, &mut d, &a, &b).unwrap();
        let capture = d.into_inner();
        let ops = capture.ops().to_vec();
        let grouped = capture.into_grouped_ops(2);
        assert_eq!(grouped, group_diff_ops(ops, 2));
        assert_eq!(grouped.len(), 2);
    }
}
