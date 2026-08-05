# PyMdown Extensions Specification

## Product Overview

`PyMdown Extensions` is a Python-Markdown extension pack that transforms authored Markdown, extension names, extension configuration, and optional local resources into rendered HTML. Its public contract is the behavior observed through Python-Markdown's `Markdown` class, documented `pymdownx` extension import strings, and documented helper functions for slugs, emoji generation, code fences, math formatting, snippets, inline highlighting, and generic blocks.

The package imports as `pymdownx`; extension modules register through Python-Markdown by import string such as `pymdownx.superfences`, `pymdownx.snippets`, or `pymdownx.blocks.tab`. Each conversion is scoped to the active `Markdown` instance, so per-document counters and trackers reset with `Markdown.reset()` while extension configuration remains attached to that instance.

## Scope

- This specification requires documented Python import surfaces under `pymdownx`, public extension registration through Python-Markdown `Markdown`, and public helper functions documented for slug creation, emoji output, SuperFences, InlineHilite, Arithmatex, Snippets, and Blocks.
- This specification requires deterministic local Markdown conversion behavior for smart symbols, snippets with local files, SuperFences and custom fences, tabbed content, task lists, MagicLink shorthand, B64, PathConverter, StripHTML, and selected generic block extensions.
- This specification requires public exception types and public callback protocols to be observable through Python calls and `Markdown.convert()`.
- This specification requires semantic HTML facts such as element names, classes, attributes, link targets, text content, and public `Markdown` instance projections. It does not require byte-identical serialization.

## Non-Goals

- This specification does not require byte-for-byte reproduction of whitespace, attribute order, line wrapping, or Pygments token markup in rendered HTML.
- This specification does not require private modules, private attributes, version parser internals, database modules, or source-file layout.
- This specification does not require network downloads for snippets; URL snippet behavior is limited to the no-network policy described here.
- This specification does not define CSS, JavaScript, theme assets, command-line tools, documentation-site build behavior, or browser rendering.
- This specification does not require sanitizing arbitrary untrusted HTML beyond the configured comment and attribute stripping behavior.

## Representative Workflow(s)

A documentation page combines snippets, repository links, emoji, task lists, tabbed blocks, inline highlighting, and table-of-contents slugs through normal Python-Markdown construction:

```python
from pathlib import Path
import markdown
import pymdownx.emoji

base = Path("docs/includes")
md = markdown.Markdown(
    extensions=[
        "markdown.extensions.toc",
        "pymdownx.snippets",
        "pymdownx.magiclink",
        "pymdownx.emoji",
        "pymdownx.tasklist",
        "pymdownx.blocks.tab",
        "pymdownx.inlinehilite",
    ],
    extension_configs={
        "pymdownx.snippets": {"base_path": [str(base)]},
        "pymdownx.magiclink": {"repo_url_shorthand": True, "user": "docs-team", "repo": "guidepack"},
        "pymdownx.emoji": {"emoji_generator": pymdownx.emoji.to_alt},
    },
)
html = md.convert(source_text)
```

A math-heavy page registers the Arithmatex formatters with InlineHilite and SuperFences so inline math and fenced math share the same wrapper contract:

