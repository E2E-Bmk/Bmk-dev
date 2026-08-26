// Oracle atomic tests for the text diffing library reconstruction task.
#![cfg(test)]
#![allow(clippy::all)]

use similar::algorithms::{Capture, DiffHook, NoFinishHook, Replace};
use similar::udiff::UnifiedHunkHeader;
use similar::utils::TextDiffRemapper;
use similar::{
    capture_diff, capture_diff_slices, get_close_matches, get_diff_ratio, group_diff_ops,
    Algorithm, Change, ChangeTag, DiffOp, DiffTag, DiffableStr, DiffableStrRef, TextDiff,
    TextDiffConfig,
};

// ---------------------------------------------------------------------------
// Tokenization (spec: Text Diffing > Diffable strings)
// ---------------------------------------------------------------------------

#[test]
fn test_split_lines() {
    assert_eq!(
        DiffableStr::tokenize_lines("first\nsecond\rthird\r\nfourth\nlast"),
        vec!["first\n", "second\r", "third\r\n", "fourth\n", "last"]
    );
    assert_eq!(DiffableStr::tokenize_lines("\n\n"), vec!["\n", "\n"]);
    assert_eq!(DiffableStr::tokenize_lines("\n"), vec!["\n"]);
    assert!(DiffableStr::tokenize_lines("").is_empty());
}

#[test]
fn test_split_words() {
    assert_eq!(
        DiffableStr::tokenize_words("foo    bar baz\n\n  aha"),
        ["foo", "    ", "bar", " ", "baz", "\n\n  ", "aha"]
    );
}

#[test]
fn test_split_chars() {
    assert_eq!(
        DiffableStr::tokenize_chars("abcfö❄️"),
        vec!["a", "b", "c", "f", "ö", "❄", "\u{fe0f}"]
    );
}

#[test]
fn test_split_graphemes() {
    assert_eq!(
        DiffableStr::tokenize_graphemes("abcfö❄️"),
        vec!["a", "b", "c", "f", "ö", "❄️"]
    );
}

#[test]
fn generated_tokenize_unicode_words() {
    assert_eq!(
        DiffableStr::tokenize_unicode_words("ah(be) ce"),
        vec!["ah", "(", "be", ")", " ", "ce"]
    );
}

#[test]
fn generated_tokenize_lines_and_newlines() {
    assert_eq!(
        DiffableStr::tokenize_lines_and_newlines("a\n\r\nb"),
        vec!["a", "\n\r\n", "b"]
    );
}

#[test]
fn generated_diffable_str_inspection() {
    assert!(DiffableStr::ends_with_newline("tail\n"));
    assert!(DiffableStr::ends_with_newline("tail\r"));
    assert!(!DiffableStr::ends_with_newline("tail"));
    assert_eq!(DiffableStr::len("höhe"), 5);
    assert_eq!(DiffableStr::slice("planet", 1..4), "lan");
    assert_eq!(DiffableStr::as_str("ok"), Some("ok"));
    assert_eq!(DiffableStr::to_string_lossy("ok"), "ok");
    assert!(DiffableStr::is_empty(""));
    assert!(!DiffableStr::is_empty("x"));
    assert_eq!(DiffableStr::as_bytes("ab"), b"ab");
}

#[test]
fn generated_diffable_str_ref_owned() {
    let owned = String::from("alpha\nbeta\n");
    let new = String::from("alpha\ngamma\n");
    assert_eq!(owned.as_diffable_str(), "alpha\nbeta\n");
    let diff = TextDiff::from_lines(&owned, &new);
    let tags: Vec<_> = diff
        .iter_all_changes()
        .map(|c| (c.tag(), c.value()))
        .collect();
    assert_eq!(
        tags,
        vec![
            (ChangeTag::Equal, "alpha\n"),
            (ChangeTag::Delete, "beta\n"),
            (ChangeTag::Insert, "gamma\n"),
        ]
    );
}

// ---------------------------------------------------------------------------
// DiffOp semantics (spec: Captured Operation Streams)
// ---------------------------------------------------------------------------

#[test]
fn generated_diffop_tag_tuples() {
    let equal = DiffOp::Equal {
        old_index: 2,
        new_index: 5,
        len: 3,
    };
    assert_eq!(equal.tag(), DiffTag::Equal);
    assert_eq!(equal.old_range(), 2..5);
    assert_eq!(equal.new_range(), 5..8);
    assert_eq!(equal.as_tag_tuple(), (DiffTag::Equal, 2..5, 5..8));

    let delete = DiffOp::Delete {
        old_index: 4,
        old_len: 2,
        new_index: 7,
    };
    assert_eq!(delete.as_tag_tuple(), (DiffTag::Delete, 4..6, 7..7));

    let insert = DiffOp::Insert {
        old_index: 3,
        new_index: 1,
        new_len: 4,
    };
    assert_eq!(insert.as_tag_tuple(), (DiffTag::Insert, 3..3, 1..5));

    let replace = DiffOp::Replace {
        old_index: 1,
        old_len: 2,
        new_index: 2,
        new_len: 3,
    };
    assert_eq!(replace.as_tag_tuple(), (DiffTag::Replace, 1..3, 2..5));
}

