# Solved-Audit Batch

Date: 2026-06-28

## Purpose

Apply `C:\Users\12547\.codex\skills\gap-solved-auditor` to the remaining no-gap, near-solved, or materially-enrich candidate tasks. Each audit was run by a read-only subagent using only the skill path, task directory, and run-artifact directory. No task files were edited by the subagents.

## Verdict Matrix

| Task | Verdict | Main Evidence | Next Action |
|---|---|---|---|
| MiniRedis | `provenance-repair` | Current Codex 100/100 artifact is byte-identical to reference; OpenHands DeepSeek is independent but 80% unit / 100% system with public primitive misses | Rerun fresh public-packet Codex/OpenHands or mark current 100/100 as contaminated; do not retire yet |
| MiniKV | `provenance-repair` | Codex 100/100 is behaviorally solved and not reference-identical, but no matching trace/log proves public-packet-only provenance | Rerun or attach clean Codex/OpenHands provenance; retire if provenance checks out |
| MiniTemplate | `solved-retire` | Codex lifecycle-v3 artifact is 100/100 on current rubric, non-identical to reference, and semantically covers environment/cache/registry/include/import/inheritance/macro/autoescape lifecycle | Retire current task; further gap would require materially larger public template-language scope |
| MiniDynaconf | `not-solved-revise` | Current lifecycle-v3 best Codex artifact is 75% unit / 80% system; fails public auto-cast, delete return, import/export cast normalization, and export/reload validator projection | Revise primitive readiness and rerun fresh agent with trace; do not retire or accept gap |
| MiniPackaging | `not-solved-revise` | Codex v3 passes all resolver system rows but fails public version alias/marker serialization and lacks public `MetadataIndex` lifecycle implementation; current rubric undercovers that public surface | Add/revise public `MetadataIndex` lifecycle coverage, then rerun fresh agents |
| MiniMarkdown | `provenance-repair` from prior forward-test | Workspace-v4 reports cover current 37-case / 212-weight rubric and show near-solved 95.24% unit / 93.75% system after fairness cleanup, but score schema/provenance binding needed normalization | Keep near-solved/provenance-repair; do not retire until current workspace evidence is trace-bound |
| MiniBitcask | `solved-retire` from prior forward-test | OpenHands DeepSeek 100/100 with clean provenance, non-identical implementation, and no fair remaining invariant at this task scale | Retire |

## Cross-Task Findings

1. `system = 100` is not enough.
   - MiniRedis has a 100/100 Codex artifact, but it is byte-identical to the reference.
   - MiniKV has a 100/100 Codex artifact, but strict solved status needs trace provenance.

2. Some tasks are genuinely solved at current scope.
   - MiniTemplate lifecycle-v3 now has enough non-identical, semantically equivalent Codex evidence to retire at this scope.
   - MiniBitcask already has clean OpenHands solved evidence and should stay retired.

3. Some tasks are not solved, but also not accepted gaps.
   - MiniDynaconf has public primitive/cast readiness failures that block lifecycle evidence.
   - MiniPackaging has a public lifecycle surface (`MetadataIndex`) that is not covered strongly enough by the current rubric.

4. The strongest next construction signal is not "add more hidden rows" but "repair public lifecycle coverage".
   - MiniPackaging is the clearest candidate for a real revision because the missing surface is public and product-natural.
   - MiniDynaconf needs primitive readiness cleanup before another lifecycle run.
   - MiniRedis/MiniKV need provenance repair before retirement decisions.

## Immediate Queue

1. MiniPackaging: revise task/rubric around public `MetadataIndex` lifecycle: importability, add/update/remove, atomic `apply`, revision/index projections, export/import replay, and `dependents_of()` reverse queries.
2. MiniDynaconf: decide whether to simplify or move public auto-cast/delete/import primitives so lifecycle rows are not primitive-capped.
3. MiniKV: rerun or attach clean 100/100 provenance; likely retire if provenance holds.
4. MiniRedis: rerun clean public-packet capable agent; current 100/100 evidence is contaminated.
5. MiniMarkdown: normalize workspace-v4 provenance/report binding before deciding retire versus material rescope.

