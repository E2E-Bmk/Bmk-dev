# Filter notes — ojg-jsonpath-engine-fullrepro-001

## Stage 1 evidence brief

```
repo: ohler55/ojg
source_path: https://github.com/ohler55/ojg (local clone wip/repos/ojg)
commit: fc5d690db5103e00c48f56b37544bd22ba0d77b9 (tag v1.28.5)
src_loc: 10916 in scope (jp package, tests excluded; whole module ~31k across
         jp/oj/sen/alt/gen/asm/pretty; no generated code, no vendoring)
test_functions: 159 (jp package)
test_files: 19 (jp package); 18 external black-box (package jp_test),
            1 in-package (norm_test.go)
dominant_test_styles: table-driven black-box via the in-repo tt assert
    package; two mega-table suites (get_test.go getTestData, remove_test.go)
    keyed to shared fixture builders; per-behavior small tests elsewhere
public_docs: go doc -all github.com/ohler55/ojg/jp (doc comments on all
    exported symbols), README.md JSONPath section, doc.go package comment
core_fact_source: the path expression (Expr, a sequence of fragments)
    produced by parsing path text or by the builder API, plus the filter
    Equation tree embedded in it
derived_views: (1) normalized string form — String/BracketString/Append;
    (2) selection — Get/First/FirstFound/Has/Locate over native Go data
    (maps, slices, primitives, public struct members via reflection);
    (3) mutation — Set/SetOne/Del/DelOne/Remove/RemoveOne/Modify/ModifyOne
    and Must* variants; (4) enumeration — Walk with per-leaf paths;
    (5) matching — PathMatch and MatchHandler; (6) filter view — Equation
    parse/build + String round trip
external_deps: none (go.mod has zero requires); no network, no CGO
test_import_audit: HIGH_RISK for Track A retention — ~100% of jp test files
    import out-of-scope ojg packages at module level (tt asserts everywhere;
    gen typed-node variants, oj/sen printers, alt, pretty in the big suites);
    Track B expected, consistent with the rest of this batch
docs_test_alignment: aligned — doc comments cover the same library API the
    tests exercise (no CLI-only docs)
contamination_note: ojg@v1.28.5, released 2026-08-21 (4 days before this
    packet), after any plausible training cutoff; older ojg versions are
    certainly in training data, so the binding is pinned-tag observables,
    and recent behavior deltas (e.g. sen '+' panic fix in the same release
    window) make memorized behavior unreliable
decision: keep
reason: rule-engine shape — a JSONPath dialect (parser + normalized printer
    + evaluator + mutator) whose semantics are the author's judgement calls,
    not a recallable standard, over one fact source with six public
    projections
risks: JSONPath is a familiar pattern (goessner/RFC 9535) — saturation risk
    mitigated by binding to pinned v1.28.5 observables where the dialect
    diverges (union order, descent order, slice clamping, filter coercions,
    mutation auto-creation); reflection paths over structs can surface
    unstatable edge behavior — keep struct coverage to public-member
    happy paths; module spans 7 packages — scope is jp only, gen/oj/sen/alt
    /asm/pretty declared out of scope
scope_plan: target_subdomain = jp path engine over native Go data
    (parse/build/normalize, get/first/has/locate, set/del/remove/modify,
    walk, path match, filter equations); expected_oracle_max = 170
```

## Stage 2 spec sources (source_boundary detail)

Spec v1 was written from: `go doc -all github.com/ohler55/ojg/jp`
(doc comments on all exported symbols, captured to
wip/probe/ojg/api_dump.txt), the README JSONPath section, and 51 probe
rounds against pinned v1.28.5 executed from a scratch module
(`wip/probe/ojg/`): parse/render round trips and error catalog (R1-R2,
R28, R40-R41, R51), builder equivalence (R3, R35), Get/First/Has
semantics incl. typed containers and structs (R4-R5, R14, R29, R42,
R48, R50), filter operators, literals, and functions (R6, R26-R27,
R30, R34, R43, R47), Set/Del/Remove/Modify semantics and error texts
(R7-R9, R19-R22, R31, R38, R44), Walk/Locate/PathMatch (R10-R13,
R23-R25, R47, R49), map-order nondeterminism (R18, R32-R33), and
Script/Filter/Equation carriers (R15-R16, R26, R36, R46). Upstream
source consulted for rule confirmation only (absence of sorting in
get.go wildcard evaluation; Wildcard spelling byte).

Deliberately excluded from spec scope (declared in Non-Goals or left
unstated): gen.Node operations (GetNodes/FirstNode), MatchHandler/
TargetRest streaming handlers, Proc/Procedure/CompileScript and the
script-function registries, Indexed/Keyed/RemovableIndexed custom
collections, Form/Script.Inspect/Script.Eval introspection, struct
mutation (observed silent no-op on value fields), the ConstList
rendering gap for plain-int elements (renders empty; spec states the
int64/float64/string/bool/nil vocabulary instead), and descent
Get-order on slice-only data (observed deepest-first but stated
unspecified alongside all descent ordering).

Stage 3 generation probes added three entries to this exclusion list
and two spec corrections. Excluded: root-anchored operands built with
the `Get` equation constructor (`jp.Get(jp.R()...)`) render identically
to parsed `$`-references but evaluate to nothing in the pinned
reference — the workflow checks use `MustParseEquation`, whose
converted filters do resolve root references, and the constructor
corner stays out of both spec and oracle. Also excluded: the rendering
of `!` applied to a parenthesized group followed by more operators —
the pinned reference folds the trailing operators into the negated
group (`!(A) && B` renders `!(A && B)`), so the spec scopes the
parenthesization guarantee to binary-operator nesting and declares the
negated-group rendering unspecified; no oracle test enters that zone. Corrected in the spec (spec_iter 1): a final descent
`Set` creates the named key in every map the descent visits rather than
writing only to existing keys, and CVI 6 is scoped to targets without
negative index fragments because PathMatch — as the spec itself states —
never matches a negative target index against the non-negative indexes
Locate emits.

Difficulty shapes exhibited (selection rationale, not a checklist):
reimplementation of a format rule (dialect parser + normalized-form printer
with two bracket styles); an equivalence judgement (PathMatch pattern-vs-path
decision, Normal-form classification); integration tests can span >= 3
projections of one expression (parse -> String round trip, Get/Locate
agreement, Set -> Get read-back, Walk vs Locate agreement); mutation with
implementation-defined auto-creation semantics.