#[test]
fn generated_diffop_iter_changes_replace_order() {
    let old = vec!["a", "b"];
    let new = vec!["x", "y", "z"];
    let op = DiffOp::Replace {
        old_index: 0,
        old_len: 2,
        new_index: 0,
        new_len: 3,
    };
    let changes: Vec<_> = op
        .iter_changes(&old, &new)
        .map(|c| (c.tag(), c.old_index(), c.new_index(), c.value()))
        .collect();
    assert_eq!(
        changes,
        vec![
            (ChangeTag::Delete, Some(0), None, "a"),
            (ChangeTag::Delete, Some(1), None, "b"),
            (ChangeTag::Insert, None, Some(0), "x"),
            (ChangeTag::Insert, None, Some(1), "y"),
            (ChangeTag::Insert, None, Some(2), "z"),
        ]
    );
}

#[test]
fn generated_diffop_iter_slices() {
    let old = vec![10, 20, 30];
    let new = vec![10, 40, 50];
    let equal = DiffOp::Equal {
        old_index: 0,
        new_index: 0,
        len: 1,
    };
    let got: Vec<_> = equal.iter_slices(&old[..], &new[..]).collect();
    assert_eq!(got, vec![(ChangeTag::Equal, &[10][..])]);

    let replace = DiffOp::Replace {
        old_index: 1,
        old_len: 2,
        new_index: 1,
        new_len: 2,
    };
    let got: Vec<_> = replace.iter_slices(&old[..], &new[..]).collect();
    assert_eq!(
        got,
        vec![
            (ChangeTag::Delete, &[20, 30][..]),
            (ChangeTag::Insert, &[40, 50][..]),
        ]
    );
}

