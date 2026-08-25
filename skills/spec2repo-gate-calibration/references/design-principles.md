# Design principles for real separation

## 1. Optimize for independent decisions, not assertion count

The useful unit is a product decision that cannot be inferred from a nearby
decision. Adding more boundary examples to one parser, one mapping, or one
rollback wrapper usually raises test count without reducing a capable
candidate's pass rate.

Strong gates combine distinct mechanics such as:

- an owner generation or fenced lease;
- append-only lineage and immutable snapshots;
- prepare, commit/publish, delivery, and acknowledgement as separate states;
- exact-byte artifact manifests and atomic visibility;
- a durable result journal with tentative, terminal, and acknowledged states;
- an outbox with claim, retry, and exactly-once acknowledgement;
- lifecycle obligations with reverse-order cleanup after failure;
- cross-process reopen, recovery, adoption, and stale-owner rejection.

Each owner needs its own durable state and public responsibility. A single
dictionary plus a generic rollback method must not satisfy most families.

## 2. Layer roots by ownership

Atomic roots should test one local value, protocol, transition, or owner.
Composition roots should require two or more independent owners. System/E2E
roots should normally require four or more owners and a receipt closure that
proves every prerequisite is reachable and verified.

Every composed root should name:

1. owners present before the operation;
2. the decisive transition or failure;
3. the affected outcome;
4. a healthy sibling, replacement, or previous generation that must survive;
5. a fresh/reopened public observation.

If “close everything and start again” or “return a happy-path dictionary” can
pass, the root is not structurally independent enough.

## 3. Use mutation as product design

Mutation roots should introduce coherent public behavior, not evaluator-only
branches. Use several non-dominant families; a practical default is 5–9
families with no family controlling more than about one quarter of mutation
votes.

Good mutation families expose different failure modes and state ownership.
The API shape should remain available in clean and broad controls so missing
behavior becomes a semantic call-phase failure, not ImportError or
AttributeError setup noise.

Mutation fraction alone is insufficient. Require:

- exact union and native complement;
- primary family assignment;
- family-level pass slices;
- Integration roots crossing owners/families;
- System roots spanning several families;
- broad controls that omit or collapse one architectural idea while retaining
  all public signatures.

## 4. Keep native controls in Composition

If all Composition roots are mutations and many Atomic roots are native, the
clean-upstream Gap is produced by vote allocation. Add genuine native
cross-view controls to Composition and calculate:

- raw Atomic rate;
- raw Composition rate;
- Combined as the mean of layer rates;
- raw Gap = Atomic rate - Composition rate;
- conditional Composition rate among roots whose declared prerequisites pass;
- adjusted Gap = Atomic rate - conditional Composition rate.

An adjusted negative Gap does not automatically reject a mutation gate, but it
must be disclosed: the clean score is then wiring evidence, not difficulty
evidence. The source-blank Solver remains the separation authority.

## 5. Write a normal OSS specification

Write generation rules and invariants that support a family of tests:

- public imports and signatures;
- value/record shapes and required keys;
- ownership and state transitions;
- idempotency, fencing, recovery, and atomic visibility;
- positive and negative protocol behavior;
- a few ordinary cross-owner usage examples.

Do not include root IDs, expected vectors, mutation labels, fixture language,
or sentences no credible OSS documentation would contain. A clause should
support several meaningful observations, not encode one assertion.

Before freeze, mechanically compare the evaluator's actual imports,
operations, attribute/key reads, and call shapes to the public contract. This
prevents the common defect where an oracle imports an undeclared constant or
requires an undocumented helper.

## 6. Useful hardening tricks

- Put candidate-side calls behind evaluator-owned bounded deadlines. A product
  hang becomes a finite call-phase failure; only the outer evaluator deadline
  is infrastructure-invalid.
- In threaded/concurrent roots, capture worker exceptions, release or abort
  barriers in `finally`, and use bounded joins. Assert no evaluator thread is
  left alive.
- Validate record shape before indexing. Missing public data should produce a
  controlled semantic mismatch, while a raw harness `KeyError` remains
  invalid.
- Require owner-ledger receipts for every declared Atomic prerequisite before
  a Composition pass is admitted.
- Use source-blank clean API scaffolds that preserve signatures but provide no
  synthetic behavior. This distinguishes missing semantics from collection
  failure.
- Test exact-byte visibility and previous-generation preservation, not just
  existence of a success flag.
