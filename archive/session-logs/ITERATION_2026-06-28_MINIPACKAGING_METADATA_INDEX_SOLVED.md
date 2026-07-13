# MiniPackaging MetadataIndex Lifecycle Solved Audit

Date: 2026-06-28

## Current Surface

MiniPackaging has been materially rescoped from a one-shot `resolve_metadata()` graph into a public `MetadataIndex` lifecycle:

- mutable candidate fact table;
- add/update/remove and batch `apply`;
- stateful `resolve`;
- reverse `dependents_of`;
- local `resolve_lock` and `apply_lock`;
- export/import replay;
- environment/extras reuse;
- stale lock rejection and failed mutation atomicity.

This is a strong product-shaped redesign, but current capable agents solve it.

## Current Score Reports

Rubric: `task/minipackaging-realrepo-001/rubric.json`

- Reference: `score_report_reference_metadata_index_lifecycle_current_20260628.json`
  - 31/31 cases, weight 172/172, unit 100.00%, system 100.00%.
- Codex subagent MetadataIndex lifecycle artifact: `score_report_codex_subagent_metadata_index_lifecycle_current_20260628.json`
  - 31/31 cases, weight 172/172, unit 100.00%, system 100.00%.
- OpenHands DeepSeek V4 Pro MetadataIndex lifecycle artifact: `score_report_openhands_deepseek_v4_pro_metadata_index_lifecycle_current_20260628.json`
  - 31/31 cases, weight 172/172, unit 100.00%, system 100.00%.

## Provenance And Implementation Relation

OpenHands trace: `runs/minipackaging-realrepo-001/openhands_deepseek_v4_pro_metadata_index_lifecycle_001_utf8.log`.

The OpenHands task file gave the public PRD and target output directory. The log shows a fresh agent reading the public packet, implementing `minipackaging.py`, debugging against public behavior, and finishing with a scoreable artifact.

Implementation hashes differ from the reference:

- reference: 31,295 bytes, sha256 `c9b1deca947cc90b238a1262213ab5452788bacd4cf7a73b132144bf7de33fa8`
- Codex: 34,145 bytes, sha256 `32a1fa4acf0e900bdf0401c79f071ce1bb08dd4022b84bc8c60711033d766d84`
- OpenHands: 58,301 bytes, sha256 `c6227ab130e84f77bbee7311252eec3e6e28cae8000b485aa3b8301878eefa4f`

Line-level similarity is low, and shared structure is product-obvious: normalized candidate table, revision, resolver projections, and lock replay.

## Independent Solved Audit

A read-only solved-auditor subagent returned `solved-retire`.

Rationale:

- Reference, Codex, and OpenHands all match the current 31-case / 172-weight rubric at 100/100.
- Two non-identical candidate implementations satisfy the public lifecycle surface.
- Current tests already cover add/update/remove, invalidation, reverse dependents, environment/extras reuse, lock freeze/replay, stale lock rejection, export/import, atomic failed apply/remove/update, exclusions, and stateless/stateful projection equivalence.
- Remaining possible checks would be distorted unless the public product scope becomes materially larger.

Rejected future checks:

- exact lock layout;
- private export shape;
- exact exception text/classes beyond public families;
- arbitrary ordering;
- private helper state;
- source architecture identity;
- full pip backtracking, network behavior, or installer-scale lockfile semantics.

## Decision

Retire MiniPackaging at the current MetadataIndex lifecycle scope. Do not add adjacent hidden rows. Continue only if the public product scope is materially enlarged beyond this local metadata index, which would be a new task rather than a repair of this one.
