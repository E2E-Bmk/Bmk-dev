# Spec-Test Map

oracle_version: 2026-07-20-native-v2
spec_version: v1
filter/oracle_source: upstream_rewritten
scorer_isolation: task-local native tests with the selected implementation first on PYTHONPATH

| test_nodeid | source | layer | spec_section | status | notes |
|---|---|---|---|---|---|
| oracle/test_simple.py::TestLiteral::runTest | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_simple_unit.py::TestLiteral::runTest |
| oracle/test_simple.py::TestCaselessLiteral::runTest | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_simple_unit.py::TestCaselessLiteral::runTest |
| oracle/test_simple.py::TestWord::runTest | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_simple_unit.py::TestWord::runTest |
| oracle/test_simple.py::TestCombine::runTest | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_simple_unit.py::TestCombine::runTest |
| oracle/test_simple.py::TestRepetition::runTest | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_simple_unit.py::TestRepetition::runTest |
| oracle/test_simple.py::TestResultsName::runTest | upstream_rewritten | integration | Public API - ParseResults | covered | source: tests/test_simple_unit.py::TestResultsName::runTest |
| oracle/test_simple.py::TestGroups::runTest | upstream_rewritten | integration | Public API - ParseResults | covered | source: tests/test_simple_unit.py::TestGroups::runTest |
| oracle/test_simple.py::TestParseAction::runTest | upstream_rewritten | integration | Public API - Helper Parse Actions | covered | source: tests/test_simple_unit.py::TestParseAction::runTest |
| oracle/test_simple.py::TestResultsModifyingParseAction::runTest | upstream_rewritten | integration | Public API - Helper Parse Actions | covered | source: tests/test_simple_unit.py::TestResultsModifyingParseAction::runTest |
| oracle/test_simple.py::TestRegex::runTest | upstream_rewritten | integration | Public API - Expression Construction | covered | source: tests/test_simple_unit.py::TestRegex::runTest |
| oracle/test_simple.py::TestParseCondition::runTest | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_simple_unit.py::TestParseCondition::runTest |
| oracle/test_simple.py::TestTransformStringUsingParseActions::runTest | upstream_rewritten | system_e2e | Public API - Helper Parse Actions | covered | source: tests/test_simple_unit.py::TestTransformStringUsingParseActions::runTest |
| oracle/test_simple.py::TestCommonHelperExpressions::runTest | upstream_rewritten | integration | Public API - Common Constants and Namespaces | covered | source: tests/test_simple_unit.py::TestCommonHelperExpressions::runTest |
| oracle/test_simple.py::TestWhitespaceMethods::runTest | upstream_rewritten | integration | Public API - Whitespace, Tabs, Comments, and Ignored Text | covered | source: tests/test_simple_unit.py::TestWhitespaceMethods::runTest |
| oracle/test_integration.py::Test02_WithoutPackrat::testAddCondition | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testAddCondition |
| oracle/test_integration.py::Test02_WithoutPackrat::testAtLineStart | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testAtLineStart |
| oracle/test_integration.py::Test02_WithoutPackrat::testCStyleCommentParser | upstream_rewritten | atomic | Public API - Whitespace, Tabs, Comments, and Ignored Text | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testCStyleCommentParser |
| oracle/test_integration.py::Test02_WithoutPackrat::testCaselessKeywordVsKeywordCaseless | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testCaselessKeywordVsKeywordCaseless |
| oracle/test_integration.py::Test02_WithoutPackrat::testCaselessOneOf | upstream_rewritten | atomic | Public API - Helper Constructors | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testCaselessOneOf |
| oracle/test_integration.py::Test02_WithoutPackrat::testChainedTernaryOperator | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testChainedTernaryOperator |
| oracle/test_integration.py::Test02_WithoutPackrat::testCharAsKeyword | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testCharAsKeyword |
| oracle/test_integration.py::Test02_WithoutPackrat::testCharsNotIn | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testCharsNotIn |
| oracle/test_integration.py::Test02_WithoutPackrat::testClearParseActions | upstream_rewritten | integration | Public API - Helper Parse Actions | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testClearParseActions |
| oracle/test_integration.py::Test02_WithoutPackrat::testCloseMatch | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testCloseMatch |
| oracle/test_integration.py::Test02_WithoutPackrat::testCloseMatchCaseless | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testCloseMatchCaseless |
| oracle/test_integration.py::Test02_WithoutPackrat::testCol | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testCol |
| oracle/test_integration.py::Test02_WithoutPackrat::testCombineWithResultsNames | upstream_rewritten | integration | Public API - ParseResults | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testCombineWithResultsNames |
| oracle/test_integration.py::Test02_WithoutPackrat::testCommonUrl | upstream_rewritten | integration | Public API - Common Constants and Namespaces | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testCommonUrl |
| oracle/test_integration.py::Test02_WithoutPackrat::testCommonUrlExprs | upstream_rewritten | integration | Public API - Common Constants and Namespaces | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testCommonUrlExprs |
| oracle/test_integration.py::Test02_WithoutPackrat::testCommonUrlParts | upstream_rewritten | integration | Public API - Common Constants and Namespaces | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testCommonUrlParts |
| oracle/test_integration.py::Test02_WithoutPackrat::testConvertToDateErr | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testConvertToDateErr |
| oracle/test_integration.py::Test02_WithoutPackrat::testConvertToDatetimeErr | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testConvertToDatetimeErr |
| oracle/test_integration.py::Test02_WithoutPackrat::testCountedArray | upstream_rewritten | atomic | Public API - Helper Constructors | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testCountedArray |
| oracle/test_integration.py::Test02_WithoutPackrat::testCountedArrayTest2 | upstream_rewritten | atomic | Public API - Helper Constructors | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testCountedArrayTest2 |
| oracle/test_integration.py::Test02_WithoutPackrat::testCountedArrayTest3 | upstream_rewritten | atomic | Public API - Helper Constructors | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testCountedArrayTest3 |
| oracle/test_integration.py::Test02_WithoutPackrat::testCountedArrayTest4 | upstream_rewritten | atomic | Public API - Helper Constructors | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testCountedArrayTest4 |
| oracle/test_integration.py::Test02_WithoutPackrat::testCuneiformTransformString | upstream_rewritten | system_e2e | Public API - ParserElement Lifecycle | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testCuneiformTransformString |
| oracle/test_integration.py::Test02_WithoutPackrat::testCustomQuotes | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testCustomQuotes |
| oracle/test_integration.py::Test02_WithoutPackrat::testCustomQuotes2 | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testCustomQuotes2 |
| oracle/test_integration.py::Test02_WithoutPackrat::testDateTimeValidation | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testDateTimeValidation |
| oracle/test_integration.py::Test02_WithoutPackrat::testDelimitedListMinMax | upstream_rewritten | integration | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testDelimitedListMinMax |
| oracle/test_integration.py::Test02_WithoutPackrat::testDelimitedListOfStrLiterals | upstream_rewritten | integration | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testDelimitedListOfStrLiterals |
| oracle/test_integration.py::Test02_WithoutPackrat::testDelimitedListParseActions1 | upstream_rewritten | integration | Public API - Helper Parse Actions | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testDelimitedListParseActions1 |
| oracle/test_integration.py::Test02_WithoutPackrat::testDelimitedListParseActions2 | upstream_rewritten | integration | Public API - Helper Parse Actions | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testDelimitedListParseActions2 |
| oracle/test_integration.py::Test02_WithoutPackrat::testDelimitedListParseActions3 | upstream_rewritten | integration | Public API - Helper Parse Actions | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testDelimitedListParseActions3 |
| oracle/test_integration.py::Test02_WithoutPackrat::testDoubleSlashCommentParser | upstream_rewritten | atomic | Public API - Whitespace, Tabs, Comments, and Ignored Text | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testDoubleSlashCommentParser |
| oracle/test_integration.py::Test02_WithoutPackrat::testEachWithMultipleMatch | upstream_rewritten | integration | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testEachWithMultipleMatch |
| oracle/test_integration.py::Test02_WithoutPackrat::testEachWithOptionalWithResultsName | upstream_rewritten | integration | Public API - ParseResults | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testEachWithOptionalWithResultsName |
| oracle/test_integration.py::Test02_WithoutPackrat::testEllipsisRepetition | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testEllipsisRepetition |
| oracle/test_integration.py::Test02_WithoutPackrat::testEllipsisRepetitionWithResultsNames | upstream_rewritten | integration | Public API - ParseResults | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testEllipsisRepetitionWithResultsNames |
| oracle/test_integration.py::Test02_WithoutPackrat::testEmptyDictDoesNotRaiseException | upstream_rewritten | integration | Public API - ParseResults | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testEmptyDictDoesNotRaiseException |
| oracle/test_integration.py::Test02_WithoutPackrat::testEmptyExpressionsAreHandledProperly | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testEmptyExpressionsAreHandledProperly |
| oracle/test_integration.py::Test02_WithoutPackrat::testExprSplitter | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testExprSplitter |
| oracle/test_integration.py::Test02_WithoutPackrat::testFollowedBy | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testFollowedBy |
| oracle/test_integration.py::Test02_WithoutPackrat::testGoToColumn | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testGoToColumn |
| oracle/test_integration.py::Test02_WithoutPackrat::testGreedyQuotedStrings | upstream_rewritten | integration | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testGreedyQuotedStrings |
| oracle/test_integration.py::Test02_WithoutPackrat::testHTMLEntities | upstream_rewritten | atomic | Public API - Common Constants and Namespaces | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testHTMLEntities |
| oracle/test_integration.py::Test02_WithoutPackrat::testHTMLStripper | upstream_rewritten | system_e2e | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testHTMLStripper |
| oracle/test_integration.py::Test02_WithoutPackrat::testHtmlCommentParser | upstream_rewritten | atomic | Public API - Whitespace, Tabs, Comments, and Ignored Text | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testHtmlCommentParser |
| oracle/test_integration.py::Test02_WithoutPackrat::testIgnoreString | upstream_rewritten | atomic | Public API - Whitespace, Tabs, Comments, and Ignored Text | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testIgnoreString |
| oracle/test_integration.py::Test02_WithoutPackrat::testIndentedBlock | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testIndentedBlock |
| oracle/test_integration.py::Test02_WithoutPackrat::testIndentedBlockClass | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testIndentedBlockClass |
| oracle/test_integration.py::Test02_WithoutPackrat::testIndentedBlockClass2 | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testIndentedBlockClass2 |
| oracle/test_integration.py::Test02_WithoutPackrat::testIndentedBlockClassWithRecursion | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testIndentedBlockClassWithRecursion |
| oracle/test_integration.py::Test02_WithoutPackrat::testIndentedBlockScan | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testIndentedBlockScan |
| oracle/test_integration.py::Test02_WithoutPackrat::testIndentedBlockTest2 | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testIndentedBlockTest2 |
| oracle/test_integration.py::Test02_WithoutPackrat::testInfixNotationBasicArithEval | upstream_rewritten | system_e2e | Public API - Helper Constructors | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testInfixNotationBasicArithEval |
| oracle/test_integration.py::Test02_WithoutPackrat::testInfixNotationEvalBoolExprUsingAstClasses | upstream_rewritten | system_e2e | Public API - Helper Constructors | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testInfixNotationEvalBoolExprUsingAstClasses |
| oracle/test_integration.py::Test02_WithoutPackrat::testInfixNotationExceptions | upstream_rewritten | system_e2e | Error Semantics | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testInfixNotationExceptions |
| oracle/test_integration.py::Test02_WithoutPackrat::testInfixNotationGrammarTest5 | upstream_rewritten | system_e2e | Public API - Helper Constructors | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testInfixNotationGrammarTest5 |
| oracle/test_integration.py::Test02_WithoutPackrat::testInfixNotationMinimalParseActionCalls | upstream_rewritten | system_e2e | Public API - Helper Constructors | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testInfixNotationMinimalParseActionCalls |
| oracle/test_integration.py::Test02_WithoutPackrat::testInfixNotationTernaryOperator | upstream_rewritten | system_e2e | Public API - Helper Constructors | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testInfixNotationTernaryOperator |
| oracle/test_integration.py::Test02_WithoutPackrat::testInfixNotationWithAlternateParenSymbols | upstream_rewritten | system_e2e | Public API - Helper Constructors | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testInfixNotationWithAlternateParenSymbols |
| oracle/test_integration.py::Test02_WithoutPackrat::testInfixNotationWithNonOperators | upstream_rewritten | system_e2e | Public API - Helper Constructors | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testInfixNotationWithNonOperators |
| oracle/test_integration.py::Test02_WithoutPackrat::testInfixNotationWithParseActions | upstream_rewritten | system_e2e | Public API - Helper Constructors | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testInfixNotationWithParseActions |
| oracle/test_integration.py::Test02_WithoutPackrat::testInvalidMinMaxArgs | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testInvalidMinMaxArgs |
| oracle/test_integration.py::Test02_WithoutPackrat::testLineAndStringEnd | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testLineAndStringEnd |
| oracle/test_integration.py::Test02_WithoutPackrat::testLineMethodSpecialCaseAtStart | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testLineMethodSpecialCaseAtStart |
| oracle/test_integration.py::Test02_WithoutPackrat::testLineStart | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testLineStart |
| oracle/test_integration.py::Test02_WithoutPackrat::testLineStart2 | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testLineStart2 |
| oracle/test_integration.py::Test02_WithoutPackrat::testLineStartWithLeadingSpaces | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testLineStartWithLeadingSpaces |
| oracle/test_integration.py::Test02_WithoutPackrat::testLiteralException | upstream_rewritten | atomic | Error Semantics | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testLiteralException |
| oracle/test_integration.py::Test02_WithoutPackrat::testLiteralVsKeyword | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testLiteralVsKeyword |
| oracle/test_integration.py::Test02_WithoutPackrat::testMakeXMLTags | upstream_rewritten | integration | Public API - Helper Constructors | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testMakeXMLTags |
| oracle/test_integration.py::Test02_WithoutPackrat::testMarkInputLine | upstream_rewritten | atomic | Error Semantics | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testMarkInputLine |
| oracle/test_integration.py::Test02_WithoutPackrat::testMatchFirstIteratesOverAllChoices | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testMatchFirstIteratesOverAllChoices |
| oracle/test_integration.py::Test02_WithoutPackrat::testMatchOnlyAtCol | upstream_rewritten | atomic | Public API - Helper Parse Actions | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testMatchOnlyAtCol |
| oracle/test_integration.py::Test02_WithoutPackrat::testMatchOnlyAtColErr | upstream_rewritten | atomic | Public API - Helper Parse Actions | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testMatchOnlyAtColErr |
| oracle/test_integration.py::Test02_WithoutPackrat::testMulWithEllipsis | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testMulWithEllipsis |
| oracle/test_integration.py::Test02_WithoutPackrat::testMulWithNegativeNumber | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testMulWithNegativeNumber |
| oracle/test_integration.py::Test02_WithoutPackrat::testNestedAsDict | upstream_rewritten | integration | Public API - ParseResults | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testNestedAsDict |
| oracle/test_integration.py::Test02_WithoutPackrat::testNestedExpressionRandom | upstream_rewritten | integration | Public API - Helper Constructors | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testNestedExpressionRandom |
| oracle/test_integration.py::Test02_WithoutPackrat::testNestedExpressions | upstream_rewritten | integration | Public API - Helper Constructors | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testNestedExpressions |
| oracle/test_integration.py::Test02_WithoutPackrat::testNestedExpressions2 | upstream_rewritten | integration | Public API - Helper Constructors | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testNestedExpressions2 |
| oracle/test_integration.py::Test02_WithoutPackrat::testNestedExpressions3 | upstream_rewritten | integration | Public API - Helper Constructors | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testNestedExpressions3 |
| oracle/test_integration.py::Test02_WithoutPackrat::testNestedExpressions4 | upstream_rewritten | integration | Public API - Helper Constructors | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testNestedExpressions4 |
| oracle/test_integration.py::Test02_WithoutPackrat::testOneOrMoreStop | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testOneOrMoreStop |
| oracle/test_integration.py::Test02_WithoutPackrat::testOnlyOnce | upstream_rewritten | atomic | Public API - Helper Parse Actions | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testOnlyOnce |
| oracle/test_integration.py::Test02_WithoutPackrat::testOptionalBeyondEndOfString | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testOptionalBeyondEndOfString |
| oracle/test_integration.py::Test02_WithoutPackrat::testOptionalEachTest1 | upstream_rewritten | integration | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testOptionalEachTest1 |
| oracle/test_integration.py::Test02_WithoutPackrat::testOptionalEachTest2 | upstream_rewritten | integration | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testOptionalEachTest2 |
| oracle/test_integration.py::Test02_WithoutPackrat::testOptionalEachTest3 | upstream_rewritten | integration | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testOptionalEachTest3 |
| oracle/test_integration.py::Test02_WithoutPackrat::testOptionalEachTest4 | upstream_rewritten | integration | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testOptionalEachTest4 |
| oracle/test_integration.py::Test02_WithoutPackrat::testOptionalWithResultsNameAndNoMatch | upstream_rewritten | integration | Public API - ParseResults | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testOptionalWithResultsNameAndNoMatch |
| oracle/test_integration.py::Test02_WithoutPackrat::testOriginalTextFor | upstream_rewritten | atomic | Public API - Helper Constructors | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testOriginalTextFor |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseActionIndexErrorException | upstream_rewritten | integration | Error Semantics | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseActionIndexErrorException |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseActionNesting | upstream_rewritten | integration | Public API - Helper Parse Actions | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseActionNesting |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseActionRunsInNotAny | upstream_rewritten | integration | Public API - Helper Parse Actions | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseActionRunsInNotAny |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseActionWithDelimitedList | upstream_rewritten | integration | Public API - Helper Parse Actions | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseActionWithDelimitedList |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseAll | upstream_rewritten | atomic | Public API - ParserElement Lifecycle | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseAll |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseCommaSeparatedValues | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseCommaSeparatedValues |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseExpressionResults | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseExpressionResults |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseExpressionResultsAccumulate | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseExpressionResultsAccumulate |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseFatalException | upstream_rewritten | atomic | Error Semantics | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseFatalException |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseFatalException2 | upstream_rewritten | atomic | Error Semantics | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseFatalException2 |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseFatalException3 | upstream_rewritten | atomic | Error Semantics | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseFatalException3 |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseFile | upstream_rewritten | atomic | Public API - ParserElement Lifecycle | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseFile |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseHTMLTags | upstream_rewritten | system_e2e | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseHTMLTags |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseKeyword | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseKeyword |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseResultsAcceptingACollectionTypeValue | upstream_rewritten | integration | Public API - ParseResults | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseResultsAcceptingACollectionTypeValue |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseResultsAddingSuppressedTokenWithResultsName | upstream_rewritten | integration | Public API - ParseResults | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseResultsAddingSuppressedTokenWithResultsName |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseResultsAppend | upstream_rewritten | integration | Public API - ParseResults | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseResultsAppend |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseResultsArithmeticContract | upstream_rewritten | integration | Public API - ParseResults | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseResultsArithmeticContract |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseResultsBool | upstream_rewritten | integration | Public API - ParseResults | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseResultsBool |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseResultsClear | upstream_rewritten | integration | Public API - ParseResults | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseResultsClear |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseResultsCopy | upstream_rewritten | integration | Public API - ParseResults | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseResultsCopy |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseResultsDeepcopy | upstream_rewritten | integration | Public API - ParseResults | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseResultsDeepcopy |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseResultsDeepcopy2 | upstream_rewritten | integration | Public API - ParseResults | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseResultsDeepcopy2 |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseResultsDeepcopy3 | upstream_rewritten | integration | Public API - ParseResults | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseResultsDeepcopy3 |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseResultsDel | upstream_rewritten | integration | Public API - ParseResults | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseResultsDel |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseResultsExtendWithParseResults | upstream_rewritten | integration | Public API - ParseResults | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseResultsExtendWithParseResults |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseResultsExtendWithString | upstream_rewritten | integration | Public API - ParseResults | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseResultsExtendWithString |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseResultsFromDict | upstream_rewritten | integration | Public API - ParseResults | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseResultsFromDict |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseResultsInsert | upstream_rewritten | integration | Public API - ParseResults | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseResultsInsert |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseResultsInsertWithResultsNames | upstream_rewritten | integration | Public API - ParseResults | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseResultsInsertWithResultsNames |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseResultsNameBelowUngroupedName | upstream_rewritten | integration | Public API - ParseResults | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseResultsNameBelowUngroupedName |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseResultsNamedResultWithEmptyString | upstream_rewritten | integration | Public API - ParseResults | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseResultsNamedResultWithEmptyString |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseResultsNamesInGroupWithDict | upstream_rewritten | integration | Public API - ParseResults | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseResultsNamesInGroupWithDict |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseResultsNewEdgeCases | upstream_rewritten | integration | Public API - ParseResults | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseResultsNewEdgeCases |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseResultsReversed | upstream_rewritten | integration | Public API - ParseResults | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseResultsReversed |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseResultsStringListUsingCombine | upstream_rewritten | integration | Public API - ParseResults | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseResultsStringListUsingCombine |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseResultsValues | upstream_rewritten | integration | Public API - ParseResults | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseResultsValues |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseResultsWithAsListWithAndWithoutFlattening | upstream_rewritten | integration | Public API - ParseResults | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseResultsWithAsListWithAndWithoutFlattening |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseResultsWithNamedTuple | upstream_rewritten | integration | Public API - ParseResults | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseResultsWithNamedTuple |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseResultsWithNestedNames | upstream_rewritten | integration | Public API - ParseResults | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseResultsWithNestedNames |
| oracle/test_integration.py::Test02_WithoutPackrat::testParseUsingRegex | upstream_rewritten | integration | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParseUsingRegex |
| oracle/test_integration.py::Test02_WithoutPackrat::testParserElementAddOperatorWithOtherTypes | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParserElementAddOperatorWithOtherTypes |
| oracle/test_integration.py::Test02_WithoutPackrat::testParserElementEachOperatorWithOtherTypes | upstream_rewritten | integration | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParserElementEachOperatorWithOtherTypes |
| oracle/test_integration.py::Test02_WithoutPackrat::testParserElementMatchFirstOperatorWithOtherTypes | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParserElementMatchFirstOperatorWithOtherTypes |
| oracle/test_integration.py::Test02_WithoutPackrat::testParserElementMatchLongestWithOtherTypes | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParserElementMatchLongestWithOtherTypes |
| oracle/test_integration.py::Test02_WithoutPackrat::testParserElementMulByZero | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParserElementMulByZero |
| oracle/test_integration.py::Test02_WithoutPackrat::testParserElementMulOperatorWithOtherTypes | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParserElementMulOperatorWithOtherTypes |
| oracle/test_integration.py::Test02_WithoutPackrat::testParserElementMulOperatorWithTuples | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParserElementMulOperatorWithTuples |
| oracle/test_integration.py::Test02_WithoutPackrat::testParserElementPassedStrToMultiplierShorthand | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParserElementPassedStrToMultiplierShorthand |
| oracle/test_integration.py::Test02_WithoutPackrat::testParserElementPassedThreeArgsToMultiplierShorthand | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParserElementPassedThreeArgsToMultiplierShorthand |
| oracle/test_integration.py::Test02_WithoutPackrat::testParserElementSubOperatorWithOtherTypes | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testParserElementSubOperatorWithOtherTypes |
| oracle/test_integration.py::Test02_WithoutPackrat::testPatientOr | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testPatientOr |
| oracle/test_integration.py::Test02_WithoutPackrat::testPop | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testPop |
| oracle/test_integration.py::Test02_WithoutPackrat::testPopKwargsErr | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testPopKwargsErr |
| oracle/test_integration.py::Test02_WithoutPackrat::testPrecededBy | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testPrecededBy |
| oracle/test_integration.py::Test02_WithoutPackrat::testPythonQuotedStrings | upstream_rewritten | integration | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testPythonQuotedStrings |
| oracle/test_integration.py::Test02_WithoutPackrat::testQuotedStringEscapedExtendedChars | upstream_rewritten | integration | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testQuotedStringEscapedExtendedChars |
| oracle/test_integration.py::Test02_WithoutPackrat::testQuotedStringEscapedQuotes | upstream_rewritten | integration | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testQuotedStringEscapedQuotes |
| oracle/test_integration.py::Test02_WithoutPackrat::testQuotedStringLoc | upstream_rewritten | integration | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testQuotedStringLoc |
| oracle/test_integration.py::Test02_WithoutPackrat::testQuotedStringUnquotesAndConvertWhitespaceEscapes | upstream_rewritten | integration | Public API - Whitespace, Tabs, Comments, and Ignored Text | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testQuotedStringUnquotesAndConvertWhitespaceEscapes |
| oracle/test_integration.py::Test02_WithoutPackrat::testQuotedStrings | upstream_rewritten | integration | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testQuotedStrings |
| oracle/test_integration.py::Test02_WithoutPackrat::testReStringRange | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testReStringRange |
| oracle/test_integration.py::Test02_WithoutPackrat::testRecursiveCombine | upstream_rewritten | system_e2e | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testRecursiveCombine |
| oracle/test_integration.py::Test02_WithoutPackrat::testRegexAsType | upstream_rewritten | integration | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testRegexAsType |
| oracle/test_integration.py::Test02_WithoutPackrat::testRegexInvalidType | upstream_rewritten | integration | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testRegexInvalidType |
| oracle/test_integration.py::Test02_WithoutPackrat::testRegexLoopPastEndOfString | upstream_rewritten | integration | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testRegexLoopPastEndOfString |
| oracle/test_integration.py::Test02_WithoutPackrat::testRepeater | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testRepeater |
| oracle/test_integration.py::Test02_WithoutPackrat::testRepeater2 | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testRepeater2 |
| oracle/test_integration.py::Test02_WithoutPackrat::testRepeater3 | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testRepeater3 |
| oracle/test_integration.py::Test02_WithoutPackrat::testRepeater4 | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testRepeater4 |
| oracle/test_integration.py::Test02_WithoutPackrat::testRepeater5 | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testRepeater5 |
| oracle/test_integration.py::Test02_WithoutPackrat::testRepeaterPreservesParseAction | upstream_rewritten | integration | Public API - Helper Parse Actions | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testRepeaterPreservesParseAction |
| oracle/test_integration.py::Test02_WithoutPackrat::testRepeaterRecursiveFalse | upstream_rewritten | system_e2e | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testRepeaterRecursiveFalse |
| oracle/test_integration.py::Test02_WithoutPackrat::testRepeaterRecursiveWhitespace | upstream_rewritten | system_e2e | Public API - Whitespace, Tabs, Comments, and Ignored Text | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testRepeaterRecursiveWhitespace |
| oracle/test_integration.py::Test02_WithoutPackrat::testRequiredEach | upstream_rewritten | integration | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testRequiredEach |
| oracle/test_integration.py::Test02_WithoutPackrat::testRunTests | upstream_rewritten | integration | Public API - ParserElement Lifecycle | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testRunTests |
| oracle/test_integration.py::Test02_WithoutPackrat::testRunTestsPostParse | upstream_rewritten | integration | Public API - ParserElement Lifecycle | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testRunTestsPostParse |
| oracle/test_integration.py::Test02_WithoutPackrat::testScanString | upstream_rewritten | atomic | Public API - ParserElement Lifecycle | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testScanString |
| oracle/test_integration.py::Test02_WithoutPackrat::testScanStringWithOverlap | upstream_rewritten | atomic | Public API - ParserElement Lifecycle | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testScanStringWithOverlap |
| oracle/test_integration.py::Test02_WithoutPackrat::testSetParseActionUncallableErr | upstream_rewritten | integration | Public API - Helper Parse Actions | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testSetParseActionUncallableErr |
| oracle/test_integration.py::Test02_WithoutPackrat::testSetResultsNameWithOneOrMoreAndZeroOrMore | upstream_rewritten | integration | Public API - ParseResults | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testSetResultsNameWithOneOrMoreAndZeroOrMore |
| oracle/test_integration.py::Test02_WithoutPackrat::testSingleArgException | upstream_rewritten | atomic | Error Semantics | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testSingleArgException |
| oracle/test_integration.py::Test02_WithoutPackrat::testSkipToIgnoreExpr2 | upstream_rewritten | atomic | Public API - Whitespace, Tabs, Comments, and Ignored Text | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testSkipToIgnoreExpr2 |
| oracle/test_integration.py::Test02_WithoutPackrat::testSkipToParserTests | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testSkipToParserTests |
| oracle/test_integration.py::Test02_WithoutPackrat::testSkipToPreParseIgnoreExprs | upstream_rewritten | atomic | Public API - Whitespace, Tabs, Comments, and Ignored Text | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testSkipToPreParseIgnoreExprs |
| oracle/test_integration.py::Test02_WithoutPackrat::testStringStart | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testStringStart |
| oracle/test_integration.py::Test02_WithoutPackrat::testStringStartAndLineStartInsideAnd | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testStringStartAndLineStartInsideAnd |
| oracle/test_integration.py::Test02_WithoutPackrat::testSumParseResults | upstream_rewritten | integration | Public API - ParseResults | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testSumParseResults |
| oracle/test_integration.py::Test02_WithoutPackrat::testTagElements | upstream_rewritten | integration | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testTagElements |
| oracle/test_integration.py::Test02_WithoutPackrat::testTokenMap | upstream_rewritten | atomic | Public API - Helper Parse Actions | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testTokenMap |
| oracle/test_integration.py::Test02_WithoutPackrat::testTraceParseActionDecorator | upstream_rewritten | integration | Public API - Helper Parse Actions | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testTraceParseActionDecorator |
| oracle/test_integration.py::Test02_WithoutPackrat::testTransformString | upstream_rewritten | system_e2e | Public API - ParserElement Lifecycle | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testTransformString |
| oracle/test_integration.py::Test02_WithoutPackrat::testTransformStringWithExpectedLeadingWhitespace | upstream_rewritten | system_e2e | Public API - Whitespace, Tabs, Comments, and Ignored Text | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testTransformStringWithExpectedLeadingWhitespace |
| oracle/test_integration.py::Test02_WithoutPackrat::testTransformStringWithLeadingNotAny | upstream_rewritten | system_e2e | Public API - ParserElement Lifecycle | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testTransformStringWithLeadingNotAny |
| oracle/test_integration.py::Test02_WithoutPackrat::testTransformStringWithLeadingWhitespace | upstream_rewritten | system_e2e | Public API - Whitespace, Tabs, Comments, and Ignored Text | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testTransformStringWithLeadingWhitespace |
| oracle/test_integration.py::Test02_WithoutPackrat::testTransformStringWithLeadingWhitespaceFromTranslateProject | upstream_rewritten | system_e2e | Public API - Whitespace, Tabs, Comments, and Ignored Text | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testTransformStringWithLeadingWhitespaceFromTranslateProject |
| oracle/test_integration.py::Test02_WithoutPackrat::testUnicodeSetNameEquivalence | upstream_rewritten | integration | Public API - Common Constants and Namespaces | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testUnicodeSetNameEquivalence |
| oracle/test_integration.py::Test02_WithoutPackrat::testUnicodeTests | upstream_rewritten | integration | Public API - Common Constants and Namespaces | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testUnicodeTests |
| oracle/test_integration.py::Test02_WithoutPackrat::testUnicodeTests2 | upstream_rewritten | integration | Public API - Common Constants and Namespaces | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testUnicodeTests2 |
| oracle/test_integration.py::Test02_WithoutPackrat::testUpcaseDowncaseUnicode | upstream_rewritten | integration | Public API - Common Constants and Namespaces | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testUpcaseDowncaseUnicode |
| oracle/test_integration.py::Test02_WithoutPackrat::testWithAttributeParseAction | upstream_rewritten | integration | Public API - Helper Constructors | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testWithAttributeParseAction |
| oracle/test_integration.py::Test02_WithoutPackrat::testWordBoundaryExpressions | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testWordBoundaryExpressions |
| oracle/test_integration.py::Test02_WithoutPackrat::testWordBoundaryExpressions2 | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testWordBoundaryExpressions2 |
| oracle/test_integration.py::Test02_WithoutPackrat::testWordCopyWhenWordCharsIncludeSpace | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testWordCopyWhenWordCharsIncludeSpace |
| oracle/test_integration.py::Test02_WithoutPackrat::testWordCopyWhenWordCharsIncludeSpace2 | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testWordCopyWhenWordCharsIncludeSpace2 |
| oracle/test_integration.py::Test02_WithoutPackrat::testWordCopyWhenWordCharsIncludeSpace3 | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testWordCopyWhenWordCharsIncludeSpace3 |
| oracle/test_integration.py::Test02_WithoutPackrat::testWordExact | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testWordExact |
| oracle/test_integration.py::Test02_WithoutPackrat::testWordExclude | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testWordExclude |
| oracle/test_integration.py::Test02_WithoutPackrat::testWordExclude2 | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testWordExclude2 |
| oracle/test_integration.py::Test02_WithoutPackrat::testWordMaxGreaterThanZeroAndAsKeyword1 | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testWordMaxGreaterThanZeroAndAsKeyword1 |
| oracle/test_integration.py::Test02_WithoutPackrat::testWordMaxGreaterThanZeroAndAsKeyword2 | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testWordMaxGreaterThanZeroAndAsKeyword2 |
| oracle/test_integration.py::Test02_WithoutPackrat::testWordMin | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testWordMin |
| oracle/test_integration.py::Test02_WithoutPackrat::testWordMinMaxArgs | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testWordMinMaxArgs |
| oracle/test_integration.py::Test02_WithoutPackrat::testWordMinMaxExactArgs | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testWordMinMaxExactArgs |
| oracle/test_integration.py::Test02_WithoutPackrat::testWordWithIdentChars | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testWordWithIdentChars |
| oracle/test_integration.py::Test02_WithoutPackrat::testZeroOrMoreStop | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testZeroOrMoreStop |
| oracle/test_integration.py::Test11_LR1_Recursion::test_add_sub | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test11_LR1_Recursion::test_add_sub |
| oracle/test_integration.py::Test11_LR1_Recursion::test_binary_associative | upstream_rewritten | system_e2e | Public API - Expression Construction | covered | source: tests/test_unit.py::Test11_LR1_Recursion::test_binary_associative |
| oracle/test_integration.py::Test11_LR1_Recursion::test_binary_recursive | upstream_rewritten | system_e2e | Public API - Expression Construction | covered | source: tests/test_unit.py::Test11_LR1_Recursion::test_binary_recursive |
| oracle/test_integration.py::Test11_LR1_Recursion::test_math | upstream_rewritten | system_e2e | Public API - Expression Construction | covered | source: tests/test_unit.py::Test11_LR1_Recursion::test_math |
| oracle/test_integration.py::Test11_LR1_Recursion::test_non_peg | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test11_LR1_Recursion::test_non_peg |
| oracle/test_integration.py::Test11_LR1_Recursion::test_repeat_as_recurse | upstream_rewritten | system_e2e | Public API - Expression Construction | covered | source: tests/test_unit.py::Test11_LR1_Recursion::test_repeat_as_recurse |
| oracle/test_integration.py::Test11_LR1_Recursion::test_terminate_empty | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_unit.py::Test11_LR1_Recursion::test_terminate_empty |
| oracle/test_integration.py::TestShowBestPractices::test_cli_invocation_with_module_flag | upstream_rewritten | atomic | Installable Surface | covered | source: tests/test_unit.py::TestShowBestPractices::test_cli_invocation_with_module_flag |
| oracle/test_integration.py::TestShowBestPractices::test_fallback_when_file_missing | upstream_rewritten | atomic | Installable Surface | covered | source: tests/test_unit.py::TestShowBestPractices::test_fallback_when_file_missing |
| oracle/test_integration.py::TestShowBestPractices::test_loads_markdown_file | upstream_rewritten | atomic | Installable Surface | covered | source: tests/test_unit.py::TestShowBestPractices::test_loads_markdown_file |
| oracle/test_atomic.py::test_col[First column, no newline-0-abcdef-1] | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_util.py::test_col[First column, no newline-0-abcdef-1] |
| oracle/test_atomic.py::test_col[Second column, no newline-1-abcdef-2] | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_util.py::test_col[Second column, no newline-1-abcdef-2] |
| oracle/test_atomic.py::test_col[First column after newline-4-abc
def-1] | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_util.py::test_col[First column after newline-4-abc
def-1] |
| oracle/test_atomic.py::test_col[Second column after newline-5-abc
def-2] | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_util.py::test_col[Second column after newline-5-abc
def-2] |
| oracle/test_atomic.py::test_col[Column after multiple newlines-9-abc
def
ghi-2] | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_util.py::test_col[Column after multiple newlines-9-abc
def
ghi-2] |
| oracle/test_atomic.py::test_col[Location at start of string-0-abcdef-1] | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_util.py::test_col[Location at start of string-0-abcdef-1] |
| oracle/test_atomic.py::test_col[Location at end of string-5-abcdef-6] | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_util.py::test_col[Location at end of string-5-abcdef-6] |
| oracle/test_atomic.py::test_col[Column after newline at end-3-abc
-4] | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_util.py::test_col[Column after newline at end-3-abc
-4] |
| oracle/test_atomic.py::test_col[Tab character in the string-4-a\tbcd\tef-5] | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_util.py::test_col[Tab character in the string-4-a\tbcd\tef-5] |
| oracle/test_atomic.py::test_col[Multiple lines with tab-8-a\tb
c\td-5] | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_util.py::test_col[Multiple lines with tab-8-a\tb
c\td-5] |
| oracle/test_atomic.py::test_line[Single line, no newlines-0-abcdef-abcdef] | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_util.py::test_line[Single line, no newlines-0-abcdef-abcdef] |
| oracle/test_atomic.py::test_line[First line in multi-line string-2-abc
def-abc] | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_util.py::test_line[First line in multi-line string-2-abc
def-abc] |
| oracle/test_atomic.py::test_line[Second line in multi-line string-5-abc
def-def] | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_util.py::test_line[Second line in multi-line string-5-abc
def-def] |
| oracle/test_atomic.py::test_line[Location at start of second line-4-abc
def-def] | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_util.py::test_line[Location at start of second line-4-abc
def-def] |
| oracle/test_atomic.py::test_line[Empty string-0--] | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_util.py::test_line[Empty string-0--] |
| oracle/test_atomic.py::test_line[Location at newline character-3-abc
def-abc] | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_util.py::test_line[Location at newline character-3-abc
def-abc] |
| oracle/test_atomic.py::test_line[Last line without trailing newline-7-abc
def
ghi-def] | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_util.py::test_line[Last line without trailing newline-7-abc
def
ghi-def] |
| oracle/test_atomic.py::test_line[Single line with newline at end-2-abc
-abc] | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_util.py::test_line[Single line with newline at end-2-abc
-abc] |
| oracle/test_atomic.py::test_line[Multi-line with multiple newlines-6-line1
line2
line3-line2] | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_util.py::test_line[Multi-line with multiple newlines-6-line1
line2
line3-line2] |
| oracle/test_atomic.py::test_line[Multi-line with trailing newline-11-line1
line2
line3
-line2] | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_util.py::test_line[Multi-line with trailing newline-11-line1
line2
line3
-line2] |
| oracle/test_atomic.py::test_lineno[Single line, no newlines-0-abcdef-1] | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_util.py::test_lineno[Single line, no newlines-0-abcdef-1] |
| oracle/test_atomic.py::test_lineno[First line in multi-line string-2-abc
def-1] | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_util.py::test_lineno[First line in multi-line string-2-abc
def-1] |
| oracle/test_atomic.py::test_lineno[Second line in multi-line string-5-abc
def-2] | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_util.py::test_lineno[Second line in multi-line string-5-abc
def-2] |
| oracle/test_atomic.py::test_lineno[Location at start of second line-4-abc
def-2] | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_util.py::test_lineno[Location at start of second line-4-abc
def-2] |
| oracle/test_atomic.py::test_lineno[Multiple newlines, third line-10-abc
def
ghi-3] | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_util.py::test_lineno[Multiple newlines, third line-10-abc
def
ghi-3] |
| oracle/test_atomic.py::test_lineno[Empty string-0--1] | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_util.py::test_lineno[Empty string-0--1] |
| oracle/test_atomic.py::test_lineno[Location at newline character-3-abc
def-1] | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_util.py::test_lineno[Location at newline character-3-abc
def-1] |
| oracle/test_atomic.py::test_lineno[Last line without trailing newline-7-abc
def
ghi-2] | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_util.py::test_lineno[Last line without trailing newline-7-abc
def
ghi-2] |
| oracle/test_atomic.py::test_lineno[Single line with newline at end-4-abc
-2] | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_util.py::test_lineno[Single line with newline at end-4-abc
-2] |
| oracle/test_atomic.py::test_lineno[Multi-line with trailing newline-12-line1
line2
line3
-3] | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_util.py::test_lineno[Multi-line with trailing newline-12-line1
line2
line3
-3] |
| oracle/test_atomic.py::test_lineno[Location in middle of a tabbed string-7-a\tb
c\td-2] | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_util.py::test_lineno[Location in middle of a tabbed string-7-a\tb
c\td-2] |
| oracle/test_atomic.py::test_html_entities | upstream_rewritten | atomic | Public API - Expression Construction | covered | source: tests/test_util.py::test_html_entities |

