# MiniKV Unit/System Requirement Map

Date: 2026-06-06

Public packet: `prd.md`

Rubric: `rubric.json`

## Public Requirements

| ID | Capability | Public packet section | Observable behavior |
| --- | --- | --- | --- |
| `REQ-feature-set` | Bounded 7-module feature set | Feature Set | String KV, bulk ops, integer ops, expiry, key enum, persistence, errors |
| `REQ-global-invariants` | Cross-feature key-value invariants | Global Invariants | GET/SET consistency, EXISTS/DELETE correctness, type coherence, expiry semantics, persistence fidelity, DBSIZE/KEYS agreement |
| `REQ-string-kv` | String key-value operations | `SET`, `GET`, `EXISTS`, `DELETE` | SET stores, GET retrieves, EXISTS checks, DELETE removes and returns count |
| `REQ-bulk-ops` | Bulk operations | `MSET`, `MGET` | MSET stores multiple keys; MGET returns JSON array with null for missing |
| `REQ-integer-ops` | Integer counter operations | `INCR`, `DECR` | Increment/decrement, auto-create at 0, fail on non-integer type |
| `REQ-expiry` | Key expiry | `EXPIRE`, `TTL`, `PERSIST` | EXPIRE sets timeout, TTL reads remaining seconds, PERSIST removes expiry; SET overwrite removes old expiry |
| `REQ-key-enum` | Key enumeration and metadata | `KEYS`, `TYPE`, `DBSIZE` | KEYS with glob pattern, TYPE returns type string, DBSIZE returns live count |
| `REQ-persistence` | Persistence | `SAVE`, `LOAD`, `FLUSH` | SAVE writes JSON, LOAD restores, FLUSH clears in-memory state |
| `REQ-errors` | Error and atomicity behavior | Error Behavior | Invalid commands, bad file paths, type mismatches fail non-zero without corrupting state |
| `REQ-unit-eval` | Unit testing definition | Evaluation Style | Unit cases test one module with direct state setup |
| `REQ-system-eval` | System testing definition | Evaluation Style | System cases cross at least two modules and carry `system_dimension` labels |

## Unit Coverage

| Feature module | Unit tests | Requirement refs | Public basis |
| --- | --- | --- | --- |
| String key-value | `MKVU001`, `MKVU002`, `MKVU003` | `REQ-string-kv` | SET/GET round-trip, EXISTS 1/0, DELETE count and removal |
| Bulk operations | `MKVU004` | `REQ-bulk-ops` | MSET stores, MGET returns JSON with null for missing keys |
| Integer operations | `MKVU005`, `MKVU006` | `REQ-integer-ops` | INCR auto-creates and increments; DECR auto-creates and decrements |
| Expiry | `MKVU007`, `MKVU008`, `MKVU017` | `REQ-expiry`, `REQ-string-kv` | EXPIRE/TTL round-trip, PERSIST removal, SET with EX flag |
| Key enumeration | `MKVU009`, `MKVU010`, `MKVU011`, `MKVU018` | `REQ-key-enum` | KEYS with/without pattern, TYPE for all variants, DBSIZE after mutations, `?` wildcard |
| Persistence | `MKVU012`, `MKVU013` | `REQ-persistence` | SAVE→FLUSH→LOAD round-trip, FLUSH clears all |
| Errors | `MKVU014`, `MKVU015`, `MKVU016` | `REQ-errors`, `REQ-integer-ops`, `REQ-persistence` | INCR on non-integer fails; LOAD missing file fails; invalid command syntax fails |

Unit requirement coverage:

- `REQ-string-kv`: `MKVU001`, `MKVU002`, `MKVU003`, `MKVU017`
- `REQ-bulk-ops`: `MKVU004`
- `REQ-integer-ops`: `MKVU005`, `MKVU006`, `MKVU014`
- `REQ-expiry`: `MKVU007`, `MKVU008`, `MKVU017`
- `REQ-key-enum`: `MKVU009`, `MKVU010`, `MKVU011`, `MKVU018`
- `REQ-persistence`: `MKVU012`, `MKVU013`, `MKVU015`
- `REQ-errors`: `MKVU014`, `MKVU015`, `MKVU016`

## System Coverage

