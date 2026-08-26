# Rewrite Audit — univocity-parsers-fullrepro-001

Oracle source: **generated_only** (Track B). No upstream test was copied or
rewritten; the upstream suite (~1000+ test functions, dominated by issue-number
regression classes and bean-annotation processing outside this spec's scope)
was used only as a behavior checklist.

Every oracle test was written directly against the spec's public surface and
validated empirically against the pinned 2.9.1 artifact before being pinned:

- 59 atomic tests across nine files covering CSV parsing (quoting, escape
  doubling, dialect characters, comments, trimming, line-separator and format
  detection), null/empty substitution and the maxCharsPerColumn safety limit,
  streaming (parseNext / stopParsing / iterate / currentRecord), header
  extraction and column selection with and without reordering, typed record
  access and record metadata, CSV writing (conditional quoting, quote-all,
  null substitution, writeRowToString), the TSV escape dialect, fixed-width
  layouts (positional and named fields, alignment, padding, header rows), and
  session lifecycle (fresh sessions, writer accumulation, settings capture at
  construction).
- 31 integration tests across three files covering write-then-parse round
  trips in all three dialects (including the documented null/empty collapse
  and the padded fixed-width round trip), agreement between parseAll /
  parseNext / iterate / record projections plus header and currentRecord
  invariants in every format, and option-driven reshaping (selection order,
  reordering-disabled index preservation, records under selection, detected
  formats feeding writers).

Assertions pin only behavior stated in the spec: exact writer output for
documented dialects and padding rules, the documented substitution defaults,
and the declared exception classes (`TextParsingException`,
`NumberFormatException`, `IllegalArgumentException`).

Every test imports only `com.univocity.parsers` symbols listed in the spec's
Public Interface (enforced by the import lint; see `lint_result.txt`).
