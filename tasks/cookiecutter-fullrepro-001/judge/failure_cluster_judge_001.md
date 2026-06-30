# Cookiecutter Failure Cluster Judge 001

Date: 2026-06-29
Run: Codex subagent fresh candidate
Score file: `Bmk-dev/results/codex-subagent/cookiecutter-fullrepro-001/score_filegroup.json`

## Summary

Gate B' and Gate B pass, but the evidence is narrow. Most failures are still explained by missing public APIs, collection/import errors, or primitive context/rendering bugs. The qualifying cross-component evidence is a system-level state-transfer failure that is isolated from the lower-level generator by mocking.

## Score Shape

- Summary: 15 passed, 189 failed, 4 skipped, 11 error, 38 collection_error, 257 total counted cases.
- Pass rate excluding skips: 5.93%.
- Layer results:
  - atomic: 6 / 125 passed, 38 collection_error.
  - integration: 3 / 73 passed.
  - system_e2e: 6 / 59 passed.

## Main Failure Clusters

### Missing public API / collection error

This is the largest cluster. Examples include missing `cookiecutter.log`, prompt reader helpers, `YesNoPrompt`/`JsonPrompt`, `generate.generate_file`, extension exports, and utility helpers such as `work_in`, `create_tmp_repo_dir`, and `force_delete`. These explain many atomic failures and collection errors and should not be counted as independent compositional evidence.

### Primitive rendering/context failures

Many integration/system failures are cascades from context-shape bugs such as `UndefinedVariableInTemplate: 'dict object' has no attribute ...`. These include failures for `repo_dir`, `food`, `repo_name`, `binary_test`, hook template names, and copy-without-render fixtures. These show real implementation gaps, but most are primitive cascade rather than cross-component drift.

### Integration independent candidates

Nested-template selection and some hook/copy-without-render combinations show possible independent integration failures. However, several are polluted by missing prompt APIs or primitive rendering bugs, so they are secondary evidence.

### System independent evidence

Primary evidence: `tests/test_main.py::test_original_cookiecutter_options_preserved_in__cookiecutter`.

- Taxonomy layer: `system_e2e`.
- Outcome: failed.
- Crash: `KeyError: '_cookiecutter'` at `tests/test_main.py:24`.
- Why it is independent: the test patches `cookiecutter.main.generate_files`, so file rendering, Jinja behavior, hooks, and filesystem generation are not on the failure path.
- Behavioral meaning: top-level `cookiecutter()` should preserve original context options under `context['_cookiecutter']` when handing context to the generation stage. The candidate constructs context through config/defaults/prompt flow but does not preserve this cross-stage state view.

This is a cross-component state drift between the top-level context/config view and the generation-stage context view, not merely a primitive render failure.

## Gate Read

- Gate A: PASS. Codex pass rate is far below the >80%/90% solved threshold.
- Gate B': PASS. At least one system failure is not explained by atomic primitive cascade: `_cookiecutter` preservation with generator mocked.
- Gate B: PASS, narrow. The `_cookiecutter` preservation failure is a system workflow failure caused by cross-stage state drift.
- Gate C: PROVISIONAL PASS. Reference passed the current kept subset, but retained-test fairness still needs a final audit because the kept set includes many documented public helper APIs.

## Qualification Caveat

Do not over-interpret the raw 5.93% score as broad compositional measurement. A large fraction of failed weight comes from missing public API surface and primitive rendering/context failures. The task remains useful only if final reporting separates the narrow Gate B evidence from the broad missing-surface failures.
