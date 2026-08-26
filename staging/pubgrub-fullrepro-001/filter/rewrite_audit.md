# Rewrite audit — pubgrub-fullrepro-001

Upstream test surface at v0.3.0 (086d70b): 4 external test files + in-crate
unit tests in the pubgrub crate, plus the version-ranges sibling crate's
in-crate tests (out of target-crate scope, behaviors reachable through the
`pubgrub::Ranges` re-export).

Decision: **generated_only** oracle. Every upstream file is discarded as a
carrier; behavioral intents are re-expressed as freshly authored tests with
new package vocabulary and new universes, expected values verified by running
the pinned reference (probe binary, three rounds).

## Per-file disposition

| file | fns | disposition | reason |
|---|---|---|---|
| tests/examples.rs | 6 | discard, re-express | public-API-only, but the universes are verbatim from the published solver documentation scenarios (menu/dropdown, a/b/c holes) — memorization-prone; file-level `init_log` helper drags the `log`/`env_logger` dev-deps into the carrier. Intents kept: chain solve, conflict avoidance during decision making, conflict resolution with backtracking, partial-satisfier conflict, double decision choices, holes report (raw + collapsed report strings, packages() census) |
| tests/tests.rs | 3 | discard, re-express | intents kept with fresh vocabulary: repeated-run determinism, unsatisfiable empty-range dependency (both direct and transitive), self-dependency solvable/unsolvable pair |
| tests/proptest.rs | 12 | discard | property-based (proptest strategies over random registries) checked against a varisat SAT model — both deps out of scope, assertions non-deterministic by construction; the one deterministic fn (`should_cancel_can_panic`) verifies panic propagation through `should_cancel`, a panic-based contract the spec does not declare |
| tests/sat_dependency_provider.rs | 0 | discard | helper module (varisat SAT encoder), not a test carrier |
| src/term.rs unit tests | 6 | discard | proptests over `pub(crate)` Term methods (`relation_with`, `satisfied_by`, `is_disjoint`, `subset_of`, `union` as crate-internal ops) — private surface; the public Term contract (variants, Display, Eq/Clone) is covered by generated tests |
| src/internal/incompatibility.rs unit tests | 2 | discard | private module |
| src/internal/small_vec.rs unit tests | 2 | discard | private data structure |
| src/version.rs unit test | 1 | discard, re-express | `from_str_for_semantic_version` asserts public parse-error payloads — intent kept with fresh version strings |
| version-ranges/src/lib.rs unit tests | 31 | discard (out of crate) | separate crate; the algebra behaviors (canonical equality, union/intersection/complement laws, contains/contains_many, simplify, from_iter normalization, display) are re-expressed against `pubgrub::Ranges` |

functions_in_scope: 32 (pubgrub crate: 6 + 3 + 12 + 6 + 2 + 2 + 1)

## Fresh-vocabulary policy

Oracle universes use harbor/expedition vocabulary (apex, mast, hull, sail,
gear, axle, keel, helm, rudder, winch, flag, rope, lantern, envoy, carto,
flint, plinth, …) — no overlap with the dart-doc scenarios (root, foo, bar,
baz, menu, dropdown, icons, intl) beyond generic structure. All numeric and
semver universes were re-derived and probe-verified rather than copied.

## Dummy-gate considerations

A stub crate whose functions all `unimplemented!()` panics on first call, so
any test that calls into the crate and asserts a produced value fails against
it. Report-string and tree-structure tests assert exact produced values.
Failure-path tests (parse errors, provider-error wrapping, NoSolution
classification) are paired with positive assertions on payload fields or
sibling successes within the same behavior family so no test passes on a
reject-everything implementation. No `#[should_panic]` tests are included.