```python
import markdown
import pymdownx.arithmatex as arithmatex

md = markdown.Markdown(
    extensions=["pymdownx.inlinehilite", "pymdownx.superfences"],
    extension_configs={
        "pymdownx.inlinehilite": {
            "custom_inline": [
                {"name": "math", "class": "arithmatex", "format": arithmatex.arithmatex_inline_format(mode="generic")}
            ]
        },
        "pymdownx.superfences": {
            "custom_fences": [
                {"name": "math", "class": "arithmatex", "format": arithmatex.arithmatex_fenced_format(mode="generic")}
            ]
        },
    },
)
html = md.convert("`#!math x^2`\n\n```math\ny^2\n```")
```

## Extension Registration And Shared State

This behavior covers how extension modules are discovered, how bundles route configuration, and how Markdown-instance state is preserved or reset.

**Extension Loading.** Every documented extension module must expose `makeExtension` and must load through Python-Markdown by string name. The returned extension object must be a Python-Markdown `Extension`. `markdown.Markdown` must construct successfully with each documented extension string. When Python-Markdown is asked to load an unknown extension name, the failure must come from Python-Markdown's extension loading path.

**Bundle Composition.** The `pymdownx.extra` extension must enable the PyMdown replacements for better emphasis and SuperFences together with Python-Markdown footnotes, attribute lists, definition lists, tables, abbreviations, and Markdown-in-HTML. When configuration is supplied under `pymdownx.extra`, keys named for bundled subextensions must be routed to that subextension.

**Instance State.** A `Markdown` instance must preserve extension configuration across conversions and resets. When `reset()` is called, per-document counters such as tab group identifiers and caption numbering must restart for the next document. Registering replacement extensions together with the Python-Markdown extension they replace must produce one public behavior, not duplicate output.

## Inline Typography And Text Replacements

This behavior covers inline extensions whose public result is text-level HTML inside the surrounding Markdown document.

**Emphasis, Inserts, Deletes, Marking, And Symbols.** The caret extension must render `^^text^^` as inserted text and `^text^` as superscript when those feature flags are enabled; disabled caret features must leave their delimiters literal. The tilde extension must render `~~text~~` as deleted text and `~text~` as subscript when those feature flags are enabled; disabled tilde features must leave their delimiters literal. The mark extension must render `==text==` as marked text. SmartSymbols must replace only enabled symbol families including trademark, copyright, registered, care-of, plus-minus, arrows, not-equal, fractions, and ordinal numbers; a disabled family must remain literal.

**Keys, Progress, Tasks, Quotes, And Critic Markup.** The keys extension must render `++...++` chords as nested `kbd` elements, apply the configured `class`, and emit the configured visible separator between parts. The progressbar extension must clamp visual percentages and, with `level_class=True`, must choose a level class using `progress_increment`. Tasklist must convert `[ ]`, `[x]`, and `[X]` list markers into task-list item classes and checkbox inputs; `custom_checkbox=True` must add control and indicator elements, and `clickable_checkbox=True` must leave generated inputs enabled. With `callouts=True`, quotes must render a callout marker at the start of a blockquote as a callout structure while preserving Markdown parsing of the body. CriticMarkup must support view, accept, and reject modes: accept mode returns accepted text by applying additions and substitutions and dropping deletions, while reject mode returns original text by dropping additions and preserving rejected text.

**Slug Helpers.** `pymdownx.slugs.slugify` returns a Python-Markdown TOC-compatible callback. The `case` option accepts `none`, `lower`, `lower-ascii`, and `fold`; `percent_encode=True` percent-encodes Unicode output; `normalize` controls Unicode normalization before filtering. Legacy slug helpers `uslugify`, `uslugify_encoded`, `uslugify_cased`, and `uslugify_cased_encoded` must remain callable and must delegate to the corresponding lowercased, encoded, case-preserving, or case-preserving encoded behavior.

**Emoji Indexes And Generators.** `pymdownx.emoji.emojione`, `pymdownx.emoji.gemoji`, and `pymdownx.emoji.twemoji` must return index dictionaries with keys `name`, `emoji`, and `aliases`. `pymdownx.emoji.to_png`, `pymdownx.emoji.to_png_sprite`, `pymdownx.emoji.to_svg_sprite`, and `pymdownx.emoji.to_alt` must build the documented public emoji output from the supplied emoji entry fields, options, and Markdown instance.

## Links Paths Snippets And HTML Resources

This behavior covers extensions that rewrite links, local files, snippet directives, and HTML attributes.

**Magic Links.** MagicLink must autolink supported raw URLs and email addresses. With `hide_protocol=True`, rendered link text must omit the protocol while the `href` keeps it. With `repo_url_shorthand=True`, repository shorthand must resolve mentions, repositories, issues, pull requests, discussions, commits, and compare ranges using configured `provider`, `user`, and `repo` context. Explicit provider, user, or repository text must override defaults for that link. MagicLink must not verify that a remote account or repository exists.

**Local Paths And Images.** B64 must rewrite eligible local PNG, JPEG, and GIF image `src` attributes into `data:image/...;base64,...` URIs after resolving them against `base_path`. With `restrict_path=True`, images outside `base_path` or outside `root_path` must remain unchanged. Missing, unsupported, remote, or disallowed image paths must remain unchanged. PathConverter must inspect configured `href` and `src` tags, convert only local relative paths, preserve fragments and query strings, and leave URL schemes and absolute URLs unchanged. In absolute mode it must resolve against `base_path`; with `file_scheme=True`, absolute output must use `file://` URLs. In relative mode it must rewrite paths relative to `relative_path`.

