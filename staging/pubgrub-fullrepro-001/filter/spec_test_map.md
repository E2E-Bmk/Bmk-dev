# Specification coverage map — pubgrub-fullrepro-001


oracle_source: generated_only (all tests written against the spec with
expected values verified by running the pinned reference — probe binary,
five rounds, plus full suite runs on both the patched path and the
registry lock; upstream tests and examples served as a behavioral
checklist only — see rewrite_audit.md).

Test IDs are `{crate}::{module path}::{function}` as reported by
cargo-nextest against the oracle workspace.

| test_nodeid | layer | assertion_kind | spec_section | status | notes |
|-------------|-------|----------------|--------------|--------|-------|
| `atomic::generated_display_atoms` | atomic | positive | ## Version Set Algebra | covered | single-segment display forms: ∅, *, exact, half-bounded |
| `atomic::generated_display_bounded_pairs` | atomic | positive | ## Version Set Algebra | covered | bounded-pair forms incl. inclusive/exclusive mixes |
| `atomic::generated_display_union_join` | atomic | positive | ## Version Set Algebra | covered | multi-segment rendering joined by " \| " |
| `atomic::generated_constructor_boundaries` | atomic | positive | ## Version Set Algebra | covered | empty/full/singleton/higher_than/strictly_lower_than/between membership at boundaries |
| `atomic::generated_from_range_bounds_forms` | atomic | positive | ## Version Set Algebra | covered | every RangeBounds shape maps to its canonical set |
| `atomic::generated_from_iter_normalizes` | atomic | positive | ## Version Set Algebra | covered | from_iter merges overlaps and skips invalid pairs |
| `atomic::generated_contains_many_lockstep` | atomic | positive | ## Version Set Algebra | covered | contains_many agrees with contains on sorted queries |
| `atomic::generated_as_singleton_rules` | atomic | positive | ## Version Set Algebra | covered | Some only for exactly-one-version sets |
| `atomic::generated_bounding_range_rules` | atomic | positive | ## Version Set Algebra | covered | bounding_range across empty/half-open/multi-segment shapes |
| `atomic::generated_segment_iteration` | atomic | positive | ## Version Set Algebra | covered | iter() yields canonical segments in ascending order |
| `atomic::generated_is_empty_paths` | atomic | positive | ## Version Set Algebra | covered | emptiness of constructions and intersect-to-empty results |
| `atomic::generated_union_merges_touching` | atomic | positive | ## Version Set Algebra | covered | touching/overlapping segments merge into one segment |
| `atomic::generated_union_keeps_discrete_gaps` | atomic | positive | ## Version Set Algebra | covered | discrete-gap unions keep separate segments (no discreteness assumption) |
| `atomic::generated_equality_canonical_forms` | atomic | positive | ## Version Set Algebra | covered | distinct constructions of one set compare equal |
| `atomic::generated_complement_laws` | atomic | positive | ## Version Set Algebra | covered | complement round-trip, full/empty laws |
| `atomic::generated_intersection_and_empty` | atomic | positive | ## Version Set Algebra | covered | intersections incl. disjoint-to-empty |
| `atomic::generated_disjoint_and_subset` | atomic | positive | ## Version Set Algebra | covered | is_disjoint / subset_of relations |
| `atomic::generated_simplify_fixed_rules` | atomic | positive | ## Version Set Algebra | covered | the three fixed simplify rules on sorted versions |
| `atomic::generated_simplify_partial` | atomic | positive | ## Version Set Algebra | covered | simplification keeps segments still separating given versions |
| `atomic::generated_versionset_trait_laws` | atomic | positive | ## Version Set Algebra | covered | VersionSet trait defaults agree with the inherent algebra |
| `atomic::generated_semver_construct_display` | atomic | positive | ## Semantic Versions | covered | new/zero/one construction and dotted display |
| `atomic::generated_semver_ordering_total` | atomic | positive | ## Semantic Versions | covered | (major, minor, patch) lexicographic total order |
| `atomic::generated_semver_bump_rules` | atomic | positive | ## Semantic Versions | covered | bump_patch/minor/major zeroing of lower components |
| `atomic::generated_semver_tuple_conversions` | atomic | positive | ## Semantic Versions | covered | (u32,u32,u32) conversions in both directions |
| `atomic::generated_semver_parse_display_roundtrip` | atomic | positive | ## Semantic Versions | covered | parse∘display identity on valid three-part strings |
| `atomic::generated_semver_not_three_parts` | atomic | failure_path | ## Error Semantics | covered | NotThreeParts payload carries full_version; valid sibling parses |
| `atomic::generated_semver_parse_int_error_payloads` | atomic | failure_path | ## Error Semantics | covered | ParseIntError payload fields full_version/version_part |
| `atomic::generated_offline_registry_views` | atomic | positive | ## Dependency Universes and Providers | covered | packages()/versions() sorted read-back views |
| `atomic::generated_offline_replacement` | atomic | positive | ## Dependency Universes and Providers | covered | re-adding a (package, version) replaces its constraints |
| `atomic::generated_offline_choose_version_strategy` | atomic | positive | ## Dependency Universes and Providers | covered | highest contained version; None once the range excludes all |
| `atomic::generated_offline_unavailable_message` | atomic | positive | ## Dependency Universes and Providers | covered | unknown pair yields the documented unavailability sentence |
| `atomic::generated_offline_prioritize_ordering` | atomic | positive | ## Dependency Universes and Providers | covered | no-match packages outrank all; fewer candidates rank higher |
| `atomic::generated_statistics_default` | atomic | positive | ## Dependency Universes and Providers | covered | default statistics report zero conflicts |
| `atomic::generated_resolve_chain_map` | atomic | positive | ## Resolution | covered | linear chain solves to one version per reachable package |
| `atomic::generated_resolve_prefers_newest` | atomic | positive | ## Resolution | covered | in-memory strategy selects the newest matching version |
| `atomic::generated_resolve_backtracks_to_older` | atomic | positive | ## Resolution | covered | newest versions abandoned when constraints force older ones |
| `atomic::generated_resolve_intersects_shared_dep` | atomic | positive | ## Resolution | covered | shared dependency selected from the constraint intersection |
| `atomic::generated_resolve_cycles_and_self` | atomic | positive | ## Resolution | covered | dependency cycles and satisfiable self-dependencies solve |
| `atomic::generated_resolve_forced_older_choice` | atomic | positive | ## Resolution | covered | conflict avoidance picks a non-newest version during decisions |
| `atomic::generated_resolve_empty_range_rejects` | atomic | failure_path | ## Resolution | covered | empty-range dependency yields NoSolution; solvable sibling passes |
| `atomic::generated_resolve_semver_universe` | atomic | positive | ## Resolution | covered | semver-typed universe end to end |
| `atomic::generated_resolve_repeated_runs_equal` | atomic | positive | ## Cross-View Invariants | covered | repeated solves yield identical maps (invariant 6) |
| `atomic::generated_error_choosing_version_wrap` | atomic | failure_path | ## Error Semantics | covered | ErrorChoosingVersion wraps package + source; Display checked |
| `atomic::generated_error_retrieving_dependencies_wrap` | atomic | failure_path | ## Error Semantics | covered | ErrorRetrievingDependencies payload and Display |
| `atomic::generated_error_cancel_wrap` | atomic | failure_path | ## Error Semantics | covered | ErrorInShouldCancel wraps source; "The solver was cancelled" |
| `atomic::generated_nosolution_error_display_from` | atomic | failure_path | ## Error Semantics | covered | NoSolution Display "There is no solution"; From<tree> conversion |
| `atomic::generated_term_display_and_eq` | atomic | positive | ## Failure Proofs: Derivation Trees | covered | Positive displays as the set; Negative as "Not ( … )"; Eq/Clone |
| `atomic::generated_external_notroot_noversions_display` | atomic | positive | ## Failure Proofs: Derivation Trees | covered | NotRoot sentence; both NoVersions sentence forms |
| `atomic::generated_external_custom_fromdep_display` | atomic | positive | ## Failure Proofs: Derivation Trees | covered | Custom two forms; FromDependencyOf all four set-dropping forms |
| `atomic::generated_derived_node_fields` | atomic | positive | ## Failure Proofs: Derivation Trees | covered | terms/shared_id/cause1/cause2 field access on a hand-built node |
| `atomic::generated_tree_packages_by_variant` | atomic | positive | ## Failure Proofs: Derivation Trees | covered | packages() census for each external variant and derived nodes |
| `atomic::generated_format_terms_shapes` | atomic | positive | ## Failure Reports | covered | empty/single-positive/single-negative/pos-neg pair normalization |
| `atomic::generated_format_external_passthrough` | atomic | positive | ## Failure Reports | covered | format_external equals the fact's Display form |
| `atomic::generated_report_single_external` | atomic | positive | ## Failure Reports | covered | single-external tree reports exactly the bare sentence |
| `atomic::generated_report_two_external_derived` | atomic | positive | ## Failure Reports | covered | hand-built derived node renders "Because … and …, …." |
| `atomic::generated_report_with_formatter_default_equiv` | atomic | positive | ## Failure Reports | covered | report equals report_with_formatter(default formatter) |
| `integration::solving::generated_diamond_intersection_solution` | integration | positive | ## Resolution | covered | diamond universe; selected shared version lies in the computed intersection |
| `integration::solving::generated_deep_backtrack_solution` | integration | positive | ## Resolution | covered | two newest versions abandoned to satisfy a sibling constraint |
| `integration::solving::generated_solution_satisfies_all_constraints` | integration | positive | ## Cross-View Invariants | covered | invariant 1: walk the provider, every requesting range contains its target |
| `integration::solving::generated_string_packages_semver_universe` | integration | positive | ## Resolution | covered | String packages with semver sets |
| `integration::solving::generated_failing_determinism_across_runs` | integration | positive | ## Cross-View Invariants | covered | invariant 6: identical reports across repeated failing solves, raw and collapsed |
| `integration::solving::generated_custom_lowest_strategy_provider` | integration | positive | ## Dependency Universes and Providers | covered | solver honors a lowest-version provider; offline picks newest on the same universe |
| `integration::solving::generated_cancel_budget_provider` | integration | failure_path | ## Error Semantics | covered | generous budget solves; exhausted budget surfaces ErrorInShouldCancel with payload |
| `integration::solving::generated_dependencies_fetched_once` | integration | positive | ## State Model | covered | get_dependencies called exactly once per reachable pair |
| `integration::proofs::generated_unknown_root_tree_is_single_noversions` | integration | failure_path | ## Failure Proofs: Derivation Trees | covered | unknown root: single NoVersions leaf; set, report, census asserted positively |
| `integration::proofs::generated_conflict_tree_structure_and_externals` | integration | positive | ## Failure Proofs: Derivation Trees | covered | derived root terms = positive root term; all six leaf facts; census |
| `integration::proofs::generated_collapse_folds_noversions_into_fact` | integration | positive | ## Failure Proofs: Derivation Trees | covered | collapse folds NoVersions into the surviving dependency fact |
| `integration::proofs::generated_collapse_merges_partial_conflict` | integration | positive | ## Failure Proofs: Derivation Trees | covered | collapsed conflict keeps only dependency facts; same conclusion and census |
| `integration::proofs::generated_hand_built_shared_node_cited_once` | integration | positive | ## Failure Reports | covered | shared_id node explained once then cited "(1)"; empty terms render fallback |
| `integration::reports::generated_linear_chain_report_exact` | integration | positive | ## Failure Reports | covered | exact two-line chain report; exact collapsed one-liner |
| `integration::reports::generated_branching_report_refs_and_blank_line` | integration | positive | ## Failure Reports | covered | exact branching report: " (1)" marker, blank-line separation, citation |
| `integration::reports::generated_branching_collapsed_report_exact` | integration | positive | ## Failure Reports | covered | exact collapsed branching report |
| `integration::reports::generated_custom_formatter_drives_reporter` | integration | positive | ## Failure Reports | covered | caller formatter drives every callback; reporter keeps joining/refs |
| `integration::reports::generated_semver_universe_report_exact` | integration | positive | ## Failure Reports | covered | semver range displays flow verbatim into raw and collapsed reports |
| `integration::strategy::generated_fewest_candidates_decided_first` | integration | positive | ## Dependency Universes and Providers | covered | decision order follows fewest-candidates strategy; one prioritize per package |
| `integration::strategy::generated_prioritize_reasked_after_narrowing` | integration | positive | ## State Model | covered | priority cache: re-ask only after the constraint narrows |
| `integration::strategy::generated_conflict_statistics_observed` | integration | positive | ## State Model | covered | conflict counters rise for contested packages, stay zero for the root |
| `integration::strategy::generated_unavailable_reason_reported` | integration | positive | ## Failure Proofs: Derivation Trees | covered | Unavailable metadata becomes a version-scoped Custom fact and exact report |
| `integration::compose::generated_flip_success_to_failure` | integration | positive | ## Representative Workflows | covered | one withdrawn version flips solution to proof; raw + collapsed exact |
| `integration::compose::generated_algebra_computed_constraint_flows` | integration | positive | ## Cross-View Invariants | covered | invariant 3: algebra-computed set renders canonically inside the proof |
| `integration::compose::generated_bump_chain_universe` | integration | positive | ## Semantic Versions | covered | bump-derived universe; window membership; parse/display round-trip |
| `integration::compose::generated_clone_then_collapse_leaves_original` | integration | positive | ## Failure Proofs: Derivation Trees | covered | collapsing a clone leaves the original proof and census untouched |
| `integration::compose::generated_census_matches_report_mentions` | integration | positive | ## Cross-View Invariants | covered | invariant 2: every census package appears in the rendered report |

## Floor checks

- base functions: 83 (56 atomic, 27 integration) — ≥ 60 total, ≥ 20 integration ✓
- failure_path share: 9/83 ≈ 11% — every failure-path test asserts produced
  payloads or is paired with a positive sibling in the same behaviour family;
  no `#[should_panic]` tests ✓
- all tests import only `pubgrub::…` public paths (plus std) ✓
- dummy gate: a stub crate panics via `unimplemented!()` on first call in
  every test; report/tree/solution assertions compare produced values, so no
  test passes on a reject-everything or empty-value implementation ✓
