# Failure Diagnosis And Qwen Control

Date: 2026-06-28

## Scope

This iteration continued the gap loop after balance recovery with read-only subagent failure diagnosis and OpenHands + Qwen control runs.

Subagents analyzed:

- `miniredis-realrepo-submit`
- `minikv-realrepo-submit`
- `minidynaconf-realrepo-001`
- `minipackaging-realrepo-001`
- `minimarkdown-realrepo-001`
- `minitemplate-realrepo-submit`

MiniTemplate was analyzed after the first five because it is a solved/no-gap 100/100 negative control.

## Qwen Control

Condition:

- Agent scaffold: OpenHands CLI headless
- Model: `openai/Qwen/Qwen3.5-397B-A17B`
- Provider: SiliconFlow OpenAI-compatible endpoint via runtime environment variables
- Public packet only: task-specific `runs/*/openhands_qwen_task.txt`
- Output: task-specific `runs/*/solution-openhands-qwen-001`
- Trace: task-specific `runs/*/openhands_qwen_001.log` plus OpenHands conversation persistence where available

Score:

| Task | Candidate | Unit | System | Gap |
|---|---|---:|---:|---:|
| MiniRedis | OpenHands + Qwen | 80.00% | 80.00% | 0.00pp |
| MiniKV | OpenHands + Qwen | 94.44% | 100.00% | -5.56pp |
| MiniTemplate lifecycle-v3 | OpenHands + Qwen | 0.00% | 0.00% | 0.00pp |
| MiniDynaconf v2 | OpenHands + Qwen | 54.55% | 25.00% | 29.55pp |
| MiniPackaging | OpenHands + Qwen | 66.67% | 83.33% | -16.67pp |
| MiniMarkdown | OpenHands + Qwen | 0.00% | 0.00% | 0.00pp |

The Qwen agent produced `miniredis.py` but did not finish cleanly: it got stuck during local PowerShell self-verification, and the run was stopped after timeout. The implementation is still scoreable and the trace is retained.

Rerun note: after receiving a new SiliconFlow Qwen credential, MiniMarkdown and MiniTemplate were retried through OpenHands with `PYTHONIOENCODING=utf-8` to avoid the Windows GBK console crash seen in the first retry attempt. Both reruns reached the OpenAI-compatible endpoint but failed before action selection with `litellm.APIError: OpenAIException - Sorry, your account balance is insufficient`. The rerun logs are retained as:

- `runs/minimarkdown-realrepo-001/openhands_qwen_rerun_001_utf8.log`
- `runs/minitemplate-realrepo-submit/openhands_qwen_rerun_001_utf8.log`

A second SiliconFlow Qwen credential was tested through the same OpenHands CLI scaffold and model setting (`openai/Qwen/Qwen3.5-397B-A17B`). Both MiniMarkdown and MiniTemplate again initialized the OpenHands agent and failed on the first model call with `litellm.APIError: APIError: OpenAIException - Sorry, your account balance is insufficient`. No tool actions or solution files were produced. The new logs are retained as:

- `runs/minimarkdown-realrepo-001/openhands_qwen_rerun_002.log`
- `runs/minitemplate-realrepo-submit/openhands_qwen_rerun_002.log`

A third SiliconFlow Qwen credential provided after balance recovery was tested through OpenHands, not direct completion, on MiniMarkdown rerun 003. The OpenHands conversation `0f90f7b0-558a-4bce-85e3-61248db25443` again failed before action selection with `litellm.APIError: APIError: OpenAIException - Sorry, your account balance is insufficient`. No `solution-openhands-qwen-rerun-003` artifact was produced. The trace is retained as:

- `runs/minimarkdown-realrepo-001/openhands_qwen_rerun_003.log`

A later SiliconFlow Qwen credential was tested through OpenHands on MiniMarkdown rerun 006. The OpenHands conversation `6f632032-dae0-48f8-8972-714660fd45a3` initialized the Qwen model and failed before action selection with the same `account balance is insufficient` provider error. No `solution-openhands-qwen-rerun-006` artifact was produced. The trace is retained as:

