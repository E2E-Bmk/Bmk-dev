# Specification coverage map — config-rs-fullrepro-001

Test IDs are `{crate}::{module path}::{function}` as reported by
cargo-nextest against the oracle workspace.

| test_nodeid | layer | spec_section | status | notes |
|-------------|-------|--------------|--------|-------|
| `atomic::empty_deserializes` | atomic | ## Whole-Configuration Deserialization | covered | empty config into skipped fields |
| `atomic::env_custom_prefix_separator` | atomic | ## The Environment Source | covered | prefix separator independent of level separator |
| `atomic::env_custom_separator` | atomic | ## The Environment Source | covered | custom level separator |
| `atomic::env_default_lowercases_keys` | atomic | ## The Environment Source | covered | key lowercasing |
| `atomic::env_empty_value_is_ignored` | atomic | ## The Environment Source | covered | ignore_empty drops empty values |
| `atomic::env_keep_prefix` | atomic | ## The Environment Source | covered | keep_prefix retains matched pattern |
| `atomic::env_prefix_is_removed_from_key` | atomic | ## The Environment Source | covered | prefix strip |
| `atomic::env_prefix_matches_variant_spellings` | atomic | ## The Environment Source | covered | case-insensitive prefix match |
| `atomic::env_separator_nests_keys` | atomic | ## The Environment Source | covered | separator to dot translation |
| `atomic::generated_env_nonmatching_prefix_skips_key` | atomic | ## The Environment Source | covered | non-matching keys skipped entirely |
| `atomic::generated_env_without_parsing_keeps_strings` | atomic | ## The Environment Source | covered | no try_parsing: string leaves |
| `atomic::generated_get_table_and_array` | atomic | ## Typed Access and Coercions | covered | table/array access and scalar mismatch errors |
| `atomic::generated_ini_values_are_string_leaves` | atomic | ## Sources and Formats | covered | INI string leaves recovered by coercion |
| `atomic::generated_lookup_kind_mismatch_is_not_found` | atomic | ## Path Grammar and Key Expansion | covered | wrong-kind steps and OOB subscripts are NotFound |
| `atomic::generated_set_default_path_parse_error` | atomic | ## Error Semantics | covered | PathParse on malformed key expression |
| `atomic::generated_typed_get_forms_agree` | atomic | ## Typed Access and Coercions | covered | typed get_* forms and coercions agree |
| `atomic::generated_value_coercion_rules` | atomic | ## Typed Access and Coercions | covered | into_* coercion table incl. word booleans and rounding |
| `atomic::invalid_signedness` | atomic | ## Typed Access and Coercions | covered | negative into unsigned is a Type error |
| `atomic::nonwrapping_u32` | atomic | ## Typed Access and Coercions | covered | in-range unsigned lookup |
| `atomic::set_defaults` | atomic | ## Whole-Configuration Deserialization | covered | empty config with serde defaults |
| `atomic::test_array_scalar` | atomic | ## Typed Access and Coercions | covered | Vec<i64> lookup |
| `atomic::test_colon_key_json` | atomic | ## Whole-Configuration Deserialization | covered | renamed field with ':' key |
| `atomic::test_deser_unsigned_int_hm` | atomic | ## Building a Configuration | covered | custom ValueKind conversion accepted by set_default |
| `atomic::test_doublebackslash_key_json` | atomic | ## Whole-Configuration Deserialization | covered | renamed field with backslash key |
| `atomic::test_get_scalar_path` | atomic | ## Path Grammar and Key Expansion | covered | dotted-path reads |
| `atomic::test_get_scalar_path_subscript` | atomic | ## Path Grammar and Key Expansion | covered | subscripts incl. negative on reads |
| `atomic::test_map` | atomic | ## Typed Access and Coercions | covered | Map<String, Value> lookup and into_* coercions |
| `atomic::test_map_str` | atomic | ## Typed Access and Coercions | covered | map of strings lookup |
| `atomic::test_not_found` | atomic | ## Error Semantics | covered | NotFound carries the requested key |
| `atomic::test_scalar` | atomic | ## Typed Access and Coercions | covered | bool lookups on parsed leaves |
| `atomic::test_scalar_type_loose` | atomic | ## Typed Access and Coercions | covered | loose scalar coercions through get |
| `atomic::test_set_arr_path` | atomic | ## Path Grammar and Key Expansion | covered | auto-vivifying writes incl. negative subscripts |
| `atomic::test_set_capital` | atomic | ## Path Grammar and Key Expansion | covered | case-sensitive key storage and lookup |
| `atomic::test_set_override_scalar` | atomic | ## Building a Configuration | covered | single-key override layer |
| `atomic::test_set_scalar_default` | atomic | ## Building a Configuration | covered | defaults lose to sources; absent keys fall back |
| `atomic::test_set_scalar_path` | atomic | ## Building a Configuration | covered | path-keyed defaults/overrides precedence |
| `atomic::test_slash_key_json` | atomic | ## Whole-Configuration Deserialization | covered | renamed field with '/' key |
| `atomic::try_from_defaults` | atomic | ## Whole-Configuration Deserialization | covered | try_from round-trip of defaults |
| `atomic::wrapping_u16` | atomic | ## Typed Access and Coercions | covered | unsigned range violation is a Type error |
| `integration::env_pipeline::test_parse_bool` | integration | ## The Environment Source | covered | try_parsing yields boolean kind |
| `integration::env_pipeline::test_parse_float` | integration | ## The Environment Source | covered | try_parsing yields float kind |
| `integration::env_pipeline::test_parse_int` | integration | ## The Environment Source | covered | try_parsing yields integer kind |
| `integration::env_pipeline::test_parse_int_default` | integration | ## The Environment Source | covered | defaults through an empty snapshot |
| `integration::env_pipeline::test_parse_int_fail` | integration | ## The Environment Source | covered | unparsable value stays string; self-describing target errors |
| `integration::env_pipeline::test_parse_off_bool` | integration | ## The Environment Source | covered | try_parsing off keeps strings; typed enum target errors |
| `integration::env_pipeline::test_parse_off_float` | integration | ## The Environment Source | covered | try_parsing off keeps strings; typed enum target errors |
| `integration::env_pipeline::test_parse_off_int` | integration | ## The Environment Source | covered | try_parsing off keeps strings; typed enum target errors |
| `integration::env_pipeline::test_parse_off_string` | integration | ## The Environment Source | covered | try_parsing off keeps strings; typed enum target errors |
| `integration::env_pipeline::test_parse_string` | integration | ## The Environment Source | covered | string value through parsing pipeline |
| `integration::env_pipeline::test_parse_string_and_list` | integration | ## The Environment Source | covered | list split only for registered keys |
| `integration::env_pipeline::test_parse_string_and_list_ignores_list_parse_key_case` | integration | ## The Environment Source | covered | list-parse key compared against normalized key |
| `integration::env_pipeline::test_parse_string_list` | integration | ## The Environment Source | covered | list separator without key filter |
| `integration::env_pipeline::test_parse_uint` | integration | ## The Environment Source | covered | try_parsing integer into unsigned field |
| `integration::env_pipeline::test_parse_uint_default` | integration | ## The Environment Source | covered | defaults through an empty snapshot |
| `integration::formats::deserialize_invalid_type_is_error` | integration | ## Error Semantics | covered | field coercion failure fails try_deserialize |
| `integration::formats::env_overrides_file_value` | integration | ## Building a Configuration | covered | environment layer shadows file leaf |
| `integration::formats::get_invalid_type_carries_key` | integration | ## Error Semantics | covered | Type error carries offending key |
| `integration::formats::ini_file_full` | integration | ## Sources and Formats | covered | INI string leaves into a typed struct |
| `integration::formats::ini_parse_error` | integration | ## Error Semantics | covered | parse failure surfaces from build |
| `integration::formats::json_parse_error` | integration | ## Error Semantics | covered | FileParse without URI for string documents |
| `integration::formats::toml_file_full` | integration | ## Sources and Formats | covered | TOML typed leaves into a struct |
| `integration::formats::toml_parse_error` | integration | ## Error Semantics | covered | FileParse without URI for string documents |
| `integration::generated::generated_clone_reads_independently` | integration | ## State Model | covered | clone deserializes independently |
| `integration::generated::generated_config_as_source_reproduces_keys` | integration | ## Cross-View Invariants | covered | built Config re-added as a source |
| `integration::generated::generated_cross_format_agreement` | integration | ## Cross-View Invariants | covered | TOML/JSON/INI pairwise agreement |
| `integration::generated::generated_env_collect_matches_built_lookup` | integration | ## Cross-View Invariants | covered | Source::collect equals built lookups |
| `integration::generated::generated_layer_precedence_chain` | integration | ## Cross-View Invariants | covered | total layer precedence per key |
| `integration::generated::generated_try_from_roundtrip` | integration | ## Cross-View Invariants | covered | try_from then try_deserialize reproduces the struct |
| `integration::merge::test_merge` | integration | ## Building a Configuration | covered | key-wise deep merge preserves siblings |
| `integration::merge::test_merge_missing_and_empty_maps` | integration | ## Building a Configuration | covered | empty/missing map merge cases |
| `integration::merge::test_merge_populated_and_null_maps` | integration | ## Building a Configuration | covered | populated/null map merge cases |
| `integration::merge::test_merge_whole_config` | integration | ## State Model | covered | Config as a Source; independent builders |
| `integration::structs::respect_field_case` | integration | ## Whole-Configuration Deserialization | covered | mixed-case field names match verbatim |
| `integration::structs::respect_path_case` | integration | ## Path Grammar and Key Expansion | covered | case-sensitive path lookup |
| `integration::structs::respect_renamed_field` | integration | ## Whole-Configuration Deserialization | covered | serde rename matches stored key |
| `integration::structs::test_enum` | integration | ## Whole-Configuration Deserialization | covered | externally shaped enum variants |
| `integration::structs::test_enum_key` | integration | ## Whole-Configuration Deserialization | covered | enum map keys and hash-set values |
| `integration::structs::test_file_struct` | integration | ## Whole-Configuration Deserialization | covered | whole-document struct with coerced fields |
| `integration::structs::test_int_key` | integration | ## Whole-Configuration Deserialization | covered | integer map keys from string keys |
| `integration::structs::test_map_struct` | integration | ## Typed Access and Coercions | covered | map of strings lookup |
| `integration::structs::test_scalar_struct` | integration | ## Typed Access and Coercions | covered | bool lookups on parsed leaves |
| `integration::structs::test_struct_array` | integration | ## Whole-Configuration Deserialization | covered | renamed Vec<String> with int->string coercion |

## Layer balance

- atomic: 39 (single-surface lookups, coercions, path writes, env normalization)
- integration: 43 (multi-layer merge, deserialization, env pipeline, formats, cross-view)
- system_e2e: 0 (library-only task; no CLI surface in scope)

## Dummy-gate audit

Every test calls Config/ConfigBuilder/Environment/File entry points and
asserts produced values, deserialized structs, or specific ConfigError
kinds. No `#[should_panic]` tests are present (upstream ones were
rewritten to error-kind asserts), so a stub crate whose public items
panic cannot pass any test.
