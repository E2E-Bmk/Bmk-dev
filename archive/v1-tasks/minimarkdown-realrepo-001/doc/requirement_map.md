# Requirement Map

## Public Requirements

| Requirement ID | PRD Section | Summary |
|---|---|---|
| REQ-public-api | Overview, Data Model | `minimarkdown.py` exports `Markdown`, `HTMLRenderer`, `ASTRenderer`, and `escape_html`; `Markdown` is callable and exposes parse/tree, render replay, walk, TOC, and registration APIs. |
| REQ-canonical-tree | Data Model, Rendering, Global Invariants | `parse(text)`/`tokens(text)` return the candidate-owned canonical public token tree after block parsing, inline parsing, plugin recognition, and heading id assignment; AST, HTML, TOC, walk, and renderer replay project from that tree. |
| REQ-blocks | Block Parsing | Supports headings, paragraphs, fenced and indented code, block quotes, ordered/unordered lists, horizontal rules, and tight/loose item behavior. |
| REQ-inline | Inline Parsing | Supports text, escapes, code spans, emphasis, strong emphasis, links, images, autolinks, line breaks, balanced delimiters, and nested inline parsing except inside literal code islands. |
| REQ-render-html | Rendering | `HTMLRenderer` emits escaped HTML for core block and inline tokens, including heading `id` attributes, and can replay an existing public tree without mutating it. |
| REQ-render-ast | Rendering | `ASTRenderer` returns public token dictionaries with nested children and without private parser state. |
| REQ-heading-index | Data Model, Block Parsing, Rendering | Heading tokens include generated `attrs["id"]`; `markdown.toc(text)` returns heading level, plain text, and id from the same parsed heading facts used by AST and HTML rendering. |
| REQ-token-schema | Data Model | Public token names and required fields are enumerated for core blocks, inline nodes, headings, lists, tables, links, images, task-list metadata, and custom plugin token types. |
| REQ-plugins | Plugins | Supports known `strikethrough`, `table`, and `task_list` plugins plus custom plugin registration with public parse/render callback signatures; plugin tokens and metadata travel through the same tree as core syntax. |
| REQ-errors | Error Behavior | Malformed syntax degrades to literal text where appropriate; unknown plugin names raise `ValueError`; malformed parses do not corrupt later parses. |
| REQ-workspace-api | Workspace Index | `MarkdownWorkspace` publicly supports update, remove, paths, tokens, render, toc, links, backlinks, diagnostics, graph, export, and import_snapshot. |
| REQ-workspace-paths | Workspace Index | Workspace paths are normalized to POSIX-style relative paths; empty or escaping paths are invalid. |
| REQ-workspace-links | Workspace Index | Relative Markdown links and `#anchor` links are indexed with source, target, anchor, label text, kind, resolution state, and document-order metadata. |
| REQ-workspace-lifecycle | Workspace Index | Adding, replacing, removing, and importing documents keeps all workspace views consistent with the live document set. |

## Global Invariants

