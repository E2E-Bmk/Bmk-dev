# Specification to Test Map

Every physical test below is mapped to the public behavior described in `spec.md`.

## Atomic Cases

- `test_new_document_uses_requested_version_and_units`: covered
- `test_new_document_sets_metric_measurement_header`: covered
- `test_new_document_exposes_modelspace`: covered
- `test_new_document_setup_populates_requested_standard_tables`: covered
- `test_header_user_integer_and_float_values_are_mutable`: covered
- `test_layer_table_adds_colored_layer_and_supports_case_insensitive_lookup`: covered
- `test_layer_dxf_attributes_can_be_mutated`: covered
- `test_linetype_table_exposes_continuous_linetype`: covered
- `test_appid_table_registers_custom_application`: covered
- `test_default_paperspace_is_available`: covered
- `test_layout_manager_creates_named_paperspace`: covered
- `test_block_table_creates_named_block_and_entity_space`: covered
- `test_line_factory_stores_start_end_and_layer`: covered
- `test_circle_factory_stores_center_radius_and_color`: covered
- `test_arc_factory_stores_angles`: covered
- `test_point_factory_stores_three_dimensional_location`: covered
- `test_text_factory_and_public_placement_enum`: covered
- `test_mtext_factory_stores_content_and_height`: covered
- `test_lwpolyline_factory_stores_vertices_and_closed_flag`: covered
- `test_polyline3d_factory_stores_vertices`: covered
- `test_ellipse_factory_stores_center_axis_and_ratio`: covered
- `test_spline_factory_stores_fit_points`: covered
- `test_ray_and_xline_factories_store_direction_vectors`: covered
- `test_solid_trace_and_face_factories_create_expected_types`: covered
- `test_entity_dxf_namespace_supports_assignment_and_set`: covered
- `test_modelspace_query_selects_by_entity_type`: covered
- `test_query_attribute_filter_selects_layer`: covered
- `test_query_attribute_filter_can_ignore_case`: covered
- `test_entity_query_assignment_updates_supported_entities`: covered
- `test_entity_query_slice_and_attribute_selection_are_sequence_views`: covered
- `test_layout_groupby_groups_entities_by_layer`: covered
- `test_layout_groupby_accepts_a_public_key_function`: covered
- `test_rgb_integer_helpers_round_trip`: covered
- `test_rgb_and_rgba_public_classes_round_trip_hex_and_floats`: covered
- `test_transparency_helpers_preserve_endpoints`: covered
- `test_vec3_arithmetic_and_distance_are_public`: covered
- `test_ucs_converts_points_to_and_from_wcs`: covered
- `test_ocs_converts_points_to_and_from_wcs`: covered
- `test_matrix44_translation_transforms_a_point`: covered
- `test_appdata_high_level_methods_store_and_discard_tags`: covered
- `test_xdata_high_level_methods_store_and_replace_tags`: covered
- `test_user_xdata_list_commits_supported_values`: covered
- `test_user_xdata_dict_commits_mapping_values`: covered
- `test_extension_dictionary_xrecord_exposes_public_tag_storage`: covered
- `test_destroyed_entity_is_removed_by_layout_purge`: covered
- `test_viewport_factory_is_available_in_paperspace`: covered
- `test_block_reference_factory_stores_insert_transform`: covered
- `test_block_reference_attribute_can_be_added_and_placed`: covered
- `test_paperspace_viewport_and_layout_entities_have_distinct_storage`: covered
- `test_document_write_produces_readable_ascii_stream`: covered
- `test_document_ascii_projection_contains_selected_public_entity_facts`: covered

## Integration Cases

- `test_new_document_entities_survive_text_stream_round_trip`: covered
- `test_modelspace_and_named_paperspace_survive_file_round_trip`: covered
- `test_block_definition_and_reference_survive_file_round_trip`: covered
- `test_block_attribute_template_and_value_survive_round_trip`: covered
- `test_layer_assignment_query_and_groupby_agree_after_round_trip`: covered
- `test_query_mutation_is_reflected_in_serialized_entities`: covered
- `test_case_insensitive_query_and_color_grouping_share_entity_selection`: covered
- `test_appdata_and_xdata_survive_stream_round_trip`: covered
- `test_user_xdata_list_and_dict_survive_file_round_trip`: covered
- `test_extension_dictionary_xrecord_survives_file_round_trip`: covered
- `test_color_projections_survive_entity_and_layer_round_trip`: covered
- `test_line_geometry_mutation_survives_stream_round_trip`: covered
- `test_common_entity_factory_set_preserves_types_and_attributes`: covered
- `test_polyline_and_spline_geometry_survives_round_trip`: covered
- `test_text_and_mtext_public_content_and_placement_survive_round_trip`: covered
- `test_ocs_circle_projection_agrees_before_and_after_round_trip`: covered
- `test_ucs_converted_point_can_be_stored_and_reloaded`: covered
- `test_matrix_transform_mutates_line_geometry_and_round_trips`: covered
- `test_destroy_and_purge_changes_query_and_round_trip_state`: covered
- `test_multiple_block_references_keep_independent_transforms_and_attributes`: covered
- `test_owner_queries_include_modelspace_paperspace_and_block_entities`: covered
- `test_document_groupby_combines_entities_from_all_public_layouts`: covered
- `test_read_stream_can_be_reused_for_equivalent_public_projections`: covered
- `test_unicode_text_survives_readfile_without_snapshot_comparison`: covered
- `test_setup_tables_and_entity_linetype_assignment_survive_round_trip`: covered
- `test_header_user_values_survive_file_round_trip`: covered
- `test_layer_mutation_and_entity_reassignment_survive_round_trip`: covered
- `test_insert_query_and_block_definition_remain_connected_after_round_trip`: covered
- `test_query_selection_can_be_grouped_and_serialized_as_one_workflow`: covered
- `test_r2000_line_round_trip_preserves_version_and_basic_geometry`: covered
- `test_full_public_workflow_connects_entities_blocks_layouts_and_custom_data`: covered

final_scoreable: 82
