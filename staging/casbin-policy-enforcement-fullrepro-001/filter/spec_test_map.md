# spec_test_map — casbin-policy-enforcement-fullrepro-001

oracle_source: generated_only (Track B; see rewrite_audit.md)
oracle_version: 2026-08-25T01
node id format: {suite}::{TestFunc} (Go base test functions; suites atomic/, integration/)
source: generated (all rows; upstream suite not liftable)

| test_nodeid | layer | assertion_kind | spec_section | status | notes |
|-------------|-------|----------------|--------------|--------|------|
| atomic::TestModelFromStringParses | atomic | positive | section Model Definition + section Request Enforcement | covered |  |
| atomic::TestMissingSectionsError | atomic | failure_path | section Error Semantics | covered |  |
| atomic::TestMissingSectionErrorNamesSection | atomic | failure_path | section Error Semantics | covered |  |
| atomic::TestEnforceWrongArityError | atomic | failure_path | section Error Semantics + section Request Enforcement | covered |  |
| atomic::TestUndefinedFunctionError | atomic | failure_path | section Error Semantics | covered |  |
| atomic::TestEmptyPolicyDeniesAllEffects | atomic | failure_path | section Error Semantics + section Model Definition | covered | negative predicate; twin TestModelFromStringParses |
| atomic::TestImplicitEftReadsAllow | atomic | positive | section Model Definition | covered |  |
| atomic::TestThreePlaceRoleDefinitionParses | atomic | positive | section Model Definition + section Role Inheritance | covered |  |
| atomic::TestExactStringMatcher | atomic | positive | section Matcher Language | covered |  |
| atomic::TestInequalityMatcher | atomic | positive | section Matcher Language | covered |  |
| atomic::TestBooleanConnectives | atomic | positive | section Matcher Language | covered |  |
| atomic::TestNumericComparisonMatcher | atomic | positive | section Matcher Language | covered |  |
| atomic::TestInOperator | atomic | positive | section Matcher Language | covered |  |
| atomic::TestAbacFieldAccess | atomic | positive | section Matcher Language | covered |  |
| atomic::TestEvalPolicyRule | atomic | positive | section Matcher Language | covered |  |
| atomic::TestKeyMatchPrefix | atomic | positive | section Matcher Language | covered |  |
| atomic::TestKeyMatchExactEquality | atomic | positive | section Matcher Language | covered |  |
| atomic::TestKeyMatch2NamedSegment | atomic | positive | section Matcher Language | covered |  |
| atomic::TestRegexMatch | atomic | positive | section Matcher Language | covered |  |
| atomic::TestGlobMatchSegmentScoped | atomic | positive | section Matcher Language | covered |  |
| atomic::TestIpMatchCidr | atomic | positive | section Matcher Language | covered |  |
| atomic::TestRolePredicateInMatcher | atomic | positive | section Matcher Language + section Role Inheritance | covered |  |
| atomic::TestAllowOverrideEffect | atomic | positive | section Model Definition | covered |  |
| atomic::TestDenyOverrideVeto | atomic | failure_path | section Model Definition | covered | negative predicate; twin TestDenyOverrideAllowOnly |
| atomic::TestDenyOverrideAllowOnly | atomic | positive | section Model Definition | covered |  |
| atomic::TestDenyRuleAloneDoesNotAllow | atomic | failure_path | section Model Definition | covered | negative predicate; twin TestDenyOverrideAllowOnly |
| atomic::TestPriorityFirstMatchDecides | atomic | positive | section Model Definition | covered |  |
| atomic::TestPriorityNoMatchDenies | atomic | failure_path | section Model Definition | covered | negative predicate; twin TestPriorityFirstMatchDecides |
| atomic::TestAddPolicyAndHasPolicy | atomic | positive | section Policy Management | covered |  |
| atomic::TestAddPolicyDuplicateReturnsFalse | atomic | positive | section Policy Management | covered |  |
| atomic::TestRemovePolicy | atomic | positive | section Policy Management | covered |  |
| atomic::TestGetPolicyListsAll | atomic | positive | section Policy Management | covered |  |
| atomic::TestGetFilteredPolicyByIndex | atomic | positive | section Policy Management | covered |  |
| atomic::TestGetFilteredPolicyEmptyStringWildcard | atomic | positive | section Policy Management | covered |  |
| atomic::TestRemoveFilteredPolicy | atomic | positive | section Policy Management | covered |  |
| atomic::TestAddPoliciesAtomicOnDuplicate | atomic | positive | section Policy Management | covered |  |
| atomic::TestUpdatePolicyReplacesRule | atomic | positive | section Policy Management | covered |  |
| atomic::TestGroupingPolicyCrud | atomic | positive | section Policy Management | covered |  |
| atomic::TestGetAllCatalogs | atomic | positive | section Policy Management | covered |  |
| atomic::TestBatchEnforceOrder | atomic | positive | section Request Enforcement | covered |  |
| atomic::TestEnforceExExplanation | atomic | positive | section Request Enforcement | covered |  |
| atomic::TestGetRolesForUserDirectOnly | atomic | positive | section Role Inheritance | covered |  |
| atomic::TestGetUsersForRole | atomic | positive | section Role Inheritance | covered |  |
| atomic::TestHasRoleForUser | atomic | positive | section Role Inheritance | covered |  |
| atomic::TestAddRoleForUserAndDelete | atomic | positive | section Role Inheritance | covered |  |
| atomic::TestGetImplicitRolesTransitive | atomic | positive | section Role Inheritance | covered |  |
| atomic::TestGetImplicitRolesDiamond | atomic | positive | section Role Inheritance | covered |  |
| atomic::TestPermissionsForUserDirectOnly | atomic | positive | section Role Inheritance | covered |  |
| atomic::TestImplicitPermissionsIncludeRoleRules | atomic | positive | section Role Inheritance | covered |  |
| atomic::TestPermissionHelpers | atomic | positive | section Role Inheritance | covered |  |
| atomic::TestStringAdapterLoadsRules | atomic | positive | section Persistence | covered |  |
| atomic::TestSavePolicyWritesStringAdapter | atomic | positive | section Persistence | covered |  |
| atomic::TestLoadPolicyDiscardsUnsaved | atomic | positive | section Persistence | covered |  |
| atomic::TestFileEnforcerConstruction | atomic | positive | section Persistence | covered |  |
| atomic::TestModelOnlyEnforcerStartsEmpty | atomic | positive | section Persistence | covered | negative predicate; twins in persist family |
| integration::TestMutationVisibleAcrossProjections | integration | positive | section Cross-View Invariants + section State Model | covered |  |
| integration::TestEnforceExAgreesWithEnforce | integration | positive | section Cross-View Invariants + section Request Enforcement | covered |  |
| integration::TestBatchAgreesWithSingle | integration | positive | section Cross-View Invariants + section Request Enforcement | covered |  |
| integration::TestRoleSubsetInvariant | integration | positive | section Cross-View Invariants + section Role Inheritance | covered |  |
| integration::TestRoleLinkFlipsVerdictAndQuery | integration | positive | section Cross-View Invariants + section Role Inheritance | covered |  |
| integration::TestGroupingRemovalRebuildsGraph | integration | positive | section Role Inheritance + section State Model | covered |  |
| integration::TestDomainIsolation | integration | positive | section Cross-View Invariants + section Role Inheritance | covered |  |
| integration::TestDomainRoleRemovalScoped | integration | positive | section Cross-View Invariants + section Role Inheritance | covered |  |
| integration::TestCatalogsFollowStore | integration | positive | section Policy Management + section State Model | covered |  |
| integration::TestFilteredRemovalAffectsEnforcement | integration | positive | section Policy Management + section Cross-View Invariants | covered |  |
| integration::TestUpdatePolicyAffectsEnforcement | integration | positive | section Policy Management + section Cross-View Invariants | covered |  |
| integration::TestAddPoliciesVisibleAtomically | integration | positive | section Policy Management + section Error Semantics | covered |  |
| integration::TestPermissionHelpersProjectToPolicy | integration | positive | section Role Inheritance + section Policy Management | covered |  |
| integration::TestRbacDocumentWorkflow | integration | positive | section Representative Workflows | covered |  |
| integration::TestDenyAuditWorkflow | integration | positive | section Representative Workflows | covered |  |
| integration::TestDenyOverridesInheritedAllow | integration | positive | section Representative Workflows + section Model Definition | covered |  |
| integration::TestTransitiveChainEnforcement | integration | positive | section Role Inheritance | covered |  |
| integration::TestKeyMatchWithRbacWorkflow | integration | positive | section Matcher Language + section Role Inheritance | covered |  |
| integration::TestAbacWithRbacMixed | integration | positive | section Matcher Language + section Role Inheritance | covered |  |
| integration::TestEvalWorkflowWithMutations | integration | positive | section Matcher Language + section Policy Management | covered |  |
| integration::TestPriorityWithRoleRules | integration | positive | section Model Definition + section Role Inheritance | covered |  |
| integration::TestStringAdapterPersistenceWorkflow | integration | positive | section Persistence + section Cross-View Invariants | covered |  |
| integration::TestSaveLoadRoundTrip | integration | positive | section Persistence + section Cross-View Invariants | covered |  |
| integration::TestFileAdapterRoundTrip | integration | positive | section Persistence + section Cross-View Invariants | covered |  |
| integration::TestLoadPolicyRebuildsRoleGraph | integration | positive | section Persistence + section State Model | covered |  |
| integration::TestExplanationTracksStoreMutation | integration | positive | section Request Enforcement + section State Model | covered |  |
| integration::TestManyModelsOneStoreShape | integration | positive | section Model Definition + section State Model | covered |  |
| integration::TestGetUsersForRoleInDomainProjection | integration | positive | section Role Inheritance + section Cross-View Invariants | covered |  |
| integration::TestWrongArityLeavesStoreUsable | integration | positive | section Error Semantics + section Representative Workflows | covered |  |

Total: 84 | kept (covered): 84 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 84

Layer counts: atomic 55 | integration 29 | system_e2e 0
Assertion-kind counts: atomic positive 47, failure_path 8; integration positive 29, failure_path 0; no_check 0
