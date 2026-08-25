# Stage 1 evidence brief — cty-value-type-system-fullrepro-001

```
repo: zclconf/go-cty
source_path: https://github.com/zclconf/go-cty (wip/screen/go-cty)
commit: pinned tag v1.19.0 (released 2026-07-06); HEAD at screen time a918e1174fcf2a25b7a222e7e78b00ea40ace26c
src_loc: 11776 in scope (cty 7296 + convert 2404 + json 987 + msgpack 1089); repo total ~20k incl. function/stdlib 5960, gocty 1392 (out of scope)
test_functions: 83 in scope dirs (cty, convert, json, msgpack); 165 repo-wide
test_files: 30 in scope (16 cty + 6 convert + 5 json + 2 msgpack + 1 ctystrings excluded)
dominant_test_styles: table-driven mega-runners (TestValueEquals alone: ~589 cases in one func); in-package white-box placement (package cty/convert/json/msgpack, only 2 files external)
public_docs: README.md, docs/types.md, docs/concepts.md, docs/convert.md, docs/json.md, docs/refinements.md, docs/marks.md, godoc for cty/convert/json/msgpack
core_fact_source: one dynamic value/type system — values carry a cty.Type, nullness, unknownness (+refinements), and marks; every subsystem projects the same value semantics
derived_views: (1) value operation API (Equals/RawEquals/arithmetic/GetAttr/Index/Length/sets), (2) type system checks (Type.Equals/TestConformance/FriendlyName/GoString), (3) convert: safe/unsafe conversion + type unification, (4) JSON round trip incl. type serialization and ImpliedType, (5) msgpack round trip incl. unknown-value extension + refinement encoding
external_deps: go proxy modules only (vmihailenco/msgpack/v5, apparentlymart/go-textseg, golang.org/x/text, go-cmp test-only); no network at test time beyond module download
test_import_audit: HIGH_RISK for Track A — in-package (white-box) test placement for nearly all files means lifting requires rehoming; mega-runner style means base-function granularity is far too coarse for per-test scoring (83 funcs hide thousands of cases)
docs_test_alignment: aligned — docs/ describes exactly the behaviours the tests exercise (equality ladder, conversion/unification rules, serialization round trips, refinements, marks)
contamination_note: zclconf/go-cty@v1.19.0, released 2026-07-06, relative to training cutoff: after (refinement/marks details from recent minors reduce memorisation value); library widely used via Terraform so older API shapes are known — spec pins observable v1.19.0 behaviour
decision: keep
reason: a single shared fact source (dynamic values with type/null/unknown/marks) projected through five public surfaces, with equivalence-judgement semantics (Equals vs RawEquals vs type unification) that resist pattern-matching.
risks: big.Float precision semantics must be specified carefully; msgpack byte-level encoding must be tested via round trip + targeted prefix checks, not full golden bytes; scope must stay out of function/stdlib and gocty
scope_plan: target_subdomain=core value/type system + convert + json + msgpack (exclude cty/function, cty/function/stdlib, cty/gocty, cty/ctystrings, cty/set internals, cty/planmerge), expected_oracle_max=115
```

## Hard gates

| gate | result | evidence |
|------|--------|----------|
| LOC >= 3000 | PASS | in-scope source 11776 LOC (cty core alone 7296) |
| not single-file | PASS | value semantics spread over ~40 files and 4 packages |
| shared fact source, >= 2 projections | PASS | 5 projections listed above over one value/type model |
| usable test suite | PASS (shape caveat) | table-driven, deterministic, no network; but mega-runner granularity and in-package placement push oracle to Track B |
| not closed standard / high-saturation | PASS | cty's semantics (unknowns, refinements, marks, unification) are project-defined, not an RFC; no other implementation to memorise |
| no private details needed | PASS | all listed behaviours observable through exported API |
| docs-test projection match | PASS | docs/*.md cover the same library API surface tests exercise |

## Difficulty shapes (soft signals)

- **equivalence judgement**: Value.Equals (three-valued with unknowns) vs
  RawEquals (meta-equality) vs Type.Equals vs convert.Unify — four distinct
  sameness relations that must not be conflated.
- **rule reimplementation**: conversion matrix (object->map, tuple->list,
  null/unknown passthrough, unsafe string->number) and msgpack/JSON encodings
  of types and unknown-value refinements.
- **lazily resolved / partial knowledge**: unknown values with refinements
  (null-ness, numeric bounds, string prefix, collection length bounds) must
  propagate through operations and serialization.
- **integration across >= 3 projections**: value -> convert -> json -> msgpack
  round trips over the same facts.

## Upstream test audit summary (S3A preview)

- ~81/83 in-scope test functions are declared in-package (`package cty` etc.):
  white-box placement, cannot be lifted as-is into an external oracle module.
- Dominant style is one mega-runner per API with 100-600 anonymous subcases;
  per-test outcomes at base-function granularity would be ~83 coarse bits and
  a single behavioural defect would flip whole families.
- Decision preview: Track B generation targeted from spec sections, mirroring
  the approach used for jsonschema/dig/gocmp/participle packets.

## Dedup

Not present in `tasks/` (no Go tasks on main) nor in the `origin/go-tasks-20260821`
register (afero, bbolt, casbin, expr, gojq, goose, nutsdb, ristretto, tengo,
validator). No shape overlap with tasks 1-4 of this batch: jsonschema (schema
validation), dig (DI graph), go-cmp (equality diffing of native Go values —
different fact source: go-cmp compares arbitrary Go values structurally; cty
implements its own dynamic type lattice with unknowns/marks), participle
(parser building).
