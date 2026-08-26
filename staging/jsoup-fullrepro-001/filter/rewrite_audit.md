# Rewrite Audit — jsoup-fullrepro-001

Oracle source: **generated_only** (Track B). No upstream test was copied or
rewritten; the upstream suite (~1263 test functions, largely same-package
white-box against tokenizer/tree-builder internals) was used only as a
behavior checklist.

Every oracle test was written directly against the spec's public surface and
validated empirically against the pinned 1.18.3 artifact before being pinned:

- 73 atomic tests across six files covering parse normalization, the CSS
  selector engine, DOM traversal, attribute/class management, text extraction
  and entities, and output settings.
- 33 integration tests across three files covering parse–select–extract
  workflows, mutate-then-serialize workflows with cross-view checks, and
  sanitization plus XML-mode pipelines.

Assertions pin only behavior stated in the spec: exact serialized markup where
the spec fixes layout (one-space indent default, inline-vs-block layout, void
element forms), entity repertoires per escape mode and charset, safelist
admission outcomes, selector result sets and order, and the declared exception
classes (`Selector.SelectorParseException`, `IllegalArgumentException`,
`IndexOutOfBoundsException`).

Every test imports only `org.jsoup` symbols listed in the spec's Public
Interface (enforced by the import lint; see `lint_result.txt`).
