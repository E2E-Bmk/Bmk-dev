# MiniKV Invariant Redesign Note

## Shared Fact Source

The task now names one canonical fact source: a single key namespace where each live key has a stored value, a type tag, and optional expiry metadata. The public packet explicitly treats every method as a projection over that fact source rather than as independent feature storage.

## Derived Views

The revised system layer checks agreement among these public views:

- direct reads, existence, delete, counters, and bulk writes;
- list, set, and hash views;
- mutable objects returned by `smembers` and `hgetall`;
- wrong-type behavior and failed-operation atomicity;
- expiry cleanup, key reuse, and flush;
- save/load/save/load persistence.

## Expected Gap Mechanism

A candidate can pass many unit tests by implementing method-local behavior, but system tests require the same key's value/type/expiry state to project consistently through multiple consumers. After the fairness revision, system cases no longer charge counter auto-creation or missing-key `lrange` repeatedly. Counters in system cases are pre-seeded before increment/decrement, and delete/flush checks validate that names can be reused with fresh typed projections.

The remaining direct DeepSeek system failure is compositional: bulk writes do not share the same type-detection path as direct writes, so list/set/hash values exist in direct reads but reject type-specific views and cannot round-trip as the same public typed state. The OpenHands candidate no longer loses system points because its remaining misses are unit/local primitives.

## Current Validation

| Agent | Unit | System | Gap |
| --- | ---: | ---: | ---: |
| Reference | 100.00% | 100.00% | 0.00pp |
| Codex subagent | 100.00% | 100.00% | 0.00pp |
| OpenHands + DeepSeek V4 | 77.78% | 100.00% | -22.22pp |
| DeepSeek V4 direct | 94.44% | 85.71% | 8.73pp |

## Audit Risks

- The Codex subagent remains 100/100, so the task is not a universal separator for current agent populations.
- After cascade trimming, the stored candidates do not show the target 15pp unit-over-system gap. This is a fairness outcome, not a reason to re-add primitive cascades.
- Counter initialization and missing-key `lrange` remain public unit contracts, but they should not be used again in system unless a downstream projection diverges independently.
- The rubric avoids private data shapes and exact error text. Persistence tests use unique temp files to avoid environment collisions.
