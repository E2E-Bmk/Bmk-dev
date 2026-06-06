# SQLite-Utils Case Summary

## Outcome

`sqlite-utils-realrepo-001` is accepted as a provisional target-band task.

- Raw score: 64.52%
- Audited score: 74.19%
- Expanded/audited score: 70.64%
- Reference expanded score: 100.00%
- Decision: provisionally useful, with a clustered-failure caveat

## Why It Worked

SQLite-utils-style workflows create separability because the implementation must persist and mutate real relational state across commands. The public packet describes the product surface, while hidden rubrics compose that surface into durable database workflows:

- JSON and CSV import with useful type inference
- primary-key insert and upsert behavior
- schema alteration while preserving existing rows
- extracted lookup tables and foreign-key-like relationships
- full-text search as a derived index over source rows
- table transforms that preserve data while changing schema
- atomic failure behavior for invalid transforms and imports

## Audit Notes

The first audit removed or relaxed assumptions that were not fair products of the public packet:

- inferred column order was not treated as a hidden requirement
- transform atomicity checks were changed to validate schema equality without relying on insertion-order artifacts

The expanded rubric then added simpler coverage for compound primary keys, metadata outputs, FTS, and a narrower transform path. This pulled the audited score from 74.19% to 70.64%.

## Caveat

The remaining failed weight is valid but clustered:

- 20 weight points come from FTS behavior
- 12 weight points come from the richer transform workflow

This means the task is useful for relational workflow reconstruction, but less broadly diagnostic than Cookiecutter. The score should be reported with the FTS/transform cluster noted.

## Lesson

Relational CLI tasks are promising when the scorer inspects durable database state instead of exact terminal formatting. The best rubrics here are traceable but non-isomorphic: the public packet names import, query, upsert, extract, FTS, transform, and atomicity principles, while hidden tests combine them into persisted schemas, derived indexes, and recovery workflows.
