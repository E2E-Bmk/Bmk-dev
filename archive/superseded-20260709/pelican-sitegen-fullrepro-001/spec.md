# Pelican Specification

## Product Overview

Pelican is a static site generator for sites whose source of truth is a directory of content files, settings, templates, static assets, and optional cache data. It reads Markdown, reStructuredText, and HTML content, combines that content with project settings and themes, and writes a static output tree containing HTML pages, index pages, archives, author/category/tag pages, feeds, copied assets, and optional source files.

Pelican can be used from the `pelican` command, from `python -m pelican`, and from Python code. The command-line tools `pelican-quickstart`, `pelican-import`, `pelican-themes`, and `pelican-plugins` are installable public commands.

## Scope

This specification covers:

- Building a site from a content directory, settings file, command-line overrides, and a theme.
- Reading article and page metadata from reStructuredText, Markdown, HTML, filenames, paths, and default settings.
- Generating articles, pages, indexes, archives, author/category/tag pages, feeds, static files, attached files, and direct template pages.
- Public settings loading and normalization through `read_settings`.
- Public data objects visible to templates and plugins: articles, pages, statics, authors, categories, tags, pagination pages, and writers/readers.
- Plugin registration through public signal hooks and plugin settings.
- Project skeleton creation, import conversion, theme management, and plugin listing at their command-level contracts.

## Installable Surface

Public package imports include:

```python
from pelican import Pelican, main, parse_arguments, get_config, get_instance
from pelican import read_settings, signals
from pelican.contents import Article, Page, Static, Content, SkipStub
from pelican.readers import BaseReader, Readers, RstReader, MarkdownReader, HTMLReader
from pelican.settings import read_settings, configure_settings, get_settings_from_file
from pelican.writers import Writer, FileOverwriteFailedError
from pelican.urlwrappers import Author, Category, Tag
from pelican.paginator import Paginator
```

Installable commands:

```text
pelican [path] [options]
python -m pelican [path] [options]
pelican-quickstart [options]
pelican-import [options] input
pelican-themes [options]
pelican-plugins
```

The main `pelican` command accepts a content path, `--settings/-s`, `--output/-o`, `--theme-path/-t`, `--delete-output-directory/-d`, verbosity flags, `--version`, `--autoreload/-r`, `--print-settings`, `--relative-urls`, `--cache-path`, `--ignore-cache`, `--fatal errors|warnings`, `--log-handler plain|rich`, `--logs-dedup-min-level`, `--listen/-l`, `--port/-p`, `--bind/-b`, and `--extra-settings/-e` overrides.

## Public API

### Settings

`read_settings(path=None, override=None)` returns a settings dictionary. If `path` is `None`, defaults are used unless the caller or CLI finds a `pelicanconf.py` in the current working directory. Settings from a file are merged with defaults, then explicit overrides win over both. Path-like settings are normalized relative to the settings file where the documented behavior calls for relative resolution.

`--extra-settings` accepts `KEY=VALUE` pairs where `VALUE` is JSON notation. Strings must therefore be JSON strings, booleans use `true` or `false`, and null uses `null`. Invalid pairs or invalid JSON values raise a value error before site generation proceeds.

Important settings include `PATH`, `OUTPUT_PATH`, `THEME`, `SITENAME`, `SITEURL`, `ARTICLE_PATHS`, `PAGE_PATHS`, `STATIC_PATHS`, `DELETE_OUTPUT_DIRECTORY`, `OUTPUT_RETENTION`, `CACHE_CONTENT`, `LOAD_CONTENT_CACHE`, `CACHE_PATH`, `CHECK_MODIFIED_METHOD`, `RELATIVE_URLS`, URL/save-as patterns, feed settings, pagination settings, template settings, plugin settings, and metadata extraction settings.

`get_config(args)` converts parsed CLI arguments into setting overrides. `get_instance(args)` loads settings, resolves `PELICAN_CLASS` when it is a dotted string, constructs the Pelican object, and returns `(pelican_instance, settings)`.

### Site Generation

`Pelican(settings).run()` reads content, builds context, runs generators, writes output, and prints a summary of processed articles, drafts, hidden articles, pages, hidden pages, and draft pages. If `DELETE_OUTPUT_DIRECTORY` is enabled, Pelican deletes the output directory before writing unless that directory is a parent of the input content path; `OUTPUT_RETENTION` names files that survive deletion.

Articles are chronological content. Pages are non-chronological content. Static files are copied without content processing when they are selected by `STATIC_PATHS`, linked with `{static}`, or attached with `{attach}`.

### Content Objects

Article and page objects expose template-visible attributes such as title, content, metadata, date, modified date, slug, author, authors, category, tags, status, source path, relative source path, URL, save path, summary, and translations. String conversion of article and page objects represents the source path.

`Author`, `Category`, and `Tag` wrap a display name and a slug. They are comparable and usable in generated collections, and `as_dict()` returns their public data for template and plugin use.

`Static` represents a static source file and exposes source, destination, URL, and save path behavior. When attached to an article or page, its output location follows the linking content's output directory.

### Readers

