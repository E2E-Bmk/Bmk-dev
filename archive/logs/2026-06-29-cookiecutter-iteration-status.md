# Cookiecutter Iteration Status

Date: 2026-06-29

Remote-first iteration in progress on `westb-44741`.

Last verified remote state before SSH timeout:

- Task path: `/root/autodl-tmp/swe-e2e/Bmk-dev/wip/cookiecutter-fullrepro-001`
- Step 1 completed with user-approved LOC exception.
- Source LOC: 2806 across 18 package Python files.
- Source test functions: 222 across 36 top-level test files.
- Step 2 spec draft written and patched after two spec judge failures.
- Step 3 taxonomy written:
  - kept source test functions: 213
  - dropped source test functions: 9
  - preserved rate: 95.95%
  - atomic kept: 104
  - integration kept: 66
  - system/E2E kept: 43
- Reference run succeeded before the timeout:
  - run dir: `/root/autodl-tmp/swe-e2e/logs/2026-06-29-cookiecutter-reference`
  - exit code: 0
  - pytest result shown in terminal: `274 passed, 4 skipped`

Pending after reconnect:

- Confirm/write `oracle_candidates/reference_score.json`.
- Append reference result to remote `filter_notes.md` if not already written.
- Run one more full spec judge before candidate execution.
- Continue Step 4 candidate evaluation.
