# MkDocs Specification

## Product Overview

MkDocs builds static project documentation from Markdown source files and a YAML configuration file. A MkDocs project normally contains a `mkdocs.yml` or `mkdocs.yaml` file beside a documentation directory, usually `docs/`. The `mkdocs` command can create a starter project, serve a live-reloading preview, build static output into a site directory, deploy that output to GitHub Pages, and report inferred Python packages required by configured plugins.

MkDocs exposes a Python API for configuration loading, programmatic builds, plugin development, theme development, navigation/page/file objects, search indexing, and template helpers. Public behavior is centered on the same project model: configuration values, Markdown pages, non-Markdown assets, theme templates, plugin events, and generated site files.

## Scope

This specification covers:

- Creating, loading, validating, and overriding MkDocs project configuration.
- The `mkdocs` console command and the public behavior of `new`, `serve`, `build`, `gh-deploy`, and `get-deps`.
- Static site construction from Markdown pages, media files, static templates, extra templates, themes, and the default search plugin.
- Public Python import paths used by plugin authors, theme authors, and programmatic callers.
- Public data objects for files, pages, navigation, table of contents entries, themes, templates, plugins, localization, exceptions, and documented utility helpers.
- User-visible warning, strict-mode, abort, and plugin error behavior.
- Cross-view relationships among config, source files, generated URLs, pages, navigation, templates, search output, and plugin events.

## Installable Surface

MkDocs is installed as the Python package `mkdocs` and provides the console script:

```text
mkdocs
```

The package exposes:

```python
import mkdocs
mkdocs.__version__
```

Public command line interface:

```text
mkdocs [GLOBAL OPTIONS] COMMAND [COMMAND OPTIONS]
mkdocs new PROJECT_DIRECTORY
mkdocs serve [OPTIONS]
mkdocs build [OPTIONS]
mkdocs gh-deploy [OPTIONS]
mkdocs get-deps [OPTIONS]
```

Global options are:

```text
-h, --help
-V, --version
-q, --quiet
-v, --verbose
--color / --no-color
```

Shared configuration options for commands that load a project are:

```text
-f, --config-file FILE
-s, --strict / --no-strict
-t, --theme THEME_NAME
--use-directory-urls / --no-directory-urls
```

The main public Python import paths are `mkdocs.config.load_config`; `build` and `site_directory_contains_stale_files` from `mkdocs.commands.build`; `get_context` from `mkdocs.utils.templates`; and the exception classes `MkDocsException`, `Abort`, `ConfigurationError`, `BuildError`, and `PluginError` from `mkdocs.exceptions`.

Configuration schemas use `Config` from `mkdocs.config.base` and the documented validators in `mkdocs.config.config_options`. Plugin authors import `BasePlugin`, `CombinedEvent`, `PluginCollection`, `event_priority`, and `get_plugin_logger` from `mkdocs.plugins`.

The documented site model is imported through `File`, `Files`, `InclusionLevel`, and `get_files` from `mkdocs.structure.files`; `Page` from `mkdocs.structure.pages`; `Navigation`, `Section`, `Link`, and `get_navigation` from `mkdocs.structure.nav`; and `AnchorLink`, `TableOfContents`, and `get_toc` from `mkdocs.structure.toc`. Themes use `Theme` from `mkdocs.theme`. The date, file, URL, path, theme-discovery, and logging helpers listed under Utilities are public names in `mkdocs.utils`, except `DuplicateFilter` and `CountHandler`, which are imported from `mkdocs.utils.log`.

The built-in theme entry points are named `mkdocs` and `readthedocs`. The built-in plugin entry point is named `search`.

## Public API

### Command Line

`mkdocs new PROJECT_DIRECTORY` creates a project directory if needed, writes `mkdocs.yml` with `site_name: My Docs`, and writes `docs/index.md` containing the starter documentation. If the target configuration file already exists, the command leaves the project in place and reports that it already exists. If `docs/index.md` already exists, it is not overwritten.

