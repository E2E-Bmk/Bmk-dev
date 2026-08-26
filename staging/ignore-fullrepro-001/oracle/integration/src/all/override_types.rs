// Override and type matchers driving walks, checked against their own
// pure-query verdicts on the same tree.
mod override_types {
    use ignore::overrides::OverrideBuilder;
    use ignore::types::TypesBuilder;
    use ignore::WalkBuilder;

    use super::{names, walk_sorted, TreeFixture};

    #[test]
    fn generated_walk_matches_override_verdicts() {
        let t = TreeFixture::new("ovagree");
        let files = ["main.tin", "sub/dev.tin", "sub/notes.md", "guide.md"];
        for f in files {
            t.file(f, "");
        }

        let mut ob = OverrideBuilder::new(t.path());
        ob.add("*.tin").unwrap();
        ob.add("!dev.tin").unwrap();
        let ov = ob.build().unwrap();

        let mut wb = WalkBuilder::new(t.path());
        wb.overrides(ob.build().unwrap());
        let walked = walk_sorted(&wb, t.path());

        // CVI: yielded files are exactly those whose override verdict is
        // not Ignore; directories are unaffected
        let mut expected: Vec<&str> = vec![".", "sub"];
        for f in files {
            let keep = !ov.matched(f, false).is_ignore();
            assert_eq!(
                walked.contains(&f.to_string()),
                keep,
                "override walk and matcher disagree on {f}"
            );
            if keep {
                expected.push(f);
            }
        }
        assert_eq!(walked, names(&expected));
        assert_eq!(walked, names(&[".", "sub", "main.tin"]));
    }

    #[test]
    fn generated_walk_matches_types_verdicts() {
        let t = TreeFixture::new("tyagree");
        let files = [
            "pages/index.html",
            "pages/app.css",
            "top.html",
            "readme.txt",
        ];
        for f in files {
            t.file(f, "");
        }

        let mut tb = TypesBuilder::new();
        tb.add("markup", "*.html").unwrap();
        tb.add("style", "*.css").unwrap();
        tb.select("markup");
        tb.select("style");
        let ty = tb.build().unwrap();

        let mut wb = WalkBuilder::new(t.path());
        wb.types(tb.build().unwrap());
        let walked = walk_sorted(&wb, t.path());

        let mut expected: Vec<&str> = vec![".", "pages"];
        for f in files {
            let keep = !ty.matched(f, false).is_ignore();
            assert_eq!(
                walked.contains(&f.to_string()),
                keep,
                "types walk and matcher disagree on {f}"
            );
            if keep {
                expected.push(f);
            }
        }
        assert_eq!(walked, names(&expected));
        assert_eq!(
            walked,
            names(&[".", "pages", "pages/index.html", "pages/app.css", "top.html"])
        );
    }

    #[test]
    fn generated_override_and_types_compose() {
        let t = TreeFixture::new("compose");
        let files = [
            "kiln.pot",
            "kiln.jar",
            "shelf/urn.pot",
            "shelf/urn.txt",
            "notes.bak",
        ];
        for f in files {
            t.file(f, "");
        }

        // negation-only override: *.bak is ignored, everything else falls
        // through to the next source
        let mut ob = OverrideBuilder::new(t.path());
        ob.add("!*.bak").unwrap();
        let ov = ob.build().unwrap();

        let mut tb = TypesBuilder::new();
        tb.add("pottery", "*.pot").unwrap();
        tb.select("pottery");
        let ty = tb.build().unwrap();

        let mut wb = WalkBuilder::new(t.path());
        wb.overrides(ob.build().unwrap());
        wb.types(tb.build().unwrap());
        let walked = walk_sorted(&wb, t.path());

        // fold per the source-precedence contract: a decisive override
        // verdict is final; otherwise the type filter decides for files
        for f in files {
            let over = ov.matched(f, false);
            let keep = if !over.is_none() {
                !over.is_ignore()
            } else {
                !ty.matched(f, false).is_ignore()
            };
            assert_eq!(
                walked.contains(&f.to_string()),
                keep,
                "composed filters disagree on {f}"
            );
        }
        assert_eq!(
            walked,
            names(&[".", "kiln.pot", "shelf", "shelf/urn.pot"])
        );
    }

