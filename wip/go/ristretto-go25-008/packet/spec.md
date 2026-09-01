# Ristretto Cache Forks

> This document defines the supported public behavior of cache forks for this
> module version.

## Context

Ristretto deliberately buffers writes and access samples. Applications still
sometimes need an in-process branch point: trying a different warm-up plan,
handing a stable generation to another component, or comparing two capacity
policies without replaying the original workload.

`Fork` creates that branch. It returns another ordinary `Cache` representing
one coherent point in the source cache's history. It is not a continuing
replica, an operation log, or a deep copier for application values.

## Use

```go
primary, err := ristretto.NewCache(&ristretto.Config[string, *Record]{
	NumCounters: 10_000,
	MaxCost:     1_024,
	BufferItems: 64,
})
if err != nil {
	return err
}
defer primary.Close()

primary.Set("profile:42", record, 8)
branch := primary.Fork()
if branch == nil {
	return errors.New("cache is unavailable")
}
defer branch.Close()
```

The returned cache uses the existing `Cache` API. No fork-specific reader,
commit method, artifact format, or background service is introduced.

## Behavior

### Generation boundary

A successful fork contains all cache work submitted before its selected
boundary. Buffered admission, replacement, deletion, access sampling, cost
calculation, expiration, and resulting callbacks that belong before the
boundary are complete before `Fork` returns. Calls concurrent with a fork may
fall on either side, but the child must represent one legal placement across
contents, capacity, leases, admission history, and lifecycle state.

Ordinary calls retain their buffered behavior. `Fork` does not make later
`Set`, `Get`, or `Del` operations synchronous.

### Behavioral continuation

The child begins as the same cache generation, not merely the same collection
of currently visible values. Given equivalent operations after the fork, the
two caches make equivalent admission and eviction decisions. Accesses before
the boundary therefore continue to matter when later pressure is applied,
including a partial access batch that had not reached its normal drain size.

Capacity, admitted costs, custom key hashing, value-based costing, update
decisions, and lease deadlines continue with the forked generation. A lease is
not restarted by the fork. Work already rejected or dropped does not become
owned merely because a fork occurs.

Values have the same copy semantics as `Set`: the cache-owned association is
copied, while a pointer, slice, map, or other reference-bearing value is not
recursively cloned.

### Independent ownership

After return, source and child have independent cache ownership and policy
state. Reads, writes, deletions, capacity changes, expiration cleanup, clear,
and close in either cache do not perform the corresponding operation in the
other. Equal post-fork workloads may keep them aligned; different workloads
may cause them to diverge.

Configured callbacks remain applicable to later events in each cache, but
creating the child is not itself an admission, update, rejection, eviction, or
exit event. The child starts a fresh metrics lifetime. Source metrics are not
changed by copying, and subsequent metrics are accumulated by the cache in
which the operation occurs.

### Lifecycle

Forking a nil or closed cache returns `nil`. A successful child is open even if
the source is closed immediately afterwards. Closing or clearing one
generation releases only that generation's ownership and leaves the other
usable. Repeated forks create independent siblings at their respective source
boundaries.

## Contract

The observable contract is behavioral rather than representational:

1. The child begins with the source's live associations, admitted costs,
   capacity, remaining leases, and policy history at one boundary.
2. Equivalent continuation workloads produce equivalent visible values and
   capacity outcomes in source and child.
3. Divergent continuation workloads affect only the generation receiving
   them.
4. Fork creation emits no cache event and does not inherit metric totals.
5. A child remains usable after any later source lifecycle transition.

No private map, counter sketch, queue, shard, timer bucket, or sampling layout
is part of the public API.

## Reference

The import surface remains `github.com/dgraph-io/ristretto/v2`. Within that
package the additive method is:

```go
func (c *Cache[K, V]) Fork() *Cache[K, V]
```

The feature is additive. Existing constructors, configuration, buffering,
callbacks, metrics, TTL behavior, and generic key/value support remain source
compatible.

## Compatibility guidance

Compatibility checks should generate ordinary cache histories and compare
public continuations rather than inspect private state. Useful dimensions
include buffered and admitted writes, hits and misses, competing costs,
replacement decisions, finite leases, capacity changes, lifecycle branches,
and explicitly synchronized concurrent calls. Observations should use the
existing cache methods, callbacks, and metrics.

## Environment

The evaluation environment is Linux amd64 with Go 1.25.11 and a pinned offline
module closure. Workflows are process-local and use bounded monotonic timing.
They require no network, service, credential, container, fixed port, or shared
filesystem location.
