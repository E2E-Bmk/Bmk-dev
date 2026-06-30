# Source Repository

## Identity

- Repository: `coleifer/simpledb`
- URL: https://github.com/coleifer/simpledb
- Pinned commit: (TBD — latest main at time of construction)
- Local checkout: (TBD)
- Source language: Python
- Benchmark case: `minikv-realrepo-001`

## Public Evidence Used

- `README.md`: product narrative — a miniature Redis-like server, basic key-value operations, pub/sub support, simplicity focus.
- `simpledb/__init__.py`: core implementation with SET, GET, DELETE, EXISTS, INCR, DECR, EXPIRE, TTL, KEYS, FLUSH, SAVE, LOAD commands.
- `simpledb/server.py`: TCP server implementation (not used for benchmark — CLI only).
- `simpledb/client.py`: client implementation for reference (not used directly).

## Reconstruction Boundary

The candidate does not rebuild the TCP server or client protocol. The benchmark will ask for a compact Python 3.11 CLI named `minikv.py` that manages an in-memory key-value store with optional JSON file persistence. Hidden scoring should evaluate user-visible behavior: setting/getting keys, bulk operations, integer counters, expiry with TTL, key enumeration with glob patterns, type metadata, and persistence.

## Why This Case

A key-value store is a classic "mini" systems project that exercises cross-feature state dependencies:

- string data flows from SET through GET, EXISTS, DELETE, KEYS, MGET, SAVE/LOAD;
- integer counters create a distinct type that interacts with INCR/DECR error semantics;
- expiry creates time-dependent state that interacts with GET, EXISTS, TTL, PERSIST, and KEYS filtering;
- persistence (SAVE/LOAD) must capture the complete state including types and expiry;
- FLUSH clears all state but does not affect the persisted file until the next SAVE.

The fairness risk is manageable: the public packet defines a compact subset (string+integer types only, no lists/sets/hashes, no networking) that is well within reach of current models while still exposing the "unit pass / system fail" gap.

This task complements the three existing benchmark cases:

- `zk-realrepo-001` exercises filesystem state (notes, tags, links, config);
- `sqlite-utils-realrepo-001` exercises SQL database state (insert, upsert, extract, transform, FTS);
- `miniurlutils-realrepo-001` exercises in-memory parsing and mutation (URL components);
- `minikv-realrepo-001` exercises in-memory key-value state with expiry and persistence, completing the coverage of state management paradigms.
