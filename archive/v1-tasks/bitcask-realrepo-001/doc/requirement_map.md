# MiniBitcask KV Store Unit/System Requirement Map

Date: 2026-06-20

Public packet: `prd.md`

Rubric: `rubric.json`

## Public Requirements

| ID | Capability | Public packet section | Observable behavior |
| --- | --- | --- | --- |
| `REQ-put` | Write / overwrite | put / update | `put` stores a value and overwrites prior values; latest write wins |
| `REQ-update` | Conditional update | put / update | `update` writes only when the key exists, else fails non-zero |
| `REQ-get` | Read latest value | get / mget | `get` returns the latest value or fails non-zero; `mget` omits missing keys |
| `REQ-delete` | Tombstone delete | delete | `delete` removes an existing key; deleting a missing key fails non-zero |
| `REQ-metadata` | State reporting | keys / count / list / stats | metadata reflects exactly the current live key set and disk record count |
| `REQ-compact` | Compaction | compact | keeps latest live values, drops tombstones/superseded, preserves semantics |
| `REQ-durability` | Persistence | Durability And Storage | committed state survives across separate invocations via on-disk replay |
| `REQ-atomic` | Error & atomicity | Error Behavior | failed commands exit non-zero, append nothing, preserve state |
| `REQ-global-invariants` | Cross-feature invariants | Global Invariants | values, deletions, metadata, and compaction stay mutually consistent |
| `REQ-unit-eval` | Unit testing definition | Evaluation Style | unit tests exercise one module and use public CLI setup when state is needed |
| `REQ-system-eval` | System testing definition | Evaluation Style | system tests cross at least two modules and carry `system_dimension` labels |

## Unit Coverage

| Test | Feature | Requirement refs | Public basis |
| --- | --- | --- | --- |
| `KVU001` | put | `REQ-put` | put then get returns stored value |
| `KVU002` | put | `REQ-put` | re-put overwrites; latest value wins |
| `KVU003` | get | `REQ-get` | get on missing key fails non-zero |
| `KVU004` | update | `REQ-update` | update on existing key writes new value |
| `KVU005` | update/error | `REQ-update`, `REQ-atomic` | update on missing key fails and preserves state |
| `KVU006` | delete | `REQ-delete` | delete removes a key from the live set |
| `KVU007` | delete/error | `REQ-delete`, `REQ-atomic` | delete on missing key fails and preserves state |
| `KVU008` | metadata | `REQ-metadata` | keys returns live keys sorted |
| `KVU009` | metadata | `REQ-metadata` | count returns number of live keys |
| `KVU010` | metadata | `REQ-metadata` | list returns full live key/value map |
| `KVU011` | get | `REQ-get` | mget returns found keys, omits missing |
| `KVU012` | metadata | `REQ-metadata` | stats reports live_keys and log_entries |
| `KVU013` | compact | `REQ-compact` | compact drops superseded records, keeps latest |
| `KVU014` | durability | `REQ-durability` | value written by one invocation read by a later one |
| `KVU015` | compact | `REQ-compact` | compact removes tombstoned keys entirely |
| `KVU016` | metadata | `REQ-metadata` | metadata on empty store is consistent and empty |
| `KVU017` | error/atomicity | `REQ-atomic` | malformed command fails and appends nothing |

Unit requirement coverage:

- `REQ-put`: `KVU001`, `KVU002`
- `REQ-update`: `KVU004`, `KVU005`
- `REQ-get`: `KVU003`, `KVU011`
- `REQ-delete`: `KVU006`, `KVU007`
- `REQ-metadata`: `KVU008`, `KVU009`, `KVU010`, `KVU012`, `KVU016`
- `REQ-compact`: `KVU013`, `KVU015`
- `REQ-durability`: `KVU014`
- `REQ-atomic`: `KVU005`, `KVU007`, `KVU017`

## System Coverage

