# Oracle Atomic Import Cleanup Results

Date: 2026-07-14

## Decision Rule

An import path is promised only when it appears in the spec's `Installable Surface` or an equivalent explicit public import-list section. Behavioral prose that merely mentions a module does not make that module path part of the installable contract.

Equivalent sections used for specs with different headings:

- Cookiecutter: `Public Interfaces` -> `Python API`
- Dynaconf: `Public Import Surface`
- Packaging: `Package Shape`
- Boltons: the H2 public module headings such as `boltons.cacheutils`

All 34 `oracle/test_atomic.py` files were parsed and checked against those sections. After cleanup, no atomic file imports the target package from an unpromised submodule path.

## Changes

| task | atomic before | atomic after | removed now | result |
|---|---:|---:|---:|---|
| fsspec-filesystem-fullrepro-001 | 23 | 8 | 15 | Removed tests bound to `fsspec.implementations.*`; removed the obsolete autouse memory carrier. |
| invoke-taskrunner-fullrepro-001 | 30 | 29 | 1 | Removed the test importing `invoke.exceptions.UnknownFileType`; the spec promises the root export, not this carrier path. |
| mkdocs-sitebuild-fullrepro-002 | 25 | 6 | 19 | Removed tests bound to undocumented `mkdocs.__main__`, structure, theme, search, and utils carriers. |
| pre-commit-hooks-fullrepro-002 | 19 | 7 | 12 | Kept only atomic tests using the documented `pre_commit.main.main` path. |
| marshmallow-schema-fullrepro-001 | 26 | 26 | 0 | Removed an unused module-level `marshmallow.experimental.context` import; no test referenced it. |
| cookiecutter-fullrepro-001 | 2 | 2 | 0 in this pass | Confirmed `cookiecutter.main.cookiecutter` in `Public Interfaces -> Python API`; synchronized the inherited 9-test oracle metadata and recorded the prior 7-test cleanup. |

New test-function removals in this pass: **47**.

## Counts By Task

`Scoreable` is `stats.atomic + stats.integration + stats.system_e2e`. `Physical functions` counts `test_*` functions physically present in the two oracle files; this can be larger when excluded/unmapped functions remain in a carrier file.

