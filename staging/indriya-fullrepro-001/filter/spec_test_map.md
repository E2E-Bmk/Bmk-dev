# Spec Test Map

| test_nodeid | layer | spec_section | status | notes |
|---|---|---|---|---|
| atomic::ArithmeticAtomicTest::addSameUnit | atomic | Quantity Arithmetic | covered | Covers public behavior for `addSameUnit`. |
| atomic::ArithmeticAtomicTest::addMixedUnitsKeepsLeftUnit | atomic | Quantity Arithmetic | covered | Covers public behavior for `addMixedUnitsKeepsLeftUnit`. |
| atomic::ArithmeticAtomicTest::subtractKeepsLeftUnit | atomic | Quantity Arithmetic | covered | Covers public behavior for `subtractKeepsLeftUnit`. |
| atomic::ArithmeticAtomicTest::multiplyQuantityComposesUnits | atomic | Quantity Arithmetic | covered | Covers public behavior for `multiplyQuantityComposesUnits`. |
| atomic::ArithmeticAtomicTest::divideQuantityComposesUnits | atomic | Quantity Arithmetic | covered | Covers public behavior for `divideQuantityComposesUnits`. |
| atomic::ArithmeticAtomicTest::multiplyByNumberKeepsUnit | atomic | Quantity Arithmetic | covered | Covers public behavior for `multiplyByNumberKeepsUnit`. |
| atomic::ArithmeticAtomicTest::divideByNumberKeepsUnit | atomic | Quantity Arithmetic | covered | Covers public behavior for `divideByNumberKeepsUnit`. |
| atomic::ArithmeticAtomicTest::sameUnitDivisionCancelsToOne | atomic | Quantity Arithmetic | covered | Covers public behavior for `sameUnitDivisionCancelsToOne`. |
| atomic::ArithmeticAtomicTest::crossUnitDivisionKeepsQuotientUnit | atomic | Quantity Arithmetic | covered | Covers public behavior for `crossUnitDivisionKeepsQuotientUnit`. |
| atomic::ArithmeticAtomicTest::inverseReciprocatesValueAndUnit | atomic | Quantity Arithmetic | covered | Covers public behavior for `inverseReciprocatesValueAndUnit`. |
| atomic::ArithmeticAtomicTest::negateFlipsSign | atomic | Quantity Arithmetic | covered | Covers public behavior for `negateFlipsSign`. |
| atomic::ArithmeticAtomicTest::asTypeChecksDimension | atomic | Quantity Arithmetic | covered | Covers public behavior for `asTypeChecksDimension`. |
| atomic::ComparisonAtomicTest::equalsIsUnitSensitive | atomic | Comparison and Equivalence | covered | Covers public behavior for `equalsIsUnitSensitive`. |
| atomic::ComparisonAtomicTest::equalsIsRepresentationInsensitive | atomic | Comparison and Equivalence | covered | Covers public behavior for `equalsIsRepresentationInsensitive`. |
| atomic::ComparisonAtomicTest::equalTriplesAreEqual | atomic | Comparison and Equivalence | covered | Covers public behavior for `equalTriplesAreEqual`. |
| atomic::ComparisonAtomicTest::compareToOrdersAcrossUnits | atomic | Comparison and Equivalence | covered | Covers public behavior for `compareToOrdersAcrossUnits`. |
| atomic::ComparisonAtomicTest::compareToNumericTypeInsensitive | atomic | Comparison and Equivalence | covered | Covers public behavior for `compareToNumericTypeInsensitive`. |
| atomic::ComparisonAtomicTest::relationalHelpersAgree | atomic | Comparison and Equivalence | covered | Covers public behavior for `relationalHelpersAgree`. |
| atomic::ComparisonAtomicTest::equivalenceAcrossPrefixedUnits | atomic | Comparison and Equivalence | covered | Covers public behavior for `equivalenceAcrossPrefixedUnits`. |
| atomic::ComparisonAtomicTest::equivalenceAcrossOffsetUnits | atomic | Comparison and Equivalence | covered | Covers public behavior for `equivalenceAcrossOffsetUnits`. |
| atomic::ComparisonAtomicTest::equivalenceRepresentationInsensitive | atomic | Comparison and Equivalence | covered | Covers public behavior for `equivalenceRepresentationInsensitive`. |
| atomic::ConstructionAtomicTest::factoryBindsValueUnitScale | atomic | Quantity Construction and Values | covered | Covers public behavior for `factoryBindsValueUnitScale`. |
| atomic::ConstructionAtomicTest::explicitScaleFactory | atomic | Quantity Construction and Values | covered | Covers public behavior for `explicitScaleFactory`. |
| atomic::ConstructionAtomicTest::textFactoryParsesValueAndUnit | atomic | Quantity Construction and Values | covered | Covers public behavior for `textFactoryParsesValueAndUnit`. |
| atomic::ConstructionAtomicTest::textFactoryParsesDecimal | atomic | Quantity Construction and Values | covered | Covers public behavior for `textFactoryParsesDecimal`. |
| atomic::ConstructionAtomicTest::textFactoryParsesPrefixedUnit | atomic | Quantity Construction and Values | covered | Covers public behavior for `textFactoryParsesPrefixedUnit`. |
| atomic::ConstructionAtomicTest::integralInputStaysIntegral | atomic | Quantity Construction and Values | covered | Covers public behavior for `integralInputStaysIntegral`. |
| atomic::ConstructionAtomicTest::toStringRendersValueUnit | atomic | Quantity Construction and Values | covered | Covers public behavior for `toStringRendersValueUnit`. |
| atomic::ConstructionAtomicTest::exactDecimalAddition | atomic | Quantity Construction and Values | covered | Covers public behavior for `exactDecimalAddition`. |
| atomic::ConstructionAtomicTest::exactDivisionMultiplicationRoundTrip | atomic | Quantity Construction and Values | covered | Covers public behavior for `exactDivisionMultiplicationRoundTrip`. |
| atomic::ConstructionAtomicTest::exactResultsKeepNumericShape | atomic | Quantity Construction and Values | covered | Covers public behavior for `exactResultsKeepNumericShape`. |
| atomic::ConversionAtomicTest::kilometreToMetreIntegral | atomic | Conversion and Converters | covered | Covers public behavior for `kilometreToMetreIntegral`. |
| atomic::ConversionAtomicTest::hourToSeconds | atomic | Conversion and Converters | covered | Covers public behavior for `hourToSeconds`. |
| atomic::ConversionAtomicTest::metreToKilometre | atomic | Conversion and Converters | covered | Covers public behavior for `metreToKilometre`. |
| atomic::ConversionAtomicTest::compoundUnitConversionExact | atomic | Conversion and Converters | covered | Covers public behavior for `compoundUnitConversionExact`. |
| atomic::ConversionAtomicTest::celsiusToKelvinOffset | atomic | Conversion and Converters | covered | Covers public behavior for `celsiusToKelvinOffset`. |
| atomic::ConversionAtomicTest::gramToKilogram | atomic | Conversion and Converters | covered | Covers public behavior for `gramToKilogram`. |
| atomic::ConversionAtomicTest::selfConversionReturnsEqual | atomic | Conversion and Converters | covered | Covers public behavior for `selfConversionReturnsEqual`. |
| atomic::ConversionAtomicTest::converterConvertsValues | atomic | Conversion and Converters | covered | Covers public behavior for `converterConvertsValues`. |
| atomic::ConversionAtomicTest::offsetConverterValues | atomic | Conversion and Converters | covered | Covers public behavior for `offsetConverterValues`. |
| atomic::ConversionAtomicTest::converterIdentityAndLinearity | atomic | Conversion and Converters | covered | Covers public behavior for `converterIdentityAndLinearity`. |
| atomic::ConversionAtomicTest::converterToAnyIncompatibleRaises | atomic | Conversion and Converters | covered | Covers public behavior for `converterToAnyIncompatibleRaises`. |
| atomic::ErrorsAtomicTest::textFactoryUnparseableRaises | atomic | Error Semantics | covered | Covers public behavior for `textFactoryUnparseableRaises`. |
| atomic::ErrorsAtomicTest::formatParseWithoutNumberRaises | atomic | Error Semantics | covered | Covers public behavior for `formatParseWithoutNumberRaises`. |
| atomic::ErrorsAtomicTest::unitParseUnknownRaises | atomic | Error Semantics | covered | Covers public behavior for `unitParseUnknownRaises`. |
| atomic::ErrorsAtomicTest::quantityAsTypeMismatchRaises | atomic | Error Semantics | covered | Covers public behavior for `quantityAsTypeMismatchRaises`. |
| atomic::ErrorsAtomicTest::unitAsTypeMismatchRaises | atomic | Error Semantics | covered | Covers public behavior for `unitAsTypeMismatchRaises`. |
| atomic::ErrorsAtomicTest::converterToAnyRaisesChecked | atomic | Error Semantics | covered | Covers public behavior for `converterToAnyRaisesChecked`. |
| atomic::FormatAtomicTest::quantityFormatRendersValueUnit | atomic | Formatting and Parsing | covered | Covers public behavior for `quantityFormatRendersValueUnit`. |
| atomic::FormatAtomicTest::quantityParseReadsBack | atomic | Formatting and Parsing | covered | Covers public behavior for `quantityParseReadsBack`. |
| atomic::FormatAtomicTest::quantityFormatRoundTrips | atomic | Formatting and Parsing | covered | Covers public behavior for `quantityFormatRoundTrips`. |
| atomic::FormatAtomicTest::factoryAgreesWithFormatParse | atomic | Formatting and Parsing | covered | Covers public behavior for `factoryAgreesWithFormatParse`. |
| atomic::FormatAtomicTest::unitFormatRendersSymbols | atomic | Formatting and Parsing | covered | Covers public behavior for `unitFormatRendersSymbols`. |
| atomic::FormatAtomicTest::unitParsePrefixed | atomic | Formatting and Parsing | covered | Covers public behavior for `unitParsePrefixed`. |
| atomic::FormatAtomicTest::unitParseQuotient | atomic | Formatting and Parsing | covered | Covers public behavior for `unitParseQuotient`. |
| atomic::FormatAtomicTest::unknownUnitSymbolRaises | atomic | Formatting and Parsing | covered | Covers public behavior for `unknownUnitSymbolRaises`. |
| atomic::FormatAtomicTest::nonNumericQuantityTextRaises | atomic | Formatting and Parsing | covered | Covers public behavior for `nonNumericQuantityTextRaises`. |
| atomic::ScaleAtomicTest::defaultScaleIsAbsolute | atomic | Scales and Temperature Arithmetic | covered | Covers public behavior for `defaultScaleIsAbsolute`. |
| atomic::ScaleAtomicTest::explicitRelativeScale | atomic | Scales and Temperature Arithmetic | covered | Covers public behavior for `explicitRelativeScale`. |
| atomic::ScaleAtomicTest::absoluteCelsiusConvertsWithOffset | atomic | Scales and Temperature Arithmetic | covered | Covers public behavior for `absoluteCelsiusConvertsWithOffset`. |
| atomic::ScaleAtomicTest::relativeCelsiusConvertsByFactorOnly | atomic | Scales and Temperature Arithmetic | covered | Covers public behavior for `relativeCelsiusConvertsByFactorOnly`. |
| atomic::ScaleAtomicTest::absolutePlusAbsoluteSumsOnAbsoluteScale | atomic | Scales and Temperature Arithmetic | covered | Covers public behavior for `absolutePlusAbsoluteSumsOnAbsoluteScale`. |
| atomic::ScaleAtomicTest::absolutePlusRelativeTreatsDelta | atomic | Scales and Temperature Arithmetic | covered | Covers public behavior for `absolutePlusRelativeTreatsDelta`. |
| atomic::ScaleAtomicTest::relativePlusRelativeAddsDeltas | atomic | Scales and Temperature Arithmetic | covered | Covers public behavior for `relativePlusRelativeAddsDeltas`. |
| atomic::StateModelAtomicTest::operationsLeaveOperandsUntouched | atomic | State Model | covered | Covers public behavior for `operationsLeaveOperandsUntouched`. |
| atomic::StateModelAtomicTest::equalTriplesBehaveIdentically | atomic | State Model | covered | Covers public behavior for `equalTriplesBehaveIdentically`. |
| atomic::StateModelAtomicTest::formatSingletonsAreSharedAndStateless | atomic | State Model | covered | Covers public behavior for `formatSingletonsAreSharedAndStateless`. |
| atomic::StateModelAtomicTest::unitsSingletonIsStable | atomic | State Model | covered | Covers public behavior for `unitsSingletonIsStable`. |
| atomic::StateModelAtomicTest::unitAlgebraLeavesConstantsUntouched | atomic | State Model | covered | Covers public behavior for `unitAlgebraLeavesConstantsUntouched`. |
| atomic::UnitAlgebraAtomicTest::baseUnitSymbols | atomic | Unit Algebra and the System of Units | covered | Covers public behavior for `baseUnitSymbols`. |
| atomic::UnitAlgebraAtomicTest::systemSingletonAndContents | atomic | Unit Algebra and the System of Units | covered | Covers public behavior for `systemSingletonAndContents`. |
| atomic::UnitAlgebraAtomicTest::prefixBuildsScaledUnit | atomic | Unit Algebra and the System of Units | covered | Covers public behavior for `prefixBuildsScaledUnit`. |
| atomic::UnitAlgebraAtomicTest::prefixedUnitSystemUnit | atomic | Unit Algebra and the System of Units | covered | Covers public behavior for `prefixedUnitSystemUnit`. |
| atomic::UnitAlgebraAtomicTest::prefixedUnitSymbolIsNull | atomic | Unit Algebra and the System of Units | covered | Covers public behavior for `prefixedUnitSymbolIsNull`. |
| atomic::UnitAlgebraAtomicTest::multiplyAndPowDeriveSquare | atomic | Unit Algebra and the System of Units | covered | Covers public behavior for `multiplyAndPowDeriveSquare`. |
| atomic::UnitAlgebraAtomicTest::divideDerivesQuotient | atomic | Unit Algebra and the System of Units | covered | Covers public behavior for `divideDerivesQuotient`. |
| atomic::UnitAlgebraAtomicTest::rootInvertsPow | atomic | Unit Algebra and the System of Units | covered | Covers public behavior for `rootInvertsPow`. |
| atomic::UnitAlgebraAtomicTest::structuralEqualityDistinguishesConstruction | atomic | Unit Algebra and the System of Units | covered | Covers public behavior for `structuralEqualityDistinguishesConstruction`. |
| atomic::UnitAlgebraAtomicTest::compatibilityAndDimension | atomic | Unit Algebra and the System of Units | covered | Covers public behavior for `compatibilityAndDimension`. |
| atomic::UnitAlgebraAtomicTest::unitAsTypeChecksDimension | atomic | Unit Algebra and the System of Units | covered | Covers public behavior for `unitAsTypeChecksDimension`. |
| integration::InvariantsIntegrationTest::equivalenceConversionAgreement | integration | Cross-View Invariants | covered | Covers public behavior for `equivalenceConversionAgreement`. |
| integration::InvariantsIntegrationTest::orderingEquivalenceCoherence | integration | Cross-View Invariants | covered | Covers public behavior for `orderingEquivalenceCoherence`. |
| integration::InvariantsIntegrationTest::arithmeticUnitAlgebraAgreement | integration | Cross-View Invariants | covered | Covers public behavior for `arithmeticUnitAlgebraAgreement`. |
| integration::InvariantsIntegrationTest::conversionConverterAgreement | integration | Cross-View Invariants | covered | Covers public behavior for `conversionConverterAgreement`. |
| integration::InvariantsIntegrationTest::leftUnitRuleAcrossPairs | integration | Cross-View Invariants | covered | Covers public behavior for `leftUnitRuleAcrossPairs`. |
| integration::InvariantsIntegrationTest::exactnessAcrossChains | integration | Cross-View Invariants | covered | Covers public behavior for `exactnessAcrossChains`. |
| integration::InvariantsIntegrationTest::formatRoundTripAgreement | integration | Cross-View Invariants | covered | Covers public behavior for `formatRoundTripAgreement`. |
| integration::InvariantsIntegrationTest::oneMeasureManyViews | integration | Cross-View Invariants | covered | Covers public behavior for `oneMeasureManyViews`. |
| integration::InvariantsIntegrationTest::algebraUnitsReparseToNamedConstants | integration | Cross-View Invariants | covered | Covers public behavior for `algebraUnitsReparseToNamedConstants`. |
| integration::ScaleLifecycleIntegrationTest::deltaLedgerAccumulates | integration | Scales and Temperature Arithmetic | covered | Covers public behavior for `deltaLedgerAccumulates`. |
| integration::ScaleLifecycleIntegrationTest::summedDeltasApplyLikeSequentialDeltas | integration | Scales and Temperature Arithmetic | covered | Covers public behavior for `summedDeltasApplyLikeSequentialDeltas`. |
| integration::ScaleLifecycleIntegrationTest::scaleRoundTripsDiverge | integration | Scales and Temperature Arithmetic | covered | Covers public behavior for `scaleRoundTripsDiverge`. |
| integration::ScaleLifecycleIntegrationTest::absoluteSumAgreesWithKelvinComputation | integration | Scales and Temperature Arithmetic | covered | Covers public behavior for `absoluteSumAgreesWithKelvinComputation`. |
| integration::ScaleLifecycleIntegrationTest::quantityTripleSurvivesUse | integration | State Model | covered | Covers public behavior for `quantityTripleSurvivesUse`. |
| integration::ScaleLifecycleIntegrationTest::formatBehaviorIsStableAcrossUse | integration | State Model | covered | Covers public behavior for `formatBehaviorIsStableAcrossUse`. |
| integration::ScaleLifecycleIntegrationTest::mixedSeriesOrdersByMeasure | integration | Cross-View Invariants | covered | Covers public behavior for `mixedSeriesOrdersByMeasure`. |
| integration::WorkflowIntegrationTest::parseConvertComputeFormatPipeline | integration | Cross-View Invariants | covered | Covers public behavior for `parseConvertComputeFormatPipeline`. |
| integration::WorkflowIntegrationTest::tripSpeedComputation | integration | Cross-View Invariants | covered | Covers public behavior for `tripSpeedComputation`. |
| integration::WorkflowIntegrationTest::speedTimesTimeYieldsLength | integration | Cross-View Invariants | covered | Covers public behavior for `speedTimesTimeYieldsLength`. |
| integration::WorkflowIntegrationTest::massLedgerAccumulation | integration | Cross-View Invariants | covered | Covers public behavior for `massLedgerAccumulation`. |
| integration::WorkflowIntegrationTest::mixedUnitAccumulationStaysExact | integration | Cross-View Invariants | covered | Covers public behavior for `mixedUnitAccumulationStaysExact`. |
| integration::WorkflowIntegrationTest::dimensionlessRatioWorkflow | integration | Cross-View Invariants | covered | Covers public behavior for `dimensionlessRatioWorkflow`. |
| integration::WorkflowIntegrationTest::converterChainRestoresInput | integration | Cross-View Invariants | covered | Covers public behavior for `converterChainRestoresInput`. |
| integration::WorkflowIntegrationTest::textEntryPointsAgreeOnMeasure | integration | Formatting and Parsing | covered | Covers public behavior for `textEntryPointsAgreeOnMeasure`. |
| integration::WorkflowIntegrationTest::errorPathsLeaveStateIntact | integration | Error Semantics | covered | Covers public behavior for `errorPathsLeaveStateIntact`. |
| integration::WorkflowIntegrationTest::timeStaircasePreservesMeasure | integration | Cross-View Invariants | covered | Covers public behavior for `timeStaircasePreservesMeasure`. |
