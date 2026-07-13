# Requirement Map

| Requirement | Public packet section | Rubric IDs |
| --- | --- | --- |
| `REQ-string-ops` | String Operations | `MDRU001`, `MDRU002`, `MDRU003`, `MDRS001`, `MDRS002`, `MDRS003`, `MDRS004`, `MDRS006`, `MDRS007`, `MDRS008`, `MDRS010`, `MDRS011`, `MDRS012` |
| `REQ-list-ops` | List Operations | `MDRU004`, `MDRU005`, `MDRU006`, `MDRU007`, `MDRU018`, `MDRS001`, `MDRS002`, `MDRS003`, `MDRS004`, `MDRS006`, `MDRS007`, `MDRS008`, `MDRS010`, `MDRS011`, `MDRS012` |
| `REQ-set-ops` | Set Operations | `MDRU008`, `MDRU009`, `MDRU010`, `MDRS001`, `MDRS002`, `MDRS003`, `MDRS008`, `MDRS010`, `MDRS012` |
| `REQ-hash-ops` | Hash Operations | `MDRU011`, `MDRU012`, `MDRU013`, `MDRS001`, `MDRS002`, `MDRS003`, `MDRS006`, `MDRS008`, `MDRS010`, `MDRS011`, `MDRS012` |
| `REQ-key-mgmt` | Key Management and Global Invariants | `MDRU014`, `MDRU015`, `MDRU016`, `MDRU019`, `MDRS001`, `MDRS002`, `MDRS003`, `MDRS004`, `MDRS006`, `MDRS007`, `MDRS008`, `MDRS010`, `MDRS011`, `MDRS012` |
| `REQ-db-mgmt` | Database Management | `MDRU017`, `MDRS001`, `MDRS002`, `MDRS003`, `MDRS004`, `MDRS006`, `MDRS007`, `MDRS008`, `MDRS010`, `MDRS011`, `MDRS012` |
| `REQ-errors` | Error Behavior | `MDRU018`, `MDRU020`, `MDRS004`, `MDRS006`, `MDRS007`, `MDRS011` |
| `REQ-interface` | Overview and Evaluation Style | `MDRU019`, `MDRU020` |

## System Case Intent

| Rubric ID | Cross-feature contract |
| --- | --- |
| `MDRS001` | Mixed type creation with simple tokens must project consistently through key listing, type reads, value reads, DBSIZE, and TTL. |
| `MDRS002` | DEL must immediately remove list/hash keys from every view and allow type reuse. |
| `MDRS003` | Immediate expiry must make all four types invisible across live-key and type-specific views. |
| `MDRS004` | A wrong-type list write against a string must preserve value, type, listing, DBSIZE, and TTL. |
| `MDRS006` | Wrong-type operations across existing string/hash/list keys must preserve values, types, listing, DBSIZE, and TTL. |
| `MDRS007` | SET over an expiring typed key must reset value, type, and TTL, then remain atomic under a wrong-type read. |
| `MDRS008` | Mixed DEL/LPOP/SREM/HDEL mutations must leave all remaining projections in agreement. |
| `MDRS010` | Unpatterned namespace views must agree with type-specific reads after mixed create/delete/expiry. |
| `MDRS011` | Wrong-type writes must not shadow existing string/hash keys or change namespace projections. |
| `MDRS012` | FLUSHDB must clear all value/type/expiry projections and permit type reuse. |

## Unit/Interface Case Intent

| Rubric ID | Local contract |
| --- | --- |
| `MDRU019` | Shell-like batch splitting preserves quoted values and quoted glob patterns. |
| `MDRU020` | Invalid arity and invalid numeric arguments fail without partial mutation. |

## Validation Notes

Previous reference-compatible implementation: 100.00% unit, 100.00% system.

Previous Codex subagent: 100.00% unit, 100.00% system, 0.00pp gap.

Previous OpenHands + DeepSeek V4: 88.89% unit, 83.33% system, 5.56pp gap. Remaining system failures were explained by unit-level LPUSH ordering and KEYS glob behavior, so the system layer was redesigned around projection consistency over a shared namespace.

Invariant v2 reference-compatible implementation: 100.00% unit, 100.00% system.

Invariant v2 Codex subagent: 100.00% unit, 100.00% system, 0.00pp gap.

Invariant v2 OpenHands + DeepSeek V4: 88.89% unit, 70.00% system, 18.89pp gap. System failures are grouped by shell-like batch parsing with quoted values, invalid write atomicity, and one glob namespace projection case.

Invariant v2 direct DeepSeek V4: 66.67% unit, 0.00% system, 66.67pp gap, dominated by feature-level hash/type-output defects.

Invariant v3 fairness revision moves shell quoting, glob argument parsing, invalid arity, and invalid numeric syntax into unit/interface cases. System cases avoid quoted arguments and pattern fixtures, and only use wrong-type failures as expected errors.

Invariant v3 reference-compatible implementation: 100.00% unit, 100.00% system.

Invariant v3 Codex subagent: 100.00% unit, 100.00% system, 0.00pp gap.

Invariant v3 OpenHands + DeepSeek V4: 80.00% unit, 100.00% system, -20.00pp gap. The prior system gap no longer remains after cascade trimming.

Invariant v3 direct DeepSeek V4: 65.00% unit, 0.00% system, 65.00pp gap, dominated by feature-level hash/type/display defects rather than clean compositional evidence.
