# Benchmark Candidate Task Registry

**Last updated**: 2026-06-28  
**Scope**: All candidate tasks evaluated for inclusion in the Unit/System Gap Benchmark. Tasks advance to `core strong` only after passing all three gates (Reference + Candidate + Fairness).

---

## Scale Audit Decision

The 2026-06-28 repo-scale audit found that several upstream repositories were
substantial, but the extracted benchmark tasks were compressed into one-file,
100-1,000 LOC "mini" implementations. This invalidates those packets as strict
SWE-E2E benchmark candidates even when the source repository is large.

New strict tasks must be full bounded subsystem reproductions:

- installable package or service, not one source file;
- 10+ candidate-owned modules and roughly 2,000+ non-test reference LOC;
- product-grade PRD with state model, CLI/API schemas, persistence, lifecycle,
  recovery, error, and compatibility semantics;
- 50+ executable hidden checks before the first strict candidate run, with
  integration/system tests crossing API/CLI/persistence/materialized-output
  boundaries;
- cleanroom mini-SWE-agent-style harness with no access to rubrics, reference,
  prior candidates, score reports, or iteration notes.

Legacy `Mini*` tasks remain historical diagnostics only. They must not be
promoted or repaired by adding adjacent hidden rows. Reusing a domain now means
building a new full-reproduction subsystem task.

---

## Status Definitions

| Status | Meaning |
|---|---|
| `core strong` | Passed all three gates; included in benchmark suite |
| `candidate/validated` | Passed Reference gate; candidate agent run confirmed gap ≥ 15pp |
| `candidate/unvalidated` | PRD and rubric written; no candidate agent run yet |
| `candidate/no-gap-observed` | Candidate agent run did not show gap ≥ 15pp |
| `candidate/no-gap-provenance-repair-after-*` | Apparent gap disappeared, but strict solved/retire still needs provenance-clean rerun or solved audit |
| `candidate/materially-enrich-after-*` | Current surface has no accepted gap; continue only by adding a materially larger public lifecycle/scope |
| `candidate/revise-after-*` | Current numeric gap is primitive/cascade dominated; revise primitive readiness or system layering before rerun |
| `candidate/no-gap-after-*` | A named redesign improved the invariant shape but fresh candidates still did not pass the accepted gap gate |
| `candidate/retire-after-*` | A named redesign reached the natural task surface and further gap pressure would require distorted or materially new scope |
| `retired/current-scope-*` | Current task surface is retired by Layer-0 structural audit or solved audit; only a materially new public product scope may reuse the domain |
| `needs-redesign/*` | Current task is not gap evidence, but the domain may be reused after a material public lifecycle or primitive-readiness redesign |
| `prospect` | Identified via scouting; no PRD yet |
| `excluded` | Evaluated and dropped; reason recorded |

---

## Existing Candidates

### MiniRedis
- **Source repo**: redis/redis
- **Origin**: tyx010/tyx-Bmk-dev
- **Status**: `retired/current-scope-structural-dead`
- **PRD**: `task/miniredis-realrepo-submit/prd.md`
- **Domain**: In-memory data structure store (CLI)
- **Modules (7)**: strings, lists, sets, hashes, key management + expiry, database management, error atomicity
- **Shared contract**: All 7 command modules share one type-tagged key namespace; expiry applies uniformly at command dispatch regardless of which module handles the command; failed commands must not corrupt any module's state.
- **Validation result (2026-06-27)**: Reference-compatible 100/100; Codex subagent 100.00% unit / 100.00% system; OpenHands + DeepSeek V4 Pro 88.89% unit / 83.33% system, 5.56pp gap. Remaining OpenHands system failures are cascade failures from unit-level LPUSH ordering and KEYS glob behavior.
- **Iteration result (2026-06-28)**: Invariant-v2 produced an 18.89pp OpenHands gap, but judge classified it as CLI parsing/quoting and arity cascade. After moving those roots into unit/interface coverage, reference and Codex remained 100/100 and OpenHands scored 80.00% unit / 100.00% system.
- **Qwen control (2026-06-28)**: OpenHands + Qwen scored 80.00% unit / 80.00% system, 0.00pp gap. The run produced a complete implementation but timed out during self-verification; the saved solution and log are retained as weak-model control evidence, not formal gap evidence.
- **Final supplemental audit (2026-06-28)**: A read-only subagent judged MiniRedis as `materially-enrich`, not strict solved/retired. Reference is 100/100, OpenHands DeepSeek v3 is 80.00% unit / 100.00% system, and Qwen is 80.00% / 80.00%; the remaining losses are parser/list/glob/arity primitives rather than the shared namespace invariant.
- **Solved-auditor batch (2026-06-28)**: Verdict `provenance-repair`. The current Codex 100/100 artifact is byte-identical to the reference, so it is contaminated for strict solved evidence. Independent OpenHands artifacts are not reference-equivalent because they still miss public list/glob/quoted parsing/arity/expiry primitives.
- **Layer-0 structural audit (2026-06-28)**: Verdict `STRUCTURAL_DEAD` for the current scope. The shared namespace is an obvious single-store model; after primitive cleanup, system rows are solved or weak-control no-gap. Unit rows also include feature-pure violations from cross-type setup and order-sensitive checks.
- **Recommendation**: Retire the current packet. Do not add hidden rows around parser/display primitives. Reuse the domain only through a materially larger public product lifecycle.

---

