# Rewrite Audit — jsonpath-fullrepro-001

Oracle source: **generated_only** (Track B). No upstream test was copied or
rewritten; the upstream suite (~1200 test functions, heavily tied to internal
token/provider classes and multi-provider matrices) was used only as a
behavior checklist.

Every oracle test was written directly against the spec's public surface and
validated empirically against the pinned 2.9.0 artifact before being pinned:

- 85 atomic tests across nine files covering path grammar constructs (dot and
  bracket forms, indexes, slices, unions, wildcards, deep scan), the loaded
  document model types, inline filters and the Criteria/Filter builders,
  aggregate functions, parse and DocumentContext projections, compiled paths,
  write operations, configuration options, and the declared error semantics.
- 31 integration tests across three files covering entry-point agreement
  (static / compiled / context), option-driven result reshaping with re-read
  consistency (AS_PATH_LIST, ALWAYS_RETURN_LIST, suppression composition,
  REQUIRE_PROPERTIES), and write–read coherence across every projection.

Assertions pin only behavior stated in the spec: evaluated values and their
runtime types, match order, normalized path strings, mutated document
projections, the declared exception classes (`PathNotFoundException`,
`InvalidPathException`, `InvalidJsonException`, `InvalidModificationException`
under `JsonPathException`, plus `IllegalArgumentException` for null/empty
path text), and the normalized-path naming in failure messages.

Every test imports only `com.jayway.jsonpath` symbols listed in the spec's
Public Interface (enforced by the import lint; see `lint_result.txt`).