Historical total before Diagrams repair: 298 | kept: 298 | spec_gap: 0 | source-only: 0 | excluded: 0 | scoreable: 298
| oracle/test_integration.py::Test02_WithoutPackrat::testDiagramToRailroadPreservesNamedGrammarAndResultsName | task_local_generated | integration | Diagrams | covered | source: task-local/generated-diagrams::testDiagramToRailroadPreservesNamedGrammarAndResultsName |
| oracle/test_integration.py::Test02_WithoutPackrat::testDiagramRailroadToHtmlSupportsDocumentAndEmbedModes | task_local_generated | integration | Diagrams | covered | source: task-local/generated-diagrams::testDiagramRailroadToHtmlSupportsDocumentAndEmbedModes |
| oracle/test_integration.py::Test02_WithoutPackrat::testCreateDiagramWritesCompleteOrEmbeddedHtml | task_local_generated | integration | Diagrams | covered | source: task-local/generated-diagrams::testCreateDiagramWritesCompleteOrEmbeddedHtml |
| oracle/test_integration.py::Test02_WithoutPackrat::testLocatedExprLeadingWhitespace | upstream_rewritten | integration | Whitespace, Tabs, Comments, and Ignored Text | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testLocatedExprLeadingWhitespace |
| oracle/test_integration.py::Test02_WithoutPackrat::testLocatedExprUsingLocated | upstream_rewritten | integration | Expression Construction | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testLocatedExprUsingLocated |
| oracle/test_integration.py::Test02_WithoutPackrat::testOneOfKeywords | upstream_rewritten | atomic | Helper Constructors | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testOneOfKeywords |
| oracle/test_integration.py::Test02_WithoutPackrat::testOneOfWithEmptyList | upstream_rewritten | atomic | Helper Constructors | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testOneOfWithEmptyList |
| oracle/test_integration.py::Test02_WithoutPackrat::testOneOfWithUnexpectedInput | upstream_rewritten | atomic | Helper Constructors | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testOneOfWithUnexpectedInput |
| oracle/test_integration.py::Test02_WithoutPackrat::testUpdateDefaultWhitespace2 | upstream_rewritten | integration | Whitespace, Tabs, Comments, and Ignored Text | covered | source: tests/test_unit.py::Test02_WithoutPackrat::testUpdateDefaultWhitespace2 |

Total: 272 | upstream_rewritten: 269 | generated: 3 | excluded_for_private_or_format_contract: 29 | final_scoreable: 272
