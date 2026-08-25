# filter_notes — config-rs-fullrepro-001

```
repo: rust-cli/config-rs
source_path: https://github.com/rust-cli/config-rs (local: /tmp/refs/config-rs)
commit: 532ab4d827db199c1b0e9e457441fcc82b819fb9 (tag v0.15.11)
language: rust
target_crates: config
src_loc: 4887 across src/, excluding tests/ and examples/
test_functions: 154 in tests/testsuite (25 modules) + inline units
test_files: tests/testsuite/{get,set,env,merge,errors,defaults,empty,case,
  weird_keys,integer_range,unsigned_int*,file,file_toml,file_json,file_ini,
  file_yaml,file_ron,file_json5,file_corn,ron_enum,log,async_builder}.rs
dominant_test_styles: value-equality asserts on typed lookups and deserialized
  structs; snapbox string snapshots concentrated in errors.rs and the
  file-format parse-error tests (~25% of suite, rewritten or dropped); no
  golden files for behavior, only two JSON fixtures for error-message tests
public_docs: docs.rs/config rustdoc (builder, sources, Environment, File,
  Value semantics; #![warn(missing_docs)] discipline), README, examples/
core_fact_source: the merged configuration table built by ConfigBuilder from
  ordered layers (defaults, sources, overrides)
derived_views: (1) typed lookups get::<T> plus get_string/int/float/bool/
  table/array with loose coercions; (2) whole-config try_deserialize into
  serde structs/enums/maps; (3) dotted-path and [index] traversal syntax;
  (4) Environment source key normalization (prefix, separators, list parsing,
  try_parsing) observed via Source::collect and via merged lookups;
  (5) Config as a Source merged into another builder; (6) ConfigError
  taxonomy (NotFound, Type with key attribution, FileParse, Frozen)
external_deps: format parsers (toml, serde_json, rust-ini) are dependencies of
  the target crate itself, not of the oracle; oracle test deps: serde derive
  only (float-cmp rewritten to abs-tolerance; chrono/datetime tests skipped;
  snapbox rewritten to kind asserts; temp-env replaced by Environment::source
  injected maps; warp/reqwest async tests out of scope)
test_import_audit: clean — tests import only `config::{...}` public items
  (0% private-module imports)
docs_test_alignment: aligned — docs.rs documents exactly the builder/source/
  lookup/deserialize projections the suite exercises
contamination_note: config@0.15.11, released 2025-03-12, near/before 2025-era
  training cutoffs; the crate API is old and stable (builder API since 0.12,
  2021) so prior-version semantics are likely memorized; mitigated by
  generated tests with values distinct from upstream and by the
  version-specific v0.15 behaviors (Environment::source injection,
  list parsing keys, negative-subscript writes)
decision: keep
reason: layered-config rule engine (ordered-layer deep-merge into one fact
  source) with 6 public projections, multi-format agreement obligations, and
  a fully doc-traceable surface.
risks: config loading is a common pattern; mitigated because the specific
  coercion table (bool<->int<->string), path grammar with negative indices,
  env normalization pipeline (prefix strip, separator translation, list
  parse keys, try_parsing) and layer precedence rules are library-specific;
  MSRV: v0.15.12+ pull toml 0.9/1.x whose subcrates need rustc 1.85
  (edition 2024), so the task pins v0.15.11 (edition 2018, MSRV 1.75,
  toml 0.8) which builds on the sandbox toolchain (1.83); the oracle
  Cargo.lock additionally pins indexmap 2.7.1 / hashbrown 0.15.5 to keep
  transitive resolution inside edition-2021 crates
scope_plan: target_subdomain=core engine + toml/json/ini formats via
  File::from_str + Environment via injected source maps; expected_oracle_max=70
  (excluded: yaml/ron/json5/corn formats, async sources, file-on-disk
  loading, log-crate integration, datetime/chrono, preserve_order feature)
```

## Difficulty shapes (candidate-selector heuristic)

- **Rule engine resisting pattern-matching**: layer precedence (defaults <
  sources in order < overrides) combined with deep table merge (nested maps
  merge key-wise; scalars and arrays replace) and null/empty-map edge cases.
- **Reimplementation of a format rule**: dotted-path grammar with `[n]` and
  negative subscripts, applied uniformly to lookups and to set_default/
  set_override key expansion (auto-vivifying nested tables/arrays).
- **Multi-projection integration**: one merged table must agree across typed
  get, loose-coerced get, whole-struct deserialize, tagged/untagged enum
  deserialize, and Source::collect — 5+ public projections of the same facts.
- **Equivalence judgement**: the same logical document expressed in TOML,
  JSON, and INI must produce identical typed views (cross-format agreement).

## Dummy-gate audit note (Rust)

Every kept test calls Config/ConfigBuilder/Environment/File entry points and
asserts produced values, deserialized structs, or specific ConfigError kinds;
upstream `#[should_panic]` tests are rewritten to `is_err()`/`matches!` form,
so no kept test can pass against a stub crate that panics on first call.
Verified statically over the merged oracle (see filter/spec_test_map.md).
