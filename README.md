# Unit/System Gap Benchmark Core Tasks

This repository contains the strict core task set for the unit-vs-system benchmark.

## Included tasks

| Task | Source repo | Reference unit/system | Codex unit/system | OpenHands + DeepSeek unit/system | Status |
| --- | --- | ---: | ---: | ---: | --- |
| SQLite | `simonw/sqlite-utils` | 100.00 / 100.00 | 87.50 / 41.67 | 93.75 / 41.67 | core strong |
| ZK | `zk-org/zk` | 100.00 / 100.00 | 83.33 / 58.33 | 83.33 / 41.67 | core strong |
| MiniURLUtils | `mahmoud/boltons` | 100.00 / 100.00 | 100.00 / 70.00 | 100.00 / 60.00 | core strong |

MiniTofu is intentionally not included in this strict package because it is only provisional core evidence.

## Task layout

Each task directory contains:

- `source_repo.md`: source repository and provenance notes.
- `candidate_task_unit_system/public_packet.md`: public product packet shown to candidate agents.
- `candidate_task_unit_system/README.md`: task-facing usage notes when available.
- `scoring/rubrics_unit_system_v1.json`: hidden rubric cases.
- `scoring/requirement_map_unit_system_v1.md`: traceability from public packet to hidden cases.
- `scoring/score_*_unit_system.py`: deterministic scorer.
- `solution-reference/`: reference solution, which passes 100/100.
- `solution-codex-subagent-001/`: fresh Codex candidate.
- `solution-openhands-deepseek-v4-pro-001/`: comparison candidate.
- `score_report_*_unit_system_v1.json`: reference and candidate score reports.

## Evaluation principle

The benchmark separates local feature success from composed system behavior:

- Unit cases test local, single-module functionality.
- System cases test state accumulation, global invariants, cross-feature dataflow, operation order, boundary crossing, and error atomicity.
- Hidden tests must be traceable to the public packet but non-isomorphic to public examples.
- Gaps caused by exact formatting preference, environment accident, or private implementation shape are not accepted.

See `docs/unit_system_gap_benchmark_audit_v3_2026-06-03.md` for the current strict-core audit.
