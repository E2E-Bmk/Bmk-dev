# Cookiecutter Corrected Final Gate Report

Date: 2026-06-29
Candidate: cookiecutter (`repo-pool/cookiecutter`)
Task id: `cookiecutter-fullrepro-001`

## Correction

Earlier Qwen scores of 97.81% were invalid. There were two different problems:

1. run004 accessed reference/benchmark paths (`envs/cookiecutter-ref`, `repo-pool`).
2. cleanroom run002 installed the target distribution `cookiecutter==2.6.0` from PyPI.
3. cleanroom run003 blocked target-package install, but the first score still imported the original source package from `oracle_worktree/cookiecutter` because the scorer copied the source tree and ran pytest with `cwd=oracle_worktree`; `sys.path[0] == ''` beat `PYTHONPATH=solution_dir`.

Corrected scoring reran with `--remove-path cookiecutter --remove-path cookiecutter.egg-info`, forcing imports to come from the candidate solution.

## Step Status

[STEP 1 COMPLETE] Cookiecutter passed test-count and public-projection gates, but failed strict source LOC (2806 package LOC < 3000). A first-pilot exception is recorded; future candidates should not inherit this exception.

[STEP 2 COMPLETE] Spec/public packet was patched from docs audit: Jinja2 rendering, `cookiecutter.` namespace, private variables, `__prompts__`, nested `templates`/`template`, `_jinja2_env_vars`, and replay naming behavior were made explicit.

[STEP 3 COMPLETE] Test taxonomy and kept nodeids are under `oracle_candidates/`. Reference implementation passed current kept subset: 274 passed, 4 skipped, 278 parameterized cases. Preserved rate: 95.95% by source test function count.

[STEP 4 COMPLETE WITH TOOLING CAVEATS]

Valid corrected scores:

- Codex subagent candidate, source package removed from oracle worktree: 17 passed, 187 failed, 4 skipped, 11 error, 38 collection_error; pass rate excluding skips 6.72%.
- Qwen cleanroom run003, source package removed from oracle worktree and target-package install blocked: 24 passed, 169 failed, 4 skipped, 11 error, 49 collection_error; pass rate excluding skips 9.49%.

Invalidated scores:

- Qwen run004 97.81%: invalid reference-path leakage.
- Qwen cleanroom run002 97.81%: invalid target-package install.
- Qwen cleanroom run003 initial 97.81%: invalid scorer source-package shadowing.

Unavailable baselines:

- DeepSeek fallback failed before implementation due API connection/InternalServerError.
- OpenHands failed before task execution due installed CLI/SDK mismatch.

## Gate Results

Gate A: PASS. Valid corrected strong/weak baselines are far below the >80% solved threshold.

Gate B': PASS. Codex corrected run retains independent system/integration failures not explained solely by atomic cascade; the cleanest evidence remains `tests/test_main.py::test_original_cookiecutter_options_preserved_in__cookiecutter`, where `generate_files` is mocked and the candidate fails to preserve `context['_cookiecutter']` across top-level context assembly and generation.

Gate B: PASS, narrow. The `_cookiecutter` preservation failure is a cross-stage state drift between the top-level context/config view and generation-stage context, not a primitive rendering failure. Other system failures are numerous but many cascade from missing API or primitive context bugs, so report the narrow evidence honestly.

Gate C: PASS for reference execution and current retained subset. Reference passed >=95% of retained tests. Fairness audit notes: some retained tests import documented helper modules from `docs/cookiecutter.rst`; this is acceptable because the public API reference exposes them, but future tasks should avoid letting public module lists become too isomorphic.

## Decision

Task status: QUALIFIED, with tooling caveats.

Reason: After correcting scorer isolation, both valid candidate baselines fail substantially, while reference passes and at least one independent system-level cross-component failure exists. The task measures more than atomic primitives, though failure diversity is partly polluted by missing public API and collection-error clusters.

## Required Follow-up Before Large-Scale Use

