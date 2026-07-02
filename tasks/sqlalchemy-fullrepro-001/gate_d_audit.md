# Gate D Audit - sqlalchemy-fullrepro-001

## Step 0 - Data Collection

H2/H3 sections:
- Product Overview
- Scope
- Installable Surface
- Public API
- Engine and Execution
- Metadata, Tables, Columns, and Types
- Reflection and Inspection
- SQL Expressions and Compilation
- DML
- ORM Declarative Mapping
- Session and Unit of Work
- Relationships and Loading
- SQLite Dialect Behavior
- Error Semantics
- Cross-View Invariants
- Representative Workflows
- Core and ORM over SQLite
- Non-Goals
- Evaluation Notes

Covered counts by section:
- Product Overview: 0
- Scope: 0
- Installable Surface: 1
- Public API: 1
- Engine and Execution: 5
- Metadata, Tables, Columns, and Types: 2
- Reflection and Inspection: 2
- SQL Expressions and Compilation: 4
- DML: 2
- ORM Declarative Mapping: 2
- Session and Unit of Work: 7
- Relationships and Loading: 6
- SQLite Dialect Behavior: 7
- Error Semantics: 6
- Cross-View Invariants: 5
- Representative Workflows: 1
- Core and ORM over SQLite: 2
- Non-Goals: 0
- Evaluation Notes: 0

`wc -l tasks/sqlalchemy-fullrepro-001/kept_nodeids.txt`: `50 tasks/sqlalchemy-fullrepro-001/kept_nodeids.txt`

## Gate D - Coverage Gap Audit (retroactive)

| spec section | covered_count | minimum | verdict |
|---|---:|---:|---|
| Product Overview | 0 | 3 | ZERO |
| Scope | 0 | 3 | ZERO |
| Installable Surface | 1 | 3 | LOW |
| Public API | 1 | 3 | LOW |
| Engine and Execution | 5 | 3 | OK |
| Metadata, Tables, Columns, and Types | 2 | 3 | LOW |
| Reflection and Inspection | 2 | 3 | LOW |
| SQL Expressions and Compilation | 4 | 3 | OK |
| DML | 2 | 3 | LOW |
| ORM Declarative Mapping | 2 | 3 | LOW |
| Session and Unit of Work | 7 | 3 | OK |
| Relationships and Loading | 6 | 3 | OK |
| SQLite Dialect Behavior | 7 | 3 | OK |
| Error Semantics | 6 | 5 | OK |
| Cross-View Invariants | 5 | 5 | OK |
| Representative Workflows | 1 | 3 | LOW |
| Core and ORM over SQLite | 2 | 3 | LOW |
| Non-Goals | 0 | 3 | ZERO |
| Evaluation Notes | 0 | 3 | ZERO |

Gate D note: remaining ZERO rows, if any, are non-behavioral narrative/boundary sections rather than spec-derivable oracle targets; all core invariant/error/workflow/public-surface sections are covered after retroactive map repair and supplements.
Coverage verdict: PARTIAL
Oracle count before: 30 | after: 50
Sections with zero coverage: 4
Zero sections: Product Overview, Scope, Non-Goals, Evaluation Notes

Reference gate evidence: direct pytest reference run reported 50 passed; formal harness reference_score_retro_gate_d.json reports passed=50,total=50,pass_rate_excluding_skips=1.0.
Candidate runs were not re-run or modified.