### MiniKV
- **Source repo**: huangshand/walrus
- **Origin**: tyx010/tyx-Bmk-dev
- **Status**: `retired/current-scope-structural-dead`
- **PRD**: `task/minikv-realrepo-submit/prd.md`
- **Domain**: In-memory KV store (Python class API)
- **Modules (6)**: string ops, bulk string ops, list ops, set ops, hash ops, key management + persistence
- **Shared contract**: All methods operate on a single key namespace; every key has exactly one type; type-restricted methods must raise `CommandError` on wrong-type keys; expiry applies uniformly across all type modules.
- **Validation result (2026-06-27)**: Reference 100/100; Codex subagent 100.00% unit / 100.00% system; OpenHands + DeepSeek V4 Pro 77.78% unit / 83.33% system, -5.56pp gap.
- **Iteration result (2026-06-28)**: Invariant-v2 produced a 20.63pp OpenHands gap, but judge traced it to counter auto-create and missing-key `lrange` cascades. After cleanup, OpenHands scored 77.78% unit / 100.00% system. Direct DeepSeek retained only an 8.73pp gap from one `kv_mset` typed-projection issue, below gate and not formal OpenHands evidence.
- **Qwen control (2026-06-28)**: OpenHands + Qwen scored 94.44% unit / 100.00% system, -5.56pp gap. The only scored miss is a list primitive (`lpush` order/return), while all system shared-namespace invariants pass.
- **Final supplemental audit (2026-06-28)**: A read-only subagent judged MiniKV as no-gap/solved-after-cleanup for the terminal surface, but not strict retire because the 100/100 non-reference candidate provenance is weak. OpenHands/Qwen failures are local primitives while all current system namespace invariants pass.
- **Solved-auditor batch (2026-06-28)**: Verdict `provenance-repair`. The Codex 100/100 artifact appears behaviorally solved and is not reference-identical, but no matching trace/log proves public-packet-only provenance. OpenHands/Qwen solve system while missing local primitives.
- **Layer-0 structural audit (2026-06-28)**: Verdict `STRUCTURAL_DEAD` for the current scope. The task collapses to one typed in-memory store; current system rows are solved while remaining losses are local primitive or return-shape issues.
- **Recommendation**: Retire the current packet. Do not continue provenance repair unless a paper trail is needed for solved accounting.

---

### MiniTemplate
- **Source repo**: pallets/jinja
- **Origin**: tyx010/tyx-Bmk-dev
- **Status**: `needs-redesign/known-pattern-lifecycle`
- **PRD**: `task/minitemplate-realrepo-submit/prd.md`
- **Domain**: Template engine
- **Modules**: lexer, parser, AST, renderer, filters, template inheritance, control flow
- **Shared contract**: The rendering context (variable bindings, filter registry, block definitions from inheritance) must thread consistently through lexer → parser → AST → renderer; each feature reads from and writes to the same context object.
- **Validation result (2026-06-27)**: Reference-compatible 100/100; Codex subagent 100.00% unit / 100.00% system; OpenHands + DeepSeek V4 Pro 100.00% unit / 100.00% system.
- **Failure diagnosis (2026-06-28)**: Read-only subagent judged the task too simple/checklist-like. OpenHands independently implemented the obvious recursive parser/rendering/context architecture. The Codex candidate is byte-identical to the reference and should be treated as possible procedural contamination unless separately explained.
- **Lifecycle redesign (2026-06-28)**: Rebuilt as a MiniJinja lifecycle task centered on one `Environment` shared by loader/cache, filters/tests, globals, includes/imports, inheritance, macros, undefined behavior, whitespace, and autoescape. Reference stayed 100.00% unit / 100.00% system. Fresh Codex subagent v2-001 scored 100.00% / 100.00%. OpenHands + DeepSeek V4 v2-001 initially scored 88.89% / 66.67%, but fairness judging found one ambiguous macro caller-context row and one cascade from malformed block parsing. After lifecycle-v3 cleanup, the same scoreable artifact scored 88.89% / 83.33%, a 5.56pp gap. OpenHands + Qwen produced no `minitemplate.py`, scoring 0.00% / 0.00% as a weak-control no-artifact failure. Later SiliconFlow Qwen reruns reached the endpoint but failed before action selection with `account balance is insufficient`; the rerun traces and no-artifact score reports are retained separately, including `openhands_qwen_rerun_002.log`.
- **Final supplemental audit (2026-06-28)**: A read-only subagent kept MiniTemplate as no-gap-after-lifecycle-v3, not strict solved/retired. Codex is 100/100, DeepSeek is 88.89% / 83.33% after cleanup, and Qwen remains no-artifact provider evidence. The remaining system loss is one markup/autoescape cluster plus primitive parser misses, below gate.
- **Solved-auditor batch (2026-06-28)**: Verdict `solved-retire`. The fresh Codex lifecycle-v3 artifact scores 100/100 on the current rubric, is not byte-identical to reference, and covers the public environment/cache/registry/include/import/inheritance/macro/autoescape lifecycle. Further fair gap pressure would require a materially larger public template-language scope.
- **Layer-0 structural audit (2026-06-28)**: Verdict `KNOWN_PATTERN`. The registry/cache/include lifecycle is real, but the Jinja2-like surface is saturated by known implementation patterns and fresh capable agents solve it.
- **Recommendation**: Retire the current Jinja-like packet. Reuse only with a materially different public lifecycle and syntax; do not tighten with adjacent hidden rows.

---

