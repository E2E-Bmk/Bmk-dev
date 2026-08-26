# Spec Test Map

| test_nodeid | layer | spec_section | status | notes |
|---|---|---|---|---|
| atomic::CompiledPathsAtomicTest::compiledReadEqualsStaticRead | atomic | Compiled Paths | covered | Covers public behavior for `compiledReadEqualsStaticRead`. |
| atomic::CompiledPathsAtomicTest::getPathNormalizesToBracketForm | atomic | Compiled Paths | covered | Covers public behavior for `getPathNormalizesToBracketForm`. |
| atomic::CompiledPathsAtomicTest::isDefiniteTrueForPlainPath | atomic | Compiled Paths | covered | Covers public behavior for `isDefiniteTrueForPlainPath`. |
| atomic::CompiledPathsAtomicTest::isDefiniteFalseForIndefiniteConstructs | atomic | Compiled Paths | covered | Covers public behavior for `isDefiniteFalseForIndefiniteConstructs`. |
| atomic::CompiledPathsAtomicTest::compiledReadHonorsConfiguration | atomic | Compiled Paths | covered | Covers public behavior for `compiledReadHonorsConfiguration`. |
| atomic::CompiledPathsAtomicTest::compileBindsFilterPlaceholder | atomic | Compiled Paths | covered | Covers public behavior for `compileBindsFilterPlaceholder`. |
| atomic::ContextsAtomicTest::parseReturnsReadableContext | atomic | Parsing and Document Contexts | covered | Covers public behavior for `parseReturnsReadableContext`. |
| atomic::ContextsAtomicTest::staticReadEqualsParseThenRead | atomic | Parsing and Document Contexts | covered | Covers public behavior for `staticReadEqualsParseThenRead`. |
| atomic::ContextsAtomicTest::typedReadCoercesIntegerToString | atomic | Parsing and Document Contexts | covered | Covers public behavior for `typedReadCoercesIntegerToString`. |
| atomic::ContextsAtomicTest::typedReadKeepsInteger | atomic | Parsing and Document Contexts | covered | Covers public behavior for `typedReadKeepsInteger`. |
| atomic::ContextsAtomicTest::typedReadCoercesDoubleToString | atomic | Parsing and Document Contexts | covered | Covers public behavior for `typedReadCoercesDoubleToString`. |
| atomic::ContextsAtomicTest::jsonReturnsLiveModelRoot | atomic | Parsing and Document Contexts | covered | Covers public behavior for `jsonReturnsLiveModelRoot`. |
| atomic::ContextsAtomicTest::jsonStringSerializesModelState | atomic | Parsing and Document Contexts | covered | Covers public behavior for `jsonStringSerializesModelState`. |
| atomic::ContextsAtomicTest::usingBindsConfigurationToContext | atomic | Parsing and Document Contexts | covered | Covers public behavior for `usingBindsConfigurationToContext`. |
| atomic::DocumentModelAtomicTest::wholeNumberLoadsAsInteger | atomic | Path Grammar and Read Evaluation | covered | Covers public behavior for `wholeNumberLoadsAsInteger`. |
| atomic::DocumentModelAtomicTest::decimalNumberLoadsAsDouble | atomic | Path Grammar and Read Evaluation | covered | Covers public behavior for `decimalNumberLoadsAsDouble`. |
| atomic::DocumentModelAtomicTest::objectLoadsAsInsertionOrderedMap | atomic | Path Grammar and Read Evaluation | covered | Covers public behavior for `objectLoadsAsInsertionOrderedMap`. |
| atomic::DocumentModelAtomicTest::booleanAndNullLoadAsModelValues | atomic | Path Grammar and Read Evaluation | covered | Covers public behavior for `booleanAndNullLoadAsModelValues`. |
| atomic::DocumentModelAtomicTest::arrayLoadsAsList | atomic | Path Grammar and Read Evaluation | covered | Covers public behavior for `arrayLoadsAsList`. |
| atomic::ErrorsAtomicTest::missingPropertyRaisesPathNotFound | atomic | Error Semantics | covered | Covers public behavior for `missingPropertyRaisesPathNotFound`. |
| atomic::ErrorsAtomicTest::outOfRangeIndexRaisesPathNotFound | atomic | Error Semantics | covered | Covers public behavior for `outOfRangeIndexRaisesPathNotFound`. |
| atomic::ErrorsAtomicTest::descendingIntoScalarRaisesPathNotFound | atomic | Error Semantics | covered | Covers public behavior for `descendingIntoScalarRaisesPathNotFound`. |
| atomic::ErrorsAtomicTest::unparseablePathRaisesInvalidPath | atomic | Error Semantics | covered | Covers public behavior for `unparseablePathRaisesInvalidPath`. |
| atomic::ErrorsAtomicTest::nullPathRaisesIllegalArgument | atomic | Error Semantics | covered | Covers public behavior for `nullPathRaisesIllegalArgument`. |
| atomic::ErrorsAtomicTest::emptyPathRaisesIllegalArgument | atomic | Error Semantics | covered | Covers public behavior for `emptyPathRaisesIllegalArgument`. |
| atomic::ErrorsAtomicTest::invalidJsonRaisesInvalidJson | atomic | Error Semantics | covered | Covers public behavior for `invalidJsonRaisesInvalidJson`. |
| atomic::ErrorsAtomicTest::addToNonArrayRaisesInvalidModification | atomic | Error Semantics | covered | Covers public behavior for `addToNonArrayRaisesInvalidModification`. |
| atomic::ErrorsAtomicTest::libraryFailuresAreJsonPathExceptions | atomic | Error Semantics | covered | Covers public behavior for `libraryFailuresAreJsonPathExceptions`. |
| atomic::FiltersAtomicTest::existenceFilterKeepsElementsWithProperty | atomic | Filters and Criteria | covered | Covers public behavior for `existenceFilterKeepsElementsWithProperty`. |
| atomic::FiltersAtomicTest::numericLessThanFilter | atomic | Filters and Criteria | covered | Covers public behavior for `numericLessThanFilter`. |
| atomic::FiltersAtomicTest::numericGreaterThanFilter | atomic | Filters and Criteria | covered | Covers public behavior for `numericGreaterThanFilter`. |
| atomic::FiltersAtomicTest::stringEqualityFilter | atomic | Filters and Criteria | covered | Covers public behavior for `stringEqualityFilter`. |
| atomic::FiltersAtomicTest::rootReferenceComparison | atomic | Filters and Criteria | covered | Covers public behavior for `rootReferenceComparison`. |
| atomic::FiltersAtomicTest::regexFilterMatches | atomic | Filters and Criteria | covered | Covers public behavior for `regexFilterMatches`. |
| atomic::FiltersAtomicTest::membershipInFilter | atomic | Filters and Criteria | covered | Covers public behavior for `membershipInFilter`. |
| atomic::FiltersAtomicTest::filterMatchingNothingYieldsEmptyList | atomic | Filters and Criteria | covered | Covers public behavior for `filterMatchingNothingYieldsEmptyList`. |
| atomic::FiltersAtomicTest::criteriaWhereIsSelectsByEquality | atomic | Filters and Criteria | covered | Covers public behavior for `criteriaWhereIsSelectsByEquality`. |
| atomic::FiltersAtomicTest::criteriaLtSelectsBelowBound | atomic | Filters and Criteria | covered | Covers public behavior for `criteriaLtSelectsBelowBound`. |
| atomic::FiltersAtomicTest::criteriaAndChainsConstraints | atomic | Filters and Criteria | covered | Covers public behavior for `criteriaAndChainsConstraints`. |
| atomic::FiltersAtomicTest::filterToStringRendersInlineForm | atomic | Filters and Criteria | covered | Covers public behavior for `filterToStringRendersInlineForm`. |
| atomic::FunctionsAtomicTest::lengthYieldsArraySize | atomic | Functions | covered | Covers public behavior for `lengthYieldsArraySize`. |
| atomic::FunctionsAtomicTest::minYieldsSmallestValue | atomic | Functions | covered | Covers public behavior for `minYieldsSmallestValue`. |
| atomic::FunctionsAtomicTest::maxYieldsLargestValue | atomic | Functions | covered | Covers public behavior for `maxYieldsLargestValue`. |
| atomic::FunctionsAtomicTest::sumYieldsTotal | atomic | Functions | covered | Covers public behavior for `sumYieldsTotal`. |
| atomic::FunctionsAtomicTest::avgYieldsMean | atomic | Functions | covered | Covers public behavior for `avgYieldsMean`. |
| atomic::FunctionsAtomicTest::keysYieldsKeySetInDocumentOrder | atomic | Functions | covered | Covers public behavior for `keysYieldsKeySetInDocumentOrder`. |
| atomic::OptionsAtomicTest::defaultConfigurationHasNoOptions | atomic | Configuration Options | covered | Covers public behavior for `defaultConfigurationHasNoOptions`. |
| atomic::OptionsAtomicTest::addOptionsAddsToConfiguration | atomic | Configuration Options | covered | Covers public behavior for `addOptionsAddsToConfiguration`. |
| atomic::OptionsAtomicTest::builderConstructsConfiguration | atomic | Configuration Options | covered | Covers public behavior for `builderConstructsConfiguration`. |
| atomic::OptionsAtomicTest::alwaysReturnListWrapsDefiniteResult | atomic | Configuration Options | covered | Covers public behavior for `alwaysReturnListWrapsDefiniteResult`. |
| atomic::OptionsAtomicTest::alwaysReturnListKeepsIndefiniteUnchanged | atomic | Configuration Options | covered | Covers public behavior for `alwaysReturnListKeepsIndefiniteUnchanged`. |
| atomic::OptionsAtomicTest::asPathListReturnsNormalizedPaths | atomic | Configuration Options | covered | Covers public behavior for `asPathListReturnsNormalizedPaths`. |
| atomic::OptionsAtomicTest::defaultPathLeafToNullYieldsNull | atomic | Configuration Options | covered | Covers public behavior for `defaultPathLeafToNullYieldsNull`. |
| atomic::OptionsAtomicTest::suppressExceptionsYieldsNull | atomic | Configuration Options | covered | Covers public behavior for `suppressExceptionsYieldsNull`. |
| atomic::OptionsAtomicTest::suppressWithAlwaysListYieldsEmptyList | atomic | Configuration Options | covered | Covers public behavior for `suppressWithAlwaysListYieldsEmptyList`. |
| atomic::OptionsAtomicTest::requirePropertiesRaisesOnMissingDefinite | atomic | Configuration Options | covered | Covers public behavior for `requirePropertiesRaisesOnMissingDefinite`. |
| atomic::OptionsAtomicTest::requirePropertiesRaisesOnIndefinite | atomic | Configuration Options | covered | Covers public behavior for `requirePropertiesRaisesOnIndefinite`. |
| atomic::PathGrammarAtomicTest::dotFormReadsNestedProperty | atomic | Path Grammar and Read Evaluation | covered | Covers public behavior for `dotFormReadsNestedProperty`. |
| atomic::PathGrammarAtomicTest::bracketFormEqualsDotForm | atomic | Path Grammar and Read Evaluation | covered | Covers public behavior for `bracketFormEqualsDotForm`. |
| atomic::PathGrammarAtomicTest::indexAddressesElement | atomic | Path Grammar and Read Evaluation | covered | Covers public behavior for `indexAddressesElement`. |
| atomic::PathGrammarAtomicTest::negativeIndexCountsFromEnd | atomic | Path Grammar and Read Evaluation | covered | Covers public behavior for `negativeIndexCountsFromEnd`. |
| atomic::PathGrammarAtomicTest::sliceIsHalfOpen | atomic | Path Grammar and Read Evaluation | covered | Covers public behavior for `sliceIsHalfOpen`. |
| atomic::PathGrammarAtomicTest::sliceOpenStartBeginsAtZero | atomic | Path Grammar and Read Evaluation | covered | Covers public behavior for `sliceOpenStartBeginsAtZero`. |
| atomic::PathGrammarAtomicTest::sliceOpenEndRunsToLast | atomic | Path Grammar and Read Evaluation | covered | Covers public behavior for `sliceOpenEndRunsToLast`. |
| atomic::PathGrammarAtomicTest::indexUnionSelectsListedOrder | atomic | Path Grammar and Read Evaluation | covered | Covers public behavior for `indexUnionSelectsListedOrder`. |
| atomic::PathGrammarAtomicTest::propertyUnionProjectsOrderedMap | atomic | Path Grammar and Read Evaluation | covered | Covers public behavior for `propertyUnionProjectsOrderedMap`. |
| atomic::PathGrammarAtomicTest::propertyUnionUsesListedOrder | atomic | Path Grammar and Read Evaluation | covered | Covers public behavior for `propertyUnionUsesListedOrder`. |
| atomic::PathGrammarAtomicTest::wildcardOverArraySelectsAll | atomic | Path Grammar and Read Evaluation | covered | Covers public behavior for `wildcardOverArraySelectsAll`. |
| atomic::PathGrammarAtomicTest::wildcardOverObjectSelectsMemberValues | atomic | Path Grammar and Read Evaluation | covered | Covers public behavior for `wildcardOverObjectSelectsMemberValues`. |
| atomic::PathGrammarAtomicTest::deepScanSelectsAllDepths | atomic | Path Grammar and Read Evaluation | covered | Covers public behavior for `deepScanSelectsAllDepths`. |
| atomic::PathGrammarAtomicTest::deepScanReturnsListForSingleMatch | atomic | Path Grammar and Read Evaluation | covered | Covers public behavior for `deepScanReturnsListForSingleMatch`. |
| atomic::PathGrammarAtomicTest::deepScanUnderPrefixCollectsSubtree | atomic | Path Grammar and Read Evaluation | covered | Covers public behavior for `deepScanUnderPrefixCollectsSubtree`. |
| atomic::PathGrammarAtomicTest::definiteYieldsValueIndefiniteYieldsList | atomic | Path Grammar and Read Evaluation | covered | Covers public behavior for `definiteYieldsValueIndefiniteYieldsList`. |
| atomic::PathGrammarAtomicTest::indefiniteSkipsMissingProperties | atomic | Path Grammar and Read Evaluation | covered | Covers public behavior for `indefiniteSkipsMissingProperties`. |
| atomic::WriteOperationsAtomicTest::setReplacesAddressedValue | atomic | Write Operations | covered | Covers public behavior for `setReplacesAddressedValue`. |
| atomic::WriteOperationsAtomicTest::setIndefiniteAppliesToAllMatches | atomic | Write Operations | covered | Covers public behavior for `setIndefiniteAppliesToAllMatches`. |
| atomic::WriteOperationsAtomicTest::putAddsMember | atomic | Write Operations | covered | Covers public behavior for `putAddsMember`. |
| atomic::WriteOperationsAtomicTest::putReplacesExistingMember | atomic | Write Operations | covered | Covers public behavior for `putReplacesExistingMember`. |
| atomic::WriteOperationsAtomicTest::addAppendsToArray | atomic | Write Operations | covered | Covers public behavior for `addAppendsToArray`. |
| atomic::WriteOperationsAtomicTest::deleteRemovesValueFromParent | atomic | Write Operations | covered | Covers public behavior for `deleteRemovesValueFromParent`. |
| atomic::WriteOperationsAtomicTest::deleteWithFilterRemovesMatches | atomic | Write Operations | covered | Covers public behavior for `deleteWithFilterRemovesMatches`. |
| atomic::WriteOperationsAtomicTest::renameKeyRenamesMember | atomic | Write Operations | covered | Covers public behavior for `renameKeyRenamesMember`. |
| atomic::WriteOperationsAtomicTest::mapTransformsEachMatch | atomic | Write Operations | covered | Covers public behavior for `mapTransformsEachMatch`. |
| atomic::WriteOperationsAtomicTest::mapFunctionReceivesConfiguration | atomic | Write Operations | covered | Covers public behavior for `mapFunctionReceivesConfiguration`. |
| atomic::WriteOperationsAtomicTest::writesReturnSameContextForChaining | atomic | Write Operations | covered | Covers public behavior for `writesReturnSameContextForChaining`. |
| integration::CrossEntryPointIntegrationTest::entryPointsAgreeOnDefinitePath | integration | Cross-View Invariants | covered | Covers public behavior for `entryPointsAgreeOnDefinitePath`. |
| integration::CrossEntryPointIntegrationTest::entryPointsAgreeOnIndefinitePath | integration | Cross-View Invariants | covered | Covers public behavior for `entryPointsAgreeOnIndefinitePath`. |
| integration::CrossEntryPointIntegrationTest::entryPointsAgreeOnFilterPath | integration | Cross-View Invariants | covered | Covers public behavior for `entryPointsAgreeOnFilterPath`. |
| integration::CrossEntryPointIntegrationTest::normalizedDefinitePathReEvaluatesSame | integration | Cross-View Invariants | covered | Covers public behavior for `normalizedDefinitePathReEvaluatesSame`. |
| integration::CrossEntryPointIntegrationTest::normalizedScanPathReEvaluatesSame | integration | Cross-View Invariants | covered | Covers public behavior for `normalizedScanPathReEvaluatesSame`. |
| integration::CrossEntryPointIntegrationTest::isDefiniteTruePredictsBareValue | integration | Cross-View Invariants | covered | Covers public behavior for `isDefiniteTruePredictsBareValue`. |
| integration::CrossEntryPointIntegrationTest::isDefiniteFalsePredictsListResult | integration | Cross-View Invariants | covered | Covers public behavior for `isDefiniteFalsePredictsListResult`. |
| integration::CrossEntryPointIntegrationTest::repeatedReadsLeaveDocumentUnchanged | integration | State Model | covered | Covers public behavior for `repeatedReadsLeaveDocumentUnchanged`. |
| integration::CrossEntryPointIntegrationTest::configurationAppliesEquallyAcrossEntryPoints | integration | Cross-View Invariants | covered | Covers public behavior for `configurationAppliesEquallyAcrossEntryPoints`. |
| integration::CrossEntryPointIntegrationTest::placeholderFilterEqualsInlineFilterText | integration | Cross-View Invariants | covered | Covers public behavior for `placeholderFilterEqualsInlineFilterText`. |
| integration::CrossEntryPointIntegrationTest::filterToStringRoundTripsThroughPathText | integration | Cross-View Invariants | covered | Covers public behavior for `filterToStringRoundTripsThroughPathText`. |
| integration::OptionShapeIntegrationTest::pathListOfScanRereadsToPlainValues | integration | Cross-View Invariants | covered | Covers public behavior for `pathListOfScanRereadsToPlainValues`. |
| integration::OptionShapeIntegrationTest::pathListOfFilterRereadsToFilteredValues | integration | Cross-View Invariants | covered | Covers public behavior for `pathListOfFilterRereadsToFilteredValues`. |
| integration::OptionShapeIntegrationTest::pathListOfDefinitePathNamesSingleMatch | integration | Configuration Options | covered | Covers public behavior for `pathListOfDefinitePathNamesSingleMatch`. |
| integration::OptionShapeIntegrationTest::wrappedDefiniteElementEqualsUnwrappedRead | integration | Cross-View Invariants | covered | Covers public behavior for `wrappedDefiniteElementEqualsUnwrappedRead`. |
| integration::OptionShapeIntegrationTest::wrappedIndefiniteResultEqualsDefaultRead | integration | Cross-View Invariants | covered | Covers public behavior for `wrappedIndefiniteResultEqualsDefaultRead`. |
| integration::OptionShapeIntegrationTest::suppressionAppliesAcrossEntryPoints | integration | Configuration Options | covered | Covers public behavior for `suppressionAppliesAcrossEntryPoints`. |
| integration::OptionShapeIntegrationTest::suppressionComposesWithListWrapping | integration | Configuration Options | covered | Covers public behavior for `suppressionComposesWithListWrapping`. |
| integration::OptionShapeIntegrationTest::leafToNullAffectsOnlyMissingLeaf | integration | Configuration Options | covered | Covers public behavior for `leafToNullAffectsOnlyMissingLeaf`. |
| integration::OptionShapeIntegrationTest::requirePropertiesFlipsSkipIntoRaise | integration | Configuration Options | covered | Covers public behavior for `requirePropertiesFlipsSkipIntoRaise`. |
| integration::OptionShapeIntegrationTest::addOptionsBehavesLikeBuilder | integration | Configuration Options | covered | Covers public behavior for `addOptionsBehavesLikeBuilder`. |
| integration::WriteReadCoherenceIntegrationTest::setVisibleThroughAllProjections | integration | Cross-View Invariants | covered | Covers public behavior for `setVisibleThroughAllProjections`. |
| integration::WriteReadCoherenceIntegrationTest::chainedWriteSequenceAccumulates | integration | Write Operations | covered | Covers public behavior for `chainedWriteSequenceAccumulates`. |
| integration::WriteReadCoherenceIntegrationTest::deletedLocationNoLongerReadable | integration | State Model | covered | Covers public behavior for `deletedLocationNoLongerReadable`. |
| integration::WriteReadCoherenceIntegrationTest::renameKeyPreservesValueAndDropsOldKey | integration | Write Operations | covered | Covers public behavior for `renameKeyPreservesValueAndDropsOldKey`. |
| integration::WriteReadCoherenceIntegrationTest::mapTransformationVisibleInJsonString | integration | Cross-View Invariants | covered | Covers public behavior for `mapTransformationVisibleInJsonString`. |
| integration::WriteReadCoherenceIntegrationTest::jsonRootIsLiveAcrossWrites | integration | State Model | covered | Covers public behavior for `jsonRootIsLiveAcrossWrites`. |
| integration::WriteReadCoherenceIntegrationTest::reparsedDocumentIsIndependent | integration | State Model | covered | Covers public behavior for `reparsedDocumentIsIndependent`. |
| integration::WriteReadCoherenceIntegrationTest::storeWriteSequenceKeepsProjectionsCoherent | integration | Cross-View Invariants | covered | Covers public behavior for `storeWriteSequenceKeepsProjectionsCoherent`. |
| integration::WriteReadCoherenceIntegrationTest::putPropertyVisibleToFilters | integration | Cross-View Invariants | covered | Covers public behavior for `putPropertyVisibleToFilters`. |
| integration::WriteReadCoherenceIntegrationTest::indefiniteSetVisibleThroughPathList | integration | Cross-View Invariants | covered | Covers public behavior for `indefiniteSetVisibleThroughPathList`. |