| Test | system_dimension | Crossed modules | Requirement refs | Public basis |
| --- | --- | --- | --- | --- |
| `KVS001` | `cross_feature_dataflow` | put -> compact -> list/stats | `REQ-put`, `REQ-compact`, `REQ-metadata`, `REQ-global-invariants` | overwritten values flow through compaction into metadata |
| `KVS002` | `state_accumulation` | put -> update -> delete -> list/count | `REQ-put`, `REQ-update`, `REQ-delete`, `REQ-metadata`, `REQ-global-invariants` | interleaved mutations accumulate to latest live state |
| `KVS003` | `global_invariant` | put -> delete -> keys/count/get | `REQ-put`, `REQ-delete`, `REQ-get`, `REQ-metadata`, `REQ-global-invariants` | keys, count, and get stay mutually consistent |
| `KVS004` | `error_atomicity` | put -> invalid update -> list/count | `REQ-update`, `REQ-atomic`, `REQ-metadata`, `REQ-global-invariants` | failed update leaves rows and count unchanged |
| `KVS005` | `error_atomicity` | put -> invalid delete -> stats/get | `REQ-delete`, `REQ-atomic`, `REQ-metadata` | failed delete appends nothing; log and value intact |
| `KVS006` | `operation_order_sensitivity` | put -> delete -> put -> get/keys | `REQ-put`, `REQ-delete`, `REQ-get`, `REQ-metadata` | put after delete resurrects the key with new value |
| `KVS007` | `operation_order_sensitivity` | put -> compact -> update/put -> list/stats | `REQ-compact`, `REQ-update`, `REQ-put`, `REQ-metadata`, `REQ-global-invariants` | writes after compaction append cleanly; latest wins |
| `KVS008` | `durability_reload` | put -> compact -> get/list | `REQ-durability`, `REQ-compact`, `REQ-get`, `REQ-metadata` | values persist across invocations, including post-compact |
| `KVS009` | `boundary_crossing` | put -> delete -> compact -> list/count/stats | `REQ-put`, `REQ-delete`, `REQ-compact`, `REQ-metadata`, `REQ-global-invariants` | overwrite, delete, and compaction compose cleanly |
| `KVS010` | `global_invariant` | put -> delete -> put -> compact -> keys/get | `REQ-compact`, `REQ-delete`, `REQ-put`, `REQ-get`, `REQ-global-invariants` | compaction never resurrects deleted keys or reverts values |
| `KVS011` | `state_accumulation` | put across rolled segments -> compact -> list | `REQ-put`, `REQ-compact`, `REQ-metadata`, `REQ-durability` | correctness holds when writes span multiple segments |
| `KVS012` | `boundary_crossing` | put -> update -> delete -> mget/list | `REQ-get`, `REQ-update`, `REQ-delete`, `REQ-metadata`, `REQ-global-invariants` | mget reflects updates and deletions and matches list |

System dimension coverage:

- `cross_feature_dataflow`: `KVS001`
- `state_accumulation`: `KVS002`, `KVS011`
- `global_invariant`: `KVS003`, `KVS010`
- `error_atomicity`: `KVS004`, `KVS005`
- `operation_order_sensitivity`: `KVS006`, `KVS007`
- `boundary_crossing`: `KVS009`, `KVS012`
- `durability_reload`: `KVS008`

The system set covers all seven requested dimensions. `durability_reload` is a
bitcask-specific extension to the standard six-dimension family, reflecting that
durable on-disk reload is this product's defining property.

## Fairness Notes

- Only CLI output and exit codes are scored; the on-disk format, segment naming,
  and rollover threshold are free implementation choices and are never inspected.
- Test setup also uses public CLI commands rather than writing private on-disk
  records, so candidates are not forced into the reference implementation's file
  format.
- `compact` is checked through the product's own `stats.log_entries`, not by
  counting files, so stronger storage layouts are not penalized.
- `update`/`delete` on a missing key are defined as failures in the packet, so the
  error-atomicity cases test published behavior rather than a gray area.
