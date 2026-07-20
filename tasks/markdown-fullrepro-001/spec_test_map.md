# Spec-Test Map

oracle_version: 2026-07-20-native-v1
spec_version: v1
filter/oracle_source: upstream_rewritten
scorer_isolation: task-local native tests with the selected implementation first on PYTHONPATH

| test_nodeid | source | layer | spec_section | status | notes |
|---|---|---|---|---|---|
| oracle/test_atomic.py::TestMarkdownBasics::testBlankInput | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_apis.py::TestMarkdownBasics::testBlankInput |
| oracle/test_atomic.py::TestMarkdownBasics::testDotNotationExtension | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_apis.py::TestMarkdownBasics::testDotNotationExtension |
| oracle/test_atomic.py::TestMarkdownBasics::testDotNotationExtensionWithClass | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_apis.py::TestMarkdownBasics::testDotNotationExtensionWithClass |
| oracle/test_atomic.py::TestMarkdownBasics::testEntryPointExtension | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_apis.py::TestMarkdownBasics::testEntryPointExtension |
| oracle/test_atomic.py::TestMarkdownBasics::testInstanceExtension | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_apis.py::TestMarkdownBasics::testInstanceExtension |
| oracle/test_atomic.py::TestMarkdownBasics::testSimpleInput | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_apis.py::TestMarkdownBasics::testSimpleInput |
| oracle/test_atomic.py::TestMarkdownBasics::testWhitespaceOnly | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_apis.py::TestMarkdownBasics::testWhitespaceOnly |
| oracle/test_atomic.py::TestConvertFile::testFileNames | upstream_rewritten | integration | Cross-View Invariants + Representative Workflow | covered | source: tests/test_apis.py::TestConvertFile::testFileNames |
| oracle/test_atomic.py::TestConvertFile::testFileObjects | upstream_rewritten | integration | Cross-View Invariants + Representative Workflow | covered | source: tests/test_apis.py::TestConvertFile::testFileObjects |
| oracle/test_atomic.py::TestConvertFile::testStdinStdout | upstream_rewritten | integration | Cross-View Invariants + Representative Workflow | covered | source: tests/test_apis.py::TestConvertFile::testStdinStdout |
| oracle/test_atomic.py::TestBlockParser::testParseChunk | upstream_rewritten | integration | Cross-View Invariants | covered | source: tests/test_apis.py::TestBlockParser::testParseChunk |
| oracle/test_atomic.py::TestBlockParser::testParseDocument | upstream_rewritten | integration | Cross-View Invariants | covered | source: tests/test_apis.py::TestBlockParser::testParseDocument |
| oracle/test_atomic.py::TestBlockParserState::testBlankState | upstream_rewritten | integration | Cross-View Invariants | covered | source: tests/test_apis.py::TestBlockParserState::testBlankState |
| oracle/test_atomic.py::TestBlockParserState::testIsSate | upstream_rewritten | integration | Cross-View Invariants | covered | source: tests/test_apis.py::TestBlockParserState::testIsSate |
| oracle/test_atomic.py::TestBlockParserState::testReset | upstream_rewritten | integration | Cross-View Invariants | covered | source: tests/test_apis.py::TestBlockParserState::testReset |
| oracle/test_atomic.py::TestBlockParserState::testSetSate | upstream_rewritten | integration | Cross-View Invariants | covered | source: tests/test_apis.py::TestBlockParserState::testSetSate |
| oracle/test_atomic.py::TestHtmlStash::testReset | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_apis.py::TestHtmlStash::testReset |
| oracle/test_atomic.py::TestHtmlStash::testSimpleStore | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_apis.py::TestHtmlStash::testSimpleStore |
| oracle/test_atomic.py::TestHtmlStash::testStoreMore | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_apis.py::TestHtmlStash::testStoreMore |
| oracle/test_atomic.py::RegistryTests::testCreateRegistry | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_apis.py::RegistryTests::testCreateRegistry |
| oracle/test_atomic.py::RegistryTests::testDeregister | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_apis.py::RegistryTests::testDeregister |
| oracle/test_atomic.py::RegistryTests::testGetIndexForName | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_apis.py::RegistryTests::testGetIndexForName |
| oracle/test_atomic.py::RegistryTests::testIsSorted | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_apis.py::RegistryTests::testIsSorted |
| oracle/test_atomic.py::RegistryTests::testRegisterDupplicate | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_apis.py::RegistryTests::testRegisterDupplicate |
| oracle/test_atomic.py::RegistryTests::testRegisterWithoutPriority | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_apis.py::RegistryTests::testRegisterWithoutPriority |
| oracle/test_atomic.py::RegistryTests::testRegistryContains | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_apis.py::RegistryTests::testRegistryContains |
| oracle/test_atomic.py::RegistryTests::testRegistryDelItem | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_apis.py::RegistryTests::testRegistryDelItem |
| oracle/test_atomic.py::RegistryTests::testRegistryGetItemByIndex | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_apis.py::RegistryTests::testRegistryGetItemByIndex |
| oracle/test_atomic.py::RegistryTests::testRegistryGetItemByItem | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_apis.py::RegistryTests::testRegistryGetItemByItem |
| oracle/test_atomic.py::RegistryTests::testRegistryIter | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_apis.py::RegistryTests::testRegistryIter |
| oracle/test_integration.py::TestExtensionClass::testConfigAsKwargsOnInit | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_extensions.py::TestExtensionClass::testConfigAsKwargsOnInit |
| oracle/test_integration.py::TestExtensionClass::testGetConfig | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_extensions.py::TestExtensionClass::testGetConfig |
| oracle/test_integration.py::TestExtensionClass::testGetConfigDefault | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_extensions.py::TestExtensionClass::testGetConfigDefault |
| oracle/test_integration.py::TestExtensionClass::testGetConfigInfo | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_extensions.py::TestExtensionClass::testGetConfigInfo |
| oracle/test_integration.py::TestExtensionClass::testGetConfigs | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_extensions.py::TestExtensionClass::testGetConfigs |
| oracle/test_integration.py::TestExtensionClass::testSetConfig | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_extensions.py::TestExtensionClass::testSetConfig |
| oracle/test_integration.py::TestExtensionClass::testSetConfigWithBadKey | upstream_rewritten | atomic | Error Semantics | covered | source: tests/test_extensions.py::TestExtensionClass::testSetConfigWithBadKey |
| oracle/test_integration.py::TestMetaData::testBasicMetaData | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_extensions.py::TestMetaData::testBasicMetaData |
| oracle/test_integration.py::TestMetaData::testMetaDataReset | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_extensions.py::TestMetaData::testMetaDataReset |
| oracle/test_integration.py::TestMetaData::testMetaDataWithoutNewline | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_extensions.py::TestMetaData::testMetaDataWithoutNewline |
| oracle/test_integration.py::TestMetaData::testMissingMetaData | upstream_rewritten | atomic | Error Semantics | covered | source: tests/test_extensions.py::TestMetaData::testMissingMetaData |
| oracle/test_integration.py::TestMetaData::testYamlMetaData | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_extensions.py::TestMetaData::testYamlMetaData |
| oracle/test_integration.py::TestWikiLinks::testBasicWikilinks | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_extensions.py::TestWikiLinks::testBasicWikilinks |
| oracle/test_integration.py::TestWikiLinks::testComplexSettings | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_extensions.py::TestWikiLinks::testComplexSettings |
| oracle/test_integration.py::TestWikiLinks::testSimpleSettings | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_extensions.py::TestWikiLinks::testSimpleSettings |
| oracle/test_integration.py::TestWikiLinks::testURLCallback | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_extensions.py::TestWikiLinks::testURLCallback |
| oracle/test_integration.py::TestWikiLinks::testWikilinkWhitespace | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_extensions.py::TestWikiLinks::testWikilinkWhitespace |
| oracle/test_integration.py::TestWikiLinks::testWikilinksMetaData | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_extensions.py::TestWikiLinks::testWikilinksMetaData |
| oracle/test_integration.py::TestAdmonition::testRE | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_extensions.py::TestAdmonition::testRE |
| oracle/test_integration.py::TestSmarty::testCustomSubstitutions | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_extensions.py::TestSmarty::testCustomSubstitutions |
| oracle/test_legacy.py::TestBasic::test_amps_and_angle_encoding | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_legacy.py::TestBasic::test_amps_and_angle_encoding |
| oracle/test_legacy.py::TestBasic::test_angle_links_and_img | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_legacy.py::TestBasic::test_angle_links_and_img |
| oracle/test_legacy.py::TestBasic::test_auto_links | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_legacy.py::TestBasic::test_auto_links |
| oracle/test_legacy.py::TestBasic::test_backlash_escapes | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_legacy.py::TestBasic::test_backlash_escapes |
| oracle/test_legacy.py::TestBasic::test_blockquotes_with_code_blocks | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_legacy.py::TestBasic::test_blockquotes_with_code_blocks |
| oracle/test_legacy.py::TestBasic::test_codeblock_in_list | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_legacy.py::TestBasic::test_codeblock_in_list |
| oracle/test_legacy.py::TestBasic::test_hard_wrapped | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_legacy.py::TestBasic::test_hard_wrapped |
| oracle/test_legacy.py::TestBasic::test_horizontal_rules | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_legacy.py::TestBasic::test_horizontal_rules |
| oracle/test_legacy.py::TestBasic::test_links_inline | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_legacy.py::TestBasic::test_links_inline |
| oracle/test_legacy.py::TestBasic::test_links_reference | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_legacy.py::TestBasic::test_links_reference |
| oracle/test_legacy.py::TestBasic::test_literal_quotes | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_legacy.py::TestBasic::test_literal_quotes |
| oracle/test_legacy.py::TestBasic::test_markdown_documentation_basics | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_legacy.py::TestBasic::test_markdown_documentation_basics |
| oracle/test_legacy.py::TestBasic::test_markdown_syntax | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_legacy.py::TestBasic::test_markdown_syntax |
| oracle/test_legacy.py::TestBasic::test_nested_blockquotes | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_legacy.py::TestBasic::test_nested_blockquotes |
| oracle/test_legacy.py::TestBasic::test_ordered_and_unordered_list | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_legacy.py::TestBasic::test_ordered_and_unordered_list |
| oracle/test_legacy.py::TestBasic::test_strong_and_em_together | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_legacy.py::TestBasic::test_strong_and_em_together |
| oracle/test_legacy.py::TestBasic::test_tabs | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_legacy.py::TestBasic::test_tabs |
| oracle/test_legacy.py::TestBasic::test_tidyness | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_legacy.py::TestBasic::test_tidyness |
| oracle/test_legacy.py::TestMisc::test_CRLF_line_ends | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_legacy.py::TestMisc::test_CRLF_line_ends |
| oracle/test_legacy.py::TestMisc::test_adjacent_headers | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_legacy.py::TestMisc::test_adjacent_headers |
| oracle/test_legacy.py::TestMisc::test_arabic | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_legacy.py::TestMisc::test_arabic |
| oracle/test_legacy.py::TestMisc::test_autolinks_with_asterisks | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_legacy.py::TestMisc::test_autolinks_with_asterisks |
| oracle/test_legacy.py::TestMisc::test_autolinks_with_asterisks_russian | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_legacy.py::TestMisc::test_autolinks_with_asterisks_russian |
| oracle/test_legacy.py::TestMisc::test_backtick_escape | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_legacy.py::TestMisc::test_backtick_escape |
| oracle/test_legacy.py::TestMisc::test_bidi | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_legacy.py::TestMisc::test_bidi |
| oracle/test_legacy.py::TestMisc::test_blank_block_quote | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_legacy.py::TestMisc::test_blank_block_quote |
| oracle/test_legacy.py::TestMisc::test_blank_lines_in_codeblocks | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_legacy.py::TestMisc::test_blank_lines_in_codeblocks |
| oracle/test_legacy.py::TestMisc::test_blockquote | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_legacy.py::TestMisc::test_blockquote |
| oracle/test_legacy.py::TestMisc::test_blockquote_below_paragraph | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_legacy.py::TestMisc::test_blockquote_below_paragraph |
| oracle/test_legacy.py::TestMisc::test_blockquote_hr | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_legacy.py::TestMisc::test_blockquote_hr |
| oracle/test_meta.py::TestVersion::test__version__IsValid | upstream_rewritten | atomic | Installable Surface | covered | source: tests/test_meta.py::TestVersion::test__version__IsValid |
| oracle/test_meta.py::TestVersion::test_get_version | upstream_rewritten | atomic | Installable Surface | covered | source: tests/test_meta.py::TestVersion::test_get_version |
| oracle/test_blockquotes.py::TestBlockquoteBlocks::test_nesting_limit | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_syntax/blocks/test_blockquotes.py::TestBlockquoteBlocks::test_nesting_limit |
| oracle/test_code_blocks.py::TestCodeBlocks::test_codeblock_escape | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_syntax/blocks/test_code_blocks.py::TestCodeBlocks::test_codeblock_escape |
| oracle/test_code_blocks.py::TestCodeBlocks::test_codeblock_second_line | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_syntax/blocks/test_code_blocks.py::TestCodeBlocks::test_codeblock_second_line |
| oracle/test_code_blocks.py::TestCodeBlocks::test_codeblock_with_blankline | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_syntax/blocks/test_code_blocks.py::TestCodeBlocks::test_codeblock_with_blankline |
| oracle/test_code_blocks.py::TestCodeBlocks::test_multiline_codeblock | upstream_rewritten | atomic | Cross-View Invariants | covered | source: tests/test_syntax/blocks/test_code_blocks.py::TestCodeBlocks::test_multiline_codeblock |
| oracle/test_code_blocks.py::TestCodeBlocks::test_spaced_codeblock | upstream_rewritten | atomic | Cross-View Invariants + Public API Behavior | covered | source: tests/test_syntax/blocks/test_code_blocks.py::TestCodeBlocks::test_spaced_codeblock |
| oracle/test_code_blocks.py::TestCodeBlocks::test_tabbed_codeblock | upstream_rewritten | atomic | Cross-View Invariants + Public API Behavior | covered | source: tests/test_syntax/blocks/test_code_blocks.py::TestCodeBlocks::test_tabbed_codeblock |
| oracle/test_headers.py::TestSetextHeaders::test_p_followed_by_setext_h1 | upstream_rewritten | atomic | Cross-View Invariants + Public API Behavior + Error Semantics | covered | source: tests/test_syntax/blocks/test_headers.py::TestSetextHeaders::test_p_followed_by_setext_h1 |

Total: 90 | kept: 90 | spec_gap: 0 | source-only: 0 | excluded: 0 | final_scoreable: 90
