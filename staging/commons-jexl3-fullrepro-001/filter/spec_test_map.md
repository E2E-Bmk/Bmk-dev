# Spec Test Map

| test_nodeid | layer | spec_section | status | notes |
|---|---|---|---|---|
| atomic::ArithmeticAtomicTest::integerArithmeticStaysInteger | atomic | Expression Language | covered | Covers public behavior for `integerArithmeticStaysInteger`. |
| atomic::ArithmeticAtomicTest::integerDivisionTruncates | atomic | Expression Language | covered | Covers public behavior for `integerDivisionTruncates`. |
| atomic::ArithmeticAtomicTest::floatingOperandProducesDouble | atomic | Expression Language | covered | Covers public behavior for `floatingOperandProducesDouble`. |
| atomic::ArithmeticAtomicTest::overflowWidensToLong | atomic | Expression Language | covered | Covers public behavior for `overflowWidensToLong`. |
| atomic::ArithmeticAtomicTest::longArithmetic | atomic | Expression Language | covered | Covers public behavior for `longArithmetic`. |
| atomic::ArithmeticAtomicTest::plusConcatenatesWithStrings | atomic | Expression Language | covered | Covers public behavior for `plusConcatenatesWithStrings`. |
| atomic::ArithmeticAtomicTest::concatenationAssociativity | atomic | Expression Language | covered | Covers public behavior for `concatenationAssociativity`. |
| atomic::ArithmeticAtomicTest::unaryMinusNegates | atomic | Expression Language | covered | Covers public behavior for `unaryMinusNegates`. |
| atomic::ComparisonLogicAtomicTest::relationalOperators | atomic | Expression Language | covered | Covers public behavior for `relationalOperators`. |
| atomic::ComparisonLogicAtomicTest::equalityCoerces | atomic | Expression Language | covered | Covers public behavior for `equalityCoerces`. |
| atomic::ComparisonLogicAtomicTest::keywordEqualityAliases | atomic | Expression Language | covered | Covers public behavior for `keywordEqualityAliases`. |
| atomic::ComparisonLogicAtomicTest::logicalOperators | atomic | Expression Language | covered | Covers public behavior for `logicalOperators`. |
| atomic::ComparisonLogicAtomicTest::ternarySelectsByTruthiness | atomic | Expression Language | covered | Covers public behavior for `ternarySelectsByTruthiness`. |
| atomic::ComparisonLogicAtomicTest::elvisIsTruthinessBased | atomic | Expression Language | covered | Covers public behavior for `elvisIsTruthinessBased`. |
| atomic::ComparisonLogicAtomicTest::nullCoalescingKeepsFalsyNonNull | atomic | Expression Language | covered | Covers public behavior for `nullCoalescingKeepsFalsyNonNull`. |
| atomic::ComparisonLogicAtomicTest::fallbacksTolerateUndefined | atomic | Expression Language | covered | Covers public behavior for `fallbacksTolerateUndefined`. |
| atomic::EnginesErrorsAtomicTest::strictUndefinedVariableRaises | atomic | Error Semantics | covered | Covers public behavior for `strictUndefinedVariableRaises`. |
| atomic::EnginesErrorsAtomicTest::strictNullOperandRaises | atomic | Error Semantics | covered | Covers public behavior for `strictNullOperandRaises`. |
| atomic::EnginesErrorsAtomicTest::strictDivisionByZeroRaises | atomic | Error Semantics | covered | Covers public behavior for `strictDivisionByZeroRaises`. |
| atomic::EnginesErrorsAtomicTest::strictNullConditionRaises | atomic | Error Semantics | covered | Covers public behavior for `strictNullConditionRaises`. |
| atomic::EnginesErrorsAtomicTest::lenientSubstitutesNeutralValues | atomic | Engines and Evaluation Modes | covered | Covers public behavior for `lenientSubstitutesNeutralValues`. |
| atomic::EnginesErrorsAtomicTest::lenientDivisionByZeroYieldsZero | atomic | Engines and Evaluation Modes | covered | Covers public behavior for `lenientDivisionByZeroYieldsZero`. |
| atomic::EnginesErrorsAtomicTest::silentConvertsErrorsToNull | atomic | Engines and Evaluation Modes | covered | Covers public behavior for `silentConvertsErrorsToNull`. |
| atomic::EnginesErrorsAtomicTest::unsafeNullNavigationRaises | atomic | Error Semantics | covered | Covers public behavior for `unsafeNullNavigationRaises`. |
| atomic::EnginesErrorsAtomicTest::syntaxErrorsRaiseParsing | atomic | Error Semantics | covered | Covers public behavior for `syntaxErrorsRaiseParsing`. |
| atomic::EnginesErrorsAtomicTest::missingArgumentRaises | atomic | Error Semantics | covered | Covers public behavior for `missingArgumentRaises`. |
| atomic::EnginesErrorsAtomicTest::sourceTextIsPreserved | atomic | Engines and Evaluation Modes | covered | Covers public behavior for `sourceTextIsPreserved`. |
| atomic::LiteralsAtomicTest::integerLiteral | atomic | Expression Language | covered | Covers public behavior for `integerLiteral`. |
| atomic::LiteralsAtomicTest::longLiteral | atomic | Expression Language | covered | Covers public behavior for `longLiteral`. |
| atomic::LiteralsAtomicTest::doubleLiteral | atomic | Expression Language | covered | Covers public behavior for `doubleLiteral`. |
| atomic::LiteralsAtomicTest::stringLiterals | atomic | Expression Language | covered | Covers public behavior for `stringLiterals`. |
| atomic::LiteralsAtomicTest::booleanAndNullLiterals | atomic | Expression Language | covered | Covers public behavior for `booleanAndNullLiterals`. |
| atomic::LiteralsAtomicTest::arrayLiteralIsIntArray | atomic | Expression Language | covered | Covers public behavior for `arrayLiteralIsIntArray`. |
| atomic::LiteralsAtomicTest::mapLiteral | atomic | Expression Language | covered | Covers public behavior for `mapLiteral`. |
| atomic::LiteralsAtomicTest::setLiteral | atomic | Expression Language | covered | Covers public behavior for `setLiteral`. |
| atomic::MatchingSizeAtomicTest::regexMatch | atomic | Expression Language | covered | Covers public behavior for `regexMatch`. |
| atomic::MatchingSizeAtomicTest::containmentMatch | atomic | Expression Language | covered | Covers public behavior for `containmentMatch`. |
| atomic::MatchingSizeAtomicTest::prefixAndSuffixOperators | atomic | Expression Language | covered | Covers public behavior for `prefixAndSuffixOperators`. |
| atomic::MatchingSizeAtomicTest::sizeAcrossShapes | atomic | Expression Language | covered | Covers public behavior for `sizeAcrossShapes`. |
| atomic::MatchingSizeAtomicTest::emptyAcrossShapes | atomic | Expression Language | covered | Covers public behavior for `emptyAcrossShapes`. |
| atomic::NavigationContextAtomicTest::propertyNavigationForms | atomic | Expression Language | covered | Covers public behavior for `propertyNavigationForms`. |
| atomic::NavigationContextAtomicTest::listIndexing | atomic | Expression Language | covered | Covers public behavior for `listIndexing`. |
| atomic::NavigationContextAtomicTest::methodCallOnValue | atomic | Expression Language | covered | Covers public behavior for `methodCallOnValue`. |
| atomic::NavigationContextAtomicTest::safeNavigationOnNullBase | atomic | Engines and Evaluation Modes | covered | Covers public behavior for `safeNavigationOnNullBase`. |
| atomic::NavigationContextAtomicTest::assignmentWritesThrough | atomic | Expression Language | covered | Covers public behavior for `assignmentWritesThrough`. |
| atomic::NavigationContextAtomicTest::compoundAssignment | atomic | Expression Language | covered | Covers public behavior for `compoundAssignment`. |
| atomic::NavigationContextAtomicTest::hasDistinguishesAbsentFromNull | atomic | Contexts | covered | Covers public behavior for `hasDistinguishesAbsentFromNull`. |
| atomic::NavigationContextAtomicTest::wrappedMapIsSharedStore | atomic | Contexts | covered | Covers public behavior for `wrappedMapIsSharedStore`. |
| atomic::ScriptsAtomicTest::lastStatementIsResult | atomic | Scripts and Control Flow | covered | Covers public behavior for `lastStatementIsResult`. |
| atomic::ScriptsAtomicTest::varLocalsDoNotLeak | atomic | Scripts and Control Flow | covered | Covers public behavior for `varLocalsDoNotLeak`. |
| atomic::ScriptsAtomicTest::ifElseSelects | atomic | Scripts and Control Flow | covered | Covers public behavior for `ifElseSelects`. |
| atomic::ScriptsAtomicTest::whileLoops | atomic | Scripts and Control Flow | covered | Covers public behavior for `whileLoops`. |
| atomic::ScriptsAtomicTest::forIteratesCollection | atomic | Scripts and Control Flow | covered | Covers public behavior for `forIteratesCollection`. |
| atomic::ScriptsAtomicTest::forIteratesRange | atomic | Scripts and Control Flow | covered | Covers public behavior for `forIteratesRange`. |
| atomic::ScriptsAtomicTest::returnEndsScript | atomic | Scripts and Control Flow | covered | Covers public behavior for `returnEndsScript`. |
| atomic::ScriptsAtomicTest::lambdaIsCallable | atomic | Scripts and Control Flow | covered | Covers public behavior for `lambdaIsCallable`. |
| atomic::ScriptsAtomicTest::parametersBindPositionally | atomic | Scripts and Control Flow | covered | Covers public behavior for `parametersBindPositionally`. |
| atomic::ScriptsAtomicTest::parametersDoNotLeakToContext | atomic | Scripts and Control Flow | covered | Covers public behavior for `parametersDoNotLeakToContext`. |
| atomic::ScriptsAtomicTest::variableIntrospection | atomic | Scripts and Control Flow | covered | Covers public behavior for `variableIntrospection`. |
| atomic::ScriptsAtomicTest::expressionRejectsStatements | atomic | Scripts and Control Flow | covered | Covers public behavior for `expressionRejectsStatements`. |
| integration::ContextFlowIntegrationTest::assignmentAndContextAgree | integration | Cross-View Invariants | covered | Covers public behavior for `assignmentAndContextAgree`. |
| integration::ContextFlowIntegrationTest::wrappedMapSingleStore | integration | Cross-View Invariants | covered | Covers public behavior for `wrappedMapSingleStore`. |
| integration::ContextFlowIntegrationTest::parsedObjectReusableAcrossContexts | integration | Cross-View Invariants | covered | Covers public behavior for `parsedObjectReusableAcrossContexts`. |
| integration::ContextFlowIntegrationTest::expressionAndScriptAgreeOnFormulas | integration | Cross-View Invariants | covered | Covers public behavior for `expressionAndScriptAgreeOnFormulas`. |
| integration::ContextFlowIntegrationTest::scriptWritesFeedLaterExpressions | integration | Cross-View Invariants | covered | Covers public behavior for `scriptWritesFeedLaterExpressions`. |
| integration::ContextFlowIntegrationTest::parameterRunsAreIndependent | integration | Cross-View Invariants | covered | Covers public behavior for `parameterRunsAreIndependent`. |
| integration::ContextFlowIntegrationTest::introspectionPredictsStrictErrors | integration | Cross-View Invariants | covered | Covers public behavior for `introspectionPredictsStrictErrors`. |
| integration::ContextFlowIntegrationTest::parameterListMatchesBinding | integration | Cross-View Invariants | covered | Covers public behavior for `parameterListMatchesBinding`. |
| integration::ContextFlowIntegrationTest::compoundAssignmentAccumulatesInLoop | integration | Cross-View Invariants | covered | Covers public behavior for `compoundAssignmentAccumulatesInLoop`. |
| integration::DisciplineMatrixIntegrationTest::undefinedVariableAcrossDisciplines | integration | Cross-View Invariants | covered | Covers public behavior for `undefinedVariableAcrossDisciplines`. |
| integration::DisciplineMatrixIntegrationTest::divisionByZeroAcrossDisciplines | integration | Cross-View Invariants | covered | Covers public behavior for `divisionByZeroAcrossDisciplines`. |
| integration::DisciplineMatrixIntegrationTest::nullOperandAcrossDisciplines | integration | Cross-View Invariants | covered | Covers public behavior for `nullOperandAcrossDisciplines`. |
| integration::DisciplineMatrixIntegrationTest::nullConditionAcrossDisciplines | integration | Cross-View Invariants | covered | Covers public behavior for `nullConditionAcrossDisciplines`. |
| integration::DisciplineMatrixIntegrationTest::safeAxisFlipsNullNavigation | integration | Cross-View Invariants | covered | Covers public behavior for `safeAxisFlipsNullNavigation`. |
| integration::DisciplineMatrixIntegrationTest::silenceDoesNotCoverParsing | integration | Cross-View Invariants | covered | Covers public behavior for `silenceDoesNotCoverParsing`. |
| integration::DisciplineMatrixIntegrationTest::truthinessUniformForEmptyString | integration | Cross-View Invariants | covered | Covers public behavior for `truthinessUniformForEmptyString`. |
| integration::DisciplineMatrixIntegrationTest::truthinessUniformForZeroAndFalse | integration | Cross-View Invariants | covered | Covers public behavior for `truthinessUniformForZeroAndFalse`. |
| integration::DisciplineMatrixIntegrationTest::truthinessUniformForTruthyValues | integration | Cross-View Invariants | covered | Covers public behavior for `truthinessUniformForTruthyValues`. |
| integration::LanguageCompositionIntegrationTest::sizeAndEmptyAgree | integration | Cross-View Invariants | covered | Covers public behavior for `sizeAndEmptyAgree`. |
| integration::LanguageCompositionIntegrationTest::loopCountMatchesSize | integration | Cross-View Invariants | covered | Covers public behavior for `loopCountMatchesSize`. |
| integration::LanguageCompositionIntegrationTest::matchingDrivesControlFlow | integration | Cross-View Invariants | covered | Covers public behavior for `matchingDrivesControlFlow`. |
| integration::LanguageCompositionIntegrationTest::lambdaComposesWithLoop | integration | Cross-View Invariants | covered | Covers public behavior for `lambdaComposesWithLoop`. |
| integration::LanguageCompositionIntegrationTest::literalAndContextMapsNavigateAlike | integration | Cross-View Invariants | covered | Covers public behavior for `literalAndContextMapsNavigateAlike`. |
| integration::LanguageCompositionIntegrationTest::coercingEqualityWithContextValues | integration | Cross-View Invariants | covered | Covers public behavior for `coercingEqualityWithContextValues`. |
| integration::LanguageCompositionIntegrationTest::fallbackChainsOverContext | integration | Cross-View Invariants | covered | Covers public behavior for `fallbackChainsOverContext`. |
| integration::LanguageCompositionIntegrationTest::navigationConcatenationPipeline | integration | Cross-View Invariants | covered | Covers public behavior for `navigationConcatenationPipeline`. |
| integration::LanguageCompositionIntegrationTest::coercionAppliesUniformlyToContextValues | integration | Cross-View Invariants | covered | Covers public behavior for `coercionAppliesUniformlyToContextValues`. |
