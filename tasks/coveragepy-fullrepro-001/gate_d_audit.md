# Gate D Audit - coveragepy-fullrepro-001

## Step 0 - Data Collection

H2/H3 sections:
- Product Overview
- Scope
- Installable Surface
- Public API
- Coverage
- CoverageData
- Command-Line Behavior
- `coverage help`
- `coverage run`
- `coverage report`
- `coverage json`, `coverage xml`, and `coverage html`
- `coverage combine` and `coverage erase`
- `coverage debug`
- Configuration
- Measurement Semantics
- Data Files
- Report Semantics
- Error Semantics
- Cross-View Invariants
- Representative Workflow
- Non-Goals
- Evaluation Notes

Covered counts by section:
- Product Overview: 0
- Scope: 0
- Installable Surface: 1
- Public API: 1
- Coverage: 3
- CoverageData: 9
- Command-Line Behavior: 1
- `coverage help`: 1
- `coverage run`: 2
- `coverage report`: 1
- `coverage json`, `coverage xml`, and `coverage html`: 4
- `coverage combine` and `coverage erase`: 4
- `coverage debug`: 1
- Configuration: 3
- Measurement Semantics: 5
- Data Files: 2
- Report Semantics: 2
- Error Semantics: 7
- Cross-View Invariants: 6
- Representative Workflow: 1
- Non-Goals: 0
- Evaluation Notes: 0

`wc -l tasks/coveragepy-fullrepro-001/kept_nodeids.txt`: `51 tasks/coveragepy-fullrepro-001/kept_nodeids.txt`

## Gate D - Coverage Gap Audit (retroactive)

| spec section | covered_count | minimum | verdict |
|---|---:|---:|---|
| Product Overview | 0 | 3 | ZERO |
| Scope | 0 | 3 | ZERO |
| Installable Surface | 1 | 3 | LOW |
| Public API | 1 | 3 | LOW |
| Coverage | 3 | 3 | OK |
| CoverageData | 9 | 3 | OK |
| Command-Line Behavior | 1 | 3 | LOW |
| `coverage help` | 1 | 3 | LOW |
| `coverage run` | 2 | 3 | LOW |
| `coverage report` | 1 | 3 | LOW |
| `coverage json`, `coverage xml`, and `coverage html` | 4 | 3 | OK |
| `coverage combine` and `coverage erase` | 4 | 3 | OK |
| `coverage debug` | 1 | 3 | LOW |
| Configuration | 3 | 3 | OK |
| Measurement Semantics | 5 | 3 | OK |
| Data Files | 2 | 3 | LOW |
| Report Semantics | 2 | 3 | LOW |
| Error Semantics | 7 | 5 | OK |
| Cross-View Invariants | 6 | 5 | OK |
| Representative Workflow | 1 | 3 | LOW |
| Non-Goals | 0 | 3 | ZERO |
| Evaluation Notes | 0 | 3 | ZERO |

Gate D note: remaining ZERO rows, if any, are non-behavioral narrative/boundary sections rather than spec-derivable oracle targets; all core invariant/error/workflow/public-surface sections are covered after retroactive map repair and supplements.
Coverage verdict: PARTIAL
Oracle count before: 32 | after: 51
Sections with zero coverage: 4
Zero sections: Product Overview, Scope, Non-Goals, Evaluation Notes

Reference gate evidence: direct kept-oracle pytest run reported 50 passed; additional Installable Surface test passed 1/1 via harness, pass_rate_excluding_skips=1.0, JSON saved to wip/coveragepy-fullrepro-001/filter/reference_score_retro_gate_d_installable.json.
Candidate runs were not re-run or modified.
