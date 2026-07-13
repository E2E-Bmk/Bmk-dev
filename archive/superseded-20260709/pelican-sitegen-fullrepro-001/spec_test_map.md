# Spec Test Map

oracle_source: upstream
spec: spec/spec_v3.md
merge_note: v3 keeps the same 156 upstream nodeids after updating public compatibility import surface, neutralizing non-scoreable test-package bootstrap, and excluding the private settings helper nodeid from the carrier.

| test_nodeid | source | layer | spec_section | status | notes |
|-------------|--------|-------|--------------|--------|-------|
| pelican/tests/test_cli.py::TestParseOverrides::test_flags | upstream | atomic | section Public API | covered |  |
| pelican/tests/test_cli.py::TestParseOverrides::test_parse_invalid_json | upstream | atomic | section Public API | covered |  |
| pelican/tests/test_cli.py::TestParseOverrides::test_parse_invalid_syntax | upstream | atomic | section Public API | covered |  |
| pelican/tests/test_cli.py::TestParseOverrides::test_parse_multiple_items | upstream | atomic | section Public API | covered |  |
| pelican/tests/test_cli.py::TestParseOverrides::test_parse_valid_json | upstream | atomic | section Public API | covered |  |
| pelican/tests/test_cli.py::TestGetConfigFromArgs::test_overrides_known_keys | upstream | atomic | section Public API | covered |  |
| pelican/tests/test_cli.py::TestGetConfigFromArgs::test_overrides_non_default_type | upstream | atomic | section Public API | covered |  |
| pelican/tests/test_contents.py::TestPage::test_defaultlang | upstream | atomic | section Content and Metadata Behavior | covered |  |
| pelican/tests/test_contents.py::TestPage::test_get_content | upstream | atomic | section Content and Metadata Behavior | covered |  |
| pelican/tests/test_contents.py::TestPage::test_intrasite_link | upstream | atomic | section Links, Static Files, and Attachments | covered |  |
| pelican/tests/test_contents.py::TestPage::test_intrasite_link_absolute | upstream | atomic | section Links, Static Files, and Attachments | covered |  |
| pelican/tests/test_contents.py::TestPage::test_intrasite_link_escape | upstream | atomic | section Links, Static Files, and Attachments | covered |  |
| pelican/tests/test_contents.py::TestPage::test_intrasite_link_markdown_spaces | upstream | atomic | section Links, Static Files, and Attachments | covered |  |
| pelican/tests/test_contents.py::TestPage::test_intrasite_link_more | upstream | atomic | section Links, Static Files, and Attachments | covered |  |
| pelican/tests/test_contents.py::TestPage::test_intrasite_link_source_and_generated | upstream | atomic | section Links, Static Files, and Attachments | covered |  |
| pelican/tests/test_contents.py::TestPage::test_intrasite_link_to_static_content_with_filename | upstream | atomic | section Links, Static Files, and Attachments | covered |  |
| pelican/tests/test_contents.py::TestPage::test_mandatory_properties | upstream | atomic | section Content and Metadata Behavior | covered |  |
| pelican/tests/test_contents.py::TestPage::test_metadata_url_format | upstream | atomic | section Content and Metadata Behavior | covered |  |
| pelican/tests/test_contents.py::TestPage::test_multiple_authors | upstream | atomic | section Content and Metadata Behavior | covered |  |
| pelican/tests/test_contents.py::TestPage::test_relative_source_path | upstream | atomic | section Content and Metadata Behavior | covered |  |
| pelican/tests/test_contents.py::TestPage::test_save_as | upstream | atomic | section URL, Output, and Feed Rules | covered |  |
| pelican/tests/test_contents.py::TestPage::test_signal | upstream | atomic | section Plugins and Signals | covered |  |
| pelican/tests/test_contents.py::TestPage::test_slug | upstream | atomic | section Content and Metadata Behavior | covered |  |
| pelican/tests/test_contents.py::TestPage::test_summary_end_suffix | upstream | atomic | section Content and Metadata Behavior | covered |  |
| pelican/tests/test_contents.py::TestPage::test_summary_from_metadata | upstream | atomic | section Content and Metadata Behavior | covered |  |
| pelican/tests/test_contents.py::TestPage::test_summary_max_length | upstream | atomic | section Content and Metadata Behavior | covered |  |
| pelican/tests/test_contents.py::TestPage::test_summary_paragraph | upstream | atomic | section Content and Metadata Behavior | covered |  |
| pelican/tests/test_contents.py::TestPage::test_summary_paragraph_long_max_length | upstream | atomic | section Content and Metadata Behavior | covered |  |
| pelican/tests/test_contents.py::TestPage::test_summary_paragraph_max_length | upstream | atomic | section Content and Metadata Behavior | covered |  |
| pelican/tests/test_contents.py::TestPage::test_summary_strips_toc_elements | upstream | atomic | section Content and Metadata Behavior | covered |  |
| pelican/tests/test_contents.py::TestPage::test_template | upstream | atomic | section Themes and Templates | covered |  |
| pelican/tests/test_contents.py::TestPage::test_use_args | upstream | atomic | section Content and Metadata Behavior | covered |  |
| pelican/tests/test_contents.py::TestArticle::test_slugify_category_author | upstream | atomic | section URL, Output, and Feed Rules | covered |  |
| pelican/tests/test_contents.py::TestArticle::test_slugify_category_with_dots | upstream | atomic | section URL, Output, and Feed Rules | covered |  |
| pelican/tests/test_contents.py::TestArticle::test_slugify_with_author_substitutions | upstream | atomic | section URL, Output, and Feed Rules | covered |  |
| pelican/tests/test_contents.py::TestArticle::test_template | upstream | atomic | section Content and Metadata Behavior | covered |  |
| pelican/tests/test_contents.py::TestArticle::test_valid_save_as_detects_breakout | upstream | atomic | section Content and Metadata Behavior | covered |  |
| pelican/tests/test_contents.py::TestArticle::test_valid_save_as_detects_breakout_to_root | upstream | atomic | section Content and Metadata Behavior | covered |  |
| pelican/tests/test_contents.py::TestArticle::test_valid_save_as_passes_valid | upstream | atomic | section Content and Metadata Behavior | covered |  |
| pelican/tests/test_contents.py::TestStatic::test_attach_link_syntax | upstream | atomic | section Links, Static Files, and Attachments | covered |  |
| pelican/tests/test_contents.py::TestStatic::test_attach_to_does_not_override_an_override | upstream | atomic | section Links, Static Files, and Attachments | covered |  |
| pelican/tests/test_contents.py::TestStatic::test_attach_to_does_nothing_after_save_as_referenced | upstream | atomic | section Links, Static Files, and Attachments | covered |  |
| pelican/tests/test_contents.py::TestStatic::test_attach_to_does_nothing_after_url_referenced | upstream | atomic | section Links, Static Files, and Attachments | covered |  |
| pelican/tests/test_contents.py::TestStatic::test_attach_to_ignores_subsequent_calls | upstream | atomic | section Links, Static Files, and Attachments | covered |  |
| pelican/tests/test_contents.py::TestStatic::test_attach_to_other_dir | upstream | atomic | section Links, Static Files, and Attachments | covered |  |
| pelican/tests/test_contents.py::TestStatic::test_attach_to_parent_dir | upstream | atomic | section Links, Static Files, and Attachments | covered |  |
| pelican/tests/test_contents.py::TestStatic::test_attach_to_same_dir | upstream | atomic | section Links, Static Files, and Attachments | covered |  |
| pelican/tests/test_contents.py::TestStatic::test_author_link_syntax | upstream | atomic | section Links, Static Files, and Attachments | covered |  |
| pelican/tests/test_contents.py::TestStatic::test_category_link_syntax | upstream | atomic | section Links, Static Files, and Attachments | covered |  |
| pelican/tests/test_contents.py::TestStatic::test_index_link_syntax | upstream | atomic | section Links, Static Files, and Attachments | covered |  |
| pelican/tests/test_contents.py::TestStatic::test_index_link_syntax_with_spaces | upstream | atomic | section Links, Static Files, and Attachments | covered |  |
| pelican/tests/test_contents.py::TestStatic::test_link_to_unknown_file | upstream | atomic | section Links, Static Files, and Attachments | covered |  |
| pelican/tests/test_contents.py::TestStatic::test_not_save_as_draft | upstream | atomic | section Links, Static Files, and Attachments | covered |  |
| pelican/tests/test_contents.py::TestStatic::test_tag_link_syntax | upstream | atomic | section Links, Static Files, and Attachments | covered |  |
| pelican/tests/test_contents.py::TestStatic::test_unknown_link_syntax | upstream | atomic | section Links, Static Files, and Attachments | covered |  |
| pelican/tests/test_generators.py::TestArticlesGenerator::test_articles_draft | upstream | integration | section Content and Metadata Behavior | covered |  |
| pelican/tests/test_generators.py::TestArticlesGenerator::test_articles_hidden | upstream | integration | section Content and Metadata Behavior | covered |  |
| pelican/tests/test_generators.py::TestArticlesGenerator::test_direct_templates_save_as_false | upstream | integration | section Themes and Templates | covered |  |
| pelican/tests/test_generators.py::TestArticlesGenerator::test_direct_templates_save_as_url_default | upstream | integration | section Themes and Templates | covered |  |
| pelican/tests/test_generators.py::TestArticlesGenerator::test_direct_templates_save_as_url_modified | upstream | integration | section Themes and Templates | covered |  |
| pelican/tests/test_generators.py::TestArticlesGenerator::test_do_not_use_folder_as_category | upstream | integration | section Content and Metadata Behavior | covered |  |
| pelican/tests/test_generators.py::TestArticlesGenerator::test_generate_feeds | upstream | integration | section URL, Output, and Feed Rules | covered |  |
| pelican/tests/test_generators.py::TestArticlesGenerator::test_generate_feeds_override_url | upstream | integration | section URL, Output, and Feed Rules | covered |  |
| pelican/tests/test_generators.py::TestPageGenerator::test_generate_sorted | upstream | integration | section Content and Metadata Behavior | covered |  |
| pelican/tests/test_generators.py::TestPageGenerator::test_static_and_attach_links_on_generated_pages | upstream | integration | section Links, Static Files, and Attachments | covered |  |
| pelican/tests/test_generators.py::TestPageGenerator::test_tag_and_category_links_on_generated_pages | upstream | integration | section Links, Static Files, and Attachments | covered |  |
| pelican/tests/test_generators.py::TestTemplatePagesGenerator::test_generate_output | upstream | system_e2e | section Themes and Templates | covered |  |
| pelican/tests/test_generators.py::TestStaticGenerator::test_copy_one_file | upstream | system_e2e | section Links, Static Files, and Attachments | covered |  |
| pelican/tests/test_generators.py::TestStaticGenerator::test_static_exclude_sources | upstream | system_e2e | section Links, Static Files, and Attachments | covered |  |
| pelican/tests/test_generators.py::TestStaticGenerator::test_static_excludes | upstream | system_e2e | section Links, Static Files, and Attachments | covered |  |
| pelican/tests/test_generators.py::TestStaticGenerator::test_static_links | upstream | system_e2e | section Links, Static Files, and Attachments | covered |  |
| pelican/tests/test_generators.py::TestStaticGenerator::test_theme_static_paths_dirs | upstream | system_e2e | section Themes and Templates | covered |  |
| pelican/tests/test_generators.py::TestStaticGenerator::test_theme_static_paths_files | upstream | system_e2e | section Themes and Templates | covered |  |
| pelican/tests/test_generators.py::TestJinja2Environment::test_jinja2_extension | upstream | integration | section Themes and Templates | covered |  |
| pelican/tests/test_generators.py::TestJinja2Environment::test_jinja2_filter | upstream | integration | section Themes and Templates | covered |  |
| pelican/tests/test_generators.py::TestJinja2Environment::test_jinja2_filter_plugin_enabled | upstream | integration | section Themes and Templates | covered |  |
| pelican/tests/test_generators.py::TestJinja2Environment::test_jinja2_global | upstream | integration | section Themes and Templates | covered |  |
| pelican/tests/test_generators.py::TestJinja2Environment::test_jinja2_test | upstream | integration | section Themes and Templates | covered |  |
| pelican/tests/test_importer.py::TestBuildHeader::test_build_header | upstream | integration | section Command-Line Workflows | covered |  |
| pelican/tests/test_importer.py::TestBuildHeader::test_build_header_with_east_asian_characters | upstream | integration | section Command-Line Workflows | covered |  |
| pelican/tests/test_importer.py::TestBuildHeader::test_build_header_with_fields | upstream | integration | section Command-Line Workflows | covered |  |
| pelican/tests/test_importer.py::TestMediumImporter::test_medium_slug | upstream | integration | section Command-Line Workflows | covered |  |
| pelican/tests/test_paginator.py::TestPage::test_custom_pagination_pattern | upstream | atomic | section Writers and Pagination | covered |  |
| pelican/tests/test_paginator.py::TestPage::test_custom_pagination_pattern_last_page | upstream | atomic | section Writers and Pagination | covered |  |
| pelican/tests/test_paginator.py::TestPage::test_save_as_preservation | upstream | atomic | section Writers and Pagination | covered |  |
| pelican/tests/test_pelican.py::TestPelican::test_cyclic_intersite_links_no_warnings | upstream | integration | section Public API | covered |  |
| pelican/tests/test_pelican.py::TestPelican::test_main_help | upstream | integration | section Command-Line Workflows | covered |  |
| pelican/tests/test_pelican.py::TestPelican::test_main_on_content_markdown_disabled | upstream | system_e2e | section Command-Line Workflows | covered |  |
| pelican/tests/test_pelican.py::TestPelican::test_main_version | upstream | integration | section Command-Line Workflows | covered |  |
| pelican/tests/test_pelican.py::TestPelican::test_md_extensions_deprecation | upstream | integration | section Public API | covered |  |
| pelican/tests/test_pelican.py::TestPelican::test_module_load | upstream | integration | section Installable Surface | covered |  |
| pelican/tests/test_pelican.py::TestPelican::test_parse_errors | upstream | integration | section Error Semantics | covered |  |
| pelican/tests/test_pelican.py::TestPelican::test_theme_static_paths_copy | upstream | integration | section Themes and Templates | covered |  |
| pelican/tests/test_pelican.py::TestPelican::test_theme_static_paths_copy_single_file | upstream | integration | section Themes and Templates | covered |  |
| pelican/tests/test_readers.py::ReaderTest::test_markdown_disabled | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::DefaultReaderTest::test_markdown_disabled | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::DefaultReaderTest::test_readfile_path_metadata_explicit_date_implicit_modified | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::DefaultReaderTest::test_readfile_path_metadata_explicit_dates | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::DefaultReaderTest::test_readfile_path_metadata_implicit_date_explicit_modified | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::DefaultReaderTest::test_readfile_path_metadata_implicit_dates | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::DefaultReaderTest::test_readfile_unknown_extension | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::RstReaderTest::test_article_extra_path_metadata | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::RstReaderTest::test_article_extra_path_metadata_dont_overwrite | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::RstReaderTest::test_article_extra_path_metadata_recurse | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::RstReaderTest::test_article_metadata_key_lowercase | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::RstReaderTest::test_article_with_capitalized_metadata | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::RstReaderTest::test_article_with_filename_metadata | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::RstReaderTest::test_article_with_metadata | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::RstReaderTest::test_article_with_multiple_authors | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::RstReaderTest::test_article_with_multiple_authors_list | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::RstReaderTest::test_article_with_multiple_authors_semicolon | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::RstReaderTest::test_article_with_optional_filename_metadata | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::RstReaderTest::test_default_date_formats | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::RstReaderTest::test_markdown_disabled | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::RstReaderTest::test_parse_error | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::MdReaderTest::test_article_with_file_extensions | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::MdReaderTest::test_article_with_filename_metadata | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::MdReaderTest::test_article_with_footnote | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::MdReaderTest::test_article_with_markdown_markup_extension | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::MdReaderTest::test_article_with_metadata | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::MdReaderTest::test_article_with_optional_filename_metadata | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::MdReaderTest::test_duplicate_tags_or_authors_are_removed | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::MdReaderTest::test_empty_file | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::MdReaderTest::test_empty_file_with_bom | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::MdReaderTest::test_markdown_disabled | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::MdReaderTest::test_metadata_has_no_discarded_data | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::MdReaderTest::test_metadata_not_parsed_for_metadata | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::HTMLReaderTest::test_article_metadata_key_lowercase | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::HTMLReaderTest::test_article_with_attributes_containing_double_quotes | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::HTMLReaderTest::test_article_with_comments | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::HTMLReaderTest::test_article_with_inline_svg | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::HTMLReaderTest::test_article_with_keywords | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::HTMLReaderTest::test_article_with_metadata | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::HTMLReaderTest::test_article_with_metadata_and_contents_attrib | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::HTMLReaderTest::test_article_with_multiple_authors | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::HTMLReaderTest::test_article_with_multiple_similar_metadata_tags | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::HTMLReaderTest::test_article_with_nonconformant_meta_tags | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::HTMLReaderTest::test_article_with_null_attributes | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_readers.py::HTMLReaderTest::test_markdown_disabled | upstream | atomic | section Readers | covered |  |
| pelican/tests/test_settings.py::TestSettingsConfiguration::test_configure_settings | upstream | atomic | section Settings | covered |  |
| pelican/tests/test_settings.py::TestSettingsConfiguration::test_default_encoding | upstream | atomic | section Settings | covered |  |
| pelican/tests/test_settings.py::TestSettingsConfiguration::test_defaults_not_overwritten | upstream | atomic | section Settings | covered |  |
| pelican/tests/test_settings.py::TestSettingsConfiguration::test_feeds_warning_with_feed_domain | upstream | atomic | section Settings | covered |  |
| pelican/tests/test_settings.py::TestSettingsConfiguration::test_feeds_warning_with_siteurl | upstream | atomic | section Settings | covered |  |
| pelican/tests/test_settings.py::TestSettingsConfiguration::test_feeds_warning_without_siteurl_or_feed_domain | upstream | atomic | section Settings | covered |  |
| pelican/tests/test_settings.py::TestSettingsConfiguration::test_invalid_settings_throw_exception | upstream | atomic | section Settings | covered |  |
| pelican/tests/test_settings.py::TestSettingsConfiguration::test_keep_default_settings | upstream | atomic | section Settings | covered |  |
| pelican/tests/test_settings.py::TestSettingsConfiguration::test_overwrite_existing_settings | upstream | atomic | section Settings | covered |  |
| pelican/tests/test_settings.py::TestSettingsConfiguration::test_read_empty_settings | upstream | atomic | section Settings | covered |  |
| pelican/tests/test_settings.py::TestSettingsConfiguration::test_settings_return_independent | upstream | atomic | section Settings | covered |  |
| pelican/tests/test_settings.py::TestSettingsConfiguration::test_theme_and_extra_templates_exception | upstream | atomic | section Settings | covered |  |
| pelican/tests/test_settings.py::TestSettingsConfiguration::test_theme_settings_exceptions | upstream | atomic | section Settings | covered |  |
| pelican/tests/test_urlwrappers.py::TestURLWrapper::test_author_slug_substitutions | upstream | atomic | section Content Objects | covered |  |
| pelican/tests/test_urlwrappers.py::TestURLWrapper::test_equality | upstream | atomic | section Content Objects | covered |  |
| pelican/tests/test_urlwrappers.py::TestURLWrapper::test_ordering | upstream | atomic | section Content Objects | covered |  |
| pelican/tests/test_urlwrappers.py::TestURLWrapper::test_slugify_with_substitutions_and_dots | upstream | atomic | section Content Objects | covered |  |

Total: 156 | kept (covered): 156 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 156 | spec_version: v3

Total: 156 | kept (covered): 156 | spec_gap: 0 | source-only: 0 | excluded: 0 | final_scoreable: 156
