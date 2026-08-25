# Spec Test Map — pypdf-fullrepro-001

oracle_version: 2026-08-03-stage3-mixed-v5-specgap-derivability
oracle_source: upstream_plus_generated
oracle_files: test_atomic.py, test_integration.py
runtime_requirements: requirements.txt
scorer_isolation: --remove-path pypdf --pytest-arg=--rootdir=.
depends_on_annotation_coverage: 32/32
track_a_upstream_kept: 29
track_b_generated_kept: 39
scope_plan: target_subdomain=document workflow core; expected_oracle_max=120; actual_oracle=68

| test_nodeid | source | layer | assertion_kind | spec_section | status | notes |
|---|---|---|---|---|---|---|
| test_atomic.py::test_pagerange_string_inputs_normalize_to_slices | upstream | atomic | positive | Page Ranges, Generic Objects, and Constants | covered | upstream public PageRange rewrite |
| test_atomic.py::test_pagerange_invalid_syntax_is_rejected | upstream | atomic | failure_path | Page Ranges, Generic Objects, and Constants | covered | upstream public PageRange invalid syntax rewrite |
| test_atomic.py::test_parse_filename_page_ranges_assigns_default_all_pages | upstream | atomic | positive | Page Ranges, Generic Objects, and Constants | covered | upstream public filename/range rewrite |
| test_atomic.py::test_parse_filename_page_ranges_rejects_leading_range | upstream | atomic | failure_path | Page Ranges, Generic Objects, and Constants | covered | upstream public filename/range error rewrite |
| test_atomic.py::test_user_access_permissions_roundtrip_named_flags | upstream | atomic | positive | Writing, Merging, and Serialization | covered | upstream public permissions rewrite |
| test_atomic.py::test_user_access_permissions_rejects_unknown_names | upstream | atomic | failure_path | Writing, Merging, and Serialization | covered | upstream public permissions error rewrite |
| test_atomic.py::test_papersize_a4_exposes_positive_dimensions | upstream | atomic | positive | Page Ranges, Generic Objects, and Constants | covered | upstream public PaperSize rewrite |
| test_atomic.py::test_blank_page_without_known_size_raises | upstream | atomic | failure_path | Error Semantics | covered | upstream public blank-page error rewrite |
| test_integration.py::test_blank_page_roundtrip_preserves_page_count_and_size | upstream | system_e2e | positive | Cross-View Invariants | covered | upstream writer/read roundtrip rewrite |
| test_integration.py::test_insert_page_controls_page_order | upstream | integration | positive | Writing, Merging, and Serialization | covered | upstream public page insertion rewrite |
| test_integration.py::test_metadata_add_replace_and_remove_roundtrip | upstream | system_e2e | positive | Cross-View Invariants | covered | upstream metadata roundtrip rewrite |
| test_integration.py::test_attachment_roundtrip_exposes_mapping_and_object_view | upstream | system_e2e | positive | Cross-View Invariants | covered | upstream attachment cross-view rewrite |
| test_integration.py::test_outline_roundtrip_preserves_nested_destination | upstream | system_e2e | positive | Cross-View Invariants | covered | upstream outline cross-view rewrite |
| test_integration.py::test_page_labels_roundtrip_matches_page_order | upstream | system_e2e | positive | Cross-View Invariants | covered | upstream page-label roundtrip rewrite |
| test_atomic.py::test_encrypt_rejects_unknown_algorithm | upstream | atomic | failure_path | Error Semantics | covered | upstream encryption error rewrite |
| test_integration.py::test_encrypt_default_owner_password_roundtrip | upstream | system_e2e | positive | Writing, Merging, and Serialization | covered | upstream encryption roundtrip rewrite |
| test_atomic.py::test_rectangle_object_coordinates_are_mutable | upstream | atomic | positive | Page Geometry, Transformations, and Extraction | covered | upstream rectangle rewrite |
| test_atomic.py::test_page_rotate_accepts_right_angles_and_rejects_other_angles | upstream | atomic | positive | Page Geometry, Transformations, and Extraction | covered | upstream rotation rewrite |
| test_atomic.py::test_transformation_translate_scale_and_apply_on_point | upstream | atomic | positive | Page Geometry, Transformations, and Extraction | covered | upstream transformation rewrite |
| test_atomic.py::test_page_scale_by_updates_page_box | upstream | atomic | positive | Page Geometry, Transformations, and Extraction | covered | upstream scaling rewrite |
| test_atomic.py::test_annotation_dictionaries_expose_expected_public_entries | upstream | atomic | positive | Metadata, Forms, Outlines, Attachments, and Annotations | covered | upstream annotation object rewrite |
| test_atomic.py::test_polyline_rejects_empty_vertices | upstream | atomic | failure_path | Metadata, Forms, Outlines, Attachments, and Annotations | covered | upstream annotation error rewrite |
| test_atomic.py::test_free_text_font_style_entry_reflects_constructor_options | upstream | atomic | positive | Metadata, Forms, Outlines, Attachments, and Annotations | covered | upstream FreeText rewrite |
| test_integration.py::test_writer_add_annotation_roundtrip | upstream | system_e2e | positive | Metadata, Forms, Outlines, Attachments, and Annotations | covered | upstream annotation writer/reader rewrite |
| test_atomic.py::test_content_stream_data_roundtrip_on_decoded_stream | upstream | atomic | positive | Page Ranges, Generic Objects, and Constants | covered | upstream stream object rewrite |
| test_atomic.py::test_destination_exposes_title_page_and_fit_fields | upstream | atomic | positive | Page Ranges, Generic Objects, and Constants | covered | upstream Destination/Fit rewrite |
| test_atomic.py::test_hex_to_rgb_normalizes_channels | upstream | atomic | positive | Page Ranges, Generic Objects, and Constants | covered | upstream color utility rewrite |
| test_integration.py::test_reader_get_page_number_returns_none_for_foreign_page | upstream | integration | positive | Document Reading and Navigation | covered | upstream reader page-number rewrite |
| test_atomic.py::test_javascript_action_can_be_added_to_page_trigger | upstream | atomic | positive | Metadata, Forms, Outlines, Attachments, and Annotations | covered | upstream JavaScript page action rewrite |
| test_atomic.py::test_generated_pagerange_negative_single_page_indices | generated | atomic | positive | Page Ranges, Generic Objects, and Constants | covered | generated public PageRange test |
| test_atomic.py::test_generated_pagerange_reverse_all_indices | generated | atomic | positive | Page Ranges, Generic Objects, and Constants | covered | generated public PageRange test |
| test_atomic.py::test_generated_pagerange_empty_string_is_invalid | generated | atomic | failure_path | Error Semantics | covered | generated PageRange error test |
| test_atomic.py::test_generated_transformation_matrix_for_translate_and_scale | generated | atomic | positive | Page Geometry, Transformations, and Extraction | covered | generated transformation test |
| test_atomic.py::test_generated_matrix_multiplication_combines_translation | generated | atomic | positive | Page Geometry, Transformations, and Extraction | covered | generated matrix multiplication test |
| generated_tests.py::test_generated_permissions_all_is_32_bit_without_reserved_low_bits | generated | atomic | positive | Writing, Merging, and Serialization | source-only | excluded: hard-coded reserved permission bitmask is not a public behavior contract |
| test_atomic.py::test_generated_zero_permissions_verbose_mapping_is_all_false | generated | atomic | positive | Writing, Merging, and Serialization | covered | generated permissions test |
| test_atomic.py::test_generated_create_string_object_text_and_bytes_types | generated | atomic | positive | Page Ranges, Generic Objects, and Constants | covered | generated string object test |
| test_atomic.py::test_generated_decoded_stream_stores_replaced_bytes | generated | atomic | positive | Page Ranges, Generic Objects, and Constants | covered | generated stream object test |
| test_atomic.py::test_generated_destination_fit_horizontally_exposes_top | generated | atomic | positive | Page Ranges, Generic Objects, and Constants | covered | generated Destination/Fit test |
| test_atomic.py::test_generated_reader_empty_stream_raises_empty_file_error | generated | atomic | failure_path | Document Reading and Navigation | covered | generated empty input reader error test |
| test_integration.py::test_generated_blank_page_roundtrip_page_number_and_count | generated | system_e2e | positive | Cross-View Invariants | covered | generated page writer/read roundtrip |
| test_atomic.py::test_generated_insert_blank_page_uses_previous_dimensions_when_omitted | generated | atomic | positive | Writing, Merging, and Serialization | covered | generated blank-page insertion test |
| test_integration.py::test_generated_remove_page_changes_serialized_page_sequence | generated | system_e2e | positive | Cross-View Invariants | covered | generated remove-page roundtrip |
| test_integration.py::test_generated_append_reader_preserves_page_order | generated | system_e2e | positive | Cross-View Invariants | covered | generated append reader roundtrip |
| test_integration.py::test_generated_merge_reader_at_position_inserts_before_existing_page | generated | integration | positive | Writing, Merging, and Serialization | covered | generated merge position test |
| test_integration.py::test_generated_metadata_custom_key_survives_roundtrip | generated | system_e2e | positive | Cross-View Invariants | covered | generated metadata roundtrip |
| test_integration.py::test_generated_xmp_create_assign_and_read_title | generated | system_e2e | positive | Cross-View Invariants | covered | generated XMP roundtrip |
| test_integration.py::test_generated_duplicate_attachment_names_return_content_list | generated | system_e2e | positive | Cross-View Invariants | covered | generated attachment mapping roundtrip |
| test_integration.py::test_generated_attachment_delete_removes_writer_attachment | generated | integration | positive | Metadata, Forms, Outlines, Attachments, and Annotations | covered | generated attachment delete test |
| test_integration.py::test_generated_text_annotation_roundtrip_and_remove | generated | system_e2e | positive | Metadata, Forms, Outlines, Attachments, and Annotations | covered | generated annotation remove roundtrip |
| test_integration.py::test_generated_link_annotation_to_url_roundtrip | generated | system_e2e | positive | Metadata, Forms, Outlines, Attachments, and Annotations | covered | generated link annotation roundtrip |
| test_atomic.py::test_generated_page_action_delete_removes_action_dictionary | generated | atomic | positive | Metadata, Forms, Outlines, Attachments, and Annotations | covered | generated page action delete test |
| test_integration.py::test_generated_add_document_javascript_writes_names_entry | generated | integration | positive | Metadata, Forms, Outlines, Attachments, and Annotations | covered | generated document JavaScript test |
| test_atomic.py::test_generated_page_scale_to_updates_both_dimensions | generated | atomic | positive | Page Geometry, Transformations, and Extraction | covered | generated page scaling test |
| test_atomic.py::test_generated_add_transformation_without_expand_keeps_page_box | generated | atomic | positive | Page Geometry, Transformations, and Extraction | covered | generated transform boundary test |
| test_atomic.py::test_generated_transfer_rotation_to_content_resets_rotation | generated | atomic | positive | Page Geometry, Transformations, and Extraction | covered | generated rotation transfer test |
| test_integration.py::test_generated_encrypted_reader_wrong_password_does_not_unlock | generated | system_e2e | failure_path | Writing, Merging, and Serialization | covered | generated encryption wrong-password test |
| test_integration.py::test_generated_encrypted_reader_owner_password_unlocks_document | generated | system_e2e | positive | Writing, Merging, and Serialization | covered | generated owner-password roundtrip |
| test_integration.py::test_generated_reader_get_destination_page_number_for_outline | generated | system_e2e | positive | Document Reading and Navigation | covered | generated outline destination reader test |
| test_integration.py::test_generated_reader_get_page_returns_zero_based_page | generated | integration | positive | Document Reading and Navigation | covered | generated reader page access test |
| test_integration.py::test_generated_page_rotation_roundtrip_preserves_rotation | generated | system_e2e | positive | Cross-View Invariants | covered | generated rotation writer/read roundtrip |
| test_integration.py::test_generated_state_model_reader_projections_reflect_document_graph | generated | system_e2e | positive | State Model | covered | generated reader projection state-model test |
| test_integration.py::test_generated_state_model_writer_page_sequence_mutations_are_projected | generated | integration | positive | State Model | covered | generated writer projection state-model test |
| test_integration.py::test_generated_state_model_file_projection_roundtrips_written_bytes | generated | system_e2e | positive | State Model | covered | generated file projection state-model test |
| test_integration.py::test_generated_workflow_merge_transform_and_append_roundtrip | generated | system_e2e | positive | Representative Workflows | covered | generated merge/transform workflow test |
| test_integration.py::test_generated_workflow_clone_edit_encrypt_and_read_features | generated | system_e2e | positive | Representative Workflows | covered | generated clone/edit/encrypt workflow test |
| test_integration.py::test_generated_workflow_path_read_append_and_serialize | generated | system_e2e | positive | Representative Workflows | covered | generated path/read/append workflow test |
| test_integration.py::test_generated_workflow_feature_preservation_without_encryption | generated | system_e2e | positive | Representative Workflows | covered | generated feature preservation workflow test |
| test_atomic.py::test_generated_reader_get_page_out_of_range_raises_index_error | generated | atomic | failure_path | Error Semantics | covered | generated reader error test |

Total: 940 | kept upstream rewrites: 29 | generated: 39 | spec_gap: 0 | source-only: 35 | excluded upstream: 911 | final scoreable: 68
