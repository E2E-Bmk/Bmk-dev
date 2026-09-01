package shellgate_test

import "testing"

func TestShellDialectParserMode(t *testing.T)              { runSynthetic(t, "A01", "M-PARSE-DIALECT") }
func TestShellDialectParserModeBoundary(t *testing.T)      { runSynthetic(t, "A01", "M-PARSE-DIALECT") }
func TestShellHeredocAndCommentParse(t *testing.T)         { runSynthetic(t, "A02", "M-PARSE-DIALECT") }
func TestShellHeredocAndCommentParseBoundary(t *testing.T) { runSynthetic(t, "A02", "M-PARSE-DIALECT") }
func TestShellASTPositionIdentity(t *testing.T)            { runSynthetic(t, "A03", "M-AST-IDENTITY") }
func TestShellASTPositionIdentityBoundary(t *testing.T)    { runSynthetic(t, "A03", "M-AST-IDENTITY") }
func TestShellASTWalkNodeOwnership(t *testing.T)           { runSynthetic(t, "A04", "M-AST-IDENTITY") }
func TestShellASTWalkNodeOwnershipBoundary(t *testing.T)   { runSynthetic(t, "A04", "M-AST-IDENTITY") }
func TestShellPrinterStatementLayout(t *testing.T)         { runSynthetic(t, "A05", "M-PRINT-IDEMPOTENCE") }
func TestShellPrinterStatementLayoutBoundary(t *testing.T) {
	runSynthetic(t, "A05", "M-PRINT-IDEMPOTENCE")
}
func TestShellPrinterMinifyPolicy(t *testing.T) { runSynthetic(t, "A06", "M-PRINT-IDEMPOTENCE") }
func TestShellPrinterMinifyPolicyBoundary(t *testing.T) {
	runSynthetic(t, "A06", "M-PRINT-IDEMPOTENCE")
}
func TestShellParameterExpansion(t *testing.T)           { runSynthetic(t, "A07", "M-WORD-EXPANSION") }
func TestShellParameterExpansionBoundary(t *testing.T)   { runSynthetic(t, "A07", "M-WORD-EXPANSION") }
func TestShellArithmeticExpansion(t *testing.T)          { runSynthetic(t, "A08", "M-WORD-EXPANSION") }
func TestShellArithmeticExpansionBoundary(t *testing.T)  { runSynthetic(t, "A08", "M-WORD-EXPANSION") }
func TestShellGlobPatternMatch(t *testing.T)             { runSynthetic(t, "A09", "M-PATTERN-MATCH") }
func TestShellGlobPatternMatchBoundary(t *testing.T)     { runSynthetic(t, "A09", "M-PATTERN-MATCH") }
func TestShellExtendedPatternMatch(t *testing.T)         { runSynthetic(t, "A10", "M-PATTERN-MATCH") }
func TestShellExtendedPatternMatchBoundary(t *testing.T) { runSynthetic(t, "A10", "M-PATTERN-MATCH") }
func TestShellRunnerAssignmentEnvironment(t *testing.T) {
	runSynthetic(t, "A11", "M-RUNNER-ENVIRONMENT")
}
func TestShellRunnerAssignmentEnvironmentBoundary(t *testing.T) {
	runSynthetic(t, "A11", "M-RUNNER-ENVIRONMENT")
}
func TestShellRedirectionFileEffect(t *testing.T) { runSynthetic(t, "A12", "M-FILESYSTEM-EFFECT") }
func TestShellRedirectionFileEffectBoundary(t *testing.T) {
	runSynthetic(t, "A12", "M-FILESYSTEM-EFFECT")
}
func TestShellNativeExitStatus(t *testing.T)                   { runNative(t, "A13", "") }
func TestShellNativeExitStatusBoundary(t *testing.T)           { runNative(t, "A13", "") }
func TestShellNativeCommandSubstitution(t *testing.T)          { runNative(t, "A14", "") }
func TestShellNativeCommandSubstitutionBoundary(t *testing.T)  { runNative(t, "A14", "") }
func TestShellNativeSyntaxError(t *testing.T)                  { runNative(t, "A15", "") }
func TestShellNativeSyntaxErrorBoundary(t *testing.T)          { runNative(t, "A15", "") }
func TestShellNativeReaderWriterContract(t *testing.T)         { runNative(t, "A16", "") }
func TestShellNativeReaderWriterContractBoundary(t *testing.T) { runNative(t, "A16", "") }
func TestShellParsePrintParseIdentity(t *testing.T)            { runSynthetic(t, "I01", "M-AST-IDENTITY") }
func TestShellParsedProgramRuns(t *testing.T)                  { runSynthetic(t, "I02", "M-PARSE-DIALECT") }
func TestShellExpansionReadsRunnerEnvironment(t *testing.T) {
	runSynthetic(t, "I03", "M-WORD-EXPANSION")
}
func TestShellGlobReadsSandboxFilesystem(t *testing.T) { runSynthetic(t, "I04", "M-PATTERN-MATCH") }
func TestShellRedirectionPublishesFile(t *testing.T)   { runSynthetic(t, "I05", "M-FILESYSTEM-EFFECT") }
func TestShellPipelinePropagatesEnvironment(t *testing.T) {
	runSynthetic(t, "I06", "M-RUNNER-ENVIRONMENT")
}
func TestShellCommandSubstitutionCapturesOutput(t *testing.T) {
	runSynthetic(t, "I07", "M-RUNNER-ENVIRONMENT")
}
func TestShellFunctionScopeRestoresVariables(t *testing.T) {
	runSynthetic(t, "I08", "M-RUNNER-ENVIRONMENT")
}
func TestShellShfmtUsesPrinterPolicy(t *testing.T) { runSynthetic(t, "I09", "M-CLI-API-EQUIVALENCE") }
func TestShellGoshUsesInterpreterHandlers(t *testing.T) {
	runSynthetic(t, "I10", "M-CLI-API-EQUIVALENCE")
}
func TestShellPrinterPreservesCommentsAndHeredocs(t *testing.T) {
	runSynthetic(t, "I11", "M-PRINT-IDEMPOTENCE")
}
func TestShellDiagnosticUsesASTPositions(t *testing.T)  { runSynthetic(t, "I12", "M-AST-IDENTITY") }
func TestShellExpandedPatternMatchesFiles(t *testing.T) { runSynthetic(t, "I13", "M-PATTERN-MATCH") }
func TestShellRunnerWritesThenReadsSandbox(t *testing.T) {
	runSynthetic(t, "I14", "M-FILESYSTEM-EFFECT")
}
func TestShellShfmtDialectFlagChangesParse(t *testing.T)    { runSynthetic(t, "I15", "M-PARSE-DIALECT") }
func TestShellCLIAndAPIFormatAgree(t *testing.T)            { runSynthetic(t, "I16", "M-CLI-API-EQUIVALENCE") }
func TestShellNativeStatusReachesCaller(t *testing.T)       { runNative(t, "I17", "") }
func TestShellNativeSubstitutionTrimsNewlines(t *testing.T) { runNative(t, "I18", "") }
func TestShellNativeSyntaxFailureDoesNotRun(t *testing.T)   { runNative(t, "I19", "") }
func TestShellNativeIORoundTrip(t *testing.T)               { runNative(t, "I20", "") }
func TestShellNativePrinterSecondPass(t *testing.T)         { runNative(t, "I21", "") }
func TestShellNativeEmptyGlobBehavior(t *testing.T)         { runNative(t, "I22", "") }
func TestShellNativeEnvironmentIsolation(t *testing.T)      { runNative(t, "I23", "") }
func TestShellNativeFileDescriptorClosure(t *testing.T)     { runNative(t, "I24", "") }
func TestShellScriptExecutionFreshStateReceipt(t *testing.T) {
	runSynthetic(t, "S01", "M-RUNNER-ENVIRONMENT")
}
func TestShellShfmtSemanticIdentityReceipt(t *testing.T) {
	runSynthetic(t, "S02", "M-PRINT-IDEMPOTENCE")
}
func TestShellExpansionGlobExecutionReceipt(t *testing.T) { runSynthetic(t, "S03", "M-PATTERN-MATCH") }
func TestShellFunctionRedirectionIsolationReceipt(t *testing.T) {
	runSynthetic(t, "S04", "M-FILESYSTEM-EFFECT")
}
func TestShellCLIAPIFormatRunReceipt(t *testing.T)       { runSynthetic(t, "S05", "M-CLI-API-EQUIVALENCE") }
func TestShellFailedCommandStateReceipt(t *testing.T)    { runSynthetic(t, "S06", "M-RUNNER-ENVIRONMENT") }
func TestShellNativeParseRunIOWorkflow(t *testing.T)     { runNative(t, "S07", "") }
func TestShellNativeSyntaxFailureNoEffects(t *testing.T) { runNative(t, "S08", "") }
