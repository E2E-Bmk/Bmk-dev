# jrnl Specification

## Product Overview

`jrnl` is a command-line journal for creating, viewing, searching, editing, importing, exporting, encrypting, and decrypting local journal entries. Its durable state is stored on the local filesystem as plain text journals, date-organized folder journals, DayOne Classic folders, or encrypted single-file journals.

The primary user interface is the `jrnl` command. A small Python API is also available for opening journals, representing entries, selecting import/export plugins, and invoking the CLI entry point.

## Scope

This specification covers:

- command-line entry composition, search, display, edit, delete, change-time, import, export, list, encrypt, decrypt, version, diagnostic, and debug behavior
- YAML configuration loading, journal selection, per-journal overrides, command-line configuration overrides, alternate config files, templates, and editor integration
- single-file journals, folder journals, and DayOne Classic journal folders
- plain text, pretty, short, fancy/boxed, JSON, Markdown, XML, YAML, tags, dates, calendar, and heatmap export names and behavior
- public Python import paths exposed from package initializer modules
- user-visible error and exit behavior for invalid commands, missing inputs, missing editors, bad templates, unsupported encryption, unsupported import formats, and invalid export targets

## Installable Surface

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

## Public API

### CLI Entry

```python
def jrnl.main.run(manual_args: list[str] | None = None) -> int
```

When `manual_args` is `None`, arguments are read from `sys.argv[1:]`. Successful commands normally return `None`, which produces process exit status `0` through the module and console wrappers. The parser's `--help` action raises `SystemExit(0)` after writing help. Handled `JrnlException`, keyboard interrupt, or uncaught exceptions return `1`. In debug mode, uncaught exceptions include traceback details on stderr; otherwise they are reported as a user-facing error.

### Journal Objects

```python
class Entry:
    def __init__(
        self,
        journal: Journal,
        date: datetime.datetime | None = None,
        text: str = "",
        starred: bool = False,
    ): ...
```

An `Entry` belongs to a journal and exposes `date`, `text`, `starred`, `title`, `body`, `tags`, and `fulltext`. `title`, `body`, and `tags` are derived from `text` using the journal's configured tag symbols and title-splitting rules. Tags are normalized to lowercase and include their leading tag symbol. `str(entry)` returns the storage text for the entry, including the configured timestamp format and trailing star marker when starred. `entry.pprint(short=False)` returns the display text; `short=True` returns only the timestamp and title line.

```python
class Journal:
    def __init__(self, name: str = "default", **kwargs): ...
```

A `Journal` stores entries in a single file. It is iterable over entries and `len(journal)` returns the number of entries. `open(filename=None)` creates a missing file and parent directory, reads and decrypts existing data when configured, parses entries, sorts them by date, and returns the journal. `write(filename=None)` persists the current entries through the selected storage and encryption contract. `validate_parsing()` reports whether serializing and parsing the current entries preserves their public values, and `create_file(filename)` creates an empty journal file.

Entries are created with `new_entry(raw, date=None, sort=True)`. `sort()` restores chronological order, while `limit(n)` keeps the latest `n` entries. `import_(other_journal_txt)` parses jrnl text, de-duplicates equal entries, merges them with current state, and sorts the result. `from_journal(other)` creates the requested journal type with the other journal's configuration and entries.

`filter(...)` replaces the current entry view with the selected subset. It accepts tag, date, starred, tagged, inclusion-text, and exclusion constraints; `strict=True` requires all supplied tags or text terms instead of any. The `tags` property returns summary objects whose `name` and `count` describe the current entry view, with each tag counted at most once per entry.

User-driven changes remain observable through the same journal object. `delete_entries(entries)` removes the selected entries, `change_date_entries(date, entries)` updates their timestamps, and `prompt_action_entries(message)` returns the entries accepted by the user. `editable_str()` produces the editable storage view, `parse_editable_str(edited)` applies that view back to the journal, and `get_change_counts()` returns the added, deleted, and modified counts for the session. `pprint(short=False)` renders the current entry view, with `short=True` omitting bodies.

```python
class Folder(Journal):
    def __init__(self, name: str = "default", **kwargs): ...
```

