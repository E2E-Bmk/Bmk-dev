# Spec Test Map — Ristretto v1

| Node range | Clauses | Source | Focus |
|---|---|---|---|
| `atomic::TestRST001`–`TestRST011` | configuration, metrics, cost projection | generated | constructor validation and capacity views |
| `atomic::TestRST012`–`TestRST016` | lifecycle | generated | nil-cache receiver safety |
| `atomic::TestRST017`–`TestRST026` | buffered writes, TTL, values | generated | visibility, update/delete/clear, expiration and nil values |
| `atomic::TestRST027`–`TestRST035` | iteration, hashing, admission, metrics | generated | traversal, collisions, costs, update policy and counters |
| `integration::TestRST036`–`TestRST044` | cross-view and lifecycle workflows | generated | TTL transitions, ordering, reuse and close behavior |
| `integration::TestRST045`–`TestRST052` | callbacks, capacity and custom hooks | generated | ownership exits, eviction, resizing, cost and hash hooks |
| `integration::TestRST053`–`TestRST060` | concurrency and composed behavior | generated | concurrent access, batch visibility, metrics and closed iteration |
