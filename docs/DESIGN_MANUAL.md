# Benchmark Design Manual

Version: 2026-06-28 full-reproduction revision
Scope: Unit/system-gap task selection, structural audit, task construction, candidate runs, and fairness judging.

This manual is the operating contract for the benchmark loop. It replaces the earlier "build first, judge later" workflow with a gate-driven pipeline. The main lesson from the 2026-06-28 iteration is that raw unit-system gaps are cheap to manufacture and easy to misread. Only residual compositional gaps count.

The later 2026-06-28 scale audit adds a stronger lesson: reducing a 20k-300k LOC upstream project to a 100-1,000 LOC "mini" implementation destroys the benchmark surface. New strict tasks must be full bounded product/subsystem reproductions with product-grade docs, multi-file implementation requirements, and a scoring suite sized to the system.

## Core Thesis

The benchmark measures whether coding agents can reconstruct a bounded but complete software subsystem and keep several public views of one evolving product state coherent.

The target signal is:

```text
unit score high, system score lower, residual compositional gap >= 15pp
```

Residual means the gap remains after removing primitive failures, cascade failures, evaluator defects, provider/scaffold failures, exact-format traps, and contaminated artifacts.

Do not accept raw `unit - system` as evidence by itself. Do not accept any new one-file or toy "mini" task as strict benchmark evidence, even if it shows a numeric gap.

## Key Definitions

### Shared Fact Source

The state or record from which all product views are derived. Strong sources are durable, historical, or lifecycle-sensitive. Weak sources are tiny dicts, token trees, config trees, or one-shot graphs unless the public product adds visible history, replay, rollback, tombstones, cache invalidation, or multi-consumer lifecycle.

### Public Projection

A candidate-owned observable view of the shared fact source. Examples: primary query output, reverse index, diagnostics, export/import bytes, lockfile, stats report, recovery log, rendered output, dependency graph, cache state, or explanation API.

### Agreement Surface

A cross-view consistency surface where locally reasonable implementation choices can diverge unless constrained by a public global invariant.

This is not permission to under-specify behavior. A fair agreement surface has:

- local freedom in isolated unit behavior;
- a public product invariant that removes the ambiguity at system level;
- no hidden oracle preference among equally valid public interpretations.

### Forced Surface

A surface where public specs or widely known standards uniquely determine the result. PEP 440/503-style normalization is a typical forced surface unless the task adds a materially new public lifecycle around it.

### Collapse

The intended agreement surface disappears because the obvious implementation routes every public projection through one helper or one small model. This is good engineering, but weak benchmark design unless the public lifecycle can still make views drift.

### Primitive-Capped Evidence

System rows fail because prerequisite local primitives failed first. Primitive-capped raw gaps are not accepted gap evidence.

### Known-Pattern Saturation

The task is so close to a famous library or standard pattern that strong agents may reproduce the design by prior exposure rather than by fresh compositional reasoning. Treat this as a task-risk label. Do not claim data contamination unless there is concrete evidence.

## Layer 0: One-Time Structural Audit

Every candidate must pass this audit before task construction or another redesign cycle. This layer does not loop. It decides whether the task is worth building, needs material rescope, or should be retired.

Record the result in `STRUCTURAL_AUDIT.csv`.

### Required Checks

1. Architecture integrity
   - Does the task expose at least two logical components?
   - Do they share more than a tiny dict/tree?
   - Are there at least three public projections that can drift?

2. Scale integrity
   - Does the task require an installable package or service, not a single module?
   - Does the reference naturally require at least 10 source files and roughly 2,000+ non-test LOC?
   - Does the public packet require at least one CLI or service boundary and one importable API boundary?
   - If a capable agent can pass with a compact one-file rewrite, mark `UNDER_SCOPED`.

3. Agreement-surface freedom
   - What local choices can be correct in unit isolation?
   - Which public system invariant forces them to agree?
   - If every choice is forced by a public standard, mark `FORCED`.

4. Known-pattern risk
   - Is the task a near-clone of Redis, Jinja2, PEP 440 packaging, CommonMark, Dynaconf, or another heavily represented implementation?
   - If yes, either add a product-natural variant outside that known pattern or mark `KNOWN_PATTERN`.

5. Feature-pure unit scan
   - Unit setup may use only the feature under test, direct constructor input, or explicit mocks.
   - If a unit row uses another public feature to build state, move it to system or replace setup with direct state construction.

6. Unit semantic scan
   - Unit tests should check public semantic behavior, not private display details.
   - Exact text, exact exception classes, exact normalized strings, and internal serialization are allowed only when the PRD makes them public API.

