# Spec Test Map - dogpile-cache-fullrepro-001

oracle_version: 2026-08-04-artifact-only-v1
oracle_source: generated_public_api
oracle_files: oracle/test_atomic.py, oracle/test_integration.py
runtime_requirements: oracle/requirements.txt
reference_source: https://github.com/sqlalchemy/dogpile.cache
reference_commit: 39e3c57180ce9b4f27a256ffdf31f063d54fb685
stage4_evidence: ARTIFACT_ONLY
counts: atomic=38, integration=34, system_e2e=0, total=72
depends_on_annotation_coverage: 34/34 integration tests
final_scoreable: 72

| test_nodeid | source | layer | assertion_kind | spec_section | status | notes |
|---|---|---|---|---|---|---|
| `oracle/test_atomic.py::test_no_value_is_false_and_distinct_from_none` | generated | atomic | positive | Region Value Operations | covered | single public API behavior |
| `oracle/test_atomic.py::test_cached_value_exposes_payload_metadata_and_dynamic_age` | generated | atomic | positive | Region Value Operations | covered | single public API behavior |
| `oracle/test_atomic.py::test_make_region_preserves_public_name` | generated | atomic | positive | Cross-View Invariants | covered | single public API behavior |
| `oracle/test_atomic.py::test_unconfigured_region_reports_state_and_rejects_backend_access` | generated | atomic | failure_path | Region Configuration And Backend Selection | covered | single public API behavior |
| `oracle/test_atomic.py::test_configure_memory_returns_same_region_and_enables_use` | generated | atomic | positive | Region Configuration And Backend Selection | covered | single public API behavior |
| `oracle/test_atomic.py::test_configure_unknown_backend_raises_plugin_not_found` | generated | atomic | failure_path | Region Configuration And Backend Selection | covered | single public API behavior |
| `oracle/test_atomic.py::test_duplicate_configure_requires_replace_flag` | generated | atomic | failure_path | Region Configuration And Backend Selection | covered | single public API behavior |
| `oracle/test_atomic.py::test_replace_existing_backend_allows_reconfiguration` | generated | atomic | positive | Backend Extension Serialization And Proxies | covered | single public API behavior |
| `oracle/test_atomic.py::test_invalid_expiration_type_raises_validation_error` | generated | atomic | failure_path | Expiration Invalidation And Creation | covered | single public API behavior |
| `oracle/test_atomic.py::test_timedelta_expiration_is_converted_to_seconds` | generated | atomic | positive | Expiration Invalidation And Creation | covered | single public API behavior |
| `oracle/test_atomic.py::test_region_set_and_get_round_trip_a_value` | generated | atomic | positive | Region Value Operations | covered | single public API behavior |
| `oracle/test_atomic.py::test_missing_key_returns_no_value_sentinel` | generated | atomic | positive | Region Value Operations | covered | single public API behavior |
| `oracle/test_atomic.py::test_delete_is_idempotent_and_removes_cached_value` | generated | atomic | positive | Region Value Operations | covered | single public API behavior |
| `oracle/test_atomic.py::test_set_multi_get_multi_preserves_requested_order` | generated | atomic | positive | Region Value Operations | covered | single public API behavior |
| `oracle/test_atomic.py::test_get_multi_empty_sequence_returns_empty_list` | generated | atomic | shape | Region Value Operations | covered | single public API behavior |
| `oracle/test_atomic.py::test_delete_multi_removes_existing_and_ignores_missing` | generated | atomic | positive | Region Value Operations | covered | single public API behavior |
| `oracle/test_atomic.py::test_get_value_metadata_returns_cached_value_object` | generated | atomic | positive | Region Value Operations | covered | single public API behavior |
| `oracle/test_atomic.py::test_get_value_metadata_returns_none_for_missing_key` | generated | atomic | positive | Region Value Operations | covered | single public API behavior |
| `oracle/test_atomic.py::test_get_honors_zero_expiration_time` | generated | atomic | positive | Expiration Invalidation And Creation | covered | single public API behavior |
| `oracle/test_atomic.py::test_get_ignore_expiration_returns_stale_payload` | generated | atomic | positive | Expiration Invalidation And Creation | covered | single public API behavior |
| `oracle/test_atomic.py::test_get_or_create_creates_once_then_reuses_cached_value` | generated | atomic | positive | Expiration Invalidation And Creation | covered | single public API behavior |
| `oracle/test_atomic.py::test_get_or_create_passes_creator_args_when_generation_is_needed` | generated | atomic | positive | Expiration Invalidation And Creation | covered | single public API behavior |
| `oracle/test_atomic.py::test_get_or_create_should_cache_false_returns_without_storing` | generated | atomic | positive | Expiration Invalidation And Creation | covered | single public API behavior |
| `oracle/test_atomic.py::test_get_or_create_negative_one_expiration_means_no_expiration` | generated | atomic | positive | Expiration Invalidation And Creation | covered | single public API behavior |
| `oracle/test_atomic.py::test_get_or_create_multi_returns_values_in_input_order` | generated | atomic | positive | Expiration Invalidation And Creation | covered | single public API behavior |
| `oracle/test_atomic.py::test_get_or_create_multi_duplicate_keys_reuse_same_generated_value` | generated | atomic | positive | Expiration Invalidation And Creation | covered | single public API behavior |
| `oracle/test_atomic.py::test_null_backend_never_stores_values` | generated | atomic | positive | Backend Extension Serialization And Proxies | covered | single public API behavior |
| `oracle/test_atomic.py::test_memory_backend_basic_mapping_contract` | generated | atomic | positive | Backend Extension Serialization And Proxies | covered | single public API behavior |
| `oracle/test_atomic.py::test_function_key_generator_uses_module_function_namespace_and_positional_values` | generated | atomic | positive | Decorator Caching Workflows | covered | single public API behavior |
| `oracle/test_atomic.py::test_function_key_generator_rejects_keyword_arguments` | generated | atomic | failure_path | Decorator Caching Workflows | covered | single public API behavior |
| `oracle/test_atomic.py::test_kwarg_function_key_generator_sorts_argument_names_and_uses_defaults` | generated | atomic | positive | Decorator Caching Workflows | covered | single public API behavior |
| `oracle/test_atomic.py::test_function_multi_key_generator_returns_one_key_per_argument` | generated | atomic | positive | Decorator Caching Workflows | covered | single public API behavior |
| `oracle/test_atomic.py::test_sha1_mangle_key_accepts_text_and_bytes` | generated | atomic | positive | Decorator Caching Workflows | covered | single public API behavior |
| `oracle/test_atomic.py::test_length_conditional_mangler_only_changes_long_keys` | generated | atomic | positive | Region Value Operations | covered | single public API behavior |
| `oracle/test_atomic.py::test_cache_backend_from_config_dict_filters_prefix` | generated | atomic | positive | Backend Extension Serialization And Proxies | covered | single public API behavior |
| `oracle/test_atomic.py::test_cache_backend_serialized_default_methods_delegate_to_plain_methods` | generated | atomic | positive | Backend Extension Serialization And Proxies | covered | single public API behavior |
| `oracle/test_atomic.py::test_lock_uses_creator_when_value_function_reports_regeneration_needed` | generated | atomic | positive | Dogpile Lock Coordination | covered | single public API behavior |
| `oracle/test_atomic.py::test_lock_returns_existing_value_when_it_is_not_expired` | generated | atomic | positive | Dogpile Lock Coordination | covered | single public API behavior |
| `oracle/test_integration.py::test_configure_from_config_builds_backend_with_prefixed_arguments` | generated | integration | positive | Region Configuration And Backend Selection | covered | public API composition seam |
| `oracle/test_integration.py::test_user_key_mangler_is_applied_to_set_get_and_delete` | generated | integration | positive | Region Value Operations | covered | public API composition seam |
| `oracle/test_integration.py::test_backend_key_mangler_is_adopted_when_region_has_no_user_mangler` | generated | integration | positive | Backend Extension Serialization And Proxies | covered | public API composition seam |
| `oracle/test_integration.py::test_region_key_mangler_overrides_backend_key_mangler` | generated | integration | positive | Backend Extension Serialization And Proxies | covered | public API composition seam |
| `oracle/test_integration.py::test_key_mangler_applies_to_multi_key_operations` | generated | integration | positive | Region Value Operations | covered | public API composition seam |
| `oracle/test_integration.py::test_hard_invalidation_forces_next_get_or_create_regeneration` | generated | integration | positive | Expiration Invalidation And Creation | covered | public API composition seam |
| `oracle/test_integration.py::test_ignore_expiration_bypasses_hard_invalidation_for_get` | generated | integration | positive | Expiration Invalidation And Creation | covered | public API composition seam |
| `oracle/test_integration.py::test_soft_invalidation_regenerates_when_expiration_is_available` | generated | integration | positive | Expiration Invalidation And Creation | covered | public API composition seam |
| `oracle/test_integration.py::test_soft_invalidation_without_expiration_raises_cache_exception` | generated | integration | failure_path | Expiration Invalidation And Creation | covered | public API composition seam |
| `oracle/test_integration.py::test_get_or_create_multi_generates_only_missing_keys_and_preserves_existing` | generated | integration | positive | Region Value Operations | covered | public API composition seam |
| `oracle/test_integration.py::test_get_or_create_multi_should_cache_fn_filters_each_generated_value` | generated | integration | positive | Expiration Invalidation And Creation | covered | public API composition seam |
| `oracle/test_integration.py::test_metadata_projection_agrees_with_cached_payload_and_expiration` | generated | integration | positive | Region Value Operations | covered | public API composition seam |
| `oracle/test_integration.py::test_cache_on_arguments_caches_results_per_argument_tuple` | generated | integration | positive | Decorator Caching Workflows | covered | public API composition seam |
| `oracle/test_integration.py::test_cache_on_arguments_invalidate_targets_one_argument_tuple` | generated | integration | positive | Expiration Invalidation And Creation | covered | public API composition seam |
| `oracle/test_integration.py::test_cache_on_arguments_helper_methods_share_the_region_key` | generated | integration | positive | Decorator Caching Workflows | covered | public API composition seam |
| `oracle/test_integration.py::test_cache_on_arguments_accepts_equivalent_keyword_calls_for_wrapped_signature` | generated | integration | positive | Decorator Caching Workflows | covered | public API composition seam |
| `oracle/test_integration.py::test_cache_on_arguments_with_kwarg_generator_accepts_equivalent_kwarg_calls` | generated | integration | positive | Decorator Caching Workflows | covered | public API composition seam |
| `oracle/test_integration.py::test_cache_on_arguments_namespaces_isolate_same_callable_arguments` | generated | integration | positive | Decorator Caching Workflows | covered | public API composition seam |
| `oracle/test_integration.py::test_cache_multi_on_arguments_caches_subset_and_invalidates_one_key` | generated | integration | positive | Expiration Invalidation And Creation | covered | public API composition seam |
| `oracle/test_integration.py::test_cache_multi_on_arguments_asdict_preserves_keyed_result_shape` | generated | integration | positive | Decorator Caching Workflows | covered | public API composition seam |
| `oracle/test_integration.py::test_cache_multi_on_arguments_refresh_updates_selected_cached_keys` | generated | integration | positive | Decorator Caching Workflows | covered | public API composition seam |
| `oracle/test_integration.py::test_custom_function_key_generator_controls_decorator_cache_identity` | generated | integration | positive | Decorator Caching Workflows | covered | public API composition seam |
| `oracle/test_integration.py::test_proxy_backend_can_count_and_delegate_region_operations` | generated | integration | positive | Backend Extension Serialization And Proxies | covered | public API composition seam |
| `oracle/test_integration.py::test_proxy_chain_exposes_actual_underlying_backend` | generated | integration | positive | Backend Extension Serialization And Proxies | covered | public API composition seam |
| `oracle/test_integration.py::test_proxy_set_multi_must_not_mutate_values_returned_by_get_or_create_multi` | generated | integration | positive | Region Value Operations | covered | public API composition seam |
| `oracle/test_integration.py::test_registered_public_backend_is_loaded_by_region_configuration` | generated | integration | positive | Backend Extension Serialization And Proxies | covered | public API composition seam |
| `oracle/test_integration.py::test_dbm_backend_persists_values_across_regions` | generated | integration | positive | Backend Extension Serialization And Proxies | covered | public API composition seam |
| `oracle/test_integration.py::test_dbm_backend_delete_is_visible_to_later_regions` | generated | integration | positive | Backend Extension Serialization And Proxies | covered | public API composition seam |
| `oracle/test_integration.py::test_region_serializer_and_deserializer_round_trip_payloads` | generated | integration | positive | Backend Extension Serialization And Proxies | covered | public API composition seam |
| `oracle/test_integration.py::test_cant_deserialize_exception_causes_regeneration` | generated | integration | positive | Backend Extension Serialization And Proxies | covered | public API composition seam |
| `oracle/test_integration.py::test_async_creation_runner_refreshes_stale_value_and_returns_old_value_first` | generated | integration | positive | Expiration Invalidation And Creation | covered | public API composition seam |
| `oracle/test_integration.py::test_memory_pickle_backend_returns_independent_payload_copy` | generated | integration | positive | Backend Extension Serialization And Proxies | covered | public API composition seam |
| `oracle/test_integration.py::test_decorated_method_ignores_self_for_default_cache_key` | generated | integration | positive | Cross-View Invariants | covered | public API composition seam |
| `oracle/test_integration.py::test_cache_multi_on_arguments_should_cache_fn_filters_dict_values` | generated | integration | positive | Decorator Caching Workflows | covered | public API composition seam |
