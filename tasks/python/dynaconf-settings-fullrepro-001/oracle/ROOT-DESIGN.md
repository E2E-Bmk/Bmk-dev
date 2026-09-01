# Dynaconf v5 synthetic root design

Status: private evaluator architecture fixed before reference qualification.

The roster contains 22 Atomic, 40 Integration, and 28 System/E2E roots. The
68 Integration plus System roots form Composition. Scores are layer-balanced;
there is no fixed-count benchmark template.

v5 retains the 78-root v4 suite as compatibility and architecture evidence and
adds twelve cross-owner recovery roots. Clean upstream passes exactly the same
18 native roots and fails the 72 preregistered mutation roots.

## Structural surfaces

| Surface | Public state machine | Direct roots |
| --- | --- | --- |
| Settings generation | load -> validate -> hook -> committed views, with rollback and correction | A01-A16, I01-I22, S01-S10 |
| Fenced durable store | unowned -> live lease -> committed generations -> release; crash -> adoption | A17-A19, I23-I28, S14 |
| Append-only lineage | byte/existence observation -> accepted/rejected event -> cursor and projection | A20-A21, I29-I34 |
| Acknowledged transport | staged -> delivered-pending -> acknowledged, or pending -> rollback | A22, I35-I40 |
| Basic cross-resource flow | watcher projection -> store generation -> acknowledged artifact | S11-S13, S15-S16 |
| Recoverable publication | prepared fence -> tentative generation -> delivery -> acknowledgement, or crash -> compensation -> replacement -> reconciliation | S17-S28 |

The v5 roots cross lineage, store, outbox, sink, and protocol-ledger ownership.
Every phase is reopened, several run in fresh processes, and failures occur
between owner commits. No in-memory coordinator can retain the state needed to
pass after process replacement.

The settings engine accounts for 30 of 72 mutation roots. Durable ownership
accounts for 10, lineage for 8, transport for 7, basic cross-resource flow for
5, and recoverable publication for 12. No surface accounts for half the
mutation portfolio. The new family is intentionally Composition-only: it adds
no shallow Atomic roots, and every observation requires at least three
independently persisted owner projections.

## Paired-reference preregistration

- M1 patched reference: 90/90.
- M2 clean upstream: exactly 18/90, failing exactly 72 mutation roots.
- Dummy: 0/90 with every root collected and reaching call phase.
- M2 Atomic: 10/22; Composition: 8/68; Combined 28.6096%; Gap +33.6898pp.
- Each control runs natural, reverse, and seeded-permuted order three times in
  fresh scorer processes.

Candidate-visible prose states ordinary product laws: ownership, durability,
fencing, append-only replay, acknowledgement, compensation, recovery, and
reconciliation. It contains no root IDs, fixtures, expected vectors, mutation
labels, anchor outcomes, or implementation recipe.

## Required incomplete controls

At least four incomplete candidates must collect exactly 90 roots, keep setup
and teardown valid, terminate within the root bound, and fail at call phase:

1. all durable owners with coordinator state retained only in memory;
2. publication that treats delivery as acknowledgement;
3. crash retry without generation/cursor fencing or compensation;
4. watcher recovery that recomputes or rewrites accepted lineage.

These controls are diagnostic, not score targets. Their failure roots must
span S17-S28 rather than one shared missing import.
