---
name: spec-writer
description: "Write a behavioral specification (public packet) for a SWE-E2E reconstruction benchmark task. Use when drafting, iterating, or judging a spec for a candidate Python library before candidate evaluation. The spec describes the public API behavioral contract — what the library promises to callers. Source code may be read freely; the constraint is public intent (exported surface, user-facing docstrings, examples), not documentation coverage."
---

# Spec Writer

## State Machine Interface

**Entry:** Read `wip/{task}/PIPELINE_STATE.md`. Verify `state` is `S2_SPEC_DRAFT` or `S2_SPEC_CHECK`. If `spec_iter > 3`, stop and escalate to orchestrator — do not proceed.

**Exit (all 12 validation checks + style gate pass):** Set `state → S2_SPEC_DONE`, then `→ S3A_IMPORT_AUDIT`, append History row.

**Exit (loop — any check fails):** Set `state → S2_SPEC_DRAFT`, increment `spec_iter`, reset `todo` to S2_SPEC_DRAFT catalogue todo, append History row.

---

## Core Standard

Two questions decide every inclusion decision. Both must be answered:

**Q1 — Does this belong to the public behavioral contract?**
> What the library promises to callers via its intended external interface.
> - Yes → proceed to Q2
> - No → omit

**Q2 — Is this non-derivable?**
> Can a senior engineer infer this from domain knowledge, design judgment, or common practice — without reading the library's source or docs?
> - Yes, derivable → omit (the model can figure it out)
> - No, library-specific → include explicitly

**Q3 — Is this a contract, not a test instance?**
> Three sub-tests, all must hold before adding any sentence to the spec:
> - **Upstream-doc ceiling:** would the library's own documentation (README, API reference, official tutorial) plausibly contain this statement? If no upstream doc would ever write it, it is test scaffolding — route to test-filter (fix the test) instead of the spec.
> - **1:N support:** does the statement support a family of behaviors (multiple present or future tests), or exactly one oracle assertion? A sentence that can only ever justify one test is a checklist item, not a contract.
> - **Rule, not instance:** state the generating rule ("page numbering starts at 1 and `page_range` is a contiguous sequence"), never the instance ("`page_range == [1, 2, 3]`").

Only items that pass all questions belong in the spec. The goal is not exhaustive coverage of all public API details — it is making every non-derivable contract detail explicit so the model is never blocked by a knowledge gap it could not reasonably close on its own.

**Granularity principle:** Spec describes the contract, not the implementation. But all non-derivable contract details must be explicit. A spec that is too sparse causes collection failures; a spec that is too dense becomes a fill-in-the-blanks template rather than a reconstruction target.

**Public API** means: names in `__all__` or `__init__` exports, classes/functions with user-facing docstrings, types used in public examples or workflows. A name without an underscore prefix is not automatically public; the test is whether it is part of the intended external interface.

**Behavioral language** means: what the API promises (inputs, outputs, side effects, error conditions, state invariants) — not how it is implemented internally.

## Clause Discipline (SDD/EARS)

Behavioral statements follow requirements-engineering discipline. This section is normative for all NEW or MODIFIED spec content; existing prose that already uses `must` phrasing is grandfathered (must ≈ SHALL) and is not rewritten wholesale.

**EARS templates.** Every new behavioral clause takes one of five shapes:

| Pattern | Template | Use for |
|---|---|---|
| Ubiquitous | The `<subject>` must `<response>`. | unconditional contracts (signatures, invariants) |
| Event-driven | When `<trigger>`, the `<subject>` must `<response>`. | call/input-driven behavior |
| State-driven | While `<state>`, the `<subject>` must `<response>`. | mode- or lifecycle-dependent behavior |
| Optional feature | Where `<feature/config>` is present, the `<subject>` must `<response>`. | configurable behavior |
| Unwanted behavior | If `<error condition>`, then the `<subject>` must raise/return `<response>`. | failure paths |

These templates force trigger + observable response. They make it structurally impossible to write a test instance ("given fixture X the output is 12") as a spec clause — there is no EARS shape for it.

**Clause IDs.** Each atomic behavioral clause gets a stable ID `<TASK-ABBREV>-<SECTION-ABBREV>-<NNN>` (e.g. `KEDRO-SCAF-003`). IDs live in a sidecar file `tasks/<task-id>/clauses.md` (clause ID → verbatim quoted sentence + section anchor), NOT inline in the candidate-visible body — the candidate never needs them; auditors and test-filter do.

