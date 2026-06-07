# MiniRedis Unit/System Requirement Map

Date: 2026-06-06

Public packet: `prd.md`

Rubric: `rubric.json`

## Public Requirements

| ID | Capability | Public packet section | Observable behavior |
| --- | --- | --- | --- |
| `REQ-feature-set` | Bounded 7-module feature set | Feature Set | String, list, set, hash ops; key mgmt; db mgmt; errors |
| `REQ-global-invariants` | Cross-feature data structure invariants | Global Invariants | Type determined by creator; type-restricted ops fail; DEL resets type; list order preserved; set dedup; hash field-value exact; EXPIRE/TTL semantics; KEYS excludes expired; DBSIZE counts live keys; FLUSHDB clears all types |
| `REQ-string-ops` | String key-value operations | `SET`, `GET`, `DEL`, `EXISTS` | SET stores; GET retrieves; DEL removes any type and returns count; EXISTS checks |
| `REQ-list-ops` | List data structure operations | `LPUSH`, `RPUSH`, `LPOP`, `RPOP`, `LRANGE`, `LLEN` | LPUSH prepends; RPUSH appends; LPOP/RPOP remove and return; LRANGE with +/- indices; LLEN returns length |
| `REQ-set-ops` | Set data structure operations | `SADD`, `SREM`, `SMEMBERS`, `SISMEMBER`, `SCARD` | SADD adds with dedup; SREM removes; SMEMBERS returns all; SISMEMBER checks; SCARD returns count |
| `REQ-hash-ops` | Hash data structure operations | `HSET`, `HGET`, `HDEL`, `HGETALL`, `HEXISTS` | HSET sets fields; HGET retrieves; HDEL removes; HGETALL returns all; HEXISTS checks |
| `REQ-key-mgmt` | Key management and expiry | `KEYS`, `TYPE`, `EXPIRE`, `TTL` | KEYS with glob pattern; TYPE returns type string; EXPIRE sets timeout; TTL reads remaining |
| `REQ-db-mgmt` | Database management | `FLUSHDB`, `DBSIZE` | FLUSHDB clears all keys; DBSIZE returns live count |
| `REQ-errors` | Error handling and atomicity | Error Behavior | Type mismatches fail non-zero; invalid syntax fails; failed commands preserve state |
| `REQ-unit-eval` | Unit testing definition | Evaluation Style | Unit cases test one module with direct command invocation |
| `REQ-system-eval` | System testing definition | Evaluation Style | System cases cross at least two modules and carry `system_dimension` labels |

## Unit Coverage

| Feature module | Unit tests | Requirement refs | Public basis |
| --- | --- | --- | --- |
| String operations | `MDRU001`, `MDRU002`, `MDRU003` | `REQ-string-ops` | SET/GET round-trip, DEL count, SET overwrite |
| List operations | `MDRU004`, `MDRU005`, `MDRU006`, `MDRU007` | `REQ-list-ops` | LPUSH prepend order, RPUSH append order, LPOP/LLEN, LRANGE negative indices |
| Set operations | `MDRU008`, `MDRU009`, `MDRU010` | `REQ-set-ops` | SADD/SMEMBERS, dedup/SREM/SISMEMBER, SCARD after mutations |
| Hash operations | `MDRU011`, `MDRU012`, `MDRU013` | `REQ-hash-ops` | HSET/HGET, multi-field/HDEL/HGETALL, HEXISTS |
| Key management | `MDRU014`, `MDRU015`, `MDRU016` | `REQ-key-mgmt` | TYPE for all types, KEYS with/without pattern, EXPIRE/TTL |
| DB management | `MDRU017` | `REQ-db-mgmt` | FLUSHDB clears all; DBSIZE reflects count; KEYS returns empty |
| Errors | `MDRU018` | `REQ-errors`, `REQ-list-ops` | LPOP on string fails non-zero |

Unit requirement coverage:

- `REQ-string-ops`: `MDRU001`, `MDRU002`, `MDRU003`
- `REQ-list-ops`: `MDRU004`, `MDRU005`, `MDRU006`, `MDRU007`, `MDRU018`
- `REQ-set-ops`: `MDRU008`, `MDRU009`, `MDRU010`
- `REQ-hash-ops`: `MDRU011`, `MDRU012`, `MDRU013`
- `REQ-key-mgmt`: `MDRU014`, `MDRU015`, `MDRU016`
- `REQ-db-mgmt`: `MDRU017`
- `REQ-errors`: `MDRU018`

## System Coverage

