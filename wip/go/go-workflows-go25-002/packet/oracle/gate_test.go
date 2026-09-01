package workflowsgate_test

import "testing"

func TestGoWorkflowsAtomicDeterministicWorkflowResult(t *testing.T) {
	runSynthetic(t, "A01", "GWF-HISTORY-REPLAY")
}
func TestGoWorkflowsAtomicReplayReturnsSameResult(t *testing.T) {
	runSynthetic(t, "A01", "GWF-HISTORY-REPLAY")
}
func TestGoWorkflowsAtomicSideEffectRecordedOnce(t *testing.T) {
	runSynthetic(t, "A02", "GWF-HISTORY-REPLAY")
}
func TestGoWorkflowsAtomicReplayDoesNotRepeatSideEffect(t *testing.T) {
	runSynthetic(t, "A02", "GWF-HISTORY-REPLAY")
}
func TestGoWorkflowsAtomicActivityRetryPolicy(t *testing.T) {
	runSynthetic(t, "A03", "GWF-ACTIVITY-RETRY")
}
func TestGoWorkflowsAtomicNonRetryableActivityError(t *testing.T) {
	runSynthetic(t, "A03", "GWF-ACTIVITY-RETRY")
}
func TestGoWorkflowsAtomicActivityPayloadRoundTrip(t *testing.T) {
	runSynthetic(t, "A04", "GWF-ACTIVITY-RETRY")
}
func TestGoWorkflowsAtomicActivityErrorPropagation(t *testing.T) {
	runSynthetic(t, "A04", "GWF-ACTIVITY-RETRY")
}
func TestGoWorkflowsAtomicTimerFuturePending(t *testing.T) { runSynthetic(t, "A05", "GWF-TIMER-CLOCK") }
func TestGoWorkflowsAtomicTimerFutureReadyAtDeadline(t *testing.T) {
	runSynthetic(t, "A05", "GWF-TIMER-CLOCK")
}
func TestGoWorkflowsAtomicTesterClockAdvance(t *testing.T) { runSynthetic(t, "A06", "GWF-TIMER-CLOCK") }
func TestGoWorkflowsAtomicTesterClockDoesNotRunEarly(t *testing.T) {
	runSynthetic(t, "A06", "GWF-TIMER-CLOCK")
}
func TestGoWorkflowsAtomicSignalReceive(t *testing.T) { runSynthetic(t, "A07", "GWF-SIGNAL-CHANNEL") }
func TestGoWorkflowsAtomicSignalPayloadConversion(t *testing.T) {
	runSynthetic(t, "A07", "GWF-SIGNAL-CHANNEL")
}
func TestGoWorkflowsAtomicChannelSendReceiveOrder(t *testing.T) {
	runSynthetic(t, "A08", "GWF-SIGNAL-CHANNEL")
}
func TestGoWorkflowsAtomicSelectorChoosesReadyBranch(t *testing.T) {
	runSynthetic(t, "A08", "GWF-SIGNAL-CHANNEL")
}
func TestGoWorkflowsAtomicMemoryBackendInstanceLifecycle(t *testing.T) {
	runSynthetic(t, "A09", "GWF-BACKEND-EQUIVALENCE")
}
func TestGoWorkflowsAtomicMemoryBackendPendingTask(t *testing.T) {
	runSynthetic(t, "A09", "GWF-BACKEND-EQUIVALENCE")
}
func TestGoWorkflowsSeamHistoryToDeterministicReplay(t *testing.T) {
	runSynthetic(t, "I01", "GWF-HISTORY-REPLAY")
}
func TestGoWorkflowsSeamReplayKeepsWorkflowResult(t *testing.T) {
	runSynthetic(t, "I01", "GWF-HISTORY-REPLAY")
}
func TestGoWorkflowsSeamFreshWorkerReplaysPendingWorkflow(t *testing.T) {
	runSynthetic(t, "I02", "GWF-HISTORY-REPLAY")
}
func TestGoWorkflowsSeamReplayDoesNotDuplicateCompletedStep(t *testing.T) {
	runSynthetic(t, "I02", "GWF-HISTORY-REPLAY")
}
func TestGoWorkflowsSeamActivityRetryThenSuccess(t *testing.T) {
	runSynthetic(t, "I03", "GWF-ACTIVITY-RETRY")
}
func TestGoWorkflowsSeamActivityAttemptCount(t *testing.T) {
	runSynthetic(t, "I03", "GWF-ACTIVITY-RETRY")
}
func TestGoWorkflowsSeamNonRetryableErrorStopsAttempts(t *testing.T) {
	runSynthetic(t, "I04", "GWF-ACTIVITY-RETRY")
}
func TestGoWorkflowsSeamActivityErrorReachesWorkflow(t *testing.T) {
	runSynthetic(t, "I04", "GWF-ACTIVITY-RETRY")
}
func TestGoWorkflowsSeamActivityPayloadAcrossWorker(t *testing.T) {
	runSynthetic(t, "I05", "GWF-ACTIVITY-RETRY")
}
func TestGoWorkflowsSeamTimerToMockClockResult(t *testing.T) {
	runSynthetic(t, "I06", "GWF-TIMER-CLOCK")
}
func TestGoWorkflowsSeamTimerWaitsUntilDeadline(t *testing.T) {
	runSynthetic(t, "I06", "GWF-TIMER-CLOCK")
}
func TestGoWorkflowsSeamCancelledTimerDoesNotResume(t *testing.T) {
	runSynthetic(t, "I07", "GWF-TIMER-CLOCK")
}
func TestGoWorkflowsSeamTimerCancellationReachesFuture(t *testing.T) {
	runSynthetic(t, "I07", "GWF-TIMER-CLOCK")
}
func TestGoWorkflowsSeamActivityRetryTimerOrdering(t *testing.T) {
	runSynthetic(t, "I08", "GWF-TIMER-CLOCK")
}
func TestGoWorkflowsSeamRetryBackoffUsesWorkflowClock(t *testing.T) {
	runSynthetic(t, "I08", "GWF-TIMER-CLOCK")
}
func TestGoWorkflowsSeamClientSignalWakesWorkflow(t *testing.T) {
	runSynthetic(t, "I09", "GWF-SIGNAL-CHANNEL")
}
func TestGoWorkflowsSeamSignalPayloadPreserved(t *testing.T) {
	runSynthetic(t, "I09", "GWF-SIGNAL-CHANNEL")
}
func TestGoWorkflowsSeamMultipleSignalsKeepOrder(t *testing.T) {
	runSynthetic(t, "I10", "GWF-SIGNAL-CHANNEL")
}
func TestGoWorkflowsSeamSelectorTimerVersusSignal(t *testing.T) {
	runSynthetic(t, "I10", "GWF-SIGNAL-CHANNEL")
}
func TestGoWorkflowsSeamMemorySQLiteCompletedResult(t *testing.T) {
	runSynthetic(t, "I11", "GWF-BACKEND-EQUIVALENCE")
}
func TestGoWorkflowsSeamMemorySQLiteStatusAgreement(t *testing.T) {
	runSynthetic(t, "I11", "GWF-BACKEND-EQUIVALENCE")
}
func TestGoWorkflowsSeamSQLiteReopenPendingTask(t *testing.T) {
	runSynthetic(t, "I12", "GWF-BACKEND-EQUIVALENCE")
}
func TestGoWorkflowsSeamSQLiteReopenCompletedResult(t *testing.T) {
	runSynthetic(t, "I12", "GWF-BACKEND-EQUIVALENCE")
}
func TestGoWorkflowsSeamBackendRemovalEquivalence(t *testing.T) {
	runSynthetic(t, "I13", "GWF-BACKEND-EQUIVALENCE")
}
func TestGoWorkflowsSeamSQLiteRemovalPersistsReopen(t *testing.T) {
	runSynthetic(t, "I13", "GWF-BACKEND-EQUIVALENCE")
}
func TestGoWorkflowsSeamContinueAsNewInputToNextRun(t *testing.T) {
	runSynthetic(t, "I14", "GWF-CONTINUE-LIFECYCLE")
}
func TestGoWorkflowsSeamContinueAsNewPreservesLogicalInstance(t *testing.T) {
	runSynthetic(t, "I15", "GWF-CONTINUE-LIFECYCLE")
}
func TestGoWorkflowsSeamCancellationStopsPendingActivity(t *testing.T) {
	runSynthetic(t, "I16", "GWF-CANCEL-LOCK-RECOVERY")
}
func TestGoWorkflowsSeamExpiredWorkerLockIsRecovered(t *testing.T) {
	runSynthetic(t, "I17", "GWF-CANCEL-LOCK-RECOVERY")
}
func TestGoWorkflowsSeamBackendIdentityIgnoredAfterReopen(t *testing.T) {
	runSynthetic(t, "I18", "GWF-BACKEND-EQUIVALENCE")
}
func TestGoWorkflowsSeamBackendTransferKeepsSemanticDigest(t *testing.T) {
	runSynthetic(t, "I18", "GWF-BACKEND-EQUIVALENCE")
}
func TestGoWorkflowsSeamContinueLineageToTerminalResult(t *testing.T) {
	runSynthetic(t, "I19", "GWF-CONTINUE-LIFECYCLE")
}
func TestGoWorkflowsSeamContinueLineageRejectsCycle(t *testing.T) {
	runSynthetic(t, "I19", "GWF-CONTINUE-LIFECYCLE")
}
func TestGoWorkflowsSeamCancellationClearsCompletionAndLock(t *testing.T) {
	runSynthetic(t, "I20", "GWF-CANCEL-LOCK-RECOVERY")
}
func TestGoWorkflowsSeamRecoveredLockCannotCompleteCancelledRun(t *testing.T) {
	runSynthetic(t, "I20", "GWF-CANCEL-LOCK-RECOVERY")
}
func TestGoWorkflowsSystemHistoryReplayFreshReceipt(t *testing.T) {
	runSynthetic(t, "S01", "GWF-HISTORY-REPLAY")
}
func TestGoWorkflowsSystemActivityRetryFreshReceipt(t *testing.T) {
	runSynthetic(t, "S02", "GWF-ACTIVITY-RETRY")
}
func TestGoWorkflowsSystemTimerClockFreshReceipt(t *testing.T) {
	runSynthetic(t, "S03", "GWF-TIMER-CLOCK")
}
func TestGoWorkflowsSystemSignalOrderingFreshReceipt(t *testing.T) {
	runSynthetic(t, "S04", "GWF-SIGNAL-CHANNEL")
}
func TestGoWorkflowsSystemBackendEquivalenceFreshReceipt(t *testing.T) {
	runSynthetic(t, "S05", "GWF-BACKEND-EQUIVALENCE")
}
