package alertmanagergate_test

import "testing"

func TestAlertmanagerRouteMatcherSelection(t *testing.T) { runSynthetic(t, "A01", "M-ROUTE-MATCHING") }
func TestAlertmanagerRouteMatcherSelectionBoundary(t *testing.T) {
	runSynthetic(t, "A01", "M-ROUTE-MATCHING")
}
func TestAlertmanagerRouteContinueTraversal(t *testing.T) { runSynthetic(t, "A02", "M-ROUTE-MATCHING") }
func TestAlertmanagerRouteContinueTraversalBoundary(t *testing.T) {
	runSynthetic(t, "A02", "M-ROUTE-MATCHING")
}
func TestAlertmanagerGroupKeyIdentity(t *testing.T) { runSynthetic(t, "A03", "M-GROUP-LIFECYCLE") }
func TestAlertmanagerGroupKeyIdentityBoundary(t *testing.T) {
	runSynthetic(t, "A03", "M-GROUP-LIFECYCLE")
}
func TestAlertmanagerGroupTimingTransitions(t *testing.T) {
	runSynthetic(t, "A04", "M-GROUP-LIFECYCLE")
}
func TestAlertmanagerGroupTimingTransitionsBoundary(t *testing.T) {
	runSynthetic(t, "A04", "M-GROUP-LIFECYCLE")
}
func TestAlertmanagerSilenceMatcherState(t *testing.T) { runSynthetic(t, "A05", "M-SILENCE-STATE") }
func TestAlertmanagerSilenceMatcherStateBoundary(t *testing.T) {
	runSynthetic(t, "A05", "M-SILENCE-STATE")
}
func TestAlertmanagerSilenceExpiryBoundary(t *testing.T) { runSynthetic(t, "A06", "M-SILENCE-STATE") }
func TestAlertmanagerSilenceExpiryBoundaryBoundary(t *testing.T) {
	runSynthetic(t, "A06", "M-SILENCE-STATE")
}
func TestAlertmanagerInhibitionSourceTargetJoin(t *testing.T) {
	runSynthetic(t, "A07", "M-INHIBITION-JOIN")
}
func TestAlertmanagerInhibitionSourceTargetJoinBoundary(t *testing.T) {
	runSynthetic(t, "A07", "M-INHIBITION-JOIN")
}
func TestAlertmanagerInhibitionEqualLabels(t *testing.T) { runSynthetic(t, "A08", "M-INHIBITION-JOIN") }
func TestAlertmanagerInhibitionEqualLabelsBoundary(t *testing.T) {
	runSynthetic(t, "A08", "M-INHIBITION-JOIN")
}
func TestAlertmanagerNotificationRetryPolicy(t *testing.T) {
	runSynthetic(t, "A09", "M-NOTIFICATION-DELIVERY")
}
func TestAlertmanagerNotificationRetryPolicyBoundary(t *testing.T) {
	runSynthetic(t, "A09", "M-NOTIFICATION-DELIVERY")
}
func TestAlertmanagerNotificationLogDedupKey(t *testing.T) { runSynthetic(t, "A10", "M-NFLOG-DEDUP") }
func TestAlertmanagerNotificationLogDedupKeyBoundary(t *testing.T) {
	runSynthetic(t, "A10", "M-NFLOG-DEDUP")
}
func TestAlertmanagerAPISilenceRepresentation(t *testing.T) { runSynthetic(t, "A11", "M-API-STATE") }
func TestAlertmanagerAPISilenceRepresentationBoundary(t *testing.T) {
	runSynthetic(t, "A11", "M-API-STATE")
}
func TestAlertmanagerConfigReloadGeneration(t *testing.T) { runSynthetic(t, "A12", "M-CONFIG-RELOAD") }
func TestAlertmanagerConfigReloadGenerationBoundary(t *testing.T) {
	runSynthetic(t, "A12", "M-CONFIG-RELOAD")
}
func TestAlertmanagerAlertFingerprintNative(t *testing.T)            { runNative(t, "A13", "") }
func TestAlertmanagerAlertFingerprintNativeBoundary(t *testing.T)    { runNative(t, "A13", "") }
func TestAlertmanagerMemoryProviderNativeState(t *testing.T)         { runNative(t, "A14", "") }
func TestAlertmanagerMemoryProviderNativeStateBoundary(t *testing.T) { runNative(t, "A14", "") }
func TestAlertmanagerTimeIntervalNativeMatch(t *testing.T)           { runNative(t, "A15", "") }
func TestAlertmanagerTimeIntervalNativeMatchBoundary(t *testing.T)   { runNative(t, "A15", "") }
func TestAlertmanagerTemplateDataNativeFields(t *testing.T)          { runNative(t, "A16", "") }
func TestAlertmanagerTemplateDataNativeFieldsBoundary(t *testing.T)  { runNative(t, "A16", "") }
func TestAlertmanagerConfigBuildsRouteTree(t *testing.T)             { runSynthetic(t, "I01", "M-CONFIG-RELOAD") }
func TestAlertmanagerProviderAlertSelectsReceiver(t *testing.T) {
	runSynthetic(t, "I02", "M-ROUTE-MATCHING")
}
func TestAlertmanagerRouteSelectionCreatesGroup(t *testing.T) {
	runSynthetic(t, "I03", "M-GROUP-LIFECYCLE")
}
func TestAlertmanagerSilenceMarksBeforeDispatch(t *testing.T) {
	runSynthetic(t, "I04", "M-SILENCE-STATE")
}
func TestAlertmanagerInhibitionMarksTargetGroup(t *testing.T) {
	runSynthetic(t, "I05", "M-INHIBITION-JOIN")
}
func TestAlertmanagerGroupSendsNotification(t *testing.T) {
	runSynthetic(t, "I06", "M-NOTIFICATION-DELIVERY")
}
func TestAlertmanagerDeliveryWritesNotificationLog(t *testing.T) {
	runSynthetic(t, "I07", "M-NFLOG-DEDUP")
}
func TestAlertmanagerAPIWritesSilenceStore(t *testing.T) { runSynthetic(t, "I08", "M-API-STATE") }
func TestAlertmanagerReloadReplacesRouteGeneration(t *testing.T) {
	runSynthetic(t, "I09", "M-CONFIG-RELOAD")
}
func TestAlertmanagerContinueRouteOwnsMultipleReceivers(t *testing.T) {
	runSynthetic(t, "I10", "M-ROUTE-MATCHING")
}
func TestAlertmanagerGroupWaitAndRepeatIntervals(t *testing.T) {
	runSynthetic(t, "I11", "M-GROUP-LIFECYCLE")
}
func TestAlertmanagerSilenceAPIExpiryObservation(t *testing.T) {
	runSynthetic(t, "I12", "M-SILENCE-STATE")
}
func TestAlertmanagerInhibitionMarkerReleases(t *testing.T) {
	runSynthetic(t, "I13", "M-INHIBITION-JOIN")
}
func TestAlertmanagerRetryThenDedupReceipt(t *testing.T) { runSynthetic(t, "I14", "M-NFLOG-DEDUP") }
func TestAlertmanagerAPIAlertGroupsMirrorDispatcher(t *testing.T) {
	runSynthetic(t, "I15", "M-API-STATE")
}
func TestAlertmanagerReceiverConfigBuildsPipeline(t *testing.T) {
	runSynthetic(t, "I16", "M-CONFIG-RELOAD")
}
func TestAlertmanagerNativeProviderFingerprintLookup(t *testing.T) { runNative(t, "I17", "") }
func TestAlertmanagerNativeInvalidConfigDiagnostic(t *testing.T)   { runNative(t, "I18", "") }
func TestAlertmanagerNativeTimeIntervalRouteGate(t *testing.T)     { runNative(t, "I19", "") }
func TestAlertmanagerNativeTemplateNotificationData(t *testing.T)  { runNative(t, "I20", "") }
func TestAlertmanagerNativeProviderFeedsAPI(t *testing.T)          { runNative(t, "I21", "") }
func TestAlertmanagerNativeEmptyGroupNoDelivery(t *testing.T)      { runNative(t, "I22", "") }
func TestAlertmanagerNativeExpiredSilenceRemoved(t *testing.T)     { runNative(t, "I23", "") }
func TestAlertmanagerNativeReceiverWithoutAlertsIdle(t *testing.T) { runNative(t, "I24", "") }
func TestAlertmanagerAlertRouteDeliveryReceipt(t *testing.T) {
	runSynthetic(t, "S01", "M-ROUTE-MATCHING")
}
func TestAlertmanagerSilencedGroupFreshAPIReceipt(t *testing.T) {
	runSynthetic(t, "S02", "M-SILENCE-STATE")
}
func TestAlertmanagerInhibitionReleaseDeliveryReceipt(t *testing.T) {
	runSynthetic(t, "S03", "M-INHIBITION-JOIN")
}
func TestAlertmanagerRetryDedupLifecycleReceipt(t *testing.T) {
	runSynthetic(t, "S04", "M-NFLOG-DEDUP")
}
func TestAlertmanagerReloadedRouteGenerationReceipt(t *testing.T) {
	runSynthetic(t, "S05", "M-CONFIG-RELOAD")
}
func TestAlertmanagerAmtoolAPIStateReceipt(t *testing.T)        { runSynthetic(t, "S06", "M-API-STATE") }
func TestAlertmanagerNativeAlertToWebhookWorkflow(t *testing.T) { runNative(t, "S07", "") }
func TestAlertmanagerNativeBadReloadKeepsLastGood(t *testing.T) { runNative(t, "S08", "") }
