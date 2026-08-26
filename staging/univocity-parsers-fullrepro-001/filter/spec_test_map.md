# Spec Test Map

| test_nodeid | layer | spec_section | status | notes |
|---|---|---|---|---|
| atomic::CsvParsingAtomicTest::parseAllReturnsEveryRow | atomic | CSV Parsing | covered | Covers public behavior for `parseAllReturnsEveryRow`. |
| atomic::CsvParsingAtomicTest::quotedValueWithDelimiterIsRead | atomic | CSV Parsing | covered | Covers public behavior for `quotedValueWithDelimiterIsRead`. |
| atomic::CsvParsingAtomicTest::doubledQuoteDecodesInsideQuotedValue | atomic | CSV Parsing | covered | Covers public behavior for `doubledQuoteDecodesInsideQuotedValue`. |
| atomic::CsvParsingAtomicTest::defaultDialectCharacters | atomic | CSV Parsing | covered | Covers public behavior for `defaultDialectCharacters`. |
| atomic::CsvParsingAtomicTest::customDelimiterAndQuote | atomic | CSV Parsing | covered | Covers public behavior for `customDelimiterAndQuote`. |
| atomic::CsvParsingAtomicTest::commentsAndEmptyLinesAreSkipped | atomic | CSV Parsing | covered | Covers public behavior for `commentsAndEmptyLinesAreSkipped`. |
| atomic::CsvParsingAtomicTest::whitespaceTrimmedByDefault | atomic | CSV Parsing | covered | Covers public behavior for `whitespaceTrimmedByDefault`. |
| atomic::CsvParsingAtomicTest::trimValuesFalsePreservesWhitespace | atomic | CSV Parsing | covered | Covers public behavior for `trimValuesFalsePreservesWhitespace`. |
| atomic::CsvParsingAtomicTest::lineSeparatorDetectionAcceptsCrlf | atomic | CSV Parsing | covered | Covers public behavior for `lineSeparatorDetectionAcceptsCrlf`. |
| atomic::CsvParsingAtomicTest::formatDetectionChoosesDelimiter | atomic | CSV Parsing | covered | Covers public behavior for `formatDetectionChoosesDelimiter`. |
| atomic::CsvParsingAtomicTest::emptyInputParsesToEmptyList | atomic | CSV Parsing | covered | Covers public behavior for `emptyInputParsesToEmptyList`. |
| atomic::CsvWritingAtomicTest::headersAndRowsProduceLines | atomic | Writing | covered | Covers public behavior for `headersAndRowsProduceLines`. |
| atomic::CsvWritingAtomicTest::quotingOnlyForDelimiterBearingValues | atomic | Writing | covered | Covers public behavior for `quotingOnlyForDelimiterBearingValues`. |
| atomic::CsvWritingAtomicTest::embeddedQuoteDoubledWhenQuoted | atomic | Writing | covered | Covers public behavior for `embeddedQuoteDoubledWhenQuoted`. |
| atomic::CsvWritingAtomicTest::lineBreakBearingValueIsQuoted | atomic | Writing | covered | Covers public behavior for `lineBreakBearingValueIsQuoted`. |
| atomic::CsvWritingAtomicTest::quoteAllFieldsQuotesEverything | atomic | Writing | covered | Covers public behavior for `quoteAllFieldsQuotesEverything`. |
| atomic::CsvWritingAtomicTest::nullValueSubstitutionOnWrite | atomic | Writing | covered | Covers public behavior for `nullValueSubstitutionOnWrite`. |
| atomic::CsvWritingAtomicTest::writeRowsWritesCollection | atomic | Writing | covered | Covers public behavior for `writeRowsWritesCollection`. |
| atomic::CsvWritingAtomicTest::writeRowToStringHasNoLineSeparator | atomic | Writing | covered | Covers public behavior for `writeRowToStringHasNoLineSeparator`. |
| atomic::FixedWidthAtomicTest::positionalLayoutCutsAtBoundaries | atomic | Fixed-Width Format | covered | Covers public behavior for `positionalLayoutCutsAtBoundaries`. |
| atomic::FixedWidthAtomicTest::surroundingWhitespaceTrimmed | atomic | Fixed-Width Format | covered | Covers public behavior for `surroundingWhitespaceTrimmed`. |
| atomic::FixedWidthAtomicTest::namedFieldsBecomeDerivedHeaders | atomic | Fixed-Width Format | covered | Covers public behavior for `namedFieldsBecomeDerivedHeaders`. |
| atomic::FixedWidthAtomicTest::namedFieldsUsableForRecordAccess | atomic | Fixed-Width Format | covered | Covers public behavior for `namedFieldsUsableForRecordAccess`. |
| atomic::FixedWidthAtomicTest::headerExtractionConsumesFirstPhysicalRow | atomic | Fixed-Width Format | covered | Covers public behavior for `headerExtractionConsumesFirstPhysicalRow`. |
| atomic::FixedWidthAtomicTest::writerPadsWithSpacesLeftByDefault | atomic | Fixed-Width Format | covered | Covers public behavior for `writerPadsWithSpacesLeftByDefault`. |
| atomic::FixedWidthAtomicTest::rightAlignedZeroPaddedField | atomic | Fixed-Width Format | covered | Covers public behavior for `rightAlignedZeroPaddedField`. |
| atomic::FixedWidthAtomicTest::centerAlignedFieldPadsBothSides | atomic | Fixed-Width Format | covered | Covers public behavior for `centerAlignedFieldPadsBothSides`. |
| atomic::FixedWidthAtomicTest::headerWritingEmitsPaddedFieldNames | atomic | Fixed-Width Format | covered | Covers public behavior for `headerWritingEmitsPaddedFieldNames`. |
| atomic::HeadersSelectionAtomicTest::headerExtractionConsumesFirstRow | atomic | Headers and Column Selection | covered | Covers public behavior for `headerExtractionConsumesFirstRow`. |
| atomic::HeadersSelectionAtomicTest::selectFieldsReordersToSelectionOrder | atomic | Headers and Column Selection | covered | Covers public behavior for `selectFieldsReordersToSelectionOrder`. |
| atomic::HeadersSelectionAtomicTest::selectIndexesSelectsByPosition | atomic | Headers and Column Selection | covered | Covers public behavior for `selectIndexesSelectsByPosition`. |
| atomic::HeadersSelectionAtomicTest::reorderingDisabledKeepsPositions | atomic | Headers and Column Selection | covered | Covers public behavior for `reorderingDisabledKeepsPositions`. |
| atomic::HeadersSelectionAtomicTest::unknownSelectionYieldsEmptyProjection | atomic | Headers and Column Selection | covered | Covers public behavior for `unknownSelectionYieldsEmptyProjection`. |
| atomic::RecordsAtomicTest::stringAndIntAccessors | atomic | Records | covered | Covers public behavior for `stringAndIntAccessors`. |
| atomic::RecordsAtomicTest::numericAndBooleanAccessors | atomic | Records | covered | Covers public behavior for `numericAndBooleanAccessors`. |
| atomic::RecordsAtomicTest::getValuesReturnsUnderlyingRow | atomic | Records | covered | Covers public behavior for `getValuesReturnsUnderlyingRow`. |
| atomic::RecordsAtomicTest::getValueAppliesDefaultOnNull | atomic | Records | covered | Covers public behavior for `getValueAppliesDefaultOnNull`. |
| atomic::RecordsAtomicTest::iterateRecordsStreams | atomic | Records | covered | Covers public behavior for `iterateRecordsStreams`. |
| atomic::RecordsAtomicTest::metadataReportsSchema | atomic | Records | covered | Covers public behavior for `metadataReportsSchema`. |
| atomic::RecordsAtomicTest::numericAccessorOnTextRaises | atomic | Error Semantics | covered | Covers public behavior for `numericAccessorOnTextRaises`. |
| atomic::RecordsAtomicTest::unknownHeaderRaisesIllegalArgument | atomic | Error Semantics | covered | Covers public behavior for `unknownHeaderRaisesIllegalArgument`. |
| atomic::SessionsAtomicTest::parserRunsMultipleFreshSessions | atomic | State Model | covered | Covers public behavior for `parserRunsMultipleFreshSessions`. |
| atomic::SessionsAtomicTest::writerAccumulatesUntilClose | atomic | State Model | covered | Covers public behavior for `writerAccumulatesUntilClose`. |
| atomic::SessionsAtomicTest::settingsCapturedAtConstruction | atomic | State Model | covered | Covers public behavior for `settingsCapturedAtConstruction`. |
| atomic::StreamingAtomicTest::parseNextStreamsRowsThenNull | atomic | CSV Parsing | covered | Covers public behavior for `parseNextStreamsRowsThenNull`. |
| atomic::StreamingAtomicTest::stopParsingEndsSession | atomic | CSV Parsing | covered | Covers public behavior for `stopParsingEndsSession`. |
| atomic::StreamingAtomicTest::iterateYieldsRows | atomic | CSV Parsing | covered | Covers public behavior for `iterateYieldsRows`. |
| atomic::StreamingAtomicTest::currentRecordCountsRows | atomic | Headers and Column Selection | covered | Covers public behavior for `currentRecordCountsRows`. |
| atomic::StreamingAtomicTest::headersReportedWithoutExtraction | atomic | Headers and Column Selection | covered | Covers public behavior for `headersReportedWithoutExtraction`. |
| atomic::TsvAtomicTest::rowsSplitOnTabs | atomic | TSV Format | covered | Covers public behavior for `rowsSplitOnTabs`. |
| atomic::TsvAtomicTest::escapedTabDecodes | atomic | TSV Format | covered | Covers public behavior for `escapedTabDecodes`. |
| atomic::TsvAtomicTest::escapedNewlineDecodes | atomic | TSV Format | covered | Covers public behavior for `escapedNewlineDecodes`. |
| atomic::TsvAtomicTest::writerEncodesTabAndNewline | atomic | TSV Format | covered | Covers public behavior for `writerEncodesTabAndNewline`. |
| atomic::TsvAtomicTest::headersAndRowsOverTabDialect | atomic | TSV Format | covered | Covers public behavior for `headersAndRowsOverTabDialect`. |
| atomic::ValuesAndLimitsAtomicTest::nullValueSubstitutesAbsentValues | atomic | CSV Parsing | covered | Covers public behavior for `nullValueSubstitutesAbsentValues`. |
| atomic::ValuesAndLimitsAtomicTest::emptyValueSubstitutesQuotedEmpties | atomic | CSV Parsing | covered | Covers public behavior for `emptyValueSubstitutesQuotedEmpties`. |
| atomic::ValuesAndLimitsAtomicTest::defaultSubstitutionsAreNull | atomic | CSV Parsing | covered | Covers public behavior for `defaultSubstitutionsAreNull`. |
| atomic::ValuesAndLimitsAtomicTest::maxCharsBoundaryParses | atomic | CSV Parsing | covered | Covers public behavior for `maxCharsBoundaryParses`. |
| atomic::ValuesAndLimitsAtomicTest::maxCharsViolationRaisesTextParsing | atomic | Error Semantics | covered | Covers public behavior for `maxCharsViolationRaisesTextParsing`. |
| integration::ProjectionAgreementIntegrationTest::parseAllAndParseNextAgree | integration | Cross-View Invariants | covered | Covers public behavior for `parseAllAndParseNextAgree`. |
| integration::ProjectionAgreementIntegrationTest::parseAllAndIterateAgree | integration | Cross-View Invariants | covered | Covers public behavior for `parseAllAndIterateAgree`. |
| integration::ProjectionAgreementIntegrationTest::recordValuesMatchRowsPositionally | integration | Cross-View Invariants | covered | Covers public behavior for `recordValuesMatchRowsPositionally`. |
| integration::ProjectionAgreementIntegrationTest::contextAndMetadataHeadersAgree | integration | Cross-View Invariants | covered | Covers public behavior for `contextAndMetadataHeadersAgree`. |
| integration::ProjectionAgreementIntegrationTest::headerRowNotAmongParsedRows | integration | Cross-View Invariants | covered | Covers public behavior for `headerRowNotAmongParsedRows`. |
| integration::ProjectionAgreementIntegrationTest::currentRecordCountsCsv | integration | Cross-View Invariants | covered | Covers public behavior for `currentRecordCountsCsv`. |
| integration::ProjectionAgreementIntegrationTest::currentRecordCountsTsv | integration | Cross-View Invariants | covered | Covers public behavior for `currentRecordCountsTsv`. |
| integration::ProjectionAgreementIntegrationTest::currentRecordCountsFixedWidth | integration | Cross-View Invariants | covered | Covers public behavior for `currentRecordCountsFixedWidth`. |
| integration::ProjectionAgreementIntegrationTest::tsvProjectionsAgree | integration | Cross-View Invariants | covered | Covers public behavior for `tsvProjectionsAgree`. |
| integration::ProjectionAgreementIntegrationTest::fixedWidthProjectionsAgree | integration | Cross-View Invariants | covered | Covers public behavior for `fixedWidthProjectionsAgree`. |
| integration::ProjectionAgreementIntegrationTest::recordStreamsAgree | integration | Cross-View Invariants | covered | Covers public behavior for `recordStreamsAgree`. |
| integration::RoundTripIntegrationTest::csvRoundTripRestoresValues | integration | Cross-View Invariants | covered | Covers public behavior for `csvRoundTripRestoresValues`. |
| integration::RoundTripIntegrationTest::csvQuotedDelimiterValueRoundTrips | integration | Cross-View Invariants | covered | Covers public behavior for `csvQuotedDelimiterValueRoundTrips`. |
| integration::RoundTripIntegrationTest::csvEmbeddedQuoteRoundTrips | integration | Cross-View Invariants | covered | Covers public behavior for `csvEmbeddedQuoteRoundTrips`. |
| integration::RoundTripIntegrationTest::csvLineBreakValueRoundTrips | integration | Cross-View Invariants | covered | Covers public behavior for `csvLineBreakValueRoundTrips`. |
| integration::RoundTripIntegrationTest::csvNullCollapsesAcrossRoundTrip | integration | Cross-View Invariants | covered | Covers public behavior for `csvNullCollapsesAcrossRoundTrip`. |
| integration::RoundTripIntegrationTest::csvQuoteAllFieldsRoundTrips | integration | Cross-View Invariants | covered | Covers public behavior for `csvQuoteAllFieldsRoundTrips`. |
| integration::RoundTripIntegrationTest::tsvTabEscapeRoundTrips | integration | Cross-View Invariants | covered | Covers public behavior for `tsvTabEscapeRoundTrips`. |
| integration::RoundTripIntegrationTest::tsvNewlineEscapeRoundTrips | integration | Cross-View Invariants | covered | Covers public behavior for `tsvNewlineEscapeRoundTrips`. |
| integration::RoundTripIntegrationTest::fixedWidthRoundTripAndLineLengths | integration | Cross-View Invariants | covered | Covers public behavior for `fixedWidthRoundTripAndLineLengths`. |
| integration::RoundTripIntegrationTest::fixedWidthPaddedFieldRoundTrips | integration | Cross-View Invariants | covered | Covers public behavior for `fixedWidthPaddedFieldRoundTrips`. |
| integration::RoundTripIntegrationTest::crossDialectRewriteRoundTrips | integration | Cross-View Invariants | covered | Covers public behavior for `crossDialectRewriteRoundTrips`. |
| integration::SelectionReshapeIntegrationTest::reorderedSelectionShapesEveryRow | integration | Cross-View Invariants | covered | Covers public behavior for `reorderedSelectionShapesEveryRow`. |
| integration::SelectionReshapeIntegrationTest::reorderingDisabledPreservesIndexes | integration | Cross-View Invariants | covered | Covers public behavior for `reorderingDisabledPreservesIndexes`. |
| integration::SelectionReshapeIntegrationTest::recordsFollowSelectionProjection | integration | Cross-View Invariants | covered | Covers public behavior for `recordsFollowSelectionProjection`. |
| integration::SelectionReshapeIntegrationTest::indexAndNameSelectionAgree | integration | Cross-View Invariants | covered | Covers public behavior for `indexAndNameSelectionAgree`. |
| integration::SelectionReshapeIntegrationTest::selectedProjectionRewriteReadsBack | integration | Cross-View Invariants | covered | Covers public behavior for `selectedProjectionRewriteReadsBack`. |
| integration::SelectionReshapeIntegrationTest::selectionAppliesOverTsv | integration | Cross-View Invariants | covered | Covers public behavior for `selectionAppliesOverTsv`. |
| integration::SelectionReshapeIntegrationTest::detectedFormatFeedsWriterRoundTrip | integration | Cross-View Invariants | covered | Covers public behavior for `detectedFormatFeedsWriterRoundTrip`. |
| integration::SelectionReshapeIntegrationTest::fixedWidthRecordsMatchRows | integration | Cross-View Invariants | covered | Covers public behavior for `fixedWidthRecordsMatchRows`. |
| integration::SelectionReshapeIntegrationTest::unknownSelectionEmptyInBothViews | integration | Cross-View Invariants | covered | Covers public behavior for `unknownSelectionEmptyInBothViews`. |
