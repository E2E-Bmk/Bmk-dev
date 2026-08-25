# Rewrite Audit — textwrap-fullrepro-001

Upstream commit: mgeisler/textwrap @ 4770e55af425a0cffb9ad8496599d2a1a4f5ed14 (v0.16.2)
Upstream test inventory: 137 test functions (127 in-crate `#[cfg(test)]` mods, 10 external under `tests/`).

## Why the oracle is generated-only

1. **In-crate unit tests are structurally unavailable.** 127 of 137 upstream
   tests live in `#[cfg(test)]` modules inside `src/`. They compile as part of
   the crate itself and cannot be imported by an external oracle that scores a
   candidate through `[patch.crates-io]`. They cannot be "kept" in any form;
   only their behavioral intent can be re-expressed externally.
2. **Private-surface reliance in the unit mods.** `core.rs` tests call
   `pub(crate) skip_ansi_escape_sequence` directly; `wrap.rs` tests reach
   `wrap_single_line`/`wrap_single_line_slow_path`; `word_separators.rs`
   tests use an internal emoji-property helper. These behaviors are
   re-expressed through the public surface (`display_width`, `wrap`,
   `find_words`) instead.
3. **Out-of-scope features.** Tests behind `hyphenation` (dictionary
   splitting) and `terminal_size` cfg gates test features the spec scopes
   out. `tests/version-numbers.rs` (4 fns) asserts version-string consistency
   between Cargo.toml and docs — an environment artifact, excluded.
4. **Anti-memorization.** `tests/indent.rs` (6 fns) is public-API clean but
   ports Python-stdlib fixtures ("Hi.\nThis is a test.\nTesting.") that are
   memorization-prone; the roundtrip behaviors are re-expressed with fresh
   vocabulary and the same assertions re-derived by running the reference.

Track B early trigger applies: after rewrite attempts, 0 upstream files are
keepable as-is (in-crate mods structurally excluded; `tests/indent.rs`
re-expressed; `tests/version-numbers.rs` excluded).

## Per-file disposition

| Upstream file | Fns | Disposition |
|---|---|---|
| src/wrap.rs tests | 45 | behaviors re-expressed via public `wrap`/`fill` (whitespace discipline, indents, break_words, Cow, widths); `wrap_single_line*` internals dropped |
| src/refill.rs tests | 20 | behaviors re-expressed (unfill inference matrix, refill line-ending conversion) with fresh text |
| src/fill.rs tests | 18 | behaviors re-expressed (fill joining, fill_inplace last-space rule, no-break rule) |
| src/indentation.rs tests | 13 | behaviors re-expressed (indent trimmed-prefix rule, dedent common-prefix, ws-only lines) |
| tests/indent.rs | 6 | public-API clean; roundtrip behaviors re-expressed with fresh vocabulary |
| src/word_splitters.rs tests | 6 | behaviors re-expressed (split_points alphanumeric rule, split_words penalties) |
| src/core.rs tests | 6 | `skip_ansi_escape_sequence` unit test dropped (pub(crate)); width/break behaviors re-expressed via `display_width`/`break_words` |
| src/columns.rs tests | 6 | behaviors re-expressed (arithmetic, remainder padding, zero-column panic via catch_unwind with positive check first) |
| src/word_separators.rs tests | 5 | behaviors re-expressed (AsciiSpace runs, UnicodeBreakProperties divergences, word joiner) |
| tests/version-numbers.rs | 4 | excluded — version-string consistency, environment artifact |
| src/wrap_algorithms/optimal_fit.rs tests | 3 | behaviors re-expressed (overflow error, penalty model effects) |
| src/line_ending.rs tests | 3 | `NonEmptyLines` internal iterator tests dropped; `as_str` re-expressed |
| src/wrap_algorithms.rs tests | 1 | re-expressed (usize-width wrap on Word slices) |
| src/options.rs tests | 1 | re-expressed (defaults equality) |

## Fairness notes

- All expected values in generated tests were derived by executing the pinned
  reference (probe program under /tmp/twprobe), not by inference from source.
- No assertions on `Debug`/`Display` strings, no exact error message text;
  `OverflowError` is checked by type equality (`PartialEq`) only.
- The zero-column `wrap_columns` panic test uses `std::panic::catch_unwind`
  with a positive-direction check first, so a dummy that panics everywhere
  does not pass it.
- Cow borrowing tests assert `matches!(.., Cow::Borrowed(..))` — this is
  spec-stated behavior ("Borrowing" subsection), not an internal detail.
- Fresh fixture vocabulary throughout (kestrel/bramble/otter families);
  no upstream doctest sentences reused.
- Unicode assertions restricted to spec-stated behaviors: emoji/CJK
  double-width, combining-accent zero width, ANSI CSI/OSC skipping, no
  hyphen-minus break, U+2060 suppression.