| Test | system_dimension | Crossed modules | Requirement refs | Public basis |
| --- | --- | --- | --- | --- |
| `MDRS001` | `cross_feature_dataflow` | string+list+set+hash → TYPE → GET/LRANGE/SMEMBERS/HGET | `REQ-string-ops`, `REQ-list-ops`, `REQ-set-ops`, `REQ-hash-ops`, `REQ-key-mgmt` | TYPE and data retrieval agree for all four type-creating commands |
| `MDRS002` | `cross_feature_dataflow` | hash → EXPIRE → TTL → HGET → HEXISTS | `REQ-hash-ops`, `REQ-key-mgmt` | Hash data accessible after EXPIRE; TTL reflects timeout |
| `MDRS003` | `state_accumulation` | list → LPUSH+RPUSH mixed → LRANGE → LPOP → RPOP | `REQ-list-ops` | Mixed push directions accumulate; pops reflect accumulated order |
| `MDRS004` | `state_accumulation` | set → SADD+SREM → SCARD → SMEMBERS → SISMEMBER | `REQ-set-ops` | Add/dedup/remove accumulate; all accessors agree |
| `MDRS005` | `global_invariant` | all-types → DBSIZE → KEYS → DEL → DBSIZE → KEYS → FLUSHDB | `REQ-string-ops`, `REQ-list-ops`, `REQ-set-ops`, `REQ-hash-ops`, `REQ-key-mgmt`, `REQ-db-mgmt` | DBSIZE == len(KEYS) after every mutation across all types |
| `MDRS006` | `global_invariant` | list → DEL → EXISTS → TYPE → SET(string) → TYPE → GET | `REQ-string-ops`, `REQ-list-ops`, `REQ-key-mgmt` | DEL resets type; same key name can be reused with different type |
| `MDRS007` | `error_atomicity` | string → failed RPUSH → GET → TYPE | `REQ-string-ops`, `REQ-list-ops`, `REQ-errors`, `REQ-key-mgmt` | RPUSH on string fails; original value and type preserved |
| `MDRS008` | `error_atomicity` | set → failed HSET → SCARD → TYPE → SMEMBERS | `REQ-set-ops`, `REQ-hash-ops`, `REQ-errors`, `REQ-key-mgmt` | HSET on set fails; cardinality, type, members preserved |
| `MDRS009` | `operation_order_sensitivity` | string → EXPIRE → TTL → SET → TTL → EXPIRE → TTL | `REQ-string-ops`, `REQ-key-mgmt` | SET after EXPIRE removes expiry; EXPIRE must be re-applied |
| `MDRS010` | `operation_order_sensitivity` | list → LPUSH→LPOP (LIFO) vs RPUSH→LPOP (FIFO) | `REQ-list-ops` | Push/pop direction order determines FIFO vs LIFO behavior |
| `MDRS011` | `boundary_crossing` | all-types → KEYS pattern → TYPE → DBSIZE → DEL → KEYS → DBSIZE | `REQ-string-ops`, `REQ-list-ops`, `REQ-set-ops`, `REQ-hash-ops`, `REQ-key-mgmt`, `REQ-db-mgmt` | Pattern filter, type check, count, and delete compose across all types |
| `MDRS012` | `boundary_crossing` | all-types → FLUSHDB → DBSIZE → KEYS → GET → LRANGE → SMEMBERS → HGETALL → TYPE | `REQ-string-ops`, `REQ-list-ops`, `REQ-set-ops`, `REQ-hash-ops`, `REQ-db-mgmt`, `REQ-key-mgmt` | After FLUSHDB, all accessors return nil/empty/none across all types |

System dimension coverage:

- `cross_feature_dataflow`: `MDRS001`, `MDRS002`
- `state_accumulation`: `MDRS003`, `MDRS004`
- `global_invariant`: `MDRS005`, `MDRS006`
- `error_atomicity`: `MDRS007`, `MDRS008`
- `operation_order_sensitivity`: `MDRS009`, `MDRS010`
- `boundary_crossing`: `MDRS011`, `MDRS012`

All 6 required system dimensions are covered with 2 tests each.

## Verification Targets

| Solution | Unit (target) | System (target) | Gap (target) |
| --- | ---: | ---: | ---: |
| Reference | 100.00% | 100.00% | 0.00pp |
| Candidate (expected) | 70-90% | 40-70% | 15-50pp |

Unit score target band: 70-90% (18 unit cases × weight 4 = 72 total). System gap target: ≥15pp below unit.

## Fairness Notes

- Expiry TTL checks use `step_stdout_in_range` to accommodate implementation variance in wall-clock TTL tracking. No actual time-passage tests are included.
- Type mismatch error stderr matching uses broad terms (`type`, `string`, `list`, `set`, `hash`, `wrong`, `error`) to accommodate diverse error message phrasing without unfairly penalizing any implementation.
- SET overwrites both value and type: this is standard Redis semantics documented in the public packet ("Overwrites any previous value and type").
- LPUSH/RPUSH on non-existent key creates a list: documented in the public packet ("If the key does not exist, create an empty list first").
- No persistence commands are required, keeping the scope focused on in-memory data structure operations and type enforcement.
- All four types (string, list, set, hash) have equal unit coverage (3-4 tests each), ensuring no type is tested only at the system level.
