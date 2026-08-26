# Rewrite Audit — javapoet-fullrepro-001

Oracle source: **generated_only** (Track B). No upstream test was copied or
rewritten; the upstream suite (365 test functions under
`src/test/java/com/squareup/javapoet`) was used only as a behavior checklist
to select which documented behaviors deserve coverage.

Every oracle test was written directly against the spec's public surface:

- 61 atomic tests across six files covering the format language, the type-name
  model, class-name navigation, method/field/parameter/annotation emission,
  type declarations, and name allocation.
- 30 integration tests across three files covering compilation-unit assembly
  and import resolution, multi-object generation workflows, and cross-view
  invariants (equality, `toBuilder` round trips, `writeTo`/`toString`
  agreement).

Assertions pin only behavior stated in the spec: exact rendered text where the
spec fixes layout (2-space indent, import sorting, blank-line separation),
`IllegalArgumentException`/`IllegalStateException`/`UnsupportedOperationException`
exactly where Error Semantics declares them, and equality/round-trip laws from
State Model and Cross-View Invariants.

Every test imports only `com.squareup.javapoet` symbols listed in the spec's
Public Interface (enforced by the import lint; see `lint_result.txt`).
