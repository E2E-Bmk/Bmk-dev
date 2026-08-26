# Specification coverage map — governor-fullrepro-001


oracle_source: generated_only (all tests written against the spec with
expected values verified by running the pinned reference — probe binary,
two probe rounds during spec drafting, then full-suite runs on both the
patched path and the registry lock; upstream tests served as a behavioral
checklist only — see rewrite_audit.md).

Test IDs are `{crate}::{module path}::{function}` as reported by
cargo-nextest against the oracle workspace.

| test_nodeid | layer | assertion_kind | spec_section | status | notes |
|-------------|-------|----------------|--------------|--------|-------|
| `atomic::generated_per_second_interval_division` | atomic | positive | ## Quotas and Time Arithmetic | covered | per_second interval division, burst getter, full replenish figure |
| `atomic::generated_nanosecond_truncation` | atomic | positive | ## Quotas and Time Arithmetic | covered | 1e9/3 truncates to 333333333ns; replenished_in = 999999999ns |
| `atomic::generated_per_minute_per_hour_intervals` | atomic | positive | ## Quotas and Time Arithmetic | covered | per_minute/per_hour period division incl. 8571428571ns case |
| `atomic::generated_with_period_and_zero` | atomic | both | ## Quotas and Time Arithmetic | covered | with_period burst 1 + Some; zero period → None |
| `atomic::generated_allow_burst_replaces_only_burst` | atomic | positive | ## Quotas and Time Arithmetic | covered | allow_burst swaps burst, keeps interval |
| `atomic::generated_deprecated_new_divides_period` | atomic | both | ## Quotas and Time Arithmetic | covered | deprecated new divides period by burst; zero period → None |
| `atomic::generated_quota_equality_and_copy` | atomic | invariant | ## Quotas and Time Arithmetic | covered | equality = (burst, interval) pair; Copy semantics |
| `atomic::generated_quota_debug_form` | atomic | positive | ## Quotas and Time Arithmetic | covered | Debug renders both fields incl. truncated-interval form |
| `atomic::generated_fresh_limiter_admits_burst` | atomic | both | ## Rate-Limiting Decisions | covered | fresh limiter admits exactly burst_size cells |
| `atomic::generated_single_cell_regain_exact_boundary` | atomic | both | ## Rate-Limiting Decisions | covered | boundary conforms; 1ns earlier denies; regained cell consumed |
| `atomic::generated_no_extra_cell_after_long_idle` | atomic | both | ## Rate-Limiting Decisions | covered | long idle never mints extra cells (upstream issue-107 intent) |
| `atomic::generated_denials_do_not_consume` | atomic | invariant | ## Rate-Limiting Decisions | covered | denied checks leave state unchanged |
| `atomic::generated_check_n_one_equals_check` | atomic | invariant | ## Rate-Limiting Decisions | covered | check_n(1) sequence ≡ check sequence |
| `atomic::generated_batch_drain_and_deny` | atomic | both | ## Rate-Limiting Decisions | covered | batch weight math drains exactly the burst |
| `atomic::generated_batch_impossible_capacity` | atomic | negative | ## Error Semantics | covered | InsufficientCapacity value/field/Display; state untouched |
| `atomic::generated_full_burst_batch_replenish` | atomic | positive | ## Rate-Limiting Decisions | covered | full-burst batch conforms again after burst_size_replenished_in |
| `atomic::generated_partial_regain_batch` | atomic | both | ## Rate-Limiting Decisions | covered | partial regain admits exactly the regained batch |
| `atomic::generated_batch_equals_singles_history` | atomic | invariant | ## Cross-View Invariants | covered | invariant 6: batch history ≡ n singles history |
| `atomic::generated_denial_earliest_and_wait` | atomic | positive | ## Rate-Limiting Decisions | covered | earliest_possible value; wait_time_from shrink + zero clamp |
| `atomic::generated_display_fixed_sentence` | atomic | positive | ## Rate-Limiting Decisions | covered | `rate-limited until Nanos(1s)` Display sentence |
| `atomic::generated_pre_advanced_start_reference` | atomic | positive | ## Clocks and Time Sources | covered | start reference includes pre-construction clock offset |
| `atomic::generated_wait_advance_reconform` | atomic | invariant | ## Cross-View Invariants | covered | invariant 2: advertised wait is exact to the nanosecond |
| `atomic::generated_quota_round_trip_on_denial` | atomic | positive | ## Rate-Limiting Decisions | covered | NotUntil::quota reconstructs the constructed quota |
| `atomic::generated_batch_denial_earliest` | atomic | positive | ## Rate-Limiting Decisions | covered | batch earliest = (TAT + w) − tau; conforms at that instant |
| `atomic::generated_keys_independent_budgets` | atomic | both | ## Keyed Limiters and Store Housekeeping | covered | distinct keys own full budgets under one quota |
| `atomic::generated_first_seen_key_unset_state` | atomic | positive | ## Keyed Limiters and Store Housekeeping | covered | first-seen key = unset state at current instant |
| `atomic::generated_check_key_n_capacity_precedes_state` | atomic | negative | ## Keyed Limiters and Store Housekeeping | covered | impossible batch reports capacity without creating the key |
| `atomic::generated_len_and_is_empty` | atomic | positive | ## Keyed Limiters and Store Housekeeping | covered | population counts distinct keys, not checks |
| `atomic::generated_retain_recent_exact_boundary` | atomic | both | ## Keyed Limiters and Store Housekeeping | covered | TAT == threshold evicted; strictly newer retained |
| `atomic::generated_retain_recent_staggered_keys` | atomic | positive | ## Keyed Limiters and Store Housekeeping | covered | staggered TATs evicted in stored-time order |
| `atomic::generated_eviction_resets_key` | atomic | positive | ## Keyed Limiters and Store Housekeeping | covered | evicted key re-checks as first-seen |
| `atomic::generated_shrink_to_fit_no_decision_effect` | atomic | invariant | ## Keyed Limiters and Store Housekeeping | covered | shrink_to_fit has no observable decision effect |
| `atomic::generated_into_state_store_live_keys` | atomic | positive | ## Keyed Limiters and Store Housekeeping | covered | store extraction keeps live keys |
| `atomic::generated_dashmap_store_parity` | atomic | invariant | ## Cross-View Invariants | covered | invariant 7: hashmap and dashmap stores decide identically |
| `atomic::generated_custom_hasher_families` | atomic | positive | ## Keyed Limiters and Store Housekeeping | covered | hasher-accepting constructors on both families, both clocks |
| `atomic::generated_ratelimiter_new_explicit_store` | atomic | positive | ## Keyed Limiters and Store Housekeeping | covered | RateLimiter::new from explicit HashMapStateStore |
| `atomic::generated_keyed_default_alias` | atomic | positive | ## Keyed Limiters and Store Housekeeping | covered | keyed/dashmap default constructors, real clock, len |
| `atomic::generated_fake_clock_starts_at_zero` | atomic | positive | ## Clocks and Time Sources | covered | default reading is zero Nanos |
| `atomic::generated_fake_clock_advance_and_read` | atomic | positive | ## Clocks and Time Sources | covered | advance accumulates into now() |
| `atomic::generated_fake_clock_clones_share` | atomic | positive | ## Clocks and Time Sources | covered | clones share one reading in both directions |
| `atomic::generated_fake_clock_equality` | atomic | invariant | ## Clocks and Time Sources | covered | clock equality tracks current readings |
| `atomic::generated_nanos_conversions` | atomic | positive | ## Clocks and Time Sources | covered | Duration/u64 conversions round-trip |
| `atomic::generated_nanos_debug_wraps_duration` | atomic | positive | ## Clocks and Time Sources | covered | `Nanos(1.5s)` / `Nanos(200ms)` debug wrapper |
| `atomic::generated_reference_arithmetic_on_nanos` | atomic | positive | ## Clocks and Time Sources | covered | duration_since saturation, saturating_sub, Add<Nanos> |
| `atomic::generated_duration_implements_reference` | atomic | positive | ## Clocks and Time Sources | covered | Duration as Reference incl. receiver-unchanged underflow |
| `atomic::generated_real_clocks_first_checks` | atomic | positive | ## Clocks and Time Sources | covered | Monotonic/System/Default clocks: first ok, burst-1 second denied |
| `atomic::generated_clock_accessor_reflects_advances` | atomic | positive | ## Rate-Limiting Decisions | covered | clock() component access reflects advances |
| `atomic::generated_snapshot_countdown_and_deny` | atomic | positive | ## Middleware and State Snapshots | covered | b−1 countdown to 0, then denial |
| `atomic::generated_snapshot_regained_cell_consumed` | atomic | positive | ## Middleware and State Snapshots | covered | regained-and-consumed reports 0; idle reset reports b−1 |
| `atomic::generated_snapshot_quota_reconstruction` | atomic | positive | ## Middleware and State Snapshots | covered | snapshot quota round trip incl. with_period-derived quotas |
| `atomic::generated_denials_unchanged_by_middleware` | atomic | invariant | ## Middleware and State Snapshots | covered | middleware never changes the denial value |
| `atomic::generated_custom_middleware_outcomes` | atomic | positive | ## Middleware and State Snapshots | covered | caller middleware chooses both outcome types |
| `atomic::generated_keyed_snapshot_per_key` | atomic | positive | ## Middleware and State Snapshots | covered | per-key snapshots, batch snapshot arithmetic |
| `atomic::generated_noop_unit_outcome` | atomic | positive | ## Middleware and State Snapshots | covered | NoOp default returns unit on conforming checks |
| `atomic::generated_snapshot_eq_and_clone` | atomic | invariant | ## Middleware and State Snapshots | covered | snapshot Clone/PartialEq/Debug traits |
| `integration::gateway::generated_steady_drip_admits_all` | integration | invariant | ## Representative Workflows | covered | drip loop: decision rule + wait honor + regain (WF1) |
| `integration::gateway::generated_burst_recovery_window` | integration | positive | ## Representative Workflows | covered | snapshot countdown → 2-cell window → full replenish reset |
| `integration::gateway::generated_batch_reservation_pipeline` | integration | both | ## Representative Workflows | covered | batch drain → capacity error → advertised batch wait honored |
| `integration::gateway::generated_two_quotas_one_clock` | integration | positive | ## Representative Workflows | covered | two quotas on one shared clock recover at their own rates |
| `integration::tenants::generated_tenant_isolation_and_retention` | integration | positive | ## Representative Workflows | covered | staggered tenants → threshold eviction → fresh re-entry (WF3) |
| `integration::tenants::generated_store_families_agree` | integration | invariant | ## Cross-View Invariants | covered | scripted parity across both store families incl. retention |
| `integration::tenants::generated_bulk_admission_accounting` | integration | both | ## Representative Workflows | covered | keyed batches + snapshots + capacity guard + wait honor |
| `integration::tenants::generated_evicted_key_fresh_state_math` | integration | positive | ## Keyed Limiters and Store Housekeeping | covered | eviction restarts denial math from current instant |
| `integration::observability::generated_rate_headers_pipeline` | integration | positive | ## Representative Workflows | covered | remaining-capacity headers + retry-after honored (WF2) |
| `integration::observability::generated_quota_recovery_from_snapshot` | integration | invariant | ## Middleware and State Snapshots | covered | snapshot-rebuilt quota drives an identical limiter |
| `integration::observability::generated_custom_middleware_gateway` | integration | positive | ## Middleware and State Snapshots | covered | unit/unit middleware over keyed limiter + retention |
| `integration::scheduling::generated_wait_and_retry_schedule` | integration | positive | ## Clocks and Time Sources | covered | pre-advanced start: absolute schedule Nanos(2.5s)/Nanos(3s) |
| `integration::scheduling::generated_quota_ladder_regain_intervals` | integration | invariant | ## Cross-View Invariants | covered | invariant 3: observed regains equal replenish_interval |

## Coverage notes

- Every behavioral section of the spec has at least four atomic tests;
  each of the three Representative Workflows is realized by at least one
  integration test.
- Not asserted anywhere: the clock-overflow panic row of Error Semantics
  (panic contract left untested by design — no #[should_panic] in the
  oracle), quanta-clock specifics, async/jitter surfaces (Non-Goals).
- All 68 kept tests import exclusively through the spec's Import Surface
  (`governor`, `governor::clock`, `governor::nanos`, `governor::middleware`,
  `governor::state`, `governor::state::keyed`) plus `nonzero_ext` and std.
