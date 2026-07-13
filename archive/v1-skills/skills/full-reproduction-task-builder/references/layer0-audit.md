# Layer-0 Audit Reference

Use this audit once per candidate before task construction. Do not loop inside
Layer 0. Record evidence, verdict, and next action.

## Required Checks

Architecture integrity:

- at least two logical modules/classes/services;
- shared fact source is more than a tiny dict/tree;
- at least four public projections can drift;
- product lifecycle includes create/update/delete/replay/recovery or equivalent
  state transitions.

Scale integrity:

- natural reference requires 10+ source files;
- roughly 2,000+ non-test LOC;
- public CLI/service and importable API both matter;
- one-file or prompt-sized solution is rejected as `UNDER_SCOPED`.

Agreement-surface freedom:

- each key design decision has at least two locally plausible choices;
- a public system invariant chooses among those choices;
- if public standards/specs uniquely determine all decisions, verdict is
  `FORCED`.

Contamination risk:

- near-clone of a famous library, benchmark, protocol, or standard gets
  `CONTAMINATED` unless the task introduces a product-natural variant;
- do not claim model data leakage without trace evidence.

Feature-pure test scan:

- unit setup uses only the feature under test, constructor state, or mocks;
- cross-feature setup belongs in integration/system tests.

Unit semantic scan:

- unit checks assert public behavior, not private strings, reprs, file order,
  internal serialization, or exact exception classes unless public.

Collapse scan:

- if all views can route through one obvious helper/model and system tests pass
  automatically, verdict is `COLLAPSE`;
- if all views are recomputable from current state in one pass, require public
  history, replay, rollback, cache invalidation, or materialized outputs.

## Verdicts

- `BUILD`: proceed to PRD/rubric.
- `RESCOPE`: promising domain, current surface too small.
- `REPAIR_PRIMITIVES`: concept valid, primitive coverage blocks fair signal.
- `UNDER_SCOPED`: upstream large but extracted task too small.
- `FORCED`: public spec/standard determines the result.
- `CONTAMINATED`: too close to famous implementation or benchmark pattern.
- `COLLAPSE`: obvious shared helper/model eliminates agreement surface.
- `STRUCTURAL_DEAD`: no plausible agreement surface at this scope.
- `EXCLUDED`: no reliable public product surface or oracle.

## Audit Record Template

```text
candidate_id:
source_repo:
upstream_scale:
product_surface:
shared_fact_source:
public_projections:
local_free_choices:
global_public_invariants:
contamination_risk:
scale_gate:
feature_pure_risks:
unit_semantic_risks:
collapse_risk:
verdict:
next_action:
```
