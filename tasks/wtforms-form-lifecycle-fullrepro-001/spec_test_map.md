# Spec Test Map

| test_nodeid | layer | spec_section | status | notes |
|---|---|---|---|---|
| oracle/test_integration.py::test_string_input_reaches_field_and_form_data[x-x] | integration | Scalar and temporal fields; Consistency Invariants | covered | Submitted string retention and matching form-data projection. |
| oracle/test_integration.py::test_string_input_reaches_field_and_form_data[-] | integration | Scalar and temporal fields; Consistency Invariants | covered | Submitted string retention and matching form-data projection. |
| oracle/test_integration.py::test_string_input_reaches_field_and_form_data[first-first] | integration | Scalar and temporal fields; Consistency Invariants | covered | Submitted string retention and matching form-data projection. |
| oracle/test_atomic.py::test_integer_input_is_coerced[1-1] | atomic | Scalar and temporal fields | covered | Documented IntegerField coercion. |
| oracle/test_atomic.py::test_integer_input_is_coerced[0-0] | atomic | Scalar and temporal fields | covered | Documented IntegerField coercion. |
| oracle/test_atomic.py::test_integer_input_is_coerced[-9--9] | atomic | Scalar and temporal fields | covered | Documented IntegerField coercion. |
| oracle/test_atomic.py::test_invalid_integer_is_reported_by_validation[bad] | atomic | Error Semantics | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_invalid_integer_is_reported_by_validation[1.2] | atomic | Error Semantics | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_invalid_integer_is_reported_by_validation[] | atomic | Error Semantics | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_boolean_field_uses_documented_false_values[false-False] | atomic | Scalar and temporal fields | covered | Documented BooleanField false-value processing. |
| oracle/test_atomic.py::test_boolean_field_uses_documented_false_values[-False] | atomic | Scalar and temporal fields | covered | Documented BooleanField false-value processing. |
| oracle/test_atomic.py::test_boolean_field_uses_documented_false_values[yes-True] | atomic | Scalar and temporal fields | covered | Documented BooleanField false-value processing. |
| oracle/test_atomic.py::test_submit_field_is_false_when_missing | atomic | Scalar and temporal fields | covered | Documented SubmitField BooleanField behavior. |
| oracle/test_atomic.py::test_float_field_coerces_public_values[1.5-1.5] | atomic | Scalar and temporal fields | covered | Documented FloatField coercion. |
| oracle/test_atomic.py::test_float_field_coerces_public_values[0-0.0] | atomic | Scalar and temporal fields | covered | Documented FloatField coercion. |
| oracle/test_atomic.py::test_float_field_coerces_public_values[-2--2.0] | atomic | Scalar and temporal fields | covered | Documented FloatField coercion. |
| oracle/test_atomic.py::test_decimal_field_coerces_submitted_text[1.20-expected0] | atomic | Scalar and temporal fields | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_decimal_field_coerces_submitted_text[0-expected1] | atomic | Scalar and temporal fields | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_decimal_field_coerces_submitted_text[-3.5-expected2] | atomic | Scalar and temporal fields | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_date_field_parses_documented_format[2024-01-02-expected0] | atomic | Scalar and temporal fields | covered | Documented DateField parsing. |
| oracle/test_atomic.py::test_date_field_parses_documented_format[2000-12-31-expected1] | atomic | Scalar and temporal fields | covered | Documented DateField parsing. |
| oracle/test_atomic.py::test_date_field_parses_documented_format[1999-01-01-expected2] | atomic | Scalar and temporal fields | covered | Documented DateField parsing. |
| oracle/test_atomic.py::test_password_field_keeps_submitted_data | atomic | Scalar and temporal fields | covered | Documented PasswordField submitted-data behavior. |
| oracle/test_integration.py::test_select_field_selection_and_validation[a-True] | integration | Choice fields, datalists, and nesting; Consistency Invariants | covered | Choice membership and selected-choice projection. |
| oracle/test_integration.py::test_select_field_selection_and_validation[b-True] | integration | Choice fields, datalists, and nesting; Consistency Invariants | covered | Choice membership and selected-choice projection. |
| oracle/test_integration.py::test_select_field_selection_and_validation[z-False] | integration | Choice fields, datalists, and nesting; Consistency Invariants | covered | Choice membership rejection. |
| oracle/test_integration.py::test_select_multiple_preserves_all_values_and_rejects_invalid_members[values0-True] | integration | Choice fields, datalists, and nesting; Consistency Invariants | covered | Multiple-choice list coercion and membership. |
| oracle/test_integration.py::test_select_multiple_preserves_all_values_and_rejects_invalid_members[values1-True] | integration | Choice fields, datalists, and nesting; Consistency Invariants | covered | Multiple-choice list coercion and membership. |
| oracle/test_integration.py::test_select_multiple_preserves_all_values_and_rejects_invalid_members[values2-False] | integration | Choice fields, datalists, and nesting; Consistency Invariants | covered | Multiple-choice invalid-member rejection. |
| oracle/test_integration.py::test_select_can_disable_membership_validation | integration | Choice fields, datalists, and nesting | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_missing_choices_raise_when_membership_is_required | atomic | Error Semantics | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_data_required_uses_post_coercion_truthiness[x-True] | atomic | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_data_required_uses_post_coercion_truthiness[-False] | atomic | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_data_required_uses_post_coercion_truthiness[   -False] | atomic | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_input_required_requires_nonempty_submitted_raw_data[raw0-None-True] | atomic | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_input_required_requires_nonempty_submitted_raw_data[raw1-None-False] | atomic | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_input_required_requires_nonempty_submitted_raw_data[None-default-False] | atomic | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_integration.py::test_optional_stops_following_data_required_for_empty_input | integration | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_length_enforces_inclusive_bounds[ab-True] | atomic | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_length_enforces_inclusive_bounds[a-False] | atomic | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_length_enforces_inclusive_bounds[abcd-False] | atomic | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_length_rejects_unbounded_constructor | atomic | Error Semantics | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_number_range_is_inclusive[3-True] | atomic | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_number_range_is_inclusive[2-True] | atomic | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_number_range_is_inclusive[5-False] | atomic | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_number_range_rejects_nan | atomic | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_integration.py::test_equal_to_compares_named_field_data[x-x-True] | integration | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_integration.py::test_equal_to_compares_named_field_data[x-y-False] | integration | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_integration.py::test_equal_to_compares_named_field_data[--True] | integration | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_regexp_uses_prefix_matching_by_default[abc-True] | atomic | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_regexp_uses_prefix_matching_by_default[xabc-False] | atomic | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_regexp_uses_prefix_matching_by_default[-False] | atomic | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_ip_address_honors_enabled_family[127.0.0.1-True] | atomic | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_ip_address_honors_enabled_family[::1-False] | atomic | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_ip_address_honors_enabled_family[not-ip-False] | atomic | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_ip_address_requires_an_enabled_family | atomic | Error Semantics | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_mac_address_requires_colon_hex_octets[aa:bb:cc:dd:ee:ff-True] | atomic | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_mac_address_requires_colon_hex_octets[aa-bb-cc-dd-ee-ff-False] | atomic | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_mac_address_requires_colon_hex_octets[xx:bb:cc:dd:ee:ff-False] | atomic | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_url_requires_scheme_host_and_valid_port[https://example.com-True] | atomic | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_url_requires_scheme_host_and_valid_port[https://example.com:bad-False] | atomic | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_url_requires_scheme_host_and_valid_port[example.com-False] | atomic | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_uuid_accepts_parseable_uuid_text[123e4567-e89b-12d3-a456-426614174000-True] | atomic | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_uuid_accepts_parseable_uuid_text[not-a-uuid-False] | atomic | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_uuid_accepts_parseable_uuid_text[-False] | atomic | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_any_of_accepts_members_and_list_intersection[a-True] | atomic | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_any_of_accepts_members_and_list_intersection[z-False] | atomic | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_any_of_accepts_members_and_list_intersection[value2-True] | atomic | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_none_of_rejects_members_and_list_intersection[z-True] | atomic | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_none_of_rejects_members_and_list_intersection[a-False] | atomic | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_none_of_rejects_members_and_list_intersection[value2-False] | atomic | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_integration.py::test_readonly_rejects_changed_value_and_sets_flag | integration | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_integration.py::test_disabled_rejects_submitted_value_and_sets_flag | integration | Validator predicates | covered | Public v3 behavioral contract. |
| oracle/test_integration.py::test_form_data_precedence_beats_object_kwargs_and_data | system_e2e | Forms and data processing | covered | Complete documented source-precedence order. |
| oracle/test_integration.py::test_object_precedence_beats_kwargs_and_data | integration | Forms and data processing | covered | Public v3 behavioral contract. |
| oracle/test_integration.py::test_kwargs_precedence_beats_data_and_default | integration | Forms and data processing | covered | Public v3 behavioral contract. |
| oracle/test_integration.py::test_declared_extra_and_inline_filters_run_in_order | integration | Forms and data processing | covered | Public v3 behavioral contract. |
| oracle/test_integration.py::test_filter_value_error_becomes_processing_error | integration | Error Semantics | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_form_item_access_and_missing_key_behavior | atomic | Forms and data processing | covered | Public v3 behavioral contract. |
| oracle/test_integration.py::test_populate_obj_overwrites_matching_attribute | system_e2e | Forms and data processing | covered | Documented populate_obj assignment behavior. |
| oracle/test_integration.py::test_form_field_projects_nested_data_and_errors | system_e2e | Choice fields, datalists, and nesting; Consistency Invariants | covered | Nested FormField data/error projection. |
| oracle/test_integration.py::test_field_list_compacts_sparse_input_indices | integration | Choice fields, datalists, and nesting; Consistency Invariants | covered | Sparse FieldList compaction and contiguous public names. |
| oracle/test_integration.py::test_field_list_min_entries_creates_blank_entries | integration | Choice fields, datalists, and nesting | covered | Public v3 behavioral contract. |
| oracle/test_integration.py::test_field_list_append_insert_and_pop_preserve_order | integration | Choice fields, datalists, and nesting | covered | Public v3 behavioral contract. |
| oracle/test_integration.py::test_default_meta_disables_translations_for_false_locales | integration | Meta, CSRF, and translations | covered | Public v3 behavioral contract. |
| oracle/test_integration.py::test_default_meta_rejects_plain_mapping_formdata | integration | Meta, CSRF, and translations | covered | Public v3 behavioral contract. |
| oracle/test_integration.py::test_default_meta_accepts_getlist_adapter | integration | Meta, CSRF, and translations | covered | Public v3 behavioral contract. |
| oracle/test_atomic.py::test_rendering_returns_html_safe_value_without_exact_markup_contract | atomic | Fields, validation, and rendering | covered | HTML-safe public rendering interface without markup bytes. |
| oracle/test_integration.py::test_invalid_extra_validator_raises_type_error_before_field_validation | integration | Forms and data processing; Error Semantics | covered | Invalid extra validator is rejected before the declared validator chain runs. |
