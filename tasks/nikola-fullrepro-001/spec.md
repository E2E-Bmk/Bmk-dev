# Static Site Generator Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

This package is a static site and blog generator. A project contains configuration, content source files, themes, assets, plugins, and generated output. The console command and the Python API operate on the same project state: source posts and pages are scanned, metadata is resolved, paths and links are computed, compilers render source documents, build tasks produce files, and the output directory contains the generated website.

The system is modular. Commands, compilers, template systems, taxonomies, metadata extractors, shortcodes, and tasks are plugin categories. A local site build must work without network access when the project uses local content, local themes, and installed Python dependencies.

## Non-Goals

- This specification does not require private helper functions, private attributes, internal task dictionaries, dependency-cache keys, plugin-manager internals, or exact dependency-graph construction order.
- This specification does not require exact theme-specific HTML bytes, whitespace, asset ordering, or template implementation details.
- This specification does not require live deployment, plugin download or install behavior, external network checks, or image-processing algorithms.
- This specification does not require every optional plugin shipped with the upstream project. It covers the public plugin category contracts and the local site lifecycle commands listed below.
- Exact rich or text representation strings, log message text, and warning wording are not part of the contract.

## Representative Workflows

### Initialize, Author, and Build

```python
from pathlib import Path
from nikola.__main__ import main

root = Path("orbital-site")
assert main(["init", "--quiet", str(root)]) in (0, None)
assert main(["--conf=" + str(root / "conf.py"), "new_post", "-t", "Ceramic Mugs Guide"]) in (0, None)
assert main(["--conf=" + str(root / "conf.py"), "build"]) == 0
assert (root / "output" / "index.html").is_file()
```

The initialization command must create a local project with configuration and content folders. A post created afterward must be discoverable during a later build, and the build must write generated pages under the configured output directory.

### Register and Apply a Shortcode

```python
from nikola import Nikola

site = Nikola(SITE_URL="https://orbital.test/", TRANSLATIONS={"en": ""}, DEFAULT_LANG="en")
site.register_shortcode("marker", lambda site, data, lang, post=None: "MARKER")
rendered, deps = site.apply_shortcodes("{{% marker %}}", "fragment.rst", "en", {})
assert rendered == "MARKER"
assert deps == []
```

Registering a shortcode on the site object must make it available to later shortcode application through the same registry and context.

### Resolve Post Paths

```python
post = site.posts[0]
destination = post.destination_path("en")
permalink = post.permalink("en")
assert destination.endswith("index.html") or destination.endswith(".html")
assert permalink.startswith("/")
```

For a scanned post, the destination path and permalink must agree with the site's configured URL style and path handlers.

## Site Initialization and CLI Commands

The supported console command is `nikola`. Direct invocation through `nikola.__main__.main(args)` is supported as the Python entry surface.

**Configuration-free commands.** `help`, `version`, `init`, and import commands must run without an existing project configuration. `help` and `version` must return success.

**Project initialization.** `init TARGET` must create a local project directory containing a configuration file and folders needed for content and generated output. If the target cannot be used as a destination, the command must fail without claiming success.

**Build.** `build` must read configuration, scan posts and pages, load plugins, produce build tasks, and write generated files to the configured output folder. When strict mode is enabled, warnings that would otherwise be non-fatal must cause a non-zero result.

**Check.** `check` must inspect generated site links and files. It returns success when checked links and generated paths satisfy the selected constraints.

**Content creation.** `new_post` and `new_page` must create source files with metadata in the configured folders. If the requested destination file already exists, the command must fail rather than overwrite silently.

**Import.** `import_wordpress` must read a WordPress export file and create local content files and metadata. Malformed import input must fail as an import error.

**Failure handling.** Unknown commands, invalid command options, malformed configuration files, missing required configuration files for commands that need a project, and duplicate `new_post` or `new_page` targets must return non-zero status.

## Text Utilities and Metadata Helpers