`mkdocs build` loads configuration and writes the static site to `site_dir`.

```text
mkdocs build [-c|--clean / --dirty] [-d|--site-dir PATH] [shared config options]
```

Clean mode is the default and removes existing non-hidden contents of `site_dir` before writing. Dirty mode skips unchanged files and warns that navigation and links may be inaccurate. `--site-dir` overrides the configured output directory for that invocation.

`mkdocs serve` builds into a temporary site directory and starts a development server.

```text
mkdocs serve [-a|--dev-addr IP:PORT] [-o|--open] [--no-livereload] [--dirty] [-c|--clean] [--watch-theme] [-w|--watch PATH] [shared config options]
```

By default it uses live reload, watches the docs directory and config file, serves at `127.0.0.1:8000`, and mounts under the path component of `site_url` when one is configured. `--clean` makes the preview build behave like a pure `mkdocs build`, without serve-only draft behavior. Extra `--watch` paths are added to the live reload watcher.

`mkdocs gh-deploy` first performs a build and then publishes `site_dir` to a GitHub Pages branch using the configured or overridden remote settings.

```text
mkdocs gh-deploy [-c|--clean / --dirty] [-m|--message TEXT] [-b|--remote-branch BRANCH] [-r|--remote-name NAME] [--force] [--no-history] [--ignore-version] [--shell] [-d|--site-dir PATH] [shared config options]
```

If no message is provided, the deployment message includes the current git short SHA and the MkDocs version. `{sha}` and `{version}` are valid expansions in a custom message. Deployment checks the previous deployment version unless `--ignore-version` is passed. If a `CNAME` file exists in the built site, the reported Pages URL is based on that host; otherwise a GitHub remote URL is used when recognizable.

`mkdocs get-deps` reads configuration and prints required PyPI packages inferred from configured MkDocs-related projects.

```text
mkdocs get-deps [-f|--config-file FILE] [-p|--projects-file PATH_OR_URL] [-v|--verbose]
```

### Configuration Loading

`mkdocs.config.load_config(config_file=None, *, config_file_path=None, **kwargs)` returns a validated `MkDocsConfig`. If `config_file` is `None`, MkDocs looks for `mkdocs.yml` and then `mkdocs.yaml` in the current working directory. A string is opened as a path. An open file object is read from the beginning when possible. The special file name `-` is supported by the command line and means standard input.

Configuration is loaded in this order:

1. Start with the `MkDocsConfig` defaults.
2. Load YAML from the selected configuration file.
3. Apply keyword overrides whose values are not `None`.
4. Validate the result.

Unknown config keys are warnings. Validation errors are logged and raise `mkdocs.exceptions.Abort`. When `strict` is true, configuration warnings also raise `Abort`.

The YAML loader supports:

- `!ENV NAME` and `!ENV [NAME, FALLBACK_NAME, default_value]` for environment variables.
- `!relative`, `!relative $docs_dir`, and `!relative $config_dir` path placeholders, intended for contexts such as Markdown extension options.
- An uppercase `INHERIT` key whose value is a path relative to the current config file; the parent YAML is loaded first and deep-merged with the child. Mapping values are merged, while non-mapping values, including lists, are replaced by the child.

The minimum user configuration is `site_name`. Core configuration keys include:

```text
site_name, site_url, site_description, site_author, copyright
repo_url, repo_name, edit_uri, edit_uri_template
nav, exclude_docs, draft_docs, not_in_nav, validation
theme, docs_dir, site_dir, use_directory_urls, strict, dev_addr
extra_css, extra_javascript, extra_templates, markdown_extensions
plugins, hooks, watch, remote_branch, remote_name, extra
```

Path-based options are resolved relative to the directory containing the active configuration file unless an absolute path is supplied. `docs_dir` must exist by default. `site_dir` and `docs_dir` must not contain one another.

`Config` is the base class for class-based configuration schemas. Subclasses define config options as class attributes. A `Config` instance behaves like a dictionary and also supports attribute access for schema options. `Config.validate()` returns `(errors, warnings)`, where each entry carries the config key and message or exception. Calling `Config` directly creates a `LegacyConfig` compatibility instance.

