package memberlist_gate_test

import "testing"

// Verifies: ML-ALIVE-A01
func TestMemberlistAtomicAliveHigherIncarnationWinsPrimary(t *testing.T) { runAliveContract(t) }

// Verifies: ML-ALIVE-A01
func TestMemberlistAtomicAliveHigherIncarnationWinsEdge(t *testing.T) { runAliveContract(t) }

// Verifies: ML-ALIVE-A02
func TestMemberlistAtomicAliveEqualIncarnationMetadataRulePrimary(t *testing.T) { runAliveContract(t) }

// Verifies: ML-ALIVE-A02
func TestMemberlistAtomicAliveEqualIncarnationMetadataRuleEdge(t *testing.T) { runAliveContract(t) }

// Verifies: ML-JOIN-A01
func TestMemberlistAtomicMockNetworkAddressRegistrationPrimary(t *testing.T) { runJoinContract(t) }

// Verifies: ML-JOIN-A01
func TestMemberlistAtomicMockNetworkAddressRegistrationEdge(t *testing.T) { runJoinContract(t) }

// Verifies: ML-JOIN-A02
func TestMemberlistAtomicMockTransportPeerLookupPrimary(t *testing.T) { runJoinContract(t) }

// Verifies: ML-JOIN-A02
func TestMemberlistAtomicMockTransportPeerLookupEdge(t *testing.T) { runJoinContract(t) }

// Verifies: ML-BCAST-A01
func TestMemberlistAtomicBroadcastRetransmitLimitPrimary(t *testing.T) { runBroadcastContract(t) }

// Verifies: ML-BCAST-A01
func TestMemberlistAtomicBroadcastRetransmitLimitEdge(t *testing.T) { runBroadcastContract(t) }

// Verifies: ML-BCAST-A02
func TestMemberlistAtomicNamedBroadcastInvalidatesOlderPrimary(t *testing.T) { runBroadcastContract(t) }

// Verifies: ML-BCAST-A02
func TestMemberlistAtomicNamedBroadcastInvalidatesOlderEdge(t *testing.T) { runBroadcastContract(t) }

// Verifies: ML-LEAVE-A01
func TestMemberlistAtomicLeaveStateTransitionPrimary(t *testing.T) { runLeaveContract(t) }

// Verifies: ML-LEAVE-A01
func TestMemberlistAtomicLeaveStateTransitionEdge(t *testing.T) { runLeaveContract(t) }

// Verifies: ML-LEAVE-A02
func TestMemberlistAtomicLeaveTimeoutCompletionPrimary(t *testing.T) { runLeaveContract(t) }

// Verifies: ML-LEAVE-A02
func TestMemberlistAtomicLeaveTimeoutCompletionEdge(t *testing.T) { runLeaveContract(t) }

// Verifies: ML-META-A01
func TestMemberlistAtomicDelegateNodeMetaLimitPrimary(t *testing.T) { runMetadataContract(t) }

// Verifies: ML-META-A01
func TestMemberlistAtomicDelegateNodeMetaLimitEdge(t *testing.T) { runMetadataContract(t) }

// Verifies: ML-META-A02
func TestMemberlistAtomicUpdateNodeLocalMetadataPrimary(t *testing.T) { runMetadataContract(t) }

// Verifies: ML-META-A02
func TestMemberlistAtomicUpdateNodeLocalMetadataEdge(t *testing.T) { runMetadataContract(t) }

// Verifies: ML-SUSPECT-A01
func TestMemberlistAtomicSuspicionConfirmationThresholdPrimary(t *testing.T) { runSuspicionContract(t) }

// Verifies: ML-SUSPECT-A01
func TestMemberlistAtomicSuspicionConfirmationThresholdEdge(t *testing.T) { runSuspicionContract(t) }

// Verifies: ML-KEY-A01
func TestMemberlistAtomicKeyringPrimaryKeySelectionPrimary(t *testing.T) { runKeyContract(t) }

// Verifies: ML-KEY-A01
func TestMemberlistAtomicKeyringPrimaryKeySelectionEdge(t *testing.T) { runKeyContract(t) }