### MiniDynaconf
- **Source repo**: rochacbruno/dynaconf
- **Status**: `needs-redesign/primitive-readiness-and-rescope`
- **PRD**: `task/minidynaconf-realrepo-001/prd.md`
- **Domain**: Layered configuration management
- **Modules (6)**: settings file loader, environment variable loader, secrets loader, type casting, validators, runtime settings API
- **Shared contract**: Defaults, files, env vars, secrets, and runtime assignments merge into one canonical dotted key namespace; casting and validators must inspect the fully merged final state and failed updates must be atomic.
- **Validation result (2026-06-27)**: Reference 100/100; Codex subagent 100.00% unit / 100.00% system; OpenHands + DeepSeek V4 Pro 38.89% unit / 25.00% system, 13.89pp gap.
- **Lifecycle v3 (2026-06-28)**: Rebuilt around one canonical nested configuration tree with durable sources, runtime overlays, deletion tombstones, validators, `as_dict`, export/reimport, reload, and configure lifecycle projections. Reference passed 100.00% unit / 100.00% system. Fresh Codex subagent scored 75.00% unit / 80.00% system, so no gap. Fresh OpenHands + DeepSeek V4 Pro scored 25.00% unit / 0.00% system, but independent judge rejected the 25pp numeric gap as primitive/cascade-dominated: nested dict attribute proxy and validator-view primitives failed in unit rows and then capped every system row. Two real lifecycle defects were observed, but not enough to accept the run as compositional evidence.
- **Final supplemental audit (2026-06-28)**: A dedicated read-only subagent judged lifecycle-v3 as `revise`. The design is principled: one canonical configuration tree projects through attribute, item, dotted `get`, `exists`, export/reload/configure, and validators. The evidence is not a fair gap: Codex scored 75.00% unit / 80.00% system, while OpenHands DeepSeek V4 Pro scored 25.00% unit / 0.00% system because nested dict projection, PathLike, type-cast, file/env loader, and validator-view primitives failed before the lifecycle invariant could be isolated. OpenHands Qwen scored 54.55% / 25.00% on the earlier packet and is weak-control primitive-cascade evidence.
- **Solved-auditor batch (2026-06-28)**: Verdict `not-solved-revise`. Current lifecycle-v3 Codex is not semantically equivalent to reference: runtime auto-cast, delete return contract, import/export cast normalization, and export/reload validator projection still fail public behavior.
- **Primitive-readiness current rerun (2026-06-28)**: Current fairness-revised rubric was rerun against reference, Codex lifecycle-v3, and OpenHands DeepSeek lifecycle-v3. Reference remained 100.00% / 100.00%. Codex scored 75.00% unit / 100.00% system, so residual compositional gap is 0pp for the capable artifact; remaining misses are unit-level runtime cast/delete/import primitive details. OpenHands scored 25.00% / 40.00%, with nested attribute proxy, runtime cast, delete return, and validator/attribute primitive roots still capping the run. A read-only subagent audited the current evidence and recommended solved-audit/material rescope, not more adjacent hidden rows.
- **Layer-0 structural audit (2026-06-28)**: Verdict `REPAIR_PRIMITIVES` then `RESCOPE`. Current evidence is primitive-capped or system-solved. The concept is usable only if a larger public lifecycle makes multi-environment state, tombstones, failed configure rollback, export/import replay, validators, and reload projections interact.
- **Recommendation**: Do not accept as gap evidence and do not continue primitive-only revision on the same surface.

---

### MiniPackaging
- **Source repo**: pypa/packaging
- **Status**: `retired/current-scope-forced-pep-surface`
- **PRD**: `task/minipackaging-realrepo-001/prd.md`
- **Domain**: Package version and dependency metadata
- **Modules (6)**: version parser, specifier set, requirement parser, marker evaluator, environment builder, requirement satisfaction helper
- **Shared contract**: Requirement strings combine normalized names/extras, specifiers, markers, direct URLs, and installed versions; satisfaction must compose these pieces without changing their individual semantics.
- **Validation result (2026-06-27)**: Reference 100/100; Codex subagent 83.33% unit / 91.67% system; OpenHands + DeepSeek V4 Pro 72.22% unit / 91.67% system.
- **Iteration result (2026-06-28)**: A metamorphic revision briefly produced Codex 83.33% unit / 66.67% system, but independent fairness judging classified the gap as repeated primitive cascade from requirement equality/hash and invalid URL+specifier parsing. After removing repeated primitive roots from system scoring, reference remained 100/100 and usable candidates reached 100% system.
- **Qwen control (2026-06-28)**: OpenHands + Qwen produced a scoreable artifact but timed out before clean finish; scored 66.67% unit / 83.33% system, -16.67pp gap. Failures are dominated by version canonicalization/local ordering, direct URL formatting, invalid URL+specifier parsing, marker membership, one shared parser projection, and prerelease string projection. This remains weak-control/no-gap evidence.
- **Resolve metadata v3 (2026-06-28)**: Rebuilt the task around public candidate-owned `resolve_metadata(roots, candidates, environment=None, requested_extras=None, prereleases=None)`. System tests now call the candidate resolver and compare semantic graph projections: `selected`, `excluded`, `edges`, `dependents`, `requested_extras`, and `requirements`. Independent read-only audit judged the direction structurally fair, and fresh runs confirmed no accepted gap. Reference passed 100.00% unit / 100.00% system. Fresh Codex subagent scored 89.47% unit / 100.00% system, so system remains solved. Fresh OpenHands + DeepSeek V4 Pro scored 57.89% unit / 50.00% system, a 7.89pp gap below gate, with remaining loss still mixed primitive and graph-projection misses. Fresh OpenHands + Qwen v3 did not produce `minipackaging.py`; a mechanical 0/0 report is retained as no-artifact scaffold evidence, not functional model evidence. A corrected `-f` OpenHands rerun (`fa2380c8-4e93-4e30-8195-42a05f38ec8a`) reached the first model call with the later SiliconFlow key and failed before action selection with `account balance is insufficient`; `score_report_openhands_qwen_resolve_metadata_v3_002_noartifact_20260628.json` is accounting only.
- **Final supplemental audit (2026-06-28)**: A dedicated read-only subagent judged resolve-metadata-v3 as `materially-enrich`, not strict solved. Codex v3 scored 89.47% unit / 100.00% system; OpenHands DeepSeek V4 Pro scored 57.89% unit / 50.00% system, a 7.89pp gap below gate with mixed primitive and graph-projection roots. Qwen v3 produced no functional artifact in the corrected OpenHands rerun.
- **Solved-auditor batch (2026-06-28)**: Verdict `not-solved-revise`. Codex v3 passes all resolver system rows but is not fully equivalent to the public packet: it misses the public pre-release alias `1.0ALPHA2`, differs on marker quote serialization, and does not implement the public `MetadataIndex` lifecycle surface that only the reference currently has.
- **Layer-0 structural audit (2026-06-28)**: Verdict `FORCED` for the current PEP surface. Version/specifier/requirement behavior is heavily standardized, and current resolver rows are one-shot or solved. A custom repository/index/lock lifecycle would be a new scope, not a repair of the old PEP-only task.
- **Recommendation**: Retire the current PEP surface. If reused, rebuild as a custom package repository with add/update/remove/apply/export/import/revision/dependents lifecycle.

