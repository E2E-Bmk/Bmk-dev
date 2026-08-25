# spec_test_map — cty-value-type-system-fullrepro-001

All tests generated (Track B); upstream suite fully excluded (see
rewrite_audit.md). Spec: spec.md (v1). Totals: 132 tests =
96 atomic + 36 integration. Atomic positive share:
80/96 = 83% (>= 60% floor). Every behavior
section >= 4 tests, Error Semantics >= 4, Representative Workflows >= 4,
each of the seven Cross-View Invariants covered by >= 2 integration tests
(CVI numbers noted in the spec_section column).

| test_nodeid | layer | assertion_kind | spec_section | status | source |
|---|---|---|---|---|---|
| oracle/atomic::TestJSONMarshalShapes | atomic | positive | JSON Codec | covered | generated |
| oracle/atomic::TestJSONMarshalRefusals | atomic | failure_path | JSON Codec + Error Semantics | covered | generated |
| oracle/atomic::TestJSONTypeSerialization | atomic | positive | JSON Codec | covered | generated |
| oracle/atomic::TestJSONImpliedType | atomic | positive | JSON Codec | covered | generated |
| oracle/atomic::TestSimpleJSONValue | atomic | positive | JSON Codec | covered | generated |
| oracle/atomic::TestMsgpackRoundTripKnown | atomic | positive | MessagePack Codec | covered | generated |
| oracle/atomic::TestMsgpackUnknownAndRefinements | atomic | positive | MessagePack Codec + Unknown Values and Refinements | covered | generated |
| oracle/atomic::TestMsgpackMarkedRefused | atomic | failure_path | MessagePack Codec + Error Semantics | covered | generated |
| oracle/atomic::TestPrimitiveConversionTiers | atomic | positive | Conversion Engine | covered | generated |
| oracle/atomic::TestNumberToStringFormatting | atomic | positive | Conversion Engine | covered | generated |
| oracle/atomic::TestStringToNumberParsing | atomic | positive | Conversion Engine | covered | generated |
| oracle/atomic::TestStringToBoolStrict | atomic | failure_path | Conversion Engine + Error Semantics | covered | generated |
| oracle/atomic::TestConvertNullAndUnknownPassthrough | atomic | positive | Conversion Engine + Unknown Values and Refinements | covered | generated |
| oracle/atomic::TestConvertSameTypeIdentity | atomic | positive | Conversion Engine | covered | generated |
| oracle/atomic::TestMismatchMessages | atomic | failure_path | Conversion Engine + Error Semantics | covered | generated |
| oracle/atomic::TestMarkAndInspect | atomic | positive | Marks | covered | generated |
| oracle/atomic::TestMarkPropagationThroughOps | atomic | positive | Marks | covered | generated |
| oracle/atomic::TestUnmarkReturnsMarkSet | atomic | positive | Marks | covered | generated |
| oracle/atomic::TestIntegrationMethodsPanicOnMarked | atomic | failure_path | Marks + Error Semantics | covered | generated |
| oracle/atomic::TestContainmentPredicates | atomic | positive | Marks | covered | generated |
| oracle/atomic::TestRawEqualsIsMarkSensitive | atomic | positive | Marks + Value Operations | covered | generated |
| oracle/atomic::TestDeepUnmarkAndPathRecords | atomic | positive | Marks + Paths | covered | generated |
| oracle/atomic::TestSetValFlattensElementMarks | atomic | positive | Marks + Value Construction and Content Model | covered | generated |
| oracle/atomic::TestWithMarksAndNewValueMarks | atomic | positive | Marks | covered | generated |
| oracle/atomic::TestEqualsKnownValues | atomic | positive | Value Operations | covered | generated |
| oracle/atomic::TestEqualsCrossTypeFalse | atomic | positive | Value Operations | covered | generated |
| oracle/atomic::TestEqualsNulls | atomic | positive | Value Operations | covered | generated |
| oracle/atomic::TestEqualsUnknownYieldsRefinedUnknownBool | atomic | positive | Value Operations + Unknown Values and Refinements | covered | generated |
| oracle/atomic::TestNotEqual | atomic | positive | Value Operations | covered | generated |
| oracle/atomic::TestRawEqualsUnknowns | atomic | positive | Value Operations | covered | generated |
| oracle/atomic::TestArithmetic | atomic | positive | Value Operations | covered | generated |
| oracle/atomic::TestDivisionAndModulo | atomic | positive | Value Operations | covered | generated |
| oracle/atomic::TestComparisons | atomic | positive | Value Operations | covered | generated |
| oracle/atomic::TestBoolOps | atomic | positive | Value Operations | covered | generated |
| oracle/atomic::TestOperationTypeMismatchPanics | atomic | failure_path | Value Operations + Error Semantics | covered | generated |
| oracle/atomic::TestUnknownOperandPropagation | atomic | positive | Value Operations + Unknown Values and Refinements | covered | generated |
| oracle/atomic::TestListIndexing | atomic | positive | Value Operations | covered | generated |
| oracle/atomic::TestMapIndexing | atomic | positive | Value Operations | covered | generated |
| oracle/atomic::TestTupleIndexing | atomic | positive | Value Operations | covered | generated |
| oracle/atomic::TestSetMembership | atomic | positive | Value Operations | covered | generated |
| oracle/atomic::TestGetAttrBehavior | atomic | positive | Value Operations | covered | generated |
| oracle/atomic::TestLengthOnNullPanics | atomic | failure_path | Value Operations + Error Semantics | covered | generated |
| oracle/atomic::TestSetWithUnknownsLengthRange | atomic | positive | Value Operations + Unknown Values and Refinements | covered | generated |
| oracle/atomic::TestIterationOrderAndEarlyStop | atomic | positive | Value Operations | covered | generated |
| oracle/atomic::TestNativeExtractors | atomic | positive | Value Operations | covered | generated |
| oracle/atomic::TestCanIterateElements | atomic | positive | Value Operations | covered | generated |
| oracle/atomic::TestPathApplySuccess | atomic | positive | Paths | covered | generated |
| oracle/atomic::TestPathApplyErrors | atomic | failure_path | Paths + Error Semantics | covered | generated |
| oracle/atomic::TestPathEqualsAndHasPrefix | atomic | positive | Paths | covered | generated |
| oracle/atomic::TestPathStepShapes | atomic | positive | Paths | covered | generated |
| oracle/atomic::TestPathCopyIndependence | atomic | positive | Paths + State Model | covered | generated |
| oracle/atomic::TestRefineNotNullVsNull | atomic | positive | Unknown Values and Refinements | covered | generated |
| oracle/atomic::TestStringPrefixTrimming | atomic | positive | Unknown Values and Refinements | covered | generated |
| oracle/atomic::TestNumberRangeKnownComparisons | atomic | positive | Unknown Values and Refinements | covered | generated |
| oracle/atomic::TestCollectionLengthRefinement | atomic | positive | Unknown Values and Refinements | covered | generated |
| oracle/atomic::TestRefineKnownValueSelfCheck | atomic | positive | Unknown Values and Refinements | covered | generated |
| oracle/atomic::TestContradictoryRefinementPanics | atomic | failure_path | Unknown Values and Refinements + Error Semantics | covered | generated |
| oracle/atomic::TestRefineNullCollapses | atomic | positive | Unknown Values and Refinements | covered | generated |
| oracle/atomic::TestDynamicValIgnoresRefinements | atomic | positive | Unknown Values and Refinements | covered | generated |
| oracle/atomic::TestValueRangeProjections | atomic | positive | Unknown Values and Refinements | covered | generated |
| oracle/atomic::TestPrimitiveTypeIdentity | atomic | positive | Type System | covered | generated |
| oracle/atomic::TestCollectionKindPredicates | atomic | positive | Type System | covered | generated |
| oracle/atomic::TestKindSpecificElementAccessors | atomic | positive | Type System | covered | generated |
| oracle/atomic::TestElementTypeOnNonCollectionPanics | atomic | failure_path | Type System + Error Semantics | covered | generated |
| oracle/atomic::TestObjectAttributeIntrospection | atomic | positive | Type System | covered | generated |
| oracle/atomic::TestObjectAttributeTypeMissingPanics | atomic | failure_path | Type System + Error Semantics | covered | generated |
| oracle/atomic::TestTupleElementIntrospection | atomic | positive | Type System | covered | generated |
| oracle/atomic::TestTypeLengthOnNonTuplePanics | atomic | failure_path | Type System + Error Semantics | covered | generated |
| oracle/atomic::TestTypeEqualityStructural | atomic | positive | Type System | covered | generated |
| oracle/atomic::TestOptionalAttrsAffectTypeIdentity | atomic | positive | Type System | covered | generated |
| oracle/atomic::TestConformanceDynamicWildcard | atomic | positive | Type System | covered | generated |
| oracle/atomic::TestFriendlyNames | atomic | positive | Type System | covered | generated |
| oracle/atomic::TestGoStringOfTypes | atomic | positive | Type System | covered | generated |
| oracle/atomic::TestHasDynamicTypesDeep | atomic | positive | Type System | covered | generated |
| oracle/atomic::TestEmptyStructuralTypes | atomic | positive | Type System | covered | generated |
| oracle/atomic::TestValueSetBasics | atomic | positive | Value Operations | covered | generated |
| oracle/atomic::TestValueSetCopyIndependence | atomic | positive | Value Operations + State Model | covered | generated |
| oracle/atomic::TestValueSetAlgebra | atomic | positive | Value Operations | covered | generated |
| oracle/atomic::TestValueSetWrongTypePanics | atomic | failure_path | Value Operations + Error Semantics | covered | generated |
| oracle/atomic::TestSetValFromValueSet | atomic | positive | Value Operations + Value Construction and Content Model | covered | generated |
| oracle/atomic::TestStringNFCNormalization | atomic | positive | Value Construction and Content Model | covered | generated |
| oracle/atomic::TestAsStringPanicsOnNumber | atomic | failure_path | Value Operations + Error Semantics | covered | generated |
| oracle/atomic::TestBoolValTrueFalse | atomic | positive | Value Construction and Content Model | covered | generated |
| oracle/atomic::TestNumberIntegerExactness | atomic | positive | Value Construction and Content Model | covered | generated |
| oracle/atomic::TestParseNumberValInvalid | atomic | failure_path | Value Construction and Content Model + Error Semantics | covered | generated |
| oracle/atomic::TestDecimalCorrection | atomic | positive | Value Construction and Content Model | covered | generated |
| oracle/atomic::TestNegativeZeroEqualsZero | atomic | positive | Value Construction and Content Model | covered | generated |
| oracle/atomic::TestInfinityOrdering | atomic | positive | Value Construction and Content Model + Value Operations | covered | generated |
| oracle/atomic::TestListValPreconditions | atomic | failure_path | Value Construction and Content Model + Error Semantics | covered | generated |
| oracle/atomic::TestListValEmpty | atomic | positive | Value Construction and Content Model | covered | generated |
| oracle/atomic::TestMapValAndEmpty | atomic | positive | Value Construction and Content Model | covered | generated |
| oracle/atomic::TestSetValDedup | atomic | positive | Value Construction and Content Model | covered | generated |
| oracle/atomic::TestTupleObjectValTypeDerivation | atomic | positive | Value Construction and Content Model + Type System | covered | generated |
| oracle/atomic::TestNullAndUnknownConstructors | atomic | positive | Value Construction and Content Model + Unknown Values and Refinements | covered | generated |
| oracle/atomic::TestWhollyKnownDistinction | atomic | positive | Unknown Values and Refinements | covered | generated |
| oracle/atomic::TestUnknownAsNullDeep | atomic | positive | Value Construction and Content Model + Unknown Values and Refinements | covered | generated |
| oracle/integration::TestJSONRoundTripIdentity | integration | positive | JSON Codec + Cross-View Invariants (CVI 2) | covered | generated |
| oracle/integration::TestJSONMarshalConvertsFirst | integration | failure_path | JSON Codec + Conversion Engine + Error Semantics | covered | generated |
| oracle/integration::TestJSONDynamicEmbedding | integration | positive | JSON Codec + Type System | covered | generated |
| oracle/integration::TestJSONUnmarshalObjectLenience | integration | positive | JSON Codec + Error Semantics | covered | generated |
| oracle/integration::TestImpliedTypeDecodeAgreesWithTypedDecode | integration | positive | JSON Codec + Cross-View Invariants (CVI 2) | covered | generated |
| oracle/integration::TestMsgpackRoundTripBattery | integration | positive | MessagePack Codec + Cross-View Invariants (CVI 3) | covered | generated |
| oracle/integration::TestMsgpackUnknownPreservation | integration | positive | MessagePack Codec + Cross-View Invariants (CVI 3) | covered | generated |
| oracle/integration::TestMsgpackRefinementSuperset | integration | positive | MessagePack Codec + Cross-View Invariants (CVI 3) | covered | generated |
| oracle/integration::TestMsgpackDynamicTypeEmbedding | integration | positive | MessagePack Codec + Type System | covered | generated |
| oracle/integration::TestCodecsAgreeOnKnownValues | integration | positive | Cross-View Invariants (CVI 6) + JSON Codec + MessagePack Codec | covered | generated |
| oracle/integration::TestUnknownAsNullEnablesJSON | integration | positive | JSON Codec + Unknown Values and Refinements + Representative Workflows | covered | generated |
| oracle/integration::TestListSetConversionsBothWays | integration | positive | Conversion Engine | covered | generated |
| oracle/integration::TestTupleToCollectionUnification | integration | positive | Conversion Engine | covered | generated |
| oracle/integration::TestEmptyTupleToList | integration | positive | Conversion Engine | covered | generated |
| oracle/integration::TestObjectMapConversions | integration | positive | Conversion Engine | covered | generated |
| oracle/integration::TestObjectStructuralTyping | integration | positive | Conversion Engine + Type System | covered | generated |
| oracle/integration::TestObjectAttrRecursiveConversion | integration | positive | Conversion Engine | covered | generated |
| oracle/integration::TestDynamicPlaceholderConversions | integration | positive | Conversion Engine + Cross-View Invariants (CVI 1) | covered | generated |
| oracle/integration::TestListToTupleUnavailable | integration | failure_path | Conversion Engine + Error Semantics | covered | generated |
| oracle/integration::TestMarksThroughConversion | integration | positive | Conversion Engine + Marks + Cross-View Invariants (CVI 5) | covered | generated |
| oracle/integration::TestUnifyTiers | integration | positive | Conversion Engine | covered | generated |
| oracle/integration::TestUnifiedConversionsProduceOneType | integration | positive | Conversion Engine + Cross-View Invariants | covered | generated |
| oracle/integration::TestConversionPreservesEqualityClasses | integration | positive | Cross-View Invariants (CVI 1) + Conversion Engine | covered | generated |
| oracle/integration::TestRefinedAnswersAgreeWithEventualValues | integration | positive | Cross-View Invariants (CVI 4) + Unknown Values and Refinements | covered | generated |
| oracle/integration::TestMarksNeverAlterData | integration | positive | Cross-View Invariants (CVI 5) + Marks | covered | generated |
| oracle/integration::TestTypeProjectionsAgree | integration | positive | Cross-View Invariants (CVI 6) + Type System | covered | generated |
| oracle/integration::TestIterationAgreesWithAccess | integration | positive | Cross-View Invariants (CVI 7) + Value Operations | covered | generated |
| oracle/integration::TestEqualityLadderDisagreesExactlyAsSpecified | integration | positive | Cross-View Invariants + Value Operations | covered | generated |
| oracle/integration::TestWalkTransformAgree | integration | positive | Cross-View Invariants (CVI 7) + Paths | covered | generated |
| oracle/integration::TestSetLevelMarksVisibleAcrossViews | integration | positive | Cross-View Invariants (CVI 5) + Marks | covered | generated |
| oracle/integration::TestPathApplyAgreesWithDirectAccess | integration | positive | Cross-View Invariants + Paths | covered | generated |
| oracle/integration::TestConfigNormalizationWorkflow | integration | positive | Representative Workflows | covered | generated |
| oracle/integration::TestPartialEvaluationWorkflow | integration | positive | Representative Workflows + Unknown Values and Refinements (CVI 4) | covered | generated |
| oracle/integration::TestSchemaEvolutionWorkflow | integration | positive | Representative Workflows + Conversion Engine | covered | generated |
| oracle/integration::TestSensitiveDataAuditWorkflow | integration | positive | Representative Workflows + Marks | covered | generated |
| oracle/integration::TestTypeInferenceWorkflow | integration | positive | Representative Workflows + Type System | covered | generated |
