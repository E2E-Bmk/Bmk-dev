# Candidate Run Diagnosis - gpt5.5-miette-fullrepro-001-specv2-20260903-002

Outcome: evidence_invalid

The scorer setup reached `cargo nextest run --no-run`, patched the oracle to the candidate crate, and then failed during compilation. The run is not a semantic score.

## Spec gaps found

1. `diagnostic!` named options: the oracle uses `labels = value`, but the spec named only code, severity, help, and URL options. The public macro accepts labels as metadata.
2. Concrete handler `render_report`: `JSONReportHandler`, `NarratableReportHandler`, and `GraphicalReportHandler` accept `&mut impl fmt::Write`, not `&mut fmt::Formatter`. The spec described the operation but did not state this public writer type precisely.
3. `MietteSpanContents::new` and `new_named`: the span parameter is `SourceSpan`. The spec only said the constructors create contents, which allowed a candidate to choose `impl Into<SourceSpan>` and make caller-side `.into()` ambiguous.

These gaps were patched into spec_v2, `clauses.md`, and the packet copy.

## Model-owned failures that remain

1. The derived `Diagnostic` implementation for lifetime-generic structs still emits invalid tokens for `DynamicHelp<'a>`.
2. The candidate makes `Diagnostic` require extra `as_any` and `as_any_mut` methods. The spec does not declare these methods, and manual `Diagnostic` impls are expected to compile with the declared method set.

## Revalidation

After patching the spec and packet:

- oracle import lint: `LINT_PASS`
- patched reference (M1): 62/62 passed
- clean upstream control (M2): failed exactly the three preregistered mutation witnesses:
  - `atomic::severity_default_is_advice`
  - `integration::json_absent_severity_renders_advice`
  - `integration::narrated_absent_severity_renders_advice`

Next candidate cleanroom: `candidate-runs/gpt5.5-miette-fullrepro-001-specv2-20260903-003`.
