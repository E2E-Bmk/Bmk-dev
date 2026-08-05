# Spec Test Map

| nodeid | layer | behavior | status |
|---|---|---|---|
| `oracle/test_atomic.py::test_typed_path_parameter_is_converted` | atomic | typed path parameter is converted | covered |
| `oracle/test_atomic.py::test_typed_query_parameter_is_converted` | atomic | typed query parameter is converted | covered |
| `oracle/test_atomic.py::test_default_query_parameter_is_used` | atomic | default query parameter is used | covered |
| `oracle/test_atomic.py::test_repeated_query_values_fill_list` | atomic | repeated query values fill list | covered |
| `oracle/test_atomic.py::test_invalid_typed_path_returns_bad_request` | atomic | invalid typed path returns bad request | covered |
| `oracle/test_atomic.py::test_missing_required_query_returns_bad_request` | atomic | missing required query returns bad request | covered |
| `oracle/test_atomic.py::test_json_body_dataclass_is_parsed` | atomic | json body dataclass is parsed | covered |
| `oracle/test_atomic.py::test_invalid_json_body_returns_bad_request` | atomic | invalid json body returns bad request | covered |
| `oracle/test_atomic.py::test_request_headers_are_injected` | atomic | request headers are injected | covered |
| `oracle/test_atomic.py::test_request_object_exposes_path` | atomic | request object exposes path | covered |
| `oracle/test_atomic.py::test_get_defaults_to_ok` | atomic | get defaults to ok | covered |
| `oracle/test_atomic.py::test_post_defaults_to_created` | atomic | post defaults to created | covered |
| `oracle/test_atomic.py::test_put_defaults_to_ok` | atomic | put defaults to ok | covered |
| `oracle/test_atomic.py::test_patch_defaults_to_ok` | atomic | patch defaults to ok | covered |
| `oracle/test_atomic.py::test_delete_defaults_to_no_content` | atomic | delete defaults to no content | covered |
| `oracle/test_atomic.py::test_dict_return_is_json` | atomic | dict return is json | covered |
| `oracle/test_atomic.py::test_text_media_type_sets_plain_content` | atomic | text media type sets plain content | covered |
| `oracle/test_atomic.py::test_html_media_type_sets_html_content` | atomic | html media type sets html content | covered |
| `oracle/test_atomic.py::test_explicit_response_preserves_status_and_header` | atomic | explicit response preserves status and header | covered |
| `oracle/test_atomic.py::test_named_dependency_is_injected` | atomic | named dependency is injected | covered |
| `oracle/test_atomic.py::test_dependency_receives_query_value` | atomic | dependency receives query value | covered |
| `oracle/test_atomic.py::test_router_dependency_is_injected` | atomic | router dependency is injected | covered |
| `oracle/test_atomic.py::test_guard_allows_authorized_request` | atomic | guard allows authorized request | covered |
| `oracle/test_atomic.py::test_guard_denies_unauthorized_request` | atomic | guard denies unauthorized request | covered |
| `oracle/test_atomic.py::test_router_prefix_is_applied` | atomic | router prefix is applied | covered |
| `oracle/test_atomic.py::test_controller_prefix_is_applied` | atomic | controller prefix is applied | covered |
| `oracle/test_atomic.py::test_nested_router_prefixes_are_composed` | atomic | nested router prefixes are composed | covered |
| `oracle/test_atomic.py::test_controller_exposes_multiple_methods` | atomic | controller exposes multiple methods | covered |
| `oracle/test_atomic.py::test_controller_class_can_be_reused` | atomic | controller class can be reused | covered |
| `oracle/test_atomic.py::test_multiple_route_paths_are_served` | atomic | multiple route paths are served | covered |
| `oracle/test_atomic.py::test_path_mismatch_returns_not_found` | atomic | path mismatch returns not found | covered |
| `oracle/test_atomic.py::test_unsupported_method_returns_method_not_allowed` | atomic | unsupported method returns method not allowed | covered |
| `oracle/test_atomic.py::test_auto_options_advertises_methods` | atomic | auto options advertises methods | covered |
| `oracle/test_atomic.py::test_route_handler_name_is_reversible` | atomic | route handler name is reversible | covered |
| `oracle/test_atomic.py::test_route_reverse_accepts_handler` | atomic | route reverse accepts handler | covered |
| `oracle/test_atomic.py::test_route_reverse_rejects_missing_parameter` | atomic | route reverse rejects missing parameter | covered |
| `oracle/test_atomic.py::test_route_reverse_rejects_wrong_parameter_type` | atomic | route reverse rejects wrong parameter type | covered |
| `oracle/test_atomic.py::test_public_routes_expose_registered_paths` | atomic | public routes expose registered paths | covered |
| `oracle/test_atomic.py::test_openapi_contains_typed_path_parameter` | atomic | openapi contains typed path parameter | covered |
| `oracle/test_atomic.py::test_openapi_contains_query_parameter` | atomic | openapi contains query parameter | covered |
| `oracle/test_atomic.py::test_openapi_contains_response_media_type` | atomic | openapi contains response media type | covered |
| `oracle/test_atomic.py::test_openapi_hides_excluded_route` | atomic | openapi hides excluded route | covered |
| `oracle/test_atomic.py::test_openapi_uses_custom_title_and_version` | atomic | openapi uses custom title and version | covered |
| `oracle/test_atomic.py::test_route_decorator_combines_methods` | atomic | route decorator combines methods | covered |
| `oracle/test_integration.py::test_crud_state_workflow` | integration | crud state workflow | covered |
| `oracle/test_integration.py::test_nested_router_controller_reverse_and_http` | integration | nested router controller reverse and http | covered |
| `oracle/test_integration.py::test_typed_request_validation_workflow` | integration | typed request validation workflow | covered |
| `oracle/test_integration.py::test_guarded_read_write_workflow` | integration | guarded read write workflow | covered |
| `oracle/test_integration.py::test_dependency_query_and_response_workflow` | integration | dependency query and response workflow | covered |
| `oracle/test_integration.py::test_response_defaults_across_resource_operations` | integration | response defaults across resource operations | covered |
| `oracle/test_integration.py::test_multi_method_route_and_options_workflow` | integration | multi method route and options workflow | covered |
| `oracle/test_integration.py::test_openapi_matches_live_typed_route` | integration | openapi matches live typed route | covered |
| `oracle/test_integration.py::test_openapi_nested_route_matches_reverse` | integration | openapi nested route matches reverse | covered |
| `oracle/test_integration.py::test_hidden_route_live_but_schema_excluded` | integration | hidden route live but schema excluded | covered |
| `oracle/test_integration.py::test_controller_reused_under_two_prefixes` | integration | controller reused under two prefixes | covered |
| `oracle/test_integration.py::test_multi_path_handler_and_reverse_workflow` | integration | multi path handler and reverse workflow | covered |
| `oracle/test_integration.py::test_request_header_to_response_workflow` | integration | request header to response workflow | covered |
| `oracle/test_integration.py::test_router_and_app_dependencies_combine` | integration | router and app dependencies combine | covered |
| `oracle/test_integration.py::test_guard_and_dependency_order_workflow` | integration | guard and dependency order workflow | covered |
| `oracle/test_integration.py::test_error_surface_workflow` | integration | error surface workflow | covered |
| `oracle/test_integration.py::test_custom_response_and_openapi_status_workflow` | integration | custom response and openapi status workflow | covered |
| `oracle/test_integration.py::test_json_body_round_trip_workflow` | integration | json body round trip workflow | covered |
| `oracle/test_integration.py::test_query_filter_pagination_workflow` | integration | query filter pagination workflow | covered |
| `oracle/test_integration.py::test_controller_path_parameter_workflow` | integration | controller path parameter workflow | covered |
| `oracle/test_integration.py::test_route_name_used_inside_handler` | integration | route name used inside handler | covered |
| `oracle/test_integration.py::test_openapi_operation_metadata_workflow` | integration | openapi operation metadata workflow | covered |
| `oracle/test_integration.py::test_different_media_types_workflow` | integration | different media types workflow | covered |
| `oracle/test_integration.py::test_router_registration_public_paths_workflow` | integration | router registration public paths workflow | covered |
| `oracle/test_integration.py::test_app_route_reverse_and_client_agree` | integration | app route reverse and client agree | covered |

final_scoreable: 69