- `runs/minimarkdown-realrepo-001/openhands_qwen_rerun_006.log`

After balance was reported as restored, rerun 007 first validated the current OpenHands CLI environment path and failed before model invocation because the newer `--override-with-envs` entrypoint requires `LLM_API_KEY`, not only `OPENAI_API_KEY`. That trace is retained as launch/config accounting only:

- `runs/minimarkdown-realrepo-001/openhands_qwen_rerun_007.log`

Rerun 008 supplied `LLM_API_KEY`, `LLM_MODEL=openai/Qwen/Qwen3.5-397B-A17B`, and the SiliconFlow OpenAI-compatible base URL. OpenHands successfully initialized conversation `bbf0cde6-d764-4045-b55d-1fde97acf214`, passed the public task file to the agent, and reached the first model call, but the provider again returned `litellm.APIError: APIError: OpenAIException - Sorry, your account balance is insufficient` before any tool action. No `solution-openhands-qwen-rerun-008` artifact was produced. The trace is retained as:

- `runs/minimarkdown-realrepo-001/openhands_qwen_rerun_008.log`

Rerun 009 used the newly supplied SiliconFlow credential through OpenHands only, with `LLM_API_KEY`, `LLM_MODEL=openai/Qwen/Qwen3.5-397B-A17B`, and `LLM_BASE_URL=https://api.siliconflow.cn/v1`. OpenHands initialized conversation `e861c791-6481-4675-a5a7-9d7c27a817f6`, passed the current MiniMarkdown canonical-tree task file to the agent, and again failed before action selection with the same provider balance error. No `solution-openhands-qwen-rerun-009/minimarkdown.py` artifact was produced. The trace is retained as:

- `runs/minimarkdown-realrepo-001/openhands_qwen_rerun_009.log`

Rerun 010 repeated the MiniMarkdown OpenHands run with a clean temporary OpenHands home and persistence directory to reduce user-skill prompt injection while preserving the OpenHands tool-using agent scaffold. The first model call still returned `account balance is insufficient`, before any tool action. A separate minimal non-benchmark SiliconFlow 1-token probe against `Qwen/Qwen3.5-397B-A17B` also returned HTTP 403 with `code=30001` and the same balance message, confirming that the credential/account is not currently callable even outside the benchmark prompt. The trace is retained as:

- `runs/minimarkdown-realrepo-001/openhands_qwen_rerun_010_cleanhome.log`

Rerun 012 used the later supplied SiliconFlow Qwen key through OpenHands only, with `LLM_API_KEY`, `LLM_MODEL=openai/Qwen/Qwen3.5-397B-A17B`, and `LLM_BASE_URL=https://api.siliconflow.cn/v1`. OpenHands initialized conversation `db17ce5a-8e8c-48f8-bfec-e128a1880726`, passed the public MiniMarkdown canonical-tree task file to the agent, and again failed before action selection with `litellm.APIError: APIError: OpenAIException - Sorry, your account balance is insufficient`. No `solution-openhands-qwen-rerun-012/minimarkdown.py` artifact was produced. The trace is retained as:

- `runs/minimarkdown-realrepo-001/openhands_qwen_rerun_012.log`

Rerun 013 used the latest supplied SiliconFlow Qwen key through OpenHands only, with `LLM_API_KEY`, `LLM_MODEL=openai/Qwen/Qwen3.5-397B-A17B`, and `LLM_BASE_URL=https://api.siliconflow.cn/v1`. A direct 1-token SiliconFlow probe returned HTTP 403 / `code=30001`, and the OpenHands run independently confirmed the same provider state: conversation `a311ba098f0a4290bf8b24b8ebfb7e47` initialized, received `runs/minimarkdown-realrepo-001/openhands_qwen_rerun_013_task.txt` as the public task file, then failed before action selection with `litellm.APIError: APIError: OpenAIException - Sorry, your account balance is insufficient`. No `solution-openhands-qwen-rerun-013/minimarkdown.py` artifact was produced. The trace is retained as:

