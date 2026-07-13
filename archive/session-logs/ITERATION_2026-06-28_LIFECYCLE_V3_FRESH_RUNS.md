# Lifecycle V3 Fresh Runs

Date: 2026-06-28

## Scope

This iteration continued the gap loop after the Qwen provider-balance rerun. Two task-builder subagents redesigned negative/near-solved tasks around stronger shared-fact-source invariants, then fresh Codex subagent and OpenHands + DeepSeek V4 Pro candidates were scored.

## MiniDynaconf Lifecycle V3

Changed by subagent:

- `task/minidynaconf-realrepo-001/prd.md`
- `task/minidynaconf-realrepo-001/rubric.json`
- `task/minidynaconf-realrepo-001/doc/requirement_map.md`
- `task/minidynaconf-realrepo-001/doc/redesign_note.md`
- `runs/minidynaconf-realrepo-001/solution-reference/minidynaconf.py`

Shared fact source:

- One canonical nested, case-insensitive configuration tree built from durable sources plus runtime overlays and deletion tombstones.
- Projections: dot access, item access, attr proxy, `exists`, validators/defaults, `as_dict`, `export`, JSON reimport, `load_file`, `load_env_file`, `import_dict`, `delete`, `reload`, and `configure`.

Scores:

| Candidate | Unit | System | Gap | Report |
|---|---:|---:|---:|---|
| Reference lifecycle-v3 | 100.00% | 100.00% | 0.00pp | `task/minidynaconf-realrepo-001/doc/score_reports/score_report_reference_lifecycle_v3_20260628.json` |
| Codex subagent lifecycle-v3-001 | 75.00% | 80.00% | -5.00pp | `task/minidynaconf-realrepo-001/doc/score_reports/score_report_codex_subagent_lifecycle_v3_001_20260628.json` |
| OpenHands + DeepSeek V4 Pro lifecycle-v3-001 | 25.00% | 0.00% | 25.00pp | `task/minidynaconf-realrepo-001/doc/score_reports/score_report_openhands_deepseek_v4_pro_lifecycle_v3_001_20260628.json` |

OpenHands trace:

- `runs/minidynaconf-realrepo-001/openhands_deepseek_v4_pro_lifecycle_v3_001.log`
- Conversation: `88074842-561b-481d-978d-ff08fcddb263`
- The process exited nonzero because the stop hook failed on Windows; the agent finished and produced a scoreable artifact.

Judge verdict:

- `reject`
- The 25pp OpenHands numeric gap is primitive/cascade-dominated.
- Dominant roots: nested dict attribute proxy and validator-view primitives fail in unit rows and then cap every system row.
- Real lifecycle defects exist in source-priority replay and failed-configure rollback, but they are not the main scored loss.

Decision:

- Do not accept MiniDynaconf v3 as gap evidence.
- Next fair move would require either a candidate that passes nested attr/validator-view primitives before system scoring, or a redesign that isolates those primitives more cleanly before lifecycle rows.

## MiniMarkdown Canonical Tree V3

Changed by subagent:

- `task/minimarkdown-realrepo-001/prd.md`
- `task/minimarkdown-realrepo-001/rubric.json`
- `task/minimarkdown-realrepo-001/doc/requirement_map.md`
- `task/minimarkdown-realrepo-001/doc/redesign_note.md`
- `runs/minimarkdown-realrepo-001/solution-reference/minimarkdown.py`

Shared fact source:

- `parse(text)` / `tokens(text)` are the canonical token tree.
- Projections: AST rendering, HTML rendering, TOC, `walk(tokens)`, plugin metadata, and `render(tokens, renderer=...)` replay/idempotence.

Scores:

| Candidate | Unit | System | Gap | Report |
|---|---:|---:|---:|---|
| Reference canonical-tree-v3 | 100.00% | 100.00% | 0.00pp | `task/minimarkdown-realrepo-001/doc/score_reports/score_report_reference_canonical_tree_v3_20260628.json` |
| Codex subagent canonical-tree-v3-001 | 100.00% | 91.67% | 8.33pp | `task/minimarkdown-realrepo-001/doc/score_reports/score_report_codex_subagent_canonical_tree_v3_001_20260628.json` |
| OpenHands + DeepSeek V4 Pro canonical-tree-v3-001 | 88.89% | 83.33% | 5.56pp | `task/minimarkdown-realrepo-001/doc/score_reports/score_report_openhands_deepseek_v4_pro_canonical_tree_v3_001_20260628.json` |

OpenHands trace:

- `runs/minimarkdown-realrepo-001/openhands_deepseek_v4_pro_canonical_tree_v3_001.log`
- Conversation: `be43b732-fa9b-49fe-825c-ec0e198f70b5`
- The process exited nonzero because the stop hook failed on Windows; the agent finished and produced a scoreable artifact.

Judge verdict:

