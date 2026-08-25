// Oracle atomic tests for the ignore rules and directory walking library
#![cfg(test)]
#![allow(clippy::all)]

use std::fs;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::{Arc, Mutex};

use ignore::gitignore::{Gitignore, GitignoreBuilder};
use ignore::overrides::{Override, OverrideBuilder};
use ignore::types::{Types, TypesBuilder};
use ignore::{Match, Walk, WalkBuilder, WalkState};

static NEXT_FIXTURE: AtomicUsize = AtomicUsize::new(0);

/// A unique temporary directory tree, removed on drop.
struct TreeFixture {
    root: PathBuf,
}

impl TreeFixture {
    fn new(tag: &str) -> TreeFixture {
        let n = NEXT_FIXTURE.fetch_add(1, Ordering::SeqCst);
        let root = std::env::temp_dir()
            .join(format!("oracle_ig_a_{}_{}_{}", tag, std::process::id(), n));
        let _ = fs::remove_dir_all(&root);
        fs::create_dir_all(&root).unwrap();
        TreeFixture { root }
    }

    fn file(&self, rel: &str, contents: &str) -> &Self {
        let p = self.root.join(rel);
        if let Some(parent) = p.parent() {
            fs::create_dir_all(parent).unwrap();
        }
        fs::write(p, contents).unwrap();
        self
    }

    fn dir(&self, rel: &str) -> &Self {
        fs::create_dir_all(self.root.join(rel)).unwrap();
        self
    }

    fn path(&self) -> &Path {
        &self.root
    }
}

impl Drop for TreeFixture {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.root);
    }
}

fn rel_name(root: &Path, p: &Path) -> String {
    let s = p
        .strip_prefix(root)
        .expect("entry outside root")
        .to_string_lossy()
        .replace('\\', "/");
    if s.is_empty() {
        ".".to_string()
    } else {
        s
    }
}

/// Collect the walk as sorted root-relative names ("." for the root).
fn walk_sorted(wb: &WalkBuilder, root: &Path) -> Vec<String> {
    let mut out: Vec<String> = wb
        .build()
        .map(|r| r.expect("unexpected walk error"))
        .map(|e| rel_name(root, e.path()))
        .collect();
    out.sort();
    out
}

fn names(v: &[&str]) -> Vec<String> {
    let mut out: Vec<String> = v.iter().map(|s| s.to_string()).collect();
    out.sort();
    out
}

// ---------------------------------------------------------------------------
// Match verdicts
// ---------------------------------------------------------------------------

#[test]
fn generated_match_variant_predicates() {
    let none: Match<u32> = Match::None;
    let ign: Match<u32> = Match::Ignore(7);
    let wl: Match<u32> = Match::Whitelist(9);

    assert!(none.is_none() && !none.is_ignore() && !none.is_whitelist());
    assert!(!ign.is_none() && ign.is_ignore() && !ign.is_whitelist());
    assert!(!wl.is_none() && !wl.is_ignore() && wl.is_whitelist());
}

#[test]
fn generated_match_inner_payload() {
    let none: Match<&str> = Match::None;
    let ign: Match<&str> = Match::Ignore("grit");
    let wl: Match<&str> = Match::Whitelist("pearl");

    assert_eq!(none.inner(), None);
    assert_eq!(ign.inner(), Some(&"grit"));
    assert_eq!(wl.inner(), Some(&"pearl"));
}

#[test]
fn generated_match_invert_swaps() {
    let none: Match<u32> = Match::None;
    let wl: Match<u32> = Match::Whitelist(4);

    assert!(none.invert().is_none());
    assert!(wl.invert().is_ignore());
    let inverted = Match::Ignore(3u32).invert();
    assert!(inverted.is_whitelist());
    assert_eq!(inverted.inner(), Some(&3));
}

#[test]
fn generated_match_map_transforms_payload() {
    let ign: Match<u32> = Match::Ignore(21);
    let mapped = ign.map(|v| v * 2);
    assert!(mapped.is_ignore());
    assert_eq!(mapped.inner(), Some(&42));

    let none: Match<u32> = Match::None;
    assert!(none.map(|v| v * 2).is_none());
}

#[test]
fn generated_match_or_prefers_receiver() {
    let none: Match<u32> = Match::None;
    let ign: Match<u32> = Match::Ignore(1);
    let wl: Match<u32> = Match::Whitelist(2);

    assert!(none.or(Match::Ignore(5)).is_ignore());
    assert_eq!(ign.or(Match::Whitelist(5)).inner(), Some(&1));
    assert_eq!(wl.or(Match::Ignore(5)).inner(), Some(&2));
}

// ---------------------------------------------------------------------------
// Gitignore pattern dialect
// ---------------------------------------------------------------------------

#[test]
fn generated_gitignore_name_pattern_matches_any_depth() {
    let mut b = GitignoreBuilder::new("/plot");
    b.add_line(None, "silt.log").unwrap();
    let gi = b.build().unwrap();

    assert!(gi.matched("silt.log", false).is_ignore());
    assert!(gi.matched("furrow/silt.log", false).is_ignore());
    assert!(gi.matched("furrow/deep/silt.log", false).is_ignore());
    assert!(gi.matched("other.log", false).is_none());
}