---

### MiniMarkdown
- **Source repo**: lepture/mistune
- **Status**: `needs-redesign/collapse-or-provenance-retire`
- **PRD**: `task/minimarkdown-realrepo-001/prd.md`
- **Domain**: Markdown block/inline parsing and rendering
- **Modules (6)**: block parsing, inline parsing, shared AST tokens, HTML rendering, plugin registration, error recovery
- **Shared contract**: Prose-bearing block tokens must feed inline parsing, renderers must consume the same public token semantics, and built-in/custom plugins must compose with the core parser and renderer dispatch.
- **Validation result (2026-06-27)**: Reference 100/100; Codex subagent 50.00% unit / 66.67% system; OpenHands + DeepSeek V4 Pro 27.78% unit / 33.33% system.
- **Iteration result (2026-06-28)**: Independent judging of the redesign-v2 Codex run found 94.44% unit / 91.67% system, gap 2.78pp. Remaining failures are narrow feature/cascade issues rather than compositional failure; OpenHands evidence appears stale against an older public packet.
- **Qwen control (2026-06-28)**: OpenHands + Qwen initialized but produced no `minimarkdown.py` and no file/terminal actions. The persisted conversation reports provider balance exhaustion before action selection; the mechanical no-artifact score is 0.00% unit / 0.00% system, but this should be recorded as provider/scaffold failure, not a compositional task or model-quality signal. Later SiliconFlow Qwen reruns again reached the endpoint but failed before any agent action with `account balance is insufficient`, including `openhands_qwen_rerun_002.log`, `openhands_qwen_rerun_003.log`, `openhands_qwen_rerun_006.log`, `openhands_qwen_rerun_008.log`, and the new-key `openhands_qwen_rerun_009.log`; rerun 007 is separately retained as launch-config failure because `LLM_API_KEY` was missing. Rerun 010 used a clean temporary OpenHands home/persistence directory to reduce user-skill prompt overhead and still failed with the same provider balance error. Rerun 012 used the later supplied SiliconFlow Qwen key through OpenHands, initialized conversation `db17ce5a-8e8c-48f8-bfec-e128a1880726`, and again failed before action selection with the same balance error; no `solution-openhands-qwen-rerun-012/minimarkdown.py` was produced. Rerun 013 used the latest supplied SiliconFlow Qwen key through the same OpenHands `--headless --json -f ... --override-with-envs` path, initialized conversation `a311ba098f0a4290bf8b24b8ebfb7e47`, passed the public task file, and again failed before action selection with `account balance is insufficient`; no `solution-openhands-qwen-rerun-013/minimarkdown.py` was produced. Rerun 014 used the newly supplied SiliconFlow credential `Qwen/Qwen3.5-397B-A17B` through OpenHands with the same public-packet file path and again failed before any tool action with `account balance is insufficient`; no `solution-openhands-qwen-rerun-014/minimarkdown.py` was produced. Direct provider probes to `/chat/completions` for both `Qwen/Qwen3.5-397B-A17B` and `Qwen/Qwen2.5-7B-Instruct` also returned HTTP 403 / `code=30001`. They remain no-artifact infra evidence only.
- **V3 probe (2026-06-28)**: A read-only task-builder proposed five stronger canonical-token-tree system cases over parse, AST, HTML, TOC, plugin matrix, renderer replay, no-mutation, and table-boundary ordering. Reference and Codex redesign-v2 passed all five probes; OpenHands DeepSeek errored or timed out. This supports solved classification for current Codex rather than adding more current-surface system rows.
- **Canonical tree v3 fresh runs (2026-06-28)**: Rebuilt around public `parse`/`tokens` canonical tree projections through AST, HTML, TOC, `walk`, plugin metadata, and renderer replay. Reference passed 100.00% unit / 100.00% system. Fresh Codex subagent scored 100.00% unit / 91.67% system, 8.33pp. Fresh OpenHands + DeepSeek V4 Pro scored 88.89% unit / 83.33% system, 5.56pp. Independent judge classified the task as solved/near-solved for current agents: remaining losses are one narrow loose-list metadata miss for Codex and small local feature/order failures for DeepSeek, not a broad compositional gap.
- **Workspace v4 follow-up (2026-06-28)**: A fresh Codex subagent implemented the richer multi-document `MarkdownWorkspace` surface and initially scored 90.48% unit / 87.50% system, 2.98pp. A read-only judge rejected the gap and found two evaluator fairness issues: `MMU021` required a specific exception class for rejected updates, and `MMS016` reached into private `clone._parser`. After revising those checks to use public behavior only, reference remained 100.00% / 100.00% and the same Codex artifact scored 95.24% unit / 93.75% system, 1.49pp. Remaining misses are malformed inline recovery and one table-boundary ordering invariant.
- **Final supplemental audit (2026-06-28)**: A dedicated read-only subagent judged canonical-tree-v3 as `materially-enrich`, and a later workspace-v4 judge classified the enriched surface as below-gate/near-solved after fairness cleanup. The system tests now satisfy the shared-fact-source principle: `parse`/`tokens` are the canonical tree and workspace documents project through AST, HTML, TOC, `walk`, plugin metadata, link/backlink indexes, diagnostics, export/import, and replay. The task is still below gate: Codex workspace-v4 after fairness revision scored 95.24% unit / 93.75% system, and OpenHands DeepSeek V4 Pro canonical-tree-v3 scored 88.89% unit / 83.33% system. Qwen remains provider/no-artifact evidence only, including reruns 012, 013, and 014 with later supplied `LLM_API_KEY` values.
- **Solved-auditor batch (2026-06-28)**: Verdict `provenance-repair`. Workspace-v4 reports match the current 37-case / 212-weight rubric and show near-solved behavior after fairness cleanup, but the current evidence still needs trace-bound provenance/report normalization before strict retire. Remaining misses are not an accepted broad compositional gap.
- **Layer-0 structural audit (2026-06-28)**: Verdict `COLLAPSE` / near-solved. The parser/workspace has multiple public projections, but current slug/tree surfaces collapse through shared helpers and the workspace-v4 lifecycle remains below gate after fairness cleanup.
- **Recommendation**: Do not accept as a gap. Do not ban shared helpers. Either retire after provenance normalization or materially rescope to update/delete/import replay over public materialized projections.

