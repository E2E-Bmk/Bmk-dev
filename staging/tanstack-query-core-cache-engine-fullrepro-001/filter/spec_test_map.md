# spec_test_map — tanstack-query-core-cache-engine-fullrepro-001

filter/oracle_source: generated_only
oracle_version: 2026-08-25

| test_nodeid | layer | assertion_kind | spec_section | status | notes |
|-------------|-------|----------------|--------------|--------|-------|
| atomic::a client exposes the caches it was constructed with | atomic | positive | section Client And Cache Fundamentals | covered | QC-CLI-001, QC-CLI-002 |
| atomic::defaultOptions.queries are merged into every fetch | atomic | positive | section Client And Cache Fundamentals | covered | QC-CLI-001 |
| atomic::clear empties both caches | atomic | positive | section Client And Cache Fundamentals | covered | QC-CLI-003 |
| atomic::hashKey is deterministic and insensitive to property order | atomic | positive | section Client And Cache Fundamentals | covered | QC-CLI-004 |
| atomic::partialMatchKey implements deep-prefix matching | atomic | positive | section Client And Cache Fundamentals | covered | QC-CLI-005 |
| atomic::a cache entry exposes queryKey, queryHash, and state | atomic | positive | section Client And Cache Fundamentals | covered | QC-CLI-006 |
| atomic::state fields reflect a successful fetch | atomic | positive | section Client And Cache Fundamentals + section Fetching And Query State | covered | QC-CLI-007, QC-FET-002 |
| atomic::setQueryDefaults supplies a queryFn to key-only fetches | atomic | positive | section Client And Cache Fundamentals | covered | QC-CLI-008 |
| atomic::setMutationDefaults lets mutate run with only a mutationKey | atomic | positive | section Client And Cache Fundamentals | covered | QC-CLI-009 |
| atomic::fetchQuery resolves with the queryFn's value | atomic | positive | section Fetching And Query State | covered | QC-FET-001 |
| atomic::the queryFn context carries client, queryKey, meta, and signal | atomic | positive | section Fetching And Query State | covered | QC-FET-001 |
| atomic::a failing fetch rejects with the error and records error state | atomic | failure_path | section Fetching And Query State + section Error Semantics | covered | QC-FET-003, QC-ERR-001 |
| atomic::cached data within staleTime is served without invoking queryFn | atomic | positive | section Fetching And Query State | covered | QC-FET-004 |
| atomic::with the default staleTime of zero a repeat fetch refetches | atomic | positive | section Fetching And Query State | covered | QC-FET-004 |
| atomic::ensureQueryData fetches only when no fresh data exists | atomic | positive | section Fetching And Query State | covered | QC-FET-005 |
| atomic::prefetchQuery resolves undefined on success and on failure | atomic | positive | section Fetching And Query State + section Error Semantics | covered | QC-FET-006, QC-ERR-002 |
| atomic::concurrent fetches for one key share a single queryFn invocation | atomic | positive | section Fetching And Query State | covered | QC-FET-007 |
| atomic::retry: 2 makes exactly three attempts and counts the failures | atomic | positive | section Fetching And Query State | covered | QC-FET-008, QC-FET-009 |
| atomic::the default retry count in this environment is zero | atomic | positive | section Fetching And Query State | covered | QC-FET-008 |
| atomic::cancelQueries aborts the signal and rejects with CancelledError | atomic | failure_path | section Fetching And Query State + section Error Semantics | covered | QC-FET-010, QC-ERR-003 |
| atomic::an unused entry is collected after its gcTime | atomic | positive | section Fetching And Query State | covered | QC-FET-011 |
| atomic::reads distinguish absent keys from present ones | atomic | positive | section Direct Cache Reads And Writes + section Error Semantics | covered | QC-DIR-001, QC-ERR-005 |
| atomic::setQueryData accepts a plain value or a functional updater | atomic | positive | section Direct Cache Reads And Writes | covered | QC-DIR-003 |
| atomic::an updater returning undefined skips the write | atomic | positive | section Direct Cache Reads And Writes | covered | QC-DIR-004 |
| atomic::direct writes count as successful data updates | atomic | positive | section Direct Cache Reads And Writes | covered | QC-DIR-005 |
| atomic::getQueriesData returns key/data pairs for every match | atomic | positive | section Direct Cache Reads And Writes | covered | QC-DIR-002 |
| atomic::setQueriesData applies one updater to every match | atomic | positive | section Direct Cache Reads And Writes | covered | QC-DIR-006 |
| atomic::isFetching counts in-flight fetches and returns to zero | atomic | positive | section Direct Cache Reads And Writes | covered | QC-DIR-007 |
| atomic::queryKey filters prefix-match and exact filters hash-match | atomic | positive | section Query Filters And Bulk Operations | covered | QC-FLT-001 |
| atomic::type filters split entries by observer activity | atomic | positive | section Query Filters And Bulk Operations | covered | QC-FLT-001 |
| atomic::invalidation marks entries and makes them match stale filters | atomic | positive | section Query Filters And Bulk Operations | covered | QC-FLT-004, QC-FLT-005, QC-FLT-006 |
| atomic::fetchStatus filters select by fetching activity | atomic | positive | section Query Filters And Bulk Operations | covered | QC-FLT-001 |
| atomic::predicate filters receive the query object | atomic | positive | section Query Filters And Bulk Operations | covered | QC-FLT-001 |
| atomic::matchQuery makes the same decision as the cache | atomic | positive | section Query Filters And Bulk Operations | covered | QC-FLT-002 |
| atomic::find is exact by default while findAll prefix-matches | atomic | positive | section Query Filters And Bulk Operations | covered | QC-FLT-003 |
| atomic::refetchQueries refetches matches regardless of staleness | atomic | positive | section Query Filters And Bulk Operations | covered | QC-FLT-007 |
| atomic::removeQueries deletes matching entries outright | atomic | positive | section Query Filters And Bulk Operations | covered | QC-FLT-008 |
| atomic::resetQueries returns an inactive entry to its pristine state | atomic | positive | section Query Filters And Bulk Operations | covered | QC-FLT-009 |
| atomic::the cache event stream reports added, updated, and removed | atomic | positive | section Query Filters And Bulk Operations | covered | QC-FLT-010 |
| atomic::subscribing triggers a fetch and delivers the success result | atomic | positive | section Query Observers | covered | QC-OBS-001, QC-OBS-004 |
| atomic::getCurrentResult reads the latest result synchronously | atomic | positive | section Query Observers | covered | QC-OBS-002 |
| atomic::derived booleans agree with the underlying state | atomic | positive | section Query Observers | covered | QC-OBS-003 |
| atomic::failure results expose failureCount and failureReason | atomic | positive | section Fetching And Query State + section Query Observers | covered | QC-FET-009, QC-OBS-003 |
| atomic::select transforms the result while the cache keeps raw data | atomic | positive | section Query Observers | covered | QC-OBS-005 |
| atomic::initialData seeds the cache and starts the observer at success | atomic | positive | section Query Observers | covered | QC-OBS-006 |
| atomic::placeholderData shows immediately and never enters the cache | atomic | positive | section Query Observers | covered | QC-OBS-007 |
| atomic::keepPreviousData carries prior data across a key change | atomic | positive | section Query Observers | covered | QC-OBS-008 |
| atomic::enabled: false suppresses fetching while refetch still works | atomic | positive | section Query Observers | covered | QC-OBS-009, QC-OBS-002 |
| atomic::a deep-equal refetch keeps the previous data identity | atomic | positive | section Query Observers | covered | QC-OBS-010 |
| atomic::unchanged sub-trees keep their identity through a partial change | atomic | positive | section Query Observers | covered | QC-OBS-010 |
| atomic::replaceEqualDeep shares every deep-equal sub-tree | atomic | positive | section Query Observers | covered | QC-OBS-011 |
| atomic::skipToken marks the query unrunnable | atomic | failure_path | section Query Observers | covered | QC-OBS-012 |
| atomic::setOptions re-targets the observer to another key | atomic | positive | section Query Observers | covered | QC-OBS-002 |
| atomic::fetchInfiniteQuery resolves parallel pages and pageParams arrays | atomic | positive | section Infinite Queries | covered | QC-INF-001 |
| atomic::fetchNextPage appends the next page while one exists | atomic | positive | section Infinite Queries | covered | QC-INF-002, QC-INF-003 |
| atomic::an undefined next param ends paging without growth | atomic | positive | section Infinite Queries | covered | QC-INF-003 |
| atomic::fetchPreviousPage prepends the page and its parameter | atomic | positive | section Infinite Queries | covered | QC-INF-004 |
| atomic::maxPages keeps a sliding window with aligned pageParams | atomic | positive | section Infinite Queries | covered | QC-INF-005 |
| atomic::a successful mutation runs its lifecycle in order with context | atomic | positive | section Mutations | covered | QC-MUT-001, QC-MUT-002, QC-MUT-004 |
| atomic::a failing mutation rejects and reports through onError then onSettled | atomic | positive | section Mutations + section Error Semantics | covered | QC-MUT-003, QC-MUT-004, QC-ERR-004 |
| atomic::getCurrentResult reports the run and reset returns to idle | atomic | positive | section Mutations | covered | QC-MUT-005, QC-MUT-006 |
| atomic::mutation retry re-invokes the function and counts failures | atomic | positive | section Mutations | covered | QC-MUT-007 |
| atomic::the mutation cache records runs and answers find queries | atomic | positive | section Mutations | covered | QC-MUT-008 |
| atomic::isMutating counts running mutations and filters by key | atomic | positive | section Mutations + section Direct Cache Reads And Writes | covered | QC-MUT-008, QC-DIR-007 |
| atomic::dehydrate includes only successful queries by default | atomic | positive | section Serialization And Managers | covered | QC-SER-001, QC-SER-002 |
| atomic::a shouldDehydrateQuery predicate replaces the default | atomic | positive | section Serialization And Managers | covered | QC-SER-002 |
| atomic::hydrate merges entries preserving data and timestamps | atomic | positive | section Serialization And Managers | covered | QC-SER-003 |
| atomic::scheduled callbacks are deferred and run in submission order | atomic | positive | section Serialization And Managers | covered | QC-SER-004 |
| atomic::focusManager reports and forces the focus flag | atomic | positive | section Serialization And Managers | covered | QC-SER-005 |
| atomic::onlineManager reports and sets the online flag | atomic | positive | section Serialization And Managers | covered | QC-SER-005 |
| integration::one entry's data agrees across reads, observers, cache queries, and pair listings | integration | positive | section Cross-View Invariants | covered | QC-CVI-001; CVI-001 |
| integration::hash-equal keys address one entry, one fetch, and one query object | integration | positive | section Cross-View Invariants + section Fetching And Query State | covered | QC-CVI-002, QC-FET-007; CVI-002 |
| integration::invalidateQueries touches exactly the entries matchQuery selects | integration | positive | section Cross-View Invariants + section Query Filters And Bulk Operations | covered | QC-CVI-003, QC-FLT-004; CVI-003 |
| integration::removeQueries with a predicate deletes exactly the matchQuery set | integration | positive | section Cross-View Invariants + section Query Filters And Bulk Operations | covered | QC-CVI-003, QC-FLT-008; CVI-003 |
| integration::the event stream journals what other projections observe | integration | positive | section Cross-View Invariants + section Query Filters And Bulk Operations | covered | QC-CVI-004, QC-FLT-010; CVI-004 |
| integration::observer flags track entry state through a fetch lifecycle | integration | positive | section Cross-View Invariants | covered | QC-CVI-006; CVI-006 |
| integration::after clear every projection reports emptiness | integration | positive | section Cross-View Invariants | covered | QC-CVI-007; CVI-007 |
| integration::invalidateQueries refetches the actively observed entry | integration | positive | section Query Filters And Bulk Operations | covered | QC-FLT-004 |
| integration::refetchType none marks an observed entry stale without fetching | integration | positive | section Query Filters And Bulk Operations | covered | QC-FLT-005, QC-FLT-006, QC-FLT-007 |
| integration::a direct write is pushed to a subscribed observer immediately | integration | positive | section Direct Cache Reads And Writes + section Cross-View Invariants | covered | QC-DIR-003, QC-CVI-001; CVI-001 |
| integration::a select observer re-derives its view from raw cache writes | integration | positive | section Query Observers + section Direct Cache Reads And Writes | covered | QC-OBS-005, QC-DIR-003 |
| integration::placeholder data is observer-local and absent from cache projections | integration | positive | section Query Observers + section Cross-View Invariants | covered | QC-OBS-007, QC-CVI-001; CVI-001 |
| integration::cancelQueries settles an observed fetch back to idle without error | integration | failure_path | section Fetching And Query State | covered | QC-FET-010 |
| integration::retry progress is visible through observer failure fields | integration | positive | section Fetching And Query State | covered | QC-FET-008, QC-FET-009 |
| integration::resetQueries reverts and refetches an actively observed entry | integration | positive | section Query Filters And Bulk Operations | covered | QC-FLT-009 |
| integration::an observer fetch and an imperative fetch share one invocation | integration | positive | section Fetching And Query State + section Cross-View Invariants | covered | QC-FET-007, QC-CVI-002; CVI-002 |
| integration::a direct write refreshes staleness for later fetches | integration | positive | section Fetching And Query State + section Direct Cache Reads And Writes | covered | QC-FET-004, QC-DIR-005 |
| integration::activity counters partition concurrent queries and mutations | integration | positive | section Direct Cache Reads And Writes + section Mutations | covered | QC-DIR-007, QC-MUT-008 |
| integration::per-key defaults drive observers that carry only a key | integration | positive | section Client And Cache Fundamentals | covered | QC-CLI-008 |
| integration::mutation success handlers can write query state other views observe | integration | positive | section Mutations + section Cross-View Invariants | covered | QC-MUT-002, QC-CVI-001; CVI-001 |
| integration::the mutation cache indexes concurrent keyed runs | integration | positive | section Mutations | covered | QC-MUT-008 |
| integration::maxPages window slides while the cache read stays aligned | integration | positive | section Infinite Queries + section Cross-View Invariants | covered | QC-INF-005, QC-CVI-001; CVI-001 |
| integration::a dehydrated cache round-trips into a fresh client with staleness intact | system_e2e | positive | section Cross-View Invariants + section Serialization And Managers | covered | QC-CVI-005, QC-SER-001, QC-SER-003; CVI-005 |
| integration::keepPreviousData bridges a paged browse while both entries stay cached | system_e2e | positive | section Query Observers + section Cross-View Invariants | covered | QC-OBS-008, QC-CVI-001; CVI-001 |
| integration::an infinite browse pages forward to exhaustion with consistent views | system_e2e | positive | section Infinite Queries | covered | QC-INF-001, QC-INF-002, QC-INF-003 |
| integration::an optimistic update is rolled back through the mutation context on failure | system_e2e | positive | section Mutations + section Direct Cache Reads And Writes | covered | QC-MUT-003, QC-MUT-004, QC-DIR-003 |
| integration::an abandoned entry is garbage collected and journaled as removed | system_e2e | positive | section Fetching And Query State + section Query Filters And Bulk Operations | covered | QC-FET-011, QC-FLT-010 |
| integration::a full invalidate cycle refreshes data and clears staleness everywhere | system_e2e | positive | section Cross-View Invariants + section Query Filters And Bulk Operations | covered | QC-CVI-004, QC-FLT-004, QC-FLT-006; CVI-004 |

Total: 98 | kept (covered): 98 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 98

Track A note: upstream tests import monorepo-relative source paths and are not
portable to a clean package install; the oracle is Track B generated from the
spec with expected values observed by executing the pinned reference release.
