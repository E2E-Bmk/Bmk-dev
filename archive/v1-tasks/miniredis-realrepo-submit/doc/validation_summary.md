# Validation Summary

Status: `candidate/no-fair-gap-after-fairness-revision`

| Agent | Unit | System | Gap | Judgment |
| --- | ---: | ---: | ---: | --- |
| Reference-compatible | 100.00% | 100.00% | 0.00pp | Reference gate passes on invariant v3 |
| Codex subagent | 100.00% | 100.00% | 0.00pp | Near-reference candidate remains solved |
| OpenHands + DeepSeek V4 | 80.00% | 100.00% | -20.00pp | Prior gap removed after parser, quoting, glob, and arity roots moved to unit/interface checks |
| Direct DeepSeek V4 | 65.00% | 0.00% | 65.00pp | Too many feature-level hash/type/display failures to use as clean compositional evidence |

Invariant v3 keeps shell parsing, quoted glob patterns, invalid arity, invalid numeric syntax, and display syntax in unit/interface coverage. System scoring now avoids quoted arguments and pattern fixtures, and it only uses expected errors for wrong-type operations whose downstream value/type/TTL/KEYS/DBSIZE projections must remain consistent.

Fair gap verdict: no fair unit-over-system gap remains for the strongest stored candidate. The task should be marked likely solved for this candidate population unless deeper natural MiniRedis lifecycle scope is added.