- `runs/minimarkdown-realrepo-001/openhands_qwen_rerun_013.log`

Rerun 014 used the newly supplied SiliconFlow Qwen credential through OpenHands only, with `LLM_API_KEY`, `LLM_MODEL=openai/Qwen/Qwen3.5-397B-A17B`, and `LLM_BASE_URL=https://api.siliconflow.cn/v1`. OpenHands initialized conversation `32399152-a124-41bb-a02f-839040b511a4`, received `runs/minimarkdown-realrepo-001/openhands_qwen_rerun_014_task.txt` as the public task file, then failed before action selection with `litellm.APIError: APIError: OpenAIException - Sorry, your account balance is insufficient`. No `solution-openhands-qwen-rerun-014/minimarkdown.py` artifact was produced. Direct provider probes with the same credential returned HTTP 403 / `code=30001` for both `Qwen/Qwen3.5-397B-A17B` and `Qwen/Qwen2.5-7B-Instruct`, while `/v1/models` successfully listed the requested model. The trace is retained as:

- `runs/minimarkdown-realrepo-001/openhands_qwen_rerun_014.log`

A corrected MiniPackaging resolve-metadata-v3 Qwen rerun was launched through OpenHands with `--headless --json -f ... --override-with-envs`, avoiding the earlier unquoted task-text CLI parse failure. The OpenHands conversation `fa2380c8-4e93-4e30-8195-42a05f38ec8a` initialized the Qwen model and then failed before action selection with `litellm.APIError: APIError: OpenAIException - Sorry, your account balance is insufficient`. No `solution-openhands-qwen-resolve-metadata-v3-001/minipackaging.py` artifact was produced. The trace is retained as:

- `runs/minipackaging-realrepo-001/openhands_qwen_resolve_metadata_v3_002.log`

No solution artifacts were produced. Mechanical no-artifact score reports were written for accounting only:

- `task/minimarkdown-realrepo-001/doc/score_reports/score_report_openhands_qwen_rerun_001_noartifact_20260628.json`
- `task/minitemplate-realrepo-submit/doc/score_reports/score_report_openhands_qwen_rerun_001_noartifact_20260628.json`
- `task/minimarkdown-realrepo-001/doc/score_reports/score_report_openhands_qwen_rerun_002_noartifact_20260628.json`
- `task/minitemplate-realrepo-submit/doc/score_reports/score_report_openhands_qwen_rerun_002_noartifact_20260628.json`
- `task/minimarkdown-realrepo-001/doc/score_reports/score_report_openhands_qwen_rerun_003_noartifact_20260628.json`
- `task/minimarkdown-realrepo-001/doc/score_reports/score_report_openhands_qwen_rerun_006_noartifact_20260628.json`
- `task/minimarkdown-realrepo-001/doc/score_reports/score_report_openhands_qwen_rerun_007_noartifact_20260628.json`
- `task/minimarkdown-realrepo-001/doc/score_reports/score_report_openhands_qwen_rerun_008_noartifact_20260628.json`
- `task/minimarkdown-realrepo-001/doc/score_reports/score_report_openhands_qwen_rerun_009_noartifact_20260628.json`
- `task/minimarkdown-realrepo-001/doc/score_reports/score_report_openhands_qwen_rerun_010_cleanhome_noartifact_20260628.json`
- `task/minimarkdown-realrepo-001/doc/score_reports/score_report_openhands_qwen_rerun_012_noartifact_20260628.json`
- `task/minimarkdown-realrepo-001/doc/score_reports/score_report_openhands_qwen_rerun_013_noartifact_20260628.json`
- `task/minimarkdown-realrepo-001/doc/score_reports/score_report_openhands_qwen_rerun_014_noartifact_20260628.json`
- `task/minipackaging-realrepo-001/doc/score_reports/score_report_openhands_qwen_resolve_metadata_v3_002_noartifact_20260628.json`

