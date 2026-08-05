# MkDocs Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

MkDocs builds static project documentation from Markdown source files and a YAML configuration file. A MkDocs project normally contains a `mkdocs.yml` or `mkdocs.yaml` file beside a documentation directory, usually `docs/`. The `mkdocs` command can create a starter project, serve a live-reloading preview, build static output into a site directory, deploy that output to GitHub Pages, and report inferred Python packages required by configured plugins.

MkDocs exposes a Python API for configuration loading, programmatic builds, plugin development, theme development, navigation/page/file objects, search indexing, and template helpers. Public behavior is centered on the same project model: configuration values, Markdown pages, non-Markdown assets, theme templates, plugin events, and generated site files.

## Non-Goals

- Reproducing MkDocs' internal helper names, private classes, private attributes, or implementation call graph.
- Requiring a particular third-party dependency version beyond the behavior described here.
- Implementing a real network deployment service beyond the public `gh-deploy` behavior and error handling.
- Matching byte-for-byte HTML formatting that is not user-visible or documented by MkDocs.
- Supporting undocumented test helpers, upstream test fixtures, or private modules.
- Recreating every bundled static asset exactly; the public contract is that built-in themes and search assets are available and copied/rendered according to the documented behavior.
- Guaranteeing compatibility with arbitrary third-party themes, plugins, or Markdown extensions beyond the public entry point, config, hook, and event contracts.
- Preserving soft-deprecated internals beyond their documented importability and stated behavior.

## Representative Workflows

Create and build a small site:

```bash
mkdocs new my-project
cd my-project
mkdocs build
```

The new project contains `mkdocs.yml` and `docs/index.md`. The build reads the config, discovers `docs/index.md`, renders it to `site/index.html`, copies theme assets, renders static templates such as `404.html` and `sitemap.xml` when available, and writes the built-in search index because the default `search` plugin is enabled.

Customize navigation, theme, and search:

```yaml
site_name: Example Docs
site_url: https://example.com/docs/
nav:
  - Home: index.md
  - Guide:
      - Intro: guide/intro.md
      - API: guide/api.md
  - Project: https://github.com/example/project
theme:
  name: readthedocs
  locale: en
plugins:
  - search:
      indexing: sections
      min_search_length: 2
```

Running `mkdocs serve` previews the site at a URL mounted under `/docs/`, watches the docs directory and configuration file, rebuilds when watched files change, includes draft documents with a draft marker, and exposes page, navigation, search, and theme context values consistently to templates and plugins.

Programmatic plugin example:

```python
from mkdocs.plugins import BasePlugin, event_priority, get_plugin_logger

log = get_plugin_logger(__name__)

class MyPlugin(BasePlugin):
    @event_priority(-50)
    def on_page_markdown(self, markdown, *, page, config, files):
        log.info("Updating %s", page.file.src_uri)
        return f"{markdown}\n\n> Preview\n"
```

The plugin can be enabled through `plugins`, receives validated config, participates in priority ordering for `page_markdown`, and returns a replacement Markdown string for each page.

## Source Files and Generated Files

This section covers how source files map to site output and how virtual files are created.

**File mapping.** A `File` represents how one source-like item maps into the output site. `src_uri` is always a slash-separated path relative to the source directory. `src_path` is the OS-native view. `dest_uri` is the slash-separated destination path relative to `site_dir`; `dest_path` is the OS-native view. When `use_directory_urls` is true, a Markdown file such as `guide/start.md` must map to `guide/start/index.html` with URL `guide/start/`. When `use_directory_urls` is false, `guide/start.md` must map to `guide/start.html` with URL `guide/start.html`. Index files and `README.md` at the root must map to `index.html` with URL `./` when directory URLs are enabled.

**File classification.** `is_documentation_page()`, `is_static_page()`, `is_media_file()`, `is_javascript()`, and `is_css()` must classify the file by source extension. Non-Markdown files must keep their original `dest_uri` and URL unchanged. Recognized Markdown extensions include `.markdown`, `.mdown`, `.mkdn`, `.mkd`, and `.md`.