#[test]
fn generated_gitignore_slash_prefix_anchors_to_root() {
    let mut b = GitignoreBuilder::new("/plot");
    b.add_line(None, "/topsoil.txt").unwrap();
    let gi = b.build().unwrap();

    assert!(gi.matched("topsoil.txt", false).is_ignore());
    assert!(gi.matched("bed/topsoil.txt", false).is_none());
}

#[test]
fn generated_gitignore_mid_slash_anchors_and_star_stays_in_component() {
    let mut b = GitignoreBuilder::new("/plot");
    b.add_line(None, "docs/*.tmp").unwrap();
    let gi = b.build().unwrap();

    assert!(gi.matched("docs/draft.tmp", false).is_ignore());
    // single `*` never crosses a separator
    assert!(gi.matched("docs/sub/draft.tmp", false).is_none());
    // a non-trailing slash anchors the whole pattern to the root
    assert!(gi.matched("other/docs/draft.tmp", false).is_none());
}

#[test]
fn generated_gitignore_trailing_slash_directory_only() {
    let mut b = GitignoreBuilder::new("/plot");
    b.add_line(None, "silo/").unwrap();
    let gi = b.build().unwrap();

    assert!(gi.matched("silo", true).is_ignore());
    assert!(gi.matched("barn/silo", true).is_ignore());
    // does not match a plain file of the same name
    assert!(gi.matched("silo", false).is_none());
}

#[test]
fn generated_gitignore_double_star_prefix_all_depths() {
    let mut b = GitignoreBuilder::new("/plot");
    b.add_line(None, "**/deep.txt").unwrap();
    let gi = b.build().unwrap();

    assert!(gi.matched("deep.txt", false).is_ignore());
    assert!(gi.matched("a/deep.txt", false).is_ignore());
    assert!(gi.matched("a/b/c/deep.txt", false).is_ignore());
}

#[test]
fn generated_gitignore_double_star_middle_spans_components() {
    let mut b = GitignoreBuilder::new("/plot");
    b.add_line(None, "sub/**/leaf.md").unwrap();
    let gi = b.build().unwrap();

    assert!(gi.matched("sub/leaf.md", false).is_ignore());
    assert!(gi.matched("sub/a/leaf.md", false).is_ignore());
    assert!(gi.matched("sub/a/b/leaf.md", false).is_ignore());
    assert!(gi.matched("other/leaf.md", false).is_none());
}

#[test]
fn generated_gitignore_negation_last_match_wins() {
    let mut b = GitignoreBuilder::new("/plot");
    b.add_line(None, "*.log").unwrap();
    b.add_line(None, "!keep.log").unwrap();
    let gi = b.build().unwrap();

    assert!(gi.matched("debug.log", false).is_ignore());
    assert!(gi.matched("keep.log", false).is_whitelist());
    assert!(gi.matched("src/keep.log", false).is_whitelist());
}

#[test]
fn generated_gitignore_ignore_after_whitelist_wins() {
    let mut b = GitignoreBuilder::new("/plot");
    b.add_line(None, "!keep.log").unwrap();
    b.add_line(None, "*.log").unwrap();
    let gi = b.build().unwrap();

    // the later ignore pattern decides
    assert!(gi.matched("keep.log", false).is_ignore());
    assert!(gi.matched("debug.log", false).is_ignore());
}

#[test]
fn generated_gitignore_comments_and_blanks_add_nothing() {
    let mut b = GitignoreBuilder::new("/plot");
    b.add_line(None, "# a comment").unwrap();
    b.add_line(None, "").unwrap();
    b.add_line(None, "   ").unwrap();
    let gi = b.build().unwrap();

    assert_eq!(gi.len(), 0);
    assert!(gi.is_empty());
    assert!(gi.matched("# a comment", false).is_none());
}

#[test]
fn generated_gitignore_escaped_hash_matches_literal() {
    let mut b = GitignoreBuilder::new("/plot");
    b.add_line(None, "\\#pinned").unwrap();
    let gi = b.build().unwrap();

    assert_eq!(gi.len(), 1);
    assert!(gi.matched("#pinned", false).is_ignore());
    assert!(gi.matched("pinned", false).is_none());
}

#[test]
fn generated_gitignore_trailing_space_trimmed_unless_escaped() {
    let mut b = GitignoreBuilder::new("/plot");
    b.add_line(None, "plain ").unwrap();
    b.add_line(None, "trail\\ ").unwrap();
    let gi = b.build().unwrap();

    // unescaped trailing whitespace is trimmed
    assert!(gi.matched("plain", false).is_ignore());
    assert!(gi.matched("plain ", false).is_none());
    // escaped trailing space is a literal space
    assert!(gi.matched("trail ", false).is_ignore());
    assert!(gi.matched("trail", false).is_none());
}

#[test]
fn generated_gitignore_case_insensitive_applies_to_later_lines() {
    let mut b = GitignoreBuilder::new("/plot");
    b.add_line(None, "early.txt").unwrap();
    b.case_insensitive(true).unwrap();
    b.add_line(None, "*.LATE").unwrap();
    let gi = b.build().unwrap();

    // pattern added before the toggle stays case-sensitive
    assert!(gi.matched("early.txt", false).is_ignore());
    assert!(gi.matched("EARLY.TXT", false).is_none());
    // patterns added afterward match without regard to case
    assert!(gi.matched("notes.late", false).is_ignore());
    assert!(gi.matched("notes.LaTe", false).is_ignore());
}

