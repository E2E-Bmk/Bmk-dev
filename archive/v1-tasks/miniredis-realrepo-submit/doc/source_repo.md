# Source Repo: Redis

- Repository: `redis/redis`
- Benchmark case: `miniredis-realrepo-submit`
- Source surface: Redis-style string, list, set, hash, key expiry, key enumeration, and database management commands.
- Origin packet: `tyx010/tyx-Bmk-dev`

## Selected Surface

This task uses a compact Redis-like CLI with a shared type-tagged key namespace. The public packet asks candidates to implement string, list, set, hash, key management, expiry, database management, and error atomicity behavior.

## Rationale

The intended compositional contract is that all command families share key type metadata, expiry state, and failed-command atomicity. This is structurally aligned with the unit/system gap benchmark, but the validated candidate runs showed the current public packet and rubric are too direct for Codex and do not produce a clean gap for OpenHands + DeepSeek V4.
