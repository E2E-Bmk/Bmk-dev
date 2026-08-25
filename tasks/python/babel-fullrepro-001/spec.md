# Babel Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

=== Context Layer ===

## Product Overview

`babel` is a Python internationalization package that manages gettext message catalogs for local application files. In this specification, the covered system represents catalog entries as Python objects, extracts translatable strings from source files, reads and writes PO and MO catalog files, and exposes the same catalog facts through local command-line and setup command workflows.

The central state is a message catalog: header metadata, locale metadata, active messages, obsolete messages, message locations, translator comments, format flags, plural message forms, and optional message context. The same state is visible through `Catalog` and `Message` objects, extraction result tuples, PO text, MO bytes, and local `pybabel` commands.

## Non-Goals

- This specification does not require locale date, number, unit, list, territory, or CLDR display-name formatting outside the catalog metadata needed by message files.
- This specification does not require network access, external translation services, database storage, web framework integration, or gettext runtime lookup APIs.
- This specification does not require performance-measurement behavior from any test helper package.
- This specification does not define private modules, private helper functions, internal parser classes, internal token objects, exact `repr()` strings, exact warning text, or exact logging text.
- This specification does not require Jinja2, Genshi, or other third-party extractors unless the user supplies a callable extractor or an importable extractor reference.

=== Orientation Layer ===

## Representative Workflows

**Create, update, and serialize a catalog.** A user creates a template catalog, adds extracted messages, updates a locale catalog from that template, then writes and reads a PO file.

```python
from io import BytesIO, StringIO
from babel.messages import Catalog
from babel.messages.pofile import read_po, write_po

template = Catalog(project="Demo", version="1.0")
template.add("Hello", locations=[("app.py", 3)], auto_comments=["shown on home page"])
template.add(("One file", "%(num)d files"), locations=[("app.py", 8)])

translated = Catalog(locale="fr_FR", project="Demo", version="1.0")
translated.add("Hello", "Bonjour")
translated.update(template)

buf = BytesIO()
write_po(buf, translated, omit_header=False)
round_tripped = read_po(StringIO(buf.getvalue().decode("utf-8")), locale="fr_FR")
```

**Extract source messages and compile them.** A user extracts strings from source files, stores them in a catalog, writes PO text, and compiles the catalog to MO bytes.

```python
from io import BytesIO
from pathlib import Path
from babel.messages import Catalog
from babel.messages.extract import extract_from_dir
from babel.messages.mofile import write_mo, read_mo

catalog = Catalog(locale="en")
for filename, lineno, message, comments, context in extract_from_dir(Path("src")):
    catalog.add(message, locations=[(filename, lineno)], auto_comments=comments, context=context)

mo = BytesIO()
write_mo(mo, catalog, use_fuzzy=False)
mo.seek(0)
loaded = read_mo(mo)
```

**Run catalog commands for local files.** A project invokes `pybabel extract` to create a POT file, `pybabel init` to create a locale PO file, `pybabel update` to merge a changed POT file, and `pybabel compile` to create MO files. Each command reads and writes only local paths supplied by command options.

=== Behavior Layer ===

## Catalog State and Message Objects

Catalog state behavior covers the in-memory representation that all file and command workflows share.

**Message identity and flags.** A `Message` accepts an `id`, an optional `string`, `locations`, `flags`, `auto_comments`, `user_comments`, `previous_id`, `lineno`, and `context`. When `id` is a tuple or list, the message must be pluralizable and an empty translation value must become a tuple of empty strings. When a message id contains old-style percent formatting fields, the message must include the `python-format` flag. When a message id contains brace formatting fields, the message must include the `python-brace-format` flag. When the id does not contain such fields, those flags must not be present unless supplied explicitly for another purpose.

**Message comparisons and copies.** A message must order and compare by singular message id and context. For a plural message, the singular id is the first id element. `clone()` returns a separate `Message` with copied ids, string, locations, flags, comments, previous ids, line number, and context. `is_identical()` returns `True` only when the compared message has the same public message data. If `is_identical()` receives a non-message object, then it must raise `AssertionError`.

**Message validation.** `Message.check()` returns a list of `TranslationError` objects raised by registered translation checkers. When a catalog is supplied, plural-count validation must use that catalog's locale or plural header state. When no checker reports an error, `Message.check()` returns an empty list.

