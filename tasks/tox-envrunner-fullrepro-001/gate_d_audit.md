# Gate D Audit - tox-envrunner-fullrepro-001

## Step 0 - Data Collection

H2/H3 sections:
- Product Overview
- Scope
- Installable Surface
- Public API
- Configuration Files
- Environment Selection
- Environment Lifecycle
- Packaging
- Substitutions and Conditional Values
- Environment Variables and Commands
- Parallel and Failure Behavior
- Error Semantics
- Cross-View Invariants
- Representative Workflows
- Non-Goals
- Evaluation Notes

Covered counts by section:
- Product Overview: 0
- Scope: 0
- Installable Surface: 3
- Public API: 5
- Configuration Files: 9
- Environment Selection: 9
- Environment Lifecycle: 2
- Packaging: 2
- Substitutions and Conditional Values: 5
- Environment Variables and Commands: 3
- Parallel and Failure Behavior: 2
- Error Semantics: 5
- Cross-View Invariants: 6
- Representative Workflows: 1
- Non-Goals: 0
- Evaluation Notes: 0

`wc -l tasks/tox-envrunner-fullrepro-001/kept_nodeids.txt`: `51 tasks/tox-envrunner-fullrepro-001/kept_nodeids.txt`

## Gate D - Coverage Gap Audit (retroactive)

| spec section | covered_count | minimum | verdict |
|---|---:|---:|---|
| Product Overview | 0 | 3 | ZERO |
| Scope | 0 | 3 | ZERO |
| Installable Surface | 3 | 3 | OK |
| Public API | 5 | 3 | OK |
| Configuration Files | 9 | 3 | OK |
| Environment Selection | 9 | 3 | OK |
| Environment Lifecycle | 2 | 3 | LOW |
| Packaging | 2 | 3 | LOW |
| Substitutions and Conditional Values | 5 | 3 | OK |
| Environment Variables and Commands | 3 | 3 | OK |
| Parallel and Failure Behavior | 2 | 3 | LOW |
| Error Semantics | 5 | 5 | OK |
| Cross-View Invariants | 6 | 5 | OK |
| Representative Workflows | 1 | 3 | LOW |
| Non-Goals | 0 | 3 | ZERO |
| Evaluation Notes | 0 | 3 | ZERO |

Gate D note: remaining ZERO rows, if any, are non-behavioral narrative/boundary sections rather than spec-derivable oracle targets; all core invariant/error/workflow/public-surface sections are covered after retroactive map repair and supplements.
Coverage verdict: PARTIAL
Oracle count before: 31 | after: 51
Sections with zero coverage: 4
Zero sections: Product Overview, Scope, Non-Goals, Evaluation Notes

Reference gate evidence: harness/score_pytest_original.py with .envs/tox-reference/Scripts/python.exe passed 51/51, pass_rate_excluding_skips=1.0; JSON saved to wip/tox-envrunner-fullrepro-001/filter/reference_score_retro_gate_d.json.
Candidate runs were not re-run or modified.