**Traceability.** Every oracle test added or modified after this rule ships must name the clause IDs it verifies in its docstring (`Verifies: KEDRO-SCAF-003, KEDRO-SCAF-004`). Two audits become mechanical:
- test with no supporting clause → leaked implementation detail → fix or delete the test;
- clause with no covering test → coverage gap → candidate for ADD-TEST.

**Layer of abstraction.** Signatures, parameter names, field names, enum members, exception classes are contract vocabulary — include them (any API reference would). Concrete test values, fixture layouts, golden outputs are instances — never include them.

## Dual Audience Principle

**Write as the library author.** Every section of the spec body should read as if you are a developer explaining your own library to someone using it for the first time. A reader must not be able to tell this is a benchmark artifact. If any sentence sounds like it was written for an evaluator rather than a developer, rewrite it.

The spec serves two simultaneous purposes:

**1. Natural API documentation** — The candidate reads the spec as its sole information source. No benchmark metadata, no task IDs, no audit trail in the body. The spec title is just the library name; the content covers what the library does and how to use it.

**2. Evaluation protocol transparency** — The candidate must never fail due to confusion about how evaluation works, only due to a genuine capability gap. The `Implementation Guidance` section explicitly describes test dimensions and scoring approach — without revealing fixture shapes or expected values — so the candidate understands what will be tested and can prepare accordingly.

These two purposes are structurally separate: the spec body is natural library documentation; protocol information is confined to `Implementation Guidance`; audit metadata (task ID, version, delta, source boundary) lives in a stripped internal header never sent to the candidate.

## Source Documentation

Read source code and public documentation together to map the public API surface:

1. Source code: `__init__.py`, `__all__`, public class/function signatures, docstrings
2. PyPI page or GitHub README — product overview and install
3. Official docs site — getting started, API reference, CLI reference, examples/cookbook
4. `--help` output for each CLI subcommand

Record the exact sources consulted in the internal header (`source_boundary`) — not in the candidate-visible body.

**Reading workflow — do not begin writing the spec until these steps are complete:**

1. Read `__init__.py` and `__all__`. Produce a **public API surface list**: every exported name, with file path. This list is your working set. If this list is empty, you have not done the reading — stop.
2. Read docs body (not just headings): scan for `from pkg.module import Name` patterns, NamedTuple class names in return value examples, exception classes users catch or compare.
3. For each item on the surface list, answer Q1 then Q2 **individually**, one item at a time, before moving to the next. Do not batch-decide multiple items.
4. Write spec sections only after the full surface list has been processed.

The candidate agent must not see source code, tests, or score reports. The spec writer must read them.

## Must Include

Items in these categories belong in the spec **only when they pass Q2** — i.e., a senior engineer could not reasonably infer them without reading the library's docs or source. Standard patterns a competent engineer would produce anyway do not need to be stated.

- All public import paths and names: functions, classes, exceptions, namedtuples — including re-exports that appear in the public API surface even when they look like module-level aliases
- Scan docs body (not just headings): `from pkg.module import Name` patterns in code examples, NamedTuple class names in return value reprs, exception classes users are expected to catch or compare
- Function signatures: parameter names, types, defaults — where defaults or parameter names are library-specific and non-obvious
- Documented namespaces, engines, and data models a first-day engineer must know (e.g. Jinja2 syntax and `{{ cookiecutter.name }}` namespace)
- Special user-visible context keys (e.g. `_copy_without_render`, `_extensions`, `__prompts__`) when they appear in official docs
- Error semantics: which trigger condition -> which exception class — when the exception type is library-specific or non-obvious

**Behavioral constraints (engineer might implement inconsistently):**
- Product overview
- Context precedence rules (multi-source merge order)
- **Product State Model** — before writing per-subsystem sections, write a top-level state model that enumerates the three public projections of the library's core state and states at least three cross-view invariants (e.g. "a value written via API A is visible via API B within the same session"). This gives the candidate a unified state machine to implement against, rather than a list of independent behaviors.
- Cross-View Invariants: >=6 items, user-observable language, spanning all public projection pairs. Write each invariant with `must` or `returns` — never `can` or `may`.
- Every behavioral statement uses `must when [condition]` not `can`. If a behavior is conditional, state the condition explicitly.
- Every behavior description includes its failure path: what the system `must raise` or `must return` when the precondition is violated.
- >=1 complete end-to-end workflow example
- Implementation Guidance: what test dimensions exist, no fixture shapes

