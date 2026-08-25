// Source-rank precedence contracts exercised on real trees.
mod precedence {
    use ignore::gitignore::{Gitignore, GitignoreBuilder};
    use ignore::overrides::OverrideBuilder;
    use ignore::WalkBuilder;

    use super::{names, walk_sorted, TreeFixture};

    #[test]
    fn generated_dotignore_whitelist_rescues_gitignored() {
        let t = TreeFixture::new("rescue");
        t.dir(".git");
        t.file(".gitignore", "*.log\n");
        t.file(".ignore", "!bulletin.log\n");
        t.file("bulletin.log", "");
        t.file("trace.log", "");
        t.file("readme.md", "");

        // `.ignore` outranks `.gitignore`: its whitelist re-includes one log
        let wb = WalkBuilder::new(t.path());
        assert_eq!(
            walk_sorted(&wb, t.path()),
            names(&[".", "bulletin.log", "readme.md"])
        );
    }

    #[test]
    fn generated_custom_file_outranks_dotignore() {
        let t = TreeFixture::new("custrank");
        t.file(".ignore", "*.dat\n");
        t.file("custom_rules", "!keep.dat\n");
        t.file("keep.dat", "");
        t.file("drop.dat", "");
        t.file("plain.txt", "");

        let mut wb = WalkBuilder::new(t.path());
        wb.add_custom_ignore_filename("custom_rules");
        assert_eq!(
            walk_sorted(&wb, t.path()),
            names(&[".", "custom_rules", "keep.dat", "plain.txt"])
        );
    }

    #[test]
    fn generated_override_outranks_all_sources() {
        let t = TreeFixture::new("overrank");
        t.dir(".git");
        t.file(".gitignore", "*.rs\n");
        t.file(".ignore", "*.rs\n");
        t.file("gear.rs", "");
        t.file("gear.toml", "");

        let mut over = OverrideBuilder::new(t.path());
        over.add("*.rs").unwrap();
        let mut wb = WalkBuilder::new(t.path());
        wb.overrides(over.build().unwrap());

        // the override whitelist beats both ignore-file sources; the
        // blanket rule drops every other file
        assert_eq!(walk_sorted(&wb, t.path()), names(&[".", "gear.rs"]));
    }

    #[test]
    fn generated_add_ignore_lowest_rank() {
        let t = TreeFixture::new("addrank");
        t.dir(".git");
        t.file(".gitignore", "!notes.txt\n");
        t.file("extra_rules", "*.txt\n");
        t.file("notes.txt", "");
        t.file("memo.txt", "");
        t.file("data.csv", "");

        let mut wb = WalkBuilder::new(t.path());
        assert!(wb.add_ignore(t.path().join("extra_rules")).is_none());

        // the .gitignore whitelist outranks the add_ignore rule stack;
        // files only the low-rank source mentions stay dropped
        assert_eq!(
            walk_sorted(&wb, t.path()),
            names(&[".", "notes.txt", "data.csv", "extra_rules"])
        );
    }

    #[test]
    fn generated_deeper_file_outranks_shallower() {
        let t = TreeFixture::new("deeper");
        t.dir(".git");
        t.file(".gitignore", "*.cfg\n");
        t.file("sub/.gitignore", "!local.cfg\n");
        t.file("root.cfg", "");
        t.file("sub/local.cfg", "");
        t.file("sub/other.cfg", "");
        t.file("sub/app.txt", "");

        let wb = WalkBuilder::new(t.path());
        assert_eq!(
            walk_sorted(&wb, t.path()),
            names(&[".", "sub", "sub/local.cfg", "sub/app.txt"])
        );
    }

    #[test]
    fn generated_whitelist_cannot_rescue_inside_ignored_dir() {
        let t = TreeFixture::new("norescue");
        t.dir(".git");
        t.file(".gitignore", "vault/\n!vault/gem.txt\n");
        t.file("vault/gem.txt", "");
        t.file("vault/coal.txt", "");
        t.file("open.txt", "");

        // the pure matcher query for the file alone reports Whitelist...
        let mut b = GitignoreBuilder::new(t.path());
        b.add_line(None, "vault/").unwrap();
        b.add_line(None, "!vault/gem.txt").unwrap();
        let gi = b.build().unwrap();
        assert!(gi.matched("vault/gem.txt", false).is_whitelist());

        // ...but the walker never descends into the ignored directory
        let wb = WalkBuilder::new(t.path());
        assert_eq!(walk_sorted(&wb, t.path()), names(&[".", "open.txt"]));
    }

    #[test]
    fn generated_last_match_wins_through_walker() {
        let t = TreeFixture::new("lastwins");
        t.dir(".git");
        t.file(".gitignore", "*.tone\n!chime.tone\n");
        t.file("chime.tone", "");
        t.file("hum.tone", "");
        t.file("solo.wav", "");

        // matcher view of the same rule file
        let (gi, err) = Gitignore::new(t.path().join(".gitignore"));
        assert!(err.is_none());
        assert!(gi.matched("hum.tone", false).is_ignore());
        assert!(gi.matched("chime.tone", false).is_whitelist());

        // walker view agrees
        let wb = WalkBuilder::new(t.path());
        assert_eq!(
            walk_sorted(&wb, t.path()),
            names(&[".", "chime.tone", "solo.wav"])
        );
    }
}