**Snippets And Stripping.** Snippets must process single-line and block scissors directives before normal Markdown parsing. Paths must be searched against `base_path` entries in order, and the first valid match wins. With `restrict_base_path=True`, local snippets outside the base path must not be read. Missing snippets must be removed silently when `check_paths=False` and must raise `SnippetMissingError` when `check_paths=True`. Line selections must support start, end, ranges, comma-separated selections, negative indexes, and line number `0` clamped to line `1`; named section selections must omit marker lines and, with `dedent_subsections=True`, dedent common leading whitespace. With `url_download=False`, URL directives must not perform network access and must follow missing-snippet behavior. StripHTML must remove comments when `strip_comments=True`, remove configured attributes, remove `on*` attributes when `strip_js_on_attributes=True`, and preserve tag names and text content otherwise.

## Code Math Highlighting And Custom Formatters

This behavior covers code fences, highlighter sharing, custom callback contracts, and math wrappers.

**Highlight And SuperFences.** Highlight must provide shared settings for SuperFences and InlineHilite when it appears in the same Markdown instance. With `use_pygments=False`, code blocks must use a JavaScript-highlighter shape: a `pre` wrapper using the configured CSS class and a `code` element whose language class uses `language_prefix`, unless `code_attr_on_pre=True` moves language and extra attributes to `pre`. SuperFences must recognize matching runs of at least three backticks or tildes, require matching character, length, and indentation for closing fences, and support nested fences in blockquotes and list contexts when the documented indentation rules are satisfied.

**Custom Fences And Inline Highlighting.** `fence_code_format` must escape source and wrap it in `pre` and `code`; `fence_div_format` must escape source and wrap it in `div`. Both helpers must apply supplied `classes`, `id_value`, and `attrs` to the first output element. `highlight_validator` must place highlighter options in the `options` mapping, place element attributes in the `attrs` mapping, and return a truthy acceptance value. A custom SuperFences validator must accept language, input values, options, attrs, and the Markdown instance. A custom SuperFences formatter must receive source, language, class name, options, the Markdown instance, and keyword attributes. A custom InlineHilite formatter must receive source, language, class name, and the Markdown instance. Formatter exceptions of type `SuperFencesException` or `InlineHiliteException` must propagate.

**Math Formatters.** `arithmatex_inline_format` must return a formatter for InlineHilite custom inline entries. In generic mode, it must wrap inline math in `\(...\)` inside the selected tag with class `arithmatex`. `arithmatex_fenced_format` must return a formatter for SuperFences custom fence entries. In generic mode, it must wrap block math in `\[...\]` inside the selected tag with class `arithmatex`. Legacy fenced math formatter functions must remain callable, emit `DeprecationWarning`, and return the corresponding block math wrapper.

## Generic Blocks And Tabbed Content

This behavior covers the generic Blocks API and built-in block extensions that expose block-level HTML structures.

**Blocks API.** `BlocksExtension` subclasses must register generic block types by overriding `extendMarkdownBlocks` and receiving both the Markdown instance and a block manager. `Block` subclasses must define `NAME`, `ARGUMENT`, and `OPTIONS` to control syntax, argument acceptance, and option validation. Block instances must expose `length`, `tracker`, `md`, `argument`, `options`, and `config`; tracker state must persist across blocks in one document and reset with the Markdown instance. Returning `False` from `on_validate` must leave the source block unparsed as a generic block.

**Validators.** The validator functions in `pymdownx.blocks.block` must return converted values when accepted and must raise `ValueError` when rejected. `type_any` returns its input, `type_none` accepts only `None`, `type_number` accepts integers and floats, `type_integer` accepts integers and integer-valued floats, `type_ranged_number` and `type_ranged_integer` enforce inclusive bounds, `type_boolean` accepts only booleans, `type_ternary` accepts `None` and booleans, `type_string` accepts strings, `type_string_insensitive` lowercases strings, `type_html_identifier` accepts HTML identifier names, `type_string_in` restricts strings to an accepted set, `type_string_delimiter` splits and validates delimited strings, `type_html_classes` returns a list of valid classes, `type_html_attribute_dict` normalizes `class` and `id`, and `type_multi` accepts the first validator that succeeds.

