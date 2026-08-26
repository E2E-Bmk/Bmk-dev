# filter_notes — goyaml-yaml-engine-fullrepro-001

repo: goccy/go-yaml
source_path: https://github.com/goccy/go-yaml
commit: pinned tag v1.19.2 (92bc79cb5f685e999ad131473168fc45215d12d9, released 2026-01-08)
src_loc: 15260 (non-test .go, excluding benchmarks/, cmd/, testdata/)
test_functions: 140 (excluding benchmarks/)
test_files: 13 (decode_test.go 53, encode_test.go 29, testdata/yaml_test.go 16,
  parser/parser_test.go 12, path_test.go 9, yaml_test.go 7, lexer 5, printer 3,
  token 2, ast 2, others)
dominant_test_styles: black-box table-driven unit tests in external `yaml_test`
  packages; one data-driven official-suite runner (TestYAMLTestSuite over
  testdata/yaml-test-suite goldens); a few golden-string printer tests
public_docs: README.md (420 lines: features, struct tags, anchors/aliases,
  CommentMap, Path, validation, errors), pkg.go.dev API docs for yaml, parser,
  ast, lexer, printer, token packages
core_fact_source: one YAML document model (token stream -> AST -> Go values)
  with anchor/alias resolution, YAML 1.2 scalar typing rules, struct-tag
  mapping rules, and comment association
derived_views: (1) yaml.Unmarshal/Decoder into Go values incl. struct tags,
  anchors, merge keys; (2) yaml.Marshal/Encoder from Go values incl. quoting,
  flow/block styles, auto-alias; (3) parser/ast: ParseBytes -> typed AST with
  positions, ast.Node String() rendering; (4) yaml.Path / PathString queries:
  Read/Filter/Replace/Merge addressed by JSONPath-like syntax; (5) CommentMap
  round trip decode->encode; (6) source-annotated errors: yaml.FormatError with
  line/col and caret, structured error text; (7) lexer/token stream with
  offsets, line/column; (8) JSONToYAML/YAMLToJSON converters
external_deps: none at runtime (go.mod has zero requires); tests use
  google/go-cmp (assertion-only, acceptable in oracle module) and
  goccy/go-yaml/testdata packages (excluded)
test_import_audit: clean at module level for the main suite (external
  yaml_test packages, public imports); exceptions: decode_test.go imports
  internal/errors (one file), yaml_test_suite_test.go binds to testdata
  goldens — both excluded from any lifted set
docs_test_alignment: aligned — README + package docs describe the same
  decode/encode/path/comment/error projections the tests exercise
contamination_note: goccy/go-yaml@v1.19.2, released 2026-01-08, relative to
  training cutoff: after (v1.15+ rewrote error formatting and comment
  handling; behaviour of recent minors diverges from widely memorised
  gopkg.in/yaml.v2/v3 semantics, which is itself a difficulty asset: the
  fact source rewards observing this engine, not recalling the classic one)
decision: keep
reason: one document model projected through 8 public surfaces, anchor/alias
  resolution is a lazily resolved reference graph, YAML scalar typing +
  struct-tag mapping is a language-rule reimplementation, and the suite is
  black-box table-driven — all difficulty shapes without private coupling.
risks: YAML core is a public standard (saturation pressure on scalar rules;
  mitigated by engine-specific projections: Path, CommentMap, annotated
  errors, token positions); a handful of printer tests are golden-string
  (excluded or rewritten); mega-table functions (TestDecoder ~500 cases)
  are too coarse for per-test scoring (Track B likely for those areas)
scope_plan: target_subdomain = core yaml package public API (Unmarshal/
  Marshal/Path/CommentMap/errors/converters) + parser/lexer/token positions
  and AST rendering as secondary projections; expected_oracle_max = 140
language: go
source_boundary: spec.md ships without internal header; candidate sees spec
  only. Oracle tests live in benchmark-owned module `goyaml-yaml-engine-
  oracle`; scoring wires the candidate module via go mod edit -replace
  github.com/goccy/go-yaml => <candidate>.
