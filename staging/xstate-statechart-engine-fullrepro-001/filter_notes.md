# filter_notes — xstate-statechart-engine-fullrepro-001

```
repo: statelyai/xstate (npm name xstate, packages/core of the monorepo)
source_path: https://github.com/statelyai/xstate (local mirror wip/repo-cache/xstate-src)
commit: c25dba07a2b68565edbe83d83c5d679dd85e00b2 (tag xstate@5.32.5, npm xstate@5.32.5, published 2026-07-14)
language: typescript
src_loc: 15467 (packages/core/src/**/*.ts excluding tests)
test_functions: 1375 it()/test() call sites under packages/core/test
test_files: packages/core/test/*.test.ts (~50 files: actions, after, assign, always/eventless, deterministic, entry-exit order, final, guards, history, initial, internalTransitions, interpreter, parallel, transient, ...)
dominant_test_styles: unit + integration through the public API (vitest in-repo); assertions on snapshot.value/context/status and recorded action order; no live services; timers driven by SimulatedClock or fake timers
public_docs: stately.ai/docs (machines, states, transitions, guards, actions, context, parallel/history/final states, delayed transitions, persistence, actors), README of packages/core — full statechart API reference
core_fact_source: one machine definition (statechart: states, transitions, guards, actions, context) interpreted over a current configuration
derived_views: (1) actor interpretation via createActor/send with snapshot.value/context/status, (2) pure step functions getInitialSnapshot/getNextSnapshot with no actor lifecycle, (3) snapshot query surface matches()/can()/hasTag() plus matchesState util, (4) persistence round-trip getPersistedSnapshot -> createActor({snapshot}), (5) deterministic time projection: delayed (after) transitions driven by the exported SimulatedClock, (6) completion projection: final states, onDone, machine output, toPromise
external_deps: none at runtime; oracle needs only vitest/typescript; no network, no real timers (SimulatedClock)
test_import_audit: HIGH_RISK for direct reuse — upstream tests import from '../src/index.ts' relative paths and shared test utils; monorepo-internal, not portable to a clean npm install; oracle is Track B generated (precedent: orama/rrule/kysely packets)
docs_test_alignment: aligned — docs and tests both specify statechart interpretation semantics observed through snapshots
contamination_note: xstate@5.32.5, released 2026-07-14 (recent); the v5 API is public since 2023-12 → treat as known; anti-memorization via novel machine fixtures (no traffic-light/toggle examples from docs; distinct state names, events and context shapes)
decision: keep
reason: statechart interpreter is a rule-engine reimplementation (SCXML-style transition selection, exit/entry set computation, microstep loop with raised events, parallel completion, history resolution) with >= 5 public projections over one machine definition; the difficulty lives in the algorithmic semantics, not API recall
risks: very large semantic surface -> strict scope plan; async actor logic (promises/observables/invoke) is timing-sensitive -> excluded except toPromise over synchronously-completed actors; v4-to-v5 memorization traps (models recall v4 semantics) actually raise difficulty but require the spec to state v5 behavior precisely
scope_plan: target_subdomain=machine definition + synchronous interpretation (createActor/send), pure step functions, guards (incl. and/or/not/stateIn, params), assign/raise actions and ordering, hierarchy/parallel/final/history states, eventless (always) transitions, wildcard descriptors, reenter semantics, delayed transitions under SimulatedClock, persistence round-trip, input, tags, output; expected_oracle_max=100. Excluded: invoke/spawn of promise/callback/observable/transition logics, actor systems and inter-actor messaging (sendParent/sendTo/forwardTo/emit), inspection API, error states from thrown actions, log/cancel/stopChild actions, getMeta, mapState/getStateNodes graph utilities, deprecated interpret alias.
difficulty_shapes: reimplementation-of-format-rule (SCXML-like selection/exit/entry/microstep algorithm); integration tests spanning >=3 public projections (definition -> interpretation -> query surface -> persistence -> timed transitions); equivalence judgement (state value shapes, matches() partial-value equivalence); lazily-resolved-reference flavor in history states (stored configuration replayed on re-entry)
```
