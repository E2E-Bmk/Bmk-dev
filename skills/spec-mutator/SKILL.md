---
name: spec-mutator
description: "Mutate a task's spec and oracle together so the described system diverges from its upstream namesake. Validates the mutation with paired reference gates (patched = 100%, unpatched = fails exactly the marked tests). Use after a task passes the reference gate and before it enters the release set."
---

# Spec Mutator

## State Machine Interface

**Entry:** Read `wip/{language}/{task}/PIPELINE_STATE.md`; `state` must be `S5_MUTATE`.
Preconditions (both required):

1. `harness/core/verify_task.py <task-id>` prints `STATIC_VALID`
2. Baseline reference gate passes — upstream package installed, 100% of the
   oracle passing

If either fails, set `state → S2_SPEC_DRAFT` and escalate.

**Exit (accepted):** `mutation/record.md`, `mutation/reference_patch.py`, both
gate logs exist, and `harness/core/verify_task.py <variant-id>` prints `STATIC_VALID`.
Set `state → S5_MUTATE_DONE`, append History row.

**Exit (loop):** Gate M2 shows no divergence — set `state → S5_MUTATE`, increment
`mutate_iter`, choose a different target. Above `mutate_iter > 3`, stop and
escalate.

---

## Purpose

A score against a task built from a real library is ambiguous: the model may have
implemented the spec, or recalled the library. Mutation resolves this by changing
one behavior in the spec and oracle together so the described system diverges
from the upstream. An implementation from the spec is unaffected; one from recall
fails on the mutated tests.

One mutation per task. The output is a paired measurement over the mutated tests,
not a change in the total score.

---

## Step 1 — Select the mutation target

### 1a. Five criteria (all required)

| # | Criterion | Check |
|---|---|---|
| 1 | **Spec-stated** | The behavior appears in the spec with a traceable clause or section reference. Mutating undeclared behavior tests nothing. |
| 2 | **Multi-test** | At least 2 tests whose pass/fail flips under the mutation. Count by reading test bodies — a `grep` hit is not a flip. |
| 3 | **Independently implementable** | A candidate satisfies the mutated form without restructuring the rest of the package. |
| 4 | **Divergent from upstream** | Establish by *running code* against the installed package. Not by inference, docs, or naming. |
| 5 | **Unguessable in the mutated direction** | A competent engineer's default guess must be the upstream form. Mutate *toward* the surprising form. |

### 1b. Direction rule

Mutate *away from* the intuitive answer, not toward it. If the upstream behavior
is already counter-intuitive, it is a bad target — mutating it into the natural
form hands the answer to everyone.

The ideal target: upstream does what everyone would guess, and the mutation
requires something only the spec discloses.

### 1c. Mutation kinds (by signal strength)

| Kind | Shape |
|---|---|
| Changed return shape | container type, arity, ordering |
| Inverted default | a sentinel value's meaning reversed |
| Renamed public argument | keyword takes a different name |
| Different exception type | failure raises a different public exception |
| Reordered composition | pipeline passes result at a different position |

### 1d. Disqualifications

- Behavior requires changes inside a third-party dependency (unimplementable).
- The behavior is also an *input* to the oracle (mutation propagates beyond
  the clause, failing the M2 containment check).
- Only 1 test flips (indistinguishable from run-to-run noise).
- The mutated form is what an engineer would guess anyway (criterion 5 fails).

### 1e. Record

Write `mutation/record.md` before editing anything:

```
target clause:   <spec section + line or clause ID>
upstream form:   <what the package does — verified by running code>
mutated form:    <what the spec will now require>
oracle tests:    <every test whose outcome flips>
implementable:   <why a candidate can satisfy the mutated form independently>
divergent:       <evidence from running the upstream package>
unguessable:     <why the upstream form is what everyone would guess>
```

---

## Step 2 — Edit spec and oracle together

Both must change in one step. A mutation in only one is a defect:
- Spec only → oracle contradicts spec → candidates fail unfairly
- Oracle only → spec no longer describes scored behavior → fairness violation

### 2a. Spec side

Rewrite the clause in place. Do not add or remove clauses (positional IDs shift).
The rewritten sentence must read as ordinary library documentation — never hint
that a mutation occurred.

### 2b. Oracle side

Change only assertion values in the affected tests. Keep test names unchanged
(Step 6 pairs runs by test id). Keep setup code unchanged. The diff between
baseline and mutated oracle should contain only assertion lines.

### 2c. Containment check

Verify no unintended tests changed:

```bash
python3 <<'EOF' <baseline> <mutated>
import ast, sys
def funcs(path):
    return {n.name: ast.dump(n) for n in ast.walk(ast.parse(open(path).read()))
            if isinstance(n, ast.FunctionDef)}
a, b = funcs(sys.argv[1]), funcs(sys.argv[2])
print("changed:", sorted(k for k in a.keys() & b.keys() if a[k] != b[k]))
EOF
```

The printed list must equal the test list in `record.md`. Any extra name means
the edit leaked.

---

## Step 3 — Classify mutated tests

