DO NOT send optional commentary

# Non-negotiable rules

Five rules. Everything else lives in `dev/skills/{skill}/SKILL.md`; read the skill
for the pipeline stage you are in before touching any artifact.

## 1. Read the stage skill first

Before starting a pipeline stage, read `dev/skills/{skill}/SKILL.md` for that
stage. When delegating to a subagent, put the exact skill path in the delegation
prompt and instruct it to read the skill before inspecting artifacts.

## 2. Every oracle change requires a fresh lint result on disk

```bash
python harness/oracle_import_lint.py <task_id> tasks/<task_id>/spec.md \
  > wip/<task>/filter/lint_result.txt 2>&1
```

First line must read `LINT_PASS`. This is a state transition requirement, not a
suggestion: `S4_SETUP` and `QUALIFIED` are both blocked without it, and the file
must be newer than every test file under `oracle/`.

A task once shipped with eight atomic tests asserting an upstream exception tree
the spec never declared. The fairness spot-check ran as specified and did not see
them, because a sample of a subset cannot cover a defect concentrated in one
behaviour family. The rule was followed and the defect passed. Landing the output
makes the check reviewable instead of self-reported.

## 3. Never widen the spec to make a test pass

If an oracle test references a symbol the spec does not declare, remove the test.
Adding the symbol to the spec inverts what the benchmark measures: the assertion
then rewards a delivery that recalls upstream internals over one that implements
the specification. Route a spec change through spec-writer only when the
*behaviour* is in scope, never to satisfy a failing assertion.

## 4. A task is not qualified until the reference implementation passes 100%

The reference implementation, installed from `repo_commit`, must pass the complete
oracle with zero failures, recorded in `filter/reference_score.json`.

This is the only evidence separating a hard task from a broken oracle. One task
holds every model below 57% integration while its reference passes 86 of 86 - real
capability difficulty. Another had a reference that passed while spec-following
deliveries could not - a defective oracle. The scores alone do not distinguish
them.

## 5. Do not engineer the oracle toward a score target

Difficulty comes from candidate selection and post-hoc tiering. Calibration
thresholds (gap magnitude, top-model ceilings) are health checks on a finished
task, not admission criteria. Reverse-engineering an oracle until a task clears a
threshold costs more than keeping a task that turned out easy.
