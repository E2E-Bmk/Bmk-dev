# Stage 1 evidence brief — gocmp-equality-engine-fullrepro-001

```
repo: google/go-cmp
source_path: https://github.com/google/go-cmp (local: dev/repo-pool/go-cmp)
commit: 9b12f366a942ebc7254abc7f32ca05068b455fb7 (tag v0.7.0, released 2025-01-14)
src_loc: 3986 (cmp package) + 1840 (cmp/internal/{diff,function,value,flags}) = 5826
  (cmpopts subpackage excluded from scope)
test_functions: 4 top-level Test funcs in cmp (giant table-driven runners over
  ~1000 cases) + cmpopts tests (out of scope)
test_files: compare_test.go, options_test.go, example_*.go + testdata golden files
dominant_test_styles: table-driven mega-runners comparing against golden diff
  transcripts (testdata/diffs), white-box option introspection
public_docs: package godoc (456 lines: Equal rule ladder, Diff format contract,
  every Option constructor, Path/PathStep/Result API), README.md
core_fact_source: the recursive equality judgement over a pair of Go value trees:
  an option set (ignore/transform/compare + path/value filters) resolved at every
  node, an Equal-method dispatch rule, kind-wise structural rules, visited-address
  cycle tracking
derived_views: (1) Equal boolean verdict; (2) Diff text (empty iff Equal; -/+
  line prefixes are documented contract, layout is explicitly unstable);
  (3) Reporter protocol (PushStep/Report/PopStep traversal with typed PathStep
  union and Result cause flags ByFunc/ByMethod/ByIgnore/ByCycle); (4) Path
  projections (String simplified, GoString Go-syntax, Index/Last); (5) panic
  surface (unexported fields, ambiguous options, unfiltered Ignore, malformed
  option functions)
external_deps: none (go.mod has no requirements)
test_import_audit: HIGH_RISK for direct lift — the 4 runners depend on golden
  transcript files and unexported test scaffolding; Track B expected
docs_test_alignment: aligned — godoc specifies exactly the judgement rules the
  tests exercise
contamination_note: go-cmp@v0.7.0, released 2025-01-14, relative to training
  cutoff: likely before (ubiquitous test dependency; API shape is public
  knowledge — difficulty must come from the precise rule ladder, filter
  composition, and cycle semantics, not obscurity)
decision: keep
reason: an equivalence-judgement engine (difficulty shape #3 verbatim) with a
  documented rule ladder, an option-filtering mini-language, reflection-driven
  traversal with cycle detection, and >= 4 public projections of one judgement.
risks: (a) Diff layout is documented unstable -> tests may only assert
  empty-iff-equal and the -/+ prefix contract, never layout; (b) panic-heavy
  contract needs careful recover-based tests; (c) cmpopts is a large helper
  surface -> excluded from scope (spec never mentions it).
scope_plan: target_subdomain=cmp package only (Equal/Diff, fundamental options
  + filters, Reporter/Path/Result), expected_oracle_max=100; cmpopts excluded.
```

## Difficulty shapes observed (selection rationale, not oracle targets)

- **Equivalence judgement**: the entire library is one — false alarms as wrong
  as misses; nil vs empty distinction, interface concrete-type agreement,
  Equal-method precedence over structural descent.
- **Lazily resolved reference graph**: visited-address tracking during descent;
  cyclic linked structures equal only when both sides revisit at the same step.
- **Reimplementation of a language rule**: assignability-driven dispatch of
  Comparer/Transformer/filters; embedded-struct field traversal order; the
  documented rule ladder ordering (options > Equal method > kinds).
- **>= 3 public projections**: Equal verdict, Diff emptiness/prefix contract,
  Reporter traversal with Result cause flags, Path renderings.

## source_boundary (spec internal header, recorded here per batch convention)

```
task_id: gocmp-equality-engine-fullrepro-001
spec_version: v1
delta: initial version
source_boundary:
  - package godoc of cmp at v0.7.0 (go doc -all ./cmp)
  - README.md
  - behavior probes against pinned v0.7.0 checkout (wip probe logs): rule
    ladder order, Equal-method dispatch incl. nil receivers, nil-vs-empty,
    interface/pointer/cycle rules, panic surface (unexported fields,
    unfiltered Ignore, ambiguous options, bad option signatures), filter
    composition, transformer recursion guard, Reporter call protocol,
    Path.String/GoString shapes, Diff prefix contract
  - upstream test tree read for behavior-family inventory only; no test code
    lifted (Track B)
```

## Selection record

| repo | status | metric | detail |
|------|--------|--------|--------|
| golang-jwt/jwt | REJECTED | 2371 LOC | hard gates: LOC < 3000; JWT is a closed standard (RFC 7519) with high pattern-match saturation |
| google/go-cmp | SELECTED | 5826 LOC, 4 upstream runners | equivalence engine; option filter language; Reporter/Path projections; Track B |
