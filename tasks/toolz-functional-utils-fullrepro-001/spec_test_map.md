# Behavior Map

Each physical check below is covered by the corresponding public behavior
section. The final scoreable count is 68.

| Layer | Test | Scope section | Coverage |
| --- | --- | --- | --- |
| atomic | test_public_import_surface_exposes_functional_names | Public Import Surface | covered |
| atomic | test_identity_apply_and_basic_aliases | Public Import Surface | covered |
| atomic | test_accumulate_supports_default_and_initial | Product State Model | covered |
| atomic | test_groupby_accepts_callable_and_member_key | Product State Model | covered |
| atomic | test_iterable_slicing_helpers_materialize_expected_values | Product State Model | covered |
| atomic | test_get_supports_scalar_multiple_and_default | Cross-View Invariants | covered |
| atomic | test_first_second_nth_last_access_sequences | Product State Model | covered |
| atomic | test_concat_concatv_and_mapcat_flatten_sequences | Product State Model | covered |
| atomic | test_cons_and_interpose_preserve_order | Product State Model | covered |
| atomic | test_frequencies_counts_hashable_values | Product State Model | covered |
| atomic | test_reduceby_groups_and_reduces_with_init | Cross-View Invariants | covered |
| atomic | test_partition_and_partition_all_handle_remainders | Product State Model | covered |
| atomic | test_pluck_and_sliding_window_project_data | Product State Model | covered |
| atomic | test_unique_and_isdistinct_preserve_first_occurrences | Product State Model | covered |
| atomic | test_merge_sorted_and_topk_order_values | Product State Model | covered |
| atomic | test_diff_and_peek_helpers_preserve_stream_views | Cross-View Invariants | covered |
| atomic | test_count_works_for_materialized_and_generator | Product State Model | covered |
| atomic | test_merge_and_merge_with_precedence | Product State Model | covered |
| atomic | test_mapping_transforms_preserve_key_value_relationships | Cross-View Invariants | covered |
| atomic | test_mapping_filters_select_by_predicate | Product State Model | covered |
| atomic | test_assoc_and_dissoc_return_copies | Cross-View Invariants | covered |
| atomic | test_nested_dict_updates_are_immutable | Cross-View Invariants | covered |
| atomic | test_get_in_reads_nested_sequences_with_default | Cross-View Invariants | covered |
| atomic | test_compose_compose_left_and_pipe_order | Product State Model | covered |
| atomic | test_juxt_returns_parallel_results | Product State Model | covered |
| atomic | test_curry_supports_partial_positional_and_keyword_application | Product State Model | covered |
| atomic | test_curry_exposes_public_bound_arguments | Cross-View Invariants | covered |
| atomic | test_memoize_reuses_result_without_timing | Cross-View Invariants | covered |
| atomic | test_do_and_complement_compose_side_effect_and_predicate | Representative Workflows | covered |
| atomic | test_thread_first_and_thread_last_place_values | Product State Model | covered |
| atomic | test_flip_and_excepts_adapt_callables | Error Semantics | covered |
| atomic | test_curried_iterable_functions_accept_partial_arguments | Public Import Surface | covered |
| atomic | test_curried_dict_functions_accept_partial_arguments | Public Import Surface | covered |
| atomic | test_curried_compose_and_pipe_workflow | Representative Workflows | covered |
| atomic | test_custom_factories_are_used_for_mapping_results | Cross-View Invariants | covered |
| atomic | test_update_in_applies_function_to_default_for_missing_path | Error Semantics | covered |
| atomic | test_random_sample_is_repeatable_with_explicit_seed | Product State Model | covered |
| atomic | test_join_matches_records_by_public_key_functions | Representative Workflows | covered |
| integration | test_text_analytics_pipeline_combines_flatten_count_and_ranking | Representative Workflows | covered |
| integration | test_grouped_scores_workflow_uses_grouping_then_reduction | Representative Workflows | covered |
| integration | test_chunk_transform_workflow_reassembles_normalized_values | Representative Workflows | covered |
| integration | test_lazy_window_selection_workflow_preserves_source_count | Cross-View Invariants | covered |
| integration | test_sorted_stream_comparison_workflow_reports_ranked_differences | Representative Workflows | covered |
| integration | test_peek_and_index_workflow_reads_a_replayable_record_stream | Cross-View Invariants | covered |
| integration | test_nested_profile_workflow_updates_then_reads_without_mutation | Representative Workflows | covered |
| integration | test_dictionary_cleaning_workflow_merges_filters_and_maps_values | Representative Workflows | covered |
| integration | test_composed_curry_workflow_builds_parameterized_formatter | Representative Workflows | covered |
| integration | test_memoized_composition_workflow_counts_only_distinct_inputs | Cross-View Invariants | covered |
| integration | test_parallel_projection_workflow_logs_and_classifies_values | Representative Workflows | covered |
| integration | test_threaded_chunk_workflow_transforms_values_before_partitioning | Representative Workflows | covered |
| integration | test_curried_record_workflow_filters_then_plucks_fields | Representative Workflows | covered |
| integration | test_curried_nested_update_workflow_reuses_public_partial_forms | Representative Workflows | covered |
| integration | test_curried_reduction_workflow_accumulates_each_group | Cross-View Invariants | covered |
| integration | test_curried_pipeline_workflow_normalizes_and_selects_values | Representative Workflows | covered |
| integration | test_merge_with_frequency_workflow_combines_partition_counts | Cross-View Invariants | covered |
| integration | test_multi_level_update_workflow_creates_missing_branch_and_reads_it | Cross-View Invariants | covered |
| integration | test_member_group_workflow_renames_groups_and_projects_rows | Cross-View Invariants | covered |
| integration | test_token_stream_workflow_adds_prefixes_and_delimiters | Representative Workflows | covered |
| integration | test_windowed_batch_workflow_computes_adjacent_pair_sums | Representative Workflows | covered |
| integration | test_join_workflow_enriches_matching_records_then_groups_by_category | Representative Workflows | covered |
| integration | test_seeded_sampling_workflow_can_be_ranked_deterministically | Representative Workflows | covered |
| integration | test_generator_count_and_replay_workflow_preserves_observed_prefix | Cross-View Invariants | covered |
| integration | test_ranked_record_workflow_plucks_values_and_selects_largest | Representative Workflows | covered |
| integration | test_adapted_predicate_workflow_filters_and_recovers_invalid_items | Error Semantics | covered |
| integration | test_ordered_mapping_workflow_keeps_projection_order_across_updates | Cross-View Invariants | covered |
| integration | test_curried_end_to_end_workflow_projects_clean_nested_records | Representative Workflows | covered |
| integration | test_function_adapter_workflow_binds_then_threads_arguments | Representative Workflows | covered |
| integration | test_summary_workflow_reduces_rows_into_nested_report | Representative Workflows | covered |

final_scoreable: 68
