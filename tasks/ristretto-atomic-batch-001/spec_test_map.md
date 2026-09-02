# Spec-Test Map

oracle_version: 2026-08-31T04:00:00+08:00
oracle_source: generated_only
atomic_count: 32
integration_count: 40
total_count: 72

| test_id | source | status | clauses | layer | seam | depends_on | assertion surface |
|---|---|---|---|---|---|---|---|
| atomic::TestEmptyBatchSucceeds | generated | covered | RAB-BATCH-001 | atomic | single API behavior | - | public result, value, state, callback, metric, or capacity |
| atomic::TestNilCacheRejectsNonEmptyBatch | generated | covered | RAB-ERR-001 | atomic | single API behavior | - | public result, value, state, callback, metric, or capacity |
| atomic::TestClosedCacheRejectsBatch | generated | covered | RAB-ERR-001 | atomic | single API behavior | - | public result, value, state, callback, metric, or capacity |
| atomic::TestInvalidOperationIsReported | generated | covered | RAB-ERR-002 | atomic | single API behavior | - | public result, value, state, callback, metric, or capacity |
| atomic::TestInvalidGuardIsReported | generated | covered | RAB-ERR-003 | atomic | single API behavior | - | public result, value, state, callback, metric, or capacity |
| atomic::TestNegativeTTLIsRejected | generated | covered | RAB-ERR-004 | atomic | single API behavior | - | public result, value, state, callback, metric, or capacity |
| atomic::TestNegativeCostIsRejected | generated | covered | RAB-ERR-005 | atomic | single API behavior | - | public result, value, state, callback, metric, or capacity |
| atomic::TestRequireAbsentAllowsInsertion | generated | covered | RAB-GUARD-001 | atomic | single API behavior | - | public result, value, state, callback, metric, or capacity |
| atomic::TestRequireAbsentRejectsExistingKey | generated | covered | RAB-GUARD-001, RAB-BATCH-004 | atomic | single API behavior | - | public result, value, state, callback, metric, or capacity |
| atomic::TestRequirePresentAllowsReplacement | generated | covered | RAB-GUARD-002 | atomic | single API behavior | - | public result, value, state, callback, metric, or capacity |
| atomic::TestRequirePresentRejectsMissingKey | generated | covered | RAB-GUARD-002 | atomic | single API behavior | - | public result, value, state, callback, metric, or capacity |
| atomic::TestDeleteMissingWithAnyIsSuccessfulNoOp | generated | covered | RAB-BATCH-002 | atomic | single API behavior | - | public result, value, state, callback, metric, or capacity |
| atomic::TestDeleteExistingRemovesValue | generated | covered | RAB-BATCH-002 | atomic | single API behavior | - | public result, value, state, callback, metric, or capacity |
| atomic::TestRepeatedSetUsesLastValue | generated | covered | RAB-ORDER-001, RAB-BATCH-003 | atomic | single API behavior | - | public result, value, state, callback, metric, or capacity |
| atomic::TestSetThenDeleteLeavesKeyAbsent | generated | covered | RAB-ORDER-001 | atomic | single API behavior | - | public result, value, state, callback, metric, or capacity |
| atomic::TestDeleteThenSetObservesVirtualAbsence | generated | covered | RAB-ORDER-001, RAB-GUARD-001 | atomic | single API behavior | - | public result, value, state, callback, metric, or capacity |
| atomic::TestFailureIdentifiesFirstInvalidItem | generated | covered | RAB-RESULT-001 | atomic | single API behavior | - | public result, value, state, callback, metric, or capacity |
| atomic::TestValidationFailureRollsBackEarlierItems | generated | covered | RAB-BATCH-004 | atomic | single API behavior | - | public result, value, state, callback, metric, or capacity |
| atomic::TestDynamicCostIsEvaluated | generated | covered | RAB-COST-001 | atomic | single API behavior | - | public result, value, state, callback, metric, or capacity |
| atomic::TestShouldUpdateAllowsSequentialReplacement | generated | covered | RAB-UPDATE-001 | atomic | single API behavior | - | public result, value, state, callback, metric, or capacity |
| atomic::TestShouldUpdateRejectsWholeBatch | generated | covered | RAB-UPDATE-001, RAB-BATCH-004 | atomic | single API behavior | - | public result, value, state, callback, metric, or capacity |
| atomic::TestBatchMayFillCapacityExactly | generated | covered | RAB-CAP-001 | atomic | single API behavior | - | public result, value, state, callback, metric, or capacity |
| atomic::TestCapacityOverflowRejectsWholeBatch | generated | covered | RAB-CAP-001, RAB-BATCH-004 | atomic | single API behavior | - | public result, value, state, callback, metric, or capacity |
| atomic::TestReplacementUsesNetCostDelta | generated | covered | RAB-CAP-002 | atomic | single API behavior | - | public result, value, state, callback, metric, or capacity |
| atomic::TestDeleteFreesCapacityForLaterItem | generated | covered | RAB-CAP-002, RAB-ORDER-001 | atomic | single API behavior | - | public result, value, state, callback, metric, or capacity |
| atomic::TestPositiveTTLSetsExpiringEntry | generated | covered | RAB-TTL-001 | atomic | single API behavior | - | public result, value, state, callback, metric, or capacity |
| atomic::TestZeroTTLCreatesPermanentEntry | generated | covered | RAB-TTL-001 | atomic | single API behavior | - | public result, value, state, callback, metric, or capacity |
| atomic::TestGetManyPreservesInputOrder | generated | covered | RAB-SNAP-001 | atomic | single API behavior | - | public result, value, state, callback, metric, or capacity |
| atomic::TestGetManyPreservesDuplicatePositions | generated | covered | RAB-SNAP-001 | atomic | single API behavior | - | public result, value, state, callback, metric, or capacity |
| atomic::TestGetManyReportsRemainingTTL | generated | covered | RAB-SNAP-002 | atomic | single API behavior | - | public result, value, state, callback, metric, or capacity |
| atomic::TestGetManyPermanentAndMissingTTLAreZero | generated | covered | RAB-SNAP-002 | atomic | single API behavior | - | public result, value, state, callback, metric, or capacity |
| atomic::TestHashConflictRejectsBatch | generated | covered | RAB-HASH-001, RAB-BATCH-004 | atomic | single API behavior | - | public result, value, state, callback, metric, or capacity |
| integration::TestMixedCommitAppearsThroughOrdinaryGets | generated | covered | RAB-BATCH-003, RAB-CVI-001 | integration | config interaction | TestDeleteExistingRemovesValue, TestRequireAbsentAllowsInsertion | public result, value, state, callback, metric, or capacity |
| integration::TestAcceptedSetBeforeBatchIsDrainedFirst | generated | covered | RAB-BATCH-005, RAB-CVI-001 | integration | lifecycle crossing | TestRequirePresentAllowsReplacement | public result, value, state, callback, metric, or capacity |
| integration::TestOrdinarySetAfterBatchUsesCommittedState | generated | covered | RAB-BATCH-005, RAB-CVI-001 | integration | config interaction | TestRepeatedSetUsesLastValue | public result, value, state, callback, metric, or capacity |
| integration::TestSnapshotMatchesCommittedMultiKeyState | generated | covered | RAB-SNAP-001, RAB-CVI-002 | integration | config interaction | TestGetManyPreservesInputOrder, TestRepeatedSetUsesLastValue | public result, value, state, callback, metric, or capacity |
| integration::TestIterationMatchesBatchFinalState | generated | covered | RAB-BATCH-003, RAB-CVI-003 | integration | config interaction | TestDeleteExistingRemovesValue, TestRepeatedSetUsesLastValue | public result, value, state, callback, metric, or capacity |
| integration::TestRemainingCostTracksMixedBatch | generated | covered | RAB-CAP-002, RAB-CVI-004 | integration | config interaction | TestReplacementUsesNetCostDelta, TestDeleteFreesCapacityForLaterItem | public result, value, state, callback, metric, or capacity |
| integration::TestTTLViewsAgreeAfterCommit | generated | covered | RAB-TTL-001, RAB-CVI-005 | integration | config interaction | TestPositiveTTLSetsExpiringEntry, TestGetManyReportsRemainingTTL | public result, value, state, callback, metric, or capacity |
| integration::TestReplacementCallsOnExitOnce | generated | covered | RAB-CALLBACK-001, RAB-CVI-006 | integration | state consistency | TestRequirePresentAllowsReplacement | public result, value, state, callback, metric, or capacity |
| integration::TestDeleteCallsOnExitOnce | generated | covered | RAB-CALLBACK-001, RAB-CVI-006 | integration | state consistency | TestDeleteExistingRemovesValue | public result, value, state, callback, metric, or capacity |
| integration::TestGuardFailureProducesNoBatchCallbacks | generated | covered | RAB-CALLBACK-002, RAB-BATCH-004 | integration | config interaction | TestValidationFailureRollsBackEarlierItems | public result, value, state, callback, metric, or capacity |
| integration::TestCapacityFailureProducesNoCallbacks | generated | covered | RAB-CALLBACK-002, RAB-CAP-001 | integration | config interaction | TestCapacityOverflowRejectsWholeBatch | public result, value, state, callback, metric, or capacity |
| integration::TestRepeatedReplacementExitsOnlyOriginalValue | generated | covered | RAB-ORDER-002, RAB-CALLBACK-001 | integration | config interaction | TestRepeatedSetUsesLastValue | public result, value, state, callback, metric, or capacity |
| integration::TestNewThenDeletedKeyProducesNoExit | generated | covered | RAB-ORDER-002, RAB-CALLBACK-001 | integration | config interaction | TestSetThenDeleteLeavesKeyAbsent | public result, value, state, callback, metric, or capacity |
| integration::TestDeleteThenSetExitsOriginalOnce | generated | covered | RAB-ORDER-002, RAB-CALLBACK-001 | integration | config interaction | TestDeleteThenSetObservesVirtualAbsence | public result, value, state, callback, metric, or capacity |
| integration::TestMetricsCountCommittedNewKeys | generated | covered | RAB-METRIC-001, RAB-CVI-007 | integration | config interaction | TestRequireAbsentAllowsInsertion | public result, value, state, callback, metric, or capacity |
| integration::TestMetricsCountCommittedUpdates | generated | covered | RAB-METRIC-001, RAB-CVI-007 | integration | config interaction | TestRequirePresentAllowsReplacement | public result, value, state, callback, metric, or capacity |
| integration::TestSnapshotContributesHitAndMissMetrics | generated | covered | RAB-METRIC-002, RAB-SNAP-001 | integration | config interaction | TestGetManyPreservesInputOrder | public result, value, state, callback, metric, or capacity |
| integration::TestRejectedBatchDoesNotCountWrites | generated | covered | RAB-METRIC-001, RAB-BATCH-004 | integration | config interaction | TestCapacityOverflowRejectsWholeBatch | public result, value, state, callback, metric, or capacity |
| integration::TestExpiredValueIsMissingFromBothReadViews | generated | covered | RAB-TTL-002, RAB-CVI-005 | integration | config interaction | TestPositiveTTLSetsExpiringEntry, TestGetManyReportsRemainingTTL | public result, value, state, callback, metric, or capacity |
| integration::TestExpiredKeySatisfiesAbsentGuard | generated | covered | RAB-TTL-002, RAB-GUARD-001 | integration | lifecycle crossing | TestRequireAbsentAllowsInsertion, TestPositiveTTLSetsExpiringEntry | public result, value, state, callback, metric, or capacity |
| integration::TestExpiredKeyFailsPresentGuardWithoutReplacement | generated | covered | RAB-TTL-002, RAB-GUARD-002 | integration | lifecycle crossing | TestRequirePresentRejectsMissingKey, TestPositiveTTLSetsExpiringEntry | public result, value, state, callback, metric, or capacity |
| integration::TestZeroValueRemainsDistinguishableFromMissing | generated | covered | RAB-SNAP-001, RAB-CVI-002 | integration | config interaction | TestGetManyPreservesInputOrder | public result, value, state, callback, metric, or capacity |
| integration::TestCustomHashDistinctPrimariesCommitNormally | generated | covered | RAB-HASH-001, RAB-CVI-001 | integration | config interaction | TestHashConflictRejectsBatch | public result, value, state, callback, metric, or capacity |
| integration::TestHashConflictInLaterItemRollsBackEarlierItem | generated | covered | RAB-HASH-001, RAB-BATCH-004 | integration | config interaction | TestHashConflictRejectsBatch, TestValidationFailureRollsBackEarlierItems | public result, value, state, callback, metric, or capacity |
| integration::TestConcurrentSnapshotsNeverSeePartialCommit | generated | covered | RAB-ATOMIC-001, RAB-SNAP-001 | integration | config interaction | TestGetManyPreservesInputOrder, TestDeleteExistingRemovesValue | public result, value, state, callback, metric, or capacity |
| integration::TestConcurrentDisjointBatchesAllCommit | generated | covered | RAB-ATOMIC-002 | integration | config interaction | TestRequireAbsentAllowsInsertion | public result, value, state, callback, metric, or capacity |
| integration::TestOrdinarySetWaitsForOpenBatchBoundary | generated | covered | RAB-ATOMIC-001, RAB-BATCH-005 | integration | config interaction | TestDynamicCostIsEvaluated, TestAcceptedSetBeforeBatchIsDrainedFirst | public result, value, state, callback, metric, or capacity |
| integration::TestShouldUpdateSeesPriorVirtualValue | generated | covered | RAB-UPDATE-001, RAB-ORDER-001 | integration | config interaction | TestShouldUpdateAllowsSequentialReplacement, TestRepeatedSetUsesLastValue | public result, value, state, callback, metric, or capacity |
| integration::TestVirtualUpdateRejectionRestoresOriginal | generated | covered | RAB-UPDATE-001, RAB-BATCH-004 | integration | config interaction | TestShouldUpdateRejectsWholeBatch, TestRepeatedSetUsesLastValue | public result, value, state, callback, metric, or capacity |
| integration::TestCapacityUsesAllFinalPerKeyEffects | generated | covered | RAB-CAP-002, RAB-ORDER-001 | integration | config interaction | TestDeleteFreesCapacityForLaterItem, TestReplacementUsesNetCostDelta | public result, value, state, callback, metric, or capacity |
| integration::TestEffectsCountsDistinctTouchedHashes | generated | covered | RAB-RESULT-002, RAB-ORDER-002 | integration | config interaction | TestRepeatedSetUsesLastValue | public result, value, state, callback, metric, or capacity |
| integration::TestSuccessfulResultClearsFailureFields | generated | covered | RAB-RESULT-001, RAB-RESULT-002 | integration | config interaction | TestEmptyBatchSucceeds | public result, value, state, callback, metric, or capacity |
| integration::TestClosedSnapshotPreservesRequestedShape | generated | covered | RAB-SNAP-003 | integration | lifecycle crossing | TestGetManyPreservesInputOrder | public result, value, state, callback, metric, or capacity |
| integration::TestNilSnapshotPreservesRequestedShape | generated | covered | RAB-SNAP-003 | integration | lifecycle crossing | TestGetManyPreservesInputOrder | public result, value, state, callback, metric, or capacity |
| integration::TestBatchSupportsNonStringKeyType | generated | covered | RAB-API-001, RAB-CVI-001 | integration | config interaction | TestRequireAbsentAllowsInsertion | public result, value, state, callback, metric, or capacity |
| integration::TestLargeBatchCommitsAsSingleCapacityDecision | generated | covered | RAB-ATOMIC-001, RAB-CAP-001 | integration | config interaction | TestBatchMayFillCapacityExactly, TestRequireAbsentAllowsInsertion | public result, value, state, callback, metric, or capacity |
| integration::TestRejectedReplacementLeavesCapacityAndValueUnchanged | generated | covered | RAB-BATCH-004, RAB-CVI-004 | integration | config interaction | TestCapacityOverflowRejectsWholeBatch, TestReplacementUsesNetCostDelta | public result, value, state, callback, metric, or capacity |
| integration::TestLaterGuardFailureRestoresMultipleOriginalKeys | generated | covered | RAB-GUARD-001, RAB-ORDER-001, RAB-BATCH-004 | integration | config interaction | TestDeleteThenSetObservesVirtualAbsence, TestValidationFailureRollsBackEarlierItems | public result, value, state, callback, metric, or capacity |
| integration::TestLastRepeatedSetDeterminesTTL | generated | covered | RAB-TTL-001, RAB-ORDER-001 | integration | config interaction | TestPositiveTTLSetsExpiringEntry, TestRepeatedSetUsesLastValue | public result, value, state, callback, metric, or capacity |
| integration::TestRepeatedSnapshotKeysCountIndependently | generated | covered | RAB-SNAP-001, RAB-METRIC-002 | integration | config interaction | TestGetManyPreservesDuplicatePositions, TestSnapshotContributesHitAndMissMetrics | public result, value, state, callback, metric, or capacity |
