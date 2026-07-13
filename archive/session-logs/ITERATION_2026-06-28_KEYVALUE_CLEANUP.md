# Key-Value Task Cleanup Iteration

Date: 2026-06-28

## Scope

This iteration applied the gap-skill loop to the two key-value candidates:

- `miniredis-realrepo-submit`
- `minikv-realrepo-submit`

Both tasks were previously classified as `candidate/no-gap-observed` and suspected to be checklist-like. The goal was to redesign their system tests around a shared type-tagged namespace and then judge whether any observed gap was fair.

## Qwen Control Note

The next model-control condition should include Qwen via OpenHands only, not direct completion. The intended ordering is:

`Codex > OpenHands + DeepSeek V4 > OpenHands + Qwen`

Do not store provider API keys in benchmark reports. Use an environment/configured OpenHands credential at runtime and write outputs to separate `solution-openhands-qwen-*` directories.

## MiniRedis

### Invariant-v2 Redesign

The first redesign strengthened system cases around one canonical key namespace projected through:

- `KEYS`
- `TYPE`
- value readers
- `TTL`
- `DBSIZE`
- expiry
- deletion
- failed writes
- batch-visible state

Scores:

| Implementation | Unit | System | Gap |
|---|---:|---:|---:|
| reference | 100.00% | 100.00% | 0.00pp |
| codex-subagent-001 | 100.00% | 100.00% | 0.00pp |
| openhands-deepseek-v4-pro-001 | 88.89% | 70.00% | 18.89pp |

Judge verdict: `revise`.

Reason:

- The gap was dominated by CLI parsing/quoting and strict arity feature roots.
- `parse_line()` used plain splitting, so quoted values and quoted glob patterns cascaded into system failures.
- Invalid `SET key value extra` was accepted and produced an atomicity-looking failure, but the root was local arity validation.
- The candidate passed most persuasive shared-namespace cases.

### Invariant-v3 Fairness Cleanup

The second revision moved shell quoting, glob parsing, invalid arity, invalid numeric syntax, and list-order primitive behavior into unit/interface rows. System fixtures no longer rely on whitespace, `*`, or `?` command-line parser behavior.

Current scores:

| Implementation | Unit | System | Gap |
|---|---:|---:|---:|
| reference | 100.00% | 100.00% | 0.00pp |
| codex-subagent-001 | 100.00% | 100.00% | 0.00pp |
| openhands-deepseek-v4-pro-001 | 80.00% | 100.00% | -20.00pp |

Final judge verdict: `solved` for the invariant-v3 unit/system-gap objective.

Conclusion:

- Do not promote MiniRedis as gap evidence.
- Stored candidates satisfy the fair shared-namespace system layer.
- Future work requires product-natural enrichment, not reintroducing parser/glob/formatting cascades.

## MiniKV

### Invariant-v2 Redesign

The first redesign strengthened system cases around one canonical type-tagged namespace in the Python class API, including:

- direct reads
- existence/delete/flush
- wrong-type behavior
- expiry
- persistence save/load
- counters/list/set/hash projections
- mutable returned set/dict views
- round-trip persistence

Scores:

| Implementation | Unit | System | Gap |
|---|---:|---:|---:|
| reference | 100.00% | 100.00% | 0.00pp |
| codex-subagent-001 | 100.00% | 100.00% | 0.00pp |
| openhands-deepseek-v4-pro-001 | 77.78% | 57.14% | 20.63pp |
| direct-deepseek-v4-pro-001 | 94.44% | 71.43% | 23.02pp |

Judge verdict: `revise`.

Reason:

- OpenHands system loss was dominated by two already-visible unit roots:
  - `kv_incr` / `kv_decr` created `0` and returned `0` instead of applying the first increment/decrement.
  - missing-key `lrange` raised instead of returning `[]`.
- The candidate otherwise passed wrong-type atomicity, expiry reuse, bulk typed projection, mutable set/hash view agreement, and direct/type-specific projections.

### Fairness Cleanup

The second revision kept counter auto-create and missing-key `lrange` in unit/local tests, removed repeated system dependence on those roots, pre-seeded counters before system increments, and rewrote delete/flush cases around fresh type reuse and projection agreement.

Current scores:

| Implementation | Unit | System | Gap |
|---|---:|---:|---:|
| reference | 100.00% | 100.00% | 0.00pp |
| codex-subagent-001 | 100.00% | 100.00% | 0.00pp |
| openhands-deepseek-v4-pro-001 | 77.78% | 100.00% | -22.22pp |
| direct-deepseek-v4-pro-001 | 94.44% | 85.71% | 8.73pp |

Final judge verdict: `solved` for current gap-benchmark purposes.

Conclusion:

- Do not promote MiniKV as gap evidence.
- The remaining OpenHands failures are local feature failures.
- The direct DeepSeek `kv_mset` typed-projection miss is meaningful but below the 15pp gate and is not formal OpenHands evidence.

## Skill Feedback

`gap-invariant-task-builder` was updated during this loop to add a CLI-specific warning:

- Keep shell parsing, quoting, arity validation, and display syntax in unit or low-weight interface cases unless downstream state views diverge after otherwise valid commands.
- Do not let one command-line parser root dominate several system cases.

This update complements the earlier rule not to count one primitive identity/parsing/serialization defect across several system rows unless downstream projections actually diverge.

## Current Decision

No new `core strong` task was accepted.

Both key-value candidates are now classified as solved-after-cascade-cleanup for the stored candidate population. Their fair system layers are useful negative evidence: compact key-value namespace tasks are too directly solvable unless product scope is materially enriched.

Next loop:

- Add OpenHands + Qwen as a weaker-model control condition.
- Prefer new or enriched lifecycle-heavy tasks over further tuning of MiniRedis/MiniKV.
- If a future numeric gap appears, send it to a fairness judge before promotion.
