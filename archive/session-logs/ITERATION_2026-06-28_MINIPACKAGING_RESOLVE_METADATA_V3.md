# MiniPackaging Resolve Metadata V3 Iteration

Date: 2026-06-28

## What Changed

Subagent Feynman implemented a MiniPackaging redesign centered on a public candidate-owned resolver API:

`resolve_metadata(roots, candidates, environment=None, requested_extras=None, prereleases=None)`

The shared fact source is the local metadata graph produced from root requirements, candidate records, markers, specifiers, extras, URLs, environment, and prerelease policy. The public derived views are `selected`, `excluded`, `edges`, `dependents`, `requested_extras`, and `requirements`.

Gauss performed a read-only fairness audit and judged the direction structurally fair but pending fresh runs. The audit did not find a dominant private-shape, exact-text, arbitrary-order, or hidden-resolver risk.

## Scores

| Candidate | Unit | System | Gap | Status |
|---|---:|---:|---:|---|
| reference-resolve-metadata-v3 | 100.00 | 100.00 | 0.00pp | reference pass |
| codex-subagent-resolve-metadata-v3-001 | 89.47 | 100.00 | -10.53pp | no accepted gap |
| openhands-deepseek-v4-pro-resolve-metadata-v3-001 | 57.89 | 50.00 | 7.89pp | below gate |
| openhands-qwen-resolve-metadata-v3-001 | 0.00 | 0.00 | 0.00pp | no artifact / scaffold launch failure |

Score reports:

- `task/minipackaging-realrepo-001/doc/score_reports/score_report_reference_resolve_metadata_v3_20260628.json`
- `task/minipackaging-realrepo-001/doc/score_reports/score_report_codex_subagent_resolve_metadata_v3_001_20260628.json`
- `task/minipackaging-realrepo-001/doc/score_reports/score_report_openhands_deepseek_v4_pro_resolve_metadata_v3_001_20260628.json`
- `task/minipackaging-realrepo-001/doc/score_reports/score_report_openhands_qwen_resolve_metadata_v3_001_20260628.json`

## Provenance Notes

- Codex subagent was instructed to read only `task/minipackaging-realrepo-001/prd.md` and write only `runs/minipackaging-realrepo-001/solution-codex-subagent-redesign-v3-001/minipackaging.py`.
- OpenHands + DeepSeek produced a scoreable `minipackaging.py` artifact under `solution-openhands-deepseek-v4-pro-resolve-metadata-v3-001`.
- The Qwen v3 OpenHands attempt did not create the requested solution directory or `minipackaging.py`. The 0/0 JSON score is an accounting artifact caused by missing module import, not a functional comparison.
- Two direct `--task` OpenHands attempts failed argument parsing because the large task text was split into subcommand-looking tokens. These are scaffold launch failures and are excluded from model-order evidence.

## Interpretation

The redesigned system layer now measures the right kind of object: one shared dependency metadata graph with redundant public projections. However, the fresh evidence still does not satisfy the candidate gate. Codex solves every system row while missing only unit primitives, and DeepSeek's system drop is 7.89pp, below the 15pp threshold.

Current decision: keep this as a useful construction pattern and negative result, not a promoted benchmark task.
