# Rewrite audit — config-rs-fullrepro-001

Sources: upstream `tests/testsuite/*.rs` at 532ab4d (v0.15.11). Kept suites:
`get`, `set`, `defaults`, `empty`, `weird_keys`, `integer_range`,
`unsigned_int`, `unsigned_int_hm`, `env`, `merge`, `file_toml`, `file_json`,
`file_ini`, `errors` (subset). Excluded suites: `async_builder` (async feature
out of scope), `file_json5`/`file_yaml`/`file_ron` (formats out of scope),
`file` path-based loading and `log` (filesystem/logging out of scope),
`legacy` module (deprecated surface), `ser` (Config-as-serializer out of
scope), `custom_str_deserialize`.

## Removals / rewrites (undeclared surface — spec is never widened for a test)

| test | rewrite | reason |
|------|---------|--------|
| all `snapbox::assert_data_eq!` error-string asserts | `matches!` / field checks on `ConfigError` variants (`NotFound`, `PathParse { .. }`, `FileParse { .. }`, `Type { .. }`) | spec declares error variants and their carried data, not exact `Display` strings |
| `errors.rs` tests asserting full rendered messages | kept only variant + key/origin field assertions | same |
| `env.rs` tests mutating process environment (`temp_env::with_var`) | rewritten onto `Environment::default().source(Some(map))` | deterministic; spec declares the injected-source form; process-env mutation is racy under parallel nextest |
| `test_parse_*` env suite | same `source(Some(map))` rewrite, values preserved | same |
| `set.rs` `#[should_panic]` on invalid path index | `assert!(matches!(err, ConfigError::PathParse { .. }))` on the returned `Result` | spec declares the error return, not a panic |
| `get.rs` `Path`/`PathBuf` getter block | removed | filesystem path coercion not declared |
| `file_*.rs` tests loading from disk via `File::with_name` | rewritten to `File::from_str(<literal>, FileFormat::X)` | spec's file-source surface is exercised through string sources; no fixture files ship with the oracle |
| `defaults.rs` `#[derive(Default)]` upstream fixture structs | re-declared locally in the oracle with distinct field values | anti-memorization; behavior identical |

## Deduplication

Upstream repeats scalar-lookup assertions across `get.rs`, `file_toml.rs`,
`file_json.rs`; one copy is kept in `atomic` and the format-specific copies are
collapsed into `integration::formats::{toml,json,ini}_file_full`, which each
assert the same key set against their own format text.

## Generated additions (coverage gaps)

- `atomic::generated_env_nonmatching_prefix_skips_key`,
  `atomic::generated_env_without_parsing_keeps_strings` — prefix filtering and
  `try_parsing(false)` defaults were untested upstream.
- `atomic::generated_get_table_and_array`,
  `atomic::generated_typed_get_forms_agree`,
  `atomic::generated_value_coercion_rules`,
  `atomic::generated_lookup_kind_mismatch_is_not_found`,
  `atomic::generated_set_default_path_parse_error`,
  `atomic::generated_ini_values_are_string_leaves` — direct tests of the
  spec's Typed Access and Coercions rules with values distinct from upstream.
- `integration::generated::*` (6 tests) — direct tests of the spec's
  Cross-View Invariants section: cross-format agreement on one logical config,
  full four-layer precedence chain, `Config` used as a `Source` reproducing
  its own keys, `try_deserialize`/`try_from` roundtrip agreement, env
  `collect()` agreeing with built lookups, and clone independence.

## Fairness audit

Identifier sweep of all oracle sources against the spec vocabulary: every
flagged identifier is a test function name, a local binding, a serde derive
attribute, or a std item; every reached crate root (`config`, `serde`) is
named in the spec's Import Surface / Appendix A. No test names a module path
inside the target crate (`config::…` paths are all re-exported root items
declared in the API catalog). `filter/lint_result.txt` holds the machine
check.
