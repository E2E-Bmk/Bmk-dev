# Stage 5 Judge Diagnosis: beancount-ledger-fullrepro-001

Verdict: QUALIFIED. The prior unfair 483-nodeid upstream carrier was repaired into a 51-test public-surface oracle. The corrected oracle passes reference, fails dummy, and produces a non-saturated candidate score with public behavior failures.

## Preflight output

Command:

```powershell
$env:PYTHONPATH='G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-beancount-specv1-20260701-001\solution'; python -c "import beancount; print(beancount.__file__)"
```

Literal output:

```text
G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-beancount-specv1-20260701-001\solution\beancount\__init__.py
```

The import provenance points into the cleanroom candidate solution directory, not repo-pool, a reference worktree, or an installed real Beancount package.

## Anti-Cheat

The cleanroom manifest records only `public_packet/spec.md` and `task_prompt.txt` as candidate inputs. A targeted scan of the candidate solution found no forbidden references to hidden oracle files, kept nodeids, score reports, reference scores, filter artifacts, or benchmark test modules. The only matches for filter/test/report terms are the public task prompt prohibition and manifest exclusion policy.

Anti-cheat result: pass.

## Solvability

The corrected oracle is the expanded repaired public-surface set in `filter/rewritten_public_surface_tests.py`, selected by `filter/kept_nodeids.txt` and classified by `filter/taxonomy.jsonl`.

- Reference gate: 51 passed / 51 total in `filter/reference_score.json`.
- Dummy gate: 0 passed / 51 total in `filter/dummy_gate_report.json`.
- Layer coverage: atomic 22, integration 21, system_e2e 8.

Solvability result: pass.

## Fairness Gate A: Spec Mapping Spot-Check

Spot-checked covered rows map to real spec sections and behavioral descriptions:

- `test_load_doc_decorator_supplies_parsed_ledger_to_function` -> `### Loading Ledgers`.
- `test_get_account_open_close_keeps_first_lifecycle_directives` -> `### Account and Entry Getters`.
- `test_format_entry_write_source_emits_source_comment` -> `### Formatted Output`.
- `test_load_file_raw_plugin_mode_skips_standard_balance_validation` -> `### Plugins and Transformations`.
- `test_realized_transaction_postings_preserve_parent_transaction` -> `### Account Realization`.

Each sampled test exercises public Beancount behavior through root API names, public directive objects, public loader functions, formatted output, or realized account projections. No sampled assertion requires upstream source-module layout, private parser helpers, or test harness imports.

Gate A result: pass.

## Fairness Gate B: Failure Pattern Audit

Candidate score file: `candidate-runs/codex-beancount-specv1-20260701-001/score_result.json`.

Observed summary:

- Total: 51.
- Passed: 44.
- Failed: 7.
- Collection errors: 0.
- By layer: atomic 20/22, integration 18/21, system_e2e 6/8.

The 7 failures are public behavior gaps:

- `load_doc()` decorator argument ordering and `expect_errors=True` handling.
- Account helper edge behavior for root-account `parent()` and first open/close lifecycle retention.
- Source-aware formatted output with `write_source=True`.
- Custom directive value shape for parsed amount values.
- Raw plugin processing mode skipping normal balance validation.

These are model implementation gaps, not hidden carrier/module-layout failures. The score is non-saturated and preserves useful gradient across atomic, integration, and system_e2e layers.

Gate B result: pass.

## Fairness Gate C: Repaired Oracle Spot-Check

The final oracle is repaired public-surface rather than generated-only, but the expansion added Track-B-style public behavioral tests. I spot-checked the repaired expansion against the same standard used for generated-only assertions:

- The assertions are derivable from `spec_v1.md` sections and public Beancount behavior.
- They avoid exact repr checks, private attributes, hidden module paths, and upstream fixture shape.
- They run through `import beancount as bn`, public root exports, and documented file/ledger behavior.

Gate C result: pass.

## Final Decision

QUALIFIED.

Required records:

- `CANDIDATES.md`: append a QUALIFIED row for the rescued 51-test Beancount public-surface oracle.
- `weakness_table.md`: record the candidate's 7 public behavior failures by cluster.
- `tasks/` copy is deferred because another agent is actively working under task directories in this workspace.