**Generated files.** `File.generated` must create a virtual file backed by in-memory text or bytes when `content` is supplied, or backed by a physical file outside `docs_dir` when `abs_src_path` is supplied. Exactly one of `content` and `abs_src_path` must be provided; otherwise `TypeError` must be raised. Generated files must use the active plugin key as `generated_by`.

**Content access.** `File.content_bytes` and `File.content_string` are the public way to read or replace file contents. Real files read from `abs_src_path`; in-memory generated files read from stored content. `content_string` uses UTF-8 with BOM support. Assigning either property replaces the content and clears `abs_src_path`.

**Edit URI.** `File.edit_uri` defaults to `src_uri` for real source files and to `None` for generated files. Plugins may overwrite it.

**Relative URLs.** `File.url_relative_to(other)` must return this file's URL relative to another `File` or URL string.

**Files collection.** `Files` is a collection keyed by `File.src_uri`. It is iterable, has length, supports `get_file_from_path(path)`, and provides `src_uris`. `append(file)` adds or replaces a file by `src_uri`. `remove(file)` removes by `src_uri` or raises `ValueError` when absent. `documentation_pages()`, `static_pages()`, `media_files()`, `javascript_files()`, and `css_files()` must return filtered sequences.

**Inclusion levels.** `InclusionLevel` values are `EXCLUDED`, `DRAFT`, `NOT_IN_NAV`, `UNDEFINED`, and `INCLUDED`.

## Pages, Metadata, Links, and Table of Contents

This section covers how documentation pages are read, rendered, and linked.

**Page construction.** A `Page` associates a `File` with a rendered documentation page. It exposes `title`, `markdown`, `content`, `toc`, `meta`, `url`, `file`, `abs_url`, `canonical_url`, `edit_url`, `is_homepage`, `previous_page`, `next_page`, `parent`, `children`, `active`, `is_section`, `is_page`, `is_link`, `present_anchor_ids`, and `links_to_anchors`.

**Reading source.** `Page.read_source(config)` obtains the source from `on_page_read_source` when a plugin returns a string; otherwise it reads `page.file.content_string`. It separates document metadata from Markdown body. YAML front matter must begin on the first line with `---` and end with `---` or `...`; it is accepted only when it parses to a mapping. Parsed metadata must be available through `Page.meta`.

**Title resolution.** `Page.title` is resolved in this order: (1) title passed when the page was created from explicit `nav`, (2) `title` metadata in the page source, (3) the first rendered level-1 heading, (4) `Home` for the homepage, (5) the file stem converted by replacing hyphens and underscores with spaces and capitalizing only all-lowercase stems.

**Rendering.** `Page.render(config, files)` converts Markdown to HTML using `config.markdown_extensions` and `config.mdx_configs`, populates `content`, `toc`, title-from-render, present anchors, and outbound anchor links. Internal Markdown links to known source files must be rewritten to output URLs relative to the current page. Query strings and fragments must be preserved. Calling `render()` before `read_source()` must raise `RuntimeError`.

**Table of contents.** `AnchorLink` represents a table-of-contents item with `title`, `id`, `level`, `url` (as `'#' + id`), and `children`. `TableOfContents` is iterable, has length, and provides nested anchor links. `get_toc(toc_tokens)` converts toc tokens to a `TableOfContents`.

## Navigation

This section covers how navigation is built and how pages link to each other.

**Building navigation.** `get_navigation(files, config)` must build `Navigation(items, pages)` from config and files. `Navigation` is iterable over top-level items, has length, `homepage`, and `pages`. The `pages` list is the flat list of pages included in navigation order and is the basis for previous/next links.

**Navigation items.** Items are `Page`, `Section`, or `Link`. A `Section` has `is_section=True`, children, no URL, and an `active` property that propagates to ancestors when a child page is active. A `Link` represents a nav item that does not resolve to a MkDocs page; `children` is `None`, `active` is always false, and `is_link=True`.

**Omitted pages.** When documentation files are not referenced by explicit nav, they still receive `Page` objects and are built, but they are not included in `Navigation.pages` and do not get previous/next links.

## Themes and Templates

This section covers how themes provide templates and static assets.

