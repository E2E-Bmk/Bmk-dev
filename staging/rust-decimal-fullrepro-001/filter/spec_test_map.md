# Specification coverage map — rust-decimal-fullrepro-001


oracle_source: generated_only (all tests written against the spec with
expected values verified by running the pinned reference — probe binary,
five probe rounds during spec drafting plus three during oracle authoring,
then full-suite runs on both the patched path and the registry lock;
upstream tests served as a behavioral checklist only — see
rewrite_audit.md).

Test IDs are `{crate}::{module path}::{function}` as reported by
cargo-nextest against the oracle workspace.

| test_nodeid | layer | assertion_kind | spec_section | status | notes |
|-------------|-------|----------------|--------------|--------|-------|
| `atomic::generated_constants_render` | atomic | positive | ## Value Model and Construction | covered | ZERO/ONE/NEGATIVE_ONE/TWO/TEN/ONE_HUNDRED/ONE_THOUSAND, MAX_SCALE, Default |
| `atomic::generated_domain_bounds_render` | atomic | positive | ## Value Model and Construction | covered | MAX/MIN renderings, MIN = -MAX, scale 0 |
| `atomic::generated_new_scale_forms` | atomic | positive | ## Value Model and Construction | covered | new(i64, scale) keeps stored scale incl. trailing zeros |
| `atomic::generated_try_new_paths` | atomic | both | ## Value Model and Construction | covered | try_new Ok + ScaleExceedsMaximumPrecision(30) |
| `atomic::generated_new_panics_on_bad_scale` | atomic | negative | ## Value Model and Construction | covered | new panics at scale > 28; paired positive assertion |
| `atomic::generated_from_i128_with_scale_ok` | atomic | positive | ## Value Model and Construction | covered | 128-bit mantissa constructor inside the 96-bit domain |
| `atomic::generated_try_from_i128_errors` | atomic | both | ## Value Model and Construction | covered | ScaleExceedsMaximumPrecision / ExceedsMaximumPossibleValue / LessThanMinimumPossibleValue + Ok path |
| `atomic::generated_from_i128_panics_out_of_domain` | atomic | negative | ## Value Model and Construction | covered | from_i128_with_scale panics out of domain; paired positive |
| `atomic::generated_from_parts_limbs` | atomic | positive | ## Value Model and Construction | covered | 32-bit limb assembly (documented rustdoc example value) |
| `atomic::generated_from_integer_impls` | atomic | positive | ## Value Model and Construction | covered | From<all 12 integer primitives> at scale 0 |
| `atomic::generated_from_int128_panics_on_overflow` | atomic | negative | ## Value Model and Construction | covered | From<u128> panics beyond 96 bits; paired positive |
| `atomic::generated_fromstr_basic_scale` | atomic | positive | ## String Parsing and Rendering | covered | grammar forms: "5.", ".5", "+", stored-scale law |
| `atomic::generated_fromstr_underscores` | atomic | both | ## String Parsing and Rendering | covered | embedded `_` legal, leading `_` is ErrorString |
| `atomic::generated_fromstr_29digit_rounding_away` | atomic | positive | ## String Parsing and Rendering | covered | midpoint-away rounding at fractional digit 29 |
| `atomic::generated_fromstr_scientific_forms` | atomic | both | ## String Parsing and Rendering | covered | e/E suffix shifting, exponent overflow → ScaleExceedsMaximumPrecision |
| `atomic::generated_fromstr_error_variants` | atomic | negative | ## String Parsing and Rendering | covered | empty/bare-sign/double-point/alpha/oversized integer → ErrorString |
| `atomic::generated_from_str_exact_paths` | atomic | both | ## String Parsing and Rendering | covered | exact parse Ok; >28 nonzero digits → Underflow |
| `atomic::generated_tryfrom_str_matches_fromstr` | atomic | both | ## String Parsing and Rendering | covered | TryFrom<&str> behaves as FromStr |
| `atomic::generated_from_str_radix_integers` | atomic | positive | ## String Parsing and Rendering | covered | radix 2/8/16/36 digit-letter parsing |
| `atomic::generated_from_str_radix_ten_matches_fromstr` | atomic | positive | ## String Parsing and Rendering | covered | radix 10 = FromStr incl. fractional and sign |
| `atomic::generated_from_str_radix_errors` | atomic | negative | ## String Parsing and Rendering | covered | radix <2 / >36 / digit outside radix → ErrorString |
| `atomic::generated_from_scientific_paths` | atomic | positive | ## String Parsing and Rendering | covered | mandatory-exponent parsing, e/E, 5e28, 1e-28 |
| `atomic::generated_from_scientific_errors` | atomic | negative | ## String Parsing and Rendering | covered | no marker → ErrorString; 5e-30 → ScaleExceedsMaximumPrecision |
| `atomic::generated_from_scientific_lossy_rounds` | atomic | both | ## String Parsing and Rendering | covered | lossy rounds excess significand digits; bare overflow still fails |
| `atomic::generated_parse_zero_sign_normalized` | atomic | positive | ## String Parsing and Rendering | covered | parsed "-0"/"-0.0" carries positive sign, keeps scale |
| `atomic::generated_display_trailing_zeros` | atomic | positive | ## String Parsing and Rendering | covered | Display preserves stored scale as trailing zeros |
| `atomic::generated_display_precision_truncates` | atomic | positive | ## String Parsing and Rendering | covered | {:.N} truncates toward zero when scale larger |
| `atomic::generated_display_precision_pads` | atomic | positive | ## String Parsing and Rendering | covered | {:.N} pads with zeros when scale smaller |
| `atomic::generated_display_width_and_fill` | atomic | positive | ## String Parsing and Rendering | covered | width, zero-fill, alignment options |
| `atomic::generated_lowerexp_forms` | atomic | positive | ## String Parsing and Rendering | covered | {:e} normalized scientific incl. 1e0 and 0e0 |
| `atomic::generated_upperexp_forms` | atomic | positive | ## String Parsing and Rendering | covered | {:E} uppercase exponent forms |
| `atomic::generated_debug_equals_display` | atomic | invariant | ## String Parsing and Rendering | covered | Debug output equals Display output |
| `atomic::generated_array_string_unsigned_magnitude` | atomic | positive | ## String Parsing and Rendering | covered | array_string renders unsigned magnitude, drops `-` |
| `atomic::generated_negative_zero_renders_sign` | atomic | positive | ## String Parsing and Rendering | covered | set sign flag renders "-0.00" while comparing equal to zero |
| `atomic::generated_add_sub_scale_law` | atomic | positive | ## Arithmetic and Scale Propagation | covered | result scale = larger operand scale, signed zero sums |
| `atomic::generated_add_keeps_exact_when_it_fits` | atomic | positive | ## Arithmetic and Scale Propagation | covered | exact sum kept at 28 significant digits |
| `atomic::generated_add_overflow_rescales_bankers` | atomic | positive | ## Arithmetic and Scale Propagation | covered | scale reduced digit-by-digit with banker's rounding |
| `atomic::generated_max_boundary_add` | atomic | both | ## Arithmetic and Scale Propagation | covered | MAX+0.4 rounds back to MAX; MAX+0.5 and MAX+1 panic |
| `atomic::generated_mul_scale_sum` | atomic | positive | ## Arithmetic and Scale Propagation | covered | product scale = sum of operand scales |
| `atomic::generated_mul_bankers_at_representational_cut` | atomic | positive | ## Arithmetic and Scale Propagation | covered | banker's rounding when product exceeds 28 places |
| `atomic::generated_mul_mantissa_overflow_paths` | atomic | both | ## Arithmetic and Scale Propagation | covered | MAX*0.5 / MAX*0.1 keep value; MAX*2 panics |
| `atomic::generated_div_exact_values` | atomic | positive | ## Arithmetic and Scale Propagation | covered | exact quotients compared by value (scale unspecified) |
| `atomic::generated_div_inexact_rounds_at_final_digit` | atomic | positive | ## Arithmetic and Scale Propagation | covered | 2/3, 1/7 etc. rounded at maximal representable digit |
| `atomic::generated_div_bankers_ties_at_cut` | atomic | positive | ## Arithmetic and Scale Propagation | covered | nearest-even ties at the last representable digit |
| `atomic::generated_zero_divisor_paths` | atomic | both | ## Arithmetic and Scale Propagation | covered | /0 and %0 panic; checked forms None; Ok path |
| `atomic::generated_rem_sign_and_scale` | atomic | positive | ## Arithmetic and Scale Propagation | covered | remainder sign follows dividend, larger operand scale |
| `atomic::generated_checked_family_matches_operators` | atomic | both | ## Arithmetic and Scale Propagation | covered | checked_* Some mirrors operators, None at domain edges |
| `atomic::generated_saturating_family` | atomic | positive | ## Arithmetic and Scale Propagation | covered | saturating_* clamp to MAX/MIN by true-result sign |
| `atomic::generated_neg_flips_sign_flag` | atomic | positive | ## Arithmetic and Scale Propagation | covered | unary Neg flips flag incl. negative zero image |
| `atomic::generated_reference_operand_forms` | atomic | invariant | ## Arithmetic and Scale Propagation | covered | &a op &b / mixed reference forms equal owned forms |
| `atomic::generated_assign_operator_chain` | atomic | positive | ## Arithmetic and Scale Propagation | covered | += -= *= /= %= behave as operator + assignment |
| `atomic::generated_sum_product_aggregation` | atomic | positive | ## Arithmetic and Scale Propagation | covered | Sum/Product over owned and reference iterators, empty = ZERO/ONE |
| `atomic::generated_round_bankers_to_integer` | atomic | positive | ## Rounding and Scale Surgery | covered | round() nearest-even at scale 0 |
| `atomic::generated_round_dp_bankers` | atomic | positive | ## Rounding and Scale Surgery | covered | round_dp banker's at requested places |
| `atomic::generated_round_dp_no_padding_at_or_above_scale` | atomic | positive | ## Rounding and Scale Surgery | covered | rounding never pads; value returned unchanged |
| `atomic::generated_round_dp_matches_nearest_even_strategy` | atomic | invariant | ## Rounding and Scale Surgery | covered | round_dp ≡ round_dp_with_strategy(MidpointNearestEven) |
| `atomic::generated_strategy_matrix_positive_midpoint` | atomic | positive | ## Rounding and Scale Surgery | covered | all 7 strategies on 2.35 |
| `atomic::generated_strategy_matrix_negative_midpoint` | atomic | positive | ## Rounding and Scale Surgery | covered | all 7 strategies on -2.35 |
| `atomic::generated_strategy_matrix_below_midpoint` | atomic | positive | ## Rounding and Scale Surgery | covered | below-midpoint agreement + directional variants on ±2.34 |
| `atomic::generated_midpoint_variants_disagree_only_on_exact_half` | atomic | positive | ## Rounding and Scale Surgery | covered | 2.45 nearest-even vs away-from-zero; toward-zero above half |
| `atomic::generated_round_sf_basic` | atomic | positive | ## Rounding and Scale Surgery | covered | significant-figure rounding across magnitudes |
| `atomic::generated_round_sf_edges` | atomic | both | ## Rounding and Scale Surgery | covered | digits=0, zero value, padding, MAX/MIN → None |
| `atomic::generated_round_sf_with_strategy` | atomic | positive | ## Rounding and Scale Surgery | covered | strategy-parameterized significant figures |
| `atomic::generated_trunc_and_fract` | atomic | positive | ## Rounding and Scale Surgery | covered | trunc to scale 0, fract keeps sign, trunc+fract identity |
| `atomic::generated_trunc_with_scale` | atomic | positive | ## Rounding and Scale Surgery | covered | truncation toward zero; padding when at/above stored scale |
| `atomic::generated_floor_ceil` | atomic | positive | ## Rounding and Scale Surgery | covered | floor toward -inf, ceil toward +inf, scale 0 |
| `atomic::generated_rescale_pads_zeros_up` | atomic | positive | ## Rounding and Scale Surgery | covered | rescale up appends zeros |
| `atomic::generated_rescale_clamps_at_mantissa_headroom` | atomic | positive | ## Rounding and Scale Surgery | covered | clamped at largest achievable scale; MAX has no headroom |
| `atomic::generated_rescale_down_rounds_midpoint_away` | atomic | positive | ## Rounding and Scale Surgery | covered | rescale down uses midpoint-away (differs from round_dp) |
| `atomic::generated_set_scale_reinterprets_mantissa` | atomic | both | ## Rounding and Scale Surgery | covered | radix-point move; >28 → ScaleExceedsMaximumPrecision, value kept |
| `atomic::generated_normalize_strips_trailing_zeros` | atomic | positive | ## Rounding and Scale Surgery | covered | canonical image, value preserved |
| `atomic::generated_normalize_zero_canonical` | atomic | positive | ## Rounding and Scale Surgery | covered | negative zero normalizes to positive zero scale 0; normalize_assign |
| `atomic::generated_image_accessors` | atomic | positive | ## Introspection, Ordering, and Conversion | covered | scale(), signed mantissa(), sign predicates |
| `atomic::generated_zero_and_integer_predicates` | atomic | positive | ## Introspection, Ordering, and Conversion | covered | is_zero at any scale; is_integer ignores trailing zeros |
| `atomic::generated_sign_mutators_abs_signum` | atomic | positive | ## Introspection, Ordering, and Conversion | covered | set_sign_*, abs, signum incl. zero of either sign |
| `atomic::generated_min_max_by_value` | atomic | positive | ## Introspection, Ordering, and Conversion | covered | max/min numeric comparison |
| `atomic::generated_equality_across_scales` | atomic | invariant | ## Introspection, Ordering, and Conversion | covered | 1.0 == 1.00 == 1.000; negative zero equals zero |
| `atomic::generated_ordering_total_numeric` | atomic | invariant | ## Introspection, Ordering, and Conversion | covered | total numeric order; sort across scale images |
| `atomic::generated_hash_agrees_with_eq` | atomic | invariant | ## Introspection, Ordering, and Conversion | covered | equal values hash identically; HashSet lookup across scales |
| `atomic::generated_serialize_byte_layout` | atomic | positive | ## Introspection, Ordering, and Conversion | covered | 16-byte layout: flags, scale byte, sign byte, LE limbs |
| `atomic::generated_serialize_deserialize_round_trip` | atomic | invariant | ## Introspection, Ordering, and Conversion | covered | deserialize(serialize(x)) reproduces value + stored image |
| `atomic::generated_to_integer_truncates_toward_zero` | atomic | positive | ## Introspection, Ordering, and Conversion | covered | to_i8..to_u128/isize/usize truncate toward zero |
| `atomic::generated_to_integer_out_of_range` | atomic | negative | ## Introspection, Ordering, and Conversion | covered | None when out of target domain; i128 fits MAX/MIN |
| `atomic::generated_to_float` | atomic | positive | ## Introspection, Ordering, and Conversion | covered | to_f32/to_f64 nearest binary float |
| `atomic::generated_try_from_decimal_matches_trait` | atomic | both | ## Introspection, Ordering, and Conversion | covered | TryFrom<Decimal> Ok where trait Some, ConversionTo where None |
| `atomic::generated_infallible_as_forms` | atomic | positive | ## Introspection, Ordering, and Conversion | covered | as_i128/as_f64 agree with trait results |
| `atomic::generated_from_integer_primitives` | atomic | both | ## Introspection, Ordering, and Conversion | covered | FromPrimitive integer sources; None outside 96-bit domain |
| `atomic::generated_from_infallible_int_conversions` | atomic | positive | ## Introspection, Ordering, and Conversion | covered | From<int> infallible forms render at scale 0 |
| `atomic::generated_from_float_shortest_rendering` | atomic | positive | ## Introspection, Ordering, and Conversion | covered | from_f32/from_f64/TryFrom produce shortest decimal |
| `atomic::generated_from_float_rejects_non_finite` | atomic | negative | ## Introspection, Ordering, and Conversion | covered | NaN/inf/out-of-range → None / ConversionTo |
| `atomic::generated_from_float_retain_binary_expansion` | atomic | positive | ## Introspection, Ordering, and Conversion | covered | retain variants keep full binary expansion to 28 places |
| `atomic::generated_zero_one_trait_surface` | atomic | positive | ## Introspection, Ordering, and Conversion | covered | Zero/One traits agree with constants; is_one across scales |
| `atomic::generated_signed_trait_agrees_with_inherent` | atomic | invariant | ## Introspection, Ordering, and Conversion | covered | Signed trait mirrors inherent sign-flag members incl. zero |
| `integration::billing::generated_invoice_scale_flow` | integration | positive | ## Representative Workflows | covered | parse → mul/sub scale laws → round_dp → format truncation |
| `integration::billing::generated_tax_ladder_with_strategies` | integration | positive | ## Arithmetic and Scale Propagation | covered | product scale → three strategies diverge → add → to_f64 |
| `integration::billing::generated_ledger_sum_then_split` | integration | positive | ## Arithmetic and Scale Propagation | covered | Sum → inexact div → round_dp → mantissa introspection |
| `integration::billing::generated_running_balance_with_checked_guards` | integration | both | ## Arithmetic and Scale Propagation | covered | checked_sub chain → zero predicates → checked_div None → round_sf |
| `integration::billing::generated_unit_price_backout_via_rem` | integration | positive | ## Arithmetic and Scale Propagation | covered | rem → exact div → normalize → to_u32 → reconstruction identity |
| `integration::billing::generated_percentage_change_report` | integration | positive | ## Cross-View Invariants | covered | div/mul chain → normalize → format precision → to_f64 |
| `integration::canonical::generated_aggregation_canonical_form` | integration | invariant | ## Representative Workflows | covered | Sum scale → normalize → eq/hash across images → serialize |
| `integration::canonical::generated_scale_representations_one_bucket` | integration | invariant | ## Cross-View Invariants | covered | HashMap folds four scale images into one bucket incl. div result |
| `integration::canonical::generated_negative_zero_pipeline` | integration | invariant | ## Cross-View Invariants | covered | sign flag → Display/serialize keep it → normalize clears it |
| `integration::canonical::generated_sort_stability_across_scales` | integration | invariant | ## Introspection, Ordering, and Conversion | covered | stable sort, Iterator::max last-max image, sub scale law |
| `integration::canonical::generated_display_distinguishes_what_eq_conflates` | integration | invariant | ## Cross-View Invariants | covered | eq/hash conflate; Display/scale/mantissa distinguish; normalize maps |
| `integration::canonical::generated_byte_image_survives_arithmetic_identity` | integration | invariant | ## Cross-View Invariants | covered | identity add keeps image; byte round trip; abs clears sign byte |
| `integration::precision::generated_exact_vs_rounding_parse_pipeline` | integration | both | ## String Parsing and Rendering | covered | Underflow vs rounded parse → arithmetic at scale 28 → round_dp |
| `integration::precision::generated_smallest_positive_unit_flow` | integration | positive | ## Value Model and Construction | covered | epsilon: div underflow to zero, mul doubles, {:e} rendering |
| `integration::precision::generated_max_boundary_saturation_chain` | integration | both | ## Arithmetic and Scale Propagation | covered | near-MAX: checked None / saturating clamp / rounding-back window |
| `integration::precision::generated_division_precision_then_reround` | integration | positive | ## Arithmetic and Scale Propagation | covered | 1/3*3 ≠ 1 at max precision → round_dp/round_sf recover ONE |
| `integration::precision::generated_scale_28_arithmetic_rounds_to_fit` | integration | both | ## Arithmetic and Scale Propagation | covered | scale-reduction rounding at 28-digit budget; tie keeps even |
| `integration::precision::generated_sf_rounding_versus_dp_on_same_value` | integration | positive | ## Rounding and Scale Surgery | covered | round_sf vs round_dp vs trunc on one quotient at two magnitudes |
| `integration::precision::generated_rescale_headroom_walk` | integration | positive | ## Rounding and Scale Surgery | covered | rescale up/clamp/down walk; midpoint-away vs round_dp divergence |
| `integration::conversion_flow::generated_float_ingest_two_modes_diverge` | integration | positive | ## Introspection, Ordering, and Conversion | covered | shortest vs retain ingestion → drift arithmetic → to_f64 |
| `integration::conversion_flow::generated_scientific_ingest_to_fixed_report` | integration | positive | ## String Parsing and Rendering | covered | from_scientific → mul scale law → normalize → {:e}/{:E} |
| `integration::conversion_flow::generated_parse_compute_render_exp_round_trip` | integration | both | ## String Parsing and Rendering | covered | {:e} render → from_scientific round trip → 1e-30 error |
| `integration::conversion_flow::generated_integer_export_after_arithmetic` | integration | both | ## Introspection, Ordering, and Conversion | covered | product → trunc/ceil/round exports → to_u8 None / ConversionTo |
| `integration::conversion_flow::generated_radix_ingest_arithmetic_export` | integration | both | ## String Parsing and Rendering | covered | radix 2/16/36 ingest → arithmetic → to_u16 → radix errors |
| `integration::conversion_flow::generated_hash_map_keyed_accumulation` | integration | invariant | ## Cross-View Invariants | covered | Decimal keys fold across scales; += accumulation; Sum; to_f32 |
| `integration::conversion_flow::generated_underscore_ledger_parse_and_fold` | integration | invariant | ## String Parsing and Rendering | covered | underscore parse via TryFrom/from_str_exact → fold → serialize/hash |