A `Folder` journal stores unencrypted entries under a directory tree organized as `YYYY/MM/DD.txt`. Opening a folder journal reads valid day files from that tree. Writing a folder journal rewrites files for dates that changed, creates missing year/month directories, and removes empty day files. Folder journals cannot be encrypted.

```python
class DayOne(Journal):
    def __init__(self, **kwargs): ...
```

A `DayOne` journal reads and writes DayOne Classic `.doentry` plist files under a DayOne Classic folder. It preserves DayOne UUIDs when editing existing entries, maps DayOne tags into jrnl tags using the first configured tag symbol, and cannot be encrypted.

```python
def open_journal(journal_name: str, config: dict, legacy: bool = False) -> Journal
```

`open_journal` validates that `journal_name` exists in `config["journals"]`, scopes the journal path, detects the journal type, opens it, and returns the opened journal object. A directory path ending in `.dayone` or containing an `entries` subdirectory opens as `DayOne`. Other existing directory paths open as `Folder`. A path ending with the platform path separator is treated as a folder journal. Other paths open as single-file `Journal`; if encryption is configured, the journal is opened through the selected encryption method. `legacy=True` opens single-file journals using the legacy jrnl 1.x parser and uses the jrnl v1 encryption selector for encrypted legacy journals.

### Plugins and Exporters

```python
EXPORT_FORMATS: list[str]
IMPORT_FORMATS: list[str]
def get_exporter(format: str) -> type[TextExporter] | None
def get_importer(format: str) -> type[JRNLImporter] | None
```

`EXPORT_FORMATS` contains all built-in export names plus `pretty` and `short`. `IMPORT_FORMATS` contains `jrnl`. `get_exporter()` returns the exporter class for class-backed formats and returns `None` for `pretty`, `short`, and unknown names. `get_importer()` returns `JRNLImporter` for `jrnl` and `None` for unknown or export-only formats.

Exporter classes expose `names`, `extension`, `export_entry(entry)`, `export_journal(journal)`, and `export(journal, output=None)` where supported. `TextExporter.export()` returns a string when `output` is omitted, writes one file when `output` is a file path, and writes one file per entry when `output` is an existing directory. Directory export filenames are built from the entry date, a slugified title, and the exporter extension.

Built-in export names are:

```text
pretty, short, text, txt, fancy, boxed, json, md, markdown, xml,
yaml, tags, dates, calendar, heatmap
```

Built-in import names are:

```text
jrnl
```

`JRNLImporter.import_(journal, input=None)` imports jrnl text into a journal. When `input` is a file path, data is read from that file; otherwise data is read from stdin. Imported entries with the exact same content and timestamp as existing entries are de-duplicated.

### Encryption Selection

```python
class EncryptionMethods(str, Enum):
    NONE = "NoEncryption"
    JRNLV1 = "Jrnlv1Encryption"
    JRNLV2 = "Jrnlv2Encryption"

def determine_encryption_method(config: str | bool) -> type
```

The encryption selector maps `True` to jrnl v2 encryption, `False` to no encryption, `"jrnlv1"` to jrnl v1 encryption, and `"jrnlv2"` to jrnl v2 encryption. String values are case-insensitive.

## Command-Line Behavior

`jrnl` has composing mode and viewing/searching mode.

Composing mode is used whenever the command has no search filters, display options, or action options. It creates a new journal entry from command-line text, piped stdin, an external editor, or a template-backed editor session.

Viewing/searching mode is used when the command includes filters, display options, action options, or text that consists only of configured tags. It selects existing entries and then either displays them or applies an action to them.

Single-dash arguments filter entries. Double-dash arguments control display, configuration, standalone commands, or actions. At most one standalone command should be used in a single invocation.

### Standalone Commands

```text
--help, -h
--version, -v
--diagnostic
--list, --ls, -ls
--encrypt
--decrypt
--import
```

`--help` prints help and exits. `--version` prints the package title, version, copyright, and GPL notice. `--diagnostic` prints jrnl version, Python version, and operating system information.

`--list` prints the config file location and configured journals. With `--format json` or `--format yaml`, it serializes the same listing as JSON or YAML.

`--encrypt` encrypts the selected journal in place unless `--file FILENAME` is provided. When encrypting in place, the configuration is updated to set that journal's `encrypt` value to true. If the journal is already encrypted, the command re-encrypts it with a new password.