| Invariant ID | PRD Source | Summary |
|---|---|---|
| INV-canonical-projections | Global Invariants | AST output, HTML output, TOC entries, walking, plugin metadata, and renderer replay are projections of one canonical public tree. |
| INV-render-replay | Rendering, Global Invariants | `render(tokens)` can render an existing public token tree through HTML or AST without reparsing source text. |
| INV-no-render-mutation | Rendering, Global Invariants | Rendering or walking a parsed tree is deterministic and does not add, remove, or rewrite public token fields. |
| INV-inline-in-blocks | Global Invariants | Every prose-bearing block text field flows through inline parsing before rendering. |
| INV-code-literal | Global Invariants | Code spans and code blocks suppress nested inline parsing but still escape literal content. |
| INV-escaping | Global Invariants | Escaping applies consistently to text, attributes, code, and plugin output. |
| INV-renderer-independent-tokens | Global Invariants | HTML and AST rendering share parse semantics and token names. |
| INV-round-trip-stability | Global Invariants | Parse/render/parse over the same source and parser instance preserves semantic tokens, heading ids, TOC entries, nested inline children, and plugin tokens. |
| INV-parser-reuse | Global Invariants | Malformed, rendered, or plugin-enabled parses must not mutate parser state in a way that changes later parses of the same valid source. |
| INV-heading-projection | Global Invariants | Heading AST tokens, HTML anchors, and TOC entries agree on plain text, generated ids, order, and duplicate suffixes. |
| INV-nested-inline-containers | Global Invariants | Block containers and plugin-provided inline containers preserve nested inline token trees in AST and equivalent HTML. |
| INV-plugin-shared-dispatch | Global Invariants | Built-in and custom plugins share parser and renderer dispatch with core syntax. |
| INV-plugin-projection | Global Invariants | Plugin tokens and metadata recognized during parsing are visible to AST rendering and, when a render function is registered, to HTML rendering. |
| INV-error-recovery | Global Invariants | Malformed constructs preserve literal text and do not poison later parsing. |
| INV-inline-scope | Global Invariants | Block, list item, table cell, code, and quote boundaries define inline parsing scope. |
| INV-table-boundary-order | Global Invariants | Table header, delimiter, and row order determines table recognition before inline parsing begins. |
| INV-workspace-projections | Global Invariants | Workspace paths, token trees, render output, TOC, links, backlinks, diagnostics, graph, and export snapshots are projections of one live document set. |
| INV-workspace-update-atomicity | Global Invariants | Failed updates do not mutate the previous workspace, and successful updates/removals do not leave stale headings, links, backlinks, diagnostics, or exported sources. |
| INV-workspace-link-inversion | Global Invariants | Backlinks are the reverse projection of outbound workspace links to the same target document and optional anchor. |
| INV-workspace-snapshot-replay | Global Invariants | Importing an exported workspace reproduces graph, TOC, links, backlinks, diagnostics, and render output. |

## Unit Rubric Trace

| Test ID | Type | Requirement Refs | Feature-Pure Rationale |
|---|---|---|---|
| MMU001 | unit | REQ-public-api | Imports, constructor/call shape, canonical-tree helper presence, and escaping without inspecting private attributes. |
| MMU002 | unit | REQ-blocks, REQ-heading-index | Single heading token contract, including public generated id and inline child presence. |
| MMU003 | unit | REQ-blocks | Fenced code block tokenization and public language/text fields. |
| MMU004 | unit | REQ-blocks | Indented code and thematic-break tokenization only. |
| MMU005 | unit | REQ-blocks | Ordered/unordered list block structure and simple item fields only. |
| MMU006 | unit | REQ-blocks | Block quote block structure only. |
| MMU007 | unit | REQ-inline | Emphasis and strong inline parsing only. |
| MMU008 | unit | REQ-inline | Code span inline rendering behavior only. |
| MMU009 | unit | REQ-inline | Link and image inline rendering only. |
| MMU010 | unit | REQ-inline | Escape, autolink, and public line-break token behavior only. |
| MMU011 | unit | REQ-render-html | Renderer escaping API and attribute escaping from direct tokens only. |
| MMU012 | unit | REQ-render-html, REQ-heading-index | Core renderer tag output and heading anchor rendering from direct/public tokens only. |
| MMU013 | unit | REQ-render-ast | AST renderer output shape and public inline token names only. |
| MMU014 | unit | REQ-plugins | Strikethrough plugin isolated from block nesting. |
| MMU015 | unit | REQ-plugins | Table plugin block recognition and alignment only. |
| MMU016 | unit | REQ-plugins | Task list marker recognition only. |
| MMU017 | unit | REQ-plugins | Custom inline plugin registration and callback arity only. |
| MMU018 | unit | REQ-errors | Local malformed syntax and unknown plugin error behavior only. |
| MMU019 | unit | REQ-workspace-api, REQ-workspace-paths | Public workspace import, add/update, path normalization, token/render/TOC access. |
| MMU020 | unit | REQ-workspace-links | Simple relative link extraction, anchor resolution, and backlink projection. |
| MMU021 | unit | REQ-workspace-lifecycle | Remove, failed-update atomicity, and export/import primitives. |

