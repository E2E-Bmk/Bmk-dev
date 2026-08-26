# Spec Test Map

| test_nodeid | layer | spec_section | status | notes |
|---|---|---|---|---|
| atomic::management::attrGetSetAndChaining | atomic | (unmapped) | covered | Covers public behavior for `attrGetSetAndChaining`. |
| atomic::management::missingAttributeIsEmptyString | atomic | (unmapped) | covered | Covers public behavior for `missingAttributeIsEmptyString`. |
| atomic::management::hasAttrAndRemoveAttr | atomic | (unmapped) | covered | Covers public behavior for `hasAttrAndRemoveAttr`. |
| atomic::management::attributesCollectionIterationOrder | atomic | (unmapped) | covered | Covers public behavior for `attributesCollectionIterationOrder`. |
| atomic::management::booleanAttributeValueAndRendering | atomic | (unmapped) | covered | Covers public behavior for `booleanAttributeValueAndRendering`. |
| atomic::management::idAccessor | atomic | (unmapped) | covered | Covers public behavior for `idAccessor`. |
| atomic::management::classListManagement | atomic | (unmapped) | covered | Covers public behavior for `classListManagement`. |
| atomic::management::toggleClassAddsAndRemoves | atomic | (unmapped) | covered | Covers public behavior for `toggleClassAddsAndRemoves`. |
| atomic::management::datasetExposesDataAttributes | atomic | (unmapped) | covered | Covers public behavior for `datasetExposesDataAttributes`. |
| atomic::management::absUrlResolvesAgainstBase | atomic | (unmapped) | covered | Covers public behavior for `absUrlResolvesAgainstBase`. |
| atomic::management::absPrefixEqualsAbsUrl | atomic | (unmapped) | covered | Covers public behavior for `absPrefixEqualsAbsUrl`. |
| atomic::management::absUrlWithoutBaseIsEmpty | atomic | (unmapped) | covered | Covers public behavior for `absUrlWithoutBaseIsEmpty`. |
| atomic::management::emptyAttributeKeyRaises | atomic | (unmapped) | covered | Covers public behavior for `emptyAttributeKeyRaises`. |
| atomic::OutputSettingsAtomicTest::prettyPrintIsDefaultWithOneSpaceIndent | atomic | Serialization and Output Settings | covered | Covers public behavior for `prettyPrintIsDefaultWithOneSpaceIndent`. |
| atomic::OutputSettingsAtomicTest::prettyPrintOffSerializesCompact | atomic | Serialization and Output Settings | covered | Covers public behavior for `prettyPrintOffSerializesCompact`. |
| atomic::OutputSettingsAtomicTest::defaultSettingsProjection | atomic | Serialization and Output Settings | covered | Covers public behavior for `defaultSettingsProjection`. |
| atomic::OutputSettingsAtomicTest::indentAmountControlsIndentWidth | atomic | Serialization and Output Settings | covered | Covers public behavior for `indentAmountControlsIndentWidth`. |
| atomic::OutputSettingsAtomicTest::nestedBlocksIndentPerDepth | atomic | Serialization and Output Settings | covered | Covers public behavior for `nestedBlocksIndentPerDepth`. |
| atomic::OutputSettingsAtomicTest::inlineElementsStayOnParentLine | atomic | Serialization and Output Settings | covered | Covers public behavior for `inlineElementsStayOnParentLine`. |
| atomic::OutputSettingsAtomicTest::outlineTreatsInlineAsBlock | atomic | Serialization and Output Settings | covered | Covers public behavior for `outlineTreatsInlineAsBlock`. |
| atomic::OutputSettingsAtomicTest::xmlSyntaxSelfClosesVoidElements | atomic | Serialization and Output Settings | covered | Covers public behavior for `xmlSyntaxSelfClosesVoidElements`. |
| atomic::OutputSettingsAtomicTest::htmlSyntaxRendersVoidBare | atomic | Serialization and Output Settings | covered | Covers public behavior for `htmlSyntaxRendersVoidBare`. |
| atomic::OutputSettingsAtomicTest::outerHtmlEqualsHtmlOnDocument | atomic | Serialization and Output Settings | covered | Covers public behavior for `outerHtmlEqualsHtmlOnDocument`. |
| atomic::ParseNormalizationAtomicTest::parseAddsImplicitHtmlHeadBody | atomic | Parsing and Document Normalization | covered | Covers public behavior for `parseAddsImplicitHtmlHeadBody`. |
| atomic::ParseNormalizationAtomicTest::titleElementMovesIntoHead | atomic | Parsing and Document Normalization | covered | Covers public behavior for `titleElementMovesIntoHead`. |
| atomic::ParseNormalizationAtomicTest::tagAndAttributeNamesAreLowercased | atomic | Parsing and Document Normalization | covered | Covers public behavior for `tagAndAttributeNamesAreLowercased`. |
| atomic::ParseNormalizationAtomicTest::attributeValuesKeepCase | atomic | Parsing and Document Normalization | covered | Covers public behavior for `attributeValuesKeepCase`. |
| atomic::ParseNormalizationAtomicTest::parseBodyFragmentPlacesNodesInBody | atomic | Parsing and Document Normalization | covered | Covers public behavior for `parseBodyFragmentPlacesNodesInBody`. |
| atomic::ParseNormalizationAtomicTest::createShellIsEmptyNormalizedDocument | atomic | Parsing and Document Normalization | covered | Covers public behavior for `createShellIsEmptyNormalizedDocument`. |
| atomic::ParseNormalizationAtomicTest::doctypeIsPreservedAsFirstChild | atomic | Parsing and Document Normalization | covered | Covers public behavior for `doctypeIsPreservedAsFirstChild`. |
| atomic::ParseNormalizationAtomicTest::unclosedListItemsAreClosed | atomic | Parsing and Document Normalization | covered | Covers public behavior for `unclosedListItemsAreClosed`. |
| atomic::ParseNormalizationAtomicTest::tableAcquiresImplicitTbody | atomic | Parsing and Document Normalization | covered | Covers public behavior for `tableAcquiresImplicitTbody`. |
| atomic::ParseNormalizationAtomicTest::scriptContentIsDataNotText | atomic | Parsing and Document Normalization | covered | Covers public behavior for `scriptContentIsDataNotText`. |
| atomic::ParseNormalizationAtomicTest::documentNodeNameAndLocation | atomic | Parsing and Document Normalization | covered | Covers public behavior for `documentNodeNameAndLocation`. |
| atomic::SelectorAtomicTest::idClassAndTagSelectors | atomic | CSS Selector Engine | covered | Covers public behavior for `idClassAndTagSelectors`. |
| atomic::SelectorAtomicTest::commaGroupReturnsDocumentOrder | atomic | CSS Selector Engine | covered | Covers public behavior for `commaGroupReturnsDocumentOrder`. |
| atomic::SelectorAtomicTest::attributePresenceAndExactValue | atomic | CSS Selector Engine | covered | Covers public behavior for `attributePresenceAndExactValue`. |
| atomic::SelectorAtomicTest::attributePrefixSuffixSubstring | atomic | CSS Selector Engine | covered | Covers public behavior for `attributePrefixSuffixSubstring`. |
| atomic::SelectorAtomicTest::attributeNamePrefixSelector | atomic | CSS Selector Engine | covered | Covers public behavior for `attributeNamePrefixSelector`. |
| atomic::SelectorAtomicTest::childCombinatorScopesToDirectChildren | atomic | CSS Selector Engine | covered | Covers public behavior for `childCombinatorScopesToDirectChildren`. |
| atomic::SelectorAtomicTest::siblingCombinators | atomic | CSS Selector Engine | covered | Covers public behavior for `siblingCombinators`. |
| atomic::SelectorAtomicTest::indexPseudoSelectors | atomic | CSS Selector Engine | covered | Covers public behavior for `indexPseudoSelectors`. |
| atomic::SelectorAtomicTest::structuralPseudoSelectors | atomic | CSS Selector Engine | covered | Covers public behavior for `structuralPseudoSelectors`. |
| atomic::SelectorAtomicTest::onlyChildPseudoSelector | atomic | CSS Selector Engine | covered | Covers public behavior for `onlyChildPseudoSelector`. |
| atomic::SelectorAtomicTest::hasAndNotPseudoSelectors | atomic | CSS Selector Engine | covered | Covers public behavior for `hasAndNotPseudoSelectors`. |
| atomic::SelectorAtomicTest::containsAndContainsOwn | atomic | CSS Selector Engine | covered | Covers public behavior for `containsAndContainsOwn`. |
| atomic::SelectorAtomicTest::matchesRegexPseudoSelector | atomic | CSS Selector Engine | covered | Covers public behavior for `matchesRegexPseudoSelector`. |
| atomic::SelectorAtomicTest::isMatchesReceiver | atomic | CSS Selector Engine | covered | Covers public behavior for `isMatchesReceiver`. |
| atomic::SelectorAtomicTest::selectFirstReturnsFirstMatchOrNull | atomic | Error Semantics | covered | Covers public behavior for `selectFirstReturnsFirstMatchOrNull`. |
| atomic::SelectorAtomicTest::unknownPseudoRaisesSelectorParseException | atomic | Error Semantics | covered | Covers public behavior for `unknownPseudoRaisesSelectorParseException`. |
| atomic::TextEntitiesAtomicTest::textNormalizesWhitespace | atomic | Text Extraction and Entities | covered | Covers public behavior for `textNormalizesWhitespace`. |
| atomic::TextEntitiesAtomicTest::ownTextExcludesChildElements | atomic | Text Extraction and Entities | covered | Covers public behavior for `ownTextExcludesChildElements`. |
| atomic::TextEntitiesAtomicTest::wholeTextPreservesWhitespace | atomic | Text Extraction and Entities | covered | Covers public behavior for `wholeTextPreservesWhitespace`. |
| atomic::TextEntitiesAtomicTest::hasTextIgnoresBlank | atomic | Text Extraction and Entities | covered | Covers public behavior for `hasTextIgnoresBlank`. |
| atomic::TextEntitiesAtomicTest::documentTextSpansHeadAndBody | atomic | Text Extraction and Entities | covered | Covers public behavior for `documentTextSpansHeadAndBody`. |
| atomic::TextEntitiesAtomicTest::preElementKeepsWhitespace | atomic | Text Extraction and Entities | covered | Covers public behavior for `preElementKeepsWhitespace`. |
| atomic::TextEntitiesAtomicTest::textNodeCarriesCharacterData | atomic | Text Extraction and Entities | covered | Covers public behavior for `textNodeCarriesCharacterData`. |
| atomic::TextEntitiesAtomicTest::entitiesEscapeDefaults | atomic | Text Extraction and Entities | covered | Covers public behavior for `entitiesEscapeDefaults`. |
| atomic::TextEntitiesAtomicTest::entitiesUnescapeNamedAndNumeric | atomic | Text Extraction and Entities | covered | Covers public behavior for `entitiesUnescapeNamedAndNumeric`. |
| atomic::TextEntitiesAtomicTest::defaultCharsetEmitsLiteralsAndNbspEntity | atomic | Text Extraction and Entities | covered | Covers public behavior for `defaultCharsetEmitsLiteralsAndNbspEntity`. |
| atomic::TextEntitiesAtomicTest::xhtmlModeUsesNumericNbsp | atomic | Text Extraction and Entities | covered | Covers public behavior for `xhtmlModeUsesNumericNbsp`. |
| atomic::TextEntitiesAtomicTest::asciiCharsetUsesBaseEntities | atomic | Text Extraction and Entities | covered | Covers public behavior for `asciiCharsetUsesBaseEntities`. |
| atomic::TextEntitiesAtomicTest::asciiExtendedModeUsesFullNames | atomic | Text Extraction and Entities | covered | Covers public behavior for `asciiExtendedModeUsesFullNames`. |
| atomic::TraversalAtomicTest::childrenAndChildIndex | atomic | DOM Traversal and Manipulation | covered | Covers public behavior for `childrenAndChildIndex`. |
| atomic::TraversalAtomicTest::childNodesCountAllTypes | atomic | DOM Traversal and Manipulation | covered | Covers public behavior for `childNodesCountAllTypes`. |
| atomic::TraversalAtomicTest::parentAndParentsChain | atomic | DOM Traversal and Manipulation | covered | Covers public behavior for `parentAndParentsChain`. |
| atomic::TraversalAtomicTest::siblingNavigation | atomic | DOM Traversal and Manipulation | covered | Covers public behavior for `siblingNavigation`. |
| atomic::TraversalAtomicTest::elementSiblingIndexAndSiblingElements | atomic | DOM Traversal and Manipulation | covered | Covers public behavior for `elementSiblingIndexAndSiblingElements`. |
| atomic::TraversalAtomicTest::rootAndOwnerDocument | atomic | DOM Traversal and Manipulation | covered | Covers public behavior for `rootAndOwnerDocument`. |
| atomic::TraversalAtomicTest::cssSelectorBuildsUniquePath | atomic | DOM Traversal and Manipulation | covered | Covers public behavior for `cssSelectorBuildsUniquePath`. |
| atomic::TraversalAtomicTest::detachedElementHasNullParent | atomic | DOM Traversal and Manipulation | covered | Covers public behavior for `detachedElementHasNullParent`. |
| atomic::TraversalAtomicTest::childOutOfRangeRaises | atomic | Error Semantics | covered | Covers public behavior for `childOutOfRangeRaises`. |
| atomic::TraversalAtomicTest::classicGettersReturnMatches | atomic | CSS Selector Engine | covered | Covers public behavior for `classicGettersReturnMatches`. |
| integration::CleanXmlIntegrationTest::cleanStaticEqualsCleanerComposition | integration | Cross-View Invariants | covered | Covers public behavior for `cleanStaticEqualsCleanerComposition`. |
| integration::CleanXmlIntegrationTest::isValidAgreesBetweenProjections | integration | Cross-View Invariants | covered | Covers public behavior for `isValidAgreesBetweenProjections`. |
| integration::CleanXmlIntegrationTest::basicSafelistKeepsLinksWithNofollow | integration | Sanitization | covered | Covers public behavior for `basicSafelistKeepsLinksWithNofollow`. |
| integration::CleanXmlIntegrationTest::noneAndSimpleTextSafelists | integration | Sanitization | covered | Covers public behavior for `noneAndSimpleTextSafelists`. |
| integration::CleanXmlIntegrationTest::basicWithImagesEnforcesProtocols | integration | Sanitization | covered | Covers public behavior for `basicWithImagesEnforcesProtocols`. |
| integration::CleanXmlIntegrationTest::customSafelistAdmitsConfiguredTagsOnly | integration | Sanitization | covered | Covers public behavior for `customSafelistAdmitsConfiguredTagsOnly`. |
| integration::CleanXmlIntegrationTest::removeTagsNarrowsStockSafelist | integration | Sanitization | covered | Covers public behavior for `removeTagsNarrowsStockSafelist`. |
| integration::CleanXmlIntegrationTest::baseUriResolvesCleanedLinks | integration | Sanitization | covered | Covers public behavior for `baseUriResolvesCleanedLinks`. |
| integration::CleanXmlIntegrationTest::relaxedKeepsTableStructure | integration | Sanitization | covered | Covers public behavior for `relaxedKeepsTableStructure`. |
| integration::CleanXmlIntegrationTest::xmlParserPreservesStructureLiterally | integration | XML Parsing Mode | covered | Covers public behavior for `xmlParserPreservesStructureLiterally`. |
| integration::CleanXmlIntegrationTest::htmlParserAppliesHtmlRulesWhenNamed | integration | XML Parsing Mode | covered | Covers public behavior for `htmlParserAppliesHtmlRulesWhenNamed`. |
| integration::MutateSerializeIntegrationTest::appendPrependRenderInOrder | integration | Representative Workflows | covered | Covers public behavior for `appendPrependRenderInOrder`. |
| integration::MutateSerializeIntegrationTest::wrapAddsStructureAroundElement | integration | DOM Traversal and Manipulation | covered | Covers public behavior for `wrapAddsStructureAroundElement`. |
| integration::MutateSerializeIntegrationTest::beforeAndAfterInsertSiblings | integration | DOM Traversal and Manipulation | covered | Covers public behavior for `beforeAndAfterInsertSiblings`. |
| integration::MutateSerializeIntegrationTest::removeDeletesAndUnwrapKeepsChildren | integration | DOM Traversal and Manipulation | covered | Covers public behavior for `removeDeletesAndUnwrapKeepsChildren`. |
| integration::MutateSerializeIntegrationTest::replaceWithSwapsNode | integration | DOM Traversal and Manipulation | covered | Covers public behavior for `replaceWithSwapsNode`. |
| integration::MutateSerializeIntegrationTest::emptyRemovesAllChildren | integration | DOM Traversal and Manipulation | covered | Covers public behavior for `emptyRemovesAllChildren`. |
| integration::MutateSerializeIntegrationTest::textSetterEscapesMarkup | integration | Text Extraction and Entities | covered | Covers public behavior for `textSetterEscapesMarkup`. |
| integration::MutateSerializeIntegrationTest::htmlSetterReplacesChildren | integration | DOM Traversal and Manipulation | covered | Covers public behavior for `htmlSetterReplacesChildren`. |
| integration::MutateSerializeIntegrationTest::bulkClassOperationVisibleEverywhere | integration | Cross-View Invariants | covered | Covers public behavior for `bulkClassOperationVisibleEverywhere`. |
| integration::MutateSerializeIntegrationTest::cloneIsDeepAndIndependent | integration | State Model | covered | Covers public behavior for `cloneIsDeepAndIndependent`. |
| integration::MutateSerializeIntegrationTest::serializationFixpointHoldsAfterMutation | integration | Cross-View Invariants | covered | Covers public behavior for `serializationFixpointHoldsAfterMutation`. |
| integration::MutateSerializeIntegrationTest::cssSelectorRoundTripsToSameElement | integration | Cross-View Invariants | covered | Covers public behavior for `cssSelectorRoundTripsToSameElement`. |
| integration::MutateSerializeIntegrationTest::createdElementsRenameAndAttach | integration | DOM Traversal and Manipulation | covered | Covers public behavior for `createdElementsRenameAndAttach`. |
| integration::ParseSelectExtractIntegrationTest::parseQueryExtractWorkflow | integration | Representative Workflows | covered | Covers public behavior for `parseQueryExtractWorkflow`. |
| integration::ParseSelectExtractIntegrationTest::selectResultsAgreeWithClassicGetters | integration | Cross-View Invariants | covered | Covers public behavior for `selectResultsAgreeWithClassicGetters`. |
| integration::ParseSelectExtractIntegrationTest::elementsAggregatesProjectMatchedSet | integration | CSS Selector Engine | covered | Covers public behavior for `elementsAggregatesProjectMatchedSet`. |
| integration::ParseSelectExtractIntegrationTest::elementsFilteringNarrowsSelection | integration | CSS Selector Engine | covered | Covers public behavior for `elementsFilteringNarrowsSelection`. |
| integration::ParseSelectExtractIntegrationTest::nestedSelectScopesToSubtree | integration | CSS Selector Engine | covered | Covers public behavior for `nestedSelectScopesToSubtree`. |
| integration::ParseSelectExtractIntegrationTest::groupAndCombinatorQueriesKeepDocumentOrder | integration | CSS Selector Engine | covered | Covers public behavior for `groupAndCombinatorQueriesKeepDocumentOrder`. |
| integration::ParseSelectExtractIntegrationTest::hasAndNotComposeAcrossTree | integration | CSS Selector Engine | covered | Covers public behavior for `hasAndNotComposeAcrossTree`. |
| integration::ParseSelectExtractIntegrationTest::baseUriFlowsFromParseToAbsUrl | integration | Parsing and Document Normalization | covered | Covers public behavior for `baseUriFlowsFromParseToAbsUrl`. |
| integration::ParseSelectExtractIntegrationTest::fragmentParsingKeepsBaseUri | integration | Parsing and Document Normalization | covered | Covers public behavior for `fragmentParsingKeepsBaseUri`. |