#[test]
fn generated_gitignore_invalid_glob_line_is_error() {
    let mut b = GitignoreBuilder::new("/plot");
    assert!(b.add_line(None, "bad[").is_err());
    // the builder stays usable after a rejected line
    b.add_line(None, "fine.txt").unwrap();
    let gi = b.build().unwrap();
    assert_eq!(gi.len(), 1);
    assert!(gi.matched("fine.txt", false).is_ignore());
}

#[test]
fn generated_gitignore_counters_and_root_path() {
    let mut b = GitignoreBuilder::new("/orchard");
    b.add_line(None, "*.pit").unwrap();
    b.add_line(None, "core/").unwrap();
    b.add_line(None, "!graft.pit").unwrap();
    let gi = b.build().unwrap();

    assert_eq!(gi.num_ignores(), 2);
    assert_eq!(gi.num_whitelists(), 1);
    assert_eq!(gi.len(), 3);
    assert!(!gi.is_empty());
    assert_eq!(gi.path(), Path::new("/orchard"));
}

#[test]
fn generated_gitignore_empty_matcher_answers_none() {
    let gi = Gitignore::empty();
    assert!(gi.is_empty());
    assert_eq!(gi.len(), 0);
    assert!(gi.matched("anything.txt", false).is_none());
    assert!(gi.matched("some/dir", true).is_none());
    assert!(gi
        .matched_path_or_any_parents(Path::new("a/b/c.txt"), false)
        .is_none());
}

#[test]
fn generated_gitignore_new_reads_file_and_roots_at_parent() {
    let t = TreeFixture::new("ginew");
    t.file("ruleset", "*.tuf\n!keep.tuf\n");

    let (gi, err) = Gitignore::new(t.path().join("ruleset"));
    assert!(err.is_none());
    assert_eq!(gi.len(), 2);
    // rooted at the file's parent directory
    assert_eq!(gi.path(), t.path());
    assert!(gi.matched("mound.tuf", false).is_ignore());
    assert!(gi.matched("keep.tuf", false).is_whitelist());
}

#[test]
fn generated_gitignore_glob_provenance_fields() {
    let t = TreeFixture::new("prov");
    t.file("srcrules", "vellum.txt\n");

    let mut b = GitignoreBuilder::new(t.path());
    assert!(b.add(t.path().join("srcrules")).is_none());
    b.add_line(None, "!quill.md").unwrap();
    b.add_line(None, "stash/").unwrap();
    let gi = b.build().unwrap();

    let src = t.path().join("srcrules");
    let m = gi.matched("vellum.txt", false);
    let g = m.inner().expect("expected a deciding pattern");
    assert_eq!(g.original(), "vellum.txt");
    assert_eq!(g.from(), Some(src.as_path()));
    assert!(!g.is_whitelist());
    assert!(!g.is_only_dir());

    let m = gi.matched("quill.md", false);
    assert!(m.is_whitelist());
    let g = m.inner().unwrap();
    assert_eq!(g.original(), "!quill.md");
    assert_eq!(g.from(), None);
    assert!(g.is_whitelist());

    let m = gi.matched("stash", true);
    let g = m.inner().unwrap();
    assert_eq!(g.original(), "stash/");
    assert!(g.is_only_dir());
}

#[test]
fn generated_gitignore_absolute_path_stripped_to_relative() {
    let mut b = GitignoreBuilder::new("/plot");
    b.add_line(None, "/topsoil.txt").unwrap();
    let gi = b.build().unwrap();

    // an absolute path under the root is stripped to its relative form
    assert!(gi.matched("/plot/topsoil.txt", false).is_ignore());
}

#[test]
fn generated_gitignore_parent_dir_rule_hits_descendants() {
    let mut b = GitignoreBuilder::new("/plot");
    b.add_line(None, "cellar/").unwrap();
    let gi = b.build().unwrap();

    // the file alone matches nothing...
    assert!(gi.matched("cellar/wine.txt", false).is_none());
    // ...but an ignored ancestor directory decides the parent-aware query
    assert!(gi
        .matched_path_or_any_parents(Path::new("cellar/wine.txt"), false)
        .is_ignore());
    assert!(gi
        .matched_path_or_any_parents(Path::new("attic/box.txt"), false)
        .is_none());
}

#[test]
fn generated_gitignore_add_unreadable_file_reports_error() {
    let t = TreeFixture::new("unread");
    let mut b = GitignoreBuilder::new(t.path());
    let err = b.add(t.path().join("missing_rules"));
    let err = err.expect("expected an error for an unreadable file");
    assert!(err.is_io());
    // the builder stays usable
    b.add_line(None, "*.ash").unwrap();
    let gi = b.build().unwrap();
    assert!(gi.matched("ember.ash", false).is_ignore());
}

#[test]
fn generated_gitignore_partial_error_for_multiple_bad_lines() {
    let t = TreeFixture::new("partial");
    t.file("badrules", "one[\ntwo[\n");
    t.file("onebad", "one[\nfine.txt\n");

    let mut b = GitignoreBuilder::new(t.path());
    let err = b.add(t.path().join("badrules")).expect("expected error");
    assert!(err.is_partial());
    assert!(!err.is_io());

    let mut b = GitignoreBuilder::new(t.path());
    let err = b.add(t.path().join("onebad")).expect("expected error");
    assert!(!err.is_partial());
    // the valid line still took effect
    let gi = b.build().unwrap();
    assert!(gi.matched("fine.txt", false).is_ignore());
}

// ---------------------------------------------------------------------------
// Override globs
// ---------------------------------------------------------------------------