- `solved / near-solved`
- No gate-level unit > system gap.
- Codex has one narrow `MMS010` loose-list metadata miss.
- DeepSeek failures are small local feature/order misses: blockquote paragraph text, malformed strong recovery, table boundary ordering, and loose-list state.
- `MMS010` has a mild exact public-key risk around the literal `loose` field; avoid using that key alone to manufacture a gap.

Decision:

- Do not accept MiniMarkdown v3 as gap evidence.
- Treat it as near-solved for current agents unless materially enriched beyond parser/render/plugin projection, such as multi-document indexing, incremental reference maintenance, or stronger semantic plugin lifecycle.

## Qwen Control Status

The corrected MiniPackaging Qwen rerun used OpenHands `--headless --json -f ... --override-with-envs` and reached model initialization, but the SiliconFlow endpoint returned `account balance is insufficient` before action selection.

After another Qwen credential was provided, MiniMarkdown rerun 008 was launched through the same OpenHands path with `LLM_API_KEY` and the SiliconFlow OpenAI-compatible base URL. The run initialized conversation `bbf0cde6-d764-4045-b55d-1fde97acf214` and reached the first model call, but the provider again returned `account balance is insufficient` before any file or terminal action. Rerun 007 is retained separately as a launch-config failure caused by missing `LLM_API_KEY`.

After the later `sk-vit...` SiliconFlow credential was supplied, MiniMarkdown rerun 009 again used OpenHands `--headless --json -f ... --override-with-envs` with `LLM_API_KEY`, `LLM_MODEL=openai/Qwen/Qwen3.5-397B-A17B`, and the SiliconFlow base URL. OpenHands initialized conversation `e861c791-6481-4675-a5a7-9d7c27a817f6` but the provider returned `account balance is insufficient` before action selection. Rerun 010 repeated the same task with a clean temporary OpenHands home/persistence directory to reduce skill-prompt overhead; it initialized conversation `5ee1072e-5c40-475e-ace6-c9ba7af8d97b` and hit the same provider error. A minimal 1-token SiliconFlow probe also returned HTTP 403 / `code=30001`, so these are credential/account failures, not benchmark model scores.

Trace and accounting report:

- `runs/minipackaging-realrepo-001/openhands_qwen_resolve_metadata_v3_002.log`
- `task/minipackaging-realrepo-001/doc/score_reports/score_report_openhands_qwen_resolve_metadata_v3_002_noartifact_20260628.json`
- `runs/minimarkdown-realrepo-001/openhands_qwen_rerun_007.log`
- `runs/minimarkdown-realrepo-001/openhands_qwen_rerun_008.log`
- `runs/minimarkdown-realrepo-001/openhands_qwen_rerun_009.log`
- `runs/minimarkdown-realrepo-001/openhands_qwen_rerun_010_cleanhome.log`
- `task/minimarkdown-realrepo-001/doc/score_reports/score_report_openhands_qwen_rerun_007_noartifact_20260628.json`
- `task/minimarkdown-realrepo-001/doc/score_reports/score_report_openhands_qwen_rerun_008_noartifact_20260628.json`
- `task/minimarkdown-realrepo-001/doc/score_reports/score_report_openhands_qwen_rerun_009_noartifact_20260628.json`
- `task/minimarkdown-realrepo-001/doc/score_reports/score_report_openhands_qwen_rerun_010_cleanhome_noartifact_20260628.json`

Decision:

- This is provider/no-artifact evidence only, not a Qwen functional score.

## Cross-Task Lesson

The fresh v3 runs reinforce the earlier diagnosis:

- A numeric unit-system gap is not enough when system loss is capped by a public primitive.
- A stronger public invariant helps, but capable agents can still solve compact domains once the canonical fact source is obvious.
- The next accepted tasks should add product-natural lifecycle scope where multiple public consumers must stay consistent over time, not just more one-shot projection fields.

## Skill Feedback

Updated and validated:

- `C:\Users\12547\.codex\skills\gap-invariant-task-builder`
- `C:\Users\12547\.codex\skills\gap-benchmark-iteration`
- `C:\Users\12547\.codex\skills\gap-fairness-judge`

Changes added from this round:

- Add a primitive-readiness gate before accepting lifecycle/system evidence. If nested attribute proxies, validator views, token metadata, parser recovery, or similar public primitives fail first, system loss must be classified as cascade unless residual lifecycle loss remains after clustering.
- Treat low-unit, high-gap runs as suspect. A 15pp+ number is not enough when system rows crash or short-circuit before reaching the intended invariant.
- Treat near-reference candidates as solved/near-solved when remaining misses are one public metadata bit or exact field shape while semantic projections agree. Do not add adjacent exact-key checks merely to create separation.

Validation command:

`py -3.11 C:\Users\12547\.codex\skills\.system\skill-creator\scripts\quick_validate.py <skill-dir>`

All three updated skills returned `Skill is valid!`.