`Readers(settings)` chooses an enabled reader from file extension and reads content through `read_file(...)`. Built-in readers cover reStructuredText, Markdown when the Markdown dependency is available, and HTML. Reader results are content strings plus processed metadata.

`BaseReader.process_metadata(name, value)` converts documented metadata fields into Pelican objects or typed values. Author and tag lists may be comma-separated or semicolon-separated. Metadata embedded in a content file takes precedence over filename or path metadata.

`default_metadata`, `path_metadata`, and `parse_path_metadata` expose the same metadata extraction rules used by site generation. Unknown or disabled reader formats fail as an unsupported content type rather than being silently treated as plain text.

### Writers and Pagination

`Writer(output_path, settings=None)` writes rendered files and feeds under the output path. If two content items attempt to write incompatible content to the same output file, `FileOverwriteFailedError` is raised.

`Paginator` divides ordered object lists into pages. Public page objects expose whether next/previous pages exist, next and previous page numbers, and one-based start/end indexes for the current page.

## Content and Metadata Behavior

reStructuredText content may use document title syntax and field-list metadata. Markdown content uses `Key: Value` metadata at the top of the file. HTML content reads the `<title>` and `<meta name="...">` entries, with the body as content. HTML `keywords` and Pelican `tags` metadata are interchangeable for tags.

Reserved metadata keys include `title`, `date`, `modified`, `tags`, `keywords`, `category`, `slug`, `author`, `authors`, `summary`, `lang`, `translation`, `status`, `template`, `save_as`, and `url`. Custom metadata keys are preserved and exposed to templates unless they conflict with reserved keys.

The only required content metadata is the title. Dates may come from metadata, filename/path extraction, default settings, or the file mtime when `DEFAULT_DATE` is `fs`. If `modified` is absent it defaults to `date`. If category metadata is absent and `USE_FOLDER_AS_CATEGORY` is enabled, Pelican derives the category from the containing folder. If slug metadata is absent, Pelican derives a slug according to the configured slug source and substitutions.

Status controls publication:

- `published` content is output normally and included in indexes and feeds.
- `draft` articles and pages are written under draft locations and excluded from normal indexes and feeds.
- `hidden` content is written to its normal save path but excluded from indexes, menus, and feeds.
- `skip` content is not output.

## Links, Static Files, and Attachments

Pelican recognizes internal link prefixes in content:

- `{filename}path` links to another source content file and resolves to that file's generated URL.
- `{static}path` links to a static file and causes that file to be copied if needed.
- `{attach}path` links to a static file and relocates the static output under the linking article or page's output directory.
- `{author}name`, `{category}name`, `{tag}name`, and `{index}` link to generated collection pages.

Forward slashes are the path separator for link directives on all platforms. Deprecated vertical-bar forms remain accepted for compatibility. When the same static file is attached by multiple documents, the first processed attachment determines the relocation; later uses behave like static links.

## URL, Output, and Feed Rules

URL and save-as settings use format fields from content metadata and date fields. Common settings include `ARTICLE_URL`, `ARTICLE_SAVE_AS`, language variants, draft variants, `PAGE_URL`, `PAGE_SAVE_AS`, author/category/tag pages, archives, and index pages. `RELATIVE_URLS` makes generated links document-relative for local development.

`PATH_METADATA` and `FILENAME_METADATA` extract named regex groups from a source path or filename. `EXTRA_PATH_METADATA` assigns metadata by relative source path and can override output locations for individual files. Metadata embedded in the content file takes precedence over filename and path extraction.

Feed settings control Atom and RSS output for all posts, categories, authors, tags, and translations. When a feed save path is `None`, that feed is not generated. If a feed URL is not separately configured, the save path is used as the relative URL. Feed item limits, RSS summary behavior, and optional reference query parameters are controlled by settings.

Pagination is controlled by `DEFAULT_PAGINATION`, `PAGINATED_TEMPLATES`, `DEFAULT_ORPHANS`, and `PAGINATION_PATTERNS`. Pagination patterns are triples of minimum page number, page URL pattern, and save-as pattern. Pattern fields include the base save path, extension, page number, and stripped base name.

## Themes and Templates

Themes are directories with templates and static assets. Built-in themes include `simple` and `notmyidea`; settings or `--theme-path` choose a theme. Template variables include settings, articles, pages, authors, categories, tags, feeds, dates, pagination objects, output file name, and the current content object where applicable.

Theme static files are copied under `THEME_STATIC_DIR` from `THEME_STATIC_PATHS`. `THEME_TEMPLATES_OVERRIDES` is searched before the theme's own templates, and templates may extend theme templates with the `!theme` prefix. User metadata fields become attributes on article and page objects for template use.

`pelican-themes` lists, installs, removes, symlinks, and cleans themes. Listing shows installed themes; install copies themes into the theme path; symlink installs by linking; remove deletes an installed theme entry; clean removes broken theme links.

## Plugins and Signals

Plugins are enabled by `PLUGINS` and may be discovered from namespace packages or paths listed in `PLUGIN_PATHS`. A plugin module is expected to register signal handlers when it is loaded. `pelican-plugins` lists discoverable namespace plugins.

