# beets Specification

## Product Overview

beets is a music library manager. It catalogs audio files in a persistent library database, keeps track of albums and individual tracks, formats paths from metadata, reads and writes media tags, and exposes the same library through a Python API, the `beet` command-line program, configuration files, and plugins.

The central fact in a beets installation is a library: a database of `Item` objects for tracks and `Album` objects for groups of tracks. File paths, command output, media tags, and plugin-provided views are projections of that library state.

## Scope

This specification covers the public behavior of:

- the installable `beets` package and the `beet` command-line entry point;
- `beets.config`, YAML configuration loading, command-line configuration overlays, and plugin selection;
- the `beets.library` and `beets.dbcore` public database API for libraries, models, results, queries, and sorts;
- item and album metadata access, persistence, album inheritance, media-file synchronization, moves/copies/links, album art placement, and removal side effects;
- the query language used by the Python API and CLI commands;
- path template syntax, path-format selection, built-in template functions, replacement rules, and plugin template extensions;
- built-in CLI commands for importing, listing, modifying, moving, updating, writing, removing, showing fields, showing stats, showing configuration, version/help, and completion;
- the public plugin extension surface for loading plugins, adding commands, registering template fields/functions, declaring flexible field types, adding media fields, and receiving events.

## Installable Surface

Install the package as `beets`. The distribution provides a console script:

```text
beet = beets.ui:main
```

Public imports include:

```python
import beets
from beets import config
from beets.library import (
    Album,
    AnyLibModel,
    FileOperationError,
    Item,
    LibModel,
    Library,
    ReadError,
    WriteError,
    parse_query_parts,
    parse_query_string,
)
from beets.dbcore import (
    AndQuery,
    Database,
    FieldQuery,
    Index,
    InvalidQueryError,
    MatchQuery,
    Model,
    OrQuery,
    Query,
    Results,
    Type,
    parse_sorted_query,
    query_from_strings,
    sort_from_strings,
)
from beets.plugins import BeetsPlugin
from beets.ui import Subcommand, main
```

The `beets.importer` and `beets.autotag` packages expose importer sessions, import tasks, metadata information objects, match objects, distance helpers, and tagging helpers for plugins and advanced integrations. The core behavior specified here treats those objects as public extension points, but it does not define the full MusicBrainz matching algorithm or provider-specific match scoring.

## Public API

### Configuration

`beets.config` is a lazy configuration object for the `beets` application. It reads defaults, the user configuration, and any YAML files named in the `include` setting. Included filenames are resolved as configuration filenames, and unreadable included files report a configuration import failure.

The user configuration file is named `config.yaml`. `BEETSDIR` points beets at a configuration directory and also affects where relative auxiliary paths, including the default library database, are resolved. The global `--config FILE` option reads an additional YAML file and merges it as an overlay whose values override the base configuration without replacing unrelated options.

Important configuration keys include:

- `library`: path to the library database, defaulting to `library.db` alongside the configuration file.
- `directory`: library root for imported or moved files, defaulting to `Music` in the user's home directory.
- `plugins`: a space-separated string or YAML list of plugin names to load.
- `pluginpath`: one or more directories that extend the `beetsplug` namespace for plugin discovery.
- `include`: extra configuration files to merge.
- `replace`, `path_sep_replace`, `asciify_paths`, `max_filename_length`: filename legalization and transliteration rules.
- `paths`: path-format templates and query-conditioned path formats.
- `format_item`, `format_album`: default display templates for items and albums.
- `sort_item`, `sort_album`, `sort_case_insensitive`: default ordering for library queries.
- `import.write`, `import.copy`, `import.move`, `import.link`, `import.hardlink`, `import.reflink`, `import.resume`, `import.incremental`, `import.quiet`, `import.quiet_fallback`, `import.timid`: defaults for the import command.
- `id3v23`: whether MP3 tags are written as ID3v2.3 instead of ID3v2.4.