**Built-In Blocks And Legacy Blocks.** The HTML block must create the requested element and apply `attrs` to its outer element. The admonition block must render an admonition wrapper, title, and Markdown-parsed body. The details block must render `details` and `summary`, and its `open` option must control the outer element. Invalid block options must leave source literal. The legacy details syntax must render details structures. The legacy tabbed syntax and `pymdownx.blocks.tab` must both produce tabbed sets with input, label, and tab content projections.

## Product State Model

The core state is the tuple of authored Markdown text, enabled extension list, extension configuration, local resource files, callback objects, and per-instance conversion state. The public projections are rendered HTML, Markdown instance state such as TOC tokens, callback return values, raised public exception types, and local file effects observed through rendered links or image sources.

A conversion must not mutate local input files. A `Markdown.reset()` call must clear per-document counters and trackers while preserving extension configuration. Callback registrations must affect only the Markdown instance that receives them. Local resource lookup must use the configured base paths for that conversion and must not depend on host-specific absolute paths beyond values supplied by the caller.

## Error Semantics

| Condition | Exception or result |
| --- | --- |
| A snippet is missing while `check_paths=True` | `SnippetMissingError` |
| A snippet is missing while `check_paths=False` | The directive is removed without raising |
| An unknown emoji shortname is encountered with `strict=True` | `RuntimeError` |
| An unknown emoji shortname is encountered with `strict=False` | The literal shortname remains in output |
| A SuperFences formatter raises `SuperFencesException` | The same exception type propagates |
| An InlineHilite formatter raises `InlineHiliteException` | The same exception type propagates |
| A Blocks validator receives an unsupported value | `ValueError` |
| MagicLink custom provider configuration has an invalid provider name, missing required key, or unsupported type | `ValueError` or `KeyError` during extension setup |
| A generic block has an invalid option | The block source remains literal rather than creating the requested block |

## Cross-View Invariants

1. Rendered HTML from extension strings must match the behavior of direct `makeExtension` registration for the same extension configuration.
2. Configuration supplied through `pymdownx.extra` must reach the same subextension behavior observed when that subextension is registered directly.
3. Resetting a Markdown instance must restart document-local counters visible in tab, caption, and block projections while preserving configured MagicLink, Snippets, and formatter behavior.
4. Snippet-inserted Markdown must pass through the same downstream Markdown parser and enabled extensions as text written directly in the parent document.
5. Highlight settings must be shared by SuperFences and InlineHilite in the same Markdown instance so code blocks and inline code use consistent classes and language prefixes.
6. MagicLink and SaneHeaders must compose so issue-like shorthand at the beginning of a line remains linkable text rather than becoming a header.
7. B64 and PathConverter must rewrite only local eligible resources and must preserve disallowed, remote, missing, query, and fragment portions according to their own resource rules.
8. Legacy tabbed/details syntax and Blocks tab/details syntax must expose equivalent public HTML roles for tab sets and details elements even though the authoring syntax differs.
9. Custom SuperFences, InlineHilite, emoji, and Arithmatex callbacks must receive the documented arguments and their returned elements or HTML must enter the rendered output.

## Installable Surface

### Import Surface

```python
import pymdownx.arithmatex
import pymdownx.b64
import pymdownx.betterem
import pymdownx.blocks.admonition
import pymdownx.blocks.caption
import pymdownx.blocks.definition
import pymdownx.blocks.details
import pymdownx.blocks.html
import pymdownx.blocks.tab
import pymdownx.caret
import pymdownx.critic
import pymdownx.details
import pymdownx.emoji
import pymdownx.escapeall
import pymdownx.extra
import pymdownx.fancylists
import pymdownx.highlight
import pymdownx.inlinehilite
import pymdownx.keys
import pymdownx.magiclink
import pymdownx.mark
import pymdownx.pathconverter
import pymdownx.progressbar
import pymdownx.quotes
import pymdownx.saneheaders
import pymdownx.slugs
import pymdownx.smartsymbols
import pymdownx.snippets
import pymdownx.striphtml
import pymdownx.superfences
import pymdownx.tabbed
import pymdownx.tasklist
import pymdownx.tilde
from markdown import Markdown
from markdown.extensions import Extension
from pymdownx import slugs
from pymdownx.emoji import emojione, gemoji, twemoji, to_alt, to_png, to_png_sprite, to_svg_sprite
from pymdownx.snippets import SnippetMissingError
from pymdownx.superfences import SuperFencesException, fence_code_format, fence_div_format, highlight_validator
from pymdownx.inlinehilite import InlineHiliteException
from pymdownx.arithmatex import arithmatex_inline_format, arithmatex_fenced_format, fence_mathjax_format, fence_mathjax_preview_format, fence_generic_format
from pymdownx.blocks import BlocksExtension
from pymdownx.blocks.block import Block, type_any, type_none, type_number, type_integer, type_ranged_number, type_ranged_integer, type_boolean, type_ternary, type_string, type_string_insensitive, type_html_identifier, type_string_in, type_string_delimiter, type_html_classes, type_html_attribute_dict, type_multi
```