`--decrypt` decrypts the selected journal in place unless `--file FILENAME` is provided. When decrypting in place, the configuration is updated to set that journal's `encrypt` value to false.

`--import` imports entries into the selected journal. `--file FILENAME` selects a file source; without it, import reads stdin. `--format TYPE` selects the import format and defaults to `jrnl`.

### Writing Entries

Examples:

```sh
jrnl today at 3am: I just met Steve Buscemi in a bar! What a nice guy.
jrnl yesterday: Called in sick. Used the time to clean the house.
jrnl *: Best day of my life.
jrnl work at 10am: Meeting with @Steve
```

When raw entry text begins with a parseable date or time phrase followed by `: `, the phrase becomes the entry date and is removed from the stored title/body text. If only a date is supplied, the configured `default_hour` and `default_minute` are used. If no date is supplied, the current date and time are used.

The title is the first sentence or first line of the entry. Sentence-ending punctuation includes `.`, `?`, `!`, and common Unicode sentence terminators. The body is the remaining text. Literal escaped newlines in command-line text are converted to real newlines.

An entry is starred when the date phrase before the colon ends with `*`, when the first line starts with `*`, when the first line ends with `*`, or when the raw text starts with `*`. Starred entries are stored with a star marker on the title line.

When no command-line text is supplied, `jrnl` opens the configured editor if one is configured. If no editor is configured, it reads from stdin with an interactive writing prompt. Piped stdin is accepted as entry text.

`--edit` can be used while composing with command-line text. In that case the command-line text prepopulates the editor, and the saved editor contents become the new entry.

`--template TEMPLATE` reads a template either from the default jrnl templates directory or from the provided relative/absolute path. A configured `template` value is used when `--template` is omitted. Templates require editor-based composition. If the saved editor content is unchanged from the template, no entry is saved.

### Searching and Filtering

Search filters can be combined. Different filter categories narrow the result set together. Within tag filters and repeated text filters, the default is "any"; `-and` requires all supplied tags/text filters to match.

Supported filters:

```text
-on DATE
-today-in-history
-month DATE
-day DATE
-year DATE
-from DATE
-to DATE
-until DATE
-contains TEXT
-and
-starred
-tagged
-n [NUMBER]
-NUMBER
-not TAG
-not -starred
-not -tagged
```

`-on DATE` selects entries on that date. `-from DATE` is inclusive. `-to DATE` and `-until DATE` are inclusive. `-today-in-history` selects entries with today's month and day across years. `-month`, `-day`, and `-year` match those date components.

Tag filters are supplied as positional text beginning with one of the configured tag symbols. Tags are matched case-insensitively. If all positional text tokens are tags, the command searches by tag rather than composing a new entry.

`-contains TEXT` searches titles and bodies case-insensitively. Multiple `-contains` filters match any text by default and all text with `-and`.

`-starred` selects starred entries. `-tagged` selects entries with at least one tag. `-not TAG` excludes entries containing that tag. `-not -starred` excludes starred entries. `-not -tagged` excludes tagged entries. Passing `-not` without a tag or supported flag is a command-line error.

`-n NUMBER` keeps the last `NUMBER` entries from the filtered result. A numeric shorthand such as `-3` is equivalent to `-n 3`.

### Actions on Search Results

```text
--edit
--delete
--change-time [DATE]
```

Search actions operate on the selected entries. If no search filters are supplied, they operate on the entire selected journal.

`--edit` opens selected entries in the configured editor. After the editor closes, jrnl parses the edited text, preserves unselected entries, sorts all entries by date, writes the journal, and reports counts for added, modified, and deleted entries. Removing all text in the editor is treated as a cancelled edit rather than a request to delete all entries.

`--delete` prompts once per selected entry and deletes only entries confirmed by the user.

`--change-time DATE` prompts once per selected entry and changes confirmed entries to the supplied date/time. If `DATE` is omitted, it uses `now`.

### Display and Export

```text
--format TYPE
--export TYPE
--file FILENAME
--tags
--short, -s
-o FILENAME
```

When search results are displayed without an action, `--format TYPE` selects an output format. `--export TYPE` is an alias for `--format TYPE`. If no format is supplied, the configured `display_format` is used when present; otherwise the pretty display is used. `--file` and `-o` write export output to a file path instead of stdout. When the selected exporter's output path is an existing directory, one file is written per entry.