`config_options` provides validators for plugin and MkDocs schemas:

```python
SubConfig(ConfigSubclass)
PropagatingSubConfig(ConfigSubclass)
ListOfItems(option)
DictOfItems(option)
Type(type_, length=None, default=..., required=...)
Choice(choices, default=...)
Deprecated(moved_to=None, message=None, removed=False, option_type=None)
IpAddress(default=...)
URL(default=..., is_dir=False)
Optional(option)
FilesystemObject(exists=False)
Dir(exists=False)
File(exists=False)
ListOfPaths(default=[])
Theme(default='mkdocs')
Nav()
Private()
ExtraScript()
MarkdownExtensions(builtins=None, configkey='mdx_configs', default=[])
Plugins(theme_key='theme', default=['search'])
Hooks('plugins')
PathSpec()
```

The validators raise `ValidationError` for invalid values. `Type` requires the Python type and optional length. `Choice` accepts only one of the configured values. `Optional` allows `None` for an option that otherwise has no default. `PathSpec` accepts a multiline gitignore-style string. `ExtraScript` accepts either a string path or a mapping with `path`, `type`, `defer`, and `async` fields; `.mjs` script paths default to `type: module`.

### Project Configuration Semantics

`nav` may be omitted. When omitted, MkDocs discovers Markdown pages under `docs_dir`, sorts them alphanumerically, places index pages first within each directory, nests them by path, and excludes pages marked as not intended for navigation. When `nav` is supplied, it is a list of strings or one-item mappings. Strings are paths or links. Mappings assign titles or define sections. Sections contain children and do not have URLs of their own.

Markdown source extensions recognized as documentation pages are:

```text
.markdown, .mdown, .mkdn, .mkd, .md
```

`index.md` and `README.md` both map to `index.html`. If both exist in the same directory, `index.md` wins and the `README.md` source is ignored for the built site.

`use_directory_urls: true` maps `foo.md` to `foo/index.html` and the URL `foo/`; `index.md` maps to `index.html` and the URL `./`. `use_directory_urls: false` maps `foo.md` to `foo.html`. Non-Markdown files keep their original destination path.

`exclude_docs`, `draft_docs`, and `not_in_nav` use gitignore-style patterns relative to `docs_dir`. Dot files and the top-level `templates/` directory are excluded by default. Excluded files are not part of normal builds. Draft files are available during `mkdocs serve` and marked as draft in the served page, but are excluded from normal `mkdocs build`. Files marked `not_in_nav` are built but do not produce omitted-from-navigation warnings.

`validation` controls the logging level for navigation and Markdown link diagnostics. Supported levels are `warn`, `info`, and `ignore`; absolute-link settings also accept `relative_to_docs`. With `relative_to_docs`, Markdown or nav links beginning with `/` are resolved relative to `docs_dir` and then converted to relative output URLs.

`markdown_extensions` always includes MkDocs' built-in Markdown extensions `toc`, `tables`, and `fenced_code`; user extensions are appended with duplicates removed while preserving order. Extension config may be supplied in list form or mapping form, and per-extension config is stored in `mdx_configs`.

`plugins` defaults to `['search']`. If the user defines `plugins`, the default list is replaced; include `search` explicitly to keep the built-in search plugin. Plugin config may be list form or mapping form. A generic boolean `enabled` option is honored for plugins that do not define their own `enabled` option.

`hooks` is a list of Python files relative to the configuration file. Each hook file is imported as a module and registered as a plugin-like object. Hook files can define standard `on_*` plugin event functions. During import, the hook file's directory is temporarily available on `sys.path`.

`site_url` controls canonical URLs and the mount path used by `mkdocs serve`. An empty `site_url` is valid and is used for `file://`-friendly builds together with `use_directory_urls: false` and search disabled.

