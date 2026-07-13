# Gap Loop Iteration Report

Date: 2026-06-28

## Skill Changes

Created and validated:

- `C:\Users\12547\.codex\skills\gap-benchmark-iteration`

Updated and validated:

- `C:\Users\12547\.codex\skills\gap-invariant-task-builder`

The new orchestration skill defines the full loop: redesign task, run reference and candidate gates, send observed gaps to a fairness judge, send missing gaps to a no-gap judge, then either revise, enrich, accept, or mark solved.

The task-builder skill now explicitly warns against:

- separating near-reference candidates with artificial hidden behavior;
- under-discriminating resolver/graph system tests that only use small final-result fixtures;
- counting the same primitive parsing, identity, hashing, or serialization defect across multiple system cases unless downstream projections diverge.

All three gap skills currently validate with `quick_validate.py`:

- `gap-benchmark-iteration`
- `gap-invariant-task-builder`
- `gap-fairness-judge`

## Subagent Loop

Initial task-builder subagents failed because the external subagent backend returned 403 insufficient balance. After balance recovery, the loop continued with subagents.

Read-only no-gap judges:

- MiniMarkdown judge verdict: `solved / enrich, not accept`
- MiniPackaging first judge verdict: `revise`

Packaging task-builder workers:

- First revision produced a numeric Codex gap, but the fairness judge rejected it as cascade-driven.
- Second revision removed repeated primitive roots from system scoring. The final no-gap judge classified the cleaned task as solved for the current unit/system-gap objective.

## MiniMarkdown Current Evidence

Reference:

- unit 100.00%
- system 100.00%

Best current Codex redesign-v2 candidate:

- unit 94.44%
- system 91.67%
- gap 2.78pp

Judge conclusion:

- Not acceptable gap evidence.
- Remaining misses are narrow feature/cascade failures: hard-break parsing and list-item inline projection.
- The task is effectively near-solved for the current Codex population.
- OpenHands evidence appears stale because the task log reflects an older public packet without the current TOC/heading-id contract.

Next action:

- Enrich with materially deeper parser lifecycle scope, or retire for gap purposes.

## MiniPackaging Cascade-Cleanup Iteration

### Before Cascade Cleanup

After the first metamorphic revision:

| Implementation | Unit | System | Gap |
|---|---:|---:|---:|
| reference | 100.00% | 100.00% | 0.00pp |
| codex-subagent-001 | 83.33% | 66.67% | 16.67pp |
| codex-subagent-redesign-v2-001 | 83.33% | 66.67% | 16.67pp |
| openhands-deepseek-v4-pro-001 | 72.22% | 66.67% | 5.56pp |

Fairness judge verdict: `revise`.

Reason:

- The numeric Codex gap was mostly repeated primitive cascade.
- `Requirement.__eq__` / `__hash__` failure from `MPU013` was counted again in `MPS002`, `MPS005`, and `MPS010`.
- Invalid URL+specifier parsing from `MPU014` was counted again in `MPS009`, even though atomic recovery and later valid resolution passed.

### After Cascade Cleanup

Current scores:

| Implementation | Unit | System | Gap |
|---|---:|---:|---:|
| reference | 100.00% | 100.00% | 0.00pp |
| codex-subagent-001 | 83.33% | 100.00% | -16.67pp |
| codex-subagent-redesign-v2-001 | 83.33% | 100.00% | -16.67pp |
| openhands-deepseek-v4-pro-001 | 72.22% | 100.00% | -27.78pp |

Final judge verdict: `solved` for the current unit/system-gap objective.

Reason:

- All usable candidates satisfy the remaining downstream resolver/projection invariants.
- Surviving failures are unit-level primitives: requirement formatting, equality/hash semantics, invalid URL+specifier rejection, and OpenHands exception wrapping.
- No major hacking signal was found.

Next action:

- Do not accept MiniPackaging as gap evidence.
- Continue only with material product-natural enrichment, not scoring tweaks.

## Files Updated

- `task/minipackaging-realrepo-001/prd.md`
- `task/minipackaging-realrepo-001/rubric.json`
- `task/minipackaging-realrepo-001/doc/requirement_map.md`
- `task/minipackaging-realrepo-001/doc/redesign_note.md`
- `task/minipackaging-realrepo-001/doc/score_reports/*`
- `runs/minipackaging-realrepo-001/solution-reference/minipackaging.py`
- `runs/minipackaging-realrepo-001/score_report_current_*_20260628.json`
- `MANIFEST.json`
- `CANDIDATES.md`
- `score_summary.csv`

## Current Decision

No new task is promoted to `core strong` in this iteration.

The loop did produce the desired methodological result: a numeric gap was generated, independently judged as unfair/cascade-driven, removed, and documented. This confirms that the updated skills now guard against manufacturing a gap by repeated primitive-root scoring.

Open next loop:

- Build or enrich tasks with deeper product-natural lifecycle state.
- Run fresh Codex and OpenHands agent candidates against the enriched packet.
- Judge any observed gap before accepting.