---

### MiniBitcask
- **Source repo**: SarthakMakhija/bitcask
- **Origin**: Nixer-713/bitcask-bench-task
- **Status**: `retired/current-scope-solved`
- **PRD**: `task/bitcask-realrepo-001/prd.md`
- **Domain**: Append-only log storage engine
- **Shared contract**: All operations (put/get/delete/merge) route through a single in-memory keydir (key → file-offset map); merge/compaction rebuilds keydir from hint files.
- **Reference gate (2026-06-28)**: Reference scored 100.00% unit / 100.00% system. The scorer now supports Bitcask's `kvmini.py DBDIR COMMAND [ARGS...]` CLI without regressing MiniRedis scoring.
- **Codex subagent result (2026-06-28)**: Fresh Codex subagent scored 100.00% unit / 100.00% system, 0.00pp gap. The score report is retained at `task/bitcask-realrepo-001/doc/score_reports/score_report_codex_subagent_001_unit_system_v1.json`.
- **OpenHands DeepSeek result (2026-06-28)**: Fresh OpenHands headless run with `openai/deepseek-v4-pro` produced a scoreable `kvmini.py`, conversation `90f7e307-93e6-4282-95c7-674543deb384`, and scored 100.00% unit / 100.00% system, 0.00pp gap. The trace is `runs/bitcask-realrepo-001/openhands_deepseek_v4_pro_001.log`.
- **Independent audit (2026-06-28)**: A read-only judge classified the evidence as `no-gap-observed, not a solved audit`. The candidate is not byte-identical to the reference and appears semantically equivalent on the current product surface, but the raw evidence lacks a full agent trace/provenance record. That is enough for no-gap, too thin for strict solved.
- **Solved audit (2026-06-28)**: A second read-only judge classified the updated evidence as `solved / retire`. The OpenHands trace gives trustworthy provenance, the OpenHands implementation is not reference-identical, no hacking or contamination signal was found, and no fair remaining invariant exists at this task scale without crash-consistency simulation, private disk-shape assertions, exact-format traps, or scope beyond the public CLI product.
- **Gap assessment**: **Solved / retire for this population**. The current public lifecycle is principled, but both Codex and OpenHands DeepSeek implemented the obvious append-only log plus replay/key-index architecture and passed every unit and system row.
- **Layer-0 structural audit (2026-06-28)**: Verdict `RETIRE_SOLVED`. The current CLI scope lacks independent public log/index/recovery projections; Codex and OpenHands DeepSeek solve all rows.
- **Recommendation**: Do not advance as core evidence and do not tighten this packet with adjacent hidden checks. Replace it only with a materially larger public WAL/index/recovery/stats lifecycle.

---

### Xitkit
- **Source repo**: hoechstleistungshaartrockner/xitkit
- **Origin**: Nixer-713/bitcask-bench-task
- **Status**: `excluded`
- **Shared contract**: Unclear; low community adoption, obscure module structure.
- **Gap assessment**: **None observed**. No clear shared cross-feature contract across 5+ modules identified.
- **Recommendation**: **Excluded** pending further investigation. Do not advance.

---

## New Prospects (Scouting Round 2026-06-27)

### dynaconf
- **Source repo**: rochacbruno/dynaconf
- **Status**: `prospect`
- **Domain**: Configuration management
- **Modules (~6)**: file loader (TOML/INI/YAML), environment variable override, secrets loader, type casting, validator, runtime settings API
- **Shared contract**: All configuration sources merge into one key namespace according to a fixed priority order (defaults → files → env vars → secrets → runtime); type casting and validators both act on the fully-merged result, not on individual source layers.
- **Gap assessment**: **Likely**. An agent implementing the env-override layer and the type-casting layer correctly in isolation will miss that an env var delivering a string override must be type-cast before reaching the validator — the ordering contract between layers is a cross-module invariant that unit tests per-layer do not expose.
- **Why distinct**: Config management is not represented in the existing 3 tasks or the 5 candidates.
- **Next step**: Write PRD; implement mini version (~500–900 lines Python).

---

### pypa/packaging
- **Source repo**: pypa/packaging
- **Status**: `prospect`
- **Domain**: Package version/dependency metadata
- **Modules (~5)**: version parser (PEP 440), specifier matching, requirement string parser, environment marker evaluator, extras resolver
- **Shared contract**: Specifier matching, marker evaluation, and extras resolution all operate on the same normalized version object and requirement string grammar; the resolver must correctly compose all three when evaluating whether a requirement is satisfied in a given environment.
- **Gap assessment**: **Likely**. `requests[security]>=2.0; python_version>="3.8"` requires all three modules (extras, specifier, marker) to be parsed from one string and evaluated together — the composition is only visible as a cross-module contract in system tests.
- **Why distinct**: Package versioning is a distinct domain with formal PEP 440 spec as oracle.
- **Next step**: Evaluate reference implementation size; write PRD if within 200–1500 line scope.

---

### lepture/mistune
- **Source repo**: lepture/mistune
- **Status**: `prospect`
- **Domain**: Markdown parsing
- **Modules (~5)**: block lexer, inline lexer, AST builder, renderer, plugin registry
- **Shared contract**: The inline lexer must be invoked on every text fragment produced by the block lexer; plugins register token handlers into the same dispatch table shared by both block and inline rendering.
- **Gap assessment**: **Likely**. An agent that implements block parsing and inline parsing correctly in isolation will fail system tests for nested constructs (emphasis inside table cells, code spans inside link titles) because the recursive inline-within-block invocation contract is only visible at the system level. Oracle is CommonMark spec + mistune.
- **Why distinct**: Markdown parsing is a distinct domain.
- **Next step**: Scope reference implementation; write PRD.

