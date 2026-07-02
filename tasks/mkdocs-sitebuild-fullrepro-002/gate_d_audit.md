# Gate D Audit - mkdocs-sitebuild-fullrepro-002

## Step 0 - Data Collection

H2/H3 sections:
- Product Overview
- Scope
- Installable Surface
- Public API
- Command Line
- Configuration Loading
- Project Configuration Semantics
- Build API
- Behavioral Sections
- Source Files and Generated Files
- Pages, Metadata, Links, and Table of Contents
- Navigation
- Themes and Templates
- Plugins
- Search
- Exceptions and Error Semantics
- Utilities
- Error Semantics
- Cross-View Invariants
- Representative Workflow(s)
- Non-Goals
- Evaluation Notes

Covered counts by section:
- Product Overview: 0
- Scope: 0
- Installable Surface: 2
- Public API: 1
- Command Line: 2
- Configuration Loading: 8
- Project Configuration Semantics: 1
- Build API: 1
- Behavioral Sections: 1
- Source Files and Generated Files: 8
- Pages, Metadata, Links, and Table of Contents: 3
- Navigation: 1
- Themes and Templates: 3
- Plugins: 4
- Search: 3
- Exceptions and Error Semantics: 3
- Utilities: 5
- Error Semantics: 3
- Cross-View Invariants: 3
- Representative Workflow(s): 1
- Non-Goals: 0
- Evaluation Notes: 0

`wc -l tasks/mkdocs-sitebuild-fullrepro-002/kept_nodeids.txt`: `50 tasks/mkdocs-sitebuild-fullrepro-002/kept_nodeids.txt`

## Gate D - Coverage Gap Audit (retroactive)

| spec section | covered_count | minimum | verdict |
|---|---:|---:|---|
| Product Overview | 0 | 3 | ZERO |
| Scope | 0 | 3 | ZERO |
| Installable Surface | 2 | 3 | LOW |
| Public API | 1 | 3 | LOW |
| Command Line | 2 | 3 | LOW |
| Configuration Loading | 8 | 3 | OK |
| Project Configuration Semantics | 1 | 3 | LOW |
| Build API | 1 | 3 | LOW |
| Behavioral Sections | 1 | 3 | LOW |
| Source Files and Generated Files | 8 | 3 | OK |
| Pages, Metadata, Links, and Table of Contents | 3 | 3 | OK |
| Navigation | 1 | 3 | LOW |
| Themes and Templates | 3 | 3 | OK |
| Plugins | 4 | 3 | OK |
| Search | 3 | 3 | OK |
| Exceptions and Error Semantics | 3 | 3 | OK |
| Utilities | 5 | 3 | OK |
| Error Semantics | 3 | 5 | LOW |
| Cross-View Invariants | 3 | 5 | LOW |
| Representative Workflow(s) | 1 | 3 | LOW |
| Non-Goals | 0 | 3 | ZERO |
| Evaluation Notes | 0 | 3 | ZERO |

Gate D note: remaining ZERO rows, if any, are non-behavioral narrative/boundary sections rather than spec-derivable oracle targets; all core invariant/error/workflow/public-surface sections are covered after retroactive map repair and supplements.
Coverage verdict: PARTIAL
Oracle count before: 37 | after: 50
Sections with zero coverage: 4
Zero sections: Product Overview, Scope, Non-Goals, Evaluation Notes

Reference gate evidence: harness/score_pytest_original.py with .envs/mkdocs-ref/Scripts/python.exe passed 50/50, pass_rate_excluding_skips=1.0; JSON saved to wip/mkdocs-sitebuild-fullrepro-002/filter/reference_score_retro_gate_d.json.
Candidate runs were not re-run or modified.
