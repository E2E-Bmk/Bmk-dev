# jrnl Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`jrnl` is a command-line journal for creating, viewing, searching, editing, importing, exporting, encrypting, and decrypting local journal entries. Its durable state is stored on the local filesystem as plain text journals, date-organized folder journals, DayOne Classic folders, or encrypted single-file journals.

The primary user interface is the `jrnl` command. A small Python API is also available for opening journals, representing entries, selecting import/export plugins, and invoking the CLI entry point.

## Non-Goals

- This specification does not require Private helper functions, private parser actions, or private controller functions.
- This specification does not require Exact terminal coloring, rendering internals, box-drawing glyph choices, traceback formatting, or platform-specific terminal wrapping detailsexcept where user-visible data routing is specified.
- This specification does not require DayOne 2.0 journal formats; only DayOne Classic folders are covered.
- This specification does not require Network synchronization, cloud storage, mobile app integration, or remote backup behavior.
- This specification does not require Reimplementing third-party libraries; behavior may use suitable dependencies.
- This specification does not require Internal upgrade flows for old configuration filesexcept where legacy journal opening and public encryption labels are explicitly described.
- This specification does not require Exact prose of every user-facing status messageunless the behavior depends on stdout/stderr routing, exit status, or a named error condition.

## Representative Workflows

### Daily journaling and search

```sh
jrnl yesterday: Called in sick. Used the time to clean the house and write.
jrnl today at 3am: I just met Steve in a bar! What a nice guy.
jrnl @health -from yesterday -to today --short
jrnl -contains "clean the house" --edit
jrnl --tags
```

The first two commands append entries to the selected journal. The first parseable date phrase before `: ` sets each entry's timestamp; the first sentence becomes the title. The search command selects entries matching the tag and inclusive date range, then shows timestamp/title lines only. The edit command opens matching entries in the configured editor and writes any saved changes back to the journal. The tag report counts tags in the selected journal.

### Multiple journals and export/import

```yaml
journals:
  default: ~/journal.txt
  work:
    journal: ~/work.txt
    display_format: json
  archive: ~/archive/
```

```sh
jrnl work at 10am: Meeting with @Steve.
jrnl work -n 3
jrnl work --format txt | jrnl archive --import
jrnl archive --format yaml --file ./entries/
```

The `work` token selects the configured `work` journal and applies its overrides. The export/import pipeline moves jrnl text into the `archive` journal, de-duplicating exact duplicate entries. YAML export writes one file per selected entry because the output target is a directory.

## Command-Line Behavior

`jrnl` has composing mode and viewing/searching mode.

**Composing mode.** Composing mode is used whenever the command has no search filters, display options, or action options. It creates a new journal entry from command-line text, piped stdin, an external editor, or a template-backed editor session.

**Viewing/searching mode.** Viewing/searching mode is used when the command includes filters, display options, action options, or text that consists only of configured tags. It selects existing entries and then either displays them or applies an action to them.

Single-dash arguments filter entries. Double-dash arguments control display, configuration, standalone commands, or actions. At most one standalone command should be used in a single invocation.

**Standalone commands.** `--help` prints help and exits. `--version` prints the package title, version, copyright, and GPL notice; `jrnl.__title__` must equal `"jrnl"` and `jrnl.__version__` must reflect the installed package version. `--diagnostic` prints jrnl version, Python version, and operating system information.

`--list` prints the config file location and configured journals. With `--format json` or `--format yaml`, it serializes the same listing as JSON or YAML; JSON output must include a `journals` key whose value maps journal names to their configurations.

`--encrypt` encrypts the selected journal in place unless `--file FILENAME` is provided. When encrypting in place, the configuration is updated to set that journal's `encrypt` value to true. If the journal is already encrypted, the command re-encrypts it with a new password.

`--decrypt` decrypts the selected journal in place unless `--file FILENAME` is provided. When decrypting in place, the configuration is updated to set that journal's `encrypt` value to false.

