DO NOT send optional commentary

# Non-negotiable rules

Nine rules. Everything else lives in `dev/skills/{skill}/SKILL.md`; read the skill
for the pipeline stage you are in before touching any artifact.

## 1. Read the stage skill first

Before starting a pipeline stage, read `dev/skills/{skill}/SKILL.md` for that
stage. When delegating to a subagent, put the exact skill path in the delegation
prompt and instruct it to read the skill before inspecting artifacts.

## 2. Every oracle change requires a fresh lint result on disk

```bash
python harness/oracle_import_lint.py <task_id> tasks/<task_id>/spec.md \
  > wip/<task>/filter/lint_result.txt 2>&1
```

First line must read `LINT_PASS`. This is a state transition requirement, not a
suggestion: `S4_SETUP` and `QUALIFIED` are both blocked without it, and the file
must be newer than every test file under `oracle/`.

A task once shipped with eight atomic tests asserting an upstream exception tree
the spec never declared. The fairness spot-check ran as specified and did not see
them, because a sample of a subset cannot cover a defect concentrated in one
behaviour family. The rule was followed and the defect passed. Landing the output
makes the check reviewable instead of self-reported.

## 3. Never widen the spec to make a test pass

If an oracle test references a symbol the spec does not declare, remove the test.
Adding the symbol to the spec inverts what the benchmark measures: the assertion
then rewards a delivery that recalls upstream internals over one that implements
the specification. Route a spec change through spec-writer only when the
*behaviour* is in scope, never to satisfy a failing assertion.

## 4. A task is not qualified until the reference implementation passes 100%

The reference implementation, installed from `repo_commit`, must pass the complete
oracle with zero failures, recorded in `filter/reference_score.json`.

This is the only evidence separating a hard task from a broken oracle. One task
holds every model below 57% integration while its reference passes 86 of 86 - real
capability difficulty. Another had a reference that passed while spec-following
deliveries could not - a defective oracle. The scores alone do not distinguish
them.

## 5. Do not engineer the oracle toward a score target

Difficulty comes from candidate selection and post-hoc tiering. Calibration
thresholds (gap magnitude, top-model ceilings) are health checks on a finished
task, not admission criteria. Reverse-engineering an oracle until a task clears a
threshold costs more than keeping a task that turned out easy.

## 6. A task is not qualified until a mutation distinguishes spec-following from recall

Every task built from a real library must carry one validated mutation before it
enters the release set. Read `dev/skills/spec-mutator/SKILL.md` and run its
`S5_MUTATE` stage: change one spec clause and its oracle assertions together so the
described system diverges from the upstream namesake, mark each flipping test with
`// MUTATED: <clause-ref>`, and validate with the paired reference gates -- the
patched reference passes 100%, the unpatched upstream fails exactly the marked
tests.

Without this, a low candidate score is ambiguous: the model may have implemented
the spec, or recalled the crate. That ambiguity is the one thing the benchmark
exists to remove, so its absence is a release blocker. `task.json` must carry a `mutation` block
(`clauses`, `families`, `tests`), `ROOT-MAP.json` must exist and pass
`spec2repo-gate-calibration/scripts/audit_gate_design.py`, and the clean-upstream (M2)
control log must show exactly the preregistered mutation set failing. `check 9` of
`harness/verify_rust_task.sh` enforces this.

### 6a. Mutation is part of the spec, not a later stage

There is no separate "mutate the task afterwards" step. `spec2repo-gate-calibration`
lists M1 (patched reference), M2 (clean upstream), the behaviour-empty control and the
broad incomplete controls together as **Required controls**, all qualified in one step
(its workflow step 5). Treat mutation as product design, applied once, when the spec is
produced:

- **Before the spec** (candidate-selector exit): design the behavioural owners and
  preregister `ROOT-MAP.json` — every root with `id / layer / mutation / family /
  depends_on`. Mutation union roughly 60-75% of roots over 5-9 independent families, no
  family above about a quarter of mutation votes, native controls retained in the
  Composition layer.
- **In the spec** (spec-writer): write the mutated behaviour as the contract. The spec is
  born describing the mutated system; it never describes the upstream form and then gets
  edited. The INTERNAL header records which families diverge and why the upstream form is
  the guess a competent engineer would make.
- **At oracle qualification** (test-filter): the reference implementation *is* the patched
  upstream, so the ordinary reference gate at 100% **is** M1 — there is nothing extra to
  run. Add one more control run with the pristine upstream mounted: that is M2, and it
  must fail exactly the preregistered mutation set and pass the native set.