| Test | system_dimension | Crossed modules | Requirement refs | Public basis |
| --- | --- | --- | --- | --- |
| `MKVS001` | `cross_feature_dataflow` | SET → EXPIRE → TTL → GET | `REQ-string-kv`, `REQ-expiry` | SET with EX and EXPIRE produce coherent TTL and GET results |
| `MKVS002` | `cross_feature_dataflow` | SET → INCR → TYPE → MGET → KEYS | `REQ-string-kv`, `REQ-integer-ops`, `REQ-key-enum`, `REQ-bulk-ops` | SET and INCR values flow through TYPE, MGET, and KEYS consistently |
| `MKVS003` | `state_accumulation` | SET → MSET → DELETE → MGET → DBSIZE | `REQ-string-kv`, `REQ-bulk-ops` | Overwrites and deletions accumulate correctly in MGET and DBSIZE |
| `MKVS004` | `state_accumulation` | SET → INCR → SAVE → FLUSH → LOAD → GET → TYPE | `REQ-string-kv`, `REQ-integer-ops`, `REQ-persistence`, `REQ-key-enum` | Full persistence round-trip restores strings, integers, and types |
| `MKVS005` | `global_invariant` | SET → DELETE → FLUSH → DBSIZE → KEYS | `REQ-string-kv`, `REQ-key-enum` | DBSIZE and KEYS length agree after every state mutation |
| `MKVS006` | `global_invariant` | SET → INCR → DECR → TYPE → DELETE → TYPE | `REQ-string-kv`, `REQ-integer-ops`, `REQ-key-enum` | TYPE is always consistent with the last SET/INCR/DECR/DELETE |
| `MKVS007` | `error_atomicity` | SET → INCR → failed LOAD → GET → TYPE → DBSIZE | `REQ-persistence`, `REQ-errors`, `REQ-string-kv` | Failed LOAD leaves existing state and type metadata unchanged |
| `MKVS008` | `error_atomicity` | SET → EXPIRE → failed INCR → GET → TYPE → TTL → DBSIZE | `REQ-string-kv`, `REQ-integer-ops`, `REQ-errors`, `REQ-key-enum` | Failed INCR on string preserves value, type, expiry, and DBSIZE |
| `MKVS009` | `operation_order_sensitivity` | SET → EXPIRE → TTL → SET → TTL | `REQ-string-kv`, `REQ-expiry` | SET after EXPIRE removes expiry; EXPIRE must be re-applied |
| `MKVS010` | `operation_order_sensitivity` | SET → INCR → SAVE → SET → INCR → DELETE → LOAD → GET → TYPE | `REQ-string-kv`, `REQ-integer-ops`, `REQ-persistence` | SAVE snapshot is unaffected by later mutations; LOAD restores it |
| `MKVS011` | `boundary_crossing` | SET with EX → PERSIST → TTL → KEYS → EXPIRE → EXPIRE again → TTL | `REQ-string-kv`, `REQ-expiry`, `REQ-key-enum` | SET EX, PERSIST, and repeated EXPIRE compose correctly |
| `MKVS012` | `boundary_crossing` | SET → INCR → KEYS pattern → TYPE → DBSIZE → DELETE → KEYS → DBSIZE | `REQ-string-kv`, `REQ-integer-ops`, `REQ-key-enum`, `REQ-bulk-ops` | Pattern filtering, type metadata, count, and deletion compose |

System dimension coverage:

- `cross_feature_dataflow`: `MKVS001`, `MKVS002`
- `state_accumulation`: `MKVS003`, `MKVS004`
- `global_invariant`: `MKVS005`, `MKVS006`
- `error_atomicity`: `MKVS007`, `MKVS008`
- `operation_order_sensitivity`: `MKVS009`, `MKVS010`
- `boundary_crossing`: `MKVS011`, `MKVS012`

The v1 MiniKV system set covers all 6 required system dimensions.

## Verification Targets

| Solution | Unit (target) | System (target) | Gap (target) |
| --- | ---: | ---: | ---: |
| Reference | 100.00% | 100.00% | 0.00pp |
| Candidate (expected) | 70-90% | 40-70% | 15-50pp |

Unit score target band: 70-90% (18 unit cases × weight 4 = 72 total). System gap target: ≥15pp below unit.

## Fairness Notes

- Expiry TTL checks use `step_stdout_in_range` with a generous range to accommodate implementation variance in wall-clock TTL tracking.
- SET without EX on a previously-expiring key removes expiry: this is documented in the public packet ("SET overwrites any previous value and removes any existing expiry" implied by the SET command spec).
- KEYS `?` wildcard is explicitly mentioned in the public packet (`KEYS [pattern]` with `*` and `?` support).
- The rubric avoids time-dependent tests (no sleep-based expiry validation); all expiry behavior is tested via TTL/PERSIST interaction semantics rather than actual time passage.
- No Redis protocol compatibility is required; only the documented CLI behavior is tested.