`--tags` is an alias for the tags format. `--short` and `-s` display only timestamp/title lines.

Status and diagnostic messages are written to stderr. Exported data and displayed entries are written to stdout.

## Configuration

`jrnl` stores configuration as YAML. The default config file is `~/.config/jrnl/jrnl.yaml`, or `$XDG_CONFIG_HOME/jrnl/jrnl.yaml` when `XDG_CONFIG_HOME` is set. On Windows, the default path is typically `%USERPROFILE%\.config\jrnl\jrnl.yaml`.

Important config keys:

```yaml
version: package version written by jrnl
journals:
  default:
    journal: path/to/journal
editor: command used for editor-based writing and editing
encrypt: false
template: false
default_hour: 9
default_minute: 0
timeformat: "%F %r"
tagsymbols: "#@"
highlight: true
linewrap: 79
indent_character: "|"
colors:
  body: none
  date: none
  tags: none
  title: none
display_format: optional default display/export format
```

The `journals` mapping defines journal names. A journal can be configured directly as a path string or as a mapping with a `journal` key. When a journal mapping contains keys that also exist at the top level, those journal-specific values override top-level values for that journal.

The first positional token is treated as a journal name when it matches a configured journal. A trailing colon on that token is ignored for journal-name detection. If no configured journal name is supplied, the `default` journal is used.

`--config-file CONFIG_FILE_PATH` and `--cf CONFIG_FILE_PATH` use an alternate config file for the current invocation.

`--config-override CONFIG_KEY CONFIG_VALUE` and `--co CONFIG_KEY CONFIG_VALUE` apply one-off config changes for the current invocation. Dot notation addresses nested keys, such as `colors.title`. Multiple overrides may be supplied. Override values are parsed as YAML scalar or mapping values.

The `editor` command must be a blocking process. jrnl writes a temporary file, runs the editor command with that file path appended, reads the saved content after the editor exits, then deletes the temporary file.

Template lookup checks the jrnl templates directory first, then treats the argument as a local, relative, or absolute path.

## Journal Storage

Single-file journals store entries as text. Each entry begins with a timestamp line:

```text
[timestamp] title
body
```

The timestamp is formatted with the journal's `timeformat`. Starred entries include a star marker on the title line. Entries are sorted chronologically when a journal is opened, written, imported, or modified through normal journal operations.

If a single-file journal path does not exist, opening it creates missing parent directories, creates the file, writes the initial journal state, and reports the created path.

Folder journals store one UTF-8 text file per day under:

```text
YYYY/MM/DD.txt
```

Multiple entries on the same day share the same day file. Folder journals are detected from existing directory paths or paths ending with a path separator. Folder journals cannot be encrypted.

DayOne Classic journals are detected from directories ending in `.dayone` or directories containing an `entries` subdirectory. They use `.doentry` plist files and cannot be encrypted. DayOne Classic support is not DayOne 2.0 support.

Changing a configured journal path from one storage type to another is not a migration. To move between storage types, define a new journal and import text exported from the old journal.

## Format Contracts

`pretty` is the default display format. It prints the configured timestamp and title on the first line and the body below it. It honors `colors`, `indent_character`, `linewrap`, and `timeformat`. `linewrap: auto` uses terminal width when available and falls back to a normal terminal-width value when it is not.

`short` prints only the timestamp and title line for each entry.

`text` and `txt` output the same plain-text format jrnl uses for single-file storage.

`json` outputs an object with `tags` and `entries`. Each entry includes `title`, `body`, `date`, `time`, `tags`, and `starred`. DayOne-originated entries may include `uuid` and `creator` metadata.

`md` and `markdown` group entries by year and month, then render each entry as a Markdown heading with its timestamp and title followed by the body. Existing Markdown headings in entry bodies are shifted down so they remain nested under jrnl's generated headings.

`xml` outputs a `journal` document containing `entries` and `tags`. Entry elements include date and starred attributes, tag children, and entry text. DayOne-originated entries may include UUID attributes.

`yaml` writes one Markdown-with-YAML-front-matter file per entry and therefore requires the output target to be a directory. YAML front matter includes title, date, starred status, tags without their leading symbol, optional DayOne metadata, and a block body. YAML export to stdout or to a single file is an error.

