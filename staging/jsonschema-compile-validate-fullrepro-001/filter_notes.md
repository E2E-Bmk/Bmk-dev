# Stage 1 evidence brief — jsonschema-compile-validate-fullrepro-001

```
repo: santhosh-tekuri/jsonschema
source_path: https://github.com/santhosh-tekuri/jsonschema (module github.com/santhosh-tekuri/jsonschema/v6)
commit: b0fc661f4939578bc429f408c18202573dbafcc4 (tag v6.0.3, released 2026-06-28)
src_loc: 5607 (4956 root package + 651 kind package; cmd/jv is a separate module and out of scope)
test_functions: 27 Test funcs + 11 Example funcs
test_files: 15 (suite_test.go is a data-driven runner over the official
  JSON-Schema-Test-Suite in testdata/; the rest are unit/regression files and
  runnable examples)
dominant_test_styles: data-driven conformance suite (majority of coverage),
  unit tests on compiler errors and output formats, example tests
public_docs: pkg.go.dev/github.com/santhosh-tekuri/jsonschema/v6 (package doc,
  all exported types), README.md, kind subpackage doc
core_fact_source: the compiled schema resource graph — schemas added as
  resources, cross-referenced by $ref/$anchor/$dynamicRef, compiled into
  *Schema nodes that share one registry per Compiler
derived_views: (1) Compile/MustCompile returning *Schema with exported
  metadata fields; (2) Schema.Validate error tree (*ValidationError);
  (3) three standardized output projections FlagOutput/BasicOutput/
  DetailedOutput of the same error state; (4) error-kind taxonomy in the kind
  subpackage discriminating causes; (5) compiler-level error types
  (ResourceExistsError, AnchorNotFoundError, ...)
external_deps: golang.org/x/text (message printers for localization; only the
  non-localized paths are in scope), dlclark/regexp2 (test-only upstream).
  No network use in the library: default loader is FileLoader; URL loading is
  injected via URLLoader.
test_import_audit: clean for behavioral intent, but upstream tests are not
  liftable: suite_test.go is a testdata-driven runner (needs the upstream
  testdata tree), example tests assert stdout text. Track B generation
  required. Estimated liftable share < 10%.
docs_test_alignment: aligned — package docs and README describe exactly the
  compile/validate/output surface the suite exercises
contamination_note: jsonschema@v6.0.3, released 2026-06-28, relative to
  training cutoff: after (v6 API largely stable since 2024-05, so partial
  familiarity is assumed; behavior depth is in the JSON Schema drafts)
decision: keep
reason: reference-graph compiler with cross-draft validation rules and three
  standardized projections of one error state; rule-engine shape resists
  pattern matching and integration spans >= 3 public projections.
risks: JSON Schema is a published standard (saturation risk is mitigated by
  scoping to draft 2020-12 + draft-07 subset and by asserting output-format
  invariants rather than suite conformance); large keyword surface must be
  scoped so the spec stays honest.
scope_plan: N/A by thresholds (src_loc < 15000, test_functions < 300), but
  spec deliberately scopes to: default draft 2020-12 compilation, $ref/$anchor/
  $defs resolution, core validation keywords, boolean schemas, draft-07
  $ref-only interop, output formats, compiler error semantics. Custom
  vocabularies, content assertions, format assertion vocabulary internals,
  localization, and http loading are Non-Goals.
```

## Difficulty shapes observed (candidate-selector heuristics)

- **Lazily resolved reference graph**: `$ref`/`$anchor`/`$dynamicRef` chains
  resolved at compile time across resources; cycle detection
  (MetaSchemaCycleError); unresolved anchors must fail the whole compile.
- **Reimplementation of a format rule**: JSON Schema draft semantics
  (unevaluatedProperties/items interplay, contains bounds, dependent schemas)
  rather than a call into an existing engine.
- **Equivalence judgement**: uniqueItems/enum/const use JSON value equality
  where 1 vs 1.0 equality and object key-order independence must be decided.
- **Integration across >= 3 projections**: one failed validation is observed
  through Error() string tree, FlagOutput, BasicOutput, DetailedOutput and
  the kind taxonomy; all must agree.

## Selection log row (CANDIDATES.md deferred; write scope is staging/ only)

| santhosh-tekuri/jsonschema | SELECTED | 5607 LOC | 27 test funcs | ref-graph compiler + multi-projection validation errors |
