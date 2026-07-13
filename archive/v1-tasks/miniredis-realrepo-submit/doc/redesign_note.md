# MiniRedis Invariant Redesign Note

## Shared Fact Source

The redesigned task uses one canonical fact source: the live key namespace, where each key has a name, type tag, value object, and optional expiry timestamp.

Derived views are:

- value projections: `GET`, `LRANGE`, `SMEMBERS`, `HGETALL`;
- metadata projections: `TYPE`, `TTL`, `EXISTS`;
- namespace projections: `KEYS`, `DBSIZE`;
- batch-visible state after prior successful or failed commands.

## Expected Gap Mechanism

Unit tests remain isolated command contracts for strings, lists, sets, hashes, key management, database management, and one local wrong-type case. A function-by-function implementation can pass many of those without maintaining a coherent canonical namespace.

System tests now assert projection consistency after mixed operations. They require DEL and immediate expiry to be invisible across all views, SET to reset type and TTL, wrong-type failures to preserve value/type/listing/TTL/DBSIZE, and FLUSHDB to clear all projections before type reuse. Shell-like batch splitting, quoted values, quoted glob patterns, invalid arity, invalid numeric syntax, and display syntax are covered by unit/interface rows instead of serving as repeated system-gap evidence.

On the stored OpenHands + DeepSeek V4 candidate, invariant v3 scores 80.00% unit and 100.00% system. After moving shell parsing, quoted glob parsing, and invalid arity validation into unit/interface checks, the prior 18.89pp system gap no longer remains. The direct DeepSeek V4 candidate scores 65.00% unit and 0.00% system, but that result is dominated by feature-level hash/type-output/display defects and is not clean compositional evidence.

## Audit Risks

- `KEYS` glob behavior is still tested, but only in unit/interface coverage so a glob primitive bug does not dominate system scoring.
- List order is asserted only where public list projection semantics require it; system scoring does not repeat LPUSH ordering as a root across many cases.
- The task has no persistence requirement. The persistence-like invariant is represented as batch-visible state within one `--batch` process.
- Immediate expiry with `EXPIRE key 0` is now public semantics, because hidden tests rely on it to avoid sleeps and timing flakiness.
- The revised OpenHands result is system-perfect, so this task should be treated as likely solved for that candidate population unless natural product scope is added. Adding new system rows should focus on deeper product-natural lifecycle behavior, not parser/display edge cases.
