# Dynaconf v3 evaluator root catalog — Draft C

Status: private pre-freeze design, not candidate-facing. This Draft C replaces
the undersized Draft B mutation allocation before any scorer run or freeze.

The v4 fixed roster is 22 Atomic, 40 Integration, and 16 System/E2E roots. The
clean-upstream mutation set is exactly A06, A08, A10, A12, A15, A16; I02,
I04–I10, I13–I18, I21–I22; and S02–S03, S05–S10. All other roots are native
controls. v4 adds A17-A22, I23-I40, and S11-S16 to the mutation set. M1 must
pass 78/78; M2 must fail exactly 60 and pass exactly 18.

## Atomic roots

| ID | Class | Public obligation |
| --- | --- | --- |
| A01 | native | Public imports, version metadata, `Dynaconf`/`LazySettings` identity, global settings instance, and console entry point. |
| A02 | native | Independently constructed settings own independent runtime state and never write through the module singleton. |
| A03 | native | Case-insensitive top-level access, dotted versus literal lookup, callable/get equivalence, and controlled missing attributes. |
| A04 | native | `set`, `update`, dotted mutation, and `as_dict` agree without deleting unrelated siblings. |
| A05 | native | TOML, JSON, and Python sources decode public types and apply supplied order. |
| A06 | M-PARSE-RECOVER | Optional missing patterns produce an empty committed load receipt; a matched malformed multi-file load publishes none and a corrected retry returns a complete receipt. |
| A07 | native | Default, global, selected, and ordered named environments layer with the documented precedence. |
| A08 | M-SNAPSHOT | A derived view can produce an immutable owned `snapshot` whose values and generation survive later child and parent changes. |
| A09 | native | Prefix lists, unprefixed policy, ignore-unknown behavior, process selector, and fallback policy remain object-scoped. |
| A10 | M-DEPENDENCY | A `bind_file` dependency reevaluates current UTF-8 bytes through its converter and recovers after missing/restored lifetime. |
| A11 | native | Validator predicates, composition, defaults, callable defaults, and current error details behave through public APIs. |
| A12 | M-ENVSTACK | One `using_env` scope yields its settings owner as a lease, owns a restorable frame, and survives explicit `setenv` within the frame. |
| A13 | native | Valid fresh access observes rewritten source while unrelated runtime values remain. |
| A14 | native | Discovered, constructor, and decorated hooks apply deterministic order with replacement versus marked merge semantics. |
| A15 | M-PROVENANCE | History and inspection agree on current values, committed status, and the same public generation. |
| A16 | M-ARTIFACT | Settings-bound artifact publication returns a receipt for one complete settings/secrets/ignore bundle without secret leakage. |

## Integration roots