**Catalog construction and metadata.** A `Catalog` accepts optional `locale`, `domain`, `header_comment`, project metadata, translator metadata, `charset`, creation and revision dates, and a `fuzzy` header flag. When `locale` is a locale identifier string, the catalog must expose the parsed locale when the identifier is known and must preserve the original locale identifier when locale data is unknown. If `locale` is not `None`, a locale identifier string, or a `Locale` object, then setting it must raise `TypeError`.

**Catalog collection operations.** `Catalog.add()` must create a `Message`, insert it into the active catalog, and return it. `Catalog.get()` returns the active message for an id and context, or `None` when no matching message exists. `Catalog.delete()` removes a matching active message and leaves missing ids unchanged. `len(catalog)` returns the count of active non-header messages. Iterating a catalog returns a synthesized header message first, followed by active messages in insertion order.

**Catalog merge semantics.** Assigning a `Message` to an existing id must merge locations, automatic comments, user comments, and flags without duplicate entries. When a new plural message replaces an existing singular message with the same key, the stored id and string must become plural message data. Assigning the empty id must update MIME headers, header comments, and the header fuzzy flag rather than adding a normal message.

**Catalog update semantics.** `Catalog.update()` merges an existing locale catalog with a template catalog. Messages present in the template remain active. Messages absent from the template move to `obsolete` unless fuzzy matching accounts for them. Existing translations and user comments must be preserved when their matching template message remains active and `keep_user_comments` is true. When fuzzy matching matches a changed id, the resulting message must keep the old translation, set the `fuzzy` flag, and record the previous id. When `no_fuzzy_matching` is true, changed ids must not be fuzzy matched. When `update_header_comment` is true, the target header comment must be copied from the template. When `update_creation_date` is true, the target creation date must be copied from the template.

## PO and MO File Interchange

PO and MO behavior covers conversion between catalog objects and gettext file formats.

**PO reading.** `read_po()` accepts a text file object or iterable of text lines and returns a `Catalog`. The `locale`, `domain`, `charset`, `ignore_obsolete`, and `abort_invalid` parameters control the returned catalog metadata and invalid-input behavior. When the PO header contains `Language`, charset, plural-form, creation-date, or revision-date headers, the returned catalog must reflect those fields. When `ignore_obsolete` is false, obsolete PO entries must populate `catalog.obsolete`; when it is true, obsolete entries must be skipped. If `abort_invalid` is true and the PO input is structurally invalid, then `read_po()` must raise `PoFileError`.

**PO writing.** `write_po()` writes bytes for a `Catalog` to a writable binary file object. The output must include a header entry unless `omit_header` is true. The output must include active messages, user comments, automatic comments, flags, context markers, plural forms, and location comments unless the corresponding option suppresses them. When `no_location` is true, location comments must not be emitted. When `include_lineno` is false, location comments must include filenames without line numbers. When `include_previous` is true, previous message ids must be emitted as previous-id comments. When `ignore_obsolete` is true, obsolete messages must not be emitted. `sort_output` sorts by message id; `sort_by_file` sorts by location.

**PO string helpers.** `escape()` returns a double-quoted PO string with backslashes, tabs, carriage returns, newlines, and quotes escaped. `unescape()` reverses that quoted representation. `normalize()` returns a PO-ready string representation, splitting multiline or wide text according to `width` and `prefix`. `denormalize()` reverses a normalized PO string into plain text. If `width` is absent, zero, or negative, wrapping must be disabled.

**MO reading and writing.** `write_mo()` writes GNU MO bytes for a catalog to a writable binary file object. `read_mo()` reads GNU MO bytes from a readable binary file object and returns a `Catalog`. Singular, plural, and context messages must round-trip through MO format. When `use_fuzzy` is false, fuzzy messages must be omitted from the MO file. When `use_fuzzy` is true, fuzzy messages must be included. If an MO file has an unsupported byte order or malformed table structure, then `read_mo()` must raise a standard binary parsing exception rather than returning unrelated catalog content.

## Message Extraction and Mapping

Extraction behavior covers how local source files become message tuples for catalog construction.

**Extraction result shape.** `extract()` returns tuples containing line number, message value, translator comments, and context. `extract_from_file()` returns those tuples for one file. `extract_from_dir()` returns tuples containing relative filename, line number, message value, translator comments, and context. A message value is a string for singular calls and a tuple for plural or context-aware calls.

**Extractor selection.** The `method` parameter accepts a callable extractor, a built-in extractor name, an entry point name, or an import reference in `package.module:function` or `package.module.function` form. If no extractor is registered or importable for the requested method, then `extract()` must raise `ValueError`. `extract_nothing()` must return an empty list.

