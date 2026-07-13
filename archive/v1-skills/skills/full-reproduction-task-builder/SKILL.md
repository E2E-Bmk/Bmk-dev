---
name: full-reproduction-task-builder
description: Build or audit full-reproduction SWE-E2E benchmark tasks from real repositories. Use when creating full subsystem PRDs, Layer-0 structural audits, requirement maps, hidden unit/integration/system rubrics, cleanroom harness plans, or task-builder skills that must avoid one-file mini clones.
---

# Full-Reproduction Task Builder

## Core Rule

Build complete bounded subsystem tasks, not mini reimplementations. Reject a
candidate if a capable agent can naturally pass it with one file, one dict, one
helper, or a compact prompt-sized rewrite.

The task source of truth is a real upstream repository. Do not hand-write LOC to
make a task look large. First derive a public packet and hidden capability
rubric from upstream docs, tests, examples, changelog, and observed source
behavior; then let the candidate agent reconstruct an implementation from the
public packet in a cleanroom workspace. If a tiny candidate implementation
passes against a large upstream-derived packet, treat that as evaluator
under-coverage or PRD under-specification, not as proof that the task is
full-reproduction.

Prefer interface-defined architecture for strict unit/system gap tasks:
candidate-visible starter files lock module boundaries and public signatures,
while candidates implement behavior. This keeps unit tests module-local and
lets system tests measure real cross-module invariants instead of architecture
invention or incomplete implementation.

Minimum strict-task shape:

- installable package or runnable service;
- 10+ candidate-owned source modules;
- roughly 2,000+ non-test reference LOC;
- public CLI/service boundary plus importable API boundary;
- durable state, materialized outputs, indexes, ledgers, caches, or generated
  reports;
- at least four public projections that can drift;
- 50+ executable checks before the first strict candidate run.

## Workflow

1. Run Layer-0 audit before writing a PRD.
   - Use `references/layer0-audit.md`.
   - First run `tools/source_candidate_gate.py` from the benchmark repo to
     record upstream scale, docs/tests/examples signals, and the exact source
     path or clone URL.
   - Stop immediately on `FORCED`, `CONTAMINATED`, `COLLAPSE`,
     `UNDER_SCOPED`, or `STRUCTURAL_DEAD`.
   - Record upstream file/LOC scale and evidence sources before any reference
     implementation work.
   - Treat any local `solution-reference` that was not generated from an
     upstream evidence map as a prototype only; it cannot prove task scale.

2. Write a public product packet only for passing candidates.
   - Use `references/prd-rubric-contract.md`.
   - Use `references/candidate-profiles.md` for the current accepted candidate
     surfaces and test templates.
   - Specify product behavior, state lifecycle, public schemas, persistence,
     recovery, errors, determinism, and non-goals.
   - Do not reveal hidden fixtures, scoring rows, reference file names, or
     implementation internals.

3. Build the hidden rubric as capability tests.
   - Unit tests are feature-pure: setup uses only the feature under test,
     direct constructor state, or explicit mocks.
   - Integration tests cross API/CLI/persistence boundaries.
   - System tests name the cross-feature contract and exercise operation
     sequences, rollback, replay, cache/index invalidation, generated reports,
     export/import, and reverse projections.

4. Preserve oracle provenance.
   - Document the upstream evidence for every public behavior.
   - Prefer public docs, examples, tests, changelogs, and observed source
     behavior.
   - Avoid exact public standards as the whole agreement surface; add a
     product-natural lifecycle or reject as `FORCED`.
   - Keep upstream source and hidden rubrics outside the candidate workspace.
     Candidate-visible files are limited to the public packet and starter
     skeleton.

5. Use cleanroom scoring.
   - Candidate workspace contains only the public packet, starter skeleton, and
     empty/incomplete implementation.
   - Never expose rubric, reference, score reports, prior candidates, traces, or
     iteration notes.
   - Save full agent trajectory and score externally.

## Candidate Output

For each accepted candidate, produce:

- `prospects/<id>/layer0_audit.md`;
- `task/<id>/prd.md`;
- `task/<id>/doc/requirement_map.md`;
- `task/<id>/rubric.json`;
- `task/<id>/doc/harness.md`;
- reference implementation passing all checks;
- score reports and trace paths for each candidate run.

## Gap Acceptance

Accept only residual compositional gap:

- reference passes 100%;
- candidate gap is at least 15pp after removing primitive/cascade/evaluator
  defects;
- no feature-pure unit violations;
- no hidden ambiguity or private-shape assertion;
- gap reproduces across two scoreable artifacts, or one strong artifact plus a
  judge-approved causal explanation;
- trace provenance is clean.
