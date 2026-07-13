# Loop Failure Reassessment

Date: 2026-06-28

## Core Judgment

The first successful tasks worked because they were not merely larger checklists. They had product-natural external state and multiple public projections that could drift even when local APIs looked correct.

- SQLite: tables, schema metadata, lookup tables, FTS/search views, transforms, query output, and error atomicity all had to remain consistent.
- ZK: filesystem notes, parsed frontmatter, tags, links, config filters, graph/list exports, and sorting all projected from shared durable files.
- MiniURLUtils: parsed fields, authority/userinfo, mutation order, normalization, navigation, query collections, and serialization all projected from one mutable URL state.

The later loop mostly tried to reproduce this shape inside compact mini-products. Strong agents often found the obvious canonical representation and routed every projection through it. Weaker agents often failed primitive loaders, parsers, casts, command parsing, or schema details before the intended invariant was reached.

## What The Trajectories Imply

The recurring model behavior is not "agents cannot compose." It is more specific:

1. If the public packet makes the canonical model obvious and small, capable agents implement it directly.
2. If the task is made harder by adding rows near one missed behavior, judge cleanup often reclassifies the gap as primitive cascade, exact interface trap, or private-shape assertion.
3. If weak controls fail before action selection or fail all primitives, their scores calibrate infrastructure or primitive readiness, not compositional difficulty.
4. Direct model completions overstate gap potential; OpenHands/Codex agents self-test compact surfaces and often solve them.

## Judge Assessment

The judge standard is not the main problem. The standard is exposing the problem.

The raw gate `unit - system >= 15pp` is useful only as a trigger. The real acceptance criterion must be residual compositional gap after clustering primitive roots, evaluator artifacts, provider failures, stale packets, and contamination.

The fact that MiniRedis, MiniKV, MiniTemplate, MiniPackaging, MiniMarkdown, and MiniDynaconf repeatedly lose their apparent gap after fairness cleanup means the judge is filtering false positives. It does not mean the judge is too strict.

One refinement is still needed: every report should show both raw gap and residual gap after root-cause clustering. MiniDynaconf is the clearest example: a 25pp raw gap is not accepted because the system rows are capped by nested-projection, loader, cast, and validator primitives.

## Why The Loop Stalled

The loop developed a scope-conservation bias. It kept the same candidate identities and tried to enrich them until a number appeared.

That creates a treadmill:

- add lifecycle/projection tests;
- get a numeric gap;
- judge removes primitive/cascade/private-shape causes;
- capable candidates become near-solved or system-easier-than-unit;
- add adjacent rows on the same surface;
- repeat.

The correct conclusion is not "one more hidden invariant." The correct conclusion is often "this public product surface is solved at this scale."

## Current Task Implications

- MiniRedis and MiniKV: compact single-namespace stores. Current fair system rows are solved by OpenHands/Qwen despite unit misses. Do not enrich with nearby parser/list/glob rows.
- MiniTemplate: conventional parser/environment architecture is obvious to capable agents. Retire current surface unless public scope becomes a much larger template language.
- MiniDynaconf: conceptually promising, but current packet is primitive-capped. Revise primitive readiness only if a cleaner public lifecycle can isolate composition.
- MiniPackaging: one-shot `resolve_metadata` is under-discriminating. Only a public `MetadataIndex` lifecycle with add/update/remove/apply/export/import/reverse-query state is worth another attempt.
- MiniMarkdown: best redesigned surface, but near-solved after fairness cleanup. Needs provenance normalization or materially larger public workspace semantics, not more adjacent canonical-tree rows.
- MiniBitcask: solved/retire at current CLI scope.

## Replacement Selection Rule

Before building another task, reject domains where one small obvious dict/tree/AST/graph can satisfy all natural projections.

Prefer domains with all of the following:

- durable external state, not only in-memory current inputs;
- at least three independently nontrivial public projections;
- order-sensitive lifecycle, cache invalidation, replay/import/export, reverse index, or rollback;
- system rows that still run after public primitives pass;
- hidden checks that compare public behavior, not private object shapes or exact incidental text;
- early smoke run showing capable agents are not already above roughly 90/90 after fairness cleanup.

The next productive move is scouting new product surfaces with the SQLite/ZK/MiniURLUtils shape, not continuing micro-iteration on current negative candidates.

## Skill Updates

Updated the local gap workflow skills so this diagnosis changes future behavior:

- `gap-domain-scout`: added accepted-anchor calibration, stop-loss after fresh capable 90/90-ish runs, explicit `revise-primitives`, provenance-contamination handling, and a definition of fresh capable evidence.
- `gap-opportunity-auditor`: added anchor comparison, mandatory raw-vs-residual gap distinction, stop-loss for repeated enrich/fairness-cleanup cycles, `revise-primitives`, and fresh-capable evidence exclusions.
- `gap-benchmark-iteration`: added anchor comparison before reruns, a two-cycle micro-iteration stop condition, report-gate language for residual compositional gap, `revise-primitives` handling, and fresh-capable evidence exclusions.

Validation: all three updated skills passed `quick_validate.py` using the bundled Codex runtime Python.

Forward test: a read-only explorer used the updated `gap-domain-scout` on `CANDIDATES.md` and `score_summary.csv`. It applied the intended stop-loss behavior: MiniKV, MiniTemplate, MiniMarkdown, and MiniBitcask route to solved/provenance audit; MiniRedis and MiniPackaging require material rescope; Xitkit rejects; MiniDynaconf remains the only current build-shaped candidate, but only after primitive-readiness revision. The explorer also surfaced three ambiguities, which were patched into the skills: `revise-primitives`, contaminated provenance, and the definition of fresh capable agent evidence.
