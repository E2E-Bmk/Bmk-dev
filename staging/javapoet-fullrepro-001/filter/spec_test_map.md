# Spec Test Map

| test_nodeid | layer | spec_section | status | notes |
|---|---|---|---|---|
| atomic::ClassNameAtomicTest::getBuildsFromPackageAndSimpleName | atomic | Type Name Model | covered | Covers public behavior for `getBuildsFromPackageAndSimpleName`. |
| atomic::ClassNameAtomicTest::bestGuessSplitsPackageAndNestedClasses | atomic | Type Name Model | covered | Covers public behavior for `bestGuessSplitsPackageAndNestedClasses`. |
| atomic::ClassNameAtomicTest::reflectionNameUsesDollarForNesting | atomic | Cross-View Invariants | covered | Covers public behavior for `reflectionNameUsesDollarForNesting`. |
| atomic::ClassNameAtomicTest::topLevelClassNameIsChainHead | atomic | Cross-View Invariants | covered | Covers public behavior for `topLevelClassNameIsChainHead`. |
| atomic::ClassNameAtomicTest::nestedClassEnclosingRoundTrip | atomic | Cross-View Invariants | covered | Covers public behavior for `nestedClassEnclosingRoundTrip`. |
| atomic::ClassNameAtomicTest::peerClassNamesSibling | atomic | Type Name Model | covered | Covers public behavior for `peerClassNamesSibling`. |
| atomic::ClassNameAtomicTest::defaultPackageRendersBareName | atomic | Type Name Model | covered | Covers public behavior for `defaultPackageRendersBareName`. |
| atomic::ClassNameAtomicTest::equalChainsAreEqualAndComparable | atomic | Type Name Model | covered | Covers public behavior for `equalChainsAreEqualAndComparable`. |
| atomic::ClassNameAtomicTest::bestGuessWithoutClassSegmentThrows | atomic | Error Semantics | covered | Covers public behavior for `bestGuessWithoutClassSegmentThrows`. |
| atomic::FormatLanguageAtomicTest::literalPlaceholderEmitsNumbersBooleansAndText | atomic | Code Blocks and the Format Language | covered | Covers public behavior for `literalPlaceholderEmitsNumbersBooleansAndText`. |
| atomic::FormatLanguageAtomicTest::literalPlaceholderEmitsNullText | atomic | Code Blocks and the Format Language | covered | Covers public behavior for `literalPlaceholderEmitsNullText`. |
| atomic::FormatLanguageAtomicTest::stringPlaceholderQuotesAndEscapes | atomic | Code Blocks and the Format Language | covered | Covers public behavior for `stringPlaceholderQuotesAndEscapes`. |
| atomic::FormatLanguageAtomicTest::stringPlaceholderEmitsUnquotedNull | atomic | Code Blocks and the Format Language | covered | Covers public behavior for `stringPlaceholderEmitsUnquotedNull`. |
| atomic::FormatLanguageAtomicTest::typePlaceholderIsFullyQualifiedStandalone | atomic | Code Blocks and the Format Language | covered | Covers public behavior for `typePlaceholderIsFullyQualifiedStandalone`. |
| atomic::FormatLanguageAtomicTest::namePlaceholderEmitsMethodName | atomic | Code Blocks and the Format Language | covered | Covers public behavior for `namePlaceholderEmitsMethodName`. |
| atomic::FormatLanguageAtomicTest::doubleDollarEmitsOneDollar | atomic | Code Blocks and the Format Language | covered | Covers public behavior for `doubleDollarEmitsOneDollar`. |
| atomic::FormatLanguageAtomicTest::joinConcatenatesBlocksWithSeparator | atomic | Code Blocks and the Format Language | covered | Covers public behavior for `joinConcatenatesBlocksWithSeparator`. |
| atomic::FormatLanguageAtomicTest::joiningCollectorMatchesJoin | atomic | Code Blocks and the Format Language | covered | Covers public behavior for `joiningCollectorMatchesJoin`. |
| atomic::FormatLanguageAtomicTest::isEmptyReflectsContent | atomic | Code Blocks and the Format Language | covered | Covers public behavior for `isEmptyReflectsContent`. |
| atomic::FormatLanguageAtomicTest::equalContentBlocksAreEqual | atomic | Code Blocks and the Format Language | covered | Covers public behavior for `equalContentBlocksAreEqual`. |
| atomic::FormatLanguageAtomicTest::unknownPlaceholderThrows | atomic | Error Semantics | covered | Covers public behavior for `unknownPlaceholderThrows`. |
| atomic::FormatLanguageAtomicTest::mismatchedArgumentCountThrows | atomic | Error Semantics | covered | Covers public behavior for `mismatchedArgumentCountThrows`. |
| atomic::FormatLanguageAtomicTest::codeBlockToBuilderRoundTripsEqually | atomic | Code Blocks and the Format Language | covered | Covers public behavior for `codeBlockToBuilderRoundTripsEqually`. |
| atomic::MethodFieldAtomicTest::emptyMethodRendersVoidAndEmptyBraces | atomic | Methods, Fields, Parameters, and Annotations | covered | Covers public behavior for `emptyMethodRendersVoidAndEmptyBraces`. |
| atomic::MethodFieldAtomicTest::methodRendersModifiersParametersAndBody | atomic | Methods, Fields, Parameters, and Annotations | covered | Covers public behavior for `methodRendersModifiersParametersAndBody`. |
| atomic::MethodFieldAtomicTest::controlFlowRendersBracesAndElseChaining | atomic | Code Blocks and the Format Language | covered | Covers public behavior for `controlFlowRendersBracesAndElseChaining`. |
| atomic::MethodFieldAtomicTest::varargsRendersEllipsisOnFinalArrayParameter | atomic | Methods, Fields, Parameters, and Annotations | covered | Covers public behavior for `varargsRendersEllipsisOnFinalArrayParameter`. |
| atomic::MethodFieldAtomicTest::javadocRendersCommentBlockAboveDeclaration | atomic | Methods, Fields, Parameters, and Annotations | covered | Covers public behavior for `javadocRendersCommentBlockAboveDeclaration`. |
| atomic::MethodFieldAtomicTest::abstractMethodWithCodeThrows | atomic | Error Semantics | covered | Covers public behavior for `abstractMethodWithCodeThrows`. |
| atomic::MethodFieldAtomicTest::constructorFlagAndMethodNameProjection | atomic | Methods, Fields, Parameters, and Annotations | covered | Covers public behavior for `constructorFlagAndMethodNameProjection`. |
| atomic::MethodFieldAtomicTest::fieldRendersModifiersTypeAndInitializer | atomic | Methods, Fields, Parameters, and Annotations | covered | Covers public behavior for `fieldRendersModifiersTypeAndInitializer`. |
| atomic::MethodFieldAtomicTest::parameterSpecCarriesAnnotationsAndModifiers | atomic | Methods, Fields, Parameters, and Annotations | covered | Covers public behavior for `parameterSpecCarriesAnnotationsAndModifiers`. |
| atomic::MethodFieldAtomicTest::annotationRendersMembersInInsertionOrder | atomic | Methods, Fields, Parameters, and Annotations | covered | Covers public behavior for `annotationRendersMembersInInsertionOrder`. |
| atomic::MethodFieldAtomicTest::markerAnnotationRendersBareType | atomic | Methods, Fields, Parameters, and Annotations | covered | Covers public behavior for `markerAnnotationRendersBareType`. |
| atomic::MethodFieldAtomicTest::methodToBuilderRoundTripsEqually | atomic | State Model | covered | Covers public behavior for `methodToBuilderRoundTripsEqually`. |
| atomic::NameAllocatorAtomicTest::keywordSuggestionGetsUnderscoreSuffix | atomic | Name Allocation | covered | Covers public behavior for `keywordSuggestionGetsUnderscoreSuffix`. |
| atomic::NameAllocatorAtomicTest::duplicateSuggestionGetsSuffix | atomic | Name Allocation | covered | Covers public behavior for `duplicateSuggestionGetsSuffix`. |
| atomic::NameAllocatorAtomicTest::illegalCharactersAreReplaced | atomic | Name Allocation | covered | Covers public behavior for `illegalCharactersAreReplaced`. |
| atomic::NameAllocatorAtomicTest::leadingDigitIsPrefixed | atomic | Name Allocation | covered | Covers public behavior for `leadingDigitIsPrefixed`. |
| atomic::NameAllocatorAtomicTest::tagRegistrationRoundTrips | atomic | Name Allocation | covered | Covers public behavior for `tagRegistrationRoundTrips`. |
| atomic::NameAllocatorAtomicTest::cloneCarriesRegistrationsIndependently | atomic | Name Allocation | covered | Covers public behavior for `cloneCarriesRegistrationsIndependently`. |
| atomic::TypeNameAtomicTest::primitiveConstantEqualsGetOnClass | atomic | Type Name Model | covered | Covers public behavior for `primitiveConstantEqualsGetOnClass`. |
| atomic::TypeNameAtomicTest::objectConstantRendersCanonicalName | atomic | Type Name Model | covered | Covers public behavior for `objectConstantRendersCanonicalName`. |
| atomic::TypeNameAtomicTest::boxMapsPrimitiveToBoxedClass | atomic | Type Name Model | covered | Covers public behavior for `boxMapsPrimitiveToBoxedClass`. |
| atomic::TypeNameAtomicTest::boxThenUnboxReturnsPrimitive | atomic | Type Name Model | covered | Covers public behavior for `boxThenUnboxReturnsPrimitive`. |
| atomic::TypeNameAtomicTest::primitiveClassificationFlags | atomic | Type Name Model | covered | Covers public behavior for `primitiveClassificationFlags`. |
| atomic::TypeNameAtomicTest::unboxOnPlainClassThrows | atomic | Error Semantics | covered | Covers public behavior for `unboxOnPlainClassThrows`. |
| atomic::TypeNameAtomicTest::parameterizedTypeRendersAngleBrackets | atomic | Type Name Model | covered | Covers public behavior for `parameterizedTypeRendersAngleBrackets`. |
| atomic::TypeNameAtomicTest::parameterizedTypeClassOverloadAgrees | atomic | Type Name Model | covered | Covers public behavior for `parameterizedTypeClassOverloadAgrees`. |
| atomic::TypeNameAtomicTest::arrayTypeRendersBrackets | atomic | Type Name Model | covered | Covers public behavior for `arrayTypeRendersBrackets`. |
| atomic::TypeNameAtomicTest::wildcardSubtypeOfObjectIsBareQuestionMark | atomic | Type Name Model | covered | Covers public behavior for `wildcardSubtypeOfObjectIsBareQuestionMark`. |
| atomic::TypeNameAtomicTest::boundedWildcardsRenderExtendsAndSuper | atomic | Type Name Model | covered | Covers public behavior for `boundedWildcardsRenderExtendsAndSuper`. |
| atomic::TypeNameAtomicTest::typeVariableExposesNameAndBounds | atomic | Type Name Model | covered | Covers public behavior for `typeVariableExposesNameAndBounds`. |
| atomic::TypeSpecAtomicTest::interfaceOmitsPublicAbstractOnMethods | atomic | Type Declarations | covered | Covers public behavior for `interfaceOmitsPublicAbstractOnMethods`. |
| atomic::TypeSpecAtomicTest::initializerBlocksRenderInDocumentedOrder | atomic | Type Declarations | covered | Covers public behavior for `initializerBlocksRenderInDocumentedOrder`. |
| atomic::TypeSpecAtomicTest::enumConstantsRenderArgumentsAndBodies | atomic | Type Declarations | covered | Covers public behavior for `enumConstantsRenderArgumentsAndBodies`. |
| atomic::TypeSpecAtomicTest::enumWithoutConstantsThrows | atomic | Error Semantics | covered | Covers public behavior for `enumWithoutConstantsThrows`. |
| atomic::TypeSpecAtomicTest::interfaceMethodWithProtectedModifierThrows | atomic | Error Semantics | covered | Covers public behavior for `interfaceMethodWithProtectedModifierThrows`. |
| atomic::TypeSpecAtomicTest::typeSpecNameAndToBuilderRoundTrip | atomic | Type Declarations | covered | Covers public behavior for `typeSpecNameAndToBuilderRoundTrip`. |
| atomic::TypeSpecAtomicTest::superclassAndInterfacesRenderInHeader | atomic | Type Declarations | covered | Covers public behavior for `superclassAndInterfacesRenderInHeader`. |
| atomic::TypeSpecAtomicTest::annotationTypeRendersAtInterface | atomic | Type Declarations | covered | Covers public behavior for `annotationTypeRendersAtInterface`. |
| integration::FileAssemblyIntegrationTest::javaLangTypesAreImportedByDefault | integration | Source File Assembly and Import Resolution | covered | Covers public behavior for `javaLangTypesAreImportedByDefault`. |
| integration::FileAssemblyIntegrationTest::skipJavaLangImportsRendersShortNamesWithoutImports | integration | Source File Assembly and Import Resolution | covered | Covers public behavior for `skipJavaLangImportsRendersShortNamesWithoutImports`. |
| integration::FileAssemblyIntegrationTest::simpleNameCollisionFullyQualifiesLaterType | integration | Source File Assembly and Import Resolution | covered | Covers public behavior for `simpleNameCollisionFullyQualifiesLaterType`. |
| integration::FileAssemblyIntegrationTest::nestedTypeImportsTopLevelAndRendersQualifiedNesting | integration | Source File Assembly and Import Resolution | covered | Covers public behavior for `nestedTypeImportsTopLevelAndRendersQualifiedNesting`. |
| integration::FileAssemblyIntegrationTest::staticImportRendersBareMemberReference | integration | Source File Assembly and Import Resolution | covered | Covers public behavior for `staticImportRendersBareMemberReference`. |
| integration::FileAssemblyIntegrationTest::importsAreSortedLexicographically | integration | Source File Assembly and Import Resolution | covered | Covers public behavior for `importsAreSortedLexicographically`. |
| integration::FileAssemblyIntegrationTest::fileCommentAndCustomIndentApply | integration | Source File Assembly and Import Resolution | covered | Covers public behavior for `fileCommentAndCustomIndentApply`. |
| integration::FileAssemblyIntegrationTest::defaultPackageOmitsPackageStatement | integration | Source File Assembly and Import Resolution | covered | Covers public behavior for `defaultPackageOmitsPackageStatement`. |
| integration::FileAssemblyIntegrationTest::writeToCreatesPackageTreeWithIdenticalContent | integration | Cross-View Invariants | covered | Covers public behavior for `writeToCreatesPackageTreeWithIdenticalContent`. |
| integration::FileAssemblyIntegrationTest::parameterizedFieldImportsRawAndArgumentTypes | integration | Source File Assembly and Import Resolution | covered | Covers public behavior for `parameterizedFieldImportsRawAndArgumentTypes`. |
| integration::FileAssemblyIntegrationTest::javaFileExposesPackageAndTypeSpec | integration | State Model | covered | Covers public behavior for `javaFileExposesPackageAndTypeSpec`. |
| integration::GenerationWorkflowIntegrationTest::helloWorldClassRendersCompleteCompilationUnit | integration | Representative Workflows | covered | Covers public behavior for `helloWorldClassRendersCompleteCompilationUnit`. |
| integration::GenerationWorkflowIntegrationTest::enumWithBodiedConstantsRendersConstructorAndOverrides | integration | Type Declarations | covered | Covers public behavior for `enumWithBodiedConstantsRendersConstructorAndOverrides`. |
| integration::GenerationWorkflowIntegrationTest::anonymousComparatorEmbedsThroughLiteralPlaceholder | integration | Type Declarations | covered | Covers public behavior for `anonymousComparatorEmbedsThroughLiteralPlaceholder`. |
| integration::GenerationWorkflowIntegrationTest::genericMethodRendersTypeVariableBoundsAndThrows | integration | Methods | covered | Covers public behavior for `genericMethodRendersTypeVariableBoundsAndThrows`. |
| integration::GenerationWorkflowIntegrationTest::multiWayControlFlowComposesInsideMethod | integration | Code Blocks | covered | Covers public behavior for `multiWayControlFlowComposesInsideMethod`. |
| integration::GenerationWorkflowIntegrationTest::nameAllocatorFeedsGeneratedFieldsWithoutCollisions | integration | Name Allocation | covered | Covers public behavior for `nameAllocatorFeedsGeneratedFieldsWithoutCollisions`. |
| integration::GenerationWorkflowIntegrationTest::interfaceWithConstantAndMethodRendersImplicitModifiers | integration | Type Declarations | covered | Covers public behavior for `interfaceWithConstantAndMethodRendersImplicitModifiers`. |
| integration::GenerationWorkflowIntegrationTest::joinedFragmentsFormOneStatementInsideMethod | integration | Code Blocks | covered | Covers public behavior for `joinedFragmentsFormOneStatementInsideMethod`. |
| integration::GenerationWorkflowIntegrationTest::nestedTypeRendersInsideEnclosingBody | integration | Type Declarations | covered | Covers public behavior for `nestedTypeRendersInsideEnclosingBody`. |
| integration::RoundTripIntegrationTest::typeSpecToBuilderReproducesEqualSpecAndText | integration | Cross-View Invariants | covered | Covers public behavior for `typeSpecToBuilderReproducesEqualSpecAndText`. |
| integration::RoundTripIntegrationTest::memberSpecsRoundTripThroughToBuilder | integration | Cross-View Invariants | covered | Covers public behavior for `memberSpecsRoundTripThroughToBuilder`. |
| integration::RoundTripIntegrationTest::differentConstructionPathsWithSameContentAreEqual | integration | State Model | covered | Covers public behavior for `differentConstructionPathsWithSameContentAreEqual`. |
| integration::RoundTripIntegrationTest::classNameNavigationIsSelfConsistent | integration | Cross-View Invariants | covered | Covers public behavior for `classNameNavigationIsSelfConsistent`. |
| integration::RoundTripIntegrationTest::javaFileToBuilderPreservesRendering | integration | State Model | covered | Covers public behavior for `javaFileToBuilderPreservesRendering`. |
| integration::RoundTripIntegrationTest::writeToPathReturnsFileMatchingToString | integration | Source File Assembly | covered | Covers public behavior for `writeToPathReturnsFileMatchingToString`. |
| integration::RoundTripIntegrationTest::toJavaFileObjectAgreesWithToString | integration | Source File Assembly | covered | Covers public behavior for `toJavaFileObjectAgreesWithToString`. |
| integration::RoundTripIntegrationTest::typeSpecPublicFieldsProjectMembers | integration | State Model | covered | Covers public behavior for `typeSpecPublicFieldsProjectMembers`. |
| integration::RoundTripIntegrationTest::distinctContentIsUnequalAndRendersDifferently | integration | Cross-View Invariants | covered | Covers public behavior for `distinctContentIsUnequalAndRendersDifferently`. |
| integration::RoundTripIntegrationTest::standaloneRenderingUsesQualifiedNamesWhereFileUsesImports | integration | Cross-View Invariants | covered | Covers public behavior for `standaloneRenderingUsesQualifiedNamesWhereFileUsesImports`. |
