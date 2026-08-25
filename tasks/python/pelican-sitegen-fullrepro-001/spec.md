# Pelican Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

This package turns a directory of written content into a static site. A project combines settings, Markdown documents, templates, and static assets; generation produces article and page files, collection pages, feeds, and copied assets that all describe the same content objects.

## Non-Goals

- This specification does not require Import conversion, project quickstart, theme installation or removal, or plugin discovery.
- This specification does not require Live serving, autoreload loops, or cache file compatibility.
- This specification does not require Private helpers, exact log wording, exact HTML whitespace, or implementation-specific object representations.

## Representative Workflows

### Generate a site from settings and content

```python
from pelican import Pelican
from pelican.settings import read_settings

settings = read_settings(path="pelicanconf.py", override={
    "SITENAME": "My Blog",
    "SITEURL": "https://example.com",
    "PATH": "content",
    "OUTPUT_PATH": "output",
    "FEED_ALL_ATOM": "feeds/all.atom.xml",
})

pelican = Pelican(settings)
pelican.run()
```

`read_settings` loads defaults, file settings, and explicit overrides into one mapping. `Pelican(settings).run()` reads the configured content directory and writes the generated site (articles, pages, taxonomy pages, feeds, and static assets) to `OUTPUT_PATH`. The resulting article files, index entries, and feed entries must expose the same title, URL, and taxonomy values derived from Markdown metadata.

### Parse arguments and generate via CLI

```console
$ pelican content -s pelicanconf.py -o output --extra-settings SITENAME=\"My Blog\"
```

```python
from pelican import parse_arguments, get_config, Pelican

args = parse_arguments(["content", "-s", "pelicanconf.py", "-o", "output"])
settings = get_config(args)
assert settings["SITENAME"] is not None

pelican = Pelican(settings)
pelican.run()
```

`parse_arguments` parses CLI arguments including `--extra-settings` overrides. `get_config` converts the parsed namespace into generation settings. Changing an article's `Status: hidden` keeps its file but removes it from indexes and feeds; `Status: draft` writes under the draft location and likewise excludes it from normal collections.

## Content and Metadata Behavior

Content items are articles and pages whose metadata drives their placement, classification, and appearance in the generated site.

**Article metadata.** Markdown metadata must supply title, date, category, author, tags, slug, summary, and status values. These values must be available to the article template as `article.title`, `article.url`, `article.save_as`, `article.category`, `article.author`, `article.tags`, `article.summary`, and `article.content`. The template context must also include `SITENAME` and `SITEURL` from the effective settings.

**Publication status.** Published articles must appear in the main index and feeds. When `Status: hidden` is set, the article must retain its output file at the configured article location but must be omitted from the index and all feeds. When `Status: draft` is set, the article must be written under the configured draft location determined by `DRAFT_URL` and `DRAFT_SAVE_AS`, and must be omitted from the main index and all feeds.

**Page metadata.** Pages use the page URL and save-path settings (`PAGE_URL` and `PAGE_SAVE_AS`) independently from article settings. The page template must receive `page.title`, `page.url`, and `page.content`.

**Taxonomy collection pages.** Category, tag, and author collection pages must be generated from the corresponding article metadata. Each unique category must produce a collection page at the location determined by `CATEGORY_SAVE_AS`. Each unique tag must produce a page at `TAG_SAVE_AS`. Each unique author must produce a page at `AUTHOR_SAVE_AS`.

**Static assets.** A static path selected by `STATIC_PATHS` must be copied to the output tree. A `{static}` link in Markdown content must resolve to the copied asset under the configured `SITEURL`, producing an `href` attribute pointing to the full site URL plus the asset path.

## Site Generation and Feeds

`Pelican(settings).run()` reads the configured content directory and produces the complete output site.

**Article output.** Article files must be written to the path determined by `ARTICLE_SAVE_AS`. The rendered output must contain the article's title, URL, save path, category, author, tags, summary, and body as derived from its Markdown metadata.

**Page output.** Page files must be written to the path determined by `PAGE_SAVE_AS`. The rendered output must contain the page body.

**Index output.** The generated index must list published articles by title. Hidden and draft articles must not appear in the index.

