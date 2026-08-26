# Stage 1 screening — indexmap-fullrepro-001

repo: indexmap-rs/indexmap
source_path: https://github.com/indexmap-rs/indexmap (local pin /tmp/refs/indexmap)
commit: 42e57a395b939292c08d32a317bae7bec3b7b5d8 (tag 2.7.1, released
  2025-01-19; chosen over 2.9.0 to keep the surface free of the
  get_disjoint_mut family and the *_with_default! macros, and to match the
  indexmap 2.7.1 pin already used transitively by prior packets)
language: rust
src_loc: 8085 core (src/ excluding the optional-dependency adapters
  rayon/{map,set}.rs, serde.rs, serde_seq.rs, borsh.rs, arbitrary.rs and the
  inline tests.rs modules)
test_functions: 72 (35 inline in src/map/tests.rs, 30 inline in
  src/set/tests.rs, quickcheck harness in tests/quick.rs (~20 properties in
  one macro-driven #[test] block), 6 across tests/tests.rs,
  tests/equivalent_trait.rs, tests/macros_full_path.rs)
test_files: src/map/tests.rs, src/set/tests.rs, tests/{quick,tests,
  equivalent_trait,macros_full_path}.rs
dominant_test_styles: inline unit tests over crate internals (use super::*),
  quickcheck property loops comparing against HashMap/Vec models,
  a few doc-style external API tests
public_docs: docs.rs/indexmap 2.9.0 (crate root, IndexMap/IndexSet method
  docs with per-method order semantics, map::Entry/VacantEntry/OccupiedEntry,
  map::Slice / set::Slice, macros indexmap!/indexset!), README
core_fact_source: one ordered sequence of key-value pairs (map) / values
  (set) with a hash index over the keys — every operation is defined by how
  it reads or rewrites that sequence and its index positions
derived_views:
  - key-hash view: get/contains_key/remove-by-key via Equivalent lookups
  - index view: get_index/get_index_of/first/last/swap_indices/move_index
  - slice view: as_slice/get_range/Slice binary_search/partition_point
  - order-rewrite engine: swap_remove vs shift_remove, insert_before /
    shift_insert, sort families (stable/unstable/by-key), reverse, truncate,
    split_off, drain, retain (order-preserving)
  - entry state machine: Entry::Occupied/Vacant, or_insert*, and_modify,
    index() before and after insertion
  - set algebra view: intersection/union/difference/symmetric_difference
    iteration-order laws, subset/superset predicates, BitAnd/BitOr/BitXor/Sub
    operators producing new sets with documented order
  - equivalence view: == on maps/sets ignores order while slice comparisons
    and Ord on slices are order-sensitive
external_deps: hashbrown 0.15 (internal table; pin 0.15.5 for cargo 1.83 as
  in prior packets), equivalent 1.0 (public trait re-export). Optional serde /
  rayon / borsh / arbitrary / quickcheck surfaces are out of scope (default
  features = std only).
test_import_audit: HIGH_RISK for direct reuse — the two dominant test modules
  are inline #[cfg(test)] files compiled into the crate (use super::*,
  reaching non-public internals such as core table state), and tests/quick.rs
  is quickcheck-driven with fnv/itertools dev-dependencies. Handled as
  generated_only in Stage 3 (same disposition as rstar/governor):
  upstream tests serve as a behavior checklist.
docs_test_alignment: aligned — docs.rs states per-method order semantics
  (which operations preserve order, which perturb it and how) and the tests
  exercise exactly those observable sequences.
contamination_note: indexmap@2.7.1, released 2025-01-19; widely-known API
  relative to training cutoff (before/unknown). Same contamination posture as
  petgraph/rust-decimal in this packet series: the assessed surface is exact
  order/index bookkeeping laws, not API recall.
decision: keep
reason: an order-preserving map/set is a rule engine over one shared fact
  source (entry sequence + hash index) with six public projections; the
  swap/shift/move/sort order laws and the order-insensitive-equality vs
  order-sensitive-slice split are exactly the equivalence-judgement and
  rule-reimplementation difficulty shapes.
risks:
  - API breadth: the full surface (incl. MutableKeys, RawEntry v1, GetDisjointMut)
    would balloon the spec; scope to the core map/set/slice/entry/macros
    surface and name the exclusions in Non-Goals.
  - saturation: models know the IndexMap API; difficulty must come from exact
    order bookkeeping under mixed operation sequences (probe-pinned), not
    from API existence.
  - capacity/allocation observables are implementation details; keep
    capacity() out of the oracle except where docs pin it (with_capacity
    lower bound is not contractual — exclude).
difficulty_shapes: equivalence judgement (== ignores order; slices and Ord
  do not); rule reimplementation (swap_remove back-fill law, shift_remove
  closure law, move_index rotation, insert_before index arithmetic, set
  algebra iteration order by operand); multi-projection integration (one
  mutation sequence checked through key view + index view + slice view +
  equality view).
scope_plan: N/A (src_loc < 15000 after feature-adapters exclusion;
  test_functions 102 < 300). Oracle targeted at the core two-container
  surface; serde/rayon/borsh/arbitrary/raw-entry/MutableKeys excluded.