### API Catalog

| Name | Kind | Role |
| --- | --- | --- |
| Extension modules under `pymdownx.*` | module | Python-Markdown extension entry points exposing `makeExtension`. |
| `Markdown` | class | Python-Markdown conversion surface that loads extension strings and exposes `convert()` and `reset()`. |
| `Extension` | class | Python-Markdown base type returned by extension module `makeExtension` functions. |
| `pymdownx.extra` | extension module | Bundle for common PyMdown replacements and Python-Markdown extras. |
| `pymdownx.slugs.slugify` | function | Builds TOC-compatible slug callbacks. |
| `uslugify`, `uslugify_encoded`, `uslugify_cased`, `uslugify_cased_encoded` | function | Compatibility callbacks for common slug modes. |
| `emojione`, `gemoji`, `twemoji` | function | Return emoji index dictionaries with `name`, `emoji`, and `aliases`. |
| `to_png`, `to_png_sprite`, `to_svg_sprite`, `to_alt` | function | Convert emoji entries into ElementTree or stashed HTML output. |
| `fence_code_format` | function | Built-in SuperFences formatter for escaped `pre`/`code` output. |
| `fence_div_format` | function | Built-in SuperFences formatter for escaped `div` output. |
| `highlight_validator` | function | Separates SuperFences highlighter options from element attributes. |
| Arithmatex formatter builders | function | Produce inline and block math callbacks for InlineHilite and SuperFences. |
| Legacy Arithmatex formatters | function | Compatibility SuperFences formatters for block math output. |
| `BlocksExtension` | class | Base class for generic block extension registration. |
| `Block` | class | Base class for custom generic block implementations. |
| `type_any`, `type_none`, `type_number`, `type_integer`, `type_ranged_number`, `type_ranged_integer`, `type_boolean`, `type_ternary`, `type_string`, `type_string_insensitive`, `type_html_identifier`, `type_string_in`, `type_string_delimiter`, `type_html_classes`, `type_html_attribute_dict`, `type_multi` | function | Public validators for block option coercion and rejection. |
| `SnippetMissingError` | exception | Missing-snippet failure when path checking is enabled. |
| `SuperFencesException` | exception | Custom fence failure propagated from formatter code. |
| `InlineHiliteException` | exception | Custom inline highlighter failure propagated from formatter code. |

### CLI Entry Points

There is no console script for this package. `python -m pymdownx` is not supported. Programmatic use is through Python imports and Python-Markdown extension registration.

## Invocation Protocol

Tests and applications invoke this package by installing the project, importing documented public modules, constructing `markdown.Markdown` with extension strings and `extension_configs`, and calling `convert()` on Markdown text. Local-resource tests provide temporary files through configured paths. Network access is not part of the invocation protocol.

## Environment

The working environment runs Python 3.11 on Linux without network access. The following third-party packages are preinstalled and importable:

- `pytest`
- `pytest-json-report`
- `Markdown`
- `PyYAML`
- `Pygments`

The target package is not pre-installed. The assessment environment provides the same interpreter and package set. The project must declare packaging metadata in a standard `pyproject.toml` or `setup.py` at the project root so it installs with pip.

## Implementation Guidance

Assessment exercises public imports, extension registration, single-extension rendering behavior, callback contracts, local file handling, reset behavior, and multi-extension composition. Tests inspect semantic HTML facts such as tags, classes, attributes, links, text, callback observations, and exception types. They do not require exact serialization whitespace, exact attribute ordering, private state, private module imports, live network access, or exact exception-message prose.