The utility surface provides string, path, metadata, and locale helpers used across the site lifecycle.

**Slug helpers.** `slugify` must lowercase ASCII words, transliterate diacritics, and remove unsafe punctuation from slugs. `unslugify` must restore a human-readable title from a slug.

**Link encoding.** `encodelink` must percent-encode spaces and Unicode characters while preserving already-encoded sequences.

**Translation filenames.** `get_translation_candidate(config, path, lang)` must derive translated source filenames from `TRANSLATIONS`, `DEFAULT_LANG`, and `TRANSLATIONS_PATTERN`. Supported patterns include `{path}.{lang}.{ext}` and `{path}.{ext}.{lang}`.

**Metadata booleans.** `bool_from_meta(meta, key, fallback=..., blank=...)` must treat `true`, `yes`, and `1` as true; `false`, `no`, and `0` as false; use `blank` when the key is missing; and use `fallback` for unrecognized text.

**Metadata writing.** `write_metadata(data, format_name)` must serialize declared metadata keys. For the Nikola metadata format, title and slug entries must appear as `.. title:` and `.. slug:` lines followed by a blank line.

**Redirect and data files.** `create_redirect(path, url)` must write an HTML redirect document containing the target URL. `load_data(path)` must load JSON mappings from `.json` files.

**Locale settings.** `TranslatableSetting(name, inp, translations)` must return language-specific values through `setting(lang)`. When `inp` is a `{lang: value}` mapping, each configured language must receive its declared value. `config_changed(config, identifier)` must store the configuration snapshot and expose it through `config` and `identifier`. `LocaleBorg.initialize(locales, initial_lang)` must initialize locale state used by translatable settings.

## Shortcode Processing

Shortcodes are named functions embedded in source text.

**Extraction.** `extract_shortcodes(data)` must replace each shortcode occurrence with a token placeholder and return the tokenized text plus a replacement map.

**Application.** `apply_shortcodes(data, registry, site, filename, raise_exceptions, lang, extra_context)` must expand registered shortcodes and return the rendered text plus dependency paths. Unknown shortcodes with exceptions enabled must yield empty rendered output. Shortcodes with body content must pass the body to the handler.

**Site integration.** `Nikola.register_shortcode(name, handler)` must store the handler in `shortcode_registry`. `Nikola.apply_shortcodes(data, filename, lang, extra_context)` must expand shortcodes using that registry and return the same rendered result as the standalone shortcode API when given the same registry and context.

**Errors.** Malformed shortcode syntax must raise `ParsingError` when exceptions are not suppressed.

## Path Resolution and Link Generation

Path handlers map named entities to URL path components.

**Registration.** `register_path_handler(kind, handler)` must register a callable for `kind`. `path(kind, name, lang, is_link)` must return the configured path for that entity and language. When `is_link` is true, the result must be an absolute link path beginning with `/`. When `is_link` is false, the result must be relative to the output directory using platform separators. Unknown path kinds must return an empty string.

**Post paths.** `Post.destination_path(lang, extension, sep)` must return the generated output path for a scanned post. `Post.permalink(lang, absolute, extension, query)` must return the public URL path for the same post and language.

**Links.** `rel_link(from_path, to_path)` must compute a relative link between two generated page paths under pretty URLs.

## Content Scanning, Compilation, and Build Output

**Scanning.** After `init_plugins()` and `scan_posts()`, the site must expose scanned content through `site.posts`. A source file created by `new_post` or `new_page` must appear in `site.posts` or the page collection on the next scan using the same configuration.

**Compiler selection.** `get_compiler(source_name)` must select a compiler based on the source extension and configured compiler registry. A `.rst` post source must resolve to the reStructuredText compiler.

**Generated projections.** A successful `build` must write at minimum:

- the site index page;
- post and page output files under `output/posts/` and `output/pages/`;
- archive, category, RSS, and sitemap outputs when enabled by default configuration;
- category pages for tag metadata attached to published posts.

