# Rewrite Audit — snakeyaml-engine-fullrepro-001

Oracle source: **generated_only** (Track B). No upstream test was copied or
rewritten; the upstream suite (~420 test functions, many exercising internal
scanner/parser classes) was used only as a behavior checklist.

Every oracle test was written directly against the spec's public surface and
validated empirically against the pinned 2.9 artifact before being pinned:

- 66 atomic tests across six files covering load object mapping, schema-driven
  scalar resolution (JSON default vs core), default dump projection, dump
  presentation settings, the compose node model, and load settings plus error
  semantics.
- 27 integration tests across three files covering load–dump round trips,
  compose/load cross-view agreement, and settings interactions spanning both
  pipelines.

Assertions pin only behavior stated in the spec: exact dumped text where the
spec fixes presentation (flow/block layout, quoting of ambiguous strings,
canonical form, markers, indentation, wrapping), loaded Java types and values
per schema, node tags and structure, and the declared exception hierarchy
(`ScannerException`/`ParserException`/`DuplicateKeyException` under
`MarkedYamlEngineException` under `YamlEngineException`) with positional marks.

Every test imports only `org.snakeyaml.engine` symbols listed in the spec's
Public Interface (enforced by the import lint; see `lint_result.txt`).
