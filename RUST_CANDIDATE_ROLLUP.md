# Rust candidate state after the 2026-08-24 session

Four screening axes, all established by measurement this session:

1. **Reconstruction difficulty** — the existing qwen score. If it is high, nothing else helps.
2. **Statable declaration surface** — every enum variant shape, trait method set and struct public
   field the oracle uses must be pinnable in the spec.
3. **Oracle observes decisions** — the suite must assert order/priority/precedence, not only
   concrete values, or no semantic family can move the pass rate.
4. **A family that is both coherent and observed** — coherence means the mutated system is still a
   product a reasonable engineer could ship. Judge it by WHERE failures are raised: assertions
   raised inside the target library mean an internal invariant was violated (not coherent); only
   oracle-raised failures count as observed divergence.

| task | score | blocker | status key |
|---|---|---|---|
| gix-status-001 | 12.5% | none — QUALIFIED | ALL CHECKS PASSED |
| gix-ref-txn-001 | 41.2% | none — QUALIFIED | ALL CHECKS PASSED |
| gix-config-file-001 | 47.9% | none — QUALIFIED | ALL CHECKS PASSED |
| lsm-tree-001 | 52.8% (gap +100pp) | axis 4: SEQNO r35 breaks reads; RESTART hits an internal invariant; RATIO/VERDICT r0 | SIGFIX_52.8_NO_COHERENT_FAMILY_EXHAUSTED |
| guppy-...-001 | 4.5% | v2 structure absent; RESOLVER family needs 2 large structural assertions recomputed | GATE_A_FIXED_V2_STRUCTURE_PENDING |
| egglog-lang-layer-001 | unscored | sealed supertrait chain blocks the sigfix probe | PRODUCT_FAILURE_SIGFIX_BLOCKED_BY_SEAL |
| sanakirja-001 | 77.7% | axis 4: families measured <=6 roots | sigfix_score recorded |
| gix-ref-peel-001 | 81.9% | axis 4: constant families cost nothing (rule 10) | CONTROLS_COMPLETE_PASS_RATE_TOO_HIGH |
| gix-ref-store-001 | 71.1% | axes 3+4: oracle pins concrete values in name_model | semantic_family_survey |
| pest-meta-001 | 100% | axis 1 | ELIMINATED_AXIS1_SCORES_100 |

**Compliant: 3 of 10.**

Closest to a fourth: **guppy at 4.5%** — E1 is already met and Gate A (the user-ruled spec defect,
eight undeclared reject conditions) is fixed. What it lacks is the whole v2 structure: taxonomy for
155 tests, a mutation block, ROOT-MAP, M2 and two broad controls. The robust route for its RESOLVER
family is to regenerate the two diverging tests' expected values programmatically from a captured
V2 run rather than editing the 31-entry package list and ~30-line trace by hand.

Unscreened candidates still holding: config-rs, crop-rope, native-db, turmoil-netsim, taskchampion,
plus the gitoxide tasks. Note the concentration problem: 18 of 29 rust tasks come from gitoxide and
all three qualifiers are gix-*, so a model that learns gitoxide idiom gets a correlated lift.
Prefer non-gitoxide candidates, screened on axis 1 (existing qwen score) first.

## Axis-1 sweep over the remaining candidates (2026-08-24, measured)

Median of the scored non-sigfix qwen runs per task. Only a task in the 10-50% band is worth the
downstream work; above 50% the pass rate has to be pushed down and this session proved that needs a
family that is both coherent and observed, which none of the surveyed rust oracles offer.

| task | median | note |
|---|---|---|
| graphql-inspector-schemadiff-fullrepro-001 | **33.9%** | in band — but TypeScript, not rust |
| dependency-cruiser-ruleset-fullrepro-001 | 68.4% | above band |
| gix-odb-dynstore-001 | 69.4% | above band |
| gix-filter-001 | 73.0% | above band |
| gix-blame-001 | 73.1% | above band |
| config-rs-001 | 73.8% | above band |
| gix-index-state-001 | 74.7% | above band |
| gix-dir-001 | 81.5% | above band |
| gix-protocol-handshake-001 | 86.9% | above band |
| gix-pathspec-001 | 89.8% | above band |
| crop-rope-001 | 93.7% | above band |
| gix-object-parse-001 | 97.3% | above band |
| gix-config-parse-001 | 97.4% | above band |

**Conclusion of the sweep: among rust candidates that already have a valid score, none sits below
50% except the three that already qualify.** Pushing any of the >68% tasks down requires the
coherent-and-observed family that this session showed is absent from these oracles.

### The only untapped reservoir: tasks whose runs are all compile errors

These eight have never produced a valid score because the candidate delivery does not compile. Their
true difficulty is unknown until a sigfix probe aligns the declared signatures — exactly the route
that took lsm-tree from `error` to a valid 52.8% with a +100pp gap.

- gix-commitgraph-001 (M1 baseline 64/64 already verified, carve persisted)
- gix-merge-001 (3-way merge and conflict resolution; algorithmic)
- gix-diff-rewrites-001 (rename/copy detection with similarity scoring)
- gix-pack-decode-001
- native-db-001 (carve persisted, 6277 lines)
- turmoil-netsim-001 (network simulation, stateful scheduling)
- taskchampion-fullrepro-001
- casbin-policy-enforcement-fullrepro-001 (no scored run at all)

**Recommended next action:** run `harness/sigfix_probe.sh <id> stage|build|score` on these eight in
order of algorithmic depth (gix-merge, gix-diff-rewrites, turmoil-netsim, native-db first). Each
probe is cheap relative to family design, and it is the only measurement that can reveal a rust
candidate naturally below 50%. lsm-tree is the precedent: its `error` status hid a genuine 52.8%
with the strongest integration gap measured in this session.
