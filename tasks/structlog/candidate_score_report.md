# Cleanroom Candidate Score

- Environment: Docker Linux `python:3.11-slim`.
- Oracle: 64 filtered nodeids with scorer isolation `--remove-path structlog`.
- Result: 63 passed, 1 failed (98.44%).
- Layer results: atomic 22/23; integration 38/38; system_e2e 3/3.

The failed atomic behavior is `recreate_defaults(log_level=logging.INFO)`: the candidate left the root logger at `WARNING` instead of configuring the requested threshold. This is a public, v3-specified standard-library configuration behavior.

Raw grouped results are in [candidate_score_report.json](candidate_score_report.json). Candidate import provenance is retained in the cleanroom run's `linux-score/` evidence.
