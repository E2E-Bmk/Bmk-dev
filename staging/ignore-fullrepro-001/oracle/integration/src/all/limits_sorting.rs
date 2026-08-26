// Selection limits, toggle bundles, sorting, and depth accounting.
mod limits_sorting {
    use std::collections::HashMap;
    use std::path::Path;

    use ignore::types::TypesBuilder;
    use ignore::WalkBuilder;

    use super::{names, rel_name, walk_sorted, TreeFixture};

    #[test]
    fn generated_standard_filters_equivalence() {
        let t = TreeFixture::new("stdfil");
        t.dir(".git/info");
        t.file(".git/info/exclude", "*.exc\n");
        t.file(".gitignore", "*.gig\n");
        t.file(".ignore", "*.dig\n");
        t.file(".hidden.txt", "");
        t.file("a.exc", "");
        t.file("b.gig", "");
        t.file("c.dig", "");
        t.file("d.txt", "");

        let mut bundled = WalkBuilder::new(t.path());
        bundled.standard_filters(false);

        let mut individual = WalkBuilder::new(t.path());
        individual
            .hidden(false)
            .parents(false)
            .ignore(false)
            .git_ignore(false)
            .git_global(false)
            .git_exclude(false);

        let bundled_set = walk_sorted(&bundled, t.path());
        let individual_set = walk_sorted(&individual, t.path());
        assert_eq!(bundled_set, individual_set);

        // with every standard filter off, nothing is filtered
        for kept in ["a.exc", "b.gig", "c.dig", "d.txt", ".hidden.txt", ".gitignore"] {
            assert!(
                bundled_set.contains(&kept.to_string()),
                "{kept} missing with filters disabled"
            );
        }
    }

    #[test]
    fn generated_max_depth_is_subset() {
        let t = TreeFixture::new("depthsub");
        t.file("a.txt", "");
        t.file("one/b.txt", "");
        t.file("one/two/c.txt", "");
        t.file("one/two/three/d.txt", "");

        // unlimited walk: depth() equals the component distance from the root
        let unlimited: Vec<(String, usize)> = WalkBuilder::new(t.path())
            .build()
            .map(|r| r.unwrap())
            .map(|e| (rel_name(t.path(), e.path()), e.depth()))
            .collect();
        for (name, depth) in &unlimited {
            let expected = if name == "." {
                0
            } else {
                Path::new(name).components().count()
            };
            assert_eq!(*depth, expected, "depth mismatch for {name}");
        }

        // the limited walk is exactly the depth-filtered subset
        let mut wb = WalkBuilder::new(t.path());
        wb.max_depth(Some(2));
        let limited = walk_sorted(&wb, t.path());
        let mut expected: Vec<String> = unlimited
            .iter()
            .filter(|(_, d)| *d <= 2)
            .map(|(n, _)| n.clone())
            .collect();
        expected.sort();
        assert_eq!(limited, expected);
        assert_eq!(
            limited,
            names(&[".", "a.txt", "one", "one/b.txt", "one/two"])
        );
    }

    #[test]
    fn generated_sorted_multiset_unchanged() {
        let t = TreeFixture::new("sortinv");
        t.file("walnut/husk.txt", "");
        t.file("acorn.txt", "");
        t.file("birch/bark.txt", "");
        t.file("birch/twig/leaf.txt", "");
        t.file("cedar.txt", "");

        let unsorted = walk_sorted(&WalkBuilder::new(t.path()), t.path());

        let mut wb = WalkBuilder::new(t.path());
        wb.sort_by_file_name(|a, b| b.cmp(a)); // reverse name order
        let order: Vec<String> = wb
            .build()
            .map(|r| rel_name(t.path(), r.unwrap().path()))
            .collect();

        // (a) sorting never changes the visibility set
        let mut sorted_set = order.clone();
        sorted_set.sort();
        assert_eq!(sorted_set, unsorted);

        // (b) every directory is yielded before its contents
        let index: HashMap<&str, usize> = order
            .iter()
            .enumerate()
            .map(|(i, n)| (n.as_str(), i))
            .collect();
        for name in order.iter().filter(|n| n.as_str() != ".") {
            let parent = match Path::new(name).parent() {
                Some(p) if !p.as_os_str().is_empty() => p.to_string_lossy().into_owned(),
                _ => ".".to_string(),
            };
            assert!(
                index[parent.as_str()] < index[name.as_str()],
                "{name} yielded before its parent {parent}"
            );
        }

        // (c) siblings appear in comparator order (reverse of name order)
        let mut by_parent: HashMap<String, Vec<String>> = HashMap::new();
        for name in order.iter().filter(|n| n.as_str() != ".") {
            let parent = match Path::new(name).parent() {
                Some(p) if !p.as_os_str().is_empty() => p.to_string_lossy().into_owned(),
                _ => ".".to_string(),
            };
            let base = Path::new(name)
                .file_name()
                .unwrap()
                .to_string_lossy()
                .into_owned();
            by_parent.entry(parent).or_default().push(base);
        }
        for (parent, kids) in by_parent {
            let mut expected = kids.clone();
            expected.sort_by(|a, b| b.cmp(a));
            assert_eq!(kids, expected, "siblings out of order under {parent}");
        }
    }

    #[test]
    fn generated_max_filesize_with_types() {
        let t = TreeFixture::new("sizetypes");
        t.file("tiny.dat", "xx");
        t.file("huge.dat", &"x".repeat(500));
        t.file("tiny.txt", "xx");
        t.file("bin/mid.dat", &"x".repeat(50));

        let mut tb = TypesBuilder::new();
        tb.add("data", "*.dat").unwrap();
        tb.select("data");

        let mut wb = WalkBuilder::new(t.path());
        wb.types(tb.build().unwrap());
        wb.max_filesize(Some(100));

        // a file must pass both the size limit and the type filter;
        // directories are affected by neither
        assert_eq!(
            walk_sorted(&wb, t.path()),
            names(&[".", "tiny.dat", "bin", "bin/mid.dat"])
        );
    }

    #[test]
    fn generated_multi_root_depths_reset() {
        let t = TreeFixture::new("multiroot");
        t.file("east/a/x.txt", "");
        t.file("west/y.txt", "");
        let east = t.path().join("east");
        let west = t.path().join("west");

        let mut wb = WalkBuilder::new(&east);
        wb.add(&west);

        let mut seen_roots = 0;
        for result in wb.build() {
            let e = result.unwrap();
            let root = if e.path().starts_with(&east) { &east } else { &west };
            let expected = e
                .path()
                .strip_prefix(root)
                .unwrap()
                .components()
                .count();
            // depth counts from each entry's own root
            assert_eq!(e.depth(), expected, "depth mismatch for {:?}", e.path());
            if e.depth() == 0 {
                seen_roots += 1;
            }
        }
        assert_eq!(seen_roots, 2);
    }

    #[test]
    fn generated_filter_entry_sees_hidden_when_disabled() {
        let t = TreeFixture::new("prehidden");
        t.file(".attic/relic.txt", "");
        t.file("skipzone/junk.txt", "");
        t.file("keep.txt", "");
        t.file(".stash.txt", "");

        let mut wb = WalkBuilder::new(t.path());
        wb.hidden(false);
        wb.filter_entry(|e| !e.file_name().to_string_lossy().contains("skip"));

        // the predicate applies to dot entries once hidden filtering is off
        assert_eq!(
            walk_sorted(&wb, t.path()),
            names(&[".", ".attic", ".attic/relic.txt", "keep.txt", ".stash.txt"])
        );
    }
}
