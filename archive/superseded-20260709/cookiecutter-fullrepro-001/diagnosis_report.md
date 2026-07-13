# cookiecutter-fullrepro-001 Diagnosis Report

user-authorized exception on 2026-07-03: this report repairs the already-exported task package after a retroactive Gate D oracle supplement from 213 to 222 nodeids. The candidate was not re-run against the 9 supplemental tests; this is explicitly recorded as an authorized exit-repair exception, not a normal SKILL transition.

## Preflight output

```text
cookiecutter.__file__=/mnt/g/research/01_agents/swe-e2e/Bmk-dev/candidate-runs/codex-cookiecutter-specv2only-20260629-001/output/cookiecutter/__init__.py
```

The import provenance points inside the candidate solution directory. Historical corrected scoring also recorded the remote Linux candidate path `/root/autodl-tmp/swe-e2e/Bmk-dev/results/codex-subagent/cookiecutter-fullrepro-001/specv2only-20260629-001/output/cookiecutter/__init__.py` with `--remove-path cookiecutter` and `--remove-path cookiecutter.egg-info`.

## Candidate score platform

Accepted score artifact: `tasks/cookiecutter-fullrepro-001/score_result.json`, reconstructed from `candidate-runs/codex-cookiecutter-specv2only-20260629-001/codex_specv2only_score_report.md` under the user-authorized exception. The platform field is Linux remote scoring text and contains no Windows path. Candidate score: 66 passed / 264 expanded cases, pass_rate_excluding_skips 25.38%.

## Reference solvability

Original reference score: `tasks/cookiecutter-fullrepro-001/reference_score.json`. Retroactive generated supplement gate: `wip/cookiecutter-fullrepro-001/filter/reference_score_retro_gate_d_generated.json`, 9/9 passed. The terminal oracle now has 222 base nodeids and `wip/cookiecutter-fullrepro-001/PIPELINE_STATE.md` records `oracle_count: 222`.

## Gate D - Coverage Gap Audit

Coverage verdict: PARTIAL. The retroactive `wip/cookiecutter-fullrepro-001/judge/diagnosis_report.md` records 222 kept tests after supplementing Gate D coverage. Remaining zero-coverage rows are narrative/boundary sections (`Product Overview`, `Non-Goals`, `Evaluation Notes`), not core workflow, error, or cross-view invariant sections. `Cross-View Invariants` has 9 covered rows.

## Verdict

QUALIFIED under the user-authorized exception on 2026-07-03. Terminal task artifacts were refreshed from the WIP oracle so `kept_nodeids.txt`, `taxonomy.jsonl`, and `spec_test_map.md` agree at 222 base nodeids.
