# Ristretto Atomic Batch Extension Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`github.com/dgraph-io/ristretto/v2` is a concurrent in-memory cache package that combines buffered writes, cost-based capacity, optional TTLs, callbacks, and metrics. This extension adds conditional multi-key mutations and ordered multi-key snapshots without replacing the package's existing cache behavior.

An atomic batch evaluates an ordered list against a virtual cache state and publishes the final per-key effects at one visibility boundary. The feature is intended for workflows in which related cached facts must move between valid states together.

## Non-Goals

- This specification does not require persistence, distributed coordination, or recovery after process termination.
- This specification does not define transactions that remain open across multiple method calls.
- This specification does not require an admission-policy decision or eviction of unrelated entries during a batch commit.
- This specification does not define value equality or compare-and-swap guards.
- This specification does not require deterministic ordering from `IterValues`.

## Representative Workflows

The first workflow replaces a pair of related entries only while the source is present and the destination is absent. A successful return means ordinary cache reads observe the final state.

```go
result := cache.ApplyBatch([]ristretto.BatchItem[string, Record]{
    {
        Operation: ristretto.BatchDelete,
        Key:       "active:user-7",
        Guard:     ristretto.BatchRequirePresent,
    },
    {
        Operation: ristretto.BatchSet,
        Key:       "archived:user-7",
        Value:     archived,
        Cost:      4,
        Guard:     ristretto.BatchRequireAbsent,
    },
})
if !result.Applied {
    log.Printf("batch stopped at item %d: %v", result.FailedIndex, result.Failure)
}
```

The second workflow obtains a single ordered snapshot for a caller-provided key list. Duplicate keys remain duplicate positions, and missing entries remain represented in the result.

```go
snapshot := cache.GetMany([]string{"profile:7", "quota:7", "profile:7"})
for _, entry := range snapshot {
    if entry.Found {
        use(entry.Key, entry.Value, entry.RemainingTTL)
    }
}
```

## Ordered Batch Planning

Batch planning defines which logical state each operation sees and prevents a late failure from exposing an early mutation.

**Empty and missing receivers.** When `ApplyBatch` receives an empty or nil item slice, it must return a successful `BatchResult` with `Applied` true, `FailedIndex` equal to `-1`, `Failure` equal to `BatchSucceeded`, and `Effects` equal to zero. When a non-empty batch is invoked on a nil or closed cache, it must fail at index zero with `BatchCacheClosed` and must not mutate state.

**Operations.** A `BatchItem` with `Operation` equal to `BatchSet` must stage its `Value`, effective `Cost`, and TTL for its `Key`. A `BatchItem` with `Operation` equal to `BatchDelete` must stage absence for its key; deleting a logically missing key under `BatchAny` must be a successful no-op. When all items validate, `ApplyBatch` must publish the final state for every touched key before any concurrent ordinary read or `GetMany` call returns.

**Failure atomicity.** If any item fails validation, a guard, update policy, hash-conflict check, or capacity reservation, then the cache must retain the state, TTLs, costs, metrics, and callbacks that existed before the batch. Accepted buffered writes that precede the batch must be applied before its first guard is evaluated.

## Guards and Repeated Keys

Guards and repeated keys make a batch an ordered state transition rather than an unordered collection of writes.

**Guard evaluation.** `BatchAny` must impose no presence precondition. `BatchRequirePresent` must succeed only when the key is logically present at that item position. `BatchRequireAbsent` must succeed only when the key is logically absent at that item position. Expired entries must be logically absent for both guards.

**Virtual state.** When a key occurs more than once, each later item must observe the staged result of earlier items for that key. The final set determines the committed value, cost, and TTL; the final delete determines absence. `Effects` must equal the number of distinct touched primary hashes, including a successful delete of a missing key.

**Compacted callbacks.** Repeated operations on one key must publish only the original-to-final transition. Intermediate staged values must not trigger callbacks or metric changes.

## Capacity, Cost, and Update Policy

Capacity planning applies existing cache configuration to the complete final batch rather than to each operation independently.

**Effective cost.** When a set item has nonzero `Cost`, that value must be its user cost. When a set item has zero `Cost` and `Config.Cost` is configured, the cache must invoke `Config.Cost` once for that staged value. Unless `Config.IgnoreInternalCost` is true, the cache must add the package's ordinary internal item cost in the same way as `Set`.

