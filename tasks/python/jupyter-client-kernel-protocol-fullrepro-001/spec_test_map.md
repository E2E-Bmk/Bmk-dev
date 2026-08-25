# Spec-to-test map — jupyter-client-kernel-protocol-fullrepro-001

oracle_version: 2026-07-17T01:30:00+08:00
oracle_source: generated_only
scorer_isolation: score_pytest_original.py --remove-path jupyter_client; source oracle worktree has no package directory and PYTHONPATH explicitly selects the solution.

| test_nodeid | layer | spec_section | status | notes |
|---|---|---|---|---|
| oracle/test_atomic.py::test_root_kernel_surface_is_importable[KernelClient] | atomic | ## Installable Surface | covered | public import availability and alias identity |
| oracle/test_atomic.py::test_root_kernel_surface_is_importable[BlockingKernelClient] | atomic | ## Installable Surface | covered | public import availability and alias identity |
| oracle/test_atomic.py::test_root_kernel_surface_is_importable[AsyncKernelClient] | atomic | ## Installable Surface | covered | public import availability and alias identity |
| oracle/test_atomic.py::test_root_kernel_surface_is_importable[KernelManager] | atomic | ## Installable Surface | covered | public import availability and alias identity |
| oracle/test_atomic.py::test_root_kernel_surface_is_importable[AsyncKernelManager] | atomic | ## Installable Surface | covered | public import availability and alias identity |
| oracle/test_atomic.py::test_root_kernel_surface_is_importable[KernelProvisionerBase] | atomic | ## Installable Surface | covered | public import availability and alias identity |
| oracle/test_atomic.py::test_root_kernel_surface_is_importable[LocalProvisioner] | atomic | ## Installable Surface | covered | public import availability and alias identity |
| oracle/test_atomic.py::test_connection_helpers_are_available_at_both_public_paths[KernelConnectionInfo] | atomic | ## Installable Surface | covered | public import availability and alias identity |
| oracle/test_atomic.py::test_connection_helpers_are_available_at_both_public_paths[find_connection_file] | atomic | ## Installable Surface | covered | public import availability and alias identity |
| oracle/test_atomic.py::test_connection_helpers_are_available_at_both_public_paths[write_connection_file] | atomic | ## Installable Surface | covered | public import availability and alias identity |
| oracle/test_atomic.py::test_write_connection_file_preserves_explicit_connection_values[0] | atomic | ### Connection information | covered | connection-file output or lookup behavior |
| oracle/test_atomic.py::test_write_connection_file_preserves_explicit_connection_values[1] | atomic | ### Connection information | covered | connection-file output or lookup behavior |
| oracle/test_atomic.py::test_write_connection_file_preserves_explicit_connection_values[2] | atomic | ### Connection information | covered | connection-file output or lookup behavior |
| oracle/test_atomic.py::test_write_connection_file_preserves_explicit_connection_values[3] | atomic | ### Connection information | covered | connection-file output or lookup behavior |
| oracle/test_atomic.py::test_find_connection_file_returns_matching_absolute_path[kernel.json] | atomic | ### Connection information | covered | connection-file output or lookup behavior |
| oracle/test_atomic.py::test_find_connection_file_returns_matching_absolute_path[kernel] | atomic | ### Connection information | covered | connection-file output or lookup behavior |
| oracle/test_atomic.py::test_find_connection_file_returns_matching_absolute_path[kern*] | atomic | ### Connection information | covered | connection-file output or lookup behavior |
| oracle/test_atomic.py::test_find_connection_file_raises_for_missing_file | atomic | ### Connection information | covered | connection-file output or lookup behavior |
| oracle/test_atomic.py::test_session_msg_has_public_message_shape[content0] | atomic | ### Sessions and clients | covered | message/header/signature behavior |
| oracle/test_atomic.py::test_session_msg_has_public_message_shape[content1] | atomic | ### Sessions and clients | covered | message/header/signature behavior |
| oracle/test_atomic.py::test_session_msg_has_public_message_shape[content2] | atomic | ### Sessions and clients | covered | message/header/signature behavior |
| oracle/test_atomic.py::test_session_headers_have_independent_message_ids[execute_request] | atomic | ### Sessions and clients | covered | message/header/signature behavior |
| oracle/test_atomic.py::test_session_headers_have_independent_message_ids[kernel_info_request] | atomic | ### Sessions and clients | covered | message/header/signature behavior |
| oracle/test_atomic.py::test_session_headers_have_independent_message_ids[complete_request] | atomic | ### Sessions and clients | covered | message/header/signature behavior |
| oracle/test_atomic.py::test_session_with_empty_key_serializes_empty_signature | atomic | ### Sessions and clients | covered | message/header/signature behavior |
| oracle/test_atomic.py::test_session_rejects_invalid_signature | atomic | ### Sessions and clients | covered | message/header/signature behavior |
| oracle/test_atomic.py::test_kernelspec_from_resource_dir_has_serializable_public_fields[Example] | atomic | ### Kernel specifications | covered | kernelspec parsing or input validation |
| oracle/test_atomic.py::test_kernelspec_from_resource_dir_has_serializable_public_fields[Python Example] | atomic | ### Kernel specifications | covered | kernelspec parsing or input validation |
| oracle/test_atomic.py::test_kernelspec_from_resource_dir_has_serializable_public_fields[Example 3] | atomic | ### Kernel specifications | covered | kernelspec parsing or input validation |
| oracle/test_atomic.py::test_install_kernel_spec_rejects_invalid_name[has space] | atomic | ### Kernel specifications | covered | kernelspec parsing or input validation |
| oracle/test_atomic.py::test_install_kernel_spec_rejects_invalid_name[\xfcnicode] | atomic | ### Kernel specifications | covered | kernelspec parsing or input validation |
| oracle/test_atomic.py::test_install_kernel_spec_rejects_invalid_name[bad/name] | atomic | ### Kernel specifications | covered | kernelspec parsing or input validation |
| oracle/test_atomic.py::test_install_kernel_spec_rejects_user_and_prefix_together | atomic | ### Kernel specifications | covered | kernelspec parsing or input validation |
| oracle/test_integration.py::test_client_loaded_from_connection_mapping_reports_same_values[0] | integration | ## Product State Model | covered | connection representation flows into a client projection |
| oracle/test_integration.py::test_client_loaded_from_connection_mapping_reports_same_values[1] | integration | ## Product State Model | covered | connection representation flows into a client projection |
| oracle/test_integration.py::test_client_loaded_from_connection_mapping_reports_same_values[2] | integration | ## Product State Model | covered | connection representation flows into a client projection |
| oracle/test_integration.py::test_client_loaded_from_connection_mapping_reports_same_values[3] | integration | ## Product State Model | covered | connection representation flows into a client projection |
| oracle/test_integration.py::test_connection_file_can_be_written_then_loaded_by_client[0] | integration | ## Product State Model | covered | connection representation flows into a client projection |
| oracle/test_integration.py::test_connection_file_can_be_written_then_loaded_by_client[1] | integration | ## Product State Model | covered | connection representation flows into a client projection |
| oracle/test_integration.py::test_connection_file_can_be_written_then_loaded_by_client[2] | integration | ## Product State Model | covered | connection representation flows into a client projection |
| oracle/test_integration.py::test_session_serialization_round_trip_preserves_routing_and_content[payload0] | integration | ### Sessions and clients | covered | session message travels through framing and decoding |
| oracle/test_integration.py::test_session_serialization_round_trip_preserves_routing_and_content[payload1] | integration | ### Sessions and clients | covered | session message travels through framing and decoding |
| oracle/test_integration.py::test_session_serialization_round_trip_preserves_routing_and_content[payload2] | integration | ### Sessions and clients | covered | session message travels through framing and decoding |
| oracle/test_integration.py::test_kernelspec_discovery_and_lookup_share_resource_directory[alpha] | integration | ### Kernel specifications | covered | kernelspec filesystem/discovery/selection workflow |
| oracle/test_integration.py::test_kernelspec_discovery_and_lookup_share_resource_directory[beta] | integration | ### Kernel specifications | covered | kernelspec filesystem/discovery/selection workflow |
| oracle/test_integration.py::test_kernelspec_discovery_and_lookup_share_resource_directory[mixed-name] | integration | ### Kernel specifications | covered | kernelspec filesystem/discovery/selection workflow |
| oracle/test_integration.py::test_install_discover_and_remove_kernelspec_round_trip[installed] | integration | ### Kernel specifications | covered | kernelspec filesystem/discovery/selection workflow |
| oracle/test_integration.py::test_install_discover_and_remove_kernelspec_round_trip[installed_two] | integration | ### Kernel specifications | covered | kernelspec filesystem/discovery/selection workflow |
| oracle/test_integration.py::test_install_discover_and_remove_kernelspec_round_trip[installed-three] | integration | ### Kernel specifications | covered | kernelspec filesystem/discovery/selection workflow |
| oracle/test_integration.py::test_first_kernelspec_directory_wins_duplicate_name[priority-one] | integration | ### Kernel specifications | covered | kernelspec filesystem/discovery/selection workflow |
| oracle/test_integration.py::test_first_kernelspec_directory_wins_duplicate_name[priority-two] | integration | ### Kernel specifications | covered | kernelspec filesystem/discovery/selection workflow |
| oracle/test_integration.py::test_first_kernelspec_directory_wins_duplicate_name[priority-three] | integration | ### Kernel specifications | covered | kernelspec filesystem/discovery/selection workflow |
| oracle/test_integration.py::test_allowed_kernelspecs_filters_discovery[allowed0] | integration | ### Kernel specifications | covered | kernelspec filesystem/discovery/selection workflow |
| oracle/test_integration.py::test_allowed_kernelspecs_filters_discovery[allowed1] | integration | ### Kernel specifications | covered | kernelspec filesystem/discovery/selection workflow |
| oracle/test_integration.py::test_allowed_kernelspecs_filters_discovery[allowed2] | integration | ### Kernel specifications | covered | kernelspec filesystem/discovery/selection workflow |
| oracle/test_integration.py::test_missing_kernelspec_raises_public_exception[missing] | integration | ### Kernel specifications | covered | kernelspec filesystem/discovery/selection workflow |
| oracle/test_integration.py::test_missing_kernelspec_raises_public_exception[unknown] | integration | ### Kernel specifications | covered | kernelspec filesystem/discovery/selection workflow |
| oracle/test_integration.py::test_missing_kernelspec_raises_public_exception[not-installed] | integration | ### Kernel specifications | covered | kernelspec filesystem/discovery/selection workflow |
| oracle/test_integration.py::test_manager_connection_mapping_flows_to_created_client[0] | integration | ### Kernel managers and provisioners | covered | manager/client or no-kernel lifecycle behavior |
| oracle/test_integration.py::test_manager_connection_mapping_flows_to_created_client[1] | integration | ### Kernel managers and provisioners | covered | manager/client or no-kernel lifecycle behavior |
| oracle/test_integration.py::test_manager_connection_mapping_flows_to_created_client[2] | integration | ### Kernel managers and provisioners | covered | manager/client or no-kernel lifecycle behavior |
| oracle/test_integration.py::test_manager_operations_without_kernel_raise_runtime_error[interrupt_kernel] | integration | ### Kernel managers and provisioners | covered | manager/client or no-kernel lifecycle behavior |
| oracle/test_integration.py::test_manager_operations_without_kernel_raise_runtime_error[signal_kernel] | integration | ### Kernel managers and provisioners | covered | manager/client or no-kernel lifecycle behavior |
| oracle/test_integration.py::test_disabled_transport_encryption_is_accepted | integration | ### Transport encryption | covered | public transport-encryption configuration behavior |
| oracle/test_integration.py::test_unknown_transport_encryption_mode_is_rejected | integration | ### Transport encryption | covered | public transport-encryption configuration behavior |
| oracle/test_integration.py::test_disabled_transport_encryption_writes_no_curve_keys | integration | ### Transport encryption | covered | public transport-encryption configuration behavior |
| oracle/test_integration.py::test_documented_python_module_invocations_report_usage[jupyter_client.kernelspecapp] | integration | ## Invocation Protocol | covered | documented command-module usage behavior |
| oracle/test_integration.py::test_documented_python_module_invocations_report_usage[jupyter_client.runapp] | integration | ## Invocation Protocol | covered | documented command-module usage behavior |
| oracle/test_integration.py::test_documented_python_module_invocations_report_usage[jupyter_client.kernelapp] | integration | ## Invocation Protocol | covered | documented command-module usage behavior |
| oracle/test_integration.py::test_manager_client_keeps_loaded_workflow_connection_info | integration | ## Representative Workflow | covered | manager-to-client workflow handoff |
| oracle/test_integration.py::test_blocking_workflow_returns_request_id_before_empty_shell_reply | system_e2e | ## Representative Workflow | covered | request then documented empty-receive workflow |
| oracle/test_integration.py::test_workflow_start_with_unknown_kernel_fails_without_running_one | system_e2e | ## Representative Workflow | covered | documented startup failure workflow |

Total: 72 | kept (covered): 72 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 72

Layer counts: atomic=33 | integration=37 | system_e2e=2.
