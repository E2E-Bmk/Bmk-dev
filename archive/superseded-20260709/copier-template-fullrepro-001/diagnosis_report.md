# Diagnosis Report - copier-template-fullrepro-001

Status: QUALIFIED
Date: 2026-07-03
Mode: user-authorized exception on 2026-07-03
Candidate run: $run
Score file: 	asks/copier-template-fullrepro-001/score_result.json

## Preflight output

`	ext
python -c "import copier; print(copier.__file__)"
/mnt/g/research/01_agents/swe-e2e/Bmk-dev/candidate-runs/codex-copier-specv1-20260701-001/solution/copier/__init__.py
`

The import provenance is recorded as pointing at the candidate solution for this exception package. This report is intentionally marked as a user-authorized exception and is not represented as an ordinary uninterrupted Stage 5 pass.

## Hard Checks

Platform: PASS for the exception ledger. The copied score has platform $(@{platform=Linux-5.15.153.1-microsoft-standard-WSL2-x86_64-with-glibc2.31; python_version=3.11.15 (main, Mar 24 2026, 22:50:29) [Clang 22.1.1 ]; timeout_seconds=180; remove_paths=System.Object[]; source_repo=/mnt/g/research/01_agents/swe-e2e/Bmk-dev/.tmp/copier-public-oracle-carrier-iter2; solution_dir=/mnt/g/research/01_agents/swe-e2e/Bmk-dev/candidate-runs/codex-copier-specv1-20260701-001/solution; nodeids=/mnt/g/research/01_agents/swe-e2e/Bmk-dev/wip/copier-template-fullrepro-001/filter/kept_nodeids.txt; taxonomy=/mnt/g/research/01_agents/swe-e2e/Bmk-dev/wip/copier-template-fullrepro-001/filter/taxonomy.jsonl; run_dir=/mnt/g/research/01_agents/swe-e2e/Bmk-dev/candidate-runs/codex-copier-specv1-20260701-001/score-work-wsl-filter51; grouped_results=; summary=; pass_rate_excluding_skips=0.6862745098039216; by_layer=; cases=System.Object[]}.platform) and does not contain Windows.

Reference solvability: accepted from the existing reference evidence under wip/copier-template-fullrepro-001/filter/ and the restored task artifacts.

## Candidate Score

Summary: passed=35, failed=16, collection_error=, total=51.

## Gate D - Coverage Gap Audit

Coverage verdict: PARTIAL, accepted under user-authorized exception on 2026-07-03. Any remaining coverage or carrier caveats are preserved as exception context rather than hidden.

## Verdict

QUALIFIED under user-authorized exception on 2026-07-03.
