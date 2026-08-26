# filter_notes — mobx-reactivity-engine-fullrepro-001

```
repo: mobxjs/mobx (npm name mobx, packages/mobx of the monorepo)
source_path: https://github.com/mobxjs/mobx (local mirror wip/repo-cache/mobx-src)
commit: 5dbb04a15f7eb0ef6b844904c43955357a9bbdfc (npm mobx@7.0.3, published 2026-08-19)
language: typescript
src_loc: 7249 (packages/mobx/src/**/*.ts excluding tests, 56 files across api/core/types/utils layers)
test_functions: 804 it()/test() call sites under packages/mobx/__tests__
test_files: 39 files (base/: autorun, action, observables, computeds, reaction, intercept, observe, makeObservable, map, array, set, object-api, transaction, typescript-tests, ...)
dominant_test_styles: unit + integration through the public API (jest in-repo); assertions on recorded effect-run sequences, computed recomputation counts, observe/intercept event shapes, introspection predicates; no live services, fully synchronous
public_docs: mobx.js.org (observable state, computeds, reactions, actions, collections, observe/intercept, spy, configure, API reference) — full behavioral reference
core_fact_source: one reactive dependency graph: observable atoms (object props, boxes, arrays, maps, sets) plus derived computed nodes and reaction nodes, with transaction batching and invalidation rules
derived_views: (1) effect projections autorun/reaction/when with documented scheduling and disposal, (2) computed values with caching, lazy re-evaluation and unobserved suspension, (3) mutation event streams via observe() and veto hooks via intercept(), (4) plain snapshots via toJS() and keys/values/entries object-api, (5) introspection predicates isObservable*/isComputed*/isAction/isBoxedObservable, (6) lifecycle hooks onBecomeObserved/onBecomeUnobserved, (7) global policy via configure({ enforceActions }) changing write legality
external_deps: none at runtime; oracle needs only vitest/typescript; fully synchronous core (no timers needed when reactions use default scheduling)
test_import_audit: HIGH_RISK for direct reuse — upstream tests require("../../src/mobx.ts") monorepo-relative and shared test-utils; not portable to a clean npm install; oracle is Track B generated (precedent: orama/rrule/kysely/xstate packets)
docs_test_alignment: aligned — docs and tests both specify graph invalidation/scheduling semantics observed through public effects and events
contamination_note: mobx@7.0.3, released 2026-08-19 (days before selection); v7 is a fresh major — v6 semantics are heavily represented in training data, so every claim is grounded by executing the pinned v7 release, and v6-memorization traps raise difficulty
decision: keep
reason: the reactivity core is a rule engine (dependency tracking, invalidation propagation, batched reaction scheduling, computed caching/suspension) with >= 5 public projections over one dependency graph; correctness lives in run counts and event ordering that cannot be pattern-matched from a single API call
risks: v7-vs-v6 behavioral drift must be probed, not assumed; proxies make identity semantics subtle (observable(obj) !== obj); some surfaces (flow, decorators, React bindings) are async or environment-bound -> excluded by scope; run-count assertions must pin exact documented semantics to stay fair
scope_plan: target_subdomain=core reactivity: observable objects/boxes/arrays/maps/sets (deep and shallow), makeObservable/makeAutoObservable annotations, computed (caching, suspension, equality option), autorun/reaction/when (sync scheduling, disposal, fireImmediately, delay excluded), action/runInAction batching and untracked, observe/intercept event and veto semantics, toJS, object-api (keys/values/entries/set/remove/has/get), introspection predicates, onBecomeObserved/onBecomeUnobserved, configure enforceActions; expected_oracle_max=100. Excluded: flow/async actions and generators, spy internals beyond documented event kinds (spy excluded entirely), decorators, extendObservable legacy paths, React/observer integration, reaction custom schedulers and delay timers, comparer customization beyond structural, trace, requiresReaction/keepAlive computed options, cross-observable cycle detection internals.
difficulty_shapes: lazily-resolved reference graph (computed values cache while observed and suspend when unobserved - observable behaviour differs by observation state); rule-engine reimplementation (invalidation + batching rules decide exact reaction run counts and ordering); equivalence judgement (structural comparer, toJS snapshots vs live proxies); integration tests spanning >=3 projections (mutation -> computed -> reaction -> observe/event stream -> snapshot)
```