Failure roots:

- `MDRU004`: LPUSH order primitive.
- `MDRU015`: glob/pattern primitive.
- `MDRU019`: quoted value and quoted glob parsing primitive.
- `MDRU020`: invalid arity and failed-command atomicity.
- `MDRS003`: wrong-type/type-projection preservation across several views.
- `MDRS010`: flush/reuse/batch-visible state inconsistency.

Interpretation: Qwen is weaker than DeepSeek on the same OpenHands scaffold, but the weaker model did not create the desired unit>system gap. It failed both local primitives and two shared-state cases, yielding 0pp. This is useful control evidence that "weaker model" is not sufficient; the benchmark needs system invariants that a component-complete implementation still misses.

Additional controls:

- MiniKV produced a scoreable artifact and scored 94.44% unit / 100.00% system. The only miss is the local `lpush` ordering/return primitive; all shared-namespace system cases pass. This is strong negative evidence for the current MiniKV system layer as a compositional discriminator.
- MiniPackaging produced a scoreable artifact but timed out before clean finish. It scored 66.67% unit / 83.33% system, so the system layer was again easier than unit. The failed rows cluster around primitive version canonicalization/local ordering, direct URL string formatting, invalid URL+specifier rejection, marker membership, one shared parser projection, and prerelease string projection. The Qwen trace shows active self-testing and debugging, not refusal or direct-completion contamination.
- MiniMarkdown initialized OpenHands but produced no `minimarkdown.py` and no file/terminal actions. The persisted conversations report an OpenAI-compatible provider error for insufficient account balance before action selection, including rerun 012 with the later supplied key. The retained 0/0 score reports are no-artifact accounting records only; these runs should be classified as `completion_failure / no_solution_artifact / infra_provider_error`.

## Subagent Failure Diagnosis

MiniRedis:

- Current fair scores: Codex 100/100, OpenHands DeepSeek 80/100.
- The earlier 18.89pp gap was parser/quoting/glob/arity cascade.
- After cleanup, OpenHands passes all fair shared-namespace system rows.
- Diagnosis: task is too compact; a single `{type, value, expires_at}` store naturally satisfies the intended system invariants.

MiniKV:

- Current fair scores: Codex 100/100, OpenHands DeepSeek 77.78/100, direct DeepSeek 94.44/85.71.
- The earlier 20.63pp OpenHands gap was counter auto-create and missing-key `lrange` cascade.
- Direct DeepSeek has one meaningful `kv_mset` typed-projection miss, but it is direct-only and below gate.
- Qwen scored 94.44/100.00 with one list primitive miss and no system loss.
- Diagnosis: useful negative evidence; compact typed namespace is too directly solvable by OpenHands/Codex.

MiniDynaconf:

- Original OpenHands score: 38.89/25.00, 13.89pp, below gate.
- Later redesign can create a larger numeric gap, but it is dominated by primitive failures: PathLike handling, nested attribute projection, explicit casts, dict normalization, and validator snapshot API.
- Diagnosis: system layer gets cut off before reaching the intended merged-configuration invariant. Unit primitives are too strong relative to model ability.

MiniPackaging:

- Current fair scores: Codex 83.33/100, Codex redesign-v2 83.33/100, OpenHands DeepSeek 72.22/100.
- The temporary 16.67pp Codex gap was repeated primitive cascade from requirement equality/hash and invalid URL+specifier parsing.
- After semantic cleanup, usable candidates pass resolver/projection system rows.
- Qwen control scored 66.67/83.33. Its failures are mostly primitive semantics with limited cascade: PEP 440 canonical strings/local ordering, PEP 508 URL/specifier rejection and formatting, and marker `in` membership. The two system misses surface those primitives rather than a new cross-component invariant.
- Diagnosis: the current resolver graph is under-discriminating once primitive identity/parser failures are isolated; even a weak control passes 10/12 system rows.