**Publication status.** Draft posts must be excluded from the public RSS feed and from public index listings. Published posts must appear in RSS and in the site index.

**Cross-output consistency.** The site index, RSS feed, and sitemap must reference the same public post URL for a published post.

## Plugin Contracts

Plugins must receive the active site through `set_site(site)` before they are used.

- A `Command` plugin must expose command-line behavior through `execute(options, args)`.
- A `Task` or `LateTask` plugin must yield build tasks with observable targets, file dependencies, and actions.
- A `PageCompiler` plugin must compile supported source files.
- A `MetadataExtractor` plugin must extract metadata from source text, filenames, or sidecar files.
- A `ShortcodePlugin` must register its handler on the active site when `set_site()` is called.
- A `Taxonomy` plugin must classify posts and provide paths and contexts for classification pages.

Task generation must be deterministic for the same configuration and content state.

## State Model

The system exposes one project through three public projections.

1. **Configuration projection** — the configuration file and runtime configuration dictionary. It defines folders, post and page patterns, languages, URL style, compilers, themes, feeds, taxonomies, and build options.
2. **Content projection** — the source tree containing posts, pages, translations, sidecar metadata files, static assets, themes, templates, and plugin files. `Post` objects and metadata extractors read this projection.
3. **Generated projection** — the output site containing rendered HTML pages, feeds, sitemaps, copied assets, and taxonomy outputs. CLI commands and render methods write this projection.

State written through one projection must be visible through the others on the same project.

## Error Semantics

| Condition | Required result |
| --- | --- |
| Invalid configuration file passed to `--conf=` | Non-zero CLI status; no successful build |
| Missing configuration file for a command that requires a project | Non-zero CLI status |
| Unknown CLI command | Non-zero CLI status |
| Invalid CLI option | Non-zero CLI status |
| Duplicate `new_post` or `new_page` destination | Non-zero CLI status |
| Malformed shortcode with exceptions enabled | Raise `ParsingError` |
| Unknown shortcode with exceptions enabled | Empty rendered output |
| Unknown path handler kind | Return empty path string from `path()` |
| Unsupported source extension in `get_compiler()` | Terminate with non-zero process status |

`help` and `version` must return success without a project configuration.

## Cross-View Invariants

1. A site initialized by `init` must contain configuration and content folders that a later `build` reads from the same project directory.
2. A source file created by `new_post` must be discoverable as a scanned `Post` on the next scan using the same configuration.
3. A `Post.destination_path()` value must match the generated file path written during a build for the same post, language, extension, and URL style.
4. A `Post.permalink()` value must match the URL produced by the site's path and link handlers for the same post and language.
5. Category pages must contain the same posts that the corresponding post tag metadata assigns to those classifications.
6. RSS feeds must include feed-eligible published posts and must exclude draft posts.
7. A scanned post title must appear in the rendered HTML output for that post.
8. A shortcode registered on the site must produce the same replacement text through `Nikola.apply_shortcodes()` and through the standalone shortcode API with the same registry and context.
9. A sitemap entry must correspond to a generated public output file and public URL.
10. The compiler selected for a scanned post source extension must be the compiler used for that source during build.

## Public Interface

### Import Surface

The package is imported as `nikola`.

```python
import nikola
from nikola import Nikola
from nikola.__main__ import main
from nikola.post import Post
from nikola.shortcodes import ParsingError, apply_shortcodes, extract_shortcodes
from nikola.utils import (
    LocaleBorg,
    TranslatableSetting,
    bool_from_meta,
    config_changed,
    create_redirect,
    encodelink,
    get_translation_candidate,
    get_root_dir,
    load_data,
    slugify,
    unslugify,
    write_metadata,
)
from nikola.plugin_categories import (
    BasePlugin,
    Command,
    CompilerExtension,
    Importer,
    LateTask,
    MetadataExtractor,
    PageCompiler,
    ShortcodePlugin,
    Task,
    Taxonomy,
    TemplateSystem,
)
from nikola.metadata_extractors import default_metadata_extractors_by
```