**Net reservation.** The capacity decision must subtract the costs of deleted or replaced original entries and add only the final costs of staged entries. When the final used cost exceeds `MaxCost`, the whole batch must fail with `BatchCapacityExceeded`; it must not evict unrelated entries and must not invoke `OnReject`.

**Update policy.** When a set replaces a logically present value and `Config.ShouldUpdate` is configured, the callback must receive the staged new value and the current virtual previous value. If it returns false, the whole batch must fail with `BatchUpdateRejected`. Repeated sets must therefore pass each earlier staged value as the previous value for the next update decision.

## TTL and Hash Identity

TTL and hash rules determine logical presence and ensure that atomic planning respects the cache's configured key identity.

**TTL assignment.** A set item with zero `TTL` must create a permanent entry. A set item with positive `TTL` must use one shared batch planning time as the TTL origin. A set item with negative `TTL` must fail with `BatchInvalidTTL`. After expiration, `Get`, `GetTTL`, and `GetMany` must all report the entry as missing.

**Hash identity.** Every item and snapshot position must use `Config.KeyToHash` when it is configured and the package's normal key hashing otherwise. If two logical keys in a batch resolve to the same primary hash but different conflict hashes, or an item conflicts with the stored conflict hash, the whole batch must fail with `BatchHashConflict`.

## Ordered Snapshot Reads

`GetMany` provides a single visibility boundary while retaining the caller's positional key list.

**Shape and values.** `GetMany` must return exactly one `BatchValue` per input key in the same order. Duplicate keys must produce duplicate positions. Each result must copy its input `Key`; `Found` must distinguish a stored zero value from a missing value.

**TTL projection.** A permanent or missing entry must have zero `RemainingTTL`. A live expiring entry must have a positive `RemainingTTL` no greater than its configured TTL. Expired entries must have `Found` false and the zero value of `V`.

**Lifecycle.** When `GetMany` is called on a nil or closed cache, it must preserve result length, order, and keys while returning every position as not found. Each live lookup position must update frequency accounting and optional hit/miss metrics as an independent `Get` would.

## Callbacks and Metrics

Callbacks and metrics project the committed transition and must never reveal discarded virtual states.

**Exit behavior.** When a committed batch replaces or deletes a live original value, `OnExit` must receive that original value exactly once. When a touched original is expired, its normalization must use the ordinary eviction callback path. A staged value that is later replaced or deleted inside the same batch must not invoke `OnExit`, `OnEvict`, or `OnReject`.

**Rejected batches.** When a batch fails, it must not invoke callbacks for any staged effect and must not increment committed-key or committed-cost metrics.

**Committed metrics.** When metrics are enabled, each final new entry must count as one added key and each final replacement must count as one updated key. Every `GetMany` position must count independently as a hit or miss.

## State Model

The cache has four user-observable state layers:

1. Accepted ordinary writes wait in the existing write buffer until processing or `Wait`.
2. An `ApplyBatch` call owns an isolated virtual state while it evaluates ordered operations.
3. A successful commit publishes final stored values, TTL metadata, and policy costs as one visibility boundary.
4. Ordinary reads, ordered snapshots, iteration, callbacks, capacity methods, and metrics project the committed state.

Multiple `ApplyBatch` calls must serialize their planning and commit boundaries. Ordinary `Set`, `SetWithTTL`, and `Del` calls that begin while a batch is planning must not cross its publication boundary.

## Error Semantics

| Condition | `BatchFailure` | Required result |
|---|---|---|
| Non-empty batch on nil or closed cache | `BatchCacheClosed` | Failure at index zero |
| Unknown operation value | `BatchInvalidOperation` | Failure at the item's index |
| Unknown guard value | `BatchInvalidGuard` | Failure at the item's index |
| Negative set TTL | `BatchInvalidTTL` | Failure at the item's index |
| Negative explicit or dynamically calculated cost | `BatchInvalidCost` | Failure at the item's index |
| Presence guard is false in virtual state | `BatchConditionFailed` | Failure at the item's index |
| `Config.ShouldUpdate` rejects a replacement | `BatchUpdateRejected` | Failure at the item's index |
| Primary-hash identity has incompatible conflict hash | `BatchHashConflict` | Failure at the first conflicting index |
| Final state exceeds `MaxCost` | `BatchCapacityExceeded` | Failure at an item whose final cost makes the plan impossible |