| task | atomic | integration | system_e2e | scoreable | physical functions | cleanup removed | count status |
|---|---:|---:|---:|---:|---:|---:|---|
| attrs-classes-fullrepro-001 | 53 | 12 | 16 | 81 | 81 | 0 | OK |
| bandit-securityscan-fullrepro-001 | 24 | 26 | 11 | 61 | 61 | 0 | OK |
| beancount-ledger-fullrepro-002 | 22 | 21 | 8 | 51 | 54 | 0 | 3 unscored physical functions |
| boltons-coreutils-fullrepro-001 | 38 | 24 | 24 | 86 | 172 | 0 | metadata mismatch: `oracle.count=85` |
| cattrs-converters-fullrepro-001 | 39 | 18 | 5 | 62 | 62 | 0 | OK |
| cookiecutter-fullrepro-001 | 2 | 2 | 5 | 9 | 9 | 7 prior | **below 50** |
| copier-template-fullrepro-001 | 22 | 12 | 17 | 51 | 51 | 0 | OK |
| coveragepy-fullrepro-001 | 20 | 17 | 14 | 51 | 51 | 0 | OK |
| dateparser-dates-fullrepro-001 | 55 | 12 | 5 | 72 | 72 | 0 | OK |
| dbt-core-fullrepro-001 | 4 | 27 | 23 | 54 | 54 | 0 | OK |
| diskcache-cache-fullrepro-001 | 35 | 24 | 7 | 66 | 67 | 0 | 1 unscored physical function |
| doit-taskrunner-fullrepro-002 | 16 | 28 | 7 | 51 | 53 | 0 | 2 unscored physical functions |
| dvc-fullrepro-001 | 14 | 27 | 9 | 50 | 51 | 0 | at floor; 1 unscored physical function |
| dynaconf-settings-fullrepro-001 | 14 | 30 | 5 | 49 | 51 | 0 | **below 50** |
| fsspec-filesystem-fullrepro-001 | 8 | 17 | 18 | 43 | 43 | 15 | **below 50; needs at least 7 new tests** |
| h2-protocol-fullrepro-001 | 22 | 26 | 7 | 55 | 55 | 0 | OK |
| httpcore-transport-fullrepro-001 | 15 | 35 | 14 | 64 | 65 | 0 | 1 unscored physical function |
| httpx-client-fullrepro-001 | 40 | 26 | 12 | 78 | 78 | 0 | OK |
| invoke-taskrunner-fullrepro-001 | 29 | 22 | 15 | 66 | 66 | 1 | OK after cleanup |
| jrnl-journal-fullrepro-002 | 9 | 109 | 102 | 220 | 12 | 0 | **severe stale metadata; count is not trustworthy** |
| kedro-pipeline-fullrepro-001 | 50 | 20 | 1 | 71 | 71 | 0 | OK |
| luigi-workflow-fullrepro-001 | 26 | 13 | 21 | 60 | 60 | 0 | OK |
| marshmallow-schema-fullrepro-001 | 26 | 19 | 24 | 69 | 70 | 0 | 1 excluded physical function |
| mkdocs-sitebuild-fullrepro-002 | 6 | 15 | 10 | 31 | 31 | 19 | **below 50; needs at least 19 new tests** |
| nbformat-notebook-fullrepro-001 | 36 | 27 | 4 | 67 | 69 | 0 | 2 unscored physical functions |
| packaging-core-fullrepro-001 | 10 | 3 | 10 | 23 | 23 | 0 | **below 50; stale `oracle.count=133`** |
| pelican-sitegen-fullrepro-001 | 29 | 21 | 6 | 56 | 56 | 0 | Installable Surface explicitly promises the retained paths |
| pgqueuer-fullrepro-001 | 25 | 17 | 15 | 57 | 57 | 0 | OK |
| pre-commit-hooks-fullrepro-002 | 7 | 19 | 14 | 40 | 47 | 12 | **below 50; needs at least 10 new scoreable tests** |
| requests-cache-fullrepro-001 | 21 | 22 | 15 | 58 | 58 | 0 | OK |
| sqlalchemy-fullrepro-001 | 15 | 27 | 6 | 48 | 48 | 0 | **below 50** |
| starlette-asgi-fullrepro-001 | 22 | 31 | 11 | 64 | 64 | 0 | OK |
| tox-envrunner-fullrepro-001 | 9 | 27 | 10 | 46 | 51 | 0 | **below 50** |
| vcrpy-fullrepro-001 | 8 | 20 | 13 | 41 | 8 + missing integration file | 0 | **below 50; oracle artifact incomplete** |

Metadata scoreable total: **2051** across 34 tasks. **25** tasks are at or above 50; **9** are below 50.

## Verification

- Parsed all 34 atomic files with Python AST.
- Strict public-surface import audit: 34 tasks checked, 0 unpromised target-package submodule imports remain.
- Reference atomic runs passed for all changed test sets: Cookiecutter 2/2, fsspec 8/8, Invoke 29/29, Marshmallow 26/26, MkDocs 6/6, pre-commit 7/7.
- For the five task metadata files changed by this pass, `stats.atomic` matches the physical atomic test-function count and `oracle.count` matches taxonomy size.
- Cookiecutter's inherited reduced oracle was synchronized separately: 9 physical functions, 9 taxonomy entries, 9/9 existing reference result.

## Follow-up Required

Do not restore any removed path-bound tests to reach the count floor. Use Track B reference-observed generation through only the documented public entry points. The immediate refill priorities are Cookiecutter (+41), MkDocs (+19), pre-commit (+10), and fsspec (+7), subject to the per-spec-section quotas in `skills/test-filter/SKILL.md`.

The existing candidate scores for fsspec, Invoke, MkDocs, and pre-commit were produced against older oracle versions and must be treated as superseded until those tasks are re-scored. Cookiecutter's 6/9 candidate score already corresponds to its synchronized 9-test oracle.
