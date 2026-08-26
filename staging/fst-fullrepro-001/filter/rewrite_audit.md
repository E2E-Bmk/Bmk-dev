# Rewrite audit — fst-fullrepro-001

Upstream v0.4.7 carries 11 integration-style tests in `tests/test.rs`,
~58 test functions in `src/raw/tests.rs` (many expanded from
`test_set!`/`test_map!`/`test_range!` macros), a handful of inline tests
in `src/raw/{ops,node,registry,counting_writer}.rs`, `src/set.rs`,
`src/bytes.rs`, plus doc-tests. The oracle is **generated-only**: 105
fresh test functions (68 atomic, 37 integration) written against the
spec, with expected values verified by running the pinned reference
(probe binary + full suite run). No upstream function was kept verbatim.

## Why generated-only

1. **Private-surface reliance**: `src/raw/tests.rs` builds fixtures
   through the crate-private `fst_map`/`fst_set`/`fst_inputstrs` helpers
   and asserts node/state details (`fst_set_100000` checks image size
   against `node.rs` internals; `one_vec_multiple_fsts` reads
   `as_slice` offsets). `src/raw/{node,registry,counting_writer}.rs`
   tests are module-private. Every such test fails Q1.
2. **Out-of-scope features**: `tests/test.rs` opens with two
   `levenshtein` tests behind the `levenshtein` feature, which the spec
   scopes out (Non-Goals); `invalid_version*` tests craft images through
   private constants. Excluded.
3. **Sparse keepable core**: the remaining public-path tests
   (`complement_small`, `startswith_small`, `intersection_small`,
   `union_small`, `str`, `subsequence`, `bytes_written`, `get_key_*`,
   range macros) cover perhaps two dozen behaviors — well under the
   60-test floor — so Track B generation was required regardless; the
   generated suite subsumes each of those behaviors with fresh data
   (see spec_test_map.md).
4. **Anti-memorization**: upstream fixtures (`fruit1..4`, `a..z` pairs,
   the `words-10000` file) circulate in public forks. All oracle
   fixtures are fresh vocabularies (minerals, elements, herbs, repo
   paths) with expected values recomputed on the reference.

## Upstream disposition by file

| upstream file | functions | disposition |
|---------------|-----------|-------------|
| `tests/test.rs` | 11 | 2 levenshtein (feature scoped out), 1 `implements_default` (shape-only), 8 public-path behaviors re-expressed with fresh fixtures in `atomic`/`integration::search`/`integration::lattice` |
| `src/raw/tests.rs` | ~58 | private fixture helpers throughout; behaviors (ordering errors, range bounds, get_key, bytes_written, 100k-scale builds) re-expressed through public builders; scale tests replaced by deterministic small fixtures |
| `src/raw/ops.rs` tests | 13 | private `fst_map`/`fst_set` construction; op semantics re-expressed in `integration::lattice` incl. 3-stream difference/symmetric-difference and IndexedValue provenance |
| `src/raw/{node,registry,counting_writer}.rs` tests | 12 | compressed-node internals — excluded (spec Non-Goals: no node-level introspection) |
| `src/set.rs`, `src/bytes.rs` tests | 2 | debug/format internals — excluded |
| doc-tests | ~60 | served as behavioral checklist for generation; not imported |

## Fairness notes

- No test asserts image byte layout beyond equality of images built from
  identical input through different construction paths (spec Cross-View
  Invariant 6) and round-trip stability — never against hardcoded bytes.
- No test asserts `Display` wording, checksum values, or `raw::VERSION`'s
  numeric value; error assertions match variants and payload fields the
  spec's Error Semantics table declares. Matches carry wildcard arms
  (the spec reserves enum growth).
- `Output::sub` underflow is asserted via `catch_unwind` after a positive
  subtraction check, so a stub that panics everywhere still fails.
- One spec_gap patch was routed during oracle work: key-only duplicate
  insertion (`SetBuilder::insert`, `raw::Builder::add`, `Set::from_iter`)
  is a silent no-op, while value-carrying insertion fails with
  `DuplicateKey` — confirmed by probe against the reference; grounded in
  upstream rustdoc, not motivated by a failing assertion.
- Static dummy audit: every test calls into `fst` and asserts produced
  values or exact error payloads; a stub crate panicking with
  `unimplemented!()` fails all 105 (no `#[should_panic]` tests, no
  shape-only tests).
