# Meta Diagnosis: Why The Loop Stalled After The First Three Tasks

Date: 2026-06-28

## Bottom Line

The first three tasks worked because they were naturally product-sized systems with durable state and several public projections that could drift from each other. The later loop mostly tried to manufacture the same gap inside compact mini-products. Strong agents responded by building the obvious unified representation, while weaker agents failed local primitives before reaching the intended invariant.

This is not primarily a judge-standard failure. The judge is strict, but the strictness is doing useful work: after fairness cleanup, many apparent gaps disappear because they were primitive cascades, private-shape checks, or exact-interface traps. The deeper failure is upstream task selection and loop dynamics.

## Why SQLite, ZK, And MiniURLUtils Worked

The successful tasks have irreducible external state:

- SQLite has database tables, schema metadata, extracted lookup tables, FTS indexes, query outputs, transform state, and atomic error behavior.
- ZK has notebook files, parsed title/tag/link facts, config filters, graph output, list views, and late link resolution over a filesystem.
- MiniURLUtils has one mutable URL representation that must project consistently into parsed fields, authority, query order, navigation, normalization, and serialization.

The observed model pattern was the desired one: agents passed many local contracts but failed when several independently reasonable components had to share one coherent state model. MiniURLUtils is the cleanest example: OpenHands DeepSeek passed 100% unit but only 60% system, with failures in authority/userinfo consistency, scheme-relative state, query mutation order, and IPv6 family/authority projection.

## What Changed In Later Iterations

The later candidates often had a canonical fact source that was too small:

- MiniRedis and MiniKV collapse to one type-tagged dictionary.
- MiniTemplate collapses to a conventional parser plus render context.
- MiniPackaging resolve-metadata-v3 collapses to a one-shot dependency graph projection.
- MiniMarkdown v3/v4 became structurally principled, but capable agents solved nearly all of it after fairness cleanup.
- MiniDynaconf has the right canonical-tree idea, but weak/capable runs do not isolate the lifecycle invariant: weak models fail nested projection, loaders, casts, or validators first; Codex has system >= unit.

Once the obvious model exists, adding adjacent system cases mostly adds more checks on the same representation. That does not create a compositional gap; it creates either a solved task or a primitive/spec trap.

## What The Agent Traces Show

The traces and artifacts show four recurring behaviors:

1. Strong agents build the obvious shared model.
   - MiniKV Qwen and MiniRedis DeepSeek both implement a single `_store`/type-tag state and naturally satisfy current shared-namespace system rows.
   - MiniPackaging v3 DeepSeek builds a public `resolve_metadata(...)` projection pipeline; remaining misses are mixed primitive and graph details, below gate.
   - MiniMarkdown workspace-v4 Codex builds a full `MarkdownWorkspace` with documents, tokens, TOC, links, backlinks, diagnostics, graph, export, and import.

2. Weak agents often fail too early.
   - MiniDynaconf DeepSeek/Qwen fail nested dict projection, PathLike/file loader, cast, and validator primitives before the lifecycle invariant is meaningful.
   - MiniRedis/Qwen misses local LPUSH/glob/arity-style behavior alongside two shared rows, producing no clean unit-over-system signal.

3. Some negative evidence is not model behavior.
   - Qwen MiniMarkdown and MiniTemplate reruns repeatedly failed before action selection with SiliconFlow account-balance errors. These are provider/completion failures, not 0% model solutions.

4. Direct completions were misleading.
   - Direct model output occasionally showed a plausible shared-state miss, but when the same domain was run through OpenHands or Codex subagents, the scaffolded agent often self-tested and solved the compact product. Formal evidence must stay agent-based.

## Is The Judge Standard Wrong?

The current acceptance standard is mostly right:

- `reference = 100/100`
- fresh agent provenance
- `unit - system >= 15pp`
- fairness audit showing residual system loss is compositional

The uncomfortable fact is that this standard rejects most current candidates because they do not actually contain a fair gap. When a fairness judge removes exact exceptions, private attributes, repeated parser roots, or primitive cascades, scores rise. That is a sign that the judge is filtering false positives, not that the benchmark is over-strict.

