# MiniMarkdown Public Product Packet

## Overview

Build `minimarkdown.py`, a dependency-free Python module that parses a practical subset of Markdown into a canonical token tree, renders that tree to HTML or AST, exposes a heading table of contents derived from the same tree, supports a small extension system, and can maintain a multi-document Markdown workspace index. The design is inspired by real Markdown parser libraries such as Mistune: block parsing creates structural tokens, inline parsing annotates textual content inside those blocks, renderers consume the shared token model, derived views project the same token facts, plugins extend the same parser/renderer pipeline, and workspace-level views project the same stored document facts over time.

The module must be importable from the solution directory:

```python
from minimarkdown import Markdown, MarkdownWorkspace, HTMLRenderer, ASTRenderer, escape_html
```

Use only the Python standard library.

## Feature Set

The product has seven feature modules:

1. Block parsing for document-level Markdown structures.
2. Inline parsing for emphasis, links, code spans, escaping, and line breaks.
3. Shared token and AST rendering model.
4. HTML rendering and escaping.
5. Heading anchor and table-of-contents projection.
6. Plugin registration for extra block and inline constructs.
7. Error recovery and deterministic parsing boundaries.
8. Workspace indexing for multiple Markdown documents with cross-document links, backlinks, diagnostics, graph export, and deterministic snapshot replay.

These modules are intentionally compositional. Block tokens contain text fragments that must be parsed through the inline parser; renderer output and the table-of-contents view depend on the same heading tokens and inline text; plugins register handlers into the same dispatch model; and malformed local syntax should degrade to literal text without corrupting later parsing.

The workspace index is a larger public product surface, not a hidden evaluator feature. A `MarkdownWorkspace` stores document sources, parses each document through the same `Markdown` pipeline, and exposes derived views that must remain consistent after document updates and removals.

## Data Model

`Markdown(renderer=None, plugins=None)` constructs a parser object.

- If `renderer` is omitted, render to HTML using `HTMLRenderer`.
- If `renderer` is `"ast"` or an `ASTRenderer` instance, return a list of token dictionaries.
- If `renderer` is an `HTMLRenderer` instance, use that renderer.
- `plugins` is an optional iterable. Each item may be a known plugin name or a callable that receives the `Markdown` instance and registers behavior.

The parser exposes:

- `markdown(text)`: parse and render text.
- `markdown.parse(text)`: return the canonical public token tree after block parsing, inline parsing, plugin recognition, and heading id assignment.
- `markdown.tokens(text)`: return the same canonical public token tree as `parse`; this alias exists for callers that think of the tree as renderer input rather than a parsing side effect.
- `markdown.walk(tokens)`: iterate public token dictionaries inside a parsed token tree, including block nodes, inline nodes, list items, table cells, and plugin tokens.
- `markdown.render(tokens, renderer=None)`: render an existing parsed token tree through the parser's renderer, or through a supplied renderer such as `"ast"` or an `HTMLRenderer` instance.
- `markdown.toc(text)`: return a flat heading table of contents derived from the same parsed heading tokens used by AST and HTML rendering.
- `markdown.register_inline(name, pattern, parse_func, render_func=None)`.
- `markdown.register_block(name, pattern, parse_func, render_func=None)`.

Registration callbacks use public signatures: `parse_func(match)` returns token fields for the matched syntax, and `render_func(renderer, token)` returns HTML for that token. Implementations may adapt internally, but plugin authors should not need private parser objects.

Token dictionaries use a stable public shape:

- `type`: token type name.
- `children`: nested inline or block tokens when present.
- `text`: raw or literal text where applicable.
- Additional type-specific keys such as `level`, `ordered`, `items`, `attrs`, `url`, `title`, `lang`, `checked`, or `align`.
- Heading tokens must include `attrs["id"]` after inline heading text is known.

The following token names are public when the corresponding feature is implemented and may be asserted directly by unit tests:

- Block tokens: `paragraph`, `heading`, `block_code`, `block_quote`, `list`, `thematic_break`, and plugin block names such as `table`.
- Inline tokens: `text`, `emphasis`, `strong`, `code_span`, `link`, `image`, `line_break`, `soft_break`, `strikethrough`, and custom plugin names registered through `register_inline`.
- A `heading` token has `level`, `text`, `children`, and `attrs["id"]`.
- A `block_code` token has `text` and optional `lang`.
- A `block_quote` token has block `children`.
- A `list` token has `ordered` and `items`; each item is a public dictionary with `text` when simple source text exists, inline `children` after parsing, optional nested block `children` or `blocks` for loose content, and optional plugin metadata such as `checked`.
- A `table` token has `header`, `align`, and `rows`; header and body cells have `text` and inline `children` after parsing.
- A `link` token has `url`, optional `title`, and label `children`; an `image` token has `url`, optional `title`, plain `alt`, and optional alt `children`.

