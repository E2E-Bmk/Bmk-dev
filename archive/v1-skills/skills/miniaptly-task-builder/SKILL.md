---
name: miniaptly-task-builder
description: Build, revise, or audit the MiniAptly SWE unit/system-gap benchmark task. Use when editing MiniAptly PRDs, rubrics, reference implementations, candidate packets, score reports, or judge notes for archive snapshot/publish/cleanup/recovery lifecycle invariants.
---

# MiniAptly Task Builder

## Goal

Construct MiniAptly as an aptly-inspired archive lifecycle task, not a Debian compatibility task. The benchmark must test whether archive state remains consistent across package pool, local repos, immutable snapshots, published indexes, cleanup reachability, recovery journal, and graph projections.

## Agreement Surface

Treat these as local free choices:

- package DB and pool layout
- snapshot and publish storage format
- index materialization strategy
- transaction journal format
- graph edge ordering
- cleanup reachability algorithm

Treat these as public invariants:

- package identity is `(name, version, arch)` and checksum is SHA256 of payload bytes
- same identity with different checksum is rejected atomically
- snapshots are immutable after creation
- publish metadata, published index, graph, and cleanup reachability agree on the published snapshot
- cleanup never removes checksums reachable from repos, snapshots, published prefixes, or pending transactions
- failed publish/switch creates a public pending state; mutating commands fail until `recover()`
- `recover()` is idempotent and leaves all projections consistent

## Unit Test Template

Unit rows must be feature-pure and should not build state through unrelated subsystems except for the minimum public setup required by that feature.

- package parser: valid control stanza, missing fields, invalid version/name/arch
- repo: add, idempotent add, conflict rejection, search predicates
- snapshot: create from repo, duplicate name rejection, merge/filter selection rules
- publish: package index and digest for explicit snapshot membership
- cleanup: reachability over simple repo/snapshot/publish states
- recovery: one fail hook and idempotent `recover()`
- graph: semantic edge presence, not edge order

Do not unit-test private pool dictionaries, exact file layout, exact graph ordering, or Debian-specific behavior.

## System Test Template

Every system row must name the cross-feature contract and compare at least three public projections.

- Snapshot immutability across repo mutation: compare `snapshot_show`, `snapshot_diff`, `published_index`, and `graph`.
- Publish switch: compare `publish_show`, `published_index`, `graph`, and `cleanup_dry_run`.
- Cleanup reachability: compare dry-run, apply result, published index, and old snapshot reachability.
- Failed publish recovery: compare old committed publish view, blocked cleanup/mutations, `recover`, graph, and final publish view.
- Merge/filter lifecycle: compare merged snapshot membership, filtered publish index, repo search/show, graph parent edges, and cleanup.

System rows should use prevalidated package fixtures so parser/checksum bugs do not dominate residual gap scoring.

## Oracle

Use the simplified reference implementation under `runs/miniaptly-realrepo-001/solution-reference/miniaptly.py` as oracle once it scores 100% unit and 100% system.

Use `tools/score_unit_system.py` with `task/miniaptly-realrepo-001/rubric.json`. Preserve score reports under `task/miniaptly-realrepo-001/doc/score_reports/`.

## Fairness Rules

- Compare semantic objects, not display strings.
- Do not require exact Debian version ordering, GPG, compression, network mirrors, or `.deb` parsing.
- Do not create hidden private-shape checks around transaction files or pool layout.
- Cluster repeated package-parser, version-parser, or checksum failures as primitive roots.
- Accept a gap only if residual compositional loss remains at least 15pp after primitive, evaluator, provider, and contamination roots are removed.

## Stop Condition

Stop after three construction cycles. Retire or rescope if a fresh capable OpenHands or Codex agent scores roughly 90%+ on both unit and system after fairness cleanup, or if all remaining failures are parser/display primitives or adjacent exact checks.
