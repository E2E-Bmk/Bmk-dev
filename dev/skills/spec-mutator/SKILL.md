---
name: spec-mutator
description: "Mutate a task's spec and oracle together so the described system diverges from its upstream namesake, then re-score to measure whether a model's result comes from reading the spec or recalling the library. Use after a task passes the reference gate and before it enters the release set. Covers mutation selection, paired reference gates, mutated-test classification, and the memorisation verdict."
---

# Spec Mutator

Mutate a task so a recalled library no longer answers it, then measure what
changes.

| Step | Produces | Gate that closes it |
|---|---|---|
| [1 — Select the target](#step-1--select-the-mutation-target) | `mutation/record.md` | five criteria all met |
| [2 — Mutate spec and oracle](#step-2--mutate-spec-and-oracle-together) | edited `spec.md`, edited oracle | structural diff equals the declared test list |
| [3 — Classify and re-verify](#step-3--classify-the-mutated-tests) | `mutation` block, markers | `STATIC_VALID` on the variant id; three records agree |
| [4 — Run the paired gates](#step-4--the-reference-gate-restated) | two reference logs | M1 passes 100%, M2 fails exactly the marked tests |
| [5 — Score both packets](#step-5--score-both-packets) | paired run directories | each mutated test stable within its own side |
| [6 — Read the result](#step-6--read-the-result) | the verdict | one of four quadrants, stated as counts |

---

## Orientation

### Why mutate

A score against a task built from a real library is ambiguous: the model may have
implemented the spec, or recalled the library and been rewarded for it. Both
produce the same number.

Mutation resolves the ambiguity. Change a behavior in the spec and the oracle
together, so the described system no longer matches the library the model may
have memorised. An implementation written from the spec is unaffected; one
written from recall now fails on exactly the mutated behavior.

The output is a **paired measurement** over the mutated tests — same model, same
settings, both packets. How those few tests move between the two runs is the
evidence, not the change in either total, which a handful of tests cannot shift
far.

### State machine interface

**Entry.** Read `wip/{task}/PIPELINE_STATE.md`; `state` must be `S5_MUTATE`.
Two preconditions:

1. `harness/verify_task.py <task-id>` prints `STATIC_VALID`
2. the baseline reference gate passes — upstream package installed, 100% of the
   oracle passing

If either fails, set `state → S2_SPEC_DRAFT` and escalate. Mutating a defective
task measures the defect, not the model.

**Exit — accepted.** `mutation/record.md`, `mutation/reference_patch.py`, both
reference logs and the paired scores all exist, and
`harness/verify_task.py <variant-id>` prints `STATIC_VALID`. Set
`state → S5_MUTATE_DONE`, append History row.

**Exit — loop.** Gate M2 shows no divergence: set `state → S5_MUTATE`, increment
`mutate_iter`, choose a different target. Above `mutate_iter > 3`, stop and
escalate — this task may have no mutable surface.

### Reading the commands

Every check below is stated as a principle, then illustrated with a command for
a Python packet — the majority language in this pool. For a packet in another
language, keep the principle and replace the tool: a parser for that language
instead of `ast`, its test framework's tagging mechanism instead of a pytest
marker, its dependency-injection point instead of a `.pth` file. A check skipped
because its example command does not apply is a check not performed.

### Relationship to spec-writer

`spec-writer` owns one artifact and one question: does this spec describe the
behavior completely and derivably? This skill edits two artifacts under a joint
constraint, requires two opposite gate outcomes, produces a paired measurement,
and runs after the reference gate — when spec-writer's state machine has exited.

The linkage is a handoff: `spec-writer` delivers a complete spec, the reference
gate confirms it, and this skill establishes whether the resulting score means
what it appears to mean.

---

## Step 1 — Select the mutation target

### 1a. The five criteria

Read `clauses.md` and pick a clause meeting all five:

| # | Criterion | How to check |
|---|---|---|
| 1 | **Spec-stated** | The behavior has a clause ID. Mutating undeclared behavior tests nothing — a candidate could not have known either version. |
| 2 | **Asserted by more than one test** | Read the body of every test that mentions the behavior; a `grep` count is not the number of dependent tests. Count only tests whose pass/fail flips under the mutation. One is not enough — a single flip cannot be told from the run-to-run variation Step 5 measures — but padding the count with tests that merely mention the name is worse than a small honest set. |
| 3 | **Independently implementable** | A candidate can satisfy the mutated form without restructuring the rest of the package. |
| 4 | **Divergent from upstream** | Establish divergence by *observation*, not inference. Run the behavior against the installed package and see what it does. Documentation, a similarly-named helper, or a sibling code path implementing the same rule are all unreliable — a library may enforce a rule on one entry point and not another, and the oracle exercises exactly one of them. |
| 5 | **Unguessable in the mutated direction** | Ask what a competent engineer would write knowing nothing of this library. If that is the *mutated* form, the mutation cannot discriminate: a candidate reaching it from intuition looks identical to one reaching it from the spec, and both pass. Mutate *toward* the surprising form, not away from it. |

### 1b. Choosing the direction

**Criterion 5 is the one most easily got backwards.** A library's
counter-intuitive rules look like tempting targets — they are exactly what a
model must recall or read. But mutating such a rule *into* the natural one hands
the answer to everybody: the recall-driven and the spec-driven candidate now
write the same code. Go the other way — take a rule whose upstream form is what
anyone would guess, and mutate it into something only the spec discloses.

**Criteria 3 and 5 pull against each other, and criterion 3 wins.** The
surprising direction is often surprising precisely because the natural rule is
load-bearing elsewhere: invert it and everything relying on it breaks. Check
mechanically before writing the patch — count the tests *outside*
`mutation.tests` that exercise the same rule. If that count is not zero, the
inversion reaches them and Gate M1 fails on tests you never meant to touch. A
target satisfying both criteria is one whose natural form is *incidental*.

**Mutation kinds, by signal strength:**

| Kind | Shape | Why recall fails it |
|---|---|---|
| Inverted default | a sentinel value's meaning is reversed | recall supplies the opposite semantics |
| Renamed public argument | a keyword argument takes a different name | recall supplies the upstream name |
| Changed return shape | a function returns a different arity or ordering | recall supplies the upstream shape |
| Reordered composition | a pipeline passes its previous result at a different position | recall supplies the upstream order |
| Different exception type | a failure condition raises a different public exception | recall supplies the upstream type |

### 1c. Disqualifications

Beyond what the criteria already exclude:

- **Anything requiring changes inside a third-party dependency** —
  unimplementable, so Gate M1 can never pass.
- **The behavior is also an input.** Where the oracle *passes* the value it also
  checks — a coordinate base, an index origin, a unit — mutating it changes what
  every call means, not just what the assertions expect. Such a mutation reaches
  far past its clause and fails the M2 containment check.

One behavior per variant. A compound mutation cannot be attributed when the
score moves.

**Expect to reject candidates**, most often on criterion 2 or 4: a name
appearing a dozen times is usually a fixture argument, a setup value, or an
unrelated scenario, and only the assertions that flip count. Reject and move on
rather than stretching a marginal candidate; repeated failures mean the task may
have no mutable surface, which the state machine treats as an escalation.

### 1d. Record before editing

Write `mutation/record.md`:

```
target clause:   <CLAUSE-ID>
upstream form:   <what the library does>
mutated form:    <what the spec will now require>
oracle tests:    <every test whose outcome flips under the mutation>
implementable:   <why a candidate can satisfy the mutated form independently>
divergent:       <why the upstream package will now fail>
```

---

## Step 2 — Mutate spec and oracle together

Both, in one change. A mutation in only one is a defect:

- spec only → the oracle contradicts the spec; every candidate fails unfairly
- oracle only → the spec no longer describes the scored behavior; the task
  violates the fairness rule this pipeline exists to enforce

### 2a. Spec side

Rewrite the clause in its EARS template — *in place*, as a replacement for the
sentence that is there.

**Rewrite the clause; do not add or remove one.** Clause IDs are positional, so
inserting or deleting one renumbers every later clause in that section. The
oracle's `Verifies:` citations still resolve — to the wrong clauses — and nothing
reports it, because a citation is checked for existence, not meaning. If the
mutated behavior genuinely needs a new clause, add it at the *end* of its
section, where no existing ID moves, then re-verify that section's citations.

Regenerate the sidecar and confirm the count is unchanged:

```bash
SPEC2REPO_TASKS_DIR=<pool> python3 analysis/gen_clause_anchors.py <task-id>
```

**The clause must read as ordinary library documentation.** A sentence that
sounds like a deliberate deviation ("unlike other libraries, this one…") tells
the candidate a mutation happened and defeats the measurement.

### 2b. Oracle side

Update every assertion reading the mutated behavior. Change nothing else.

**Keep the test names, and prefer editing an existing test to adding one.**
Step 6 pairs the two runs by test id, so any id that exists in only one packet
drops out of the comparison — which a rename and a new test cause equally.
Renaming is the stronger instinct, since a mutated test now asserts the opposite
of what its name says; resist it. Where a name becomes actively misleading
(`..._rejects_...` on a test that now admits), leave the name and let the
`Mutated:` docstring paragraph carry the divergence.

**If the mutation reaches only one test**, look for other *existing* tests
through the same clause. Extending beats replacing: a test asserting that
something is refused can assert the mutated acceptance *and* keep its original
refusal for a case the mutation does not cover — the old id survives, the
coverage survives, and the mutation gets a home.

**Change the assertion, not the setup.** A rewrite that reaches for a new
capability — a factory in the setup line, but equally a registered name, a
configured key, or an optional feature named inside the assertion — makes the
test depend on something the mutation is not about. A candidate implementing the
mutated rule correctly then still fails for lacking that piece, and Step 6
attributes the failure to the mutated clause.

The safe rule: every name the mutated version depends on must also be reached by
some test the baseline packet already passes, so the baseline run itself proves
the candidate has it. Diff the two versions before the gates; only assertion
lines should differ.

Where you must add a test, verify its premise against the installed package
first — one built on a value, name or option that does not exist upstream fails
for the wrong reason, and Gate M1 will reject it once the patch is in place.

### 2c. Check: nothing outside the intended tests moved

A text diff will not reveal an accidental edit buried in a large change:

```bash
python3 - <<'EOF' <baseline-oracle>/test_atomic.py <mutated-oracle>/test_atomic.py
import ast, sys
def strip(tree):
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            b = n.body
            if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) \
               and isinstance(b[0].value.value, str):
                n.body = b[1:] or [ast.Pass()]
    return tree
old, new = (strip(ast.parse(open(p).read())) for p in sys.argv[1:3])
a = {n.name: ast.dump(n) for n in ast.walk(old) if isinstance(n, ast.FunctionDef)}
b = {n.name: ast.dump(n) for n in ast.walk(new) if isinstance(n, ast.FunctionDef)}
print("changed:", sorted(k for k in a.keys() & b.keys() if a[k] != b[k]))
EOF
```

The printed list must equal the test list in `record.md`.

---

## Step 3 — Classify the mutated tests

A mutated test is unsatisfiable by the upstream package by construction. Every
downstream gate needs to know which tests those are, or it will read a
deliberate divergence as a defect. Mark at three levels; all three must agree.

### 3a. In the test itself

Both machine-readable and human-readable. The machine-readable form is whatever
the language's test framework offers for attaching metadata to a test — an
annotation, a tag, a naming convention. The human-readable form is a note in the
test's own documentation saying what was mutated and why it fails upstream. For
a Python packet:

```python
@pytest.mark.mutated("<CLAUSE-ID>")
@pytest.mark.depends_on("<atomic test it builds on>")
def test_<name>(<fixtures>):
    """<existing Seam/CVI sentence, unchanged>

    Mutated: <the mutated requirement>. The upstream package implements
    <the upstream behavior>, so this test fails against it by construction.

    Verifies: <CLAUSE-ID>
    """
```

**Register the metadata where the harness cannot override it.** A config file is
the obvious place and the wrong one: a runner passing marker definitions on the
command line *replaces* the config key rather than adding to it, so a marker
registered only in config vanishes at scoring time while still working locally.
Read the runner, find where it injects its own metadata, and register alongside.
For Python that is the oracle's `conftest.py`, not `pytest.ini`:

```python
# conftest.py
def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "mutated(clause_id): asserts behavior that diverges from the upstream package",
    )
```

### 3b. In `task.json`

The authoritative list the harness reads:

```json
"mutation": {
  "variant_of": "<baseline-task-id>",
  "clauses": ["<CLAUSE-ID>"],
  "tests": ["test_atomic::<name>", "test_integration::<name>"],
  "upstream_expected_failures": <count>
}
```

### 3c. In `mutation/record.md`

The prose record from Step 1, section 1d.

### 3d. Re-verify the variant as a task in its own right

**A mutated variant is a new task, and the pipeline treats it as one.** Every
static gate the baseline passed applies again under the variant's own id, and
`STATIC_VALID` on it is a precondition for Step 4:

```bash
SPEC2REPO_TASKS_DIR=<pool> python3 harness/verify_task.py <task-id>-mut-<n>
```

Two failures are specific to variants — expect them rather than discover them:

- **Metadata drift.** The `mutation` block is additive, but the rest of
  `task.json` still describes the baseline's test set — counts, taxonomy, layer,
  dependency lists. Regenerate every field that enumerates or counts tests.
- **The new id is registered nowhere.** Every registry keyed by task id lacks it,
  and the one mapping a task to its upstream distribution fails *closed*: scoring
  aborts before a single test runs, producing no failures and no error — only an
  absent result, which reads like a candidate that built nothing. Register the
  variant beside its baseline before scoring.

### 3e. Check: the three records agree, and the ids are pairable

A marked-but-undeclared test reads to the harness as an ordinary failure; a
declared-but-unmarked one means the list is stale. Separately, every declared id
must also exist in the *baseline* packet or Step 6 has nothing to compare it
against — a mutation-only id still belongs in the list, but record it as
uncomparable so the reading is not silently computed over a smaller set than it
appears:

```bash
python3 - <<'EOF' <baseline-pool>/<baseline-task-id> <pool>/<task-id>
import ast, json, pathlib, sys
base, mut = (pathlib.Path(p) for p in sys.argv[1:3])

def collect(pkt, pred):
    return {f"{f[:-3]}::{n.name}"
            for f in ("test_atomic.py", "test_integration.py")
            for n in ast.walk(ast.parse((pkt / "oracle" / f).read_text()))
            if isinstance(n, ast.FunctionDef) and pred(n)}

declared = set(json.loads((mut / "task.json").read_text(encoding="utf-8-sig"))
               .get("mutation", {}).get("tests", []))
marked = collect(mut, lambda n: any("mutated" in ast.dump(d) for d in n.decorator_list))
baseline = collect(base, lambda n: n.name.startswith("test_"))

print("marked not declared:", sorted(marked - declared))    # must be empty
print("declared not marked:", sorted(declared - marked))    # must be empty
print("pairable:           ", sorted(declared & baseline))
print("mutation-only:      ", sorted(declared - baseline))  # record as uncomparable
EOF
```

The first two lines must be empty. If everything lands in `mutation-only`, the
mutation renamed its tests — go back and restore the original names.

---

## Step 4 — The reference gate, restated

**This step is where mutation most easily goes wrong.** The constitution requires
that the *reference implementation passes 100% of the oracle*, and a mutated
oracle cannot satisfy that against the upstream package — divergence is the
point. Running the ordinary reference gate here and reading its failure as a
defect inverts the result: it rejects exactly the mutations that worked. The
mutated packet therefore gets **its own reference** — upstream plus
`mutation/reference_patch.py` — and **two gates with opposite required
outcomes**.

### 4a. Building the patch

**Find the smallest patch that satisfies the clause.** It proves
implementability, not good design, and the obvious edit is often not the
smallest: a mutated exception type may be reachable by widening the existing type
rather than rewriting every raise site; a mutated return value by wrapping one
function rather than editing its callers. Small is easier to check against
`record.md`, and the size is itself evidence of criterion 3.

**The patch must be in force wherever the oracle runs**, which rules out a
one-off script before the test command: the gate runs the oracle in its own
process, so a patch applied only where it was installed changes nothing. Use
whatever mechanism the language offers for "modify the installed package before
user code loads". Two properties follow, both easy to miss:

- **Idempotent** — it may be loaded more than once.
- **Rebinds every name the oracle reaches** — a binding captured at import time
  does not follow a later reassignment of its source, so patching an attribute
  is not enough when the oracle imported that attribute directly.

For a Python packet, a `.pth` file in site-packages is imported before any user
code, in every process:

```python
# reference_patch.py — module-level statements, no main guard
from <upstream> import <target>

if not getattr(<target>, "_s2r_patched", False):
    _original = <target>.<name>

    def _replacement(*args, **kwargs):
        ...  # the mutated behavior, delegating to _original
        return _original(*args, **kwargs)

    <target>.<name> = _replacement
    <target>._s2r_patched = True
```

### 4b. Running the two gates

**They differ only in whether that patch is installed.** Run the oracle in the
packet's image both ways:

```bash
# shared prologue, both gates
docker run --rm \
  -v <pool>/<task-id>/oracle:/oracle:ro \
  -v <pool>/<task-id>/mutation:/mutation:ro \
  spec2repo-base:latest bash -c '
    mkdir -p /run && cp -r /oracle/. /run/ && cd /run
    pip install -q -r requirements.txt <upstream-package> >/dev/null 2>&1

    # M1 ONLY — install the patch; omit these three lines for M2
    SITE=$(python -c "import site; print(site.getsitepackages()[0])")
    cp /mutation/reference_patch.py "$SITE/_s2r_mut.py"
    echo "import _s2r_mut" > "$SITE/_s2r_mut.pth"

    python -m pytest test_atomic.py test_integration.py -q -p no:cacheprovider 2>&1 | tail -20'
```

**Gate M1 (patched) — the mutated reference passes 100%.** The constitutional
gate restated: it proves the mutation is implementable, which is what "reference
passes" always meant. Required **0 failed, 0 error**; a failure means the
mutation is unimplementable, so revise rather than proceed.

**Gate M2 (unpatched) — upstream fails, and only where predicted.** This gate
proves divergence, and it is new. Compare mechanically — a near-miss reads as a
match by eye:

```bash
... | python3 - <pool>/<task-id> <<'EOF'
import json, pathlib, re, sys
d = pathlib.Path(sys.argv[1])
declared = set(json.loads((d / "task.json").read_text(encoding="utf-8-sig"))
               .get("mutation", {}).get("tests", []))
failed = {f"{m.group(1)}::{m.group(2)}"
          for m in re.finditer(r"^FAILED (\S+?)\.py::(\S+)", sys.stdin.read(), re.M)}
print("expected but passed:", sorted(declared - failed))
print("failed unexpectedly:", sorted(failed - declared))
EOF
```

| M2 outcome | Meaning | Action |
|---|---|---|
| Upstream passes everything | No divergence; recall still rewarded | Return to Step 1 |
| Fails exactly the marked tests | Mutation works | Proceed to Step 5 |
| Fails more than marked | Reached further than intended, or broke a shared fixture | Narrow the mutation, or extend the marker list if the extra failures are the same divergence |
| Fails fewer than marked | Some marked tests do not depend on the mutated behavior | Remove those markers — they carry no signal |

**Both logs ship, named so the difference is visible** —
`logs/reference_mutated_*.json` (0 failed, the constitutional gate) and
`logs/upstream_unpatched_*.json` (N failed, the divergence evidence). The second
is not a failure record but the proof that recall no longer helps; never let it
stand as the packet's reference evidence.

### 4c. The dummy gate still applies

Unchanged in principle — a dummy where every public callable raises must still
pass zero positive tests. But a mutation turning a value assertion into an error
assertion can make a test dummy-passable, so compare against the baseline
packet's count rather than against zero:

```bash
python3 -c "
import json, sys
b = json.load(open(sys.argv[1]))['summary'].get('passed') or 0
m = json.load(open(sys.argv[2]))['summary'].get('passed') or 0
print(f'baseline {b} -> mutated {m}', 'OK' if m <= b else 'REGRESSION')
" logs/dummy_py311.json logs/dummy_mutated_py311.json
```

A rise means the mutation weakened an assertion. Strengthen it: assert the new
value, not merely that the old one no longer holds.

---

## Step 5 — Score both packets

### 5a. The paired run

Same model, same settings, same harness revision. Only the packet differs.

```bash
harness/evaluate.py --model <model> --tasks <task-id> \
  --tasks-dir <baseline-pool>  --oracle-dir <baseline-oracle>  --output-dir <out>/base
harness/evaluate.py --model <model> --tasks <task-id> \
  --tasks-dir <mutated-pool>   --oracle-dir <mutated-oracle>   --output-dir <out>/mut
```

Never compare a mutated run against a score from an earlier session. Harness
changes, package upgrades, and gateway settings all move scores; only a paired
run isolates the mutation.

### 5b. Establish the noise floor first

One run per side cannot distinguish a mutation effect from ordinary run-to-run
variation: the same model given the same packet twice writes different code, so
individual tests flip for reasons unrelated to the mutation. Run each side at
least three times and check the mutated tests' outcomes *within* each side —
using the Step 6a reader, pointed at one side's repeats — before comparing
across sides.

A test whose outcome is not stable across repeats of the *same* packet carries
no signal: the model is not reliably doing either thing, so its movement between
packets says nothing. Report those as unstable and exclude them from the Step 6
reading rather than counting them.

---

## Step 6 — Read the result

### 6a. What to measure

**Measure on the mutated tests, not on the total.** A mutation touches a handful
of tests, so its effect on the total is bounded by that fraction — commonly under
five percentage points. A threshold against the total is unreachable by
construction and reports "no effect" however the model behaved.

The signal is the pass rate over the stable `mutation.tests` alone —
`recall_rate` from the baseline runs, `spec_rate` from the mutated ones. Those
tests assert the upstream behavior in the baseline packet and the mutated
behavior in the mutated one; the same model faces both.

One reader serves both steps: pass one side's repeats to see stability, or the
two sides to read the pair.

```bash
python3 - <<'EOF' <pool>/<task-id> <run-dir>...
import json, pathlib, sys
d, *runs = sys.argv[1:]
ids = json.loads((pathlib.Path(d) / "task.json")
                 .read_text(encoding="utf-8-sig"))["mutation"]["tests"]
for r in runs:
    p = pathlib.Path(r)
    t = json.loads(next(p.rglob("result.json")).read_text())["score"]["tests"]
    hit = [t.get(i) for i in ids]                    # None = absent, not failed
    print(f"{p.name:12s} {sum(h == 'passed' for h in hit)}/{len(ids)}",
          [h or "ABSENT" for h in hit])
EOF
```

An `ABSENT` is not a failure — it means the id is missing from that run, so the
pair is not comparable until Step 3e's pairability check is satisfied.

### 6b. The four quadrants

| baseline | mutated | Reading |
|---|---|---|
| high | low | The model reproduced the upstream behavior and did not follow the mutated clause. Its baseline score on this behavior was recall. |
| low | high | The model followed the spec. The mutated clause was implemented; the upstream one was not assumed. |
| high | high | Both forms satisfied. Either the model read the spec both times, or the mutation was too weak to force a choice. **Distinguish by reading the delivery** — see 6c. |
| low | low | The model implemented neither. The behavior is beyond it, and this mutation says nothing about recall. |

Only the first row is evidence of memorisation, and only the second is evidence
of spec-following. The other two mean the mutation did not discriminate on this
model — report that plainly rather than forcing a verdict.

### 6c. Resolving "high / high" — read the code, not the score

The two explanations are identical in the numbers and distinguishable in the
delivery. Open the mutated run's workspace:

- **The candidate wrote something the upstream package does not contain** — a
  helper, a resolution step, a branch with no upstream counterpart. It could not
  have recalled what does not exist, so it read the clause. The mutation worked;
  the model is spec-driven on this behavior.
- **The implementation is recognisably the upstream one and the mutated
  assertion happens to hold anyway** — the mutation did not force a choice.
  Return to criterion 5.

Record which you observed, with the workspace evidence. Reliance on recall varies
by model, so "high / high" is the *expected* outcome for one that does not lean
on memory — and a model that never shows the first row is a finding about that
model, not a broken method. Before blaming the mutation, check whether it
discriminates on a model known to rely on recall; if it does, the method is
sound.

### 6d. Reporting constraints

**Do not convert this into a threshold.** With a handful of tests, a rate is a
small-sample proportion — three of four is not meaningfully different from two of
four. Report the counts.

**Condition-set caveat.** A mutated atomic test that most candidates now fail
shrinks the conditional set for every integration test depending on it, widening
`adjusted_gap` for reasons unrelated to composition ability. Report the
condition-set size alongside any gap from a mutated packet; below roughly ten,
the gap carries little weight.

**What the result does not say:**

- **Not that the spec is complete.** It shows recall was not used *for the
  mutated behavior*; other clauses may still be underspecified, which is what
  `harness/oracle_import_lint.py` and the shared-helper audit cover.
- **Not that the model is deficient.** A recall result condemns the
  *measurement* — the baseline was reading recall here. The model may be fully
  capable of spec-following elsewhere.
- **Not anything about the task as a whole.** One mutation covers one behavior;
  a task spanning many domains needs several variants, and even then the
  statement is "on these behaviors, this model relied on recall" — not a number.

---

## Release Rules

- Where the paired result shows recall (baseline high, mutated low), the task's
  published score is the **mutated** score. Record the baseline beside it — the
  difference is itself the finding, not something to discard.
- Where the result does not discriminate (both high, or both low), publish the
  baseline and record that the mutation was uninformative on this model. Do not
  present an uninformative mutation as evidence of spec-following.
- Mutated variants ship as separate task ids (`<task-id>-mut-<NNN>`), never as
  silent replacements. The baseline packet stays reproducible.
- A mutated packet ships only with: `mutation/record.md`,
  `mutation/reference_patch.py`, both reference logs, the `mutation` block in
  `task.json`, and markers on every diverging test.
