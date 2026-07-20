# Babel Message Catalog Specification

## Product Overview

Babel provides internationalization utilities for Python applications. This surface focuses on gettext message catalogs: representing source messages and translations, checking Python format compatibility, extracting messages from JavaScript, and reading PO and MO catalog files.

The central model is a `Catalog` containing `Message` values. Extraction produces message IDs that can be inserted into a catalog; PO and MO readers reconstruct the same catalog state from serialized gettext data; message checks enforce translation compatibility.

## Scope

This document covers:

- `Message` and `Catalog` construction, cloning, comment/location merging, and plural identity;
- detection and checking of percent-style and brace-style Python placeholders;
- JavaScript extraction for gettext calls, comments, dotted keywords, template literals, interpolation, and JSX;
- PO string utilities, location comments, malformed-location errors, incomplete entries, and mixed iterable types;
- MO catalog reading and preservation of metadata, singular translations, and plural translations.

Locale display names, date/number formatting, command-line tools, catalog compilation, directory traversal, Python extraction, project configuration, and private helper functions are outside this scope.

## Installable Surface

The distribution is installed as `Babel` and supports these imports:

```python
from babel.messages import Catalog, Message, TranslationError
from babel.messages import extract, mofile, pofile
from babel.messages.catalog import Catalog, Message, TranslationError
from babel.messages.checkers import python_format
```

The covered public functions are:

- `babel.messages.extract.extract(method, fileobj, keywords, comment_tags, options)`;
- `babel.messages.extract.extract_javascript(fileobj, keywords, comment_tags, options)`;
- `babel.messages.mofile.read_mo(fileobj)`;
- `babel.messages.pofile.read_po(fileobj, locale=None, domain=None, ignore_obsolete=False, charset=None, abort_invalid=False)`;
- `babel.messages.pofile.unescape(string)` and `denormalize(string)`;
- `babel.messages.checkers.python_format(catalog, message)`.

`babel.messages.pofile.PoFileError` is the public PO parsing error used by this surface.

## Product State Model

Message catalog state has four public projections:

- Message projection: IDs, translated strings, flags, locations, comments, context, and plural form.
- Catalog projection: keyed lookup, insertion, merging, iteration, locale metadata, and catalog metadata.
- Extraction projection: source line, message ID or plural pair, translator comments, and context.
- File projection: PO or MO input reconstructed as public `Catalog` and `Message` values.

These projections must agree. A message read from a file must expose the same public ID, string, comments, locations, and plural shape as a directly constructed message. A source string extracted from JavaScript must be suitable as a catalog message ID. Placeholder checks must use the same IDs, strings, and flags exposed by `Message`.

## Messages And Catalogs

### Message

`Message(id, string="", locations=(), flags=(), auto_comments=(), user_comments=(), previous_id=(), lineno=None, context=None)` stores a singular string ID or a `(singular, plural)` ID pair. A plural message with no translation starts with two empty strings. `locations`, `auto_comments`, and `user_comments` preserve insertion order while removing duplicates. `flags` behaves as a set.

`pluralizable` is true for tuple/list IDs. `fuzzy` reflects membership of `"fuzzy"` in `flags`. `clone()` returns a distinct message whose mutable locations, comments, and flags can change without modifying the original.

`python_format` is true when a singular or plural ID contains a percent-style placeholder such as `%s`, `%d`, `%r`, `%(name)06d`, or `%(name)*.*f`. `python_brace_format` is true for complete replacement fields such as `{}`, `{name}`, `{name!r}`, and `{name!r:10.2f}`. Plain text, isolated braces, incomplete fields, and escaped `{{}}` are not brace-format messages. Construction synchronizes the `python-format` and `python-brace-format` flags with these properties.

`check(catalog=None)` returns a list of `TranslationError` values rather than raising the errors directly. It checks enabled message flags against the translation and, when a catalog is supplied, checks plural count.

### Catalog

`Catalog(locale=None, domain=None, header_comment=..., project=None, version=None, copyright_holder=None, msgid_bugs_address=None, creation_date=None, revision_date=None, last_translator=None, language_team=None, charset=None, fuzzy=True)` creates a catalog.

`add(id, string=None, locations=(), flags=(), auto_comments=(), user_comments=(), previous_id=(), lineno=None, context=None)` returns the resulting `Message`. A singular ID and plural ID pair with the same singular ID occupy one catalog entry. Adding an existing ID merges new locations, automatic comments, and user comments without duplicates.

Assigning `catalog[id] = Message(...)` uses the same merge behavior. Existing locations remain first, followed by new locations in insertion order. `catalog[id]` returns the message for that singular ID, and `len(catalog)` counts message entries without counting the metadata header.

## Python Placeholder Compatibility

`python_format(catalog, message)` and `message.check()` apply these rules when the source message has the `python-format` flag:

- A translated percent placeholder must be compatible with the source placeholder kind.
- Removing a required positional placeholder is invalid.
- Positional and named placeholders cannot be mixed in one format string.
- A positional source and named translation, or the reverse, are incompatible.
- Plural source IDs are checked against their corresponding translated plural strings.
- An empty translation is accepted.
- A source ID with no percent placeholders does not enable the percent checker, so its translation is not constrained by percent placeholders.
- Compatible placeholders may be reordered, and compatible numeric families include `%i`/`%d`/`%u`, `%x`/`%X`, and `%f`/`%F`/`%g`/`%G`.