#[test]
fn generated_override_empty_answers_none() {
    let ov = Override::empty();
    assert!(ov.is_empty());
    assert!(ov.matched("anything.txt", false).is_none());
    assert!(ov.matched("somedir", true).is_none());

    let built = OverrideBuilder::new("/plot").build().unwrap();
    assert!(built.is_empty());
    assert!(built.matched("anything.txt", false).is_none());
}

#[test]
fn generated_override_plain_glob_whitelists_match() {
    let mut b = OverrideBuilder::new("/plot");
    b.add("*.tin").unwrap();
    let ov = b.build().unwrap();

    assert!(ov.matched("box.tin", false).is_whitelist());
    assert!(ov.matched("shed/box.tin", false).is_whitelist());
}

#[test]
fn generated_override_unmatched_file_ignored_when_plain_glob_exists() {
    let mut b = OverrideBuilder::new("/plot");
    b.add("*.tin").unwrap();
    let ov = b.build().unwrap();

    assert!(ov.matched("readme.md", false).is_ignore());
}

#[test]
fn generated_override_unmatched_directory_none() {
    let mut b = OverrideBuilder::new("/plot");
    b.add("*.tin").unwrap();
    let ov = b.build().unwrap();

    // directories stay undecided so walkers still descend
    assert!(ov.matched("shed", true).is_none());
}

#[test]
fn generated_override_negated_glob_ignores() {
    let mut b = OverrideBuilder::new("/plot");
    b.add("*.js").unwrap();
    b.add("!*.min.js").unwrap();
    let ov = b.build().unwrap();

    assert!(ov.matched("app.js", false).is_whitelist());
    assert!(ov.matched("app.min.js", false).is_ignore());
}

#[test]
fn generated_override_only_negations_leave_unmatched_none() {
    let mut b = OverrideBuilder::new("/plot");
    b.add("!*.gz").unwrap();
    let ov = b.build().unwrap();

    assert!(ov.matched("bundle.gz", false).is_ignore());
    // with only `!` globs, an unmatched file stays undecided
    assert!(ov.matched("notes.txt", false).is_none());
}

#[test]
fn generated_override_counters_inverted_and_invalid_glob() {
    let mut b = OverrideBuilder::new("/quarry");
    b.add("*.ore").unwrap();
    b.add("!slag.ore").unwrap();
    assert!(b.add("bad[").is_err());
    let ov = b.build().unwrap();

    // inverted counting: plain globs are whitelists, `!` globs are ignores
    assert_eq!(ov.num_whitelists(), 1);
    assert_eq!(ov.num_ignores(), 1);
    assert!(!ov.is_empty());
    assert_eq!(ov.path(), Path::new("/quarry"));
}

#[test]
fn generated_override_case_insensitive_toggle() {
    let mut b = OverrideBuilder::new("/plot");
    b.case_insensitive(true).unwrap();
    b.add("*.ledger").unwrap();
    let ov = b.build().unwrap();

    assert!(ov.matched("MAIN.LEDGER", false).is_whitelist());
    assert!(ov.matched("main.ledger", false).is_whitelist());
}

// ---------------------------------------------------------------------------
// File type filters
// ---------------------------------------------------------------------------

#[test]
fn generated_types_name_validation_rules() {
    let mut b = TypesBuilder::new();
    // names must be alphanumeric (Unicode letters and numbers only)
    assert!(b.add("bad-name", "*.x").is_err());
    assert!(b.add("bad_name", "*.x").is_err());
    // the reserved word `all` is rejected
    assert!(b.add("all", "*.x").is_err());
    // a valid name works
    assert!(b.add("fine9", "*.x").is_ok());
    b.select("fine9");
    let t = b.build().unwrap();
    assert!(t.matched("thing.x", false).is_whitelist());
}

#[test]
fn generated_types_accumulate_globs_and_sorted_definitions() {
    let mut b = TypesBuilder::new();
    b.add("script", "*.sh").unwrap();
    b.add("script", "*.bash").unwrap();
    b.add("art", "*.svg").unwrap();

    let defs = b.definitions();
    let names: Vec<&str> = defs.iter().map(|d| d.name()).collect();
    // sorted by name
    assert_eq!(names, vec!["art", "script"]);
    let script = defs.iter().find(|d| d.name() == "script").unwrap();
    assert_eq!(script.globs().len(), 2);
    assert!(script.globs().contains(&"*.sh".to_string()));
    assert!(script.globs().contains(&"*.bash".to_string()));
}

#[test]
fn generated_types_add_def_name_colon_glob() {
    let mut b = TypesBuilder::new();
    b.add_def("web:*.html").unwrap();
    // the glob may contain commas
    b.add_def("tab:*.{tsv,csv}").unwrap();
    b.select("tab");
    let t = b.build().unwrap();
    assert!(t.matched("grid.tsv", false).is_whitelist());
    assert!(t.matched("grid.csv", false).is_whitelist());
    assert!(t.matched("grid.html", false).is_ignore());
}

#[test]
fn generated_types_add_def_malformed_strings_error() {
    let mut b = TypesBuilder::new();
    // wrong segment count
    assert!(b.add_def("nameonly").is_err());
    assert!(b.add_def("a:b:c:d").is_err());
    // three segments require the literal middle `include`
    assert!(b.add_def("odd:with:colon").is_err());
    // empty name or glob
    assert!(b.add_def(":*.x").is_err());
    assert!(b.add_def("name:").is_err());
    // include naming an undefined type
    assert!(b.add_def("combo:include:ghost").is_err());
    // a well-formed definition still works afterwards
    assert!(b.add_def("fine:*.ok").is_ok());
}

