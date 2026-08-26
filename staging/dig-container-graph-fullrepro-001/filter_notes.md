# Stage 1 evidence brief — dig-container-graph-fullrepro-001

```
repo: uber-go/dig
source_path: https://github.com/uber-go/dig (local: dev/repo-pool/dig)
commit: af45368b8ef9faaff2102eceac6535b62bebb185 (tag v1.19.0, released 2025-05-13)
src_loc: 5056 (root package) + 978 (internal/{digreflect,dot,graph,digerror,digclock}) = ~6034
test_functions: 72 top-level Test funcs (~165 t.Run subtests in dig_test.go alone) + 1 Example
test_files: 17 (*_test.go at root)
dominant_test_styles: mixed black-box (package dig_test via internal/digtest wrapper)
  and white-box (package dig: param/result/provide/error/constructor internals);
  one golden-file test (visualize_golden_test.go vs testdata/*.dot)
public_docs: doc.go (348-line package doc: containers, parameter/result objects,
  optional/name/group tags, scopes), README.md, pkg.go.dev/go.uber.org/dig,
  uber-go/dig GoDoc examples (example_test.go)
core_fact_source: a per-scope dependency graph keyed by (type, name|group):
  provider nodes with constructor functions, memoized results, decorator layers,
  and parent/child scope visibility rules
derived_views: (1) Invoke execution semantics (lazy constructor calls, memoization,
  error propagation); (2) Provide-time graph verification (immediate vs deferred
  acyclic check, duplicate detection); (3) error tree projection (dig.Error,
  RootCause unwrapping, formatted multi-line messages with provider locations);
  (4) DOT-graph text projection (Visualize / VisualizeError); (5) String() dump
  of nodes and values; (6) struct-tag mini-language (dig.In/dig.Out with
  name/group/optional/flatten/soft) reinterpreted by reflection
external_deps: none at runtime (go.mod requires only testify for tests); no
  network, no filesystem state
test_import_audit: HIGH_RISK for direct lift — 5 of 6 black-box test files import
  go.uber.org/dig/internal/digtest and internal/digclock (internal wrapper API);
  white-box files are in-package. Track B expected.
docs_test_alignment: aligned — doc.go + godoc describe exactly the projections the
  tests exercise (provide/invoke semantics, tags, scopes, errors)
contamination_note: dig@v1.19.0, released 2025-05-13, relative to training cutoff:
  likely before (library is popular, semantics documented; API shape is public
  knowledge — difficulty must come from precise rule-engine behavior, not obscurity)
decision: keep
reason: reflection-driven DI rule engine with a lazily materialized dependency
  graph, cycle detection, layered scopes and >= 4 public projections of one graph
  state; single-file implementation impossible without violating the packet.
risks: (a) upstream tests not liftable (internal digtest wrapper) -> Track B
  generation cost; (b) callbacks/PanicError/DOT-visualization surface is large —
  scope the spec to the core graph engine + error/visualize projections actually
  specified; (c) group value ordering is documented as unspecified — tests must
  use order-insensitive assertions.
scope_plan: target_subdomain=core container/scope graph engine (Provide/Invoke/
  Decorate/Scope + In/Out tag language + error projection + String/Visualize
  structural properties), expected_oracle_max=90; callbacks (WithProviderCallback
  et al.), DryRun, LocationForPC, PanicError formatting details out of scope.
```

## Difficulty shapes observed (selection rationale, not oracle targets)

- **Lazily resolved reference graph**: constructors run only when demanded by an
  Invoke, results are memoized per scope, cycle detection either at Provide time
  or deferred to Invoke (DeferAcyclicVerification); a failed chain must leave no
  prefix memoized as resolved.
- **Reimplementation of a format rule**: the dig.In/dig.Out struct-tag language
  (`name`, `group`, `optional`, `flatten`, `soft`) is interpreted via reflection,
  including embedding rules and error cases (e.g. exported-field requirement,
  tag combinations that are rejected).
- **Equivalence judgement**: keys are (type, name) identity; As() re-registers a
  constructor under interface types; decorators must shadow exactly the decorated
  key within scope visibility, not globally.
- **>= 3 public projections of one state**: invoke results, error trees with
  RootCause, String() dumps, and DOT visualization all reflect the same graph.

## source_boundary (spec internal header, recorded here per batch convention)

```
task_id: dig-container-graph-fullrepro-001
spec_version: v1
delta: initial version
source_boundary:
  - doc.go (348-line package documentation: Container/Provide/Invoke,
    parameter & result objects, optional deps, named values, value groups)
  - godoc of every exported symbol (go doc -all at v1.19.0)
  - README.md
  - behavior probes against pinned v1.19.0 checkout (wip probe logs):
    provide/invoke validation errors, duplicate & cycle rejection + rollback,
    DeferAcyclicVerification whole-graph invoke check, memoization
    (success-only; failed ctor re-runs), named values, groups
    (flatten/soft/empty/failing member), scope visibility + Export,
    decorator scoping/at-most-once/already-decorated/group decoration,
    RecoverFromPanics + PanicError + RootCause, String()/Visualize() shape,
    IsIn/IsOut
  - upstream test tree read for behavior-family inventory only; no test
    code lifted (Track B)
```

## Selection record

| repo | status | metric | detail |
|------|--------|--------|--------|
| uber-go/dig | SELECTED | ~6.0k LOC, 72 test funcs | DI graph engine; scopes/groups/decorators; Track B expected |
