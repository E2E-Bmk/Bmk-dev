# Judge Reaudit - 2026-07-03

This file records the Stage 5 judge-agent verdicts from the 2026-07-03 re-audit.
These verdicts supersede terminal-package-only `verify_task.py` results. The
mechanical verifier may be used as an exit checklist helper, but it is not a
judge verdict.

## Summary

| verdict | count |
|---|---:|
| QUALIFIED | 21 |
| BROKEN | 0 |
| CHEAT_DETECTED | 0 |
| INSUFFICIENT_EVIDENCE | 0 |

## QUALIFIED By Judge

| task | judge basis |
|---|---|
| alembic-migrations-fullrepro-001 | Repaired generated oracle import carrier and SQL-format assertion; final judge report `diagnosis_report_sql_repair_20260704.md` returned QUALIFIED with provenance inside candidate `solution_with_deps`, reference ceiling 50/50, and Gate D FULL. |
| beancount-ledger-fullrepro-001 | Repaired 51-test public-surface oracle; WSL score 44/51; reference 51/51; Gate A/B/D pass or acceptable partial; generated-only Gate C not applicable. |
| beancount-ledger-fullrepro-002 | Reopened task id with same repaired 51-test Beancount oracle; WSL score 44/51; reference 51/51; Gate A/B/D pass or acceptable partial. |
| boltons-coreutils-fullrepro-001 | Expanded failed 38-test rescope to 86-test oracle covering cache key, FrozenDict, iterutils, and urlutils gaps; judge report `diagnosis_report_expanded_20260704.md` returned QUALIFIED with reference 86/86, candidate 78/86, and Gate D PARTIAL acceptable. |
| coveragepy-fullrepro-001 | WSL fallback score 30/51; reference 51/51; preflight points to candidate output; Gate A/B pass and Gate D partial acceptable. |
| cookiecutter-fullrepro-001 | Repaired WSL 222-node carrier/dependencies and reran reference/candidate; judge report `diagnosis_report_repaired_20260704.md` returned QUALIFIED with solvability caveat, preflight pass, reference pass rate >=95%, and Gate D PARTIAL acceptable. |
| copier-template-fullrepro-001 | Repaired generated-only carrier and reran fresh 51-test WSL candidate score; judge report `diagnosis_report_fresh_20260704.md` returned QUALIFIED with reference 51/51, candidate 36/51, generated-only Gate C pass, and Gate D PARTIAL acceptable. |
| doit-taskrunner-fullrepro-001 | WSL no-BOM score 47/53; reference 53/53; dummy 0/53; generated-only Gate C pass; Gate D partial acceptable. |
| doit-taskrunner-fullrepro-002 | WSL score 47/53; reference 53/53; generated-only Gate C pass; no same-pass oracle mutation found. |
| dynaconf-settings-fullrepro-001 | Clean Stage 5 rejudge on frozen 51-test oracle returned QUALIFIED in `diagnosis_report_clean_rejudge_20260704.md`; WSL no-BOM score 36/51, reference 51/51, dummy 0/51, and Gate A/B/C/D pass without oracle edits. |
| dvc-fullrepro-001 | WSL rerun score 41/50; reference 50/50; REOPENED_S3 rerun chain before final QUALIFIED; Gate A/B/C/D pass or acceptable partial. |
| invoke-taskrunner-fullrepro-001 | WSL score 52/67; reference 67/67; upstream oracle; Gate A/B pass and Gate D partial acceptable. |
| mkdocs-sitebuild-fullrepro-002 | WSL score 38/50; reference 50/50; later 50-test WSL rejudge supersedes earlier retroactive expansion issue; Gate A/B pass and Gate D partial acceptable. |
| packaging-core-fullrepro-001 | Repaired-carrier WSL score 149 passed / 153 failed / 2 timeout; reference 5488/5488; Gate A/B/D pass; generated rows sampled and accepted. |
| pelican-sitegen-fullrepro-001 | Replaced private pelican.tests harness with 56-test public carrier; judge report `diagnosis_report_public_carrier_20260704.md` returned QUALIFIED with reference 56/56, candidate 40/56, Gate D PARTIAL acceptable, and 0 collection errors. |
| pre-commit-hooks-fullrepro-001 | Re-audit repair remapped 11 existing generated integration/system_e2e rows to `## Cross-View Invariants`; task-judge report `diagnosis_report_crossview_20260703.md` returned QUALIFIED with Gate 0/1/2/3 passing. |
| pre-commit-hooks-fullrepro-002 | WSL score 43/52; reference 52/52; generated-only Gate C pass; Gate D partial acceptable with Error Semantics covered. |
| sqlalchemy-fullrepro-001 | WSL score 25/50; reference 50/50; generated-only Gate C pass; Cross-View and Error Semantics covered. |
| tox-envrunner-fullrepro-001 | WSL score 11/51; reference 51/51; upstream_and_generated oracle; Gate A/B/D pass or acceptable partial. |
| tomlkit-fullrepro-001 | Rebuilt too-narrow/inconsistent oracle to 96 base nodeids / 195 expanded cases with public generated TOML item/document carrier; judge report `diagnosis_report_v4_20260704.md` returned QUALIFIED with reference 195/195 and candidate 106/195. |
| vcrpy-fullrepro-001 | Re-audit repair added four upstream public Error Semantics rows; combined WSL reference score 42/42 and candidate score 28/42; task-judge report `diagnosis_report_v6_20260703.md` returned QUALIFIED with Gate 0/1/2/3 passing. |

## BROKEN By Judge

| task | root judge failure | required route |
|---|---|---|

## Repair Order

1. Gate D coverage-only repairs: `vcrpy-fullrepro-001` and `pre-commit-hooks-fullrepro-001` are now QUALIFIED by judge.
2. REOPENED_S3/rerun repairs with stable oracle: `dynaconf-settings-fullrepro-001` and `cookiecutter-fullrepro-001` are now QUALIFIED by judge.
3. Fairness/carrier repairs: `alembic-migrations-fullrepro-001`, `copier-template-fullrepro-001`, and `pelican-sitegen-fullrepro-001` are now QUALIFIED by judge.
4. Lineage/oracle rebuilds: `tomlkit-fullrepro-001` and `boltons-coreutils-fullrepro-001` are now QUALIFIED by judge.
