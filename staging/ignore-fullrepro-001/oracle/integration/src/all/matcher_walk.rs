// Matcher queries and real walks as agreeing projections of one rule stack.
mod matcher_walk {
    use std::path::Path;

    use ignore::gitignore::{Gitignore, GitignoreBuilder};
    use ignore::overrides::OverrideBuilder;
    use ignore::WalkBuilder;

    use super::{kind, names, walk_sorted, TreeFixture};

    #[test]
    fn generated_walk_agrees_with_matcher_stack() {
        let t = TreeFixture::new("agree");
        t.file(".gitignore", "*.tmp\nlogs/\n!keep.tmp\n**/raw.dat\n");
        let files = [
            "keep.tmp",
            "a.tmp",
            "logs/x.txt",
            "data/raw.dat",
            "data/fine.txt",
            "nested/deep/keep.tmp",
        ];
        for f in files {
            t.file(f, "");
        }

        let (gi, err) = Gitignore::new(t.path().join(".gitignore"));
        assert!(err.is_none());

        let mut wb = WalkBuilder::new(t.path());
        wb.require_git(false);
        let walked = walk_sorted(&wb, t.path());

        // CVI: a file appears in the walk exactly when the parent-aware
        // matcher query does not report Ignore.
        let mut expected: Vec<&str> = vec![".", "data", "nested", "nested/deep"];
        for f in files {
            let verdict = gi.matched_path_or_any_parents(Path::new(f), false);
            assert_eq!(
                walked.contains(&f.to_string()),
                !verdict.is_ignore(),
                "walk and matcher disagree on {f}"
            );
            if !verdict.is_ignore() {
                expected.push(f);
            }
        }
        assert_eq!(walked, names(&expected));
        // the ignored directory is not yielded either
        assert!(!walked.contains(&"logs".to_string()));
    }

    #[test]
    fn generated_mpap_equals_ancestor_fold() {
        let mut b = GitignoreBuilder::new("/plot");
        b.add_line(None, "hollow/").unwrap();
        b.add_line(None, "!spark.txt").unwrap();
        b.add_line(None, "*.raw").unwrap();
        let gi = b.build().unwrap();

        // manual fold: the path itself, then each ancestor as a directory,
        // deepest first; the first decisive verdict wins
        let fold = |p: &str, is_dir: bool| -> u8 {
            let k = kind(&gi.matched(p, is_dir));
            if k != 0 {
                return k;
            }
            let mut anc = Path::new(p).parent();
            while let Some(a) = anc {
                if a.as_os_str().is_empty() {
                    break;
                }
                let k = kind(&gi.matched(a, true));
                if k != 0 {
                    return k;
                }
                anc = a.parent();
            }
            0
        };

        let cases = [
            ("hollow/ember/spark.txt", false),
            ("hollow/ember/dust.bin", false),
            ("spark.txt", false),
            ("field.raw", false),
            ("meadow/clover.txt", false),
            ("hollow/ember", true),
        ];
        for (p, is_dir) in cases {
            assert_eq!(
                kind(&gi.matched_path_or_any_parents(Path::new(p), is_dir)),
                fold(p, is_dir),
                "fold mismatch for {p}"
            );
        }

        // spot-check the concrete verdicts the fold implies
        assert!(gi
            .matched_path_or_any_parents(Path::new("hollow/ember/spark.txt"), false)
            .is_whitelist());
        assert!(gi
            .matched_path_or_any_parents(Path::new("hollow/ember/dust.bin"), false)
            .is_ignore());
        assert!(gi
            .matched_path_or_any_parents(Path::new("meadow/clover.txt"), false)
            .is_none());
    }

    #[test]
    fn generated_override_inverts_gitignore() {
        let lines = ["*.note", "!pinned.note"];

        let mut gb = GitignoreBuilder::new("/plot");
        let mut ob = OverrideBuilder::new("/plot");
        for line in lines {
            gb.add_line(None, line).unwrap();
            ob.add(line).unwrap();
        }
        let gi = gb.build().unwrap();
        let ov = ob.build().unwrap();

        // matched paths report exactly inverted verdicts
        for p in ["memo.note", "pinned.note", "stack/memo.note"] {
            assert_eq!(
                kind(&ov.matched(p, false)),
                kind(&gi.matched(p, false).invert()),
                "inversion mismatch for {p}"
            );
        }
        assert!(gi.matched("memo.note", false).is_ignore());
        assert!(ov.matched("memo.note", false).is_whitelist());
        assert!(gi.matched("pinned.note", false).is_whitelist());
        assert!(ov.matched("pinned.note", false).is_ignore());

        // the extra override rule: an unmatched file becomes Ignore because
        // a plain glob exists, while the gitignore stays undecided
        assert!(gi.matched("readme.txt", false).is_none());
        assert!(ov.matched("readme.txt", false).is_ignore());
        // unmatched directories stay undecided on both sides
        assert!(gi.matched("box", true).is_none());
        assert!(ov.matched("box", true).is_none());
    }

    #[test]
    fn generated_two_build_routes_agree() {
        let t = TreeFixture::new("routes");
        t.file("furrules", "*.pelt\n!fox.pelt\nden/\n");

        let (from_file, err) = Gitignore::new(t.path().join("furrules"));
        assert!(err.is_none());

        let mut b = GitignoreBuilder::new(t.path());
        for line in ["*.pelt", "!fox.pelt", "den/"] {
            b.add_line(None, line).unwrap();
        }
        let from_lines = b.build().unwrap();

        assert_eq!(from_file.len(), from_lines.len());
        assert_eq!(from_file.num_ignores(), from_lines.num_ignores());
        assert_eq!(from_file.num_whitelists(), from_lines.num_whitelists());

        let probes = [
            ("wolf.pelt", false),
            ("fox.pelt", false),
            ("den", true),
            ("den", false),
            ("sett/wolf.pelt", false),
        ];
        for (p, is_dir) in probes {
            assert_eq!(
                kind(&from_file.matched(p, is_dir)),
                kind(&from_lines.matched(p, is_dir)),
                "build routes disagree on {p}"
            );
        }
        assert!(from_file.matched("wolf.pelt", false).is_ignore());
        assert!(from_file.matched("fox.pelt", false).is_whitelist());
        assert!(from_file.matched("den", true).is_ignore());
        assert!(from_file.matched("den", false).is_none());
    }

    #[test]
    fn generated_case_insensitive_matcher_and_walk_agree() {
        let t = TreeFixture::new("caseless");
        t.file(".ignore", "*.log\n");
        t.file("REPORT.LOG", "");
        t.file("report.log", "");
        t.file("Data.TXT", "");

        // case-sensitive default: only the lowercase name is filtered
        let wb = WalkBuilder::new(t.path());
        assert_eq!(
            walk_sorted(&wb, t.path()),
            names(&[".", "REPORT.LOG", "Data.TXT"])
        );

        // case-insensitive walk drops both
        let mut wb = WalkBuilder::new(t.path());
        wb.ignore_case_insensitive(true);
        let walked = walk_sorted(&wb, t.path());
        assert_eq!(walked, names(&[".", "Data.TXT"]));

        // a matcher built the same way agrees file by file
        let mut b = GitignoreBuilder::new(t.path());
        b.case_insensitive(true).unwrap();
        b.add_line(None, "*.log").unwrap();
        let gi = b.build().unwrap();
        for f in ["REPORT.LOG", "report.log", "Data.TXT"] {
            assert_eq!(
                walked.contains(&f.to_string()),
                !gi.matched(f, false).is_ignore(),
                "case-insensitive views disagree on {f}"
            );
        }
    }
}
