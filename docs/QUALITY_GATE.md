# Spec2Repo Task Quality Gate

All tasks in the benchmark MUST pass every gate below before merge.
`harness/core/validate_ledger.py` enforces the machine-checkable subset;
human-review items are marked *(review)*.

---

## Java Maven branch (authoritative override)

For a task whose `task.json.language` is `java`, the semantic gates below are
unchanged, but these Java artifacts and commands replace Python-only paths and
commands elsewhere in this document.

**Required oracle files:**

```text
tasks/{language}/{id}/oracle/pom.xml
tasks/{language}/{id}/oracle/requirements.txt
tasks/{language}/{id}/oracle/src/test/java/atomic/*.java
tasks/{language}/{id}/oracle/src/test/java/integration/*.java
tasks/{language}/{id}/oracle/src/test/java/support/*.java    # optional
```

Java dependencies and plugins are declared in `oracle/pom.xml`;
`requirements.txt` remains a required packet marker. The target dependency
must use `${candidate.version}`. Counts and taxonomy are derived by
`JavaRunner`, using `atomic::Class::method` and
`integration::Class::method` base-function IDs. The same layer floors apply to
those directories. Java collection safety requires a successful Maven
`test-compile` against the pinned reference and a non-zero, stable
`JavaRunner.discover()` denominator. Relative fixtures and resources referenced
by Java tests must exist under the oracle tree.

Integration dependency coverage is declared in the nearest method Javadoc as
`Depends-On: atomicMethodA, atomicMethodB`. Assertion composition and private
surface checks remain review gates for Java where the Python AST checks do not
apply.

**Reference validation:** first produce a fresh lint result on disk:

```bash
python harness/core/oracle_import_lint.py <task_id> tasks/<language>/<task_id>/spec.md \
  > wip/<language>/<task>/filter/lint_result.txt 2>&1
```

Its first line must be `LINT_PASS` and it must be newer than every selected
oracle `.java` source. Then run the pinned reference through the Java scorer:

```bash
python harness/lang/java/score_java.py \
  --task-dir wip/<language>/<task_id>/ \
  --oracle-dir <assembled-oracle-dir>/ \
  --taxonomy wip/<language>/<task_id>/filter/taxonomy.jsonl \
  --maven-coordinate <groupId>:<artifactId> \
  --solution-dir repo/<reference-checkout>/ \
  --run-dir wip/<language>/<task_id>/filter/reference-run/ \
  --json-out wip/<language>/<task_id>/filter/reference_score.json \
  --reference
```

The reference gate requires `valid == true`, provenance status `passed`, equal
non-empty candidate/resolved JAR SHA-256 values, and 100% of the complete
oracle passing. Java dummy discrimination uses the same scorer against a
minimal Maven candidate and must satisfy Gate 6. All score-bearing batches and
provenance probes run in Docker with no network.

---

## Gate 0 — File Completeness

| Required file | Purpose |
|---------------|---------|
| `tasks/{language}/{id}/spec.md` | Behavioral specification given to the model |
| `tasks/{language}/{id}/task.json` | Machine-readable metadata |
| `tasks/{language}/{id}/oracle/test_atomic.py` | Atomic-layer oracle tests |
| `tasks/{language}/{id}/oracle/test_integration.py` | Integration-layer oracle tests |
| `tasks/{language}/{id}/oracle/requirements.txt` | Third-party dependencies for scoring |

All fixture files referenced by tests (e.g. TOML data files, sample configs)
MUST also be present under `tasks/{language}/{id}/oracle/`.

The oracle lives inside the task packet so that each task is self-contained and
there is one copy of every test. The release repo uses a separate top-level
`oracle/{id}/` tree instead, because a leakage-resistant evaluation there swaps
in a private oracle via `--oracle-dir`. Bmk-dev is the construction side and
does not need that, and a second copy on this side drifted from the first
(a comparison of the two found zero identical files).

---

## Gate 1 — Spec Structure

`spec.md` MUST contain these `##`-level sections. The authority for the section
set is the six-layer structure in `docs/SPEC_STANDARD.md`; the aliases
column lists the pre-restructure names that `harness/core/verify_task.py` still
accepts, so a spec written before the SDD rewrite is not reported as broken.
New specs use the current name.

| Section (current) | Accepted aliases (legacy) |
|---------|---------|
| Product Overview | — |
| Non-Goals | Scope |
| Public Interface | Installable Surface, Public Import Surface, Public API |
| State Model | Product State Model, Notebook JSON State Model |
| Error Semantics | Validation And Error Reporting |
| Cross-View Invariants | Cross-Component Invariants |
| Representative Workflows | Representative Workflow |
| Appendix A: Environment | Environment |
| Appendix B: Assessment Notes | Evaluation Notes, Implementation Guidance |

`Invocation Protocol` is no longer a top-level section: CLI behavior belongs
under `Public Interface > CLI Entry Points`.

---

## Gate 2 — Spec Content Rules

### 2a. No information leakage *(automated)*

The spec body (excluding inline code in backticks) MUST NOT contain:
`task_id`, `source_boundary`, `candidate-visible`, `benchmark`, `oracle`,
`judge`, `scoring`.

### 2b. Public API names are contractual *(review)*

Every class name, public attribute name, and public method name that oracle
tests assert on MUST appear in the spec. This is NOT "giving away the answer"
— it is defining the interface contract.