7. Obvious-model test
   - Can a competent agent implement one obvious store/tree/graph/helper and naturally pass all system rows?
   - If yes, reject, retire, or materially expand lifecycle.

8. One-shot recomputation test
   - Can every system view be recomputed in one straightforward pass from current inputs?
   - If yes, require public history, replay, rollback, tombstones, cache invalidation, or state reuse before building.

### Layer-0 Verdicts

Use exactly one primary verdict:

```text
BUILD
REPAIR_PRIMITIVES
RESCOPE
RETIRE_SOLVED
STRUCTURAL_DEAD
FORCED
KNOWN_PATTERN
COLLAPSE
UNDER_SCOPED
EXCLUDED
```

Recommended meanings:

- `BUILD`: Strong opportunity; proceed to Layer 1.
- `REPAIR_PRIMITIVES`: Product shape is promising but current evidence is primitive-capped.
- `RESCOPE`: Current surface is too compact; build a materially larger public lifecycle.
- `RETIRE_SOLVED`: Scoreable capable agents semantically solve current public surface.
- `STRUCTURAL_DEAD`: No plausible public agreement surface at this task scale.
- `FORCED`: Public standard/spec uniquely determines the surface.
- `KNOWN_PATTERN`: Too close to a famous library/pattern; needs a variant or replacement.
- `COLLAPSE`: Obvious helper/model makes system rows automatic.
- `UNDER_SCOPED`: Upstream is large but the extracted task is too small, too few files, or testable by a compact rewrite.
- `EXCLUDED`: Not enough public product surface or reliable oracle.

## Layer 1: Skill-Driven Task Construction

Only tasks with `BUILD`, `REPAIR_PRIMITIVES`, or `RESCOPE` may enter this layer.

Before editing PRD/rubric, write an enrichment brief:

```text
agreement_surface:
local_free_choices:
global_public_invariant:
shared_fact_source:
public_projections:
lifecycle_sequence:
why_unit_not_enough:
oracle_semantics:
fairness_risks:
stop_condition:
```

If this brief cannot be written from public product semantics, do not build the task.

### PRD Rules

- Specify user-visible behavior, not internal architecture.
- Avoid telling agents to use a canonical store/tree/helper.
- State consistency, lifecycle, rollback, replay, and projection semantics as public behavior.
- Include no hidden fixture names or sample test shapes.
- Include non-goals to avoid unbounded real-library scope.
- Include state model, durable artifacts, CLI/API schemas, error semantics, ordering/determinism rules, lifecycle examples, and recovery behavior.
- The public packet must be long enough to support a real implementation. Prompt-sized PRDs are rejected for strict tasks.

### Unit-Test Rules

Unit rows must be feature-pure and atomic.

Each feature should have:

```text
basic happy path
edge case
error case
```

Unit rows should establish primitive readiness without repeating exact implementation details across many tests.

### System-Test Rules

Every system row must include one sentence naming the cross-feature contract.

Prefer:

- metamorphic checks;
- operation-sequence checks;
- export/import round trips;
- failed-update rollback;
- cache/index invalidation;
- forward/reverse projection consistency;
- ordering and replay invariants.

Avoid:

- final-result-only checks;
- hidden private shapes;
- exact text traps;
- arbitrary ordering;
- repeating one primitive defect across many system rows;
- evaluator-only projections the candidate does not own.

### Test Scale Rules

The scoring suite must match a full-reproduction task:

- at least 50 executable checks before first strict candidate run;
- preferably 80+ checks once the task is stabilized;
- unit tests cover primitives across modules without cross-feature setup;
- integration tests cross API/CLI/persistence boundaries;
- system tests cover multi-step workflows, materialized outputs, rollback, replay, cache/index invalidation, and reverse projections;
- hidden scoring imports only public APIs or calls public CLIs/services.

## Layer 2: Gap Analysis And Judge

Run only after reference passes 100/100.

### Candidate Matrix

Minimum formal matrix:

```text
reference implementation
Codex subagent public-packet run
OpenHands DeepSeek public-packet run
```

Weak controls such as Qwen are optional calibration only. They must use the same agent scaffold. Provider failure, no-artifact runs, and launch failures are infrastructure evidence, not model scores.

### Branch A: No Gap Or Near-Solved

If unit and system are both high, or system >= unit:

1. Check cascade: is unit below 80%?
2. Check forced surface: are decisions fully determined by spec/standard?
3. Check collapse: did one helper or one obvious model make all views agree?
4. Check known-pattern saturation.
5. If no material public lifecycle remains, mark solved/retired for the current population.

Do not add adjacent hidden rows to separate a near-reference implementation.

### Branch B: Gap Exists