#[derive(Default)]
struct CallRecorder(Vec<(&'static str, usize, usize, usize, usize)>);

impl DiffHook for CallRecorder {
    type Error = std::convert::Infallible;

    fn equal(&mut self, old_index: usize, new_index: usize, len: usize) -> Result<(), Self::Error> {
        self.0.push(("equal", old_index, new_index, len, 0));
        Ok(())
    }

    fn delete(
        &mut self,
        old_index: usize,
        old_len: usize,
        new_index: usize,
    ) -> Result<(), Self::Error> {
        self.0.push(("delete", old_index, old_len, new_index, 0));
        Ok(())
    }

    fn insert(
        &mut self,
        old_index: usize,
        new_index: usize,
        new_len: usize,
    ) -> Result<(), Self::Error> {
        self.0.push(("insert", old_index, new_index, new_len, 0));
        Ok(())
    }

    fn replace(
        &mut self,
        old_index: usize,
        old_len: usize,
        new_index: usize,
        new_len: usize,
    ) -> Result<(), Self::Error> {
        self.0
            .push(("replace", old_index, old_len, new_index, new_len));
        Ok(())
    }

    fn finish(&mut self) -> Result<(), Self::Error> {
        self.0.push(("finish", 0, 0, 0, 0));
        Ok(())
    }
}

#[test]
fn generated_diffop_apply_to_hook() {
    let mut rec = CallRecorder::default();
    DiffOp::Equal {
        old_index: 1,
        new_index: 2,
        len: 3,
    }
    .apply_to_hook(&mut rec)
    .unwrap();
    DiffOp::Replace {
        old_index: 4,
        old_len: 1,
        new_index: 5,
        new_len: 2,
    }
    .apply_to_hook(&mut rec)
    .unwrap();
    assert_eq!(
        rec.0,
        vec![("equal", 1, 2, 3, 0), ("replace", 4, 1, 5, 2)]
    );
}

#[test]
fn generated_default_replace_splits_into_delete_insert() {
    // A hook that keeps the trait's default `replace` must observe
    // delete followed by insert.
    struct NoReplace(Vec<(&'static str, usize, usize, usize)>);
    impl DiffHook for NoReplace {
        type Error = std::convert::Infallible;
        fn delete(&mut self, oi: usize, ol: usize, ni: usize) -> Result<(), Self::Error> {
            self.0.push(("delete", oi, ol, ni));
            Ok(())
        }
        fn insert(&mut self, oi: usize, ni: usize, nl: usize) -> Result<(), Self::Error> {
            self.0.push(("insert", oi, ni, nl));
            Ok(())
        }
    }
    let mut h = NoReplace(Vec::new());
    DiffOp::Replace {
        old_index: 2,
        old_len: 1,
        new_index: 2,
        new_len: 2,
    }
    .apply_to_hook(&mut h)
    .unwrap();
    assert_eq!(h.0, vec![("delete", 2, 1, 2), ("insert", 2, 2, 2)]);
}

#[test]
fn test_non_string_iter_change() {
    let old = vec![1, 2, 3];
    let new = vec![1, 2, 4];
    let ops = capture_diff_slices(Algorithm::Myers, &old, &new);
    let changes: Vec<_> = ops
        .iter()
        .flat_map(|x| x.iter_changes(&old, &new))
        .map(|x| (x.tag(), x.value()))
        .collect();

    assert_eq!(
        changes,
        vec![
            (ChangeTag::Equal, 1),
            (ChangeTag::Equal, 2),
            (ChangeTag::Delete, 3),
            (ChangeTag::Insert, 4),
        ]
    );
}

// ---------------------------------------------------------------------------
// Algorithm entry points (spec: Diff Algorithms and the Hook Protocol)
// ---------------------------------------------------------------------------

#[test]
fn test_myers_diff_ops() {
    let a: &[usize] = &[0, 1, 2, 3, 4];
    let b: &[usize] = &[0, 1, 2, 9, 4];
    let mut d = Replace::new(Capture::new());
    similar::algorithms::myers::diff(&mut d, a, 0..a.len(), b, 0..b.len()).unwrap();
    assert_eq!(
        d.into_inner().into_ops(),
        vec![
            DiffOp::Equal { old_index: 0, new_index: 0, len: 3 },
            DiffOp::Replace { old_index: 3, old_len: 1, new_index: 3, new_len: 1 },
            DiffOp::Equal { old_index: 4, new_index: 4, len: 1 },
        ]
    );
}

#[test]
fn test_myers_contiguous_ops() {
    let a: &[usize] = &[0, 1, 2, 3, 4, 4, 4, 5];
    let b: &[usize] = &[0, 1, 2, 8, 9, 4, 4, 7];
    let mut d = Replace::new(Capture::new());
    similar::algorithms::myers::diff(&mut d, a, 0..a.len(), b, 0..b.len()).unwrap();
    assert_eq!(
        d.into_inner().into_ops(),
        vec![
            DiffOp::Equal { old_index: 0, new_index: 0, len: 3 },
            DiffOp::Replace { old_index: 3, old_len: 1, new_index: 3, new_len: 2 },
            DiffOp::Equal { old_index: 4, new_index: 5, len: 2 },
            DiffOp::Replace { old_index: 6, old_len: 2, new_index: 7, new_len: 1 },
        ]
    );
}

#[test]
fn test_myers_raw_capture_minimal_script() {
    // Myers must produce a shortest edit script: here one deletion (the 3)
    // and two insertions (8, 9), reported through ordered hook callbacks.
    let a: &[usize] = &[0, 1, 3, 4, 5];
    let b: &[usize] = &[0, 1, 4, 5, 8, 9];
    let mut d = Capture::new();
    similar::algorithms::myers::diff(&mut d, a, 0..a.len(), b, 0..b.len()).unwrap();
    let ops = d.into_ops();
    let mut deleted = 0usize;
    let mut inserted = 0usize;
    let mut rebuilt: Vec<usize> = Vec::new();
    for op in &ops {
        let (tag, old_range, new_range) = op.as_tag_tuple();
        match tag {
            DiffTag::Equal => {
                assert_eq!(&a[old_range.clone()], &b[new_range.clone()]);
                rebuilt.extend_from_slice(&a[old_range]);
            }
            DiffTag::Delete => deleted += old_range.len(),
            DiffTag::Insert => {
                inserted += new_range.len();
                rebuilt.extend_from_slice(&b[new_range]);
            }
            DiffTag::Replace => {
                deleted += old_range.len();
                inserted += new_range.len();
                rebuilt.extend_from_slice(&b[new_range]);
            }
        }
    }
    assert_eq!(rebuilt, b);
    assert_eq!(deleted, 1);
    assert_eq!(inserted, 2);
}

#[test]
fn test_lcs_diff_ops() {
    let a: &[usize] = &[0, 1, 2, 3, 4];
    let b: &[usize] = &[0, 1, 2, 9, 4];
    let mut d = Replace::new(Capture::new());
    similar::algorithms::lcs::diff(&mut d, a, 0..a.len(), b, 0..b.len()).unwrap();
    assert_eq!(
        d.into_inner().into_ops(),
        vec![
            DiffOp::Equal { old_index: 0, new_index: 0, len: 3 },
            DiffOp::Replace { old_index: 3, old_len: 1, new_index: 3, new_len: 1 },
            DiffOp::Equal { old_index: 4, new_index: 4, len: 1 },
        ]
    );
}

#[test]
fn test_lcs_contiguous_ops() {
    let a: &[usize] = &[0, 1, 2, 3, 4, 4, 4, 5];
    let b: &[usize] = &[0, 1, 2, 8, 9, 4, 4, 7];
    let mut d = Replace::new(Capture::new());
    similar::algorithms::lcs::diff(&mut d, a, 0..a.len(), b, 0..b.len()).unwrap();
    assert_eq!(
        d.into_inner().into_ops(),
        vec![
            DiffOp::Equal { old_index: 0, new_index: 0, len: 3 },
            DiffOp::Replace { old_index: 3, old_len: 2, new_index: 3, new_len: 2 },
            DiffOp::Equal { old_index: 5, new_index: 5, len: 2 },
            DiffOp::Replace { old_index: 7, old_len: 1, new_index: 7, new_len: 1 },
        ]
    );
}

#[test]
fn test_lcs_same_single_equal() {
    // Equal inputs through the pinned capture pipeline produce a single
    // Equal op covering both sequences.
    let a = vec![0, 1, 2, 3, 4, 4, 4, 5];
    assert_eq!(
        capture_diff_slices(Algorithm::Lcs, &a, &a),
        vec![DiffOp::Equal { old_index: 0, new_index: 0, len: 8 }]
    );
}

#[test]
fn test_lcs_bad_range_regression() {
    let mut d = Capture::new();
    similar::algorithms::lcs::diff(&mut d, &[0], 0..1, &[0, 0], 0..2).unwrap();
    assert_eq!(
        d.into_ops(),
        vec![
            DiffOp::Equal { old_index: 0, new_index: 0, len: 1 },
            DiffOp::Insert { old_index: 1, new_index: 1, new_len: 1 },
        ]
    );
}

#[test]
fn test_patience_diff_ops() {
    let a: &[usize] = &[11, 1, 2, 2, 3, 4, 4, 4, 5, 47, 19];
    let b: &[usize] = &[10, 1, 2, 2, 8, 9, 4, 4, 7, 47, 18];
    let mut d = Replace::new(Capture::new());
    similar::algorithms::patience::diff(&mut d, a, 0..a.len(), b, 0..b.len()).unwrap();
    assert_eq!(
        d.into_inner().into_ops(),
        vec![
            DiffOp::Replace { old_index: 0, old_len: 1, new_index: 0, new_len: 1 },
            DiffOp::Equal { old_index: 1, new_index: 1, len: 3 },
            DiffOp::Replace { old_index: 4, old_len: 1, new_index: 4, new_len: 2 },
            DiffOp::Equal { old_index: 5, new_index: 6, len: 2 },
            DiffOp::Replace { old_index: 7, old_len: 2, new_index: 8, new_len: 1 },
            DiffOp::Equal { old_index: 9, new_index: 9, len: 1 },
            DiffOp::Replace { old_index: 10, old_len: 1, new_index: 10, new_len: 1 },
        ]
    );
}

#[test]
fn test_patience_shrink_ops() {
    let a: &[usize] = &[1, 2, 3, 4];
    let b: &[usize] = &[1, 2, 3];
    let mut d = Replace::new(Capture::new());
    similar::algorithms::patience::diff(&mut d, a, 0..a.len(), b, 0..b.len()).unwrap();
    assert_eq!(
        d.into_inner().into_ops(),
        vec![
            DiffOp::Equal { old_index: 0, new_index: 0, len: 3 },
            DiffOp::Delete { old_index: 3, old_len: 1, new_index: 3 },
        ]
    );
}

struct HasRunFinish(bool);

impl DiffHook for HasRunFinish {
    type Error = ();
    fn finish(&mut self) -> Result<(), Self::Error> {
        self.0 = true;
        Ok(())
    }
}

#[test]
fn test_myers_finish_called() {
    let mut d = HasRunFinish(false);
    let slice = &[1, 2];
    let slice2 = &[1, 2, 3];
    similar::algorithms::myers::diff(&mut d, slice, 0..slice.len(), slice2, 0..slice2.len())
        .unwrap();
    assert!(d.0);

    let mut d = HasRunFinish(false);
    let slice = &[1, 2];
    similar::algorithms::myers::diff(&mut d, slice, 0..slice.len(), slice, 0..slice.len())
        .unwrap();
    assert!(d.0);

    let mut d = HasRunFinish(false);
    let slice: &[u8] = &[];
    similar::algorithms::myers::diff(&mut d, slice, 0..slice.len(), slice, 0..slice.len())
        .unwrap();
    assert!(d.0);
}

#[test]
fn test_lcs_finish_called() {
    let mut d = HasRunFinish(false);
    let slice = &[1, 2];
    let slice2 = &[1, 2, 3];
    similar::algorithms::lcs::diff(&mut d, slice, 0..slice.len(), slice2, 0..slice2.len())
        .unwrap();
    assert!(d.0);

    let mut d = HasRunFinish(false);
    let slice: &[u8] = &[];
    similar::algorithms::lcs::diff(&mut d, slice, 0..slice.len(), slice, 0..slice.len()).unwrap();
    assert!(d.0);
}

#[test]
fn test_patience_finish_called() {
    let mut d = HasRunFinish(false);
    let slice = &[1, 2];
    let slice2 = &[1, 2, 3];
    similar::algorithms::patience::diff(&mut d, slice, 0..slice.len(), slice2, 0..slice2.len())
        .unwrap();
    assert!(d.0);

    let mut d = HasRunFinish(false);
    let slice: &[u8] = &[];
    similar::algorithms::patience::diff(&mut d, slice, 0..slice.len(), slice, 0..slice.len())
        .unwrap();
    assert!(d.0);
}

#[test]
fn test_replace_merges_delete_insert() {
    let a: &[usize] = &[0, 1, 2, 3, 4];
    let b: &[usize] = &[0, 1, 2, 7, 8, 9];
    let mut d = Replace::new(Capture::new());
    similar::algorithms::diff_slices(Algorithm::Myers, &mut d, a, b).unwrap();
    assert_eq!(
        d.into_inner().into_ops(),
        vec![
            DiffOp::Equal { old_index: 0, new_index: 0, len: 3 },
            DiffOp::Replace { old_index: 3, old_len: 2, new_index: 3, new_len: 3 },
        ]
    );
}

#[test]
fn test_replace_merges_on_line_slices() {
    let a: &[&str] = &[
        ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n",
        "a\n",
        "b\n",
        "c\n",
        "================================\n",
        "d\n",
        "e\n",
        "f\n",
        "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<\n",
    ];
    let b: &[&str] = &[
        ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n",
        "x\n",
        "b\n",
        "c\n",
        "================================\n",
        "y\n",
        "e\n",
        "f\n",
        "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<\n",
    ];
    let mut d = Replace::new(Capture::new());
    similar::algorithms::diff_slices(Algorithm::Myers, &mut d, a, b).unwrap();
    assert_eq!(
        d.into_inner().into_ops(),
        vec![
            DiffOp::Equal { old_index: 0, new_index: 0, len: 1 },
            DiffOp::Replace { old_index: 1, old_len: 1, new_index: 1, new_len: 1 },
            DiffOp::Equal { old_index: 2, new_index: 2, len: 3 },
            DiffOp::Replace { old_index: 5, old_len: 1, new_index: 5, new_len: 1 },
            DiffOp::Equal { old_index: 6, new_index: 6, len: 3 },
        ]
    );
}

#[test]
fn generated_nofinish_hook_swallows_finish() {
    let inner = HasRunFinish(false);
    let mut wrapped = NoFinishHook::new(inner);
    similar::algorithms::diff_slices(Algorithm::Myers, &mut wrapped, &[1, 5], &[1, 6]).unwrap();
    let inner = wrapped.into_inner();
    assert!(!inner.0);
}

#[test]
fn generated_hook_error_propagates() {
    struct FailOnDelete;
    impl DiffHook for FailOnDelete {
        type Error = &'static str;
        fn delete(&mut self, _oi: usize, _ol: usize, _ni: usize) -> Result<(), Self::Error> {
            Err("delete rejected")
        }
    }
    let mut d = FailOnDelete;
    let res = similar::algorithms::diff_slices(Algorithm::Myers, &mut d, &[4, 8, 9], &[4, 9]);
    assert_eq!(res, Err("delete rejected"));
}

// ---------------------------------------------------------------------------
// One-call capture (spec: Captured Operation Streams > One-call capture)
// ---------------------------------------------------------------------------

#[test]
fn generated_capture_diff_slices_doc() {
    let a = vec![1, 2, 3, 4, 5];
    let b = vec![1, 2, 3, 4, 7];
    let ops = capture_diff_slices(Algorithm::Myers, &a, &b);
    assert_eq!(
        ops,
        vec![
            DiffOp::Equal { old_index: 0, new_index: 0, len: 4 },
            DiffOp::Replace { old_index: 4, old_len: 1, new_index: 4, new_len: 1 },
        ]
    );
}

#[test]
fn generated_capture_empty_and_equal() {
    let empty: Vec<u32> = vec![];
    assert_eq!(capture_diff_slices(Algorithm::Myers, &empty, &empty), vec![]);
    let same = vec![7, 7, 9];
    assert_eq!(
        capture_diff_slices(Algorithm::Lcs, &same, &same),
        vec![DiffOp::Equal { old_index: 0, new_index: 0, len: 3 }]
    );
}

#[test]
fn generated_capture_diff_matches_slices_shortcut() {
    let a = vec!["ein", "zwei", "drei", "vier"];
    let b = vec!["ein", "drei", "vier", "acht"];
    let via_ranges = capture_diff(Algorithm::Patience, &a[..], 0..a.len(), &b[..], 0..b.len());
    let via_slices = capture_diff_slices(Algorithm::Patience, &a, &b);
    assert_eq!(via_ranges, via_slices);
    assert!(!via_slices.is_empty());
}

// ---------------------------------------------------------------------------
// Grouping and similarity (spec: Grouping and Similarity)
// ---------------------------------------------------------------------------

#[test]
fn generated_group_diff_ops_small() {
    let old: Vec<i32> = vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15];
    let mut new = old.clone();
    new[1] = 99;
    new[13] = 77;
    let ops = capture_diff_slices(Algorithm::Myers, &old, &new);
    let grouped = group_diff_ops(ops, 2);
    assert_eq!(
        grouped,
        vec![
            vec![
                DiffOp::Equal { old_index: 0, new_index: 0, len: 1 },
                DiffOp::Replace { old_index: 1, old_len: 1, new_index: 1, new_len: 1 },
                DiffOp::Equal { old_index: 2, new_index: 2, len: 2 },
            ],
            vec![
                DiffOp::Equal { old_index: 11, new_index: 11, len: 2 },
                DiffOp::Replace { old_index: 13, old_len: 1, new_index: 13, new_len: 1 },
                DiffOp::Equal { old_index: 14, new_index: 14, len: 1 },
            ],
        ]
    );
}

#[test]
fn generated_group_diff_ops_empty_and_all_equal() {
    assert_eq!(group_diff_ops(vec![], 3), Vec::<Vec<DiffOp>>::new());
    let only_equal = vec![DiffOp::Equal { old_index: 0, new_index: 0, len: 40 }];
    assert_eq!(group_diff_ops(only_equal, 3), Vec::<Vec<DiffOp>>::new());
}

#[test]
fn test_ratio() {
    let diff = TextDiff::from_chars("abcd", "bcde");
    assert_eq!(diff.ratio(), 0.75);
    let diff = TextDiff::from_chars("", "");
    assert_eq!(diff.ratio(), 1.0);
}

#[test]
fn generated_get_diff_ratio_direct() {
    let ops = vec![
        DiffOp::Equal { old_index: 0, new_index: 0, len: 3 },
        DiffOp::Replace { old_index: 3, old_len: 2, new_index: 3, new_len: 1 },
    ];
    assert_eq!(get_diff_ratio(&ops, 5, 4), 2.0 * 3.0 / 9.0);
    assert_eq!(get_diff_ratio(&[], 0, 0), 1.0);
}

#[test]
fn test_get_close_matches() {
    let matches = get_close_matches("appel", &["ape", "apple", "peach", "puppy"][..], 3, 0.6);
    assert_eq!(matches, vec!["apple", "ape"]);
    let matches = get_close_matches(
        "hulo",
        &[
            "hi", "hulu", "hali", "hoho", "amaz", "zulo", "blah", "hopp", "uulo", "aulo",
        ][..],
        5,
        0.7,
    );
    assert_eq!(matches, vec!["aulo", "hulu", "uulo", "zulo"]);
}

#[test]
fn generated_close_matches_below_cutoff_empty() {
    let matches = get_close_matches("qqqq", &["aaaa", "bbbb"][..], 5, 0.9);
    assert!(matches.is_empty());
}

// ---------------------------------------------------------------------------
// Text diffing (spec: Text Diffing)
// ---------------------------------------------------------------------------

#[test]
fn generated_diff_lines_doc() {
    let diff = TextDiff::configure().diff_lines("a\nb\nc", "a\nb\nC");
    let changes: Vec<_> = diff
        .iter_all_changes()
        .map(|x| (x.tag(), x.value()))
        .collect();
    assert_eq!(
        changes,
        vec![
            (ChangeTag::Equal, "a\n"),
            (ChangeTag::Equal, "b\n"),
            (ChangeTag::Delete, "c"),
            (ChangeTag::Insert, "C"),
        ]
    );
}

#[test]
fn test_captured_ops() {
    let diff = TextDiff::from_lines(
        "Hello World\nsome stuff here\nsome more stuff here\n",
        "Hello World\nsome amazing stuff here\nsome more stuff here\n",
    );
    assert_eq!(
        diff.ops(),
        &[
            DiffOp::Equal { old_index: 0, new_index: 0, len: 1 },
            DiffOp::Replace { old_index: 1, old_len: 1, new_index: 1, new_len: 1 },
            DiffOp::Equal { old_index: 2, new_index: 2, len: 1 },
        ]
    );
}

#[test]
fn test_char_diff() {
    let diff = TextDiff::from_chars("Hello World", "Hallo Welt");
    assert_eq!(
        diff.ops(),
        &[
            DiffOp::Equal { old_index: 0, new_index: 0, len: 1 },
            DiffOp::Replace { old_index: 1, old_len: 1, new_index: 1, new_len: 1 },
            DiffOp::Equal { old_index: 2, new_index: 2, len: 5 },
            DiffOp::Replace { old_index: 7, old_len: 2, new_index: 7, new_len: 1 },
            DiffOp::Equal { old_index: 9, new_index: 8, len: 1 },
            DiffOp::Replace { old_index: 10, old_len: 1, new_index: 9, new_len: 1 },
        ]
    );
}

#[test]
fn test_virtual_newlines() {
    let diff = TextDiff::from_lines("a\nb", "a\nc\n");
    assert!(diff.newline_terminated());
    let changes: Vec<_> = diff
        .ops()
        .iter()
        .flat_map(|op| diff.iter_changes(op))
        .map(|c| (c.tag(), c.old_index(), c.new_index(), c.value(), c.missing_newline()))
        .collect();
    assert_eq!(
        changes,
        vec![
            (ChangeTag::Equal, Some(0), Some(0), "a\n", false),
            (ChangeTag::Delete, Some(1), None, "b", true),
            (ChangeTag::Insert, None, Some(1), "c\n", false),
        ]
    );
}

#[test]
fn test_lifetimes_on_iter() {
    fn diff_lines<'x, T>(old: &'x T, new: &'x T) -> Vec<Change<&'x T::Output>>
    where
        T: DiffableStrRef + ?Sized,
    {
        TextDiff::from_lines(old, new).iter_all_changes().collect()
    }

    let a = "1\n2\n3\n".to_string();
    let b = "1\n99\n3\n".to_string();
    let changes: Vec<_> = diff_lines(&a, &b)
        .into_iter()
        .map(|c| (c.tag(), c.old_index(), c.new_index(), c.value()))
        .collect();
    assert_eq!(
        changes,
        vec![
            (ChangeTag::Equal, Some(0), Some(0), "1\n"),
            (ChangeTag::Delete, Some(1), None, "2\n"),
            (ChangeTag::Insert, None, Some(1), "99\n"),
            (ChangeTag::Equal, Some(2), Some(2), "3\n"),
        ]
    );
}

#[test]
fn generated_from_words_changes() {
    let diff = TextDiff::from_words("foo bar baz", "foo BAR baz");
    let changes: Vec<_> = diff
        .iter_all_changes()
        .map(|x| (x.tag(), x.value()))
        .collect();
    assert_eq!(
        changes,
        vec![
            (ChangeTag::Equal, "foo"),
            (ChangeTag::Equal, " "),
            (ChangeTag::Delete, "bar"),
            (ChangeTag::Insert, "BAR"),
            (ChangeTag::Equal, " "),
            (ChangeTag::Equal, "baz"),
        ]
    );
}

#[test]
fn generated_from_graphemes_changes() {
    let diff = TextDiff::from_graphemes("💩🇦🇹🦠", "💩🇦🇱❄️");
    let changes: Vec<_> = diff
        .iter_all_changes()
        .map(|x| (x.tag(), x.value()))
        .collect();
    assert_eq!(
        changes,
        vec![
            (ChangeTag::Equal, "💩"),
            (ChangeTag::Delete, "🇦🇹"),
            (ChangeTag::Delete, "🦠"),
            (ChangeTag::Insert, "🇦🇱"),
            (ChangeTag::Insert, "❄️"),
        ]
    );
}

#[test]
fn generated_from_unicode_words_changes() {
    let diff = TextDiff::from_unicode_words("ah(be)ce", "ah(ah)ce");
    let changes: Vec<_> = diff
        .iter_all_changes()
        .map(|x| (x.tag(), x.value()))
        .collect();
    assert_eq!(
        changes,
        vec![
            (ChangeTag::Equal, "ah"),
            (ChangeTag::Equal, "("),
            (ChangeTag::Delete, "be"),
            (ChangeTag::Insert, "ah"),
            (ChangeTag::Equal, ")"),
            (ChangeTag::Equal, "ce"),
        ]
    );
}

#[test]
fn generated_from_slices_changes() {
    let old = &["foo", "bar", "baz"];
    let new = &["foo", "BAR", "baz"];
    let diff = TextDiff::from_slices(old, new);
    let changes: Vec<_> = diff
        .iter_all_changes()
        .map(|x| (x.tag(), x.value()))
        .collect();
    assert_eq!(
        changes,
        vec![
            (ChangeTag::Equal, "foo"),
            (ChangeTag::Delete, "bar"),
            (ChangeTag::Insert, "BAR"),
            (ChangeTag::Equal, "baz"),
        ]
    );
}

#[test]
fn generated_newline_terminated_flags() {
    assert!(TextDiff::from_lines("a\nb\n", "a\nc\n").newline_terminated());
    assert!(!TextDiff::from_words("a b", "a c").newline_terminated());
    assert!(!TextDiff::from_chars("ab", "ac").newline_terminated());
    let overridden = TextDiff::configure()
        .newline_terminated(true)
        .diff_words("a b", "a c");
    assert!(overridden.newline_terminated());
    let overridden = TextDiff::configure()
        .newline_terminated(false)
        .diff_lines("a\nb\n", "a\nc\n");
    assert!(!overridden.newline_terminated());
}

#[test]
fn generated_algorithm_selection() {
    assert_eq!(Algorithm::default(), Algorithm::Myers);
    let diff = TextDiff::from_lines("x\n", "y\n");
    assert_eq!(diff.algorithm(), Algorithm::Myers);
    let diff = TextDiff::configure()
        .algorithm(Algorithm::Lcs)
        .diff_lines("x\n", "y\n");
    assert_eq!(diff.algorithm(), Algorithm::Lcs);
    let cfg = TextDiffConfig::default();
    let diff = cfg.diff_lines("x\n", "y\n");
    assert_eq!(diff.algorithm(), Algorithm::Myers);
}

#[test]
fn generated_old_new_slices_expose_tokens() {
    let diff = TextDiff::from_lines("ab\ncd\n", "ab\nzz\n");
    assert_eq!(diff.old_slices(), &["ab\n", "cd\n"]);
    assert_eq!(diff.new_slices(), &["ab\n", "zz\n"]);
}

#[test]
fn generated_change_tag_display() {
    assert_eq!(format!("{}", ChangeTag::Equal), " ");
    assert_eq!(format!("{}", ChangeTag::Delete), "-");
    assert_eq!(format!("{}", ChangeTag::Insert), "+");
}

#[test]
fn generated_change_accessors_and_display() {
    let diff = TextDiff::from_lines("one\ntwo", "one\nfive");
    let changes: Vec<_> = diff.iter_all_changes().collect();
    assert_eq!(changes.len(), 3);
    let del = changes[1];
    assert_eq!(del.tag(), ChangeTag::Delete);
    assert_eq!(del.old_index(), Some(1));
    assert_eq!(del.new_index(), None);
    assert_eq!(del.value(), "two");
    assert_eq!(*del.value_ref(), "two");
    assert_eq!(del.as_str(), Some("two"));
    assert_eq!(del.to_string_lossy(), "two");
    assert!(del.missing_newline());
    // Display appends the virtual newline for values missing one.
    assert_eq!(format!("{}", del), "two\n");
    let eq = changes[0];
    assert!(!eq.missing_newline());
    assert_eq!(format!("{}", eq), "one\n");
}

// ---------------------------------------------------------------------------
// Unified diff pieces (spec: Unified Diff Output)
// ---------------------------------------------------------------------------

#[test]
fn generated_hunk_header_formats() {
    let h = UnifiedHunkHeader::new(&[DiffOp::Delete { old_index: 1, old_len: 1, new_index: 1 }]);
    assert_eq!(h.to_string(), "@@ -2 +1,0 @@");
    let h = UnifiedHunkHeader::new(&[DiffOp::Insert { old_index: 2, new_index: 2, new_len: 2 }]);
    assert_eq!(h.to_string(), "@@ -2,0 +3,2 @@");
    let h = UnifiedHunkHeader::new(&[DiffOp::Equal { old_index: 0, new_index: 0, len: 1 }]);
    assert_eq!(h.to_string(), "@@ -1 +1 @@");
    let h = UnifiedHunkHeader::new(&[
        DiffOp::Equal { old_index: 3, new_index: 3, len: 2 },
        DiffOp::Replace { old_index: 5, old_len: 2, new_index: 5, new_len: 3 },
    ]);
    assert_eq!(h.to_string(), "@@ -4,4 +4,5 @@");
}

#[test]
fn test_empty_unified_diff() {
    let diff = TextDiff::from_lines("abc", "abc");
    assert_eq!(diff.unified_diff().header("a.txt", "b.txt").to_string(), "");
}

// ---------------------------------------------------------------------------
// Utils: one-call diffs and remapping (spec: Convenience Diff Functions)
// ---------------------------------------------------------------------------

#[test]
fn test_remapper() {
    let a = "foo bar baz";
    let words = a.tokenize_words();
    let remap = TextDiffRemapper::new(&words, &words, a, a);
    assert_eq!(remap.slice_old(0..3), Some("foo bar"));
    assert_eq!(remap.slice_old(1..3), Some(" bar"));
    assert_eq!(remap.slice_old(0..1), Some("foo"));
    assert_eq!(remap.slice_old(0..5), Some("foo bar baz"));
    assert_eq!(remap.slice_old(0..6), None);
    assert_eq!(remap.slice_new(0..5), Some("foo bar baz"));
    assert_eq!(remap.slice_new(2..6), None);
}

#[test]
fn generated_utils_diff_chars() {
    use similar::utils::diff_chars;
    assert_eq!(
        diff_chars(Algorithm::Myers, "foobarbaz", "fooBARbaz"),
        vec![
            (ChangeTag::Equal, "foo"),
            (ChangeTag::Delete, "bar"),
            (ChangeTag::Insert, "BAR"),
            (ChangeTag::Equal, "baz"),
        ]
    );
}

#[test]
fn generated_utils_diff_words_values() {
    use similar::utils::diff_words;
    assert_eq!(
        diff_words(Algorithm::Myers, "yo! foo bar baz", "yo! foo bor baz"),
        vec![
            (ChangeTag::Equal, "yo! foo "),
            (ChangeTag::Delete, "bar"),
            (ChangeTag::Insert, "bor"),
            (ChangeTag::Equal, " baz"),
        ]
    );
}

#[test]
fn generated_utils_diff_lines() {
    use similar::utils::diff_lines;
    assert_eq!(
        diff_lines(Algorithm::Myers, "foo\nbar\nbaz\nblah", "foo\nbar\nbaz\nblurgh"),
        vec![
            (ChangeTag::Equal, "foo\n"),
            (ChangeTag::Equal, "bar\n"),
            (ChangeTag::Equal, "baz\n"),
            (ChangeTag::Delete, "blah"),
            (ChangeTag::Insert, "blurgh"),
        ]
    );
}

#[test]
fn generated_utils_diff_unicode_words() {
    use similar::utils::diff_unicode_words;
    let old = "The quick (\"brown\") fox can't jump 32.3 feet, right?";
    let new = "The quick (\"brown\") fox can't jump 9.84 meters, right?";
    assert_eq!(
        diff_unicode_words(Algorithm::Myers, old, new),
        vec![
            (ChangeTag::Equal, "The quick (\"brown\") fox can\'t jump "),
            (ChangeTag::Delete, "32.3"),
            (ChangeTag::Insert, "9.84"),
            (ChangeTag::Equal, " "),
            (ChangeTag::Delete, "feet"),
            (ChangeTag::Insert, "meters"),
            (ChangeTag::Equal, ", right?"),
        ]
    );
}

#[test]
fn generated_utils_diff_graphemes() {
    use similar::utils::diff_graphemes;
    let old = "The flag of Austria is 🇦🇹";
    let new = "The flag of Albania is 🇦🇱";
    assert_eq!(
        diff_graphemes(Algorithm::Myers, old, new),
        vec![
            (ChangeTag::Equal, "The flag of A"),
            (ChangeTag::Delete, "ustr"),
            (ChangeTag::Insert, "lban"),
            (ChangeTag::Equal, "ia is "),
            (ChangeTag::Delete, "🇦🇹"),
            (ChangeTag::Insert, "🇦🇱"),
        ]
    );
}

#[test]
fn generated_utils_diff_slices() {
    use similar::utils::diff_slices;
    let old = "foo\nbar\nbaz".lines().collect::<Vec<_>>();
    let new = "foo\nbar\nBAZ".lines().collect::<Vec<_>>();
    assert_eq!(
        diff_slices(Algorithm::Myers, &old, &new),
        vec![
            (ChangeTag::Equal, &["foo", "bar"][..]),
            (ChangeTag::Delete, &["baz"][..]),
            (ChangeTag::Insert, &["BAZ"][..]),
        ]
    );
}

// ---------------------------------------------------------------------------
// Inline changes, single-op shapes (spec: Inline Change Emphasis)
// ---------------------------------------------------------------------------

#[test]
fn generated_inline_equal_single_unemphasized() {
    let diff = TextDiff::from_lines("same\nline\n", "same\nline\n");
    let op = diff.ops()[0];
    let inline: Vec<_> = diff.iter_inline_changes(&op).collect();
    assert_eq!(inline.len(), 2);
    for (ic, expected) in inline.iter().zip(["same\n", "line\n"]) {
        assert_eq!(ic.tag(), ChangeTag::Equal);
        assert_eq!(ic.values(), &[(false, expected)]);
        assert!(!ic.missing_newline());
    }
}

#[test]
fn generated_inline_from_change() {
    use similar::InlineChange;
    let diff = TextDiff::from_lines("aaa\nbbb", "aaa\nccc");
    let change = diff.iter_all_changes().last().unwrap();
    let inline: InlineChange<str> = change.into();
    assert_eq!(inline.tag(), ChangeTag::Insert);
    assert_eq!(inline.new_index(), Some(1));
    assert_eq!(inline.values(), &[(false, "ccc")]);
    assert!(inline.missing_newline());
    let lossy: Vec<_> = inline.iter_strings_lossy().collect();
    assert_eq!(lossy.len(), 1);
    assert_eq!(lossy[0].0, false);
    assert_eq!(lossy[0].1, "ccc");
    // Display of an unemphasized change carries no markers and adds the
    // virtual trailing newline.
    assert_eq!(inline.to_string(), "ccc\n");
}
