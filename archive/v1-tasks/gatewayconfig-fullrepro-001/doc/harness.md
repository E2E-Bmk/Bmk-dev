# GatewayConfig Harness Plan

## Cleanroom Candidate Workspace

Visible files:

- `public_packet.md`
- starter package `edgegate/`
- `pyproject.toml`
- public examples

Hidden from candidates:

- source repository clone
- reference implementation
- `rubric.json`
- scorer implementation
- score reports
- previous candidate traces

## Scoring

The scorer imports the candidate package and invokes public APIs and CLI
entrypoints from outside the candidate package. It must not import private helper
modules unless they are explicitly public in the starter skeleton.

Candidate runs are not allowed until:

- reference implementation passes all checks;
- starter baseline fails nontrivially;
- fairness judge confirms no private-shape, exact-text, APISIX-specific, or
  evaluator-only projection traps;
- cleanroom leakage scan passes.

## Required Trace

Every strict candidate evaluation must save:

- full mini-SWE-agent or OpenHands trajectory;
- final artifact snapshot;
- external score report;
- leakage scan report.