`--import` imports entries into the selected journal. `--file FILENAME` selects a file source; without it, import reads stdin. `--format TYPE` selects the import format and defaults to `jrnl`.

**Writing entries.** When raw entry text begins with a parseable date or time phrase followed by `: `, the phrase becomes the entry date and is removed from the stored title/body text. If only a date is supplied, the configured `default_hour` and `default_minute` are used. If no date is supplied, the current date and time are used.

The title is the first sentence or first line of the entry. Sentence-ending punctuation includes `.`, `?`, `!`, and common Unicode sentence terminators. The body is the remaining text. Literal escaped newlines in command-line text are converted to real newlines.

An entry is starred when the date phrase before the colon ends with `*`, when the first line starts with `*`, when the first line ends with `*`, or when the raw text starts with `*`. Starred entries are stored with a star marker on the title line.

When no command-line text is supplied, `jrnl` opens the configured editor if one is configured. If no editor is configured, it reads from stdin with an interactive writing prompt. Piped stdin is accepted as entry text.

`--edit` can be used while composing with command-line text. In that case the command-line text prepopulates the editor, and the saved editor contents become the new entry.

`--template TEMPLATE` reads a template either from the default jrnl templates directory or from the provided relative/absolute path. A configured `template` value is used when `--template` is omitted. Templates require editor-based composition. If the saved editor content is unchanged from the template, no entry is saved.

**Searching and filtering.** Search filters can be combined. Different filter categories narrow the result set together. Within tag filters and repeated text filters, the default is "any"; `-and` requires all supplied tags/text filters to match.

`-on DATE` selects entries on that date. `-from DATE` is inclusive. `-to DATE` and `-until DATE` are inclusive. `-today-in-history` selects entries with today's month and day across years. `-month`, `-day`, and `-year` match those date components.

Tag filters are supplied as positional text beginning with one of the configured tag symbols. Tags are matched case-insensitively. If all positional text tokens are tags, the command searches by tag rather than composing a new entry.

`-contains TEXT` searches titles and bodies case-insensitively. Multiple `-contains` filters match any text by default and all text with `-and`.

`-starred` selects starred entries. `-tagged` selects entries with at least one tag. `-not TAG` excludes entries containing that tag. `-not -starred` excludes starred entries. `-not -tagged` excludes tagged entries. Passing `-not` without a tag or supported flag is a command-line error.

`-n NUMBER` keeps the last `NUMBER` entries from the filtered result. A numeric shorthand such as `-3` is equivalent to `-n 3`.

**Actions on search results.** `--edit` opens selected entries in the configured editor. After the editor closes, jrnl parses the edited text, preserves unselected entries, sorts all entries by date, writes the journal, and reports counts for added, modified, and deleted entries. Removing all text in the editor is treated as a cancelled edit rather than a request to delete all entries.

`--delete` prompts once per selected entry and deletes only entries confirmed by the user.

`--change-time DATE` prompts once per selected entry and changes confirmed entries to the supplied date/time. If `DATE` is omitted, it uses `now`.

**Display and export.** When search results are displayed without an action, `--format TYPE` selects an output format. `--export TYPE` is an alias for `--format TYPE`. If no format is supplied, the configured `display_format` is used when present; otherwise the pretty display is used. `--file` and `-o` write export output to a file path instead of stdout. When the selected exporter's output path is an existing directory, one file is written per entry.

`--tags` is an alias for the tags format. `--short` and `-s` display only timestamp/title lines.

Status and diagnostic messages are written to stderr. Exported data and displayed entries are written to stdout.

## Journal and Entry Python API

This section covers the Python-level journal and entry objects used for programmatic journal manipulation.