---

## New Prospects (Layer-0 Scouting Round 2026-06-28)

### MiniAptly
- **Source inspiration**: aptly archive manager
- **Status**: `candidate/no-gap-after-primitive-frontload`
- **Domain**: Debian-like archive snapshot/publish/recovery manager
- **Public projections**: package index files, release metadata, published tree, snapshot diff/list, search/show references, graph output, cleanup dry-run report
- **Agreement surface**: Package identity, checksum, snapshot membership, published component, and unreferenced-file reachability must agree across archive DB, pool, snapshots, published indexes, graph, and cleanup/recovery reports.
- **Gap assessment**: **Promising**. Unit rows can cover control parsing, query predicates, and checksum formatting while system rows catch snapshot immutability, publish switching, cleanup refcounts, graph consistency, and crash recovery.
- **Risk**: Avoid collapsing to static package-index generation.
- **Brief**: `prospects/miniaptly-prospect-001/enrichment_brief.md`
- **Second-pass audit**: `PRD_READY`; first PRD section should be `Public Product Contract And Semantic Output Schemas`.
- **PRD draft**: `task/miniaptly-realrepo-001/prd.md`
- **Rubric draft**: `task/miniaptly-realrepo-001/rubric.json`
- **Reference/candidate gate (2026-06-28)**: Reference v5 primitive-frontload passes 100.00% unit / 100.00% system. Fresh Codex subagent v5 scores 100.00% / 100.00%, so the capable-agent gate shows no gap on the current surface. OpenHands + DeepSeek V4 Pro v5 scores 66.67% unit / 60.00% system, a 6.67pp raw gap below the 15pp threshold after snapshot-diff and recovery primitives were frontloaded into unit rows.
- **Independent v5 judge**: Verdict `solved-audit`; residual compositional gap is 0pp or below gate. `MAU011`/`MAS001` are one `snapshot_diff.changed` primitive/cascade root, and `MAU009`/`MAU012`/`MAS004` are one pending publish recovery/isolation primitive/cascade root. Re-counting those system rows as residual gap would inflate cascade evidence.
- **Current decision**: Do not promote to CORE. Run solved audit or materially rescope; continue only with a larger public lifecycle if the audit finds a fair remaining invariant.

---

### MiniMigrationManager
- **Source inspiration**: Alembic revision graph and migration commands
- **Status**: `candidate/reference-passed-fairness-cleanup`
- **Domain**: Toy migration manager with revision DAG and applied schema state
- **Public projections**: revision graph/history, current DB version, schema introspection, upgrade/downgrade plan, branch-head report, dry-run SQL
- **Agreement surface**: Revision graph, version table, schema state, and generated plans must agree after branch merges, partial upgrades, stamping, downgrade, and failed transactional migration.
- **Gap assessment**: **Promising**. Unit rows can validate DAG traversal and schema operations while system rows catch drift among history/current/schema/plan after lifecycle operations.
- **Risk**: Avoid exact Alembic clone; use deterministic toy DDL and custom migration file format.
- **Brief**: `prospects/minimigrationmanager-prospect-001/enrichment_brief.md`
- **Second-pass audit**: `PRD_READY`; first PRD section should be `Public Product Contract And Migration State Model`.
- **Task-builder skill**: `skills/minimigrationmanager-task-builder/SKILL.md`
- **PRD draft**: `task/minimigrationmanager-realrepo-001/prd.md`
- **Rubric**: `task/minimigrationmanager-realrepo-001/rubric.json` with 12 executable unit rows and 5 executable system rows.
- **Requirement map**: `task/minimigrationmanager-realrepo-001/doc/requirement_map.md`
- **Forward audit**: Verdict `revise_before_reference`; task shape passed, but PRD needed tighter public semantics for `restore_*` metadata, ledger kinds, `recover()` statuses, `heads` target behavior, and unit/system layering. These revisions were applied in the current PRD draft.
- **Reference gate**: `score_report_reference_unit_system_v2_fairness.json`; 17/17 cases, unit 100.00%, system 100.00%. The executable audit found order/repr fairness risks; rubric was revised to canonicalize schema projections and avoid independent branch ordering assumptions.
- **Codex subagent run**: Raw v1 scored 83.33% unit / 40.00% system, but failures were evaluator/order/shape issues (`history` order, `base` current representation, stamp ledger revision field). After fairness cleanup, the same fresh artifact scores 100.00% unit / 100.00% system, 0.00pp gap.
- **Next step**: Judge the Codex no-gap result and run OpenHands DeepSeek/Qwen controls on the fairness-cleaned executable packet.

---

### MiniJobLedger
- **Source inspiration**: Oban-style database-backed job processing
- **Status**: `prospect/multifile-layer0-build`
- **Domain**: Persistent job queue, scheduler, retry, cron, metrics, and history ledger
- **Required project shape**: multi-file package or service with separate store, scheduler, retry, uniqueness, metrics, event, recovery, and CLI/API modules. A one-file `minijobledger.py` implementation is disallowed for strict construction.
- **Public projections**: job detail/history, queue counts, cron next-run view, uniqueness/conflict report, metrics rollups, event stream
- **Agreement surface**: Job row state, event log, queue counts, cron ledger, uniqueness windows, and metrics must agree after enqueue, schedule, cancel, claim, complete, fail, retry, and cron insert workflows.
- **Gap assessment**: **Promising**. Retry math, cron parsing, and enqueue primitives do not imply stale metrics, duplicate cron insert prevention, rollback after failed insert, or uniqueness drift across retained rows.
- **Risk**: Medium known-pattern risk from Oban/Celery/Sidekiq; avoid exact schema/API names.
- **Next step**: Write a multi-file rescope enrichment brief before PRD; strict runs must use mini-SWE-agent cleanroom, not same-tree OpenHands.

