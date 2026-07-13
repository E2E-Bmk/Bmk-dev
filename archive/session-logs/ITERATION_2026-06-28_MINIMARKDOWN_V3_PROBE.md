# MiniMarkdown V3 Probe

Date: 2026-06-28

## Purpose

After the failure-audit round, MiniMarkdown was the clearest candidate for a principled redesign: system tests should force one canonical parsed token tree to feed AST rendering, HTML rendering, TOC projection, and plugin projections.

A read-only task-builder subagent proposed five v3 system-case shapes:

- rich heading projection across parse, AST, HTML, and TOC
- AST token replay through `HTMLRenderer`
- one plugin matrix combining strikethrough, task list, table, links, and inline nesting
- renderer/TOC calls do not mutate parsed public tokens
- table boundary classification before inline parsing

The cases avoid private implementation structures and mostly compare semantic projections rather than exact full-document HTML.

## Probe Result

The proposed cases were run manually as probes against:

- `runs/minimarkdown-realrepo-001/solution-reference`
- `runs/minimarkdown-realrepo-001/solution-codex-subagent-redesign-v2-001`
- `runs/minimarkdown-realrepo-001/solution-openhands-deepseek-v4-pro-001`

| Probe | Reference | Codex redesign-v2 | OpenHands DeepSeek |
|---|---|---|---|
| rich heading projection | pass | pass | error in `toc` |
| AST replay through HTMLRenderer | pass | pass | timeout |
| plugin matrix | pass | pass | timeout |
| no token mutation | pass | pass | timeout |
| table boundary before inline parsing | pass | pass | timeout |

## Interpretation

These are the natural v3 invariants suggested by the task-builder and by `gap-invariant-task-builder`: a shared parsed document tree with AST, HTML, TOC, and plugin-derived views.

They do not separate Codex redesign-v2 from the reference. Adding them would mostly create additional DeepSeek failures, but DeepSeek already has broad primitive/API/schema failures on this task. That would not satisfy the benchmark gate that most system loss be compositional rather than primitive, timeout, or cascade.

## Decision

Do not modify MiniMarkdown v2 into this v3 rubric merely to increase numeric gap. Treat MiniMarkdown as solved for the current Codex population unless a materially deeper, product-natural Markdown lifecycle is identified.

Acceptable future enrichment would need a new public workflow beyond parser/render/plugin projection, such as incremental document indexing, link/heading reference index maintenance, or multi-document include/rewrite lifecycle. Small variations of the current canonical-token-tree tests are insufficient.
