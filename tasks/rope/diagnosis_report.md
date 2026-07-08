# rope task-judge diagnosis after second filter correction

Verdict: QUALIFIED

## Preflight output

```text
/Users/zijian/Bmk-dev-main/wip/rope/evaluation/solution/rope/__init__.py
```

## Inputs

- task_id: rope
- package: rope
- model: codex-candidate
- spec: `tasks/rope/spec.md`
- public packet: `tasks/rope/spec.md`
- final score: `tasks/rope/candidate_score_report.json`
- final junit: `tasks/rope/candidate_junit_final.xml`

## Hard checks

### Anti-cheat / provenance

The required import provenance preflight was run from `/Users/zijian/Bmk-dev-main/wip/rope/evaluation/manual_worktree` before opening the final score report. It resolves `rope` to the candidate solution directory, not to the oracle worktree or an installed package.

I did not find a local implementation trajectory/transcript artifact for this rope run under `wip/rope` or `candidate-runs`, so the full forbidden-access scan cannot be independently reconstructed from local artifacts. The available local evidence contains no positive indication of cheating, and the provenance preflight passes. This is not a `CHEAT_DETECTED` verdict.

### Solvability

Orchestrator evidence after the second filter correction:

- filter footer: `Total: 2104 | kept (covered): 33 | spec_gap: 0 | source-only: 1656 | excluded: 415 | final scoreable: 33`
- layer counts: atomic 20, integration 9, system_e2e 4
- reference collect: `33 tests collected in 0.02s`
- reference run: `33 passed, 33 warnings in 0.06s`
- candidate final run: `20 passed, 13 failed`, no collection errors

The oracle is solvable at 100% on the final 33-node scoring set, satisfying the solvability hard check.

### Candidate final score

| layer | passed | failed | total |
|-------|--------|--------|-------|
| atomic | 13 | 7 | 20 |
| integration | 6 | 3 | 9 |
| system_e2e | 1 | 3 | 4 |
| total | 20 | 13 | 33 |

Overall candidate pass rate: 20/33 = 60.61%.

## Gate A - spec mapping spot-check

Gate A passed on the final 33-node oracle. The retained rows I sampled are covered by the public packet and check observable behavior rather than internals:

- `CodeAssistTest::test_completing_global_variables` maps to `### Code Assist and Find APIs`: `code_assist()` returns completion proposals and `CompletionProposal.scope` includes `"global"` and `"local"`.
- `CodeAssistTest::test_get_calltips_for_classes` maps to `### Code Assist and Find APIs`: `get_calltip()` must return callable signatures, and classes report `__init__`.
- `CodeAssistInProjectsTest::test_assist_on_relative_imports` maps to `### Code Assist and Find APIs`: the `resource` argument enables relative import handling.
- `FindErrorsTest::test_defined_later` and `test_bad_attributes` map to `### Generation and Other Contrib Helpers`: `find_errors()` reports defined-later and unresolved attribute accesses with public `Error.lineno`.
- `FindItTest::test_trivial_find_definition` maps to `### Code Assist and Find APIs`: `find_definition()` returns a public `Location` with `resource`, `region`, `offset`, and `lineno`.
- `FixModuleNamesTest::test_fixing_contents` and package cases map to `### Generation and Other Contrib Helpers` plus cross-view invariant 3: module renames are returned as changes and import/use sites are updated.
- `ChangeStackTest::test_change_stack` maps to `### Generation and Other Contrib Helpers`: `push()`, `pop_all()`, and `merged()` expose a public temporary-change workflow.
- `HistoryTest::test_moving_files_to_folders` maps to `### Changes and History`: `Resource.move()` applies through `Project.do()`, and `project.history.undo()` restores committed filesystem changes.

The prior invalid carrier clusters from the 52-node run, direct generation-class constructors and direct `History.do()` usage, are absent from the final kept-node set. Gate C is not applicable; the filter map does not declare `oracle_source: generated_only`.

## Gate B - failure pattern audit

Gate B passed. The 13 final failures are spec-driven behavioral failures on public outputs or filesystem state:

1. Code assist and find query behavior, 6 failures, dimension `atomic-behavior`
   - `test_completing_global_variables`: module assignment is proposed with scope `"local"` instead of `"global"`.
   - `test_get_calltips_for_classes`: class calltip falls back to `C(...)` instead of reporting `C.__init__(self)`.
   - `test_assist_on_relative_imports`: project resource context is not used to resolve a relative import.
   - `test_completing_after_dot`: class attribute completion misses `sample_method`.
   - `test_trivial_find_definition`: in-memory definition lookup returns `None` instead of a `Location`.
   - `test_trivial_find_implementations`: selected method itself is returned as an implementation when no implementations should be found.

2. Error reporting, 2 failures, dimension `error-semantics`
   - `find_errors()` detects a totally unresolved variable but misses defined-later access and unresolved attribute access. The observed behavior is under-reporting public `Error` objects, not message wording.

3. FixModuleNames workflow, 3 failures, dimension `workflow-completeness`
   - The simple module case passes, but package renames, nested modules, and import text updates fail. This is a public refactoring workflow gap: the returned change set does not fully connect resource moves with source import edits.

4. Change/history state, 2 failures, dimension `state-management`
   - `ChangeStack.pop_all()` restores temporary state but `merged()` loses the pushed changes afterward, so applying the merged change set does not reach the final state.
   - Moving a file to a folder records an invalid destination shape, and undo leaves a directory at the original file path, causing `File.read()` to raise `IsADirectoryError`.

No final failure cluster is dominated by exact reprs, private field names, exception message text, or undocumented direct carrier APIs. These failures are model weaknesses.

## Cascade analysis

The 13 failures reduce to four root clusters:

- incomplete code assist/find semantic analysis: 6 failures
- incomplete `find_errors()` diagnostics: 2 failures
- incomplete FixModuleNames package/import workflow: 3 failures
- faulty temporary-change/history move state management: 2 failures

The task is not cascade-dominated by a missing import or a single absent class. There is some composition signal in the FixModuleNames and ChangeStack/history failures, while most atomic failures expose primitive analysis gaps.

## Task labels

- `discriminating`: the candidate lands at 60.61% with failures across atomic, integration, and system_e2e layers.
- `composition-signal`: FixModuleNames and ChangeStack/history failures require coordinated resource, source-text, and history state.
- `not-cascade-dominated`: 13 failures map to four behavioral root clusters, not one missing public surface.
- `contrib-ide-workflows`: the oracle primarily stresses code assist, find, diagnostics, module-name fixing, and change history workflows.

## Actions

- Overwrote `/Users/zijian/Bmk-dev-main/wip/rope/judge/diagnosis_report.md`.
- Appended a wip qualification row to `/Users/zijian/Bmk-dev-main/CANDIDATES.md`.
- Appended real model weakness rows to `/Users/zijian/Bmk-dev-main/weakness_table.md`.
- Published the qualified artifact copy to `/Users/zijian/Bmk-dev-main/tasks/rope/` on 2026-07-07.