### Library and Models

```python
Library(path="library.blb", directory=None, set_music_dir=True)
```

`Library` represents a database of songs and albums. `path` selects the database file. `directory` selects the library root for path generation and file organization; if omitted, beets uses the platform music directory. When `set_music_dir` is true, path conversion context uses this library root.

```python
Library.add(obj) -> int
Library.add_album(items) -> Album
Library.items(query=None, sort=None) -> Results[Item]
Library.albums(query=None, sort=None) -> Results[Album]
Library.get_item(id_: int) -> Item | None
Library.get_album(item_or_id: Item | int) -> Album | None
Library.transaction()
```

`Library.add` accepts an `Item` or `Album`, stores it, associates it with the library, and returns its new id. `Library.add_album` requires at least one item, creates an album from album-level metadata on the first item, adds unstored items as needed, assigns all items to the album, and returns the new `Album`.

`Library.items` and `Library.albums` accept `None`, a query string, a list or tuple of query parts, or a `Query` object. String and list queries are parsed with beets query syntax. Sort terms embedded in the parsed query override an explicit `sort` argument. When no explicit sort is supplied, item results use `sort_item` and album results use `sort_album`.

`Item`, `Album`, and `LibModel` behave like mutable mappings as well as attribute containers. Metadata can be read and written with either `item["artist"]` or `item.artist`. Fixed fields use typed conversion; unknown fields are flexible attributes. `keys(computed=False)` returns available fields, and `get`, `update`, `items`, iteration, containment, and formatting follow the model mapping behavior.

`Item` represents a track or singleton. `Album` represents an album row plus the items associated with it. An item with no `album_id` is a singleton. `Item.get_album()` returns the associated album or `None`. `Album.items()` returns the album's items as library query results.

Items fall back to album fields when an item lookup does not find a key locally and the item has an associated album. `Item.keys(with_album=True)` includes album-level fields; `Item.get(..., with_album=False)` skips album fallback.

```python
LibModel.store(fields=None)
LibModel.load()
LibModel.remove()
LibModel.add(lib=None)
LibModel.formatted(for_path=False)
LibModel.evaluate_template(template, for_path=False)
LibModel.set_parse(key, string)
```

Storing writes dirty fields to the database. Loading refreshes the object from the database. Removing deletes the database row. Adding inserts a new row. Formatting uses the model's configured display template when no format string is supplied.

`Album.store(fields=None, inherit=True)` persists album metadata. When `inherit` is true, changed album fields that are inheritable are applied to every item on the album, and changed flexible album attributes are also propagated or removed from the items. The album `id` and art path are not inherited.

`Results` is lazy and repeatable. Iterating a result set constructs model objects from database rows and caches constructed objects. `len(results)` returns the number of matching objects, applying slow query filtering if needed. `bool(results)` is true when at least one object matches. `results[n]` returns the nth matching object or raises `IndexError`. `results.get()` returns the first matching object or `None`.

### Query Objects

`Query` objects have two public matching forms:

```python
query.clause() -> tuple[str | None, Sequence[Any]]
query.match(model) -> bool
query.field_names -> set[str]
```

`clause()` returns an SQL `WHERE` clause and substitution values when the query can run in SQLite. Returning `(None, ())` means the query must be applied in Python with `match()`. `FieldQuery(field_name, pattern, fast=True)` searches one field; when `fast` is false, the query intentionally falls back to Python matching. `MatchQuery` performs exact field equality and treats list-valued fields as matching when the pattern is one of the values. `AndQuery` and `OrQuery` contain subqueries, support sequence operations, and match all or any subquery respectively. The `&` operator combines two queries into an `AndQuery`.

