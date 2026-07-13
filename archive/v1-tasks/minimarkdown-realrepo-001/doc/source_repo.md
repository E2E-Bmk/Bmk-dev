# Source Repository Notes

## Candidate

- Task ID: `minimarkdown-realrepo-001`
- Display name: MiniMarkdown
- Source repository: `lepture/mistune`
- Domain: Markdown parsing and rendering
- Candidate status at creation: `prospect`

## Why This Repo

Mistune is a mature Python Markdown parser with a useful benchmark shape for the unit/system gap suite. Its public product model is not just "turn Markdown into HTML"; it separates block parsing, inline parsing, renderers, and plugins. Those surfaces can be implemented independently in unit tests, while realistic Markdown documents require the surfaces to compose through a shared token stream and dispatch model.

## Reference Behavior Used for Task Design

The task is a scoped mini implementation inspired by Mistune rather than a full clone. The relevant source behaviors are:

- Markdown parsing has distinct block-level and inline-level responsibilities.
- Renderers consume parser output and can produce HTML or structured token/AST-like output.
- Plugins extend syntax such as tables, strikethrough, and task lists.
- Inline parsing must run inside block containers such as headings, paragraphs, list items, block quotes, and table cells.
- Escaping and literal-code behavior must be consistent across core syntax and plugin output.

## Scoped Surface

MiniMarkdown intentionally excludes full CommonMark compatibility and advanced Mistune features such as directives, footnotes, raw HTML passthrough, math, syntax highlighting, and reference-style links. The target is a 200-1500 line dependency-free Python library with enough shared state to expose compositional failures.

## Expected Shared Contract

The central contract is:

> Block parsing, inline parsing, rendering, and plugins all operate on the same token semantics; any prose-bearing block or plugin cell must invoke the inline parser, while literal code regions must suppress inline parsing but still participate in escaping and rendering.

This contract is expected to be easy to miss when an agent implements the features one by one.
