# MiniAptly V5 Primitive-Frontload Status

Date: 2026-06-28

## Purpose

Record the post-v4 MiniAptly evidence after adding primitive-frontload coverage for the suspected `snapshot_diff` and recovery/pending-transaction roots.

## Score Evidence

| Condition | Report | Unit | System | Raw gap | Status |
|---|---|---:|---:|---:|---|
| Reference | `task/miniaptly-realrepo-001/doc/score_reports/score_report_reference_unit_system_v5_primitive_frontload.json` | 100.00% | 100.00% | 0.00pp | Reference gate passes |
| Codex subagent | `task/miniaptly-realrepo-001/doc/score_reports/score_report_codex_subagent_001_unit_system_v5_primitive_frontload.json` | 100.00% | 100.00% | 0.00pp | No capable-agent gap |
| OpenHands + DeepSeek V4 Pro | `task/miniaptly-realrepo-001/doc/score_reports/score_report_openhands_deepseek_v4_pro_003_unit_system_v5_primitive_frontload.json` | 66.67% | 60.00% | 6.67pp | Below gate |

## Failure Clusters In V5 OpenHands + DeepSeek

- `MAU002`: malformed package parser primitive rejects only 2 of 3 invalid artifacts.
- `MAU011` and `MAS001`: `snapshot_diff.changed` does not report old/new replacement records. The same root is now visible in unit and should not be counted as independent residual system evidence.
- `MAU009`, `MAU012`, and `MAS004`: failed publish-switch pending state exposes the new publish view early and does not block cleanup as expected. The primitive-frontload unit rows now expose this root before system scoring.

## Current Interpretation

MiniAptly has a strong task shape, but the current v5 evidence does not satisfy the candidate gate. Codex solves the current public/rubric surface at 100/100, and the weaker OpenHands DeepSeek run has only a 6.67pp raw unit-over-system gap after primitive roots are frontloaded.

Do not promote MiniAptly to CORE from this evidence. The next valid action is an independent fairness/solved audit. If the audit finds no residual compositional gap, continue only by naming a materially new public lifecycle or mark the current MiniAptly surface as no-gap/near-solved for capable agents.

## Independent Judge Result

Verdict: `solved-audit`.

Residual compositional gap: 0pp, or below gate.

The judge classified `MAU011` + `MAS001` as one `snapshot_diff.changed` primitive/cascade root: the system row fails because the already-frontloaded changed-record primitive returns an empty list while the other projections in the row pass. The judge classified `MAU009` + `MAU012` + `MAS004` as one pending publish isolation/recovery primitive/cascade root: the system row repeats the frontloaded failure where a failed switch exposes the new publish view early and cleanup is not blocked. `MAU002` is a package-parser primitive only.

The judge concluded that re-counting `MAS001` and `MAS004` as residual system loss would be cascade inflation. MiniAptly should not enter CORE on this evidence; the next action is solved audit or material public lifecycle rescope.

## Files Synchronized

- `MANIFEST.json`
- `CANDIDATES.md`
- `score_summary.csv`
