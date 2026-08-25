# query-core Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`@tanstack/query-core` is a framework-agnostic asynchronous state-management engine. A `QueryClient` owns two caches: a query cache mapping hashed query keys to query state machines (data, error, status, timestamps, invalidation marks) and a mutation cache of mutation state machines. Callers fetch and read through imperative client methods, observe entries reactively through observer objects, operate on whole cache slices through a shared filter algebra, and serialize cache content for transfer between clients.

The engine encodes the caching rules an application would otherwise hand-roll: request deduplication, staleness windows, retry with backoff, cancellation through abort signals, structural sharing of refetched data, garbage collection of unused entries, and paged (infinite) data assembly. All of it is head-less: there is no rendering, no DOM requirement, and no framework dependency.

The installable package name is `@tanstack/query-core`. All functionality is reachable through named exports of the package root.

## Non-Goals

- This specification does not require framework bindings, rendering integration, or hook implementations.
- This specification does not require interval-based automatic refetching (`refetchInterval`) or automatic refetch on window focus, reconnect, or DOM visibility events; focus and online state are covered only as manually driven manager state.
- This specification does not require streamed queries, environment managers, or timeout-manager configuration.
- This specification does not require mutation scopes, paused-mutation resumption, or offline persistence.
- This specification does not require the multi-query observer that combines several queries into one result.
- This specification does not define behavior for circular or non-serializable query keys beyond deterministic hashing of plain JSON-compatible values.

## Representative Workflows

**Fetch, cache, and reuse.** A client fetches once, serves repeat requests from cache while fresh, and exposes state for inspection:

```ts
import { QueryClient } from '@tanstack/query-core';

const client = new QueryClient();
client.mount();

const user = await client.fetchQuery({
  queryKey: ['user', 31],
  queryFn: async ({ queryKey }) => ({ id: queryKey[1], name: 'ada' }),
  staleTime: 60_000,
});

client.getQueryData(['user', 31]);           // { id: 31, name: 'ada' }
client.getQueryState(['user', 31]).status;   // 'success'

// within staleTime the cached value is returned without calling queryFn again
await client.fetchQuery({ queryKey: ['user', 31], queryFn: failing, staleTime: 60_000 });
```

**Observe, invalidate, refetch.** An observer subscribes to one cache entry; invalidation marks matching entries and refetches the actively observed ones:

```ts
import { QueryClient, QueryObserver } from '@tanstack/query-core';

const client = new QueryClient();
client.mount();

const observer = new QueryObserver(client, {
  queryKey: ['todos', { list: 4 }],
  queryFn: fetchTodoList,
});
const unsubscribe = observer.subscribe((result) => {
  result.status;      // 'pending' -> 'success'
  result.data;        // list payload once fetched
});

await client.invalidateQueries({ queryKey: ['todos'] }); // refetches the observed entry
unsubscribe();
```

## Client And Cache Fundamentals

The client is the single entry object; keys, hashing, and per-key defaults define how entries are identified and configured.

**Client construction.** A `QueryClient` accepts an optional configuration object with `queryCache`, `mutationCache`, and `defaultOptions` (whose `queries` and `mutations` sub-objects supply defaults such as `staleTime`, `retry`, or `gcTime` merged into every matching operation). `client.mount()` activates the client and `client.unmount()` releases it; `getQueryCache()` and `getMutationCache()` return the owned caches. `client.clear()` empties both caches.

**Query keys and hashing.** A query key is an array of JSON-compatible values. Keys are identified by a deterministic hash: `hashKey(key)` returns a string that is insensitive to object property insertion order, so `[{ a: 1, b: 2 }]` and `[{ b: 2, a: 1 }]` name the same cache entry. `partialMatchKey(a, b)` returns `true` exactly when `b` is a deep prefix of `a` — every array element and object property present in `b` must deep-equal the corresponding part of `a`, while `a` is free to carry extra elements and properties.