**Atom feeds.** When `FEED_ALL_ATOM` is configured, an all-articles Atom feed must be generated at the configured path. Each published article must produce a feed entry whose title matches the article title and whose link `href` matches the full article URL including `SITEURL`. Hidden and draft articles must not appear in the feed. When `CATEGORY_FEED_ATOM` is configured, a category feed must be generated using the category slug in its output path.

**Source exclusion.** Source Markdown files must not be copied into the generated output tree unless they are separately selected as static assets.

**Settings consistency.** The command-line and programmatic settings views must describe the same site name when given equivalent `SITENAME` values through `get_config` and `read_settings` respectively.

## Settings and Configuration

Settings loading merges defaults, file settings, and explicit overrides into one effective mapping.

**Default settings.** `DEFAULT_CONFIG` must contain built-in default values. The `DEFAULT_LANG` default must be `"en"`. All defaults must be present in the effective settings unless explicitly overridden.

**Settings loading.** `read_settings` must return the effective settings mapping. Built-in defaults must always be present, settings loaded from a file (when a `path` is provided) must replace matching defaults, and explicit `override` values must replace both. When `OUTPUT_PATH` is supplied through an override, it must be normalized as a filesystem path.

**CLI argument parsing.** `parse_arguments` must parse command arguments. Each `--extra-settings` (or `-e`) value must use `KEY=JSON_VALUE` format where the value is valid JSON; repeated options must accumulate in the returned `overrides` mapping on the parsed arguments object. A missing equals sign must raise `ValueError`. An invalid JSON value after the equals sign (such as bare `True` instead of `true`) must raise `ValueError`. The `--relative-urls` flag must be accepted.

**CLI-to-settings conversion.** `get_config` must convert the parsed namespace into generation settings, incorporating the overrides and the relative-URL option. When `--relative-urls` is passed, the resulting settings must set `RELATIVE_URLS` to `True`.

## Readers, Utilities, Taxonomy, and Pagination

These components support content processing, URL generation, taxonomy classification, and collection pagination.

**Content readers.** `Readers.read_file` must select a reader by file extension. Markdown input must return rendered content accessible through the result's `content` attribute and normalized metadata accessible through `metadata`, including at least the `title` field. An extension with no enabled reader must raise `TypeError` instead of being treated as plain text.

**Slug generation.** `slugify` must apply configured regular-expression substitution pairs passed as `regex_subs` and return the URL slug. When `preserve_case` is not set or is `False`, the result must be lowercased. When `preserve_case` is `True`, the original casing must be retained.

**Path utilities.** `posixize_path` must normalize paths to forward-slash form on every platform. `path_to_url` must produce forward-slash URL paths.

**Date parsing.** `get_date` must parse Pelican date metadata strings into datetime values. Unparseable date metadata must raise a date-parsing error.

**Taxonomy wrappers.** `Author`, `Category`, and `Tag` must each be created with a display name and a `settings` mapping. Each must expose a `slug`, `url`, and `save_as` derived from the display name and the corresponding URL/save-as setting patterns. The slug must be generated from the display name using standard slug rules. `as_dict()` must return a mapping containing at least the public `name` and `slug`.

**Pagination.** `Paginator` must divide an ordered collection into pages based on a `per_page` count. It must report `count` (total items), `num_pages` (total pages), and `page_range` (list of page numbers starting at 1). `Paginator.page(n)` must return a page object exposing `object_list` for that page's items, `has_next()` returning whether a next page exists, and `has_previous()` returning whether a previous page exists. The first page must have a next page but no previous page; a middle page must have both neighbors. `PaginationRule` must be a public three-field value containing `min_page`, `URL` pattern, and `SAVE_AS` pattern.

**Signals.** Signal objects must be available through both `from pelican import signals` and `from pelican.plugins import signals`. The same signal objects must be shared between both namespaces; `signals.article_generator_finalized` from either import path must be the same object, and `signals.content_object_init` must likewise be the same object.

## State Model

A generated site has three public projections of the same state: the loaded settings mapping, the in-memory content and taxonomy objects, and the output tree containing rendered pages, feeds, and assets. Generation must keep these projections aligned.

A setting used to derive an article URL must produce the same URL in the article object, its rendered template context, and its feed entry. Metadata read from a source document must remain the same when exposed as content attributes and rendered page values. Publication status must control both where a content item is written and whether it appears in indexes and feeds.

