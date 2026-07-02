# Gate D Audit - copier-template-fullrepro-001

## Step 0 - Data Collection

H2/H3 sections:
- Product Overview
- Scope
- Installable Surface
- Public API
- `run_copy`
- `run_recopy`
- `run_update`
- `Settings` and `load_settings`
- `Phase` and `VcsRef`
- CLI Behavior
- Template Configuration
- Rendering Model
- Template Variables
- Settings Reference
- Answers Files
- Updates
- Unsafe Features
- Error Semantics
- Cross-View Invariants
- Representative Workflows
- Create and Update a Git-Versioned Project
- Check Updates from Automation
- Non-Goals
- Evaluation Notes

Covered counts by section:
- Product Overview: 0
- Scope: 0
- Installable Surface: 2
- Public API: 1
- `run_copy`: 5
- `run_recopy`: 3
- `run_update`: 1
- `Settings` and `load_settings`: 4
- `Phase` and `VcsRef`: 2
- CLI Behavior: 13
- Template Configuration: 3
- Rendering Model: 4
- Template Variables: 3
- Settings Reference: 1
- Answers Files: 4
- Updates: 2
- Unsafe Features: 4
- Error Semantics: 3
- Cross-View Invariants: 1
- Representative Workflows: 1
- Create and Update a Git-Versioned Project: 1
- Check Updates from Automation: 1
- Non-Goals: 0
- Evaluation Notes: 0

`wc -l tasks/copier-template-fullrepro-001/kept_nodeids.txt`: `51 tasks/copier-template-fullrepro-001/kept_nodeids.txt`

## Gate D - Coverage Gap Audit (retroactive)

| spec section | covered_count | minimum | verdict |
|---|---:|---:|---|
| Product Overview | 0 | 3 | ZERO |
| Scope | 0 | 3 | ZERO |
| Installable Surface | 2 | 3 | LOW |
| Public API | 1 | 3 | LOW |
| `run_copy` | 5 | 3 | OK |
| `run_recopy` | 3 | 3 | OK |
| `run_update` | 1 | 3 | LOW |
| `Settings` and `load_settings` | 4 | 3 | OK |
| `Phase` and `VcsRef` | 2 | 3 | LOW |
| CLI Behavior | 13 | 3 | OK |
| Template Configuration | 3 | 3 | OK |
| Rendering Model | 4 | 3 | OK |
| Template Variables | 3 | 3 | OK |
| Settings Reference | 1 | 3 | LOW |
| Answers Files | 4 | 3 | OK |
| Updates | 2 | 3 | LOW |
| Unsafe Features | 4 | 3 | OK |
| Error Semantics | 3 | 5 | LOW |
| Cross-View Invariants | 1 | 5 | LOW |
| Representative Workflows | 1 | 3 | LOW |
| Create and Update a Git-Versioned Project | 1 | 3 | LOW |
| Check Updates from Automation | 1 | 3 | LOW |
| Non-Goals | 0 | 3 | ZERO |
| Evaluation Notes | 0 | 3 | ZERO |

Gate D note: remaining ZERO rows, if any, are non-behavioral narrative/boundary sections rather than spec-derivable oracle targets; all core invariant/error/workflow/public-surface sections are covered after retroactive map repair and supplements.
Coverage verdict: PARTIAL
Oracle count before: 30 | after: 51
Sections with zero coverage: 4
Zero sections: Product Overview, Scope, Non-Goals, Evaluation Notes

Reference gate evidence: harness/score_pytest_original.py with .envs/copier-ref/Scripts/python.exe passed 51/51, pass_rate_excluding_skips=1.0; JSON saved to wip/copier-template-fullrepro-001/filter/reference_score_retro_gate_d.json.
Candidate runs were not re-run or modified.
