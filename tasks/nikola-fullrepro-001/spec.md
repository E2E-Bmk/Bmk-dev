# Nikola Specification

## Product Overview

Nikola is a static site and blog generator. A project contains configuration, content source files, themes, assets, plugins, and generated output. The `nikola` command and the Python API both operate on the same project state: source posts and pages are scanned, metadata is resolved, paths and links are computed, compilers render source documents, tasks produce files, and the output directory contains the generated website.

Nikola is modular. Commands, compilers, template systems, taxonomies, metadata extractors, shortcodes, and tasks are plugin categories. A local site build must work without network access when the project uses local content, local themes, and installed Python dependencies.

## Scope

This specification covers the documented local site lifecycle:

- package import and version/debug flags;
- the `nikola` command line interface for local commands including `init`, `build`, `check`, `new_post`, `new_page`, `serve`, `help`, `version`, and `import_wordpress`;
- `nikola.Nikola` as the site object that owns configuration, posts, path handlers, compilers, template rendering, shortcodes, filters, taxonomies, and generated tasks;
- `nikola.post.Post` as the public post/page object with metadata, translations, source paths, destination paths, permalinks, dependencies, and rendered text;
- metadata extraction from source text, sidecar metadata files, filename patterns, and configured metadata formats;
- Markdown, reStructuredText, HTML, and notebook-style page compiler behavior at the level of accepted source files and generated fragments;
- path handlers, links, permalinks, slugs, taxonomy/category/tag paths, RSS/Atom output, sitemap output, and generated file-tree invariants;
- public plugin category base classes and hooks needed to author local command, task, compiler, metadata, shortcode, taxonomy, and template plugins.

This specification describes public behavior and observable project state. It does not define exact theme markup, private task dictionaries, internal dependency-cache keys, or implementation order.

## Installable Surface

The package is imported as `nikola`. The console entry point is `nikola`, which calls `nikola.__main__.main(args=None)`. The top-level package exposes `nikola.Nikola`, `nikola.__version__`, and debug flags derived from environment variables.

Public documentation and automodule pages expose `nikola.nikola.Nikola`, `nikola.post.Post`, `nikola.metadata_extractors`, `nikola.plugin_categories`, `nikola.shortcodes`, and selected utility APIs from `nikola.utils`. Public plugin modules under `nikola.plugins.command`, `nikola.plugins.compile`, `nikola.plugins.task`, `nikola.plugins.template`, and `nikola.plugins.misc` are extension points when they implement documented plugin categories.

The supported local source formats in this scope are reStructuredText, Markdown, HTML fragments, and notebook files when the corresponding dependencies are installed. The implementation is permitted to use any template engine internally, but public behavior must expose template rendering through the `Nikola` and `TemplateSystem` contracts.

## Public API

`nikola.__version__` returns the package version string. `nikola.DEBUG`, `nikola.TEMPLATES_TRACE`, and `nikola.SHOW_TRACEBACKS` are booleans derived from `NIKOLA_DEBUG`, `NIKOLA_TEMPLATES_TRACE`, and `NIKOLA_SHOW_TRACEBACKS`.

`main(args=None)` runs the command line interface. When `args` is `None`, it uses process command-line arguments. It returns an integer exit status. Commands that do not require a site configuration, such as `init`, `version`, and import commands, must run without a `conf.py`. Commands that operate on an existing site must locate or load the configuration file before creating the site object.

`Nikola(**config)` constructs a site object from configuration values. The object must expose configuration values, source/output folders, compilers, path handlers, posts, translations, taxonomies, and task plugins through public methods. Missing required configuration values must be reported as command/configuration errors rather than producing a partial successful build.

`Post(source_path, config, destination, use_in_feeds, messages, template_name, compiler, destination_base=None, metadata_extractors_by=None)` represents a post or page source. It must resolve source paths, translations, metadata, destination paths, permalink, rendered text, dependencies, title, author, description, tags, and status from the source file, sidecar files, configuration, and compiler.