## Error Semantics

- When `parse_arguments` encounters a `--extra-settings` value missing an equals sign, it must raise `ValueError`.
- When `parse_arguments` encounters a `--extra-settings` value with invalid JSON after the equals sign, it must raise `ValueError`.
- When `Readers.read_file` is called with a file extension that has no enabled reader, it must raise `TypeError` instead of treating the file as plain text.
- When the content source directory (`PATH`) does not exist, generation must fail rather than report a successful partial site.
- When required templates are missing, generation must fail rather than report a successful partial site.
- When the output location (`OUTPUT_PATH`) is unwritable, generation must fail rather than report a successful partial site.
- When `slugify` receives input with disabled case preservation, the result must be lowercased.
- When `get_date` receives unparseable date metadata, it must raise a date-parsing error.

## Cross-View Invariants

1. Loaded defaults and explicit overrides must produce the same effective values through `read_settings()` and `get_config()`.
2. Article metadata must match the values visible in its content object and template context.
3. Article URL and save-path settings must agree with the written file and all links to it.
4. Published, hidden, and draft status must agree across output location, index membership, and feed membership.
5. Category, author, and tag slugs must agree across wrapper objects and generated collection paths.
6. A feed entry title and URL must match the corresponding generated article page.
7. A static link must resolve to the same asset copied into the output tree.
8. Pagination neighbor values must agree with the page count and page range for the same collection.

## Public Interface

### Import Surface

The package is imported as `pelican`.

```python
from pelican import Pelican, get_config, parse_arguments, signals
from pelican.plugins import signals as plugin_signals
from pelican.settings import DEFAULT_CONFIG, read_settings
from pelican.readers import Readers
from pelican.urlwrappers import Author, Category, Tag
from pelican.paginator import PaginationRule, Paginator
from pelican.utils import get_date, path_to_url, posixize_path, slugify
```

Signal objects are available through both `from pelican import signals` and `from pelican.plugins import signals`.

The `pelican` command accepts a content directory together with settings and output options. `python -m pelican` follows the same site-generation entry path.

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `read_settings` | function | Loads defaults, file settings, and overrides into one mapping |
| `parse_arguments` | function | Parses CLI arguments and extra-settings overrides |
| `get_config` | function | Converts parsed CLI arguments into generation settings |
| `DEFAULT_CONFIG` | constant | Built-in default settings mapping |
| `Readers` | class | Selects content readers by file extension |
| `Pelican` | class | Site generator for articles, pages, feeds, and assets |
| `Author` | class | Author taxonomy wrapper with slug and URL |
| `Category` | class | Category taxonomy wrapper with slug and URL |
| `Tag` | class | Tag taxonomy wrapper with slug and URL |
| `Paginator` | class | Divides ordered collections into pages |
| `PaginationRule` | class | Minimum page, URL pattern, and save-path pattern |
| `slugify` | function | Converts display text into URL slugs |
| `posixize_path` | function | Normalizes paths to forward-slash form |
| `path_to_url` | function | Converts filesystem paths to URL paths |
| `get_date` | function | Parses Pelican date metadata into datetime values |
| `signals` | module | Public signal objects for plugin hooks |

Settings loading, CLI parsing, reader selection, slug and path utilities, taxonomy wrappers, and pagination behavior are defined in the behavior sections above.

### CLI Entry Points

The `pelican CONTENT -s SETTINGS -o OUTPUT` command generates a local site and returns zero on success. Invalid arguments or generation failures return nonzero. `python -m pelican` supports the same behavior. Other Pelican helper commands are outside this scope.

## Appendix A: Environment

The implementation may use third-party packages available on PyPI. Runtime dependencies must be declared in a standard `requirements.txt` or `pyproject.toml` at the project root and are installed before use. Site generation must remain deterministic with local temporary files and must not require network services.

## Appendix B: Assessment Notes

Correctness is evaluated through public behavior: CLI parsing and generation, settings loading and override precedence, content reader metadata, generated file trees, feeds, links, themes, static files, cache-visible behavior, plugin extension points, importer/theme helper command behavior, and the public Python objects used by templates and plugins.

The checks use temporary projects and local files. They do not require external services. Assertions focus on observable output, effective settings, object attributes, exceptions, and cross-view consistency rather than private helper names or source layout.
