# Gate D Audit - packaging-core-fullrepro-001

## Step 0 - Data Collection

H2/H3 sections:
- Product Overview
- Non-Goals
- Package Shape
- Version Handling
- Specifiers
- Version Ranges
- Markers
- Requirements
- Tags
- Utilities
- Metadata
- Direct URL Records
- Dependency Groups
- Pylock Files
- License Expressions
- Error Helpers
- Cross-Component Invariants
- Error Semantics
- Candidate Agent Input Boundary

Covered counts by section:
- Product Overview: 0
- Non-Goals: 0
- Package Shape: 1
- Version Handling: 1
- Specifiers: 1
- Version Ranges: 1
- Markers: 1
- Requirements: 1
- Tags: 1
- Utilities: 1
- Metadata: 2
- Direct URL Records: 1
- Dependency Groups: 1
- Pylock Files: 1
- License Expressions: 1
- Error Helpers: 1
- Cross-Component Invariants: 1
- Error Semantics: 3
- Candidate Agent Input Boundary: 0

`wc -l tasks/packaging-core-fullrepro-001/kept_nodeids.txt`: `123 tasks/packaging-core-fullrepro-001/kept_nodeids.txt`

## Gate D - Coverage Gap Audit (retroactive)

| spec section | covered_count | minimum | verdict |
|---|---:|---:|---|
| Product Overview | 0 | 3 | ZERO |
| Non-Goals | 0 | 3 | ZERO |
| Package Shape | 1 | 3 | LOW |
| Version Handling | 1 | 3 | LOW |
| Specifiers | 1 | 3 | LOW |
| Version Ranges | 1 | 3 | LOW |
| Markers | 1 | 3 | LOW |
| Requirements | 1 | 3 | LOW |
| Tags | 1 | 3 | LOW |
| Utilities | 1 | 3 | LOW |
| Metadata | 2 | 3 | LOW |
| Direct URL Records | 1 | 3 | LOW |
| Dependency Groups | 1 | 3 | LOW |
| Pylock Files | 1 | 3 | LOW |
| License Expressions | 1 | 3 | LOW |
| Error Helpers | 1 | 3 | LOW |
| Cross-Component Invariants | 1 | 3 | LOW |
| Error Semantics | 3 | 5 | LOW |
| Candidate Agent Input Boundary | 0 | 3 | ZERO |

Gate D note: remaining ZERO rows, if any, are non-behavioral narrative/boundary sections rather than spec-derivable oracle targets; all core invariant/error/workflow/public-surface sections are covered after retroactive map repair and supplements.
Coverage verdict: PARTIAL
Oracle count before: 110 | after: 123
Sections with zero coverage: 3
Zero sections: Product Overview, Non-Goals, Candidate Agent Input Boundary

Reference gate evidence: selected 122-nodeid oracle passed under harness with expanded pytest result 5487/5487; additional Tags test passed 1/1 via harness, pass_rate_excluding_skips=1.0, JSON saved to wip/packaging-core-fullrepro-001/filter/reference_score_retro_gate_d_tags.json.
Candidate runs were not re-run or modified.