**Cache entries.** Each cache entry is a query object exposing `queryKey`, `queryHash`, and `state`. The `state` object carries `data`, `error`, `status` (`'pending'`, `'success'`, or `'error'`), `fetchStatus` (`'fetching'`, `'paused'`, or `'idle'`), `dataUpdatedAt` (epoch milliseconds of the last successful data write), `dataUpdateCount`, `fetchFailureCount`, and `isInvalidated`.

**Per-key defaults.** `client.setQueryDefaults(keyPrefix, options)` registers option defaults applied to every query whose key starts with the prefix; `getQueryDefaults` returns them. WHEN a fetch is issued for a key covered by defaults that include a `queryFn`, THEN that function is used without being repeated at each call site. `setMutationDefaults(keyPrefix, options)` / `getMutationDefaults` do the same for mutations, letting `mutate` run with only a `mutationKey`.

## Fetching And Query State

Imperative fetching drives the query state machine; its rules are deduplication, staleness, retry, and cancellation.

**fetchQuery.** `client.fetchQuery(options)` takes `queryKey`, `queryFn`, and per-call options and returns a promise of the data. The `queryFn` receives a context object carrying `client`, `queryKey`, `meta`, and an `AbortSignal` named `signal`. On success the entry's `status` becomes `'success'`, `fetchStatus` returns to `'idle'`, `data` holds the resolved value, and `dataUpdatedAt` records the write time. If the `queryFn` rejects and retries are exhausted, then `fetchQuery` rejects with the function's error, the entry's `status` becomes `'error'`, and the `error` is retained in state.

**Staleness.** Every fetch consults `staleTime` (milliseconds, default 0): WHEN cached data exists whose age is within `staleTime`, THEN `fetchQuery` resolves with the cached value without invoking `queryFn`; otherwise it refetches. `ensureQueryData(options)` behaves like `fetchQuery` but is the canonical "fetch only if needed" spelling. `prefetchQuery(options)` performs the same fetch but always resolves with `undefined` and never rejects — a failed prefetch leaves the entry in `'error'` state silently.

**Deduplication.** WHILE a fetch for a key is in flight, further fetch requests for the same key must not start a second `queryFn` invocation; they await and receive the same result.

**Retry.** The `retry` option is the number of additional attempts after the initial failure; in this environment the default is 0 (a single attempt). `retry: 2` yields exactly 3 invocations. `retryDelay` (milliseconds or a function of attempt index and error) spaces attempts. During a failing fetch the state's `fetchFailureCount` counts failed attempts and observer results expose `failureCount` and `failureReason` accordingly.

**Cancellation.** `client.cancelQueries(filters)` aborts in-flight fetches for matching entries: the `queryFn`'s `signal` fires, the fetch promise rejects with a `CancelledError` (recognized by `isCancelledError`), and the entry returns to `fetchStatus: 'idle'` without recording an error status when no data had been produced.

**Garbage collection.** `gcTime` (milliseconds) bounds how long an entry with no observers survives: WHEN an entry has been unused past its `gcTime`, THEN it is removed from the cache and its data is no longer readable.

## Direct Cache Reads And Writes

Synchronous accessors read and write entry state without fetching.

**Reading.** `getQueryData(key)` returns the entry's data or `undefined`. `getQueryState(key)` returns the state object described above, or `undefined` for an absent entry. `getQueriesData(filters)` returns an array of `[queryKey, data]` pairs for every matching entry.

**Writing.** `setQueryData(key, updater)` writes data directly: a plain value replaces the current data, and a function receives the previous data and returns the next. WHEN the updater function returns `undefined`, THEN the write is skipped and the entry keeps its previous data; the call returns the value written, or `undefined` when skipped. Direct writes mark the entry as updated (its `dataUpdatedAt` advances) and count as successful data. `setQueriesData(filters, updater)` applies the same write to every matching entry.