`repo_url`, `repo_name`, `edit_uri`, and `edit_uri_template` control repository and edit links. Known GitHub, GitLab, and Bitbucket repository URLs derive default repository names and edit URI styles. `edit_uri_template` and `edit_uri` are mutually exclusive; templates support `{path}`, `{path_noext}`, and `{path!q}` percent encoding.

### Build API

`build(config, *, serve_url=None, dirty=False)` performs a complete site build using a validated configuration. It gathers files, applies plugin events, constructs navigation, reads and renders Markdown pages, renders templates, copies static files, writes output, validates anchor links, and runs post-build events. The contract is the generated site and plugin-visible event data, not the internal implementation sequence.

`get_context(nav, files, config, page=None, base_url='')` returns a `TemplateContext` with:

```text
nav, pages, base_url, extra_css, extra_javascript, mkdocs_version, build_date_utc, config, page
```

When `page` is supplied, `base_url` is computed relative to that page. `extra_css` and `extra_javascript` in the returned context are URL-normalized for the page or base URL, but theme authors should prefer `config.extra_css` and `config.extra_javascript` together with the provided filters.

`site_directory_contains_stale_files(site_directory)` returns true when the directory exists and contains at least one entry.

## Behavioral Sections

### Source Files and Generated Files

`File(path, src_dir, dest_dir, use_directory_urls, *, dest_uri=None, inclusion=InclusionLevel.UNDEFINED)` represents how one source-like item maps into the output site. `src_uri` is always a slash-separated path relative to the source directory. `src_path` is the OS-native view of `src_uri`. `dest_uri` is the slash-separated destination path relative to `site_dir`; `dest_path` is the OS-native view.

`File.generated(config, src_uri, *, content=..., inclusion=...)` creates a virtual file backed by in-memory text or bytes. `File.generated(config, src_uri, *, abs_src_path=..., inclusion=...)` creates a virtual file backed by a physical file outside `docs_dir`. Exactly one of `content` and `abs_src_path` must be provided. Generated files pretend to originate at `src_uri` under `docs_dir`, use `config.site_dir` and `config.use_directory_urls`, and set `generated_by` to the active plugin key or `'<unknown>'`.

`File.content_bytes` and `File.content_string` are the public way to read or replace file contents. Real files are read from `abs_src_path`; in-memory generated files read from stored content. `content_string` uses UTF-8 with BOM support and strict decoding. Assigning either property replaces the file content and clears `abs_src_path`.

`File.edit_uri` defaults to `src_uri` for real source files and to `None` for generated files. Plugins may overwrite it to control edit links.

`File.url_relative_to(other)` returns this file's URL relative to another `File` or URL string. `is_documentation_page()`, `is_static_page()`, `is_media_file()`, `is_javascript()`, and `is_css()` classify the file by source extension.

`Files(files)` is a collection keyed by `File.src_uri`. It is iterable, has length, supports `get_file_from_path(path)`, and provides `src_uris`. `append(file)` adds or replaces a file by `src_uri`; replacing an existing file emits a deprecation warning unless the caller removes it first. `remove(file)` removes by `src_uri` or raises `ValueError` when absent. `documentation_pages()`, `static_pages()`, `media_files()`, `javascript_files()`, and `css_files()` return filtered sequences. `copy_static_files(dirty=False, *, inclusion=InclusionLevel.is_included)` copies non-documentation files that satisfy the inclusion predicate.

`InclusionLevel` values are `EXCLUDED`, `DRAFT`, `NOT_IN_NAV`, `UNDEFINED`, and `INCLUDED`. The predicate methods classify whether a file is built, visible during serve, visible in nav, or excluded.

### Pages, Metadata, Links, and Table of Contents

`Page(title, file, config)` associates a `File` with a rendered documentation page. It exposes:

```text
title, markdown, content, toc, meta, url, file, abs_url, canonical_url, edit_url
is_homepage, previous_page, next_page, parent, children, active
is_section, is_page, is_link
present_anchor_ids, links_to_anchors
```

