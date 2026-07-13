# Core Task Retroactive Fairness Judge

Date: 2026-06-28

## Purpose

The original three core tasks were strong raw-gap candidates, but they had not passed the later independent `$gap-fairness-judge` standard. Three read-only subagents were assigned one task each to audit raw gap, residual compositional gap, fairness, hacking, and provenance.

## Verdict Matrix

| Task | Judge Verdict | Raw Gap Evidence | Residual Compositional Gap | Decision |
|---|---|---|---|---|
| SQLite | `revise` | Codex 45.83pp, OpenHands DeepSeek 52.08pp | Approximately 0pp after clustering | Not accepted under current gate |
| ZK | `revise` | Codex 25.00pp, OpenHands DeepSeek 41.67pp | Codex ~0pp; OpenHands ~25pp but mixed | Not accepted yet; revise primitive cascades and preserve OpenHands composition cases |
| MiniURLUtils | `revise` | Codex 30.00pp, OpenHands DeepSeek 40.00pp | Strictly about 10pp; below 15pp gate | Not accepted under current gate |

## SQLite Findings

The raw gap is dominated by repeated primitive/cascade roots.

- `transform --default` cannot create new columns. This fails `SQU012`, then cascades into `SQS002`, `SQS004`, `SQS007`, `SQS010`, `SQS011`, and `SQS012`.
- Codex also has CSV type inference cascade from `SQU002` into system rows.
- OpenHands has an upsert unknown-column atomicity miss, but that is a feature/atomicity root rather than broad composition.

Judge conclusion: hidden behavior is mostly fair and public, but one transform primitive is underweighted in unit and over-repeated in system. Revise before accepting.

## ZK Findings

ZK has the strongest remaining signal, but it is mixed.

- Codex raw gap is dominated by sort syntax and tag expression primitive cascades.
- OpenHands retains real compositional failures after clustering: created-note graph dataflow, parsed-title wiki resolution, and late target resolution.
- Requirement reference names have minor metadata inconsistencies (`REQ-links` / `REQ-graph` vs `REQ-links-graph`).

Judge conclusion: keep the OpenHands compositional rows, add unit coverage for sort suffixes, tag expression filtering, and tag-count sorting, then rerun with preserved traces.

## MiniURLUtils Findings

MiniURLUtils has a real shared-state theme, but not enough accepted residual gap.

- Authority/userinfo projection is a fair compositional miss.
- Missing-component `None` vs `''` representation is too narrow/metadata-like.
- IPv6 family detection is primitive.
- Query replacement order is primitive/readiness for OpenHands.

Judge conclusion: revise unit coverage for absent components, IPv6 family, and query replacement order; keep authority/userinfo projection and add more true cross-view invariants after primitive readiness.

## Provenance Caveat

All three audits found task-local score reports, but not full task-specific raw run directories/traces under `runs`. The reports are useful evidence, but current acceptance should require preserved fresh agent artifacts/traces when rerun.

## Updated Routing

`score_summary.csv` now marks the three former `core_strong` candidate rows as `retro_judge_revise_*`. The triage router now treats those task names as accepted-core only when no retroactive judge-revise status is present.

Current conclusion: after applying the current judge standard, **there are no fully accepted core tasks yet**. SQLite, ZK, and MiniURLUtils remain the best repair candidates, with ZK currently the most promising.