**Directory traversal.** `extract_from_dir()` scans the supplied directory, or the current working directory when no directory is supplied. It must process files in sorted directory and filename order. A `method_map` entry maps an extended glob pattern to an extraction method. Files that match no method pattern must be ignored. An `options_map` entry keyed by pattern must supply method-specific options. A `callback` must be called before extracting each matched file with filename, method name, and options. A `directory_filter` returning false for a directory must prevent traversal into that directory.

**Python source extraction.** `extract_python()` reads bytes using the declared source encoding or UTF-8 fallback and returns translation calls matching configured keywords. Default keywords include `_`, `gettext`, `ngettext`, `ugettext`, `ungettext`, `dgettext`, `dngettext`, `dpgettext`, `N_`, `pgettext`, `npgettext`, and `dnpgettext` with gettext-compatible argument positions. It must ignore function and class definitions whose names match keywords. It must combine adjacent string literal arguments and must report translator comments that immediately precede a matched call and begin with a configured comment tag.

**JavaScript source extraction.** `extract_javascript()` reads bytes using the configured encoding or UTF-8 fallback and returns translation calls matching configured keywords. The `jsx`, `template_string`, and `parse_template_string` options control JSX token support, tagged template string calls, and recursive extraction from template string contents. Line and block translator comments that immediately precede a matched call and begin with a configured tag must be returned with that message.

**Mapping configuration.** `parse_mapping_cfg()` reads INI mapping text and returns a method map plus an options map. The `[extractors]` section maps short extractor names to import references. Other sections use `method: pattern` names and option keys. `parse_mapping()` must behave like `parse_mapping_cfg()` and emit a deprecation warning. `parse_keywords()` accepts GNU gettext keyword specifications and returns the keyword mapping consumed by extraction. If a keyword specification contains a context marker or arity marker, then the returned mapping must preserve those argument rules.

## Command and Setup Workflows

Command behavior covers the public local-file frontends for catalog extraction, initialization, update, validation, and compilation.

**Command-line interface.** The installed console script is `pybabel`. Running `pybabel --help` must list the global options and the `compile`, `extract`, `init`, and `update` commands. `pybabel --list-locales` must print known locale identifiers. Usage or option errors must terminate with a nonzero status and must not write successful output files.

**Extraction command.** `pybabel extract` reads one or more input paths and writes a POT file. The command must support `--charset`, `--keywords`, `--no-default-keywords`, `--mapping-file`, `--no-location`, `--add-location`, `--omit-header`, `--output-file`, `--width`, `--no-wrap`, `--sort-output`, `--sort-by-file`, `--msgid-bugs-address`, `--copyright-holder`, `--project`, `--version`, `--add-comments`, `--strip-comments`, `--input-dirs`, `--ignore-dirs`, and `--header-comment`. When no mapping file is supplied, Python files must use the built-in Python extractor. When a mapping file is supplied, the configured mappings must replace the default mapping. If the output file option is missing, then the command must raise an option error.

**Initialization command.** `pybabel init` reads a POT file and creates a locale PO file. The command must support `--domain`, `--input-file`, `--output-dir`, `--output-file`, `--locale`, `--width`, and `--no-wrap`. When `output_file` is not supplied, the command must write to the default path under `output_dir`, locale, `LC_MESSAGES`, and domain. If required input or locale options are missing, then the command must raise an option error.

**Update command.** `pybabel update` reads a POT file and updates one or more existing locale PO files. The command must support `--domain`, `--input-file`, `--output-dir`, `--output-file`, `--omit-header`, `--locale`, `--width`, `--no-wrap`, `--ignore-obsolete`, `--init-missing`, `--no-fuzzy-matching`, `--update-header-comment`, and `--previous`. When `init_missing` is true, missing locale output files must be initialized from the template. When `no_fuzzy_matching` is true, changed ids must not be fuzzy matched. If required input or output options are missing, then the command must raise an option error.

**Compile and check commands.** `pybabel compile` reads PO files and writes MO files. The command must support `--domain`, `--directory`, `--input-file`, `--output-file`, `--locale`, `--use-fuzzy`, and `--statistics`. When directory is supplied without output file, the default MO path must be under directory, locale, `LC_MESSAGES`, and domain. When neither input file nor locale is supplied, the command must compile all catalog files under the directory that match the domain. Catalog validation must report `TranslationError` failures from message checkers and must return a nonzero status when validation fails.

