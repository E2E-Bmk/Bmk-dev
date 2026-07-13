# MiniTemplate Lifecycle V3 And Qwen Controls

Date: 2026-06-28

## MiniTemplate Redesign

Singer redesigned MiniTemplate from the old checklist packet into a MiniJinja lifecycle task centered on one shared `Environment`: loader/cache, filters/tests, globals, includes/imports, inheritance, macros, undefined behavior, whitespace, and autoescape.

Reference gate:

| Packet | Unit | System | Gap |
|---|---:|---:|---:|
| lifecycle v3 reference | 100.00% | 100.00% | 0.00pp |

Fresh candidates:

| Candidate | Unit | System | Gap | Notes |
|---|---:|---:|---:|---|
| Codex subagent v2-001 | 100.00% | 100.00% | 0.00pp | Solved lifecycle v3 |
| OpenHands + DeepSeek V4 v2-001 | 88.89% | 83.33% | 5.56pp | Scoreable artifact; full JSONL trace was not captured |
| OpenHands + Qwen 001 | 0.00% | 0.00% | 0.00pp | Weak control; no `minitemplate.py` artifact |

The first DeepSeek v2 score before fairness cleanup was 88.89% unit / 66.67% system, a raw 22.22pp gap. Archimedes judged it `revise`: `MTES004` depended on ambiguous imported-macro caller-context semantics, and `MTES006` repeated the malformed-block primitive from `MTEU017`.

Lifecycle v3 cleanup:

- PRD now says imported macros use environment globals/registries and caller-specific values should be passed as explicit macro arguments.
- `MTES004` passes caller prefix as an explicit macro argument.
- `MTES006` now uses a missing include during a template update rather than an unclosed `{% if %}` block.

After cleanup, the same DeepSeek artifact dropped to a 5.56pp gap, below the candidate gate. MiniTemplate is therefore not promoted.

## Qwen Controls

Additional OpenHands + Qwen controls were run with SiliconFlow through OpenHands, not direct completion.

| Task | Unit | System | Gap | Interpretation |
|---|---:|---:|---:|---|
| MiniKV | 94.44% | 100.00% | -5.56pp | One list primitive miss; system solved |
| MiniDynaconf | 54.55% | 25.00% | 29.55pp | Weak-model primitive/cascade failures dominate |
| MiniTemplate lifecycle v3 | 0.00% | 0.00% | 0.00pp | No artifact; tool-use/agent execution failure |

These controls support the methodological claim: weak-model failures calibrate difficulty, but low unit/low system or no-artifact failures are not compositional gap evidence.

## Decision

Keep core strong set unchanged:

- SQLite
- ZK
- MiniURLUtils

Do not promote MiniTemplate lifecycle v3, MiniKV, or MiniDynaconf based on this round.
