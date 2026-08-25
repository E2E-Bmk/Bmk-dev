// The parallel walker as a second projection of the same visibility set.
mod parallel {
    use std::sync::{Arc, Mutex};

    use ignore::overrides::OverrideBuilder;
    use ignore::{WalkBuilder, WalkState};

    use super::{names, parallel_sorted, rel_name, walk_sorted, TreeFixture};

    #[test]
    fn generated_parallel_equals_serial_full_config() {
        let t = TreeFixture::new("parfull");
        t.dir(".git");
        t.file(".gitignore", "*.tmp\n");
        t.file(".dotfile", "");
        t.file(".dotdir/x.txt", "");
        t.file("keep.txt", "");
        t.file("skip.tmp", "");
        t.file("sub/keep2.txt", "");

        let mut wb = WalkBuilder::new(t.path());
        wb.hidden(false).threads(3);

        let serial = walk_sorted(&wb, t.path());
        let parallel = parallel_sorted(&wb, t.path());
        assert_eq!(serial, parallel);
        assert_eq!(
            serial,
            names(&[
                ".",
                ".git",
                ".gitignore",
                ".dotfile",
                ".dotdir",
                ".dotdir/x.txt",
                "keep.txt",
                "sub",
                "sub/keep2.txt"
            ])
        );
    }

    #[test]
    fn generated_parallel_thread_counts_agree() {
        let t = TreeFixture::new("parthreads");
        for d in ["oak", "elm", "fir"] {
            for i in 0..3 {
                t.file(&format!("{d}/leaf_{i}.txt"), "");
            }
        }

        let serial = walk_sorted(&WalkBuilder::new(t.path()), t.path());
        for threads in [0, 1, 4] {
            let mut wb = WalkBuilder::new(t.path());
            wb.threads(threads);
            assert_eq!(
                parallel_sorted(&wb, t.path()),
                serial,
                "thread count {threads} changed the visibility set"
            );
        }
        assert_eq!(serial.len(), 13); // root + 3 dirs + 9 files
    }

    #[test]
    fn generated_parallel_skip_equals_serial_filter() {
        let t = TreeFixture::new("parskipeq");
        t.file("hive/comb.txt", "");
        t.file("hive/inner/comb2.txt", "");
        t.file("field/daisy.txt", "");

        // parallel walk skipping descent at "hive"
        let got: Arc<Mutex<Vec<String>>> = Arc::new(Mutex::new(Vec::new()));
        let rootbuf = t.path().to_path_buf();
        let mut wb = WalkBuilder::new(t.path());
        wb.threads(2);
        wb.build_parallel().run(|| {
            let got = Arc::clone(&got);
            let rootbuf = rootbuf.clone();
            Box::new(move |result| {
                let entry = result.expect("unexpected walk error");
                let name = rel_name(&rootbuf, entry.path());
                got.lock().unwrap().push(name.clone());
                if name == "hive" {
                    WalkState::Skip
                } else {
                    WalkState::Continue
                }
            })
        });
        let mut skipped = got.lock().unwrap().clone();
        skipped.sort();

        // serial walk pruning the same directory via filter_entry
        let mut wb = WalkBuilder::new(t.path());
        wb.filter_entry(|e| e.file_name() != "hive");
        let mut filtered = walk_sorted(&wb, t.path());

        // Skip still delivers the directory entry itself; filter_entry does
        // not — the sets differ by exactly that entry.
        filtered.push("hive".to_string());
        filtered.sort();
        assert_eq!(skipped, filtered);
        assert_eq!(
            skipped,
            names(&[".", "field", "field/daisy.txt", "hive"])
        );
    }

    #[test]
    fn generated_parallel_sees_rule_stack() {
        let t = TreeFixture::new("parrules");
        t.dir(".git");
        t.file(".gitignore", "drafts/\n*.wip\n");
        t.file("drafts/a.txt", "");
        t.file("essay.wip", "");
        t.file("final.txt", "");

        let mut over = OverrideBuilder::new(t.path());
        over.add("!*.bak").unwrap();
        let mut wb = WalkBuilder::new(t.path());
        wb.overrides(over.build().unwrap()).threads(2);

        assert_eq!(
            parallel_sorted(&wb, t.path()),
            names(&[".", "final.txt"])
        );
    }

    #[test]
    fn generated_parallel_quit_delivers_subset() {
        let t = TreeFixture::new("parquits");
        for d in ["north", "south"] {
            for i in 0..10 {
                t.file(&format!("{d}/pebble_{i}.txt"), "");
            }
        }
        t.file("signal.stop", "");

        let serial = walk_sorted(&WalkBuilder::new(t.path()), t.path());

        let got: Arc<Mutex<Vec<String>>> = Arc::new(Mutex::new(Vec::new()));
        let rootbuf = t.path().to_path_buf();
        let mut wb = WalkBuilder::new(t.path());
        wb.threads(2);
        wb.build_parallel().run(|| {
            let got = Arc::clone(&got);
            let rootbuf = rootbuf.clone();
            Box::new(move |result| {
                let entry = result.expect("unexpected walk error");
                let name = rel_name(&rootbuf, entry.path());
                got.lock().unwrap().push(name.clone());
                if name == "signal.stop" {
                    WalkState::Quit
                } else {
                    WalkState::Continue
                }
            })
        });
        let delivered = got.lock().unwrap().clone();

        // every delivered entry belongs to the serial set, and the trigger
        // was delivered (either the quit fired on it, or the walk finished)
        assert!(delivered.iter().all(|n| serial.contains(n)));
        assert!(delivered.contains(&"signal.stop".to_string()));
    }
}
