# Spec-test map — nutsdb spec v1

Oracle version: 2026-08-21T00:00:00+08:00
Oracle source: generated_only

| test_nodeid | source | layer | assertion_kind | spec_section | status | notes |
|---|---|---|---|---|---|---|
| `atomic::TestOpenCreatesUsableDatabase` | generated | atomic | positive | Database Lifecycle and Transactions | covered | Verifies NUTS-DB-001, NUTS-DB-002 |
| `atomic::TestOpenRejectsLockedDirectory` | generated | atomic | failure_path | Error Semantics | covered | Verifies NUTS-DB-003 |
| `atomic::TestCloseChangesLifecycleState` | generated | atomic | positive | Database Lifecycle and Transactions | covered | Verifies NUTS-DB-004 |
| `atomic::TestSecondCloseReturnsSentinel` | generated | atomic | failure_path | Database Lifecycle and Transactions | covered | Verifies NUTS-DB-005 |
| `atomic::TestManagedTransactionsRejectNilCallback` | generated | atomic | failure_path | Error Semantics | covered | Verifies NUTS-DB-008 |
| `atomic::TestViewReadsAndRejectsWrites` | generated | atomic | positive | Database Lifecycle and Transactions | covered | Verifies NUTS-DB-009, NUTS-DB-010 |
| `atomic::TestTypedBucketConvenienceConstructors` | generated | atomic | positive | Public Interface | covered | Verifies NUTS-BKT-001, NUTS-BKT-002 |
| `atomic::TestDuplicateBucketReturnsSentinel` | generated | atomic | failure_path | Buckets, Key/Value Data, and Ordered Reads | covered | Verifies NUTS-BKT-003 |
| `atomic::TestDeleteBucketRemovesExistence` | generated | atomic | positive | Buckets, Key/Value Data, and Ordered Reads | covered | Verifies NUTS-BKT-004 |
| `atomic::TestPutGetRoundTrip` | generated | atomic | positive | Buckets, Key/Value Data, and Ordered Reads | covered | Verifies NUTS-KV-001 |
| `atomic::TestDeleteUpdatesHasAndGet` | generated | atomic | positive | Buckets, Key/Value Data, and Ordered Reads | covered | Verifies NUTS-KV-002 |
| `atomic::TestEmptyKeyReturnsSentinel` | generated | atomic | failure_path | Error Semantics | covered | Verifies NUTS-KV-003 |
| `atomic::TestMissingBucketUsesDirectEntrySentinel` | generated | atomic | failure_path | Buckets, Key/Value Data, and Ordered Reads | covered | Verifies NUTS-KV-004 |
| `atomic::TestPutIfNotExistsPreservesExistingValue` | generated | atomic | positive | Buckets, Key/Value Data, and Ordered Reads | covered | Verifies NUTS-KV-005 |
| `atomic::TestPutIfExistsRejectsMissingKey` | generated | atomic | failure_path | Buckets, Key/Value Data, and Ordered Reads | covered | Verifies NUTS-KV-006 |
| `atomic::TestMSetMGetPreservesRequestOrder` | generated | atomic | positive | Buckets, Key/Value Data, and Ordered Reads | covered | Verifies NUTS-KV-007, NUTS-KV-009 |
| `atomic::TestMSetOddArgumentsIsAtomicFailure` | generated | atomic | failure_path | Error Semantics | covered | Verifies NUTS-KV-008 |
| `atomic::TestGetSetReturnsPreviousValue` | generated | atomic | positive | Buckets, Key/Value Data, and Ordered Reads | covered | Verifies NUTS-KV-010 |
| `atomic::TestAppendAndValueLenAgree` | generated | atomic | positive | Buckets, Key/Value Data, and Ordered Reads | covered | Verifies NUTS-KV-011 |
| `atomic::TestGetAllKeysValuesShareSortedProjection` | generated | atomic | positive | Buckets, Key/Value Data, and Ordered Reads | covered | Verifies NUTS-KV-012 |
| `atomic::TestMinMaxKeysUseByteOrder` | generated | atomic | positive | Buckets, Key/Value Data, and Ordered Reads | covered | Verifies NUTS-KV-013 |
| `atomic::TestPrefixScanAppliesOffsetAndLimit` | generated | atomic | positive | Buckets, Key/Value Data, and Ordered Reads | covered | Verifies NUTS-SCN-001 |
| `atomic::TestPrefixSearchFiltersSuffix` | generated | atomic | positive | Buckets, Key/Value Data, and Ordered Reads | covered | Verifies NUTS-SCN-002 |
| `atomic::TestRangeScanUsesClosedInterval` | generated | atomic | positive | Buckets, Key/Value Data, and Ordered Reads | covered | Verifies NUTS-SCN-003 |
| `atomic::TestEmptyScansReturnSentinels` | generated | atomic | failure_path | Buckets, Key/Value Data, and Ordered Reads | covered | Verifies NUTS-SCN-004 |
| `atomic::TestIteratorForwardAndReverseOrder` | generated | atomic | positive | Buckets, Key/Value Data, and Ordered Reads | covered | Verifies NUTS-ITR-001, NUTS-ITR-002 |
| `atomic::TestIteratorSeekRewindAndRelease` | generated | atomic | positive | Buckets, Key/Value Data, and Ordered Reads | covered | Verifies NUTS-ITR-003, NUTS-ITR-004, NUTS-ITR-005 |
| `atomic::TestPersistentTTLIsMinusOne` | generated | atomic | positive | Buckets, Key/Value Data, and Ordered Reads | covered | Verifies NUTS-TTL-001 |
| `atomic::TestPersistCancelsExpiration` | generated | atomic | positive | Buckets, Key/Value Data, and Ordered Reads | covered | Verifies NUTS-TTL-002, NUTS-TTL-003 |
| `atomic::TestListPushAndRangeOrder` | generated | atomic | positive | Lists, Sets, and Sorted Sets | covered | Verifies NUTS-LST-001 |
| `atomic::TestSetUniquenessAndMembership` | generated | atomic | positive | Lists, Sets, and Sorted Sets | covered | Verifies NUTS-SET-001, NUTS-SET-002 |
| `atomic::TestSortedSetScoreAndCardinality` | generated | atomic | positive | Lists, Sets, and Sorted Sets | covered | Verifies NUTS-ZST-001, NUTS-ZST-002 |
| `atomic::TestSortedSetRanksAreOneBased` | generated | atomic | positive | Lists, Sets, and Sorted Sets | covered | Verifies NUTS-ZST-003 |
| `atomic::TestPublicErrorClassifiers` | generated | atomic | positive | Public Interface | covered | Verifies NUTS-KV-004 |
| `integration::TestManagedUpdateCommitsAllChanges` | generated | integration | positive | Representative Workflows | covered | Verifies NUTS-DB-006, NUTS-KV-001 |
| `integration::TestManagedUpdateErrorRollsBackBucketAndEntries` | generated | integration | positive | Database Lifecycle and Transactions | covered | Verifies NUTS-DB-007, NUTS-BKT-001, NUTS-KV-001 |
| `integration::TestManualCommitPublishesStagedState` | generated | integration | positive | State Model | covered | Verifies NUTS-DB-011 |
| `integration::TestManualRollbackDiscardsStagedState` | generated | integration | positive | State Model | covered | Verifies NUTS-DB-011 |
| `integration::TestManualReadTransactionClosesWithoutMutation` | generated | integration | positive | Database Lifecycle and Transactions | covered | Verifies NUTS-DB-012, NUTS-DB-013 |
| `integration::TestTypedBucketsAreEnumerableByKind` | generated | integration | positive | Buckets, Key/Value Data, and Ordered Reads | covered | Verifies NUTS-BKT-002, NUTS-BKT-005 |
| `integration::TestCommittedKVSurvivesCloseAndReopen` | generated | system_e2e | positive | Representative Workflows | covered | Verifies NUTS-DUR-001, NUTS-KV-001 |
| `integration::TestUnexpiredTTLStateSurvivesReopenThenExpires` | generated | system_e2e | positive | Buckets, Key/Value Data, and Ordered Reads | covered | Verifies NUTS-TTL-002, NUTS-DUR-001 |
| `integration::TestListPeekPopAndSizeAgree` | generated | integration | positive | Lists, Sets, and Sorted Sets | covered | Verifies NUTS-LST-002, NUTS-LST-003 |
| `integration::TestListTrimAndRemoveCompose` | generated | integration | positive | Lists, Sets, and Sorted Sets | covered | Verifies NUTS-LST-004, NUTS-LST-005 |
| `integration::TestListImplementationsExposeEquivalentResults` | generated | integration | positive | Public Interface | covered | Verifies NUTS-LST-006, NUTS-DUR-001 |
| `integration::TestSetUnionDifferenceAndRemovalAgree` | generated | integration | positive | Lists, Sets, and Sorted Sets | covered | Verifies NUTS-SET-003, NUTS-SET-004 |
| `integration::TestSetMoveChangesBothViewsAtomically` | generated | integration | positive | Lists, Sets, and Sorted Sets | covered | Verifies NUTS-SET-005 |
| `integration::TestSortedSetRangeByRankReturnsMembersAndScores` | generated | integration | positive | Lists, Sets, and Sorted Sets | covered | Verifies NUTS-ZST-004 |
| `integration::TestSortedSetScoreRangeOptionsControlEndpointsAndLimit` | generated | integration | positive | Lists, Sets, and Sorted Sets | covered | Verifies NUTS-ZST-005, NUTS-ZST-006 |
| `integration::TestSortedSetPeekPopAndRemoveStayConsistent` | generated | integration | positive | Lists, Sets, and Sorted Sets | covered | Verifies NUTS-ZST-007, NUTS-ZST-008 |
| `integration::TestMixedCollectionsSurviveReopen` | generated | system_e2e | positive | Representative Workflows | covered | Verifies NUTS-DUR-001, NUTS-LST-001, NUTS-SET-002, NUTS-ZST-001 |
| `integration::TestBackupOpensWithCommittedKVState` | generated | system_e2e | positive | Durability, Backup, Merge, and Watch Events | covered | Verifies NUTS-DUR-002 |
| `integration::TestBackupPreservesCollectionState` | generated | system_e2e | positive | Durability, Backup, Merge, and Watch Events | covered | Verifies NUTS-DUR-002, NUTS-LST-001, NUTS-SET-002 |
| `integration::TestMergeWithTooFewSegmentsReturnsSentinel` | generated | integration | failure_path | Durability, Backup, Merge, and Watch Events | covered | Verifies NUTS-DUR-003 |
| `integration::TestMergePreservesLiveAndDeletedState` | generated | system_e2e | positive | Cross-View Invariants | covered | Verifies NUTS-DUR-004 |
| `integration::TestMergedStateSurvivesReopen` | generated | system_e2e | positive | Durability, Backup, Merge, and Watch Events | covered | Verifies NUTS-DUR-001, NUTS-DUR-004 |
| `integration::TestWatchDisabledReturnsSentinel` | generated | integration | failure_path | Error Semantics | covered | Verifies NUTS-WCH-001 |
| `integration::TestCommittedSetProducesMatchingWatchMessage` | generated | system_e2e | positive | Representative Workflows | covered | Verifies NUTS-WCH-002, NUTS-WCH-004 |
| `integration::TestCommittedDeleteProducesMatchingWatchMessage` | generated | system_e2e | positive | Cross-View Invariants | covered | Verifies NUTS-WCH-002, NUTS-WCH-005 |
| `integration::TestRolledBackWriteProducesNoWatchMessage` | generated | system_e2e | positive | Durability, Backup, Merge, and Watch Events | covered | Verifies NUTS-WCH-003 |
| `integration::TestWatchReturnsCallbackError` | generated | integration | positive | Durability, Backup, Merge, and Watch Events | covered | Verifies NUTS-WCH-007 |
| `integration::TestWatchCallbackTimeoutReturnsSentinel` | generated | integration | positive | Durability, Backup, Merge, and Watch Events | covered | Verifies NUTS-WCH-006 |
| `integration::TestCloseFinishesActiveWatch` | generated | integration | positive | Durability, Backup, Merge, and Watch Events | covered | Verifies NUTS-WCH-008 |
| `integration::TestKVDirectBulkScanAndIteratorViewsAgree` | generated | integration | positive | Cross-View Invariants | covered | Verifies NUTS-KV-001, NUTS-KV-012, NUTS-SCN-001, NUTS-ITR-002 |
| `integration::TestCollectionChangesRollbackTogether` | generated | system_e2e | positive | State Model | covered | Verifies NUTS-DB-007, NUTS-LST-001, NUTS-SET-001, NUTS-ZST-001 |
| `integration::TestDeletedBucketRemainsAbsentAfterReopen` | generated | system_e2e | positive | Cross-View Invariants | covered | Verifies NUTS-BKT-004, NUTS-DUR-001 |
| `integration::TestBackupIsIndependentFromLaterSourceWrites` | generated | system_e2e | positive | Cross-View Invariants | covered | Verifies NUTS-DUR-002, NUTS-KV-001 |

Total: 67 | kept (covered): 67 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 67
Layer counts: atomic 34 | integration+system_e2e 33