`Page.read_source(config)` obtains the source from `on_page_read_source` when a plugin returns a string; otherwise it reads `page.file.content_string`. It separates document metadata from Markdown body. YAML front matter must begin on the first line with `---` and end with `---` or `...`; it is accepted only when it parses to a mapping. Without YAML delimiters, MultiMarkdown-style metadata is read from leading `key: value` lines, lowercases keys, folds indented continuation lines, and ends at the first blank line or non-metadata line.

`Page.title` is resolved in this order:

1. Title passed when the page was created from explicit `nav`.
2. `title` metadata in the page source.
3. The first rendered level-1 heading.
4. Before render, a first-line Markdown `# Heading` fallback for legacy plugin cases.
5. `Home` for the homepage.
6. The file stem converted by replacing hyphens and underscores with spaces and capitalizing only all-lowercase stems.

`Page.render(config, files)` converts Markdown to HTML using `config.markdown_extensions` and `config.mdx_configs`, populates `content`, `toc`, title-from-render, present anchors, and outbound anchor links. Internal Markdown links to known source files are rewritten to output URLs relative to the current page. Query strings and fragments are preserved. External URLs are left unchanged. Raw HTML links are not rewritten by the Markdown link converter.

`Page.validate_anchor_links(files=..., log_level=...)` logs diagnostics for links to missing anchors when anchor data is available.

`AnchorLink(title, id, level)` represents a table-of-contents item. `url` is `'#' + id`, `level` is zero-based, and `children` contains nested `AnchorLink` objects. `TableOfContents(items)` is iterable, has length, and stringifies by printing its anchor tree. `get_toc(toc_tokens)` converts Python-Markdown toc tokens to a `TableOfContents` and marks the first item active when present.

### Navigation

`get_navigation(files, config)` builds `Navigation(items, pages)` from config and files. `Navigation` is iterable over top-level items, has length, `homepage`, and `pages`. `pages` is the flat list of pages included in navigation order and is the basis for previous/next links.

Navigation items are `Page`, `Section`, or `Link`. A `Section(title, children)` has `is_section=True`, children, no URL, and an `active` property that propagates to ancestors. A `Link(title, url)` represents a nav item that does not resolve to a MkDocs page; `children` is `None`, `active` is always false, and `is_link=True`.

When navigation references a source file, that file gets a `Page`. When documentation files are not referenced by explicit nav, they still receive `Page` objects and are built, but they are not included in `Navigation.pages` and do not get previous/next links. Omitted-page diagnostics respect `not_in_nav` and `validation.nav.omitted_files`.

### Themes and Templates

`Theme(name=None, *, custom_dir=None, static_templates=(), locale=None, **user_config)` is a mutable mapping of theme variables. `name` is the theme entry point name. `custom_dir`, when supplied, is searched before the packaged theme. Packaged themes load `mkdocs_theme.yml`; a theme may extend a parent theme, whose files and defaults are included before the child. MkDocs' own shared templates are always appended at the lowest precedence.

`Theme.dirs` is the ordered list of template/media directories. `Theme.static_templates` is the set of templates that should be rendered as standalone output pages. Theme config values are available through mapping access and in templates through `config.theme`. `Theme.locale` is a parsed locale object.

`Theme.get_env()` returns a Jinja environment using the theme dirs. It registers the `url` and `script_tag` filters and installs available translations for the theme locale.

Template context variables include `config`, `nav`, `base_url`, `mkdocs_version`, `build_date_utc`, `pages`, and `page`. Page templates receive a `Page`; global/static templates receive `page=None`. `base_url` is a relative path to the site root. The `url` filter passes absolute URLs through and normalizes relative URLs against the current page or `base_url`. The `script_tag` filter renders `extra_javascript` entries as `<script>` tags with `src`, optional `type`, `defer`, and `async` attributes.

Theme files that are not templates, Python files, Markdown files, readme files, localization source files, dot files, or theme metadata are copied to the site. Files in `docs_dir` take precedence over theme files with the same path.

### Plugins

