# Validation Summary

Status: `redesigned/lifecycle-v3-no-gap-observed`

| Packet | Agent | Unit | System | Gap | Judgment |
| --- | --- | ---: | ---: | ---: | --- |
| lifecycle v2 | Reference-compatible | 100.00% | 100.00% | 0.00pp | Reference gate passes |
| lifecycle v3 | Reference-compatible | 100.00% | 100.00% | 0.00pp | Reference gate passes after fairness cleanup |
| lifecycle v3 | Codex subagent v2-001 | 100.00% | 100.00% | 0.00pp | Solved; no candidate gap |
| lifecycle v3 | OpenHands + DeepSeek V4 v2-001 | 88.89% | 83.33% | 5.56pp | No candidate gate; scoreable artifact with incomplete trace |
| lifecycle v3 | OpenHands + Qwen 001 | 0.00% | 0.00% | 0.00pp | Weak control; no artifact was written |
| checklist v1 | Codex subagent | 100.00% | 100.00% | 0.00pp | Historical only; old packet was too direct |
| checklist v1 | OpenHands + DeepSeek V4 | 100.00% | 100.00% | 0.00pp | Historical only; old packet was too direct |

The MiniTemplate task has been redesigned into a MiniJinja lifecycle benchmark. The shared fact source is `Environment`; system rows now assert consistency across loader/cache, inherited blocks, includes/imports, macros, filter/test registries, globals, undefined behavior, whitespace trim markers, and autoescape policy.

Reference command:

```powershell
py -3.11 tools\score_unit_system.py task\minitemplate-realrepo-submit\rubric.json --solution-dir runs\minitemplate-realrepo-submit\solution-reference --timeout 10 --json-out task\minitemplate-realrepo-submit\doc\score_reports\score_report_reference_unit_system_v2.json
```

Reference result: 30 / 30 cases, weighted score 168 / 168, unit 100.00%, system 100.00%.

Fairness cleanup note: an initial OpenHands + DeepSeek V4 v2 score showed 88.89% unit / 66.67% system, but an independent judge classified one system row as ambiguous macro caller-context semantics and one as a cascade from malformed block parsing. Lifecycle v3 clarifies imported macro scoping and replaces the cascade-prone error-atomicity case. After cleanup, the same scoreable DeepSeek artifact is 88.89% unit / 83.33% system, a 5.56pp gap, below the candidate gate.

Decision: do not promote MiniTemplate. The lifecycle redesign is product-natural and the reference passes, but the current Codex candidate solves it and the current OpenHands + DeepSeek evidence does not show a fair 15pp+ unit-over-system gap.
