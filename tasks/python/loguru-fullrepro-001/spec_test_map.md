# Spec Test Map: loguru-fullrepro-001

oracle_version: 2026-07-19-stage3-mixed-v6-specv3
oracle_source: mixed
upstream_rewritten_retained: 51
generated_retained: 82
dummy_gate: 0 passed, 0 failed, 133 errors
reference_gate: 133/133 passed
scorer_isolation: --remove-path loguru

## Section Coverage

| spec_section | covered_tests |
| --- | ---: |
| section Application Logging To Console And File | 3 |
| section Async Sink Completion | 3 |
| section Async, Threads, Processes, And Completion | 4 |
| section Context, Patching, And Per-Call Options | 19 |
| section Cross-View Invariants | 6 |
| section Environment | 4 |
| section Error Semantics | 23 |
| section Exception Guard | 3 |
| section Exceptions And Standard Logging Interop | 3 |
| section File Sinks And Generated Files | 6 |
| section Formatting, Records, Colors, And Serialization | 6 |
| section Installable Surface | 3 |
| section Invocation Protocol | 3 |
| section Levels, Filtering, Activation, And Configuration | 12 |
| section Library Quiet By Default | 3 |
| section Parsing Generated Logs | 3 |
| section Parsing Logged Files | 9 |
| section Product Overview | 3 |
| section Product State Model | 4 |
| section Public API | 3 |
| section Sink Registration And Message Emission | 7 |
| section Type Hints | 3 |

## Test Map

