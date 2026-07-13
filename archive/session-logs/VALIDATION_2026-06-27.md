# Validation Run 2026-06-27

## Protocol

This run followed the unit/system gap design manual:

- Reference-compatible implementation must score 100.00% unit and 100.00% system.
- Candidate gate requires at least one candidate with `unit > system` and gap >= 15pp.
- Failures are interpreted only after auditing evaluator defects and cascade roots.

Two candidate conditions were used:

- Fresh Codex subagent, seeing only the public PRD and writing to `solution-codex-subagent-001`.
- OpenHands CLI headless with `openai/deepseek-v4-pro`, seeing only the public PRD and writing to `solution-openhands-deepseek-v4-pro-001`.

A prior direct DeepSeek API generation was discarded as formal evidence because it was not an OpenHands agent loop.

## Results

| Task | Reference Unit | Reference System | Codex Unit | Codex System | Codex Gap | OpenHands Unit | OpenHands System | OpenHands Gap | Judgment |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| MiniRedis | 100.00% | 100.00% | 100.00% | 100.00% | 0.00pp | 88.89% | 83.33% | 5.56pp | No gap observed |
| MiniKV | 100.00% | 100.00% | 100.00% | 100.00% | 0.00pp | 77.78% | 83.33% | -5.56pp | No gap observed |
| MiniTemplate | 100.00% | 100.00% | 100.00% | 100.00% | 0.00pp | 100.00% | 100.00% | 0.00pp | No gap observed |
| MiniDynaconf | 100.00% | 100.00% | 100.00% | 100.00% | 0.00pp | 38.89% | 25.00% | 13.89pp | No gap observed under strict gate |
| MiniPackaging | 100.00% | 100.00% | 83.33% | 91.67% | -8.33pp | 72.22% | 91.67% | -19.44pp | No gap observed |
| MiniMarkdown | 100.00% | 100.00% | 50.00% | 66.67% | -16.67pp | 27.78% | 33.33% | -5.56pp | No gap observed |

## Audit Notes

- MiniRedis raw OpenHands failures initially included evaluator defects in TTL/SADD expectations and batch expected-error handling. After audit, the remaining failures are unit-rooted LPUSH ordering and KEYS glob behavior, with associated system failures classified as cascade.
- MiniKV had one rubric defect in the expected `kv_flush()` count after lazy expiry; after audit, the remaining OpenHands failures are feature-level counter/list/persistence issues.
- MiniTemplate is solved completely by both candidate conditions.
- MiniDynaconf was constructed during this run and passed Reference Gate after rubric/reference calibration. OpenHands produced the closest candidate signal, but 13.89pp is below the configured 15pp gate and most failures have feature-level roots.
- MiniPackaging was constructed during this run and passed Reference Gate. Both agents scored higher on system than unit tests, so it does not exhibit the target unit/system gap.
- MiniMarkdown was constructed during this run and passed Reference Gate. Both agents failed many feature-level token/API behaviors; observed system scores were higher than unit scores, so it is not compositional-gap evidence.

## Conclusion

The six newly validated candidates are now validated as `candidate/no-gap-observed`. They should not be promoted to `core strong` in their current form. The systematic unit/system gap remains supported by the existing core tasks (SQLite, ZK, MiniURLUtils), while this scale-out round documents which candidate designs did not reproduce the gap under fresh Codex subagent and OpenHands + DeepSeek V4 Pro agent conditions.