`nikola.plugin_categories` defines author-facing plugin base classes: `BasePlugin`, `Command`, `Task`, `LateTask`, `TemplateSystem`, `PageCompiler`, `CompilerExtension`, `MetadataExtractor`, `ShortcodePlugin`, `Importer`, and `Taxonomy`. Each plugin receives the active site with `set_site(site)` when loaded. Plugins must report dependencies and generated tasks through their public category methods.

`nikola.metadata_extractors` exposes metadata source, priority, and condition objects plus extractors for Nikola metadata comments, YAML metadata, TOML metadata, and filename-regex metadata. Metadata extractors return dictionaries of metadata keys and values, and metadata writers produce text in their declared format.

`nikola.shortcodes.extract_shortcodes(data)` returns parsed shortcode occurrences from text. `nikola.shortcodes.apply_shortcodes(data, registry, site, filename, raise_exceptions, lang, extra_context)` returns text with registered shortcodes expanded. Malformed shortcode syntax must raise `ParsingError` when errors are not suppressed.

The selected utility surface includes `slugify`, `unslugify`, `encodelink`, `get_translation_candidate`, `write_metadata`, `bool_from_meta`, `TranslatableSetting`, `LocaleBorg`, `config_changed`, `get_root_dir`, `create_redirect`, `load_data`, and `rss_writer`. These functions must operate on public strings, paths, metadata dictionaries, locale values, and generated files rather than on private site internals.

## Product State Model

Nikola exposes the same site through three public projections.

The configuration projection is the `conf.py` and runtime configuration dictionary. It defines folders, post/page patterns, languages, URL style, path handlers, compilers, themes, template variables, metadata formats, taxonomies, feeds, and build options.

The content projection is the source tree. It contains posts, pages, translations, sidecar metadata files, static assets, themes, templates, and plugin files. `Post` objects and metadata extractors read this projection.

The generated projection is the output site. It contains rendered HTML and other pages, feeds, sitemaps, copied assets, redirect files, and path/taxonomy outputs. CLI commands and Python render methods write this projection.

State written through one projection must be visible through the others on the same project. A post source added by `new_post` must be discoverable by a later build. A path produced by a path handler must match both the `Post.permalink()` result and the generated output location. A configuration change that changes URLs, translations, post patterns, or output folders must change the generated projection on the next build.

## Project Initialization And CLI Commands

`nikola init TARGET` must create a local project directory. An empty project must include a configuration file and folders needed for content and generated output. A demo project must additionally include sample content that is buildable. If the target exists and is not usable as a destination, the command must fail without claiming success.

`nikola build` must build the current site. It must read configuration, scan posts/pages, load plugins, produce build tasks, and write generated files to the configured output folder. With strict mode enabled, warnings that would otherwise be non-fatal must cause a non-zero result. With invariant mode enabled and the required dependency available, time-dependent output must use the invariant timestamp.

`nikola check` must inspect generated site links and files. It returns success when checked links and generated paths satisfy the command's selected constraints. It returns a non-zero status when required files or links are missing.

`nikola new_post` and `nikola new_page` must create content source files with metadata. The commands must respect configured post/page folders, default compiler, title, slug, date, scheduled publication options, and page/post selection. If the requested destination file already exists, the command must fail rather than overwrite silently.

`nikola import_wordpress` must read a WordPress export file and create local Nikola content files and metadata. It must transform WordPress post/page content into Nikola source files, preserve titles, dates, slugs, tags/categories, status, and attachments when those values are present, and report malformed input as an import failure.

`nikola help` and `nikola version` must run without a project configuration. Unknown commands and invalid command options must return non-zero status.

## Configuration, Content, And Metadata

Configuration values control folders, post/page source patterns, URLs, languages, compilers, feeds, taxonomies, templates, and plugin behavior. Values loaded from the active configuration file must be available to the site object and to plugins after the site is constructed.

Posts and pages are source files paired with metadata. Metadata is accepted from Nikola metadata comments, YAML, TOML, sidecar metadata files, or filename-derived metadata when configured. Metadata from an invalid format must raise or report a metadata error. Missing optional metadata must fall back to configured defaults. Required title/path/date values must be present before rendering the post as a normal published item.

