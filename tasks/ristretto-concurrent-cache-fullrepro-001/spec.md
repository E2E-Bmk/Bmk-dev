# Ristretto Concurrent Cache Reimplementation Specification

## Product Overview

Reimplement the public concurrent-cache behavior of `github.com/dgraph-io/ristretto/v2`. The module provides a generic, goroutine-safe, cost-bounded cache with asynchronous buffered writes, explicit synchronization through `Wait`, expiration, deletion, callbacks, configurable hashing and costing, iteration, dynamic capacity, and optional metrics.

The root package name is `ristretto`. The solution must be a self-contained Go module with no external dependencies.

## Scope

The retained surface is `Config`, `Cache`, `Item`, `NewCache`, the cache methods listed below, and observable `Metrics` counters. Internal TinyLFU sketches, ring buffers, shards, policy types, histogram representation, exact eviction victim selection, private flags, and memory layout are excluded.

Keys used by assessment are ordinary comparable Go values, including strings and integers. Values include scalars, structs, pointers, and slices. The implementation may use any safe internal hashing and eviction design that obeys the observable contracts.

## Representative Workflows

A caller constructs a cache, enqueues writes, calls `Wait`, and observes synchronized values through `Get`, `GetTTL`, or `IterValues`. Other assessed workflows update or delete entries, change capacity, clear and reuse the cache, and close it safely.

With TTL, costs, callbacks, custom hashing, or metrics enabled, the same lifecycle preserves the ordering and visibility rules below. Concurrent readers and writers retain valid values and consistent ownership transitions.

## Configuration

`NewCache` returns a usable cache when `NumCounters`, `MaxCost`, and `BufferItems` are positive. A zero or negative value for any of those three fields returns a non-nil error and no cache. Exact error wording is not required.

`Metrics: true` installs a non-nil metrics collector. When false, `Cache.Metrics` is nil and cache operations remain safe. `TtlTickerDurationInSec` controls background expiry cleanup; zero selects an implementation default.

`KeyToHash`, when non-nil, is used by every key-based operation. The primary hash chooses the storage slot and the conflict hash validates the occupant. Keys intended to coexist must have distinct primary hashes; when primary hashes collide, a different conflict hash prevents the wrong value from being returned. `Cost`, when non-nil, supplies the item cost when `Set` or `SetWithTTL` receives cost zero. `IgnoreInternalCost` prevents implementation overhead from being added to caller costs.

## Buffered Writes and Visibility

`Set` and `SetWithTTL` enqueue work. Returning true means the write entered the processing path or updated an existing stored value; it does not promise immediate visibility or final admission. Returning false means a new write was dropped or the cache was unavailable.

`Wait` blocks until all writes accepted before the call have been processed. After `Set` returns true followed by `Wait`, `Get` observes the value unless it expired or was rejected/evicted to satisfy capacity. Assessment configurations provide adequate capacity except in explicit admission/eviction tests.

Updates to an existing key replace its value and cost after `Wait`. Operation order is preserved for an accepted set followed by delete. Concurrent calls must not race, panic, corrupt state, or return a value belonging to another key.

## Lookup, Mutation, and Iteration

`Get` returns `(value, true)` for a present, unexpired key and the zero value plus false otherwise. A stored nil pointer is a successful hit. `Del` makes a present key unavailable and is harmless for a missing key.

`Clear` removes all entries, resets policy state, and clears enabled metrics. The cache remains usable afterward. `IterValues` visits each value present during its non-atomic traversal at most once, in unspecified order, and stops immediately when the callback returns true. A nil or closed cache performs no callbacks.

`GetTTL` returns `(0, true)` for a present non-expiring item. For a present expiring item it returns a positive remaining duration and true. Missing or expired items return `(0, false)`.

## Expiration

`SetWithTTL` with a positive duration creates an expiring entry. It is visible before expiry after `Wait` and unavailable after its deadline even if background cleanup has not yet run. TTL zero is non-expiring and is equivalent to `Set`. A negative TTL is a no-op that returns false.

Updating an item replaces its expiration: a TTL entry may become persistent, a persistent item may gain a TTL, and a refreshed positive TTL starts from the update. Expiration and explicit deletion must not later remove a newer replacement for the same key.

## Cost, Admission, and Eviction

The cache must keep admitted cost within its current maximum after buffered work is processed. With `IgnoreInternalCost: true`, positive caller costs and `Cost` callback results are the units used by `MaxCost` and `RemainingCost`.

An item whose cost exceeds the maximum is rejected. When admitting an item would exceed capacity, the cache rejects it or evicts one or more older/lower-value entries. Exact victim choice is not compared unless only one feasible victim exists. Rejected and evicted items are not returned by `Get` after `Wait`.

`MaxCost` returns the configured current maximum. `UpdateMaxCost` changes it for later admission and capacity decisions. `RemainingCost` reports maximum minus admitted cost and must remain between zero and `MaxCost` after `Wait`.

## Callbacks

`OnEvict` receives an `Item` describing each admitted entry removed by capacity eviction, expiry cleanup, clearing, or closing where the reference behavior classifies the removal as eviction. Its exported `Key`, `Conflict`, `Value`, `Cost`, and `Expiration` fields describe the removed entry.

`OnReject` receives an item rejected by admission. `OnExit` receives values leaving cache ownership because of rejection, replacement, deletion, eviction, clearing, or closing. Asynchronous deletion bookkeeping is permitted to deliver an additional zero value when its second removal step finds no stored value; assessment counts the actual removed value rather than requiring an exact total callback count for deletion. Callbacks must not run for a negative-TTL no-op. Exact callback goroutine identity and ordering between different keys are not required; `Wait`, `Clear`, or `Close` completes the callbacks caused by work it drains.