Plugins subclass `BasePlugin`. A plugin may define `config_scheme` as a tuple of config option pairs, or define `config_class` as a `Config` subclass, including by subclassing `BasePlugin[MyConfig]`. `load_config(options, config_file_path=None)` validates options and returns `(errors, warnings)`. After loading, `plugin.config` contains the validated config object.

Supported plugin event hooks are:

```python
on_startup(*, command, dirty)
on_shutdown()
on_serve(server, *, config, builder)
on_config(config)
on_pre_build(*, config)
on_files(files, *, config)
on_nav(nav, *, config, files)
on_env(env, *, config, files)
on_post_build(*, config)
on_build_error(*, error)
on_pre_template(template, *, template_name, config)
on_template_context(context, *, template_name, config)
on_post_template(output_content, *, template_name, config)
on_pre_page(page, *, config, files)
on_page_read_source(*, page, config)
on_page_markdown(markdown, *, page, config, files)
on_page_content(html, *, page, config, files)
on_page_context(context, *, page, config, nav)
on_post_page(output, *, page, config)
```

Hooks that receive an item may return a replacement. Returning `None` keeps the current item. `on_post_template` and `on_post_page` may return an empty string to skip writing that template or page. `on_page_read_source` returns a Unicode source string or `None` to use the default file content.

Event categories are one-time, global, template, and page events. `on_startup` and `on_shutdown` run once per command invocation. Global events run once per build. Template events run for each non-page template. Page events run for each included Markdown page.

Plugins run in the order configured, except methods decorated with `event_priority(priority)` are ordered by descending priority within an event. Undecorated methods have priority `0`. `CombinedEvent(method1, method2, ...)` lets one plugin register multiple handlers under one event name; component method names should not start with `on_`.

`PluginCollection` is a mutable mapping of plugin key to plugin instance. Setting a plugin registers its `on_*` methods. `run_event(name, item=None, **kwargs)` runs registered handlers and returns the final item or result. `supports_multiple_instances=True` declares that a plugin can be configured multiple times; otherwise repeated instances warn and are named with ` #2`, ` #3`, and so on.

`get_plugins()` returns installed plugin entry points keyed by plugin name. Third-party plugins may override core plugins; a core plugin entry point does not override an already seen third-party plugin of the same name.

`get_plugin_logger(name)` returns a logger adapter under `mkdocs.plugins.<name>` that prefixes messages with the first component of the plugin name.

### Search

The built-in `search` plugin is active by default unless the user replaces the `plugins` list. It writes `search/search_index.json` under `site_dir`. The index contains page locations, titles, and text; when prebuilding is enabled it may also contain a prebuilt search index.

Search plugin config keys are:

```text
separator: string, default '[\s\-]+'
min_search_length: integer, default 3
lang: string or list of language codes, default theme locale language or en
prebuild_index: false, true, 'node', or 'python', default false
indexing: 'full', 'sections', or 'titles', default 'full'
```

Unsupported search languages fall back to `en`. Some language codes map to supported Lunr language files, such as Ukrainian falling back to Russian. Multiple languages cause the plugin to copy the required Lunr support files into the search output directory. Japanese support includes the tokenizer file used by the bundled search assets.

Theme config may set `include_search_page` to have the plugin build a dedicated `search.html` page, and `search_index_only` to request only the index rather than the bundled client-side search assets. When full assets are enabled, the plugin adds its templates directory and `search/main.js`.

### Exceptions and Error Semantics

`MkDocsException` is the base class for MkDocs user-facing exceptions. `Abort` inherits from both `MkDocsException` and `SystemExit`, exits with code `1`, and displays only the formatted message. `ConfigurationError` is for configuration parsing or validation failures. `BuildError` is for MkDocs build failures and is caught and converted to `Abort`. `PluginError` is a `BuildError` intended for plugin events.

Configuration validation failures raise `Abort("Aborted with a configuration error!")` after logging the failing config key. Strict mode raises `Abort` when warnings were collected. A `BuildError` raised during build triggers `on_build_error`, logs the build error message, and aborts with a BuildError message. Unexpected exceptions also trigger `on_build_error` and then propagate.

