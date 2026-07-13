# FlowLedger Harness Plan

## Visibility Contract

Candidate-visible workspace contains only:

- `candidate_task/public_packet.md`;
- `candidate_task/starter/`;
- normal package dependency metadata.

Candidate workspace must not contain:

- upstream source repo;
- `doc/`;
- `rubric.json`;
- reference implementation;
- score reports;
- prior model traces;
- iteration notes or judge reports.

## Execution Contract

- Use a mini-SWE-agent-style cleanroom workspace.
- Network disabled during candidate implementation unless explicitly testing
  package installation.
- Candidate implements the Python package in the starter skeleton.
- Full trajectory is saved.
- Scoring runs externally by installing/copying the candidate artifact into a
  separate scorer workspace.

## Scoring Gate

Do not run candidate models until:

- hidden checks are executable, not only rubric intents;
- reference implementation passes every check;
- leakage audit shows no hidden paths or rubric terms in the candidate packet;
- public packet and hidden rows have been fairness audited.
