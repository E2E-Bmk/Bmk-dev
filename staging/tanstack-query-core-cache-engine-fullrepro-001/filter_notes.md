repo: TanStack/query (packages/query-core)
source_path: https://github.com/TanStack/query (wip/repo-cache/tanstack-query-src, packages/query-core; npm tarball wip/repo-cache/query-core)
commit: fd77382a3f9f8430ec9c868c6283672715a3dd80 (tag @tanstack/query-core@5.102.4)
language: typescript
src_loc: 7295 (query-core/src/*.ts excl. __tests__)
test_functions: 636 (it/test callbacks in packages/query-core/src/__tests__)
test_files: 24 (*.test.tsx / *.test.ts)
dominant_test_styles: unit + integration over one QueryClient; vitest with fake timers; behavioral assertions
public_docs: https://tanstack.com/query/latest/docs (QueryClient reference, QueryCache/MutationCache reference, guides: caching, invalidation, hydration, infinite queries, mutations)
core_fact_source: a client-owned pair of caches — a QueryCache mapping query-key hashes to Query state machines (data, error, status, fetchStatus, dataUpdatedAt, invalidation flags) and a MutationCache of Mutation state machines — plus manager singletons (focus/online/notify)
derived_views: (1) imperative client projection (fetchQuery/getQueryData/setQueryData/getQueryState/ensureQueryData);
  (2) declarative observer projection (QueryObserver/InfiniteQueryObserver/MutationObserver results with derived flags, select transforms, placeholder/initialData);
  (3) cache-inventory projection (QueryCache.find/findAll with filter predicates, cache subscribe event stream);
  (4) bulk-operation projection (invalidateQueries/refetchQueries/cancelQueries/removeQueries/resetQueries with the same filter algebra);
  (5) serialization projection (dehydrate/hydrate round trips with shouldDehydrate predicates);
  (6) key algebra projection (hashKey/matchQuery/partialMatchKey deterministic hashing and partial matching);
  (7) structural-sharing projection (replaceEqualDeep identity preservation across refetches).
external_deps: none at runtime; tests need only vitest
test_import_audit: HIGH_RISK for Track A portability — upstream tests import '..', '../utils', '../types' and workspace package '@tanstack/query-test-utils'; effectively 100% of suites affected -> Track A discarded, oracle generated (Track B)
docs_test_alignment: aligned — official docs cover the same projections the tests exercise (client methods, observers, filters, hydration, infinite queries)
contamination_note: @tanstack/query-core@5.102.4, released 2026-08-25 (same day as selection), relative to training cutoff: after (likely) for the patch; the v5 API line (2023+) is broadly documented, so difficulty rests on precise cache/observer state-machine semantics rather than surface novelty
decision: keep
reason: rule-engine reimplementation (staleness/invalidation algebra, retry state machine, structural sharing, filter matching, hydration merge rules) with 7 public projections over one cache fact source, 7.3k LOC, 636-test active suite.
risks: (1) upstream tests non-portable -> generated_only oracle; mitigated by probing the pinned release for every asserted behavior;
  (2) timer-driven behavior (gcTime, staleTime, retryDelay, refetchInterval) can flake -> oracle uses retryDelay 0, explicit small gcTime with generous sleeps, and manual manager toggles; no interval refetching;
  (3) result objects carry many derived flags -> assert the documented subset (status/fetchStatus/data/error/isStale/isPlaceholderData/failureCount...), never whole-object snapshots;
  (4) window/DOM-dependent focus/online auto-refetch semantics -> drive focusManager/onlineManager setters directly, do not simulate DOM events.
scope_plan: target_subdomain=QueryClient imperative surface (fetchQuery/ensureQueryData/prefetchQuery/getQueryData/setQueryData/setQueriesData/getQueriesData/getQueryState/invalidateQueries/refetchQueries/cancelQueries/removeQueries/resetQueries/isFetching/isMutating/defaults), Query lifecycle & retryer (status/fetchStatus transitions, retry/retryDelay, CancelledError), QueryCache find/findAll/subscribe events, QueryObserver results (select/initialData/placeholderData/enabled/staleTime/keepPreviousData/structural sharing), InfiniteQueryObserver (fetchNextPage/getNextPageParam/maxPages/hasNextPage), mutations (MutationObserver lifecycle callbacks, retry, MutationCache find/findAll/scopes... scopes excluded), hydration (dehydrate/hydrate round trip, predicates), key utilities (hashKey/matchQuery/partialMatchKey/replaceEqualDeep/skipToken/keepPreviousData), notifyManager batching, focusManager/onlineManager state; expected_oracle_max=100
excluded: experimental_streamedQuery, environmentManager, timeoutManager internals, refetchInterval/auto-refetch on focus/online/reconnect, mutation scopes serialization, queriesObserver combine, SSR server detection (isServer), dataTag symbols/unsetMarker, per-query meta propagation beyond acceptance, thenable/promise experimental features, subscribeToQueries internals
