# TorkWorkflow Harness Draft

Candidate runs must use a cleanroom mini-SWE-agent-style harness.

Visible files:

- `candidate_task/public_packet.md`
- `candidate_task/starter/` once starter modules are created
- an empty output solution directory

Hidden files:

- source repo cache
- `rubric.json`
- `doc/requirement_map.md`
- `scoring/`
- reference implementation
- score reports
- prior traces and iteration notes

Candidate network should be disabled unless a later task variant explicitly
requires local-only package installation. The scorer runs outside the candidate
workspace.

Required saved artifacts per run:

- full agent trajectory;
- final solution tree;
- score report;
- leakage scan;
- failure cluster analysis.
