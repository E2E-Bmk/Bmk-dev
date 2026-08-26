# Spec Test Map

| test_nodeid | layer | spec_section | status | notes |
|---|---|---|---|---|
| atomic::ComposeAtomicTest::nonEmptyInputComposesPresentRoot | atomic | Composing Node Graphs | covered | Covers public behavior for `nonEmptyInputComposesPresentRoot`. |
| atomic::ComposeAtomicTest::emptyInputComposesEmptyOptional | atomic | Composing Node Graphs | covered | Covers public behavior for `emptyInputComposesEmptyOptional`. |
| atomic::ComposeAtomicTest::mappingRootCarriesMapTagAndType | atomic | Composing Node Graphs | covered | Covers public behavior for `mappingRootCarriesMapTagAndType`. |
| atomic::ComposeAtomicTest::tuplesExposeKeyAndValueNodes | atomic | Composing Node Graphs | covered | Covers public behavior for `tuplesExposeKeyAndValueNodes`. |
| atomic::ComposeAtomicTest::sequenceChildrenResolveIndividualTags | atomic | Composing Node Graphs | covered | Covers public behavior for `sequenceChildrenResolveIndividualTags`. |
| atomic::ComposeAtomicTest::plainScalarsReportPlainStyle | atomic | Composing Node Graphs | covered | Covers public behavior for `plainScalarsReportPlainStyle`. |
| atomic::ComposeAtomicTest::anchorsSurfaceOnAnchoredNode | atomic | Composing Node Graphs | covered | Covers public behavior for `anchorsSurfaceOnAnchoredNode`. |
| atomic::ComposeAtomicTest::standardTagTextForms | atomic | Composing Node Graphs | covered | Covers public behavior for `standardTagTextForms`. |
| atomic::ComposeAtomicTest::aliasComposesAsAnchoredNodeInstance | atomic | Composing Node Graphs | covered | Covers public behavior for `aliasComposesAsAnchoredNodeInstance`. |
| atomic::DumpDefaultsAtomicTest::autoStyleBlocksTopLevelFlowsNested | atomic | Dumping Java Objects | covered | Covers public behavior for `autoStyleBlocksTopLevelFlowsNested`. |
| atomic::DumpDefaultsAtomicTest::topLevelListRendersFlow | atomic | Dumping Java Objects | covered | Covers public behavior for `topLevelListRendersFlow`. |
| atomic::DumpDefaultsAtomicTest::plainScalarRendersWithNewline | atomic | Dumping Java Objects | covered | Covers public behavior for `plainScalarRendersWithNewline`. |
| atomic::DumpDefaultsAtomicTest::nestedMappingRendersFlow | atomic | Dumping Java Objects | covered | Covers public behavior for `nestedMappingRendersFlow`. |
| atomic::DumpDefaultsAtomicTest::nullDocumentRendersNullText | atomic | Dumping Java Objects | covered | Covers public behavior for `nullDocumentRendersNullText`. |
| atomic::DumpDefaultsAtomicTest::scalarTypesRenderPlain | atomic | Dumping Java Objects | covered | Covers public behavior for `scalarTypesRenderPlain`. |
| atomic::DumpDefaultsAtomicTest::booleanShapedStringIsQuoted | atomic | Dumping Java Objects | covered | Covers public behavior for `booleanShapedStringIsQuoted`. |
| atomic::DumpDefaultsAtomicTest::numericShapedStringIsQuoted | atomic | Dumping Java Objects | covered | Covers public behavior for `numericShapedStringIsQuoted`. |
| atomic::DumpDefaultsAtomicTest::mappingShapedStringIsQuoted | atomic | Dumping Java Objects | covered | Covers public behavior for `mappingShapedStringIsQuoted`. |
| atomic::DumpDefaultsAtomicTest::emptyStringRendersQuotedEmpty | atomic | Dumping Java Objects | covered | Covers public behavior for `emptyStringRendersQuotedEmpty`. |
| atomic::DumpDefaultsAtomicTest::bigIntegersRenderPlain | atomic | Dumping Java Objects | covered | Covers public behavior for `bigIntegersRenderPlain`. |
| atomic::DumpDefaultsAtomicTest::nonStringKeysRenderThroughScalarRules | atomic | Dumping Java Objects | covered | Covers public behavior for `nonStringKeysRenderThroughScalarRules`. |
| atomic::DumpDefaultsAtomicTest::dumpAllMarksDocumentsAfterFirst | atomic | Dumping Java Objects | covered | Covers public behavior for `dumpAllMarksDocumentsAfterFirst`. |
| atomic::DumpSettingsAtomicTest::blockStyleLaysOutLineByLine | atomic | Dump Settings and Presentation | covered | Covers public behavior for `blockStyleLaysOutLineByLine`. |
| atomic::DumpSettingsAtomicTest::flowStyleRendersInline | atomic | Dump Settings and Presentation | covered | Covers public behavior for `flowStyleRendersInline`. |
| atomic::DumpSettingsAtomicTest::explicitStartAndEndMarkers | atomic | Dump Settings and Presentation | covered | Covers public behavior for `explicitStartAndEndMarkers`. |
| atomic::DumpSettingsAtomicTest::canonicalFormWithExplicitTags | atomic | Dump Settings and Presentation | covered | Covers public behavior for `canonicalFormWithExplicitTags`. |
| atomic::DumpSettingsAtomicTest::singleQuotedScalarStyle | atomic | Dump Settings and Presentation | covered | Covers public behavior for `singleQuotedScalarStyle`. |
| atomic::DumpSettingsAtomicTest::doubleQuotedScalarStyle | atomic | Dump Settings and Presentation | covered | Covers public behavior for `doubleQuotedScalarStyle`. |
| atomic::DumpSettingsAtomicTest::literalStyleForMultiLineStrings | atomic | Dump Settings and Presentation | covered | Covers public behavior for `literalStyleForMultiLineStrings`. |
| atomic::DumpSettingsAtomicTest::indentWidthAppliesToBlockNesting | atomic | Dump Settings and Presentation | covered | Covers public behavior for `indentWidthAppliesToBlockNesting`. |
| atomic::DumpSettingsAtomicTest::widthWrapsLongPlainScalars | atomic | Dump Settings and Presentation | covered | Covers public behavior for `widthWrapsLongPlainScalars`. |
| atomic::DumpSettingsAtomicTest::multiLineFlowSpreadsFlowCollections | atomic | Dump Settings and Presentation | covered | Covers public behavior for `multiLineFlowSpreadsFlowCollections`. |
| atomic::DumpSettingsAtomicTest::escapeStyleRendersEscapes | atomic | Dump Settings and Presentation | covered | Covers public behavior for `escapeStyleRendersEscapes`. |
| atomic::DumpSettingsAtomicTest::binaryStyleRendersBase64Block | atomic | Dump Settings and Presentation | covered | Covers public behavior for `binaryStyleRendersBase64Block`. |
| atomic::DumpSettingsAtomicTest::settingsObjectIsReusable | atomic | Dump Settings and Presentation | covered | Covers public behavior for `settingsObjectIsReusable`. |
| atomic::LoadScalarsAtomicTest::mappingLoadsAsInsertionOrderedMap | atomic | Loading YAML Documents | covered | Covers public behavior for `mappingLoadsAsInsertionOrderedMap`. |
| atomic::LoadScalarsAtomicTest::scalarValuesResolveToSchemaTypes | atomic | Loading YAML Documents | covered | Covers public behavior for `scalarValuesResolveToSchemaTypes`. |
| atomic::LoadScalarsAtomicTest::sequenceLoadsAsList | atomic | Loading YAML Documents | covered | Covers public behavior for `sequenceLoadsAsList`. |
| atomic::LoadScalarsAtomicTest::nestedStructuresLoadRecursively | atomic | Loading YAML Documents | covered | Covers public behavior for `nestedStructuresLoadRecursively`. |
| atomic::LoadScalarsAtomicTest::emptyInputLoadsAsNull | atomic | Loading YAML Documents | covered | Covers public behavior for `emptyInputLoadsAsNull`. |
| atomic::LoadScalarsAtomicTest::plainScalarDocumentLoadsAsScalar | atomic | Loading YAML Documents | covered | Covers public behavior for `plainScalarDocumentLoadsAsScalar`. |
| atomic::LoadScalarsAtomicTest::integerWideningAcrossRanges | atomic | Loading YAML Documents | covered | Covers public behavior for `integerWideningAcrossRanges`. |
| atomic::LoadScalarsAtomicTest::keysResolveLikeScalars | atomic | Loading YAML Documents | covered | Covers public behavior for `keysResolveLikeScalars`. |
| atomic::LoadScalarsAtomicTest::readerAndStreamEntryPointsAgree | atomic | Loading YAML Documents | covered | Covers public behavior for `readerAndStreamEntryPointsAgree`. |
| atomic::LoadScalarsAtomicTest::loadAllIteratesDocumentsInOrder | atomic | Loading YAML Documents | covered | Covers public behavior for `loadAllIteratesDocumentsInOrder`. |
| atomic::LoadScalarsAtomicTest::aliasResolvesToAnchoredInstance | atomic | Loading YAML Documents | covered | Covers public behavior for `aliasResolvesToAnchoredInstance`. |
| atomic::LoadSettingsErrorsAtomicTest::duplicateKeyRaisesByDefault | atomic | Error Semantics | covered | Covers public behavior for `duplicateKeyRaisesByDefault`. |
| atomic::LoadSettingsErrorsAtomicTest::allowedDuplicateKeysKeepLastValue | atomic | Loading YAML Documents | covered | Covers public behavior for `allowedDuplicateKeysKeepLastValue`. |
| atomic::LoadSettingsErrorsAtomicTest::unclosedFlowCollectionRaisesParserException | atomic | Error Semantics | covered | Covers public behavior for `unclosedFlowCollectionRaisesParserException`. |
| atomic::LoadSettingsErrorsAtomicTest::reservedIndicatorRaisesScannerException | atomic | Error Semantics | covered | Covers public behavior for `reservedIndicatorRaisesScannerException`. |
| atomic::LoadSettingsErrorsAtomicTest::explicitTagOnUnconstructibleScalarRaises | atomic | Error Semantics | covered | Covers public behavior for `explicitTagOnUnconstructibleScalarRaises`. |
| atomic::LoadSettingsErrorsAtomicTest::aliasBudgetEnforcesConfiguredMaximum | atomic | Loading YAML Documents | covered | Covers public behavior for `aliasBudgetEnforcesConfiguredMaximum`. |
| atomic::LoadSettingsErrorsAtomicTest::labelAppearsInParseErrorMessages | atomic | Load Settings | covered | Covers public behavior for `labelAppearsInParseErrorMessages`. |
| atomic::LoadSettingsErrorsAtomicTest::problemMarksCarryZeroBasedLines | atomic | Error Semantics | covered | Covers public behavior for `problemMarksCarryZeroBasedLines`. |
| atomic::LoadSettingsErrorsAtomicTest::markedExceptionsExtendEngineRoot | atomic | Error Semantics | covered | Covers public behavior for `markedExceptionsExtendEngineRoot`. |
| atomic::LoadSettingsErrorsAtomicTest::duplicateKeyExceptionIsMarked | atomic | Error Semantics | covered | Covers public behavior for `duplicateKeyExceptionIsMarked`. |
| atomic::SchemaResolutionAtomicTest::jsonSchemaResolvesNullLiteral | atomic | Schemas and Scalar Resolution | covered | Covers public behavior for `jsonSchemaResolvesNullLiteral`. |
| atomic::SchemaResolutionAtomicTest::jsonSchemaResolvesEmptyValueToNull | atomic | Schemas and Scalar Resolution | covered | Covers public behavior for `jsonSchemaResolvesEmptyValueToNull`. |
| atomic::SchemaResolutionAtomicTest::tildeStaysStringUnderJsonSchema | atomic | Schemas and Scalar Resolution | covered | Covers public behavior for `tildeStaysStringUnderJsonSchema`. |
| atomic::SchemaResolutionAtomicTest::yamlOneOneBooleansStayStrings | atomic | Schemas and Scalar Resolution | covered | Covers public behavior for `yamlOneOneBooleansStayStrings`. |
| atomic::SchemaResolutionAtomicTest::hexStaysStringUnderJsonSchema | atomic | Schemas and Scalar Resolution | covered | Covers public behavior for `hexStaysStringUnderJsonSchema`. |
| atomic::SchemaResolutionAtomicTest::coreSchemaResolvesTildeToNull | atomic | Schemas and Scalar Resolution | covered | Covers public behavior for `coreSchemaResolvesTildeToNull`. |
| atomic::SchemaResolutionAtomicTest::coreSchemaResolvesHexAndOctal | atomic | Schemas and Scalar Resolution | covered | Covers public behavior for `coreSchemaResolvesHexAndOctal`. |
| atomic::SchemaResolutionAtomicTest::coreSchemaResolvesExponentAndInfinity | atomic | Schemas and Scalar Resolution | covered | Covers public behavior for `coreSchemaResolvesExponentAndInfinity`. |
| atomic::SchemaResolutionAtomicTest::coreSchemaResolvesCaseVariantBooleans | atomic | Schemas and Scalar Resolution | covered | Covers public behavior for `coreSchemaResolvesCaseVariantBooleans`. |
| atomic::SchemaResolutionAtomicTest::dateLikeScalarsStayStrings | atomic | Schemas and Scalar Resolution | covered | Covers public behavior for `dateLikeScalarsStayStrings`. |
| integration::ComposeLoadAgreementIntegrationTest::scalarTagsCorrespondToLoadedTypes | integration | Cross-View Invariants | covered | Covers public behavior for `scalarTagsCorrespondToLoadedTypes`. |
| integration::ComposeLoadAgreementIntegrationTest::nodeStructureMirrorsLoadedStructure | integration | Cross-View Invariants | covered | Covers public behavior for `nodeStructureMirrorsLoadedStructure`. |
| integration::ComposeLoadAgreementIntegrationTest::keyOrderInNodeGraphIsDocumentOrder | integration | Cross-View Invariants | covered | Covers public behavior for `keyOrderInNodeGraphIsDocumentOrder`. |
| integration::ComposeLoadAgreementIntegrationTest::scalarNodeValuesAreRawText | integration | Composing Node Graphs | covered | Covers public behavior for `scalarNodeValuesAreRawText`. |
| integration::ComposeLoadAgreementIntegrationTest::aliasIdentityAgreesBetweenGraphAndObjects | integration | Cross-View Invariants | covered | Covers public behavior for `aliasIdentityAgreesBetweenGraphAndObjects`. |
| integration::ComposeLoadAgreementIntegrationTest::composeEmptiesExactlyWhenLoadIsNull | integration | Cross-View Invariants | covered | Covers public behavior for `composeEmptiesExactlyWhenLoadIsNull`. |
| integration::ComposeLoadAgreementIntegrationTest::dumpedTextComposesBackToMatchingNodeTypes | integration | Composing Node Graphs | covered | Covers public behavior for `dumpedTextComposesBackToMatchingNodeTypes`. |
| integration::ComposeLoadAgreementIntegrationTest::quotedStringsComposeWithStringTags | integration | Cross-View Invariants | covered | Covers public behavior for `quotedStringsComposeWithStringTags`. |
| integration::RoundTripIntegrationTest::defaultRoundTripPreservesValues | integration | Cross-View Invariants | covered | Covers public behavior for `defaultRoundTripPreservesValues`. |
| integration::RoundTripIntegrationTest::roundTripHoldsUnderBlockStyle | integration | Cross-View Invariants | covered | Covers public behavior for `roundTripHoldsUnderBlockStyle`. |
| integration::RoundTripIntegrationTest::roundTripHoldsUnderFlowStyle | integration | Cross-View Invariants | covered | Covers public behavior for `roundTripHoldsUnderFlowStyle`. |
| integration::RoundTripIntegrationTest::quotingKeepsAmbiguousStringsTypeFaithful | integration | Cross-View Invariants | covered | Covers public behavior for `quotingKeepsAmbiguousStringsTypeFaithful`. |
| integration::RoundTripIntegrationTest::sharedReferencesDumpAsAnchorsAndReloadShared | integration | Cross-View Invariants | covered | Covers public behavior for `sharedReferencesDumpAsAnchorsAndReloadShared`. |
| integration::RoundTripIntegrationTest::dumpAllAndLoadAllAreInverse | integration | Cross-View Invariants | covered | Covers public behavior for `dumpAllAndLoadAllAreInverse`. |
| integration::RoundTripIntegrationTest::dumpAllOfOneElementEqualsDumpToString | integration | Cross-View Invariants | covered | Covers public behavior for `dumpAllOfOneElementEqualsDumpToString`. |
| integration::RoundTripIntegrationTest::scalarStylesChangeTextNotValues | integration | Cross-View Invariants | covered | Covers public behavior for `scalarStylesChangeTextNotValues`. |
| integration::RoundTripIntegrationTest::canonicalFormReloadsToSameValues | integration | Cross-View Invariants | covered | Covers public behavior for `canonicalFormReloadsToSameValues`. |
| integration::RoundTripIntegrationTest::loadingAndDumpingAreDeterministic | integration | State Model | covered | Covers public behavior for `loadingAndDumpingAreDeterministic`. |
| integration::SettingsInteractionIntegrationTest::markersComposeWithFlowStyle | integration | Dump Settings and Presentation | covered | Covers public behavior for `markersComposeWithFlowStyle`. |
| integration::SettingsInteractionIntegrationTest::indentationInteractsWithBlockNesting | integration | Dump Settings and Presentation | covered | Covers public behavior for `indentationInteractsWithBlockNesting`. |
| integration::SettingsInteractionIntegrationTest::widthWrappedOutputReloadsSameValue | integration | Cross-View Invariants | covered | Covers public behavior for `widthWrappedOutputReloadsSameValue`. |
| integration::SettingsInteractionIntegrationTest::multiLineFlowOutputReloadsSameValue | integration | Cross-View Invariants | covered | Covers public behavior for `multiLineFlowOutputReloadsSameValue`. |
| integration::SettingsInteractionIntegrationTest::sameTextLoadsDifferentlyPerSchema | integration | Schemas and Scalar Resolution | covered | Covers public behavior for `sameTextLoadsDifferentlyPerSchema`. |
| integration::SettingsInteractionIntegrationTest::coreSchemaValuesRoundTripThroughDump | integration | Cross-View Invariants | covered | Covers public behavior for `coreSchemaValuesRoundTripThroughDump`. |
| integration::SettingsInteractionIntegrationTest::labelAndMarksSurviveThroughLabeledPipeline | integration | Load Settings | covered | Covers public behavior for `labelAndMarksSurviveThroughLabeledPipeline`. |
| integration::SettingsInteractionIntegrationTest::aliasBudgetInteractsWithDocumentShape | integration | Loading YAML Documents | covered | Covers public behavior for `aliasBudgetInteractsWithDocumentShape`. |
| integration::SettingsInteractionIntegrationTest::oneSettingsObjectDrivesEquivalentPipelines | integration | State Model | covered | Covers public behavior for `oneSettingsObjectDrivesEquivalentPipelines`. |
