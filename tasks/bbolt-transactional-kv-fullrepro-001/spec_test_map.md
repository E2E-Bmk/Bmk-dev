# Spec-to-test map

| Clause | Test node | Layer | Source |
| --- | --- | --- | --- |
| BOLT-001 | `atomic::TestOpenCreatesDatabaseAndReportsPath` | atomic | generated |
| BOLT-002 | `atomic::TestCloseTwiceSucceeds` | atomic | generated |
| BOLT-002 | `atomic::TestClosedDatabaseRejectsView` | atomic | generated |
| BOLT-003 | `atomic::TestConflictingOpenTimesOut` | atomic | generated |
| BOLT-004 | `atomic::TestReadOnlyDatabaseRejectsWriter` | atomic | generated |
| BOLT-005 | `atomic::TestSyncOpenDatabase` | atomic | generated |
| BOLT-006 | `atomic::TestUpdateCommits` | atomic | generated |
| BOLT-006, BOLT-061 | `atomic::TestUpdateErrorRollsBackAndPropagates` | atomic | generated |
| BOLT-007 | `atomic::TestViewIsReadOnly` | atomic | generated |
| BOLT-008 | `atomic::TestManualCommit` | atomic | generated |
| BOLT-009 | `atomic::TestManualRollback` | atomic | generated |
| BOLT-010 | `atomic::TestTransactionClosedSentinel` | atomic | generated |
| BOLT-011, BOLT-063 | `atomic::TestTransactionProperties` | atomic | generated |
| BOLT-012 | `atomic::TestWritableTransactionIDsIncrease` | atomic | generated |
| BOLT-013 | `atomic::TestOnCommitTiming` | atomic | generated |
| BOLT-015 | `atomic::TestCreateBucketDuplicate` | atomic | generated |
| BOLT-016 | `atomic::TestCreateBucketIfNotExistsReuses` | atomic | generated |
| BOLT-017 | `atomic::TestBlankBucketNameRejected` | atomic | generated |
| BOLT-018, BOLT-019 | `atomic::TestDeleteBucketLifecycle` | atomic | generated |
| BOLT-020 | `atomic::TestTopLevelBucketEnumeration` | atomic | generated |
| BOLT-021, BOLT-022 | `atomic::TestNestedBucketEnumeration` | atomic | generated |
| BOLT-023 | `atomic::TestBucketOwnerProperties` | atomic | generated |
| BOLT-024 | `atomic::TestValueBucketCollision` | atomic | generated |
| BOLT-025 | `atomic::TestPutGetReplace` | atomic | generated |
| BOLT-026 | `atomic::TestEmptyKeyRejected` | atomic | generated |
| BOLT-027 | `atomic::TestEmptyValueDistinctFromMissing` | atomic | generated |
| BOLT-028 | `atomic::TestDeleteValueAndAbsent` | atomic | generated |
| BOLT-032, BOLT-033 | `atomic::TestCursorBoundariesAndMovement` | atomic | generated |
| BOLT-034 | `atomic::TestCursorSeek` | atomic | generated |
| BOLT-036 | `atomic::TestCursorDeleteValue` | atomic | generated |
| BOLT-038 | `atomic::TestForEachOrderedAndError` | atomic | generated |
| BOLT-041 | `atomic::TestBucketSequence` | atomic | generated |
| BOLT-052 | `atomic::TestBucketStatsRelationships` | atomic | generated |
| BOLT-050 | `integration::TestCommittedValueSurvivesReopen` | integration | generated |
| BOLT-051, BOLT-062 | `integration::TestRolledBackValueAbsentAfterReopen` | integration | generated |
| BOLT-031 | `integration::TestRollbackAcrossBuckets` | integration | generated |
| BOLT-055 | `integration::TestGetForEachCursorAgree` | integration | generated |
| BOLT-056 | `integration::TestManagedAndManualCommitEquivalent` | integration | generated |
| BOLT-039 | `integration::TestNestedHierarchySurvivesReopen` | integration | generated |
| BOLT-040 | `integration::TestDeleteParentRemovesDescendants` | integration | generated |
| BOLT-042 | `integration::TestSequenceRollbackAndCommit` | integration | generated |
| BOLT-043, BOLT-057 | `integration::TestSequenceIterationStatsAfterReopen` | integration | generated |
| BOLT-044, BOLT-045 | `integration::TestReadSnapshotStableAcrossCommit` | integration | generated |
| BOLT-046 | `integration::TestUncommittedWriterInvisible` | integration | generated |
| BOLT-047 | `integration::TestWriteToProducesReopenableSnapshot` | integration | generated |
| BOLT-048 | `integration::TestCopyFileProducesReopenableSnapshot` | integration | generated |
| BOLT-049, BOLT-058 | `integration::TestBackupIndependentFromLaterWrites` | integration | generated |
| BOLT-013 | `integration::TestOnCommitObservesDurableState` | integration | generated |
| BOLT-014 | `integration::TestBatchCommitsState` | integration | generated |
| BOLT-029 | `integration::TestReadonlyMutationFamilies` | integration | generated |
| BOLT-035 | `integration::TestCursorDistinguishesNestedBucket` | integration | generated |
| BOLT-037 | `integration::TestCursorDeleteErrorModes` | integration | generated |
| BOLT-053 | `integration::TestDatabaseReadTransactionStats` | integration | generated |
| BOLT-054 | `integration::TestStatsSubTransactionDelta` | integration | generated |
| BOLT-059 | `integration::TestConcurrentReadersAgree` | integration | generated |
| BOLT-060 | `integration::TestCoordinatedWriterPreservesReader` | integration | generated |
| BOLT-030 | `integration::TestStagedViewsAgreeBeforeCommit` | integration | generated |
| BOLT-024 | `integration::TestBucketValueCollisionBothDirections` | integration | generated |
| BOLT-038 | `integration::TestNestedEntryIncludedInForEach` | integration | generated |
| BOLT-064 | `integration::TestTransactionCursorTraversesTopBuckets` | integration | generated |
| BOLT-065 | `integration::TestReadonlyCommitClosesWithoutMutation` | integration | generated |
| BOLT-047 | `integration::TestCopyMethodWritesSnapshot` | integration | generated |
| BOLT-052 | `integration::TestNestedStatsMatchHierarchy` | integration | generated |
| BOLT-004, BOLT-050 | `integration::TestReadOnlyReopenReadsNestedState` | integration | generated |
| BOLT-061, BOLT-062 | `integration::TestViewCallbackErrorDoesNotChangeState` | integration | generated |
