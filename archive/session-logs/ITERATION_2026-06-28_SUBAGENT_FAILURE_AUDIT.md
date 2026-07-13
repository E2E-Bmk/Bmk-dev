# Subagent Failure Audit

Date: 2026-06-28

## Scope

One read-only subagent was assigned to each active non-core candidate:

- MiniRedis
- MiniKV
- MiniDynaconf
- MiniPackaging
- MiniMarkdown
- MiniTemplate / MiniJinja lifecycle

Each subagent inspected task PRDs, rubrics, requirement maps, score reports, candidate implementations, and OpenHands logs where available. No subagent edited files.

## Verdict Matrix

| Task | Subagent verdict | Main root | Action |
|---|---|---|---|
| MiniRedis | No clean compositional failure remains | LPUSH, glob/quoting, arity, expiry return-code primitives; fair v3 makes OpenHands DeepSeek system 100% | Retire or add deeper lifecycle invariants |
| MiniKV | One real direct-only shared-source miss, but formal OpenHands candidates solve system | `kv_mset` type projection is meaningful in direct DeepSeek only; OpenHands failures are counter/list primitives | Keep as design seed, not accepted |
| MiniDynaconf | Retire after lifecycle-v3 audit | v3 has the right canonical-tree invariant, but Codex system is higher than unit and DeepSeek/Qwen losses are primitive-capped | Keep as diagnostic/weak-control evidence, not accepted gap |
| MiniPackaging | Fairness cleanup removes apparent gap; usable candidates pass system | Requirement/version/marker primitive defects leak into system; resolver layer under-discriminates | Retire or enrich dependency closure |
| MiniMarkdown | Retire after canonical-tree-v3 audit | v3 tests the right parse-tree projection invariant, but Codex is 100/91.67 and DeepSeek is 88.89/83.33; remaining misses are narrow metadata/parser edges | Keep as near-solved negative evidence |
| MiniTemplate | Lifecycle framing better than v1, but not a strong gap | Codex solves; DeepSeek residual is parser/syntax plus macro autoescape projection; Qwen provider/no-artifact | Do not promote; enrich with sharper environment lifecycle |

## Cross-Task Findings

The user's high-level diagnosis is supported:

> A fair unit/system gap requires a system invariant that cannot be satisfied by independently completing each feature. Several APIs or views must share one fact source and maintain consistent projections.

The rejected candidates failed in four recurring ways:

1. **System rows repeated primitives.** MiniRedis, MiniKV v2, MiniPackaging, and parts of MiniDynaconf counted local parser/API roots as system loss.
2. **Fact source was too obvious.** MiniRedis and MiniKV collapse to a single typed dictionary; capable agents naturally implement that architecture and pass system rows.
3. **Unit or public contract dominated before composition.** MiniDynaconf and MiniMarkdown failures often fail PathLike/cast/token schema/API rows before the intended cross-view invariant is isolated.
4. **No-artifact runs are not model evidence.** MiniMarkdown and MiniTemplate Qwen reruns reached SiliconFlow but failed with account balance errors before action selection. These are provider/completion failures only.

## Qwen Rerun Evidence

New SiliconFlow Qwen reruns were attempted through OpenHands only:

- `runs/minimarkdown-realrepo-001/openhands_qwen_rerun_001_utf8.log`
- `runs/minitemplate-realrepo-submit/openhands_qwen_rerun_001_utf8.log`

Both failed before action selection with:

`litellm.APIError: APIError: OpenAIException - Sorry, your account balance is insufficient`

After receiving the later SiliconFlow Qwen credential, a third MiniMarkdown OpenHands rerun was attempted with the same model condition (`openai/Qwen/Qwen3.5-397B-A17B`). It also failed before action selection with the same balance error. Conversation id: `0f90f7b0-558a-4bce-85e3-61248db25443`. Trace:

- `runs/minimarkdown-realrepo-001/openhands_qwen_rerun_003.log`