## Must Not Include

- Internal module/file organization (engineer decides this)
- Algorithm step sequences ("Step 1: load JSON, Step 2: iterate keys")
- Framework choices ("use Click for CLI")
- Dependency version constraints
- Names of internal helpers absent from the public export surface — presence in test imports alone is not sufficient; check `__all__`, `__init__` exports, and user-facing examples/docstrings
- Private names (`_name`, `__name`) and names absent from the public export surface
- Internal implementation details of public classes (field names, internal maps, singleton structure) that are not part of the API contract
- Escape-hatch language: `Most`, `generally`, `typically`, `in most cases`, `usually` when describing API support scope — these allow a candidate to skip a behavior and still satisfy the spec wording. State the exact scope of support explicitly.

## Required Structure

Every spec file has two parts. Only the body is sent to the candidate.

**Internal header** (stripped before sending to candidate):

```
<!-- INTERNAL
task_id: {task-id}
spec_version: v{N}
delta: {what was added/removed from previous version and why}
source_boundary: {list of sources consulted: docs pages, source files}
-->
```

**Candidate-visible body** — reads like natural API documentation:

```
# {Library} Specification

## Product Overview
## Scope                        <- positive list: which feature areas ARE covered
## Installable Surface          <- import paths, CLI entry point
## Public API                   <- signatures, parameter semantics, data objects
## Behavioral Sections          <- per-domain state/operation contracts
## Error Semantics              <- exception class -> trigger condition
## Cross-View Invariants        <- >=6 items, user-observable language
## Representative Workflow(s)   <- >=1 end-to-end example
## Non-Goals                    <- explicit exclusions
## Invocation Protocol          <- console script name; whether `python -m <pkg>` is supported (write "supported" or "not supported"); exit code table
## Environment                  <- runtime dependency declaration policy
## Implementation Guidance       <- test dimensions and scoring approach; no fixture shapes or expected values
```

