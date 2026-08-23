# Spec-test map — expr spec v1

Oracle version: 2026-08-21T00:00:00+08:00
Oracle source: generated_only

| test_nodeid | source | layer | assertion_kind | spec_section | status | notes |
|---|---|---|---|---|---|---|
| `atomic::TestLiterals` | generated | atomic | positive | Literals and Core Operators | covered | Verifies EXPR-001 |
| `atomic::TestArithmeticPrecedence` | generated | atomic | positive | Literals and Core Operators | covered | Verifies EXPR-002 |
| `atomic::TestStringConcatenation` | generated | atomic | positive | Literals and Core Operators | covered | Verifies EXPR-003 |
| `atomic::TestUnaryAndComparisons` | generated | atomic | positive | Literals and Core Operators | covered | Verifies EXPR-004, EXPR-005 |
| `atomic::TestMembershipAndCoalescing` | generated | atomic | positive | Literals and Core Operators | covered | Verifies EXPR-007, EXPR-008 |
| `atomic::TestOptionalMember` | generated | atomic | positive | Literals and Core Operators | covered | Verifies EXPR-009 |
| `atomic::TestIndexSliceAndRange` | generated | atomic | positive | Literals and Core Operators | covered | Verifies EXPR-010 |
| `atomic::TestLetAndSequence` | generated | atomic | positive | Variables, Environments, and Calls | covered | Verifies EXPR-018 |
| `atomic::TestMapEnvironment` | generated | atomic | positive | Variables, Environments, and Calls | covered | Verifies EXPR-011 |
| `atomic::TestStructAndTaggedEnvironment` | generated | atomic | positive | Variables, Environments, and Calls | covered | Verifies EXPR-012, EXPR-013 |
| `atomic::TestStructMethod` | generated | atomic | positive | Variables, Environments, and Calls | covered | Verifies EXPR-014 |
| `atomic::TestUnknownVariableRejected` | generated | atomic | failure_path | Variables, Environments, and Calls | covered | Verifies EXPR-015 |
| `atomic::TestAllowUndefinedVariable` | generated | atomic | failure_path | Variables, Environments, and Calls | covered | Verifies EXPR-016 |
| `atomic::TestDynamicMapMissingMember` | generated | atomic | failure_path | Variables, Environments, and Calls | covered | Verifies EXPR-017 |
| `atomic::TestQuantifiers` | generated | atomic | positive | Predicate and Collection Operations | covered | Verifies EXPR-021 |
| `atomic::TestPredicateIndex` | generated | atomic | positive | Predicate and Collection Operations | covered | Verifies EXPR-022 |
| `atomic::TestFilterAndMap` | generated | atomic | positive | Predicate and Collection Operations | covered | Verifies EXPR-023, EXPR-024 |
| `atomic::TestCountAndFind` | generated | atomic | positive | Predicate and Collection Operations | covered | Verifies EXPR-025, EXPR-026 |
| `atomic::TestGroupBy` | generated | atomic | positive | Predicate and Collection Operations | covered | Verifies EXPR-027 |
| `atomic::TestConcatFlattenUniq` | generated | atomic | positive | Predicate and Collection Operations | covered | Verifies EXPR-028 |
| `atomic::TestJoinAndReduce` | generated | atomic | positive | Predicate and Collection Operations | covered | Verifies EXPR-029, EXPR-030 |
| `atomic::TestAggregates` | generated | atomic | positive | Predicate and Collection Operations | covered | Verifies EXPR-031 |
| `atomic::TestOrderingBuiltins` | generated | atomic | positive | Predicate and Collection Operations | covered | Verifies EXPR-032, EXPR-033 |
| `atomic::TestMapKeysAndValues` | generated | atomic | positive | Predicate and Collection Operations | covered | Verifies EXPR-034 |
| `atomic::TestTrimAndCase` | generated | atomic | positive | Deterministic Builtins | covered | Verifies EXPR-035 |
| `atomic::TestOtherStringBuiltins` | generated | atomic | positive | Deterministic Builtins | covered | Verifies EXPR-036 |
| `atomic::TestLenAndGet` | generated | atomic | positive | Deterministic Builtins | covered | Verifies EXPR-037, EXPR-038 |
| `atomic::TestNumericBuiltins` | generated | atomic | positive | Deterministic Builtins | covered | Verifies EXPR-039 |
| `atomic::TestConversions` | generated | atomic | positive | Deterministic Builtins | covered | Verifies EXPR-040 |
| `atomic::TestBase64RoundTrip` | generated | atomic | positive | Deterministic Builtins | covered | Verifies EXPR-041 |
| `atomic::TestPairsRoundTrip` | generated | atomic | positive | Deterministic Builtins | covered | Verifies EXPR-042 |
| `atomic::TestBitwiseBuiltins` | generated | atomic | positive | Deterministic Builtins | covered | Verifies EXPR-043 |
| `atomic::TestReturnKindOptions` | generated | atomic | positive | Compilation and Execution Options | covered | Verifies EXPR-044, EXPR-045, EXPR-071 |
| `atomic::TestNodeBudget` | generated | atomic | failure_path | Compilation and Execution Options | covered | Verifies EXPR-051 |
| `atomic::TestBuiltinControls` | generated | atomic | failure_path | Compilation and Execution Options | covered | Verifies EXPR-056 |
| `atomic::TestCompileErrorsReturnNilProgram` | generated | atomic | failure_path | Error Semantics | covered | Verifies EXPR-066, EXPR-075 |
| `integration::TestCompileOnceRunMany` | generated | system_e2e | positive | Representative Workflows | covered | Verifies EXPR-070 |
| `integration::TestEvalCompileRunAgreement` | generated | system_e2e | positive | Cross-View Invariants | covered | Verifies EXPR-069 |
| `integration::TestOptimizationParity` | generated | integration | positive | Cross-View Invariants | covered | Verifies EXPR-049 |
| `integration::TestConcurrentProgramRuns` | generated | system_e2e | positive | Concurrency and Isolation | covered | Verifies EXPR-072 |
| `integration::TestDefaultShortCircuit` | generated | integration | positive | Literals and Core Operators | covered | Verifies EXPR-006 |
| `integration::TestDisabledShortCircuit` | generated | integration | positive | Compilation and Execution Options | covered | Verifies EXPR-050 |
| `integration::TestRegisteredFunction` | generated | integration | positive | Compilation and Execution Options | covered | Verifies EXPR-052 |
| `integration::TestRegisteredFunctionTypeCheck` | generated | integration | failure_path | Compilation and Execution Options | covered | Verifies EXPR-052 |
| `integration::TestFunctionErrorThenSuccessfulRun` | generated | system_e2e | failure_path | Error Semantics | covered | Verifies EXPR-053, EXPR-067 |
| `integration::TestOperatorOverloadComposes` | generated | system_e2e | positive | Compilation and Execution Options | covered | Verifies EXPR-054 |
| `integration::TestConstExpressionRunsAtCompileTime` | generated | system_e2e | positive | Compilation and Execution Options | covered | Verifies EXPR-055 |
| `integration::TestConstExpressionLeavesVariableCallsRuntime` | generated | system_e2e | positive | Compilation and Execution Options | covered | Verifies EXPR-055 |
| `integration::TestContextInjection` | generated | system_e2e | positive | Compilation and Execution Options | covered | Verifies EXPR-057 |
| `integration::TestTimezoneAffectsDate` | generated | integration | positive | Compilation and Execution Options | covered | Verifies EXPR-058 |
| `integration::TestProgramSourceProjection` | generated | integration | positive | Program Projections | covered | Verifies EXPR-064 |
| `integration::TestASTWalkPostOrder` | generated | integration | positive | AST Visitors and Patching | covered | Verifies EXPR-059 |
| `integration::TestASTWalkNil` | generated | integration | positive | AST Visitors and Patching | covered | Verifies EXPR-059 |
| `integration::TestASTFind` | generated | integration | positive | AST Visitors and Patching | covered | Verifies EXPR-060 |
| `integration::TestASTPatchReplacesNode` | generated | integration | positive | AST Visitors and Patching | covered | Verifies EXPR-061 |
| `integration::TestCompilePatchChangesResult` | generated | system_e2e | positive | AST Visitors and Patching | covered | Verifies EXPR-062 |
| `integration::TestCompilePatchChangesNodeNotSource` | generated | system_e2e | positive | Cross-View Invariants | covered | Verifies EXPR-062, EXPR-074 |
| `integration::TestNodeTypeRoundTrip` | generated | integration | positive | AST Visitors and Patching | covered | Verifies EXPR-063 |
| `integration::TestRuntimeFailureDoesNotPoisonProgram` | generated | system_e2e | failure_path | Error Semantics | covered | Verifies EXPR-067 |
| `integration::TestAllNumericReturnKinds` | generated | integration | positive | Cross-View Invariants | covered | Verifies EXPR-045, EXPR-071 |
| `integration::TestWarnOnAnyRejectsAny` | generated | integration | failure_path | Compilation and Execution Options | covered | Verifies EXPR-047 |
| `integration::TestWarnOnAnyMisusePanics` | generated | integration | failure_path | Error Semantics | covered | Verifies EXPR-048 |
| `integration::TestInvalidFunctionDescriptorPanics` | generated | integration | failure_path | Error Semantics | covered | Verifies EXPR-073 |
| `integration::TestUnknownTimezonePanics` | generated | integration | failure_path | Compilation and Execution Options | covered | Verifies EXPR-058 |
| `integration::TestWholeEnvironmentProjection` | generated | integration | positive | Variables, Environments, and Calls | covered | Verifies EXPR-019 |
| `integration::TestEmbeddedMethodWorkflow` | generated | integration | positive | Variables, Environments, and Calls | covered | Verifies EXPR-014 |
| `integration::TestStaticUnknownFieldRejected` | generated | integration | failure_path | Variables, Environments, and Calls | covered | Verifies EXPR-017 |
| `integration::TestCollectionPipeline` | generated | system_e2e | positive | Representative Workflows | covered | Verifies EXPR-023, EXPR-024, EXPR-029 |
| `integration::TestProgramNodeMatchesExecution` | generated | system_e2e | positive | Cross-View Invariants | covered | Verifies EXPR-065 |
| `integration::TestAsAnyAllowsDifferentResults` | generated | integration | positive | Compilation and Execution Options | covered | Verifies EXPR-046 |
| `integration::TestTypedEnvironmentFunctionWorkflow` | generated | integration | positive | Representative Workflows | covered | Verifies EXPR-020 |
| `integration::TestConcurrentRunsKeepConcreteType` | generated | system_e2e | positive | Concurrency and Isolation | covered | Verifies EXPR-072 |
| `integration::TestMapProjectionInvariant` | generated | integration | positive | Predicate and Collection Operations | covered | Verifies EXPR-034 |
| `integration::TestTimezoneProducesExpectedInstant` | generated | integration | positive | Compilation and Execution Options | covered | Verifies EXPR-058 |

Total: 74 | kept (covered): 74 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 74
Layer counts: atomic 36 | integration+system_e2e 38