---

### MiniBuildCache
- **Source inspiration**: Bazel remote cache / bazel-remote
- **Status**: `prospect/multifile-layer0-build`
- **Domain**: Remote action/cache and content-addressable storage with eviction
- **Required project shape**: multi-file package or service with separate CAS, action-cache, namespace, eviction, status, audit, recovery, and CLI/API modules. A one-file `minibuildcache.py` implementation is disallowed for strict construction.
- **Public projections**: CAS lookup, action-cache lookup, status counters, eviction/audit log, namespace hit/miss report
- **Agreement surface**: Every action-cache entry must reference existing CAS digests; status must match reachable stored bytes; LRU/access order must remain coherent after reads, writes, overwrites, failed writes, and eviction.
- **Gap assessment**: **Promising**. Digest validation and size accounting units do not prove cross-view coherence after upload, action-result insertion, failed write, eviction, and status/report checks.
- **Risk**: Avoid exact Bazel REAPI clone and final-file-only tests.
- **Next step**: Write a multi-file rescope enrichment brief before PRD; strict runs must use mini-SWE-agent cleanroom, not same-tree OpenHands.

---

### MiniSchemaRegistry
- **Source inspiration**: Schema registry subject/version/compatibility lifecycle
- **Status**: `prospect/multifile-layer0-build-with-rescope`
- **Domain**: Custom record-schema registry with versioning, compatibility, references, and soft deletes
- **Required project shape**: multi-file package or service with separate parser, canonicalizer, subject store, ID table, compatibility engine, references, deletion/tombstone, report, and CLI/API modules. A one-file `minischemaregistry.py` implementation is disallowed for strict construction.
- **Public projections**: subject list, version list, id lookup, compatibility result, referenced-by reverse index, deleted-inclusive views
- **Agreement surface**: Canonical-equivalent schemas reuse global IDs, subject versions advance only for new content, compatibility applies subject override/global fallback, and deletes affect list/get/reverse-reference views consistently.
- **Gap assessment**: **Promising with rescope**. Schema parsing and compatibility units do not prove registry behavior across id reuse, subject-local versioning, config override behavior, deletes, and reverse references.
- **Risk**: Avoid exact Confluent/Avro clone.
- **Next step**: Write a multi-file rescope enrichment brief before PRD; strict runs must use mini-SWE-agent cleanroom, not same-tree OpenHands.

---

## New Full-Reproduction Prospects (Scale Audit 2026-06-28)

These candidates passed the first full-reproduction Layer-0 screen in
`FULL_REPRO_LAYER0_AUDIT_2026-06-28.md`. They are not yet PRD/rubric tasks.

### FeatureFlagControlPlane
- **Source inspiration**: thomaspoignant/go-feature-flag
- **Status**: `prospect/full-reproduction-build`
- **Scale**: 9894 files / 465642 text LOC counted locally
- **Agreement surface**: Versioned flag definitions, retrievers, cache
  snapshots, targeting contexts, exporter batches, notifier audit, and reload
  diagnostics must agree after reloads, partial retriever failure, targeting
  changes, and batch flushes.
- **Risk**: Medium contamination risk from OpenFeature and feature-flag systems;
  avoid exact SDK/API surface and frontload bucketing/targeting primitives.
- **Next step**: Use `skills/full-reproduction-task-builder` to write full PRD
  and 50+ check rubric only if queue/cache/schema are insufficient.

### DurableWorkflow
- **Source inspiration**: cschleiden/go-workflows
- **Status**: `prospect/full-reproduction-build`
- **Scale**: 389 files / 58436 text LOC counted locally
- **Agreement surface**: Durable event history, timers, activity attempts,
  worker queues, signals, queries, retry state, and replay diagnostics must
  agree after failures, timers, signals, and worker restarts.
- **Risk**: Medium/high Temporal-style contamination; use custom API and
  deterministic virtual clock.
- **Next step**: Viable after JobLedger/BuildCache; harness complexity is
  higher.

### BackupRepository
- **Source inspiration**: kopia/kopia
- **Status**: `prospect/full-reproduction-build`
- **Scale**: 1251 files / 139575 text LOC counted locally
- **Agreement surface**: Content packs, manifest index, snapshot graph,
  retention policy state, repair log, prune report, and restore output must
  agree after backup, delete, prune, corrupt, repair, and restore workflows.
- **Risk**: Filesystem setup cost; avoid exact Kopia/restic repository formats.
- **Next step**: Strong candidate once filesystem harness budget is accepted.

### DurableAppPlatform
- **Source inspiration**: restatedev/restate
- **Status**: `prospect/full-reproduction-rescope`
- **Scale**: 1412 files / 296869 text LOC counted locally with filesystem
  fallback after Git metadata write errors.
- **Agreement surface**: Invocation journal, service state, timers,
  idempotency keys, inbox/outbox records, and recovery reports must agree after
  duplicate calls, delayed timers, failures, and restarts.
- **Risk**: Scope may overlap with JobLedger/DurableWorkflow and become too
  broad; reserve as later candidate.
- **Next step**: Rescope to a local deterministic service if used.

## Source-Repo Pipeline Correction Addendum (2026-06-28)

The strict construction route was corrected after noticing that local reference
LOC was being expanded by hand. Going forward, full-reproduction candidates must
be sourced from real upstream repositories, transformed into public packets and
hidden rubrics, then reconstructed by agents in a cleanroom workspace. Candidate
LOC is not the target; if a tiny implementation passes a large-source-derived
task, the PRD/rubric is under-covering the source behavior.

New network-scouted repositories were shallow-cloned and measured locally:

### WorkflowScheduler
- **Source inspiration**: dagucloud/dagu
- **Status**: `candidate/layer1-draft-needs-executable-tests-and-reference`
- **Scale**: 2601 tracked files / 645085 nonblank text LOC counted locally
- **Agreement surface**: Workflow specs, run records, step attempts, queue
  leases, schedules, logs/events, and history indexes must agree after schedule,
  run, failure, retry, cancel, restart, and recovery.
