# Stage 5 Judge Report - miette-fullrepro-001

Run: `candidate-runs/gpt5.5-miette-fullrepro-001-specv2-20260903-003`

Verdict: `BROKEN_EVIDENCE`

This is not a task-validity failure and not a spec gap. The candidate run reached Rust oracle compilation with the candidate crate selected, then failed to compile because the candidate's derive macro mishandles lifetime-generic diagnostics. Per the workflow rule for non-compiling candidates, the run is not a semantic score and cannot be used for QUALIFIED scoring evidence.

## Preflight output

Command:

```bash
cd /mnt/g/aaai2026/bmk-dev/candidate-runs/gpt5.5-miette-fullrepro-001-specv2-20260903-003/scorer_run/oracle
cargo metadata --format-version 1 2>/dev/null | python3 -c 'import json,sys; d=json.load(sys.stdin); print([{"name":p["name"],"version":p["version"],"manifest_path":p["manifest_path"],"source":p.get("source")} for p in d["packages"] if p["name"]=="miette"])'
```

Output:

```text
[{'name': 'miette', 'version': '0.1.0', 'manifest_path': '/mnt/g/aaai2026/bmk-dev/candidate-runs/gpt5.5-miette-fullrepro-001-specv2-20260903-003/scorer_run/workspace/Cargo.toml', 'source': None}]
```

The resolved `manifest_path` points inside the candidate run workspace. The scorer did not resolve `miette` from crates.io, the upstream checkout, or the oracle tree.

## Anti-cheat scan

The cleanroom prompt restricted the candidate to:

- `candidate-runs/gpt5.5-miette-fullrepro-001-specv2-20260903-003/public_packet`
- `candidate-runs/gpt5.5-miette-fullrepro-001-specv2-20260903-003/solution`

No forbidden source, oracle, score, prior-run, or map access was observed in the available artifacts. A full implementation trajectory log was not available, so this scan is limited to the prompt, produced files, and scorer provenance.

## Reference solvability

The patched reference passed the complete oracle:

```json
{"passed": 62, "total": 62}
```

Layer split:

```json
{"atomic": {"passed": 30, "total": 30}, "integration": {"passed": 32, "total": 32}}
```

The clean upstream mutation control failed exactly the preregistered mutation witnesses:

- `atomic::severity_default_is_advice`
- `integration::json_absent_severity_renders_advice`
- `integration::narrated_absent_severity_renders_advice`

This confirms the oracle is solvable by the patched reference and the mutation is contained.

## Candidate result

The score JSON reports setup failure for all roots:

```json
{
  "summary": {"setup_error": 62, "total": 62},
  "by_layer": {
    "atomic": {"setup_error": 30, "total": 30},
    "integration": {"setup_error": 32, "total": 32}
  }
}
```

The platform is Linux/WSL:

```text
Linux-5.15.167.4-microsoft-standard-WSL2-x86_64-with-glibc2.39
```

Because `cargo nextest run --no-run` failed, this run has no pass rate and no layer score for benchmark characterization.

## Protocol issue audit

No new spec gap is indicated by this run.

Prior Stage 4 corrections already addressed the compile-visible API gaps:

- `diagnostic!` named metadata includes `labels = value`.
- `JSONReportHandler`, `NarratableReportHandler`, and `GraphicalReportHandler` accept a mutable `fmt::Write` target for `render_report`.
- `DebugReportHandler` accepts a mutable `fmt::Formatter` target for `render_report`.
- `MietteSpanContents::new` and `new_named` accept a concrete `SourceSpan` parameter.

The candidate compiled past the earlier error sites for `diagnostic! labels`, handler writer targets, and `MietteSpanContents` span inference. The remaining errors are all derive lifetime compatibility failures.

## Gate A - Spec Mapping Spot-Check

| nodeid | assertion summary | spec_section | verdict |
|---|---|---|---|
| `rewritten_upstream_tests::severity_default_is_advice` | missing severity defaults to `Advice` | `Diagnostic Protocol` | derivable |
| `rewritten_upstream_tests::miette_span_contents_returns_stored_values` | constructed span contents return stored bytes, `SourceSpan`, line, column, and line count | `Diagnostic Protocol` | derivable |
| `generated_tests::generated_diagnostic_macro_sets_labels` | `diagnostic!` accepts `labels = value` metadata | `Diagnostic Construction` | derivable |
| `generated_tests::generated_derive_help_field_is_dynamic` | derive reads dynamic `#[help]` field values | `Diagnostic Construction` | derivable |
| `rewritten_upstream_tests::json_causes_use_diagnostic_source_first` | JSON causes prefer `diagnostic_source` over ordinary source | `Report Rendering` | derivable |
| `generated_tests::generated_report_wrap_err_forwards_inner_code` | wrapped reports preserve inner diagnostic metadata across views | `Cross-View Invariants` | derivable |

The sampled mappings are section-correct and behaviorally derivable from the spec.

## Gate B - Failure Pattern Audit

Failure cluster:

- Layer: compile setup before atomic/integration execution
- Root cause dimension: `api-surface`
- Failing surface: derive macro expansion for `#[derive(Diagnostic)]` on `struct DynamicHelp<'a> { #[help] help: &'a str }`
- Rust errors: E0308, E0478, E0803 lifetime incompatibilities emitted from the candidate derive macro

The spec requires the derive macro to preserve generics and where-clauses. The failure is a model implementation defect, not an oracle or spec defect. Since it occurs during compile setup, it still invalidates this score as evidence.

## Gate C - Generated Oracle Spot-Check

The oracle is not generated-only. It is an upstream rewrite plus generated expansion. Gate C does not apply.

## Gate D - Coverage Gap Audit

| spec section | uncovered behaviors | impact | recommendation |
|---|---|---|---|
| Core behavior sections | none observed | no coverage gap | continue with current oracle |

Coverage verdict: `FULL`

Covered core sections include `Diagnostic Protocol`, `Diagnostic Construction`, `Reports and Context`, `Report Rendering`, `Error Semantics`, `Cross-View Invariants`, and `Public Interface`.

## Gate E - Static Quality Gate

Not run to terminal qualification because this candidate run does not produce a valid semantic score. Existing prerequisite evidence remains:

- `filter/lint_result.txt` first line: `LINT_PASS`
- patched reference: 62/62 passed
- clean upstream mutation control: exactly 3 preregistered mutation witnesses failed

## Gate F - Spec Phrasing Quality

No phrasing blocker was identified in the patched clauses relevant to this judge pass. The candidate-visible packet contains the spec body only and does not expose the internal header.

## Final disposition

This candidate run is invalid evidence because it does not compile against the oracle. The task artifacts remain usable: lint passes, the patched reference passes 100%, and the mutation control is contained. The next workflow action is to run a fresh candidate sample against the corrected `specv2-20260903-003` packet if a valid score is still required.