**Journal construction and persistence.** `Journal` accepts configuration keyword arguments including `encrypt`, `timeformat`, `tagsymbols`, `default_hour`, `default_minute`, `highlight`, `linewrap`, `indent_character`, `colors`, and `journal` (the file path). `Journal.open()` must read the journal file, create missing parent directories and an empty file when the path does not exist, parse entries from storage, and return the journal. `Journal.write()` must serialize the current entries and write them to the configured path.

**Entry creation.** `Journal.new_entry(text, date=..., sort=True)` must create a new `Entry` from the supplied text and optional date, add it to the journal, optionally sort entries by date, and return the created entry.

**Iteration and length.** Iterating over a `Journal` must yield its entries in their current order. `len(journal)` must return the number of entries.

**Sorting and limiting.** `Journal.sort()` must order entries chronologically by date. `Journal.limit(n)` must keep only the last `n` entries and remove earlier entries.

**Entry structure.** An `Entry` is constructed with a journal reference, optional date, optional text, and optional `starred` flag. The text is split into a title and body. The title is the first sentence or first line. `Entry.fulltext` must return the title and body combined as a single string with space separation. `Entry.starred` must be `True` when the raw text contains a trailing star marker on the title line.

**Tags.** `Entry.tags` must return a deduplicated list of tags found in the entry text, normalized to lowercase. Tags are tokens beginning with a configured tag symbol. Email addresses must not be treated as tags.

**Entry string representation.** `str(entry)` must produce the storage format: `[timestamp] title *\nbody\n` where `*` appears only for starred entries.

**Entry display.** `Entry.pprint(short=True)` must return the timestamp and title without body text. `Journal.pprint(short=True)` must produce short display for all entries; `Journal.pprint(short=False)` must include body text.

**Tag summaries.** `Journal.tags` must return tag summary objects, each with a `name` and `count` attribute. Each tag must be counted once per entry, not once per occurrence within an entry.

**Filtering.** `Journal.filter(tags=..., strict=False, starred=False, contains=..., exclude=...)` must narrow the journal's entries in place. When `tags` is supplied, entries matching any supplied tag are kept; tags are matched case-insensitively. When `strict=True`, only entries containing all supplied tags are kept. When `starred=True`, only starred entries are kept. When `contains` is supplied, entries whose title or body includes the text (case-insensitively) are kept. When `exclude` is supplied, entries containing any excluded tag are removed.

**Importing.** `Journal.import_(text)` must parse jrnl-formatted text, add the parsed entries to the journal, sort chronologically, and deduplicate exact duplicate entries.

**Editing roundtrip.** `Journal.editable_str()` must return a text representation suitable for editing in an external editor. `Journal.parse_editable_str(text)` must parse the edited text and update the journal's entries, tracking added, modified, and deleted entries. `Journal.get_change_counts()` must return a dictionary with `modified` and `deleted` counts reflecting the last edit operation.

**Deletion and date changes.** `Journal.delete_entries(entries)` must remove the specified entries from the journal. `Journal.change_date_entries(new_date, entries)` must update the date of each specified entry.

**Folder journals.** `Folder` stores one UTF-8 text file per day under `YYYY/MM/DD.txt`. Multiple entries on the same day share the same day file. `Folder.from_journal(source)` must create a new `Folder` with the same configuration and entries as the source journal, preserving entry attributes and the source's `timeformat` and `tagsymbols` settings.

**DayOne Classic journals.** `DayOne` journals are detected from directories ending in `.dayone` or directories containing an `entries` subdirectory. They use `.doentry` plist files and cannot be encrypted.

**Opening by name.** `open_journal(name, config)` must detect the storage type from the configured path and return the appropriate journal subclass: a `Journal` for single-file paths, a `Folder` for existing directory paths, and a `DayOne` for DayOne-structured directories.

## Configuration

`jrnl` stores configuration as YAML. The default config file is `~/.config/jrnl/jrnl.yaml`, or `$XDG_CONFIG_HOME/jrnl/jrnl.yaml` when `XDG_CONFIG_HOME` is set. On Windows, the default path is typically `%USERPROFILE%\.config\jrnl\jrnl.yaml`.