The exact Python classes used internally are not public API.

`markdown.toc(text)` returns heading entries in document order. Each entry is a public dictionary containing at least:

- `level`: heading level.
- `text`: the plain heading text after inline syntax is interpreted and code spans are treated literally.
- `id`: the same anchor id stored on the heading token and emitted by the HTML renderer.

Heading ids are generated from the plain heading text by lowercasing ASCII letters, replacing runs of whitespace and punctuation with `-`, trimming leading/trailing hyphens, and appending `-2`, `-3`, and so on for duplicate ids within one document. This rule is public so implementations do not need to guess anchor behavior, but tests should not depend on private helper names.

## Workspace Index

`MarkdownWorkspace(renderer=None, plugins=None)` maintains a candidate-owned index over a set of Markdown documents. It uses the same parsing, rendering, heading id, inline parsing, and plugin semantics as `Markdown`.

The public document lifecycle is:

- `workspace.update(path, text)`: add or replace one document. `path` is a workspace-relative POSIX-style path; backslashes are normalized to `/`; empty paths and paths that escape the workspace with `..` are invalid. `text` must be a string. A failed update must not mutate the previous workspace state.
- `workspace.remove(path)`: remove one document if it exists.
- `workspace.paths()`: return all live document paths in sorted order.
- `workspace.tokens(path)`: return the stored canonical token tree for one document.
- `workspace.render(path, renderer=None)`: render the stored tree for one document through HTML or a supplied renderer such as `"ast"`.
- `workspace.toc(path=None)`: return heading entries. With a path, return that document's headings; without a path, return headings for all documents in path order. Each entry has `doc`, `level`, `text`, and `id`.
- `workspace.links(path=None)`: return cross-document Markdown links and images that use relative URLs or `#anchor` URLs. Absolute URLs with a URI scheme such as `https:` or `mailto:` are external and are not workspace references. Each entry has `source`, `target`, `anchor`, `text`, `kind`, `resolved`, and `order`.
- `workspace.backlinks(path, anchor=None)`: return the reverse projection of `links()`, filtered to a target document and optionally one target anchor.
- `workspace.diagnostics()`: return missing-document and missing-anchor diagnostics derived from unresolved workspace links.
- `workspace.graph()`: return a machine-readable snapshot with `documents`, `headings`, `links`, and `diagnostics`.
- `workspace.export()`: return a deterministic JSON-serializable snapshot of live document sources.
- `MarkdownWorkspace.import_snapshot(snapshot, renderer=None, plugins=None)`: reconstruct a workspace from `export()`.

Relative link targets are resolved relative to the source document's directory. A link `#intro` targets the current source document. A link `guide.md#install` targets document `guide.md` and anchor `install`. An anchor resolves only if it is one of the heading ids produced for the target document. Duplicate heading ids are disambiguated within each document, not globally across the workspace.

Workspace APIs are projections of one shared fact source:

```text
document path -> source text -> canonical token tree -> headings and links -> graph, backlinks, diagnostics, render output, export/import replay
```

Implementations may rebuild the index eagerly or lazily. Tests do not inspect private caches. They check that public views agree after updates, removals, malformed updates, and snapshot import/export.

## Block Parsing

Block parsing divides a document into ordered block tokens. Supported blocks are:

- ATX headings beginning with one to six `#` characters followed by heading text. The heading's inline children, plain text, generated `attrs["id"]`, HTML `id` attribute, and TOC entry must describe the same heading.
- Paragraphs formed from consecutive non-blank lines that are not another block type.
- Blank lines as separators, not renderable tokens.
- Fenced code blocks delimited by at least three backticks, with an optional language name after the opening fence.
- Indented code blocks made from lines indented by at least four spaces.
- Block quotes beginning with `>`, preserving nested block parsing inside the quote.
- Unordered lists beginning with `-`, `*`, or `+`.
- Ordered lists beginning with `1.`, `2.`, and so on; numbering does not need to be preserved, only ordered-list status.
- Horizontal rules made from a line of at least three matching `-`, `_`, or `*` markers, ignoring surrounding spaces.