- **Risk**: DAG schedulers are familiar; use benchmark-owned schemas and a
  deterministic local runner, not a Dagu UI/API clone.
- **Judge**: Layer-0 subagent judged it valid but changed next action to
  `BUILD_WITH_RESCOPE`; prevent collapse into a toy "parse DAG and return final
  status" runner.
- **Next step**: Highest-priority new candidate after rescope. Build source
  evidence map and public packet from Dagu README, README_SCHEMA, examples,
  docs, and tests.
- **Layer-1 draft (2026-06-28)**: Created PRD, source notes, requirement map,
  cleanroom harness plan, candidate public packet, 13-module starter skeleton,
  and 50-row rubric intent draft (20 unit / 15 integration / 15 system).
  Executable hidden tests and reference implementation are still missing; do
  not run model candidates yet.

### NativeBuildGrid
- **Source inspiration**: TraceMachina/nativelink
- **Status**: `prospect/full-reproduction-build-with-rescope`
- **Scale**: 859 tracked files / 146933 nonblank text LOC counted locally
- **Agreement surface**: CAS blobs, action results, scheduler leases, worker
  execution records, store metadata, and service metrics must agree after
  upload, dispatch, retry, worker loss, cache hit, and recovery.
- **Risk**: Bazel REAPI/remote-execution contamination. Use a custom local API
  and include scheduler/worker lifecycle; do not build another CAS-only mini.
- **Next step**: Consider as stronger BuildCache variant if scheduler/worker
  coordination is included.

### DurablePythonRuntime
- **Source inspiration**: dbos-inc/dbos-transact-py
- **Status**: `prospect/full-reproduction-build-with-rescope`
- **Scale**: 136 tracked files / 52838 nonblank text LOC counted locally
- **Agreement surface**: Workflow records, step records, transaction outputs,
  queue records, idempotency keys, recovery cursors, and event history must
  agree after duplicate calls, step failure, transaction rollback, queue
  delivery, and restart.
- **Risk**: Durable-execution contamination and decorator primitive cascade.
  Use a small benchmark-owned API and frontload decorator/context primitives.
- **Next step**: Reserve candidate or DurableWorkflow replacement.

### ContentIndexCache
- **Source inspiration**: npm/cacache
- **Status**: `prospect/full-reproduction-rescope`
- **Scale**: 61 tracked files / 6595 nonblank text LOC counted locally
- **Agreement surface**: Content blobs, index records, integrity metadata,
  timestamps, verify reports, and garbage-collection results must agree after
  put, get, remove, corrupt, verify, and collect.
- **Risk**: Compact library surface may collapse to a small implementation.
- **Next step**: Use only as part of a larger ContentCache/BuildCache lifecycle.

### sqlite-utils-fullrepro-001
- **Source repo**: sqlite-utils
- **Status**: `continue/filter-v5-primitive-cascade`
- **Scale**: 7,714 non-test Python LOC counted in repo-pool; 532 original test functions.
- **Current evidence (2026-06-30)**: Reference passes filter_v5 at 888 passed / 4 skipped / 0 failures (100% excluding skips). Codex spec_v6 scores 76 passed / 774 non-skipped (9.82%); NL2Repo-style spec_v7 scores 48 passed / 774 non-skipped (6.20%).
- **Diagnosis**: Valid solvability/filter, but current failures are dominated by broad API/CLI primitive gaps and cascades. Cross-view SQLite/schema/FTS failures exist but are not isolated enough for QUALIFIED.
- **Next step**: Continue sqlite-utils one more repair loop focused on primitive/API readiness, or retire if the next loops remain cascade-dominated.
---

## Summary Table

| Task | Domain | Status | Gap Confidence | Priority |
|---|---|---|---|---|
| MiniRedis | In-memory store (CLI) | retired/current-scope-structural-dead | Obvious single-store model; feature-pure unit violations; no residual gap | Retire current packet |
| MiniTemplate | Template engine | needs-redesign/known-pattern-lifecycle | Jinja2-like lifecycle is solved and known-pattern saturated | Rescope only |
| MiniDynaconf | Config management | needs-redesign/primitive-readiness-and-rescope | Current rows are primitive-capped or system-solved | Repair primitives only as part of larger lifecycle |
| MiniKV | In-memory store (API) | retired/current-scope-structural-dead | Obvious typed store; system solved while unit misses primitives | Retire current packet |
| MiniMarkdown | Markdown parsing | needs-redesign/collapse-or-provenance-retire | Workspace-v4 is near-solved below gate; helper collapse is not a public bug | Retire or materially rescope |
| MiniPackaging | Package metadata | retired/current-scope-forced-pep-surface | PEP surface is forced and one-shot; custom repo lifecycle would be new scope | Retire current packet |
| MiniBitcask | Log storage | retired/current-scope-solved | Codex and OpenHands DeepSeek both score 100/100; no fair remaining invariant at CLI scale | Retire current packet |
| Xitkit | Unknown | excluded | None | Excluded |
| MiniAptly | Archive snapshots | under-scoped historical candidate | One-file 357 LOC reference from a 54k LOC upstream; current surface solved/below gate | Replace with full ArchiveManager reproduction |
| MiniMigrationManager | Migration graph | under-scoped historical candidate | One-file 369 LOC reference from a 61k LOC upstream; fairness cleanup made Codex 100/100 | Replace with full MigrationManager reproduction |
| JobLedger | Job queue ledger | candidate/interface-locked-task-draft | Full PRD, requirement map, harness, 50-row rubric contract, and public starter skeleton created; executable reference/tests still pending | Build reference and executable test_code |
| BuildCache | CAS/action cache | full-reproduction prospect | Strong AC/CAS/status/eviction agreement surface; must include service/package boundaries | Write full subsystem PRD and 50+ check rubric |
| SchemaRegistry | Schema registry | full-reproduction prospect | Strong projections but contamination risk needs custom schema language | Write full subsystem PRD and 50+ check rubric |

