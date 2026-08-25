# Packaging federation API

The package retains Packaging's customary public version, specifier, requirement, marker, tag, and filename parsing behavior. This extension adds `packaging.federation`, a small in-memory coordination library for publishing a set of Python artifacts only when independent policy, witness, mirror, and transparency evidence agrees.

## Values and ownership

The module exports immutable value records `PolicyLayer`, `DecisionLease`, `WitnessClaim`, `MirrorView`, `LogEntry`, `CompensationPlan`, and `ReleaseRecord`. Public snapshots are deterministic tuples and mutable internal mappings are not exposed. Identifiers are strings. Stored evidence is scoped by owner wherever an owner is accepted; equal identifiers belonging to different owners must not alias.

Project names use Packaging canonical-name rules. Versions, specifiers, requirements, and markers follow the corresponding Packaging objects rather than ad-hoc string comparisons.

## Layered policy

`LayeredPolicyBook` stores named layers. `define(name, priority, rules)` accepts `(project, specifier, marker-or-None)` rules. Redefining an identical layer is idempotent and conflicting redefinition is rejected. A projection evaluates markers against an environment and resolves overlapping rules by layer priority, with deterministic ordering.

`lease(lease_id, owner, environment, candidates)` chooses the highest permitted version for every effective project. Missing, extra, or unsatisfied candidate domains are rejected. Leases record the policy revision that produced them. `get`, `valid`, and `revoke` expose lifecycle state: policy changes invalidate old leases, and revocation is idempotent.

## Witness graph

`WitnessGraph.add(claim_id, owner, artifact, digest, signer, parents=())` adds an immutable claim. Parents must already exist for the same owner. A signer may not make two distinct claims for the same owner and artifact. Identical replay is idempotent. `get` and `closure` provide owner-scoped lookup and dependency-first transitive closure.

`quorum(artifact, owner, threshold=2)` groups claims by digest and counts distinct signers. It returns the sole digest group meeting the positive threshold; absent or ambiguous quorum is rejected. This permits a build artifact to carry independent source ancestry while still requiring reproducible agreement.

## Mirror observations

`MirrorQuorum.observe(owner, mirror, epoch, artifacts)` records a mirror's immutable artifact-to-digest view at a non-negative epoch. Identical observation replay is idempotent, while the same mirror/epoch carrying different content is equivocation. `current(owner)` exposes only each mirror's highest epoch.

`agree(owner, required, threshold=2, max_staleness=0)` compares current views with the complete required mapping. A view is eligible only if it matches exactly and is no more than `max_staleness` behind the owner's highest observed epoch. Agreement requires the stated number of distinct mirrors.

## Transparency log

`TransparencyLog.append(owner, subject, digest)` appends a hash-chained immutable entry. `checkpoint()` returns the empty or current chain head and `inclusion(index)` returns the prefix ending at an index. `verify(entry, proof, checkpoint)` validates positions, links, entry hashes, terminal identity, and the supplied checkpoint. Prefix proofs therefore cannot be silently reused at later checkpoints.

## Compensation

`CompensationJournal.plan(plan_id, owner, actions)` stores a non-empty dependency graph expressed as `(action, prerequisites)`. Unknown prerequisites, self-dependencies, duplicates, and conflicting replay are rejected. `complete` accepts an action only in an open plan after its prerequisites; repeated completion is idempotent. `seal` requires all actions.

`reopen(plan_id, owner, failed_action)` reopens a sealed plan after an audit failure. It increments the generation and removes the failed action and every transitive dependent from completion, preserving independent completed work.

## Federated release workflow

`FederationCoordinator(policies, witnesses, mirrors, log, compensations)` coordinates but does not collapse those evidence stores.

- `stage(release_id, owner, lease_id, artifacts)` requires a currently valid lease and a unique, non-empty artifact set.
- `attest(..., artifact_digests, threshold=2)` requires an exact artifact mapping and a unique witness quorum whose digest matches each artifact.
- `publish(..., mirror_threshold=2, max_staleness=0)` rechecks the lease, requires mirror agreement, appends a transparency statement, and records its hash in the release audit trail.
- `audit(..., checkpoint)` is observational: it rechecks current mirror agreement and verifies the recorded statement's inclusion without mutating release state.
- `compensate(..., actions)` opens a compensation plan for an attested or published release. `recover` succeeds only after that plan is sealed.
- `get` and owner-filtered `snapshot` return stable release records. Successful state transitions increment revision; failed operations are atomic.

These rules describe reusable behavior, not a particular artifact inventory, mirror topology, or release sequence.