```python
parse_query_parts(parts, model_cls) -> tuple[Query, Sort]
parse_query_string(s, model_cls) -> tuple[Query, Sort]
query_from_strings(query_cls, model_cls, prefixes, query_parts) -> Query
sort_from_strings(model_cls, sort_parts, case_insensitive=True) -> Sort
parse_sorted_query(model_cls, parts, prefixes={}, case_insensitive=True) -> tuple[Query, Sort]
```

`parse_query_string` splits with shell-like quoting. `parse_query_parts` adds beets query prefixes and plugin query prefixes, recognizes existing path-like query parts as path queries, and uses `sort_case_insensitive` for generated sort objects.

### File and Tag Operations

```python
Item.from_path(path) -> Item
Item.read(read_path=None)
Item.write(path=None, tags=None, id3v23=None)
Item.try_write(*args, **kwargs) -> bool
Item.try_sync(write, move, with_album=True)
Item.destination(relative_to_libdir=False, basedir=None, path_formats=None) -> bytes
Item.move(operation=MoveOperation.MOVE, basedir=None, with_album=True, store=True)
Item.move_file(dest, operation=MoveOperation.MOVE)
Item.remove(delete=False, with_album=True)
```

`Item.from_path` creates an item by reading metadata from an audio file, sets the item path, and records the file's current modification time. `Item.read` reads all readable media fields from the file into the item and updates the database mtime when reading the item's own path. `Item.write` writes the item's media fields, plus any extra `tags`, to the target media file and refreshes the item mtime after a successful write. `id3v23` overrides the global setting for that write only.

Changing a media-backed item field resets the item's database mtime to `0`, except when an explicit `mtime` value is supplied through `update`. This preserves the invariant that out-of-sync database metadata is detectable by comparing database and disk mtimes.

`Item.move` computes the item destination from configured path formats, creates directories as needed, performs the selected operation, updates `item.path`, stores the item by default, and moves album art when appropriate. Move operations prune empty source directories under the library root, respecting configured clutter files. If the source file is missing, the move is skipped and the item path is not changed.

`Album.move(operation=MoveOperation.MOVE, basedir=None, store=True)` moves every item in the album and then moves album art into the item directory. `Album.move_art` keeps art with album items for move, copy, link, hardlink, and reflink operations. `Album.set_art(path, copy=True)` places an image at the album art destination, replaces old art, updates `artpath`, and emits the `art_set` event.

`Item.remove(delete=False, with_album=True)` removes the item from the database, emits an item-removed event, deletes the file when requested, and prunes empty directories. If `with_album` is true and the item was the last track on its album, the album is removed too. `Album.remove(delete=False, with_items=True)` removes the album, emits an album-removed event, optionally deletes album art, and optionally removes all associated items.

## Query Language

The CLI and Python query parsers use the same query language.

Unadorned keywords search across a default set of item fields: title, artist, album, album artist, genre, and comments. Multiple query parts are implicitly combined with AND. A comma followed by a separate query part creates OR groups; `foo,bar` is one keyword, while `foo , bar` or `foo, bar` creates separate OR branches.

`field:value` restricts matching to a field. Album queries may refer to item fields and item queries may refer to album fields where the model relationship makes that meaningful. Multi-valued fields such as `artists`, `albumartists`, `genres`, `remixers`, `lyricists`, `composers`, and `arrangers` can be queried by regular expression to match an individual value.

Ordinary field queries perform substring matching. Exact matching uses `field:=value` for case-sensitive exact matches and `field:=~value` for case-insensitive exact matches. Prefixing an unfielded query with `=` or `=~` performs the same exact matching across all default search fields.

Regular expressions use `field::pattern`; an unfielded regex uses `:pattern`. Regular expressions are Python regular expressions and are case-sensitive.

Numeric ranges use `..`: `field:4..7`, `field:4..`, and `field:..7`. The `length` field accepts minute-and-second strings such as `4:30`.

