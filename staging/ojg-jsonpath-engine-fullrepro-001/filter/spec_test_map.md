# spec_test_map — ojg-jsonpath-engine-fullrepro-001

oracle_source: generated_only (Track B; see filter/rewrite_audit.md)
oracle_version: 2026-08-26T00:00:00Z
reference: github.com/ohler55/ojg v1.28.5 (commit fc5d690db5103e00c48f56b37544bd22ba0d77b9)
suites: oracle/atomic (131 tests), oracle/integration (22 tests)
nodeid format: {suite}::{TestName}

| test_nodeid | layer | assertion_kind | spec_section | status | notes |
|-------------|-------|----------------|--------------|--------|-------|
| atomic::TestBuildShortForms | atomic | positive | section Building Expressions in Code — chained short-form builders | covered |  |
| atomic::TestBuildLongForms | atomic | positive | section Building Expressions in Code — spelled-out method forms | covered |  |
| atomic::TestBuiltEqualsParsed | atomic | positive | section Building Expressions in Code — built equals parsed | covered |  |
| atomic::TestBuildDescent | atomic | positive | section Building Expressions in Code — descent builder | covered |  |
| atomic::TestBuildAnchors | atomic | positive | section Building Expressions in Code — at and root starters | covered |  |
| atomic::TestBuildSlice | atomic | positive | section Building Expressions in Code — slice builder and SliceNotSet | covered |  |
| atomic::TestNewSliceUnset | atomic | positive | section Building Expressions in Code — NewSlice returns all-unset parts | covered |  |
| atomic::TestBuildUnion | atomic | positive | section Building Expressions in Code — union builder and key kinds | covered |  |
| atomic::TestBuildFilterFragment | atomic | positive | section Building Expressions in Code — filter attachment with F | covered |  |
| atomic::TestBuildEmptyX | atomic | positive | section Building Expressions in Code — X starts empty | covered |  |
| atomic::TestBuildBracketFlag | atomic | positive | section Building Expressions in Code — bracket display flag | covered |  |
| atomic::TestBuildWildcardSpelling | atomic | positive | section Building Expressions in Code — wildcard builder spelling | covered |  |
| atomic::TestBuildAppendReturnsExtended | atomic | positive | section Building Expressions in Code — builders leave the receiver reusable | covered |  |
| atomic::TestBuildQuotedChild | atomic | positive | section Building Expressions in Code — child keys with specials render quoted | covered |  |
| atomic::TestEquationComparisonRendering | atomic | positive | section Building and Parsing Equations — comparison constructors render | covered |  |
| atomic::TestEquationNestedRendering | atomic | positive | section Building and Parsing Equations — logical and arithmetic nesting | covered |  |
| atomic::TestEquationConstants | atomic | positive | section Building and Parsing Equations — constant rendering forms | covered |  |
| atomic::TestEquationFunctionRendering | atomic | positive | section Building and Parsing Equations — function constructors render bare | covered |  |
| atomic::TestEquationOperatorRendering | atomic | positive | section Building and Parsing Equations — operator constructors render | covered |  |
| atomic::TestEquationParse | atomic | positive | section Building and Parsing Equations — MustParseEquation round trip | covered |  |
| atomic::TestEquationFilterConversion | atomic | positive | section Building and Parsing Equations — Filter conversion | covered |  |
| atomic::TestEquationScriptConversion | atomic | positive | section Building and Parsing Equations — Script conversion and Match | covered |  |
| atomic::TestNewScriptForms | atomic | positive | section Filters and Scripts — NewScript accepts optional parentheses | covered |  |
| atomic::TestScriptMatchSemantics | atomic | positive | section Filters and Scripts — Script.Match on single elements | covered |  |
| atomic::TestNewFilterForms | atomic | failure_path | section Filters and Scripts — NewFilter requires the full bracket form | covered | wrapped-form error spec-declared; positive guard included |
| atomic::TestErrNotTerminated | atomic | failure_path | section Error Semantics — unterminated fragments | covered |  |
| atomic::TestErrPredicateTokens | atomic | failure_path | section Error Semantics — predicate operand and operator errors | covered |  |
| atomic::TestErrBracketFragments | atomic | failure_path | section Error Semantics — bracket fragment errors | covered |  |
| atomic::TestErrGenericParse | atomic | failure_path | section Error Semantics — generic parse errors | covered |  |
| atomic::TestErrFragmentStart | atomic | failure_path | section Error Semantics — fragment-start errors | covered |  |
| atomic::TestErrSetEndings | atomic | failure_path | section Error Semantics — Set ending-fragment rules | covered |  |
| atomic::TestErrDelEndings | atomic | failure_path | section Error Semantics — Del ending-fragment rules | covered |  |
| atomic::TestErrRemoveEndings | atomic | failure_path | section Error Semantics — Remove ending-fragment rules | covered |  |
| atomic::TestErrFollowKinds | atomic | failure_path | section Error Semantics — follow errors name the kind and prefix | covered |  |
| atomic::TestErrMustPanics | atomic | failure_path | section Error Semantics — Must panics mirror error texts | covered | exact messages spec-declared |
| atomic::TestFilterEquality | atomic | positive | section Filters and Scripts — equality and inequality | covered |  |
| atomic::TestFilterOrdering | atomic | positive | section Filters and Scripts — ordering comparisons | covered |  |
| atomic::TestFilterStringOrdering | atomic | positive | section Filters and Scripts — string ordering is lexicographic | covered |  |
| atomic::TestFilterNoCrossKindCoercion | atomic | positive | section Filters and Scripts — no cross-kind coercion | covered |  |
| atomic::TestFilterLogic | atomic | positive | section Filters and Scripts — logical composition and grouping | covered |  |
| atomic::TestFilterArithmetic | atomic | positive | section Filters and Scripts — arithmetic inside predicates | covered |  |
| atomic::TestFilterBarePathExistence | atomic | positive | section Filters and Scripts — bare-path predicates test existence | covered |  |
| atomic::TestFilterExistsHas | atomic | positive | section Filters and Scripts — exists and has operators | covered |  |
| atomic::TestFilterNullAndNothing | atomic | positive | section Filters and Scripts — null vs Nothing vs missing | covered |  |
| atomic::TestFilterIn | atomic | positive | section Filters and Scripts — membership with in | covered |  |
| atomic::TestFilterEmpty | atomic | positive | section Filters and Scripts — emptiness operator | covered |  |
| atomic::TestFilterRegex | atomic | positive | section Filters and Scripts — regex operator forms | covered |  |
| atomic::TestFilterLengthCount | atomic | positive | section Filters and Scripts — length and count functions | covered |  |
| atomic::TestFilterMatchSearch | atomic | positive | section Filters and Scripts — match and search functions | covered |  |
| atomic::TestFilterOnMap | atomic | positive | section Filters and Scripts — filters apply to map elements | covered |  |
| atomic::TestSetExisting | atomic | positive | section Mutating Data — Set stores at existing locations | covered |  |
| atomic::TestSetCreatesMapChain | atomic | positive | section Mutating Data — Set creates missing map chains | covered |  |
| atomic::TestSetCreatesArrayForIndex | atomic | positive | section Mutating Data — Set creates an array for a missing key + index | covered |  |
| atomic::TestSetOutOfBounds | atomic | failure_path | section Mutating Data — Set does not extend existing slices | covered | exact follow error spec-declared |
| atomic::TestSetWildcardAll | atomic | positive | section Mutating Data — Set through wildcard writes every element | covered |  |
| atomic::TestSetOneFirstOnly | atomic | positive | section Mutating Data — SetOne writes only the first match | covered |  |
| atomic::TestSetThroughFilterAndSlice | atomic | positive | section Mutating Data — Set through filter and slice fragments mid-path | covered |  |
| atomic::TestSetUnionAndDescentLast | atomic | positive | section Mutating Data — final union and descent set existing keys | covered |  |
| atomic::TestSetSilentNoOps | atomic | positive | section Mutating Data — silent no-op writes | covered |  |
| atomic::TestSetPartialCreationRemains | atomic | failure_path | section Mutating Data — partial creation stays when a later step fails | covered | exact follow error spec-declared; state assertions included |
| atomic::TestMustSetPanics | atomic | failure_path | section Mutating Data — MustSet panics with the Set error message | covered | exact message spec-declared |
| atomic::TestDelSemantics | atomic | positive | section Mutating Data — Del removes map keys and leaves slice holes | covered |  |
| atomic::TestDelOneFirstOnly | atomic | positive | section Mutating Data — DelOne clears only the first match | covered |  |
| atomic::TestDelUnionAndNegative | atomic | positive | section Mutating Data — Del union and negative index positions | covered |  |
| atomic::TestDelDescent | atomic | positive | section Mutating Data — descent Del removes existing matching keys | covered |  |
| atomic::TestRemoveShortensSlice | atomic | positive | section Mutating Data — Remove excises slice elements | covered |  |
| atomic::TestRemoveTopSliceRoot | atomic | positive | section Mutating Data — Remove on a top-level slice returns a new root | covered |  |
| atomic::TestRemoveKindsOfTargets | atomic | positive | section Mutating Data — Remove of map keys, wildcards, and filters | covered |  |
| atomic::TestRemoveOneFirstOnly | atomic | positive | section Mutating Data — RemoveOne excises only the first match | covered |  |
| atomic::TestRemoveSliceFragment | atomic | positive | section Mutating Data — Remove slice fragment target | covered |  |
| atomic::TestRemoveNoMatchSilent | atomic | positive | section Mutating Data — no-match Remove is silent | covered |  |
| atomic::TestModifyReplaces | atomic | positive | section Mutating Data — Modify replaces matched elements via callback | covered |  |
| atomic::TestModifyUnchangedFlag | atomic | positive | section Mutating Data — modifier returning false leaves elements | covered |  |
| atomic::TestModifyOneFirstOnly | atomic | positive | section Mutating Data — ModifyOne stops after the first replacement | covered |  |
| atomic::TestModifyReplacesSliceValue | atomic | positive | section Mutating Data — Modify can replace a whole slice value | covered |  |
| atomic::TestModifyRoot | atomic | positive | section Mutating Data — Modify on the root calls the modifier once | covered |  |
| atomic::TestParseStringAndParseAgree | atomic | positive | section Path Expressions and Parsing — parse entry points | covered |  |
| atomic::TestParseEmptyInput | atomic | positive | section Path Expressions and Parsing — empty input | covered |  |
| atomic::TestParseOptionalLeader | atomic | positive | section Path Expressions and Parsing — optional leading anchors | covered |  |
| atomic::TestParseDigitDotTokenIsChild | atomic | positive | section Path Expressions and Parsing — digit-only dot token is a key | covered |  |
| atomic::TestParseBracketQuoting | atomic | positive | section Path Expressions and Parsing — bracket quoting and normalization | covered |  |
| atomic::TestParseIntegerTokens | atomic | positive | section Path Expressions and Parsing — integer tokens | covered |  |
| atomic::TestParseSliceForms | atomic | positive | section Path Expressions and Parsing — slice forms parse and render | covered |  |
| atomic::TestParseUnionForms | atomic | positive | section Path Expressions and Parsing — union forms | covered |  |
| atomic::TestParseWildcardSpellings | atomic | positive | section Path Expressions and Parsing — wildcard spellings | covered |  |
| atomic::TestParseDescentForms | atomic | positive | section Path Expressions and Parsing — descent forms | covered |  |
| atomic::TestParseFilterNormalization | atomic | positive | section Path Expressions and Parsing — filter normalization at parse time | covered |  |
| atomic::TestParseDotKeyCharset | atomic | positive | section Path Expressions and Parsing — unicode and underscore dot keys | covered |  |
| atomic::TestMustParsePanics | atomic | failure_path | section Path Expressions and Parsing — MustParse panics on bad input | covered | exact messages spec-declared |
| atomic::TestParseSpacedKey | atomic | positive | section Path Expressions and Parsing — bracketed key with space | covered |  |
| atomic::TestReflectTypedContainers | atomic | positive | section Selecting Values from Data — typed slices and maps via reflection | covered |  |
| atomic::TestReflectArray | atomic | positive | section Selecting Values from Data — Go arrays are indexable | covered |  |
| atomic::TestReflectStructFieldCase | atomic | positive | section Selecting Values from Data — struct field matching ignores ASCII case | covered |  |
| atomic::TestReflectStructMultiCharCase | atomic | positive | section Selecting Values from Data — multi-character case-insensitive match | covered |  |
| atomic::TestReflectUnexportedInvisible | atomic | positive | section Selecting Values from Data — unexported fields are invisible | covered |  |
| atomic::TestReflectStructTraversal | atomic | positive | section Selecting Values from Data — wildcard and descent over struct fields | covered |  |
| atomic::TestReflectStructValue | atomic | positive | section Selecting Values from Data — struct values work like pointers | covered |  |
| atomic::TestSelectRootOnly | atomic | positive | section Selecting Values from Data — root-only expressions | covered |  |
| atomic::TestSelectChildKeys | atomic | positive | section Selecting Values from Data — child key steps | covered |  |
| atomic::TestSelectIndexes | atomic | positive | section Selecting Values from Data — index steps and bounds | covered |  |
| atomic::TestSelectWildcardSlice | atomic | positive | section Selecting Values from Data — wildcard over slices in order | covered |  |
| atomic::TestSelectWildcardMapSet | atomic | positive | section Selecting Values from Data — wildcard over maps is order-free | covered |  |
| atomic::TestSelectSliceFragment | atomic | positive | section Selecting Values from Data — slice fragments with clamping | covered |  |
| atomic::TestSelectUnion | atomic | positive | section Selecting Values from Data — union concatenation and duplicates | covered |  |
| atomic::TestSelectDescent | atomic | positive | section Selecting Values from Data — descent matching | covered |  |
| atomic::TestSelectFirstAndFirstFound | atomic | positive | section Selecting Values from Data — First and FirstFound basics | covered |  |
| atomic::TestSelectNilValueIsMatch | atomic | positive | section Selecting Values from Data — stored nil is a real match | covered |  |
| atomic::TestSelectHas | atomic | positive | section Selecting Values from Data — Has across fragment kinds | covered |  |
| atomic::TestSelectEmptyExpression | atomic | positive | section Selecting Values from Data — empty expression matches nothing | covered |  |
| atomic::TestSelectFirstSliceOrder | atomic | positive | section Selecting Values from Data — First order on slice-only branching | covered |  |
| atomic::TestSelectFilterSliceOrder | atomic | positive | section Selecting Values from Data — filters over slices keep element order | covered |  |
| atomic::TestSelectFilterRootReference | atomic | positive | section Selecting Values from Data — absolute references inside filters | covered |  |
| atomic::TestStringDotPreferred | atomic | positive | section Canonical String Forms — dot-preferred String rendering | covered |  |
| atomic::TestBracketStringRendering | atomic | positive | section Canonical String Forms — BracketString rendering | covered |  |
| atomic::TestBracketDescentDoesNotReparse | atomic | failure_path | section Canonical String Forms — bracket-form descent is output-only | covered | reparse error spec-declared; render assertions included |
| atomic::TestDescentCollapseBeforeBracket | atomic | failure_path | section Canonical String Forms — descent collapse before brackets | covered | collapsed-form reparse error spec-declared; render assertions included |
| atomic::TestAppendBuffer | atomic | positive | section Canonical String Forms — Append with and without brackets | covered |  |
| atomic::TestAppendStringEscapes | atomic | positive | section Canonical String Forms — AppendString quoting and escapes | covered |  |
| atomic::TestNormalClassification | atomic | positive | section Canonical String Forms — Normal classification | covered |  |
| atomic::TestStringParseFixpoint | atomic | positive | section Canonical String Forms — canonical form is a parse fixpoint | covered |  |
| atomic::TestNumberRendering | atomic | positive | section Canonical String Forms — number rendering in fragments | covered |  |
| atomic::TestWalkAllNodes | atomic | positive | section Walking, Locating, and Path Matching — Walk visits all nodes | covered |  |
| atomic::TestWalkJustLeaves | atomic | positive | section Walking, Locating, and Path Matching — justLeaves filtering | covered |  |
| atomic::TestWalkEmptyContainers | atomic | positive | section Walking, Locating, and Path Matching — empty containers yield no leaves | covered |  |
| atomic::TestWalkMapSet | atomic | positive | section Walking, Locating, and Path Matching — map children order-free | covered |  |
| atomic::TestExprWalk | atomic | positive | section Walking, Locating, and Path Matching — Expr.Walk matches only | covered |  |
| atomic::TestLocateBasics | atomic | positive | section Walking, Locating, and Path Matching — Locate normalized paths | covered |  |
| atomic::TestLocateMaxAndRoot | atomic | positive | section Walking, Locating, and Path Matching — Locate max and rootedness | covered |  |
| atomic::TestLocateDescentAndFilter | atomic | positive | section Walking, Locating, and Path Matching — Locate through descent and filters | covered |  |
| atomic::TestPathMatchFragments | atomic | positive | section Walking, Locating, and Path Matching — PathMatch fragment rules | covered |  |
| atomic::TestPathMatchDescentAndPrefix | atomic | positive | section Walking, Locating, and Path Matching — descent runs and prefixes | covered |  |
| integration::TestCVI1StringFixpointCorpus | integration | positive | section Cross-View Invariants 1 — canonical String form is a parse fixpoint for dot-form expressions | covered |  |
| integration::TestCVI1FixpointRepeated | integration | positive | section Cross-View Invariants 1 — fixpoint holds across repeated render/parse cycles including normalized filters | covered |  |
| integration::TestCVI2DualFormReparse | integration | positive | section Cross-View Invariants 2 — String and BracketString reparse to Get-equivalent expressions for descent-free paths | covered |  |
| integration::TestCVI2DualFormBuilt | integration | positive | section Cross-View Invariants 2 — dual-form reparse equivalence for built expressions without descent | covered |  |
| integration::TestCVI3BuiltParsedInterchangeable | integration | positive | section Cross-View Invariants 3 — built and parsed expressions are interchangeable across Get, Locate, Set, and PathMatch | covered |  |
| integration::TestCVI3BuilderFormsAgree | integration | positive | section Cross-View Invariants 3 — builder short and spelled-out forms produce identical expressions end to end | covered |  |
| integration::TestCVI4HasGetFirstFoundAgree | integration | positive | section Cross-View Invariants 4 — Has mirrors Get non-emptiness and FirstFound mirrors Has across expression kinds | covered |  |
| integration::TestCVI4NilValuePresence | integration | positive | section Cross-View Invariants 4 — stored nil counts as present for Has, Get, and FirstFound alike | covered |  |
| integration::TestCVI5LocateGetCorrespondence | integration | positive | section Cross-View Invariants 5 — Locate returns one Normal path per Get result and the paths re-evaluate to the same multiset | covered |  |
| integration::TestCVI5LocateOnNestedSlices | integration | positive | section Cross-View Invariants 5 — the correspondence holds for nested slice data with union and descent branching | covered |  |
| integration::TestCVI6WalkPathsEvaluate | integration | positive | section Cross-View Invariants 6 — Walk paths evaluate back to the exact callback values | covered |  |
| integration::TestCVI6LocatePathMatch | integration | positive | section Cross-View Invariants 6 — every Locate path satisfies PathMatch with the originating expression as target (targets without negative index fragments) | covered |  |
| integration::TestCVI7SetThenGet | integration | positive | section Cross-View Invariants 7 — a nil-error Set on a rooted normal path is immediately visible through Get | covered |  |
| integration::TestCVI7DelRemoveThenHas | integration | positive | section Cross-View Invariants 7 — Del and Remove of map-child paths leave Has false | covered |  |
| integration::TestCVI8PredicateCarriersAgree | integration | positive | section Cross-View Invariants 8 — a predicate behaves identically as parsed filter, built Equation filter, and per-element Script | covered |  |
| integration::TestCVI8CarrierRenderingsAgree | integration | positive | section Cross-View Invariants 8 — the three carriers render consistently as given in Building and Parsing Equations | covered |  |
| integration::TestWorkflowParseSelectMutateReread | integration | positive | section Cross-View Invariants 1, 5, 7 — parse, render, reparse, select, locate, mutate, and re-read one document end to end | covered |  |
| integration::TestWorkflowRootFilterQuery | integration | positive | section Cross-View Invariants 3, 8 — assemble a rooted filter query from a parsed equation, select with root references, then write through the filter | covered |  |
| integration::TestWorkflowGrowPruneAudit | integration | positive | section Cross-View Invariants 6, 7 — grow a document with Set auto-creation, prune with Del and Remove, and audit with Walk | covered |  |
| integration::TestWorkflowEquationDrivenModify | integration | positive | section Cross-View Invariants 7, 8 — equation-driven modify: parse a predicate, attach it to a path, and rewrite matching elements | covered |  |
| integration::TestWorkflowLocateAcrossMutations | integration | positive | section Cross-View Invariants 5, 6 — locate a moving target across mutations and keep PathMatch agreement | covered |  |
| integration::TestWorkflowBracketPathRoundTripReport | integration | positive | section Cross-View Invariants 2, 4 — a report pipeline renders bracket paths for storage and re-reads them consistently | covered |  |
