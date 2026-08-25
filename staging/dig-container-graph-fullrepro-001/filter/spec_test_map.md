# spec_test_map — dig-container-graph-fullrepro-001

oracle_source: generated_only (Track B; see rewrite_audit.md)
oracle_version: 2026-08-25T20:00Z
Test IDs are `suite::TestFunc` per harness/runners/go.py (suites: atomic, integration).
All rows source=generated. Spec headings referenced: Containers and Scopes;
Providing Constructors; Parameter and Result Objects; Invocation and Resolution;
Decorators; Graph Introspection; State Model; Error Semantics;
Cross-View Invariants; Representative Workflows.

| test_nodeid | layer | assertion_kind | spec_section | status | source |
|-------------|-------|----------------|--------------|--------|--------|
| atomic::TestProvideRejectsNonFunction | atomic | failure_path | Error Semantics | covered | generated |
| atomic::TestProvideRequiresNonErrorResult | atomic | failure_path | Providing Constructors + Error Semantics | covered | generated |
| atomic::TestProvideDoesNotCallConstructor | atomic | positive | Providing Constructors | covered | generated |
| atomic::TestConstructorRunsAtMostOnce | atomic | positive | Providing Constructors + State Model | covered | generated |
| atomic::TestFailedConstructorIsNotMemoized | atomic | positive | Providing Constructors + State Model | covered | generated |
| atomic::TestDuplicateProvideRejectedAndRolledBack | atomic | positive | Providing Constructors | covered | generated |
| atomic::TestNamedProvidesDoNotConflict | atomic | positive | Providing Constructors | covered | generated |
| atomic::TestDuplicateNamedProvideRejected | atomic | positive | Providing Constructors | covered | generated |
| atomic::TestNamedAndUnnamedKeysAreDistinct | atomic | positive | Providing Constructors + State Model | covered | generated |
| atomic::TestVariadicConstructorArgsIgnored | atomic | positive | Providing Constructors | covered | generated |
| atomic::TestMultipleResultsAllRegistered | atomic | positive | Providing Constructors | covered | generated |
| atomic::TestTrailingNilErrorMeansSuccess | atomic | positive | Providing Constructors | covered | generated |
| atomic::TestProvideCycleRejectedByDefault | atomic | positive | Providing Constructors + Error Semantics | covered | generated |
| atomic::TestIsCycleDetectedFalseForOtherErrors | atomic | failure_path | Error Semantics | covered | generated |
| atomic::TestGroupOptionCollectsValues | atomic | positive | Providing Constructors | covered | generated |
| atomic::TestFlattenOptionSpreadsSliceElements | atomic | positive | Providing Constructors | covered | generated |
| atomic::TestFlattenRequiresSlice | atomic | failure_path | Providing Constructors + Error Semantics | covered | generated |
| atomic::TestNameAndGroupOptionsConflict | atomic | failure_path | Providing Constructors + Error Semantics | covered | generated |
| atomic::TestAsRegistersInterfaceOnly | atomic | positive | Providing Constructors | covered | generated |
| atomic::TestAsRejectsNonInterfacePointer | atomic | failure_path | Providing Constructors + Error Semantics | covered | generated |
| atomic::TestAsRejectsUnimplementedInterface | atomic | failure_path | Providing Constructors + Error Semantics | covered | generated |
| atomic::TestAsWithNameRegistersNamedInterface | atomic | positive | Providing Constructors | covered | generated |
| atomic::TestIsInAndIsOutClassifyStructs | atomic | positive | Parameter and Result Objects | covered | generated |
| atomic::TestNestedEmbeddingQualifiesAsParameterObject | atomic | positive | Parameter and Result Objects | covered | generated |
| atomic::TestParameterObjectFieldsBecomeDependencies | atomic | positive | Parameter and Result Objects | covered | generated |
| atomic::TestResultObjectFieldsBecomeValues | atomic | positive | Parameter and Result Objects | covered | generated |
| atomic::TestOutFieldNameTagRegistersNamedValue | atomic | positive | Parameter and Result Objects | covered | generated |
| atomic::TestOutFieldGroupTagSendsValue | atomic | positive | Parameter and Result Objects | covered | generated |
| atomic::TestOutFieldFlattenTagSpreadsSlice | atomic | positive | Parameter and Result Objects | covered | generated |
| atomic::TestOutFieldFlattenRequiresSlice | atomic | failure_path | Parameter and Result Objects + Error Semantics | covered | generated |
| atomic::TestUnexportedInFieldRejected | atomic | failure_path | Parameter and Result Objects + Error Semantics | covered | generated |
| atomic::TestUnexportedOutFieldRejected | atomic | failure_path | Parameter and Result Objects + Error Semantics | covered | generated |
| atomic::TestPointerToParameterObjectRejected | atomic | positive | Parameter and Result Objects + Error Semantics | covered | generated |
| atomic::TestResultObjectAsParameterRejected | atomic | failure_path | Parameter and Result Objects + Error Semantics | covered | generated |
| atomic::TestParameterObjectAsResultRejected | atomic | failure_path | Parameter and Result Objects + Error Semantics | covered | generated |
| atomic::TestNameOptionRejectedForResultObjects | atomic | failure_path | Parameter and Result Objects + Error Semantics | covered | generated |
| atomic::TestGroupOptionRejectedForResultObjects | atomic | failure_path | Parameter and Result Objects + Error Semantics | covered | generated |
| atomic::TestOptionalMissingYieldsZeroValue | atomic | positive | Parameter and Result Objects | covered | generated |
| atomic::TestOptionalPresentUsesRegisteredValue | atomic | positive | Parameter and Result Objects | covered | generated |
| atomic::TestOptionalDoesNotTolerateConstructorFailure | atomic | failure_path | Parameter and Result Objects + Error Semantics | covered | generated |
| atomic::TestNamedTagWithOptionalMissing | atomic | positive | Parameter and Result Objects | covered | generated |
| atomic::TestGroupTagMustBeSlice | atomic | failure_path | Parameter and Result Objects + Error Semantics | covered | generated |
| atomic::TestNameAndGroupTagsConflict | atomic | failure_path | Parameter and Result Objects + Error Semantics | covered | generated |
| atomic::TestOptionalGroupTagRejected | atomic | failure_path | Parameter and Result Objects + Error Semantics | covered | generated |
| atomic::TestEmptyGroupYieldsEmptySlice | atomic | positive | Parameter and Result Objects | covered | generated |
| atomic::TestPlainStructIsOrdinaryDependency | atomic | positive | Parameter and Result Objects | covered | generated |
| atomic::TestInvokeZeroArgFunctionRuns | atomic | positive | Invocation and Resolution | covered | generated |
| atomic::TestInvokeRejectsNonFunction | atomic | failure_path | Invocation and Resolution + Error Semantics | covered | generated |
| atomic::TestMissingTypeErrorRendersKey | atomic | failure_path | Invocation and Resolution + Error Semantics | covered | generated |
| atomic::TestMissingNamedKeyRendersNameAnnotation | atomic | failure_path | Invocation and Resolution + Error Semantics | covered | generated |
| atomic::TestInvokedFunctionErrorReturnedUnchanged | atomic | positive | Invocation and Resolution | covered | generated |
| atomic::TestInvokeExtraResultsIgnored | atomic | positive | Invocation and Resolution | covered | generated |
| atomic::TestUserConstructorErrorReachableViaRootCause | atomic | positive | Invocation and Resolution + Error Semantics | covered | generated |
| atomic::TestContainerErrorsImplementDigError | atomic | shape | Invocation and Resolution + Error Semantics | covered | generated |
| atomic::TestRootCauseOfContainerOnlyChainIsDigError | atomic | positive | Invocation and Resolution | covered | generated |
| atomic::TestRecoverFromPanicsReturnsPanicError | atomic | positive | Invocation and Resolution + Error Semantics | covered | generated |
| atomic::TestPanicErrorIsNotADigError | atomic | positive | Invocation and Resolution + Error Semantics | covered | generated |
| atomic::TestPanicPropagatesWithoutRecoverOption | atomic | failure_path | Invocation and Resolution + Error Semantics | covered | generated |
| atomic::TestInvokePanicRecoveredToo | atomic | positive | Invocation and Resolution + Error Semantics | covered | generated |
| atomic::TestStringListsNodesAndValues | atomic | positive | Containers and Scopes | covered | generated |
| atomic::TestVisualizeEmitsDotDigraph | atomic | positive | Graph Introspection | covered | generated |
| atomic::TestInvokeDemandsOnlyRequestedSubgraph | atomic | positive | Invocation and Resolution | covered | generated |
| integration::TestChildScopeSeesParentRegistrations | integration | positive | Containers and Scopes | covered | generated |
| integration::TestParentCannotSeeChildRegistrations | integration | failure_path | Containers and Scopes | covered | generated |
| integration::TestSiblingScopesAreIsolated | integration | failure_path | Containers and Scopes | covered | generated |
| integration::TestExportedRegistrationVisibleEverywhere | integration | positive | Containers and Scopes + Cross-View Invariants | covered | generated |
| integration::TestExportFalseKeepsScopePrivacy | integration | positive | Containers and Scopes | covered | generated |
| integration::TestLateRegistrationVisibleToExistingChild | integration | positive | Containers and Scopes | covered | generated |
| integration::TestSharedRegistrationMemoizesAcrossScopes | integration | positive | Containers and Scopes + Cross-View Invariants | covered | generated |
| integration::TestSiblingPrivateRegistrationsIndependent | integration | positive | Containers and Scopes + State Model | covered | generated |
| integration::TestGrandchildSeesWholeAncestorChain | integration | positive | Containers and Scopes | covered | generated |
| integration::TestProvideOrderIrrelevantForResolution | integration | positive | Providing Constructors + Invocation and Resolution | covered | generated |
| integration::TestDiamondDependencyBuiltOnce | integration | positive | Invocation and Resolution + Cross-View Invariants | covered | generated |
| integration::TestDeferredCycleFailsEveryInvoke | integration | failure_path | Providing Constructors + Cross-View Invariants | covered | generated |
| integration::TestDefaultCycleRejectionLeavesGraphUsable | integration | positive | Providing Constructors + Cross-View Invariants | covered | generated |
| integration::TestConstructorFailureChainsToInvoke | integration | positive | Invocation and Resolution + Error Semantics | covered | generated |
| integration::TestTransitiveMissingDependencyReported | integration | failure_path | Invocation and Resolution + Error Semantics | covered | generated |
| integration::TestSuccessfulDependencyMemoizedDespiteDownstreamFailure | integration | positive | State Model + Providing Constructors | covered | generated |
| integration::TestGroupVisibilityFollowsScopes | integration | positive | Containers and Scopes + Parameter and Result Objects | covered | generated |
| integration::TestGroupValuesMemoizedAcrossDemands | integration | positive | State Model + Cross-View Invariants | covered | generated |
| integration::TestFlattenAndScalarProvidersMerge | integration | positive | Parameter and Result Objects + Cross-View Invariants | covered | generated |
| integration::TestSoftGroupOnlyReflectsAlreadyBuiltValues | integration | positive | Parameter and Result Objects + Cross-View Invariants | covered | generated |
| integration::TestHardGroupDemandRunsAllProviders | integration | positive | Parameter and Result Objects | covered | generated |
| integration::TestGroupProviderFailureFailsWholeDemand | integration | failure_path | Invocation and Resolution + Error Semantics | covered | generated |
| integration::TestExportedGroupProviderJoinsGroupEverywhere | integration | positive | Containers and Scopes + Parameter and Result Objects | covered | generated |
| integration::TestDecoratorReplacesValueInScope | integration | positive | Decorators | covered | generated |
| integration::TestChildDecorationInvisibleToParent | integration | positive | Decorators + Cross-View Invariants | covered | generated |
| integration::TestDecoratorReceivesUndecoratedValue | integration | positive | Decorators | covered | generated |
| integration::TestDecoratorSeesSameBaseInstanceAsAncestor | integration | positive | Decorators + State Model | covered | generated |
| integration::TestDecoratorRunsAtMostOncePerScope | integration | positive | Decorators | covered | generated |
| integration::TestSecondDecorationSameScopeRejected | integration | positive | Decorators + Error Semantics | covered | generated |
| integration::TestDecoratorDependencyFailureSurfacesAtInvoke | integration | failure_path | Decorators + Error Semantics | covered | generated |
| integration::TestGroupDecorationReplacesContent | integration | positive | Decorators | covered | generated |
| integration::TestValuesAppearInStringOnlyAfterBuild | integration | positive | Containers and Scopes + Cross-View Invariants | covered | generated |
| integration::TestVisualizeMentionsEveryProducedType | integration | positive | Graph Introspection + Cross-View Invariants | covered | generated |
| integration::TestVisualizeErrorOptionKeepsValidDot | integration | positive | Graph Introspection | covered | generated |
| integration::TestErrorRenderingConsistentAcrossStages | integration | failure_path | Cross-View Invariants + Error Semantics | covered | generated |
| integration::TestErrorClassificationSeparatesUserAndContainerErrors | integration | positive | Cross-View Invariants + Error Semantics | covered | generated |
| integration::TestApplicationAssemblyWorkflow | integration | positive | Representative Workflows | covered | generated |

Total: 99 | kept (covered): 99 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 99

Layer counts: atomic 62, integration 37 (floors: atomic >= 30 OK, integration >= 25 OK).
Atomic assertion kinds: positive 39, failure_path 22, shape 1, no_check 0 —
positive share 39/62 = 62.9% (>= 60% gate OK).
Integration assertion kinds: positive 30, failure_path 7, no_check 0.
Per-section minimums: every behavior section >= 4 rows; Error Semantics 30 rows;
Cross-View Invariants 13 rows (each CVI covered by >= 1 integration row, CVIs
1/2/3/5/6/7 by >= 2); Representative Workflows covered by the assembly workflow
plus TestProvideOrderIrrelevantForResolution and the memoization family.