#[test]
fn generated_types_add_def_include_composite() {
    let mut b = TypesBuilder::new();
    b.add("md", "*.md").unwrap();
    b.add("rst", "*.rst").unwrap();
    b.add_def("prose:include:md,rst").unwrap();
    b.select("prose");
    let t = b.build().unwrap();

    assert!(t.matched("guide.md", false).is_whitelist());
    assert!(t.matched("guide.rst", false).is_whitelist());
    assert!(t.matched("guide.txt", false).is_ignore());
}

#[test]
fn generated_types_selected_matching_whitelist_unmatched_ignore() {
    let mut b = TypesBuilder::new();
    b.add("audio", "*.flac").unwrap();
    b.select("audio");
    let t = b.build().unwrap();

    assert!(t.matched("song.flac", false).is_whitelist());
    // a file matching no selected type is ignored
    assert!(t.matched("cover.png", false).is_ignore());
    // directories are always undecided
    assert!(t.matched("album", true).is_none());
}

#[test]
fn generated_types_negate_produces_ignore() {
    let mut b = TypesBuilder::new();
    b.add("audio", "*.flac").unwrap();
    b.add("junk", "*.crdownload").unwrap();
    b.select("audio");
    b.negate("junk");
    let t = b.build().unwrap();

    assert!(t.matched("song.flac", false).is_whitelist());
    assert!(t.matched("half.crdownload", false).is_ignore());
}

#[test]
fn generated_types_only_negations_leave_unmatched_none() {
    let mut b = TypesBuilder::new();
    b.add("junk", "*.bak").unwrap();
    b.negate("junk");
    let t = b.build().unwrap();

    assert!(t.matched("old.bak", false).is_ignore());
    // no positive selection: unmatched files stay undecided
    assert!(t.matched("fresh.txt", false).is_none());
}

#[test]
fn generated_types_no_selection_matches_none() {
    let mut b = TypesBuilder::new();
    b.add("audio", "*.flac").unwrap();
    let t = b.build().unwrap();

    assert_eq!(t.len(), 0);
    assert!(t.is_empty());
    assert!(t.matched("song.flac", false).is_none());
    assert!(t.matched("cover.png", false).is_none());
}

#[test]
fn generated_types_build_unknown_name_errors() {
    let mut b = TypesBuilder::new();
    b.add("known", "*.k").unwrap();
    b.select("ghost");
    assert!(b.build().is_err());

    let empty = Types::empty();
    assert_eq!(empty.len(), 0);
    assert!(empty.is_empty());
    assert!(empty.matched("x.k", false).is_none());
}

#[test]
fn generated_types_select_all_and_clear() {
    let mut b = TypesBuilder::new();
    b.add("ink", "*.ink").unwrap();
    b.add("wax", "*.wax").unwrap();
    b.select("all");
    let t = b.build().unwrap();
    assert!(t.matched("pen.ink", false).is_whitelist());
    assert!(t.matched("seal.wax", false).is_whitelist());
    assert!(t.matched("misc.txt", false).is_ignore());

    // clear removes the definition itself; other types keep working
    let mut b = TypesBuilder::new();
    b.add("ink", "*.ink").unwrap();
    b.add("wax", "*.wax").unwrap();
    b.clear("ink");
    b.select("wax");
    let t = b.build().unwrap();
    assert!(t.matched("seal.wax", false).is_whitelist());

    // a mark naming a cleared type fails the build
    let mut b = TypesBuilder::new();
    b.add("ink", "*.ink").unwrap();
    b.select("ink");
    b.clear("ink");
    assert!(b.build().is_err());
}

#[test]
fn generated_types_glob_payload_names_owning_definition() {
    let mut b = TypesBuilder::new();
    b.add("draft", "*.dft").unwrap();
    b.select("draft");
    let t = b.build().unwrap();

    let m = t.matched("plan.dft", false);
    assert!(m.is_whitelist());
    let def = m.inner().unwrap().file_type_def().expect("owning definition");
    assert_eq!(def.name(), "draft");
    assert_eq!(def.globs(), &["*.dft".to_string()]);

    // the blanket unmatched-file verdict carries no owning definition
    let m = t.matched("plan.txt", false);
    assert!(m.is_ignore());
    assert!(m.inner().unwrap().file_type_def().is_none());
}

// ---------------------------------------------------------------------------
// Serial walking
// ---------------------------------------------------------------------------

#[test]
fn generated_walk_yields_root_first_at_depth_zero() {
    let t = TreeFixture::new("rootfirst");
    t.file("gable.txt", "");
    t.dir("eaves");

    let mut it = WalkBuilder::new(t.path()).build();
    let first = it.next().unwrap().unwrap();
    assert_eq!(first.path(), t.path());
    assert_eq!(first.depth(), 0);
}

#[test]
fn generated_walk_file_root_yields_exactly_that_file() {
    let t = TreeFixture::new("fileroot");
    t.file("solo.txt", "grain");

    let entries: Vec<_> = WalkBuilder::new(t.path().join("solo.txt"))
        .build()
        .map(|r| r.unwrap())
        .collect();
    assert_eq!(entries.len(), 1);
    assert_eq!(entries[0].path(), t.path().join("solo.txt"));
    assert_eq!(entries[0].depth(), 0);
    assert!(entries[0].file_type().unwrap().is_file());
}

