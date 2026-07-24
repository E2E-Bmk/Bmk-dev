# SWE-E2E Skills

This directory stores reusable team procedures for the new SWE-E2E task
construction direction. A skill here is a small operating manual that another
team member can follow without needing the original discussion thread.

The old v1 skills are archived under `archive/` and are not the active source
of truth.

## Skill Discipline

The active workflow authority is:

1. `task-synthesizer/SKILL.md`
2. the specialist skill for the current pipeline stage
3. the current goal/objective file

Before starting any pipeline stage, read the specialist skill for that stage.
Treat this as a mandatory pre-flight check. When delegating to a subagent,
explicitly instruct the subagent to read the same stage skill before inspecting
artifacts, and include the exact `Bmk-dev/skills/{skill-name}/SKILL.md` path in
the delegation prompt.

Do not use archived root-level or legacy SWE-E2E skills for this pipeline.
Packaged snapshots and old workflow skills live under
`archive/deprecated-skills/`; do not treat them as runtime authority.

## Active Principles

- Start from a real repository or an existing benchmark case backed by a real
  repository.
- Prefer complete multi-file project reconstruction, not mini one-file tasks.
- Keep the source repository, hidden tests, traces, previous attempts, and
  score reports unavailable to candidate agents.
- Use the public packet to specify product behavior, artifact shape, public
  interfaces, examples, behavioral principles, and non-goals.
- Use filtered original tests or deterministic executable rubrics as the
  oracle.
- Re-label tests into our own taxonomy: atomic, integration, and system/E2E.
- Accept a task only after fairness audit removes underspecified, brittle, or
  private-implementation expectations.

## Current Stage Skills

- `task-synthesizer/`: orchestrates candidate selection, spec writing, test
  filtering, evaluation, and judging.
- `candidate-selector/`: repository gate and retirement criteria.
- `spec-writer/`: public packet/spec writing rules.
- `test-filter/`: original-test filtering and preserved-surface audit.
- `task-judge/`: Gate A/B/C decision rules and cleanroom scoring requirements.

## Skill Lifecycle

1. Draft the skill during a real task build.
2. Use it once on a second candidate.
3. Revise the parts that were ambiguous or too manual.
4. Mark it stable only when another team member can follow it without private
   context.

## Skill Format

Each skill should live at `skills/{skill-name}/SKILL.md` and include:

- when to use it;
- inputs and expected outputs;
- step-by-step procedure;
- gates or rejection criteria;
- artifact paths it reads or writes;
- common failure modes;
- one short example from an actual task build.

Do not promote a speculative process into `skills/`. Keep early experiments in
`docs/` or `wip/{task}/filter_notes.md` until the workflow has survived at
least one concrete task.