Date fields such as `added` and `mtime` accept years, months, days, optional times, ranges, and relative dates. A date can be `YYYY`, `YYYY-MM`, or `YYYY-MM-DD`. A time can follow a space, `T`, or `t`, with hour, optional minute, and optional second. Relative dates use an optional sign, a number, and one of `d`, `w`, `m`, or `y`; months are 30 days and years are 365 days.

`^term` and `-term` negate a query term. On the command line, use `--` before a query term that begins with `-` when it would otherwise be parsed as an option.

`path:VALUE` matches items already in the library whose paths are recursively under a directory or equal to a file. Absolute paths under the library directory and paths relative to the library root are accepted. A query part containing the platform path separator is treated as a path query when the path exists.

`has_cover_art:true` and `has_cover_art:false` query the actual audio file for embedded images.

Sort terms are `field+` for ascending and `field-` for descending. Multiple sort terms are applied in the order given. Sorting by `artist` or `albumartist` uses the corresponding sort field when available and falls back to the ordinary field. Lexicographic sorts are case-insensitive by default unless configured otherwise. For ascending sorts on missing flexible or plugin fields, missing values appear at the beginning.

## Path Formats and Templates

Path formats are templates from the `paths` configuration section. The filename extension is added automatically. The default formats are:

```yaml
paths:
  default: $albumartist/$album%aunique{}/$track $title
  singleton: Non-Album/$artist/$title
  comp: Compilations/$album%aunique{}/$track $title
```

`default` is used only when no other configured path condition matches. `singleton` is shorthand for `singleton:true`, and `comp` is shorthand for `comp:true`. Other `paths` keys may be beets queries; they are tested in configuration order, and the first matching query selects the format. Queries on multi-valued fields match each individual value.

Templates substitute `$field` or `${field}` with model metadata. `$$` emits a literal dollar sign. `$albumartist` falls back to `$artist` when only the track artist is present, and `$artist` falls back to `$albumartist` when only the album artist is present.

Template functions use `%func{arg,arg}`. Function calls may be nested and may contain field references. Built-in functions are:

- `%lower{text}`, `%upper{text}`, `%capitalize{text}`, and `%title{text}`;
- `%left{text,n}` and `%right{text,n}`;
- `%if{condition,truetext,falsetext}` where empty, `0`, and `false` are false;
- `%asciify{text}`;
- `%aunique{identifiers,disambiguators,brackets}` for album disambiguation;
- `%sunique{identifiers,disambiguators,brackets}` for singleton disambiguation;
- `%time{date_time,format}`;
- `%first{text,count,skip,sep,join}`;
- `%ifdef{field,truetext,falsetext}` for flexible attributes.

`%aunique{}` groups albums that share all identifier fields and selects the first disambiguator that separates the duplicate albums. Its defaults are identifiers `albumartist album`, disambiguators `albumtype year label catalognum albumdisambig releasegroupdisambig`, and brackets `[]`. `%sunique{}` behaves similarly for singletons, with defaults `artist title` and `year trackdisambig`.

Special characters in template syntax are `$`, `%`, `{`, `}`, and `,`. Use `$` to escape special characters where needed. A literal comma inside a function argument is written `$,`. Undefined fields and malformed template syntax are left unreplaced. If a template function raises an exception, the expansion is a visible error string describing that exception.

Path output is normalized, optionally asciified, sanitized with `replace` and `path_sep_replace`, and made legal for the filesystem. If configured replacements would create a path that cannot fit within the maximum filename length, beets falls back to default replacements to resolve the conflict and warns.

Plugins may provide additional template functions and fields. `template_funcs` add `%name{}` functions. `template_fields` add item `$name` fields. `album_template_fields` add album `$name` fields. The `inline` plugin lets users define `item_fields` and `album_fields` in YAML using Python expressions or function bodies; item expressions have item fields and `db_obj` in scope, and album expressions have album fields plus `items`.

## Command-Line Behavior

The command-line program is invoked as:

```text
beet [global options] COMMAND [ARGS...]
beet help [COMMAND]
```