List items may contain simple continuation lines. Continuation lines indented under an item belong to that item. A blank line followed by further indented item content makes the item loose; otherwise the list is tight. Tight list item paragraphs render without wrapping `<p>` tags, while loose list item block paragraphs render normally.

Block quotes should parse their inner content as Markdown blocks after removing the quote marker from each quoted line.

## Inline Parsing

Inline parsing transforms textual content inside paragraphs, headings, list item text, block quote paragraphs, table cells, and plugin-provided inline containers.

Supported inline constructs are:

- Text.
- Backslash escapes for Markdown punctuation.
- HTML escaping for literal text in HTML output.
- Code spans delimited by backticks; inline markup inside code spans is not parsed.
- Strong emphasis using `**text**` or `__text__`.
- Emphasis using `*text*` or `_text_`.
- Links using `[label](url)` and optional quoted title `[label](url "title")`.
- Images using `![alt](url)` and optional quoted title.
- Autolinks for `<https://...>`, `<http://...>`, and email-like addresses in angle brackets.
- Hard line breaks from two trailing spaces before a newline or from a backslash before a newline.
- Soft line breaks as newline characters inside paragraph text.

Inline delimiters must be balanced. Unclosed or malformed inline constructs remain literal text. Nested inline parsing is required inside link labels, image alt text, emphasis bodies, and strong-emphasis bodies, except inside code spans.

## Rendering

`HTMLRenderer` renders tokens to an HTML string.

Required HTML behavior:

- Escape `&`, `<`, `>`, and quotes in text and attributes.
- Render headings as `<h1 id="...">` through `<h6 id="...">` using the id on the heading token.
- Render paragraphs as `<p>`.
- Render emphasis as `<em>` and strong emphasis as `<strong>`.
- Render code spans as `<code>`.
- Render fenced and indented code blocks as `<pre><code>`; fenced blocks with a language render a `class="language-..."` attribute.
- Render block quotes as `<blockquote>`.
- Render unordered and ordered lists as `<ul>` and `<ol>`, with `<li>` children.
- Render links as `<a href="...">...</a>` and images as `<img src="..." alt="...">`, including title attributes when present.
- Render horizontal rules as `<hr>`.
- Join adjacent block outputs with newlines.

`ASTRenderer` returns token dictionaries after parsing. It must include nested inline children inside blocks that carry inline content. It must not include private compiled regular expressions, callback objects, or renderer state.

`markdown.parse(text)`, `markdown.tokens(text)`, `markdown.walk(tokens)`, `markdown.render(tokens)`, `Markdown("ast")(text)`, `Markdown()(text)`, and `markdown.toc(text)` are different projections or traversals of the same semantic parse. Replaying a parsed tree through HTML or AST rendering must not mutate that tree. Repeating parse, render, walk, and TOC operations on the same `Markdown` instance must not mutate ids, nested children, plugin dispatch tables, or later parse results.

## Plugins

Known plugin names:

- `"strikethrough"` enables `~~text~~` inline syntax. It produces `strikethrough` inline tokens and renders them as `<del>`.
- `"table"` enables GitHub-style pipe tables with a header row, delimiter row, and body rows. A table starts only at a block boundary when a header row is immediately followed by a valid delimiter row; later pipe-looking lines inside an existing paragraph remain paragraph text. Cell text is parsed as inline Markdown. Supported alignments are left, right, center, and unspecified.
- `"task_list"` enables list items beginning with `[ ]` or `[x]` after the list marker. HTML output renders a disabled checkbox before the item content and records checked state in AST tokens.

Custom plugin callables may register additional inline or block rules. Registered rules participate in the same parsing and rendering pipeline as built-in rules. Inline and block `parse_func` callbacks are called with exactly the regex match object and return public token fields; the registered `name` becomes the token's public `type`. A plugin's parsed tokens must be visible to both HTML and AST renderers.

## Global Invariants

The following invariants define system correctness:

