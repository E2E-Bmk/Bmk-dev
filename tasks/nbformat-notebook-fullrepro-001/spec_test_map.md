# Oracle Spec-Test Map

oracle_version: `2026-07-10T18:02:31Z`  
oracle_source: `upstream_plus_generated`  
oracle_count: `67`  
source_counts: `upstream=36, generated=31`  
layer_counts: `atomic=36, integration=27, system_e2e=4`  
track_a_nodeid_sha256: `2759bac7eb51dc3bc6a350eaf6c2414de3b6283b5a62cf80a3045d0610846c98`  
track_b_nodeid_sha256: `3f168e14781ed5c849b7549c98b0e3f3505e8dfca3cb6ddec0830cb03ae7b50b`  
combined_nodeid_sha256: `6c374dec960b2b7898fbcdc83c87e2595b0512ecfb5c51526c59a63736ad8444`  
scorer_isolation: `harness/score_pytest_original.py --remove-path repo/nbformat`; clean carrier contains only the two oracle test modules and imports the reference from `wip/nbformat-notebook-fullrepro-001/repo`  
quota_note: `The three CLI tests map primarily to Invocation Protocol and also directly cover Installable Surface by installing the evaluated project in an isolated Python 3.11 environment, executing its generated console script, and checking package/script provenance. The generated v3-to-v4 conversion test maps primarily to Conversion and also directly covers the documented Legacy Version Packages surface.`  

