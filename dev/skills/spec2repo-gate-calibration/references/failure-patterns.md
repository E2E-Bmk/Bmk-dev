# Failure patterns and diagnosis

## Unexpectedly high pass rate

Likely causes:

- The specification is answer-like and maps each clause to one assertion.
- Composition roots are happy-path API chains rather than overlapping owner
  workflows.
- Several families share one generic state dictionary or rollback wrapper.
- More edge examples were added without adding independent behavior.
- Public operations are locally implementable and System roots do not require
  durable receipt closure or reopen.
- Broad controls were omitted, so a wholesale shortcut was never measured.

Remedy: add independent product surfaces, owner-specific persistence, failure
and recovery transitions, sibling preservation, receipt prerequisites, and
cross-process observations. Do not merely add obscure constants or exact
messages.

## Negative Gap

Integration may be easier because it reuses one broad facade, because Atomic
roots are unusually detailed, or because vote allocation makes native
Composition too sparse. Inspect family covariance and conditional/adjusted
Gap. Split shared decisions, add real native cross-view controls, and require
cross-owner evidence. Redesign under a new version; never tune a scored root.

## Artificially low pass rate

Reject apparent low scores caused by:

- missing evaluator assets or undeclared public imports;
- ImportError, collection error, setup/teardown failure;
- candidate modules loaded from an ambient package;
- warnings-as-errors, ResourceWarning, leaked threads, or timeout;
- harness `KeyError`/`IndexError` from indexing missing data without a guard;
- a dummy that lacks public classes/signatures;
- a test that never reaches the candidate call.

These are invalid evidence, not difficult semantics.

## Concrete lessons from the campaign

- A candidate that appended an installed reference package to its namespace
  appeared to pass many roots. Module-origin enumeration correctly invalidated
  the result; no semantic score was admitted.
- A frozen evaluator imported a color constant that the public SPEC never
  declared. Fourteen roots failed during module setup. The correct disposition
  was a frozen-gate contract defect, not a 1/N low score.
- Earlier packages with excellent separation combined several independent
  behavioral surfaces and cross-view workflows; simply expanding boundary
  cases did not reproduce that separation.
- Some low clean-upstream scores had conditional Composition at 100% and a
  strongly negative adjusted Gap. They qualified mutation wiring but did not
  prove source-blank difficulty.
- Thread barriers without `finally` release turned candidate failure into
  evaluator hangs. Exception queues, barrier abort/release, and bounded joins
  restored finite semantic evidence.

## Disposition taxonomy

- `qualified-release`: valid reference/control/freeze/Anchor evidence and
  acceptable score shape.
- `qualified-release-with-audit`: valid but outside the preferred range;
  architecture evidence supports usefulness.
- `redesign-required`: valid evidence but pass rate/Gap or broad-control
  analysis exposes structural weakness.
- `frozen-gate-defect`: scored version requires an evaluator or public-contract
  change; exit it and create a successor.
- `anchor-provenance-invalid`: candidate escaped its source tree; no score.
- `defer`: external runtime/dependency/authority genuinely unavailable after
  safe alternatives are exhausted.

Never call an invalid run “0%” and never call redesign/defer a successful
release.
