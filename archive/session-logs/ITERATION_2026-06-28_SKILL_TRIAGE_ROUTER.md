# Skill Triage Router Iteration

Date: 2026-06-28

## Purpose

Convert the high-level loop diagnosis into a reusable workflow guardrail. The recurring failure was not lack of hidden tests, but ad hoc routing: stale score rows, no-artifact weak-control runs, and old task variants could dominate the next action.

## Skill Changes

Updated `C:\Users\12547\.codex\skills\gap-benchmark-iteration\SKILL.md`.

- Evidence reconstruction now requires running the bundled `scripts/triage_score_summary.py` when `score_summary.csv` exists.
- The loop now starts from a task-level route table before choosing build, enrich, judge, solved-audit, provider repair, or reject.
- The skill explicitly says the triage script is bundled with the skill, not expected to live in the benchmark workspace.

Added `C:\Users\12547\.codex\skills\gap-benchmark-iteration\scripts\triage_score_summary.py`.

- Uses the last reference-started segment per task as the current variant.
- Excludes provider/no-artifact rows from primary functional routing when scoreable artifacts exist.
- Emits provider/stale/contamination as side warnings instead of letting them override capable-agent evidence.
- Separates accepted core, raw-gap judge candidates, system-under-discriminating, primitive-capped, near-solved stop-loss, solved/provenance audit, and provider repair routes.

Validation:

- `quick_validate.py` with the bundled Codex Python reports `Skill is valid!`
- The triage script runs on `score_summary.csv` without errors.

## Score Summary Repair

Updated `score_summary.csv` to include the latest MiniPackaging `MetadataIndex` lifecycle evidence:

- reference: 100.00 unit / 100.00 system
- Codex subagent: 100.00 unit / 100.00 system
- OpenHands DeepSeek V4 Pro: 100.00 unit / 100.00 system

This prevents the triage router from treating the stale `resolve-metadata-v3` packet as the current MiniPackaging variant.

## Current Triage Output

| Task | Route | Interpretation |
|---|---|---|
| SQLite | `accepted-core` | Preserve as accepted evidence |
| ZK | `accepted-core` | Preserve as accepted evidence |
| MiniURLUtils | `accepted-core` | Preserve as accepted evidence |
| MiniRedis | `solved-audit` | No accepted gap; verify provenance/retire instead of adjacent enrichment |
| MiniKV | `solved/provenance-audit` | System solved despite unit misses; repair provenance before retire |
| MiniTemplate | `solved/provenance-audit` | Lifecycle surface solved/near-solved; weak-control no-artifact is side evidence only |
| MiniDynaconf | `system-under-discriminating` | Current system is easier than unit for capable artifact; do not accept raw weak-model gap |
| MiniPackaging | `solved-audit` | Current MetadataIndex lifecycle solved 100/100 by reference, Codex, and OpenHands DeepSeek |
| MiniMarkdown | `near-solved/stop-loss` | Capable artifact near-solved; Qwen provider failures excluded |
| MiniBitcask | `solved-audit` | Current evidence points to solved/retire |

## Subagent Forward Tests

Two read-only subagents applied the workflow.

Schrodinger audited the new triage script and found three issues in the first version:

- provider/no-artifact rows wrongly dominated MiniMarkdown, MiniPackaging, and MiniTemplate;
- old and current task variants were flattened by task name;
- the skill wording made the bundled script path ambiguous.

All three were addressed in the script and skill text.

Mencius applied the gap workflow to the current task pool and recommended:

- keep SQLite, ZK, and MiniURLUtils as the only accepted core cases;
- retire or solved/provenance-audit the current mini task pool;
- stop micro-iterating current negative candidates;
- scout new product surfaces with durable external state, three or more public projections, and lifecycle/replay/rollback pressure.

## Decision

The current task pool should not be micro-extended. The next benchmark-construction action should be a new domain scouting pass, not another hidden-row enrichment for MiniRedis, MiniKV, MiniTemplate, MiniDynaconf, MiniPackaging, MiniMarkdown, or MiniBitcask.

The skill loop now encodes that routing discipline so future iterations begin with current-variant evidence and side-warning separation rather than stale raw scores.