**Activity counters.** `client.isFetching(filters)` returns the number of matching entries currently fetching; `client.isMutating(filters)` counts running mutations. Both return 0 when idle.

## Query Filters And Bulk Operations

One filter object shape selects cache slices for every bulk operation and for cache queries.

**Filter algebra.** A filter object accepts `queryKey` (matches entries whose key deep-prefix-matches, per `partialMatchKey`), `exact: true` (the key must hash-match exactly), `type` (`'active'` — entries with at least one subscribed observer, `'inactive'` — entries without, `'all'`), `stale` (`true` matches entries marked invalidated or observed-stale; `false` matches fresh ones), `fetchStatus`, and `predicate` (a function receiving the query object). `matchQuery(filters, query)` exposes the same decision as a standalone function.

**Cache queries.** `queryCache.find(filters)` returns the first matching query object or `undefined`; unlike the bulk operations, `find` treats its `queryKey` as an exact match unless `exact: false` is passed explicitly. `queryCache.findAll(filters)` uses ordinary prefix matching and returns all matches (all entries when the filter is empty).

**Invalidation.** `client.invalidateQueries(filters)` sets `isInvalidated` on every match and refetches the active ones; the returned promise settles when refetches complete. WHERE `refetchType: 'none'` is given, THEN entries are only marked and no fetch is issued. Invalidated entries match `stale: true` filters.

**Bulk fetch and removal.** `refetchQueries(filters)` refetches matching entries regardless of staleness. `removeQueries(filters)` deletes matching entries outright. `resetQueries(filters)` returns matching entries to their initial state — an entry without initial data reverts to `status: 'pending'` with `undefined` data — and refetches those with active observers.

**Cache event stream.** `queryCache.subscribe(listener)` delivers event objects with a `type` field and the affected `query`: `'added'` when an entry is created, `'updated'` on every state transition (fetch start, success, direct write, invalidation), and `'removed'` on deletion. The returned function unsubscribes.

## Query Observers

An observer projects one cache entry into a live result object with derived flags.

**Subscription lifecycle.** `new QueryObserver(client, options)` binds to the entry named by `options.queryKey`. `subscribe(listener)` starts observation — triggering a fetch when the entry has no fresh data — and returns an unsubscribe function; the listener receives a result object on every change. `getCurrentResult()` returns the latest result synchronously. `setOptions(options)` re-targets or reconfigures the observer in place. `refetch()` forces a fetch and resolves with the updated result.

**Result shape.** A result carries `status` and `fetchStatus` mirroring entry state, `data`, `error`, and derived booleans that must agree with them: `isPending`, `isSuccess`, `isError`, `isFetching`, `isStale`, `isFetched`, `isPlaceholderData`, plus `failureCount` and `failureReason` while attempts are failing. A successful fetch is observed as a transition from `{ status: 'pending', fetchStatus: 'fetching' }` to `{ status: 'success', fetchStatus: 'idle' }` with the data attached.

**Selection.** WHERE a `select` function is configured, THEN the result's `data` is the transformed value while the cache retains the raw fetched value — direct reads through `getQueryData` see the untransformed data.

**Initial and placeholder data.** `initialData` seeds the cache entry itself: the observer starts at `status: 'success'` with that data, and the seed is treated as a real data write (fresh within `staleTime`, `isPlaceholderData: false`). `placeholderData` never enters the cache: the observer reports `status: 'success'` with `isPlaceholderData: true` while the real fetch runs, then swaps to the fetched data with `isPlaceholderData: false`. Passing the exported `keepPreviousData` function as `placeholderData` makes an observer that is re-targeted to a new key keep showing the previous key's data (flagged as placeholder) until the new fetch settles.

**Enabling.** WHERE `enabled: false` is set, THEN subscribing never triggers a fetch — the result stays `status: 'pending'`, `fetchStatus: 'idle'` — while an explicit `refetch()` still fetches.

