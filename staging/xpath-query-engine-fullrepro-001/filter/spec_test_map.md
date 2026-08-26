# spec_test_map — xpath-query-engine-fullrepro-001

oracle_source: generated_only (Track B; see filter/rewrite_audit.md)
oracle_version: 2026-08-26T00:00:00Z
reference: github.com/antchfx/xpath v1.3.8 (commit d666d4b6f3b570811b144144414971401472b83c)
suites: oracle/atomic (132 tests), oracle/integration (28 tests)
nodeid format: {suite}::{TestName}

| test_nodeid | layer | assertion_kind | spec_section | status | notes |
|-------------|-------|----------------|--------------|--------|-------|
| atomic::TestCompileValidExpression | atomic | positive | section Expression Compilation and Reuse | covered | |
| atomic::TestStringReturnsExactSource | atomic | positive | section Expression Compilation and Reuse — source text round trip | covered | |
| atomic::TestMustCompileValidMatchesCompile | atomic | positive | section Expression Compilation and Reuse — MustCompile | covered | |
| atomic::TestMustCompileInvalidNoOp | atomic | positive | section Expression Compilation and Reuse — MustCompile no-op | covered | String equality is the value check |
| atomic::TestCompileWithNSStringRoundTrip | atomic | positive | section Expression Compilation and Reuse — namespace binding | covered | |
| atomic::TestCompileWithNSUnboundPrefix | atomic | failure_path | section Expression Compilation and Reuse — namespace binding + section Error Semantics | covered | exact message spec-declared |
| atomic::TestPackageLevelSelect | atomic | positive | section Expression Compilation and Reuse — package-level Select | covered | |
| atomic::TestPackageLevelSelectPanicsOnInvalid | atomic | failure_path | section Expression Compilation and Reuse — package-level Select + section Error Semantics | covered | positive guard included |
| atomic::TestExprReuseAcrossDocuments | atomic | positive | section Expression Compilation and Reuse — reuse and statelessness | covered | |
| atomic::TestSelectStartsIndependentTraversals | atomic | positive | section Expression Compilation and Reuse — reuse and statelessness | covered | |
| atomic::TestCompileEmptyExpressionRejected | atomic | failure_path | section Error Semantics (empty expression) | covered | exact message spec-declared |
| atomic::TestEvaluateNumericType | atomic | positive | section Selection, Evaluation, and Result Iteration — Evaluate | covered | |
| atomic::TestEvaluateBooleanType | atomic | positive | section Selection, Evaluation, and Result Iteration — Evaluate | covered | |
| atomic::TestEvaluateStringType | atomic | positive | section Selection, Evaluation, and Result Iteration — Evaluate | covered | |
| atomic::TestEvaluateNodeSetType | atomic | positive | section Selection, Evaluation, and Result Iteration — Evaluate | covered | |
| atomic::TestEvaluateEmptyNodeSetType | atomic | positive | section Selection, Evaluation, and Result Iteration — Evaluate | covered | non-empty guard included |
| atomic::TestSelectOnNonNodeSetYieldsNothing | atomic | positive | section Selection, Evaluation, and Result Iteration — Select | covered | non-empty guard included |
| atomic::TestIteratorCurrentBeforeMoveNext | atomic | positive | section Selection, Evaluation, and Result Iteration — iterator protocol | covered | |
| atomic::TestIteratorExhaustion | atomic | positive | section Selection, Evaluation, and Result Iteration — iterator protocol | covered | |
| atomic::TestSelectAdoptsNavigator | atomic | positive | section The Navigator Contract — cursor adoption | covered | |
| atomic::TestCurrentIdentityStableAcrossMatches | atomic | positive | section The Navigator Contract — cursor adoption | covered | |
| atomic::TestMoveToFailureFallsBackToCopy | atomic | positive | section The Navigator Contract — cursor adoption (Copy fallback) | covered | |
| atomic::TestCopyIsIndependentOfIteration | atomic | positive | section The Navigator Contract — interface methods (Copy) | covered | |
| atomic::TestNodeTypeConstantOrder | atomic | positive | section The Navigator Contract — node taxonomy | covered | |
| atomic::TestAbsolutePathFromRoot | atomic | positive | section Location Paths, Axes, and Node Tests | covered | |
| atomic::TestAbsolutePathIgnoresContextPosition | atomic | positive | section Location Paths, Axes, and Node Tests | covered | |
| atomic::TestRelativePathFromContext | atomic | positive | section Location Paths, Axes, and Node Tests | covered | |
| atomic::TestDescendantAbbreviation | atomic | positive | section Location Paths, Axes, and Node Tests | covered | |
| atomic::TestExplicitChildAndDescendantAxes | atomic | positive | section Location Paths, Axes, and Node Tests — supported axes | covered | |
| atomic::TestParentAxis | atomic | positive | section Location Paths, Axes, and Node Tests — supported axes | covered | |
| atomic::TestParentAxisReportsPerContext | atomic | positive | section Location Paths, Axes, and Node Tests — multiple context nodes and duplicates | covered | |
| atomic::TestAncestorAxisSharedAncestorsReportedOnce | atomic | positive | section Location Paths, Axes, and Node Tests — multiple context nodes and duplicates | covered | |
| atomic::TestAncestorOrSelf | atomic | positive | section Location Paths, Axes, and Node Tests — multiple context nodes and duplicates | covered | |
| atomic::TestAncestorNumericPredicatePerContext | atomic | positive | section Location Paths, Axes, and Node Tests — multiple context nodes and duplicates | covered | |
| atomic::TestDescendantChainKeepsDuplicates | atomic | positive | section Location Paths, Axes, and Node Tests — multiple context nodes and duplicates | covered | |
| atomic::TestSiblingAxes | atomic | positive | section Location Paths, Axes, and Node Tests — supported axes | covered | |
| atomic::TestFollowingAxis | atomic | positive | section Location Paths, Axes, and Node Tests — supported axes | covered | |
| atomic::TestPrecedingAxisExcludesAncestors | atomic | positive | section Location Paths, Axes, and Node Tests — supported axes | covered | |
| atomic::TestSelfAxis | atomic | positive | section Location Paths, Axes, and Node Tests — supported axes | covered | |
| atomic::TestDescendantOrSelfInner | atomic | positive | section Location Paths, Axes, and Node Tests — supported axes | covered | |
| atomic::TestAttributeAxis | atomic | positive | section Location Paths, Axes, and Node Tests — supported axes | covered | |
| atomic::TestAttributeParentIsOwningElement | atomic | positive | section Location Paths, Axes, and Node Tests — attribute parents | covered | |
| atomic::TestWildcardElementTest | atomic | positive | section Location Paths, Axes, and Node Tests — node tests | covered | |
| atomic::TestNodeTypeTests | atomic | positive | section Location Paths, Axes, and Node Tests — node tests | covered | |
| atomic::TestDoubleSlashBetweenSteps | atomic | positive | section Location Paths, Axes, and Node Tests | covered | |
| atomic::TestExpressionReuseAcrossNavigatorFlavors | atomic | positive | section Expression Compilation and Reuse — reuse and statelessness | covered | |
| atomic::TestUnprefixedTestRequiresEmptyPrefix | atomic | positive | section Namespace-Aware Matching — prefix-literal mode | covered | |
| atomic::TestPrefixLiteralMatch | atomic | positive | section Namespace-Aware Matching — prefix-literal mode | covered | |
| atomic::TestWildcardMatchesPrefixedElements | atomic | positive | section Namespace-Aware Matching — prefix-literal mode + node tests | covered | |
| atomic::TestCompileWithNSMatchesByURI | atomic | positive | section Namespace-Aware Matching — URI mode | covered | |
| atomic::TestCompileWithNSFallsBackWithoutExtension | atomic | positive | section Namespace-Aware Matching — URI mode fallback | covered | |
| atomic::TestNameQualifiedForm | atomic | positive | section Namespace-Aware Matching — name functions with prefixes | covered | |
| atomic::TestNamespaceURIWithExtension | atomic | positive | section Namespace-Aware Matching — the namespace-uri function | covered | |
| atomic::TestNamespaceURIFallbackReturnsPrefix | atomic | positive | section Namespace-Aware Matching — the namespace-uri function | covered | |
| atomic::TestNameFunctionsOnNonElements | atomic | positive | section Namespace-Aware Matching — name functions with prefixes | covered | |
| atomic::TestNumericPredicatePositions | atomic | positive | section Predicates and Position — numeric predicates | covered | |
| atomic::TestNumericPredicateTruncation | atomic | positive | section Predicates and Position — numeric predicates | covered | |
| atomic::TestNumericPredicateOutOfRange | atomic | positive | section Predicates and Position — numeric predicates | covered | positive guard included |
| atomic::TestPositionFunction | atomic | positive | section Predicates and Position — position() and last() | covered | |
| atomic::TestLastFunction | atomic | positive | section Predicates and Position — position() and last() | covered | |
| atomic::TestTopLevelPositionAndLast | atomic | positive | section Predicates and Position — position() and last() | covered | |
| atomic::TestReverseAxisPositionCountsOutward | atomic | positive | section Predicates and Position — numeric predicates (reverse axes) | covered | |
| atomic::TestStackedPredicates | atomic | positive | section Predicates and Position — stacked predicates | covered | |
| atomic::TestAttributeAxisPositions | atomic | positive | section Predicates and Position — attribute positions | covered | count guard included |
| atomic::TestParenthesizedNodeSetPositions | atomic | positive | section Predicates and Position — parenthesized node-sets | covered | |
| atomic::TestExistenceAndAttributePredicates | atomic | positive | section Predicates and Position — boolean and string predicates | covered | |
| atomic::TestContentComparisonPredicates | atomic | positive | section Predicates and Position — boolean and string predicates | covered | |
| atomic::TestNumericExpressionInsidePredicates | atomic | positive | section Predicates and Position — boolean and string predicates | covered | |
| atomic::TestConstantTruthPredicates | atomic | positive | section Predicates and Position — boolean and string predicates | covered | |
| atomic::TestArithmeticPrecedence | atomic | positive | section Operators and Type Coercion — arithmetic | covered | |
| atomic::TestUnaryMinus | atomic | positive | section Operators and Type Coercion — arithmetic | covered | |
| atomic::TestDivAndMod | atomic | positive | section Operators and Type Coercion — arithmetic | covered | |
| atomic::TestDivisionByZero | atomic | positive | section Operators and Type Coercion — arithmetic | covered | |
| atomic::TestArithmeticStringCoercion | atomic | positive | section Operators and Type Coercion — arithmetic | covered | |
| atomic::TestArithmeticNodeSetCoercion | atomic | positive | section Operators and Type Coercion — arithmetic | covered | |
| atomic::TestMultiplicationAfterCall | atomic | positive | section Operators and Type Coercion — arithmetic (`*` after a call) | covered | |
| atomic::TestEqualityStrings | atomic | positive | section Operators and Type Coercion — equality | covered | |
| atomic::TestEqualityStringNumber | atomic | positive | section Operators and Type Coercion — equality | covered | |
| atomic::TestRelationalNumeric | atomic | positive | section Operators and Type Coercion — relational | covered | |
| atomic::TestRelationalNaNAlwaysFalse | atomic | positive | section Operators and Type Coercion — relational | covered | positive guard included |
| atomic::TestNodeSetComparisonExistential | atomic | positive | section Operators and Type Coercion — equality + relational | covered | |
| atomic::TestNodeSetVsNodeSetComparison | atomic | positive | section Operators and Type Coercion — equality + relational | covered | |
| atomic::TestLogicalOperators | atomic | positive | section Operators and Type Coercion — logical | covered | |
| atomic::TestUnionConcatenationOrder | atomic | positive | section Operators and Type Coercion — union | covered | |
| atomic::TestUnionDeduplication | atomic | positive | section Operators and Type Coercion — union | covered | |
| atomic::TestUnionNonNodeSetOperands | atomic | positive | section Operators and Type Coercion — union | covered | positive guard included |
| atomic::TestUnionMixedNodeKinds | atomic | positive | section Operators and Type Coercion — union | covered | |
| atomic::TestUnionGroupedStep | atomic | positive | section Operators and Type Coercion — union + section Location Paths, Axes, and Node Tests | covered | |
| atomic::TestBooleanConversion | atomic | positive | section Operators and Type Coercion — boolean conversion | covered | |
| atomic::TestNumberConversion | atomic | positive | section Operators and Type Coercion — number conversion | covered | |
| atomic::TestStringConversionNumbers | atomic | positive | section Operators and Type Coercion — string conversion | covered | |
| atomic::TestStringConversionBooleansAndNodeSets | atomic | positive | section Operators and Type Coercion — string conversion | covered | |
| atomic::TestCountFunction | atomic | positive | section Function Library — node-set functions | covered | |
| atomic::TestSumNumericNodes | atomic | positive | section Function Library — node-set functions | covered | |
| atomic::TestSumSkipsNonNumericNodes | atomic | positive | section Function Library — node-set functions | covered | non-zero guard included |
| atomic::TestReverseFunction | atomic | positive | section Function Library — node-set functions | covered | |
| atomic::TestNameAndLocalName | atomic | positive | section Function Library — node-set functions | covered | |
| atomic::TestZeroArgContextFunctions | atomic | positive | section Function Library — string functions (zero-argument forms) | covered | |
| atomic::TestTrueFalseNot | atomic | positive | section Function Library — boolean functions | covered | |
| atomic::TestNotOnStringsAndNumbersIsFalse | atomic | positive | section Function Library — boolean functions | covered | negation guard included |
| atomic::TestFloorCeiling | atomic | positive | section Function Library — numeric functions | covered | |
| atomic::TestRoundHalfTowardPositiveInfinity | atomic | positive | section Function Library — numeric functions | covered | |
| atomic::TestConcatFunction | atomic | positive | section Function Library — string functions | covered | |
| atomic::TestAffixFunctions | atomic | positive | section Function Library — string functions | covered | |
| atomic::TestAffixEmptyString | atomic | positive | section Function Library — string functions | covered | |
| atomic::TestSubstringBasics | atomic | positive | section Function Library — string functions | covered | |
| atomic::TestSubstringRoundsBounds | atomic | positive | section Function Library — string functions | covered | |
| atomic::TestSubstringBoundaries | atomic | positive | section Function Library — string functions | covered | positive guard included |
| atomic::TestSubstringBeforeAfter | atomic | positive | section Function Library — string functions | covered | |
| atomic::TestStringLength | atomic | positive | section Function Library — string functions | covered | |
| atomic::TestNormalizeSpace | atomic | positive | section Function Library — string functions | covered | |
| atomic::TestTranslate | atomic | positive | section Function Library — string functions | covered | |
| atomic::TestLowerCase | atomic | positive | section Function Library — string functions | covered | |
| atomic::TestMatchesFunction | atomic | positive | section Function Library — string functions | covered | |
| atomic::TestReplaceFunction | atomic | positive | section Function Library — string functions | covered | |
| atomic::TestStringJoin | atomic | positive | section Function Library — string functions | covered | |
| atomic::TestStringOfElementIsDeepText | atomic | positive | section Function Library — string functions + section The Navigator Contract | covered | |
| atomic::TestStringAndNumberOfNodeSetUseFirstNode | atomic | positive | section Operators and Type Coercion — string/number conversion | covered | |
| atomic::TestMalformedExpressionError | atomic | failure_path | section Error Semantics (malformed expression) | covered | exact message spec-declared |
| atomic::TestUnknownFunctionError | atomic | failure_path | section Error Semantics (unknown function) | covered | exact message spec-declared |
| atomic::TestUnsupportedStandardFunctions | atomic | failure_path | section Error Semantics (unknown function) + section Non-Goals | covered | exact message spec-declared |
| atomic::TestUnknownAxisError | atomic | failure_path | section Error Semantics (unknown axis) | covered | exact message spec-declared |
| atomic::TestVariableReferenceError | atomic | failure_path | section Error Semantics (variable reference) | covered | exact message spec-declared |
| atomic::TestNamespaceAxisUnsupported | atomic | failure_path | section Error Semantics (namespace axis) + section Non-Goals | covered | exact message spec-declared |
| atomic::TestUnclosedStringLiteralError | atomic | failure_path | section Error Semantics (unclosed literal) | covered | exact message spec-declared |
| atomic::TestNodeSetFunctionArityErrors | atomic | failure_path | section Error Semantics (arity) | covered | exact messages spec-declared |
| atomic::TestNumericFunctionArityErrors | atomic | failure_path | section Error Semantics (arity) | covered | floor/round report ceiling per spec |
| atomic::TestStringFunctionArityErrors | atomic | failure_path | section Error Semantics (arity) | covered | exact messages spec-declared |
| atomic::TestAffixArityErrorsAreNonNil | atomic | failure_path | section Error Semantics (arity, message unspecified) | covered | error-only per spec; compile guard included |
| atomic::TestMatchesInvalidPatternCompileError | atomic | failure_path | section Error Semantics (invalid pattern in matches) | covered | error-only per spec; compile guard included |
| atomic::TestReplaceInvalidPatternPanicsOnEvaluate | atomic | failure_path | section Error Semantics (replace panic) | covered | |
| atomic::TestSumOverNonNumericStringPanics | atomic | failure_path | section Error Semantics (sum panic) | covered | message spec-declared |
| integration::TestStringRoundTripAcrossCompilers | integration | positive | section Cross-View Invariants (1) | covered | corpus sweep, node floor guard |
| integration::TestStringRoundTripOnNoOpExpressions | integration | positive | section Cross-View Invariants (1) | covered | valid guard included |
| integration::TestEvaluateSelectAgreement | integration | positive | section Cross-View Invariants (2) | covered | corpus sweep, node floor guard |
| integration::TestCountAgreesWithIteration | integration | positive | section Cross-View Invariants (2) | covered | non-empty floor guard |
| integration::TestBooleanAgreesWithNonEmptiness | integration | positive | section Cross-View Invariants (3) | covered | also checks not() agreement |
| integration::TestStringAgreesWithFirstValue | integration | positive | section Cross-View Invariants (3) | covered | non-empty floor guard |
| integration::TestReuseAcrossDocumentsAndNavigators | integration | positive | section Cross-View Invariants (4) | covered | |
| integration::TestReuseInterleavedSelectEvaluate | integration | positive | section Cross-View Invariants (4) | covered | |
| integration::TestAdoptionIdentityAcrossCorpus | integration | positive | section Cross-View Invariants (5) | covered | match floor guard |
| integration::TestAdoptionCopyFallbackAgreement | integration | positive | section Cross-View Invariants (5) | covered | |
| integration::TestUnionSelfIdentity | integration | positive | section Cross-View Invariants (6) | covered | non-empty floor guard |
| integration::TestUnionSupersetAbsorbsSubset | integration | positive | section Cross-View Invariants (6) | covered | |
| integration::TestStringJoinReverseAgreement | integration | positive | section Cross-View Invariants (7) | covered | |
| integration::TestReverseTwiceRestoresOrder | integration | positive | section Cross-View Invariants (7) | covered | |
| integration::TestNameAgreementAcrossNodes | integration | positive | section Cross-View Invariants (8) | covered | |
| integration::TestNameAgreementUnderCompileWithNS | integration | positive | section Cross-View Invariants (8) | covered | |
| integration::TestSumAgreesWithPerNodeNumbers | integration | positive | section Function Library + section Cross-View Invariants (2) | covered | |
| integration::TestAverageViaDivAgreesWithParts | integration | positive | section Operators and Type Coercion + section Function Library | covered | |
| integration::TestPositionalSelectionAgreesWithIteration | integration | positive | section Predicates and Position + section Cross-View Invariants (3) | covered | |
| integration::TestPredicateAgreesWithPerNodeEvaluation | integration | positive | section Predicates and Position + section Operators and Type Coercion | covered | |
| integration::TestUnionAgreesWithConcatenationDedup | integration | positive | section Operators and Type Coercion — union + section Cross-View Invariants (6) | covered | |
| integration::TestCountStringLengthComposition | integration | positive | section Function Library — string functions | covered | |
| integration::TestWorkflowFilterAndExtract | integration | positive | section Representative Workflows + section Cross-View Invariants (2,3) | covered | |
| integration::TestWorkflowNamespaceDualNavigators | integration | positive | section Representative Workflows + section Namespace-Aware Matching | covered | |
| integration::TestWorkflowRelativeExploration | integration | positive | section Representative Workflows + section Location Paths, Axes, and Node Tests | covered | |
| integration::TestWorkflowAggregateReport | integration | positive | section Representative Workflows + section Function Library | covered | |
| integration::TestWorkflowErrorRecovery | integration | positive | section Representative Workflows + section Error Semantics | covered | value checks on String and recovery query |
| integration::TestWorkflowDocumentEvolution | integration | positive | section Representative Workflows + section Cross-View Invariants (4) | covered | |

Total: 160 | kept (covered): 160 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 160

Layer counts: atomic 132 (positive 115, failure_path 17; positive share 87.1%),
integration 28 (positive 28). no_check: 0 in both layers.
Per-section minimums: all 8 behavior sections >= 4; Error Semantics 14 >= 4;
each of the 8 CVIs has >= 2 integration tests; Representative Workflows 6 >= 4.
