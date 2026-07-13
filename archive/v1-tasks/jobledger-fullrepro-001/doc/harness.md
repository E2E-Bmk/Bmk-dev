# JobLedger Cleanroom Harness Plan

## Candidate Workspace

Visible files:

- `public_packet/prd.md`;
- starter `pyproject.toml`;
- interface-locked `src/jobledger/` package skeleton;
- optional public examples.

Hidden from candidates:

- `rubric.json`;
- reference implementation;
- score reports;
- previous mini tasks;
- iteration notes and trace audits.

Network is disabled. Tests run from outside the candidate package and import
only `jobledger.api` or execute `python -m jobledger.cli`.

## Expected Reference Shape

The reference implementation should preserve the starter public interfaces and
use at least 10 source modules and roughly 2,000+ non-test LOC. Public modules:

- `api.py`
- `cli.py`
- `models.py`
- `store.py`
- `scheduler.py`
- `retry.py`
- `uniqueness.py`
- `cron.py`
- `events.py`
- `metrics.py`
- `recovery.py`
- `export.py`

Candidates may add private modules, but hidden tests will import the public
starter modules and run the CLI. Removing or renaming public interfaces is a
contract failure.

## Scoring Phases

1. Install candidate package in an isolated temporary environment.
2. Run unit checks that import public modules only where documented.
3. Run integration checks crossing API, CLI, and persistence.
4. Run system/metamorphic checks with fresh temp ledgers and explicit virtual
   time.
5. Emit score report with raw failures, primitive/cascade clusters, and
   residual system gap.

## Trace Requirements

Save full agent trajectory, final artifact directory, package install logs, test
stdout/stderr, and score report. Do not let candidate see hidden assets.