// Verifies: ML-NATIVE-NODE-001
func TestMemberlistAtomicNodeAddressStringPrimary(t *testing.T) { runNativeContract(t) }

// Verifies: ML-NATIVE-NODE-001
func TestMemberlistAtomicNodeAddressStringEdge(t *testing.T) { runNativeContract(t) }

// Verifies: ML-NATIVE-CONFIG-001
func TestMemberlistAtomicConfigProtocolBoundsPrimary(t *testing.T) { runNativeContract(t) }

// Verifies: ML-NATIVE-CONFIG-001
func TestMemberlistAtomicConfigProtocolBoundsEdge(t *testing.T) { runNativeContract(t) }

// Verifies: ML-NATIVE-EVENT-001
func TestMemberlistAtomicChannelEventDelegateBufferPrimary(t *testing.T) { runNativeContract(t) }

// Verifies: ML-NATIVE-EVENT-001
func TestMemberlistAtomicChannelEventDelegateBufferEdge(t *testing.T) { runNativeContract(t) }

// Verifies: ML-NATIVE-TRANSPORT-001
func TestMemberlistAtomicMockTransportShutdownPrimary(t *testing.T) { runNativeContract(t) }

// Verifies: ML-NATIVE-TRANSPORT-001
func TestMemberlistAtomicMockTransportShutdownEdge(t *testing.T) { runNativeContract(t) }

// Verifies: ML-ALIVE-I01
func TestMemberlistSeamAlivePacketToMembersViewPrimary(t *testing.T) { runAliveContract(t) }

// Verifies: ML-ALIVE-I01
func TestMemberlistSeamAlivePacketToMembersViewFailure(t *testing.T) { runAliveContract(t) }

// Verifies: ML-ALIVE-I02
func TestMemberlistSeamAliveStateToUpdateEventPrimary(t *testing.T) { runAliveContract(t) }

// Verifies: ML-ALIVE-I02
func TestMemberlistSeamAliveStateToUpdateEventFailure(t *testing.T) { runAliveContract(t) }

// Verifies: ML-JOIN-I01
func TestMemberlistSeamJoinStreamToPushPullMergePrimary(t *testing.T) { runJoinContract(t) }

// Verifies: ML-JOIN-I01
func TestMemberlistSeamJoinStreamToPushPullMergeFailure(t *testing.T) { runJoinContract(t) }

// Verifies: ML-JOIN-I02
func TestMemberlistSeamMergeRemoteStateToMembersPrimary(t *testing.T) { runJoinContract(t) }

// Verifies: ML-JOIN-I02
func TestMemberlistSeamMergeRemoteStateToMembersFailure(t *testing.T) { runJoinContract(t) }

// Verifies: ML-BCAST-I01
func TestMemberlistSeamQueueSelectionToTransportPacketPrimary(t *testing.T) { runBroadcastContract(t) }

// Verifies: ML-BCAST-I01
func TestMemberlistSeamQueueSelectionToTransportPacketFailure(t *testing.T) { runBroadcastContract(t) }

// Verifies: ML-BCAST-I02
func TestMemberlistSeamBroadcastCompletionToQueueRemovalPrimary(t *testing.T) {
	runBroadcastContract(t)
}

// Verifies: ML-BCAST-I02
func TestMemberlistSeamBroadcastCompletionToQueueRemovalFailure(t *testing.T) {
	runBroadcastContract(t)
}

// Verifies: ML-LEAVE-I01
func TestMemberlistSeamLeaveBroadcastToMemberStatusPrimary(t *testing.T) { runLeaveContract(t) }

// Verifies: ML-LEAVE-I01
func TestMemberlistSeamLeaveBroadcastToMemberStatusFailure(t *testing.T) { runLeaveContract(t) }

// Verifies: ML-LEAVE-I02
func TestMemberlistSeamLeaveStateToDelegateEventPrimary(t *testing.T) { runLeaveContract(t) }

// Verifies: ML-LEAVE-I02
func TestMemberlistSeamLeaveStateToDelegateEventFailure(t *testing.T) { runLeaveContract(t) }

// Verifies: ML-META-I01
func TestMemberlistSeamUpdateNodeToAliveBroadcastPrimary(t *testing.T) { runMetadataContract(t) }