#[test]
fn generated_walk_nonexistent_root_yields_single_io_error() {
    let t = TreeFixture::new("noroot");
    let missing = t.path().join("not_there");

    let mut it = WalkBuilder::new(&missing).build();
    let err = match it.next() {
        Some(Err(e)) => e,
        other => panic!("expected an error item, got {:?}", other.map(|r| r.is_ok())),
    };
    assert!(err.is_io());
    assert!(err.io_error().is_some());
    assert!(!err.is_partial());
    // exactly one item
    assert!(it.next().is_none());
}

#[test]
fn generated_walk_direntry_accessors_agree() {
    let t = TreeFixture::new("entry");
    t.file("ledger/entry.txt", "abcde");

    let e = WalkBuilder::new(t.path())
        .build()
        .map(|r| r.unwrap())
        .find(|e| e.file_name() == "entry.txt")
        .expect("entry.txt must be yielded");

    assert_eq!(e.path(), t.path().join("ledger/entry.txt"));
    assert_eq!(e.depth(), 2);
    assert!(e.file_type().unwrap().is_file());
    assert_eq!(e.metadata().unwrap().len(), 5);
    assert!(!e.path_is_symlink());
    let owned = e.path().to_path_buf();
    assert_eq!(e.into_path(), owned);
}

#[test]
fn generated_walk_hidden_default_skips_dot_entries() {
    let t = TreeFixture::new("hidden");
    t.file("visible.txt", "");
    t.file(".dotfile", "");
    t.file(".attic/inside.txt", "");

    let wb = WalkBuilder::new(t.path());
    assert_eq!(
        walk_sorted(&wb, t.path()),
        names(&[".", "visible.txt"])
    );
}

#[test]
fn generated_walk_hidden_disabled_yields_dot_entries() {
    let t = TreeFixture::new("nohide");
    t.file("visible.txt", "");
    t.file(".dotfile", "");
    t.file(".attic/inside.txt", "");

    let mut wb = WalkBuilder::new(t.path());
    wb.hidden(false);
    assert_eq!(
        walk_sorted(&wb, t.path()),
        names(&[".", "visible.txt", ".dotfile", ".attic", ".attic/inside.txt"])
    );
}

#[test]
fn generated_walk_gitignore_needs_repo_by_default() {
    let t = TreeFixture::new("norepo");
    t.file(".gitignore", "*.o\n");
    t.file("main.o", "");
    t.file("main.c", "");

    // no `.git`: the .gitignore rules do not apply
    let wb = WalkBuilder::new(t.path());
    assert_eq!(
        walk_sorted(&wb, t.path()),
        names(&[".", "main.o", "main.c"])
    );
}

#[test]
fn generated_walk_gitignore_applies_inside_repo() {
    let t = TreeFixture::new("repo");
    t.dir(".git");
    t.file(".gitignore", "*.o\n");
    t.file("main.o", "");
    t.file("main.c", "");

    let wb = WalkBuilder::new(t.path());
    assert_eq!(walk_sorted(&wb, t.path()), names(&[".", "main.c"]));
}

#[test]
fn generated_walk_require_git_false_applies_everywhere() {
    let t = TreeFixture::new("nogitok");
    t.file(".gitignore", "*.o\n");
    t.file("main.o", "");
    t.file("main.c", "");

    let mut wb = WalkBuilder::new(t.path());
    wb.require_git(false);
    assert_eq!(walk_sorted(&wb, t.path()), names(&[".", "main.c"]));
}

#[test]
fn generated_walk_git_ignore_toggle_disables() {
    let t = TreeFixture::new("gitoff");
    t.dir(".git");
    t.file(".gitignore", "*.o\n");
    t.file("main.o", "");

    let mut wb = WalkBuilder::new(t.path());
    wb.git_ignore(false);
    assert_eq!(walk_sorted(&wb, t.path()), names(&[".", "main.o"]));
}

#[test]
fn generated_walk_dot_ignore_applies_without_git() {
    let t = TreeFixture::new("dotig");
    t.file(".ignore", "*.raw\n");
    t.file("shot.raw", "");
    t.file("shot.jpg", "");

    // `.ignore` needs no git repository
    let wb = WalkBuilder::new(t.path());
    assert_eq!(walk_sorted(&wb, t.path()), names(&[".", "shot.jpg"]));
}

#[test]
fn generated_walk_ignore_toggle_disables_dot_ignore() {
    let t = TreeFixture::new("dotigoff");
    t.file(".ignore", "*.raw\n");
    t.file("shot.raw", "");

    let mut wb = WalkBuilder::new(t.path());
    wb.ignore(false);
    assert_eq!(walk_sorted(&wb, t.path()), names(&[".", "shot.raw"]));
}

#[test]
fn generated_walk_git_exclude_applies_and_toggles() {
    let t = TreeFixture::new("exclude");
    t.dir(".git/info");
    t.file(".git/info/exclude", "*.bak\n");
    t.file("save.bak", "");
    t.file("save.txt", "");

    let wb = WalkBuilder::new(t.path());
    assert_eq!(walk_sorted(&wb, t.path()), names(&[".", "save.txt"]));

    let mut wb = WalkBuilder::new(t.path());
    wb.git_exclude(false);
    assert_eq!(
        walk_sorted(&wb, t.path()),
        names(&[".", "save.txt", "save.bak"])
    );
}

