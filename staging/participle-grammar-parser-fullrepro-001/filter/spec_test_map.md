# spec_test_map — participle-grammar-parser-fullrepro-001

All tests generated (Track B); upstream suite fully excluded (see
rewrite_audit.md). Spec: spec.md (v1). Totals: 104 tests =
72 atomic + 32 integration. Atomic positive share:
56/72 = 78% (>= 60% floor). Every behavior
section >= 4 tests, Error Semantics >= 4, Representative Workflows >= 4,
each CVI covered by >= 2 integration tests.

| test_nodeid | layer | assertion_kind | spec_section | status | source |
|---|---|---|---|---|---|
| oracle/atomic::TestUnknownTokenTypeBuildError | atomic | failure_path | Grammar Definition Language + Error Semantics | covered | generated |
| oracle/atomic::TestUnknownTokenTypeInLiteralConstraint | atomic | failure_path | Grammar Definition Language + Error Semantics | covered | generated |
| oracle/atomic::TestLeftRecursionRejected | atomic | failure_path | Grammar Definition Language + Error Semantics | covered | generated |
| oracle/atomic::TestEmptyStructRejected | atomic | failure_path | Grammar Compilation + Error Semantics | covered | generated |
| oracle/atomic::TestNonStructRootRejected | atomic | failure_path | Grammar Compilation + Error Semantics | covered | generated |
| oracle/atomic::TestMalformedFragmentNamesField | atomic | failure_path | Grammar Definition Language + Error Semantics | covered | generated |
| oracle/atomic::TestMustBuildPanicsOnBuildError | atomic | failure_path | Grammar Compilation + Error Semantics | covered | generated |
| oracle/atomic::TestMustBuildReturnsWorkingParser | atomic | positive | Grammar Compilation | covered | generated |
| oracle/atomic::TestUnionRequiresInterfaceType | atomic | failure_path | Grammar Compilation + Error Semantics | covered | generated |
| oracle/atomic::TestParseTypeWithRequiresInterfaceType | atomic | failure_path | Grammar Compilation + Error Semantics | covered | generated |
| oracle/atomic::TestStringCaptureConcatenatesTokens | atomic | positive | Value Capture | covered | generated |
| oracle/atomic::TestIntCaptureParsesConcatenatedText | atomic | positive | Value Capture | covered | generated |
| oracle/atomic::TestUnsignedAndFloatCaptures | atomic | positive | Value Capture | covered | generated |
| oracle/atomic::TestNumericConversionFailureIsPositionedError | atomic | failure_path | Value Capture + Error Semantics | covered | generated |
| oracle/atomic::TestBoolCaptureSetsTrueRegardlessOfText | atomic | positive | Value Capture | covered | generated |
| oracle/atomic::TestBoolCaptureFalseWhenUnmatched | atomic | positive | Value Capture | covered | generated |
| oracle/atomic::TestSliceCaptureAppendsConvertedElements | atomic | positive | Value Capture | covered | generated |
| oracle/atomic::TestPointerCaptureAllocatesOnlyOnMatch | atomic | positive | Value Capture | covered | generated |
| oracle/atomic::TestStructCaptureAccumulatesPerMatch | atomic | positive | Value Capture | covered | generated |
| oracle/atomic::TestCustomCaptureInterfaceReceivesValues | atomic | positive | Value Capture + Grammar Compilation | covered | generated |
| oracle/atomic::TestTextUnmarshalerCalledPerToken | atomic | positive | Value Capture | covered | generated |
| oracle/atomic::TestLexerTokenFieldReceivesToken | atomic | positive | Value Capture | covered | generated |
| oracle/atomic::TestPosAndEndPosPopulated | atomic | positive | Value Capture | covered | generated |
| oracle/atomic::TestTokensFieldRecordsConsumedTokens | atomic | positive | Value Capture | covered | generated |
| oracle/atomic::TestEBNFBasicProductionShape | atomic | positive | EBNF Projection | covered | generated |
| oracle/atomic::TestEBNFTokenReferencesLowercased | atomic | positive | EBNF Projection | covered | generated |
| oracle/atomic::TestEBNFModifiersRendered | atomic | positive | EBNF Projection | covered | generated |
| oracle/atomic::TestEBNFNegationRendered | atomic | positive | EBNF Projection | covered | generated |
| oracle/atomic::TestEBNFLookaheadGroupsRendered | atomic | positive | EBNF Projection | covered | generated |
| oracle/atomic::TestEBNFCaptureMarkersInvisible | atomic | positive | EBNF Projection | covered | generated |
| oracle/atomic::TestEBNFMultipleProductions | atomic | positive | EBNF Projection | covered | generated |
| oracle/atomic::TestUnexpectedTokenErrorShape | atomic | failure_path | Error Semantics | covered | generated |
| oracle/atomic::TestTrailingTokensRejectedWithoutAllowTrailing | atomic | positive | Parsing and Options + Error Semantics | covered | generated |
| oracle/atomic::TestLexerErrorImplementsErrorInterface | atomic | failure_path | Error Semantics + Lexing | covered | generated |
| oracle/atomic::TestErrorfBuildsPositionedError | atomic | positive | Error Semantics | covered | generated |
| oracle/atomic::TestWrapfKeepsInnerErrorPosition | atomic | positive | Error Semantics | covered | generated |
| oracle/atomic::TestWrapfUsesGivenPositionForPlainErrors | atomic | positive | Error Semantics | covered | generated |
| oracle/atomic::TestFormatErrorOmitsZeroPosition | atomic | positive | Error Semantics | covered | generated |
| oracle/atomic::TestParseErrorImplementsErrorInterface | atomic | positive | Error Semantics | covered | generated |
| oracle/atomic::TestRepetitionGuardStopsEmptyLoops | atomic | failure_path | Grammar Definition Language + State Model | covered | generated |
| oracle/atomic::TestSequenceMatchesInOrder | atomic | positive | Grammar Definition Language | covered | generated |
| oracle/atomic::TestLiteralTerminalMatchesExactValue | atomic | positive | Grammar Definition Language | covered | generated |
| oracle/atomic::TestTokenTypeReferenceMatchesWithoutCapture | atomic | positive | Grammar Definition Language | covered | generated |
| oracle/atomic::TestAlternationFirstMatchWins | atomic | positive | Grammar Definition Language | covered | generated |
| oracle/atomic::TestGroupRepetitionCollectsElements | atomic | positive | Grammar Definition Language | covered | generated |
| oracle/atomic::TestOptionalMatchesZeroOrOnce | atomic | positive | Grammar Definition Language | covered | generated |
| oracle/atomic::TestPlusRequiresAtLeastOneMatch | atomic | positive | Grammar Definition Language | covered | generated |
| oracle/atomic::TestStarAllowsZeroMatches | atomic | positive | Grammar Definition Language | covered | generated |
| oracle/atomic::TestNegationMatchesAnyOtherToken | atomic | positive | Grammar Definition Language | covered | generated |
| oracle/atomic::TestPositiveLookaheadSelectsBranchWithoutConsuming | atomic | positive | Grammar Definition Language | covered | generated |
| oracle/atomic::TestNegativeLookaheadBlocksMatch | atomic | positive | Grammar Definition Language | covered | generated |
| oracle/atomic::TestTypedLiteralMatchesValueAndType | atomic | positive | Grammar Definition Language | covered | generated |
| oracle/atomic::TestParserTagKeyWithSingleQuotes | atomic | positive | Grammar Definition Language | covered | generated |
| oracle/atomic::TestNonEmptyModifierRejectsEmptyMatch | atomic | positive | Grammar Definition Language + Error Semantics | covered | generated |
| oracle/atomic::TestCaptureMarkerDoesNotChangeAcceptance | atomic | positive | Grammar Definition Language + Cross-View Invariants (CVI-7) | covered | generated |
| oracle/atomic::TestRecursiveGrammarNests | atomic | positive | Grammar Definition Language + Grammar Compilation | covered | generated |
| oracle/atomic::TestDefaultLexerSymbolTable | atomic | positive | Lexing | covered | generated |
| oracle/atomic::TestDefaultLexerRuneTokens | atomic | positive | Lexing | covered | generated |
| oracle/atomic::TestSimpleLexerFirstMatchWins | atomic | positive | Lexing | covered | generated |
| oracle/atomic::TestSimpleLexerOrderResolvesAmbiguity | atomic | positive | Lexing | covered | generated |
| oracle/atomic::TestSimpleLexerInvalidInputError | atomic | failure_path | Lexing + Error Semantics | covered | generated |
| oracle/atomic::TestSimpleLexerSymbolNumbering | atomic | positive | Lexing | covered | generated |
| oracle/atomic::TestSimpleLexerInvalidPatternRejected | atomic | failure_path | Lexing | covered | generated |
| oracle/atomic::TestStatefulLexerPushPop | atomic | positive | Lexing | covered | generated |
| oracle/atomic::TestStatefulLexerIncludeSplicesRules | atomic | positive | Lexing | covered | generated |
| oracle/atomic::TestStatefulLexerNoMatchError | atomic | failure_path | Lexing + Error Semantics | covered | generated |
| oracle/atomic::TestConsumeAllIncludesEOF | atomic | positive | Lexing | covered | generated |
| oracle/atomic::TestSymbolsByRuneInvertsSymbols | atomic | positive | Lexing | covered | generated |
| oracle/atomic::TestPositionStringForms | atomic | positive | Lexing | covered | generated |
| oracle/atomic::TestEOFTokenConstruction | atomic | positive | Lexing | covered | generated |
| oracle/atomic::TestUpgradePeekAndNextSkipElided | atomic | positive | Lexing | covered | generated |
| oracle/atomic::TestMustWrapsDefinitionErrors | atomic | positive | Lexing | covered | generated |
| oracle/integration::TestElideDropsTokensAtEveryPosition | integration | positive | Parsing and Options | covered | generated |
| oracle/integration::TestExplicitMatchOfElidedToken | integration | positive | Parsing and Options | covered | generated |
| oracle/integration::TestUnquoteDefaultsToStringTokens | integration | positive | Parsing and Options | covered | generated |
| oracle/integration::TestUnquoteInvalidStringFailsParse | integration | failure_path | Parsing and Options + Error Semantics | covered | generated |
| oracle/integration::TestUpperNormalisesListedTokenTypes | integration | positive | Parsing and Options | covered | generated |
| oracle/integration::TestMapAppliesInOptionOrder | integration | positive | Parsing and Options | covered | generated |
| oracle/integration::TestMapWithoutSymbolsAppliesToAllTokens | integration | positive | Parsing and Options | covered | generated |
| oracle/integration::TestCaseInsensitiveLiteralsKeepInputSpelling | integration | positive | Parsing and Options | covered | generated |
| oracle/integration::TestBranchDisambiguationAcrossLookaheads | integration | positive | Parsing and Options + Grammar Definition Language | covered | generated |
| oracle/integration::TestCustomLexerDrivesParser | integration | positive | Parsing and Options + Lexing | covered | generated |
| oracle/integration::TestEntryPointsProduceIdenticalResults | integration | positive | Cross-View Invariants (CVI-2) + Parsing and Options + State Model | covered | generated |
| oracle/integration::TestEntryPointsProduceIdenticalErrors | integration | failure_path | Cross-View Invariants (CVI-2) + Error Semantics | covered | generated |
| oracle/integration::TestParserLexAgreesWithParsedTokens | integration | positive | Cross-View Invariants (CVI-3) + Grammar Compilation | covered | generated |
| oracle/integration::TestPositionCoherenceAcrossViews | integration | positive | Cross-View Invariants (CVI-4) + Value Capture | covered | generated |
| oracle/integration::TestErrorInterfaceCoherence | integration | failure_path | Cross-View Invariants (CVI-5) + Error Semantics | covered | generated |
| oracle/integration::TestSubParserAcceptsProductionFragments | integration | positive | Cross-View Invariants (CVI-6) + Grammar Compilation | covered | generated |
| oracle/integration::TestEBNFAgreesWithAcceptance | integration | positive | Cross-View Invariants (CVI-1) + EBNF Projection | covered | generated |
| oracle/integration::TestUnionDynamicTypesAndEBNF | integration | positive | Cross-View Invariants (CVI-1) + Grammar Compilation + EBNF Projection | covered | generated |
| oracle/integration::TestPartialResultReturnedOnFailure | integration | positive | Parsing and Options | covered | generated |
| oracle/integration::TestCaptureNeutralityAcrossProjections | integration | positive | Cross-View Invariants (CVI-7) + EBNF Projection | covered | generated |
| oracle/integration::TestCaptureNeutralityUnderOptions | integration | positive | Cross-View Invariants (CVI-7) + Parsing and Options | covered | generated |
| oracle/integration::TestParserIsConcurrencySafe | integration | positive | State Model | covered | generated |
| oracle/integration::TestINIConfigWorkflow | integration | positive | Representative Workflows | covered | generated |
| oracle/integration::TestRecursiveExpressionWorkflow | integration | positive | Representative Workflows + Grammar Definition Language | covered | generated |
| oracle/integration::TestStatefulInterpolationWorkflow | integration | positive | Representative Workflows + Lexing | covered | generated |
| oracle/integration::TestUnionWithCustomCaptureWorkflow | integration | positive | Representative Workflows + Grammar Compilation + Value Capture | covered | generated |
| oracle/integration::TestParseTypeWithCustomFunction | integration | positive | Grammar Compilation | covered | generated |
| oracle/integration::TestParseableNextMatchFallthrough | integration | positive | Grammar Compilation | covered | generated |
| oracle/integration::TestSideChannelsWithElision | integration | positive | Cross-View Invariants (CVI-3) + Value Capture + Parsing and Options | covered | generated |
| oracle/integration::TestAllowTrailingEnablesPrefixComposition | integration | positive | Parsing and Options | covered | generated |
| oracle/integration::TestErrorReportingAcrossInputs | integration | failure_path | Error Semantics + Cross-View Invariants (CVI-4) + Cross-View Invariants (CVI-5) | covered | generated |
| oracle/integration::TestGrammarEvolutionRoundTrip | integration | positive | Cross-View Invariants (CVI-1) + Cross-View Invariants (CVI-6) + Representative Workflows | covered | generated |

## Totals

| layer | count | positive | failure_path |
|---|---|---|---|
| atomic | 72 | 56 | 16 |
| integration | 32 | 28 | 4 |