Global options must appear before the command:

- `-l LIBPATH` selects the library database.
- `-d DIRECTORY` selects the library root.
- `-v` increases verbosity; repeated `-v` increases it further.
- `-c FILE` reads an additional configuration overlay.
- `-p plugins` enables exactly the comma-separated plugin list for the run; `--plugins=` disables all plugins.
- `-P plugins` disables a comma-separated plugin list for the run and overrides `-p` for those plugins.

`beet import [-CMWAPRqst] [-l LOGPATH] PATH...` adds music from paths, directories, files, or supported archives. By default it copies files into the library, writes tags, and uses autotagging. `-m` moves instead of copying. `-C`, `-M`, and `-W` disable copy, move, and tag writing. `-A` imports with existing metadata. `-q` runs without interactive prompts and uses `quiet_fallback`. `-p` and `-P` answer resume prompts yes or no. `-i` enables incremental importing. `--incremental-skip-later` avoids recording skipped directories for later skipping. `--from-scratch` discards old tags when applying new metadata. `-t` asks even for close matches. `-s` imports as singletons. `--flat` treats all music under a directory as one album. `--group-albums` splits one directory into albums by metadata. `--pretend` prints what would be imported without changing state. `--search-id` restricts matching to explicit metadata IDs. Repeated `--set field=value` assignments add or override fields during import and use template syntax.

`beet import -L QUERY` reimports items already in the library. With `-L`, the arguments are a library query instead of filesystem paths, and `-s` controls whether the query matches individual items or albums.

`beet list [-apf] QUERY` queries the library. Without `-a`, it lists items; with `-a`, it lists albums. `-p` prints paths. `-f FORMAT` prints each result with a template. The same query syntax and sort syntax apply.

`beet modify [-IMWay] [-f FORMAT] QUERY [FIELD=VALUE...] [FIELD!...]` changes metadata. `FIELD=VALUE` assigns fields, and `FIELD!` removes flexible attributes. Values are templates. Multi-valued fields use semicolon-space separated values. With `-a`, queries and changes operate on albums and album-level fields; album changes inherit to tracks unless `-I` is used. Beets moves files when metadata changes require new paths unless `-M` is used, writes tags according to write settings unless overridden by `-w` or `-W`, prompts by default, and skips prompts with `-y`.

`beet move [-capt] [-d DIR] QUERY` moves or copies matching items into their configured destinations or into `DIR`. `-c` copies instead of moving. `-a` operates on albums. `-e` exports copies without changing the database. `-p` previews without changing disk or database state. `-t` asks before performing operations.

`beet update [-F FIELD] [-e EXCLUDE_FIELD] [-aMp] QUERY` reads changed file tags back into the database. It skips files whose modification times have not changed. By default it moves files to match updated metadata; `-M` disables moving. `-p` previews changes. `-F` restricts updated fields, and `-e` excludes fields. Updating one track in an album refreshes album-level data across the album from the first track's album-level metadata.

`beet write [-pf] [QUERY]` writes database metadata into files. By default, it writes only when file tags differ from the database. `-p` previews, and `-f` forces writing even when tags already match.

`beet remove [-adf] QUERY` removes matching items or albums from the database. It does not delete files unless `-d` is used. It prompts by default, `-f` skips prompting, and `-a` operates on albums.

`beet stats [-e] [QUERY]` reports statistics for the whole library or a query. By default it estimates file sizes from bitrate and duration; `-e` reads exact file sizes and exact duration.

`beet fields` lists item and album fields available to queries and templates, including plugin fields and flexible attributes.

`beet config` prints user configuration as YAML. `--default` includes defaults. `--path` prints the configuration path, and with `--default` prints the defaults path. Sensitive values are hidden unless `--clear` is used. `--edit` opens the config file in an editor.

`beet completion` prints a bash completion script. Completion suggests command names, options, and query field names. Plugin command completion reflects the plugins enabled when completion is generated.