| ID | Family | Depends on | Workflow |
| --- | --- | --- | --- |
| I01 | native | A04,A05 | Apply preload, regular, local companion, declaring-directory include, constructor include, environment, and runtime sources; verify the final coherent projection and contributions. |
| I02 | M-PARSE-RECOVER | A05,A06 | Move from an unmatched optional receipt to a failed multi-file publication and then a corrected committed generation without partial state. |
| I03 | native | A07,A09 | Compose named environments, nested process keys, merge/delete controls, prefix selection, and fallback without leaking control markers. |
| I04 | M-SNAPSHOT | A02,A07,A08 | Create parent and multiple derived owners, mutate each, freeze independent snapshots, then switch the parent environment. |
| I05 | M-ENVSTACK | A07,A12 | Persistent environment A, outer lease B, inner lease C, normal exits: exact strict LIFO restoration through all public projections. |
| I06 | M-ENVSTACK | A07,A12 | Nested leased environment bodies raise at different depths; each exit restores its own exact prior view and original exception. |
| I07 | M-ENVSTACK | A02,A08,A12 | Interleave scopes on parent, derived view, sibling, and module settings; no object pops or observes another's frame. |
| I08 | M-ENVSTACK | A02,A12 | Two threads use different nested scopes on separate objects and repeated barriers; selected environments never cross contexts. |
| I09 | M-DEPENDENCY | A09,A10 | Compose aliases and an owned converted file binding over changing dependency bytes. |
| I10 | M-DEPENDENCY | A02,A10 | Evaluate two independently owned bindings through present, missing/error-or-fallback, and restored resource states. |
| I11 | native | A04,A11 | Compose guarded, OR, AND, required, type, membership, and current-detail validators across corrected values. |
| I12 | native | A07,A10,A11 | Apply callable defaults and ordered casts in different environments when all validators succeed. |
| I13 | M-VALIDATE | A04,A11 | An explicit multi-key `transaction` stages siblings and dotted paths; exit validation either commits once or restores the snapshot at entry. |
| I14 | M-PROVENANCE | A04,A11,A15 | After a failed staged validation, inspect values/history, correct input, retry, and observe exactly one committed new generation. |
| I15 | M-SNAPSHOT | A05,A13,A15 | Valid fresh reload changes the requested value, preserves runtime peers, and updates history/inspection coherently. |
| I16 | M-PARSE-RECOVER | A05,A06,A13 | Correct a matched malformed explicit source and load it on the same usable object without process restart. |
| I17 | M-RELOAD | A05,A13,A15 | `reload_generation` rejects malformed bytes without publication and returns a receipt after corrected bytes succeed. |
| I18 | M-PROVENANCE | A02,A07,A13 | Reload builds one fresh named-environment generation and updates values/history together without altering sibling snapshots. |
| I19 | native | A05,A14 | Run all hook forms, ordered constructor hooks, replacement, and marked merge over several nested branches. |
| I20 | native | A02,A14 | Alternate settings directories with identically named hook modules and prove directory-local behavior after returning to the first. |
| I21 | M-HOOK | A04,A14,A15 | A late `run_hooks` callable fails after earlier staged mappings; public values/generation restore completely and the original exception wins. |
| I22 | M-HOOK | A06,A14 | After pipeline failure, correct the callable and rerun successfully without stale staging or negative-cache state. |

## System/E2E roots

| ID | Family | Depends on | Workflow |
| --- | --- | --- | --- |
| S01 | native | A02–A11,I01–I04,I09–I12 | Load a multi-source application configuration, derive environments, convert and validate values, mutate runtime state, and reconcile history/inspection. |
| S02 | M-VALIDATE | A04,A11,I11–I14 | Fail a late multi-key transaction, prove complete rollback, then commit a corrected settings generation into one artifact bundle. |
| S03 | M-RELOAD | A05,A07,A13,I15–I18 | Rewrite valid→malformed→corrected environment sources while fresh access, derived views, validation, and provenance retain transactional generations. |
| S04 | native | A05,A14,A15,I19,I20 | Compose ordered sources and all hook forms across directories, then compare replacement/merge results and semantic provenance. |
| S05 | M-HOOK | A04,A14,I19–I22 | Fail the final hook after earlier hooks allocate staged state, verify cleanup and original exception, then run a clean later generation. |
| S06 | M-ARTIFACT | A04,A16 | Bundle publication stages settings, secrets, and ignore entry; a late pre-commit failure preserves the prior artifact generation byte-identically. |
| S07 | M-ARTIFACT | A15,A16 | `ArtifactPublisher` report export atomically replaces a complete UTF-8 destination; pre-commit failure preserves the prior bytes and corrected retry succeeds. |
| S08 | M-SNAPSHOT | A02,A07,A08,A12,I04–I08 | Interleave several instances, derived views, environments, and threads, then explicitly return to earlier selections without leaked middle state. |
| S09 | M-PROVENANCE | A05,A07,A15,A16 | Library and fresh-process console get/list/inspect agree across selected environments and generated JSON artifacts. |
| S10 | M-PARSE-RECOVER | A02,A05,A06,A10,A11,A13,A14 | Exercise parsing, dependency, validation, conversion, and hook failures on one object while healthy siblings work and corrected retries succeed. |

## v4 durable-resource roots