Incompatibility produces a `TranslationError` through `Message.check()` or raises it when `python_format` is called directly.

When a PO header declares two plural forms, a plural entry is normalized to two translated strings. Extra indexed `msgstr` values do not survive as additional public plural strings, and the normalized message passes the catalog plural-count check.

## JavaScript Extraction

`extract("javascript", fileobj, keywords, comment_tags, options)` accepts a binary file-like object and yields `(line_number, message, comments, context)` tuples. `message` is a string for singular calls and a `(singular, plural)` tuple for plural calls.

The default keyword mapping recognizes `_`, `gettext`, `ngettext`, `ungettext`, `dgettext`, and `dngettext` with their documented argument positions. Calls are emitted only when the required message arguments are string literals. Dynamic expressions are ignored without preventing later literal calls from being extracted. A function definition named like a keyword is not a call and emits nothing.

The `keywords` mapping may contain dotted names such as `com.corporate.i18n.formatMessage` and JavaScript identifiers containing `$`. A matching call is extracted; a standalone reference with no call is ignored.

### Comments

`extract_javascript` attaches line comments and block comments whose first content begins with one of `comment_tags`. Consecutive comment lines remain separate strings. A comment is attached only to the next adjacent message call; an intervening statement discards it.

### Template Literals And JSX

Backtick strings used as ordinary call arguments and as tagged templates produce their literal content. JavaScript escapes such as `\u00eb` and `\xeb` are decoded in extracted strings.

With `parse_template_string=True`, gettext calls inside `${...}` interpolation are extracted recursively, including nested template literals. Their line number is the source line containing the nested call.

With `jsx=True`, calls inside JSX element children and attribute expressions are extracted, including dotted keywords such as `i18n._`. JSX tags and object-like attribute syntax must not become messages. With `jsx=False`, source whose JSX grammar would otherwise affect tokenization is not required to produce the complete JSX message sequence.

## Gettext File Readers

`read_po` accepts a text stream, binary stream, or homogeneous iterable of text lines or byte lines. Mixing text and bytes in one iterable raises `TypeError` or `AttributeError` rather than silently coercing values.

`unescape` removes surrounding PO quotes and decodes PO escapes for quotes and newlines. `denormalize` joins adjacent quoted lines, including irregular multiline `msgstr` input that omits an initial empty quoted line.

### Location Comments

A `#:` comment contains whitespace-separated locations. Each public message location is `(filename, line_number)`; the line number is `None` when absent. Filenames containing spaces or tabs are enclosed by Unicode First Strong Isolate U+2068 and Pop Directional Isolate U+2069. The isolate characters are removed from the public filename, and a `:line` suffix after the closing isolate is parsed as an integer.

Plain and isolated filenames may appear in the same location comment. Unbalanced isolates, an unmatched closing isolate, or closing-before-opening order cause `read_po(..., abort_invalid=True)` to raise `PoFileError`.

A blank `Language:` metadata field produces a catalog with `locale is None`. When `abort_invalid=False`, an entry with `msgid` but no `msgstr` is retained with an empty string; a plural entry with no indexed strings is retained with `("", "")`.

**MO files.**

`read_mo` returns a `Catalog` and preserves gettext metadata such as project and version. Singular translations remain strings. Plural translations remain ordered lists of strings. Catalog length counts translatable messages rather than the metadata header.

## Error Semantics

- `Message.check()` returns `TranslationError` objects for incompatible translations.
- Calling `python_format` directly raises `TranslationError` for an incompatible translation.
- `read_po(..., abort_invalid=True)` raises `PoFileError` for malformed directional isolates and other invalid PO entries.
- A PO iterable that mixes text and bytes raises `TypeError` or `AttributeError`.
- Error message wording is not part of this contract.

## Cross-View Invariants

- A cloned message must initially match the original while retaining independent mutable collections.
- Catalog insertion and assignment must expose the same deduplicated comments and locations through lookup.
- Placeholder properties, flags, direct checker calls, and `Message.check()` must agree on whether a translation is compatible.
- JavaScript extraction through `extract` and `extract_javascript` must agree on message text and translator comments.
- PO and MO readers must reconstruct message IDs, translated strings, locations, comments, and plural shape as public message state.
- PO plural normalization must agree with the catalog's public plural count.
- Source line numbers emitted during nested template extraction must refer to the original JavaScript source.

## Representative Workflow

```python
from io import BytesIO
from babel.messages import Catalog
from babel.messages import extract

source = BytesIO(b"gettext('Save'); ngettext('file', 'files', count)")
found = list(extract.extract("javascript", source, extract.DEFAULT_KEYWORDS, [], {}))

catalog = Catalog()
for _line, message_id, comments, context in found:
    catalog.add(message_id, user_comments=comments, context=context)

assert catalog["Save"].id == "Save"
assert catalog["file"].pluralizable is True
```

## Non-Goals

Private names, lexer token tuples, internal parser state, source layout, CLDR generation, locale display data, command-line output, network access, and exact error-message text are not public requirements.

## Invocation Protocol

This surface is a Python library. No console command and no `python -m babel` entry point are required.

## Environment

Runtime dependencies and packaged data files must be declared through `requirements.txt`, `pyproject.toml`, and normal Python package-data configuration. The implementation may use packages available from PyPI.