Documented signal hooks let plugins observe or modify initialization, reader setup, generator setup, content objects, article/page/static generation, writing, feed generation, and finalization. Plugins may add readers, generators, writers, or injected content using public objects such as `BaseReader`, `Article`, `Writer`, and `signals`.

When plugin behavior changes reader output or metadata, content caching can preserve old results; disabling cache or ignoring cache is the documented way to force fresh reads.

## Command-Line Workflows

`pelican content` generates a site from the `content` directory and writes to `output` unless settings or CLI options choose different paths. `-s` selects a settings file, `-o` selects an output directory, `-t` selects a theme, and `-d` deletes output first subject to retention and safety rules.

`--print-settings` prints the effective configuration and exits. With setting names, it prints only those settings and reports unrecognized names. `--relative-urls` is intended for development builds. `--ignore-cache` bypasses loading previous cache data. `--fatal errors` or `--fatal warnings` turns logged errors or warnings into a failing command. `--listen` serves the output directory over HTTP; `--autoreload` watches input files and regenerates the site when they change.

`pelican-quickstart` creates a project skeleton by asking for site settings and writing starter configuration and automation files. The generated settings are a starting point; direct use of `pelican` remains canonical.

`pelican-import` converts WordPress XML, Dotclear, Blogger, Tumblr, feed input, Medium post files, and related supported formats into Pelican content files. Its command contract is conversion into content files with Pelican metadata; network-dependent import modes should fail clearly when required inputs or services are unavailable.

## Error Semantics

Invalid `--extra-settings` syntax or non-JSON values raise `ValueError`.

If the configured theme cannot be found, settings configuration raises `ValueError`.

If a reader cannot parse a file extension because no enabled reader handles it, reading fails with a type error for an unsupported content type.

If two outputs would overwrite the same target with conflicting content, writing raises `FileOverwriteFailedError`.

If a template requested by the configured theme cannot be found, generation raises a template-not-found error.

`--fatal errors` and `--fatal warnings` convert logged errors or warnings at the selected level into a nonzero command result. `--port` and `--bind` without `--listen` are accepted but logged as having no effect.

## Cross-View Invariants

- A content item's metadata drives both its Python object attributes and the generated template variables for that item.
- A content item's generated URL and save path must agree with the same URL/save-as settings, whether observed through generated files, template context, feeds, or object attributes.
- Embedded metadata takes precedence over filename, path, and default metadata in both reader output and final generated pages.
- Draft and hidden status must be reflected consistently in generated file locations, index membership, menu membership, feed membership, and object collections.
- Static and attached file links in rendered content must correspond to copied files in the output tree.
- Feed entries must refer to the same article URLs, titles, dates, authors, summaries, and language choices as the generated article pages.
- CLI settings, settings-file values, and programmatic overrides must produce the same effective settings when they describe the same site configuration.
- Cache use may skip re-reading unchanged content, but it must not change the public output for unchanged inputs and settings.
- Theme template overrides must affect generated pages without changing the source content objects they render.
- Plugin-injected readers, writers, generators, or content must be observable through the same public generated output and signal behavior as built-in components.

## Representative Workflow

Create a site with a `content` directory and a `pelicanconf.py` settings file. Add a Markdown article:

```text
Title: Keyboard Review
Date: 2010-12-03 10:20
Category: Review
Tags: hardware, keyboards
Slug: keyboard-review

Following is a review of my favorite mechanical keyboard.
```

Run:

```text
pelican content -s pelicanconf.py -o output
```

Pelican reads the article, converts metadata into an article object, renders the article with the selected theme, writes the article page according to `ARTICLE_SAVE_AS`, updates index/category/tag/archive pages according to settings, writes configured feeds, copies selected static and theme assets, and prints a processed-content summary.

Changing `ARTICLE_SAVE_AS` and `ARTICLE_URL` changes both the written path and the links in generated pages and feeds. Adding `Status: draft` moves the article to draft output and removes it from normal indexes and feeds. Running again with `--ignore-cache` forces content to be read fresh before writing output.

## Non-Goals

- Byte-for-byte reproduction of a particular theme's whitespace, formatting, or incidental HTML ordering beyond documented visible behavior.
- Reimplementing undocumented private helpers or private module layout.
- Running a long-lived web server, watcher loop, or external network service during ordinary site generation tests.
- Supporting third-party plugins beyond the documented plugin loading and signal interfaces.
- Guaranteeing deterministic output when the user relies on ambiguous multi-document `{attach}` ordering.
- Preserving compatibility with unsupported Python versions or dependency versions.

## Evaluation Notes

Correctness is evaluated through public behavior: CLI parsing and generation, settings loading and override precedence, content reader metadata, generated file trees, feeds, links, themes, static files, cache-visible behavior, plugin extension points, importer/theme helper command behavior, and the public Python objects used by templates and plugins.

The checks use temporary projects and local files. They do not require external services. Assertions focus on observable output, effective settings, object attributes, exceptions, and cross-view consistency rather than private helper names or source layout.