Plugin authors should raise `PluginError` for user-facing plugin build failures. Uncaught Python exceptions are allowed to surface with normal tracebacks.

### Utilities

Date helpers use UTC. `get_build_datetime()` returns an aware UTC `datetime`; when `SOURCE_DATE_EPOCH` is set, it returns that epoch timestamp instead of the current time. `get_build_date()` returns `YYYY-MM-DD`. `get_build_timestamp(pages=None)` returns the latest page `update_date` timestamp when pages are supplied, otherwise the current build datetime timestamp.

File helpers:

```python
copy_file(source_path, output_path)
write_file(content: bytes, output_path)
clean_directory(directory)
```

`copy_file` and `write_file` create parent directories. If `copy_file` receives an output path that is a directory, it copies into that directory using the source basename. `clean_directory` removes non-hidden contents while preserving the directory itself and preserving entries whose names begin with `.`.

URL and path helpers:

```python
is_markdown_file(path)
is_error_template(path)
get_relative_url(url, other)
normalize_url(path, page=None, base='')
create_media_urls(path_list, page=None, base='')
dirname_to_title(dirname)
find_or_create_node(branch, key)
nest_paths(paths)
```

`get_relative_url` treats paths as slash-separated URL paths, normalizes `..`, ignores leading slashes, and treats an `other` path with a dotted basename as a file whose directory is the base. It preserves a trailing slash on the destination URL. `normalize_url` leaves fully qualified URLs, network URLs, absolute paths, and anchors unchanged; otherwise it returns a URL relative to the page when a page is supplied, or joined with `base`. Backslashes in URL paths are converted to slashes with a warning.

Theme discovery helpers:

```python
get_themes()
get_theme_names()
get_theme_dir(name)
```

`get_themes()` returns installed theme entry points by name, warns on duplicate third-party names, and raises `ConfigurationError` if a package attempts to provide a theme using a built-in theme name.

Logging helpers:

```python
DuplicateFilter()
CountHandler()
weak_property
```

`DuplicateFilter` suppresses duplicate log record messages. `CountHandler` counts handled records by level and reports sorted `(level_name, count)` pairs. `weak_property` is a read-only descriptor whose computed value can be overwritten on an instance.

Soft-deprecated helpers remain importable where listed, but new code should prefer the non-deprecated alternatives documented above.

## Error Semantics

- Missing default config file (`mkdocs.yml` and `mkdocs.yaml`) raises `ConfigurationError`.
- YAML parse errors raise `ConfigurationError` with a parsing message.
- Missing inherited config files raise `ConfigurationError`.
- Invalid config value types, unknown required values, missing required options, invalid theme names, invalid plugin names, invalid Markdown extensions, invalid path specs, and invalid URLs produce `ValidationError` entries; `load_config` logs them and raises `Abort`.
- Unknown config keys produce warnings; strict mode converts warnings into `Abort`.
- `config_file_path` cannot be set by user config and raises `ValidationError`.
- `docs_dir` and `site_dir` may not contain each other; validation raises `ValidationError`.
- `theme.custom_dir` must exist when supplied; otherwise validation raises `ValidationError`.
- A theme loaded by name must provide `mkdocs_theme.yml`; otherwise theme validation raises `ValidationError`.
- A plugin entry point must exist and load to a `BasePlugin` subclass; otherwise plugin validation raises `ValidationError`.
- Plugin config must be a mapping; invalid plugin options are reported as plugin option validation errors.
- A hook file must exist and import as a Python module; otherwise validation raises `ValidationError`.
- `File.generated()` raises `TypeError` unless exactly one of `content` or `abs_src_path` is provided.
- `Files.remove(file)` raises `ValueError` when the file is not in the collection.
- Reading a missing page source logs the source path and re-raises the I/O error.
- Reading a page source with invalid UTF-8 logs an encoding error and re-raises the decoding error.
- Calling `Page.render()` before `read_source()` raises `RuntimeError`.
- A plugin that assigns `File.page` to a non-`Page` object causes a `BuildError` during navigation.
- A `BuildError` during build triggers `on_build_error` and is converted into `Abort`.
- `gh_deploy` aborts when git is unavailable, when deploying from outside a git work tree, when version checks reject an older MkDocs deployment, or when the underlying GitHub Pages import fails.

