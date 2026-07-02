# Gate D Audit - dvc-fullrepro-001

## Step 0 - Data Collection

H2/H3 sections:
- Product Overview
- Scope
- Installable Surface
- Public API
- Pipeline Files
- Stage Creation
- Reproduction Behavior
- Status, Freeze, And Pull
- Cache And Run Cache
- Error Semantics
- Cross-View Invariants
- Representative Workflows
- Non-Goals
- Evaluation Notes

Covered counts by section:
- Product Overview: 0
- Scope: 0
- Installable Surface: 1
- Public API: 4
- Pipeline Files: 7
- Stage Creation: 6
- Reproduction Behavior: 12
- Status, Freeze, And Pull: 9
- Cache And Run Cache: 1
- Error Semantics: 5
- Cross-View Invariants: 6
- Representative Workflows: 1
- Non-Goals: 0
- Evaluation Notes: 0

`wc -l tasks/dvc-fullrepro-001/kept_nodeids.txt`: `50 tasks/dvc-fullrepro-001/kept_nodeids.txt`

## Gate D - Coverage Gap Audit (retroactive)

| spec section | covered_count | minimum | verdict |
|---|---:|---:|---|
| Product Overview | 0 | 3 | ZERO |
| Scope | 0 | 3 | ZERO |
| Installable Surface | 1 | 3 | LOW |
| Public API | 4 | 3 | OK |
| Pipeline Files | 7 | 3 | OK |
| Stage Creation | 6 | 3 | OK |
| Reproduction Behavior | 12 | 3 | OK |
| Status, Freeze, And Pull | 9 | 3 | OK |
| Cache And Run Cache | 1 | 3 | LOW |
| Error Semantics | 5 | 5 | OK |
| Cross-View Invariants | 6 | 5 | OK |
| Representative Workflows | 1 | 3 | LOW |
| Non-Goals | 0 | 3 | ZERO |
| Evaluation Notes | 0 | 3 | ZERO |

Gate D note: remaining ZERO rows, if any, are non-behavioral narrative/boundary sections rather than spec-derivable oracle targets; all core invariant/error/workflow/public-surface sections are covered after retroactive map repair and supplements.
Coverage verdict: PARTIAL
Oracle count before: 43 | after: 50
Sections with zero coverage: 4
Zero sections: Product Overview, Scope, Non-Goals, Evaluation Notes

Reference gate evidence: direct kept-oracle pytest run from wip/dvc-fullrepro-001/filter reported 50 passed in 156.76s; summary saved to reference_score_retro_gate_d.json.
Candidate runs were not re-run or modified.