Selecting a mutation after the oracle exists does not work and should not be attempted.
Three targets were investigated on `gix-config-file-001` and each was rejected by a
different criterion (traversal order was also an oracle input; escape resolution could
only be re-pointed by editing test setup; the key-split change flipped a single test).
`gix-ref-txn-001` and `guppy-cargo-graph-fullrepro-001` failed the same way. The oracle
shapes that resist mutation — parametrised classification arrays, round-trip identity
assertions, computed metrics — are fixed once the oracle is built.

### 6b. Low pass rate comes from mutation-rich architecture, not from one clause

`dev/skills/spec2repo-gate-calibration/SKILL.md` is the authority for driving a pass rate
down. Its campaign defaults are the target for any task scoring at or above 50%:

- mutation union roughly **60-75% of roots**, spread over **5-9 independent families**,
  with no family controlling more than about a quarter of mutation votes;
- combined pass rate below 50% is excellent, below 60% is the target, above 75% normally
  triggers a new design version;
- raw Atomic-minus-Composition Gap must not be negative, and +20pp or more is preferred;
- native (non-mutated) controls must remain in the Composition layer, otherwise the Gap is
  an artefact of vote allocation rather than difficulty.

A single-clause mutation is enough to disambiguate recall from spec-following (Rule 6), but
it is **not** the instrument for lowering a pass rate. Do not add more boundary cases to one
parser or one mapping to try to lower a score: per that skill's design principles this
raises test count without reducing a capable candidate's pass rate. Add independent
behavioural owners instead.

## 7. Diagnose a failed run before scoring it; do not resample to average the problem away

A candidate run that does not compile or does not execute is not a score. Triage the cause
first, and let the cause decide what happens:

| cause | classification | action |
|---|---|---|
| Harness or environment defect — missing `-L` on `docker cp`, a partial lockfile, a feature flag the oracle needs, a wrong base image, provenance escape | `evidence_invalid` | fix the defect and re-run. Never record the score. |
| Task defect — spec withholds a compile-visible signature, oracle imports an undeclared symbol, fixture absent from the oracle tree | `evidence_invalid` | fix the task (route through the owning stage) and re-run. |
| Model defect — the delivery compiles-and-runs but is wrong, or diverges from a signature the spec does state | `product_failure` | this is a valid score. Record it. |

`spec2repo-gate-calibration` states the same rule from the scoring side: count only
explicit call-phase semantic mismatches as failed product votes; collection mismatches,
provenance escape, setup/teardown failures, timeouts and missing required public structure
invalidate the evidence instead.

Repeated sampling is **not** the instrument for this. Three samples of a broken measurement
are three broken measurements, and the time cost is not justified. One valid run, whose
failure mode has been diagnosed, is better evidence than three undiagnosed ones.

The one place resampling earns its cost is a score sitting on a disposition boundary. If a
single valid run lands within 2 points of the 50% ceiling, take one more sample before
writing a verdict — `gix-ref-txn-001` drew 41.2%, 51.8% and 40.0% on the same spec, a
12-point spread straddling the line. Outside that narrow band, one valid run decides.

## 8. Two instruments, two purposes — do not conflate them

`spec-mutator` and `spec2repo-gate-calibration` both mutate, for different reasons, and the
amount of mutation each requires is different.

| instrument | stated purpose | how much mutation | when it applies |
|---|---|---|---|
| `spec-mutator` | "Mutate a task's spec and oracle together so the described system **diverges from its upstream namesake**" — i.e. tell a spec-following delivery apart from one that recalled the crate | **>= 1 family** with >= 2 diverging tests, validated by the paired controls | **every** task |
| `spec2repo-gate-calibration` | evaluators "whose **low pass rates** come from independent behavioral structure" — i.e. drive a score down | mutation union 60-75% of roots over 5-9 families (campaign default; adjustable per its own "unless the user sets another policy") | a task whose measured score is **>= 50%** |

So the policy is:

- **Every task** must carry at least one mutation family whose divergence is measured by the
  clean-upstream control and contained to its preregistered set. This is what makes the score
  unambiguous, and it is the whole of what `spec-mutator` asks for.
- **Only a task scoring >= 50%** additionally needs the mutation-rich architecture. There the
  campaign numbers apply, adjusted for a real-library carve: union >= 25% over >= 5 families,
  because at 60-75% a carve of a real crate stops being a reconstruction of that crate and
  becomes a fiction resembling it, which conflicts with `candidate-selector`'s premise and
  with `spec-writer`'s requirement that the spec read as that package's documentation.

An earlier version of this rule demanded >= 25% union from every task. That was a conflation:
it applied the pass-rate instrument to tasks that already score far below the ceiling.
`gix-status-001` scores 12.5% with one validated family; it needs no additional mutation.

What is never relaxed: each family must be measured, contained, coherent as public behaviour,
and directed away from the guessable upstream form. A candidate mutation that disables a
subsystem (observed: `EGG-PRIMCTX-002`) or that no test observes (observed: `EGG-SETORD-004`)
is rejected, not shipped.