## Cross-View Invariants

1. The configuration object, command-line overrides, and generated output agree on `site_dir`: build output is written to the effective `site_dir` after config-file values are overridden by command options.
2. The file collection and page URLs agree on `use_directory_urls`: every Markdown `File.dest_uri`, `File.url`, `Page.url`, rendered internal link, and navigation page URL uses the same directory-URL policy.
3. The navigation view and page view share page objects: a local file referenced in `nav` becomes the same `Page` object available through `File.page`, `Navigation.pages`, template `page`, and previous/next links.
4. Pages omitted from explicit `nav` are still rendered into the site unless excluded, but they are absent from `Navigation.pages` and have no previous or next page.
5. Exclusion state is consistent across file discovery, serve, build, navigation, and copying: excluded files are omitted from builds, draft files are visible only in serve previews, and `not_in_nav` files build without omitted-nav warnings.
6. Page title selection is consistent across templates, navigation labels, search entries, and generated page context: explicit nav titles outrank metadata, rendered H1 headings, homepage fallback, and filename fallback.
7. Repository edit links are derived from the same `repo_url`, `edit_uri` or `edit_uri_template`, and `File.edit_uri` values used by the `Page.edit_url` object exposed to themes.
8. Markdown metadata is removed from `Page.markdown` before plugin page-markdown hooks and rendering, while parsed metadata is exposed as `Page.meta` to plugins and templates.
9. Template `base_url`, the `url` filter, `Page.url`, and rewritten Markdown links all describe relative paths from the same current page or static template location.
10. The default search plugin indexes the rendered set of pages and writes its index under the same `site_dir` used by the build; disabling or replacing the `plugins` list removes that default behavior unless `search` is explicitly included.
11. Plugin event return values are the only public way for plugins to replace config, files, navigation, environment, page content, template context, rendered templates, or rendered pages; returning `None` preserves the current value.
12. Strict mode treats user-visible warnings consistently across config loading and site building: warnings that would otherwise be logged become abort conditions.

## Representative Workflow(s)

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

## Non-Goals

- Reproducing MkDocs' internal helper names, private classes, private attributes, or implementation call graph.
- Requiring a particular third-party dependency version beyond the behavior described here.
- Implementing a real network deployment service beyond the public `gh-deploy` behavior and error handling.
- Matching byte-for-byte HTML formatting that is not user-visible or documented by MkDocs.
- Supporting undocumented test helpers, upstream test fixtures, or private modules.
- Recreating every bundled static asset exactly; the public contract is that built-in themes and search assets are available and copied/rendered according to the documented behavior.
- Guaranteeing compatibility with arbitrary third-party themes, plugins, or Markdown extensions beyond the public entry point, config, hook, and event contracts.
- Preserving soft-deprecated internals beyond their documented importability and stated behavior.

## Invocation Protocol

The `mkdocs` console script and `python -m mkdocs` are supported and expose the same global options and commands. `--help` and `--version` exit with status `0`. A successful `new`, `build`, or `get-deps` command exits with status `0`; invalid command arguments, configuration failures, and build failures exit nonzero. `serve` remains active until interrupted after its initial build and is not required to terminate on its own.

## Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment. Site builds and deployment dry runs operate on local temporary projects; network publication is not required.

## Evaluation Notes

Assessment exercises command workflows, public APIs, configuration, local site builds, plugins and hooks, themes and templates, search output, navigation and page objects, links, metadata, errors, and documented utilities. It checks observable outputs, returned objects, public exception classes, and cross-view relationships without depending on private modules, private attributes, source layout, internal call order, or hidden fixture shapes.
