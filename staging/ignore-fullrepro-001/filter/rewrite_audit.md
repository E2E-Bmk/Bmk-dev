# Rewrite Audit — ignore-fullrepro-001

Upstream commit: BurntSushi/ripgrep @ ac02f54c892cc22cf32344600360a911537b2a27
(tag ignore-0.4.23), workspace member `crates/ignore`.
Upstream test inventory: 61 test functions — 56 in-crate `#[cfg(test)]` mods
(dir.rs 20, walk.rs 15, gitignore.rs 9, overrides.rs 9, types.rs 2,
default_types.rs 1) and 5 external in
`tests/gitignore_matched_path_or_any_parents_tests.rs`.

## Why the oracle is generated-only

1. **In-crate unit tests are structurally unavailable.** All 56 in-crate
   functions import through `super::`/`crate::` paths and the private test
   helper `crate::tests::TempDir`. An external oracle crate cannot include
   them. Beyond structure:
   - `dir.rs` (20) tests the *private* `Ignore`/`IgnoreBuilder` module
     (`mod dir;` — never exported), asserting on the internal per-directory
     matcher chain directly. Out of scope by construction.
   - `walk.rs` (15) uses the private `TempDir`, a `normal_path` helper, and
     several symlink/`same_file_system` tests the spec's Non-Goals exclude.
     In-scope intent (hidden toggle, max_depth, ignore-file discovery,
     parallel collection) is re-expressed with fresh trees.
   - `gitignore.rs` (9) uses a private `gi_from_str` constructor and partly
     targets `gitconfig_excludes_path` parsing (global git config — scoped
     out). In-scope dialect intent re-expressed.
   - `overrides.rs` (9) and `types.rs` (2) import via `super::`; intent
     fully re-expressed through the public builders.
   - `default_types.rs` (1) asserts the default type table is sorted —
     the default table is scoped out (spec covers custom definitions only).
2. **The one external file cannot be kept.** It imports only public paths
   (`ignore::gitignore::{Gitignore, GitignoreBuilder}`) but:
   - reads a 200+-pattern fixture from `tests/…​.gitignore` via a relative
     path (mechanical pre-filter rule 6: fixture-file dependency; shipping
     the verbatim upstream fixture is also maximally memorization-prone);
   - `test_path_should_be_under_root` is `#[should_panic(expected = …)]` on
     exact panic message text (Q1 violation);
   - the remaining four are checklist walks over the fixture. The behavioral
     intent — `matched_path_or_any_parents` verdicts for files under ignored
     parent directories — is re-expressed with fresh patterns.
3. **Anti-memorization.** ripgrep is among the most-cloned Rust projects.
   All oracle fixtures (patterns, tree shapes, file names) are freshly
   authored with different vocabularies and assertion angles.

Decision: `oracle_source: generated_only`. Upstream in-scope tests serve as
a behavioral checklist; every oracle test is authored fresh against the spec
and validated by executing the pinned reference.

## Per-file disposition

| file | fns | disposition | reason |
|---|---|---|---|
| src/dir.rs tests | 20 | discard | private `Ignore` module + `crate::tests::TempDir`; chain intent re-expressed via WalkBuilder walks |
| src/walk.rs tests | 15 | discard, re-express in-scope intent | private TempDir/helpers; symlink + same_file_system fns out of scope; toggles re-expressed with fresh trees |
| src/gitignore.rs tests | 9 | discard, re-express in-scope intent | private `gi_from_str`; global git-config fns out of scope; dialect intent re-expressed |
| src/overrides.rs tests | 9 | discard, re-express in-scope intent | `super::` imports; intent re-expressed through OverrideBuilder |
| src/types.rs tests | 2 | discard, re-express in-scope intent | `super::` imports; intent re-expressed through TypesBuilder custom defs |
| src/default_types.rs tests | 1 | discard | default type table out of scope |
| tests/gitignore_matched_path_or_any_parents_tests.rs | 5 | discard, re-express in-scope intent | upstream fixture file dependency + should_panic message text; parent-dir verdict intent re-expressed with fresh patterns |

functions_in_scope: 61
functions_kept: 0 (generated-only)
functions_excluded: 61

## Dummy-passable patterns avoided in generation

- `Match::None` assertions are always paired with positive `Ignore`/
  `Whitelist` siblings on the same matcher, so a stub returning `None`
  everywhere cannot collect points disproportionately.
- Whitelist tests assert `is_whitelist()` (a positive produced verdict),
  never merely `!is_ignore()`.
- Walk tests assert the exact sorted set of yielded paths (presence and
  absence together), never just "some entries were yielded".
- Error tests assert the error variant/partiality plus a positive sibling
  behavior (e.g. builder still usable), never bare `is_err()`.
- No test asserts Debug/Display output, exact error message text, or
  glob-compilation internals.
