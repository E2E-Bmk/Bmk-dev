---
name: spec2repo-gate-calibration
description: Design, calibrate, audit, freeze, and package mutation-rich Spec2Repo evaluators whose low pass rates come from independent behavioral structure rather than invalid tests, hidden answers, or infrastructure failures. Use for synthetic repository-reconstruction cases and frozen source-blank Solver evaluation; do not use for ordinary unit-test authoring.
---

# Spec2Repo gate calibration

Build gates that separate a capable source-blank implementation from shallow
API imitation while keeping every score semantically valid and auditable.

## Non-negotiable outcome

- A pinned reference passes every root with exact collection, provenance, and
  tree immutability.
- A behavior-empty candidate reaches the semantic call phase on every root
  and passes none.
- Missing imports, collection/setup/teardown failures, warnings, timeouts,
  provenance escape, or harness mistakes invalidate evidence; they never
  count as product failures.
- The candidate-facing specification reads like normal OSS documentation. It
  describes reusable behavior families, not root IDs or hidden assertions.
- Freeze all evaluator inputs before exposing them to a Solver. Do not edit a
  frozen version or its candidate after scoring.

## Campaign defaults

Treat these as defaults unless the user sets another policy:

- Mutation union: roughly 60–75% of roots.
- Combined pass rate: below 50% is excellent, below 60% is the target,
  60–75% is tolerable with an audit, and above 75% normally triggers a new
  design version.
- Raw Atomic-minus-Composition Gap must not be negative; +20 percentage
  points or more is preferred.
- Use one independent source-blank Solver per case. Natural, reverse, and
  fixed-permuted runs are local order checks of the same frozen candidate,
  not three model implementations.
- Root counts are chosen by the product architecture; never force 20+40 only
  because an earlier campaign used it.

## Workflow

1. Read the product's public surface and prior architecture-level lessons.
   Do not reuse prior candidate source or exact failed-root answers.
2. Design multiple independent behavioral owners and a closed dependency
   graph. Put native controls in both local and composed layers.
3. Write normal candidate-facing behavior rules, then audit that every public
   import, signature, record shape, and protocol operation used by the oracle
   is actually declared.
4. Preregister root inventory, mutation families, broad incomplete controls,
   score formulas, validity rules, and disposition thresholds.
5. Qualify reference, clean upstream, behavior-empty, and broad controls in
   fresh processes. Inspect raw and anti-weight metrics.
6. Freeze a minimal source-blank payload and hash-bound evaluator inventory.
7. Run exactly one independent Solver, freeze its source tree, then score that
   same tree in local order modes. Admit only valid evidence.
8. Release, redesign under a new version, or exit/defer with a precise reason.
   Package only user-requested delivery assets.

## Reference routing

- Read [design-principles.md](references/design-principles.md) when designing
  roots, mutation families, or a specification intended to reduce pass rate.
- Read [qualification-and-freeze.md](references/qualification-and-freeze.md)
  when implementing the scorer, evidence rules, manifests, or Solver protocol.
- Read [failure-patterns.md](references/failure-patterns.md) when a score is
  unexpectedly high/low, Gap is negative, or a run becomes invalid.
- Read [cost-and-operations.md](references/cost-and-operations.md) when
  optimizing token use, parallel work, retry policy, or final packaging.

Run `scripts/audit_gate_design.py ROOT-MAP.json` before qualification. It
checks layer counts, mutation ratio, family dominance, dependency closure,
cross-owner composition, and optional observed score shape.

## Judgment rules

- Clean-upstream M2 proves mutation wiring, not source-blank difficulty. Its
  conditional Composition rate and adjusted Gap must be reported.
- Low pass rate is not intrinsically good. Prefer independent decisions over
  many variants of the same edge case.
- A broad wrapper that satisfies several roots is evidence that the roots
  share one hidden decision; split the architecture, not the assertion text.
- Go or another language is appropriate only when it preserves an authentic
  public task surface. Never change language merely to force the score down.
