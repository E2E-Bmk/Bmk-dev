# Source Repository

- Repository: `simonw/sqlite-utils`
- Local checkout: `G:/research/swe-e2e/sources/simonw__sqlite-utils`
- Commit: `8f0c06e1889513ed0f01cb57783ddf07c442d4be`

## Source Signals

`sqlite-utils` is a CLI and Python library for manipulating SQLite databases. The README, docs, changelog, and tests show a product surface spanning:

- JSON/CSV/TSV import into inferred schemas
- primary keys and upserts
- altering tables as new columns appear
- querying and listing rows/tables
- full-text search enablement and search
- extracting repeated values into lookup tables
- transforming table schemas while preserving rows
- preserving/inspecting database state across commands

## Benchmark Adaptation

The candidate does not rebuild the full package. The benchmark asks for a compact Python 3.11 CLI named `dbmini.py` that implements a useful subset of the database lifecycle. Hidden scoring inspects the SQLite database directly after multi-command workflows.

This case is promising because the output artifact is durable relational state. Correct behavior requires schema inference, mutation, derived lookup/FTS state, and atomic error handling, not just formatting command output.