**Setup integration.** The setup command classes `compile_catalog`, `extract_messages`, `init_catalog`, and `update_catalog` must expose the same local-file workflows as the matching `pybabel` subcommands. `check_message_extractors()` must validate the `message_extractors` setup keyword. If a setup mapping has an invalid type or invalid shape, then validation must raise a setup option error.

=== Contract Layer ===

## State Model

The core state is a gettext catalog. It contains catalog metadata, one synthesized header entry, active messages keyed by id and optional context, obsolete messages, plural-form metadata, message comments, locations, flags, previous ids, translations, and output encoding.

Public projections of this state are:

1. `Catalog` collection operations and metadata properties.
2. `Message` public attributes, validation properties, and checker results.
3. PO text produced by `write_po()` and consumed by `read_po()`.
4. MO bytes produced by `write_mo()` and consumed by `read_mo()`.
5. Extraction tuples produced by `extract()`, `extract_from_file()`, and `extract_from_dir()`.
6. Local files produced by `pybabel` and setup command workflows.

## Error Semantics

| Condition | Required result |
|---|---|
| `Catalog.locale` receives an object that is not `None`, a locale identifier string, or a `Locale` object | raises `TypeError` |
| `Message.is_identical()` receives a non-`Message` object | raises `AssertionError` |
| `Catalog.is_identical()` receives a non-`Catalog` object | raises `AssertionError` |
| `extract()` receives an unknown extraction method | raises `ValueError` |
| `parse_mapping_cfg()` receives malformed INI mapping text | raises the parser's configuration exception |
| TOML mapping configuration has invalid section names, invalid mapping shape, or invalid value types | raises `ConfigurationError` |
| `read_po()` receives structurally invalid PO text with `abort_invalid` true | raises `PoFileError` |
| `pybabel` subcommands miss required options or receive incompatible options | raise `OptionError` or exit with a nonzero command status |
| Setup command options contain invalid extractor mapping data | raises a setup option error |
| Translation validation detects plural or Python-format mismatches | returns or reports `TranslationError` objects |

## Cross-View Invariants

1. A message added through `Catalog.add()` must appear in `Catalog.get()`, membership tests, catalog iteration, PO output, and MO output when the message is eligible for that file format.
2. Header metadata set on a `Catalog` must appear in the synthesized iteration header, PO header text, and MO header entry, and reading those files must reconstruct the same metadata fields that the file format stores.
3. A plural message must preserve singular id, plural id, plural translations, context, plural-form metadata, PO `msgid_plural` entries, and MO plural entries across catalog update and file round trips.
4. A context-specific message must use its context for catalog lookup, PO `msgctxt` output, extraction tuple context, and MO storage so that equal ids with different contexts remain distinct.
5. Translator comments and location comments returned by extraction must become `Message` comments and locations when inserted into a catalog, and `write_po()` must project them into PO comments unless the caller suppresses locations.
6. A fuzzy message must remain marked fuzzy in `Message.flags`, PO flag output, catalog update results, and validation workflows; MO writing must include or exclude it according to the `use_fuzzy` option.
7. `pybabel` and setup commands must produce the same catalog state transitions as the underlying Python APIs for extraction, PO initialization, update, validation, and MO compilation.
8. Keyword parsing rules must be shared by direct extraction, INI/TOML mapping options, `pybabel extract`, and setup extraction so that a keyword with context or plural argument positions selects the same message tuple in each projection.

=== Reference Layer ===

## Public Interface

### Import Surface

```python
from babel.messages import Catalog, Message, TranslationError
```

```python
from babel.messages.catalog import DEFAULT_HEADER, PYTHON_FORMAT, Catalog, Message, TranslationError
```

```python
from babel.messages.pofile import (
    PoFileError,
    denormalize,
    escape,
    generate_po,
    normalize,
    read_po,
    unescape,
    write_po,
)
```

```python
from babel.messages.mofile import read_mo, write_mo
```

```python
from babel.messages.extract import (
    DEFAULT_KEYWORDS,
    GROUP_NAME,
    check_and_call_extract_file,
    default_directory_filter,
    extract,
    extract_from_dir,
    extract_from_file,
    extract_javascript,
    extract_nothing,
    extract_python,
    parse_template_string,
)
```

```python
from babel.messages.frontend import (
    BaseError,
    CommandLineInterface,
    ConfigurationError,
    OptionError,
    SetupError,
    listify_value,
    main,
    parse_keywords,
    parse_mapping,
    parse_mapping_cfg,
)
```

```python
from babel.messages.plurals import get_plural
```