A later MiniMarkdown OpenHands rerun 006 with the same Qwen model condition again initialized the agent and failed before action selection with `account balance is insufficient`. Conversation id: `6f632032-dae0-48f8-8972-714660fd45a3`. Trace:

- `runs/minimarkdown-realrepo-001/openhands_qwen_rerun_006.log`

No solution artifacts were produced. Mechanical no-artifact reports were written for accounting:

- `task/minimarkdown-realrepo-001/doc/score_reports/score_report_openhands_qwen_rerun_001_noartifact_20260628.json`
- `task/minitemplate-realrepo-submit/doc/score_reports/score_report_openhands_qwen_rerun_001_noartifact_20260628.json`
- `task/minimarkdown-realrepo-001/doc/score_reports/score_report_openhands_qwen_rerun_003_noartifact_20260628.json`
- `task/minimarkdown-realrepo-001/doc/score_reports/score_report_openhands_qwen_rerun_006_noartifact_20260628.json`

## Recommended Next Task Construction Moves

1. **MiniDynaconf:** retire the current lifecycle-v3 packet as an accepted-gap candidate. It already uses a canonical config tree and multi-projection lifecycle rows; strong agents do not show unit > system, while weaker agents fail nested projection, PathLike, type-cast, and loader primitives first.
2. **MiniMarkdown:** retire the current canonical-tree-v3 packet as an accepted-gap candidate. Its system layer is now principled, but strong agents are near-solved and remaining misses are loose-list metadata or local block-boundary/parser behavior.
3. **MiniPackaging:** enrich only if adding real dependency closure: equivalent requirements must affect merged constraints, extras propagation, exclusion recovery, and reverse projections. Do not add more parser rows.
4. **MiniRedis/MiniKV:** retire unless adding natural lifecycle depth beyond one in-memory typed dictionary, such as persistence/recovery, concurrent snapshots, multi-key atomic operations, or delayed expiry/index invalidation.
5. **MiniTemplate:** do not promote lifecycle v3. If continued, test cache invalidation, registry/global mutation after compilation, failed reload atomicity, non-leaky repeated renders, and explicit macro safe-string policy without ambiguous caller scope.

## Current Count

`score_summary.csv` currently contains 10 task groups:

- Core strong: SQLite, ZK, MiniURLUtils.
- Negative / no-gap / near-solved candidates: MiniRedis, MiniKV, MiniTemplate, MiniDynaconf, MiniPackaging, MiniMarkdown, MiniBitcask.

Only the three core strong tasks satisfy the reference, candidate, and fairness gates.

## Final Supplemental Audit

Two additional read-only subagents were launched after balance recovery to re-audit the last open redesign candidates:

- MiniMarkdown canonical-tree-v3: verdict `retire`. Reference is 100/100, Codex subagent is 100.00% unit / 91.67% system, and OpenHands DeepSeek V4 is 88.89% unit / 83.33% system. The system layer is correctly framed around one canonical parse tree projecting into AST, HTML, TOC, walk, plugin metadata, and renderer replay, but the remaining Codex loss is only the `loose` list-item metadata bit in `MMS010`. Qwen remains no-artifact/provider evidence for this packet.
- MiniDynaconf lifecycle-v3: verdict `retire`. Reference is 100/100, Codex subagent is 75.00% unit / 80.00% system, and OpenHands DeepSeek V4 is 25.00% unit / 0.00% system. The PRD now tests a canonical configuration tree projected through attr/item/get/exists/export/reload/validator views, but DeepSeek/Qwen failures are dominated by nested dict projection, PathLike, cast, and loader primitives. Codex's one system miss is a narrow export/reload validator boundary, not a fair gap.
- MiniBitcask: verdict updated to `solved / retire` after fresh OpenHands DeepSeek evidence. Reference, Codex, and OpenHands DeepSeek all score 100/100. The OpenHands trace shows public-packet-only provenance, the implementation is not reference-identical, no hacking or contamination signal was found, and further separation would require distorted/private or out-of-scope checks.
