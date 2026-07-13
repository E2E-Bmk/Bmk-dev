# Source Repo: Walrus

- Repository: `huangshand/walrus`
- Benchmark case: `minikv-realrepo-submit`
- Source surface: in-memory key-value/data-structure API with strings, counters, lists, sets, hashes, expiry, and pickle persistence.
- Origin packet: `tyx010/tyx-Bmk-dev`

## Selected Surface

This task uses a Python class API, `QueueServer`, with shared state across key-value, list, set, hash, expiry, flush, and persistence operations.

## Rationale

The intended compositional contract is a single type-tagged key namespace with consistent wrong-type errors, lazy expiry, and persistence. Candidate runs showed the API is too directly implementable for Codex, and OpenHands + DeepSeek failures were mostly unit-level feature issues rather than system-level contract failures.