## Plugin Behavior

Plugins live in the `beetsplug` namespace and are enabled through configuration or CLI plugin selection. The plugin loader imports each configured plugin name, chooses the last concrete `BeetsPlugin` subclass defined in that plugin module or package namespace, instantiates it, and sends the `pluginload` event once plugins are loaded. Plugin names in `disabled_plugins` or disabled by CLI options are not loaded.

```python
class BeetsPlugin:
    def __init__(self, name: str | None = None)
    def commands(self) -> Sequence[Subcommand]
    def queries(self) -> dict[str, type[Query]]
    def add_media_field(self, name: str, descriptor) -> None
    def register_listener(self, event: str, func) -> None
    @classmethod
    def template_func(cls, name: str)
    @classmethod
    def template_field(cls, name: str)
```

Each plugin instance has `name`, `config`, `template_funcs`, `template_fields`, `album_template_fields`, `early_import_stages`, and `import_stages`. `commands()` returns `Subcommand` objects to add to the CLI. `queries()` maps query prefixes to `Query` subclasses. `add_media_field` synchronizes a MediaFile field with item read/write behavior. `register_listener` attaches a listener to a named event and prevents duplicate registration of the same function for the same event.

```python
Subcommand(name, parser=None, help="", aliases=(), hide=False)
```

A subcommand has a primary name, optional aliases, help text, an option parser, and a `func`. The function receives `(lib, opts, args)`, where `lib` is the open `Library`.

Plugin template functions are visible as `%name{}` in path templates. Plugin item template fields are visible as `$name` for item templates. Album template fields are visible for album templates. Conflicting plugin template fields raise a plugin conflict error instead of silently choosing one.

Plugins may declare `item_types` and `album_types` dictionaries that map flexible field names to `beets.dbcore.types.Type` instances. Typed flexible fields preserve typed Python access, support advanced queries such as ranges when the type supports them, validate and convert user input where applicable, and provide typed null values for missing fields.

Events include `pluginload`, `library_opened`, `database_change`, `cli_exit`, `import_begin`, `import`, `album_imported`, `item_imported`, `before_item_imported`, item copy/move/link/hardlink/reflink events, `item_removed`, `album_removed`, `write`, `after_write`, import task events, metadata info events, MusicBrainz extraction events, and match-selection prompt events. `beets.plugins.send(event, **arguments)` calls registered listeners and returns the non-`None` listener results.

Metadata source plugins subclass the public metadata-source base classes and provide album suggestions, item suggestions, ID lookups, and optional distance overrides. When matching by explicit IDs, match options are identified by `(data_source, id)` so identical provider IDs from different data sources remain distinct.

## Error Semantics

`beets.exceptions.UserError` is the command-facing exception for nonrecoverable user-visible errors. Commands raise it when the message should be displayed to the user rather than treated as an internal crash.

`beets.library.FileOperationError(path, reason)` is the base class for file read and write failures. `ReadError` is raised when an item cannot read metadata from a media file. `WriteError` is raised when an item cannot save metadata to a media file. `Item.try_write` catches `FileOperationError`, logs it, and returns `False`; otherwise it returns `True`.

`Library.add_album([])` raises `ValueError` because an album must contain at least one item.

`parse_query_string` raises `InvalidQueryError` when shell-like parsing fails or when a query part has an invalid value. `Library.items` and `Library.albums` convert invalid query argument values into `InvalidQueryError` for the original query.

`Album.item_dir()` raises `ValueError` when an album has no items and no item directory can be inferred.

Malformed regular expressions in the `replace` configuration raise `UserError` when a library builds replacement rules.

`Results[n]` raises `IndexError` when `n` is outside the matching result set.

`beets.plugins.types(model_cls)` raises a plugin conflict error when two enabled plugins declare the same flexible field with incompatible types. Plugin template field collection raises a plugin conflict error when multiple plugins define the same computed template field.

