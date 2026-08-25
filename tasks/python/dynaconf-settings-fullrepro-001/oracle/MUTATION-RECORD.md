# Dynaconf v5 mutation record

All families and impact roots are fixed before source-blank anchors.

| Family | Clean upstream rule | Synthetic public rule | Roots | Independent machinery |
| --- | --- | --- | --- | --- |
| v3 settings portfolio | Upstream settings objects lack the preregistered transactional load, immutable generation, binding, lease, provenance, and publication laws. | The retained settings surface obeys the coherent v3 synthetic contract. | A06,A08,A10,A12,A15,A16; I02,I04-I10,I13-I18,I21-I22; S02,S03,S05-S10 | Settings selection, parsing, validation, hooks, provenance, and local artifact compatibility. |
| M-DURABLE-OWNERSHIP | No public persistent fenced writer store exists. | One live writer owns a durable lease; crash adoption is explicit, advances the fence, preserves generations, and permanently retires stale tokens. | A17-A19,I23-I28,S14 | Filesystem generation state, process liveness, lease lifetime, compare-and-set, and fencing. |
| M-APPEND-LINEAGE | No public append-only source cursor or watcher projection exists. | Byte/existence changes append accepted, rejected, and delete events; rejected revisions preserve the last good materialized fact. | A20,A21,I29-I34 | Append-only event resource, source identities, byte digests, cursor replay, and watcher state. |
| M-ACK-TRANSPORT | No public durable acknowledged outbox exists. | Canonical artifacts progress through stage, delivery, acknowledgement or rollback, and survive reopen with prior-byte recovery. | A22,I35-I40 | Outbox metadata, sink replacement, acknowledgement state, replay, and byte restoration. |
| M-CROSS-RESOURCE | Upstream has no transaction law spanning these owners. | Watcher, fenced store, and transport compose while retaining independent commit and recovery boundaries. | S11-S13,S15-S16 | Cross-owner generation agreement, restart recovery, and failure isolation. |
| M-RECOVERABLE-PUBLICATION | Upstream has no fenced prepare/commit/deliver/ack protocol across independent durable owners. | A prepared generation is cursor- and generation-fenced; phase receipts survive process replacement; post-commit/pre-ack failure compensates state and artifact; retries, duplicates, stale watchers, concurrent publishers, and reconciliation preserve append-only histories. | S17-S28 | Protocol ledger, lineage cursor, store generations, outbox acknowledgement, sink visibility, process replacement, fencing, compensation, and reconciliation. |

The 72 mutation roots are 80% of 90 roots. The retained settings abstraction
can satisfy at most 30/72 mutation roots. The new family requires five durable
projections and multiple process lifetimes; it cannot be implemented as an
alias of the settings mapping, store, watcher, or transport alone.

M1 must pass every root. M2 must fail exactly this record's 72 roots and pass
the 18 native controls. Any extra clean-upstream failure rejects the gate as an
incorrect blast radius; any mutation pass rejects that mutation observation.