Rule of thumb: if a name appears in the library's official documentation,
it belongs in the spec.

### 2c. No implementation signatures *(review)*

The spec MUST NOT contain:
- Complete constructor parameter lists with types and defaults
- Internal module layout (`_internal.utils`)
- Private attribute or method names (`_cache`, `__slots__`)

**Write behavior, not signatures.** Instead of:

> `Request(method: str, uri: str, body: bytes | None = None, headers: dict | None = None)`

Write:

> A `Request` is constructed from a method string, a URI string, an optional
> body (bytes), and an optional headers mapping.

### 2d. Environment section follows template *(automated)*

The `## Environment` section MUST follow the standardized template listing
all pre-installed packages from `oracle/{id}/requirements.txt`, and MUST
state that the target package is not pre-installed and no network is available.

### 2e. EARS clause discipline *(review)*

New behavioral clauses SHOULD use one of the five EARS templates:

| Template | Pattern |
|----------|---------|
| Ubiquitous | THE \<system\> SHALL \<response\> |
| Event-driven | WHEN \<trigger\> THE \<system\> SHALL \<response\> |
| State-driven | WHILE \<state\> THE \<system\> SHALL \<response\> |
| Unwanted | IF \<condition\> THEN THE \<system\> SHALL \<response\> |
| Optional | WHERE \<feature\> THE \<system\> SHALL \<response\> |

---

## Gate 3 — Oracle Test Rules

### 3a. Layer minimums *(automated)*

| Layer | Minimum test functions |
|-------|-----------------------|
| `test_atomic.py` | ≥ 15 |
| `test_integration.py` | ≥ 15 |
| Total (atomic + integration + system_e2e) | ≥ 50 |

### 3b. Assertion composition *(automated)*

Atomic layer `positive` assertion share ≥ 60%.

- `positive`: asserts a produced value (return value, attribute, output content)
- `failure_path`: asserts an exception is raised or error status
- `shape`: asserts only type/length, not content
- `no_check`: test function with no assertions → FORBIDDEN in atomic

### 3c. No private imports *(review)*

Oracle tests MUST NOT import modules starting with `_` from the target package.

### 3d. No message-text assertions *(review)*

Oracle tests MUST NOT assert on:
- Exception message exact text (`str(e) == "..."`)
- `__repr__` format
- Log message wording

They MAY assert on:
- Exception TYPE (`isinstance(e, ValueError)`)
- Whether a string CONTAINS a key substring (`"timeout" in str(e).lower()`)

### 3e. No unresolvable name assertions *(review)*

Every attribute name, method name, or class name that an oracle test asserts on
MUST be either:
1. Explicitly named in the spec (preferred), OR
2. Deterministically derivable from spec content (e.g. `slug` derivable from
   "the URL slug is the lowercased name")

If neither holds, the test has an **unresolvable name** — fix the spec (add
the name as API contract) or fix the test (assert behavior instead of name).

### 3f. Test collection safety *(automated — to be added)*

Each test file MUST be parseable by `ast.parse()` without errors.

Each test file SHOULD NOT have duplicate top-level imports that shadow each
other. *(Detectable by comparing import sets before and after deduplication.)*

### 3g. Fixture completeness *(automated — to be added)*

Every `Path(__file__).parent / ...` or `open(...)` call in oracle tests that
references a relative file MUST have that file present in `oracle/{id}/`.

### 3h. Integration test depth *(review)*

Integration tests MUST exercise interaction between 2+ components/modules.
A test that only calls one function with different inputs is an atomic test
in the wrong file.

---

## Gate 4 — Metadata Consistency *(automated)*

- `task.json` `instance_id` matches directory name
- `task.json` `stats.atomic + stats.integration + stats.system_e2e == oracle.count`
- `task.json` `taxonomy` keys match physical test function names
- Atomic-file functions have `taxonomy == "atomic"`
- Integration-file functions have `taxonomy ∈ {"integration", "system_e2e"}`
- Task appears in `tasks/metadata.csv`

---

## Gate 5 — Reference Validation *(Docker required)*

The reference implementation (installed from `repo_commit`) MUST pass ALL
oracle tests with 0 failures and 0 errors:

```bash
docker run --rm \
  -v "$ORACLE_DIR:/oracle:ro" \
  spec2repo-base:latest bash -c \
  "pip install -q pytest pytest-timeout <requirements> <reference> && \
   python -m pytest /oracle/ -q --timeout=120"
```

Result: 0 failed, 0 error.

---

## Gate 6 — Dummy Discrimination *(Docker required, spot-check)*

An empty package (only `__init__.py`) MUST NOT pass more than 10% of oracle
tests. If it does, the tests are too weak (asserting existence rather than
behavior).

---

## Enforcement

| Gate | Enforced by | When |
|------|-------------|------|
| 0–4 | `harness/core/validate_ledger.py` | Every PR, CI |
| 2b,2c,2e,3c,3d,3e,3h | Human review | Every PR touching spec/oracle |
| 5 | Docker CI job | Every PR touching oracle |
| 6 | Manual spot-check | New tasks, major oracle changes |

Gates 3f and 3g are marked "to be added" — they should be implemented in
`verify_task.py` to catch fixture-missing and import-shadow bugs automatically.
