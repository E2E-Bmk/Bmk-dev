# Qualification, scoring, and freeze discipline

## Validity precedes score

Every root runs in a fresh process or an equivalently strong isolated process.
The scorer must record setup, call, and teardown separately.

Invalidate the run or root for:

- collection mismatch;
- import or module provenance escape;
- setup/teardown failure;
- unexpected warning or ResourceWarning;
- syntax/import/type/attribute errors caused by missing required public
  structure when the campaign classifies those as infrastructure-invalid;
- evaluator timeout, malformed receipt, or nonzero runner status;
- candidate, evaluator, dependency, or reference tree drift.

Count only explicit call-phase semantic mismatches as failed product votes.
Keep the classification table preregistered. Do not widen exception handling
after seeing an Anchor result.

## Required controls

### M1: patched reference

- Exact root collection and 100% pass.
- Correct import origin from the pinned reference artifact/tree.
- Natural, reverse, and fixed-permuted vectors identical.
- Candidate and pinned source trees unchanged.

### M2: clean upstream

- Exact preregistered mutation failures and native passes.
- Missing mutation APIs may be installed through a signature-preserving
  behavior-empty scaffold, but the scaffold must not implement product logic.
- Report raw, conditional, adjusted, layer, family, mutation, and native
  slices.

### Behavior-empty control

- Complete public import shape.
- Every root reaches call phase.
- Zero passes.
- Failures are semantic product errors, not missing modules or unsupported
  signatures.

### Broad incomplete controls

Use at least two signature-preserving profiles that collapse different ideas,
for example “delivery equals acknowledgement” and “all owners share one
transaction.” They should terminate and produce distinct, preregistered blast
radii. If one broad profile passes nearly every mutation family, the gate is
probably testing one wrapper.

## Provenance containment

For every process:

- prepend only the assigned candidate root;
- record the root package origin;
- enumerate every loaded module in the candidate namespace;
- reject any module outside the candidate tree except explicitly registered
  evaluator overlays for reference/clean controls;
- forbid candidate symlinks and ambient-package fallback;
- hash the candidate tree before and after scoring.

This catches the dangerous false success where a partial candidate extends
`__path__` into an installed reference package.

## Freeze protocol

Freeze only after all qualification controls are valid under the final scorer.
The manifest should bind:

- SPEC, TASK, environment contract;
- root/dependency/mutation/capability maps;
- tests, support, runner, scorer, and registered overlays;
- all formal qualification receipts and audits;
- pinned commit/tree/runtime/dependency identities;
- strict source-blank payload hashes.

The candidate payload should contain only the public task/spec/environment
files required to implement the product, normally two or three files and no
Python source, maps, scores, or sidecars.

Write the freeze once, recompute every file hash and aggregate independently,
then make only read-only checks. Any required semantic edit creates a new
version. Never patch a frozen gate or candidate after an Anchor has been
scored.

## Solver protocol

Use one independent Solver per case unless the user explicitly requests more.
It receives only the strict payload and an empty assigned candidate directory.
It may run public self-authored smoke tests but cannot read the evaluator,
prior candidates, scores, or pinned reference.

After public smoke:

1. remove candidate-local smoke/cache artifacts;
2. hash and freeze the source tree;
3. run natural, reverse, and fixed-permuted local score orders against that
   exact tree;
4. reject invalid evidence without converting it to a low score;
5. release or exit under the preregistered policy.

One model implementation plus several local order checks provides stability
without spending tokens on duplicate implementations.