**Environment section (required in all specs):**
Every spec must include near the end an Environment section that lists the **exact third-party packages preinstalled in the working environment** (generated from the task's oracle `requirements.txt`, minus the target package itself), plus the dependency-declaration policy:

```
## Environment

The working environment has Python 3.11 with the following packages preinstalled
and importable: {explicit package list}. The same packages are available at
assessment time. Additional runtime dependencies must be declared in a standard
`requirements.txt` or `pyproject.toml` at the project root; declared dependencies
are installed before assessment.
```

Never write "may use any third-party packages available on PyPI" — an open-ended promise the working environment cannot honor turns dependency choice into a gamble. The preinstalled list is the single source of truth shared by the agent container, the scoring container, and the spec.

The body must read as if written by a library author, not a benchmark designer. `Implementation Guidance` is the only section that describes the evaluation setup — it tells the candidate what dimensions are tested and how scoring works, so failures reflect capability gaps, not protocol confusion.

## Linkage with Test-Filter

Spec and test-filter are linked: spec describes what must be implemented; test-filter removes tests that check evaluation artifacts rather than model capability. Do not add defensive spec content to compensate for tests that should be filtered out — route those to test-filter instead.

## Validation

 (run after each draft, before candidate evaluation)

1. Is each feature traceable to public docs and "day-one required knowledge", not "experienced engineer's design choice"<-
2. Do any internal class names or undocumented module paths appear<-
3. Are invariants written in behavioral language, not code<-
4. Are Non-goals explicitly listed<-
5. Does any section implicitly assume a hidden fixture shape<-
6. Does every behavioral statement use `must` / `returns` / `raises` — not `can` / `may`<-
7. Does every conditional behavior state its condition explicitly (`must when [X]`, not `when applicable`)<-
8. Does every behavior description include its failure path (what `must raise` or `must return` on violation)<-
9. Is there a Product State Model section (or equivalent) before the per-subsystem sections, with >=3 cross-view invariants stated in user-observable language<-
10. Does any section contain an escape hatch — language ambiguous enough that a candidate can skip a behavior and still satisfy the spec wording<-
11. For every statement that describes a priority order, override rule, or multi-source merge (e.g. "A takes precedence over B", "X overrides Y"): was this verified by calling the reference implementation with a concrete input where A and B conflict, not by inferring from documentation alone? If not verified against reference behavior, mark as unverified and do not include until verified<-
12. Does the candidate-visible body contain any of the following strings: `task_id`, `delta:`, `source_boundary:`, `Candidate Agent Input Boundary`, `benchmark`, `oracle`, `judge`? Any match → strip before sending to candidate<-
13. Does every NEW or MODIFIED behavioral clause fit one of the five EARS templates, carry a clause ID in the sidecar, and pass Q3 (upstream-doc ceiling, 1:N support, rule-not-instance)<-
14. **Oracle-consistency check:** for every CLI flag, keyword argument, file-layout convention, or output format that oracle tests exercise through a shared helper/fixture, does the spec state it (or is it Q2-derivable)? A single unstated helper convention can zero an entire layer (`--colored no`, `python -m`, `regex_subs=`) — cross-check helpers explicitly<-
15. **Blind-review gate:** reading only the spec diff, would a reviewer accept it as a normal open-source documentation PR (organized by concept, no test-shaped sentences, no enumeration mirroring a test file)<-

All fifteen must pass. Any failure -> patch and re-judge.

## Style Gate

**Style gate (mandatory before proceeding to Stage 3):**
- Spec must be organized by concept/workflow, NOT by module/class hierarchy
- No continuous signature code blocks exceeding 10 lines
- "Installable Surface" must be written as natural prose (e.g. "The package is imported as `httpcore`. The primary entry point is `ConnectionPool`..."), NOT as bare import code blocks
- No leakage words: benchmark, oracle, judge, task_id, candidate-visible, scorer
- Failure: return to spec-writer for revision

**Grandfather exemption:** Utility collection libraries (e.g. `boltons`) whose public API is naturally partitioned by independent sub-modules may use module-based H2 headings (e.g. `## boltons.cacheutils`). The key test: if there is no shared state or cross-module invariant connecting the modules, module-based organization IS the natural concept grouping. Mark such specs with `<!-- style_exemption: module-partitioned-utility -->` in the internal header.

## Critical Experiment Results

| Change | Effect |
|--------|--------|
| Missing one public import path (`utils.sqlite3`) | 100% collection failure - score completely invalid |
| Removing 2 invariants from a complete behavioral specification | Lost 14 system_e2e tests (25.38% -> 16.15%) |
| Adding algorithm steps / implementation blueprint | Model implements dependencies from scratch; 74 collection errors |

---

## Patching a Spec

### Handling spec_error vs spec_gap

`spec_patch_request.md` carries a `type` field. The handling differs:

**type: spec_gap** — A behavior exists in the reference but was omitted from the spec. Add the missing behavior using the three principles below. Standard documentation inference is acceptable.

**type: spec_error** — The spec currently states X, but the judge observed the reference doing Y. Before writing any correction:
1. Re-run the reference with the exact conflicting input provided in the request. Observe the output directly — do not re-infer from documentation.
2. Confirm the judge's observed value matches what the reference actually produces.
3. If confirmed: correct the spec claim to match the reference-observed value. If the correction contradicts other spec statements, resolve those contradictions too.
4. If the reference produces a third value Z (neither X nor Y): record the discrepancy, correct to Z, and note the judge's evidence was incomplete.
5. After correction, the spec_patch_request must be routed back through all 12 validation checks before the pipeline proceeds. A confirmed spec_error blocks QUALIFIED — do not record the contradiction as a model weakness until the spec is corrected and the candidate is re-evaluated.

Never correct a spec_error by documentation inference alone. The correction must be grounded in reference execution.

---

When processing a `spec_patch_request.md` from task-judge, apply changes using these three principles:

**1. Attach to the nearest host; do not create new structure.**
If the gap is a parameter, a CLI option, or a boundary condition of an existing concept, add it to the nearest existing code block signature or behavior bullet list. Do not create a new subsection. The reader should not be able to tell where the patch was inserted.

**2. Create a new section only for an independent concept domain.**
A concept warrants its own section when it has its own initialization/use/teardown lifecycle and cannot be naturally absorbed into any existing section. New sections must match surrounding sections in granularity and style.

**3. Write behavior language, not patch language.**
Each inserted sentence states what the system promises to callers, not that something was added. Avoid connective words like "also supports", "additionally", "in addition to". State the behavior directly as if it was always there.