## Cross-View Invariants

1. A library query performed through `Library.items`, `Library.albums`, and a CLI command that accepts the same query string selects the same item or album identities before command-specific options are applied.

2. Query sorting is shared by API and CLI views: embedded `field+` and `field-` sort terms override default item or album sorting, and `artist`/`albumartist` sorting uses sort-name fields when present.

3. A model field changed through attribute access and the same field changed through mapping access produce the same stored database value, the same template value, and the same CLI field visibility.

4. Album-level fields inherited through `Album.store(inherit=True)` become visible on associated items through direct item lookup, item formatting, item queries, and CLI list output.

5. Flexible attributes created through API updates or `beet modify` are queryable, appear in template expansion, are included by `beet fields`, and persist across library reloads.

6. A destination computed by `Item.destination()` uses the same configured path format, query-conditioned path selection, template expansion, replacement rules, extension preservation, and library root as `beet move` and import/move side effects.

7. When `Item.move` or `Album.move` changes a file location, the database path changes together with the filesystem operation. Preview/export modes in the CLI do not claim the same database mutation.

8. Tag writes keep file metadata and database metadata synchronized: after `Item.write` or `beet write` succeeds for an item's own path, the item's database mtime reflects the new on-disk mtime; after database-only metadata changes, the database mtime is reset so update logic can detect divergence.

9. Removing an item or album from the database does not delete files unless deletion is requested. When deletion is requested, file deletion and empty-directory pruning are the filesystem projection of the same removal.

10. Plugin-provided template fields, template functions, query prefixes, commands, media fields, and flexible field types become visible through the same API and CLI surfaces as built-in fields once the plugin is enabled.

## Representative Workflow

A user creates a temporary configuration with a library database and music directory, then imports files:

```yaml
directory: /music
library: /music/library.db
paths:
  default: $albumartist/$album%aunique{}/$track $title
  singleton: Non-Album/$artist/$title
import:
  copy: yes
  write: yes
```

Running `beet import /incoming/album` reads the media files, creates `Item` objects, groups them into an `Album` when appropriate, writes rows to the library database, writes tags unless disabled, and copies files under `/music` using the configured path template.

Later, `beet list -af '$albumartist - $album: $albumtotal' year:1990..1999 year+` queries albums, applies the year range, sorts chronologically, and formats each album with the same template engine used for paths.

If the user runs `beet modify -a album:"Example" year=1998`, the album year is changed and inherited by its tracks. If files are inside the library directory and moving is enabled, beets recomputes each destination and moves files whose formatted paths changed. `beet write album:"Example"` then writes the database metadata to the files' tags.

A Python integration sees the same state:

```python
from beets.library import Library

lib = Library("/music/library.db", directory="/music")
album = lib.albums('album:"Example"').get()
for item in album.items():
    assert item.year == album.year
    print(item.destination(relative_to_libdir=True))
```

## Non-Goals

This specification does not require reproducing beets' private module layout, private helper names, or test utilities.

It does not define the complete autotagger scoring algorithm, every MusicBrainz or third-party metadata field adjustment, or every interactive prompt transcript. The public contract is the existence of import/autotag behavior, metadata-source extension points, and the observable database, filesystem, tag, and CLI effects.

It does not require live access to MusicBrainz, Discogs, Spotify, Tidal, ListenBrainz, Last.fm, Plex, Subsonic, or other network services.

It does not require optional external binaries such as ffmpeg, ImageMagick, fpcalc, mp3gain, or acoustic analysis tools, except where a plugin documents that such a binary is needed for that plugin's own feature.

It does not specify every built-in plugin command in detail. Plugin behavior in scope is the shared loading, command registration, field/query/template/event surface and common local projections.

It does not mandate an internal storage algorithm, SQL schema implementation strategy beyond the public database behavior, command parser framework, or dependency versions.
