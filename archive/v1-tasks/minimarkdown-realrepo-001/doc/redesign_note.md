# MiniMarkdown Canonical Tree Redesign Note

## Redesign Goal

MiniMarkdown is now framed around a candidate-owned canonical parse tree rather than a set of independent renderer projections. The public packet still describes a small Markdown parser, but the differentiating system behavior is that `parse(text)`/`tokens(text)` produce the one semantic source used by AST output, HTML rendering, TOC entries, public `walk`, plugin metadata, and renderer replay.

## Evidence From Previous Reports

The strongest previous Codex run scored 100/168 overall, with a 50% unit score and 66.67% system score. Its failures clustered around repeated public-schema and lifecycle roots: block token aliases such as `code_block`/`blockquote`, list item text stored as nested paragraphs instead of simple item fields, custom plugin callback arity, malformed inline recovery, and table order handling. Several older system cases still accepted or rejected candidates through rendered-substring checks, which made them easier to satisfy without proving a shared semantic model.

No-artifact OpenHands/Qwen reports scored 0 and are not useful as semantic MiniMarkdown evidence; they mainly confirm environment/artifact absence. The reference report passed 30/30 on the prior rubric, so the redesign needed to keep reference behavior green while shifting the hidden signal.

## New Shared Fact Source

The canonical source is the public token tree after:

- block recognition;
- inline parsing inside prose-bearing fields;
- plugin recognition and metadata attachment;
- heading plain-text extraction and id assignment.

The public projections are:

- `parse(text)` / `tokens(text)`;
- `Markdown("ast")(text)` and `render(tokens, renderer="ast")`;
- `Markdown()(text)` and `render(tokens)`;
- `toc(text)`;
- `walk(tokens)`;
- custom plugin parse/render metadata observed through both AST and HTML replay.

## Rubric Shape

Unit rows remain focused on one-node or one-renderer contracts: public imports, isolated block nodes, isolated inline nodes, direct renderer tokens, simple plugin registration, and local error recovery. They still assert public names and fields where the packet promises them, but they do not try to simulate the system lifecycle through private token positions.

System rows now test material invariants:

- parse/tokens/AST/walk equivalence over one mixed tree;
- renderer replay idempotence and non-mutation;
- heading id/text agreement among tree, TOC, and parsed HTML;
- nested inline propagation through quote/list/table containers;
- custom plugin metadata consistency across tree, walk, AST replay, and HTML replay;
- AST tree replay through an HTML renderer;
- parse/render/parse stability on a reused parser;
- malformed syntax recovery without poisoning later parses;
- product-natural table boundary ordering;
- tight/loose list lifecycle and replay;
- task-list metadata plus normal inline item content;
- code literal boundaries across tree and parsed HTML.

## Fairness Risks

- `walk` and `render(tokens)` are new public surfaces, so future candidate packets must include them clearly; otherwise system rows would be underspecified.
- Exact HTML substring checks have been reduced, but some rows still compare direct HTML equality where replay equivalence is the point. That is acceptable only because both sides are produced by the candidate's own renderers.
- List loose-item behavior remains a compact Markdown compatibility edge. It is kept because it is product-natural lifecycle behavior, but failures should be interpreted as one capability cluster if they dominate a candidate report.
- Table ordering is fair only at block boundaries. Hidden variants should avoid exotic pipe escaping or CommonMark edge cases not described in the packet.
- Public token names are still asserted in unit rows. System rows should continue using guarded traversal so a single alias choice does not cascade into many false independent failures.

## Reference Gate

The canonical-tree v3 reference gate passed all 30 cases with 168/168 weighted score on 2026-06-28 using:

`py -3.11 tools\score_unit_system.py task\minimarkdown-realrepo-001\rubric.json --solution-dir runs\minimarkdown-realrepo-001\solution-reference --timeout 10 --json-out task\minimarkdown-realrepo-001\doc\score_reports\score_report_reference_canonical_tree_v3_20260628.json`

## Workspace Index V4 Enrichment

After v3 fresh runs, independent read-only subagents judged the single-document canonical-tree surface near-solved rather than accepted gap evidence. Codex scored 100.00% unit / 91.67% system and OpenHands DeepSeek V4 Pro scored 88.89% / 83.33%; the remaining losses were narrow list metadata, parser/block-boundary, or primitive-mixed roots.

The fair next move is a material public product scope, not hidden extra rows on the single-document parser. V4 therefore adds `MarkdownWorkspace`, a public multi-document lifecycle surface. The shared fact source is:

`workspace document set -> source text -> canonical token trees -> heading/link index -> TOC, links, backlinks, diagnostics, graph, render output, and export/import replay`

Public derived views:

- `paths()` for live document ids.
- `tokens(path)` and `render(path)` for per-document projections.
- `toc(path=None)` for heading projections across one document or the workspace.
- `links(path=None)` for relative document/anchor references.
- `backlinks(path, anchor=None)` as the reverse link projection.
- `diagnostics()` for missing documents and anchors.
- `graph()` for documents, headings, links, and diagnostics.
- `export()` / `import_snapshot()` for deterministic replay.

Expected gap mechanism: a candidate can pass unit primitives by adding the API and simple local parsing, yet fail system rows if update/remove/import flows leave stale headings, stale backlinks, inconsistent diagnostics, render output using different heading ids from TOC, or graph edges that are not inverse to backlinks.

Fairness constraints:

- Workspace behavior is public in the PRD; tests must not assume a private index or cache.
- Relative path and anchor rules are explicitly stated.
- Reference-style links remain a non-goal; only inline relative links and `#anchor` links are indexed.
- System rows should cluster repeated stale-index failures as one lifecycle root when judging gap evidence.
- Existing Qwen no-artifact/provider failures remain completion failures, not model-quality evidence.
