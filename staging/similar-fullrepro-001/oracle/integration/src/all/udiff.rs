// Unified diff rendering across TextDiff, grouping, and formatting.

mod udiff {
    use similar::udiff::unified_diff;
    use similar::{Algorithm, TextDiff, TextDiffConfig};

    #[test]
    fn test_unified_diff_simple() {
        let diff = TextDiff::from_lines(
            "Hello World\nsome stuff here\nsome more stuff here\n",
            "Hello World\nsome amazing stuff here\nsome more stuff here\n",
        );
        assert!(diff.newline_terminated());
        assert_eq!(
            diff.unified_diff()
                .context_radius(3)
                .header("old", "new")
                .to_string(),
            "--- old\n+++ new\n@@ -1,3 +1,3 @@\n Hello World\n-some stuff here\n+some amazing stuff here\n some more stuff here\n"
        );
    }

    #[test]
    fn test_unified_diff_two_hunks() {
        let diff = TextDiff::from_lines(
            "a\nb\nc\nd\ne\nf\ng\nh\ni\nj\nk\nl\nm\nn\no\np\nq\nr\ns\nt\nu\nv\nw\nx\ny\nz\nA\nB\nC\nD\nE\nF\nG\nH\nI\nJ\nK\nL\nM\nN\nO\nP\nQ\nR\nS\nT\nU\nV\nW\nX\nY\nZ",
            "a\nb\nc\nd\ne\nf\ng\nh\ni\nj\nk\nl\nm\nn\no\np\nq\nr\nS\nt\nu\nv\nw\nx\ny\nz\nA\nB\nC\nD\nE\nF\nG\nH\nI\nJ\nK\nL\nM\nN\no\nP\nQ\nR\nS\nT\nU\nV\nW\nX\nY\nZ",
        );
        assert_eq!(
            diff.unified_diff().header("a.txt", "b.txt").to_string(),
            "--- a.txt\n+++ b.txt\n@@ -16,7 +16,7 @@\n p\n q\n r\n-s\n+S\n t\n u\n v\n@@ -38,7 +38,7 @@\n L\n M\n N\n-O\n+o\n P\n Q\n R\n"
        );
    }

    #[test]
    fn test_unified_diff_newline_hint() {
        let diff = TextDiff::from_lines("a\n", "b");
        assert_eq!(
            diff.unified_diff().header("a.txt", "b.txt").to_string(),
            "--- a.txt\n+++ b.txt\n@@ -1 +1 @@\n-a\n+b\n\\ No newline at end of file\n"
        );
        assert_eq!(
            diff.unified_diff()
                .missing_newline_hint(false)
                .header("a.txt", "b.txt")
                .to_string(),
            "--- a.txt\n+++ b.txt\n@@ -1 +1 @@\n-a\n+b\n"
        );
    }

    #[test]
    fn test_unified_diff_zero_radius_empty_ranges() {
        let config = TextDiffConfig::default();
        let diff = config.diff_lines("\u{18}\n\n", "\n\n\r");
        let output = diff.unified_diff().context_radius(0).to_string();
        assert_eq!(output, "@@ -1 +1,0 @@\n-\u{18}\n@@ -2,0 +2,2 @@\n+\n+\r");
    }

    #[test]
    fn generated_unified_quick_fn_equals_pipeline() {
        let old = "wolf\nbear\nlynx\nhare\n";
        let new = "wolf\nbear\nfox\nhare\n";
        let quick = unified_diff(Algorithm::Myers, old, new, 1, Some(("l", "r")));
        let pipeline = TextDiff::configure()
            .algorithm(Algorithm::Myers)
            .diff_lines(old, new)
            .unified_diff()
            .context_radius(1)
            .header("l", "r")
            .to_string();
        assert_eq!(quick, pipeline);
        assert_eq!(
            quick,
            "--- l\n+++ r\n@@ -2,3 +2,3 @@\n bear\n-lynx\n+fox\n hare\n"
        );
    }

    #[test]
    fn generated_unified_to_writer_matches_display() {
        let diff = TextDiff::from_lines("k1\nk2\nk3\n", "k1\nx2\nk3\n");
        let display = diff.unified_diff().header("a", "b").to_string();
        let mut buf: Vec<u8> = Vec::new();
        diff.unified_diff()
            .header("a", "b")
            .to_writer(&mut buf)
            .unwrap();
        assert_eq!(String::from_utf8(buf).unwrap(), display);
        assert!(!display.is_empty());
    }

    #[test]
    fn generated_unified_hunks_match_grouped_ops() {
        let old: String = (0..40).map(|i| format!("line {}\n", i)).collect();
        let new = old.replace("line 4\n", "line four\n").replace("line 30\n", "line thirty\n");
        let diff = TextDiff::from_lines(old.as_str(), new.as_str());
        let groups = diff.grouped_ops(3);
        let hunks: Vec<_> = diff.unified_diff().context_radius(3).iter_hunks().collect();
        assert_eq!(groups.len(), hunks.len());
        assert_eq!(groups.len(), 2);
        for (group, hunk) in groups.iter().zip(hunks.iter()) {
            assert_eq!(&group[..], hunk.ops());
            // Header ranges derive from the first and last op of the group.
            let expected_header =
                similar::udiff::UnifiedHunkHeader::new(&group[..]).to_string();
            assert_eq!(hunk.header().to_string(), expected_header);
            // One rendered line per change, each prefixed by its tag char.
            let rendered = hunk.to_string();
            let mut lines = rendered.lines();
            let header_line = lines.next().unwrap();
            assert!(header_line.starts_with("@@ -"));
            let changes: Vec<_> = hunk.iter_changes().collect();
            let body: Vec<_> = lines.collect();
            assert_eq!(body.len(), changes.len());
            for (line, change) in body.iter().zip(changes.iter()) {
                let tag_char = format!("{}", change.tag());
                assert!(line.starts_with(tag_char.as_str()));
                assert_eq!(&line[1..], change.value().trim_end_matches('\n'));
            }
        }
    }

    #[test]
    fn generated_unified_no_hunks_no_header() {
        let diff = TextDiff::from_lines("same\ntext\n", "same\ntext\n");
        assert_eq!(diff.unified_diff().header("a", "b").to_string(), "");
        let mut buf: Vec<u8> = Vec::new();
        diff.unified_diff().header("a", "b").to_writer(&mut buf).unwrap();
        assert_eq!(buf, b"");
    }
}
