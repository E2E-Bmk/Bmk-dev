# Spec-test map

oracle_version: `2026-08-17-go-v2`  
task: `goose-sqlite-migrations-fullrepro-001`  
oracle_source: `rewritten_upstream+generated`  
reference: `pressly/goose@520411a16119bd3b332613d1ff8312c4cc249673`

| test_nodeid | source | layer | assertion_kind | spec_section | clause_ids | status |
|---|---|---|---|---|---|---|
| `atomic::TestNumericComponentSQL` | rewritten_upstream | atomic | positive | Migration Sources and SQL Directives | GOOSE-SRC-001 | covered |
| `atomic::TestNumericComponentGo` | rewritten_upstream | atomic | positive | Migration Sources and SQL Directives | GOOSE-SRC-001 | covered |
| `atomic::TestNumericComponentRejectsMissingPrefix` | rewritten_upstream | atomic | positive | Migration Sources and SQL Directives | GOOSE-SRC-001 | covered |
| `atomic::TestNumericComponentRejectsZero` | rewritten_upstream | atomic | positive | Migration Sources and SQL Directives | GOOSE-SRC-001 | covered |
| `atomic::TestNumericComponentRejectsExtension` | rewritten_upstream | atomic | positive | Migration Sources and SQL Directives | GOOSE-SRC-001 | covered |
| `atomic::TestNewProviderRejectsNilDatabase` | rewritten_upstream | atomic | positive | Provider Construction and Status | GOOSE-PROV-001 | covered |
| `atomic::TestNewProviderRejectsNoSources` | rewritten_upstream | atomic | positive | Provider Construction and Status | GOOSE-PROV-001, GOOSE-PROV-002 | covered |
| `atomic::TestListSourcesSortsByVersion` | rewritten_upstream | atomic | positive | Provider Construction and Status | GOOSE-PROV-006 | covered |
| `atomic::TestListSourcesReportsSQLMetadata` | rewritten_upstream | atomic | positive | Provider Construction and Status | GOOSE-PROV-006 | covered |
| `atomic::TestExcludeNameRemovesSource` | rewritten_upstream | atomic | positive | Provider Construction and Status; Cross-View Invariants | GOOSE-PROV-003, GOOSE-INV-008 | covered |
| `atomic::TestExcludeVersionRemovesSource` | rewritten_upstream | atomic | positive | Provider Construction and Status; Cross-View Invariants | GOOSE-PROV-003, GOOSE-INV-008 | covered |
| `atomic::TestExcludeVersionRejectsNonPositive` | rewritten_upstream | atomic | positive | Provider Construction and Status | GOOSE-PROV-003 | covered |
| `atomic::TestExcludeNameRejectsDuplicate` | rewritten_upstream | atomic | positive | Provider Construction and Status | GOOSE-PROV-003 | covered |
| `atomic::TestTableNameRejectsEmpty` | rewritten_upstream | atomic | positive | Provider Construction and Status | GOOSE-PROV-010 | covered |
| `atomic::TestGoMigrationAppearsAsSource` | rewritten_upstream | atomic | positive | Provider Construction and Status; Cross-View Invariants | GOOSE-PROV-005, GOOSE-INV-012 | covered |
| `atomic::TestGoMigrationRejectsNonPositiveVersion` | rewritten_upstream | atomic | positive | Provider Construction and Status | GOOSE-PROV-005 | covered |
| `atomic::TestGoMigrationRejectsTwoCallbacks` | rewritten_upstream | atomic | positive | Provider Construction and Status | GOOSE-PROV-005 | covered |
| `atomic::TestGoMigrationRejectsDuplicateVersion` | rewritten_upstream | atomic | positive | Provider Construction and Status; Cross-View Invariants | GOOSE-PROV-005, GOOSE-INV-012 | covered |
| `atomic::TestDefaultTableNameValue` | rewritten_upstream | atomic | positive | Provider Construction and Status | GOOSE-PROV-010 | covered |
| `atomic::TestExcludeNamesMergeAcrossOptions` | rewritten_upstream | atomic | positive | Provider Construction and Status | GOOSE-PROV-003 | covered |
| `atomic::TestExcludeVersionsMergeAcrossOptions` | rewritten_upstream | atomic | positive | Provider Construction and Status | GOOSE-PROV-003 | covered |
| `atomic::TestCollectMigrationsSortsSources` | rewritten_upstream | atomic | positive | Migration Sources and SQL Directives; Provider Construction and Status | GOOSE-SRC-001, GOOSE-PROV-006 | covered |
| `atomic::TestCollectMigrationsEmptySourceSetReturnsSentinel` | rewritten_upstream | atomic | failure_path | Migration Sources and SQL Directives; Error Semantics | GOOSE-SRC-001 | covered |
| `atomic::TestCollectMigrationsRejectsDuplicateVersion` | rewritten_upstream | atomic | positive | Migration Sources and SQL Directives | GOOSE-SRC-001 | covered |
| `atomic::TestCollectMigrationsRejectsMissingDirectory` | rewritten_upstream | atomic | positive | Migration Sources and SQL Directives | GOOSE-SRC-001 | covered |
| `atomic::TestProviderPing` | rewritten_upstream | atomic | positive | Provider Construction and Status | GOOSE-PROV-015 | covered |
| `atomic::TestProviderCloseStopsPing` | rewritten_upstream | atomic | positive | Provider Construction and Status | GOOSE-PROV-015 | covered |
| `atomic::TestCreateSequentialSQL` | rewritten_upstream | atomic | positive | File Maintenance and Go Registration | GOOSE-FILE-001, GOOSE-FILE-003 | covered |
| `atomic::TestCreateSequentialGo` | rewritten_upstream | atomic | positive | File Maintenance and Go Registration | GOOSE-FILE-001 | covered |
| `atomic::TestCreateRejectsUnavailableDirectory` | rewritten_upstream | atomic | positive | File Maintenance and Go Registration | GOOSE-FILE-001 | covered |
| `integration::TestInitialStatusIsPending` | rewritten_upstream | integration | positive | Provider Construction and Status | GOOSE-PROV-007, GOOSE-PROV-008 | covered |
| `integration::TestHasPendingBeforeAndAfterUp` | rewritten_upstream | integration | positive | Provider Construction and Status | GOOSE-PROV-009 | covered |
| `integration::TestInitialVersions` | rewritten_upstream | integration | positive | Provider Construction and Status; Cross-View Invariants | GOOSE-PROV-014, GOOSE-INV-002 | covered |
| `integration::TestUpAppliesAllSources` | rewritten_upstream | integration | positive | Representative Workflows; Apply and inspect SQL migrations; Applying and Rolling Back; State Model; Cross-View Invariants | GOOSE-RUN-001, GOOSE-RUN-010, GOOSE-INV-003 | covered |
| `integration::TestUpWhenCompleteIsEmptySuccess` | rewritten_upstream | integration | positive | Applying and Rolling Back | GOOSE-RUN-001 | covered |
| `integration::TestUpByOneAppliesNextSource` | rewritten_upstream | integration | positive | Applying and Rolling Back; Cross-View Invariants | GOOSE-RUN-002, GOOSE-INV-002 | covered |
| `integration::TestUpByOneWhenCompleteReturnsSentinel` | rewritten_upstream | integration | failure_path | Applying and Rolling Back; Error Semantics | GOOSE-RUN-002 | covered |
| `integration::TestUpToStopsAtTarget` | rewritten_upstream | integration | positive | Applying and Rolling Back | GOOSE-RUN-003 | covered |
| `integration::TestDownRollsBackLatestSource` | rewritten_upstream | integration | positive | Applying and Rolling Back; Cross-View Invariants | GOOSE-RUN-004, GOOSE-INV-004 | covered |
| `integration::TestDownWhenEmptyReturnsSentinel` | rewritten_upstream | integration | failure_path | Applying and Rolling Back; Error Semantics | GOOSE-RUN-004 | covered |
| `integration::TestDownToPreservesTarget` | rewritten_upstream | integration | positive | Applying and Rolling Back; Cross-View Invariants | GOOSE-RUN-005, GOOSE-INV-004 | covered |
| `integration::TestDownToRejectsNegativeWithoutStateChange` | rewritten_upstream | integration | positive | Applying and Rolling Back | GOOSE-RUN-005 | covered |
| `integration::TestApplyVersionTargetsOneSource` | rewritten_upstream | integration | positive | Applying and Rolling Back | GOOSE-RUN-006 | covered |
| `integration::TestApplyVersionRejectsMissingSource` | rewritten_upstream | integration | failure_path | Applying and Rolling Back; Error Semantics | GOOSE-RUN-006 | covered |
| `integration::TestApplyVersionRejectsUnappliedDown` | rewritten_upstream | integration | failure_path | Applying and Rolling Back; Error Semantics | GOOSE-RUN-006 | covered |
| `integration::TestStatusAgreesWithAppliedSchema` | rewritten_upstream | integration | positive | Provider Construction and Status; State Model; Cross-View Invariants | GOOSE-PROV-007, GOOSE-INV-001 | covered |
| `integration::TestCustomVersionTableIsUsed` | rewritten_upstream | integration | positive | Provider Construction and Status; Cross-View Invariants | GOOSE-PROV-010, GOOSE-INV-001 | covered |
| `integration::TestDisableVersioningChangesSchemaWithoutHistory` | rewritten_upstream | integration | positive | Provider Construction and Status; State Model; Cross-View Invariants | GOOSE-PROV-013, GOOSE-INV-010 | covered |
| `integration::TestTransactionalFailureRollsBackSchemaAndVersion` | rewritten_upstream | integration | positive | Migration Sources and SQL Directives; Applying and Rolling Back; Error Semantics; Cross-View Invariants | GOOSE-SQL-003, GOOSE-RUN-011, GOOSE-INV-005 | covered |
| `integration::TestGoMigrationRunsTxCallback` | rewritten_upstream | integration | positive | Representative Workflows; Register a Go migration; Provider Construction and Status; Applying and Rolling Back; Cross-View Invariants | GOOSE-PROV-005, GOOSE-RUN-001, GOOSE-INV-012 | covered |
| `integration::TestPartialErrorReportsSuccessAndFailure` | rewritten_upstream | integration | positive | Applying and Rolling Back | GOOSE-RUN-011 | covered |
| `integration::TestEnvironmentSubstitutionWritesExpandedValue` | rewritten_upstream | integration | positive | Migration Sources and SQL Directives | GOOSE-SQL-004 | covered |
| `integration::TestApplyVersionRejectsAlreadyApplied` | rewritten_upstream | integration | failure_path | Applying and Rolling Back; Error Semantics | GOOSE-RUN-006 | covered |
| `integration::TestApplyVersionRollsBackExactSource` | rewritten_upstream | integration | positive | Applying and Rolling Back; Cross-View Invariants | GOOSE-RUN-006, GOOSE-INV-004 | covered |
| `integration::TestVersionsAgreeAfterUpTo` | rewritten_upstream | integration | positive | Provider Construction and Status; State Model; Cross-View Invariants | GOOSE-PROV-014, GOOSE-INV-003 | covered |
| `integration::TestCommittedStateSurvivesCloseAndReopen` | rewritten_upstream | integration | positive | Representative Workflows; Provider Construction and Status; State Model; Cross-View Invariants | GOOSE-PROV-015, GOOSE-INV-003 | covered |
| `integration::TestExclusionChangesEveryProjection` | rewritten_upstream | integration | positive | Provider Construction and Status; Cross-View Invariants | GOOSE-PROV-003, GOOSE-INV-008 | covered |
| `integration::TestOutOfOrderOptionAppliesMissingBeforeNew` | rewritten_upstream | integration | positive | Provider Construction and Status; State Model; Cross-View Invariants | GOOSE-PROV-004, GOOSE-PROV-012, GOOSE-INV-009 | covered |
| `integration::TestNoTransactionFailureKeepsDatabaseEffectWithoutVersion` | rewritten_upstream | integration | positive | Migration Sources and SQL Directives; Error Semantics; Cross-View Invariants | GOOSE-SQL-003, GOOSE-INV-005 | covered |
| `integration::TestMissingRequiredEnvironmentVariableLeavesVersionPending` | rewritten_upstream | integration | positive | Migration Sources and SQL Directives; Error Semantics; Cross-View Invariants | GOOSE-SQL-004, GOOSE-INV-005 | covered |
| `integration::TestCLIHelpExitsSuccessfully` | generated | system_e2e | positive | Command-Line Behavior | GOOSE-CLI-003 | covered |
| `integration::TestCLIVersionExitsSuccessfully` | generated | system_e2e | positive | Command-Line Behavior | GOOSE-CLI-003 | covered |
| `integration::TestCLIUnknownCommandExitsNonZero` | generated | system_e2e | failure_path | Command-Line Behavior; Error Semantics | GOOSE-CLI-002, GOOSE-CLI-008 | covered |
| `integration::TestCLIUpIsVisibleThroughLibraryProvider` | generated | system_e2e | positive | Representative Workflows; Move the same database through the CLI; Command-Line Behavior; State Model; Cross-View Invariants | GOOSE-RUN-001, GOOSE-CLI-003, GOOSE-INV-001, GOOSE-INV-005, GOOSE-INV-006 | covered |
| `integration::TestLibraryUpIsVisibleThroughCLIStatusAndVersion` | generated | system_e2e | positive | Representative Workflows; Command-Line Behavior; State Model; Cross-View Invariants | GOOSE-RUN-001, GOOSE-CLI-003, GOOSE-INV-004, GOOSE-INV-006 | covered |
| `integration::TestCLIUsesEnvironmentConfiguration` | generated | system_e2e | positive | Command-Line Behavior; State Model; Cross-View Invariants | GOOSE-CLI-001, GOOSE-CLI-005, GOOSE-INV-005 | covered |
| `integration::TestCLICreateSequentialSQLFile` | generated | system_e2e | positive | File Maintenance and Go Registration; Command-Line Behavior | GOOSE-FILE-003, GOOSE-FILE-004, GOOSE-CLI-003 | covered |
| `integration::TestCLIValidateAcceptsValidAndRejectsInvalidWithoutMutation` | generated | system_e2e | failure_path | File Maintenance and Go Registration; Command-Line Behavior; Error Semantics | GOOSE-CLI-002, GOOSE-CLI-003, GOOSE-CLI-007, GOOSE-CLI-008 | covered |

Total: 68 | kept (covered): 68 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 68

Layer counts: atomic 30 | integration 30 | system_e2e 8.  
Assertion composition: atomic positive 29/30 and failure_path 1/30; integration positive 25/30 and failure_path 5/30; system_e2e positive 6/8 and failure_path 2/8; no_check 0.  
Dummy gate: 0/68 passed. Reference gate: 68/68 passed.

GoRunner currently has no Go dependency-annotation parser, so adjusted integration gap dependency data is unavailable at construction time; the raw atomic/integration split remains fully defined.
