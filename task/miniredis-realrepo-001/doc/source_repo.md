# Source Repository

## Identity

- Repository: `Tsu-HaoLiu/Micro-RedisDB`
- URL: https://github.com/Tsu-HaoLiu/Micro-RedisDB
- Secondary reference: `coleifer/simpledb` (https://github.com/coleifer/simpledb)
- Pinned commit: (TBD — latest main at time of construction)
- Local checkout: (TBD)
- Source language: Python
- Benchmark case: `miniredis-realrepo-001`

## Public Evidence Used

- `Tsu-HaoLiu/Micro-RedisDB` README: miniature Redis-like in-memory key-value store, supports SET/GET/DELETE/FLUSH/MGET/MSET, multi-threaded request handling via gevent.
- `coleifer/simpledb` README: miniature Redis-like server, basic key-value operations, pub/sub support.
- `coleifer/simpledb/__init__.py`: core command implementations for reference semantics (type checking, list/set operations, expiry behavior).

## Reconstruction Boundary

The candidate does not rebuild the TCP server or client protocol. The benchmark will ask for a compact Python 3.11 CLI named `miniredis.py` that manages an in-memory data structure store supporting four types (string, list, set, hash) with key expiry. Hidden scoring should evaluate user-visible behavior: type-appropriate operations, data structure semantics (list ordering, set deduplication, hash field access), type mismatch error handling, key expiry, and cross-type consistency.

## Why This Case

A Redis-inspired in-memory data structure store is a natural step up in complexity from the existing `minikv-realrepo-001` (which covers only string and integer types):

- **multi-type state**: four distinct data types (string, list, set, hash) each with their own creation, mutation, and access semantics;
- **type enforcement**: operations must validate key types and fail on mismatches, a rich source of `error_atomicity` and `global_invariant` tests;
- **data structure semantics**: list ordering, set deduplication, and hash field-value mapping create complex `state_accumulation` scenarios;
- **cross-type composition**: KEYS, TYPE, EXPIRE, DEL, FLUSHDB operate across all types, testing `cross_feature_dataflow` and `boundary_crossing`;
- **operation order**: push/pop direction on lists, EXPIRE/SET ordering on expiry, and DEL→recreate with new type all test `operation_order_sensitivity`.

The fairness risk is manageable: the public packet defines a compact but realistic subset (4 types, no sorted sets/streams/pubsub, no networking) that exposes meaningful cross-feature interactions while remaining within reach of current models.

This task complements the existing benchmark cases:

| Task | State paradigm | Key novelty |
| --- | --- | --- |
| `zk-realrepo-001` | Filesystem (notes/tags/links) | File-based persistence, config-driven behavior |
| `sqlite-utils-realrepo-001` | SQL database (CRUD/extract/transform) | Schema evolution, FTS, compound keys |
| `miniurlutils-realrepo-001` | In-memory parsing/mutation (URL) | Component parsing, normalization, navigation |
| `minikv-realrepo-001` | In-memory KV (string+integer) | Expiry, persistence, basic type system |
| `miniredis-realrepo-001` | In-memory data structures (4 types) | Multi-type enforcement, list/set/hash semantics |
