# PRD And Rubric Contract

## Public Packet Sections

Every full-reproduction PRD must include:

1. Product overview and audience.
2. Non-goals and bounded scope.
3. State model and lifecycle.
4. Public API schemas.
5. CLI/service contracts.
6. Persistence and generated-artifact semantics.
7. Error, rollback, recovery, and replay semantics.
8. Ordering, determinism, and compatibility rules.
9. Multi-step workflow examples.
10. Ambiguity boundaries.

The PRD must be traceable to upstream evidence but non-isomorphic to the hidden
rubric. Examples teach use; hidden rows test mature behavior.

## Target Artifact Shape

State the required public artifact shape before hidden rubric design begins:

- runtime/language family if the harness requires one;
- package layout expectations;
- whether "service" means HTTP server, local daemon, CLI-backed process, or
  importable library plus CLI;
- required public entrypoints;
- allowed persistence backends;
- generated artifacts and reports that are part of the public contract.

For interface-defined tasks, provide a candidate-visible starter skeleton with
public modules, classes, function signatures, and documented return-shape
intent. Hidden unit tests may import these public modules. Hidden system tests
must integrate through the public facade, CLI, or service boundary.

For Python reference tasks, prefer:

```text
pyproject.toml
src/<package>/
  api.py
  cli.py
  store.py
  ...
```

For service-style tasks, a deterministic local process or CLI-backed service is
acceptable unless the PRD explicitly requires HTTP. Avoid real networking when a
local black-box boundary can test the same public behavior.

## Naming And Contamination Boundary

Use upstream concepts as inspiration, not exact public names. The public packet
may mention the source as inspiration in internal docs, but candidate-facing
PRDs should use benchmark-owned product names, schemas, command names, and
storage names when a famous library/protocol creates contamination risk.

Storage schemas may be public when users need to inspect or migrate them, but
do not expose private implementation layout just to make testing easier.

## Requirement Map

Map each public behavior to one or more sources:

- upstream docs;
- examples;
- tests;
- changelog;
- source-observed behavior;
- explicit benchmark variant decision.

Mark benchmark variants clearly so judges can distinguish intended custom
behavior from accidental divergence from upstream.

## Rubric Requirements

Minimum first strict suite:

- 50+ executable checks;
- at least 20 unit checks;
- at least 15 integration checks;
- at least 15 system/metamorphic checks;
- unit checks for primitives across modules;
- integration checks across public boundaries;
- system checks for lifecycle and projection consistency;
- metamorphic checks for replay/export/import/idempotence/order invariance;
- black-box execution from outside candidate workspace.

Every system row must state:

```text
cross_feature_contract:
setup_sequence:
public_assertions:
cascade_roots_to_ignore:
oracle_evidence:
```

## Fairness Rejects

Reject or revise rows that require:

- private helper imports;
- hidden internal file shapes;
- exact text not specified in PRD;
- arbitrary ordering;
- repeated primitive cascade counted as system gap;
- oracle choices not determined by public behavior;
- evaluator-only projections not produced by the candidate.