```python
from babel.messages.setuptools_frontend import (
    check_message_extractors,
    compile_catalog,
    extract_messages,
    init_catalog,
    update_catalog,
)
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Catalog` | class | Represents gettext catalog metadata, active messages, obsolete messages, plural metadata, and header state. |
| `Message` | class | Represents one gettext message id, translation, locations, flags, comments, previous ids, line number, and context. |
| `TranslationError` | exception | Represents translation validation failures from catalog and message checkers. |
| `DEFAULT_HEADER` | constant | Provides the default catalog header comment template. |
| `PYTHON_FORMAT` | constant | Provides the old-style Python formatting detector used for message flags. |
| `PoFileError` | exception | Represents invalid PO input detected during PO parsing. |
| `read_po` | function | Reads PO text into a `Catalog`. |
| `write_po` | function | Writes a `Catalog` as PO bytes. |
| `generate_po` | function | Yields PO text fragments for a `Catalog`. |
| `escape` | function | Escapes plain text for a quoted PO string. |
| `unescape` | function | Unescapes a quoted PO string. |
| `normalize` | function | Formats text as PO string syntax with optional wrapping. |
| `denormalize` | function | Converts normalized PO string syntax back to plain text. |
| `read_mo` | function | Reads GNU MO bytes into a `Catalog`. |
| `write_mo` | function | Writes a `Catalog` as GNU MO bytes. |
| `DEFAULT_KEYWORDS` | constant | Provides the default gettext keyword mapping for extraction. |
| `GROUP_NAME` | constant | Names the extractor entry point group. |
| `extract` | function | Dispatches one file object to an extraction method. |
| `extract_from_file` | function | Extracts messages from one filesystem path. |
| `extract_from_dir` | function | Extracts messages from files under a directory according to mapping rules. |
| `check_and_call_extract_file` | function | Applies method mapping to one file and invokes extraction for matches. |
| `default_directory_filter` | function | Decides whether default directory traversal includes a path. |
| `extract_python` | function | Extracts gettext calls from Python source. |
| `extract_javascript` | function | Extracts gettext calls from JavaScript source. |
| `extract_nothing` | function | Provides an extractor that yields no messages. |
| `parse_template_string` | function | Extracts JavaScript template string content according to extraction options. |
| `BaseError` | exception | Base class for command frontend errors. |
| `OptionError` | exception | Represents invalid command option combinations. |
| `SetupError` | exception | Represents setup integration failures. |
| `ConfigurationError` | exception | Represents invalid extraction mapping configuration. |
| `CommandLineInterface` | class | Implements the `pybabel` command dispatcher. |
| `listify_value` | function | Converts command or config values into lists. |
| `main` | function | Runs the command-line interface with process arguments. |
| `parse_keywords` | function | Parses GNU gettext keyword specifications into extraction rules. |
| `parse_mapping` | function | Deprecated alias for INI extraction mapping parsing. |
| `parse_mapping_cfg` | function | Parses INI extraction mapping configuration. |
| `get_plural` | function | Returns gettext plural-form metadata for a locale. |
| `check_message_extractors` | function | Validates setup `message_extractors` configuration. |
| `compile_catalog` | class | Setup command for compiling PO files to MO files. |
| `extract_messages` | class | Setup command for extracting localizable messages to POT files. |
| `init_catalog` | class | Setup command for initializing locale PO files from a template. |
| `update_catalog` | class | Setup command for updating locale PO files from a template. |

### CLI Entry Points

Console script: `pybabel`

| Exit | Meaning |
|---:|---|
| 0 | The requested command completed successfully. |
| 1 | A command option, setup, configuration, validation, or file-processing error prevented successful completion. |

Supported commands are `compile`, `extract`, `init`, and `update`.

=== Meta Layer ===

## Appendix A: Environment

The working environment runs Python 3.11 on Linux without network access. The following third-party packages are preinstalled and importable: `pytest`, `freezegun`, `setuptools`, and `pytz`. The assessment environment provides the same interpreter and package set.

The project must declare its packaging metadata in a standard `pyproject.toml` or `setup.py` at the project root so the package is installable with pip.

## Appendix B: Assessment Notes

Assessment covers observable behavior through public imports and the `pybabel` command. It checks catalog object state, PO and MO round trips, extraction from local Python and JavaScript snippets, mapping parsing, setup command configuration, command option validation, local file creation, catalog update behavior, plural and context preservation, fuzzy-message handling, and translation validation errors.

Assessment uses local temporary files and in-memory file objects. It does not inspect private attributes, private modules, internal parser state, exact diagnostic prose, performance timings, external services, or network resources.
