# Stage 1 screening — fst-fullrepro-001

```
repo: BurntSushi/fst
source_path: https://github.com/BurntSushi/fst (local clone /tmp/refs/fst)
commit: 5907b47c6d84cebe154a5a63e8e8991124b0292e (master, v0.4.7, 2024-09-25)
language: rust
src_loc: 6425 (non-test lines in src/, inline #[cfg(test)] modules excluded)
test_functions: ~58 #[test] fns (raw/tests.rs 20, raw/ops.rs 13, tests/test.rs 11, node/registry/set/bytes 13) + quickcheck properties + heavy doc-test coverage
test_files: src/raw/tests.rs, src/raw/ops.rs (inline), src/raw/node.rs, src/raw/registry.rs, tests/test.rs, doc examples
dominant_test_styles: deterministic unit asserts over small key sets; quickcheck properties (excluded from oracle); no snapshots; no network
public_docs: docs.rs/fst/0.4.7 (crate root guide, set/map/raw/automaton/stream module docs with extensive examples), README
core_fact_source: one immutable finite-state-transducer byte image mapping byte keys to u64 outputs
derived_views: (1) Set membership/contains + stream; (2) Map get/lookup + key-value streams; (3) range selection (ge/gt/le/lt) on set/map/raw streams; (4) automaton search (Str/Subsequence/StartsWith/Complement/Union/Intersection) over the same image; (5) lattice set operations across multiple images (union/intersection/difference/symmetric_difference via OpBuilder); (6) raw::Fst node-level surface (get/contains_key/stream/range) + Output algebra; (7) build surface (SetBuilder/MapBuilder/raw::Builder, in-sorted-order insertion errors, memory or io::Write targets, into_inner/bytes round trip); (8) Levenshtein feature — OUT OF SCOPE (off by default)
external_deps: none at runtime with default features (utf8-ranges only behind levenshtein feature); dev-deps quickcheck/rand/memmap2/doc-comment NOT carried into the oracle
test_import_audit: clean for keepable tests — tests/test.rs uses only public fst:: paths; raw/tests.rs mixes public raw API with private helpers/quickcheck (those are excluded); no undocumented carrier modules
docs_test_alignment: aligned — docs.rs module docs demonstrate exactly the projections the tests exercise (build, query, stream, range, automaton, set ops)
contamination_note: fst@0.4.7, released 2021-11-30 (commit pinned 2024-09-25, only CI/metadata changes after 0.4.7), before training cutoff; anti-memorization via fresh key sets in generated tests
decision: keep
reason: automaton engine with an ordered-key state machine and 7 in-scope public projections of one byte image; FST construction (sorted insertion, output distribution, streaming with automata) is a real rule-engine difficulty shape that resists pattern-matching
risks: upstream #[test] volume is modest, so the oracle leans generated (ropey precedent); must avoid asserting the on-disk byte format (implementation detail) except size/round-trip invariants; u64 output algebra edge cases (0 as identity) need careful spec language
scope_plan: N/A (6425 LOC, <300 test fns; levenshtein feature and fst-bin/regex companion crates excluded)
```

Difficulty shapes (candidate-selector heuristic): equivalence judgement
(automaton Complement/Intersection/Union agreement with brute-force set
algebra); reimplementation of a format rule (byte-lexicographic key order
enforced at build time with typed errors; last-duplicate-wins for map
inserts across unioned streams via IndexedValue); integration spanning ≥3
projections (build → range stream → automaton filter → set-op lattice on
the same image). Typical usage composes builder + container + streamer
(+ automaton), ≥3 cooperating objects.

Toolchain check: edition 2018, no MSRV pin, zero default-feature runtime
deps; `cargo build` on sandbox rustc 1.83 succeeds at the pinned commit.
