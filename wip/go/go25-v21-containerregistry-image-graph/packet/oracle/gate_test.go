package containerregistrygate_test

import "testing"

func TestContainerReferenceCanonicalization(t *testing.T) {
	runSynthetic(t, "A01", "M-REFERENCE-NORMALIZATION")
}
func TestContainerReferenceCanonicalizationBoundary(t *testing.T) {
	runSynthetic(t, "A01", "M-REFERENCE-NORMALIZATION")
}
func TestContainerDescriptorDigestAndSize(t *testing.T) {
	runSynthetic(t, "A02", "M-DESCRIPTOR-INTEGRITY")
}
func TestContainerDescriptorDigestAndSizeBoundary(t *testing.T) {
	runSynthetic(t, "A02", "M-DESCRIPTOR-INTEGRITY")
}
func TestContainerLayerCompressedUncompressedIdentity(t *testing.T) {
	runSynthetic(t, "A03", "M-LAYER-LIFECYCLE")
}
func TestContainerLayerCompressedUncompressedIdentityBoundary(t *testing.T) {
	runSynthetic(t, "A03", "M-LAYER-LIFECYCLE")
}
func TestContainerImageManifestConfigLink(t *testing.T) { runSynthetic(t, "A04", "M-MANIFEST-INDEX") }
func TestContainerImageManifestConfigLinkBoundary(t *testing.T) {
	runSynthetic(t, "A04", "M-MANIFEST-INDEX")
}
func TestContainerAppendLayerMutation(t *testing.T)         { runSynthetic(t, "A05", "M-MUTATE-GRAPH") }
func TestContainerAppendLayerMutationBoundary(t *testing.T) { runSynthetic(t, "A05", "M-MUTATE-GRAPH") }
func TestContainerOCILayoutWriteRead(t *testing.T)          { runSynthetic(t, "A06", "M-LAYOUT-TARBALL") }
func TestContainerOCILayoutWriteReadBoundary(t *testing.T) {
	runSynthetic(t, "A06", "M-LAYOUT-TARBALL")
}
func TestContainerRemoteGetPutContract(t *testing.T) { runSynthetic(t, "A07", "M-REGISTRY-TRANSPORT") }
func TestContainerRemoteGetPutContractBoundary(t *testing.T) {
	runSynthetic(t, "A07", "M-REGISTRY-TRANSPORT")
}
func TestContainerCraneOptionApplication(t *testing.T) {
	runSynthetic(t, "A08", "M-CLI-API-EQUIVALENCE")
}
func TestContainerCraneOptionApplicationBoundary(t *testing.T) {
	runSynthetic(t, "A08", "M-CLI-API-EQUIVALENCE")
}
func TestContainerTagDigestReferenceIdentity(t *testing.T) {
	runSynthetic(t, "A09", "M-REFERENCE-NORMALIZATION")
}
func TestContainerTagDigestReferenceIdentityBoundary(t *testing.T) {
	runSynthetic(t, "A09", "M-REFERENCE-NORMALIZATION")
}
func TestContainerValidationRejectsBadSize(t *testing.T) {
	runSynthetic(t, "A10", "M-DESCRIPTOR-INTEGRITY")
}
func TestContainerValidationRejectsBadSizeBoundary(t *testing.T) {
	runSynthetic(t, "A10", "M-DESCRIPTOR-INTEGRITY")
}
func TestContainerIndexPlatformSelection(t *testing.T) { runSynthetic(t, "A11", "M-MANIFEST-INDEX") }
func TestContainerIndexPlatformSelectionBoundary(t *testing.T) {
	runSynthetic(t, "A11", "M-MANIFEST-INDEX")
}
func TestContainerTarballLayerPreservation(t *testing.T) { runSynthetic(t, "A12", "M-LAYOUT-TARBALL") }
func TestContainerTarballLayerPreservationBoundary(t *testing.T) {
	runSynthetic(t, "A12", "M-LAYOUT-TARBALL")
}
func TestContainerEmptyImageNativeConfig(t *testing.T)           { runNative(t, "A13", "") }
func TestContainerEmptyImageNativeConfigBoundary(t *testing.T)   { runNative(t, "A13", "") }
func TestContainerStaticLayerNativeReads(t *testing.T)           { runNative(t, "A14", "") }
func TestContainerStaticLayerNativeReadsBoundary(t *testing.T)   { runNative(t, "A14", "") }
func TestContainerNativeRetryStatusPolicy(t *testing.T)          { runNative(t, "A15", "") }
func TestContainerNativeRetryStatusPolicyBoundary(t *testing.T)  { runNative(t, "A15", "") }
func TestContainerPartialImageLazyAccessor(t *testing.T)         { runNative(t, "A16", "") }
func TestContainerPartialImageLazyAccessorBoundary(t *testing.T) { runNative(t, "A16", "") }

