# Stage 1 screening — ignore-fullrepro-001

repo: BurntSushi/ripgrep (workspace member crates/ignore)
source_path: https://github.com/BurntSushi/ripgrep (local clone /tmp/refs/ripgrep)
commit: ac02f54c892cc22cf32344600360a911537b2a27 (tag ignore-0.4.23)
src_loc: 4808 non-test (6241 total in crates/ignore/src minus 1433 lines of in-file #[cfg(test)] mods)
test_functions: 61 (56 in-crate mods: dir.rs 20, walk.rs 15, gitignore.rs 9, overrides.rs 9, types.rs 2, default_types.rs 1; 5 external in tests/gitignore_matched_path_or_any_parents_tests.rs driven by a 200+-pattern fixture file)
test_files: in-crate mods + tests/gitignore_matched_path_or_any_parents_tests.rs (+ .gitignore fixture)
dominant_test_styles: unit through builders + matcher queries; walker tests build temp trees and compare collected paths
public_docs: docs.rs/ignore 0.4.23 (crate root, gitignore/overrides/types/walk module and item docs), ripgrep GUIDE (gitignore semantics), git-scm gitignore format description
core_fact_source: one ignore-rule stack (gitignore-format patterns with source-precedence: overrides > custom ignore files > .ignore > per-dir .gitignore chain > global/exclude, plus file-type filters and hidden-file rule)
derived_views: (1) Gitignore/GitignoreBuilder matcher queries (matched, matched_path_or_any_parents, Match enum with Ignore/Whitelist/None and glob provenance); (2) OverrideBuilder/Override inverted-precedence matcher; (3) TypesBuilder/Types selection matcher (custom defs, select/negate); (4) WalkBuilder serial directory walker as the same rules applied to a real file tree (hidden, ignore-file toggles, custom ignore filenames, max_depth, max_filesize, filter_entry, sort, require_git); (5) WalkBuilder::build_parallel with WalkState; (6) DirEntry/Error surface
external_deps: globset (same workspace; from crates.io for candidates), walkdir, same-file, crossbeam-deque, log, regex-automata via globset — all pure crates, no services; builds clean on cargo 1.83 (globset 0.4.15 via path); registry lock must pin globset to a pre-edition2024 0.4.x if latest has migrated
test_import_audit: in-crate mods (structurally unavailable to an external oracle) plus one external file importing only public paths but reading a fixture from tests/ — generated-only oracle expected, upstream as behavioral checklist
docs_test_alignment: aligned — docs.rs + gitignore format doc describe exactly the matcher/walker behavior the tests exercise
contamination_note: ignore@0.4.23, released 2024; ripgrep is extremely well known but the oracle uses fresh fixture trees/patterns and checker-style assertions
decision: keep
reason: a precedence rule engine (last-match-wins within a file, source-rank across files, negation/whitelisting, dir-only and anchoring rules) projected through two independent surfaces — pure matcher queries and real directory walks — with library-specific contracts (require_git gating, .ignore vs .gitignore rank, override inversion, type selection) that resist textbook pattern-matching.
risks: filesystem-based tests need temp trees (kept hermetic via per-test unique dirs under std temp dir); global gitignore/git-config env leakage (mitigation: oracle always disables git_global or sets explicit HOME-independent config; spec scopes global lookup out); parallel walker nondeterminism (mitigation: collect + sort); symlink semantics platform-specific (scoped out)
scope_plan: target_subdomain = Gitignore/GitignoreBuilder + Override + Types (custom definitions only; default table out of scope) + WalkBuilder serial & parallel core toggles + DirEntry/Match/Error surface; scope out: follow_links/symlinks, same_file_system, standard-stream filtering, global gitignore via git config, default type table contents; expected_oracle_max = 130

Difficulty shapes (selection rationale): language-rule reimplementation (the gitignore pattern dialect: anchoring, dir-only trailing slash, `**` handling, negation, escaping — reimplemented, not called into); precedence/equivalence judgement (Match::Ignore vs Whitelist vs None where a false whitelist is as wrong as a false ignore); integration tests spanning >=3 projections (build rule stack -> matcher query agreement -> actual walk output agreement on one tree).