- Every textual field produced by block parsing that represents prose must be passed through inline parsing before rendering.
- Code spans and code blocks are literal islands: inline syntax inside them is not interpreted, but their text is still HTML-escaped by the HTML renderer.
- HTML escaping must be applied consistently to literal text, URLs, titles, alt text, code content, and plugin-produced text.
- Block and inline token names must be renderer-independent; switching from HTML rendering to AST rendering changes only the output representation, not the parse semantics.
- Canonical-tree ownership: `parse` is the shared source of facts for AST output, HTML output, TOC entries, public walking, plugin metadata, and renderer replay. Implementations may have internal structures, but public projections must be explainable by this tree.
- Parse/render/parse stability: after a document is parsed and rendered through any public renderer, parsing the same source again with the same `Markdown` instance must produce the same semantic token tree, heading ids, TOC entries, nested inline children, and plugin tokens.
- Renderer replay/idempotence: rendering an existing public tree through HTML or AST rendering must be deterministic and must not add, remove, or rewrite token fields.
- Parser reuse stability: a malformed document, a rendered document, or a plugin-enabled document must not mutate parser state in a way that changes later parses of the same valid source on that parser instance.
- Heading projection consistency: each heading has one canonical plain text and id, and the AST token, rendered HTML anchor, and TOC entry must agree even when the heading contains nested inline syntax, code spans, escaped punctuation, or duplicate text.
- Nested inline consistency: prose-bearing block nodes, list items, block quote descendants, table cells, and plugin-provided inline containers must preserve nested inline token trees in AST output and render equivalent HTML.
- Plugin rules share the same parser and renderer dispatch tables as core syntax and must compose with core block and inline syntax.
- Plugin projection consistency: a plugin token recognized during parsing must be visible to AST rendering and, when a render function is registered, to HTML rendering without requiring separate feature-specific wiring.
- Failed recognition of a malformed inline or plugin construct must leave the original text intact and allow later constructs in the same document to parse.
- Block boundaries control inline scope: inline delimiters do not cross fenced code blocks, block quote boundaries, list item boundaries, or table cell boundaries.
- Table boundary ordering is significant: header, delimiter, and row lines must be classified before inline parsing, and reordering those lines changes whether a table exists.
- Rendering is deterministic for the same input, renderer, and plugin set.
- Workspace index consistency: `paths`, `tokens`, `render`, `toc`, `links`, `backlinks`, `diagnostics`, `graph`, and exported snapshots are projections of the live document set.
- Workspace update atomicity: replacing, removing, or rejecting one document must not leave stale headings, links, backlinks, diagnostics, rendered output, or exported sources.
- Workspace link inversion: every backlink is the reverse of an outbound workspace link, and every outbound link to a live target appears in that target's backlink view.
- Workspace snapshot replay: importing an exported workspace must reproduce the same graph, TOC, links, backlinks, diagnostics, and render outputs.

## Error Behavior

The parser should be forgiving. Markdown with malformed inline delimiters, incomplete links, unterminated code spans, or plugin-looking text that does not satisfy plugin syntax should render those fragments as literal text. Parser construction with an unknown plugin name should raise `ValueError`. Exact exception text is not public API.

Parsing one malformed document must not poison subsequent calls on the same `Markdown` instance.

## Non-Goals

Do not implement the full CommonMark specification. Do not implement raw HTML passthrough, footnotes, math, directive containers, definition lists, reference-style links, smart typography, syntax highlighting, or a command-line interface. Workspace indexing covers inline links with relative URLs and anchors; it does not require CommonMark reference-style link definitions. Do not use external Markdown packages.

## Evaluation Style

Hidden tests are split into two scores:

- Unit tests exercise one feature module at a time. Parser unit tests inspect isolated block or inline contracts; renderer unit tests render direct public token dictionaries; plugin unit tests confirm registration or local recognition without requiring unrelated containers. Workspace unit tests check the public `MarkdownWorkspace` API, document path normalization, simple heading/link extraction, and add/remove/export primitives. Exact token names and required public fields are checked in unit/schema-oriented tests, but unit tests should not be stricter than system tests about private token schema or incidental nesting choices.
- System tests exercise parser + renderer + derived-view invariants over the shared token tree and the shared workspace document set. They focus on parse/tokens/AST equivalence, renderer replay/idempotence, parse/render/parse semantic stability, heading anchor/TOC consistency, nested inline token trees inside block nodes, plugin dispatch and metadata across AST and HTML projections, escaping across renderer boundaries, product-natural order-sensitive parsing, recovery after malformed syntax, and workspace lifecycle consistency after multi-document update/remove/export/import flows. System tests should prefer semantic projections, `walk`-style traversal, and standard-library HTML parsing over brittle private token positions or exact rendered substrings, so a missing primitive root is not counted repeatedly before the cross-component invariant is reached.

System tests are labeled by dimension:

- `cross_feature_dataflow`
- `state_accumulation`
- `global_invariant`
- `error_atomicity`
- `operation_order_sensitivity`
- `boundary_crossing`
- `workspace_lifecycle`
- `projection_consistency`
- `snapshot_replay`

The benchmark does not inspect private implementation details.
