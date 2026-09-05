# Pipeline State - miette-fullrepro-001

> Usage:
> - Only modify the Current block. Catalogue is read-only reference.
> - On every transition, update state, append one History row, and replace todo with the catalogue todo for the new state.
> - On loops, write state back to the loop target, reset todo, and increment the matching iter counter.
> - If an iter counter exceeds its cap, stop and report to the orchestrator.

---

## Current

```
state:      S4_CANDIDATE_RUN
stage:      5
spec_iter:  2
filter_iter: 0
eval_iter:  1
updated:    2026-09-05
functions_in_scope: 179
functions_kept: 40
functions_excluded: 139
oracle_count: 62
```

todo:
- [x] Stage 4 compile triage accepted eight public API/signature spec gaps.
- [x] Wrote `spec/spec_v2.md` and `spec/clauses_v2.md`.
- [x] Synced current `spec/clauses.md`, packet `spec.md`, and packet `task.json` to spec_v2.
- [x] Refreshed `filter/lint_result.txt` with `LINT_PASS`.
- [x] Refreshed `filter/reference_score.json` with 62/62 patched-reference pass.
- [x] Re-run Stage 3 import/map consistency against spec_v2 before creating a fresh Stage 4 candidate run.
- [x] Created cleanroom run `candidate-runs/gpt5.5-miette-fullrepro-001-specv2-20260903-002` after removing three spec_v2 signature errors.
- [x] Diagnosed candidate 002 compile failure as mixed evidence_invalid: three remaining public signature/macro spec gaps plus two model-owned implementation failures.
- [x] Patched spec_v2/clauses/packet for `diagnostic! labels`, concrete handler `fmt::Write` render targets, and `MietteSpanContents` constructor span types.
- [x] Corrected DebugReportHandler-specific `render_report` target to `fmt::Formatter` while leaving JSON/Narratable/Graphical handlers on `fmt::Write`.
- [x] Refreshed `filter/lint_result.txt` with `LINT_PASS`, patched reference with 62/62 pass, and clean-upstream M2 with exactly the three mutation witnesses failing.
- [x] Created cleanroom run `candidate-runs/gpt5.5-miette-fullrepro-001-specv2-20260903-003`.
- [x] Ran candidate agent using only the updated spec_v2 cleanroom public packet.
- [x] Scored the resulting solution with `harness/core/score_language.py`; run failed at oracle compile setup due model-owned derive lifetime handling, so no semantic score was recorded.
- [x] Stage 5 judge report written for candidate 003.
- [x] Candidate 003 classified as invalid evidence caused by model-owned derive lifetime compile failure.
- [ ] Run a fresh candidate sample against corrected `specv2-20260903-003` packet if a valid semantic score is still required.

---

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-09-03 | S1_SCREENING | S1_SELECTED | Selected: diagnostic fact model projects through trait metadata, derive expansion, report chain/downcast APIs, and graphical/narrated/JSON handlers; Stage 3 must filter exact-rendering and trybuild artifacts. |
| 2 | 2026-09-03 | S1_SELECTED | S3A_IMPORT_AUDIT | Stage 2 wrote spec_v1 for Rust public API, derive metadata, source spans, reports, handlers, and default-severity mutation. |
| 3 | 2026-09-03 | S3A_IMPORT_AUDIT | S3A_REWRITE | Read test-filter and spec2repo-gate-calibration; audited Rust upstream test files and kept 179 functions in scope for public-API rewrite/fairness processing. |
| 4 | 2026-09-03 | S3A_REWRITE | S3B_TRIGGER | Rewrote 71 public-API Rust tests, excluded 108 retained-file source-only functions, and verified compile-only collection; clean upstream fails exactly the three mutation witnesses. |
| 5 | 2026-09-03 | S3B_TRIGGER | S3C_GENERATE | Dummy gate compiled and ran; 31 dummy-passing tests discarded, leaving 40 scoreable tests and triggering Track B generation. |
| 6 | 2026-09-03 | S3C_GENERATE | S3_ORACLE_MERGE | Generated 22 tests; reference passes 22/22, dummy passes 0/22, merged count is 62 with 30 atomic and 32 integration. |
| 7 | 2026-09-03 | S3_ORACLE_MERGE | S4_SETUP | Split Rust oracle into atomic/integration crates, added 32 integration dependency annotations, verified no-run collection, and confirmed clean upstream M2 fails exactly the three mutation witnesses. |
| 8 | 2026-09-03 | S4_SETUP | S4_CANDIDATE_RUN | Assembled packet, refreshed Rust lint to LINT_PASS, patched reference passed 62/62, and created cleanroom run miette-fullrepro-001-specv1-20260903-001. |
| 9 | 2026-09-03 | S4_CANDIDATE_RUN | S4_EVAL_RUN | Candidate run gpt5.5-miette-fullrepro-001-specv1-20260903-001 was scored after fixing invalid registry provenance; corrected run resolves to candidate but fails oracle compile, recorded in score_diagnosis.md. |
| 10 | 2026-09-03 | S4_EVAL_RUN | S2_SPEC_DRAFT | Compile triage identified spec_v1 public API/signature gaps as the primary blocker, so evaluation was routed back to spec-writer. |
| 11 | 2026-09-03 | S2_SPEC_DRAFT | S3A_IMPORT_AUDIT | spec_v2 added SourceSpan/LabeledSpan accessor types, Report context/Deref API, ReportHandler::render_report, diagnostic! options, MietteError I/O conversion, ThemeCharacters string fields, and derive label forms; lint and patched reference gate pass. |
| 12 | 2026-09-03 | S3A_IMPORT_AUDIT | S4_CANDIDATE_RUN | spec_v2 map consistency, lint, and patched-reference gates passed; created fresh cleanroom gpt5.5-miette-fullrepro-001-specv2-20260903-001. |
| 13 | 2026-09-03 | S4_CANDIDATE_RUN | S4_CANDIDATE_RUN | Corrected spec_v2 follow-up errors: removed inherent Report::wrap_err_with, removed bare severity macro form, and corrected ReportHandler required method to debug; refreshed lint/reference gates and created cleanroom gpt5.5-miette-fullrepro-001-specv2-20260903-002. |
| 14 | 2026-09-03 | S4_CANDIDATE_RUN | S4_CANDIDATE_RUN | Candidate 002 failed during compile setup; patched remaining public spec gaps for diagnostic labels, handler fmt::Write render targets, and MietteSpanContents span parameter types; lint, patched reference, and clean-upstream mutation control pass; created cleanroom gpt5.5-miette-fullrepro-001-specv2-20260903-003. |
| 15 | 2026-09-05 | S4_CANDIDATE_RUN | S4_CANDIDATE_RUN | Corrected follow-up spec_error: DebugReportHandler::render_report uses fmt::Formatter while JSON/Narratable/Graphical render_report use fmt::Write; refreshed lint/reference/M2 controls and resynced cleanroom 003 packet. |
| 16 | 2026-09-05 | S4_CANDIDATE_RUN | S4_CANDIDATE_RUN | Candidate 003 completed implementation; scorer reached candidate-patched oracle compile and failed only on derive lifetime-generic diagnostic support, a model-owned compile blocker; recorded score_diagnosis.md and left evaluation disposition pending. |
| 17 | 2026-09-05 | S5_JUDGE | S4_CANDIDATE_RUN | Stage 5 judge classified candidate 003 as BROKEN_EVIDENCE rather than a semantic score: provenance points to candidate workspace, patched reference passes 62/62, M2 is contained, and the only observed blocker is model-owned derive lifetime support. |
