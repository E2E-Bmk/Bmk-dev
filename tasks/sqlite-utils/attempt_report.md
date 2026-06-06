# Attempt Report: `sqlite-utils-realrepo-001`

## Candidate Setup

The candidate implementation was generated from `candidate_task/public_packet.md` only, using the local DeepSeek configuration. Hidden rubrics, scorer files, and source repository files were not included in the public packet.

Candidate output:

- `solution-agent-001/dbmini.py`

Reference output:

- `solution-reference/dbmini.py`

## Scoring Progression

- Reference raw score: 100.00%
- Candidate raw score: 64.52%
- Reference audited score: 100.00%
- Candidate audited score: 74.19%
- Reference expanded score: 100.00%
- Candidate expanded/audited score: 70.64%

## Failed Expanded Cases

- `SQI002` (`integrated` / `fts`, weight 12): FTS index returns original rows and can be rebuilt after data changes.
- `SQI003` (`integrated` / `transform`, weight 12): Transform renames, drops, defaults, and not-null constraints while preserving rows.
- `SQX001` (`expanded` / `fts`, weight 8): A simple FTS search after initial enable returns matching original rows.

## Interpretation

The candidate handled many durable workflows: typed import/query, upsert, extraction, compound primary keys, metadata output, simple transform, and the E2E atomicity checks. The significant gaps are concentrated in two product areas, FTS and complex transforms. This supports provisional acceptance while keeping the repeated-root caveat visible.

## Fairness Notes

The audited scorer avoids brittle expectations about arbitrary column order and checks persisted SQLite state directly. The remaining failures are traceable to the public packet's stated support for FTS and schema transforms, not to private implementation details.