There is one adjustment worth making: the gate should explicitly report "residual compositional gap after primitive clustering", not just raw unit-system gap. MiniDynaconf and MiniPackaging show why: a numeric 20pp+ raw gap can still be unusable if most system failures are downstream of public primitive failures.

## The Loop Failure Mode

The iteration loop drifted from "find product domains with natural cross-view drift" to "repair or enrich current mini-products until a number appears." That creates three pathologies:

- Local optimization against the judge: new rows are added near the failed candidate, then removed by fairness review as exact or cascade-prone.
- Scope conservation bias: we kept the same small task identity instead of admitting that a larger public product surface was required.
- Weak-control confusion: Qwen low/low or no-artifact results were tempting to read as difficulty, but they mostly measured primitive readiness or provider health.

The result is a treadmill: every fair cleanup either raises system scores to near-solved or reveals that the model never reached composition.

## Decision Rule Going Forward

Before writing another PRD or hidden system suite, require a pre-build opportunity audit:

- There must be durable state, not just a small dict/tree/graph.
- At least three public projections must be candidate-owned and independently nontrivial.
- Some projection must persist over time: update/delete propagation, cache invalidation, replay/import/export, reverse indexes, failed-update rollback, or multi-environment reuse.
- A competent agent using one obvious model must still have a real chance to miss a product-natural invariant.
- If a fresh capable agent scores roughly 90/90 after fairness cleanup, stop enriching that surface and either retire it or materially rescope.

## Current Classification

Promote / keep as core evidence:

- SQLite
- ZK
- MiniURLUtils

Do not promote current packets:

- MiniRedis: too compact; after cleanup DeepSeek system is 100%.
- MiniKV: too compact; Qwen and DeepSeek solve system despite unit misses.
- MiniTemplate: conventional parser/render architecture solved by capable agents.
- MiniDynaconf: principled but primitive-capped; current evidence is not a fair lifecycle gap.
- MiniPackaging: one-shot graph/projection surface is under-discriminating; needs real dependency lifecycle or retire.
- MiniMarkdown: best redesign so far, but near-solved after fairness cleanup.
- MiniBitcask: solved/retire at current public scope.

## Practical Next Move

Stop micro-iterating the current negative candidates. The next useful work is a scouting pass for domains whose natural product surface already has the SQLite/ZK shape: persistent external state, multiple public derived views, reverse indexes, order-sensitive lifecycle, atomic rollback, and a nontrivial real-repo behavioral model.

## Skill Update From This Diagnosis

Created `C:\Users\12547\.codex\skills\gap-solved-auditor` to make the solved/retire gate explicit. The new skill audits whether a no-gap or near-solved task is truly solved, needs provenance repair, needs primitive-readiness revision, or deserves a materially larger public lifecycle. It encodes the rule that `system = 100` is not enough: solved requires trustworthy agent provenance, semantic equivalence to the reference across product-natural workflows, and no remaining fair invariant at the current task scale.

Updated `gap-benchmark-iteration` and `gap-fairness-judge` to call `gap-solved-auditor` before retiring tasks or adding more hidden rows to near-solved surfaces.

Forward-tested the new skill with read-only subagents:

- MiniBitcask audit returned `solved-retire`, citing fresh OpenHands provenance, 100/100 scores, non-identical implementation, no remaining failure clusters, and rejecting crash/fault-injection or exact disk-shape checks as distorted/out-of-scope.
- MiniMarkdown audit returned `provenance-repair`, not retire. It correctly avoided solved-retire on a near-solved task, but exposed a report-normalization issue: workspace-v4 score reports cover the current 37-case / 212-weight rubric, yet their `unit_score` and `system_score` fields are scalar floats and `unit_system_gap` is absent. Updated `gap-solved-auditor` to normalize both score schemas, compute missing gaps, and match reports against the current rubric case/weight before judging solved status.