A post status of published, draft, private, or scheduled must affect visibility in indexes and feeds. Draft and private posts must not appear in normal public indexes and feeds. Future-dated or scheduled posts must not be published in normal builds until the configured publication condition is satisfied.

Translations are keyed by language. A translated source must map to the same logical post/page as the default-language source. When a translation is absent, translation lookup returns the configured fallback candidate or reports that the translation is unavailable.

## Paths, Links, And Taxonomies

Path handlers map named entities to URL path components. `register_path_handler(kind, f)` must register a callable for `kind`. `path(kind, name, lang, is_link)` must return the configured path for that entity and language. Asking for an unknown path kind must fail with an error rather than returning an arbitrary path.

`post_path`, `slug_path`, `slug_source`, and `filename_path` must produce paths consistent with the configured URL style, language, and index-file policy. `Post.destination_path(lang, extension, sep)` and `Post.permalink(lang, absolute, extension, query)` must agree with the site's path handlers.

`link`, `abs_link`, and `rel_link` must generate URLs using the configured site URL, base path, language, and URL style. Relative links must be computed from the source page to the target page. Encoded links must preserve valid URL characters and escape unsafe characters.

Taxonomy plugins classify posts into tags, categories, authors, and configured classification sets. Classification pages, feeds, and paths must reflect the same post membership as the post metadata. Sorting taxonomies must use the configured sort policy and language-specific friendly names.

## Compilation, Rendering, And Generated Files

A compiler maps a source file to an output fragment or document. `get_compiler(source_name)` must select a compiler based on the source extension and configured compiler registry. If no compiler supports the source, the site must report an unsupported-source error.

Markdown and reStructuredText compilers must read source text, split metadata when the format supports it, render content to HTML fragments, and report syntax or dependency errors as build failures. HTML source must pass through as HTML content while still participating in metadata and path behavior.

`render_template(template_name, output_name, context, url_type, is_fragment)` must render a template with the supplied context and write or return output according to the call. Missing templates or render failures must fail the build or rendering operation. Template variables must include site, post, navigation, translations, and configured values when those are documented for templates.

`generic_renderer`, `generic_page_renderer`, `generic_post_list_renderer`, RSS/Atom renderers, and sitemap tasks must write files under the configured output directory. The generated files must be internally consistent: links point to generated paths, feeds include feed-eligible posts, and sitemap entries correspond to generated public pages.

## Shortcodes And Filters

Shortcodes are named functions embedded in source text. Registering a shortcode name must make it available to later shortcode application. Applying shortcodes must replace each shortcode invocation with the registered function result using the active site, filename, language, and extra context. Unknown shortcodes or malformed syntax must raise `ParsingError` or report a build error when exceptions are enabled.

Filters are named transformations applied to generated output files. Registering a filter must make it available by name in configuration and task generation. Unknown filters must fail when a task attempts to use them.

## Plugin And Task Contracts

Plugins must receive the active site before they are used. A `Command` plugin must expose command-line behavior through `execute(options, args)`. A `Task` or `LateTask` plugin must yield build tasks with observable targets, file dependencies, and actions. A `PageCompiler` must compile source files and report supported extensions. A `MetadataExtractor` must extract metadata from source text, filenames, or sidecar files. A `Taxonomy` must classify posts and provide paths and contexts for classification pages.

Task generation must be deterministic for the same configuration and content state. Tasks that write generated files must declare those files as targets. A task that cannot satisfy its dependencies must fail rather than silently skipping required output.

## Error Semantics

Loading an invalid configuration file must return a non-zero CLI status and must not create a successful site object.

Building without a required configuration file must fail for commands that require an existing project. Commands documented as configuration-free, including `init`, `help`, `version`, and import commands, must not require `conf.py`.

Unknown CLI commands and invalid command options must return non-zero status. `help` and `version` must return status `0`.

Unknown path handler kinds, unsupported source extensions, missing compilers, missing templates, malformed metadata, malformed shortcodes, and invalid import input must raise an exception or return a non-zero command result appropriate to the calling surface.

