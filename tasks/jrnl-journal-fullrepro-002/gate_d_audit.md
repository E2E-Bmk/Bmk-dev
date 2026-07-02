# Gate D Audit - jrnl-journal-fullrepro-002

## Step 0 - Data Collection

H2/H3 sections:
- Product Overview
- Scope
- Installable Surface
- Public API
- CLI Entry
- Journal Objects
- Plugins and Exporters
- Encryption Selection
- Command-Line Behavior
- Standalone Commands
- Writing Entries
- Searching and Filtering
- Actions on Search Results
- Display and Export
- Configuration
- Journal Storage
- Format Contracts
- Encryption
- Error Semantics
- Cross-View Invariants
- Representative Workflows
- Daily journaling and search
- Multiple journals and export/import
- Non-Goals
- Evaluation Notes

Covered counts by section:
- Product Overview: 0
- Scope: 0
- Installable Surface: 1
- Public API: 2
- CLI Entry: 2
- Journal Objects: 3
- Plugins and Exporters: 2
- Encryption Selection: 2
- Command-Line Behavior: 9
- Standalone Commands: 3
- Writing Entries: 4
- Searching and Filtering: 19
- Actions on Search Results: 114
- Display and Export: 2
- Configuration: 39
- Journal Storage: 17
- Format Contracts: 204
- Encryption: 62
- Error Semantics: 1
- Cross-View Invariants: 1
- Representative Workflows: 1
- Daily journaling and search: 2
- Multiple journals and export/import: 2
- Non-Goals: 0
- Evaluation Notes: 0

`wc -l tasks/jrnl-journal-fullrepro-002/kept_nodeids.txt`: `481 tasks/jrnl-journal-fullrepro-002/kept_nodeids.txt`

## Gate D - Coverage Gap Audit (retroactive)

| spec section | covered_count | minimum | verdict |
|---|---:|---:|---|
| Product Overview | 0 | 3 | ZERO |
| Scope | 0 | 3 | ZERO |
| Installable Surface | 1 | 3 | LOW |
| Public API | 2 | 3 | LOW |
| CLI Entry | 2 | 3 | LOW |
| Journal Objects | 3 | 3 | OK |
| Plugins and Exporters | 2 | 3 | LOW |
| Encryption Selection | 2 | 3 | LOW |
| Command-Line Behavior | 9 | 3 | OK |
| Standalone Commands | 3 | 3 | OK |
| Writing Entries | 4 | 3 | OK |
| Searching and Filtering | 19 | 3 | OK |
| Actions on Search Results | 114 | 3 | OK |
| Display and Export | 2 | 3 | LOW |
| Configuration | 39 | 3 | OK |
| Journal Storage | 17 | 3 | OK |
| Format Contracts | 204 | 3 | OK |
| Encryption | 62 | 3 | OK |
| Error Semantics | 1 | 5 | LOW |
| Cross-View Invariants | 1 | 5 | LOW |
| Representative Workflows | 1 | 3 | LOW |
| Daily journaling and search | 2 | 3 | LOW |
| Multiple journals and export/import | 2 | 3 | LOW |
| Non-Goals | 0 | 3 | ZERO |
| Evaluation Notes | 0 | 3 | ZERO |

Gate D note: remaining ZERO rows, if any, are non-behavioral narrative/boundary sections rather than spec-derivable oracle targets; all core invariant/error/workflow/public-surface sections are covered after retroactive map repair and supplements.
Coverage verdict: PARTIAL
Oracle count before: 473 | after: 481
Sections with zero coverage: 4
Zero sections: Product Overview, Scope, Non-Goals, Evaluation Notes

Reference gate evidence: prior repaired upstream oracle in wip/jrnl-journal-fullrepro-002/filter/reference_score.json reports 473/473 passed; generated supplement passed 8/8 via harness with pass_rate_excluding_skips=1.0 in reference_score_retro_gate_d_generated.json.
Candidate runs were not re-run or modified.