| test_nodeid | source | layer | spec_section | status | notes |
|---|---|---|---|---|---|
| `filter/test_rewritten_upstream.py::test_v4_empty_notebook` | upstream | atomic | v4 Notebook Construction and JSON Functions | covered | documented constructor defaults |
| `filter/test_rewritten_upstream.py::test_v4_markdown_cell_defaults` | upstream | atomic | v4 Notebook Construction and JSON Functions | covered | documented cell defaults; generated id value not asserted |
| `filter/test_rewritten_upstream.py::test_v4_markdown_cell_source` | upstream | atomic | v4 Notebook Construction and JSON Functions | covered | public source override |
| `filter/test_rewritten_upstream.py::test_v4_raw_cell_defaults` | upstream | atomic | v4 Notebook Construction and JSON Functions | covered | documented cell defaults |
| `filter/test_rewritten_upstream.py::test_v4_raw_cell_source` | upstream | atomic | v4 Notebook Construction and JSON Functions | covered | public source override |
| `filter/test_rewritten_upstream.py::test_v4_code_cell_defaults` | upstream | atomic | v4 Notebook Construction and JSON Functions | covered | documented code-cell defaults |
| `filter/test_rewritten_upstream.py::test_v4_display_data_defaults` | upstream | atomic | v4 Notebook Construction and JSON Functions | covered | documented output defaults |
| `filter/test_rewritten_upstream.py::test_v4_stream_defaults` | upstream | atomic | v4 Notebook Construction and JSON Functions | covered | documented output defaults |
| `filter/test_rewritten_upstream.py::test_v4_execute_result_defaults` | upstream | atomic | v4 Notebook Construction and JSON Functions | covered | documented output defaults |
| `filter/test_rewritten_upstream.py::test_v4_display_data_payload` | upstream | atomic | v4 Notebook Construction and JSON Functions | covered | public mime-bundle payload |
| `filter/test_rewritten_upstream.py::test_v4_execute_result_payload` | upstream | atomic | v4 Notebook Construction and JSON Functions | covered | public payload and execution count |
| `filter/test_rewritten_upstream.py::test_v4_error_output` | upstream | atomic | v4 Notebook Construction and JSON Functions | covered | documented error output fields |
| `filter/test_rewritten_upstream.py::test_v4_code_cell_with_outputs` | upstream | integration | v4 Notebook Construction and JSON Functions | covered | combines public cell and output constructors |
| `filter/test_rewritten_upstream.py::test_v4_stream_override` | upstream | atomic | v4 Notebook Construction and JSON Functions | covered | public keyword overrides |
| `filter/test_rewritten_upstream.py::test_v4_invalid_code_cell` | upstream | integration | Error Semantics | covered | invalid public field shape raises public exception type |
| `filter/test_rewritten_upstream.py::test_v4_invalid_markdown_cell` | upstream | integration | Error Semantics | covered | missing documented field raises public exception type |
| `filter/test_rewritten_upstream.py::test_v4_invalid_raw_cell` | upstream | integration | Error Semantics | covered | missing documented field raises public exception type |
| `filter/test_rewritten_upstream.py::test_v4_sample_notebook_validates` | upstream | integration | Validation | covered | public construction plus validation |
| `filter/test_rewritten_upstream.py::test_notebooknode_nested_item_assignment` | upstream | atomic | NotebookNode and Dictionary Conversion | covered | cross-view nested mapping projection |
| `filter/test_rewritten_upstream.py::test_notebooknode_update_nested_mapping` | upstream | atomic | NotebookNode and Dictionary Conversion | covered | recursive update projection |
| `filter/test_rewritten_upstream.py::test_from_dict_recursively_converts` | upstream | atomic | NotebookNode and Dictionary Conversion | covered | recursive public conversion |
| `filter/test_rewritten_upstream.py::test_v4_splitlines_preserve_json_mime_data` | upstream | integration | Notebook Format Behavior | covered | text split and JSON mime preservation |
| `filter/test_rewritten_upstream.py::test_write_read_path_roundtrip_and_newline` | upstream | system_e2e | Cross-View Invariants | covered | path write/read durable workflow and newline |
| `filter/test_rewritten_upstream.py::test_capture_validation_error_on_write` | upstream | integration | Top-Level Reading and Writing | covered | captured public validation failure |
| `filter/test_rewritten_upstream.py::test_read_missing_path_raises_oserror` | upstream | atomic | Error Semantics | covered | filesystem exception type only |
| `filter/test_rewritten_upstream.py::test_convert_unknown_version_raises_valueerror` | upstream | atomic | Error Semantics | covered | documented exception type only |
| `filter/test_rewritten_upstream.py::test_validate_empty_notebook_raises` | upstream | atomic | Validation | covered | invalid notebook raises public exception |
| `filter/test_rewritten_upstream.py::test_isvalid_reports_false_for_invalid_notebook` | upstream | atomic | Validation | covered | public boolean failure projection |
| `filter/test_rewritten_upstream.py::test_parse_filename_ipynb` | upstream | atomic | Legacy Version Packages | covered | documented extension mapping |
| `filter/test_rewritten_upstream.py::test_parse_filename_python` | upstream | atomic | Legacy Version Packages | covered | documented extension mapping |
| `filter/test_rewritten_upstream.py::test_parse_filename_extensionless` | upstream | atomic | - | source-only | `test.nb` is an unknown-suffix input, not the extensionless case specified; append behavior is not spec-derived |
| `filter/test_rewritten_upstream.py::test_parse_filename_absolute_path` | upstream | atomic | - | source-only | full-path versus basename semantics for `notebook_name` are not specified |
| `filter/test_rewritten_upstream.py::test_notary_secret_changes_signature` | upstream | atomic | Trust and Signatures | covered | configured secret affects public digest |
| `filter/test_rewritten_upstream.py::test_notary_sign_and_check` | upstream | integration | Trust and Signatures | covered | public store state transition |
| `filter/test_rewritten_upstream.py::test_notary_content_change_invalidates_signature` | upstream | integration | Cross-View Invariants | covered | durable content mutation changes trust projection |
| `filter/test_rewritten_upstream.py::test_notary_mark_and_check_cells_removes_marker` | upstream | integration | Cross-View Invariants | covered | transient trust marker lifecycle |
| `filter/test_rewritten_upstream.py::test_notary_untrusted_safe_empty_output_cell` | upstream | integration | Trust and Signatures | covered | safe-output trust rule |
| `filter/test_rewritten_upstream.py::test_memory_signature_store_lifecycle` | upstream | atomic | Trust and Signatures | covered | public store lifecycle |
| `filter/test_rewritten_upstream.py::test_v4_valid_code_cell` | upstream | atomic | - | excluded | passed the real import-complete dummy gate |
| `filter/test_rewritten_upstream.py::test_notebooknode_update_rejects_multiple_sources` | upstream | atomic | - | excluded | passed the real import-complete dummy gate |
| `filter/test_rewritten_upstream.py::test_v4_roundtrip_without_split_lines` | upstream | integration | - | excluded | passed the real import-complete dummy gate |
| `filter/test_rewritten_upstream.py::test_v4_roundtrip_with_split_lines` | upstream | integration | - | excluded | passed the real import-complete dummy gate |
| `filter/test_rewritten_upstream.py::test_convert_same_version_returns_same_object` | upstream | atomic | - | excluded | passed the real import-complete dummy gate |
| `filter/test_rewritten_upstream.py::test_notary_signature_is_deterministic` | upstream | atomic | - | excluded | passed the real import-complete dummy gate |
| `filter/test_rewritten_upstream.py::test_notary_unsign` | upstream | atomic | - | excluded | passed the real import-complete dummy gate |
| `filter/test_generated.py::test_notebooknode_update_accepts_dictionary_patterns` | generated | atomic | NotebookNode and Dictionary Conversion | covered | Update accepts mapping, pair iterable, and keyword sources and rejects two positional sources. |
| `filter/test_generated.py::test_from_dict_converts_lists_tuples_and_scalars` | generated | atomic | NotebookNode and Dictionary Conversion | covered | from_dict recursively converts container members and preserves scalar identity. |
| `filter/test_generated.py::test_top_level_string_and_bytes_reads_preserve_content` | generated | integration | Top-Level Reading and Writing | covered | Top-level reads accepts both text and UTF-8 bytes with equivalent content. |
| `filter/test_generated.py::test_top_level_capture_validation_error_on_reads_and_writes` | generated | integration | Top-Level Reading and Writing | covered | Read and write capture validation errors while returning parsed or serialized content. |
| `filter/test_generated.py::test_top_level_file_like_errors_propagate` | generated | integration | Error Semantics | covered | File-like read and write exceptions propagate unchanged by type. |
| `filter/test_generated.py::test_convert_existing_major_is_same_object` | generated | atomic | Conversion | covered | Conversion to the existing major returns the identical mutable object. |
| `filter/test_generated.py::test_convert_v3_notebook_to_v4` | generated | integration | Conversion | covered | Public conversion upgrades a v3 worksheet notebook into v4 cells. |
| `filter/test_generated.py::test_convert_unknown_version_raises_value_error` | generated | atomic | Conversion | covered | Conversion to an unimplemented major raises ValueError. |
| `filter/test_generated.py::test_validation_accepts_nbjson_alias_and_requires_input` | generated | atomic | Validation | covered | validate accepts nbjson and explicit versions, and requires notebook input. |
| `filter/test_generated.py::test_isvalid_reports_schema_result_without_mutation` | generated | atomic | Validation | covered | isvalid distinguishes valid and invalid notebooks without mutating invalid input. |
| `filter/test_generated.py::test_iter_validate_returns_validation_errors` | generated | atomic | Validation | covered | iter_validate exposes validation failures as an iterable. |
| `filter/test_generated.py::test_normalize_repairs_ids_on_a_deep_copy` | generated | integration | Validation | covered | normalize repairs duplicate cell ids in its deep-copy result. |
| `filter/test_generated.py::test_v4_constructors_supply_valid_defaults` | generated | atomic | v4 Notebook Construction and JSON Functions | covered | v4 constructors supply ids, format fields, cell defaults, and schema-valid output. |
| `filter/test_generated.py::test_v4_new_output_defaults_and_invalid_type` | generated | atomic | v4 Notebook Construction and JSON Functions | covered | Output constructors apply documented defaults and reject an invalid stream field type. |
| `filter/test_generated.py::test_output_from_msg_converts_execute_result` | generated | atomic | v4 Notebook Construction and JSON Functions | covered | An execute_result IOPub message maps to the corresponding output node. |
| `filter/test_generated.py::test_output_from_msg_converts_stream_display_and_error` | generated | atomic | v4 Notebook Construction and JSON Functions | covered | Stream, display, and error messages convert while unsupported messages fail. |
| `filter/test_generated.py::test_durable_json_excludes_transient_trust_fields` | generated | integration | Notebook JSON State Model | covered | Durable v4 JSON strips signature and transient cell trust metadata. |
| `filter/test_generated.py::test_trust_state_is_external_to_notebook_json` | generated | integration | Notebook JSON State Model | covered | Signing changes the external signature store without adding durable signature metadata. |
| `filter/test_generated.py::test_dictionary_and_attribute_mutations_share_one_projection` | generated | atomic | Notebook JSON State Model | covered | Dictionary and attribute views observe the same recursively converted state. |
| `filter/test_generated.py::test_v4_reader_rejoins_disk_multiline_lists` | generated | integration | Notebook Format Behavior | covered | v4 reading rejoins list-form cell source and stream text. |
| `filter/test_generated.py::test_v4_writer_splits_text_but_preserves_json_mime_values` | generated | integration | Notebook Format Behavior | covered | v4 writing splits text projections while retaining JSON mime data structure. |
| `filter/test_generated.py::test_signature_changes_with_content_and_unsign_removes_it` | generated | integration | Trust and Signatures | covered | Signature recognition tracks content changes and unsigning. |
| `filter/test_generated.py::test_mark_and_check_cells_consumes_transient_marker` | generated | integration | Trust and Signatures | covered | Rich-output trust markers are honored and consumed during cell checking. |
| `filter/test_generated.py::test_generic_string_round_trip_preserves_notebook_content` | generated | integration | Cross-View Invariants | covered | Generic string serialization and parsing preserve notebook content. |
| `filter/test_generated.py::test_generic_path_round_trip_adds_newline` | generated | integration | Cross-View Invariants | covered | Generic path round trips preserve content and write a final newline. |
| `filter/test_generated.py::test_representative_in_memory_lifecycle` | generated | integration | Representative Workflow | covered | Construction, validation, JSON round trip, signing, and cell trust form one lifecycle. |
| `filter/test_generated.py::test_representative_file_lifecycle` | generated | integration | Representative Workflow | covered | A path-based read-mutate-write-read lifecycle preserves content and validity. |
| `filter/test_generated.py::test_representative_conversion_and_trust_lifecycle` | generated | integration | Representative Workflow | covered | Legacy conversion, serialization, parsing, and signing compose successfully. |
| `filter/test_generated.py::test_jupyter_trust_help` | generated | system_e2e | Invocation Protocol | covered | Isolated installation's generated console script reports documented help; package and script provenance also directly cover Installable Surface. |
| `filter/test_generated.py::test_jupyter_trust_signs_path_and_rejects_missing_path` | generated | system_e2e | Invocation Protocol | covered | Isolated installation's generated console script signs a path and rejects a missing path; package and script provenance also directly cover Installable Surface. |
| `filter/test_generated.py::test_jupyter_trust_stdin_success` | generated | system_e2e | Invocation Protocol | covered | Isolated installation's generated console script accepts valid stdin; package and script provenance also directly cover Installable Surface. |

Total: 76 | kept (covered): 67 | spec_gap: 0 | source-only: 2 | excluded: 7 | final scoreable: 67

## Section Quotas

| spec_section | count | floor | status |
|---|---:|---:|---|
| Installable Surface | 3 | 3 | met |
| NotebookNode and Dictionary Conversion | 5 | 3 | met |
| Top-Level Reading and Writing | 3 | 3 | met |
| Conversion | 3 | 3 | met |
| Validation | 7 | 3 | met |
| v4 Notebook Construction and JSON Functions | 18 | 3 | met |
| Legacy Version Packages | 3 | 3 | met |
| Notebook JSON State Model | 3 | 3 | met |
| Notebook Format Behavior | 3 | 3 | met |
| Trust and Signatures | 6 | 3 | met |
| Error Semantics | 6 | 3 | met |
| Cross-View Invariants | 5 | 5 | met |
| Representative Workflow | 3 | 3 | met |
| Invocation Protocol | 3 | 3 | met |