**Theme construction.** A `Theme` must accept `name` as the theme entry point name, `custom_dir` as an override directory, `static_templates` as a set of templates rendered as standalone pages, and `locale` as the theme locale. When `custom_dir` is supplied, it must be searched before the packaged theme and must appear first in `Theme.dirs`.

**Template environment.** `Theme.get_env()` must return a Jinja environment using the theme dirs. It must register the `url` and `script_tag` filters. The environment must list `main.html` among available templates for built-in themes. Custom templates from `custom_dir` must override packaged templates with the same name.

**Template context.** Template context variables include `config`, `nav`, `base_url`, `mkdocs_version`, `build_date_utc`, `pages`, and `page`. The `url` filter must pass absolute URLs through and normalize relative URLs against the current page or `base_url`. The `script_tag` filter must render script entries as `<script>` tags.

## Plugins

This section covers how plugins participate in the build lifecycle.

**Plugin class.** Plugins subclass `BasePlugin`. A plugin may define `config_scheme` or `config_class`. After `load_config`, `plugin.config` must contain the validated config object.

**Event hooks.** Supported hooks include `on_startup`, `on_shutdown`, `on_serve`, `on_config`, `on_pre_build`, `on_files`, `on_nav`, `on_env`, `on_post_build`, `on_build_error`, `on_pre_template`, `on_template_context`, `on_post_template`, `on_pre_page`, `on_page_read_source`, `on_page_markdown`, `on_page_content`, `on_page_context`, and `on_post_page`. Hooks that receive an item may return a replacement. Returning `None` must keep the current item.

**Event priority.** Plugins run in configured order, except methods decorated with `event_priority(priority)` are ordered by descending priority within an event. Undecorated methods have priority `0`.

**Plugin collection.** `PluginCollection` is a mutable mapping of plugin key to plugin instance. `run_event(name, item=None, **kwargs)` must run registered handlers and return the final item.

**Plugin discovery.** `get_plugins()` must return installed plugin entry points. `get_plugin_logger(name)` must return a logger adapter under `mkdocs.plugins.<name>`.

## Search

This section covers the built-in search plugin behavior.

**Default activation.** The built-in `search` plugin is active by default unless the user replaces the `plugins` list with an explicit empty list or a list that does not include `search`.

**Search index.** The plugin must write `search/search_index.json` under `site_dir`. The index must contain page locations, titles, and text. Each page entry must have a `location` matching the page URL and a `title` matching the page title.

**Indexing modes.** When `indexing` is `full`, both titles and body text must be indexed. When `indexing` is `sections`, section-level entries must be indexed. When `indexing` is `titles`, only titles must appear in the index; body text must not appear in the `text` field.

**Configuration.** Search config keys include `separator`, `min_search_length`, `lang`, `prebuild_index`, and `indexing`.

## Exceptions and Error Handling

This section covers how configuration and build errors are surfaced.

**Exception hierarchy.** `MkDocsException` is the base class for MkDocs user-facing exceptions. `Abort` inherits from both `MkDocsException` and `SystemExit`, exits with code `1`. `ConfigurationError` is for configuration parsing or validation failures. `BuildError` is for MkDocs build failures. `PluginError` is a `BuildError` intended for plugin events.

**Configuration errors.** Missing default config file (`mkdocs.yml` and `mkdocs.yaml`) must raise `ConfigurationError`. YAML parse errors and missing inherited config files must raise `ConfigurationError`. Invalid config values, unknown themes, invalid plugins, invalid markdown extensions, and missing hook files must produce validation errors and `load_config` must raise `Abort`. Unknown config keys must produce warnings; strict mode converts warnings into `Abort`.

**Path validation.** `docs_dir` and `site_dir` must not contain each other; validation must raise `Abort`. `theme.custom_dir` must exist when supplied; otherwise validation must raise `Abort`. Relative `docs_dir` and `site_dir` values must resolve from the config file directory.

**Config loading.** `load_config` must support both mapping and attribute access on the returned config. It must accept `config_file` as a string path or an open file object (rewinding if needed). Keyword overrides must replace file values; `None` overrides must be ignored. When no `config_file` is supplied, `mkdocs.yml` must be preferred over `mkdocs.yaml` in the current directory.