#[test]
fn generated_walk_custom_ignore_filename_rules_apply() {
    let t = TreeFixture::new("custom");
    t.file("rules.conf", "*.dat\n");
    t.file("blob.dat", "");
    t.file("blob.txt", "");

    let mut wb = WalkBuilder::new(t.path());
    wb.add_custom_ignore_filename("rules.conf");
    // the rule file itself is not hidden, so it is yielded; its rules apply
    assert_eq!(
        walk_sorted(&wb, t.path()),
        names(&[".", "rules.conf", "blob.txt"])
    );
}

#[test]
fn generated_walk_add_ignore_applies_to_whole_walk() {
    let t = TreeFixture::new("addig");
    t.file("side_rules", "*.swp\n");
    t.file("edit.swp", "");
    t.file("nest/deep.swp", "");
    t.file("edit.txt", "");

    let mut wb = WalkBuilder::new(t.path());
    let err = wb.add_ignore(t.path().join("side_rules"));
    assert!(err.is_none());
    assert_eq!(
        walk_sorted(&wb, t.path()),
        names(&[".", "side_rules", "edit.txt", "nest"])
    );
}

#[test]
fn generated_walk_add_ignore_unreadable_reports_error() {
    let t = TreeFixture::new("addigbad");
    t.file("kept.txt", "");

    let mut wb = WalkBuilder::new(t.path());
    let err = wb.add_ignore(t.path().join("no_such_rules"));
    let err = err.expect("expected an error for an unreadable ignore file");
    assert!(err.is_io());
    // the walk itself still works
    assert_eq!(walk_sorted(&wb, t.path()), names(&[".", "kept.txt"]));
}

#[test]
fn generated_walk_max_depth_limits_yield() {
    let t = TreeFixture::new("depth");
    t.file("a.txt", "");
    t.file("one/b.txt", "");
    t.file("one/two/c.txt", "");

    let mut wb = WalkBuilder::new(t.path());
    wb.max_depth(Some(1));
    assert_eq!(walk_sorted(&wb, t.path()), names(&[".", "a.txt", "one"]));

    let mut wb = WalkBuilder::new(t.path());
    wb.max_depth(Some(0));
    assert_eq!(walk_sorted(&wb, t.path()), names(&["."]));
}

#[test]
fn generated_walk_max_filesize_skips_large_files_only() {
    let t = TreeFixture::new("size");
    t.file("hefty.bin", &"x".repeat(600));
    t.file("light.bin", "xx");
    // a directory is never size-filtered
    t.file("hefty_dir/inner.txt", "y");

    let mut wb = WalkBuilder::new(t.path());
    wb.max_filesize(Some(100));
    assert_eq!(
        walk_sorted(&wb, t.path()),
        names(&[".", "light.bin", "hefty_dir", "hefty_dir/inner.txt"])
    );
}

#[test]
fn generated_walk_filter_entry_prunes_directory() {
    let t = TreeFixture::new("pred");
    t.file("keepme.txt", "");
    t.file("dropzone/inner.txt", "");
    t.file("dropzone/sub/deep.txt", "");

    let mut wb = WalkBuilder::new(t.path());
    wb.filter_entry(|e| e.file_name() != "dropzone");
    // the pruned directory and everything below it disappear
    assert_eq!(walk_sorted(&wb, t.path()), names(&[".", "keepme.txt"]));
}

#[test]
fn generated_walk_sort_by_file_name_orders_siblings() {
    let t = TreeFixture::new("sortname");
    t.file("pear.txt", "");
    t.file("apple.txt", "");
    t.file("quince.txt", "");

    let mut wb = WalkBuilder::new(t.path());
    wb.sort_by_file_name(|a, b| a.cmp(b));
    let order: Vec<String> = wb
        .build()
        .map(|r| rel_name(t.path(), r.unwrap().path()))
        .collect();
    // flat tree: root first, then files in comparator order
    assert_eq!(order, vec![".", "apple.txt", "pear.txt", "quince.txt"]);
}

#[test]
fn generated_walk_sort_by_file_path_orders_siblings() {
    let t = TreeFixture::new("sortpath");
    t.file("cellar.txt", "");
    t.file("attic.txt", "");
    t.file("barn.txt", "");

    let mut wb = WalkBuilder::new(t.path());
    wb.sort_by_file_path(|a, b| b.cmp(a)); // reverse order
    let order: Vec<String> = wb
        .build()
        .map(|r| rel_name(t.path(), r.unwrap().path()))
        .collect();
    assert_eq!(order, vec![".", "cellar.txt", "barn.txt", "attic.txt"]);
}

#[test]
fn generated_walk_multiple_roots_visited_in_order() {
    let t = TreeFixture::new("roots");
    t.file("east/sun.txt", "");
    t.file("west/moon.txt", "");
    let east = t.path().join("east");
    let west = t.path().join("west");

    let mut wb = WalkBuilder::new(&east);
    wb.add(&west);
    let paths: Vec<PathBuf> = wb.build().map(|r| r.unwrap().into_path()).collect();

    assert_eq!(paths[0], east);
    let east_last = paths.iter().rposition(|p| p.starts_with(&east)).unwrap();
    let west_first = paths.iter().position(|p| p.starts_with(&west)).unwrap();
    // every first-root entry comes before every second-root entry
    assert!(east_last < west_first);
    assert!(paths.contains(&east.join("sun.txt")));
    assert!(paths.contains(&west.join("moon.txt")));
}