A failed `BatchResult` must have `Applied` false, `Effects` zero, and must identify the first failing item through `FailedIndex` and `FailedKey`. A successful result must have `Applied` true, `FailedIndex` equal to `-1`, a zero `FailedKey`, and `Failure` equal to `BatchSucceeded`.

## Cross-View Invariants

1. After a successful batch, `Get` and `GetMany` must agree on value presence and value content for every touched key.
2. A `BatchValue` with `Found` true must represent the same committed value returned by an ordinary `Get` at that visibility boundary.
3. `IterValues` must include each live final batch value once and must exclude values deleted by the batch.
4. `RemainingCost` must equal `MaxCost` minus the policy cost of the final committed entries after the batch.
5. `GetTTL` and `BatchValue.RemainingTTL` must agree on permanent, live expiring, and expired states.
6. Callback arguments must describe original committed values leaving the cache, never intermediate staged values.
7. Metrics must count only committed final mutations while snapshot hit/miss metrics must count every requested position.
8. Concurrent readers must observe either the complete pre-commit state or the complete post-commit state, never a partial combination.

## Public Interface

### Import Surface

```go
import "github.com/dgraph-io/ristretto/v2"
```

The package exports the retained cache surface `Key`, `Cache`, `Config`, `Item`, `Metrics`, and `NewCache`; retained cache methods used by this extension are `Set`, `SetWithTTL`, `Wait`, `Get`, `Del`, `GetTTL`, `IterValues`, `Close`, `MaxCost`, and `RemainingCost`. Retained metric methods used by the observable contract are `Hits`, `Misses`, `KeysAdded`, and `KeysUpdated`. The new exported surface is listed below.

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `BatchOperation` | type | Identifies a set or delete operation |
| `BatchSet` | constant | Selects a staged set |
| `BatchDelete` | constant | Selects a staged delete |
| `BatchGuard` | type | Selects a presence precondition |
| `BatchAny` | constant | Applies without a presence precondition |
| `BatchRequirePresent` | constant | Requires virtual presence |
| `BatchRequireAbsent` | constant | Requires virtual absence |
| `BatchFailure` | type | Classifies a batch result |
| `BatchSucceeded` | constant | Identifies a successful result |
| `BatchCacheClosed` | constant | Identifies an unavailable receiver |
| `BatchInvalidOperation` | constant | Identifies an unknown operation |
| `BatchInvalidGuard` | constant | Identifies an unknown guard |
| `BatchInvalidTTL` | constant | Identifies a negative set TTL |
| `BatchInvalidCost` | constant | Identifies a negative effective cost |
| `BatchConditionFailed` | constant | Identifies a false presence guard |
| `BatchUpdateRejected` | constant | Identifies an update-policy rejection |
| `BatchHashConflict` | constant | Identifies incompatible conflict hashes |
| `BatchCapacityExceeded` | constant | Identifies insufficient batch capacity |
| `BatchItem` | generic struct | Carries one ordered mutation through `Operation`, `Key`, `Value`, `Cost`, `TTL`, and `Guard` |
| `BatchResult` | generic struct | Reports `Applied`, `FailedIndex`, `FailedKey`, `Failure`, and distinct-key `Effects` |
| `BatchValue` | generic struct | Reports `Key`, `Value`, `Found`, and `RemainingTTL` for one snapshot position |
| `Cache.ApplyBatch` | method | Plans and atomically publishes an ordered mutation slice |
| `Cache.GetMany` | method | Returns an ordered duplicate-preserving snapshot slice |

### CLI Entry Points

There is no console command for this package. Programmatic use is through Go imports.

## Appendix A: Environment

The working environment runs Go 1.24 or newer on Linux without network access during assessment. The starter module retains its declared dependencies: `github.com/cespare/xxhash/v2`, `github.com/dgryski/go-farm`, `github.com/dustin/go-humanize`, and `golang.org/x/sys`. The project must retain standard Go module metadata in `go.mod` at the project root.

## Appendix B: Assessment Notes

Assessment covers public compilation, single-operation boundaries, ordered virtual-state behavior, all-or-nothing failures, capacity and callback accounting, TTL projections, custom hashing, ordinary-cache interoperability, and concurrent visibility. Each independently named behavior contributes one result; formatting, private fields, and internal algorithm choices are not assessed.