MiniMarkdown:

- Current redesign-v2 Codex score: 94.44/91.67, 2.78pp.
- Original task had inverted layering: unit token schema stricter than system rendered-substring checks.
- Remaining redesign-v2 misses are hard-break and list-item AST projection roots, not parser+renderer+TOC composition.
- OpenHands evidence is stale against an older public packet.
- Qwen control is not a semantic run: OpenHands stopped before any tool action because the provider reported insufficient balance. The mechanical no-artifact 0/0 score must be segregated from functional model scores.
- Diagnosis: near-solved; needs material parser lifecycle enrichment rather than small rubric tweaks.

MiniTemplate:

- Scores: reference 100/100, Codex 100/100, OpenHands DeepSeek 100/100, direct DeepSeek 100/100.
- OpenHands independently implemented a conventional tokenizer/parser/AST renderer with scoped contexts.
- Codex candidate is byte-identical to the reference, so its score should be treated as possible procedural contamination unless separately explained.
- Diagnosis: task is too simple and checklist-like. System rows are shallow compositions of the public feature bullets rather than hidden lifecycle invariants.
- Recommended action: retire current task or rebuild as a richer MiniJinja lifecycle task with loaders, inheritance/block override resolution, filter/test registries, globals, include/import, macro scoping, whitespace controls, undefined policies, and cache invalidation.

## Fresh Subagent Audit After Qwen Rerun 002

Four read-only subagents re-audited the main negative tasks after the second Qwen rerun. No files were modified by the subagents.

- MiniDynaconf: reject as accepted gap. Current Codex v2 is 100/100. DeepSeek v2 has a 22.73pp numeric gap, but the failed system rows are mostly cascades from primitive runtime nested mutation, explicit cast handling, malformed file errors, and dotted projection. Qwen 54.55/25.00 is weak-control evidence dominated by the same primitives. Next fair move is a richer config lifecycle invariant across validator defaults, env/file/secrets/runtime overrides, deletion/reload, and export/import.
- MiniMarkdown: reject as accepted gap. Codex redesign-v2 is 94.44/91.67, only 2.78pp. The current system layer has invariant intent, but many executable checks are still rendered-substring or simple projection checks rather than forcing one canonical parse tree through HTML, AST, TOC, and plugin views. Qwen rerun 002 is provider no-artifact only.
- MiniTemplate lifecycle-v3: reject as accepted gap. Codex solves 100/100. OpenHands DeepSeek lifecycle-v3 is 88.89/83.33, only 5.56pp, with the remaining system loss concentrated in one repeated autoescape/markup-safety cluster (`MTES005`, `MTES011`) plus unit misses for integer dot index and parse-time syntax errors. Qwen rerun 002 is provider no-artifact only.
- MiniPackaging: reject as current gap. After fairness revision, Codex and DeepSeek candidates pass all system rows while still failing strict unit primitives. The prior metamorphic gap came from requirement equality/hash, semantic dedup, invalid URL+specifier, and version string primitive cascades. Current Qwen system misses (`MPS002`, `MPS007`) are marker normalization/version serialization leaks, not resolver-graph failures. A fair enrichment would expose a candidate-owned `resolve_metadata(...)` projection API with selected versions, edges, reverse dependents, exclusions, and marker/specifier facts.

## Cross-Task Lesson

The user's proposed diagnosis is supported by the traces:

> A fair gap requires a system invariant that cannot be satisfied by independently completing each feature. It must require several APIs/views to share one fact source and maintain consistent projections.

The negative candidates mostly fail for three reasons:

1. The central fact source is too small and obvious, so implementing the obvious single store solves system tests.
2. System rows accidentally repeat primitive roots already visible in unit tests.
3. Unit tests are so feature-heavy that weak agents never reach the intended composition layer.