    #[test]
    fn generated_override_verdict_bypasses_types() {
        let t = TreeFixture::new("ovfinal");
        t.file("kiln.jar", "");
        t.file("kiln.pot", "");
        t.file("plain.txt", "");

        // the override whitelists *.jar; the type filter selects only *.pot
        let mut ob = OverrideBuilder::new(t.path());
        ob.add("*.jar").unwrap();
        let mut tb = TypesBuilder::new();
        tb.add("pottery", "*.pot").unwrap();
        tb.select("pottery");

        let mut wb = WalkBuilder::new(t.path());
        wb.overrides(ob.build().unwrap());
        wb.types(tb.build().unwrap());

        // a decisive override whitelist is final — the type filter is not
        // consulted for kiln.jar; files the override has no glob for fall
        // to its blanket rule and never reach the type filter either
        assert_eq!(walk_sorted(&wb, t.path()), names(&[".", "kiln.jar"]));
    }

    #[test]
    fn generated_override_whitelist_rescues_gitignored_file() {
        let t = TreeFixture::new("ovrescue");
        t.dir(".git");
        t.file(".gitignore", "*.js\n");
        t.file("app.js", "");
        t.file("lib.js", "");
        t.file("style.css", "");

        let mut ob = OverrideBuilder::new(t.path());
        ob.add("app.js").unwrap();
        let mut wb = WalkBuilder::new(t.path());
        wb.overrides(ob.build().unwrap());

        // the override whitelist (highest rank) re-includes a gitignored
        // file; everything unmatched falls to the blanket rule
        assert_eq!(walk_sorted(&wb, t.path()), names(&[".", "app.js"]));
    }

    #[test]
    fn generated_types_ignore_beats_ignore_file_whitelist() {
        let t = TreeFixture::new("tyfinal");
        t.file(".ignore", "*.tmp\n!keep.tmp\n");
        t.file("keep.tmp", "");
        t.file("b.tmp", "");
        t.file("a.md", "");

        let mut tb = TypesBuilder::new();
        tb.add("docs", "*.md").unwrap();
        tb.select("docs");

        let mut wb = WalkBuilder::new(t.path());
        wb.types(tb.build().unwrap());

        // keep.tmp is re-included by the .ignore whitelist, but the type
        // filter is consulted afterwards and its blanket ignore drops it
        assert_eq!(walk_sorted(&wb, t.path()), names(&[".", "a.md"]));
    }

    #[test]
    fn generated_types_negate_on_walk() {
        let t = TreeFixture::new("tyneg");
        t.file("notes.md", "");
        t.file("old.bak", "");
        t.file("misc.txt", "");

        let mut tb = TypesBuilder::new();
        tb.add("docs", "*.md").unwrap();
        tb.add("junk", "*.bak").unwrap();
        tb.select("all");
        tb.negate("junk");
        let ty = tb.build().unwrap();

        let mut wb = WalkBuilder::new(t.path());
        wb.types(tb.build().unwrap());
        let walked = walk_sorted(&wb, t.path());
        assert_eq!(walked, names(&[".", "notes.md"]));

        // verdicts behind the walk: whitelist, negated ignore, blanket ignore
        assert!(ty.matched("notes.md", false).is_whitelist());
        assert!(ty.matched("old.bak", false).is_ignore());
        assert!(ty.matched("misc.txt", false).is_ignore());
    }

    #[test]
    fn generated_types_include_composite_on_walk() {
        let t = TreeFixture::new("tyinc");
        t.file("a.md", "");
        t.file("b.rst", "");
        t.file("c.txt", "");
        t.file("sub/d.md", "");

        let mut tb = TypesBuilder::new();
        tb.add("md", "*.md").unwrap();
        tb.add("rst", "*.rst").unwrap();
        tb.add_def("prose:include:md,rst").unwrap();
        tb.select("prose");

        let mut wb = WalkBuilder::new(t.path());
        wb.types(tb.build().unwrap());
        assert_eq!(
            walk_sorted(&wb, t.path()),
            names(&[".", "a.md", "b.rst", "sub", "sub/d.md"])
        );
    }
}