Attempts to overwrite existing content with `new_post` or `new_page` must fail unless an explicit overwrite behavior is selected by the command.

## Cross-View Invariants

1. A site initialized by `nikola init` must contain configuration and content folders that a later `nikola build` reads from the same project directory.
2. A source file created by `nikola new_post` or `nikola new_page` must be discoverable as a `Post` on the next scan using the same configuration.
3. A `Post.destination_path()` value must match the generated file path written during a build for the same post, language, extension, and URL style.
4. A `Post.permalink()` value must match the URL produced by the site's path/link handlers for the same post and language.
5. Tags, categories, authors, and other taxonomy pages must contain the same posts that the corresponding post metadata assigns to those classifications.
6. RSS and Atom feeds must include feed-eligible published posts and must exclude draft, private, and not-yet-published scheduled posts.
7. A template variable documented for generated pages must have the same value whether it is read by a template plugin or by a renderer context for the same page.
8. A registered shortcode must produce the same replacement text when applied through the site object and when applied through the standalone shortcode API with the same registry and context.
9. A generated sitemap entry must correspond to a generated public output file and public URL.
10. A compiler selected for a source file must be the compiler that reads that file during a build.

## Representative Workflows

Create and build a local site:

```python
from pathlib import Path
from nikola.__main__ import main

root = Path("example-site")
assert main(["init", "--quiet", str(root)]) == 0
assert main(["--conf=" + str(root / "conf.py"), "new_post", "-t", "Hello"]) == 0
assert main(["--conf=" + str(root / "conf.py"), "build"]) == 0
assert (root / "output").exists()
```

Register and apply a shortcode:

```python
from nikola import Nikola

site = Nikola(SITE_URL="https://example.invalid/", TRANSLATIONS={"en": ""}, DEFAULT_LANG="en")
site.register_shortcode("hello", lambda site, data, lang, post=None: "Hello")
assert site.apply_shortcodes("{{% hello %}}", "post.rst", "en", {}) == "Hello"
```

Resolve a post path:

```python
post = site.posts[0]
path = post.destination_path("en")
url = post.permalink("en")
assert path.endswith("index.html") or path.endswith(".html")
assert url
```

## Non-Goals

This specification does not define private helper functions, private attributes, internal task dictionaries, doit internals, cache key formats, plugin manager internals, or exact dependency-graph construction order.

This specification does not define exact theme-specific HTML bytes, whitespace, asset ordering, or template implementation details.

This specification does not define live deployment, GitHub Pages deployment, plugin download/install behavior, external network checks, live HTTP server behavior beyond local command startup, or image-processing algorithms.

This specification does not require every Nikola plugin shipped with the project. It covers the public plugin category contracts and the local site lifecycle plugins listed in Scope.

## Invocation Protocol

The supported console command is `nikola`.

`python -m nikola` is supported when the package provides a module entry point equivalent to the console command. Directly calling `nikola.__main__.main(args)` is supported as the Python invocation surface.

Exit codes:

| Invocation outcome | Exit code |
| --- | --- |
| help or version succeeds | 0 |
| a local command completes successfully | 0 |
| invalid command, invalid option, malformed configuration, missing required file, unsupported source, or build failure | non-zero |

## Environment

The implementation is permitted to use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

Nikola's normal local workflows use filesystem access and Python packages for rendering, feeds, dates, templates, localization, images, and markup parsing. Local checks are permitted to use temporary project directories. Network services, deploy targets, and plugin downloads are outside this specification.

## Evaluation Notes

Assessment focuses on public behavior through the `nikola` command, package imports, public site/post/plugin objects, and generated local files. Checks exercise initialization, configuration loading, content creation, metadata extraction, path/permalink/taxonomy projections, compiler selection, shortcode expansion, build output consistency, feeds, sitemaps, command exit status, and cross-view consistency between Python objects and generated files.

Private helpers, exact template bytes, internal task dictionaries, dependency-cache internals, and undocumented support fixtures are not assessed. Correct behavior is measured by public return values, exceptions or exit status, generated files, and durable project state.