1. Always score candidates with the source package removed from the oracle worktree, or otherwise prove `import package.__file__` points to the candidate solution.
2. Keep target-package install blocking in cleanroom runs.
3. Fix OpenHands/DeepSeek harness before using their scores in aggregate comparisons.
4. Report repeated roots separately: missing public API, primitive context/rendering, independent integration, independent system drift.

[ITERATION COMPLETE] {
  task_status: QUALIFIED,
  preserved_rate: 95.95%,
  SOTA_system_rate: Codex corrected system pass 6/59 = 10.17%,
  gate_results: {A: PASS, B': PASS, B: PASS, C: PASS_REFERENCE},
  skill_patches: [skills/candidate-selector/SKILL.md, skills/spec-writer/SKILL.md, skills/test-filter/SKILL.md, skills/task-judge/SKILL.md]
}

## Fresh Codex Spec-Delta Rerun

[STEP 4 UPDATE] Fresh Codex candidate was rerun against the patched public packet. Full report: wip/cookiecutter-fullrepro-001/codex_specdelta_score_report_2026-06-29.md.

Corrected scorer used --remove-path cookiecutter --remove-path cookiecutter.egg-info; import provenance confirmed cookiecutter.__file__ points to Bmk-dev/results/codex-subagent/cookiecutter-fullrepro-001/specdelta-20260629-001/output/cookiecutter/__init__.py.

Results: 32 passed, 182 failed, 11 error, 31 collection_error, 4 skipped, 260 total; pass rate excluding skips 12.50%. By layer: atomic 11/128 passed, integration 10/73 passed, system_e2e 11/59 passed.

Gate A remains PASS. The patched spec improves Codex over the old corrected run (6.72% -> 12.50%) but remains far below solved thresholds.

## Spec Detail Experiment: v2-only vs v3-only

[STEP 4 UPDATE] Fresh Codex candidates were rerun with single-spec cleanroom inputs to test the effect of spec detail. Reports:
- wip/cookiecutter-fullrepro-001/codex_specv2only_score_report_2026-06-29.md
- wip/cookiecutter-fullrepro-001/codex_specv3only_score_report_2026-06-29.md
- wip/cookiecutter-fullrepro-001/cookiecutter_spec_detail_experiment_summary_2026-06-29.md

Corrected scorer used --remove-path cookiecutter --remove-path cookiecutter.egg-info, and import provenance confirmed both runs imported candidate output packages.

Results: patched packet 12.50% pass rate excluding skips; spec_v2-only 25.38%; spec_v3-only 16.15%. The v2-only spec materially improves Codex performance, especially integration/system behavior, while v3-only remains above patched packet but below v2. Gate A remains PASS for all variants.

## Spec Detail Experiment: NL2RepoBench-style v4

[STEP 4 UPDATE] A new ultra-detailed NL2RepoBench-style spec was written as wip/cookiecutter-fullrepro-001/spec_v4.md and tested as a single-input cleanroom Codex run. Full report: wip/cookiecutter-fullrepro-001/codex_specv4only_score_report_2026-06-29.md. Updated summary: wip/cookiecutter-fullrepro-001/cookiecutter_spec_detail_experiment_summary_2026-06-29.md.

Corrected scorer used --remove-path cookiecutter --remove-path cookiecutter.egg-info; import provenance confirmed cookiecutter.__file__ points to Bmk-dev/results/codex-subagent/cookiecutter-fullrepro-001/specv4only-20260629-001/output/cookiecutter/__init__.py.

Results: v4-only passed 40 / 243 total, with 74 collection_error, 2 error, 123 failed, 4 skipped; pass rate excluding skips 16.74%. Diagnostic scoring that additionally removed candidate-created click/ and jinja2/ stubs produced the same score, so the weak result is not mainly caused by dependency shadowing.

Current comparison: patched packet 12.50%, spec_v2-only 25.38%, spec_v3-only 16.15%, spec_v4-only 16.74%. Spec detail is beneficial up to v2 but not monotonic; the NL2RepoBench-style long blueprint underperforms v2 and produces many collection errors. Gate A remains PASS.