| ID range | Family | Public obligations |
| --- | --- | --- |
| A17-A19 | M-DURABLE-OWNERSHIP | Initial durable generation, owned snapshot, claim/release receipts, monotonically advancing fences, and permanent retirement of stale tokens. |
| A20-A21 | M-APPEND-LINEAGE | Append-only cursor persistence plus watcher rejection and corrected recovery. |
| A22 | M-ACK-TRANSPORT | Stage, deliver, acknowledge transition order. |
| I23-I28 | M-DURABLE-OWNERSHIP | Crash adoption, live-owner exclusion, value preservation, compare-and-set, fresh-process visibility, and post-adoption fencing. |
| I29-I34 | M-APPEND-LINEAGE | Byte append-only reopen, deduplication, last-good projection, delete/recreate, independent sources, and cursor resume. |
| I35-I40 | M-ACK-TRANSPORT | Prior-byte rollback, pending replay, idempotent acknowledgement, canonical digest, reopened rollback, and independent keys. |
| S11-S13 | M-CROSS-RESOURCE | Watcher projection to fenced generation to acknowledged artifact. |
| S14 | M-DURABLE-OWNERSHIP | Crash adoption is recorded without losing committed generation. |
| S15-S16 | M-CROSS-RESOURCE | Publication rollback isolation and all-owner restart/replay agreement. |

## v5 recoverable publication roots

| ID | Family | Depends on | Public obligation |
| --- | --- | --- | --- |
| S17 | M-RECOVERABLE-PUBLICATION | A17,A20,A22,I27,I29,I36 | Prepared state survives reopen while store and artifact remain unpublished. |
| S18 | M-RECOVERABLE-PUBLICATION | I26,I34,S11 | A watcher cursor that becomes stale before commit retires preparation without visibility. |
| S19 | M-RECOVERABLE-PUBLICATION | I25,I27,I36,S12 | A crash after store commit but before delivery produces a fenced compensating generation. |
| S20 | M-RECOVERABLE-PUBLICATION | I35,I39,S15 | Recovery after delivery but before ack restores prior artifact and prior values. |
| S21 | M-RECOVERABLE-PUBLICATION | I27,I29,I36,I37,S13 | Prepare, commit, delivery, and ack each reopen in a fresh process and converge. |
| S22 | M-RECOVERABLE-PUBLICATION | I36,I37,I38 | Duplicate delivery and ack remain idempotent in state and protocol events. |
| S23 | M-RECOVERABLE-PUBLICATION | I23-I25,S14 | A concurrent publisher is fenced until explicit recovery transfers ownership. |
| S24 | M-RECOVERABLE-PUBLICATION | I26,I38 | Request idempotency returns one preparation but never aliases changed payload. |
| S25 | M-RECOVERABLE-PUBLICATION | I28,I29,S14 | Publisher replacement retires the old token and preserves recovery ledger. |
| S26 | M-RECOVERABLE-PUBLICATION | I27,I29,I34,S12 | Reconciliation converges lineage, store, and artifact without rewriting lineage bytes. |
| S27 | M-RECOVERABLE-PUBLICATION | I31,I33,I34,S11 | Stale preparation followed by reconciliation includes all independent source owners. |
| S28 | M-RECOVERABLE-PUBLICATION | I25,I35-I37,S15,S16 | Compensation, new fence, retry, and ack converge at a later generation. |

Each Composition root declares prerequisites in `ROOT-MAP.json`. The added
System roots cross at least two independently implemented resource owners; the
v5 roots cross at least three and require persistent phase receipts.

## Balance and validity

Primary mutation counts are M-ENVSTACK 5, M-PARSE-RECOVER 4, M-SNAPSHOT 4,
M-DEPENDENCY 3, M-VALIDATE 2, M-RELOAD 2, M-HOOK 3, M-PROVENANCE 4, and
M-ARTIFACT 3. Native controls exercise substantive source, environment,
conversion, validation, hook, history, console, and recovery workflows. The
The v5 dummy must collect all 90 roots, reach call phase in every root, and pass none.
M1, exact M2, and dummy each require three stable fresh-process rounds with
valid provenance, containment, warning handling, and unchanged candidate trees
before formal freeze.
