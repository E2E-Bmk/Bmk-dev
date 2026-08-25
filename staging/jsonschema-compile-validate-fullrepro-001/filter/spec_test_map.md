# Spec-to-test map — jsonschema-compile-validate-fullrepro-001

oracle_version: 2026-08-25T1
oracle_source: generated_only (upstream suite is a data-driven conformance
runner over the official JSON-Schema-Test-Suite plus stdout-comparing example
tests; no upstream test function is liftable — see rewrite_audit.md)

| test_nodeid | layer | assertion_kind | spec_section | status | source |
|-------------|-------|----------------|--------------|--------|--------|
| `atomic::TestTypeIntegerAcceptsZeroFractionNumbers` | atomic | positive | section Instance Validation: Scalar Keywords | covered | generated |
| `atomic::TestTypeKindReportsGotAndWant` | atomic | positive | section Validation Errors and Output Formats | covered | generated |
| `atomic::TestTypeListMatchesAnyListedType` | atomic | positive | section Instance Validation: Scalar Keywords | covered | generated |
| `atomic::TestEnumUsesRationalNumberEquality` | atomic | positive | section Instance Validation: Scalar Keywords | covered | generated |
| `atomic::TestConstBehavesAsSingleValueEnum` | atomic | positive | section Instance Validation: Scalar Keywords | covered | generated |
| `atomic::TestConstObjectEqualityIgnoresKeyOrder` | atomic | positive | section JSON Document Model | covered | generated |
| `atomic::TestMinimumAndMaximumAreInclusive` | atomic | positive | section Instance Validation: Scalar Keywords | covered | generated |
| `atomic::TestExclusiveBoundsRejectBoundaryValues` | atomic | positive | section Instance Validation: Scalar Keywords | covered | generated |
| `atomic::TestMultipleOfUsesRationalArithmetic` | atomic | positive | section JSON Document Model + Instance Validation: Scalar Keywords | covered | generated |
| `atomic::TestNumericKeywordsIgnoreNonNumbers` | atomic | positive | section Instance Validation: Scalar Keywords | covered | generated |
| `atomic::TestValidateAcceptsNativeGoNumbers` | atomic | positive | section JSON Document Model | covered | generated |
| `atomic::TestStringLengthCountsCodePoints` | atomic | positive | section JSON Document Model + Instance Validation: Scalar Keywords | covered | generated |
| `atomic::TestPatternMatchesAnywhereInString` | atomic | positive | section Instance Validation: Scalar Keywords | covered | generated |
| `atomic::TestPropertiesApplyToMatchingMembers` | atomic | positive | section Instance Validation: Objects and Arrays | covered | generated |
| `atomic::TestRequiredReportsExactlyMissingMembers` | atomic | positive | section Instance Validation: Objects and Arrays + Validation Errors and Output Formats | covered | generated |
| `atomic::TestPatternPropertiesApplyByNameMatch` | atomic | positive | section Instance Validation: Objects and Arrays | covered | generated |
| `atomic::TestAdditionalPropertiesFalseRejectsUnmatched` | atomic | positive | section Instance Validation: Objects and Arrays | covered | generated |
| `atomic::TestAdditionalPropertiesSchemaValidatesUnmatched` | atomic | positive | section Instance Validation: Objects and Arrays | covered | generated |
| `atomic::TestPropertyNamesValidatesMemberNames` | atomic | positive | section Instance Validation: Objects and Arrays | covered | generated |
| `atomic::TestMinAndMaxPropertiesBoundMemberCount` | atomic | positive | section Instance Validation: Objects and Arrays | covered | generated |
| `atomic::TestDependentRequiredAddsObligations` | atomic | positive | section Instance Validation: Objects and Arrays | covered | generated |
| `atomic::TestDependentSchemasApplyWhenMemberPresent` | atomic | positive | section Instance Validation: Objects and Arrays | covered | generated |
| `atomic::TestPrefixItemsThenItemsSplit` | atomic | positive | section Instance Validation: Objects and Arrays | covered | generated |
| `atomic::TestItemsAloneCoversEveryElement` | atomic | positive | section Instance Validation: Objects and Arrays | covered | generated |
| `atomic::TestMinAndMaxItemsBoundLength` | atomic | positive | section Instance Validation: Objects and Arrays | covered | generated |
| `atomic::TestUniqueItemsUsesRationalEquality` | atomic | positive | section Instance Validation: Objects and Arrays + JSON Document Model | covered | generated |
| `atomic::TestContainsRequiresAtLeastOneMatch` | atomic | positive | section Instance Validation: Objects and Arrays | covered | generated |
| `atomic::TestMinAndMaxContainsBoundMatchCount` | atomic | positive | section Instance Validation: Objects and Arrays | covered | generated |
| `atomic::TestMinContainsZeroAcceptsNoMatches` | atomic | positive | section Instance Validation: Objects and Arrays | covered | generated |
| `atomic::TestAllOfRequiresEveryBranch` | atomic | positive | section Schema Composition and Conditionals | covered | generated |
| `atomic::TestAnyOfRequiresAtLeastOneBranch` | atomic | positive | section Schema Composition and Conditionals | covered | generated |
| `atomic::TestOneOfRequiresExactlyOneMatch` | atomic | positive | section Schema Composition and Conditionals | covered | generated |
| `atomic::TestNotInvertsItsSubschema` | atomic | positive | section Schema Composition and Conditionals | covered | generated |
| `atomic::TestIfThenElseSelectsBranch` | atomic | positive | section Schema Composition and Conditionals | covered | generated |
| `atomic::TestIfWithoutBranchesConstrainsNothing` | atomic | positive | section Schema Composition and Conditionals | covered | generated |
| `atomic::TestUnmarshalJSONPreservesNumberPrecision` | atomic | positive | section JSON Document Model | covered | generated |
| `atomic::TestUnmarshalJSONDecodesContainers` | atomic | positive | section JSON Document Model | covered | generated |
| `atomic::TestUnmarshalJSONRejectsTrailingContent` | atomic | failure_path | section JSON Document Model + Error Semantics | covered | generated |
| `atomic::TestAddResourceDuplicateURLFails` | atomic | failure_path | section Resource Registration and Compilation + Error Semantics | covered | generated |
| `atomic::TestCompiledSchemaExposesLocationAndDraft` | atomic | positive | section Resource Registration and Compilation | covered | generated |
| `atomic::TestCompileMetaSchemaViolationFails` | atomic | failure_path | section Resource Registration and Compilation + Error Semantics | covered | generated |
| `atomic::TestCompileUnloadableURLFails` | atomic | failure_path | section Resource Registration and Compilation + Error Semantics | covered | generated |
| `atomic::TestMustCompilePanicsWhereCompileErrors` | atomic | failure_path | section Resource Registration and Compilation + Error Semantics | covered | generated |
| `atomic::TestSchemeURLLoaderRejectsUnknownScheme` | atomic | failure_path | section Resource Registration and Compilation + Error Semantics | covered | generated |
| `atomic::TestFileLoaderToFileConvertsURL` | atomic | positive | section Resource Registration and Compilation | covered | generated |
| `atomic::TestTrueSchemaAcceptsEverything` | atomic | positive | section Resource Registration and Compilation | covered | generated |
| `atomic::TestFalseSchemaRejectsEverything` | atomic | positive | section Resource Registration and Compilation + Validation Errors and Output Formats | covered | generated |
| `atomic::TestBooleanSubschemaInsideKeyword` | atomic | positive | section Schema Composition and Conditionals | covered | generated |
| `atomic::TestValidateReturnsNilOnConformingInstance` | atomic | positive | section Instance Validation: Scalar Keywords + Error Semantics | covered | generated |
| `atomic::TestValidationErrorRootKindIsSchema` | atomic | positive | section Validation Errors and Output Formats | covered | generated |
| `atomic::TestValidationErrorSchemaURLPointsAtFailingSubschema` | atomic | positive | section Validation Errors and Output Formats | covered | generated |
| `atomic::TestFlagOutputCarriesValidityOnly` | atomic | positive | section Validation Errors and Output Formats | covered | generated |
| `integration::TestCrossResourceRefEnforcesTargetRules` | integration | positive | section Reference Resolution | covered | generated |
| `integration::TestRefTransparencyAgreesWithDirectCompile` | integration | positive | section Cross-View Invariants | covered | generated |
| `integration::TestCompileCachingReturnsIdenticalPointer` | integration | positive | section Cross-View Invariants + State Model | covered | generated |
| `integration::TestMustCompileAgreesWithCompile` | integration | positive | section Cross-View Invariants | covered | generated |
| `integration::TestAnchorNotFoundAcrossResources` | integration | failure_path | section Reference Resolution + Error Semantics | covered | generated |
| `integration::TestEmbeddedResourceWithIDIsReferenceable` | integration | positive | section Reference Resolution | covered | generated |
| `integration::TestRecursiveSchemaValidatesNestedTree` | integration | positive | section Reference Resolution + Validation Errors and Output Formats | covered | generated |
| `integration::TestDynamicRefResolvesRecursively` | integration | positive | section Reference Resolution | covered | generated |
| `integration::TestErrorTreeAgreesWithBasicOutput` | integration | positive | section Cross-View Invariants + Validation Errors and Output Formats | covered | generated |
| `integration::TestBasicOutputFlattensWhatDetailedNests` | integration | positive | section Validation Errors and Output Formats | covered | generated |
| `integration::TestOutputProjectionsAgreeOnValidity` | integration | positive | section Cross-View Invariants + Validation Errors and Output Formats | covered | generated |
| `integration::TestBasicOutputJSONMemberNames` | integration | positive | section Validation Errors and Output Formats | covered | generated |
| `integration::TestMultipleViolationsReportedTogether` | integration | positive | section Validation Errors and Output Formats | covered | generated |
| `integration::TestNestedInstanceLocationPath` | integration | positive | section Validation Errors and Output Formats | covered | generated |
| `integration::TestCustomLoaderEquivalentToAddResource` | integration | positive | section Cross-View Invariants + Resource Registration and Compilation | covered | generated |
| `integration::TestFileLoaderCompilesFromDisk` | integration | positive | section Resource Registration and Compilation | covered | generated |
| `integration::TestSchemeURLLoaderDispatchAndFailure` | integration | positive | section Resource Registration and Compilation + Error Semantics | covered | generated |
| `integration::TestDefaultDraftSevenArrayItemsSemantics` | integration | positive | section Resource Registration and Compilation | covered | generated |
| `integration::TestSchemaDeclarationOverridesDefaultDraft` | integration | positive | section Resource Registration and Compilation | covered | generated |
| `integration::TestUnevaluatedPropertiesSeesAllOfEvaluation` | integration | positive | section Instance Validation: Objects and Arrays | covered | generated |
| `integration::TestUnevaluatedPropertiesAcrossRef` | integration | positive | section Instance Validation: Objects and Arrays + Reference Resolution | covered | generated |
| `integration::TestUnevaluatedItemsAfterPrefix` | integration | positive | section Instance Validation: Objects and Arrays | covered | generated |
| `integration::TestConstAndUniqueItemsEqualityAgree` | integration | positive | section Cross-View Invariants + JSON Document Model | covered | generated |
| `integration::TestCompiledSchemaImmuneToLaterCompilerMutations` | integration | positive | section State Model | covered | generated |
| `integration::TestValidationIsPureAcrossInstances` | integration | positive | section State Model | covered | generated |
| `integration::TestConditionalComposesWithSiblingKeywords` | integration | positive | section Schema Composition and Conditionals | covered | generated |
| `integration::TestOneOfBranchesComposeWithOuterType` | integration | positive | section Schema Composition and Conditionals | covered | generated |

Total: 79 | kept (covered): 79 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 79

Layer counts: atomic 52 | integration 27 | system_e2e 0
