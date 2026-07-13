# Current Skill Judge Audit - beancount-ledger-fullrepro-002

Audit date: 2026-07-04

Verdict: QUALIFIED.

This task is the clean successor task id for the repaired 51-test Beancount public-surface oracle. It reuses the candidate run `codex-beancount-specv1-20260701-001` and the same repaired oracle evidence that should not be double-counted under predecessor `beancount-ledger-fullrepro-001`.

## Preflight output

Command:

```powershell
$env:PYTHONPATH='G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-beancount-specv1-20260701-001\solution'; python -c "import beancount; print(beancount.__file__)"
```

Literal output:

```text
G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-beancount-specv1-20260701-001\solution\beancount\__init__.py
```

The import provenance points inside the candidate solution directory.

## Hard-check evidence

- Candidate run: `candidate-runs/codex-beancount-specv1-20260701-001/score_result_wsl_filter51.json`.
- Candidate score: 44 passed, 7 failed, 51 total; no collection errors.
- Reference score: `wip/beancount-ledger-fullrepro-002/filter/reference_score.json`, 51 passed / 51 total.
- Dummy gate evidence is recorded in `wip/beancount-ledger-fullrepro-002/filter/dummy_gate_report.json` as 0/51 dummy passes.
- Candidate failures are behavioral public-surface gaps: loader decorators, account helper edge behavior, lifecycle getter ordering, source-aware formatting, custom value representation, and raw plugin validation mode.

## Gate D Coverage Gap Audit

Coverage counts are exact primary/explicit mappings from `filter/spec_test_map.md` to H2/H3 headings in `spec/spec_v1.md`.

| spec section | covered rows | impact | recommendation |
|---|---:|---|---|
| Product Overview | 0 | narrative, non-behavioral | no gating action |
| Scope | 0 | boundary text | no gating action |
| Public API | 0 | umbrella section; child public API sections covered | no gating action |
| Behavioral Sections | 0 | umbrella section; child behavior sections covered | no gating action |
| Account Names and Account Types | 0 | secondary behavior, partly represented by Account Helpers | optional future enrichment |
| Inventories and Balances | 0 | secondary behavior, partly represented by Inventories | optional future enrichment |
| Command-Line Tools | 0 | secondary CLI surface uncovered | optional future enrichment |
| Representative Workflows | 0 | umbrella workflow section | no gating action |
| Load, Inspect, Realize, and Value a Ledger | 0 | workflow is indirectly covered across Loading, Prices, Realized Accounts | optional future enrichment |
| Check and Format from the Command Line | 0 | CLI workflow uncovered | optional future enrichment |
| Write a Plugin | 0 | plugin workflow is partially covered by Plugins / Plugins and Transformations | optional future enrichment |
| Non-Goals | 0 | boundary text | no gating action |
| Evaluation Notes | 0 | benchmark notes | no gating action |

Core sections are not empty: `Error Semantics` has 3 covered rows and `Cross-View Invariants` has 5 covered rows. State/lifecycle behavior is represented by Loading Ledgers, Ledger Loading and Validation, Account and Entry Getters, and Realized Accounts.

Coverage verdict: PARTIAL, acceptable. No unresolved core GAP blocks qualification.

## Conclusion

`beancount-ledger-fullrepro-002` is QUALIFIED under the current task-judge skill. It is the Beancount task id that should be counted.