**Structural sharing.** WHEN a refetch produces data deep-equal to the current data, THEN the result's `data` keeps the previous object identity; deep-equal sub-trees of a changed value likewise keep their identities. The standalone `replaceEqualDeep(prev, next)` implements this rule: it returns `prev` itself when the two are deep-equal, and otherwise a copy of `next` in which every sub-tree that deep-equals its counterpart in `prev` is the `prev` sub-tree by reference.

**Disabled marker.** Passing the exported `skipToken` in place of a `queryFn` marks the query as unrunnable: subscribing does not fetch and the result stays pending and idle.

## Infinite Queries

Paged data assembles into one entry whose data is a pages structure.

**Shape.** `client.fetchInfiniteQuery(options)` requires `initialPageParam` and `getNextPageParam` and resolves with an object of two parallel arrays: `pages` (each page's data) and `pageParams` (the parameter each page was fetched with). The `queryFn` context additionally carries `pageParam`.

**Paging.** `new InfiniteQueryObserver(client, options)` observes the entry; its result exposes `hasNextPage`, `hasPreviousPage`, `fetchNextPage()`, and `fetchPreviousPage()`. `getNextPageParam(lastPage, allPages, lastPageParam, allPageParams)` computes the next parameter after each fetch; WHEN it returns `undefined`, THEN `hasNextPage` is `false` and `fetchNextPage()` must not grow the pages array. `getPreviousPageParam` mirrors this at the front: `fetchPreviousPage()` prepends a page and prepends its parameter to `pageParams`.

**Bounded windows.** WHERE `maxPages` is set, THEN the pages structure keeps at most that many pages: fetching beyond the bound drops pages from the opposite end, and `pageParams` stays aligned with `pages`.

## Mutations

Mutations are one-shot writes with a managed lifecycle and their own cache.

**Running a mutation.** `new MutationObserver(client, options)` takes `mutationFn`, optional `mutationKey`, retry options, and lifecycle callbacks. `mutate(variables)` returns a promise of the function's resolved value. The lifecycle order on success is exactly: `onMutate(variables)` first — its return value becomes the context — then the `mutationFn`, then `onSuccess(data, variables, context)`, then `onSettled(data, error, variables, context)`. On failure the order is `onMutate`, the function's attempts, `onError(error, variables, context)`, then `onSettled`, and `mutate` rejects with the error. The context produced by `onMutate` must be delivered to `onSuccess`, `onError`, and `onSettled`.

**Result and reset.** `getCurrentResult()` reports `status` (`'idle'`, `'pending'`, `'success'`, or `'error'`), `data`, `error`, `variables`, `failureCount`, and matching booleans such as `isSuccess`. `reset()` returns the observer to `status: 'idle'` with `undefined` data.

**Retry.** Mutation `retry` counts additional attempts exactly as for queries (default 0 in this environment); a mutation that fails with `retry: 1` invokes its function twice and reports `failureCount: 2`.

**Mutation cache.** Every run is recorded in the `MutationCache`; `getAll()` lists runs, and `find(filters)` / `findAll(filters)` match on `mutationKey` and predicates. `client.isMutating()` counts currently running mutations.

## Serialization And Managers

Cache content crosses process boundaries as plain objects; global managers expose focus, online, and batching state.

**Dehydration.** `dehydrate(client, options)` returns a plain object with `queries` and `mutations` arrays. Each dehydrated query carries its `queryKey`, `queryHash`, and `state`. By default only successful queries are included — `defaultShouldDehydrateQuery(query)` returns `true` for `status: 'success'` and `false` otherwise; WHERE a `shouldDehydrateQuery` predicate is supplied, THEN it replaces the default and may include error or pending entries.

**Hydration.** `hydrate(client, dehydratedState)` merges the dehydrated entries into a client's cache: hydrated entries are readable through `getQueryData`, and each entry's `dataUpdatedAt` is preserved exactly, so staleness decisions carry over.

**Notify batching.** `notifyManager.schedule(cb)` defers a callback: the callback must not run during the current synchronous execution, and deferred callbacks run in submission order once it completes. `notifyManager.batch(fn)` runs `fn` synchronously and groups every callback scheduled inside it into one deferred flush — no scheduled callback runs before `fn` returns.

**Focus and online state.** `focusManager.setFocused(boolean | undefined)` forces or (with `undefined`) releases the focus flag readable via `isFocused()`; the default in this environment is focused. `onlineManager.setOnline(boolean)` sets the flag readable via `isOnline()`. Both are process-wide singletons.

## State Model

The core state is one client-owned pair of tables plus process-wide managers:

- **Query cache** — hash-keyed query entries, each a state machine over `data`, `error`, `status`, `fetchStatus`, `dataUpdatedAt`, `dataUpdateCount`, `fetchFailureCount`, `isInvalidated`, plus the entry's `queryKey`/`queryHash` and its observer list.
- **Mutation cache** — recorded mutation runs with `status`, `data`, `error`, `variables`, and `failureCount`.
- **Managers** — focus flag, online flag, and the notify scheduler.

Public projections of that state:

1. **Imperative client methods** — fetch, ensure, prefetch, read, write, count.
2. **Observers** — live result objects per entry (plain, infinite, mutation) with derived flags.
3. **Cache queries and events** — `find`/`findAll` over the filter algebra and the subscribe event stream.
4. **Bulk operations** — invalidate, refetch, cancel, remove, reset over the same filter algebra.
5. **Serialization** — dehydrate/hydrate round trips.
6. **Key algebra** — `hashKey`, `partialMatchKey`, `matchQuery` as standalone functions.

All projections read and write the same tables: a mutation made through any one is immediately observable through every other.

## Error Semantics

| Condition | Outcome |
|---|---|
| `queryFn` rejects and retries are exhausted (`fetchQuery`, `refetch`, observer fetch) | promise rejects with the function's error; entry `status: 'error'`, `error` retained, `fetchFailureCount` counts attempts |
| `prefetchQuery` fetch fails | resolves `undefined`; entry left in `'error'` state; no rejection |
| In-flight fetch cancelled via `cancelQueries` | fetch promise rejects with `CancelledError`; `isCancelledError(err)` is `true`; `queryFn` `signal` aborted |
| `mutationFn` rejects and retries are exhausted | `mutate` rejects with the error; `onError` then `onSettled` called with the `onMutate` context; mutation `status: 'error'` |
| `getQueryData` / `getQueryState` on absent key | returns `undefined`; no throw |
| `setQueryData` functional updater returns `undefined` | write skipped; previous data kept |
| Observer with `enabled: false` or `skipToken` | no fetch; result pending and idle; no error |

Error message text is application-defined and never part of this contract; assertions rely on error identity, class, and state fields.

## Cross-View Invariants

1. For any entry, the data visible through `getQueryData`, the `data` of a subscribed observer's current result (absent `select`), the `state.data` of the query object returned by `queryCache.find`, and the entry's pair in `getQueriesData` must be the same value.
2. `hashKey` equality, `partialMatchKey` with `exact` semantics, cache entry identity, and fetch deduplication must agree: two keys with equal hashes address one entry, one in-flight fetch, and one query object.
3. A bulk operation and the standalone matcher must select the same set: an entry is affected by `invalidateQueries`/`refetchQueries`/`removeQueries`/`cancelQueries` with filters exactly when `matchQuery(filters, query)` returns `true` for its query object.
4. Every state transition observable through an observer result must also surface as an `'updated'` event on the cache subscription, and entry creation/deletion as `'added'`/`'removed'` — the event stream is a complete journal of the other projections.
5. A `dehydrate` → `hydrate` round trip into a fresh client must preserve, for every included query: the data returned by `getQueryData`, the `dataUpdatedAt` timestamp, and the key/hash identity used by filters.
6. Observer derived flags must agree with entry state in every reachable configuration: `isSuccess` iff `status: 'success'`, `isFetching` iff `fetchStatus: 'fetching'`, `isPlaceholderData` only while the displayed data is not cache data, and `failureCount` equal to the entry's recorded failed attempts.
7. After `client.clear()`, every projection must report emptiness: `findAll()` returns no entries, reads return `undefined`, `isFetching()` and `isMutating()` return 0, and `dehydrate` produces empty arrays.

## Public Interface

### Import Surface

```ts
import {
  QueryClient, QueryCache, MutationCache,
  QueryObserver, InfiniteQueryObserver, MutationObserver,
  Query, Mutation,
  dehydrate, hydrate, defaultShouldDehydrateQuery,
  hashKey, matchQuery, partialMatchKey, replaceEqualDeep,
  keepPreviousData, skipToken,
  CancelledError, isCancelledError,
  notifyManager, focusManager, onlineManager,
} from '@tanstack/query-core';
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `QueryClient` | class | Entry object owning both caches; fetch/read/write/bulk methods and defaults |
| `QueryCache` | class | Query entry table; `find`, `findAll`, `subscribe` |
| `MutationCache` | class | Mutation run table; `getAll`, `find`, `findAll` |
| `QueryObserver` | class | Live result projection of one query entry |
| `InfiniteQueryObserver` | class | Observer variant assembling paged data |
| `MutationObserver` | class | Runs mutations with lifecycle callbacks |
| `Query` | class | Cache entry object exposing `queryKey`, `queryHash`, `state` |
| `Mutation` | class | Recorded mutation run exposing `state` |
| `dehydrate` | function | Serializes cache content to a plain object |
| `hydrate` | function | Merges dehydrated content into a client |
| `defaultShouldDehydrateQuery` | function | Default inclusion predicate (successful queries) |
| `hashKey` | function | Deterministic, order-insensitive key hashing |
| `matchQuery` | function | Applies a filter object to one query |
| `partialMatchKey` | function | Deep-prefix key matching |
| `replaceEqualDeep` | function | Structural-sharing merge of two values |
| `keepPreviousData` | function | `placeholderData` strategy keeping prior data across key changes |
| `skipToken` | constant | Marker disabling a query in place of its function |
| `CancelledError` | class | Rejection type for cancelled fetches |
| `isCancelledError` | function | Type guard for `CancelledError` |
| `notifyManager` | object | Batching scheduler: `batch`, `schedule` |
| `focusManager` | object | Process focus flag: `setFocused`, `isFocused` |
| `onlineManager` | object | Process online flag: `setOnline`, `isOnline` |

### CLI Entry Points

There is no console script for this package. Programmatic use is through TypeScript/JavaScript imports.

## Appendix A: Environment

The working environment runs Node.js 22 on Linux without network access. The test toolchain is `vitest` with TypeScript; tests import the package under test by its package name `@tanstack/query-core`. No other third-party runtime packages are available or needed. There is no DOM: focus and online state change only through the manager setters, and the default retry count is 0.

The project must declare its packaging metadata in a standard `package.json` at the project root, exposing the package's public entry point under the name `@tanstack/query-core`, so the test suite can resolve `import { ... } from '@tanstack/query-core'`.

## Appendix B: Assessment Notes

Assessment exercises the public surface described in this document across several dimensions: client construction and key hashing; fetch semantics (staleness, deduplication, retry, cancellation, garbage collection); direct reads and writes; the filter algebra and bulk operations with the cache event stream; observer results including selection, placeholder and initial data, and structural sharing; infinite query paging; mutation lifecycles; dehydration round trips; and manager state. Tests are split into an atomic tier, each verifying a single behavior, and an integration tier composing several projections against shared state. Expected values in tests were produced by executing this specification's reference behavior — matching the letter of this document is the only reliable strategy.