If raw `unit > system`:

1. Cluster all failures.
2. Remove primitive/cascade roots.
3. Remove evaluator/spec defects.
4. Remove provider/no-artifact rows.
5. Remove exact-format or feature-pure violations.
6. Compute residual compositional gap.
7. Require independent judge acceptance.

A task enters core only if:

```text
residual gap >= 15pp
reference = 100/100
gap is reproduced by at least two scoreable agent artifacts, or one strong fresh artifact plus a judge-approved explanation
no feature-pure violation
no under-specified oracle choice
trace/provenance is clean
```

## Exit Conditions

Stop iterating a task when any condition holds:

- `CORE`: legal residual gap >= 15pp with clean provenance.
- `SOLVED`: capable agents are semantically equivalent and no non-distorted public lifecycle remains at this scope.
- `STRUCTURAL_DEAD`: no agreement surface after Layer-0 audit.
- `UNDER_SCOPED`: source project is substantial but extracted task remains mini/toy scale.
- `MAX_ITERATION`: three construction/redesign cycles without accepted residual gap.
- `PROVIDER_BLOCKED`: weak-control provider repeatedly fails before action selection; preserve traces and exclude from scoring.

## Current Task Routing Snapshot

As of 2026-06-28, no legacy raw-gap row should be accepted without the current residual-gap judge. The original SQLite, ZK, and MiniURLUtils rows remain repair candidates under retroactive judge status, not automatically accepted core evidence.

Current candidate routing:

| Task | Routing | Reason |
|---|---|---|
| MiniBitcask | `RETIRE_SOLVED` | Current public CLI surface solved by Codex and OpenHands; no fair remaining invariant at this scale. |
| MiniKV | `STRUCTURAL_DEAD` / provenance-retire | Single-store current surface; system solved while unit misses primitives. |
| MiniRedis | `STRUCTURAL_DEAD` / retire current scope | Single-store current surface plus feature-pure unit violations. |
| MiniTemplate | `KNOWN_PATTERN` / rescope only | Jinja2-style lifecycle solved; useful only with materially different public lifecycle. |
| MiniDynaconf | `REPAIR_PRIMITIVES` then `RESCOPE` | Current evidence primitive-capped or system-solved; needs multi-environment/tombstone/replay lifecycle to continue. |
| MiniPackaging | `FORCED` for PEP surface; `RESCOPE` only | PEP surface is forced; only custom repository/index/lock lifecycle is promising. |
| MiniMarkdown | `COLLAPSE` / near-solved | Workspace-v4 below gate; do not ban helpers, require materialized public lifecycle if continuing. |
| Xitkit | `EXCLUDED` | No clear public agreement surface. |

## Current Direction: Python Native-Test Benchmark (v3)

As of 2026-06-28, the benchmark pivots from hand-authored PRD+rubric tasks to a
native-test pipeline. The source of ground truth is the original repository's
own test suite, not an evaluator-owned rubric.

### Task Format

1. Select a real Python library from `repo-pool/`.
2. Write a public spec from the library's official documentation only (no reference code).
3. Candidate receives spec only; implements from scratch in a cleanroom.
4. Score = fraction of filtered original tests that pass against the candidate implementation.

### Candidate Selection Criteria

- Pure Python; no external service dependencies (no DB server, no network).
- src LOC 3,000–8,000 (sweet spot for discrimination).
- Original test suite ≥ 30 hermetic test functions.
- Multi-module architecture with visible cross-module state invariants.
- Spec writeable entirely from official documentation.

### Current Priority Queue

| Rank | Repo | src LOC | Tests | Notes |
|---|---|---|---|---|
| 1 | `cookiecutter/cookiecutter` | ~2,100 | 242 | Pipeline: find→config→prompt→generate→hooks |
| 2 | `simonw/sqlite-utils` | ~7,300 | 501 | Best test density; v1 calibration baseline available |
| 3 | `pallets/jinja` | ~11,000 | ~500 (dense files) | Compiler pipeline; may be too large |

Walk the queue in order: establish full pipeline (spec → filter tests → Docker → score) on cookiecutter before moving to the next.

## Required Artifacts

For each iteration, preserve:

- `DESIGN_MANUAL.md` updates when methodology changes;
- `STRUCTURAL_AUDIT.csv` rows for every candidate;
- `MANIFEST.json` as the machine-readable source of task status;
- `CANDIDATES.md` as the human-readable registry;
- task-level `prd.md`, `rubric.json`, and `doc/requirement_map.md`;
- reference and candidate score reports;
- OpenHands/Codex trace paths;
- judge verdicts with raw and residual gap separated.
