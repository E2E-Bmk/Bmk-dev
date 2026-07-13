# Skill Lifecycle

Use this skill when a task-building workflow has repeated often enough that the
team should turn it into reusable procedure.

## Goal

Convert working practice into a concise, testable operating manual that can be
used by another team member or subagent without private context.

## Promotion Gate

Create or promote a skill only when all checks pass:

- The workflow was used on at least one real repository-backed task.
- The inputs, outputs, and artifact paths are stable enough to name.
- The procedure contains at least one decision gate, not just narration.
- The skill helps prevent a known failure mode from previous runs.
- Another person can execute the steps without reading session logs.

Keep the workflow in `wip/{task}/filter_notes.md` or `docs/` if it is still a
one-off experiment.

## Required Sections

Each `SKILL.md` should include:

- title and use condition;
- goal;
- required inputs;
- produced artifacts;
- ordered procedure;
- rejection or audit gates;
- common failure modes;
- maintenance notes.

## Procedure

1. Extract the repeated steps from a completed or active task build.
2. Remove task-specific details unless they are framed as an example.
3. Add concrete artifact paths relative to `Bmk-dev/`.
4. Add gates that stop bad candidates early.
5. Run the skill on a second candidate or ask another team member to dry-run it.
6. Revise unclear steps before marking it as active in `skills/README.md`.

## Common Failure Modes

- Skill repeats old mini-task assumptions instead of the current full
  reconstruction direction.
- Skill tells the model to generate code directly rather than use OpenHands or
  the selected harness.
- Skill assumes access to source repo or hidden tests during candidate runs.
- Skill records a preference but no executable procedure.
- Skill is too broad and should be split into candidate selection, test
  taxonomy, scoring audit, or remote-run setup.

## Maintenance

When a skill changes because of a real task failure, update the skill and cite
the task in the commit or session note. Do not silently preserve obsolete gates.