**Default extensions and plugins.** Default `markdown_extensions` must include `toc`, `tables`, and `fenced_code`. User extensions must be appended without duplicates. Default `plugins` must include `search`; an explicit `plugins: []` must replace the default.

**Config inheritance.** The `INHERIT` key must load a parent config and deep-merge mappings while replacing lists. Missing parent files must raise `ConfigurationError`.

**Environment variable tags.** The `!ENV` YAML tag must read named environment variables, support fallback variables, and support literal defaults.

## Utilities

This section covers date, file, URL, and theme discovery helpers.

**Date helpers.** `get_build_datetime()` must return an aware UTC `datetime`. When `SOURCE_DATE_EPOCH` is set, it must return that epoch timestamp instead of the current time. `get_build_date()` must return `YYYY-MM-DD`. `get_build_timestamp()` must return the build datetime timestamp as a numeric value.

**File helpers.** `copy_file` and `write_file` must create parent directories. When `copy_file` receives a directory as the output path, it must copy into that directory using the source basename. `clean_directory` must remove non-hidden contents while preserving the directory itself and preserving entries whose names begin with `.`.

**URL helpers.** `get_relative_url` must compute relative URL paths, normalize `..` segments, and preserve trailing slashes on destination URLs. `normalize_url` must leave fully qualified URLs, network URLs, absolute paths, and anchors unchanged; otherwise it must return a URL relative to the page when supplied, or joined with `base`. `is_markdown_file` must recognize `.markdown`, `.mdown`, `.mkdn`, `.mkd`, and `.md` extensions.

**Site stale check.** `site_directory_contains_stale_files` must return `True` when the directory exists and has content, `False` when empty or missing.

**Theme discovery.** `get_themes()`, `get_theme_names()`, and `get_theme_dir(name)` must return installed theme entry points and directories.

## State Model

An MkDocs project has three public projections of the same state: the loaded configuration, the source/navigation/page objects built from the documentation tree, and the rendered site directory. Configuration changes must be reflected in both object views and generated output. A page title, URL, and navigation position must agree across its `Page`, navigation, template, and search views. Plugin event replacements must be visible to every later projection in the same build.

## Error Semantics

- Missing default config file (`mkdocs.yml` and `mkdocs.yaml`) raises `ConfigurationError`.
- YAML parse errors raise `ConfigurationError` with a parsing message.
- Missing inherited config files raise `ConfigurationError`.
- Invalid config value types, unknown required values, missing required options, invalid theme names, invalid plugin names, invalid Markdown extensions, invalid path specs, and invalid URLs produce `ValidationError` entries; `load_config` logs them and raises `Abort`.
- Unknown config keys produce warnings; strict mode converts warnings into `Abort`.
- `docs_dir` and `site_dir` may not contain each other; validation raises `Abort`.
- `theme.custom_dir` must exist when supplied; otherwise validation raises `Abort`.
- `File.generated()` raises `TypeError` unless exactly one of `content` or `abs_src_path` is provided.
- `Files.remove(file)` raises `ValueError` when the file is not in the collection.
- Calling `Page.render()` before `read_source()` raises `RuntimeError`.
- A `BuildError` during build triggers `on_build_error` and is converted into `Abort`.

## Cross-View Invariants

1. The configuration object, command-line overrides, and generated output agree on `site_dir`: build output is written to the effective `site_dir` after config-file values are overridden by command options.
2. The file collection and page URLs agree on `use_directory_urls`: every Markdown `File.dest_uri`, `File.url`, `Page.url`, rendered internal link, and navigation page URL uses the same directory-URL policy.
3. The navigation view and page view share page objects: a local file referenced in `nav` becomes the same `Page` object available through `File.page`, `Navigation.pages`, template `page`, and previous/next links.
4. Pages omitted from explicit `nav` are still rendered into the site unless excluded, but they are absent from `Navigation.pages` and have no previous or next page.
5. Exclusion state is consistent across file discovery, serve, build, navigation, and copying.
6. Page title selection is consistent across templates, navigation labels, search entries, and generated page context.
7. Repository edit links are derived from the same `repo_url`, `edit_uri` or `edit_uri_template`, and `File.edit_uri` values.
8. Markdown metadata is removed from `Page.markdown` before plugin page-markdown hooks and rendering, while parsed metadata is exposed as `Page.meta`.
9. Template `base_url`, the `url` filter, `Page.url`, and rewritten Markdown links all describe relative paths from the same current page or static template location.
10. The default search plugin indexes the rendered set of pages and writes its index under the same `site_dir` used by the build.
11. Plugin event return values are the only public way for plugins to replace config, files, navigation, environment, page content, template context, rendered templates, or rendered pages; returning `None` preserves the current value.
12. Strict mode treats user-visible warnings consistently across config loading and site building.

