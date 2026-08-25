# Screening evidence — textwrap-fullrepro-001

repo: mgeisler/textwrap
source_path: https://github.com/mgeisler/textwrap (local pinned checkout at /tmp/refs/textwrap)
commit: 4770e55af425a0cffb9ad8496599d2a1a4f5ed14 (tag 0.16.2)
src_loc: 3183 non-test (4639 total in src/, inline #[cfg(test)] modules stripped)
test_functions: 137 (131 inline unit + 6 in tests/indent.rs; tests/version-numbers.rs is release tooling)
test_files: inline modules in src/{wrap,fill,refill,indentation,word_splitters,word_separators,core,columns,line_ending,options,wrap_algorithms,wrap_algorithms/optimal_fit}.rs + tests/indent.rs
dominant_test_styles: unit assertions on produced line vectors/strings; a few property-ish loops; no snapshots, no network
public_docs: docs.rs/textwrap/0.16.2 (crate root guide with algorithm walk-through, Options, wrap/fill/refill/unfill, core module docs for Word/Fragment/break_words/display_width, wrap_algorithms docs incl. Penalties fields, word_separators/word_splitters docs, LineEnding, indent/dedent)
core_fact_source: one wrapping configuration (width per line, indents, line ending, break_words flag, word separator, word splitter, wrap algorithm with penalties) applied to input text
derived_views: (1) wrap -> Vec<Cow<str>> of lines; (2) fill/fill_inplace -> single String; (3) refill/unfill -> prefix inference + rewrap round trip; (4) wrap_columns -> multi-column layout; (5) indent/dedent -> prefix algebra; (6) core layer: find_words/split_words/break_words/display_width fragment pipeline; (7) wrap_algorithms layer: wrap_first_fit / wrap_optimal_fit + Penalties over any Fragment type; (8) extension points: Custom separator/splitter/algorithm function variants
external_deps: unicode-linebreak 0.1.5, unicode-width 0.2, smawk 0.3.2 (default features; all build on rustc 1.83 — verified by cargo build of the checkout). Feature-gated hyphenation and terminal_size scoped out; dev-deps (unic-emoji-char, version-sync, termion) not carried
test_import_audit: clean for public behavior — inline modules use `use super::*` which reaches private items in a few files (wrap.rs uses private wrap_single_line in 3 tests; core.rs tests private WordSeparator internals); those tests are excluded per Q1, the rest assert public fn outputs
docs_test_alignment: aligned — docs.rs documents exactly the projections the tests exercise (line vectors per width, indent handling, break_words, optimal-fit penalties, splitter behavior)
contamination_note: textwrap@0.16.2, released 2025-03-03, before training cutoff; crate is widely known — anti-memorization via fresh fixture texts and non-doc widths/penalty values in generated tests
decision: keep
reason: two genuinely different wrapping algorithms (greedy first-fit vs optimal-fit DP over SMAWK with a documented penalty model) behind one configuration engine with three trait-like extension points and a prefix-inference inverse (unfill/refill) — deep behavior with 8 public projections of one fact source
risks: marginal LOC (3183, just above gate); crate is popular so API recall is likely (mitigated: oracle asserts produced line breaks on fresh texts, incl. optimal-fit penalty interactions that cannot be recalled without implementing the DP); display-width and line-break facts live in unicode-width/unicode-linebreak (allowed as dependencies, spec pins default features); fill_inplace has subtly different behavior (no indent support) that must be spec'd precisely
scope_plan: N/A (3183 LOC, 137 test functions — inside limits; hyphenation + terminal_size features excluded)

Difficulty shapes (candidate-selector heuristic): reimplementation of a
format rule (optimal-fit penalty function: overflow/hyphen/last-line short
penalties combined over squared gaps; unfill's indent-prefix inference
incl. bullet continuation rules); equivalence judgement (refill must
preserve the inferred prefixes exactly while rewrapping); integration
spanning ≥3 projections (Options + separator + splitter + algorithm feed
wrap/fill/refill/wrap_columns over one text). Typical usage composes
Options + WordSeparator + WordSplitter + WrapAlgorithm (+ Penalties),
≥3 cooperating objects.

Toolchain check: `rust-version = "1.70"`, edition 2021; default-feature
deps unicode-linebreak 0.1.5 / unicode-width 0.2 / smawk 0.3.2 build on
sandbox rustc 1.83 (verified via cargo build of the checkout).
