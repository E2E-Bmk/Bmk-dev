# Unit/System Gap Benchmark Audit v3

Date: 2026-06-03

This report supersedes `unit_system_gap_benchmark_audit_v2_2026-06-03.md` for the active objective. v2 correctly expanded SQLite/ZK and audited Cookiecutter, but Cookiecutter did not satisfy the new-repository requirement for the Codex target population. v3 adds MiniURLUtils as the third core repository.

## Completion Against The Objective

| Objective item | Status | Evidence |
| --- | --- | --- |
| Self-audit reasonableness | Complete | SQLite, ZK, MiniTOMLKit, Cookiecutter, and MiniURLUtils were classified by PRD fit, unit coverage, system dimensions, score band, and fairness risks. |
| Expand dimensions | Complete | SQLite and ZK now include `operation_order_sensitivity`; SQLite, ZK, MiniTOMLKit, Cookiecutter, and MiniURLUtils all cover all six tracked system dimensions. |
| Introduce a new repository meeting similar requirements | Complete | MiniURLUtils is newly packaged as unit/system v1 with reference 100/100, Codex 100/70, OpenHands+DeepSeek 100/60, and system cases covering state, invariants, boundaries, errors, order, and dataflow. |

## Core Benchmark

Use **SQLite + ZK + MiniURLUtils** as the current core suite.

| Task | Candidate | Unit | System | Gap | Judgment |
| --- | --- | ---: | ---: | ---: | --- |
| SQLite | Codex subagent | 87.50% | 41.67% | 45.83pp | Core strong |
| SQLite | OpenHands + DeepSeek V4 Pro | 93.75% | 41.67% | 52.08pp | Core strong; unit high but acceptable |
| ZK | Codex subagent | 83.33% | 58.33% | 25.00pp | Core strong |
| ZK | OpenHands + DeepSeek V4 Pro | 83.33% | 41.67% | 41.67pp | Core strong |
| MiniURLUtils | Codex subagent | 100.00% | 70.00% | 30.00pp | Core new repository |
| MiniURLUtils | OpenHands + DeepSeek V4 Pro | 100.00% | 60.00% | 40.00pp | Core new repository |

All three reference implementations score 100.00% unit and 100.00% system.

## Core Weighted Summary

| Suite | Candidate | Unit | System | Gap |
| --- | --- | ---: | ---: | ---: |
| SQLite + ZK | Codex subagent | 85.29% | 50.00% | 35.29pp |
| SQLite + ZK | OpenHands + DeepSeek V4 Pro | 88.24% | 41.67% | 46.57pp |
| SQLite + ZK + MiniURLUtils | Codex subagent | 88.37% | 55.88% | 32.49pp |
| SQLite + ZK + MiniURLUtils | OpenHands + DeepSeek V4 Pro | 90.70% | 47.06% | 43.64pp |

MiniURLUtils raises the unit average because both candidates pass all unit cases, but the system gap remains large and stable.

## Dimension Coverage Matrix

| Task | Cross-feature | State accumulation | Global invariant | Error atomicity | Operation order | Boundary crossing |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| SQLite | 2 | 2 | 2 | 2 | 2 | 2 |
| ZK | 2 | 2 | 2 | 1 | 2 | 3 |
| MiniURLUtils | 2 | 1 | 2 | 1 | 2 | 2 |
| MiniTOMLKit | 2 | 3 | 4 | 2 | 1 | 2 |
| Cookiecutter | 2 | 2 | 3 | 2 | 1 | 2 |

## New Repository Audit: MiniURLUtils

Rating: **core strong as third repository**.

Why it fits:

- Real source: `mahmoud/boltons`-inspired URL utility subset in `miniurlutils-realrepo-001`.
- State dependency is explicit: parsed components feed mutable `URL` objects; `QueryParamDict` mutations feed URL serialization; normalization changes later navigation; extracted links become mutable URL objects.
- Global invariants are observable: absent components, host authority vs userinfo, repeated query order, sorted-query copy isolation, IPv6 authority, and error recovery.
- Hidden system cases are traceable but non-isomorphic: unit cases test individual API surfaces; system cases combine parsing, object state, query mutation, normalization, navigation, link extraction, and serialization.

Fairness audit:

- `MUS004` was corrected to standard relative URL semantics: navigating from `/api/v1` with `../v2/users` resolves to `/v2/users`, not `/api/v2/users`.
- The scorer avoids treating percent-encoding display choices for decoded spaces/slashes as hidden requirements.
- Remaining failures are product-level invariants:
  - `MUS001`: `get_authority()` includes userinfo instead of host-plus-port only.
  - `MUS002`: absent scheme/authority/host are represented as empty strings instead of missing values.
  - `MUS007`: IPv6 family detection is absent.
  - OpenHands additionally fails `MUS003`: query replacement order after append/replace.

Artifacts:

- `runs/miniurlutils-realrepo-001/candidate_task_unit_system/public_packet.md`
- `runs/miniurlutils-realrepo-001/candidate_task_unit_system/README.md`
- `runs/miniurlutils-realrepo-001/scoring/rubrics_unit_system_v1.json`
- `runs/miniurlutils-realrepo-001/scoring/score_miniurlutils_unit_system.py`
- `runs/miniurlutils-realrepo-001/scoring/requirement_map_unit_system_v1.md`
- `runs/miniurlutils-realrepo-001/solution-reference/miniurlutils.py`
- `runs/miniurlutils-realrepo-001/score_report_*_unit_system_v1.json`

## Supporting And Rejected/Provisional Tasks

| Task | Classification | Reason |
| --- | --- | --- |
| MiniTOMLKit | Supporting | Codex gap is valid, but OpenHands+DeepSeek unit is only 40.00%, too low for clean core evidence. |
| Cookiecutter | Provisional/supporting only | Structurally strong, but Codex scores 100.00% unit and 100.00% system; OpenHands gap is only 11.67pp. |

## Current Recommendation

Use the three-task core suite:

1. SQLite: durable relational state, derived lookup/FTS/schema transformations, atomic failures.
2. ZK: durable Markdown notebook state, parsed tags/links/config, graph/list invariants.
3. MiniURLUtils: mutable object state, query-param order, normalization/navigation, serialization invariants.

This satisfies the requested end state: the benchmark has been self-audited, the system-dimension range has been expanded, and a new repository has been introduced that reaches the same unit/system-gap pattern under deterministic scoring.