#[test]
fn generated_walk_default_constructor_equivalent() {
    let t = TreeFixture::new("walknew");
    t.dir(".git");
    t.file(".gitignore", "*.tmp\n");
    t.file("stay.txt", "");
    t.file("gone.tmp", "");

    let mut via_new: Vec<String> = Walk::new(t.path())
        .map(|r| rel_name(t.path(), r.unwrap().path()))
        .collect();
    via_new.sort();

    let wb = WalkBuilder::new(t.path());
    assert_eq!(via_new, walk_sorted(&wb, t.path()));
    assert_eq!(via_new, names(&[".", "stay.txt"]));
}

#[test]
fn generated_walk_parents_toggle_stops_upward_discovery() {
    let t = TreeFixture::new("parents");
    t.dir(".git");
    t.file(".gitignore", "*.obj\n");
    t.file("inner/model.obj", "");
    t.file("inner/model.mtl", "");
    let inner = t.path().join("inner");

    // by default the walker consults rule files above the walk root
    let wb = WalkBuilder::new(&inner);
    assert_eq!(walk_sorted(&wb, &inner), names(&[".", "model.mtl"]));

    // parents(false) stops the upward search entirely
    let mut wb = WalkBuilder::new(&inner);
    wb.parents(false);
    assert_eq!(
        walk_sorted(&wb, &inner),
        names(&[".", "model.mtl", "model.obj"])
    );
}

#[test]
fn generated_walk_overrides_restrict_files() {
    let t = TreeFixture::new("walkover");
    t.file("app.wren", "");
    t.file("nest/tool.wren", "");
    t.file("nest/notes.md", "");

    let mut over = OverrideBuilder::new(t.path());
    over.add("*.wren").unwrap();
    let mut wb = WalkBuilder::new(t.path());
    wb.overrides(over.build().unwrap());

    // unmatched files are dropped; directories are still descended
    assert_eq!(
        walk_sorted(&wb, t.path()),
        names(&[".", "app.wren", "nest", "nest/tool.wren"])
    );
}

#[test]
fn generated_walk_types_restrict_files() {
    let t = TreeFixture::new("walktypes");
    t.file("score.abc", "");
    t.file("deep/tune.abc", "");
    t.file("deep/readme.txt", "");

    let mut tb = TypesBuilder::new();
    tb.add("music", "*.abc").unwrap();
    tb.select("music");
    let mut wb = WalkBuilder::new(t.path());
    wb.types(tb.build().unwrap());

    assert_eq!(
        walk_sorted(&wb, t.path()),
        names(&[".", "score.abc", "deep", "deep/tune.abc"])
    );
}

// ---------------------------------------------------------------------------
// Parallel walking
// ---------------------------------------------------------------------------

fn parallel_sorted(wb: &WalkBuilder, root: &Path) -> Vec<String> {
    let got: Arc<Mutex<Vec<String>>> = Arc::new(Mutex::new(Vec::new()));
    let rootbuf = root.to_path_buf();
    wb.build_parallel().run(|| {
        let got = Arc::clone(&got);
        let rootbuf = rootbuf.clone();
        Box::new(move |result| {
            let entry = result.expect("unexpected walk error");
            got.lock().unwrap().push(rel_name(&rootbuf, entry.path()));
            WalkState::Continue
        })
    });
    let mut v = got.lock().unwrap().clone();
    v.sort();
    v
}

#[test]
fn generated_parallel_delivers_full_entry_set() {
    let t = TreeFixture::new("parbasic");
    t.file("alpha.txt", "");
    t.file("grove/beta.txt", "");
    t.file("grove/inner/gamma.txt", "");

    let mut wb = WalkBuilder::new(t.path());
    wb.threads(2);
    assert_eq!(
        parallel_sorted(&wb, t.path()),
        names(&[
            ".",
            "alpha.txt",
            "grove",
            "grove/beta.txt",
            "grove/inner",
            "grove/inner/gamma.txt"
        ])
    );
}

#[test]
fn generated_parallel_skip_prevents_descent() {
    let t = TreeFixture::new("parskip");
    t.file("keep.txt", "");
    t.file("vault/secret.txt", "");

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
            if name == "vault" {
                WalkState::Skip
            } else {
                WalkState::Continue
            }
        })
    });
    let mut v = got.lock().unwrap().clone();
    v.sort();
    // the skipped directory itself was delivered; its contents were not
    assert_eq!(v, names(&[".", "keep.txt", "vault"]));
}

#[test]
fn generated_parallel_quit_stops_early() {
    let t = TreeFixture::new("parquit");
    for i in 0..12 {
        t.file(&format!("bead_{i}.txt"), "");
    }

    let counter: Arc<Mutex<usize>> = Arc::new(Mutex::new(0));
    let mut wb = WalkBuilder::new(t.path());
    wb.threads(1);
    wb.build_parallel().run(|| {
        let counter = Arc::clone(&counter);
        Box::new(move |result| {
            result.expect("unexpected walk error");
            *counter.lock().unwrap() += 1;
            WalkState::Quit
        })
    });
    let n = *counter.lock().unwrap();
    // at least the first result arrived, and the quit cut the walk short
    assert!(n >= 1, "no results delivered");
    assert!(n < 13, "quit did not stop the walk (saw {n} results)");
}