`tags` prints tag counts for the selected entries, sorted by frequency. If there are no tags, it prints a no-tags message.

`dates` prints one date/count pair per date represented in the selected entries.

`calendar` and `heatmap` print calendar heatmaps of journaling frequency.

`fancy` and `boxed` display each entry in a bordered terminal-oriented layout.

## Encryption

Only single-file journals can be encrypted. Folder journals and DayOne Classic journals report an error when encryption is requested.

`encrypt: true` selects jrnl v2 encryption by default. `encrypt: false` means no encryption. `encrypt: jrnlv1` selects the legacy jrnl v1 encryption method. `encrypt: jrnlv2` selects jrnl v2 encryption.

`jrnl --encrypt` replaces the selected plain text journal with encrypted data and can also re-encrypt an already encrypted journal with a new password. `jrnl --decrypt` replaces the selected encrypted journal with plain text unless an output filename is supplied. Supplying an output filename writes the converted data there and leaves the original journal path unchanged.

When encrypting, jrnl can ask whether to store the password in the system keychain. If a stored password exists, journal operations may use it instead of prompting. Passwords cannot be recovered by jrnl if lost.

jrnl v1 encrypted files are AES-CBC files whose first 16 bytes are the initialization vector and whose key is the SHA-256 hash of the password. jrnl v2 encrypted files use Fernet with a key derived from the password by PBKDF2-HMAC-SHA256 with 100,000 iterations and the jrnl v2 salt.

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

- An entry created through the CLI, imported from jrnl text, edited in an external editor, and exported as `text` represents the same timestamp, title, body, starred state, and tags.
- Search filters apply before display and before actions, so `--short`, `--tags`, `--format`, `--edit`, `--delete`, and `--change-time` all operate on the same selected entry set for a given filter expression.
- Entries remain chronological across storage views: after writes, imports, edits, deletes, and time changes, reading the journal again yields entries ordered by timestamp.
- The selected journal name determines both the storage path and journal-specific config overrides for every command in that invocation.
- Tags are user-visible consistently across search, pretty display, tag reports, JSON, YAML, XML, Markdown, and text export: matching is case-insensitive, while exported tags include the configured symbol except where a format explicitly removes it.
- Starring is preserved across composition, storage, search by `-starred`, short/pretty display, text export, JSON, YAML, XML, editing, and import.
- Messages about counts, errors, warnings, created files, and exported files do not contaminate pipeable export data because status messages are written to stderr and data output is written to stdout.
- `--file` and shell redirection are equivalent for single-file export data, while an existing directory path changes the export contract to one file per entry for exporters that support directory output.
- Folder and DayOne Classic journals expose the same entry-level search, edit, delete, display, and export behavior as single-file journals, except that they cannot be encrypted and have storage-specific file layouts.
- Configuration overrides affect only the current command invocation; persistent config changes are made by commands such as in-place encrypt/decrypt or installation/upgrade flows, not by `--config-override`.

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

## Non-Goals

- Reproducing private helper functions, private parser actions, or private controller functions is not part of the public contract.
- Exact terminal coloring, Rich rendering internals, box-drawing glyph choices, traceback formatting, and platform-specific terminal wrapping details are outside the behavioral contract except where user-visible data routing is specified.
- Implementing DayOne 2.0 is out of scope; only DayOne Classic folders are covered.
- Network synchronization, cloud storage, mobile app integration, and remote backup behavior are not part of jrnl.
- A full clone of third-party libraries such as keyring, parsedatetime, rich, cryptography, or YAML parsers is not required; jrnl behavior may use suitable dependencies.
- Internal upgrade flows for old configuration files are not covered except where legacy journal opening and public encryption labels are explicitly described.
- Exact prose of every user-facing status message is not required unless the behavior depends on stdout/stderr routing, exit status, or named error condition.

## Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment. Journal and configuration workflows use local temporary files and require no network services.

## Evaluation Notes

Assessment exercises the documented CLI, file formats, exported Python objects, plugins, storage modes, encryption selection, and state shared by write, search, edit, and export operations. It checks public values, durable files, exit status, and output routing without requiring private helpers, private attributes, undocumented module paths, or exact error prose.
