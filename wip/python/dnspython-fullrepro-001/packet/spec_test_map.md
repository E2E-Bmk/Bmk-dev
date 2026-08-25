oracle_version: 2026-07-29-stage3-mixed-v1-oracle-split-specv1
oracle_source: upstream_plus_generated
oracle_files: test_atomic.py, test_integration.py
runtime_requirements: requirements.txt
scorer_isolation: --remove-path dns --pytest-arg=--rootdir=.
track_a_upstream_kept: 52
track_b_generated_kept: 30
depends_on_annotation_coverage: 30/30

| test_nodeid | layer | assertion_kind | spec_section | status | source | notes |
|-------------|-------|----------------|--------------|--------|--------|-------|
| test_atomic.py::test_name_from_text_absolute_preserves_root_label | atomic | positive | Name And Identifier Behavior | covered | upstream | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_name_from_text_relative_with_origin_derelativizes | atomic | positive | Name And Identifier Behavior | covered | upstream | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_name_without_origin_remains_relative | atomic | positive | Name And Identifier Behavior | covered | upstream | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_name_wire_round_trip_preserves_labels | atomic | positive | Name And Identifier Behavior | covered | upstream | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_relative_name_to_wire_without_origin_raises | atomic | failure_path | Name And Identifier Behavior | covered | upstream | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_name_parent_and_concatenate_behaviors | atomic | positive | Name And Identifier Behavior | covered | upstream | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_name_relation_helpers_share_fullcompare_result | atomic | positive | Name And Identifier Behavior | covered | upstream | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_name_relativize_and_derelativize_are_inverse_for_origin | atomic | positive | Name And Identifier Behavior | covered | upstream | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_unicode_name_uses_idna_projection | atomic | positive | Name And Identifier Behavior | covered | upstream | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_reverse_ipv4_round_trip | atomic | positive | Name And Identifier Behavior | covered | upstream | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_reverse_ipv6_round_trip | atomic | positive | Name And Identifier Behavior | covered | upstream | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_rdatatype_known_and_unknown_text_conversion | atomic | positive | Name And Identifier Behavior | covered | upstream | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_rdataclass_known_and_unknown_text_conversion | atomic | positive | Name And Identifier Behavior | covered | upstream | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_opcode_and_rcode_flag_round_trips | atomic | positive | Name And Identifier Behavior | covered | upstream | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_flags_text_round_trip | atomic | positive | Name And Identifier Behavior | covered | upstream | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_ttl_unit_text_parses_to_seconds | atomic | positive | Local Query, Address, And Metadata Behavior | covered | upstream | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_serial_arithmetic_wraps_at_32_bits | atomic | positive | Local Query, Address, And Metadata Behavior | covered | upstream | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_a_rdata_from_text_exposes_class_type_and_text | atomic | positive | Resource Data And Record Set Behavior | covered | upstream | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_rdata_wire_round_trip_preserves_text_payload | atomic | positive | Resource Data And Record Set Behavior | covered | upstream | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_unknown_rdata_uses_generic_payload | atomic | positive | Resource Data And Record Set Behavior | covered | upstream | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_malformed_rdata_text_raises_syntax_error | atomic | failure_path | Resource Data And Record Set Behavior | covered | upstream | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_rdataset_from_text_keeps_ttl_and_unique_records | atomic | positive | Local Query, Address, And Metadata Behavior | covered | upstream | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_rdataset_rejects_incompatible_rdata | atomic | failure_path | Resource Data And Record Set Behavior | covered | upstream | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_rrset_from_text_preserves_owner_and_rdataset | atomic | positive | Resource Data And Record Set Behavior | covered | upstream | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_rrset_match_and_full_match_use_owner_and_record_data | atomic | positive | Resource Data And Record Set Behavior | covered | upstream | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_make_query_creates_question_rrset | atomic | positive | Resource Data And Record Set Behavior | covered | upstream | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_message_short_wire_header_raises | atomic | failure_path | Message And Update Behavior | covered | upstream | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_message_opcode_rcode_and_flags_project_through_methods | atomic | positive | Name And Identifier Behavior | covered | upstream | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_resolver_nameserver_assignment_normalizes_public_state | atomic | positive | Name And Identifier Behavior | covered | upstream | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_resolver_query_alias_is_resolve_method | atomic | positive | Zone, Transaction, And Resolver Behavior | covered | upstream | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_resolver_cache_put_get_flush_and_statistics | atomic | positive | Zone, Transaction, And Resolver Behavior | covered | upstream | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_lru_cache_evicts_least_recently_used_entry | atomic | positive | Zone, Transaction, And Resolver Behavior | covered | upstream | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_generic_edns_option_wire_round_trip_preserves_payload | atomic | positive | Local Query, Address, And Metadata Behavior | covered | upstream | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_ede_option_preserves_code_and_text_projection | atomic | positive | Cross-View Invariants | covered | upstream | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_tsigkeyring_text_round_trip_preserves_key_name_and_secret | atomic | positive | Name And Identifier Behavior | covered | upstream | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_e164_helpers_round_trip_number_with_origin | atomic | positive | Local Query, Address, And Metadata Behavior | covered | upstream | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_generated_name_split_and_choose_relativity | atomic | positive | Name And Identifier Behavior | covered | generated | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_generated_name_successor_and_predecessor_are_ordered | atomic | positive | Name And Identifier Behavior | covered | generated | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_generated_bad_escape_raises_public_exception | atomic | failure_path | Cross-View Invariants | covered | generated | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_generated_absolute_name_wire_with_origin_ignores_origin | atomic | positive | Name And Identifier Behavior | covered | generated | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_generated_mx_rdata_text_and_wire_preserve_exchange_name | atomic | positive | Name And Identifier Behavior | covered | generated | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_generated_rdataset_update_ttl_replaces_visible_ttl | atomic | positive | Local Query, Address, And Metadata Behavior | covered | generated | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_generated_rdataset_union_and_intersection_keep_compatible_members | atomic | positive | Resource Data And Record Set Behavior | covered | generated | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_generated_zone_find_node_create_false_raises_key_error | atomic | failure_path | Zone, Transaction, And Resolver Behavior | covered | generated | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_generated_resolver_cache_expired_entry_is_miss | atomic | positive | Zone, Transaction, And Resolver Behavior | covered | generated | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_generated_lru_cache_flush_selected_key_only | atomic | positive | Zone, Transaction, And Resolver Behavior | covered | generated | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_generated_resolver_reset_replaces_default_resolver | atomic | positive | Zone, Transaction, And Resolver Behavior | covered | generated | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_generated_edns_ecs_option_preserves_address_prefix_and_scope | atomic | positive | Local Query, Address, And Metadata Behavior | covered | generated | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_generated_cookie_option_preserves_client_and_server_cookie | atomic | positive | Local Query, Address, And Metadata Behavior | covered | generated | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_generated_tsigkeyring_accepts_dns_name_keys | atomic | positive | Name And Identifier Behavior | covered | generated | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_generated_zone_unknown_origin_error_for_relative_zone_without_origin | atomic | failure_path | Zone, Transaction, And Resolver Behavior | covered | generated | public API behavioral coverage; docstring cites clause IDs |
| test_atomic.py::test_generated_message_trailing_junk_parse_raises | atomic | failure_path | Message And Update Behavior | covered | generated | public API behavioral coverage; docstring cites clause IDs |
| test_integration.py::test_message_wire_round_trip_preserves_question | integration | positive | Message And Update Behavior | covered | upstream | public cross-view behavior; depends_on annotated |
| test_integration.py::test_make_response_satisfies_query_response_relationship | integration | positive | Message And Update Behavior | covered | upstream | public cross-view behavior; depends_on annotated |
| test_integration.py::test_message_find_and_get_rrset_section_behavior | integration | positive | Resource Data And Record Set Behavior | covered | upstream | public cross-view behavior; depends_on annotated |
| test_integration.py::test_message_trailing_junk_raises_when_disallowed | integration | failure_path | Message And Update Behavior | covered | upstream | public cross-view behavior; depends_on annotated |
| test_integration.py::test_message_use_edns_and_want_dnssec_configures_options | integration | positive | Message And Update Behavior | covered | upstream | public cross-view behavior; depends_on annotated |
| test_integration.py::test_message_text_round_trip_preserves_question | integration | positive | Message And Update Behavior | covered | upstream | public cross-view behavior; depends_on annotated |
| test_integration.py::test_update_message_add_delete_replace_sections_are_visible | integration | positive | Message And Update Behavior | covered | upstream | public cross-view behavior; depends_on annotated |
| test_integration.py::test_update_message_prerequisite_present_and_absent_sections | integration | positive | Message And Update Behavior | covered | upstream | public cross-view behavior; depends_on annotated |
| test_integration.py::test_zone_from_text_builds_origin_and_required_nodes | integration | positive | Zone, Transaction, And Resolver Behavior | covered | upstream | public cross-view behavior; depends_on annotated |
| test_integration.py::test_zone_replace_and_delete_rdataset_mutates_node_state | integration | positive | Resource Data And Record Set Behavior | covered | upstream | public cross-view behavior; depends_on annotated |
| test_integration.py::test_zone_iteration_exposes_owner_ttl_and_rdata | integration | positive | Local Query, Address, And Metadata Behavior | covered | upstream | public cross-view behavior; depends_on annotated |
| test_integration.py::test_zone_to_text_contains_public_record_facts | integration | positive | Zone, Transaction, And Resolver Behavior | covered | upstream | public cross-view behavior; depends_on annotated |
| test_integration.py::test_zone_origin_check_requires_soa_and_ns | integration | failure_path | Zone, Transaction, And Resolver Behavior | covered | upstream | public cross-view behavior; depends_on annotated |
| test_integration.py::test_zone_reader_is_read_only_and_writer_commits | integration | positive | Zone, Transaction, And Resolver Behavior | covered | upstream | public cross-view behavior; depends_on annotated |
| test_integration.py::test_query_response_relationship_detects_wrong_question | integration | positive | Message And Update Behavior | covered | upstream | public cross-view behavior; depends_on annotated |
| test_integration.py::test_generated_rrset_to_wire_and_message_parse_preserve_answer | integration | positive | Resource Data And Record Set Behavior | covered | generated | public cross-view behavior; depends_on annotated |
| test_integration.py::test_generated_message_section_number_round_trip | integration | positive | Message And Update Behavior | covered | generated | public cross-view behavior; depends_on annotated |
| test_integration.py::test_generated_message_get_options_filters_by_type | integration | positive | Message And Update Behavior | covered | generated | public cross-view behavior; depends_on annotated |
| test_integration.py::test_generated_message_from_file_reads_one_text_message | integration | positive | Message And Update Behavior | covered | generated | public cross-view behavior; depends_on annotated |
| test_integration.py::test_generated_update_replace_creates_delete_then_add_sequence | integration | positive | Message And Update Behavior | covered | generated | public cross-view behavior; depends_on annotated |
| test_integration.py::test_generated_update_text_wire_round_trip_preserves_sections | integration | positive | Message And Update Behavior | covered | generated | public cross-view behavior; depends_on annotated |
| test_integration.py::test_generated_zone_get_soa_returns_origin_record | integration | positive | Zone, Transaction, And Resolver Behavior | covered | generated | public cross-view behavior; depends_on annotated |
| test_integration.py::test_generated_zone_file_round_trip_via_string_buffer | integration | positive | Zone, Transaction, And Resolver Behavior | covered | generated | public cross-view behavior; depends_on annotated |
| test_integration.py::test_generated_zone_writer_delete_removes_committed_rdataset | integration | positive | Resource Data And Record Set Behavior | covered | generated | public cross-view behavior; depends_on annotated |
| test_integration.py::test_generated_message_edns_option_survives_wire_parse | integration | positive | Message And Update Behavior | covered | generated | public cross-view behavior; depends_on annotated |
| test_integration.py::test_generated_enum_message_flag_views_agree | integration | positive | Message And Update Behavior | covered | generated | public cross-view behavior; depends_on annotated |
| test_integration.py::test_udp_socket_send_receive_round_trip_local_message | system_e2e | positive | Message And Update Behavior | covered | upstream | public workflow/cross-view behavior; depends_on annotated |
| test_integration.py::test_generated_message_question_answer_zone_integration | system_e2e | positive | Message And Update Behavior | covered | generated | public workflow/cross-view behavior; depends_on annotated |
| test_integration.py::test_generated_dynamic_update_and_zone_apply_same_owner_name | system_e2e | positive | Name And Identifier Behavior | covered | generated | public workflow/cross-view behavior; depends_on annotated |
| test_integration.py::test_generated_rdataset_rrset_message_zone_cross_view_membership | system_e2e | positive | Resource Data And Record Set Behavior | covered | generated | public workflow/cross-view behavior; depends_on annotated |

Total: 82 | kept (covered): 82 | spec_gap: 0 | source-only: 0 | excluded: 0 | final_scoreable: 82