| test_nodeid | source | layer | spec_section | status | notes |
|-------------|--------|-------|--------------|--------|-------|
| filter/rewritten_upstream_tests.py::test_remove_simple | upstream | atomic | section Sink Registration And Message Emission | covered | public-API rewrite of tests/test_remove.py::test_remove_simple; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_remove_all | upstream | integration | section Product State Model | covered | public-API rewrite of tests/test_remove.py::test_remove_all; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_remove_enqueue | upstream | integration | section Async, Threads, Processes, And Completion | covered | public-API rewrite of tests/test_remove.py::test_remove_enqueue; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_remove_enqueue_filesink | upstream | integration | section Async, Threads, Processes, And Completion | covered | public-API rewrite of tests/test_remove.py::test_remove_enqueue_filesink; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_invalid_handler_id_value | upstream | atomic | section Error Semantics | covered | public-API rewrite of tests/test_remove.py::test_invalid_handler_id_value; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_invalid_handler_id_type[handler_id0] | upstream | atomic | section Error Semantics | covered | public-API rewrite of tests/test_remove.py::test_invalid_handler_id_type; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_invalid_handler_id_type[sys] | upstream | atomic | section Error Semantics | covered | public-API rewrite of tests/test_remove.py::test_invalid_handler_id_type; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_invalid_handler_id_type[handler_id2] | upstream | atomic | section Error Semantics | covered | public-API rewrite of tests/test_remove.py::test_invalid_handler_id_type; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_invalid_handler_id_type[int] | upstream | atomic | section Error Semantics | covered | public-API rewrite of tests/test_remove.py::test_invalid_handler_id_type; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_bind_after_add | upstream | integration | section Context, Patching, And Per-Call Options | covered | public-API rewrite of tests/test_bind.py::test_after_add; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_bind_before_add | upstream | integration | section Context, Patching, And Per-Call Options | covered | public-API rewrite of tests/test_bind.py::test_before_add; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_add_using_bound | upstream | integration | section Context, Patching, And Per-Call Options | covered | public-API rewrite of tests/test_bind.py::test_add_using_bound; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_bound_logger_does_not_override_parent | upstream | integration | section Context, Patching, And Per-Call Options | covered | public-API rewrite of tests/test_bind.py::test_not_override_parent_logger; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_override_previous_bound | upstream | integration | section Context, Patching, And Per-Call Options | covered | public-API rewrite of tests/test_bind.py::test_override_previous_bound; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_bind_and_add_level | upstream | integration | section Levels, Filtering, Activation, And Configuration | covered | public-API rewrite of tests/test_bind.py::test_bind_and_add_level; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_patch_after_add | upstream | integration | section Context, Patching, And Per-Call Options | covered | public-API rewrite of tests/test_patch.py::test_after_add; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_patch_before_add | upstream | integration | section Context, Patching, And Per-Call Options | covered | public-API rewrite of tests/test_patch.py::test_before_add; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_add_using_patched | upstream | integration | section Context, Patching, And Per-Call Options | covered | public-API rewrite of tests/test_patch.py::test_add_using_patched; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_multiple_patches | upstream | integration | section Context, Patching, And Per-Call Options | covered | public-API rewrite of tests/test_patch.py::test_multiple_patches; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_contextualize | upstream | integration | section Context, Patching, And Per-Call Options | covered | public-API rewrite of tests/test_contextualize.py::test_contextualize; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_contextualize_as_decorator | upstream | integration | section Context, Patching, And Per-Call Options | covered | public-API rewrite of tests/test_contextualize.py::test_contextualize_as_decorator; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_contextualize_reset | upstream | integration | section Context, Patching, And Per-Call Options | covered | public-API rewrite of tests/test_contextualize.py::test_contextualize_reset; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_contextualize_async | upstream | system_e2e | section Async, Threads, Processes, And Completion | covered | public-API rewrite of tests/test_contextualize.py::test_contextualize_async; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_contextualize_thread | upstream | system_e2e | section Async, Threads, Processes, And Completion | covered | public-API rewrite of tests/test_contextualize.py::test_contextualize_thread; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_contextualize_before_bind | upstream | integration | section Cross-View Invariants | covered | public-API rewrite of tests/test_contextualize.py::test_contextualize_before_bind; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_context_reset_despite_error | upstream | integration | section Error Semantics | covered | public-API rewrite of tests/test_contextualize.py::test_contextualize_reset_despite_error; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_log_int_level | upstream | atomic | section Levels, Filtering, Activation, And Configuration | covered | public-API rewrite of tests/test_levels.py::test_log_int_level; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_log_str_level | upstream | atomic | section Levels, Filtering, Activation, And Configuration | covered | public-API rewrite of tests/test_levels.py::test_log_str_level; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_add_level_then_log_with_int_value | upstream | integration | section Levels, Filtering, Activation, And Configuration | covered | public-API rewrite of tests/test_levels.py::test_add_level_then_log_with_int_value; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_edit_existing_level | upstream | atomic | section Levels, Filtering, Activation, And Configuration | covered | public-API rewrite of tests/test_levels.py::test_edit_existing_level; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_get_level | upstream | atomic | section Levels, Filtering, Activation, And Configuration | covered | public-API rewrite of tests/test_levels.py::test_get_level using documented level metadata attributes; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_get_existing_level | upstream | atomic | section Levels, Filtering, Activation, And Configuration | covered | public-API rewrite of tests/test_levels.py::test_get_existing_level; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_updating_level_no_not_allowed_default | upstream | atomic | section Error Semantics | covered | public-API rewrite of tests/test_levels.py::test_updating_level_no_not_allowed_default; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_log_invalid_level_type[3.4] | upstream | atomic | section Error Semantics | covered | public-API rewrite of tests/test_levels.py::test_log_invalid_level_type; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_log_invalid_level_type[level1] | upstream | atomic | section Error Semantics | covered | public-API rewrite of tests/test_levels.py::test_log_invalid_level_type; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_log_invalid_level_type[level2] | upstream | atomic | section Error Semantics | covered | public-API rewrite of tests/test_levels.py::test_log_invalid_level_type; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_log_invalid_level_value[-1] | upstream | atomic | section Error Semantics | covered | public-API rewrite of tests/test_levels.py::test_log_invalid_level_value; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_log_invalid_level_value[-999] | upstream | atomic | section Error Semantics | covered | public-API rewrite of tests/test_levels.py::test_log_invalid_level_value; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_log_unknown_level[unknown_level_for_loguru_stage3] | upstream | atomic | section Error Semantics | covered | public-API rewrite of tests/test_levels.py::test_log_unknown_level; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_log_unknown_level[debug] | upstream | atomic | section Error Semantics | covered | public-API rewrite of tests/test_levels.py::test_log_unknown_level; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_parse_file | upstream | atomic | section Parsing Logged Files | covered | public-API rewrite of tests/test_parse.py::test_file; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_parse_fileobj | upstream | atomic | section Parsing Logged Files | covered | public-API rewrite of tests/test_parse.py::test_fileobj; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_parse_pathlib | upstream | atomic | section Parsing Logged Files | covered | public-API rewrite of tests/test_parse.py::test_pathlib; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_parse_regex_pattern | upstream | atomic | section Parsing Logged Files | covered | public-API rewrite of tests/test_parse.py::test_regex_pattern; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_parse_multiline_pattern | upstream | atomic | section Parsing Logged Files | covered | public-API rewrite of tests/test_parse.py::test_regex_multiline; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_parse_without_group | upstream | atomic | section Parsing Logged Files | covered | public-API rewrite of tests/test_parse.py::test_no_group; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_parse_bytes | upstream | atomic | section Parsing Logged Files | covered | public-API rewrite of tests/test_parse.py::test_bytes; spec_v3 explicitly covers binary file objects with bytes patterns |
| filter/rewritten_upstream_tests.py::test_parse_cast_dict | upstream | atomic | section Parsing Logged Files | covered | public-API rewrite of tests/test_parse.py::test_cast_dict; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_parse_cast_function | upstream | atomic | section Parsing Logged Files | covered | public-API rewrite of tests/test_parse.py::test_cast_function; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_invalid_file | upstream | atomic | section Error Semantics | covered | public-API rewrite of tests/test_parse.py::test_invalid_file; reference gate passed and dummy gate did not pass |
| filter/rewritten_upstream_tests.py::test_invalid_pattern | upstream | atomic | section Error Semantics | covered | public-API rewrite of tests/test_parse.py::test_invalid_pattern; spec_v3 explicitly covers invalid pattern TypeError |
| filter/generated_tests.py::test_imported_logger_emits_to_public_sink | generated | atomic | section Product Overview | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_module_logger_is_same_public_object | generated | atomic | section Product Overview | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_version_is_public_non_empty_string | generated | atomic | section Installable Surface | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_public_logger_works_without_user_constructor | generated | integration | section Installable Surface | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_import_surface_remains_reusable_after_handler_changes | generated | integration | section Installable Surface | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_importlib_protocol_exposes_logger_object | generated | atomic | section Invocation Protocol | covered | public-only generated test retained from prior Stage 3 refresh; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_from_import_protocol_uses_installed_package_logger | generated | atomic | section Invocation Protocol | covered | public-only generated test retained from prior Stage 3 refresh; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_import_protocol_exposes_version_on_module | generated | atomic | section Invocation Protocol | covered | public-only generated test retained from prior Stage 3 refresh; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_logger_coordinates_formatting_record_and_sink_delivery | generated | integration | section Product Overview | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_add_returns_distinct_integer_handler_ids | generated | atomic | section Public API | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_remove_deactivates_one_handler_only | generated | integration | section Product State Model | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_remove_without_id_removes_all_handlers | generated | atomic | section Product State Model | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_remove_unknown_handler_id_raises_value_error | generated | atomic | section Error Semantics | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_remove_invalid_handler_id_type_raises_type_error | generated | atomic | section Error Semantics | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_default_add_level_is_debug_when_environment_unset | generated | atomic | section Environment | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_callable_sink_receives_string_like_message_with_record | generated | atomic | section Sink Registration And Message Emission | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_record_contains_documented_core_keys | generated | atomic | section Formatting, Records, Colors, And Serialization | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_record_level_exposes_name_number_and_icon_not_color | generated | atomic | section Type Hints | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_format_string_uses_positional_and_keyword_arguments | generated | atomic | section Formatting, Records, Colors, And Serialization | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_format_callable_receives_record | generated | atomic | section Sink Registration And Message Emission | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_format_argument_mismatch_raises | generated | atomic | section Error Semantics | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_filter_callable_selects_records | generated | atomic | section Sink Registration And Message Emission | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_filter_string_matches_module_namespace | generated | atomic | section Sink Registration And Message Emission | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_filter_dict_threshold_combines_with_handler_level | generated | integration | section Levels, Filtering, Activation, And Configuration | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_handler_level_threshold_rejects_lower_records | generated | atomic | section Sink Registration And Message Emission | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_sink_exception_propagates_when_catch_false | generated | atomic | section Error Semantics | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_sink_exception_is_suppressed_when_catch_true | generated | atomic | section Error Semantics | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_serialize_outputs_json_text_and_record | generated | atomic | section Formatting, Records, Colors, And Serialization | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_colorize_true_converts_markup_to_ansi | generated | atomic | section Formatting, Records, Colors, And Serialization | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_colorize_false_strips_format_markup | generated | atomic | section Formatting, Records, Colors, And Serialization | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_colorize_none_uses_stream_tty_detection | generated | integration | section Formatting, Records, Colors, And Serialization | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_colorize_none_is_false_for_path_sink | generated | integration | section Environment | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_no_color_environment_disables_standard_stream_auto_color | generated | integration | section Environment | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_force_color_environment_enables_standard_stream_auto_color | generated | integration | section Environment | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_bind_adds_extra_without_mutating_parent_logger | generated | integration | section Context, Patching, And Per-Call Options | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_contextualize_adds_and_restores_extra | generated | integration | section Context, Patching, And Per-Call Options | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_extra_conflict_precedence_call_over_bind_over_context_over_configure | generated | system_e2e | section Cross-View Invariants | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_contextualize_isolated_across_async_tasks | generated | integration | section Context, Patching, And Per-Call Options | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_patch_mutates_record_seen_by_formatter | generated | integration | section Context, Patching, And Per-Call Options | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_configured_patcher_runs_before_logger_view_patcher | generated | system_e2e | section Cross-View Invariants | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_opt_raw_bypasses_handler_format | generated | atomic | section Context, Patching, And Per-Call Options | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_opt_record_allows_record_placeholder_in_message | generated | atomic | section Context, Patching, And Per-Call Options | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_opt_lazy_defers_callable_when_record_filtered_out | generated | integration | section Sink Registration And Message Emission | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_opt_capture_false_excludes_kwargs_from_extra | generated | atomic | section Context, Patching, And Per-Call Options | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_builtin_levels_have_documented_numbers | generated | atomic | section Levels, Filtering, Activation, And Configuration | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_custom_level_can_be_created_and_used | generated | atomic | section Levels, Filtering, Activation, And Configuration | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_existing_level_color_and_icon_can_be_updated | generated | atomic | section Levels, Filtering, Activation, And Configuration | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_unknown_level_query_raises_value_error | generated | atomic | section Error Semantics | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_disable_and_enable_module_namespace | generated | integration | section Library Quiet By Default | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_disabled_namespace_suppresses_records_added_after_disable | generated | integration | section Library Quiet By Default | covered | public-only generated workflow test retained from prior Stage 3 refresh; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_enable_restores_only_subsequent_library_records | generated | integration | section Library Quiet By Default | covered | public-only generated workflow test retained from prior Stage 3 refresh; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_configure_replaces_handlers_and_returns_new_ids | generated | integration | section Levels, Filtering, Activation, And Configuration | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_configure_extra_is_visible_to_formatters | generated | integration | section Product State Model | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_file_sink_writes_accepted_records | generated | integration | section File Sinks And Generated Files | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_application_workflow_writes_console_and_file_views | generated | system_e2e | section Application Logging To Console And File | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_application_workflow_keeps_console_threshold_above_file | generated | system_e2e | section Application Logging To Console And File | covered | public-only generated workflow test retained from prior Stage 3 refresh; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_application_workflow_bound_context_is_written_to_file | generated | system_e2e | section Application Logging To Console And File | covered | public-only generated workflow test retained from prior Stage 3 refresh; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_file_sink_creates_parent_directories | generated | atomic | section File Sinks And Generated Files | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_file_sink_delay_opens_on_first_message | generated | atomic | section File Sinks And Generated Files | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_file_sink_rotation_creates_multiple_files | generated | integration | section File Sinks And Generated Files | covered | public-only generated test; spec_v3 explicitly covers byte-size rotation strings; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_file_sink_compression_creates_gzip_rotated_file | generated | integration | section File Sinks And Generated Files | covered | public-only generated test; spec_v3 explicitly covers gzip compression alias `gz`; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_file_sink_watch_reopens_replaced_file | generated | integration | section File Sinks And Generated Files | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_enqueue_complete_drains_queued_messages | generated | integration | section Async Sink Completion | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_coroutine_sink_is_completed_by_awaitable | generated | integration | section Async Sink Completion | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_complete_returns_awaitable_object | generated | atomic | section Async Sink Completion | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_standard_logging_handler_receives_log_record | generated | integration | section Exceptions And Standard Logging Interop | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_standard_logging_can_be_forwarded_to_loguru | generated | system_e2e | section Exceptions And Standard Logging Interop | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_catch_decorator_logs_and_returns_default | generated | system_e2e | section Exception Guard | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_catch_context_reraises_when_requested | generated | integration | section Exception Guard | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_catch_exclude_does_not_suppress_excluded_exception | generated | atomic | section Exception Guard | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_exception_method_attaches_current_exception | generated | integration | section Exceptions And Standard Logging Interop | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_parse_yields_named_groups_from_file | generated | atomic | section Parsing Generated Logs | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_parse_cast_mapping_transforms_values | generated | atomic | section Parsing Generated Logs | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_parse_cast_callable_transforms_dict | generated | atomic | section Parsing Generated Logs | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_parse_missing_file_propagates_os_error | generated | atomic | section Error Semantics | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_log_record_views_agree_across_serialized_and_callable_sinks | generated | system_e2e | section Cross-View Invariants | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_removed_handler_does_not_affect_remaining_state | generated | system_e2e | section Cross-View Invariants | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_configure_replacement_affects_only_subsequent_records | generated | system_e2e | section Cross-View Invariants | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_start_and_stop_alias_add_and_remove | generated | atomic | section Public API | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_reinstall_keeps_simple_logger_usable | generated | integration | section Public API | covered | public-only generated test; reference gate passed and dummy gate did not pass |
| filter/generated_tests.py::test_public_type_stub_file_is_packaged | generated | atomic | section Type Hints | covered | public-only generated type-information check; spec_v3 explicitly covers installed package-local type stub contract |
| filter/generated_tests.py::test_type_stub_documents_record_level_without_color | generated | atomic | section Type Hints | covered | public-only generated type-information check; spec_v3 explicitly covers installed package-local type stub contract |

Total: 133 | kept (covered): 133 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 133
Layer counts: atomic=73 | integration=48 | system_e2e=12 | integration+system_e2e=60
