# Spec Test Map — Casbin v1

| Node ID | Clauses | Source | Spec section |
|---|---|---|---|
| `atomic::TestCAS001NewModelAndAddDef` | `CAS-MOD-001` | generated | Model Construction and Parsing |
| `atomic::TestCAS002TextAndAddDefModelsAgree` | `CAS-MOD-002` | generated | Model Construction and Parsing |
| `atomic::TestCAS003ModelTextRequiredSections` | `CAS-MOD-003`, `CAS-ERR-001` | generated | Model Construction and Parsing |
| `atomic::TestCAS004ModelOnlyStartsEmpty` | `CAS-NEW-001` | generated | Construction and Loading |
| `atomic::TestCAS005ACLAllowAndDeny` | `CAS-ENF-001`, `CAS-ENF-005` | generated | Enforcement |
| `atomic::TestCAS006InvalidRequestArityReturnsError` | `CAS-ENF-002`, `CAS-ERR-002` | generated | Enforcement |
| `atomic::TestCAS007EnableEnforceRoundTrip` | `CAS-ENF-008` | generated | Enforcement |
| `atomic::TestCAS008MatcherOverrideIsCallLocal` | `CAS-ENF-009` | generated | Enforcement |
| `atomic::TestCAS009EnforceExExplanation` | `CAS-ENF-010` | generated | Enforcement |
| `atomic::TestCAS010BatchEnforceOrder` | `CAS-ENF-011` | generated | Enforcement |
| `atomic::TestCAS011ABACStructAndMapFields` | `CAS-ENF-003` | generated | Enforcement |
| `atomic::TestCAS012BuiltInPathAndRegexMatchers` | `CAS-ENF-004` | generated | Enforcement |
| `atomic::TestCAS013DenyOverride` | `CAS-ENF-006` | generated | Enforcement |
| `atomic::TestCAS014PriorityEffect` | `CAS-ENF-007` | generated | Enforcement |
| `atomic::TestCAS015ReturnedPolicyIsCallerOwned` | `CAS-STA-002` | generated | State Model |
| `atomic::TestCAS016VariadicPolicyShapesAndDuplicates` | `CAS-POL-003`, `CAS-POL-004`, `CAS-POL-005` | generated | Authorization Policy Management |
| `atomic::TestCAS017DefaultAndNamedPolicyAgree` | `CAS-POL-001` | generated | Authorization Policy Management |
| `atomic::TestCAS018FilteredPolicyAndWildcards` | `CAS-POL-002` | generated | Authorization Policy Management |
| `atomic::TestCAS019AddPoliciesStoredDuplicateIsAtomic` | `CAS-POL-006` | generated | Authorization Policy Management |
| `atomic::TestCAS020AddPoliciesExSkipsDuplicates` | `CAS-POL-007` | generated | Authorization Policy Management |
| `atomic::TestCAS021UpdatePolicyExistingAndAbsent` | `CAS-POL-008` | generated | Authorization Policy Management |
| `atomic::TestCAS022RemoveFilteredPolicy` | `CAS-POL-009` | generated | Authorization Policy Management |
| `atomic::TestCAS023NamedPolicyIsolation` | `CAS-MOD-004`, `CAS-POL-010` | generated | Model Construction and Parsing |
| `atomic::TestCAS024GroupingPolicyChangedSemantics` | `CAS-RBAC-001`, `CAS-RBAC-004` | generated | Grouping Policy and RBAC |
| `atomic::TestCAS025DirectAndTransitiveRoles` | `CAS-RBAC-002`, `CAS-RBAC-003` | generated | Grouping Policy and RBAC |
| `atomic::TestCAS026ImplicitRolesTerminateForCycle` | `CAS-RBAC-006`, `CAS-ERR-002` | generated | Grouping Policy and RBAC |
| `atomic::TestCAS027DirectAndImplicitPermissions` | `CAS-RBAC-007`, `CAS-INV-002` | generated | Grouping Policy and RBAC |
| `atomic::TestCAS028PermissionMutation` | `CAS-RBAC-008` | generated | Grouping Policy and RBAC |
| `atomic::TestCAS029BuildRoleLinksIsIdempotent` | `CAS-RBAC-005` | generated | Grouping Policy and RBAC |
| `atomic::TestCAS030RejectedMutationsPreserveLaterUse` | `CAS-STA-001`, `CAS-INV-001`, `CAS-INV-006` | generated | State Model |
| `integration::TestCAS031DomainRoleEnforcementIsolation` | `CAS-DOM-001`, `CAS-DOM-002`, `CAS-INV-003` | generated | Domain RBAC |
| `integration::TestCAS032DomainDirectRoleProjections` | `CAS-DOM-003` | generated | Domain RBAC |
| `integration::TestCAS033DomainPermissionProjection` | `CAS-DOM-004` | generated | Domain RBAC |
| `integration::TestCAS034AllUsersByDomain` | `CAS-DOM-005` | generated | Domain RBAC |
| `integration::TestCAS035StringAdapterLoadsAtConstruction` | `CAS-NEW-002`, `CAS-STR-001` | generated | Construction and Loading |
| `integration::TestCAS036EmptyStringAdapterErrors` | `CAS-STR-001`, `CAS-ERR-001` | generated | String Adapter |
| `integration::TestCAS037StringSaveLoadRoundTrip` | `CAS-STR-002`, `CAS-LOD-003`, `CAS-LOD-004`, `CAS-INV-005` | generated | String Adapter |
| `integration::TestCAS038StringAdapterUnsupportedMutations` | `CAS-STR-003` | generated | String Adapter |
| `integration::TestCAS039FilePathConstruction` | `CAS-FIL-001`, `CAS-NEW-003` | generated | File Adapter |
| `integration::TestCAS040FileSaveLoadRoundTrip` | `CAS-FIL-002`, `CAS-LOD-003`, `CAS-INV-005` | generated | File Adapter |
| `integration::TestCAS041FileAdapterUnsupportedMutations` | `CAS-FIL-003` | generated | File Adapter |
| `integration::TestCAS042ClearThenReloadUsesAdapter` | `CAS-LOD-001`, `CAS-LOD-002`, `CAS-INV-004` | generated | Construction and Loading |
| `integration::TestCAS043EmptyFileAdapterErrors` | `CAS-FIL-001`, `CAS-ERR-001` | generated | File Adapter |
| `integration::TestCAS044ConstructorFailuresReturnErrors` | `CAS-NEW-004`, `CAS-ERR-002` | generated | Construction and Loading |
| `integration::TestCAS045ConcurrentReadOnlyEnforcement` | `CAS-CON-001` | generated | Cross-View Invariants |
| `integration::TestCAS046BatchInvalidRequestErrors` | `CAS-ENF-002`, `CAS-ENF-011` | generated | Enforcement |
| `integration::TestCAS047BooleanMatcherShortCircuits` | `CAS-ENF-003` | generated | Enforcement |
| `integration::TestCAS048MapNumericComparison` | `CAS-ENF-003` | generated | Enforcement |
| `integration::TestCAS049AddPoliciesRepeatedInputRetainedOnce` | `CAS-POL-006` | generated | Authorization Policy Management |
| `integration::TestCAS050NamedMembershipAndFilter` | `CAS-MOD-004`, `CAS-POL-002`, `CAS-POL-010` | generated | Model Construction and Parsing |
| `integration::TestCAS051RemoveFilteredWildcard` | `CAS-POL-009` | generated | Authorization Policy Management |
| `integration::TestCAS052MultipleRolePathsDoNotDuplicatePermissions` | `CAS-RBAC-006`, `CAS-RBAC-007` | generated | Grouping Policy and RBAC |
| `integration::TestCAS053DomainRoleNoOpBooleans` | `CAS-DOM-002`, `CAS-STA-001` | generated | Domain RBAC |
| `integration::TestCAS054StringRoundTripIncludesGroupingPolicy` | `CAS-STR-002`, `CAS-INV-005` | generated | String Adapter |
| `integration::TestCAS055FileSaveTruncatesOldContents` | `CAS-FIL-002` | generated | File Adapter |
| `integration::TestCAS056LoadPolicyReplacesRatherThanMerges` | `CAS-LOD-002`, `CAS-INV-004` | generated | Construction and Loading |
| `integration::TestCAS057UnreadablePolicyPathErrors` | `CAS-FIL-001`, `CAS-ERR-001` | generated | File Adapter |
| `integration::TestCAS058DistinctEnforcersDoNotSharePolicy` | `CAS-STA-002` | generated | State Model |
| `integration::TestCAS059InvalidRequestDoesNotPoisonLaterRequest` | `CAS-INV-006` | generated | Cross-View Invariants |
| `integration::TestCAS060ClearPolicyRemovesAuthorizationAndGroupingRows` | `CAS-LOD-001` | generated | Construction and Loading |
