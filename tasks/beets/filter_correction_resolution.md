# Filter Correction Resolution: beets

Resolved in Stage 3 test-filter.

- Rewrote `test_destination_substitutes_metadata_values`, `test_destination_relative_to_library_root`, `test_query_conditioned_path_format_selection`, and `test_destination_sanitizes_path_separators_inside_fields` to use config-backed `config["paths"]` instead of the undocumented direct `path_formats=[...]` argument shape.
- Updated `test_destination_preserves_extension` to assert preservation of a lowercase `.flac` source extension, removing the prior uppercase `.FLAC` to lowercase `.flac` normalization expectation.
- Kept `test_cli_fields_includes_flexible_attribute`.
- No `spec_patch_request.md` is needed.
