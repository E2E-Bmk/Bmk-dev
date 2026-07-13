# Validation Summary

Status: `revised-after-independent-judge-verdict/fairness-cascade-trimmed`

| Agent | Unit | System | Gap | Judgment |
| --- | ---: | ---: | ---: | --- |
| Reference | 100.00% | 100.00% | 0.00pp | Reference gate passes |
| Codex subagent | 100.00% | 100.00% | 0.00pp | Reference-equivalent on this packet |
| OpenHands + DeepSeek V4 | 77.78% | 100.00% | -22.22pp | Unit/local misses only after cascade trimming |
| DeepSeek V4 direct | 94.44% | 85.71% | 8.73pp | One fair system projection miss, below target gap |

The revision centers MiniKV on one canonical type-tagged namespace. Unit tests cover isolated method contracts; system tests assert cross-view invariants after mixed valid operations, atomic invalid operations, delete/reuse/flush, expiry, mutable set/hash view mutation, and save/load round trips.

Fairness outcome: the prior invariant-v2 gap was dominated by repeated counter auto-creation and missing-key `lrange` roots. Those roots now remain in unit/local tests, while system failures require an independent downstream projection divergence. No stored candidate currently shows a fair unit-over-system gap above 15pp.