**Core config keys.** Important config keys include `version`, `journals`, `editor`, `encrypt`, `template`, `default_hour`, `default_minute`, `timeformat`, `tagsymbols`, `highlight`, `linewrap`, `indent_character`, `colors` (with `body`, `date`, `tags`, `title` sub-keys), and `display_format`.

**Journal mapping.** The `journals` mapping defines journal names. A journal can be configured directly as a path string or as a mapping with a `journal` key. When a journal mapping contains keys that also exist at the top level, those journal-specific values override top-level values for that journal.

**Journal name detection.** The first positional token is treated as a journal name when it matches a configured journal. A trailing colon on that token is ignored for journal-name detection. If no configured journal name is supplied, the `default` journal is used.

**Config file overrides.** `--config-file CONFIG_FILE_PATH` and `--cf CONFIG_FILE_PATH` use an alternate config file for the current invocation. `--config-override CONFIG_KEY CONFIG_VALUE` and `--co CONFIG_KEY CONFIG_VALUE` apply one-off config changes for the current invocation. Dot notation addresses nested keys. Override values are parsed as YAML scalar or mapping values. Configuration overrides affect only the current command invocation.

**Editor behavior.** The `editor` command must be a blocking process. jrnl writes a temporary file, runs the editor command with that file path appended, reads the saved content after the editor exits, then deletes the temporary file.

## Format Contracts

This section covers the export and import format behavior.

**Pretty and short display.** `pretty` is the default display format. It prints the configured timestamp and title on the first line and the body below it. It honors `colors`, `indent_character`, `linewrap`, and `timeformat`. `short` prints only the timestamp and title line for each entry.

**Text format.** `text` and `txt` output the same plain-text format jrnl uses for single-file storage. The text exporter's output for a whole journal must match the journal's `editable_str()`. When the output target is a file, the exporter must write to that file. When the output target is an existing directory, the exporter must write one file per entry.

**JSON format.** `json` outputs an object with `tags` and `entries`. Each entry includes `title`, `body`, `date`, `time`, `tags`, and `starred`. DayOne-originated entries may include `uuid` and `creator` metadata. The `tags` top-level key must map each tag to its count across the selected entries.

**Markdown format.** `md` and `markdown` group entries by year and month, then render each entry as a Markdown heading with its timestamp and title followed by the body. Existing Markdown headings in entry bodies are shifted down so they remain nested under jrnl's generated headings.

**XML format.** `xml` outputs a `journal` document containing `entries` and `tags`. Entry elements include date and starred attributes, tag children, and entry text.

**YAML format.** `yaml` writes one Markdown-with-YAML-front-matter file per entry and therefore requires the output target to be a directory. YAML export to stdout or to a single file is an error.

**Dates and tags formats.** `dates` prints one date/count pair per date represented in the selected entries. `tags` prints tag counts for the selected entries, sorted by frequency.

**Calendar and fancy formats.** `calendar` and `heatmap` print calendar heatmaps of journaling frequency. `fancy` and `boxed` display each entry in a bordered terminal-oriented layout.

**Plugin registry.** `EXPORT_FORMATS` must contain all supported export format names including `pretty`, `short`, `text`, `txt`, `json`, `md`, `markdown`, and others. `IMPORT_FORMATS` must contain import format names including `jrnl`. `get_exporter(name)` must return the exporter class for supported format names, return `None` for `pretty` (which is a display format, not a file exporter), and return `None` for unknown names. `get_importer(name)` must return the importer class for supported format names and `None` for unknown names. `text` and `txt` must resolve to the same exporter. `md` and `markdown` must resolve to the same exporter.

## Encryption

Only single-file journals can be encrypted. Folder journals and DayOne Classic journals report an error when encryption is requested.