### API Catalog

| Name | Kind | Role |
| --- | --- | --- |
| Nikola | class | Site object owning configuration, posts, compilers, and renderers |
| Post | class | Public post or page object with metadata, paths, and permalinks |
| main | function | Console entry point returning integer exit status |
| __version__ | constant | Package version string |
| DEBUG | constant | Debug flag derived from environment |
| TEMPLATES_TRACE | constant | Template trace flag derived from environment |
| SHOW_TRACEBACKS | constant | Traceback display flag derived from environment |
| slugify | function | Convert text into a URL slug |
| unslugify | function | Convert a slug into a readable title |
| encodelink | function | Percent-encode a link path |
| get_translation_candidate | function | Derive translated source filenames |
| bool_from_meta | function | Parse boolean metadata values |
| write_metadata | function | Serialize metadata to text |
| create_redirect | function | Write an HTML redirect document |
| load_data | function | Load structured data from a file |
| TranslatableSetting | class | Language-aware configuration value |
| LocaleBorg | class | Locale state shared across rendering |
| config_changed | class | Track configuration snapshots for rebuild detection |
| get_root_dir | function | Locate the project root directory |
| apply_shortcodes | function | Expand shortcodes in text |
| extract_shortcodes | function | Tokenize shortcodes in text |
| ParsingError | exception | Raised for malformed shortcode syntax |
| BasePlugin | class | Base class for plugins |
| Command | class | Plugin category for CLI commands |
| Task | class | Plugin category for build tasks |
| LateTask | class | Plugin category for late build tasks |
| PageCompiler | class | Plugin category for source compilers |
| CompilerExtension | class | Plugin category for compiler extensions |
| MetadataExtractor | class | Plugin category for metadata extraction |
| ShortcodePlugin | class | Plugin category for shortcodes |
| Taxonomy | class | Plugin category for classifications |
| TemplateSystem | class | Plugin category for template engines |
| Importer | class | Plugin category for import commands |
| default_metadata_extractors_by | mapping | Registry of built-in metadata extractors |

### CLI Entry Points

Console script: `nikola`

Supported commands in this specification:

| Command | Role |
| --- | --- |
| init | Create a new project |
| build | Build the current site |
| check | Validate generated links and files |
| new_post | Create a new post source file |
| new_page | Create a new page source file |
| import_wordpress | Import content from a WordPress export |
| help | Show command help |
| version | Print package version |

| Exit code | Meaning |
| ---: | --- |
| 0 | Success, including successful `help` and `version` |
| non-zero | Unknown command, invalid option, malformed configuration, missing required file, duplicate content target, or build failure |

## Appendix A: Environment

The working environment runs Python 3.11 on Linux without network access.
The following third-party packages are preinstalled and importable:
pytest, docutils, markdown, jinja2, pygments, python-dateutil, pytz,
unidecode, lxml, feedgenerator, blinker, doit, mako, Babel, requests,
Pillow, piexif, PyRSS2Gen, and natsort.

The assessment environment provides the same interpreter and package set.

The project must declare its packaging metadata in a standard
`pyproject.toml` (or `setup.py`) at the project root so the package
can be installed with pip.

Local workflows use filesystem access and installed Python packages for
rendering, feeds, dates, templates, localization, and markup parsing.
Temporary project directories are used for assessment instead of live
network services.

## Appendix B: Assessment Notes

Implementations are exercised through public Python APIs, the `nikola`
console command, and generated local files. Checks cover initialization,
configuration loading, content creation, metadata helpers, path and
permalink generation, shortcode expansion, plugin contracts, build output
consistency, feeds, sitemaps, command exit status, and cross-view
consistency between Python objects and generated files.

The focus is on observable behavior from the public contract above, not
private data structures, exact template bytes, or internal task dictionaries.
Tests use anti-memorization parameter values and local temporary project
directories instead of live network services.
