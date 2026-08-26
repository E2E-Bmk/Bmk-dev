# spec_test_map — gocmp-equality-engine-fullrepro-001

oracle_source: generated_only (Track B; see rewrite_audit.md)
oracle_version: 2026-08-25T01
node id format: {suite}::{TestFunc} (Go base test functions; suites atomic/, integration/)
source: generated (all rows; upstream suite not liftable)

| test_nodeid | layer | assertion_kind | spec_section | status | notes |
|-------------|-------|----------------|--------------|--------|------|
| atomic::TestBoolEquality | atomic | positive | section Equality Judgement | covered |  |
| atomic::TestIntegerEquality | atomic | positive | section Equality Judgement | covered |  |
| atomic::TestFloatEquality | atomic | positive | section Equality Judgement | covered |  |
| atomic::TestNaNNeverEqualsNaN | atomic | positive | section Equality Judgement | covered |  |
| atomic::TestComplexEquality | atomic | positive | section Equality Judgement | covered |  |
| atomic::TestStringEquality | atomic | positive | section Equality Judgement | covered |  |
| atomic::TestChannelEquality | atomic | positive | section Equality Judgement | covered |  |
| atomic::TestFunctionEquality | atomic | positive | section Equality Judgement | covered |  |
| atomic::TestStructFieldwiseEquality | atomic | positive | section Equality Judgement | covered |  |
| atomic::TestNilSliceNotEqualEmptySlice | atomic | positive | section Equality Judgement | covered |  |
| atomic::TestSliceElementwiseEquality | atomic | positive | section Equality Judgement | covered |  |
| atomic::TestNilMapNotEqualEmptyMap | atomic | positive | section Equality Judgement | covered |  |
| atomic::TestMapKeyAndValueEquality | atomic | positive | section Equality Judgement | covered |  |
| atomic::TestPointerEquality | atomic | positive | section Equality Judgement | covered |  |
| atomic::TestInterfaceConcreteTypeRules | atomic | positive | section Equality Judgement | covered |  |
| atomic::TestTopLevelTypeMismatchIsNotPanic | atomic | failure_path | section Equality Judgement + section Error Semantics | covered | negative predicate; positive twins in kinds family |
| atomic::TestUntypedNilRootsEqual | atomic | positive | section Equality Judgement | covered |  |
| atomic::TestEqualMethodDecidesVerdict | atomic | positive | section Equality Judgement | covered |  |
| atomic::TestEqualMethodOnNilPointerReceiver | atomic | positive | section Equality Judgement | covered |  |
| atomic::TestEqualMethodInterfaceForm | atomic | positive | section Equality Judgement | covered |  |
| atomic::TestComparerOverridesEqualMethod | atomic | positive | section Equality Judgement | covered |  |
| atomic::TestIgnoreOverridesEqualMethod | atomic | positive | section Equality Judgement | covered |  |
| atomic::TestComparerDecidesLeaf | atomic | positive | section Options and Filters | covered |  |
| atomic::TestUnfilteredIgnorePanics | atomic | failure_path | section Error Semantics | covered |  |
| atomic::TestAmbiguousOptionsPanic | atomic | failure_path | section Error Semantics | covered |  |
| atomic::TestInvalidComparerPanics | atomic | failure_path | section Error Semantics | covered |  |
| atomic::TestTransformerRewritesValues | atomic | positive | section Options and Filters | covered |  |
| atomic::TestTransformerInvalidNamePanics | atomic | failure_path | section Error Semantics | covered |  |
| atomic::TestTransformerEmptyNameAllowed | atomic | positive | section Options and Filters | covered |  |
| atomic::TestTransformerRecursionGuardTerminates | atomic | positive | section Options and Filters | covered |  |
| atomic::TestFilterPathScopesOption | atomic | positive | section Options and Filters | covered |  |
| atomic::TestFilterValuesScopesOption | atomic | positive | section Options and Filters | covered |  |
| atomic::TestFilterValuesSkipsOneSidedElements | atomic | positive | section Options and Filters | covered |  |
| atomic::TestFilterPathSeesOneSidedElements | atomic | positive | section Options and Filters | covered |  |
| atomic::TestOptionsListActsAsOneOption | atomic | positive | section Options and Filters | covered |  |
| atomic::TestFilteredOptionsListAppliesToElements | atomic | positive | section Options and Filters | covered |  |
| atomic::TestExporterAdmitsUnexportedFields | atomic | positive | section Options and Filters | covered |  |
| atomic::TestAllowUnexportedAdmitsListedTypes | atomic | positive | section Options and Filters | covered |  |
| atomic::TestUnexportedFieldPanicsWithoutPermission | atomic | failure_path | section Error Semantics | covered |  |
| atomic::TestIgnoredUnexportedFieldDoesNotPanic | atomic | positive | section Options and Filters | covered |  |
| atomic::TestDiffEmptyOnEqualInputs | atomic | positive | section Difference Reporting | covered |  |
| atomic::TestDiffPrefixesMarkSides | atomic | positive | section Difference Reporting | covered |  |
| atomic::TestDiffTypeMismatchNonEmpty | atomic | positive | section Difference Reporting | covered |  |
| atomic::TestDiffMentionsTransformerName | atomic | positive | section Difference Reporting | covered |  |
| atomic::TestDiffEmptyIffEqualUnderComparer | atomic | positive | section Difference Reporting | covered |  |
| atomic::TestPathStringSimplified | atomic | positive | section Traversal Reporting | covered |  |
| atomic::TestPathGoStringFull | atomic | positive | section Traversal Reporting | covered |  |
| atomic::TestPathIndexAndLast | atomic | positive | section Traversal Reporting | covered |  |
| atomic::TestStructFieldAccessors | atomic | positive | section Traversal Reporting | covered |  |
| atomic::TestSliceIndexKeyAndSplitKeys | atomic | positive | section Traversal Reporting | covered |  |
| atomic::TestMapIndexKeyAccessor | atomic | positive | section Traversal Reporting | covered |  |
| atomic::TestIndirectStepObserved | atomic | positive | section Traversal Reporting | covered |  |
| atomic::TestTypeAssertionStepObserved | atomic | positive | section Traversal Reporting | covered |  |
| atomic::TestTransformStepAccessors | atomic | positive | section Traversal Reporting | covered |  |
| integration::TestReporterPushPopBalance | integration | positive | section Traversal Reporting + section Cross-View Invariants | covered |  |
| integration::TestReporterFirstPushCarriesRoot | integration | positive | section Traversal Reporting + section Cross-View Invariants | covered |  |
| integration::TestReporterReportsOncePerLeaf | integration | positive | section Traversal Reporting | covered |  |
| integration::TestVerdictIsConjunctionOfLeafVerdicts | integration | positive | section State Model + section Cross-View Invariants | covered |  |
| integration::TestReporterObservesMapAndSliceSteps | integration | positive | section Traversal Reporting | covered |  |
| integration::TestReporterPathRenderingsConsistent | integration | positive | section Traversal Reporting | covered |  |
| integration::TestTransformStepObservedInTraversal | integration | positive | section Traversal Reporting | covered |  |
| integration::TestPointerAndInterfaceStepsObserved | integration | positive | section Traversal Reporting | covered |  |
| integration::TestEmbeddedStructEnteredAsOwnStep | integration | positive | section Traversal Reporting | covered |  |
| integration::TestDiffEmptinessMatchesEqualUnderOptions | integration | positive | section Cross-View Invariants + section Difference Reporting | covered |  |
| integration::TestIgnoreFlipsVerdictExactlyWhenValuesDiffer | integration | positive | section Cross-View Invariants | covered |  |
| integration::TestFilterScopingProjectionIndependent | integration | positive | section Cross-View Invariants + section Options and Filters | covered |  |
| integration::TestFilterValuesScopingAcrossProjections | integration | positive | section Cross-View Invariants + section Options and Filters | covered |  |
| integration::TestAmbiguityResolvedByDisjointFilters | integration | positive | section Options and Filters + section Error Semantics | covered |  |
| integration::TestStructuralRunKeepsCauseFlagsClean | integration | positive | section Cross-View Invariants + section Traversal Reporting | covered |  |
| integration::TestResultByFuncOnComparerLeaf | integration | positive | section Traversal Reporting | covered |  |
| integration::TestResultByMethodOnMethodLeaf | integration | positive | section Traversal Reporting | covered |  |
| integration::TestResultByIgnoreImpliesEqual | integration | positive | section Traversal Reporting + section Cross-View Invariants | covered |  |
| integration::TestEqualCyclesJudgedEqualByCycle | integration | positive | section Equality Judgement + section Cross-View Invariants | covered |  |
| integration::TestUnequalCyclicPayloadTerminates | integration | failure_path | section Equality Judgement + section Cross-View Invariants | covered | negative predicate; twin TestEqualCyclesJudgedEqualByCycle |
| integration::TestDifferentCycleLengthsUnequal | integration | failure_path | section Equality Judgement + section Cross-View Invariants | covered | negative predicate; twin TestDoublyLinkedCycleComparison |
| integration::TestDoublyLinkedCycleComparison | integration | positive | section Equality Judgement + section Cross-View Invariants | covered |  |
| integration::TestApproximateComparisonWorkflow | integration | positive | section Representative Workflows | covered |  |
| integration::TestPathCollectorWorkflow | integration | positive | section Representative Workflows + section Traversal Reporting | covered |  |
| integration::TestMultiOptionComposition | integration | positive | section Representative Workflows + section Options and Filters | covered |  |
| integration::TestOptionsListNestingAndFiltering | integration | positive | section Options and Filters | covered |  |
| integration::TestExporterScopedWorkflow | integration | positive | section Options and Filters + section Error Semantics | covered |  |
| integration::TestIgnoreAdditionsScopedToSlices | integration | positive | section Options and Filters | covered |  |
| integration::TestMapEntryOneSidedIgnore | integration | positive | section Options and Filters | covered |  |
| integration::TestEqualMethodWithinLargerStructure | integration | positive | section Equality Judgement + section Cross-View Invariants | covered |  |
| integration::TestTransformerOnNestedField | integration | positive | section Options and Filters | covered |  |
| integration::TestReporterAgreesWithDiffOnUnequalLeaves | integration | positive | section Representative Workflows + section State Model | covered |  |
| integration::TestMismatchedTypesDeepWorkflow | integration | positive | section State Model | covered |  |

Total: 87 | kept (covered): 87 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 87

Layer counts: atomic 54 | integration 33 | system_e2e 0
Assertion-kind counts: atomic positive 48, failure_path 6; integration positive 31, failure_path 2; no_check 0