**Encryption labels.** `encrypt: true` selects jrnl v2 encryption by default. `encrypt: false` means no encryption. `encrypt: jrnlv1` selects the legacy jrnl v1 encryption method. `encrypt: jrnlv2` selects jrnl v2 encryption.

**Encryption selection.** `determine_encryption_method(value)` must map `True` to the same method as `"jrnlv2"`, must map `False` to a distinct no-encryption result, and must accept case-insensitive string labels so that `"JRNLV1"` equals `"jrnlv1"`. The v1 and v2 methods must produce distinct encryption results.

**Encryption operations.** `jrnl --encrypt` replaces the selected plain text journal with encrypted data and can also re-encrypt an already encrypted journal with a new password. `jrnl --decrypt` replaces the selected encrypted journal with plain text unless an output filename is supplied. Supplying an output filename writes the converted data there and leaves the original journal path unchanged.

When encrypting, jrnl can ask whether to store the password in the system keychain. Passwords cannot be recovered by jrnl if lost.

## State Model

Journal state has three public projections: entry objects in memory, durable journal files on disk, and command output or exported data. Creating, editing, deleting, importing, or changing the time of an entry must update the in-memory projection before `write()` persists the same selected entries. Reopening that storage must restore the same timestamp, title, body, starred state, and tags. Search and limit operations must select the same entry set for display, actions, and export. Configuration selects storage and formatting for the current invocation without mutating unrelated journals.

## Error Semantics

`JrnlException` is the common handled exception type for user-facing jrnl failures. The CLI catches it, prints its messages to stderr, and returns exit code `1`.

User-visible error cases include:

- unknown configured journal name: command fails and lists configured journals
- missing or unparsable config file: command fails before journal operations
- duplicate YAML config keys: command warns and continues with duplicate keys allowed for loading
- invalid color names: color verification reports the invalid key/value
- `-not` without a tag, `-starred`, or `-tagged`: argument parsing fails
- no entry text from stdin/editor or only unchanged template text: no entry is saved
- missing template file: command reports the template paths checked
- editor command not found: command reports the configured editor value
- `--edit` without a configured editor: command fails and points the user to editor configuration
- empty editor result during edit: command cancels rather than deleting all selected entries
- no search results for edit/change-time/delete: command reports that nothing can be modified or deleted
- encryption requested for a folder or DayOne Classic journal: command fails because that journal type cannot be encrypted
- encrypted journal configured for an unencryptable journal type: opening reports a configuration warning
- decryption failure or wrong password: command fails without returning decrypted text
- YAML export without a directory target: command fails
- import requested for a format without an importer: command fails and names the unsupported format
- keyboard interrupt: command reports that it was aborted and returns exit code `1`

## Cross-View Invariants

1. An entry created through the CLI, imported from jrnl text, edited in an external editor, and exported as `text` represents the same timestamp, title, body, starred state, and tags.
2. Search filters apply before display and before actions, so `--short`, `--tags`, `--format`, `--edit`, `--delete`, and `--change-time` all operate on the same selected entry set for a given filter expression.
3. Entries remain chronological across storage views: after writes, imports, edits, deletes, and time changes, reading the journal again yields entries ordered by timestamp.
4. The selected journal name determines both the storage path and journal-specific config overrides for every command in that invocation.
5. Tags are user-visible consistently across search, pretty display, tag reports, JSON, YAML, XML, Markdown, and text export: matching is case-insensitive, while exported tags include the configured symbol except where a format explicitly removes it.
6. Starring is preserved across composition, storage, search by `-starred`, short/pretty display, text export, JSON, YAML, XML, editing, and import.
7. Messages about counts, errors, warnings, created files, and exported files do not contaminate pipeable export data because status messages are written to stderr and data output is written to stdout.
8. `--file` and shell redirection are equivalent for single-file export data, while an existing directory path changes the export contract to one file per entry for exporters that support directory output.
9. Folder and DayOne Classic journals expose the same entry-level search, edit, delete, display, and export behavior as single-file journals, except that they cannot be encrypted and have storage-specific file layouts.
10. Configuration overrides affect only the current command invocation; persistent config changes are made by commands such as in-place encrypt/decrypt or installation/upgrade flows, not by `--config-override`.
11. A journal written with `write()` and reopened with `open()` must preserve the same `date`, `title`, `body`, `starred`, and `tags` for every entry.
12. Text export output for a journal must match the journal's `editable_str()`, and filtering before export must select the same entries visible through the journal's iteration.

