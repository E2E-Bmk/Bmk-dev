# MiniMigrationManager PRD Draft

Date: 2026-06-28

## Scope

MiniMigrationManager advanced from `prospect/prd-ready` to `candidate/prd-draft` after the Layer-0 scout and second-pass enrichment audit.

## Artifacts Added

- `skills/minimigrationmanager-task-builder/SKILL.md`
- `skills/minimigrationmanager-task-builder/agents/openai.yaml`
- `task/minimigrationmanager-realrepo-001/prd.md`
- `task/minimigrationmanager-realrepo-001/rubric.json`
- `task/minimigrationmanager-realrepo-001/doc/requirement_map.md`
- `task/minimigrationmanager-realrepo-001/doc/source_repo.md`

## Skill Validation

The new task-builder skill was initialized with `skill-creator` and validated with the bundled Codex Python:

```text
quick_validate.py skills/minimigrationmanager-task-builder
Skill is valid!
```

## Current Task State

The PRD defines a public Python module surface:

```python
from minimigrate import MiniMigrationManager, MigrationError
```

The core shared fact source is a migration workspace consisting of revision DAG, operation list, current revision set, schema snapshot, applied ledger, stamp state, and recovery marker.

The current `rubric.json` now contains 12 executable feature-pure unit rows and 5 executable system rows.

## Next Gate

Reference gate passed first on v1 and again after executable fairness cleanup:

```text
score_report_reference_unit_system_v2_fairness.json
Passed cases: 17 / 17
Weighted score: 88 / 88
Unit: 100.00%
System: 100.00%
Gap: 0.00pp
```

Next gate: run fresh Codex/OpenHands/Qwen candidates on the fairness-cleaned executable packet.

## Forward Audit

Independent forward audit verdict: `revise_before_reference`.

The auditor found the task shape valid: revision DAG, current set, schema snapshot, plan, ledger, and recovery marker are distinct public projections over one workspace fact source, and the packet is not an Alembic clone. Required pre-reference tightening was applied:

- clarified `restore_table` and `restore_column` as downgrade metadata only;
- clarified `heads` target semantics;
- clarified ledger kind rules for `apply`, `downgrade`, `stamp`, and `recover`;
- clarified `recover()` statuses and when `completed` is allowed;
- narrowed unit intent rows so multi-projection assertions stay in system rows.

Next gate remains executable rubric plus reference implementation.

Executable packet audit verdict: `revise_before_candidate`.

The audit found the reference gate credible, but flagged exact-order / exact-repr evaluator risks. Applied cleanup:

- canonicalized schema output in rubric helpers instead of comparing raw Python dict repr;
- removed independent branch apply-order expectations in merge system rows;
- made `recover` ledger `revision: None` public in the PRD;
- narrowed a few unit row assertions that mixed in extra projections.

## Codex Candidate Gate

Fresh Codex subagent artifact:

- `runs/minimigrationmanager-realrepo-001/solution-codex-subagent-001/minimigrate.py`

Raw v1 scoring produced an apparent gap:

```text
score_report_codex_subagent_001_unit_system_v1.json
Unit: 83.33%
System: 40.00%
Gap: 43.33pp
```

Manual inspection showed this raw gap was evaluator-driven: `history()` order, `base` represented as an explicit current marker, and stamp ledger `revision` shape were over-specified. After canonicalizing those rubric helpers, the same artifact scored:

```text
score_report_codex_subagent_001_unit_system_v2_fairness.json
Unit: 100.00%
System: 100.00%
Gap: 0.00pp
```

This is Branch A evidence: no gap for the fresh Codex candidate after fairness cleanup. A no-gap judge is running to decide whether the current surface is solved, under-discriminating, or needs material enrichment.
