# High-Level Diagnosis: Why The First Three Worked

Date: 2026-06-28

## Summary

The first three core tasks worked because their system tests exposed non-local product invariants over rich, externally visible state:

- SQLite: rows, schemas, lookup tables, FTS tables, transforms, and error atomicity all had to agree after operation sequences.
- ZK: notebook files, parsed metadata, tag indexes, link resolution, graph output, config filters, and sorting had to agree over a filesystem state.
- MiniURLUtils: URL parsing, mutable object state, query parameter ordering, authority/userinfo formatting, navigation, normalization, and link extraction had to share one coherent URL representation.

The later tasks mostly failed to produce usable cases because their canonical fact source was too compact and obvious. A strong agent could naturally implement one dictionary/tree/AST/graph and route all projections through it. When a task was made harder, the added failures usually became primitive traps, exact-shape checks, or evaluator fairness problems rather than residual compositional failures.

## What Changed In The Iteration Loop

The loop drifted from selecting tasks with irreducible product complexity to repeatedly enriching small synthetic products:

- MiniRedis and MiniKV reduced to one type-tagged namespace.
- MiniTemplate reduced to a conventional parser/render context.
- MiniPackaging resolve metadata became a one-shot graph/projection function.
- MiniMarkdown canonical tree and workspace-v4 added natural projections, but Codex still scored high after fairness cleanup.
- MiniDynaconf has the right canonical-tree idea, but weaker agents are primitive-capped before system invariants can be isolated.

This is not primarily a judge-standard problem. The judge is doing useful work by removing private-shape, exact-exception, and primitive-cascade artifacts. Each fairness cleanup tends to raise candidate scores, which is evidence that the task surface was already near-solved or that the apparent gap was artificial.

## Agent Trajectory Pattern

The successful core failures show agents passing many public primitives and then losing cross-feature consistency. The failed candidate tasks show different trajectories:

- Strong agents build the obvious shared model and pass system rows.
- Weaker agents fail local loaders, parsers, casts, token schemas, or command parsing before reaching the intended invariant.
- No-artifact Qwen runs are provider/account failures and must not be read as model behavior.
- Direct completions are misleadingly cheap evidence; OpenHands/Codex scaffolds self-test and often solve compact products.

## Judge Standard Assessment

The 15pp unit-over-system gate plus fairness audit is still appropriate for a fair compositional benchmark. The standard may feel too strict only because the current candidate pool is dominated by near-solved compact tasks.

The solved criterion should remain semantic, not byte-identical source reproduction. A task is solved when a trustworthy agent artifact is behaviorally equivalent to the reference across public and product-natural hidden workflows, and any further separation would require private shapes, exact text, arbitrary ordering, or unrealistic scope.

## New Selection Rule

Before building or enriching another task, run a gap-opportunity audit:

- Reject the task if a single obvious `{key -> value}` / config tree / token tree / dependency graph model can satisfy all natural projections.
- Reject the task if all derived views can be recomputed in one straightforward pass from current inputs with no visible lifecycle/history/atomicity requirement.
- Prefer domains with durable external state plus at least three independently nontrivial projections: files or database rows, derived indexes, exported views, reverse queries, validation reports, cached/search views, or recovery/replay state.
- Require at least one product-natural workflow where independently correct components can still disagree after a sequence of operations.
- Run a cheap fresh Codex/OpenHands smoke candidate early. If it scores above roughly 90/90 after fairness cleanup, retire or radically rescope instead of adding adjacent hidden rows.

## Process Change

Future iteration should spend less effort patching negative candidates and more effort scouting new domains that already have the successful shape:

- persistent state plus derived indexes;
- operation order visible in outputs;
- multiple consumers of the same fact source;
- atomic failure that must preserve all projections;
- reverse or bidirectional views that can drift from forward views;
- enough real-repo product detail that a compact obvious implementation is insufficient.

Do not keep trying to manufacture a gap in MiniRedis, MiniKV, MiniTemplate, MiniMarkdown, MiniPackaging, or MiniDynaconf unless a materially larger public product scope is introduced.

## Skill Update

Created and validated `C:\Users\12547\.codex\skills\gap-opportunity-auditor` to run this pre-screening step before `$gap-invariant-task-builder`. The existing iteration and task-builder skills now call this pre-audit before repeated enrichment. This changes the workflow from "build then discover near-solved" to "reject obvious-model/one-shot candidates early unless the public scope is materially larger."

Forward-test result: a read-only subagent used the new skill on the current non-core candidate registry and concluded that no current non-core candidate should be enriched by adding nearby hidden rows. MiniRedis and Xitkit are `reject`; MiniKV, MiniTemplate, and MiniBitcask need solved/retire audits rather than micro-enrichment; MiniDynaconf, MiniPackaging, and MiniMarkdown only remain plausible if materially larger or cleaner public lifecycles are introduced.