// Verifies: ML-META-I02
func TestMemberlistSeamMetadataMergeToNodeViewPrimary(t *testing.T) { runMetadataContract(t) }

// Verifies: ML-META-I03
func TestMemberlistSeamMetadataChangeToUpdateEventPrimary(t *testing.T) { runMetadataContract(t) }

// Verifies: ML-SUSPECT-I01
func TestMemberlistSeamFailedPingToSuspectBroadcastPrimary(t *testing.T) { runSuspicionContract(t) }

// Verifies: ML-SUSPECT-I02
func TestMemberlistSeamSuspectRefutationToAlivePrimary(t *testing.T) { runSuspicionContract(t) }

// Verifies: ML-SUSPECT-I03
func TestMemberlistSeamAwarenessScoreToProbeTimingPrimary(t *testing.T) { runSuspicionContract(t) }

// Verifies: ML-KEY-I01
func TestMemberlistSeamEncryptedPacketToTransportDecodePrimary(t *testing.T) { runKeyContract(t) }

// Verifies: ML-KEY-I02
func TestMemberlistSeamKeyRotationToPeerAcceptancePrimary(t *testing.T) { runKeyContract(t) }

// Verifies: ML-KEY-I03
func TestMemberlistSeamUnknownKeyToNoMembershipMutationPrimary(t *testing.T) { runKeyContract(t) }

// Verifies: ML-NATIVE-SEAM-001
func TestMemberlistSeamConfigToMockTransportSeamPrimary(t *testing.T) { runNativeContract(t) }

// Verifies: ML-NATIVE-SEAM-002
func TestMemberlistSeamChannelDelegateToMembersSeamPrimary(t *testing.T) { runNativeContract(t) }

// Verifies: ML-NATIVE-SEAM-003
func TestMemberlistSeamLocalNodeToMembersSeamPrimary(t *testing.T) { runNativeContract(t) }

// Verifies: ML-NATIVE-SEAM-004
func TestMemberlistSeamTransportShutdownToMemberlistSeamPrimary(t *testing.T) { runNativeContract(t) }

// Verifies: ML-NATIVE-SEAM-005
func TestMemberlistSeamConflictDelegateToJoinSeamPrimary(t *testing.T) { runNativeContract(t) }

// Verifies: ML-NATIVE-SEAM-006
func TestMemberlistSeamMergeDelegateToCreateSeamPrimary(t *testing.T) { runNativeContract(t) }

// Verifies: ML-NATIVE-SEAM-007
func TestMemberlistSeamAliveDelegateToNodeViewSeamPrimary(t *testing.T) { runNativeContract(t) }

// Verifies: ML-ALIVE-S01
func TestMemberlistE2EFreshAliveMembershipReceiptFreshReceipt(t *testing.T) { runAliveContract(t) }

// Verifies: ML-JOIN-S01
func TestMemberlistE2EFreshMockNetworkJoinReceiptFreshReceipt(t *testing.T) { runJoinContract(t) }

// Verifies: ML-BCAST-S01
func TestMemberlistE2EFreshLatestNamedBroadcastReceiptFreshReceipt(t *testing.T) {
	runBroadcastContract(t)
}

// Verifies: ML-LEAVE-S01
func TestMemberlistE2EFreshLeaveTombstoneReceiptFreshReceipt(t *testing.T) { runLeaveContract(t) }

// Verifies: ML-META-S01
func TestMemberlistE2EFreshMetadataUpdateReceiptFreshReceipt(t *testing.T) { runMetadataContract(t) }

// Verifies: ML-NATIVE-SYS-001
func TestMemberlistE2ENativeMockClusterJoinLeaveFreshReceipt(t *testing.T) { runNativeContract(t) }

// Verifies: ML-NATIVE-SYS-002
func TestMemberlistE2ENativeDelegateMergedMembershipFreshReceipt(t *testing.T) { runNativeContract(t) }

// Verifies: ML-NATIVE-SYS-003
func TestMemberlistE2ENativeConflictRejectedClusterFreshReceipt(t *testing.T) { runNativeContract(t) }