## Public Interface

### Import Surface

The package name is `jrnl`.

The command-line entry point is:

```text
jrnl = jrnl.main:run
```

`python -m jrnl` invokes the same command-line behavior as `jrnl`.

The package root exposes:

```python
import jrnl

jrnl.__title__ == "jrnl"
jrnl.__version__  # installed package version, or "source" when unavailable
```

The public journal API is exported from `jrnl.journals`:

```python
from jrnl.journals import DayOne, Entry, Folder, Journal, open_journal
```

The public plugin API is exported from `jrnl.plugins`:

```python
from jrnl.plugins import EXPORT_FORMATS, IMPORT_FORMATS
from jrnl.plugins import get_exporter, get_importer
from jrnl.plugins import (
    CalendarHeatmapExporter,
    DatesExporter,
    FancyExporter,
    JRNLImporter,
    JSONExporter,
    MarkdownExporter,
    TagExporter,
    TextExporter,
    XMLExporter,
    YAMLExporter,
)
```

The public encryption selector API is exported from `jrnl.encryption`:

```python
from jrnl.encryption import EncryptionMethods, determine_encryption_method
```

The public exception type is:

```python
from jrnl.exception import JrnlException
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `run` | function | CLI entry point; parses arguments and dispatches commands |
| `Entry` | class | One journal entry with date, text, title, body, tags, and star state |
| `Journal` | class | Single-file journal with open, write, filter, and edit operations |
| `Folder` | class | Date-organized directory journal |
| `DayOne` | class | DayOne Classic folder journal |
| `open_journal` | function | Opens a configured journal by name and storage type |
| `EXPORT_FORMATS` | constant | Built-in export format names |
| `IMPORT_FORMATS` | constant | Built-in import format names |
| `get_exporter` | function | Resolves an export format name to an exporter class |
| `get_importer` | function | Resolves an import format name to an importer class |
| `CalendarHeatmapExporter` | class | Calendar heatmap export |
| `DatesExporter` | class | Date-count export |
| `FancyExporter` | class | Bordered terminal export |
| `JRNLImporter` | class | jrnl text import |
| `JSONExporter` | class | JSON export |
| `MarkdownExporter` | class | Markdown export |
| `TagExporter` | class | Tag frequency export |
| `TextExporter` | class | Plain-text export |
| `XMLExporter` | class | XML export |
| `YAMLExporter` | class | YAML front-matter export |
| `EncryptionMethods` | enum | Supported encryption method identifiers |
| `determine_encryption_method` | function | Maps config encryption values to encryption classes |
| `JrnlException` | exception | Handled user-facing failure type |

### CLI Entry Points

The installed `jrnl` console command and `python -m jrnl` are both supported and invoke the same command dispatcher. Successful commands return exit code `0`. Argument errors, handled `JrnlException` failures, keyboard interruption, and uncaught command failures return a nonzero exit code. Export data is written to stdout, while status and error information is written to stderr.

## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment. Journal and configuration workflows use local temporary files and require no network services.

## Appendix B: Assessment Notes

Compatibility covers the documented CLI, file formats, exported Python objects, plugins, storage modes, encryption selection, and state shared by write, search, edit, and export operations. It checks public values, durable files, exit status, and output routing without requiring private helpers, private attributes, undocumented module paths, or exact error prose.