Three records must agree. All three serve different consumers.

### 3a. In the test (machine + human readable)

```python
@pytest.mark.mutated("<clause-ref>")
def test_<name>(...):
    """<existing docstring>

    Mutated: <the mutated requirement>. The upstream package implements
    <the upstream behavior>, so this test fails against it by construction.

    Verifies: <clause-ref>
    """
```

Register the marker in `conftest.py` (not `pytest.ini` — config-only markers
vanish when the scorer passes its own `-p` flags):

```python
def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "mutated(clause_id): asserts behavior that diverges from the upstream package",
    )
```

### 3b. In task.json

```json
"mutation": {
  "variant_of": "<baseline-task-id>",
  "clauses": ["<clause-ref>"],
  "tests": ["test_atomic::<name>", "test_integration::<name>"],
  "upstream_expected_failures": <count of parametrized cases that flip>
}
```

### 3c. In record.md

Already written in Step 1e.

### 3d. Consistency check

```bash
python3 <<'EOF' <task-dir>
import ast, json, pathlib, sys
d = pathlib.Path(sys.argv[1])
declared = set(json.loads((d/"task.json").read_text(encoding="utf-8-sig"))
               .get("mutation",{}).get("tests",[]))
marked = {f"{f.stem}::{n.name}"
          for f in (d/"oracle").glob("test_*.py")
          for n in ast.walk(ast.parse(f.read_text()))
          if isinstance(n, ast.FunctionDef)
          and any("mutated" in ast.dump(dec) for dec in n.decorator_list)}
print("marked not declared:", sorted(marked - declared))
print("declared not marked:", sorted(declared - marked))
EOF
```

Both lines must be empty.

---

## Step 4 — Paired reference gates

### 4a. Build the reference patch

The patch must make the upstream package behave as the mutated spec describes.
For Python, use a `.pth` file in site-packages (loads before any user code):

```python
# mutation/reference_patch.py
def _apply():
    import <upstream_module> as _mod
    if getattr(_mod, "_s2r_patched", False):
        return
    # ... minimal mutation ...
    _mod._s2r_patched = True
_apply()
```

Install it:
```bash
SITE=$(python -c "import site; print(site.getsitepackages()[0])")
cp mutation/reference_patch.py "$SITE/_s2r_mut.py"
echo "import _s2r_mut" > "$SITE/_s2r_mut.pth"
```

**Note:** if the package is installed in a different site-packages directory than
`getsitepackages()[0]`, the `.pth` fires but the import fails silently. Verify
by checking `python -c "import <pkg>; print(<pkg>.__file__)"` points to the
expected location.

### 4b. Gate M1 — patched reference passes 100%

Run the full oracle with the patch installed. Required: 0 failed, 0 error.
A failure means the mutation is unimplementable — revise.

### 4c. Gate M2 — unpatched upstream fails exactly where predicted

Remove the patch and run again. Compare:

| Outcome | Meaning | Action |
|---|---|---|
| Passes everything | No divergence | Return to Step 1 |
| Fails exactly the marked tests | Mutation works | Proceed |
| Fails more than marked | Blast radius too wide | Narrow or extend markers |
| Fails fewer than marked | Some markers are wrong | Remove those markers |

### 4d. Clean up

Remove the `.pth` and patch files after verification to avoid polluting other
task runs.

---

## Step 5 — Score both packets

Same model, same settings, same harness. Only the packet (baseline vs mutated)
differs. Never compare against a score from an earlier session.

Run each side at least 3 times to establish per-test stability within each side
before comparing across sides. A test unstable within one side carries no signal
and is excluded from Step 6.

---

## Step 6 — Read the result

### 6a. Measure on mutated tests only

The total score barely moves (a handful of tests in a 60-100 test oracle).
Measure the pass rate over `mutation.tests` alone:
- `recall_rate`: pass rate on baseline packet
- `spec_rate`: pass rate on mutated packet

### 6b. Four quadrants

| baseline | mutated | Reading |
|---|---|---|
| high | low | Recall — model reproduced upstream, did not follow mutated clause |
| low | high | Spec-following — model implemented the mutated clause |
| high | high | Indeterminate — read the delivery code to distinguish |
| low | low | Beyond capability — mutation says nothing about recall |

Report counts, not percentages. With 3-5 tests, rates are small-sample
proportions.

### 6c. What the result does not say

- Not that the spec is complete (only one clause was tested).
- Not that the model is deficient (a recall result condemns the *measurement*
  on that behavior, not the model's general ability).
- Not anything about the task as a whole.

---

## Artifacts produced

```
tasks/<language>/<task-id>/
├── mutation/
│   ├── record.md              # Step 1e
│   └── reference_patch.py     # Step 4a
├── spec.md                    # edited in place (Step 2a)
├── oracle/
│   ├── conftest.py            # marker registration (Step 3a)
│   ├── test_atomic.py         # markers + assertion edits
│   └── test_integration.py    # markers + assertion edits
└── task.json                  # mutation block added (Step 3b)
```