func TestContainerReferenceBuildsRegistryRequest(t *testing.T) {
	runSynthetic(t, "I01", "M-REFERENCE-NORMALIZATION")
}
func TestContainerLayerDescriptorEntersManifest(t *testing.T) {
	runSynthetic(t, "I02", "M-DESCRIPTOR-INTEGRITY")
}
func TestContainerMutationRecomputesImageDigest(t *testing.T) {
	runSynthetic(t, "I03", "M-MUTATE-GRAPH")
}
func TestContainerLayoutRoundTripPreservesGraph(t *testing.T) {
	runSynthetic(t, "I04", "M-LAYOUT-TARBALL")
}
func TestContainerIndexSelectsPlatformImage(t *testing.T) { runSynthetic(t, "I05", "M-MANIFEST-INDEX") }
func TestContainerRemoteRegistryRoundTrip(t *testing.T) {
	runSynthetic(t, "I06", "M-REGISTRY-TRANSPORT")
}
func TestContainerCraneAndLibraryMutationAgree(t *testing.T) {
	runSynthetic(t, "I07", "M-CLI-API-EQUIVALENCE")
}
func TestContainerValidationCrossesManifestAndLayers(t *testing.T) {
	runSynthetic(t, "I08", "M-DESCRIPTOR-INTEGRITY")
}
func TestContainerTagResolutionReturnsCanonicalDigest(t *testing.T) {
	runSynthetic(t, "I09", "M-REFERENCE-NORMALIZATION")
}
func TestContainerLazyLayerReadMemoizesIdentity(t *testing.T) {
	runSynthetic(t, "I10", "M-LAYER-LIFECYCLE")
}
func TestContainerMutatedIndexPublishesChild(t *testing.T) { runSynthetic(t, "I11", "M-MUTATE-GRAPH") }
func TestContainerTarballToLayoutEquivalence(t *testing.T) {
	runSynthetic(t, "I12", "M-LAYOUT-TARBALL")
}
func TestContainerTransportRetryPreservesRequestBody(t *testing.T) {
	runSynthetic(t, "I13", "M-REGISTRY-TRANSPORT")
}
func TestContainerCraneSaveLoadRoundTrip(t *testing.T) {
	runSynthetic(t, "I14", "M-CLI-API-EQUIVALENCE")
}
func TestContainerDescriptorIntegrityAcrossSinks(t *testing.T) {
	runSynthetic(t, "I15", "M-DESCRIPTOR-INTEGRITY")
}
func TestContainerIndexManifestAndChildrenAgree(t *testing.T) {
	runSynthetic(t, "I16", "M-MANIFEST-INDEX")
}
func TestContainerNativeEmptyImageToLayout(t *testing.T)       { runNative(t, "I17", "") }
func TestContainerNativeStaticLayerTarball(t *testing.T)       { runNative(t, "I18", "") }
func TestContainerNativeRetryEventuallySucceeds(t *testing.T)  { runNative(t, "I19", "") }
func TestContainerNativePartialConfigRead(t *testing.T)        { runNative(t, "I20", "") }
func TestContainerNativeNameValidationBeforeHTTP(t *testing.T) { runNative(t, "I21", "") }
func TestContainerNativeManifestMediaTypeRead(t *testing.T)    { runNative(t, "I22", "") }
func TestContainerNativeLayerReaderIsolation(t *testing.T)     { runNative(t, "I23", "") }
func TestContainerNativeRegistryHeadThenGet(t *testing.T)      { runNative(t, "I24", "") }

func TestContainerMutatedImageDurableReceipt(t *testing.T) { runSynthetic(t, "S01", "M-MUTATE-GRAPH") }
func TestContainerTarballLayoutRegistryParity(t *testing.T) {
	runSynthetic(t, "S02", "M-LAYOUT-TARBALL")
}
func TestContainerLocalPushPullReceipt(t *testing.T) { runSynthetic(t, "S03", "M-REGISTRY-TRANSPORT") }
func TestContainerPlatformIndexSelectionReceipt(t *testing.T) {
	runSynthetic(t, "S04", "M-MANIFEST-INDEX")
}
func TestContainerCraneAPIArtifactReceipt(t *testing.T) {
	runSynthetic(t, "S05", "M-CLI-API-EQUIVALENCE")
}
func TestContainerCorruptLayerNoPublicationReceipt(t *testing.T) {
	runSynthetic(t, "S06", "M-LAYER-LIFECYCLE")
}
func TestContainerNativeEmptyImageWorkflow(t *testing.T)    { runNative(t, "S07", "") }
func TestContainerNativeRetryLazyReadWorkflow(t *testing.T) { runNative(t, "S08", "") }