`ShouldUpdate(cur, prev)` is consulted for an existing key. When it returns false the stored value, cost, and TTL remain unchanged. When true the update proceeds. New keys do not require approval.

## Metrics

When enabled, successful `Get` calls increment `Hits`; unsuccessful calls increment `Misses`; `Ratio` equals hits divided by hits plus misses and is zero before accesses. Admission, update, eviction, cost, dropped-set, rejected-set, and get-buffer counters are exposed through `KeysAdded`, `KeysUpdated`, `KeysEvicted`, `CostAdded`, `CostEvicted`, `SetsDropped`, `SetsRejected`, `GetsDropped`, and `GetsKept`.

Counters are safe under concurrency. `Metrics.Clear` resets observable counters and ratio. `Metrics.String` returns a non-empty stable summary containing the counter names when metrics are enabled. Exact spacing is not required.

## Lifecycle

`Close` drains/removes entries, stops background work, and is idempotent. After close, `Set` and `SetWithTTL` return false; `Get` and `GetTTL` report absence; `Del`, `Clear`, `Wait`, `UpdateMaxCost`, and `IterValues` do not panic. Calling methods on a nil `*Cache` follows the same no-op/zero-result behavior documented by their signatures, except construction is not involved.

## State Model

A cache moves from configured and open, through accepted buffered operations, to synchronized visible state after `Wait`. Each admitted entry has one current value, cost, and optional expiration. Clear returns the open cache to empty state; Close moves it permanently to closed state.

The following views must agree after synchronization:

- A value returned by `Get` must be included by `IterValues` unless concurrent mutation occurs.
- `GetTTL` reports found exactly when the corresponding unexpired entry is obtainable by `Get`.
- `RemainingCost` and enabled cost metrics reflect the same admitted entries used by eviction decisions.
- Delete, expiry, clear, and close remove values from lookup and invoke applicable exit callbacks; deletion may additionally report the zero value during asynchronous bookkeeping.
- Concurrent operations on distinct keys and repeated operations on one key preserve key identity and never expose torn values.

## Cross-View Invariants

After `Wait`, `Get`, `GetTTL`, and `IterValues` agree about whether a live entry exists. Expired entries are absent from all three views. Updates change the value and cost as one logical replacement, while deletion, clearing, eviction, expiry, and closing each release cache ownership exactly once.

Cost views remain bounded by the active maximum, metrics reflect the corresponding accepted operations, and a custom hash function is used consistently by reads, writes, deletion, TTL lookup, and related views.

## Error Semantics

Invalid construction returns errors as specified above. Ordinary cache operations do not return errors and must not panic for missing keys, repeated deletion, repeated clear, repeated close, nil receivers, closed receivers, dropped writes, rejected items, or expired items. Callback code is caller-controlled; behavior after a callback itself panics is outside scope.

## Public Interface

The module is imported as `github.com/dgraph-io/ristretto/v2`, and the root package name is `ristretto`.

The required root surface is:

```go
type Key interface { comparable }

type Config[K Key, V any] struct {
    NumCounters int64
    MaxCost int64
    BufferItems int64
    Metrics bool
    OnEvict func(*Item[V])
    OnReject func(*Item[V])
    OnExit func(V)
    ShouldUpdate func(cur, prev V) bool
    KeyToHash func(K) (uint64, uint64)
    Cost func(V) int64
    IgnoreInternalCost bool
    TtlTickerDurationInSec int64
}

type Item[V any] struct {
    Key uint64
    Conflict uint64
    Value V
    Cost int64
    Expiration time.Time
}

func NewCache[K Key, V any](*Config[K, V]) (*Cache[K, V], error)
func (*Cache[K, V]) Set(K, V, int64) bool
func (*Cache[K, V]) SetWithTTL(K, V, int64, time.Duration) bool
func (*Cache[K, V]) Get(K) (V, bool)
func (*Cache[K, V]) GetTTL(K) (time.Duration, bool)
func (*Cache[K, V]) Del(K)
func (*Cache[K, V]) Wait()
func (*Cache[K, V]) Clear()
func (*Cache[K, V]) Close()
func (*Cache[K, V]) IterValues(func(V) bool)
func (*Cache[K, V]) MaxCost() int64
func (*Cache[K, V]) UpdateMaxCost(int64)
func (*Cache[K, V]) RemainingCost() int64

func (*Metrics) Hits() uint64
func (*Metrics) Misses() uint64
func (*Metrics) KeysAdded() uint64
func (*Metrics) KeysUpdated() uint64
func (*Metrics) KeysEvicted() uint64
func (*Metrics) CostAdded() uint64
func (*Metrics) CostEvicted() uint64
func (*Metrics) SetsDropped() uint64
func (*Metrics) SetsRejected() uint64
func (*Metrics) GetsDropped() uint64
func (*Metrics) GetsKept() uint64
func (*Metrics) Ratio() float64
func (*Metrics) Clear()
func (*Metrics) String() string
```

Additional upstream-compatible declarations are permitted.

## Non-Goals

- Exact TinyLFU sketch contents, sampling algorithm, access-buffer batch timing, shard count, hashes, private policy state, or exact victim selection.
- Throughput, allocation count, cache-line layout, internal item cost when it is not ignored, and exact metrics summary formatting.
- Internal `z` helpers and histogram representation.
- Persistence, distributed caching, serialization, loader functions, filesystem access, and networking.

## Environment

The submission must declare module `github.com/dgraph-io/ristretto/v2`, build on Linux with Go 1.26.6, and run fully offline without external dependencies.

## Assessment Notes

Tests use `Wait` after accepted writes, bounded timeouts for TTL, deterministic costs, and generous buffers except where drop behavior is explicitly exercised. No test depends on map iteration order, wall-clock timestamps, exact error strings, or a particular internal eviction algorithm.