## System Rubric Trace

| Test ID | Dimension | Cross-Feature Contract |
|---|---|---|
| MMS001 | global_invariant | `parse`, `tokens`, AST rendering, and `walk` expose one canonical tree with core, table, strikethrough, and task-list metadata. |
| MMS002 | state_accumulation | HTML replay and AST replay of an existing tree are deterministic and do not mutate the tree. |
| MMS003 | global_invariant | Heading token ids, TOC entries, and parsed HTML heading ids/text agree on one inline-derived heading projection. |
| MMS004 | cross_feature_dataflow | Block quotes, lists, and table cells all contribute nested inline nodes to the walked tree and rendered HTML tag structure. |
| MMS005 | cross_feature_dataflow | Custom plugin metadata survives parse, walk, AST replay, and HTML replay from one registered rule. |
| MMS006 | global_invariant | A tree returned by AST rendering can be replayed by an HTML renderer with the same core and plugin semantics as direct HTML rendering. |
| MMS007 | state_accumulation | Parse, render, TOC projection, and later parse on one parser preserve tree equality and duplicate heading ids. |
| MMS008 | error_atomicity | Malformed inline/plugin syntax remains literal and later valid parses remain stable on the same parser. |
| MMS009 | operation_order_sensitivity | Table recognition is a product-natural block-boundary lifecycle decision, not a late inline pipe projection. |
| MMS010 | state_accumulation | Tight/loose list item state, nested block children, inline children, and replayed HTML stay consistent. |
| MMS011 | cross_feature_dataflow | Task-list checked state is plugin metadata while item prose remains normal inline content across tree and HTML projections. |
| MMS012 | boundary_crossing | Code spans and code blocks are literal islands in both the walked tree and parsed rendered HTML. |
| MMS013 | workspace_lifecycle | Updating a target document changes TOC, link resolution, backlinks, diagnostics, graph, and render output consistently. |
| MMS014 | workspace_lifecycle | Removing and restoring documents removes stale outbound edges and turns incoming references into then out of diagnostics. |
| MMS015 | projection_consistency | Outbound links, backlinks, graph edges, and per-document render/TOC views are inverse projections of one workspace state. |
| MMS016 | snapshot_replay | Export/import replay preserves workspace graph, diagnostics, links, TOC, and rendered HTML. |

## Redesign Note

The shared fact source is now explicitly the canonical public token tree returned by `parse(text)` and `tokens(text)` for single-document behavior, and the live document set managed by `MarkdownWorkspace` for multi-document behavior. AST rendering, HTML rendering, TOC, public walking, plugin metadata, replay rendering, workspace links, backlinks, diagnostics, graph, and snapshot replay must all be projections of those public sources.

The expected gap mechanism is lifecycle/compositional: a solution can pass unit tests by recognizing local block/inline/plugin syntax and rendering direct tokens, but fail system rows if it keeps separate render-only state, recomputes headings differently for TOC, mutates tokens during rendering, loses plugin metadata in AST replay, treats table detection as late inline text, or models loose list items separately from their rendered tree.

Previous evidence showed repeated root failures around list item text shape, hard/soft break token naming, custom plugin callback arity, and block token aliases. The new unit layer still states the public one-node contracts and workspace primitives, while system rows avoid repeated private-schema pressure and compare semantic projections with guarded traversal, standard-library HTML parsing, and public workspace views.

## Weight Summary

- Unit tests: 21 items x 4 points = 84 points.
- System tests: 16 items x 8 points = 128 points.
- Total: 212 points.
