package templgate_test

import "testing"

func TestTemplComponentSyntaxTree(t *testing.T)          { runSynthetic(t, "A01", "M-TEMPLATE-PARSE") }
func TestTemplComponentSyntaxTreeBoundary(t *testing.T)  { runSynthetic(t, "A01", "M-TEMPLATE-PARSE") }
func TestTemplGoExpressionBoundary(t *testing.T)         { runSynthetic(t, "A02", "M-TEMPLATE-PARSE") }
func TestTemplGoExpressionBoundaryBoundary(t *testing.T) { runSynthetic(t, "A02", "M-TEMPLATE-PARSE") }
func TestTemplURLContextEscaping(t *testing.T)           { runSynthetic(t, "A03", "M-CONTEXT-ESCAPE") }
func TestTemplURLContextEscapingBoundary(t *testing.T)   { runSynthetic(t, "A03", "M-CONTEXT-ESCAPE") }
func TestTemplScriptAndStyleSafety(t *testing.T)         { runSynthetic(t, "A04", "M-CONTEXT-ESCAPE") }
func TestTemplScriptAndStyleSafetyBoundary(t *testing.T) { runSynthetic(t, "A04", "M-CONTEXT-ESCAPE") }
func TestTemplGeneratedComponentSignature(t *testing.T) {
	runSynthetic(t, "A05", "M-COMPONENT-CODEGEN")
}
func TestTemplGeneratedComponentSignatureBoundary(t *testing.T) {
	runSynthetic(t, "A05", "M-COMPONENT-CODEGEN")
}
func TestTemplGeneratedImportOwnership(t *testing.T) { runSynthetic(t, "A06", "M-COMPONENT-CODEGEN") }
func TestTemplGeneratedImportOwnershipBoundary(t *testing.T) {
	runSynthetic(t, "A06", "M-COMPONENT-CODEGEN")
}
func TestTemplBooleanAttributeSemantics(t *testing.T) {
	runSynthetic(t, "A07", "M-ATTRIBUTE-SEMANTICS")
}
func TestTemplBooleanAttributeSemanticsBoundary(t *testing.T) {
	runSynthetic(t, "A07", "M-ATTRIBUTE-SEMANTICS")
}
func TestTemplSpreadAttributeOrdering(t *testing.T) { runSynthetic(t, "A08", "M-ATTRIBUTE-SEMANTICS") }
func TestTemplSpreadAttributeOrderingBoundary(t *testing.T) {
	runSynthetic(t, "A08", "M-ATTRIBUTE-SEMANTICS")
}
func TestTemplComponentRenderContract(t *testing.T) { runSynthetic(t, "A09", "M-RUNTIME-RENDER") }
func TestTemplComponentRenderContractBoundary(t *testing.T) {
	runSynthetic(t, "A09", "M-RUNTIME-RENDER")
}
func TestTemplCancelledContextStopsRender(t *testing.T) { runSynthetic(t, "A10", "M-RUNTIME-RENDER") }
func TestTemplCancelledContextStopsRenderBoundary(t *testing.T) {
	runSynthetic(t, "A10", "M-RUNTIME-RENDER")
}
func TestTemplFormatterWhitespacePolicy(t *testing.T) { runSynthetic(t, "A11", "M-FORMAT-IDEMPOTENCE") }
func TestTemplFormatterWhitespacePolicyBoundary(t *testing.T) {
	runSynthetic(t, "A11", "M-FORMAT-IDEMPOTENCE")
}
func TestTemplGenerateDiagnosticLocation(t *testing.T) { runSynthetic(t, "A12", "M-CLI-DIAGNOSTICS") }
func TestTemplGenerateDiagnosticLocationBoundary(t *testing.T) {
	runSynthetic(t, "A12", "M-CLI-DIAGNOSTICS")
}
func TestTemplMalformedSyntaxError(t *testing.T)                  { runNative(t, "A13", "") }
func TestTemplMalformedSyntaxErrorBoundary(t *testing.T)          { runNative(t, "A13", "") }
func TestTemplWriterErrorPropagation(t *testing.T)                { runNative(t, "A14", "") }
func TestTemplWriterErrorPropagationBoundary(t *testing.T)        { runNative(t, "A14", "") }
func TestTemplNativeFormatIdempotence(t *testing.T)               { runNative(t, "A15", "") }
func TestTemplNativeFormatIdempotenceBoundary(t *testing.T)       { runNative(t, "A15", "") }
func TestTemplDeterministicGeneratedFileSet(t *testing.T)         { runNative(t, "A16", "") }
func TestTemplDeterministicGeneratedFileSetBoundary(t *testing.T) { runNative(t, "A16", "") }
func TestTemplParseTreeToGeneratedSource(t *testing.T)            { runSynthetic(t, "I01", "M-COMPONENT-CODEGEN") }
func TestTemplDynamicAttributeEscaping(t *testing.T)              { runSynthetic(t, "I02", "M-CONTEXT-ESCAPE") }
func TestTemplGeneratedComponentRenders(t *testing.T)             { runSynthetic(t, "I03", "M-RUNTIME-RENDER") }
func TestTemplParseFormatParseIdentity(t *testing.T)              { runSynthetic(t, "I04", "M-FORMAT-IDEMPOTENCE") }
func TestTemplSafeScriptGeneration(t *testing.T)                  { runSynthetic(t, "I05", "M-CONTEXT-ESCAPE") }
func TestTemplSpreadAttributesRenderOrder(t *testing.T) {
	runSynthetic(t, "I06", "M-ATTRIBUTE-SEMANTICS")
}
func TestTemplNestedComponentCallFlow(t *testing.T) { runSynthetic(t, "I07", "M-RUNTIME-RENDER") }
func TestTemplCancellationAcrossGeneratedCall(t *testing.T) {
	runSynthetic(t, "I08", "M-RUNTIME-RENDER")
}
func TestTemplImportAliasToCompiledArtifact(t *testing.T) {
	runSynthetic(t, "I09", "M-COMPONENT-CODEGEN")
}
func TestTemplFormatPreservesGoExpressions(t *testing.T) {
	runSynthetic(t, "I10", "M-FORMAT-IDEMPOTENCE")
}
func TestTemplGenerateCLIProducesArtifact(t *testing.T) { runSynthetic(t, "I11", "M-CLI-DIAGNOSTICS") }
func TestTemplFmtCLIReportsChangedFiles(t *testing.T)   { runSynthetic(t, "I12", "M-CLI-DIAGNOSTICS") }
func TestTemplCSSExpressionEscaping(t *testing.T)       { runSynthetic(t, "I13", "M-CONTEXT-ESCAPE") }
func TestTemplURLAttributeOmissionAndRender(t *testing.T) {
	runSynthetic(t, "I14", "M-ATTRIBUTE-SEMANTICS")
}
func TestTemplParserErrorBecomesCLIDiagnostic(t *testing.T) {
	runSynthetic(t, "I15", "M-CLI-DIAGNOSTICS")
}
func TestTemplGeneratedSourceCompilesAndRenders(t *testing.T) {
	runSynthetic(t, "I16", "M-COMPONENT-CODEGEN")
}
func TestTemplNativeMalformedInputNoArtifact(t *testing.T) { runNative(t, "I17", "") }
func TestTemplNativeWriterFailureStopsTree(t *testing.T)   { runNative(t, "I18", "") }
func TestTemplNativeFormatterIdempotence(t *testing.T)     { runNative(t, "I19", "") }
func TestTemplNativeDeterministicGeneration(t *testing.T)  { runNative(t, "I20", "") }
func TestTemplPlainTextComponentRender(t *testing.T)       { runNative(t, "I21", "") }
func TestTemplEscapedTextRoundTrip(t *testing.T)           { runNative(t, "I22", "") }
func TestTemplCLIHelpAndVersionRemainNative(t *testing.T)  { runNative(t, "I23", "") }
func TestTemplGeneratedPackageCompilesTwice(t *testing.T)  { runNative(t, "I24", "") }
func TestTemplTemplateToFreshHTMLReceipt(t *testing.T)     { runSynthetic(t, "S01", "M-COMPONENT-CODEGEN") }
func TestTemplContextSafetyEndToEndReceipt(t *testing.T)   { runSynthetic(t, "S02", "M-CONTEXT-ESCAPE") }
func TestTemplGenerateCLICompileReceipt(t *testing.T)      { runSynthetic(t, "S03", "M-CLI-DIAGNOSTICS") }
func TestTemplFormatRegenerateSemanticReceipt(t *testing.T) {
	runSynthetic(t, "S04", "M-FORMAT-IDEMPOTENCE")
}
func TestTemplNestedComponentsCancellationReceipt(t *testing.T) {
	runSynthetic(t, "S05", "M-RUNTIME-RENDER")
}
func TestTemplUnsafeAttributeFailureReceipt(t *testing.T)      { runSynthetic(t, "S06", "M-CONTEXT-ESCAPE") }
func TestTemplNativeSourceGenerateRender(t *testing.T)         { runNative(t, "S07", "") }
func TestTemplNativeFailureLeavesNoStaleArtifact(t *testing.T) { runNative(t, "S08", "") }
