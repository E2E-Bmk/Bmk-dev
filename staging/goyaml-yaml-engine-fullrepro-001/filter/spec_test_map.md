# spec_test_map — goyaml-yaml-engine-fullrepro-001

oracle_version: 2026-08-25T01
oracle_source: generated_only

All tests generated (Track B); upstream suite fully excluded (see
rewrite_audit.md). Spec: spec.md (v1, two spec_error corrections applied
during Stage 3: validator annotation requires a slice of FieldError
elements; token origin concatenation drops trailing newlines after a final
plain scalar). Totals: 134 tests = 97 atomic + 37 integration.
Atomic positive share: 82/97 = 84% (>= 60% floor); zero no_check
in both layers. Every behavior section >= 4 tests, Error Semantics >= 4,
Representative Workflows >= 4, each of the eight Cross-View Invariants
covered by 2 integration tests (CVI numbers in the spec_section column).

| test_nodeid | layer | assertion_kind | spec_section | status | source |
|---|---|---|---|---|---|
| oracle/atomic::TestAliasResolvesToAnchorValue | atomic | positive | Anchors, Aliases, and Merge Keys | covered | generated |
| oracle/atomic::TestAliasSharesContainerIdentity | atomic | positive | Anchors, Aliases, and Merge Keys | covered | generated |
| oracle/atomic::TestUndefinedAliasFails | atomic | failure_path | Anchors, Aliases, and Merge Keys + Error Semantics | covered | generated |
| oracle/atomic::TestMergeKeySplice | atomic | positive | Anchors, Aliases, and Merge Keys | covered | generated |
| oracle/atomic::TestAnchorAliasStructTags | atomic | positive | Anchors, Aliases, and Merge Keys | covered | generated |
| oracle/atomic::TestCommentToMapCollectsPositions | atomic | positive | Comment Association | covered | generated |
| oracle/atomic::TestCommentToMapCollectsFootPosition | atomic | positive | Comment Association | covered | generated |
| oracle/atomic::TestCommentConstructorsEmit | atomic | positive | Comment Association | covered | generated |
| oracle/atomic::TestMultiLineHeadComment | atomic | positive | Comment Association | covered | generated |
| oracle/atomic::TestYAMLToJSONScalarsAndOrder | atomic | positive | Format Conversion | covered | generated |
| oracle/atomic::TestYAMLToJSONResolvesAnchorsAndMerge | atomic | positive | Format Conversion + Anchors, Aliases, and Merge Keys | covered | generated |
| oracle/atomic::TestJSONToYAMLBlockStyle | atomic | positive | Format Conversion | covered | generated |
| oracle/atomic::TestConverterErrorsAnnotated | atomic | failure_path | Format Conversion + Error Semantics | covered | generated |
| oracle/atomic::TestEncodeKeyDerivation | atomic | positive | Encoding from Go Values | covered | generated |
| oracle/atomic::TestEncodeMapKeyOrdering | atomic | positive | Encoding from Go Values | covered | generated |
| oracle/atomic::TestEncodeNilAsNull | atomic | positive | Encoding from Go Values | covered | generated |
| oracle/atomic::TestQuoteOtherScalarSpellings | atomic | positive | Encoding from Go Values | covered | generated |
| oracle/atomic::TestQuoteBooleanLikeWords | atomic | positive | Encoding from Go Values | covered | generated |
| oracle/atomic::TestQuoteConstructStarters | atomic | positive | Encoding from Go Values | covered | generated |
| oracle/atomic::TestQuoteEdgeAndPlainStrings | atomic | positive | Encoding from Go Values | covered | generated |
| oracle/atomic::TestMultilineStringsUseLiteralBlocks | atomic | positive | Encoding from Go Values | covered | generated |
| oracle/atomic::TestUseSingleQuoteOption | atomic | positive | Encoding from Go Values | covered | generated |
| oracle/atomic::TestFlowAndJSONStyles | atomic | positive | Encoding from Go Values | covered | generated |
| oracle/atomic::TestIndentAndIndentSequence | atomic | positive | Encoding from Go Values | covered | generated |
| oracle/atomic::TestAutoIntOption | atomic | positive | Encoding from Go Values | covered | generated |
| oracle/atomic::TestOmitEmptyAndOmitZero | atomic | positive | Encoding from Go Values | covered | generated |
| oracle/atomic::TestEncoderMultipleDocuments | atomic | positive | Encoding from Go Values | covered | generated |
| oracle/atomic::TestValueToNodeRendersLikeMarshal | atomic | positive | Encoding from Go Values | covered | generated |
| oracle/atomic::TestExportedConstants | atomic | positive | Encoding from Go Values | covered | generated |
| oracle/atomic::TestErrorMessageLineColumnPrefix | atomic | failure_path | Error Semantics | covered | generated |
| oracle/atomic::TestFormatErrorSourceExcerpt | atomic | positive | Error Semantics | covered | generated |
| oracle/atomic::TestSyntaxErrorType | atomic | failure_path | Error Semantics | covered | generated |
| oracle/atomic::TestDuplicateKeyMessageShape | atomic | failure_path | Error Semantics | covered | generated |
| oracle/atomic::TestUnknownFieldErrorType | atomic | failure_path | Error Semantics + Decoding into Go Values | covered | generated |
| oracle/atomic::TestTypeErrorFields | atomic | failure_path | Error Semantics | covered | generated |
| oracle/atomic::TestOverflowErrorType | atomic | failure_path | Error Semantics | covered | generated |
| oracle/atomic::TestYamlErrorInterface | atomic | failure_path | Error Semantics | covered | generated |
| oracle/atomic::TestBytesMarshalerSplice | atomic | positive | Custom Hooks | covered | generated |
| oracle/atomic::TestInterfaceMarshaler | atomic | positive | Custom Hooks | covered | generated |
| oracle/atomic::TestBytesUnmarshalerReceivesRawText | atomic | positive | Custom Hooks | covered | generated |
| oracle/atomic::TestInterfaceUnmarshalerDecodeFunc | atomic | positive | Custom Hooks | covered | generated |
| oracle/atomic::TestNodeUnmarshalerReceivesNode | atomic | positive | Custom Hooks | covered | generated |
| oracle/atomic::TestCustomMarshalerAndUnmarshalerOptions | atomic | positive | Custom Hooks | covered | generated |
| oracle/atomic::TestGlobalRegistrationAndPrecedence | atomic | positive | Custom Hooks | covered | generated |
| oracle/atomic::TestJSONInteropOptions | atomic | positive | Custom Hooks | covered | generated |
| oracle/atomic::TestValidatorContract | atomic | failure_path | Custom Hooks + Error Semantics | covered | generated |
| oracle/atomic::TestTokenizeStructuralTypes | atomic | positive | Syntax Tree and Tokens | covered | generated |
| oracle/atomic::TestTokenizeScalarKinds | atomic | positive | Syntax Tree and Tokens | covered | generated |
| oracle/atomic::TestTokenValueVersusOrigin | atomic | positive | Syntax Tree and Tokens | covered | generated |
| oracle/atomic::TestTokenOriginsConcatenate | atomic | positive | Syntax Tree and Tokens | covered | generated |
| oracle/atomic::TestTokenPositions | atomic | positive | Syntax Tree and Tokens | covered | generated |
| oracle/atomic::TestDisallowUnknownField | atomic | failure_path | Decoding into Go Values + Error Semantics | covered | generated |
| oracle/atomic::TestStrictMatchesDisallowUnknownField | atomic | failure_path | Decoding into Go Values + Error Semantics | covered | generated |
| oracle/atomic::TestDuplicateKeyRejectedByDefault | atomic | failure_path | Decoding into Go Values + Error Semantics | covered | generated |
| oracle/atomic::TestAllowDuplicateMapKeyLastWins | atomic | positive | Decoding into Go Values | covered | generated |
| oracle/atomic::TestUseOrderedMapDecode | atomic | positive | Decoding into Go Values | covered | generated |
| oracle/atomic::TestUseJSONUnmarshaler | atomic | positive | Decoding into Go Values | covered | generated |
| oracle/atomic::TestRawMessageCaptureAndSplice | atomic | positive | Decoding into Go Values | covered | generated |
| oracle/atomic::TestDecoderStreamAndEOF | atomic | positive | Decoding into Go Values + Error Semantics | covered | generated |
| oracle/atomic::TestNodeToValueDecodesNode | atomic | positive | Decoding into Go Values | covered | generated |
| oracle/atomic::TestDecodeFromNode | atomic | positive | Decoding into Go Values | covered | generated |
| oracle/atomic::TestParseBytesDocumentCount | atomic | positive | Syntax Tree and Tokens | covered | generated |
| oracle/atomic::TestParseCommentsMode | atomic | positive | Syntax Tree and Tokens | covered | generated |
| oracle/atomic::TestParserAllowDuplicateMapKey | atomic | positive | Syntax Tree and Tokens | covered | generated |
| oracle/atomic::TestParseTokensAndParseFile | atomic | positive | Syntax Tree and Tokens | covered | generated |
| oracle/atomic::TestNodeTypeNames | atomic | positive | Syntax Tree and Tokens | covered | generated |
| oracle/atomic::TestNodeStringAndGetToken | atomic | positive | Syntax Tree and Tokens | covered | generated |
| oracle/atomic::TestFileStringMultiDoc | atomic | positive | Syntax Tree and Tokens | covered | generated |
| oracle/atomic::TestAstWalkVisitsAndStops | atomic | positive | Syntax Tree and Tokens | covered | generated |
| oracle/atomic::TestAstMergeMappings | atomic | positive | Syntax Tree and Tokens | covered | generated |
| oracle/atomic::TestPathStringParseAndRender | atomic | positive | Path Queries | covered | generated |
| oracle/atomic::TestPathBuilderBuildsCanonicalString | atomic | positive | Path Queries | covered | generated |
| oracle/atomic::TestPathRead | atomic | positive | Path Queries | covered | generated |
| oracle/atomic::TestPathReadNode | atomic | positive | Path Queries | covered | generated |
| oracle/atomic::TestPathFilterGoValue | atomic | positive | Path Queries | covered | generated |
| oracle/atomic::TestPathFilterFileAndNode | atomic | positive | Path Queries | covered | generated |
| oracle/atomic::TestInvalidPathString | atomic | failure_path | Path Queries + Error Semantics | covered | generated |
| oracle/atomic::TestPathNotFound | atomic | failure_path | Path Queries + Error Semantics | covered | generated |
| oracle/atomic::TestAnnotateSource | atomic | positive | Path Queries | covered | generated |
| oracle/atomic::TestScalarUnsignedIntegerForms | atomic | positive | Decoding into Go Values | covered | generated |
| oracle/atomic::TestScalarNegativeIntegerIsInt64 | atomic | positive | Decoding into Go Values | covered | generated |
| oracle/atomic::TestScalarFloatForms | atomic | positive | Decoding into Go Values | covered | generated |
| oracle/atomic::TestScalarExponentWithoutPoint | atomic | positive | Decoding into Go Values | covered | generated |
| oracle/atomic::TestScalarInfinityAndNaN | atomic | positive | Decoding into Go Values | covered | generated |
| oracle/atomic::TestScalarBooleanSpellings | atomic | positive | Decoding into Go Values | covered | generated |
| oracle/atomic::TestScalarNullForms | atomic | positive | Decoding into Go Values | covered | generated |
| oracle/atomic::TestQuotedScalarsAlwaysStrings | atomic | positive | Decoding into Go Values | covered | generated |
| oracle/atomic::TestDateLikeScalarStaysString | atomic | positive | Decoding into Go Values | covered | generated |
| oracle/atomic::TestUntypedContainerShapes | atomic | positive | Decoding into Go Values | covered | generated |
| oracle/atomic::TestLiteralBlockDecode | atomic | positive | Decoding into Go Values | covered | generated |
| oracle/atomic::TestTagNamedFieldMatching | atomic | positive | Decoding into Go Values | covered | generated |
| oracle/atomic::TestUntaggedFieldLowercasedKey | atomic | positive | Decoding into Go Values | covered | generated |
| oracle/atomic::TestJSONTagFallback | atomic | positive | Decoding into Go Values | covered | generated |
| oracle/atomic::TestDashTagExcludesField | atomic | positive | Decoding into Go Values | covered | generated |
| oracle/atomic::TestUnmatchedKeysIgnoredByDefault | atomic | positive | Decoding into Go Values | covered | generated |
| oracle/atomic::TestInlineStructDecode | atomic | positive | Decoding into Go Values | covered | generated |
| oracle/atomic::TestInlineStructEncode | atomic | positive | Encoding from Go Values | covered | generated |
| oracle/integration::TestTokenOriginsReproduceSourceBattery | integration | positive | Cross-View Invariants 1 + Syntax Tree and Tokens | covered | generated |
| oracle/integration::TestTokenPositionsAgreeWithSource | integration | positive | Cross-View Invariants 1 + Syntax Tree and Tokens | covered | generated |
| oracle/integration::TestValueToNodeAgreesWithMarshal | integration | positive | Cross-View Invariants 2 + Encoding from Go Values | covered | generated |
| oracle/integration::TestParseBackNodeToValueAgreesWithUnmarshal | integration | positive | Cross-View Invariants 2 + Decoding into Go Values | covered | generated |
| oracle/integration::TestOrderedRoundTripStable | integration | positive | Cross-View Invariants 3 + Decoding into Go Values | covered | generated |
| oracle/integration::TestOrderedRoundTripPreservesKeyOrder | integration | positive | Cross-View Invariants 3 + Encoding from Go Values | covered | generated |
| oracle/integration::TestPathReadAgreesWithFullDecode | integration | positive | Cross-View Invariants 4 + Path Queries | covered | generated |
| oracle/integration::TestReadNodeAgreesWithFilterFile | integration | positive | Cross-View Invariants 4 + Path Queries | covered | generated |
| oracle/integration::TestReplaceIsLocal | integration | positive | Cross-View Invariants 5 + Path Queries | covered | generated |
| oracle/integration::TestMergePreservesExistingKeys | integration | positive | Cross-View Invariants 5 + Path Queries | covered | generated |
| oracle/integration::TestCommentRoundTripPositions | integration | positive | Cross-View Invariants 6 + Comment Association | covered | generated |
| oracle/integration::TestCommentRoundTripValueEquality | integration | positive | Cross-View Invariants 6 + Comment Association | covered | generated |
| oracle/integration::TestYAMLToJSONAgreesWithDecode | integration | positive | Cross-View Invariants 7 + Format Conversion | covered | generated |
| oracle/integration::TestConverterRoundTripDecodesSame | integration | positive | Cross-View Invariants 7 + Format Conversion | covered | generated |
| oracle/integration::TestErrorLineColumnLocatesToken | integration | positive | Cross-View Invariants 8 + Error Semantics | covered | generated |
| oracle/integration::TestFormatErrorCaretPointsIntoSource | integration | positive | Cross-View Invariants 8 + Error Semantics | covered | generated |
| oracle/integration::TestAnchorSharingAcrossViews | integration | positive | Anchors, Aliases, and Merge Keys + Format Conversion | covered | generated |
| oracle/integration::TestAnchorAliasTagRoundTrip | integration | positive | Anchors, Aliases, and Merge Keys + Syntax Tree and Tokens | covered | generated |
| oracle/integration::TestMultiDocEncodeDecodeRoundTrip | integration | positive | Decoding into Go Values + Encoding from Go Values | covered | generated |
| oracle/integration::TestRawMessageRoundTrip | integration | positive | Decoding into Go Values + Encoding from Go Values | covered | generated |
| oracle/integration::TestNodeToValueOptionsParity | integration | positive | Decoding into Go Values + Syntax Tree and Tokens | covered | generated |
| oracle/integration::TestDecodeFromNodeAgreesWithUnmarshal | integration | positive | Decoding into Go Values + Syntax Tree and Tokens | covered | generated |
| oracle/integration::TestQuotingRoundTripBattery | integration | positive | Encoding from Go Values + Decoding into Go Values | covered | generated |
| oracle/integration::TestScalarTypingThroughConverters | integration | positive | Format Conversion + Decoding into Go Values | covered | generated |
| oracle/integration::TestInlineStructRoundTrip | integration | positive | Decoding into Go Values + Encoding from Go Values | covered | generated |
| oracle/integration::TestStreamDecoderWithOptions | integration | positive | Decoding into Go Values | covered | generated |
| oracle/integration::TestPathRewriteThenReRead | integration | positive | Path Queries + Syntax Tree and Tokens | covered | generated |
| oracle/integration::TestTokensToTreeToValuePipeline | integration | positive | Syntax Tree and Tokens + State Model | covered | generated |
| oracle/integration::TestCommentMapThroughEncoder | integration | positive | Comment Association + Encoding from Go Values | covered | generated |
| oracle/integration::TestValueToNodeUsableInRewrite | integration | positive | Encoding from Go Values + Path Queries | covered | generated |
| oracle/integration::TestUndefinedAliasAnnotatedPosition | integration | failure_path | Anchors, Aliases, and Merge Keys + Error Semantics | covered | generated |
| oracle/integration::TestMapSlicePivotRoundTrip | integration | positive | Decoding into Go Values + Encoding from Go Values | covered | generated |
| oracle/integration::TestAstMergeThenDecode | integration | positive | Syntax Tree and Tokens + Decoding into Go Values | covered | generated |
| oracle/integration::TestConfigLoadingWorkflow | integration | positive | Representative Workflows + Custom Hooks | covered | generated |
| oracle/integration::TestConfigLoadingRejectsUnknownKey | integration | failure_path | Representative Workflows + Error Semantics | covered | generated |
| oracle/integration::TestSurgicalRewriteWorkflow | integration | positive | Representative Workflows + Path Queries | covered | generated |
| oracle/integration::TestCommentPreservingTransformWorkflow | integration | positive | Representative Workflows + Comment Association | covered | generated |

Total: 134 | kept (covered): 134 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 134