## 9. Characterise a task's score by the median of its samples

Where a task has more than one valid sample, its score is the **median**, and the full
distribution is recorded in `task.json` so the reasoning is auditable.

`gix-ref-txn-001` drew 41.2%, 51.8% and 40.0% on the same spec: median 41.2%, mean 44.3%,
two of three below the ceiling. Taking the maximum would classify it as a >= 50% task and so
demand the mutation-rich architecture of `spec2repo-gate-calibration` — applying the
pass-rate instrument to a task whose distribution already sits below the ceiling, which is
exactly the conflation Rule 8 corrects. Taking the median states what the samples show.

This does not weaken E1. A task whose median is at or above 50% still needs the pass-rate
work, and a task sitting within 2 points of the ceiling still takes a further sample
(Rule 7) before any verdict is written.

### Rule 10 — a constant-moving family does not lower the pass rate

Measured on gix-ref-peel-001 (`eval/runs/qwen3.8-max.4fam`, 2026-08-24): four families,
23 preregistered roots, of which the candidate failed 7 and passed 16. The split is by
family kind, not by family size.

| family | kind | roots failed |
|---|---|---|
| chain limit five to four | semantic | 4 of 4 |
| `follow` yields the reference itself | semantic | 2 of 2 |
| namespace prefix `refs/ns/` | named constant | 1 of 8 |
| packed file named `refs-packed` | named constant | 0 of 9 |

When a family moves a constant the specification states, the candidate reads the constant
and uses it. Those roots pass, and the pass rate does not move: the combined rate was 80.6%
with one family and 81.9% with four. Such a family is still worth having, because it is what
separates a candidate that follows the document from one that recalls upstream — that is
Rule 6's purpose. It is simply not pass-rate work.

Pass-rate work needs **semantic** deviations: an ordering, a limit, a precedence, a
which-wins rule — somewhere the upstream habit is strong enough that a candidate reaches for
it even after reading the document. The three qualifying tasks all rest on such a family
(gix-config: a single-value read resolves the first section, not the last; gix-status:
conflict-mask swap; gix-ref-txn: reflog previous-value).

So Rule 6b stands but needs this refinement: a mutation-rich architecture lowers the pass
rate only insofar as its families are semantic. Counting families or roots is not the
measure; the measure is how many roots the candidate actually loses.

### Rule 11 — a candidate needs a hard core *and* a statable declaration surface

Two constraints, and a candidate must satisfy both.

**Difficulty comes from reconstruction, not from counter-intuitive mutation.** Verified
independently on Java and TypeScript before it was verified here. In Java, versionsmith and
siftway carried five precisely declared counter-intuitive families each and still scored
100%, because a simple pure-function core is implemented correctly straight from the
document; they were eliminated. What scored was graph-transform at 20.3% (a whole
conflict-resolution pipeline with graph rewriting and several projections) and japicmp at 0%
(a complex bytecode API). In TypeScript, five single-concept cores saturated at 87-100% while
the one reconstruction-hard pick, schema-diff equivalence judgement, reached 45.8% with no
pass-rate work at all. Rule 10 measured the same thing from the other side: on a simple core
even a semantic family only costs the roots it names, and a constant-moving family costs
nothing. The three qualifying rust tasks fit the pattern — each is a multi-owner stateful
pipeline (status walk over index/worktree/HEAD; a reference transaction with locks, reflog
and packed refs; a config model with resolution, writers and normalisation).

**The declaration surface must be enumerable, and it is larger than functions and enum shapes.** egglog-lang-layer-001 first read as unscoreable, and that reading was wrong — it came from watching the compile-error count rise across runs without attributing the errors. Attribution per D3 showed the opposite: 28 of 38 named symbols were spec-declared and simply not delivered by the candidate. The real gap was a declaration surface stated only as type names: 19 enums with no variant bodies, 29 traits with no method sets, 26 structs with no public field lists. In a static language a trait is its method set and a struct is its public fields; a candidate cannot implement `Core` or construct `EGraph` without them. Supplying all 74 shapes verbatim from the carve (spec 1268 -> 1822 lines) moved the failures from "symbol not found" to "declared trait not implemented for this sort" — which is product_failure, the reconstruction difficulty the candidate was chosen for. So the surface must be enumerated in full (functions, enum variant shapes, trait method sets, struct public fields), but its size is not itself a disqualifier: a large surface that is fully stated and fully attributable is a valid hard task, not an unscoreable one.

What still disqualifies a candidate on this axis is a surface that cannot be enumerated by inspection at all, or one whose contract is behaviour a stub cannot stand in for. egglog sits at that edge: its remaining failures are missing trait implementations, so a signature-only probe cannot score it without supplying behaviour.
