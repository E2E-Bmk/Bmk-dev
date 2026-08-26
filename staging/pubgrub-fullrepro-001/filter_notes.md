# Stage 1 screening — pubgrub-fullrepro-001

repo: pubgrub-rs/pubgrub
source_path: https://github.com/pubgrub-rs/pubgrub (local clone /tmp/refs/pubgrub)
commit: 086d70bb1940c52d344332de4fdbfccf44151b4b (tag v0.3.0, released 2025-02-12)
src_loc: 4228 (src/ of the pubgrub crate; the re-exported Ranges type lives in
the sibling version-ranges crate, 1459 LOC, consumed through pubgrub's public
re-export only)
test_functions: 32 in-crate/external for pubgrub (6 tests/examples.rs,
3 tests/tests.rs, 12 tests/proptest.rs incl. property loops, 11 unit tests in
src/{term,internal}), plus 31 in version-ranges (out of crate scope)
test_files: tests/{examples.rs, tests.rs, proptest.rs, sat_dependency_provider.rs} + 7 examples/
dominant_test_styles: scenario tests against OfflineDependencyProvider
(resolve → exact selected-version maps), property-based solver validation via a
SAT helper (varisat), doc-example error-report string checks in examples/
public_docs: docs.rs/pubgrub 0.3.0 (crate-level solver guide, report module
docs with phrasing templates, DependencyProvider trait contract,
OfflineDependencyProvider, SemanticVersion), docs.rs/version-ranges 0.1.1
(Ranges algebra laws and normalized-form Display), pubgrub-rs guide
(pubgrub-rs-guide.netlify.app) covering the algorithm and error reporting
core_fact_source: one dependency universe — a map (package, version) →
constraints, held by a DependencyProvider; the solver state (partial solution,
incompatibility store) is derived from it
derived_views: (1) resolve — SelectedDependencies map satisfying every
constraint; (2) failure — PubGrubError::NoSolution carrying a DerivationTree
(Derived/External nodes) that proves the conflict; (3) DefaultStringReporter —
deterministic English rendering of that tree, plus collapse_no_versions and
packages() projections; (4) Ranges algebra — union/intersection/complement/
contains with canonical normalized segments and Display; (5) SemanticVersion —
parse/Display/ordering/bump arithmetic feeding every other view
external_deps: indexmap, priority-queue, rustc-hash, smallvec, log, thiserror
(all crates.io, no I/O); serde optional and out of scope; dev-only proptest/
varisat/ron discarded with the property suite
test_import_audit: clean — external tests use only pubgrub::{...} public paths;
tests/sat_dependency_provider.rs is a helper module (varisat-backed) not a test
carrier of private symbols; in-crate unit tests use super:: on internal modules
(not retainable, rewrite as public-surface tests)
docs_test_alignment: aligned — docs and tests both exercise
provider→resolve→selected-map / derivation-tree→report projections; report
phrasing appears verbatim in module docs and examples
contamination_note: pubgrub@0.3.0, released 2025-02; the PubGrub algorithm is
publicly documented (dart pub, uv's fork) and upstream examples reuse the dart
documentation scenarios (menu/dropdown packages) — memorization-prone; oracle
uses freshly named packages and freshly constructed universes
decision: keep
reason: a conflict-driven version solver (unit propagation over incompatibility
sets, conflict resolution with prior-cause merging, backtracking to decision
levels) whose failure proof is itself a public data structure with a documented
English rendering — algorithmic reimplementation plus an equivalence-heavy
range algebra, projected through ≥4 public surfaces.
risks: derivation-tree shape and report text depend on exploration order — the
spec pins OfflineDependencyProvider's documented strategy (highest version
first; prioritize by fewest-matching-versions with conflict-count tiebreak) and
the oracle asserts tree/report equality only on small linear/branching
universes probe-verified against the reference, preferring selected-map and
semantic assertions elsewhere; multiple-valid-solution universes avoided or
asserted semantically; edition2024 on 0.3.1+ forces the pin =0.3.0 for the
cargo 1.83 scorer toolchain
scope_plan: N/A (4228 LOC, 32 test functions)

Difficulty shapes (selection rationale): reimplementation of an algorithm
rather than a call into it (CDCL-style unit propagation, prior-cause conflict
resolution, decision-level backtracking); equivalence judgement (Ranges
normalization — distinct constructions must compare equal and render one
canonical Display); a lazily discovered constraint graph (incompatibilities
are derived on demand from provider callbacks; the derivation tree records the
proof DAG); integration tests spanning ≥3 projections (universe → solve →
selected map, or → derivation tree → collapse/packages → report text).