## Decision

No candidate is promoted in this iteration.

Keep the three current core strong tasks as positive evidence:

- SQLite
- ZK
- MiniURLUtils

Treat MiniRedis, MiniKV, MiniPackaging, MiniMarkdown, MiniDynaconf, and MiniTemplate as negative, solved, or near-solved evidence. After the final supplemental audits, MiniMarkdown canonical-tree-v3 and MiniDynaconf lifecycle-v3 should be retired rather than lightly enriched in place; fair new gaps would require materially new public product scope, not adjacent hidden rows.

## Final Supplemental Subagent Audit

After balance recovery, two additional read-only subagents re-audited the remaining open redesign candidates:

- MiniMarkdown canonical-tree-v3/workspace-v4: `materially-enrich / near-solved after fairness cleanup`. The task now follows the right principle: `parse/tokens` are the shared fact source and AST/HTML/TOC/walk/plugin/render replay are projections. The workspace-v4 follow-up adds a more product-natural multi-document index lifecycle. A read-only judge found the initial Codex misses included two evaluator fairness issues, so `MMU021` was relaxed to require rejection/atomicity rather than `TypeError`, and `MMS016` was rewritten to use public `tokens()` traversal rather than private `clone._parser`. Reference stayed 100.00% / 100.00%; the same Codex artifact rose to 95.24% unit / 93.75% system, only 1.49pp. Qwen remains no-artifact/provider evidence for this packet, including reruns 012, 013, and 014 with later supplied `LLM_API_KEY` values.
- MiniDynaconf lifecycle-v3: `revise`. The task follows the right principle: one canonical config tree projects through attribute, item, dotted `get`, `exists`, export/reload/configure, and validators. The evidence is not a fair gap: Codex subagent 75.00% unit / 80.00% system, OpenHands DeepSeek V4 25.00% unit / 0.00% system. DeepSeek and Qwen are primitive-capped by nested dict projection, PathLike, type-cast, file/env loader, and validator-view failures.

## Skill Feedback

Updated and validated:

- `C:\Users\12547\.codex\skills\gap-invariant-task-builder`
- `C:\Users\12547\.codex\skills\gap-benchmark-iteration`
- `C:\Users\12547\.codex\skills\gap-fairness-judge`

Changes added from this failure round:

- Task construction must pass the independent-component self-check: if separate per-function implementations can pass system, the task is checklist-like.
- System tests must add a fact-source/projection invariant beyond unit contracts; unit passing must not imply system passing.
- Weak-model controls such as OpenHands + Qwen are calibration evidence only. Low unit and low system scores do not prove compositional difficulty.
- Agent-run provenance must record whether evidence is a formal agent candidate, direct completion, weak control, stale packet, timeout/incomplete run, or contaminated artifact.
- Direct model completions are diagnostic sketches only; formal capable-candidate or weak-control evidence must use an agent scaffold such as OpenHands or Codex subagents.
- Provider balance, API auth, scaffold launch, or no-artifact 0/0 reports are `completion_failure` accounting evidence and must be excluded from functional pass-rate and model-order comparisons.
- Repeated weak-control provider failures should trigger a provider-health gate: after representative OpenHands traces and a direct minimal provider probe confirm account/auth/balance failure, stop launching more benchmark runs for that provider until the external state is verified.
- Product-natural enrichment has a stop condition: if a fresh capable agent remains high on both unit and system with a small gap after an enrichment such as MiniMarkdown workspace-v4, record below-gate/near-solved evidence instead of adding adjacent hidden rows on the same surface.
- Reference-identical candidate artifacts must be excluded from positive evidence unless provenance is repaired.
- MiniJinja-style future work should use environment/lifecycle invariants, not shallow lexer/parser/render checklists.

Validation command:

`py -3.11 C:\Users\12547\.codex\skills\.system\skill-creator\scripts\quick_validate.py <skill-dir>`

All three updated skills returned `Skill is valid!`.
