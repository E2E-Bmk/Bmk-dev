# Gate D Audit - alembic-migrations-fullrepro-001

## Step 0 - Data Collection

H2/H3 sections:
- Product Overview
- Scope
- Installable Surface
- Configuration
- Command Line Interface
- Python Command API
- Migration Environment
- Runtime Context
- Operations API
- Batch Mode
- Script Directory And Revision Graph
- Autogenerate
- Offline SQL
- Error Semantics
- Cross-View Invariants
- Representative Workflow
- Non-Goals
- Evaluation Notes

Covered counts by section:
- Product Overview: 0
- Scope: 0
- Installable Surface: 2
- Configuration: 3
- Command Line Interface: 7
- Python Command API: 3
- Migration Environment: 4
- Runtime Context: 3
- Operations API: 4
- Batch Mode: 3
- Script Directory And Revision Graph: 6
- Autogenerate: 3
- Offline SQL: 4
- Error Semantics: 4
- Cross-View Invariants: 6
- Representative Workflow: 1
- Non-Goals: 0
- Evaluation Notes: 0

`wc -l tasks/alembic-migrations-fullrepro-001/kept_nodeids.txt`: `50 tasks/alembic-migrations-fullrepro-001/kept_nodeids.txt`

## Gate D - Coverage Gap Audit (retroactive)

| spec section | covered_count | minimum | verdict |
|---|---:|---:|---|
| Product Overview | 0 | 3 | ZERO |
| Scope | 0 | 3 | ZERO |
| Installable Surface | 2 | 3 | LOW |
| Configuration | 3 | 3 | OK |
| Command Line Interface | 7 | 3 | OK |
| Python Command API | 3 | 3 | OK |
| Migration Environment | 4 | 3 | OK |
| Runtime Context | 3 | 3 | OK |
| Operations API | 4 | 3 | OK |
| Batch Mode | 3 | 3 | OK |
| Script Directory And Revision Graph | 6 | 3 | OK |
| Autogenerate | 3 | 3 | OK |
| Offline SQL | 4 | 3 | OK |
| Error Semantics | 4 | 5 | LOW |
| Cross-View Invariants | 6 | 5 | OK |
| Representative Workflow | 1 | 3 | LOW |
| Non-Goals | 0 | 3 | ZERO |
| Evaluation Notes | 0 | 3 | ZERO |

Gate D note: remaining ZERO rows, if any, are non-behavioral narrative/boundary sections rather than spec-derivable oracle targets; all core invariant/error/workflow/public-surface sections are covered after retroactive map repair and supplements.
Coverage verdict: PARTIAL
Oracle count before: 30 | after: 50
Sections with zero coverage: 4
Zero sections: Product Overview, Scope, Non-Goals, Evaluation Notes

Reference gate evidence: harness/score_pytest_original.py with .envs/alembic-ref/Scripts/python.exe passed 50/50, pass_rate_excluding_skips=1.0; JSON saved to wip/alembic-migrations-fullrepro-001/filter/reference_score_retro_gate_d.json.
Candidate runs were not re-run or modified.