## Public Interface

### Import Surface

MkDocs is installed as the Python package `mkdocs` and provides the console script `mkdocs`.

The package exposes:

```python
import mkdocs
mkdocs.__version__
```

The main public Python import paths are:

```python
import mkdocs
from mkdocs.config import load_config
from mkdocs.commands.build import build, site_directory_contains_stale_files
from mkdocs.exceptions import (
    MkDocsException, Abort, ConfigurationError, BuildError, PluginError,
)
from mkdocs.plugins import (
    BasePlugin, CombinedEvent, PluginCollection, event_priority, get_plugin_logger,
)
from mkdocs.structure.files import File, Files, InclusionLevel, get_files
from mkdocs.structure.pages import Page
from mkdocs.structure.nav import Navigation, Section, Link, get_navigation
from mkdocs.structure.toc import AnchorLink, TableOfContents, get_toc
from mkdocs.theme import Theme
from mkdocs.utils import (
    get_build_datetime, get_build_date, get_build_timestamp,
    copy_file, write_file, clean_directory,
    is_markdown_file, get_relative_url, normalize_url,
    get_themes, get_theme_names, get_theme_dir,
)
```

### API Catalog

| Name | Kind | Role |
|------|------|------|
| load_config | function | Load and validate MkDocs project configuration |
| build | function | Perform a complete static site build |
| site_directory_contains_stale_files | function | Check if site directory has existing content |
| File | class | Source-to-destination file mapping |
| Files | class | Collection of file mappings keyed by src_uri |
| InclusionLevel | class | File inclusion state enum |
| get_files | function | Discover and collect project files |
| Page | class | Documentation page with metadata and rendering |
| Navigation | class | Site navigation tree |
| Section | class | Navigation section container |
| Link | class | Navigation link to external URL |
| AnchorLink | class | Table-of-contents heading entry |
| TableOfContents | class | Ordered list of heading anchors |
| get_toc | function | Convert toc tokens to TableOfContents |
| get_navigation | function | Build navigation from files and config |
| Theme | class | Theme configuration and template directories |
| BasePlugin | class | Base class for MkDocs plugins |
| CombinedEvent | class | Multiple event handlers under one event name |
| PluginCollection | class | Mutable mapping of plugin instances |
| event_priority | decorator | Set priority for plugin event methods |
| get_plugin_logger | function | Logger adapter for plugin messages |
| MkDocsException | exception | Base class for user-facing exceptions |
| Abort | exception | Intentional exit with message |
| ConfigurationError | exception | Configuration parsing or validation failure |
| BuildError | exception | Build failure |
| PluginError | exception | Plugin event failure |

### CLI Entry Points

The `mkdocs` console script and `python -m mkdocs` are supported and expose the same global options and commands. `--help` and `--version` exit with status `0`. A successful `new`, `build`, or `get-deps` command exits with status `0`; invalid command arguments, configuration failures, and build failures exit nonzero.

## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment. Site builds and deployment dry runs operate on local temporary projects; network publication is not required.

## Appendix B: Assessment Notes

Compatibility covers command workflows, public APIs, configuration, local site builds, plugins and hooks, themes and templates, search output, navigation and page objects, links, metadata, errors, and documented utilities. It checks observable outputs, returned objects, public exception classes, and cross-view relationships without depending on private modules, private attributes, source layout, internal call order, or hidden fixture shapes.