## Coverage summary

- 119 tests: 93 atomic, 26 integration; every spec behavior family holds
  at least one atomic test and one integration flow touching it.
- Sections covered: Value Model and Construction (11 atomic + flows),
  String Parsing and Rendering (23 atomic + 5 integration), Arithmetic and
  Scale Propagation (18 atomic + 7 integration), Rounding and Scale Surgery
  (20 atomic + 2 integration), Introspection/Ordering/Conversion (21 atomic
  + 4 integration), Cross-View Invariants (6 integration), Representative
  Workflows (2 integration re-enacting the spec's worked examples).
- Error Semantics is asserted where each error arises: ErrorString
  (parsing/radix), Underflow (from_str_exact), ScaleExceedsMaximumPrecision
  (construction, set_scale, scientific), ExceedsMaximumPossibleValue /
  LessThanMinimumPossibleValue (try_from_i128_with_scale), ConversionTo
  (TryFrom float/int exports), plus the documented panic paths, each paired
  with a produced-value assertion in the same test.
- Not asserted (spec gaps deliberately left unpinned): trailing-zero scale
  of exact division quotients (spec declares value-only contract),
  `to_u*` on negative fractional inputs above -1 (reference rejects on
  sign; spec pins only the integral example), platform-width isize/usize
  domain edges.
